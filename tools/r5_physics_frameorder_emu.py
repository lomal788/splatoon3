"""[r5 physics] 프레임 작업 그래프 원본 실행 검증.

원본 함수를 unicorn 으로 그대로 실행한다.
  1) 0x7103dec4e8  CalcPriority 문자열 -> 값 (열거 문자열 표 0x7103dec698 은 미리 채운 표로 대체)
  2) 0x7103c88e74  시퀀서 노드를 관리자 목록 L[단계][그룹] 에 연결
  3) 0x7103c85fbc  프레임 작업 그래프 구성(장벽 B[p][g] 사슬 + 목록 작업 간선)
독립 재구현(아래 expected_*)과 비교한다. 재구현은 디컴파일 판독식을 따로 옮긴 것이고,
원본 실행 결과를 보고 맞춘 것이 아니다.

스텁:
  - 0x710351c678 (그래프 노드 추가, 라이브러리): 호출 순서대로 id 0,1,2... 를 돌려 주고 desc+8 의 작업 포인터를 기록
  - 0x7103e99fd0 / 0x7103e99ff0 (LockMutex/UnlockMutex): 바로 반환
  - 시퀀서 vt+0x10 (단계·노드 사용 여부): 항상 1
  - 0x7103dec698 의 정적 초기화: 원본 문자열 "Before, Default, After, Late" 를 분리한 표를 미리 메모리에 둠
검증 안 한 범위: 작업자 스레드 실행·의존 수 감소(0x7103ad3064)·동적 하위 그래프(0x7103acaee0)·배치 분기(작업자 수 >= 2).
"""
import json, struct, random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC, BASE, STACK

ROOT = Path(__file__).resolve().parents[2]
NODE_ADD = BASE + 0x351c678
LOCK = BASE + 0x3e99fd0
UNLOCK = BASE + 0x3e99ff0


def mk():
    h = UC()
    mu = h.mu
    st = {'next_id': 0, 'added': []}
    ret1 = h.alloc(0x10)

    def hook(m, a, s, d):
        if a == NODE_ADD:
            desc = m.reg_read(UC_ARM64_REG_X1)
            job = struct.unpack('<Q', bytes(m.mem_read(desc + 8, 8)))[0]
            nid = st['next_id']; st['next_id'] += 1
            st['added'].append((nid, job))
            m.reg_write(UC_ARM64_REG_X0, nid)
            m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
        elif a in (LOCK, UNLOCK):
            m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
        elif a == ret1:
            m.reg_write(UC_ARM64_REG_X0, 1)
            m.reg_write(UC_ARM64_REG_PC, m.reg_read(UC_ARM64_REG_LR))
    for a in (NODE_ADD, LOCK, UNLOCK):
        mu.hook_add(UC_HOOK_CODE, hook, begin=a, end=a)
    mu.hook_add(UC_HOOK_CODE, hook, begin=ret1, end=ret1)
    return h, st, ret1


def q(mu, a, v): mu.mem_write(a, struct.pack('<Q', v & 0xffffffffffffffff))
def u32(mu, a, v): mu.mem_write(a, struct.pack('<I', v & 0xffffffff))
def u16(mu, a, v): mu.mem_write(a, struct.pack('<H', v & 0xffff))
def r16(mu, a): return struct.unpack('<H', bytes(mu.mem_read(a, 2)))[0]
def r64(mu, a): return struct.unpack('<Q', bytes(mu.mem_read(a, 8)))[0]


