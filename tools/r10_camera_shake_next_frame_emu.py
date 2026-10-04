"""New r10 original frame constructor and render-target binding contracts.

Synthetic clock/texture manager graphs. Original code is never patched.
NVN SetRenderTargets and transition helpers are captured boundaries; this is
not a scene, boot, driver allocation, fullscreen draw or final display test.
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
ns = {'__file__': str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf8').split('\nh=H(')[0], ns)
H,R = ns['H'],ns['R']; B = R.BASE; F = np.float32
REGS = [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5]
class E(H):
    def _block(self, mu, pc, size, user):
        if pc == B+0x3e9a3d0:
            self.tick_calls += 1
            mu.reg_write(UC_ARM64_REG_X0, self.tick+self.tick_calls)
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR)); return
        if pc in self.capture:
            label = self.capture[pc]
            values = [mu.reg_read(r) for r in REGS]
            self.events.append((label, values)); self.captured[label] += 1
            if label == 'SetRenderTargets':
                n = values[1]
                self.bound = {
                    'cmd': values[0], 'count': n,
                    'textures': list(struct.unpack('<'+'Q'*n,mu.mem_read(values[2],8*n))),
                    'views': list(struct.unpack('<'+'Q'*n,mu.mem_read(values[3],8*n))),
                    'depth': values[4], 'depth_view': values[5]}
            mu.reg_write(UC_ARM64_REG_X0,0)
            mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR)); return
        super()._block(mu, pc, size, user)
e = E([B+0x3501dbc,B+0x35a83f4]); e.executed=set();e.sdklog=Counter();e.stublog=Counter()
e.capture={};e.captured=Counter();e.events=[];e.tick=0;e.tick_calls=0
def no_null(mu,access,a,size,value,user):
    if a<0x400000:raise RuntimeError(f'null read {a:#x} at {mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
obj=e.alloc(0x400);params=e.alloc(0x50); ctor=0
for fps in [0,1,2,30,60,120,255,0xffffffff]:
    for tick in [0,19200000,0x123456789,0x7fffffff]:
        raw=bytearray(bytes(range(0x50)));struct.pack_into('<I',raw,0,fps)
        e.mu.mem_write(params,bytes(raw));e.mu.mem_write(obj,b'\xa5'*0x400)
        e.tick=tick;e.tick_calls=0;e.w64(B+0x5997960,19200000)
        e.call(B+0x3501dbc,[obj,params]);assert e.tick_calls==3
        assert e.r64(obj)==B+0x571eed8
        assert bytes(e.mu.mem_read(obj+0x88,0x50))==bytes(raw)
        assert bytes(e.mu.mem_read(obj+0x220,4))==bytes([1,0,0,1])
        assert e.r64(obj+0x140)==0 and e.r64(obj+0x1e8)==0
        assert [e.r64(obj+x) for x in [0xe0,0x120,0x128]]==[tick+1,tick+2,tick+3]
        # Original order: signed tick-frequency -> f32; FOV/time-like constants
        # are preserved as their original immediate f32 bit patterns.
        expected=[0,0]
        if fps:
            freq=F(19200000); rate=F(F(60)/F(fps))
            c0=F(struct.unpack('<f',struct.pack('<I',0x3f7c28f6))[0])
            c1=F(struct.unpack('<f',struct.pack('<I',0x3bc49ba6))[0])
            expected=[int(F(F(c0/rate)*freq)),int(F(F(c1/rate)*freq))]
        assert [e.r64(obj+x) for x in [0x130,0x138]]==expected
        ctor+=1

api=e.alloc(8);e.capture[api]='SetRenderTargets';e.w64(B+0x57d61d8,api)
e.capture[B+0x3594120]='color_transition';e.capture[B+0x3594350]='depth_transition'
target=e.alloc(0x70);draw=e.alloc(0x120);cmd=e.alloc(8);e.w64(draw+0xb8,cmd)
manager=e.alloc(0x640);table=e.alloc(0x300);e.w64(B+0x59979f8,manager)
e.w32(manager+0x390,16);e.w64(manager+0x398,table);e.mu.mem_write(manager+0x402,struct.pack('<H',10))
textures=[];handles=[]
for i in range(9):
    texture=e.alloc(0x100);handle=e.alloc(8);textures.append(texture);handles.append(handle)
    e.w64(table+i*0x20+0x18,handle);e.w32(texture+0x60,10+i);e.w32(texture+0xc8,0)
bind=0
for mask in [0,1,2,3,0x80,0xff,0x55,0xaa]:
    for invalid_last in [False,True]:
        for depth in [False,True]:
            e.mu.mem_write(target,b'\0'*0x70)
            for i in range(8):e.w64(target+0x20+i*8,textures[i] if mask>>i&1 else 0)
            e.w32(textures[7]+0x60,0xffffffff if invalid_last else 17)
            e.w64(target+0x60,textures[8] if depth else 0);e.events=[];e.bound=None
            e.call(B+0x35a83f4,[target,draw])
            slots=[i for i in range(8) if mask>>i&1 and not(invalid_last and i==7)]
            n=slots[-1]+1 if slots else 0
            expected={'cmd':cmd,'count':n,
                'textures':[handles[i] if i in slots else 0 for i in range(n)],
                'views':[textures[i]+0xb8 if i in slots else 0 for i in range(n)],
                'depth':handles[8] if depth else 0,
                'depth_view':textures[8]+0xb8 if depth else 0}
            assert e.bound==expected,(mask,invalid_last,depth,e.bound,expected)
            assert e.r64(draw+0xf0)==target
            assert e.events[0][0]=='SetRenderTargets'
            assert [v[0] for v in e.events].count('color_transition')==sum(i in slots for i in range(8))
            assert [v[0] for v in e.events].count('depth_transition')==int(depth)
            bind+=1
out={'total':ctor+bind,'constructor_cases':ctor,'target_bind_cases':bind,'mismatches':0,
    'original_functions':['0x7103501dbc','0x71035a83f4'],
    'captured_boundaries':dict(e.captured), 'clock_calls':ctor*3,
    'SDK_stubs':dict(e.sdklog),'non_SDK_stubs':{hex(k):v for k,v in e.stublog.items()},
    'supplied_globals':['5997960 tick frequency19200000','59979f8 synthetic texture manager/handles'],
    'scope':'New whole original constructor/SetRenderTargets adapter. Clock and texture transition/NVN API boundaries supplied. No live nnMain full boot, driver allocation, texture contents, HDR draw or final physical display.'}
(ROOT/'analysis/camera_100_r10/posture/next_frame_native.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
