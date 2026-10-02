"""[r5 combat] 피격·판정 계산 함수를 원본 그대로 unicorn 으로 실행해 독립 재구현과 비트 대조한다.

원본 실행 대상(수정 없음):
  A 0x71017506d0  슈터 탄 데미지 감쇠(DamageParam $parent 체인 해석 포함)
  B 0x71018a6b68 / 0x71018a6fe4  탄 충돌 반경(Field / Player, CollisionParam 체인 해석 포함)
  C 0x7101e66c4c  넉백 벡터
  D 0x71016e6260  같은 샷 크리티컬 누적 링
  E 0x7101a86ec0  DamageReceiver 결과 판정(팀·배율·이력 모드 1~6·시간 창·상한) + 0x7101a87edc(모드 2)
     0x7101a86dc8  수신 이력 나이 증가(15초 삭제)
  F 0x7101a86be8  리시버 팀별 히트마커 플래그 갱신, 0x7101a87e8c  예측 히트 종류(조준 표시)
재구현은 이 파일의 ref_* 함수(문서 web/docs/combat/*.md 의 의사코드를 파이썬 f32 로 옮긴 것)이며 원본 명령을 흉내 내지 않는다.

스텁(원본 대신 파이썬이 처리한 범위):
  - 허용 목록 밖 게임 함수는 x0=0 반환(호출 기록). PLT memcpy/memset/strlen 은 파이썬, __cxa_guard_acquire 는 0(초기화 생략)
  - E: DamageInfo 복사 0x71017db2d4 는 원본 실행(모드 3 사본)
       DamageRateInfo 조회 0x7101a856e8 → s0 = 시나리오가 정한 배율(표 조회 자체는 실행 안 함)
       ObjectEffect_Up 0x7101a87aa0 → 아무것도 안 함(공격자 기어 없음과 같음)
       송신자(sender) 객체 = 힙에 만든 가짜 vtable(슬롯 0x18 핸들, 0x20 모드, 0x28 간격, 0x30/0x38 bool, 0x40 상한, 0x48 key)
       DamageInfo+0xa9(높이 필터) = 0 고정 → 그 분기는 실행 안 함
  - A/B: 파라미터 객체는 힙에 만든 가짜(vt 슬롯0 IsA 가 항상 1 을 돌려주는 기계어 3줄). 필드·설정 플래그·부모 핸들 배치는 원본 오프셋
사용: PY web/tools/r5_combat_emu.py   (불일치가 있으면 종료코드 1, 결과 analysis/combat/r5_emu_combat.txt)
"""
import math
import random
import struct
import sys
from pathlib import Path

import numpy as np
from unicorn.arm64_const import (UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_S0, UC_ARM64_REG_S1,
                                 UC_ARM64_REG_S2, UC_ARM64_REG_X0)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import respawn_emu as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "combat" / "r5_emu_combat.txt"
f32 = np.float32
LOG = []


def log(s=""):
    print(s)
    LOG.append(s)


F_DMG = 0x71017506D0
F_RAD_FIELD = 0x71018A6B68
F_RAD_PLAYER = 0x71018A6FE4
F_KB = 0x7101E66C4C
F_CRIT = 0x71016E6260
F_RESULT = 0x7101A86EC0
F_MODE2 = 0x7101A87EDC
F_AGE = 0x7101A86DC8
F_HM_FLAGS = 0x7101A86BE8
F_HM_PREDICT = 0x7101A87E8C
F_RATE = 0x7101A856E8
F_OBJUP = 0x7101A87AA0
F_INFOCOPY = 0x71017DB2D4  # DamageInfo 복사(모드 3 상한 계산용 사본, 원본 실행)
CODE = 0x31000000  # 가짜 vtable 함수 기계어 영역


def fbits(v):
    return struct.unpack("<I", struct.pack("<f", float(v)))[0]


def bitsf(u):
    return struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0]


