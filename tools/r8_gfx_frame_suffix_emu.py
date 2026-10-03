"""r8 original normalized-frame consumer nostub and model suffix with RSDB/PLT stubs."""
from pathlib import Path
import struct,json,random,math
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
F=np.float32;R=Path(__file__).resolve().parents[2];e=Emu();rng=random.Random(839)
def round4(v):
 q=F(F(v)*F(10000));z=math.floor(abs(float(q))+.5);return F(F(math.copysign(z,float(q)))/F(10000))
def re_norm(p,a,use):
 a=list(a);flags=a[0];start=F(a[8]);end=F(a[5]);override=F(a[10]);target=override if use&1 and override>=0 else end
 raw=round4(F(start+F(F(target-start)*p)))
 if ((flags&2)==0 or override>=0) and raw<F(a[4]):raw=F(a[4])
 raw=round4(raw);cur=raw;report=raw;stop=override if override>=0 else end
 if end<=raw:
  cur=end
  if ((flags&2)!=0 or raw<stop):
   cur=start
   if start<end:
    period=F(end-start)
    if F(period+period)<=raw:period=F(period*F(int(F(raw/period))))
    cur=round4(F(raw-period))
 if stop<=raw:report=stop
 a[1]=cur;a[9]=report;return a
n=0
for k in range(2048):
 e.reset_heap();x=e.alloc(64);flags=rng.randrange(4);start=F(rng.uniform(-3,3));end=F(start+rng.uniform(.1,100));lower=F(rng.uniform(-2,5));over=F(-1 if k%3==0 else float(end)+rng.uniform(0,80));p=F(rng.uniform(-.5,5));use=k%2
 a=[F(0)]*16;a[0]=flags;a[4]=lower;a[5]=end;a[8]=start;a[10]=over;b=re_norm(p,a,use)
 e.w(x,'I15f',flags,*a[1:]);expect=struct.pack('<I15f',flags,*b[1:]);m=e.call(BASE+0x39ab3fc,[x,use],[p]);assert m.reg_read(UC_ARM64_REG_PC)==RET
 got=bytes(m.mem_read(x,64));assert got==expect,(k,got.hex(),expect.hex());n+=1
state={};rows=[]
def cstr(a):return bytes(e.mu.mem_read(a,255)).split(b'\0',1)[0].decode('ascii')
def hook(mu,a,size,u):
 x=[mu.reg_read(UC_ARM64_REG_X0+i) for i in range(4)];ret=None
 if a in [BASE+i for i in (0x13c380c,0x13b6b40,0x139c940,0x13bb5a8)]:ret=state['row']
 elif a==BASE+0x3e99f20:mu.mem_write(x[0],bytes(mu.mem_read(x[1],x[2])));ret=x[0]
 if ret is not None:mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
for typ in range(5):
 for part,name in [(0,'Har_Test'),(17,'Eyb_Test'),(8,'Btm_Test'),(4,'Hed_Test'),(5,'Clt_Test'),(6,'Shs_Test')]:
  for unisex in (0,1):
   for cap in (2,9,32,64):
    e.reset_heap();mgr=e.alloc(64);table=e.alloc(0x600);row=e.alloc(0x100);s=e.alloc(256);dst=e.alloc(256);obj=e.alloc(32);e.w(BASE+0x599b420,'Q',mgr);e.w(mgr+16,'I4xQ',30,table);e.mu.mem_write(s,name.encode()+b'\0');e.w(row,'Q',s);e.w(row+0x74,'I',0);e.w(row+0x7a,'B',unisex);e.w(obj+8,'QI',dst,cap);state['row']=row
    for off in (0x208,0x230,0x258,0x280,0x2a8,0x2d0):e.w(table+off+32,'Q',row)
    expected=name+('' if unisex and part in (4,5,6) else ('_M' if typ in (1,3) else '_F'));expected=expected[:cap-1]
    m=e.call(BASE+0x26fd010,[obj,part,123,typ,0,0]);assert m.reg_read(UC_ARM64_REG_PC)==RET;got=cstr(dst);assert got==expected,(typ,part,unisex,cap,got,expected);assert m.reg_read(UC_ARM64_REG_X0)==1
    rows.append(dict(type=typ,part=part,unisex=unisex,capacity=cap,name=got))
out={'date':'2026-10-03','normalized_frame':{'count':n,'mismatch':0,'stubs':[],'function':'71039ab3fc'},'suffix':{'count':len(rows),'mismatch':0,'rows':rows,'function':'71026fd010','stubs':['RSDB lookup13c380c/13b6b40/139c940/13bb5a8 returns synthetic metadata row','memcpy PLT3e99f20']},'limits':'frameconsumer whole ASB sync/GPU pose not executed; suffix exactRSDB rows/failure/variation not tested'}
(R/'analysis/completion/r8/graphics_frame_suffix_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('normalized_frame',n,'suffix',len(rows),'mismatch0')
