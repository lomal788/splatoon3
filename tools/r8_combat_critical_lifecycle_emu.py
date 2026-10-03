"""Original critical ring constructor stores, actual Reset RTTI, registered member thunk reset.
Whole actor/process startup is not emulated. No original code modifications.
"""
import json,struct,random,sys
from pathlib import Path
from collections import Counter
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'web/tools'))
g={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec(compile(Path(g['__file__']).read_text(encoding='utf-8').split('\nh=H(')[0],g['__file__'],'exec'),g)
h=g['H']([0x7101413a60]);h.executed=set();h.sdklog=Counter();h.stublog=Counter();h.heapobjects=[]
M=h.alloc(0xbb8);rng=random.Random(0x16e48c8)
# Actual Reset message RTTI getter (message primary VT568c5b8+20).
h.call(0x7102d550c4,[0]);key=h.mu.reg_read(UC_ARM64_REG_X0);assert key==0x710582ecc0
# Original constructor member-thunk/registration fields, excluding full Scene ctor.
h.mu.reg_write(UC_ARM64_REG_X21,M);h.mu.reg_write(UC_ARM64_REG_X23,key);h.mu.reg_write(UC_ARM64_REG_X20,M+0x2f8)
h.mu.emu_start(0x71027cdff8,0x71027ce044,count=100)
assert h.r64(M+0x320)==0x7105649a28 and h.r64(M+0x328)==M and h.r64(M+0x330)==0x71016e48c8 and h.r64(M+0x338)==0 and h.r64(M+0x340)==key
# Original constructor writes target=0/key=-1/damage=0 for exactly80 cells.
h.mu.mem_write(M+0x3c0,b'\xa5'*0x500);h.mu.reg_write(UC_ARM64_REG_X21,M)
h.mu.emu_start(0x71027ce054,0x71027ce42c,count=300)
expected=b''.join(struct.pack('<Qii',0,-1,0) for _ in range(80));assert bytes(h.mu.mem_read(M+0x3c0,0x500))==expected
cases=512
for z in range(cases):
 old=b''.join(struct.pack('<QII',rng.getrandbits(64),rng.getrandbits(32),rng.getrandbits(32)) for _ in range(80));h.mu.mem_write(M+0x3c0,old);h.w64(M+0x3b8,0x0123456789abcdef);h.w32(M+0x3a8,0)
 # Invalid native actor handles follow real early return; no reference clear stubs.
 for i in range(12):h.w32(M+0x8c8+0x30*i+0x10,-1)
 h.call(0x71027d2150,[M+0x320])
 got=bytes(h.mu.mem_read(M+0x3c0,0x500));want=bytearray(old)
 for i in range(80):struct.pack_into('<I',want,16*i+8,0xffffffff)
 assert got==want,(z,'keys-only reset');assert h.r64(M+0x3b8)==0
# Native dispatcher registration, synthetic dispatcher-level lock only.
D=h.alloc(0x80);lock=h.alloc(0x40);lvt=h.alloc(0x50);node=h.alloc(0x80);tree=h.alloc(0x40);P=h.alloc(0x90);typ=h.alloc(8)
h.w64(lock,lvt)
for off in [0x18,0x28,0x30,0x40]:h.w64(lvt+off,0x7100f79498)
h.w64(D+0x58,lock);h.w64(D+0x20,node);h.w32(D+0x30,1);h.w64(D+0x40,tree);h.w32(D+0x54,1)
h.call(0x7100f3de98,[D,M+0x2f8]);assert h.r32(D+0x18)==1 and h.r64(D+0x38)==tree and h.r64(tree+0x20)==key
h.w64(0x7105801908,D);h.w64(P+0x78,typ)
for z in range(256):
 h.mu.mem_write(M+0x3c0,b'\xa5'*0x500);h.w32(typ,[0,1,2,3,0xffffffff,0x80000000][z%6]);sp=h.mu.reg_read(UC_ARM64_REG_SP)
 h.mu.reg_write(UC_ARM64_REG_X0,P);h.mu.emu_start(0x7102d53a3c,0x7102d53a90,count=100000)
 h.mu.reg_write(UC_ARM64_REG_SP,sp)
 assert all(h.r32(M+0x3c8+16*i)==0xffffffff for i in range(80))
out={'constructor_cells':80,'constructor_bytes_matched':1280,'reset_cases':cases,'reset_key_checks':cases*80,'actual_reset_broadcast_cases':256,'actual_register':'0f3de98','actual_broadcast':'2d53a3c..2d53a90→1323ea8→27d2150→16e48c8','mismatch':0,'native_ctor_blocks':['27cdff8..27ce044','27ce054..27ce42c'],'native_full':['2d550c4','27d2150','16e48c8','3c837c8'],'reset_type_key':hex(key),'SDK_stubs':dict(h.sdklog),'non_SDK_stubs':dict(h.stublog),'scope':'synthetic manager; empty bullet feedback list and12 invalid actor refs; synthetic dispatcher-level lock invokes original RET; original node mutex SDK-init boundary; full Scene/process startup and menu reset triggers excluded; ctor native stores and actual member-thunk reset executed'}
(ROOT/'analysis/completion/r8/combat_critical_lifecycle_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