class Emu(R.Emu):
    EXPLICIT = {0x7101A87E8C: 0x7101A87EC0}  # 함수 목록에 없는 작은 함수(명령 끝 ret 확인)

    def __init__(self, allowed):
        super().__init__([a for a in allowed if a not in self.EXPLICIT])
        self.allowed += [(a, self.EXPLICIT[a]) for a in allowed if a in self.EXPLICIT]
        self.mu.mem_map(CODE, 0x100000)
        self.code_next = CODE
        self.rate = 1.0
        self.special = {F_RATE: self._rate_stub}

    def _allowed(self, a):
        return CODE <= a < CODE + 0x100000 or super()._allowed(a)

    def _rate_stub(self, mu):
        mu.reg_write(UC_ARM64_REG_S0, fbits(self.rate))

    def _block(self, mu, addr, size, user):
        fn = self.special.get(addr)
        if fn is not None:
            self.calls.append((addr, "special", []))
            fn(mu)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        super()._block(mu, addr, size, user)

    # --- 작은 기계어 함수 생성 ---
    def code(self, words):
        a = self.code_next
        self.mu.mem_write(a, b"".join(struct.pack("<I", w) for w in words))
        self.code_next += (len(words) * 4 + 0xF) & ~0xF
        return a

    @staticmethod
    def _mov32(rd, v, x=False):
        v &= 0xFFFFFFFF
        base_z, base_k = (0xD2800000, 0xF2800000) if x else (0x52800000, 0x72800000)
        return [base_z | ((v & 0xFFFF) << 5) | rd, base_k | (1 << 21) | (((v >> 16) & 0xFFFF) << 5) | rd]

    @staticmethod
    def _mov64(rd, v):
        out = [0xD2800000 | ((v & 0xFFFF) << 5) | rd]
        for hw in (1, 2, 3):
            out.append(0xF2800000 | (hw << 21) | (((v >> (16 * hw)) & 0xFFFF) << 5) | rd)
        return out

    def fn_ret_w0(self, v):
        return self.code(self._mov32(0, v) + [0xD65F03C0])

    def fn_ret_s0(self, v):
        return self.code(self._mov32(9, fbits(v)) + [0x1E270120, 0xD65F03C0])  # fmov s0, w9

    def fn_store_x8(self, ptr):
        return self.code(self._mov64(9, ptr) + [0xF9000109, 0xD65F03C0])  # str x9, [x8]

    def w16(self, a, v):
        self.mu.mem_write(a, struct.pack("<H", v & 0xFFFF))

    def r8(self, a):
        return self.mu.mem_read(a, 1)[0]

    def r64(self, a):
        return struct.unpack("<Q", self.mu.mem_read(a, 8))[0]


# ---------------------------------------------------------------- 파라미터 체인(가짜 객체)
def make_param(e, size, fields, flags, parent=None):
    """fields = {off: (kind, value)}, flags = {flag_off: 0/1}. parent = 다른 make_param 결과."""
    obj = e.alloc(0x200)
    isa = getattr(e, "_isa", None) or e.fn_ret_w0(1)
    e._isa = isa
    vt = e.alloc(0x100)
    e.w64(vt, isa)
    e.w64(obj, vt)
    for off, (k, v) in fields.items():
        if k == "i":
            e.w32(obj + off, v)
        else:
            e.wf(obj + off, v)
    for off, v in flags.items():
        e.w8(obj + off, v)
    if parent is not None:
        h = e.alloc(0x20)
        e.w64(h, parent)
        e.w32(h + 0xC, 7)
        e.w64(obj + 0x10, 1)  # 부모 있음 표시(널 아님)
        e.w64(obj + 0x18, h)
        e.w32(obj + 0x20, 7)
    return obj


def resolve(chain, field_off, flag_off):
    """재구현: 자식부터 '설정됨' 플래그가 선 첫 노드의 값, 없으면 마지막 노드 값 ($parent 체인)."""
    for node in chain:
        if node["flags"].get(flag_off, 0):
            return node["fields"][field_off][1]
    return chain[-1]["fields"][field_off][1]


def build_chain(e, nodes):
    """nodes: 자식→부모 순서. 각 {'fields':…, 'flags':…}. 원본 객체 포인터(자식) 반환."""
    parent = None
    for n in reversed(nodes):
        parent = make_param(e, 0x200, n["fields"], n["flags"], parent)
    return parent


# ---------------------------------------------------------------- A. 데미지
def ref_shooter_damage(age, vmax, vmin, start, end):
    denom = end - start
    if denom == 0:
        denom = 1
    t = f32(age - start + 1) / f32(denom)
    t1 = min(t, f32(1.0))
    if t < f32(0.0):
        t1 = f32(0.0)
    d = (f32(vmin) - f32(vmax)) * t1 + f32(vmax)
    return int(np.trunc(d))


DMG_F = {"max": (0x38, 0x40), "min": (0x3C, 0x41), "start": (0x34, 0x42), "end": (0x30, 0x43)}


def test_damage(rng):
    e = Emu([F_DMG])
    bad = n = 0
    # 실제 데이터 표본(스플래시슈터 360/180/8/39 등) + 무작위 + 경계, 부모 체인 1~3단
    samples = [(360, 180, 8, 39), (620, 350, 9, 25), (280, 140, 4, 20), (1250, 1250, -1, 99), (180, 120, 8, 24),
               (100, 200, 5, 5), (360, 180, 39, 8)]
    for _ in range(60):
        samples.append((rng.randint(0, 3000), rng.randint(0, 3000), rng.randint(-5, 40), rng.randint(-5, 60)))
    for vmax, vmin, st, en in samples:
        depth = rng.randint(1, 3)
        nodes = []
        for d in range(depth):
            fields = {o: ("i", rng.randint(-50, 3000)) for o, _ in DMG_F.values()}
            flags = {fo: rng.randint(0, 1) for _, fo in DMG_F.values()}
            nodes.append({"fields": fields, "flags": flags})
        # 목표 값을 체인 어딘가에 심는다: 각 필드가 해석될 노드에 값을 쓴다
        want = {"max": vmax, "min": vmin, "start": st, "end": en}
        for k, (fo, flo) in DMG_F.items():
            idx = next((i for i, nd in enumerate(nodes) if nd["flags"][flo]), len(nodes) - 1)
            nodes[idx]["fields"][fo] = ("i", want[k])
        p = build_chain(e, nodes)
        h = e.alloc(0x20)
        e.w64(h, p)
        e.w32(h + 0xC, 3)
        info = e.alloc(0x200)
        e.w64(info + 0x110, h)
        e.w32(info + 0x118, 3)
        bullet = e.alloc(0x1300)
        e.w64(bullet + 0x108, info)
        r = [resolve(nodes, fo, flo) for fo, flo in DMG_F.values()]
        for age in list(range(-1, 45)) + [100, 1000]:
            e.w32(bullet + 0x134, age)
            e.call(F_DMG, [bullet])
            got = e.mu.reg_read(UC_ARM64_REG_X0) & 0xFFFFFFFF
            got = got - (1 << 32) if got & 0x80000000 else got
            exp = ref_shooter_damage(age, *r)
            n += 1
            if got != exp:
                bad += 1
                if bad < 5:
                    log(f"  불일치 age {age} param {r}: 원본 {got} 재구현 {exp}")
    log(f"A 데미지 0x71017506d0: {n}건 (표본 {len(samples)}종 × age −1~44,100,1000, $parent 1~3단) 불일치 {bad}")
    return bad


