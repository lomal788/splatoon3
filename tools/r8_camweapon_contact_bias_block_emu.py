"""r8 original single-body Jacobian effective mass and bias/cached-depth update f32 comparison.
Completed blocks inside0a15b70, native original fixture boundaries explicit.
"""
import json,struct,random
from pathlib import Path
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r6_player_uc import BASE
j=json.loads(Path('analysis/completion/r8/physics_kernel_fixture.json').read_text(encoding='utf8'));p=json.loads(Path('analysis/completion/r8/contact_bias_producer.json').read_text(encoding='utf8'));u=PhysicsUC();mu=u.mu
for k,file in [('heap','physics_kernel_heap.bin'),('stack','physics_kernel_stack.bin'),('bss','physics_kernel_bss.bin')]:mu.mem_write(j[k+'_base'],Path('analysis/completion/r8/'+file).read_bytes())
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bit(x):return struct.pack('<f',x).hex()
def qput(i,a):mu.reg_write(globals()['UC_ARM64_REG_Q'+str(i)],int.from_bytes(struct.pack('<4f',*a),'little'))
def qget(i):return struct.unpack('<4f',mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]).to_bytes(16,'little'))
def restore(s):
 for k,v in s['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
 for k,v in s['qs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],int(v,16))
 mu.reg_write(UC_ARM64_REG_FPCR,j['regs']['fpcr'])
def negzero(x):return x==0 and bit(x)=='00000080'
def mn(a,b):return (-0. if negzero(a) or negzero(b) else 0.) if a==0 and b==0 else min(a,b)
def mx(a,b):return (-0. if negzero(a) and negzero(b) else 0.) if a==0 and b==0 else max(a,b)
rng=random.Random(166204);mass_s=next(s for s in p['samples'] if s['pc']=='0x7100a16cd8');bias_s=next(s for s in p['samples'] if s['pc']=='0x7100a16d78')
masscases=0;massfields=0
for k in range(1024):
 restore(mass_s);x=mass_s['regs'];A=[f(rng.uniform(-1,1)) for _ in range(3)]+[0.];inv=[0.,0.,0.,f(.010009765625)]
 if k==0:A=[0.,0.,0.,0.]
 qput(0,A);mu.mem_write(x['x20'],struct.pack('<4f',*inv));mu.emu_start(BASE+0xa16cd8,BASE+0xa16d14,count=1000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa16d14
 weights=[f(inv[i]*f(A[i]*A[i])) for i in range(3)];den=f(f(weights[0]+weights[1])+f(weights[2]+inv[3]));damp=u.rf(x['x19']+8);M=f(damp/den);got=qget(0)[3];assert bit(got)==bit(M),(k,got,M);assert bit(u.rf(x['x10']+0xc))==bit(M);masscases+=1;massfields+=2

def reference(old,carry,d,vel,fresh,dt,pred,k,gamma,c0,ratio,threshold):
 predicted=f(carry+f(vel*pred));p=carry if fresh else predicted;cap=f(dt*c0)
 if old>=threshold and d>f(p-cap):return old,d,f(d*f(-gamma)),True
 tmp=mx(0.,mn(f(d*k),cap));b=tmp if fresh else mn(f(old*k),cap)
 diff=f(d-old);p=f(mn(p,0.)-diff);limit=f(cap+f(ratio*b));select=p if p>limit else 0.
 newold=f(f(old+b)-select);newcarry=f(f(diff-b)+select)
 clipped=mn(mx(newold,f(d-b)),threshold)
 return clipped,newcarry,f(newcarry*f(-gamma)),False
biascases=0;fields=0;fast=0;fixtures=[]
x=bias_s['regs'];threshold=struct.unpack('<4f',int(bias_s['qs']['q2'],16).to_bytes(16,'little'))[0]
for n in range(4097):
 restore(bias_s);fresh=x['x9']&0xffffffff
 if n==0:old=0.;carry=0.;d=f(-.15000003576278687);vel=0.;dt=f(1/60);pred=0.;k=f(-.05);c0=1.;ratio=2.;gamma=288.
 else:old=f(rng.uniform(-.3,.3));carry=f(rng.uniform(-.2,.2));d=f(rng.uniform(-.3,.3));vel=f(rng.uniform(-4,4));fresh=n&1;dt=f(1/60);pred=0. if n%3==0 else f(rng.uniform(0,1/30));k=f(-.05);c0=1.;ratio=2.;gamma=288.
 mu.reg_write(UC_ARM64_REG_X9,fresh);mu.reg_write(UC_ARM64_REG_Q5,(0 if fresh else (1<<64)-1));qput(0,[vel,vel,0.,0.]);qput(16,[old,0.,0.,0.]);qput(6,[dt,dt,0.,0.]);qput(17,[c0,c0,0.,0.]);qput(3,[ratio,ratio,0.,0.]);qput(8,[0.]*4);qput(7,[carry,carry,0.,0.])
 u.wf(x['x14']+x['x12'],carry);u.wf(x['x15']+x['x12'],old);u.wf(x['x13']+0x30,d);mu.mem_write(x['x19']+0x20,struct.pack('<2f',pred,pred));mu.mem_write(x['x21']+0xc8,struct.pack('<2f',k,k));mu.mem_write(x['x19']+0xd0,struct.pack('<2f',gamma,gamma))
 mu.emu_start(BASE+0xa16d54,BASE+0xa16d58,count=2) # original FCMP oldDepth vs threshold supplies NZCV consumed atd98
 mu.emu_start(BASE+0xa16d78,BASE+0xa16e24,count=1000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa16e24,hex(mu.reg_read(UC_ARM64_REG_PC))
 wantold,wantcarry,wanttarget,early=reference(old,carry,d,vel,fresh,dt,pred,k,gamma,c0,ratio,threshold);gotold=u.rf(x['x15']+x['x12']);gotcarry=u.rf(x['x14']+x['x12']);gotrow=struct.unpack('<4f',mu.mem_read(x['x10']+0x10,16));want=[wantold,wantcarry,0.,0.,0.,wanttarget];actual=[gotold,gotcarry,*gotrow]
 assert [bit(v) for v in actual]==[bit(v) for v in want],(n,actual,want,old,carry,d,vel,fresh,pred,early)
 biascases+=1;fields+=6;fast+=early
 if n<6:fixtures.append(dict(old=old,carry=carry,depth=d,vel=vel,fresh=fresh,predict=pred,stored=gotold,newcarry=gotcarry,target=gotrow[3],early=early))
 assert not u.null_calls and not u.auto_pages and not u.faults,(u.null_calls,u.auto_pages,u.faults)
out=dict(mass_cases=masscases,mass_fields=massfields,bias_cases=biascases,bias_fields=fields,mismatches=0,early_branch=fast,massblock='0a16cd8..0a16d14',biasblock='originalFCMP0a16d54..d58 +0a16d78..0a16e24',actual_fixture=fixtures[0],fixtures=fixtures,threshold=threshold,boundary='0a15b70 completed single-body row blocks, live kernel fixture and perturbed finite cachedDepth/carry/currentDepth/flag/projectedVelocity;caller interpretation of x21 record+c0/c8 and fresh flag w9 kept unnamed;actual defaults c0=1/c8=-.05,dt1/60,gamma288;BSS/heap/stack/runtime original fixture supplied;generic4lane/friction/dynamicpair/TOI excluded',null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r8/contact_bias_block_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
