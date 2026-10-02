"""플레이어 상태 표(0x7105630270, 32B x 0x11e) 덤프.
항목 = (u64 사람 모델 애니 이름 | 0, u64 오징어 모델 애니 이름 | 0, u64 &u32 값, u64 플래그).
상태 변경 함수 0x7102447bfc 가 state<0x11e 일 때 표[state] 를 쓴다(아니면 표[0]).
사용: PY web/tools/state_table.py [출력 tsv]
"""
import struct, sys
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
B = 0x7100000000
BASE = 0x7105630270
N = 0x11e
img = open(IMG, 'rb').read()
def u64(a): return struct.unpack_from('<Q', img, a - B)[0]
def u32(a): return struct.unpack_from('<I', img, a - B)[0]
def cstr(a):
    if a == 0: return ''
    o = a - B
    e = img.index(b'\0', o)
    return img[o:e].decode('utf8', 'replace')
lines = ['id\thex\thuman_anim\tsquid_anim\tw2_ptr\tw2_val\tflags\tflags_bin']
for i in range(N):
    w = [u64(BASE + i * 32 + j * 8) for j in range(4)]
    lines.append(f'{i}\t{i:#x}\t{cstr(w[0])}\t{cstr(w[1])}\t{w[2]:#x}\t{u32(w[2]):#x}\t{w[3]:#x}\t{w[3]:020b}')
txt = '\n'.join(lines) + '\n'
if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
    open(sys.argv[1], 'w', encoding='utf8').write(txt)
if "--md" not in sys.argv:
    print(txt)


def md_rows():
    """문서용 표 행: 번호, 이름, 모델, 블렌드 프레임, 플래그, 이동 오징어 집합(S), 상태기계 오징어 판정(Q)."""
    rows = []
    for i in range(N):
        w = [u64(BASE + i * 32 + j * 8) for j in range(4)]
        hn, sn = cstr(w[0]), cstr(w[1])
        S = (0x82 <= i <= 0x90) or (0xaa <= i <= 0xac) or i in (0xed, 0xee, 0x10c)
        Q = S or (0xb8 <= i <= 0xba)
        rows.append(f"| {i:#x} | {hn or sn} | {'사람' if hn else '오징어'} | {u32(w[2])} | {w[3]:#07x} | {'S' if S else ''}{'Q' if Q else ''} |")
    return rows


if __name__ == '__main__' and '--md' in sys.argv:
    print('\n'.join(md_rows()))
