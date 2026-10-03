"""Original0a15b70 dual-body effectiveMass and cached-depth bias completed blocks.
Actual native kinematic floor/human fixture; finite independent ordered f32 math.
"""
import json,struct,random
from pathlib import Path
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r6_player_uc import BASE
j=json.loads(Path('analysis/completion/r8/physics_kinematic_kernel_fixture.json').read_text(encoding='utf8'));p=json.loads(Path('analysis/completion/r8/contact_dual_bias_producer.json').read_text(encoding='utf8'));u=PhysicsUC();mu=u.mu
for k in ['heap','stack','bss']:mu.mem_write(j[k+'_base'],Path('analysis/completion/r8/physics_kinematic_kernel_'+k+'.bin').read_bytes())
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bit(x):return struct.pack('<f',x).hex()
def qp(i,a):mu.reg_write(globals()['UC_ARM64_REG_Q'+str(i)],int.from_bytes(struct.pack('<4f',*a),'little'))
def qg(i):return struct.unpack('<4f',mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]).to_bytes(16,'little'))
def restore(s):
 for k,v in s['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
 for k,v in s['qs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],int(v,16))
 mu.reg_write(UC_ARM64_REG_FPCR,j['regs']['fpcr'])
def nz(x):return bit(x)=='00000080'
def mn(a,b):return (-0. if nz(a) or nz(b) else 0.) if a==0 and b==0 else min(a,b)
def mx(a,b):return (-0. if nz(a) and nz(b) else 0.) if a==0 and b==0 else max(a,b)
ms=next(s for s in p['samples'] if s['pc']=='0x7100a165a0');bs=next(s for s in p['samples'] if s['pc']=='0x7100a16670');rng=random.Random(16516670)
for n in range(1024):
 restore(ms);x=ms['regs'];A=[f(rng.uniform(-1,1)) for i in range(3)]+[0.];B=[f(rng.uniform(-1,1)) for i in range(3)]+[0.];IA=[0.,0.,0.,0.];IB=[0.,0.,0.,f(.010009765625)];qp(3,A);qp(0,B);mu.mem_write(x['x20'],struct.pack('<8f',*IA,*IB));mu.emu_start(BASE+0xa165a0,BASE+0xa165ec,count=1000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa165ec
 w=[f(f(IA[i]*f(A[i]*A[i]))+f(IB[i]*f(B[i]*B[i]))) for i in range(3)]+[f(IA[3]+IB[3])];den=f(f(w[0]+w[1])+f(w[2]+w[3]));M=f(u.rf(x['x19']+8)/den);assert bit(qg(3)[3])==bit(M);assert bit(u.rf(x['x10']+0xc))==bit(M)
def ref(old,carry,d,v,flag,pred,k,c0,dt,gamma,ratio,threshold):
 p=carry if flag else f(carry+f(v*pred));cap=f(dt*c0)
 if old>=threshold and d>f(p-cap):return old,d,f(d*f(-gamma)),True
 t=mx(0.,mn(f(d*k),cap));b=t if flag else mn(f(old*k),cap);diff=f(d-old);p=f(mn(p,0.)-diff);limit=f(cap+f(ratio*b));sel=p if p>limit else 0.;newold=f(f(old+b)-sel);newcarry=f(f(diff-b)+sel);stored=mn(mx(newold,f(d-b)),threshold);return stored,newcarry,f(newcarry*f(-gamma)),False
x=bs['regs'];threshold=struct.unpack('<4f',int(bs['qs']['q1'],16).to_bytes(16,'little'))[0];earlycount=0;fixtures=[]
for n in range(4097):
 restore(bs)
 if n==0:old=0.;carry=0.;d=f(-.15000003576278687);v=0.;flag=1;pred=0.
 else:old=f(rng.uniform(-.3,.3));carry=f(rng.uniform(-.2,.2));d=f(rng.uniform(-.3,.3));v=f(rng.uniform(-4,4));flag=n&1;pred=0. if n%3==0 else f(rng.uniform(0,1/30))
 dt=f(1/60);k=f(-.05);c0=1.;gamma=288.;ratio=2.;mu.reg_write(UC_ARM64_REG_X9,flag);mu.reg_write(UC_ARM64_REG_Q4,0 if flag else (1<<64)-1);qp(0,[0.]*4);qp(3,[v,v,0.,0.]);qp(6,[dt,dt,0.,0.]);qp(7,[carry,carry,0.,0.]);qp(8,[0.]*4);qp(17,[c0,c0,0.,0.]);qp(2,[ratio,ratio,0.,0.]);u.wf(x['x15']+x['x12'],old);u.wf(x['x14']+x['x12'],carry);u.wf(x['x13']+0x30,d);mu.mem_write(x['x19']+0x20,struct.pack('<2f',pred,pred));mu.mem_write(x['x19']+0xd0,struct.pack('<2f',gamma,gamma));mu.mem_write(x['x21']+0xc8,struct.pack('<2f',k,k))
 mu.emu_start(BASE+0xa16670,BASE+0xa17548,count=1000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa17548,hex(mu.reg_read(UC_ARM64_REG_PC))
 a,b,c,early=ref(old,carry,d,v,flag,pred,k,c0,dt,gamma,ratio,threshold);got=[u.rf(x['x15']+x['x12']),u.rf(x['x14']+x['x12']),*struct.unpack('<4f',mu.mem_read(x['x10']+0x10,16))];want=[a,b,0.,0.,0.,c];assert [bit(i) for i in got]==[bit(i) for i in want],(n,got,want,old,carry,d,v,flag,pred,early);earlycount+=early
 if n<4:fixtures.append(dict(old=old,carry=carry,depth=d,velocity=v,flag=flag,predict=pred,stored=got[0],newcarry=got[1],target=got[5],early=early))
 assert not u.null_calls and not u.auto_pages and not u.faults
out=dict(mass_cases=1024,mass_fields=2048,bias_cases=4097,bias_fields=24582,mismatches=0,early_branch=earlycount,massblock='0a165a0..0a165ec',biasblock='0a16670..0a17548',actual_fixture=fixtures[0],fixtures=fixtures,scope=__doc__,boundary='original flags/c0=1/c8=-.05;finite varying cachedDepth/carry/currentDepth/w9flag/projectedVelocity;highlevel w9/name/quality not invented;inertia0 friction0;genericfriction/rotation/TOI excluded',null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r8/contact_dual_bias_block_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
