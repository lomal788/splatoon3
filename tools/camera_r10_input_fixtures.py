"""Port regression capture of already analyzed r10 camera input and 24e64f0.

Expected output comes only from original ARM64/SDK execution. Native libm traces
let tests distinguish input arithmetic from the JS Math adapter's ULP boundary.
This does not rerun the r10 independent analysis or modify its saved results.
Synthetic pre-block inputs; no raw device remap/whole input/frame/GPU claim.
"""
import json
import random
import struct
from pathlib import Path

from unicorn.arm64_const import *
from r6_player_uc import PUC, BASE, STACK, STACK_SZ
from r5_player_libm_emu import Sdk

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/port_camera_r10/input'
DEST = ROOT / 'web/games/splatoon3/tests/fixtures/camera_r10_input_native.json'


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def value(raw):
    return struct.unpack('<f', struct.pack('<I', raw & 0xffffffff))[0]


def f(value_):
    return value(bits(value_))


def main():
    sdk = Sdk()
    calls = {}
    current_trace = []
    names = {BASE + 0x3e9bb60: 'powf', BASE + 0x3e9c2a0: 'logf', BASE + 0x3e9be20: 'expf'}

    class Native(PUC):
        def _plt(self, mu, pc, size, obj):
            if pc not in names:
                return super()._plt(mu, pc, size, obj)
            name = names[pc]
            args = [mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff]
            if name == 'powf':
                args.append(mu.reg_read(UC_ARM64_REG_S1) & 0xffffffff)
            result = sdk.call(name, *[value(a) for a in args])
            calls[name] = calls.get(name, 0) + 1
            current_trace.append(dict(name=name, argBits=args, resultBits=result))
            mu.reg_write(UC_ARM64_REG_S0, result)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_X30))

    u = Native()
    mu = u.mu
    camera = u.alloc(0x2000)
    holder = u.alloc(0x200)
    body = u.alloc(0xb000)
    manager = u.alloc(0x200)
    device = u.alloc(0x200)
    correction = u.alloc(4)
    u.wq(camera + 0x1968, holder)
    u.wq(holder + 0x108, body)
    u.wq(BASE + 0x59a57d0, manager)
    u.wq(manager + 0x20, device)
    u.wq(manager + 0xd0, device)
    sp = STACK + STACK_SZ - 0x2000
    rng = random.Random(2026100310)
    rows = {'axis': [], 'bias': [], 'yaw': [], 'pitch': [], 'pitchMap': [], 'pitchFollow': []}

    def sample(lo, hi):
        return f(rng.uniform(lo, hi))

    def sf(reg, val):
        mu.reg_write(globals()['UC_ARM64_REG_S' + str(reg)], bits(val))

    def block(start, end):
        current_trace.clear()
        mu.reg_write(UC_ARM64_REG_X19, camera)
        mu.reg_write(UC_ARM64_REG_X28, camera + 0x1521)
        mu.reg_write(UC_ARM64_REG_SP, sp)
        mu.emu_start(BASE + start, BASE + end, count=10000)
        assert mu.reg_read(UC_ARM64_REG_PC) == BASE + end

    for i in range(256):
        gyro = bool(i % 2)
        x, y = sample(-1, 1), sample(-1, 1)
        if i < 24:
            x = f([0, -0., .5, -.5, 1, -1][i % 6])
            y = f([0, .5, -.5, 1][i // 6])
        old = dict(deltaX=sample(-1, 1), deltaY=sample(-1, 1), accumulator=sample(-1, 3))
        if i >= 192:
            # A real native state chain from the preceding captured output.
            old = dict(zip(old, [value(b) for b in rows['axis'][-1]['outputBits'][:3]]))
            gyro = 208 <= i < 216
        dx, dy = sample(-2, 2), sample(-2, 2)
        for off, val in zip([0x180, 0x184, 0x188], old.values()):
            u.wf(camera + off, val)
        u.wf(body + 0xaa4, dx)
        u.wf(body + 0xaa8, dy)
        mu.reg_write(UC_ARM64_REG_W8, int(gyro))
        mu.reg_write(UC_ARM64_REG_W24, bits(y))
        sf(12, abs(x)); sf(10, abs(y)); sf(9, f(-x)); sf(13, 0)
        block(0x24e0bbc, 0x24e0d78)
        output = [u.r32(camera + off) for off in [0x180, 0x184, 0x188]]
        output += [mu.reg_read(UC_ARM64_REG_S9) & 0xffffffff, mu.reg_read(UC_ARM64_REG_W24) & 0xffffffff]
        rows['axis'].append(dict(state=old, input=dict(x=x, y=y, deltaX=dx, deltaY=dy, gyro=gyro),
                                 outputBits=output, mathTrace=list(current_trace), chained=i >= 192))

    for i in range(128):
        x, y = sample(-1, 1), sample(-1, 1)
        if i < 12:
            x = f([0, .0001, .0009999, .001, .1, 1][i // 2]); y = 0
        gyro = bool(i % 2)
        mu.reg_write(UC_ARM64_REG_W8, int(gyro))
        sf(13, x); sf(6, y); sf(12, 0)
        block(0x24e0f38, 0x24e1008)
        rows['bias'].append(dict(input=dict(x=x, y=y, gyro=gyro),
                                 outputBits=[mu.reg_read(UC_ARM64_REG_S14) & 0xffffffff], mathTrace=list(current_trace)))

    for i in range(256):
        k = sample(-1, 1)
        if i < 6:
            k = f([-1, 0, 1][i // 2])
        inp = dict(k=k, gyro=bool(i % 2), velocity=sample(-.1, .1), yaw=sample(-1, 1),
                   magnitude=sample(0, 1.4), fovRatio=sample(0, 1), slowBlendDisabled=bool((i // 2) % 2),
                   movementBlend=sample(0, 1), postureState=[0, 1, 2, 3, 4, 5, 0xffffffff][i % 7],
                   capDeg=sample(.5, 7), capBlend=sample(0, 1), squidBlend=sample(0, 1), tilt=sample(-1, 1))
        for off, key in [(0x1cc, 'k'), (0x156c, 'capDeg'), (0x1550, 'capBlend'), (0x1764, 'squidBlend'),
                         (0x14d4, 'tilt'), (0x14f8, 'velocity')]:
            u.wf(camera + off, inp[key])
        u.w8(camera + 0x15d8, int(inp['gyro']))
        u.w8(camera + 0x15d9, int(inp['slowBlendDisabled']))
        u.w32(body + 0xf34, inp['postureState'])
        u.wf(sp + 0x38, inp['movementBlend'])
        mu.reg_write(UC_ARM64_REG_X9, body)
        sf(13, inp['yaw']); sf(14, inp['magnitude']); sf(8, inp['fovRatio'])
        block(0x24e10bc, 0x24e12a8)
        rows['yaw'].append(dict(input=inp, outputBits=[u.r32(camera + 0x14fc), u.r32(camera + 0x14f8)]))

    for i in range(256):
        inp = dict(k=sample(-1, 1), gyroK=sample(-1, 1), gyro=bool(i % 2), velocity=sample(-.08, .08),
                   angle=sample(-100, 100), pitch=sample(-1, 1), magnitude=sample(0, 1.4), fovRatio=sample(0, 1),
                   limitBlend=sample(0, 1), controllerMode=[0, 1, 2][i % 3], slot=[0, 1, 0xffffffff][i % 3],
                   offsets=[sample(-5, 5) for _ in range(4)])
        if i < 6:
            inp['gyroK'] = 0
            inp['angle'] = [-28, 0, 44][i // 2]
        for off, key in [(0x1cc, 'k'), (0x1c8, 'gyroK'), (0x1504, 'velocity'), (0x150c, 'angle'), (0x1680, 'limitBlend')]:
            u.wf(camera + off, inp[key])
        u.wf(camera + 0x16c, .4)
        u.w8(camera + 0x15d8, int(inp['gyro']))
        u.w8(camera + 0x15d9, 0)
        u.w32(camera + 0x15f0, inp['slot'])
        for off, val in zip([0x15f4, 0x15f8, 0x15fc, 0x1600], inp['offsets']):
            u.wf(camera + off, val)
        u.wf(camera + 0x1604, .5); u.wf(camera + 0x1608, .5)
        u.w8(device + 0x17d, inp['controllerMode'])
        u.w32(manager + 0x164, i % 8)
        u.w32(body + 0xf34, [0, 2, 4, 5][i % 4])
        u.wf(sp + 0x38, sample(0, 1))
        mu.reg_write(UC_ARM64_REG_X9, body)
        mu.reg_write(UC_ARM64_REG_W8, 0 if inp['gyro'] else 1)
        sf(6, inp['pitch']); sf(8, inp['fovRatio']); sf(14, inp['magnitude']); sf(11, 0)
        block(0x24e1674, 0x24e1c30)
        rows['pitch'].append(dict(input=inp, outputBits=[u.r32(camera + off) for off in [0x1508, 0x1504, 0x150c]],
                                  mathTrace=list(current_trace)))

    for i in range(256):
        inp = dict(angle=sample(-320, 260), gyroK=sample(-1, 1), handheldFlag=bool(i % 2),
                   offA=sample(-8, 8), offB=sample(-8, 8), stick=bool((i // 2) % 2))
        if i < 24:
            inp.update(angle=[-180, -165, -115, -103, -89, -75, -65, -53, -31, -25, 60, 195][i // 2],
                       gyroK=0, handheldFlag=False, offA=0, offB=0, stick=True)
        current_trace.clear()
        err = u.call(BASE + 0x24e64f0, int(not inp['handheldFlag']), int(inp['stick']), correction,
                     fargs=[inp['gyroK'], inp['angle'], inp['offA'], inp['offB']])
        assert err is None, err
        rows['pitchMap'].append(dict(input=inp, outputBits=[mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff, u.r32(correction)]))

    for i in range(128):
        previous, y = sample(0, 1), sample(-1, 1)
        if i < 6:
            previous = f([.2, 1, 0][i // 2]); y = f([0, 1][i % 2])
        u.wf(camera + 0x168, previous)
        mu.reg_write(UC_ARM64_REG_W24, bits(y))
        block(0x24e09e0, 0x24e0a18)
        rows['pitchFollow'].append(dict(previous=previous, remappedY=y, outputBits=[u.r32(camera + 0x168)]))

    counts = {name: len(v) for name, v in rows.items()}
    assert not (u.null_calls or u.auto_pages or u.faults or u.plt_stubbed or u.libm_used)
    meta = dict(scope=__doc__, cases=counts, sdkOriginalCalls=calls, null={}, auto=[], fault=[], plt={},
                main_image='extracted/exefs/main.reloc.img', sdk_image='extracted/exefs/sdk.img',
                expected_source='original ARM64 outputs only; native libm result/argument traces captured',
                synthetic=['pre-block state', 'body/holder/controller records', 'pitch offsets', 'post-init snapshot'],
                whole_input_or_scene=False, new_analysis_credit=False)
    OUT.mkdir(parents=True, exist_ok=True)
    data = dict(meta=meta, **rows)
    DEST.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    (OUT / 'fixture_capture.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(cases=counts, total=sum(counts.values()), sdkOriginalCalls=calls,
                          null=0, auto=0, fault=0, plt=0)))


if __name__ == '__main__':
    main()
