"""Original Context declaration and view/projection UBO writes.

Allocations are SDK boundaries. Synthetic view records use the actual descriptor
constructor and actual UBO vtable; GPU flush is absent (record+3b8=null).
Only copied View/Projection bytes are claimed bit exact, not FMA products.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
ns = {'__file__': str(ROOT / 'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT / 'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf8').split('\nh=H(')[0], ns)
H, R = ns['H'], ns['R']
B = R.BASE
e = H([B + 0x36b563c])
e.executed = set(); e.sdklog = Counter(); e.stublog = Counter()
def no_null(mu, access, a, size, value, user):
    if a < 0x400000:
        raise RuntimeError(f'null read {a:#x} at {mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ, no_null)
def packf(vals): return struct.pack('<' + 'f' * len(vals), *vals)

# Original 34-member Context declaration; actual allocator helper 35b78ec runs.
decl = e.alloc(0x80)
e.call(B + 0x36b563c, [decl, 0])
desc = e.r64(decl + 0x10)
table = e.r64(desc)
entries = []
for i in range(34):
    data = bytes(e.mu.mem_read(table + i * 12, 12))
    count, offset, columns, typ = struct.unpack_from('<IHHB', data)
    entries.append({'index': i, 'count': count, 'offset': offset, 'columns': columns, 'type': typ})
assert struct.unpack('<HH', e.mu.mem_read(desc + 8, 4)) == (34, 34)
assert [(r['offset'], r['count'], r['columns'], r['type']) for r in entries[:4]] == [(0,3,4,6),(0x30,4,4,6),(0x70,4,4,6),(0xb0,3,4,6)]
assert e.r32(decl + 0x38) == 2336

view = e.alloc(0x18b8); record = e.alloc(0x430); output = e.alloc(0xa00)
view_matrix = e.alloc(0x30); projection_matrix = e.alloc(0x40); frustum = e.alloc(0x200)
e.w32(view + 0x10, 1); e.w64(view + 0x18, record)
e.w64(record + 0x390, B + 0x57221a8)
e.w64(record + 0x3a0, desc); e.w64(record + 0x3a8, output)
e.w32(record + 0x3c8, 2336)
view_cases = [
    [1,0,0,0, 0,1,0,0, 0,0,1,0],
    [0,0,1,-23, 0,1,0,9, -1,0,0,111],
    [.5,-.25,.75,-91.25, 2,3,-4,11, 1,-2,3,-4],
]
projection_cases = [
    [1,0,0,0, 0,1,0,0, 0,0,-1,-1, 0,0,-1,0],
    [1.125,0,.0625,0, 0,2.25,-.125,0, 0,0,-1.25,-2.5, 0,0,-1,0],
    [-1.125,0,-.0625,0, 0,2.25,.125,0, 0,0,-1.25,-2.5, 0,0,-1,0],
    [1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16],
]
cases = 0
for vm in view_cases:
    for pm in projection_cases:
        for active in [0,1]:
            for force in [0,1]:
                for flag7 in [0,1]:
                    e.mu.mem_write(output, bytes([0xa5]) * 0xa00)
                    e.mu.mem_write(view_matrix, packf(vm)); e.mu.mem_write(projection_matrix, packf(pm))
                    e.mu.mem_write(record + 0x421, bytes([active]))
                    e.call(B + 0x36b2574, [view, 0, view_matrix, projection_matrix, frustum, force, flag7])
                    data = bytes(e.mu.mem_read(output, 0x920))
                    if active or force:
                        assert data[:0x30] == packf(vm)
                        assert data[0x70:0xb0] == packf(pm)
                    else:
                        assert data == bytes([0xa5]) * 0x920
                    cases += 1

out = {'cases': 1 + cases, 'descriptor_cases': 1, 'ubo_write_cases': cases,
       'mismatches': 0, 'context_bytes': e.r32(decl + 0x38), 'members': entries,
       'original_functions': ['36b563c','35b78ec','36b2574','35b810c','35b7e28','fa6fd4'],
       'SDK_stubs': dict(e.sdklog), 'allocator_boundary_calls': {hex(k):v for k,v in e.stublog.items()},
       'scope': 'Original 34-member descriptor plus whole UBO writer for synthetic view/projection/frustum; View0..2 and Projection7..10 copies bit exact. Matrix products/inverse are original execution but not independently bit-compared. No GPU buffer flush or native present execution.'}
dest = ROOT / 'analysis/camera_100_r10/posture/ubo_native.json'
dest.write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k != 'members'}))