# ---------------------------------------------------------------- B. 반경
RAD_FIELD = {"init": (0x44, 0x50), "end": (0x38, 0x51), "chg": (0x30, 0x52)}
RAD_PLAYER = {"init": (0x48, 0x4C), "end": (0x3C, 0x4D), "chg": (0x34, 0x4E)}


def ref_radius(age, init, end, chg):
    if chg == 0:
        return f32(end)
    t = f32(age) / f32(chg)
    t1 = min(t, f32(1.0))
    if t < f32(0.0):
        t1 = f32(0.0)
    v = f32(init) + t1 * (f32(end) - f32(init))
    return max(v, f32(bitsf(0x3CA3D70A)))


def test_radius(rng):
    e = Emu([F_RAD_FIELD, F_RAD_PLAYER])
    bad = n = 0
    for trial in range(80):
        nodes = []
        for d in range(rng.randint(1, 3)):
            fields, flags = {}, {}
            for tab in (RAD_FIELD, RAD_PLAYER):
                for k, (fo, flo) in tab.items():
                    if k == "chg":
                        fields[fo] = ("i", rng.choice([0, 0, 1, 2, 3, 5, 8, 12, -3, rng.randint(-10, 40)]))
                    else:
                        fields[fo] = ("f", float(f32(rng.choice([0.2, 0.15, 0.0, 0.01, rng.uniform(-0.5, 2.0)]))))
                    flags[flo] = rng.randint(0, 1)
            nodes.append({"fields": fields, "flags": flags})
        p = build_chain(e, nodes)
        for fn, tab in ((F_RAD_FIELD, RAD_FIELD), (F_RAD_PLAYER, RAD_PLAYER)):
            r = [resolve(nodes, fo, flo) for fo, flo in (tab["init"], tab["end"], tab["chg"])]
            for age in list(range(-2, 30)) + [100]:
                e.call(fn, [p, age & 0xFFFFFFFF])
                got = e.mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF
                exp = fbits(ref_radius(age, *r))
                n += 1
                if got != exp:
                    bad += 1
                    if bad < 5:
                        log(f"  불일치 {fn:#x} age {age} {r}: 원본 {bitsf(got)} 재구현 {bitsf(exp)}")
    log(f"B 반경 0x71018a6b68/0x71018a6fe4: {n}건 (체인 1~3단, ChangeFrame 0/음수/양수, age −2~29·100) 불일치 {bad}")
    return bad


# ---------------------------------------------------------------- C. 넉백
def _norm_scale(v, s):
    return [f32(x) * f32(s) for x in v]


def ref_knockback(up, dmg, vel, p):
    lo, a, hi, b, blend = p
    x, y, z = (f32(c) for c in vel)
    ln = f32(math.sqrt(float(x * x + y * y + z * z)))
    ln = f32(np.sqrt(f32(f32(x * x) + f32(y * y)) + f32(z * z)))
    if ln > 0:
        inv = f32(1.0) / ln
        x, y, z = x * inv, y * inv, z * inv
    t = f32(1.0)
    if b - a != 0:
        t = f32(dmg - a) / f32(b - a)
    t1 = min(t, f32(1.0))
    if t < 0:
        t1 = f32(0.0)
    mag = f32(lo) + (f32(hi) - f32(lo)) * t1
    ln = f32(np.sqrt(f32(f32(x * x) + f32(y * y)) + f32(z * z)))
    if ln > 0:
        s = mag / ln
        x, y, z = x * s, y * s, z * s
    ux, uy, uz = (f32(c) for c in up)
    if ux == 0 and uy == 0 and uz == 0:
        return [x, y, z]
    d = f32(f32(ux * x) + f32(uy * y)) + f32(uz * z)
    if d == 0:
        return [x, y, z]
    x, y, z = x - ux * d, y - uy * d, z - uz * d
    if not (f32(blend) > 0):
        return [x, y, z]
    ln = f32(np.sqrt(f32(f32(x * x) + f32(y * y)) + f32(z * z)))
    if f32(blend) == f32(1.0):
        if not (ln > 0):
            return [x, y, z]
        s = mag / ln
    else:
        if not (ln > 0):
            return [x, y, z]
        s = (ln + f32(blend) * (mag - ln)) / ln
    return [x * s, y * s, z * s]


