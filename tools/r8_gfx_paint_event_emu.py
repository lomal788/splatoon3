"""Original ColPaint seam helpers and baev interval selection, no function stubs."""
from pathlib import Path
import json,random,struct
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_X0
from r5_gfx_stage_emu import Emu,BASE
ROOT=Path(__file__).resolve().parents[2];F=np.float32
def norm3(v):return F(np.sqrt(F(F(v[0]*v[0]+v[1]*v[1])+v[2]*v[2])))
def area(v):
 a=np.array(v[1],dtype='float32')-v[0];b=np.array(v[2],dtype='float32')-v[0];c=[F(a[1]*b[2]-a[2]*b[1]),F(a[2]*b[0]-a[0]*b[2]),F(a[0]*b[1]-a[1]*b[0])]
 return F(np.sqrt(F(F(c[0]*c[0]+c[2]*c[2])+c[1]*c[1])))
e=Emu();R=random.Random(80903);tot={'short_edge':0,'largest_adjacent':0,'baev_trigger':0,'baev_range':0};examples=[]
for n in range(1024):
 e.reset_heap();vv=[np.array([F(R.uniform(-4,4)) for _ in range(3)]) for k in range(9)]
 if n<6:vv=[np.array([F(0),F(0),F(0)]),np.array([np.nextafter(F(.3),F(0)) if n%3==0 else (F(.3) if n%3==1 else np.nextafter(F(.3),F(1))),F(0),F(0)]),np.array([F(0),F(1),F(0)])]+vv[3:]
 va=e.alloc(9*80);vh=e.alloc(16);o=e.alloc(16);tri=e.alloc(24);e.w(vh,'IIQ',9,0,va);e.w(o,'Q',vh);e.w(tri,'III',0,1,2)
 for i,v in enumerate(vv):e.w(va+i*80,'3f',*v)
 mu=e.call(BASE+0x2be3ccc,[o,tri]);out=mu.reg_read(UC_ARM64_REG_X0)&1
 exp=int(any(norm3(vv[i]-vv[j])<F(.3) for i,j in [(0,1),(1,2),(2,0)]));assert out==exp,(n,out,exp);tot['short_edge']+=1
 ta=e.alloc(8*24);refs=[];expected=0;best=F(0);flatten=[]
 for i in range(8):
  ids=tuple(R.randrange(9) for _ in range(3));valid=R.randrange(3)!=0
  if n%5==0 and i==1:ids=(0,1,2)
  e.w(ta+i*24,'III4xQ',*ids,1234 if valid else 0);refs.append((ids,valid))
 for vert in [0,1,2]:
  lst=[i for i in range(8) if R.randrange(3)!=0];flat=e.alloc(max(8,8*len(lst)));e.w(va+vert*80+16,'IIQ',len(lst),len(lst),flat)
  for j,i in enumerate(lst):
   e.w(flat+j*8,'Q',ta+i*24);ids,valid=refs[i]
   if valid:
    ar=area([vv[k] for k in ids])
    if ar>best:expected=ta+i*24;best=ar
 mu=e.call(BASE+0x2be3ed8,[o,tri]);out=mu.reg_read(UC_ARM64_REG_X0);assert out==expected,(n,hex(out),hex(expected),float(best));tot['largest_adjacent']+=1
for kind in [0,1]:
 for n in range(2048):
  e.reset_heap();out=e.alloc(8*48);channel=e.alloc(48);lst=e.alloc(16);query=e.alloc(24);keys=e.alloc(8*24);lo=F(R.randrange(-1,20)/2);hi=F(R.randrange(-1,20)/2);cat=R.randrange(3);filt=cat if n%3==0 else(-1 if n%3==1 else cat+10);flags=[R.randrange(2) for _ in range(7)];exp=[]
  e.w(lst,'QII',channel,1,48);e.w(channel+40,'II',kind,cat);e.w(query,'ffII',lo,hi,0,filt&0xffffffff);e.mu.mem_write(query+16,bytes(flags)+b'\0')
  if kind==0:e.w(channel+8,'QII',keys,8,24)
  else:e.w(channel+24,'QII',keys,8,24)
  for i in range(8):
   a=F([-2,-1][i] if i<2 else R.randrange(0,20)/2);b=F(-1 if i%5==0 else float(a)+R.randrange(0,8)/2);e.w(keys+i*24+16,'ff',a,b)
   if filt>=0 and filt!=cat:continue
   if kind==0:
    yes=bool(flags[2] and (flags[6] or a==F(-2) and flags[1] or a==F(-1) and flags[0] or lo<a<=hi));end=True
   else:
    inside=bool(flags[4] and a<=hi and (b<0 or hi<=b));end=bool(not(b<0 or flags[6] or not flags[5] or a<=lo) and b<=hi);yes=bool(flags[3] and (flags[6] or inside or end))
   if yes:exp.append((i,end))
  mu=e.call(BASE+0x8a4790,[out,8,lst,query]);got=mu.reg_read(UC_ARM64_REG_X0)&0xffffffff;arr=[]
  for i in range(got):
   ptr=e.r(out+i*48+24,'Q')[0];b=e.r(out+i*48+40,'B')[0];arr.append(((ptr-keys)//24,bool(b)))
  assert got==len(exp) and arr==exp,(kind,n,flags,float(lo),float(hi),arr,exp);tot['baev_trigger' if kind==0 else 'baev_range']+=1
result={'date':'2026-10-03','counts':tot,'stubs':[],'inputs':'synthetic finite vertices and baev channel/flag combinations; not full GPU/ASB execution','addresses':['7102be3ccc','7102be3ed8','71008a4790']}
(ROOT/'analysis/completion/r8/graphics_paint_event_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
