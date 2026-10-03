"""r8 original body model resource selection and ordered AS binder list; asset loader/API stubs only."""
from pathlib import Path
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
R=Path(__file__).resolve().parents[2];e=Emu();state={};FAKE=RET+0x100

def cstr(a):
 b=bytearray()
 for i in range(255):
  c=e.mu.mem_read(a+i,1)[0]
  if c==0:return b.decode('ascii')
  b.append(c)
 raise ValueError('long string')
def safestr(a):return cstr(e.r(a,'Q')[0])
def hook(mu,a,size,u):
 x=[mu.reg_read(UC_ARM64_REG_X0+i) for i in range(7)];ret=None
 if a==BASE+0x2657a4c:
  file=safestr(x[1]);model=safestr(x[2]);out=e.alloc(0x300);res=e.alloc(0x300);state['base']=[file,model];state['resources'][res]=file;ret=out;mu.reg_write(UC_ARM64_REG_X1,res)
 elif a==BASE+0xf44d60:
  s=cstr(x[1])%cstr(x[2]);dst=e.r(x[0]+8,'Q')[0];mu.mem_write(dst,s.encode()+b'\0');ret=len(s)
 elif a==BASE+0x37b2b28:
  path=safestr(x[1]);res=e.alloc(0x300);vt=e.alloc(8);bf=e.alloc(0x300);e.w(vt,'Q',FAKE);e.w(res,'Q',vt);e.w(res+40,'Q',bf);state['resources'][bf]=path.removeprefix('Model/').removesuffix('.bfres');ret=res
 elif a==BASE+0x366f140:
  n=x[2];ptrs=e.r(x[0],str(n)+'Q');state['binder']=[state['resources'][p] for p in ptrs];ret=e.alloc(0x200)
 elif a==BASE+0x3e99ef0:ret=1
 elif a==BASE+0x3e99f00:ret=0
 elif a==FAKE:ret=1
 if ret is not None:mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
out=[]
for typ in range(5):
 for part in range(5):
  e.reset_heap();state.clear();state.update(resources={});f=e.alloc(64);pool=e.alloc(64);arr=e.alloc(256);free=[e.alloc(64) for _ in range(32)];heap=e.alloc(64);e.w(f,'QQ4xII',heap,pool,typ,part);e.w(pool,'IIQQ',0,32,arr,free[0])
  for i,p in enumerate(free):e.w(p,'Q',free[i+1] if i<31 else 0)
  e.w(BASE+0x5801b80,'B',1)
  try:mu=e.call(BASE+0x2656ac8,[f])
  except Exception:
   print('failure',typ,part,hex(e.mu.reg_read(UC_ARM64_REG_PC)),state);raise
  assert mu.reg_read(UC_ARM64_REG_PC)==RET;(out.append({'type':typ,'part':part,'base':state.get('base'),'binder':state.get('binder')}))
assert [o['binder'] for o in out if o['part']==0]==[['Player00'],['Player01','Player00'],['Player02','Player00'],['Player03','Player01','Player00'],['Player02','Player00']]
res={'date':'2026-10-03','count':25,'rows':out,'stubs':['2657a4c asset-model factory returns symbolic handles','37b2b28 BFRES resource loader + RTTI true','0f44d60 path format','366f140 binder API captures ordered list','__cxa_guard_acquire/release initialization guards'],'original_functions':['2656ac8','2656870','2657260'],'limits':'full BFRES parser, pose binding, resource failure and rendering not executed; list initializer366f280 separately read confirms preserved input order'}
(R/'analysis/completion/r8/graphics_binder_order.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(res))