# ---------------- 1) CalcPriority ----------------
def test_calcprio():
    h, st, _ = mk(); mu = h.mu
    names = ['Before', 'Default', 'After', 'Late']
    tbl = h.alloc(0x40)
    for i, n in enumerate(names):
        s = h.alloc(16); mu.mem_write(s, n.encode() + b'\0'); q(mu, tbl + 8 * i, s)
    q(mu, BASE + 0x59a9980, tbl)  # 0x7103dec698 가 돌려줄 표(정적 초기화 결과 대체)
    expect = {'Before': 2, 'Default': 3, 'After': 4, 'Late': 5}   # 독립 재구현: 0x7103dec4e8 판독
    cases = names + ['default', 'Lat', 'Later', '', 'Befor', 'After ']
    out = []; ok = 0
    for c in cases:
        s = h.alloc(16); mu.mem_write(s, c.encode() + b'\0')
        pv = h.alloc(16); q(mu, pv, s)
        res = h.alloc(8); u32(mu, res, 0xdeadbeef)
        r = h.call(BASE + 0x3dec4e8, res, pv) & 0xff
        val = struct.unpack('<I', bytes(mu.mem_read(res, 4)))[0]
        exp_r = 1 if c in expect else 0
        exp_v = expect.get(c, 0xdeadbeef)
        good = (r == exp_r and val == exp_v)
        ok += good
        out.append({'input': c, 'ret': r, 'value': val, 'expected_ret': exp_r, 'expected_value': exp_v, 'match': good})
    return {'function': '0x7103dec4e8', 'cases': len(cases), 'passed': ok, 'detail': out}


# ---------------- 2,3) 그래프 ----------------
def build(h, ret1, seqdefs, workers=1):
    """seqdefs: [(name, [(phase, group, pushfront)])]"""
    mu = h.mu
    mgr = h.alloc(0x600)
    G = h.alloc(0x400)
    P = h.alloc(0x10); q(mu, P, G); q(mu, mgr + 0xa0, P)
    NE = 4096
    arr = h.alloc(NE * 8); recs = h.alloc(NE * 16)
    for i in range(NE):
        q(mu, recs + 16 * i, recs + 16 * (i + 1) if i + 1 < NE else 0)
    u32(mu, G + 0x30, 0); u32(mu, G + 0x34, NE); q(mu, G + 0x38, arr); q(mu, G + 0x40, recs)
    mu.mem_write(G + 0x70, b'\xff\xff' * 256)
    jobs = {}
    def job(name):
        j = h.alloc(0x30); u16(mu, j + 0x10, 0xffff); mu.mem_write(j + 0x12, bytes([1, 0, 0xff, 0]))
        jobs[j] = name; return j
    for p in range(4):
        for g in range(8):
            q(mu, mgr + 0xa8 + p * 0x40 + g * 8, job(f'B{p}{g}'))
            bj = h.alloc(0x40); u32(mu, bj + 0x28, workers); q(mu, mgr + 0x1b0 + p * 0x40 + g * 8, bj)
    q(mu, mgr + 0x1a8, job('END'))
    lists = h.alloc(4 * 0xc0)
    for p in range(4):
        for g in range(8):
            L = lists + p * 0xc0 + g * 0x18; q(mu, L, L); q(mu, L + 8, L); u32(mu, L + 0x10, 0)
    u32(mu, mgr + 0x2e8, 4); q(mu, mgr + 0x2f0, lists)
    q(mu, mgr + 0x2f8, mgr + 0x2f8); q(mu, mgr + 0x300, mgr + 0x2f8)
    u32(mu, mgr + 0x320, 0)
    vt = h.alloc(0x40); q(mu, vt + 0x10, ret1)
    placed = []
    for name, slots in seqdefs:
        seq = h.alloc(0x200); q(mu, seq, vt); u32(mu, seq + 0x24, 4)
        for k, (p, g, front) in enumerate(slots):
            node = h.alloc(0x40)
            q(mu, node + 0x10, seq)
            mu.mem_write(node + 0x20, bytes([g, g, 1 if front else 0, 0]))
            j = job(f'{name}.P{p}'); q(mu, node + 0x28, j)
            q(mu, seq + 0x30 + p * 0x40 + g * 8, node)
            h.call(BASE + 0x3c88e74, mgr, seq, p, g)
            placed.append((name, p, g, node, j))
    return mgr, G, jobs, placed, lists


