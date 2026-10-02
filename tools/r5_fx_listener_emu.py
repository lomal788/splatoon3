"""r5 fx: Alto 리스너 TargetOffset 컨트롤러(mode 3, vtable 0x710573c1e0) 원본 실행 대조.

1) 0x710390d0cc (ctrl vt+0x40): 출력 뷰 행렬 = [R | -(R*T + off)] 를 f32 순서 그대로 재구현해 비트 비교.
   R = ctrl+0x48..+0x74 (카메라 뷰 행렬 3행), T = ctrl+0xa8 포인터가 있으면 *ptr, 없으면 ctrl+0x78..+0x80,
   off = ctrl+0x98..+0xa0 (ListenerParam TargetOffset_Offset 사본).
2) 0x710383b534 (리스너 갱신, ctrl vt+0x40 호출 → 역행렬 0x7100fa6fd4): 리스너 월드 위치(+0x13c/+0x14c/+0x15c)
   = T + R^T*off 인지 허용오차로 확인(역행렬은 일반 3x4 역이라 비트 비교 대상 아님), +0x190.. = 카메라 위치.
스텁 없음(두 함수 모두 외부 호출 없음; 0x710383b534 의 ctrl 가상 호출은 실제 vtable 로 감).
"""
import json, math, random, struct
from pathlib import Path
from network_uc import UC

ROOT = Path(__file__).resolve().parents[2]
f = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
VT = 0x710573c1e0


def rot(yaw, pitch):
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    # 카메라 기저 X(오른쪽), Y(위), Z(뒤) 를 뷰 행렬의 행으로 둔다
    z = (sy * cp, sp, cy * cp)
    x = (cy, 0.0, -sy)
    y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0])
    return [[f(v) for v in x], [f(v) for v in y], [f(v) for v in z]]


def expect_vt8(R, T, off):
    out = []
    for i in range(3):
        s = f(f(f(T[0] * R[i][0]) + f(T[1] * R[i][1])) + f(T[2] * R[i][2]))
        out.append(f(-f(s + off[i])))
    return out


def main():
    u = UC(); m = u.mu
    rng = random.Random(0x710390d0cc)
    ctrl = u.alloc(0xc0); ext = u.alloc(0x10); o1 = u.alloc(0x30); o2 = u.alloc(0x30)
    lis = u.alloc(0x200)
    n_vt8 = 0; n_pos = 0; max_err = 0.0
    for k in range(512):
        R = rot(rng.uniform(-math.pi, math.pi), rng.uniform(-1.4, 1.4))
        cam = [f(rng.uniform(-200, 200)) for _ in range(3)]
        T = [f(rng.uniform(-200, 200)) for _ in range(3)]
        off = [f(0.0), f(0.0), f(1.5)] if k % 4 == 0 else [f(rng.uniform(-3, 3)) for _ in range(3)]
        use_ext = k % 3 == 1
        # 카메라 뷰 행렬 이동 성분 = -R*cam
        tr = [f(-(R[i][0] * cam[0] + R[i][1] * cam[1] + R[i][2] * cam[2])) for i in range(3)]
        mat = b''.join(struct.pack('<4f', R[i][0], R[i][1], R[i][2], tr[i]) for i in range(3))
        m.mem_write(ctrl, b'\0' * 0xc0)
        m.mem_write(ctrl, struct.pack('<Q', VT))
        m.mem_write(ctrl + 0x48, mat)
        Tin = T
        if use_ext:
            m.mem_write(ext, struct.pack('<3f', *T)); m.mem_write(ctrl + 0x78, struct.pack('<3f', 9, 9, 9))
            m.mem_write(ctrl + 0xa8, struct.pack('<Q', ext))
        else:
            m.mem_write(ctrl + 0x78, struct.pack('<3f', *T))
        m.mem_write(ctrl + 0x98, struct.pack('<3f', *off))
        u.call(0x710390d0cc, ctrl, o1, o2)
        got = struct.unpack('<12f', m.mem_read(o1, 0x30))
        got2 = struct.unpack('<12f', m.mem_read(o2, 0x30))
        exp = expect_vt8(R, Tin, off)
        for i in range(3):
            assert got[4 * i:4 * i + 3] == tuple(R[i]), (k, i)
            assert struct.pack('<f', got[4 * i + 3]) == struct.pack('<f', exp[i]), (k, i, got[4 * i + 3], exp[i])
            assert got2[4 * i:4 * i + 4] == struct.unpack('<4f', mat[16 * i:16 * i + 16])
        n_vt8 += 1
        # 리스너 갱신 전체
        m.mem_write(lis, b'\0' * 0x200)
        m.mem_write(lis + 0xf8, struct.pack('<Q', ctrl))
        u.call(0x710383b534, lis)
        pos = struct.unpack('<f', m.mem_read(lis + 0x13c, 4))[0], struct.unpack('<f', m.mem_read(lis + 0x14c, 4))[0], struct.unpack('<f', m.mem_read(lis + 0x15c, 4))[0]
        want = [Tin[j] + sum(R[i][j] * off[i] for i in range(3)) for j in range(3)]
        campos = struct.unpack('<3f', m.mem_read(lis + 0x190, 12))
        err = max(abs(pos[j] - want[j]) for j in range(3))
        cerr = max(abs(campos[j] - cam[j]) for j in range(3))
        max_err = max(max_err, err, cerr)
        assert err < 2e-3 and cerr < 2e-3, (k, pos, want, campos, cam)
        n_pos += 1
    out = {'vt8_bit_matches': n_vt8, 'listener_pos_matches': n_pos, 'max_abs_err': max_err,
           'stubs': [], 'functions': ['0x710390d0cc', '0x710383b534', '0x7100fa6fd4'],
           'limits': ['카메라/타깃 공급(vt7 0x710390cfc4 의 isKindOf·외부 포인터 writer)는 실행 안 함',
                      '역행렬 경로는 허용오차 비교(2e-3 유닛), 비트 비교는 vt8 출력만']}
    (ROOT / 'analysis/completion/r5').mkdir(parents=True, exist_ok=True)
    (ROOT / 'analysis/completion/r5/fx_listener_emu.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
