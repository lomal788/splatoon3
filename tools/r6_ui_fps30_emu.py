"""r6 ui: UI dt 배수 플래그(SystemTask+0x458 bit0) setter 사슬을 unicorn 으로 원본 실행한다.

사슬(전부 원본 명령 실행, 각 구간은 시작~끝 주소):
  A 씬 시작(씬 vtable 0x7105579058 슬롯 6 = 0x710131fa04) 구간 0x710131fac4..0x710131faec
      씬+0x354(Tag SceneAttr_Fps30 비트, 슬롯 4 0x710131f254 가 0x710131f794 에서 씀) | 2 == 3 이면 *(0x7105999df8)+0x458 |= 1
  B 씬 종료 상태(0x7101320390, +0x220 = 5) 구간 0x71013207f0..0x7101320818
      같은 조건이면 *(0x7105999df8)+0x458 &= ~1
  C gsys::SystemTask::preCalc_ 구간 0x71037a2a30..0x71037a2b24 : 프레임워크(+0xa8→+0x40)+0x222 bit0 ← SystemTask+0x458 bit0
  D 프레임워크 UI 프레임 0x7101026dd0(전체 함수) : dt = (+0x222 bit0 ? 2 : 1) × (n≥2 ? n : 1) → 0x710138475c(dt) 인자 기록
  E 프레임워크 프레임 끝 0x7103502d10(전체 함수) : +0x222 bit0 이면 bit1 토글

스텁(검증하지 않은 범위):
  C: 0x71035f5618(프로파일러, 전역 0x7105999200=0 이라 안 부름), 프레임워크 vt+0(형 검사) → 1 반환
  D: 0x710138475c(UI 레이어 64칸 채우기) → s0 기록 후 반환, 0x71035031ec(UI 갱신 본체) → 반환
  E: 0x7103509808, 프레임워크 vt+0xe8/+0xf0/+0x70/+0x110/+0x118, 0x7103e9a3d0(시각) → 반환
  0x7105999df8 = SystemTask 인스턴스 전역(설정 0x71037a2258 이 생성 콜백으로 등록됨 0x7103d9f350) — 가짜 객체를 넣음
사용: r6_ui_fps30_emu.py  → analysis/r6_ui/fps30_emu.json
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r6_ui_lib import *

OUT = ROOT / "analysis" / "r6_ui" / "fps30_emu.json"
ST_GLOBAL = 0x7105999df8
FW_GLOBAL = 0x710580e5e8      # *0x7105791c30 = 0x710580e5e8
GUARD = 0x710580e5c0


def build():
    e = Emu()
    mu = e.mu
    scene = e.alloc(0x400)
    st = e.alloc(0x500)                       # SystemTask
    fw = e.alloc(0x400)                       # 프레임워크
    fwvt = e.stub_vt(0x60, "fwvt")
    e.wq(fw, fwvt)
    holder = e.alloc(0x50)                    # SystemTask+0xa8 → +0x40 = 프레임워크
    e.wq(holder + 0x40, fw)
    e.wq(st + 0xa8, holder)
    d0 = e.alloc(0x20)
    e.wq(st + 0xd0, d0)
    e.mu.mem_write(st + 0x458, struct.pack("<I", 0x4000f2))   # 생성자 0x71037a26e4 기본값
    e.wq(ST_GLOBAL, st)
    e.wq(FW_GLOBAL, fw)
    e.mu.mem_write(GUARD, b"\x01")
    e.wq(0x7105999200, 0)
    misc = e.alloc(0x600)
    e.wq(0x71059a9020, misc)
    # 형 검사(vt+0) → 1
    def typechk(mu_, a, s, u):
        mu_.reg_write(UC_ARM64_REG_X0, 1)
        mu_.reg_write(UC_ARM64_REG_PC, mu_.reg_read(UC_ARM64_REG_X30))
    mu.hook_add(UC_HOOK_CODE, typechk, begin=fwvt and e.rq(fwvt), end=e.rq(fwvt))
    e.dts = []
    def layerdt(mu_, a, s, u):
        e.dts.append(struct.unpack("<f", struct.pack("<I", mu_.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF))[0])
        mu_.reg_write(UC_ARM64_REG_PC, mu_.reg_read(UC_ARM64_REG_X30))
    mu.hook_add(UC_HOOK_CODE, layerdt, begin=0x710138475c, end=0x710138475c)
    for f in (0x71035031ec, 0x7103509808, 0x7103e9a3d0):
        e.patch_ret(f)
    return e, scene, st, fw


def run_seg(e, start, end, x19):
    e.mu.reg_write(UC_ARM64_REG_X19, x19)
    e.mu.reg_write(UC_ARM64_REG_SP, e.STACK + 0x1F0000)
    e.mu.emu_start(start, end, count=10000)


def flag(e, a, off, n=4):
    return int.from_bytes(bytes(e.mu.mem_read(a + off, n)), "little")


def scenario(attr, frames=6, n_seq=None):
    e, scene, st, fw = build()
    e.mu.mem_write(scene + 0x354, struct.pack("<I", attr))
    run_seg(e, 0x710131fac4, 0x710131faec, scene)          # A 씬 시작
    st458_after_start = flag(e, st, 0x458)
    rows = []
    for k in range(frames):
        run_seg(e, 0x71037a2a30, 0x71037a2b24, st)          # C preCalc_
        b222_pre = flag(e, fw, 0x222, 1)
        n = (n_seq[k] if n_seq else 1)
        e.mu.mem_write(fw + 0x2cc, struct.pack("<I", n))
        e.dts = []
        e.call(0x7101026dd0, fw)                           # D UI 프레임
        dts = list(e.dts)
        e.call(0x7103502d10, fw)                           # E 프레임 끝
        rows.append(dict(frame=k, n=n, fw222_after_precalc=b222_pre, ui_dt=dts, fw222_after_end=flag(e, fw, 0x222, 1)))
    run_seg(e, 0x71013207f0, 0x7101320818, scene)          # B 씬 종료
    st458_after_end = flag(e, st, 0x458)
    return dict(scene354=attr, st458_after_start=hex(st458_after_start), st458_after_end=hex(st458_after_end), frames=rows)


def reimpl(attr, frames=6, n_seq=None):
    st = 0x4000f2
    if (attr | 2) == 3:
        st |= 1
    b222 = 0
    rows = []
    for k in range(frames):
        if not (b222 & 1):
            b222 = (b222 & 0xFE) | (st & 1)
        elif not (b222 & 2):
            b222 = (b222 & 0xFE) | (st & 1)
        pre = b222
        n = (n_seq[k] if n_seq else 1)
        f = 2.0 if (b222 & 1) else 1.0
        dts = [f * n, f] if n >= 2 else [f]
        if b222 & 1:
            b222 ^= 2
        rows.append(dict(frame=k, n=n, fw222_after_precalc=pre, ui_dt=dts, fw222_after_end=b222))
    end = st & ~1 if (attr | 2) == 3 else st
    return dict(scene354=attr, st458_after_start=hex(st), st458_after_end=hex(end), frames=rows)


def main():
    res, ok, tot = [], 0, 0
    for attr in (0, 1, 2, 3):
        for nseq in (None, [1, 2, 1, 3, 1, 1]):
            o = scenario(attr, n_seq=nseq)
            r = reimpl(attr, n_seq=nseq)
            same = o == r
            tot += 1
            ok += same
            res.append(dict(attr=attr, nseq=nseq, orig=o, same=same, reimpl=None if same else r))
            out(f"scene+0x354={attr} n={nseq}: SystemTask+0x458 시작후 {o['st458_after_start']} 종료후 {o['st458_after_end']}, "
                f"UI dt {[f['ui_dt'] for f in o['frames']]} → {'PASS' if same else 'FAIL'}")
    out(f"{ok}/{tot} PASS")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
