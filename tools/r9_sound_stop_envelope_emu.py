"""Original stop constructor and native progress, with original renderer-clock writer block."""
import struct,json,math,random
from pathlib import Path
from network_uc import UC,BASE,STUB,END,STACK
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];D=R/'analysis/completion/r9';u=UC();m=u.mu
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
q=lambda a:struct.unpack('<Q',m.mem_read(a,8))[0]
putq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
puth=lambda a,v:m.mem_write(a,struct.pack('<H',v))
raw=lambda a,n:bytes(m.mem_read(a,n))
null=[];fault=[];bad=[];lockcount=0
allowed={BASE+0x3e99fd0,BASE+0x3e99ff0}
def hook(mu,a,n,_):
 global lockcount
 lockcount+=1;mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
for a in allowed:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
def unknown(mu,a,n,_):
 if a!=END:raise RuntimeError('unknown stub '+hex(a))
m.hook_add(UC_HOOK_CODE,unknown,begin=STUB,end=STUB+0xfff)
def invalid(mu,a,b,c,d,e):fault.append([a,hex(b),c]);return False
m.hook_add(UC_HOOK_MEM_INVALID,invalid)
def zero(mu,a,b,c,d,e):null.append([a,hex(b),c]);raise RuntimeError('null')
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,zero,begin=0,end=0xfff)
A=u.alloc(0x240);pool=u.alloc(0x60);cmds=u.alloc(0x40*32);free=u.alloc(64);envpool=u.alloc(0x60);envs=u.alloc(0x50*4);envfree=u.alloc(8);queue=u.alloc(0x40280);vec=u.alloc(0x18);slots=u.alloc(0x200);mutex=u.alloc(64);h=u.alloc(0x128)
putq(BASE+0x599a408,A);putq(A+0x1a0,pool);putq(A+0x1b0,envpool);putq(A+0x1a8,queue);putq(pool+0x20,cmds);putq(pool+0x38,free);putq(envpool+0x20,envs);putq(envpool+0x38,envfree);m.mem_write(pool+8,b'\x01');m.mem_write(envpool+8,b'\x01');putq(queue+0x40250,vec);putq(queue+0x40270,mutex);u.u32(vec+4,64);putq(vec+8,slots)
clock_cases=0
for old,new in [(0,1),(100,101),(100,104),(1,1),(1000,2000),(2**32,2**32+3)]:
 u.u32(pool+0x48,32);putq(A+0x28,old);m.reg_write(UC_ARM64_REG_X8,new);m.reg_write(UC_ARM64_REG_X23,A);m.reg_write(UC_ARM64_REG_X28,0x3ba3d70a);m.reg_write(UC_ARM64_REG_X25,0x4021c);m.reg_write(UC_ARM64_REG_SP,STACK+0xf0000)
 m.emu_start(BASE+0x37e1a70,BASE+0x37e1aa8,count=100)
 assert m.reg_read(UC_ARM64_REG_PC)==BASE+0x37e1aa8
 want=f(f(new-old)*f(.005));assert raw(A+0x30,4)==struct.pack('<f',want);clock_cases+=1
rng=random.Random(90937);cases=0;steps=0;fields=0;duration_data=[]
for case in range(768):
 duration=f([0.,-1.,.016,1/60.,.2,1.][case%6] if case<48 else rng.uniform(.001,.1));kind=case%3
 m.mem_write(cmds,b'\0'*0x800);m.mem_write(envs,b'\0'*0x140);m.mem_write(h,b'\0'*0x128);u.u32(pool+0x18,0);u.u32(pool+0x40,0);u.u32(pool+0x48,32);u.u32(envpool+0xc,0);u.u32(envpool+0x18,0);u.u32(envpool+0x40,0);u.u32(vec,0)
 for i in range(32):puth(free+i*2,i+1 if i<31 else 0xffff)
 puth(envfree,0xffff);m.mem_write(h+0x7a,b'\x01');u.u32(h+0x70,1);puth(h+0x124,0);u.f32(h+0xa8,1.)
 u.call(BASE+0x37f9790,h,kind,0,fargs=(duration,));cases+=1
 assert u.ru32(h+0x70)==2
 if duration<=0:
  assert q(q(slots))==BASE+0x5731568;assert q(h+0xb0)==0;continue
 e=q(h+0xb0);assert e==envs and q(e)==BASE+0x5730b80 and q(e+8)==BASE+0x5732158
 expect={0x10:kind,0x14:0,0x18:struct.unpack('<I',struct.pack('<f',f(1./duration)))[0],0x20:0x3f800000,0x24:0xbf800000}
 for off,w in expect.items():fields+=1;assert u.ru32(e+off)==w
 t=0.;dt=f(.005);n=0
 while n<512:
  before=t;ret=u.call(BASE+0x37e9be8,e,fargs=(dt,));steps+=1;n+=1
  if before>=1.:assert ret==1;break
  assert ret==0;t=min(f(before+f(f(1./duration)*dt)),1.)
  if raw(e+0x14,4)!=struct.pack('<f',t):bad.append([case,'progress',u.rf32(e+0x14),t])
  u.call(BASE+0x37e9cb0,e);a=t if kind==0 else (f(t*t) if kind==1 else f(math.sqrt(t)))
  want=f(1.+f(-a));got=m.reg_read(UC_ARM64_REG_S0);fields+=2
  if got!=struct.unpack('<I',struct.pack('<f',want))[0]:bad.append([case,'curve',hex(got),want])
 else:raise RuntimeError('no completion')
 if case<48:duration_data.append({'duration':duration,'kind':kind,'progress_reaches1_tick':n-1,'next_update_return1_tick':n})
res={'stop_constructor_cases':cases,'clock_writer_block_cases':clock_cases,'progress_updates':steps,'fields':fields,'mismatch':len(bad),'bad':bad[:10],'null':null,'fault':fault,'auto_map':0,'duration_examples':duration_data,'boundary':['mutex OS PLT singlethread no-op','native37f9790/37f8fec allocation pools+37e3fec queue execute','native37e9be8 progress +37e9cb0 styles0/1/2 execute','37e1834 renderer loop only exact37e1a70..1aa8 clock writer block executes; SDK renderer counter supplied','final SDK audio-stop command not executed; native CPU duration/progress and queued command verified','style3 sinf only original instruction reading, not numeric claim']}
(D/'sound_stop_envelope_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in res.items() if k!='duration_examples'},ensure_ascii=False));assert not bad and not null and not fault
