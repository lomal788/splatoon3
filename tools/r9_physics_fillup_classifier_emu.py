"""New FillUp UserShapeTag28 contact height classifier original block. Query generation and angular fallback outside executed block."""
import struct,json,random,collections
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import PhysicsUC
u=PhysicsUC();mu=u.mu;rng=random.Random(0x24f8f58)
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
C=u.alloc(0x3000);L=u.alloc(0x100);E=u.alloc(0x200);A=[u.alloc(0x80) for _ in range(32)];O=u.alloc(0x20);ST=u.alloc(0x400);SP=ST+0x100;FP=SP+0xb0
u.w32(0x71058bc7a0,0)
mu.emu_start(0x71024f0c84,0x71024f0c94,count=5)
threshold=u.rf(0x71058bc7a0);assert u.r32(0x71058bc7a0)==0x3f24360c
stop={};bad=[];results=[];fields=0

def hook(mu,p,size,data):
 if p in (0x71024f9250,0x71024f935c,0x71024f8fc8):stop['pc']=p;mu.emu_stop()
for p in (0x71024f9250,0x71024f935c,0x71024f8fc8):mu.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
for case in range(4096):
 n=1 if case<8 else rng.randrange(0,32);adj=case%2;row=[]
 for i in range(n):
  side=rng.randrange(2);norm=f(rng.choice([-.8,0.,.2,.9,-.5]));height=f(rng.randrange(-10,10)/4);sep=f(rng.uniform(-1,1));tag=rng.choice([0,0x10000000,4,0x100000,0x2000000,0x8000000,0x8200000,0x10000004]);flags=0 if i==0 else rng.choice([0,0,0,4]);eflag=side|(2 if i>0 and rng.randrange(7)==0 else 0)
  if case<8:norm=f(-1 if side==0 else 1);tag=[0,0x10000000,4,0x100000,0x2000000,0x8000000,0x8200000,0x10000004][case];flags=0;eflag=side
  u.wf(A[i]+4,height);u.wf(A[i]+0x10,norm);u.wf(A[i]+0x30,sep);u.wq(A[i]+0x40,tag if side==0 else 0);u.wq(A[i]+0x50,tag if side else 0);u.w8(A[i]+0x68,flags);u.wq(E+i*16,A[i]);u.w8(E+i*16+8,eflag);row.append(dict(side=side,norm=norm,height=height,sep=sep,tag=hex(tag),flags=flags,eflag=eflag))
 mu.mem_write(ST,bytes(0x400));mu.mem_write(O,struct.pack('<3f',11,12,13));u.w32(SP+0x40,0);u.wq(SP+0x48,E);u.w32(SP+0x50,n);u.w32(SP+0x68,0);u.wq(SP+0x70,0);u.w8(SP+0x80,0);u.wf(FP-0x24,2);u.wf(FP-4,5)
 for r,v in ((UC_ARM64_REG_SP,SP),(UC_ARM64_REG_X29,FP),(UC_ARM64_REG_X20,C),(UC_ARM64_REG_X24,L),(UC_ARM64_REG_X19,O),(UC_ARM64_REG_X22,adj),(UC_ARM64_REG_X26,0x8200000),(UC_ARM64_REG_X27,0x100004),(UC_ARM64_REG_X8,n),(UC_ARM64_REG_X9,0)):mu.reg_write(r,v)
 mu.reg_write(UC_ARM64_REG_S8,0);stop.clear();mu.emu_start(0x71024f907c,0x71024f937c,count=20000)
 found=0;special=0;retry=0;h=f(-3.4028234663852886e38);outy=f(12)
 for i,x in enumerate(row):
  if i>0 and(x['flags']&4 or x['eflag']&2):continue
  normal=x['norm'] if x['side'] else f(-x['norm'])
  if normal<threshold:continue
  hh=x['height'] if x['side'] else f(x['height']+f(x['sep']*x['norm']))
  if h>=hh:continue
  h=hh;found=1;tag=int(x['tag'],16);retry=int(bool(tag&0x8200000));special=1 if tag&0x100004 else (tag>>28)&1
  if adj:outy=h
 invalid=special|retry|(found^1);kind='retry' if retry&invalid else 'success' if invalid==0 else 'fallback';expectedpc={'retry':0x71024f8fc8,'success':0x71024f935c,'fallback':0x71024f9250}[kind]
 expectY=f(h+f(-.35)) if kind=='retry' else f(2);expectedRadius=f(f(5)-max(f(f(2)-expectY),f(0))) if kind=='retry' else f(5)
 actual=[stop.get('pc'),mu.reg_read(UC_ARM64_REG_X0)&1,mu.reg_read(UC_ARM64_REG_X1)&1,mu.reg_read(UC_ARM64_REG_X18)&1,bits(u.rf(O+4)),bits(u.rf(FP-0x24)),bits(u.rf(FP-4))];expected=[expectedpc,special,found,retry,bits(outy),bits(expectY),bits(expectedRadius)];fields+=len(expected)
 if actual!=expected:bad.append(dict(case=case,kind=kind,actual=actual,expected=expected,contacts=row))
 results.append(dict(case=case,kind=kind,contacts=row,actual=actual,expected=expected))
print('cases',len(results),'fields',fields,'bad',len(bad),'branches',dict(collections.Counter(x['kind'] for x in results)))
out=dict(scope=__doc__,threshold=threshold,threshold_bits=hex(u.r32(0x71058bc7a0)),cases=len(results),fields=fields,bad=bad,branches=dict(collections.Counter(x['kind'] for x in results)),results=results,runtime=dict(null=u.null_calls,auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed));Path('analysis/completion/r9/physics_fillup_classifier_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print('badfirst',bad[:1]);assert not bad