def test_knockback(rng):
    e = Emu([F_KB])
    bad = n = 0
    pbuf = e.alloc(0x40)
    vbuf = e.alloc(0x40)
    shooter = (95.0, 300, 280.0, 2000, 0.0)
    cases = []
    for dmg in (0, 299, 300, 360, 1000, 1150, 2000, 2500, 99998):
        cases.append(((0.0, 1.0, 0.0), dmg, (0.3, -0.2, 1.1), shooter))
    for _ in range(400):
        up = rng.choice([(0.0, 1.0, 0.0), (0.0, 0.0, 0.0), tuple(rng.uniform(-1, 1) for _ in range(3))])
        vel = rng.choice([(0.0, 0.0, 0.0), tuple(rng.uniform(-3, 3) for _ in range(3))])
        a = rng.randint(-100, 1500)
        b = rng.choice([a, a + rng.randint(1, 3000)])
        p = (rng.uniform(0, 300), a, rng.uniform(0, 400), b, rng.choice([0.0, 1.0, 0.5, rng.uniform(0, 2)]))
        cases.append((up, rng.randint(-100, 4000), vel, p))
    for up, dmg, vel, p in cases:
        lo, a, hi, b, blend = p
        e.wf(pbuf, lo); e.w32(pbuf + 4, a); e.wf(pbuf + 8, hi); e.w32(pbuf + 0xC, b); e.wf(pbuf + 0x10, blend)
        for i, c in enumerate(vel):
            e.wf(vbuf + 4 * i, c)
        mu = e.mu
        for reg, v in zip((UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2), up):
            mu.reg_write(reg, fbits(v))
        e.call(F_KB, [0, dmg & 0xFFFFFFFF, vbuf, pbuf])
        got = [mu.reg_read(r) & 0xFFFFFFFF for r in (UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2)]
        exp = [fbits(v) for v in ref_knockback(up, dmg, vel, p)]
        n += 1
        if got != exp:
            bad += 1
            if bad < 5:
                log(f"  불일치 up {up} dmg {dmg} vel {vel} p {p}: 원본 {[bitsf(g) for g in got]} 재구현 {[bitsf(x) for x in exp]}")
    # 대표값(슈터 파라미터, up=(0,1,0), vel=(0,0,1)) 크기
    reps = []
    for dmg in (360, 1150, 2500):
        e.wf(pbuf, 95.0); e.w32(pbuf + 4, 300); e.wf(pbuf + 8, 280.0); e.w32(pbuf + 0xC, 2000); e.wf(pbuf + 0x10, 0.0)
        for i, c in enumerate((0.0, 0.0, 1.0)):
            e.wf(vbuf + 4 * i, c)
        for reg, v in zip((UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2), (0.0, 1.0, 0.0)):
            e.mu.reg_write(reg, fbits(v))
        e.call(F_KB, [0, dmg, vbuf, pbuf])
        reps.append((dmg, round(bitsf(e.mu.reg_read(UC_ARM64_REG_S2)), 4)))
    log(f"C 넉백 0x7101e66c4c: {n}건 (슈터 파라미터 9 + 무작위 400: up 0/수평/임의, 속도 0 포함, blend 0/1/0.5/임의) 불일치 {bad}; 슈터 크기 {reps}")
    return bad


# ---------------------------------------------------------------- D. 크리티컬 링
def ref_crit(ring, target, pidx, key, dmg, need, needcnt):
    if pidx > 9 or key == -1:
        return False
    r = ring[pidx]
    slot = None
    for i in range(8):
        if r[i][1] == -1:
            slot = i
            break
    if slot is None:
        best = 0
        for i in range(1, 8):
            if (r[i][1] & 0xFFFFFFFF) < (r[best][1] & 0xFFFFFFFF):
                best = i
        slot = best
    r[slot] = [target, key, dmg]
    if target == 0:
        return need <= 0 and needcnt <= 0
    s = c = 0
    for t, k, d in r:
        if k == key and t == target:
            s += d
            c += 1
    return need <= s and needcnt <= c


