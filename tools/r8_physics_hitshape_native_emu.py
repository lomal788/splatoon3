"""Original entire PlayerCollision24f5dd8 ordinary single-player capsule morph -> actualCapsuleVT A0 native regeneration3a6aef4/0930b40 or092efbc/backend replace. No shape RTTI or arithmetic callbacks stubbed; body observer list empty."""
import json,random,struct
from pathlib import Path
import numpy as np
from r8_physics_native_uc import init_native
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
u,init_errors=init_native();PC=u.alloc(0xe500);B=u.alloc(0xb000);Owner=u.alloc(0x200);G=u.alloc(0x200);World=u.alloc(0x500)
u.wq(0x710599dfa8,G);u.wq(G+0xe8,World);u.wf(World+0x21c,.05)
u.wq(PC+0xe3a8,Owner);u.wq(Owner+0x108,B);u.wq(Owner+0xf0,Owner+0xe8)
Input=u.alloc(0x800);u.wq(B+8,Input)
for off,size in ((0xa7c0,0xf00),(0xa8c8,0x100),(0xa8c0,0x1100),(0xa6d8,0x100),(0xa880,0x100),(0xa6c0,0x2700)):
 p=u.alloc(size);u.wq(B+off,p)
u.w32(u.rq(B+0xa6d8)+0x88,0xffffffff)
for off,size in ((0xe378,0x1800),(0xe398,0x100),(0xe388,0x500),(0xe390,0x300)):
 u.wq(PC+off,u.alloc(size))
W=u.alloc(0x20);C=u.alloc(0x40);Body=u.alloc(0x400);Filter=u.alloc(0x40);Stage=u.alloc(0xd8)
u.wq(PC+0xe3b8,W);u.wq(W+8,C);u.wq(C+0x18,Body);u.wq(Body,0x71057468d8);u.wq(Body+0x180,Filter);u.wq(Body+0x80,Stage);u.wq(Body+0x88,4)
RT=u.alloc(4);VT=u.alloc(0x20);u.mu.mem_write(RT,struct.pack('<I',0xd65f03c0));u.wq(VT,RT)
def rtti(mu,a,size,data):mu.reg_write(UC_ARM64_REG_X0,1);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
# ActualCapsuleVT IsA executes; no RTTI hook
Caps=[]
for off in (0x48,0x58):
 body=u.alloc(0x400);cap=u.alloc(0x100);Caps.append(cap);u.wq(PC+off,body);u.wq(body+0x28,cap);u.wq(cap,0x7105745788);u.wq(cap+0x58,cap+0x58);u.wq(cap+0x60,cap+0x58)
u.mu.mem_write(Caps[0]+0xd8,struct.pack('<7f',0,.35,0,0,1.3,0,.35));u.mu.mem_write(Caps[1]+0xd8,struct.pack('<7f',0,.9,.4,0,.9,.4,1.15))
for cap in Caps:
 desc=u.alloc(0x40);u.mu.mem_write(desc+0x20,bytes(u.mu.mem_read(cap+0xd8,28)))
 init_errors.append(['backend',u.call(0x7103c243dc,desc,0)]);u.wq(cap+0xf8,u.x(0));init_errors.append(['nativeOwnerBind',u.call(0x7103c27858,u.rq(cap+0xf8),cap)])
u.w8(0x71058bbb9a,0);f=np.float32;rng=random.Random(0x8f5dd8);mismatch=[];samples=[]
inputs=[f(0),f(1),f(0)] + [f(k/10) for k in range(11)] + [f(rng.random()) for i in range(1000)]
native_fields=0;metadata_fields=0
old=f(0);expected=bytes(u.mu.mem_read(Caps[0]+0xd8,28));zold=bytes(u.mu.mem_read(Caps[1]+0xd8,28));cache=[]
for i,t in enumerate(inputs):
 same=(abs(t)<=f(2**-23) or abs(f(t-f(1)))<=f(2**-23))
 changed=(old!=t) if same else not (-f(.2)<=f(old-t)<=f(.2))
 if changed:
  old=t;r=f(f(.35)+f(f(f(.8)-f(.35))*t));height=f(f(1.65)+f(f(-f(1.65))*t))
  a=f(height*f(.5)) if height<=f(r+r) else r;b=a if height<=f(r+r) else f(height-r)
  expected=struct.pack('<7f',0.,a,0.,0.,b,0.,r)
  yy=f(f(.9)+f(t*f(.100000024)));zz=f(f(.4)-f(t*f(.4)));zold=struct.pack('<7f',0.,yy,zz,0.,yy,zz,1.15)
 error=u.call(0x71024f5dd8,PC,0,fargs=(float(t),0.))
 for label,cap,expect in zip(('colbullet','chariot'),Caps,(expected,zold)):
  native=u.rq(u.rq(cap+0xf8)+8);kind=u.r8(native+0x18);off=struct.unpack('<i',u.mu.mem_read(native+0x40,4))[0];verts=native+0x40+off
  expectedv=struct.unpack('<7f',expect);ev=list(expectedv[:3]) if expectedv[:3]==expectedv[3:6] else list(expectedv[:6]);actual=bytes(u.mu.mem_read(verts,len(ev)*4));rad=bytes(u.mu.mem_read(native+0x20,4));typ=1 if len(ev)==3 else 2
  native_fields+=len(ev)+1;metadata_fields+=3
  if u.r32(native+0x44)!=len(ev)//3:mismatch.append(dict(i=i,label='native vertex count',actual=u.r32(native+0x44),expected=len(ev)//3))
  if actual!=struct.pack('<'+'f'*len(ev),*ev) or rad!=expect[24:28] or kind!=typ or u.rq(native+0x28)!=cap:mismatch.append(dict(i=i,label='native '+label,kind=kind,expected_kind=typ,got=actual.hex(),expected=struct.pack('<'+'f'*len(ev),*ev).hex(),radius=rad.hex(),expected_radius=expect[24:28].hex(),owner=hex(u.rq(native+0x28))))
 got=bytes(u.mu.mem_read(Caps[0]+0xd8,28));zg=bytes(u.mu.mem_read(Caps[1]+0xd8,28));ct=u.rf(PC+0x16c)
 if error or got!=expected or zg!=zold or struct.pack('<f',ct)!=struct.pack('<f',old):mismatch.append(dict(i=i,t=float(t),error=error,cache=ct,expected_cache=float(old),got=got.hex(),expected=expected.hex(),zg=zg.hex(),ze=zold.hex()))
 if i<14:samples.append(dict(i=i,t=float(t),cache=ct,colbullet=struct.unpack('<7f',got),chariot=struct.unpack('<7f',zg)))
 cache.append(ct)
r=dict(init_errors=init_errors,cases=len(inputs),fields=len(inputs)*15+native_fields,native_f32_fields=native_fields,metadata_fields=metadata_fields,mismatch=mismatch,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__,cache=cache,unverified=['native body shape-change notification: fixture referencedBody list empty','special/sub actual behavior','nonordinary size overrides'])
Path('analysis/completion/r8/physics_hitshape_native_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(dict(cases=r['cases'],fields=r['fields'],native_f32_fields=native_fields,metadata_fields=metadata_fields,mismatch_count=len(mismatch),mismatch=mismatch[:3],samples=samples[:3],null=r['null'],auto=r['auto'],faults=r['faults']),ensure_ascii=False))
