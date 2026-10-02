"""[respawn] 피해 송신자(액터+0x238) 인터페이스 후보 vtable 찾기.

DamageReceiver::computeResult(0x7101a86ec0)는 송신자 vt+0x18(참조 핸들), +0x20(이력 모드 1~6),
+0x28(f32 시간), +0x40(누적 상한), +0x48(키)를 부른다. 데이터 영역에서
  vt[+0x20] 이 "mov w0,#k ; ret"(k=0..6) 이고 vt[+0x18],[+0x28],[+0x40],[+0x48]이 모두 text 포인터인
테이블을 찾아 k와 각 슬롯 함수 주소를 출력한다.
사용: PY web/tools/respawn_sender_vt.py
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img

m = load_img()
TXT_HI = BASE + TEXT_END


def q(a):
    return struct.unpack_from("<Q", m, a - BASE)[0]


def w(a):
    return struct.unpack_from("<I", m, a - BASE)[0]


def is_text(p):
    return BASE <= p < TXT_HI


def const_ret(f):
    """mov w0,#k ; ret  → k, 아니면 None"""
    i0, i1 = w(f), w(f + 4)
    if i1 != 0xD65F03C0:
        return None
    if (i0 & 0xFFE0001F) == 0x52800000:  # movz w0,#imm16
        return (i0 >> 5) & 0xFFFF
    if i0 == 0x2A1F03E0:  # mov w0,wzr
        return 0
    return None


def main():
    lo, hi = 0x7105388000, 0x7105388000 + 0x432CB0
    out = []
    for a in range(lo, hi - 0x50, 8):
        p20 = q(a + 0x20)
        if not is_text(p20):
            continue
        k = const_ret(p20)
        if k is None or not (1 <= k <= 6):
            continue
        slots = [q(a + o) for o in (0x18, 0x28, 0x30, 0x38, 0x40, 0x48)]
        if not all(is_text(s) for s in slots):
            continue
        # vtable 시작 후보: a-0x10 위치(오프셋·RTTI 슬롯) 대신 a 자체를 슬롯0으로 본다
        out.append((a, k, slots))
    for a, k, s in out:
        print(f"{a:#x} mode={k} vt18={s[0]:#x} vt28={s[1]:#x} vt30={s[2]:#x} vt38={s[3]:#x} vt40={s[4]:#x} vt48={s[5]:#x}")
    print("후보", len(out), file=sys.stderr)


if __name__ == "__main__":
    main()