def test_crit(rng):
    e = Emu([F_CRIT])
    mgr = e.alloc(0x1000)
    ring = [[[0, -1, 0] for _ in range(8)] for _ in range(10)]
    for p in range(10):
        for i in range(8):
            e.w32(mgr + 0x3C0 + p * 0x80 + i * 0x10 + 8, -1)
    targets = [e.alloc(0x100) for _ in range(3)]
    # 접촉 구조: contact+0x10 → C, C+0x38 → holder(+0 → pair, +8/+9 바이트), pair+0x69 비트4, +0x70/+0x78 액터
    contact = e.alloc(0x40)
    C = e.alloc(0x80)
    holder = e.alloc(0x20)
    pair = e.alloc(0x100)
    X = e.alloc(0x100)
    e.w64(contact + 0x10, C)
    e.w64(C + 0x38, holder)
    e.w64(holder, pair)
    e.w64(pair, X)
    bad = n = 0
    keys = [100, 101, 102, 103]
    for step in range(3000):
        tgt = rng.choice(targets + [0])
        sel = rng.randint(0, 3)  # 쌍 방향 바이트 조합
        b8, b9, bit = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1)][sel]
        e.w8(holder + 8, b8); e.w8(holder + 9, b9); e.w8(pair + 8, bit)
        e.w8(X + 0x69, rng.choice([0, 0x10]))
        # 원본 선택 규칙에 맞춰 대상이 놓일 칸: 같음&bit0=1 또는 다름&bit0=0 → +0x70(단 +0x69 비트4면 0), 그 밖 +0x78
        use70 = (b8 == b9 and bit == 1) or (b8 != b9 and bit == 0)
        e.w64(X + 0x70, tgt); e.w64(X + 0x78, tgt)
        flag69 = e.r8(X + 0x69)
        eff = (0 if (flag69 & 0x10) else tgt) if use70 else tgt
        pidx = rng.choice([0, 1, 2, 9, 10])
        key = rng.choice(keys + [-1])
        if rng.random() < 0.02:
            keys = [k + 4 for k in keys]
        dmg = rng.randint(0, 700)
        cnt = rng.choice([1, 1, 2, 3])
        e.call(F_CRIT, [mgr, contact, pidx, key & 0xFFFFFFFF, dmg, 1000, cnt])
        got = e.mu.reg_read(UC_ARM64_REG_X0) & 1
        exp = int(ref_crit(ring, eff, pidx, key, dmg, 1000, cnt))
        n += 1
        if got != exp:
            bad += 1
            if bad < 5:
                log(f"  불일치 step {step}: 원본 {got} 재구현 {exp}")
        # 링 메모리도 비교
        if pidx <= 9 and key != -1:
            for i in range(8):
                base = mgr + 0x3C0 + pidx * 0x80 + i * 0x10
                m = [e.r64(base), e.r32(base + 8), e.r32(base + 12)]
                if m != ring[pidx][i]:
                    bad += 1
                    if bad < 5:
                        log(f"  링 불일치 step {step} p{pidx} 칸{i}: 원본 {m} 재구현 {ring[pidx][i]}")
                    ring[pidx][i] = m
    log(f"D 크리티컬 누적 0x71016e6260: {n}회 연속 호출(대상 3+널, 쌍 방향 4종, 플레이어 0/1/2/9/10, key −1·증가, 필요 개수 1~3) 결과·링 불일치 {bad}")
    return bad


# ---------------------------------------------------------------- E. 수신 결과
class Hist:
    def __init__(self, age, h, dmg, key):
        self.age, self.h, self.dmg, self.key = f32(age), h, dmg, key


EPS = f32(bitsf(0x34000000))
STATS = {}


def ref_result(Rv, info, S, rate, frame, hist):
    """web/docs/combat/damage_hit.md §6.4, §6.4.1 의사코드 재구현. hist = 최신이 앞인 리스트."""
    def reset(r):
        info["dmg"] = 0
        info["kb"] = [f32(0), f32(0), f32(0)]
        return r
    m = Rv["m1e8"]
    if m == 2:
        ok = S["v30"]
    elif m == 1:
        ok = S["v30"] if S["v38"] else Rv["f1e4"]
    else:
        ok = True
    if not ok:
        return reset(Rv["r1d0"])
    t = info["team"]
    if (Rv["tmode"] == 1 and Rv["team"] not in (-1, 3) and Rv["team"] == t) or (Rv["mask"] >> (t & 31) & 1):
        return reset(Rv["r1d4"])
    res = 7 if (Rv["tmode"] == 2 and Rv["team"] not in (-1, 3) and Rv["team"] == t) else 6
    if Rv["exOn"]:
        info["dmg"] = int(np.trunc((f32(Rv["exRate"]) + f32(1e-5)) * f32(info["dmg"])))
        if Rv["exRes"] != 8:
            res = Rv["exRes"]
    info["dmg"] = int(np.trunc((f32(rate) + f32(1e-5)) * f32(info["dmg"])))
    if info["dmg"] == 0:
        return reset(Rv["exRes"] if (Rv["exOn"] and Rv["exRes"] != 6) else Rv["r1d8"])
    if not math.isnan(Rv["kb"]):
        info["kb"] = [f32(Rv["kb"]) * k for k in info["kb"]]
    mode = S["mode"]
    h = S["h"]  # (id) 또는 None
    hid = None if h is None else h["id"]
    reject = False

    def same(e_):
        return e_.h is not None and e_.h["id"] != -1 and h is not None and e_.h is h and hid != -1

    def mode1():
        if h is None or hid == -1:
            return False
        return any(same(e_) and e_.age < f32(S["v28"]) for e_ in hist)

    def mode2():
        s = sum(e_.dmg for e_ in hist if same(e_))
        info["dmg"] = max(info["dmg"] - s, 0)
        return info["dmg"] <= 0

    if mode == 1:
        reject = mode1()
    elif mode == 2:
        reject = mode2()
    elif mode == 3:
        s = sum(e_.dmg for e_ in hist if same(e_))
        cap = int(np.trunc((f32(rate) + f32(1e-5)) * f32(S["v40"])))
        if Rv["exOn"]:
            cap = int(np.trunc((f32(Rv["exRate"]) + f32(1e-5)) * f32(cap)))
        if cap <= info["dmg"] + s:
            info["dmg"] = max(cap - s, 0)
        reject = info["dmg"] < 1
    elif mode in (4, 5):
        for e_ in hist:
            if -EPS <= e_.age <= EPS:
                if e_.key < 0:
                    if h is not None and same(e_):
                        reject = True
                        break
                elif e_.key == S["v48"]:
                    reject = True
                    break
    elif mode == 6:
        if mode1():
            reject = mode2()
    if reject:
        STATS["reject_mode%d" % mode] = STATS.get("reject_mode%d" % mode, 0) + 1
        r = Rv["r1dc"] if res > 4 else res
        return reset(r)
    if Rv["twOn"] and not info["a8"]:
        u = abs(Rv["tw204"])
        cur = max(frame, 0)
        if u == cur:
            Rv["tw204"] = -cur
            mult = Rv["tw200"]
        else:
            if Rv["tw204"] < 0:
                Rv["tw204"] = Rv["tw200"] - Rv["tw204"]
            if Rv["tw204"] <= cur:
                Rv["tw204"] = -cur
                mult = Rv["tw200"]
            else:
                mult = 0
        info["dmg"] = int(np.trunc(f32(mult) * f32(info["dmg"])))
        STATS["tw_mult%d" % mult] = STATS.get("tw_mult%d" % mult, 0) + 1
        if mult == 0:
            info["kb"] = [f32(0), f32(0), f32(0)]
    if info["dmg"] > 99999:
        info["dmg"] = 99998
    if h is None or hid == -1:
        return res
    key = S["v48"] if mode == 5 else -1
    if mode == 5:
        for e_ in list(hist):
            if e_.key >= 0 and e_.key == S["v48"]:
                hist.remove(e_)
                break
    if len(hist) >= Rv["max"]:
        hist.pop()  # 가장 오래된(끝)
    hist.insert(0, Hist(0.0, h, info["dmg"], key))
    return res


