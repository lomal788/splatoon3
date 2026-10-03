"""Original0a181fc ordinary multi-contact normal loop, native-produced two-row capsule wall fixture.
Live two-row fullkernel return + finite 2..4-row completed-loop independent f32 comparison.
Rows3/4 supplied as explicit math fixtures; no claim of native manifold generation for those synthetic rows.
"""
import json,struct,random,math
from pathlib import Path
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
from r6_player_uc import BASE
j=json.loads(Path('analysis/completion/r8/contact_multi_kernel_fixture.json').read_text(encoding='utf8'));p=json.loads(Path('analysis/completion/r8/contact_multi_kernel_replay.json').read_text(encoding='utf8'));s=p['samples'][0];entry=[x for x in p['samples'] if x['pc']=='0x7100a18d8c'];post=next(x for x in p['samples'] if x['pc']=='0x7100a1911c');Nlive=next(x for x in p['samples'] if x['pc']=='0x7100a18d18')['qs']['q19'];u=PhysicsUC();mu=u.mu
for k in ['heap','stack','bss']:mu.mem_write(j[k+'_base'],Path('analysis/completion/r8/contact_multi_kernel_'+k+'.bin').read_bytes())
u.heap_next=(j['heap_base']+j['heap_length']+0xff)&~0xff;header=u.alloc(0x200);lp=u.alloc(0x40);native_header=bytes(mu.mem_read(s['regs']['x22'],0x40));sp=j['regs']['sp']-0x4000

def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bit(x):return struct.pack('<f',x).hex()
def qp(i,a):mu.reg_write(globals()['UC_ARM64_REG_Q'+str(i)],int.from_bytes(struct.pack('<4f',*a),'little'))
def qg(i):return struct.unpack('<4f',mu.reg_read(globals()['UC_ARM64_REG_Q'+str(i)]).to_bytes(16,'little'))
def ref(LA,LB,WA,WB,N,rows,lam,IA,IB):
 acc=0.;outs=[];skips=0;clamps=0
 for R,L in zip(rows,lam):
  JA=R[:4];JB=R[4:];r=[f(f(f(LA[i]-LB[i])*N[i])+f(f(WA[i]*JA[i])+f(WB[i]*JB[i]))) for i in range(3)];dot=f(f(r[0]+r[1])+r[2]);skip=dot>=JB[3] and L==0;d=0. if skip else max(f(-L),f(f(JB[3]-dot)*JA[3]));outs.append(f(L+d));skips+=skip;clamps+=int(not skip and bit(d)==bit(f(-L)))
  if not skip:
   LA=[f(LA[i]+f(N[i]*f(d*IA[3]))) for i in range(4)];LB=[f(LB[i]-f(N[i]*f(d*IB[3]))) for i in range(4)];WA=[f(WA[i]+f(f(d*IA[i])*JA[i])) for i in range(4)];WB=[f(WB[i]+f(f(d*IB[i])*JB[i])) for i in range(4)];acc=f(acc+d)
 return LA,LB,WA,WB,outs,acc,skips,clamps
