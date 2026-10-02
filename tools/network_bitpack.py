"""[network] 원본 비트 writer(넷 이벤트/상태 직렬화의 실제 구현)를 unicorn으로 실행해 비트 패킹 순서를 확인한다.

- writer 클래스 vtable = [GOT 0x7105790db8]+0x10 = 0x71057209c0 (이벤트 큐잉 0x71018b8968, 디코드 0x71018b84d4 가 스택에 만드는 객체)
  슬롯 +0xa8 = 0x7103582678 writeBits(w, sink, src, nbits), +0x60 = 0x7103581630 u8, +0x70 = 0x7103581838 u32
  객체: +8 누적 바이트, +9 누적 비트 수, +0xb 사용 플래그, +0x10 sink, +0x18 총 비트 수
  sink->vt[+8](sink, &byte, 1) 로 8비트가 찰 때마다 1바이트씩 내보낸다.
- 검사 1: 무작위 (값, 비트수) 열을 원본 writeBits 로 쓴 바이트 == 파이썬 LSB 우선 패커 결과
- 검사 2: u8/u32 스칼라 슬롯도 같은 규칙인지
- 검사 3: 원본 PlayerNetState write(0x7102418788)를 실제 writer 로 실행 → 바이트열 == network_uc 로그(값,비트) 를 파이썬으로 패킹한 것
- 검사 4: 이벤트 메시지 헤더 값 요소(U32 + ParamU64 범위, 생성 0x71012a0168, vtable 0x7105573fd0)의 write 0x71012a4080 을
  GameFrame(0~8388607)·LifeNumber(0~15) 범위로 실행 → 비트 수 = 64-clz(max-min), 값 = clamp(v,min,max)-min (v<min 이면 0)
사용: PY web/tools/network_bitpack.py [--n 2000] [--json analysis/network/bitpack_result.json]
"""
import argparse
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X1, UC_ARM64_REG_X2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, STUB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WRITER_VT = 0x71057209C0
WRITE_BITS = 0x7103582678
WRITE_U8 = 0x7103581630
WRITE_U32 = 0x7103581838
PNS_CTOR = 0x7102417A50
PNS_WRITE = 0x7102418788
SINK_SLOT = 0x800  # STUB+0x800: sink vt[+8] 훅 위치


def py_pack(items):
    """LSB 우선: 값의 비트0 부터 현재 바이트의 빈 하위 비트 위치에 채운다."""
    out = bytearray()
    acc = 0
    nacc = 0
    for v, n in items:
        for i in range(n):
            acc |= ((v >> i) & 1) << nacc
            nacc += 1
            if nacc == 8:
                out.append(acc)
                acc = 0
                nacc = 0
    return bytes(out), acc, nacc


def stream(flushed, acc, nacc):
    """내보낸 바이트 + 남은 누적 비트(0 < nacc <= 8; writer 는 8비트가 차도 다음 쓰기 때까지 들고 있음)."""
    return bytes(flushed) + (bytes([acc]) if nacc else b"")


class Harness:
    def __init__(self):
        self.u = UC()
        mu = self.u.mu
        self.sink_bytes = bytearray()
        self.sink_vt = self.u.alloc(0x40)
        mu.mem_write(self.sink_vt + 8, struct.pack("<Q", STUB + SINK_SLOT))
        self.sink = self.u.alloc(0x20)
        mu.mem_write(self.sink, struct.pack("<Q", self.sink_vt))
        self.w = self.u.alloc(0x40)
        mu.hook_add(UC_HOOK_CODE, self._sink_hook, begin=STUB + SINK_SLOT, end=STUB + SINK_SLOT)

    def _sink_hook(self, mu, addr, size, user):
        p = mu.reg_read(UC_ARM64_REG_X1)
        n = mu.reg_read(UC_ARM64_REG_X2) & 0xFFFFFFFF
        self.sink_bytes += bytes(mu.mem_read(p, n))

    def reset_writer(self):
        self.u.mu.mem_write(self.w, struct.pack("<QQQQ", WRITER_VT, 0, self.sink, 0))
        self.sink_bytes = bytearray()

    def state(self):
        b = bytes(self.u.mu.mem_read(self.w + 8, 0x18))
        return b[0], b[1], struct.unpack_from("<I", b, 0x10)[0]


