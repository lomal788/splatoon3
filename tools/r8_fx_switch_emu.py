"""Original Switch calc 38976d4 + common cancel 388e748; synthetic resource/child fixtures.
Selector, asset allocation, virtual child lifecycle are observable boundary stubs, not claimed executed.
"""
import itertools,json,struct,sys
from pathlib import Path
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
import respawn_emu as R
FN=0x71038976d4; SELECT=0x71038978bc; CREATE=0x710388e468
STUB=0x30000100
class H(R.Emu):
 def _block(self,mu,addr,size,user):
  if self._allowed(addr):return
  x=mu.reg_read(UC_ARM64_REG_X0);ret=0
  if addr==SELECT:ret=self.selected;self.trace.append('select')
  elif addr==CREATE:
   self.trace.append('create');ret=self.new if self.alloc_ok else 0
   assert mu.reg_read(UC_ARM64_REG_S0)==0x3f800000
  elif addr==STUB:ret=self.resource if self.resource_ok else 0
  elif addr==STUB+4:self.trace.append('start');ret=self.start_ok
  elif addr==STUB+8:self.trace.append('done:'+('old' if x==self.old else 'new'));ret=self.old_done if x==self.old else self.new_done
  elif addr==STUB+12:self.trace.append('cancel')
  elif addr==STUB+16:self.trace.append('release:'+('old' if x==self.old else 'new'))
  elif addr==STUB+20:
   self.trace.append('restart');ret=self.restart_ok
   if ret:self.w64(self.parent+0x18,self.new)
  elif addr==STUB+24:self.trace.append('cancel_leaf')
  else:raise RuntimeError(f'unexpected boundary {addr:#x}')
  mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 def w64(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def w32(self,a,v):self.mu.mem_write(a,struct.pack('<I',v&0xffffffff))
 def r32(self,a):return struct.unpack('<i',self.mu.mem_read(a,4))[0]
 def r64(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
h=H([FN,0x710388e748]);h.parent=h.alloc(0x80);event=h.alloc(0x100);inst=h.alloc(0x100);y=h.alloc(0x60);acc=h.alloc(0x60);accvt=h.alloc(0x30);q=h.alloc(0x30);h.resource=h.alloc(0x100);resdata=h.alloc(0xa0);ctb=h.alloc(0x90);assets=h.alloc(24);h.old=h.alloc(0x80);h.new=h.alloc(0x80);childvt=h.alloc(0x50);parentvt=h.alloc(0x50)
h.w64(h.parent,parentvt);h.w64(parentvt+0x20,STUB+20);h.w64(h.parent+8,ctb);h.w64(h.parent+0x10,event);h.w64(event+0x28,inst);h.w64(inst+0x38,y);h.w64(y+0x18,acc);h.w64(acc,accvt);h.w64(accvt+0x10,STUB);h.w64(q+0x10,h.resource);h.w64(h.resource+0x20,resdata);h.w64(resdata+0x28,ctb);h.w32(resdata+0x78,3);h.w64(resdata+0x80,assets)
# accessor returns a wrapper, not the resource itself
h.resource=q
for c in [h.old,h.new]:h.w64(c,childvt)
for off,target in [(0x18,STUB+16),(0x20,STUB+4),(0x28,STUB+8),(0x30,STUB+12)]:h.w64(childvt+off,target)
def ref(sc):
 flags,resource,bit,oldmode,selected,allocok,startok,olddone,newdone,dur,restart=sc;t=[];child=oldmode;duration=dur
 reevaluate=not(flags&16) and resource and bit and not(flags&8)
 livewatch=reevaluate
 if reevaluate:
  t.append('select')
  if child and oldmode!=2:
   t+=['cancel','release:old'];child=0
  if not child and selected:
   t.append('create')
   if allocok:
    t.append('start')
    if startok:child=3
    else:t.append('release:new')
 if child:
  old=child in [1,2];t.append('done:'+('old' if old else 'new'));done=olddone if old else newdone
  if not done:return t,child,duration,0
  t.append('release:'+('old' if old else 'new'));child=0
  if duration>0:duration-=1
  if duration!=0:
   t.append('restart')
   if restart:
    child=3;t.append('done:new');return t,child,duration,int(not livewatch and newdone)
 return t,child,duration,int(not livewatch)
count=0;examples=[]
# oldmode:0 absent;1 different from selected;2 same selected. candidate present always required for same case.
for sc in itertools.product([0,8,16,24],[0,1],[0,1],[0,1,2],[0,1],[0,1],[0,1],[0,1],[0,1],[-1,0,1,2],[0,1]):
 flags,resource,bit,oldmode,selected,allocok,startok,olddone,newdone,dur,restart=sc
 if oldmode==2 and not selected:continue
 h.trace=[];h.resource_ok=resource;h.alloc_ok=allocok;h.start_ok=startok;h.old_done=olddone;h.new_done=newdone;h.restart_ok=restart;h.selected=ctb+0x30 if selected else 0
 h.w32(event+8,flags);h.mu.mem_write(assets+2,bytes([2 if bit else 0]));h.w64(h.parent+0x18,h.old if oldmode else 0);h.w64(h.old+8,h.selected if oldmode==2 else ctb+0x60);h.w32(h.parent+0x28,dur)
 h.call(FN,[h.parent]);got=(h.trace,h.r64(h.parent+0x18),h.r32(h.parent+0x28),h.mu.reg_read(UC_ARM64_REG_W0));expect=ref(sc);ep=h.old if expect[1] in [1,2] else h.new if expect[1]==3 else 0
 assert got==(expect[0],ep,expect[2],expect[3]),(sc,got,expect)
 count+=1
 if len(examples)<8 and flags==0 and resource and bit and oldmode==1:examples.append({'input':sc,'trace':h.trace,'duration':got[2],'return':got[3]})
# Common cancel actually traverses linked child chain, forwards vt30, zeros duration, retains pointer.
forward=0;leafvt=h.alloc(0x50);h.w64(leafvt+0x30,STUB+24)
for n in range(7):
 p=h.alloc(0x80);h.w32(p+0x28,123);nodes=[h.alloc(0x80) for _ in range(n)]
 for i,c in enumerate(nodes):h.w64(c,leafvt);h.w64(c+0x20,nodes[i+1] if i+1<n else 0)
 h.w64(p+0x18,nodes[0] if n else 0);h.trace=[];h.call(0x710388e748,[p]);assert h.trace==['cancel_leaf']*n and h.r32(p+0x28)==0 and h.r64(p+0x18)==(nodes[0] if n else 0);forward+=1
out={'function':hex(FN),'cases':count,'cancel_forward_cases':forward,'mismatches':0,'stubs':['resource accessor','38978bc selector (previously read)','388e468 allocation','child start/done/cancel/release','parent restart'],'scope':'Original Switch reevaluation gates, lifecycle call order, duration, returned completion; not fade waveform or mixer duration','examples':examples}
path=Path(__file__).resolve().parents[2]/'analysis/completion/r8/fx_switch_emu.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='examples'}))
