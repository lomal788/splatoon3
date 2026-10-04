"""r7 player: 이동 계산 웹 테스트 fixture (원본 실행 결과만 담는다).

A. acos 0x7101252780, 방향 보간 0x7101252ff0(axis = null — 플레이어 호출부는 모두 null)을 unicorn으로 직접 실행.
   입력 생성은 r5_player_lerpdir_emu.py 와 같은 분포(같은 시드), 개수만 줄였다.
B. 이미 원본 실행으로 얻은 결과 파일에서 행을 옮긴다(재실행 없음):
   analysis/completion/r5_player_input_emu.json   (데드존 구간·0x71024a7100)
   analysis/completion/roll_counter_emu.json      (0x7102459b44 감쇠 반복곱·n/마지막 프레임 쓰기)
   analysis/completion/squid_speed_k.json         (0x710266c6e4)
   analysis/r6_player/walljump_emu.json           (0x7102458a18 원본 연결 실행)
결과: web/games/splatoon3/tests/fixtures/player_move_native.json
"""
import json, random, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_lerpdir_emu import UC, F, bits, cases  # noqa: E402
from unicorn.arm64_const import UC_ARM64_REG_S0  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/games/splatoon3/tests/fixtures/player_move_native.json'


def hx(u):
    return '%08x' % u


def main():
    e = UC()
    out = e.alloc(16); pa = e.alloc(16); pb = e.alloc(16)
    rng = random.Random(20261003)
    acos = []
    xs = [F(-1.5), F(-1), F(-0.9999), F(-0.7071068), F(-0.70710677), F(-0.5), F(-1e-8), F(0), F(1e-8), F(0.3),
          F(0.70710677), F(0.7071068), F(0.9999), F(1), F(1.5)] + [F(rng.uniform(-1, 1)) for _ in range(2000)]
    for x in xs:
        e.call(0x7101252780, fargs=(float(x),))
        acos.append([hx(bits(x)), hx(e.mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff)])
    all_cases = [c for c in cases(random.Random(20261003)) if c[3] is None]
    pick = all_cases[:7] + all_cases[7:7 + 700] + all_cases[6007:6007 + 500] + all_cases[9007:9007 + 400]
    pick += all_cases[10507:10507 + 200] + all_cases[-600:]
    slerp = []
    for t, a, b, _ in pick:
        e.mu.mem_write(pa, struct.pack('<3f', *map(float, a)))
        e.mu.mem_write(pb, struct.pack('<3f', *map(float, b)))
        e.mu.mem_write(out, b'\0' * 12)
        e.call(0x7101252ff0, out, pa, pb, 0, fargs=(float(t),))
        got = struct.unpack('<3I', bytes(e.mu.mem_read(out, 12)))
        slerp.append(dict(t=hx(bits(t)), a=[hx(bits(F(v))) for v in a], b=[hx(bits(F(v))) for v in b], got=[hx(g) for g in got]))

    inp = json.loads((ROOT / 'analysis/completion/r5_player_input_emu.json').read_text(encoding='utf-8'))
    dead = [dict(stick=[hx(bits(F(v))) for v in r['stick']], prev=hx(bits(F(r['prev480']))), got=[g[2:].zfill(8) for g in r['got']])
            for r in inp['deadzone_range']['rows_head']]
    wall = [dict(n=[hx(bits(F(v))) for v in r['n']], d=[hx(bits(F(v))) for v in r['d']], c=[hx(bits(F(v))) for v in r['c']],
                 stick=[hx(bits(F(v))) for v in r['stick']], prev=[hx(bits(F(v))) for v in r['prev']], got=[g[2:].zfill(8) for g in r['got']])
            for r in inp['wall_input']['rows_head']]
    roll = json.loads((ROOT / 'analysis/completion/roll_counter_emu.json').read_text(encoding='utf-8'))
    damping = [[r['n'], hx(bits(F(r['ratio']))), r['got'][2:].zfill(8)] for r in roll['damping']]
    writes = [[r['n'], r['frame'], r['got'][0], r['got'][1]] for r in roll['writes']]
    kk = json.loads((ROOT / 'analysis/completion/squid_speed_k.json').read_text(encoding='utf-8'))
    squidk = [dict(table=r['table'], flags=int(r['flags'], 16), arg=r['arg'], got=r['got'][2:].zfill(8)) for r in kk['rows']]
    wj = json.loads((ROOT / 'analysis/r6_player/walljump_emu.json').read_text(encoding='utf-8'))
    walljump = []
    for r in wj['rows']:
        if not r['at_call']:
            continue
        walljump.append(dict(F=hx(bits(F(r['F']))), c774=r['at_call']['c774'], y754_before=hx(r['at_call']['y754']),
                             y754=hx(r['y754']), b780=r['b780'], b782=r['b782'], b781=r['b781'], y748=hx(r['y748'])))
    res = dict(source='원본 실행(unicorn): acos/slerp 이번 실행, 나머지는 각 도구의 원본 실행 결과 파일',
               acos=acos, slerp=slerp, deadzone=dead, wall_input=wall, damping=damping, launch_writes=writes,
               squid_k=squidk, walljump=walljump)
    OUT.write_text(json.dumps(res, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('acos', len(acos), 'slerp', len(slerp), 'deadzone', len(dead), 'wall', len(wall), 'damping', len(damping),
          'writes', len(writes), 'squid_k', len(squidk), 'walljump', len(walljump), '->', OUT)


if __name__ == '__main__':
    main()