def check_random(h, n, seed=1):
    rnd = random.Random(seed)
    buf = h.u.alloc(16)
    bad = 0
    for _ in range(n):
        h.reset_writer()
        items = []
        for _ in range(rnd.randint(1, 12)):
            nb = rnd.randint(1, 32)
            v = rnd.getrandbits(nb)
            items.append((v, nb))
            h.u.mu.mem_write(buf, struct.pack("<Q", v))
            h.u.call(WRITE_BITS, h.w, h.sink, buf, nb)
        a, na, tot = h.state()
        if stream(h.sink_bytes, a, na) != stream(*py_pack(items)) or tot != sum(x[1] for x in items):
            bad += 1
    return bad


def check_scalar(h, n, seed=2):
    rnd = random.Random(seed)
    bad = 0
    for _ in range(n):
        h.reset_writer()
        items = []
        buf = h.u.alloc(16)
        for _ in range(rnd.randint(1, 6)):
            k = rnd.choice(["b", "u8", "u32"])
            if k == "b":
                nb = rnd.randint(1, 7)
                v = rnd.getrandbits(nb)
                h.u.mu.mem_write(buf, struct.pack("<Q", v))
                h.u.call(WRITE_BITS, h.w, h.sink, buf, nb)
                items.append((v, nb))
            elif k == "u8":
                v = rnd.getrandbits(8)
                h.u.call(WRITE_U8, h.w, h.sink, 0, v)
                items.append((v, 8))
            else:
                v = rnd.getrandbits(32)
                h.u.call(WRITE_U32, h.w, h.sink, 0, v)
                items.append((v, 32))
        a, na, _ = h.state()
        if stream(h.sink_bytes, a, na) != stream(*py_pack(items)):
            bad += 1
    return bad


def check_playernetstate(h):
    # 1) 기존 스텁 writer 로 (값, 비트) 로그
    u = h.u
    obj = u.alloc(0x1D0)
    u.call(PNS_CTOR, obj)
    # 위치·스탬프 등 몇 필드에 값 넣기
    u.f32(obj + 0x20, 10.5)
    u.f32(obj + 0x24, -3.25)
    u.f32(obj + 0x28, 100.0)
    u.u32(obj + 0x88, 12345)
    log = u.write(PNS_WRITE, obj)
    items = []
    for kind, nb, v in log:
        if kind == "bits" or kind.startswith("s"):
            items.append((v, nb))
    # 2) 실제 writer 로 실행: S+8 = writer, S+0x10 = sink
    h.reset_writer()
    S2 = u.alloc(0x20)
    u.mu.mem_write(S2, struct.pack("<QQQI", 0, h.w, h.sink, 0))
    u.call(PNS_WRITE, obj, S2)
    a, na, tot = h.state()
    return {
        "logged_bits": sum(x[1] for x in items),
        "writer_total_bits": tot,
        "bytes_flushed": len(h.sink_bytes),
        "pending_bits": na,
        "match": stream(h.sink_bytes, a, na) == stream(*py_pack(items)),
        "first_bytes_hex": bytes(h.sink_bytes[:12]).hex(),
    }


RANGED_U32_WRITE = 0x71012A4080
RANGED_U32_READ = 0x71012A40DC


def check_header(h):
    u = h.u
    el = u.alloc(0x20)
    val = u.alloc(8)
    out = {}
    for name, lo, hi, tests in (("GameFrame", 0, 8388607, [0, 1, 12345, 8388607, 8388608, 0xFFFFFFFF]),
                                ("LifeNumber", 0, 15, [0, 3, 15, 16, 200])):
        u.mu.mem_write(el + 0x14, struct.pack("<II", lo, hi))
        rows = []
        for v in tests:
            u.u32(val, v)
            u.log = []
            u.call(RANGED_U32_WRITE, el, u.S, val)
            (kind, nb, q), = u.log
            exp_nb = (hi - lo).bit_length()
            exp_q = 0 if v < lo else min(v, hi) - lo
            # read 왕복
            u.feed = [("bits", nb, q)]
            u.call(RANGED_U32_READ, el, u.S, val)
            back = u.ru32(val)
            rows.append({"v": v, "bits": nb, "q": q, "ok": nb == exp_nb and q == exp_q, "read_back": back})
        out[name] = rows
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--json", default=str(ROOT / "analysis/network/bitpack_result.json"))
    a = ap.parse_args()
    h = Harness()
    res = {
        "writeBits_random_mismatch": check_random(h, a.n),
        "scalar_mix_mismatch": check_scalar(h, a.n // 4),
        "playernetstate": check_playernetstate(h),
        "event_header_value_elements": check_header(h),
        "trials": a.n,
    }
    print(json.dumps(res, indent=1))
    Path(a.json).write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
