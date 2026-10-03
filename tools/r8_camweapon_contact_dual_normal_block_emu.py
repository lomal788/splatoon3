"""Original0a181fc dual-body normal block, actual kinematic floor+mass100/inertia0 human fixture.
0a18d8c..0a1911c finite ordered f32 comparison; no callable/PLT substitution.
Generic4lane,friction,rotation,TOI excluded. Kinematic prescribed velocities are varied.
"""
import json,struct,random,math
from pathlib import Path
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r6_player_uc import BASE
j=json.loads(Path('analysis/completion/r8/physics_kinematic_kernel_fixture.json').read_text(encoding='utf8'));p=json.loads(Path('analysis/completion/r8/contact_dual_kernel_replay.json').read_text(encoding='utf8'));s=p['samples'][0];u=PhysicsUC();mu=u.mu
for k in ['heap','stack','bss']:mu.mem_write(j[k+'_base'],Path('analysis/completion/r8/physics_kinematic_kernel_'+k+'.bin').read_bytes())
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bit(x):return struct.pack('<f',x).hex()
def qp(i,a):mu.reg_write(globals()['UC_ARM64_REG_Q'+str(i)],int.from_bytes(struct.pack('<4f',*a),'little'))
def qg(i):return struct.unpack('<4f',mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]).to_bytes(16,'little'))
sp=j['regs']['sp']-0x4000;row=s['regs']['x12']-0x10;lp=s['regs']['x11'];rng=random.Random(18881911)
def restore():
 for k,v in s['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
 for k,v in s['qs'].items():
  # Original lanes containing NaN are scratch outside the compared normal inputs.
  qp(int(k[1:]),v)
 mu.reg_write(UC_ARM64_REG_FPCR,j['regs']['fpcr']);mu.reg_write(UC_ARM64_REG_SP,sp);mu.mem_write(sp+0x3cc0,bytes.fromhex(s['stack']))
def ref(LA,LB,WA,WB,N,JA,JB,IA,IB,lam,target):
 r=[]
 for i in range(3):
  v=f(f(LA[i]-LB[i])*N[i]);a=f(f(WA[i]*JA[i])+f(WB[i]*JB[i]));r.append(f(v+a))
 dot=f(f(r[0]+r[1])+r[2]);skip=dot>=target and lam==0
 d=0. if skip else max(f(-lam),f(f(target-dot)*JA[3]));new=f(lam+d)
 if skip:return LA,LB,WA,WB,new,d,dot,skip
 da=f(d*IA[3]);db=f(d*IB[3])
 oa=[f(LA[i]+f(N[i]*da)) for i in range(4)];ob=[f(LB[i]-f(N[i]*db)) for i in range(4)]
 wa=[f(WA[i]+f(f(d*IA[i])*JA[i])) for i in range(4)];wb=[f(WB[i]+f(f(d*IB[i])*JB[i])) for i in range(4)]
 return oa,ob,wa,wb,new,d,dot,skip
fields=0;cases=0;skipcount=0;clamp=0;fixtures=[]
for n in range(4097):
 restore()
 if n==0:
  LA=s['qs']['q2'];LB=s['qs']['q3'];WA=list(struct.unpack('<4f',bytes.fromhex(s['stack'])[:16]));WB=list(struct.unpack('<4f',bytes.fromhex(s['stack'])[16:32]));R=struct.unpack('<8f',bytes.fromhex(s['row']));JA=list(R[:4]);JB=list(R[4:]);IA=s['qs']['q7'];IB=s['qs']['q16'];N=[0.,-1.,0.,f(1.8374686479671624e19)];lam=s['lambda_value'];target=JB[3]
 else:
  v=[rng.uniform(-1,1) for i in range(3)];le=math.sqrt(sum(i*i for i in v));N=[f(i/le) for i in v]+[0.];LA=[f(rng.uniform(-8,8)) for i in range(3)]+[0.];LB=[f(rng.uniform(-8,8)) for i in range(3)]+[0.];WA=WB=[0.,0.,0.,0.];IA=[0.,0.,0.,0.];IB=[0.,0.,0.,f(.010009765625)];JA=[0.,0.,0.,f(99.90243530273438)];target=f(rng.uniform(-8,8));JB=[0.,0.,0.,target];lam=0. if n%3==0 else f(rng.uniform(0,4000))
 qp(2,LA);qp(3,LB);qp(7,IA);qp(16,IB);qp(1,[0.]*4);qp(0,[-1.,-1.,0.,0.]);mu.mem_write(sp+0x3cc0,struct.pack('<8f',*WA,*WB));mu.mem_write(sp+0x3d70,struct.pack('<2f',0.,0.));mu.mem_write(row,struct.pack('<8f',*JA,*JB));mu.mem_write(s['regs']['x22']+0x10,struct.pack('<4f',*N));u.wf(lp,lam)
 mu.emu_start(BASE+0xa18d8c,BASE+0xa1911c,count=2000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa1911c,hex(mu.reg_read(UC_ARM64_REG_PC))
 oa,ob,wa,wb,nl,d,dot,skip=ref(LA,LB,WA,WB,N,JA,JB,IA,IB,lam,target);got=[*qg(2),*qg(3),*struct.unpack('<8f',mu.mem_read(sp+0x3cc0,32)),u.rf(lp),*struct.unpack('<2f',mu.mem_read(sp+0x3d70,8))];want=[*oa,*ob,*wa,*wb,nl,d,d]
 assert [bit(v) for v in got]==[bit(v) for v in want],(n,got,want,LA,LB,WA,WB,N,JA,JB,lam,target,dot,skip)
 cases+=1;fields+=len(got);skipcount+=int(skip);clamp+=int(not skip and bit(d)==bit(f(-lam)))
 if n<4:fixtures.append(dict(linearA=LA,linearB=LB,angularA=WA,angularB=WB,normal=N,invA=IA,invB=IB,rowA=JA,rowB=JB,lambda_old=lam,target=target,dot=dot,delta=d,lambda_new=got[16],output=got,skip=skip))
 assert not u.null_calls and not u.auto_pages and not u.faults
out=dict(cases=cases,fields=fields,mismatches=0,skipped=skipcount,lowerclamp=clamp,block='0a18d8c..0a1911c',actual_fixture=fixtures[0],fixture=fixtures,scope=__doc__,null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r8/contact_dual_normal_block_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
