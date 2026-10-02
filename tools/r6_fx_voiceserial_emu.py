"""r6 fx: Alto 보이스 +8(시작 순번, 제한기 동률 키) writer 0x71037d790c 원본 실행.

0x71037d790c(pool) = 보이스 풀에서 빈 보이스(+8 == 0)를 찾아(검색 시작 = pool+0x38, 끝까지 → 처음부터)
  보이스 +8 = pool+0x20, pool+0x20 += 1(0xFFFFFFFF 다음은 1, 0 건너뜀), pool+0x40 목록에 연결, pool+0x50 += 1.
하네스: 풀 객체·보이스 배열을 합성해 원본 함수를 그대로 실행하고, 독립 재구현과 반환 보이스·+8·pool+0x20/+0x38 을 비교.
스텁: nn::os::Lock/UnlockMutex PLT(0x7103e99fd0/0x7103e99ff0) ret.
사용: PY web/tools/r6_fx_voiceserial_emu.py
"""
import struct
import sys
import json
import random
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted" / "exefs" / "main.reloc.img"
BASE, HEAP, STACK, END = 0x7100000000, 0x20000000, 0x10000000, 0x30000000
FN = 0x71037d790c
NODE_OFF = 0x230


def main():
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    img = IMG.read_bytes()
    mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
    mu.mem_write(BASE, img)
    mu.mem_map(HEAP, 0x400000)
    mu.mem_map(STACK, 0x100000)
    mu.mem_map(END, 0x1000)
    mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
    for a in (0x7103e99fd0, 0x7103e99ff0):
        mu.mem_write(a, struct.pack('<I', 0xD65F03C0))
    q = lambda a, v: mu.mem_write(a, struct.pack('<Q', v))
    w = lambda a, v: mu.mem_write(a, struct.pack('<I', v & 0xffffffff))
    r32 = lambda a: struct.unpack('<I', mu.mem_read(a, 4))[0]
    rnd = random.Random(6)
    ok = bad = 0
    log = []
    for case in range(300):
        n = rnd.randint(1, 12)
        pool = HEAP
        mu.mem_write(pool, b'\0' * 0x200)
        arr = HEAP + 0x200
        voices = [HEAP + 0x1000 + i * 0x300 for i in range(n)]
        for i, v in enumerate(voices):
            mu.mem_write(v, b'\0' * 0x300)
            q(arr + 8 * i, v)
        w(pool + 0x28, n)
        q(pool + 0x30, arr)
        start = rnd.choice([1, 2, 0x7ffffffe, 0xfffffffe, 0xffffffff, rnd.randint(1, 1 << 32 - 1)])
        w(pool + 0x20, start)
        w(pool + 0x38, rnd.randint(0, n - 1))
        w(pool + 0x54, NODE_OFF)
        # 재구현 상태
        serial = [0] * n
        for i in range(n):
            if rnd.random() < 0.4:
                serial[i] = rnd.randint(1, 1000)
                w(voices[i] + 8, serial[i])
        ctr, sidx, cnt = start, r32(pool + 0x38), 0
        for step in range(rnd.randint(1, 15)):
            if rnd.random() < 0.3:
                k = rnd.randrange(n)
                serial[k] = 0
                w(voices[k] + 8, 0)
            # 재구현: 0x71037d790c
            got_idx = None
            if sidx < n:
                for j in range(sidx, n):
                    if serial[j] == 0:
                        got_idx = j
                        sidx = sidx + 1          # 찾은 칸이 아니라 검색 시작 +1 [판독 0x71037d79a8]
                        break
            if got_idx is None:
                if sidx >= 1:
                    for j in range(0, sidx):
                        if serial[j] == 0:
                            got_idx = j
                            sidx = 0 if sidx >= n else sidx + 1   # 0x71037d79c4 csinc
                            break
            exp_v = None
            if got_idx is not None:
                exp_v = voices[got_idx]
                serial[got_idx] = ctr
                ctr = 1 if ctr == 0xffffffff else ctr + 1
                cnt += 1
            mu.reg_write(UC_ARM64_REG_X0, pool)
            mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
            mu.reg_write(UC_ARM64_REG_LR, END)
            mu.emu_start(FN, END, count=100000)
            ret = mu.reg_read(UC_ARM64_REG_X0)
            got = (ret, [r32(v + 8) for v in voices], r32(pool + 0x20), r32(pool + 0x38), r32(pool + 0x50))
            exp = (exp_v or 0, list(serial), ctr, sidx, cnt)
            if got == exp:
                ok += 1
            else:
                bad += 1
                if len(log) < 5:
                    log.append({'case': case, 'step': step, 'got': [hex(got[0])] + list(got[1:]), 'exp': [hex(exp[0])] + list(exp[1:])})
    print('ok', ok, 'bad', bad)
    for l in log:
        print(l)
    out = ROOT / 'analysis/completion/r6/fx_voiceserial_emu.json'
    out.write_text(json.dumps({'ok': ok, 'bad': bad, 'first_bad': log}, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
