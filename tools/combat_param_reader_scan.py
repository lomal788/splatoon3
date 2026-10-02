"""파라미터 리더 후보 스캔.

GameParameter 접근 코드는 '설정됨 플래그'(ldrb [x,#flag])를 확인하고 부모 체인을 타고 올라간 뒤
필드(ldr w/s [x,#off])를 읽는다. 플래그 오프셋/필드 오프셋 쌍 집합이 모두 한 창(window) 안에
나타나는 위치를 찾는다.

사용: PY web/tools/combat_param_reader_scan.py 0x40:0x38 0x41:0x3c [...] [--win 0x800]
"""
import sys, numpy as np
IMG = 'C:/dev/splatoon3/extracted/exefs/main.img'
BASE = 0x7100000000
TEXT_END = 0x3e9df50

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    win = 0x800
    if '--win' in sys.argv:
        win = int(sys.argv[sys.argv.index('--win') + 1], 0)
        args = [a for a in args if a != sys.argv[sys.argv.index('--win') + 1]]
    pairs = [tuple(int(x, 0) for x in a.split(':')) for a in args]
    data = np.fromfile(IMG, dtype='<u4', count=TEXT_END // 4)
    idx = np.arange(len(data), dtype=np.int64) * 4
    def ldrb(imm):
        return (data & 0xFFFFFC00) == (0x39400000 | (imm << 10))
    def ldr32(imm):
        enc = (imm // 4) << 10
        return ((data & 0xFFFFFC00) == (0xB9400000 | enc)) | ((data & 0xFFFFFC00) == (0xBD400000 | enc))
    sets = []
    for fl, off in pairs:
        sets.append((idx[ldrb(fl)], idx[ldr32(off)]))
    # anchor: 첫 플래그 위치
    anchors = sets[0][0]
    hits = []
    for a in anchors:
        ok = True
        for fls, offs in sets:
            f = fls[(fls >= a - win) & (fls <= a + win)]
            o = offs[(offs >= a - win) & (offs <= a + win)]
            if len(f) == 0 or len(o) == 0:
                ok = False
                break
        if ok:
            hits.append(a)
    # 병합
    out = []
    for h in hits:
        if out and h - out[-1][1] < win:
            out[-1][1] = h
        else:
            out.append([h, h])
    for s, e in out:
        print(hex(BASE + s), hex(BASE + e))
    print(len(out), 'regions', file=sys.stderr)

if __name__ == '__main__':
    main()
