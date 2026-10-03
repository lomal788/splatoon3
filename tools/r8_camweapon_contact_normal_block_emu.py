"""r8 original single-body normal-impulse block vs ordered f32 reference.
Block0a1a98c..0a1abd0, no callable boundary. Actual live kernel fixture plus finite perturbed inputs.
Does not claim generic4lane/friction/restitution/TOI whole solver verification.
"""
import json,struct,random,math
from pathlib import Path
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r6_player_uc import BASE
j=json.loads(Path('analysis/completion/r8/physics_kernel_fixture.json').read_text(encoding='utf8'));p=json.loads(Path('analysis/completion/r8/contact_kernel_replay.json').read_text(encoding='utf8'));s=p['samples'][0];u=PhysicsUC();mu=u.mu
for k,file in [('heap','physics_kernel_heap.bin'),('stack','physics_kernel_stack.bin'),('bss','physics_kernel_bss.bin')]:mu.mem_write(j[k+'_base'],Path('analysis/completion/r8/'+file).read_bytes())
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bits(x):return struct.pack('<f',x).hex()
def putq(i,a):mu.reg_write(globals()['UC_ARM64_REG_Q'+str(i)],int.from_bytes(struct.pack('<4f',*a),'little'))
def getq(i):return struct.unpack('<4f',mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]).to_bytes(16,'little'))
def restore():
 for k,v in s['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
 for k,v in s['qs'].items():putq(int(k[1:]),v)
 mu.reg_write(UC_ARM64_REG_FPCR,j['regs']['fpcr']);mu.reg_write(UC_ARM64_REG_SP,j['regs']['sp']-0x4000)
def ref(L,W,N,A,M,I,lam,target):
 dot=[f(f(L[i]*N[i])+f(W[i]*A[i])) for i in range(3)];v=f(f(dot[0]+dot[1])+dot[2]);skip=v>=target and lam==0
 d=0. if skip else max(f(-lam),f(f(target-v)*M));new=f(lam+d)
 dlm=f(d*I[3]);outL=[f(L[i]+f(N[i]*dlm)) for i in range(4)];outW=[f(W[i]+f(A[i]*f(d*I[i]))) for i in range(4)]
 return outL,outW,new,d,v,skip
rng=random.Random(8194);count=0;fields=0;skipped=0;clamped=0;fixtures=[]
row=s['regs']['x12'];lp=s['regs']['x13']
for k in range(4097):
 restore()
 if k==0:
  L=s['qs']['q27'];W=s['qs']['q28'];N=s['qs']['q2'];I=s['qs']['q29'];R=struct.unpack('<8f',bytes.fromhex(s['row']));A=list(R[:4]);M=R[3];lam=s['lambda_value'];target=R[7]
 else:
  raw=[rng.uniform(-1,1) for _ in range(3)];ln=math.sqrt(sum(x*x for x in raw));N=[f(x/ln) for x in raw]+[0.];L=[f(rng.uniform(-8,8)) for _ in range(3)]+[0.];W=[0.,0.,0.,0.];A=[0.,0.,0.,f(99.90243530273438)];M=A[3];I=[0.,0.,0.,f(.010009765625)];lam=0. if k%3==0 else f(rng.uniform(0,4000));target=f(rng.uniform(-8,8))
 putq(27,L);putq(28,W);putq(2,N);putq(29,I);putq(3,[0.]*4);putq(1,[0.]*4);putq(0,[-1.,-1.,0.,0.]);mu.mem_write(row,struct.pack('<8f',*A,0.,0.,0.,target));u.wf(lp,lam)
 mu.emu_start(BASE+0xa1a98c,BASE+0xa1abd0,count=2000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa1abd0,hex(mu.reg_read(UC_ARM64_REG_PC))
 wantL,wantW,wantlam,d,dot,skip=ref(L,W,N,A,M,I,lam,target);gotL=getq(27);gotW=getq(28);gotlam=u.rf(lp);gotacc=getq(1)[0]
 # skipped row never computes scratch W lane3; kept all4fields for update, all original fields for skip.
 if skip:wantL=list(L);wantW=list(W)
 actual=list(gotL)+list(gotW)+[gotlam,gotacc];want=list(wantL)+list(wantW)+[wantlam,d]
 assert [bits(x) for x in actual]==[bits(x) for x in want],(k,actual,want,L,W,N,A,I,lam,target,dot,skip)
 count+=1;fields+=len(actual);skipped+=int(skip);clamped+=int((not skip) and bits(d)==bits(f(-lam)))
 if k<4:fixtures.append(dict(linear=L,angular=W,normal=N,rowA=A,inv=I,oldlambda=lam,target=target,dot=dot,delta=d,newlambda=gotlam,outL=gotL,outW=gotW,skip=skip))
 assert not u.null_calls and not u.auto_pages and not u.faults,(u.null_calls,u.auto_pages,u.faults)
out=dict(cases=count,fields=fields,mismatches=0,skip=skipped,lowerclamp=clamped,originalblock='0a1a98c..0a1abd0',actual_fixture=fixtures[0],fixture=fixtures,boundary='original single-body branch; live fixture+4096finite random linear/N/target/lambda;mass100 native compressed-high16-f32 inverse.010009765625, effectiveMass99.90243530273438,inertia0,angular0,friction0,normal1;rowtarget producer verified separately;generic4lane/dynamicbody/friction/TOI excluded',null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r8/contact_normal_block_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))