def run_graph(seqdefs, workers=1):
    h, st, ret1 = mk(); mu = h.mu
    mgr, G, jobs, placed, lists = build(h, ret1, seqdefs, workers)
    # 연결 결과 검증: 노드가 L[p][g] 목록에 들어갔는가(원본 0x7103c88e74 실행 결과 읽기)
    link_ok = 0
    for name, p, g, node, j in placed:
        owner = r64(mu, node + 0x18); L = lists + p * 0xc0 + g * 0x18
        link_ok += (owner == L)
    counts = {(p, g): struct.unpack('<i', bytes(mu.mem_read(lists + p * 0xc0 + g * 0x18 + 0x10, 4)))[0] for p in range(4) for g in range(8)}
    exp_counts = {}
    for _, p, g, _, _ in placed: exp_counts[(p, g)] = exp_counts.get((p, g), 0) + 1
    counts_ok = all(counts[k] == exp_counts.get(k, 0) for k in counts)
    # param_2 버퍼, 스택 인자(param_9=0, param_10=0)
    p2 = h.alloc(0x20)
    sp = STACK + 0xF0000
    q(mu, sp, 0); q(mu, sp + 8, 0)
    h.call(BASE + 0x3c85fbc, mgr, p2, 0xF, 0, 0, 0, 0, 0xffff)
    idname = {}
    for j, n in jobs.items():
        nid = r16(mu, j + 0x10)
        if nid != 0xffff: idname[nid] = n
    cnt = struct.unpack('<i', bytes(mu.mem_read(G + 0x30, 4)))[0]
    arr = r64(mu, G + 0x38)
    edges = []
    for i in range(cnt):
        rec = r64(mu, arr + 8 * i)
        a, b = struct.unpack('<HH', bytes(mu.mem_read(rec, 4)))
        edges.append((idname.get(a, f'#{a}'), idname.get(b, f'#{b}')))
    return {'edges': sorted(edges), 'link_ok': link_ok, 'placed': len(placed), 'counts_ok': counts_ok}


def expected_edges(seqdefs):
    """독립 재구현: B[p][g]->B[p][g+1], B[p][7]->B[p+1][0], B[3][7]->END, 작업 J(p,g): B[p][g]->J, J->다음 장벽."""
    E = []
    for p in range(4):
        for g in range(7): E.append((f'B{p}{g}', f'B{p}{g+1}'))
        if p < 3: E.append((f'B{p}7', f'B{p+1}0'))
    E.append(('B37', 'END'))
    def nxt(p, g):
        if g < 7: return f'B{p}{g+1}'
        return f'B{p+1}0' if p < 3 else 'END'
    for name, slots in seqdefs:
        for (p, g, front) in slots:
            J = f'{name}.P{p}'
            E += [(f'B{p}{g}', J), (J, nxt(p, g))]
    return sorted(E)


def order_check(edges):
    """원본 간선으로 도달 관계를 계산해 사격장 순서를 확인."""
    from collections import defaultdict
    adj = defaultdict(set)
    for a, b in edges: adj[a].add(b)
    def reach(a, b):
        seen = {a}; st = [a]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y == b: return True
                if y not in seen: seen.add(y); st.append(y)
        return False
    chain = ['Target.P0', 'Player.P0', 'Bullet.P0', 'PhysEntity.P0', 'ContactEntity.P1',
             'Target.P1', 'Player.P1', 'Bullet.P1', 'PhysSensor.P2']
    pairs = [(chain[i], chain[i + 1], reach(chain[i], chain[i + 1])) for i in range(len(chain) - 1)]
    same = [('PhysEntity.P0', 'PhysJoin.P0', reach('PhysEntity.P0', 'PhysJoin.P0') or reach('PhysJoin.P0', 'PhysEntity.P0')),
            ('PhysSensor.P2', 'ContactSensor.P2', reach('PhysSensor.P2', 'ContactSensor.P2') or reach('ContactSensor.P2', 'PhysSensor.P2')),
            ('Bullet2.P0', 'Bullet.P0', reach('Bullet2.P0', 'Bullet.P0') or reach('Bullet.P0', 'Bullet2.P0'))]
    return pairs, same


