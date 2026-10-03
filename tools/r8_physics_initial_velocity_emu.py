"""Whole original09d4ba8 solver initial velocities/baseline, independent finite gravity+velocity equation; synthetic motion arrays, no modifiers."""
import json,random,struct
from pathlib import Path
import numpy as np
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();CTX=u.alloc(0x80);P=u.alloc(0x150);MOD=u.alloc(0x1000);I=u.alloc(0x100);G=u.alloc(0x10);M=u.alloc(0x100);ID=u.alloc(8);C=u.alloc(0x20);B=u.alloc(0x20)
u.wq(CTX+0x30,P);u.wq(CTX+0x40,MOD);u.w32(ID,1);rng=random.Random(0x9d4ba8);bad=[];errors=[];samples=[]
for i in range(1024):
 vel=[np.float32(rng.uniform(-200,200)) for j in range(3)];ang=[np.float32(rng.uniform(-10,10)) for j in range(3)];gravity=[np.float32(rng.uniform(-30,30)) for j in range(3)];scale=np.float32(rng.choice([0.,1.,2.9387755,-1.,.5]));massbits=0 if i%5==0 else 0x3c24
 if i==0:massbits=0x3c24;vel=[np.float32(x) for x in (0,-3,0)];ang=[np.float32(0.)]*3;gravity=[np.float32(x) for x in (0,-9.81,0)];scale=np.float32(1.)
 u.call(0x7100a4517c,I);u.call(0x7100a452fc,I,fargs=(.6,1.))
 for j,v in enumerate(gravity):u.wf(G+j*4,float(v))
 error=u.call(0x7100a4536c,I,G,8,1,fargs=(1/60,1/60))
 if error:errors.append(dict(i=i,at='info',error=error));break
 u.wf(P+0x70+8,float(scale));u.mu.mem_write(M+0x80,b'\0'*0x80);u.mu.mem_write(M+0x80+0x58,struct.pack('<3H',1,0,0x4348));u.mu.mem_write(M+0x80+0x46,struct.pack('<H',massbits))
 for j in range(3):u.wf(M+0x80+0x60+j*4,float(vel[j]));u.wf(M+0x80+0x70+j*4,float(ang[j]))
 u.mu.mem_write(C,b'\xff'*32);u.mu.mem_write(B,b'\xff'*32)
 error=u.call(0x71009d4ba8,CTX,I,M,ID,1,C,B)
 if error:errors.append(dict(i=i,at='init',error=error));break
 gs=[np.float32(u.rf(I+0x90+j*4)) for j in range(3)];dv=[np.float32(gs[j]*scale) if massbits else np.float32(0.) for j in range(3)];out=[np.float32(vel[j]+dv[j]) for j in range(3)]
 expectedcur=struct.pack('<6f',*ang,out[2],out[0],out[1]);expectedbase=b'\0'*24
 gotcur=bytes(u.mu.mem_read(C,24));gotbase=bytes(u.mu.mem_read(B,24))
 if gotcur!=expectedcur or gotbase!=expectedbase:bad.append(dict(i=i,cur=gotcur.hex(),want_cur=expectedcur.hex(),base=gotbase.hex(),want_base=expectedbase.hex()))
 if i<3:samples.append(dict(i=i,vel=[float(x) for x in vel],gravity=[float(x) for x in gravity],scale=float(scale),massbits=massbits,out=struct.unpack('<6f',gotcur),baseline=struct.unpack('<6f',gotbase)))
r=dict(cases=i+1,f32_fields=12*(i+1),mismatch=bad,errors=errors,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__)
Path('analysis/completion/r8/physics_initial_velocity_emu.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k not in ('samples','mismatch')},ensure_ascii=False));print('mismatch',len(bad),bad[:2])