def ref_age(hist, dt):
    out = []
    for e_ in hist:
        a = e_.age + f32(dt)
        if a < f32(15.0):
            e_.age = a
            out.append(e_)
    hist[:] = out


class RecvWorld:
    def __init__(self, e, nfree=80):
        self.e = e
        self.R = e.alloc(0x400)
        R_ = self.R
        e.w64(R_ + 0x188, R_ + 0x188)
        e.w64(R_ + 0x190, R_ + 0x188)
        e.w32(R_ + 0x198, 0)
        free = 0
        for _ in range(nfree):
            ent = e.alloc(0x30)
            e.w64(ent, free)
            free = ent
        e.w64(R_ + 0x1A0, free)
        self.col = e.alloc(0x80)
        e.mu.mem_write(self.col, b"Default\0")
        e.w64(R_ + 0x128, self.col)
        e.w32(R_ + 0x130, 0x40)
        self.frame_obj = e.alloc(0x200)
        e.w64(0x710580E758, self.frame_obj)  # *0x7105790610 이 가리키는 전역(시간 창 카운터 +0x148)
        self.handles = []
        for i in range(3):
            hh = e.alloc(0x40)
            e.w32(hh, 1)
            e.w32(hh + 0x28, [5, 6, -1][i])
            self.handles.append({"addr": hh, "id": [5, 6, -1][i]})
        self.info = e.alloc(0x100)
        self.row = e.alloc(0x80)
        e.mu.mem_write(self.row, b"Shooter\0")
        self.sender = e.alloc(0x40)
        self.svt = e.alloc(0x80)
        e.w64(self.sender, self.svt)

    def set_recv(self, Rv):
        e, R_ = self.e, self.R
        e.w32(R_ + 0x1E8, Rv["m1e8"]); e.w8(R_ + 0x1E4, Rv["f1e4"])
        e.w32(R_ + 0x1B8, Rv["tmode"]); e.w32(R_ + 0x1BC, Rv["team"]); e.w8(R_ + 0x20C, Rv["mask"])
        e.w8(R_ + 0x1CC, Rv["exOn"]); e.wf(R_ + 0x1C4, Rv["exRate"]); e.w32(R_ + 0x1C8, Rv["exRes"])
        e.w32(R_ + 0x1D0, Rv["r1d0"]); e.w32(R_ + 0x1D4, Rv["r1d4"]); e.w32(R_ + 0x1D8, Rv["r1d8"])
        e.w32(R_ + 0x1DC, Rv["r1dc"]); e.wf(R_ + 0x1E0, Rv["kb"]); e.w32(R_ + 0x1B0, Rv["max"])
        e.w8(R_ + 0x1FC, Rv["twOn"]); e.w32(R_ + 0x200, Rv["tw200"]); e.w32(R_ + 0x204, Rv["tw204"])
        e.w8(R_ + 0x1ED, 1); e.w8(R_ + 0x1EC, 1)

    def set_sender(self, S):
        e = self.e
        h = S["h"]
        slots = {0x18: e.fn_store_x8(h["addr"] if h else 0), 0x20: e.fn_ret_w0(S["mode"]),
                 0x28: e.fn_ret_s0(S["v28"]), 0x30: e.fn_ret_w0(S["v30"]), 0x38: e.fn_ret_w0(S["v38"]),
                 0x40: e.fn_ret_w0(S["v40"]), 0x48: e.fn_ret_w0(S["v48"])}
        for off, fn in slots.items():
            e.w64(self.svt + off, fn)

    def set_info(self, info):
        e, I = self.e, self.info
        e.mu.mem_write(I, b"\0" * 0x100)
        e.w32(I, info["dmg"]); e.w32(I + 4, info["team"]); e.w32(I + 8, 0xC0000001 - (1 << 32))
        for i, k in enumerate(info["kb"]):
            e.wf(I + 0xC + 4 * i, k)
        e.w64(I + 0x58, self.row); e.w32(I + 0x60, 0x40)
        e.w8(I + 0xA8, info["a8"]); e.w8(I + 0xA9, 0)

    def read_hist(self):
        e, R_ = self.e, self.R
        out = []
        node = e.r64(R_ + 0x190)
        guard = 0
        while node != R_ + 0x188 and guard < 200:
            ent = node - 0x18
            h = e.r64(ent + 8)
            out.append((round(e.rf(ent), 7), h, e.r32(ent + 0x10) & 0xFFFFFFFF, e.r32(ent + 0x14) & 0xFFFFFFFF))
            node = e.r64(node + 8)
            guard += 1
        return out


