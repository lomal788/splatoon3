"""ASB(애니메이션 시퀀스 바이너리, 'ASB ' v0x410) 판독기 — 플레이어 애니 상태머신용.

판독 범위(근거는 web/docs/graphics/anim_state_machine.md):
  헤더 u32[26]  +0x0C 커맨드 수, +0x10 노드 수, +0x20 로컬 블랙보드, +0x24 문자열 풀, +0x30 노드 본문 시작
  커맨드(0x68부터, 0x2C B): +0 이름, +8 f32(-1), +0x18 GUID, +0x28 루트 노드 번호
  노드(커맨드 뒤, 0x24 B): u16 종류, u16 플래그, u32 0, u32 본문 오프셋, u32, u32, GUID
  본문 안 자식 목록: (n | n<<24, n<<8 | n<<24, n개 항목 오프셋) — 항목의 마지막 u32 = 자식 노드 번호(추정)
  값 참조: 0x8xxxxxxx = 블랙보드 참조(상위 4비트로 종류 구분, 하위 = 종류 안 순번)

사용:
  PY web/tools/state_asb.py <x.asb> [--tree] [--json 출력.json]
"""
import struct, sys, json

NODE_KIND = {  # [추정] 본문 모양으로 붙인 이름 (anim_state_machine.md §3)
    2: 'StringSelector', 3: 'SkeletalAnim', 6: 'FloatBlend', 7: 'Two', 8: 'IntSelector',
    9: 'Simultaneous', 10: 'IndexList', 11: 'SubAnim', 12: 'FrameCtrl', 18: 'NamedAnim',
    19: 'BoneBlend', 21: 'StringSwitch',
}


def load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'ASB ', 'ASB 아님'
    H = struct.unpack_from('<26I', d, 0)
    ver, ncmd, nnode, sp, body0 = H[1], H[3], H[4], H[9], H[12]

    def s(o):
        e = d.index(b'\0', sp + o)
        return d[sp + o:e].decode('utf8', 'replace')

    cmds = []
    o = 0x68
    for i in range(ncmd):
        name = struct.unpack_from('<I', d, o)[0]
        root = struct.unpack_from('<I', d, o + 0x28)[0]
        cmds.append({'i': i, 'name': s(name), 'root': root})
        o += 0x2C
    nodes = []
    for i in range(nnode):
        t, fl, _, body, a, b = struct.unpack_from('<HHIIII', d, o)
        nodes.append({'i': i, 'type': t, 'flag': fl, 'body': body, 'x10': a, 'x14': b})
        o += 0x24
    bodies = sorted(set(n['body'] for n in nodes))
    bend = H[14]  # +0x38 이후 섹션 시작(본문 끝 근사)
    for n in nodes:
        nxt = [x for x in bodies if x > n['body']]
        e = min(nxt) if nxt else bend
        if e <= n['body'] or e - n['body'] > 0x400:
            e = n['body'] + 0x40
        ws = list(struct.unpack_from('<%dI' % ((e - n['body']) // 4), d, n['body']))
        n['words'] = ws
        # 자식 목록
        kids = []
        klist = len(ws)
        for k in range(len(ws) - 1):
            c = ws[k] & 0xff
            if c and ws[k] == (c | c << 24) and ws[k + 1] == (c << 8 | c << 24) and k + 2 + c <= len(ws):
                offs = ws[k + 2:k + 2 + c]
                for j, off in enumerate(offs):
                    nxt_off = offs[j + 1] if j + 1 < c else None
                    if nxt_off is None:
                        ln = (offs[1] - offs[0]) if c > 1 else 4
                    else:
                        ln = nxt_off - off
                    if ln <= 0 or ln > 0x40:
                        ln = 4
                    ent = list(struct.unpack_from('<%dI' % (ln // 4), d, off))
                    kid = ent[-1]
                    case = [s(w) for w in ent[:-1] if 0 < w < 0x3000 and d[sp + w - 1:sp + w] == b'\0' and d[sp + w:sp + w + 1] != b'\0']
                    kids.append({'child': kid, 'entry': [hex(w) for w in ent], 'case': case})
                klist = k
                break
        # 문자열 인자
        strs = []
        for w in ws[:klist]:
            if 0 < w < len(d) - sp and d[sp + w - 1:sp + w] == b'\0' and d[sp + w:sp + w + 1] not in (b'\0',):
                try:
                    v = s(w)
                    if v.isprintable() and len(v) >= 2:
                        strs.append(v)
                except Exception:
                    pass
        n['strs'] = strs
        n['bbref'] = [hex(w) for w in ws[:klist] if w >> 31 and (w & 0x0fffffff) < 0x100]
        n['kids'] = kids
    return {'version': hex(ver), 'commands': cmds, 'nodes': nodes, 'header': [hex(x) for x in H]}


def tree(asb, idx, depth=0, seen=None, out=None):
    seen = seen or set()
    out = out if out is not None else []
    n = asb['nodes'][idx]
    tag = NODE_KIND.get(n['type'], 't%d' % n['type'])
    extra = ' '.join(['"%s"' % x for x in n['strs']] + n['bbref'][:2])
    out.append('  ' * depth + f'[{idx}] {tag} {extra}')
    if idx in seen or depth > 12:
        return out
    seen = seen | {idx}
    for k in n['kids']:
        c = k['child']
        if 0 <= c < len(asb['nodes']):
            if k['case']:
                out.append('  ' * (depth + 1) + 'case ' + ','.join(k['case']))
            tree(asb, c, depth + 1, seen, out)
    return out


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    asb = load(a[0])
    print('version', asb['version'], 'commands', len(asb['commands']), 'nodes', len(asb['nodes']))
    from collections import Counter
    print('node types', dict(Counter(n['type'] for n in asb['nodes'])))
    for c in asb['commands']:
        if '--tree' in a:
            print(f"== {c['i']} {c['name']} -> node {c['root']}")
            print('\n'.join(tree(asb, c['root'])))
        else:
            n = asb['nodes'][c['root']]
            print(c['i'], c['name'], 'root', c['root'], NODE_KIND.get(n['type'], n['type']), n['strs'][:3])
    if '--json' in a:
        out = a[a.index('--json') + 1]
        json.dump(asb, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
