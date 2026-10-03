"""Original filter table -> original biquad queue -> original SDK command executor."""
import sys,struct,math,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from network_uc import UC,BASE,STUB,END
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];D=R/'analysis/completion/r9';u=UC();m=u.mu
q=lambda a:struct.unpack('<Q',m.mem_read(a,8))[0]
putq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
puth=lambda a,v:m.mem_write(a,struct.pack('<H',v))
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
wires=[];fault=[];null=[];locks=0;allocs=0
SDKVALID=BASE+0x3e9cf00;SDKSET=BASE+0x3e9d8e0
allowed={BASE+0x83d2f0,BASE+0x3e99fd0,BASE+0x3e99ff0,SDKVALID,SDKSET}
def hook(mu,a,n,_):
 global locks,allocs
 if a==BASE+0x83d2f0:
  mu.reg_write(UC_ARM64_REG_X0,u.alloc(mu.reg_read(UC_ARM64_REG_X0)));allocs+=1
 elif a==SDKVALID:mu.reg_write(UC_ARM64_REG_X0,1)
 elif a==SDKSET:
  wires.append((mu.reg_read(UC_ARM64_REG_X0),mu.reg_read(UC_ARM64_REG_X1),bytes(mu.mem_read(mu.reg_read(UC_ARM64_REG_X2),12))))
 elif a in allowed:locks+=1
 else:raise RuntimeError('unexpected stub')
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
for a in allowed:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
def unknown(mu,a,n,_):
 if a!=END:raise RuntimeError('unregistered stub')
m.hook_add(UC_HOOK_CODE,unknown,begin=STUB,end=STUB+0xfff)
def badmem(mu,a,b,c,d,e):fault.append([a,hex(b),c]);return False
m.hook_add(UC_HOOK_MEM_INVALID,badmem)
def badnull(mu,a,b,c,d,e):null.append([a,hex(b),c]);raise RuntimeError('null memory')
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,badnull,begin=0,end=0xfff)
A=u.alloc(0x240);table=u.alloc(0x208);pool=u.alloc(0x60);cmds=u.alloc(0x40*4);free=u.alloc(8);queue=u.alloc(0x40280);vec=u.alloc(0x18);slots=u.alloc(64);mutex=u.alloc(64);mgr=u.alloc(0x40);h=u.alloc(0x128);sdk=u.alloc(0xb0)
putq(BASE+0x599a408,A);putq(BASE+0x59975c0,0);putq(A+0x180,table);putq(A+0x1a0,pool);putq(A+0x1a8,queue);putq(A+0x1b8,mgr);m.mem_write(A+1,b'\x01')
putq(pool+0x20,cmds);putq(pool+0x38,free);m.mem_write(pool+8,b'\x01');putq(queue+0x40250,vec);putq(queue+0x40270,mutex);u.u32(vec+4,8);putq(vec+8,slots)
m.mem_write(mgr+0x10,b'\x01');putq(mgr+0x18,h);u.u32(mgr+0x24,1);puth(mgr+0x30,1)
m.mem_write(h+0x7a,b'\x01');u.u32(h+0x100,1);u.u32(h+0x104,0x20);putq(h+0xf8,sdk+0x20);putq(sdk+0x28,h+0xf0);puth(h+0x124,0)
u.call(BASE+0x37e4424,table,48000,0)
records=json.loads((D/'sound_filter_table_emu.json').read_text(encoding='utf8'))['records'];fmt={x['slot']:x for x in records if x['sample_rate']==48000}
rng=random.Random(0x9b1);bad=[];calls=0;cache_hits=0;fields=0
inputs=[-math.inf,-2.,-0.,0.,1e-7,.25,.5,.75,1.,2.,math.inf,math.nan]
for case in range(2048):
 slot=case%16;ch=(case//16)%2;a=f(inputs[case%len(inputs)] if case<512 else rng.uniform(-.3,1.3))
 amount=0. if math.isnan(a) or a<0 else min(a,1.)
 enabled=int(slot!=0)
 if slot:
  rec=fmt[slot];v=f(f(2.-amount)*amount) if rec['warp'] else amount;idx=max(0,min(rec['count']-1,math.trunc(f(f(rec['count']-1)*v))))
  coeff=struct.pack('<5h',*rec['rows'][idx])
 else:coeff=b'\0'*10
 want=bytes([enabled,0])+coeff
 # Force cache change then construct through original pool and queue (no allocator stub here).
 m.mem_write(h+0xd4+ch,b'\x07');m.mem_write(h+0xd6+ch*10,b'\0'*10);m.mem_write(cmds,b'\0'*0x100);u.u32(pool+0x18,0);u.u32(pool+0x40,0);u.u32(pool+0x48,4);puth(free,1);puth(free+2,2);u.u32(vec,0)
 u.call(BASE+0x37fa0b8,h,ch,slot,fargs=(a,))
 cmd=q(slots);assert u.ru32(vec)==1 and cmd==cmds
 got=bytes(m.mem_read(cmd+0xe,12))
 if got!=want:bad.append([case,'packet',got.hex(),want.hex()])
 assert u.ru32(cmd+8)==ch
 wires.clear();u.call(BASE+0x37ef290,cmd);calls+=1;fields+=6
 if wires!=[(sdk+0x80,ch,want)]:bad.append([case,'wire',str(wires),want.hex()])
 u.call(BASE+0x37fa0b8,h,ch,slot,fargs=(a,))
 if u.ru32(vec)!=1:bad.append([case,'cache',u.ru32(vec)])
 else:cache_hits+=1
 assert m.reg_read(UC_ARM64_REG_PC)==END
# Native runtime P reset supplies D4=1, D8=0 and BAflags=0; default voicekind remains -1 until caller flags request change.
p=u.alloc(0x110);reset_fields=0
for case in range(256):
 m.mem_write(p,b'\xa5'*0x110);u.call(BASE+0x3885564,p)
 expected={0xb8:0,0xbc:0x3f800000,0xc0:0xbf800000,0xc4:0x3f800000,0xc8:0,0xcc:0x3f800000,0xd0:0,0xd4:0x3f800000,0xd8:0,0xdc:0,0xe0:0,0xe4:0,0xe8:0,0xec:0,0xf0:0,0xf4:0,0xf8:0,0x100:0,0x104:0}
 for off,v in expected.items():
  reset_fields+=1
  if u.ru32(p+off)!=v:bad.append([case,'P reset',off])
 assert bytes(m.mem_read(p+0x108,2))==b'\0\0'
res={'cases':calls,'sdk_coefficient_fields':fields,'cache_hits':cache_hits,'P_reset_cases':256,'P_reset_fields':reset_fields,'mismatch':len(bad),'bad':bad[:10],'null':null,'fault':fault,'auto_map':0,'boundary':['malloc supplies filter ctor objects only','mutex lock/unlock singlethread no-op','SDK IsVoiceValid returns1 for explicit fixture voice','SDK SetVoiceBiquadFilterParameter captures exact12B; audio DSP output not executed'],'native':['37e4424','37fa0b8 including native pool and37e3fec queue','37ef290 SDK executor','3885564 P reset'],'allocations':allocs,'locks':locks}
(D/'sound_filter_wire_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(res,ensure_ascii=False));assert not bad and not null and not fault
