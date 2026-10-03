"""NEW runtime reset/SLink priority + listener result aggregate → native limiter key.
Existing SLink/comparator reading reused; new whole38655dc supplies priority factor and new native joined evidence.
"""
import struct,json,random
from pathlib import Path
from network_uc import UC,BASE,STUB,END
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];D=R/'analysis/completion/r9';u=UC();m=u.mu
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
putq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
raw=lambda a,n:bytes(m.mem_read(a,n))
null=[];fault=[];bad=[];fields=0
m.mem_write(BASE+0x599aa80,b'\0'*9)
def unknown(mu,a,n,_):
 if a!=END:raise RuntimeError('unregistered stub '+hex(a))
m.hook_add(UC_HOOK_CODE,unknown,begin=STUB,end=STUB+0xfff)
def invalid(mu,a,b,c,d,e):fault.append([a,hex(b),c]);return False
m.hook_add(UC_HOOK_MEM_INVALID,invalid)
def zero(mu,a,b,c,d,e):null.append([a,hex(b),c]);raise RuntimeError('null')
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,zero,begin=0,end=0xfff)
S=u.alloc(0x200);LM=u.alloc(0x80);Larr=u.alloc(32);L=[u.alloc(0x80) for _ in range(4)];P=u.alloc(0x110);handle=u.alloc(0xb0);v=u.alloc(0x260);v2=u.alloc(0x260);result=u.alloc(0x30);acc=u.alloc(0x40);recs=u.alloc(4*0x1c);dirty=u.alloc(8)
putq(BASE+0x599a3f8,S);putq(S+0x20,LM);putq(LM+0x18,Larr);u.u32(LM+0x10,4)
for i,l in enumerate(L):putq(Larr+i*8,l);u.u32(LM+0x44+i*8,10+i)
putq(handle+0x18,P);putq(handle+0x70,v);u.u32(handle+0x78,123);u.u32(v+8,123);u.u32(v+4,2);u.u32(v2+4,2);putq(v+0x70,dirty);putq(v+0x210,acc);putq(acc+0x28,recs);u.u32(acc+0x20,4)
u.f32(v2+0xc4,.5);u.f32(v2+0xcc,1.);u.u32(v2+8,124)
rng=random.Random(0x938655dc);n=0;listener_calls=0;producer=nativecomp=0
for case in range(2048):
 u.call(BASE+0x3885564,P);pr=f(rng.uniform(-.2,1.2));scale=f(rng.choice([1.,.5,1.5,-1.]));flags=0x40 if case%4 else 0
 u.f32(P+0xd4,scale);u.f32(handle+0x38,1.);u.f32(handle+0x94,pr);m.mem_write(handle+0x82,b'\0\0');u.f32(v+0xc4,.123);u.f32(v+0xcc,f(rng.uniform(.1,1.5)))
 u.call(BASE+0x3887e3c,handle,flags);producer+=1
 expect=f(pr*scale);expect=expect if flags and 0<=expect<=1 else f(.123)
 fields+=1
 if raw(v+0xc4,4)!=struct.pack('<f',expect):bad.append([case,'SLinkPriority',u.rf32(v+0xc4),expect])
 vals={0xc:f(3.4028234663852886e38),0x10:0.,0x14:f(3.4028234663852886e38),0x18:0.};u.u32(acc+0x1c,0)
 for off,val in vals.items():u.f32(acc+off,val)
 cls=case%6-1;u.u32(v+0x12c,(10+cls if cls>=0 else -1)&0xffffffff)
 for i,l in enumerate(L):
  ws=[f(rng.uniform(0,1.)) for _ in range(4)]
  for j,w in enumerate(ws):u.f32(l+0x58+j*4,w)
  w=1. if cls<0 else ws[cls if cls<4 else 0]
  rv={off:f(rng.uniform(0,1.)) for off in [4,8,0xc,0x10,0x14,0x18,0x1c,0x20,0x24,0x28]}
  for off,val in rv.items():u.f32(result+off,val)
  u.call(BASE+0x38655dc,acc,i,result,v);listener_calls+=1
  for off,src,mode in [(0xc,8,'min'),(0x10,0xc,'max'),(0x14,0x10,'min'),(0x18,0x18,'max')]:
   x=f(1.-f(w*f(1.-rv[src]))) if mode=='min' else f(w*rv[src]);old=vals[off]
   vals[off]=(old if old<=x else x) if mode=='min' else (old if x<=old else x)
   fields+=1
   if raw(acc+off,4)!=struct.pack('<f',vals[off]):bad.append([case,i,'aggregate',off,u.rf32(acc+off),vals[off]])
  want={0:i,4:struct.unpack('<I',struct.pack('<f',f(w*rv[4])))[0],8:struct.unpack('<I',struct.pack('<f',rv[0x1c]))[0],0xc:struct.unpack('<I',struct.pack('<f',rv[0x20]))[0],0x10:struct.unpack('<I',struct.pack('<f',rv[0x24]))[0],0x14:struct.unpack('<I',struct.pack('<f',rv[0x28]))[0],0x18:struct.unpack('<I',struct.pack('<f',rv[0x14]))[0]}
  for off,val in want.items():
   fields+=1
   if u.ru32(recs+i*0x1c+off)!=val:bad.append([case,i,'record',off])
 key=int(f(f(f(u.rf32(v+0xc4)*u.rf32(v+0xcc))*vals[0x18])*255.));key2=int(f(.5*255.))
 got=u.call(BASE+0x3848c88,v,v2)&0xffffffff;got=got-2**32 if got>=2**31 else got;nativecomp+=1;fields+=1
 if got!=key2-key:bad.append([case,'key',got,key2-key])
 n+=1
res={'joined_cases':n,'native_SLink_priority_writes':producer,'native_listener_aggregate_calls':listener_calls,'native_comparators':nativecomp,'fields':fields,'mismatch':len(bad),'bad':bad[:10],'null':null,'fault':fault,'auto_map':0,'stubs':[],'new_native':'3885564 reset→3887e3c Priority; NEW38655dc AADR/AUDC listener weighted aggregate→3848c88 key','boundary':['listener output values/weights explicit fixture; original curve evaluation reused from prior evidence, not new whole assetselection','P D4 varies fixture values; default1 is original reset','voice180 custom override=null; four-listener normal aggregate branch executes','38485ac CC writer original reading; no numerical test claim for that separate scheme']}
(D/'sound_priority_chain_emu.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(res,ensure_ascii=False));assert not bad and not null and not fault
