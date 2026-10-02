"""r6 player: 원본 생성자로 플레이어 본체를 만들고 프레임 슬롯(18 메인 계산, 19 후처리)을 실행하는 월드.

- PlayerBehavior 슬롯36 0x710245717c(behavior, arg, 0): 본체 0xac80 B 생성 + 본체 vt 슬롯2 0x710234b580 컴포넌트 76개 생성(원본 실행).
- 본체 vt 슬롯3 0x710234f3ec(본체, 액터): 액터 쪽 객체 연결(+0xa8c8 = 액터+0x778 상태기계, +0xa8f0 = 액터+0x770 ...).
  액터는 엔진 객체라 만들지 않고 0으로 채운 가짜 액터(컴포넌트 배열 +0x208, 개수 +0x200)를 넘긴다.
  상태기계(SM)도 가짜: SM+0x20 = behavior, SM+0xc8 = 상태 번호(인자), SM+0xd0 = -1.  ← 스텁
- 컨트롤러: 0x7103d55638(컨트롤러 조회)을 가로채 가짜 컨트롤러를 돌려준다(+0x8 이번 눌림, +0x114 누름, +0x120/+0x124 왼쪽 스틱). ← 스텁
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_player_uc import PUC  # noqa: E402
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_PC, UC_ARM64_REG_LR

CTRL_GET = 0x7103D55638
SLOT18 = 0x7102353AD0
SLOT19 = 0x7102353D24
SLOT15 = 0x7102353A18
SLOT16 = 0x7102353AA0


class World:
    def __init__(self, state=0x56, fake_ctrl=True, local=True, slot9=True):
        u = self.u = PUC()
        self.beh = u.alloc(0x1000)
        self.arg = u.alloc(0x1000)
        u.w32(self.arg + 0x14, 0x10)  # 컴포넌트 목록(sead OffsetList) 노드 오프셋: 공통 기반의 +0x10 (팩토리 memset 시작) [판독]
        r = u.call(0x710245717C, self.beh, self.arg, 0, count=50_000_000)
        assert r is None, r
        self.body = u.rq(self.beh + 0x108)
        A = self.actor = u.alloc(0x1000)
        comps = u.alloc(0x60 * 8)
        self.fake_comps = []
        self.fakes = {}
        for i in range(0x60):
            c = self.fake_obj(f"actor.comp[{i:#x}]")
            u.wq(c + 0x18, self.fake_obj(f"actor.comp[{i:#x}]+0x18"))
            u.wq(c + 0x20, self.fake_obj(f"actor.comp[{i:#x}]+0x20"))
            u.wq(comps + 8 * i, c)
            self.fake_comps.append(c)
        u.wq(A + 0x208, comps)
        u.w32(A + 0x200, 0x60)
        self.sm = u.alloc(0x400)
        self.a_matrix = A
        u.wq(A + 0x778, self.sm)
        self.a768 = u.alloc(0x2000)
        self.a770 = u.alloc(0x2000)
        u.wq(A + 0x768, self.a768)
        u.wq(A + 0x770, self.a770)
        u.wq(self.body + 8, A)  # 본체+8 = 액터(가짜)
        r = u.call(0x710234F3EC, self.body, A)
        assert r is None, r
        # 컴포넌트 vt 슬롯7(init) 을 0 컨텍스트로 원본 실행(SideStep·Pipeline 등 상태기계 +0x30 이 0 으로 시작).
        ctx = u.alloc(0x400)
        self.init7 = {}
        for off in range(0xA650, 0xA8C8, 8):
            c = u.rq(self.body + off)
            if c:
                self.init7[off] = u.call(u.rq(u.rq(c) + 0x38), c, ctx, count=2_000_000)
        # 컴포넌트 vt 슬롯13(초기화: InputSender 0x7102631954 는 우선순위 목록 +0x30..+0x40 = 4, +0x44..+0x50 = -1) 원본 실행
        self.init13 = {}
        for off in range(0xA650, 0xA8C8, 8):
            c = u.rq(self.body + off)
            if c:
                self.init13[off] = u.call(u.rq(u.rq(c) + 0x68), c, count=2_000_000)
        u.wq(self.sm + 0x20, self.beh)
        u.w32(self.sm + 0xC8, state)
        u.w32(self.sm + 0xCC, state)
        u.w32(self.sm + 0xD0, 0xFFFFFFFF)
        pc = self.pc = u.rq(self.body + 0xA690)
        for off in range(0xE340, 0xE3C0, 8):  # PlayerCollision 의 Phive 엔진 객체 칸(액터 쪽에서 채워짐) ← 가짜
            if u.rq(pc + off) == 0:
                u.wq(pc + off, self.fake_obj(f"PC+{off:#x}"))
        # 컴포넌트가 가리키는 엔진 객체 칸(액터 쪽에서 채워짐) ← 가짜. (컴포넌트 오프셋, 칸 오프셋)
        for coff, foff in ((0xA878, 0x1968),):
            c = u.rq(self.body + coff)
            if u.rq(c + foff) == 0:
                u.wq(c + foff, self.fake_obj(f"[B+{coff:#x}]+{foff:#x}"))
        # 조작 플레이어 판정: [*0x7105801cc0]+0xc70 → +0x18 < 0 이면 메인 계산이 입력 함수 0x710249f494 를 부른다(0x7102477a0c) ← 가짜 싱글턴
        if u.rq(0x7105801CC0) == 0:
            S = self.fake_obj("*0x7105801cc0")
            T = self.fake_obj("*0x7105801cc0+0xc70")
            u.wq(S + 0xC70, T)
            u.w32(T + 0x18, 0xFFFFFFFF)
            u.wq(0x7105801CC0, S)
        if slot9:
            # PlayerBehavior 슬롯9 0x71023539ec → 0x71024719d4 (안에서 리셋 0x710249cb60 호출) — 원본 실행
            self.slot9_result = u.call(0x71023539EC, self.beh, 0, count=30_000_000)
        pd = u.rq(self.body + 0xA8A0)  # spl::PlayerDamage: HP 홀더 PD+0x30 → max +0x78, hp +0x7c (combat/player_life.md §4.1)
        u.w32(pd + 0x78, 1000)
        u.w32(pd + 0x7C, 1000)
        # 그래도 상태기계 현재 상태(+0x38)가 -1 인 컴포넌트: 0x71024c7234 가 '행동 불가'로 판정하므로 0 으로 둔다 ← 가짜
        # (CoopSeq ∈ {0,1,6,9}, MissionTicketGateAction ∈ {0,5}, MissionSeqPinch ∉ {3,4} 이어야 조작 가능)
        self.forced_state0 = []
        for off in (0xA6C8, 0xA6D8, 0xA808, 0xA818, 0xA830, 0xA860, 0xA868):
            c = u.rq(self.body + off)
            if u.rs32(c + 0x38) == -1:
                u.w32(c + 0x38, 0)
                self.forced_state0.append(off)
        if local:
            # InputSender+0x68 = 조작 대상 PlayerBehavior (생성자 0, writer 미탐색) — 없으면 우선순위 목록 갱신(0x71026310c0~)을 건너뜀 ← 설정
            u.wq(u.rq(self.body + 0xA890) + 0x68, self.beh)
            u.w8(self.body + 0x1054, 1)  # 조작 기기 플래그(입력 함수가 InputSender 갱신 0x7102630e6c 를 부르는 조건) ← 설정
        # 게임 프레임 카운터 [*0x710580e758]+0x148 (InputSender 가 버튼 누른 시각으로 기록) ← 가짜 객체, step 마다 +1
        if u.rq(0x710580E758) == 0:
            u.wq(0x710580E758, self.fake_obj("*0x710580e758"))
        self.gframe = u.rq(0x710580E758)
        u.w32(self.gframe + 0x148, 100)
        self.ctrl = u.alloc(0x400)
        if fake_ctrl:
            u.mu.hook_add(UC_HOOK_CODE, self._ctrl_hook, begin=CTRL_GET, end=CTRL_GET)
        self.frame = 0
        self.contact = None
        self.paint = None
        self.ray_hit = None
        u.mu.hook_add(UC_HOOK_CODE, self._ray_hook, begin=0x7103A5F36C, end=0x7103A5F36C)
        for ra in (0x7102483C38, 0x71024AE46C):  # 0x710268b3b8(StepPaint 갱신) 호출 직후
            u.mu.hook_add(UC_HOOK_CODE, self._paint_hook, begin=ra, end=ra)
        u.mu.hook_add(UC_HOOK_CODE, self._contact_hook, begin=0x71024ABD48, end=0x71024ABD48)

    def fake_obj(self, name, size=0x4000, lists=(0xE8,)):
        """0으로 채운 가짜 엔진 객체. lists 오프셋에는 빈 sead 리스트(머리 prev/next = 자기 자신)를 둔다."""
        u = self.u
        o = u.alloc(size)
        for l in lists:
            u.wq(o + l, o + l)
            u.wq(o + l + 8, o + l)
        self.fakes[name] = o
        return o

    def set_contact(self, ground=None, normal=(0.0, 1.0, 0.0), side=None, side_normal=(1.0, 0.0, 0.0), side_point=None):
        """Phive 접촉 결과 대체(가짜 Phive 라 원본 결과가 없음): 0x71024f7410 반환 직후(0x71024abd48) PlayerCollision 필드를 덮어쓴다.
        ground: PC+0xd0(접지), normal: PC+0xac..(지면 법선), side: PC+0xec(측면 접촉), side_normal: PC+0xe0..(측면 법선, +0xe4 = y),
        side_point: PC+0xd4..(측면 접점). None 이면 원본 값 유지. ← 스텁"""
        self.contact = dict(ground=ground, normal=normal, side=side, side_normal=side_normal, side_point=side_point)

    def set_paint(self, kind=None, own=1.0, enemy=0.0):
        """발밑 잉크 대체(도색 샘플 객체가 가짜라 원본 값이 없음): StepPaint 갱신 직후 +0x30 분류, +0x3c/+0x40 아군, +0x48/+0x54 적 비율을 덮어쓴다. ← 스텁"""
        self.paint = None if kind is None else dict(kind=kind, own=own, enemy=enemy)

    def _paint_hook(self, mu, addr, size, ud):
        p = self.paint
        if not p:
            return
        u = self.u
        sp = u.rq(self.body + 0xA688)
        u.w32(sp + 0x30, p["kind"])
        u.wf(sp + 0x3C, p["own"])
        u.wf(sp + 0x40, p["own"])
        u.wf(sp + 0x48, p["enemy"])
        u.wf(sp + 0x54, p["enemy"])

    def set_ray(self, hit=None):
        """플레이어 쪽 레이캐스트 0x7103a5f36c(호출 0x710248a6ac, 0x71024ac0ac, 0x71024ac780) 결과 대체: hit=True/False, None 이면 원본(가짜 Phive → 빗나감). ← 스텁"""
        self.ray_hit = hit

    def _ray_hook(self, mu, addr, size, ud):
        if self.ray_hit is None:
            return
        lr = mu.reg_read(UC_ARM64_REG_LR)
        if lr in (0x710248A6B0, 0x71024AC0B0, 0x71024AC784):
            mu.reg_write(UC_ARM64_REG_X0, 1 if self.ray_hit else 0)
            mu.reg_write(UC_ARM64_REG_PC, lr)

    def _contact_hook(self, mu, addr, size, ud):
        c = self.contact
        if not c:
            return
        u, pc = self.u, self.pc
        if c["ground"] is not None:
            u.w8(pc + 0xD0, 1 if c["ground"] else 0)
            if c["ground"]:
                for i, v in enumerate(c["normal"]):
                    u.wf(pc + 0xAC + 4 * i, v)
        if c["side"] is not None:
            u.w8(pc + 0xEC, 1 if c["side"] else 0)
            if c["side"]:
                for i, v in enumerate(c["side_normal"]):
                    u.wf(pc + 0xE0 + 4 * i, v)
                if c["side_point"] is not None:
                    for i, v in enumerate(c["side_point"]):
                        u.wf(pc + 0xD4 + 4 * i, v)

    def _ctrl_hook(self, mu, addr, size, ud):
        mu.reg_write(UC_ARM64_REG_X0, self.ctrl)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    def set_pad(self, hold=0, trig=0, stick=(0.0, 0.0), rstick=(0.0, 0.0)):
        u = self.u
        u.w32(self.ctrl + 0x8, trig)
        u.w32(self.ctrl + 0x114, hold)
        u.wf(self.ctrl + 0x120, stick[0])
        u.wf(self.ctrl + 0x124, stick[1])
        u.wf(self.ctrl + 0x128, rstick[0])
        u.wf(self.ctrl + 0x12C, rstick[1])

    def start(self):
        """PlayerBehavior 슬롯15 0x7102353a18 → 0x7102472c4c: 시작 배치(스포너 포즈 → 0x710249e0fc → 리셋 0x710249cb60). 한 번만 실행."""
        self.u.cur_tag = "start"
        return self.u.call(SLOT15, self.beh, 0, count=30_000_000)

    def watch_body(self, lo=0, hi=0xAC80, tag="B"):
        self.u.watch(self.body + lo, self.body + hi, tag)

    def step(self, slots=(18, 19), count=30_000_000):
        u = self.u
        res = {}
        for s in slots:
            fn = {15: SLOT15, 16: SLOT16, 18: SLOT18, 19: SLOT19}[s]
            u.cur_tag = f"f{self.frame}s{s}"
            res[s] = u.call(fn, self.beh, 0, count=count)
        self.frame += 1
        u.w32(self.gframe + 0x148, u.r32(self.gframe + 0x148) + 1)
        return res
