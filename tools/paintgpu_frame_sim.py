"""도색 GPU 한 프레임 파이프라인(0x7102c14168 패스 순서 + 모드별 렌더 상태) 재구현 · 합성 테스트.

근거(판독): 패스 순서 0x7102c14168, 모드별 렌더 상태(원본 실행 web/tools/paintgpu_renderstate_emu.py),
셰이더 web/tools/shader_paint_overpaint.py(Ryujinx 역번역 재구현), 카운터 0x7101043e64/ReportCounter(1).
한 텍셀만 다룬다(래스터·샘플링·행렬은 빼고 스탬프 마스크 값 ink_raw 를 직접 준다).
가정(추정): 색 텍스처 RG8/RGBA8 UNORM 이라 프레임 끝 저장값을 round(x*255)/255 로 양자화,
discard 된 조각은 스텐실·카운터에 반영되지 않음(셰이더 discard 후 스텐실 갱신).
사용: PY web/tools/paintgpu_frame_sim.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shader_paint_overpaint import overpaint, F32, TH  # noqa: E402

BIT = {0: 1, 1: 2, 2: 4}


class Texel:
    def __init__(self, tricolor=False):
        self.c = np.zeros(4, F32)
        self.c[3] = 1.0                     # RG8 이면 A 는 스위즐로 1 (RGBA8 이면 초기값 미확정)
        self.s = 0                          # 스텐실
        self.tricolor = tricolor

    def quant(self):
        nch = 3 if self.tricolor else 2
        for ch in range(nch):
            self.c[ch] = F32(round(float(self.c[ch]) * 255) / 255)


def frame(tx, reqs):
    """reqs: dict(queue=0|1|2, player=0..7|None, team, ink, alpha) — 요청 순서 = 큐 안 순서.
    반환: 플레이어별 카운터(그 프레임 SAMPLES_PASSED)."""
    pre = tx.c.copy()                      # 모드 4~7·0~2 는 색을 쓰지 않으므로 이 프레임 앞 색을 읽음
    cnt = {}
    q0 = [r for r in reqs if r["queue"] == 0]
    q1 = [r for r in reqs if r["queue"] == 1]
    q2 = [r for r in reqs if r["queue"] == 2]
    # 1) 큐0, 플레이어 번호 < 8: 모드 4/5/6 (알파 테스트, 스텐실 NOTEQUAL ref=팀비트 mask=팀비트, REPLACE), 카운터
    for r in q0:
        if r["player"] is None or r["player"] >= 8:
            continue
        b = BIT[r["team"]]
        v = overpaint(pre, r["ink"], r["alpha"], r["team"], alpha_test=True)
        passed = v is not None and (tx.s & b) != b
        if passed:
            tx.s = b
        cnt[r["player"]] = cnt.get(r["player"], 0) + (1 if passed else 0)
    # 2) 큐0 전체: 모드 7 (깊이만 기록, 색·스텐실 없음) — 이 텍셀 모델에서는 효과 없음
    # 3) 큐1: 모드 0/1/2 (알파 테스트, 스텐실 ALWAYS REPLACE 팀비트)
    for r in q1:
        v = overpaint(pre, r["ink"], r["alpha"], r["team"], alpha_test=True)
        if v is not None:
            tx.s = BIT[r["team"]]
    # 4) 큐0, 큐1 순서로 모드 9 (알파 테스트 없음, 색 RG(B)만, 그리기마다 배리어 → 순차 갱신)
    nch = 3 if tx.tricolor else 2
    for r in q0 + q1:
        v = overpaint(tx.c, r["ink"], r["alpha"], r["team"], alpha_test=False)
        if v is not None:
            tx.c[:nch] = v[:nch]
    # 5) 큐2(지우기): 모드 11 (지우기+알파 테스트, 스텐실 ZERO) → 모드 10 (지우기, 색)
    for r in q2:
        v = overpaint(pre, r["ink"], r["alpha"], 0, alpha_test=True, erase=True)
        if v is not None:
            tx.s = 0
    for r in q2:
        v = overpaint(tx.c, r["ink"], r["alpha"], 0, alpha_test=False, erase=True)
        if v is not None:
            tx.c[:nch] = v[:nch]
    tx.quant()
    return cnt


def owner_stencil(tx):
    """모드 14/15/16 카운트(스텐실 EQUAL 팀비트) 기준 소유 팀."""
    for t, b in BIT.items():
        if tx.s & (7 if tx.tricolor else 3) == b:
            return t
    return -1


def owner_color(tx):
    m = tx.c[:3].max()
    return -1 if m < TH else int(np.argmax(tx.c[:3]))


def req(team, ink, player=0, queue=0, alpha=1.0):
    return dict(queue=queue, player=player, team=team, ink=ink, alpha=alpha)


def main():
    cases = [
        ("빈 텍셀 팀0 ink1.0", [[req(0, 1.0)]]),
        ("같은 팀 다시 칠함(자기 땅)", [[req(0, 1.0)], [req(0, 1.0, player=1)]]),
        ("팀0 위 팀1 ink1.0", [[req(0, 1.0)], [req(1, 1.0, player=4)]]),
        ("팀0 위 팀1 ink0.4(못 뺏음)", [[req(0, 1.0)], [req(1, 0.4, player=4)]]),
        ("빈 텍셀 ink0.29(문턱 미달)", [[req(0, 0.29)]]),
        ("같은 프레임 같은 팀 2명 겹침", [[req(0, 1.0, player=0), req(0, 1.0, player=1)]]),
        ("같은 프레임 두 팀 겹침", [[req(0, 1.0, player=0), req(1, 1.0, player=4)]]),
        ("팀0 0.35 위 팀1 ink0.2(약한 덧칠)", [[req(0, 0.35)], [req(1, 0.2, player=4)]]),
        ("팀0 칠한 뒤 지우기 1.0", [[req(0, 1.0)], [dict(queue=2, player=None, team=0, ink=1.0, alpha=1.0)]]),
    ]
    for name, frames in cases:
        tx = Texel()
        log = []
        for f in frames:
            log.append(frame(tx, f))
        print(f"{name:<34} 카운터={log} 색={np.round(tx.c[:2] * 255).astype(int).tolist()} "
              f"스텐실={tx.s} 소유(스텐실)={owner_stencil(tx)} 소유(색≥0.3·최대)={owner_color(tx)}")


if __name__ == "__main__":
    main()