def rand_recv(rng):
    return {"m1e8": rng.choice([2, 2, 2, 1, 0]), "f1e4": rng.randint(0, 1), "tmode": rng.choice([1, 1, 2, 0]),
            "team": rng.choice([0, 1, 2, 3, -1]), "mask": rng.choice([0, 0, 0, 1, 2, 4, 5]),
            "exOn": rng.choice([0, 0, 0, 1]), "exRate": float(f32(rng.choice([0.0, 0.5, 1.0, 2.0, 0.344]))),
            "exRes": rng.choice([8, 8, 4, 5, 6, 7]), "r1d0": 0, "r1d4": rng.choice([0, 1]), "r1d8": rng.choice([0, 3]),
            "r1dc": rng.choice([0, 2]), "kb": rng.choice([float("nan"), float("nan"), 0.5, 2.0]),
            "max": rng.choice([64, 64, 3]), "twOn": rng.choice([0, 0, 1]), "tw200": rng.choice([1, 8, 0]),
            "tw204": 0}


def test_result(rng):
    e = Emu([F_RESULT, F_MODE2, F_AGE, F_INFOCOPY])
    e.special[F_OBJUP] = lambda mu: None
    w = RecvWorld(e)
    bad = n = 0
    modes_seen = {}
    for scen in range(60):
        Rv = rand_recv(rng)
        w = RecvWorld(e)
        w.set_recv(Rv)
        hist = []
        frame = rng.randint(0, 50)
        for step in range(40):
            S = {"mode": rng.choice([0, 1, 2, 3, 4, 5, 6]), "h": rng.choice(w.handles + [None]),
                 "v28": float(f32(rng.choice([0.05, 0.2, 1.0, 0.0]))), "v30": rng.choice([1, 1, 0]),
                 "v38": rng.randint(0, 1), "v40": rng.choice([300, 1000, 50]), "v48": rng.choice([0, 1, 2, -1])}
            rate = rng.choice([1.0, 1.0, 0.7, 0.344, 3.0, 0.0])
            info = {"dmg": rng.choice([360, 180, 843, 0, 1, 200000, rng.randint(0, 2000)]),
                    "team": rng.choice([0, 1, 2, 3]), "kb": [f32(rng.uniform(-200, 200)) for _ in range(3)],
                    "a8": rng.choice([1, 1, 0])}
            w.set_sender(S)
            w.set_info(info)
            e.rate = rate
            e.w32(w.frame_obj + 0x148, frame)
            e.call(F_RESULT, [w.R, w.info, w.sender])
            got_res = e.mu.reg_read(UC_ARM64_REG_X0) & 0xFFFFFFFF
            got_dmg = e.r32(w.info)
            got_kb = [struct.unpack("<I", e.mu.mem_read(w.info + 0xC + 4 * i, 4))[0] for i in range(3)]
            got_tw = e.r32(w.R + 0x204) & 0xFFFFFFFF
            got_hist = w.read_hist()
            Rv_ref = Rv  # tw204 갱신 공유
            exp_res = ref_result(Rv_ref, info, S, rate, frame, hist)
            exp_hist = [(round(float(h_.age), 7), h_.h["addr"], h_.dmg & 0xFFFFFFFF, h_.key & 0xFFFFFFFF) for h_ in hist]
            ok = (got_res == exp_res and got_dmg == (info["dmg"] & 0xFFFFFFFF)
                  and got_kb == [fbits(k) for k in info["kb"]] and got_hist == exp_hist
                  and got_tw == (Rv["tw204"] & 0xFFFFFFFF))
            n += 1
            modes_seen[S["mode"]] = modes_seen.get(S["mode"], 0) + 1
            if not ok:
                bad += 1
                if bad < 6:
                    log(f"  불일치 scen {scen} step {step} mode {S['mode']}: 원본 res {got_res} dmg {got_dmg} "
                        f"hist {got_hist[:3]} tw {got_tw} / 재구현 res {exp_res} dmg {info['dmg']} hist {exp_hist[:3]} tw {Rv['tw204']}")
                # 재동기화: 원본 상태를 재구현 쪽에 반영하지 않고 다음 시나리오로
                break
            # 나이 증가(0x7101a86dc8) — 프레임 사이 1/60 초 또는 큰 값
            if rng.random() < 0.6:
                dt = rng.choice([1 / 60, 1 / 60, 0.5, 6.0])
                e.mu.reg_write(UC_ARM64_REG_S0, fbits(dt))
                e.call(F_AGE, [w.R])
                ref_age(hist, dt)
                frame += 1
                gh = w.read_hist()
                eh = [(round(float(h_.age), 7), h_.h["addr"], h_.dmg & 0xFFFFFFFF, h_.key & 0xFFFFFFFF) for h_ in hist]
                n += 1
                if gh != eh:
                    bad += 1
                    if bad < 6:
                        log(f"  나이 불일치 scen {scen}: 원본 {gh[:3]} 재구현 {eh[:3]}")
                    break
    log(f"E 수신 결과 0x7101a86ec0(+0x7101a87edc) · 이력 나이 0x7101a86dc8: {n}건(시나리오 60 × 최대 40히트, 모드별 {dict(sorted(modes_seen.items()))}; 재구현 쪽 거부·시간창 경로 {dict(sorted(STATS.items()))}) 불일치 {bad}")
    return bad