rng=random.Random(188244);fields=0;cases=0;rowscount=0;skipcount=0;clampcount=0;fixtures=[];fullkernel_fields=0
for n in range(1025):
 for k,v in s['regs'].items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
 for k,v in s['qs'].items():qp(int(k[1:]),v)
 mu.reg_write(UC_ARM64_REG_SP,sp);mu.reg_write(UC_ARM64_REG_FPCR,j['regs']['fpcr']);mu.mem_write(sp+0x3cc0,bytes.fromhex(s['stack']))
 if n==0:
  count=len(entry);LA=s['qs']['q2'];LB=s['qs']['q3'];WA=list(struct.unpack('<4f',bytes.fromhex(s['stack'])[:16]));WB=list(struct.unpack('<4f',bytes.fromhex(s['stack'])[16:32]));N=Nlive;IA=s['qs']['q7'];IB=s['qs']['q16'];R=[list(struct.unpack('<8f',bytes.fromhex(t['row']))) for t in entry];lam=[t['lambda_value'] for t in entry]
 else:
  count=2+(n%3);raw=[rng.uniform(-1,1) for i in range(3)];ln=math.sqrt(sum(i*i for i in raw));N=[f(i/ln) for i in raw]+[0.];LA=[f(rng.uniform(-8,8)) for i in range(3)]+[0.];LB=[f(rng.uniform(-8,8)) for i in range(3)]+[0.];WA=WB=[0.,0.,0.,0.];IA=[0.,0.,0.,0.];IB=[0.,0.,0.,f(.010009765625)];R=[[f(rng.uniform(-2,2)) for i in range(3)]+[f(99.90243530273438)]+[f(rng.uniform(-2,2)) for i in range(3)]+[f(rng.uniform(-8,8))] for a in range(count)];lam=[0. if a%2==0 else f(rng.uniform(0,4000)) for a in range(count)]
 mu.mem_write(header,native_header);u.w8(header+4,count);mu.mem_write(header+0x10,struct.pack('<4f',*N));mu.mem_write(header+0x40,b''.join(struct.pack('<8f',*a) for a in R));mu.mem_write(lp,struct.pack('<'+'f'*count,*lam));mu.reg_write(UC_ARM64_REG_X22,header);mu.reg_write(UC_ARM64_REG_X12,header+0x50);mu.reg_write(UC_ARM64_REG_X11,lp);mu.reg_write(UC_ARM64_REG_X14,count);qp(2,LA);qp(3,LB);qp(7,IA);qp(16,IB);qp(1,[0.]*4);qp(0,[-1.,-1.,0.,0.]);mu.mem_write(sp+0x3cc0,struct.pack('<8f',*WA,*WB));mu.mem_write(sp+0x3d70,struct.pack('<2f',0.,0.))
 mu.emu_start(BASE+0xa18d8c,BASE+0xa1911c,count=10000);assert mu.reg_read(UC_ARM64_REG_PC)==BASE+0xa1911c
 oa,ob,wa,wb,new,acc,skip,clamp=ref(LA,LB,WA,WB,N,R,lam,IA,IB);got=[*qg(2),*qg(3),*struct.unpack('<8f',mu.mem_read(sp+0x3cc0,32)),*struct.unpack('<'+'f'*count,mu.mem_read(lp,4*count)),*struct.unpack('<2f',mu.mem_read(sp+0x3d70,8))];want=[*oa,*ob,*wa,*wb,*new,acc,acc];assert [bit(v) for v in got]==[bit(v) for v in want],(n,got,want,R,lam)
 if n==0:
  # Actual native2-row full kernel's corresponding pre-writeback state also equals reference.
  live=[*post['qs']['q2'],*post['qs']['q3'],*struct.unpack('<8f',bytes.fromhex(post['stack'])[:32]),*struct.unpack('<2f',bytes.fromhex(post['stack'])[0xb0:0xb8])];livewant=[*oa,*ob,*wa,*wb,acc,acc];assert [bit(v) for v in live]==[bit(v) for v in livewant],(live,livewant);live_lambda=[int(w[3],16) for w in p["heapwrites"] if int(w[1],16) in [entry[0]["regs"]["x11"],entry[1]["regs"]["x11"]]];assert live_lambda==[int.from_bytes(struct.pack("<f",v),"little") for v in new];fullkernel_fields=len(live)+len(live_lambda)
 fields+=len(got);cases+=1;rowscount+=count;skipcount+=skip;clampcount+=clamp
 if n<4:fixtures.append(dict(count=count,normal=N,linearA=LA,linearB=LB,rows=R,lambda_old=lam,lambda_new=new,output=got,skipped=skip,lowerclamp=clamp))
 assert not u.null_calls and not u.auto_pages and not u.faults
out=dict(cases=cases,row_operations=rowscount,fields=fields,mismatches=0,fullkernel_live_fields=fullkernel_fields,native_contact_count=len(entry),skipped=skipcount,lowerclamp=clampcount,block='0a18d8c..0a1911c loop,header+4 count,row stride20,lambda stride4',fixture=fixtures,scope=__doc__,null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r8/contact_multi_normal_loop_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
