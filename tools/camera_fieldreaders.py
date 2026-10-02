"""파라미터 필드 리더 찾기: 설정됨 플래그 ldrb [x,#flag] 와 값 ldr [x,#off] 가 가까이(±win) 있는 위치 → 함수 시작.
사용: camera_fieldreaders.py <param_reflect json> [필드명...] [--win 24]
"""
import sys, json, argparse, numpy as np
R = r"C:/dev/splatoon3"; BASE = 0x7100000000; TEXT_END = 0x3e9df50
ap = argparse.ArgumentParser(); ap.add_argument('json'); ap.add_argument('fields', nargs='*'); ap.add_argument('--win', type=int, default=24)
a = ap.parse_args()
d = np.fromfile(R + "/extracted/exefs/main.img", dtype='<u4', count=TEXT_END // 4)
starts = np.load(R + "/analysis/camera/func_starts.npy")
J = json.load(open(a.json))
for f in J['fields']:
    if a.fields and f['name'] not in a.fields: continue
    k = f['kind']; off = f['offset']; fl = f['flag_offset']
    if k not in ('f32', 's32', 'bool'): continue
    if k == 'f32': v = 0xBD400000 | ((off // 4) << 10)
    elif k == 's32': v = 0xB9400000 | ((off // 4) << 10)
    else: v = 0x39400000 | (off << 10)
    fv = 0x39400000 | (fl << 10)
    vi = np.nonzero((d & 0xFFFFFC00) == v)[0]
    fi = np.nonzero((d & 0xFFFFFC00) == fv)[0]
    fs = set()
    j = np.searchsorted(fi, vi - a.win)
    for x, jj in zip(vi, j):
        if jj < len(fi) and fi[jj] <= x + a.win:
            s = starts[np.searchsorted(starts, x * 4, 'right') - 1]
            fs.add(int(s))
    print(f['name'], ' '.join(hex(BASE + s) for s in sorted(fs)))