# ---------------------------------------------------------------- F. 히트마커 플래그
def ref_hm_flags(Rv):
    if Rv["m208"] == 2:
        return [0, 0, 0, 0]
    if Rv["m208"] == 1:
        return [1, 1, 1, 1]
    if Rv["m208"] != 0:
        return None  # 변경 없음
    eff = (Rv["exRes"] > 4) if Rv["exOn"] else True
    out = []
    for t in range(4):
        f = eff and not (Rv["mask"] >> t & 1)
        if Rv["tmode"] == 1 and Rv["team"] not in (-1, 3) and Rv["team"] == t:
            f = False
        out.append(int(f))
    return out


def ref_hm_predict(flags, team):
    if team == -1:
        return 1
    f = flags[team] if 0 <= team < 4 else flags[0]
    return 2 if f else 1


def test_hitmarker(rng):
    e = Emu([F_HM_FLAGS, F_HM_PREDICT])
    R_ = e.alloc(0x300)
    tb = e.alloc(8)
    bad = n = 0
    for _ in range(1500):
        Rv = {"m208": rng.choice([0, 0, 0, 1, 2, 3]), "tmode": rng.choice([1, 1, 2, 0]), "team": rng.choice([0, 1, 2, 3, -1]),
              "mask": rng.randint(0, 15), "exOn": rng.randint(0, 1), "exRes": rng.choice([0, 1, 4, 5, 6, 7, 8])}
        before = [rng.randint(0, 1) for _ in range(4)]
        e.mu.mem_write(R_ + 0x1C0, bytes(before))
        e.w32(R_ + 0x208, Rv["m208"]); e.w32(R_ + 0x1B8, Rv["tmode"]); e.w32(R_ + 0x1BC, Rv["team"])
        e.w8(R_ + 0x20C, Rv["mask"]); e.w8(R_ + 0x1CC, Rv["exOn"]); e.w32(R_ + 0x1C8, Rv["exRes"])
        e.call(F_HM_FLAGS, [R_])
        got = list(e.mu.mem_read(R_ + 0x1C0, 4))
        exp = ref_hm_flags(Rv) or before
        n += 1
        if got != exp:
            bad += 1
            if bad < 5:
                log(f"  플래그 불일치 {Rv}: 원본 {got} 재구현 {exp}")
        for team in (-1, 0, 1, 2, 3, 4, 7):
            e.w32(tb, team)
            e.call(F_HM_PREDICT, [R_, tb])
            g = e.mu.reg_read(UC_ARM64_REG_X0) & 0xFFFFFFFF
            x = ref_hm_predict(got, team)
            n += 1
            if g != x:
                bad += 1
                if bad < 5:
                    log(f"  예측 불일치 team {team} flags {got}: 원본 {g} 재구현 {x}")
    log(f"F 히트마커 플래그 0x7101a86be8 · 예측 0x7101a87e8c: {n}건(모드 0/1/2/3, 팀 모드 0/1/2, 팀 −1~3, 무시 마스크 0~15, 추가 결과 on/off) 불일치 {bad}")
    return bad


def main():
    rng = random.Random(20261003)
    bad = 0
    log("[r5 combat] 피격·판정 원본 실행 대조 (unicorn, 원본 함수 무수정)")
    for t in (test_damage, test_radius, test_knockback, test_crit, test_result, test_hitmarker):
        bad += t(rng)
    log(f"합계 불일치 {bad}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
