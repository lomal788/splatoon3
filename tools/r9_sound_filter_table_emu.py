"""Execute original aal filter registration + quantized coefficient callbacks."""
import sys,struct,math,json,random,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from network_uc import UC,BASE,STUB,END,IMG
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
R=Path(__file__).resolve().parents[2];D=R/'analysis/completion/r9'
u=UC();m=u.mu
fault=[];null=[];calls=[]
def stopfault(mu,a,b,c,d,e):
 fault.append([a,hex(b),c]);return False
def checknull(mu,a,b,c,d,e):
 null.append([a,hex(b),c]);raise RuntimeError('null memory access')
def code(mu,a,n,_):
 if a==BASE+0x83d2f0:
  sz=mu.reg_read(UC_ARM64_REG_X0);ptr=u.alloc(sz);calls.append(sz)
  mu.reg_write(UC_ARM64_REG_X0,ptr);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif STUB<=a<STUB+0x1000 and a!=END:raise RuntimeError('unexpected stub')
m.hook_add(UC_HOOK_MEM_INVALID,stopfault)
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,checknull,begin=0,end=0xfff)
m.hook_add(UC_HOOK_CODE,code,begin=BASE+0x83d2f0,end=BASE+0x83d2f0)
m.hook_add(UC_HOOK_CODE,code,begin=STUB,end=STUB+0xfff)
q=lambda a:struct.unpack('<Q',m.mem_read(a,8))[0]
putq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
putq(BASE+0x59975c0,0)
common=[(0x4aecd26,112,0),(0x4aed186,97,0),(0x4aed550,122,1),(0x4aeda14,93,1),(0x4aeddb6,93,1)]
fmt48=[(0x4af09bc,121,0),(0x4af0e76,112,0),(0x4af12d6,122,1),(0x4af179a,116,1),(0x4af1c22,116,1)]+common+[(0x4aee158,112,0),(0x4aee5b8,97,0),(0x4aee982,122,1),(0x4aeee46,93,1),(0x4aef1e8,93,1)]
fmt32=[(0x4aef58a,112,0),(0x4aef9ea,97,0),(0x4aefdb4,122,1),(0x4af0278,93,1),(0x4af061a,93,1)]+common+common
rng=random.Random(9022026);bad=[];records=[];checks=0;initfields=0
out=u.alloc(16)
for fs,items in [(48000,fmt48),(32000,fmt32),(44100,[])]:
 tab=u.alloc(0x208);u.call(BASE+0x37e4424,tab,fs,0)
 assert q(tab+8)==0
 if not items:
  assert all(q(tab+8+j*8)==0 for j in range(64));continue
 for slot,(data,count,warp) in enumerate(items,1):
  obj=q(tab+8+slot*8);vt=BASE+(0x57307c0 if warp else 0x5730778);fn=BASE+(0x37e42bc if warp else 0x37e4278)
  expect=(vt,BASE+data,count)
  got=(q(obj),q(obj+8),u.ru32(obj+16));initfields+=3
  assert got==expect,(fs,slot,got,expect)
  raw=bytes(m.mem_read(BASE+data,count*10));rows=[list(struct.unpack_from('<5h',raw,j*10)) for j in range(count)]
  sample=[]
  amounts=[0.0,1.0,0.25,0.5,0.75]+[j/(count-1) for j in range(count)]+[rng.random() for _ in range(512)]
  for a in amounts:
   a=f(a);v=f(f(2.0-a)*a) if warp else a;idx=max(0,min(count-1,math.trunc(f(f(count-1)*v))))
   u.call(fn,obj,out,fargs=(a,));got=bytes(m.mem_read(out,10));want=raw[idx*10:idx*10+10];checks+=5
   if got!=want:bad.append([fs,slot,a,idx,got.hex(),want.hex()])
   if a in [0.0,.25,.5,.75,1.0]:sample.append({'amount':a,'index':idx,'q14':list(struct.unpack('<5h',got))})
  records.append({'sample_rate':fs,'slot':slot,'object_vtable':hex(vt),'callback':hex(fn),'data':hex(BASE+data),'count':count,'warp':warp,'sha256':hashlib.sha256(raw).hexdigest(),'sample':sample,'rows':rows})
assert m.reg_read(UC_ARM64_REG_PC)==END
res={'entry':'0x71037e4424','image_sha256':hashlib.sha256(IMG.read_bytes()).hexdigest(),'initializers':3,'initialized_objects':len(records),'init_fields':initfields,'coefficient_fields':checks,'cases':checks//5,'mismatch':len(bad),'bad':bad[:10],'malloc_calls':len(calls),'malloc_sizes':sorted(set(calls)),'null':null,'fault':fault,'auto_map':0,'boundary':'malloc allocation only; actual 48k/32k registrations and original table callbacks executed; 44100 unsupported leaves supplied empty table empty','records':records}
(D/'sound_filter_table_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in res.items() if k!='records'},ensure_ascii=False))
assert not bad and not null and not fault
