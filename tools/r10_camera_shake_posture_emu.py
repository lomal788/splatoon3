"""New renderer input/selection bridges, using original instructions.

Synthetic camera/render/list graphs and synthetic posture. Captured downstream
frustum/UBO entry calls are explicit boundaries, not GPU execution. SDK trig
executes original SDK instructions. Never establishes live Lby posture.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
ns = {'__file__': str(ROOT / 'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT / 'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf8').split('\nh=H(')[0], ns)
H, R = ns['H'], ns['R']
from r5_player_libm_emu import Sdk
B = R.BASE
sdk = Sdk()
F = np.float32
trig = {B + 0x3e9be40: 'sinf', B + 0x3e9be30: 'cosf', B + 0x3e9c1f0: 'tanf'}
def bits(f): return struct.unpack('<I', struct.pack('<f', float(f)))[0]
def packf(vals): return struct.pack('<' + 'f' * len(vals), *map(float, vals))

class E(H):
    def _block(self, mu, pc, size, user):
        if pc in self.capture:
            args = [mu.reg_read(r) for r in [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6]]
            data = bytes(mu.mem_read(args[3], 0xc0)) if pc == B + 0x36b2350 and self.mode == 'context' else None
            self.events.append({'entry': hex(pc), 'args': args, 'projection': data})
            mu.reg_write(UC_ARM64_REG_X0, 0)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            self.boundaries[hex(pc)] += 1
            return
        if pc in self.helpers:
            self.boundaries[hex(pc)] += 1
            mu.reg_write(UC_ARM64_REG_X0, 0)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if pc in trig:
            v = struct.unpack('<f', struct.pack('<I', mu.reg_read(UC_ARM64_REG_S0) & 0xffffffff))[0]
            mu.reg_write(UC_ARM64_REG_S0, sdk.call(trig[pc], v))
            self.sdklog[trig[pc] + '_originalSDK'] += 1
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        super()._block(mu, pc, size, user)

e = E([B + 0x36c9198])
e.executed = set(); e.sdklog = Counter(); e.stublog = Counter()
e.capture = set(); e.helpers = set(); e.events = []; e.boundaries = Counter(); e.mode = ''
def no_null(mu, access, a, size, value, user):
    if a < 0x400000:
        raise RuntimeError(f'null read {a:#x} at {mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ, no_null)
counts = Counter()

# Original per-context local Perspective constructor, including gate/list order.
mgr = e.alloc(0x600); root = e.alloc(0x50); scene = e.alloc(0x40)
nodes = [e.alloc(0x18) for _ in range(2)]
contexts = [e.alloc(0x600) for _ in range(2)]
e.w64(B + 0x5812890, root); e.w64(root + 0x28, scene)
e.capture = {B + 0x36b2350}; e.mode = 'context'
sentinel = mgr + 0x2f0
for nctx in [0, 1, 2]:
    e.w64(mgr + 0x2f8, nodes[0] if nctx else sentinel)
    for i in range(nctx):
        e.w64(nodes[i] + 8, nodes[i + 1] if i + 1 < nctx else sentinel)
        e.w64(nodes[i] + 0x10, contexts[i])
    for width, height, typ in [(0, 0, 0), (0, 0, 3), (1, 1, 0), (1280, 720, 0), (1920, 1080, 3), (65535, 0, 3), (2, 65535, 2)]:
        for posture in [0, 1, 2, 3, 4, 5, 6, 0xffffffff]:
            for gate, match in [(0, True), (1, True), (0, False)]:
                for i, ctx in enumerate(contexts):
                    e.mu.mem_write(ctx + 0x40, struct.pack('<HH', width, height))
                    e.mu.mem_write(ctx + 0x4a, struct.pack('<H', typ))
                    e.mu.mem_write(ctx + 0x4c4, packf([.5 + i, 1500 + i, .8 + i * .1]))
                e.w32(B + 0x5997898, posture); e.w32(B + 0x599789c, bits(.2))
                e.events = []
                e.call(B + 0x117230c, [mgr, gate, scene if match else scene + 8, scene])
                assert len(e.events) == (nctx if gate == 0 and match else 0)
                for i, event in enumerate(e.events):
                    args, p = event['args'], event['projection']
                    assert args[1:3] == [24 + i, contexts[i] + 0x4e8]
                    assert args[4] == args[2]
                    assert struct.unpack_from('<Q', p)[0] == B + 0x57213b8
                    assert p[8:10] == b'\x01\x01'
                    assert struct.unpack_from('<I', p, 0x8c)[0] == posture
                    assert struct.unpack_from('<I', p, 0x90)[0] == bits(1)
                    assert struct.unpack_from('<I', p, 0x94)[0] == bits(.2)
                    assert p[0x98:0xa4] == packf([.5 + i, 1500 + i, .8 + i * .1])
                    with np.errstate(divide='ignore', invalid='ignore'):
                        aspect = F(F(max(width, 1)) / F(height if typ == 3 else max(height, 1)))
                    assert struct.unpack_from('<I', p, 0xb0)[0] == bits(aspect)
                    angle = F(F(.8 + i * .1) * F(.5))
                    assert p[0xa4:0xb0] == struct.pack('<III', *[sdk.call(n, angle) for n in ['sinf', 'cosf', 'tanf']])
                counts['context_projection_provider'] += 1

# Full original renderer selector, with downstream renderer work captured.
e.mode = 'renderer'; e.capture = {B + 0x36b2350}
e.helpers = {B + a for a in [0x367c688, 0x371e014, 0x36f5158, 0x371121c, 0x367c814, 0x374e580]}
renderer = e.alloc(0x5400); view = e.alloc(0x18b8); env = e.alloc(0xe00)
meta = e.alloc(0x258); output = e.alloc(0x7f0); resources = e.alloc(0x2348)
holder = e.alloc(0x18); alt = e.alloc(0x200); camera = e.alloc(0x400); altprojection = e.alloc(0xc0)
clock = e.alloc(0x10); e.w64(B + 0x5997a18, clock)
e.w32(renderer + 0x188, 1); e.w64(renderer + 0x190, view)
e.w64(view + 0x5c8, env); e.w64(env + 0x78, camera + 0x190); e.w64(env + 0x80, camera + 0x220)
e.w32(renderer + 0x3090, 1); e.w64(renderer + 0x3098, meta)
e.w32(renderer + 0x4ae8, 1); e.w64(renderer + 0x4af0, output)
e.w64(renderer + 0x3080, holder); e.w32(holder + 8, 1); e.w64(holder + 0x10, resources)
e.w64(alt + 0x160, altprojection)
for active in [0, 1]:
    for flags in [0, 1, 2, 3, 0x20, 0x21, 0x22, 0x23, 0xffff]:
        for present in [0, 1]:
            for keepmainprev in [0, 1]:
                for missingmain in [0, 1]:
                    e.mu.mem_write(view + 0x620, bytes([active]))
                    e.mu.mem_write(env + 0x8a, struct.pack('<H', flags))
                    e.w64(env + 0x1f8, alt if present else 0)
                    e.mu.mem_write(renderer + 0x5245, bytes([8 if keepmainprev else 0]))
                    e.w64(env + 0x78, 0 if missingmain else camera + 0x190)
                    e.w64(env + 0x80, 0 if missingmain else camera + 0x220)
                    e.events = []
                    e.call(B + 0x36c9198, [renderer])
                    assert len(e.events) == (3 if active else 0)
                    usealt = bool(flags & 0x21) and bool(flags & 2) and present
                    expectedview = alt + 0x10 if usealt else ((B + 0x5999258 if missingmain else camera + 0x190) + 8)
                    expectedproj = altprojection if usealt else (B + 0x59992c0 if missingmain else camera + 0x220)
                    expectedprev = alt + 0x10 if usealt and not keepmainprev else ((B + 0x5999258 if missingmain else camera + 0x190) + 8)
                    for i, event in enumerate(e.events):
                        assert event['args'][:5] == [view, i, expectedview, expectedproj, expectedprev], event
                    counts['renderer_view_projection_selection'] += 1

# Actual uniform submit caller passes record+C0 (logical), not device+4C.
e.mode = 'submit'; e.capture = {B + 0x36b2574}
e.helpers = {B + 0x36b8550, B + 0x36b1e20}
record = e.alloc(0x430 * 3); e.w64(view + 0x18, record)
for active in [0, 1]:
    for nrecords in [0, 1, 2, 3]:
        for bit2 in [0, 1]:
            e.mu.mem_write(view + 0x620, bytes([active])); e.w32(view + 0x10, nrecords)
            e.w32(renderer + 0x5238, bit2 * 4); e.events = []
            e.call(B + 0x36ceec4, [renderer, 0])
            assert len(e.events) == (nrecords if active else 0)
            for i, event in enumerate(e.events):
                args = event['args']; rec = record + i * 0x430
                assert args[:7] == [view, i, rec, rec + 0xc0, rec + 0x60, 0, bit2], args
            counts['gsys_uniform_submit_logical_pointer'] += 1

# Actual Projection consumer updates both matrices yet forwards logical+0C.
e.mode = 'consumer'; e.capture = {B + 0x36242b0}; e.helpers = set()
projection = e.alloc(0xc0); destination = e.alloc(0x280)
for logicaldirty in [0, 1]:
    for devicedirty in [0, 1]:
        for posture in [0, 1, 2, 3, 4, 5, 6, 0xffffffff]:
            e.mu.mem_write(projection, bytes(0xc0)); e.w64(projection, B + 0x57213b8)
            e.mu.mem_write(projection + 8, bytes([logicaldirty, devicedirty]))
            e.w32(projection + 0x8c, posture); e.w32(projection + 0x90, bits(1)); e.w32(projection + 0x94, bits(0))
            e.mu.mem_write(projection + 0x98, packf([1, 100, 1]))
            e.mu.mem_write(projection + 0xa4, struct.pack('<III', *[sdk.call(n, .5) for n in ['sinf', 'cosf', 'tanf']]))
            e.w32(projection + 0xb0, bits(F(4 / 3)))
            logical = packf([F(.1 * i + 1) for i in range(16)])
            device = packf([F(.2 * i - 1) for i in range(16)])
            e.mu.mem_write(projection + 0xc, logical); e.mu.mem_write(projection + 0x4c, device)
            e.events = []
            e.call(B + 0x3624cd0, [destination, projection])
            assert len(e.events) == 1
            assert e.events[0]['args'][:2] == [destination, projection + 0xc]
            assert e.mu.mem_read(projection + 8, 2) == b'\0\0'
            if not logicaldirty:
                assert e.mu.mem_read(projection + 0xc, 64) == logical
            if not logicaldirty and not devicedirty:
                assert e.mu.mem_read(projection + 0x4c, 64) == device
            counts['actual_projection_consumer_forwards_logical'] += 1

out = {'counts': dict(counts), 'total': sum(counts.values()), 'mismatches': 0,
       'captured_boundaries': dict(e.boundaries), 'SDK_stubs': dict(e.sdklog), 'non_SDK_stubs': {hex(k): v for k, v in e.stublog.items()},
       'scope': 'original117230c provider/local ctor, original36c9198 selector, original36ceec4 submit caller, original3624cd0 consumer with actual Projection VT; synthetic graphs/posture; downstream36b2350/36b2574/36242b0 and named renderer helpers captured; originalSDK trig; no live GPU/frame/scene/platform posture',
       'functions': ['117230c', '36c9198', '36ceec4', '3624cd0']}
assert not e.stublog
dest = ROOT / 'analysis/camera_100_r10/posture/bridge_native.json'
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(out, ensure_ascii=False))
