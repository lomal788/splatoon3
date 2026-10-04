"""Original viewport/scissor wrapper and actual present gates.

Original game instructions execute; NVN calls are captured API boundaries.
Synthetic positive rectangles/postures/window state do not prove native driver
swizzle defaults, platform posture, or actual Lby framebuffer presentation.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R'];B=R.BASE;F=np.float32
def packf(v):return struct.pack('<'+'f'*len(v),*map(float,v))
class E(H):
    def _block(self,mu,pc,size,user):
        if pc in self.nvn:
            a=[mu.reg_read(r) for r in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4]]
            s=[mu.reg_read(r)&0xffffffff for r in [UC_ARM64_REG_S0,UC_ARM64_REG_S1]]
            self.events.append({'api':self.nvn[pc],'x':a,'s':s})
            self.capture_count[self.nvn[pc]]+=1
            mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
        super()._block(mu,pc,size,user)
e=E([B+0x358b9d0]);e.executed=set();e.sdklog=Counter();e.stublog=Counter();e.capture_count=Counter();e.events=[];e.nvn={}
def no_null(mu,access,a,size,value,user):
    if a<0x400000:raise RuntimeError(f'null read {a:#x} at {mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
for cell,name in [(0x57d6090,'nvnCommandBufferSetScissor'),(0x57d6078,'nvnCommandBufferSetViewport'),(0x57d60a0,'nvnCommandBufferSetDepthRange'),(0x57d5538,'nvnQueuePresentTexture'),(0x57d55b8,'nvnWindowAcquireTexture')]:
    pc=e.alloc(8);e.nvn[pc]=name;e.w64(B+cell,pc)
callback=e.alloc(8);e.nvn[callback]='optional_present_callback'
rect=e.alloc(0x40);target=e.alloc(0x30);draw=e.alloc(0xc0);cmd=e.alloc(0x20);e.w64(draw+0xb8,cmd)
depth=packf([.125,.875]);e.mu.mem_write(rect+0x1c,depth)
viewport_cases=0;examples=[]
for tw,th,px,py,pw,ph in [(1280,720,0,0,1280,720),(1280,720,17,31,1920,1080),(720,1280,0,0,720,1280)]:
    e.mu.mem_write(target+8,packf([tw,th,px,py,px+pw,py+ph]))
    for l,t,r,b in [(0,0,tw,th),(13.25,11.5,200.75,150.125),(10,20,10,20)]:
        for posture in [0,1,2,3,4,5,6,0xffffffff]:
            e.mu.mem_write(rect+8,packf([l,t,r,b]));e.w32(rect+0x18,posture);e.events=[]
            e.call(B+0x358b9d0,[rect,draw,target])
            w=F(F(r)-F(l));h=F(F(b)-F(t));x=F(l);y=F(t)
            if posture==1:x=F(t);y=F(F(F(th)-w)-F(l))
            elif posture==2:x=F(F(F(tw)-h)-F(t));y=F(l)
            elif posture==3:x=F(F(F(tw)-w)-F(l));y=F(F(F(th)-h)-F(t))
            elif posture==4:x=F(F(F(tw)-w)-F(l))
            elif posture==5:y=F(F(F(th)-h)-F(t))
            x=F(F(F(x/F(tw))*F(pw))+F(px));y=F(F(F(y/F(th))*F(ph))+F(py))
            if posture in [1,2]:w,h=h,w
            w=F(F(w/F(tw))*F(pw));h=F(F(h/F(th))*F(ph))
            y=F(F(F(ph)-h)-y);xi=int(x);yi=int(y)
            wi=max(0,int(F(F(w+x)-F(xi))));hi=max(0,int(F(F(h+y)-F(yi))))
            expected=[cmd,xi&0xffffffff,yi&0xffffffff,wi,hi]
            assert len(e.events)==3
            assert [z['api'] for z in e.events]==['nvnCommandBufferSetScissor','nvnCommandBufferSetViewport','nvnCommandBufferSetDepthRange']
            assert e.events[0]['x']==expected and e.events[1]['x']==expected,(posture,e.events,expected)
            assert e.events[2]['x'][0]==cmd
            assert struct.pack('<II',*e.events[2]['s'])==depth
            if l==0 and tw==1280 and px==0:examples.append({'posture':posture,'viewport':expected[1:]})
            viewport_cases+=1

# Whole original present wrapper, actual gate/optional callback/acquire order.
obj=e.alloc(0x230);window=e.alloc(0x70);device=e.alloc(0x90);queue=e.alloc(8);winhandle=e.alloc(8);image=e.alloc(8)
e.w64(B+0x59978a0,device);e.w64(device+0x38,queue);e.w64(obj+0x140,window)
e.w64(window+0x18,winhandle);e.w64(window+0x20,image);e.w32(window+0x28,19)
present_cases=0
present_functions=[B+0x3503410,e.r64(B+0x55552c8+0x100)]
assert present_functions[1]==B+0x3d98c6c
for entry in present_functions:
    for state in [0,1,2,3,0xffffffff]:
        for enabled in [0,1]:
            for deferred in [0,1]:
                for cb in [0,1]:
                    e.w32(obj+0x50,state);e.mu.mem_write(window+0x10,bytes([enabled]));e.mu.mem_write(obj+0xa6,bytes([deferred]));e.w64(obj+0x158,callback if cb else 0);e.events=[]
                    e.call(entry,[obj])
                    names=[z['api'] for z in e.events]
                    expected=[]
                    if state==2 and enabled:
                        if cb:expected.append('optional_present_callback')
                        expected.append('nvnQueuePresentTexture')
                        if not deferred:expected.append('nvnWindowAcquireTexture')
                    assert names==expected,(entry,state,enabled,deferred,cb,names,expected)
                    for z in e.events:
                        if z['api']=='nvnQueuePresentTexture':assert z['x'][:3]==[queue,winhandle,19]
                        if z['api']=='nvnWindowAcquireTexture':assert z['x'][:3]==[winhandle,image,window+0x28]
                    present_cases+=1
out={'total':viewport_cases+present_cases,'viewport_cases':viewport_cases,'present_cases':present_cases,'present_functions':[hex(fn) for fn in present_functions],'mismatches':0,'native_api_captures':dict(e.capture_count),'SDK_stubs':dict(e.sdklog),'non_SDK_stubs':{hex(k):v for k,v in e.stublog.items()},'full_rectangle_examples':examples,'scope':'Original358b9d0+358baf4 rectangle arithmetic/API order and whole3503410+actualVT55552c8/100=3d98c6c present gate. Native NVN calls captured, no driver/GPU/swizzle default/output texture provenance or actual Lby Scene execution.'}
(ROOT/'analysis/camera_100_r10/posture/viewport_native.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