def main():
    res = {'calc_priority': test_calcprio()}
    # 사격장 구성: 그룹 = CalcPriority 값(Before 2 / Default 3 / After 4), 물리 노드 (0,6)/(2,0), 접촉 반응 (1,0)/(2,0)
    scene = [
        ('Target', [(0, 2, False), (1, 2, False)]),
        ('Player', [(0, 3, False), (1, 3, False)]),
        ('Bullet', [(0, 4, False), (1, 4, False)]),
        ('Bullet2', [(0, 4, True), (1, 4, True)]),
        ('PhysEntity', [(0, 6, True), (2, 0, True)]),
        ('PhysJoin', [(0, 6, True)]),
        ('ContactEntity', [(1, 0, True)]),
        ('ContactSensor', [(2, 0, True)]),
    ]
    # PhysEntity 의 단계2 노드는 Sensor 갱신이다(0x7103db48a4: 0x10606 / 0x10000). 이름만 구분해 둔다.
    scene_named = [(n if not (n == 'PhysEntity') else n, s) for n, s in scene]
    g = run_graph(scene_named)
    # 단계2 노드 이름을 PhysSensor 로 바꿔 순서 검사에 쓴다.
    ren = lambda x: 'PhysSensor.P2' if x == 'PhysEntity.P2' else x
    g_edges = sorted((ren(a), ren(b)) for a, b in g['edges'])
    exp = sorted((ren(a), ren(b)) for a, b in expected_edges(scene_named))
    pairs, same = order_check(g_edges)
    res['graph_scene'] = {'functions': ['0x7103c88e74', '0x7103c85fbc'], 'edges_original': len(g_edges),
                          'edges_expected': len(exp), 'exact_match': g_edges == exp,
                          'link_ok': f"{g['link_ok']}/{g['placed']}", 'list_counts_ok': g['counts_ok'],
                          'order_pairs(a before b)': pairs, 'same_group_unordered(a~b reachable?)': same}
    # 무작위 배치 200 회: 임의 (p,g)·앞/뒤 삽입
    rng = random.Random(20261003); ok = 0; fails = []
    for t in range(500):
        n = rng.randrange(1, 9)
        defs = []
        for i in range(n):
            slots = []; used = set()
            for _ in range(rng.randrange(1, 4)):
                p = rng.randrange(4)
                if p in used: continue
                used.add(p); slots.append((p, rng.randrange(8), rng.random() < 0.5))
            defs.append((f'S{i}', slots))
        r = run_graph(defs)
        e = expected_edges(defs)
        good = (r['edges'] == e and r['link_ok'] == r['placed'] and r['counts_ok'])
        ok += good
        if not good and len(fails) < 3: fails.append({'defs': defs, 'orig': r['edges'][:20], 'exp': e[:20]})
    res['graph_random'] = {'cases': 500, 'passed': ok, 'fails': fails}
    res['stubs'] = ['0x710351c678 그래프 노드 추가 → 순번 id', 'LockMutex/UnlockMutex 반환', '시퀀서 vt+0x10 → 1',
                    '0x7103dec698 정적 표를 원본 문자열 분리 결과로 미리 채움']
    res['unverified'] = ['작업자 수 >= 2 배치 분기', '시퀀서 간 의존 목록(관리자+0x320)', '외부 작업 목록(param_4 bit0)',
                         '동적 하위 그래프 0x7103acaee0 와 합류 해제 0x7103ad3064', '실제 액터 CalcPriority 런타임 값(데이터로만 확인)']
    p = ROOT / 'analysis/completion/r5_physics_frameorder_emu.json'
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    cp = res['calc_priority']; gs = res['graph_scene']; gr = res['graph_random']
    print(f"CalcPriority 0x7103dec4e8: {cp['passed']}/{cp['cases']}")
    print(f"scene graph: exact={gs['exact_match']} edges {gs['edges_original']}/{gs['edges_expected']} link {gs['link_ok']} counts {gs['list_counts_ok']}")
    for a, b, r in gs['order_pairs(a before b)']: print(f"   {a} -> {b}: {r}")
    for a, b, r in gs['same_group_unordered(a~b reachable?)']: print(f"   same group {a} ~ {b}: reachable={r}")
    print(f"random graphs: {gr['passed']}/{gr['cases']}")
    print('result', p)


if __name__ == '__main__':
    main()
