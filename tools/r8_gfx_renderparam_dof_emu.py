"""Original RenderingDay typed getters and DOFGaussian apply writer; output fields only."""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import BASE
ROOT=Path(__file__).resolve().parents[2]; F=np.float32
u=GUC();rg=random.Random(0x2b68ef4);env=u.alloc(0x2b00);obj=u.alloc(0x898)
a=u.alloc(0x80);b=u.alloc(0x80);ra=u.alloc(0x200);rb=u.alloc(0x200);pa=u.alloc(0x100);pb=u.alloc(0x100);da=u.alloc(0x80);db=u.alloc(0x80)
for w,r,p,d in ((a,ra,pa,da),(b,rb,pb,db)):
 u.wq(w,BASE+0x5564930);h=u.alloc(0x160);u.wq(w+8,h);u.wq(h+0x158,r)
 u.mu.mem_write(r+0x82,b'\1\1');u.mu.mem_write(r+0x89,b'\1');u.wq(r+0x70,p);u.mu.mem_write(p+0x50,b'\1');u.wq(p+0x40,d)
 for f in range(0x41,0x46):u.mu.mem_write(d+f,b'\1')
u.wq(env+0x2ac8,obj); notify=[]
def hook(mu,pc,n,ctx):
 if pc==BASE+0x35e553c:
  notify.append(mu.reg_read(UC_ARM64_REG_X0));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
u.mu.hook_add(UC_HOOK_CODE,hook)
def lerp(x,y,t):return F(y+F(F(x-y)*t))
for i in range(1024):
 av=[F(rg.uniform(-10,1000)) for _ in range(4)];bv=[F(rg.uniform(-10,1000)) for _ in range(4)]
 t=F([0.,1.,-.5,.5,2.][i%5]); en=i&1; prev=(i>>1)&1
 u.mu.mem_write(obj,bytes(0x898));u.mu.mem_write(obj+0x1a8,bytes([prev]));u.mu.mem_write(obj+0x68,b'\0');u.u32(obj+0x7d0,4)
 for d,v in ((da,av),(db,bv)):
  u.mu.mem_write(d+0x30,struct.pack('<4f',*v));u.mu.mem_write(d+0x40,bytes([en]))
 assert u.call(BASE+0x10c4c20,a)==da and u.call(BASE+0x10c4c20,b)==db
 # Independently exercise the two other typed accessors against distinct sentinel pointers.
 u.wq(ra+0x78,0x34567000+i*8);u.wq(ra+0x58,0x45678000+i*8)
 assert u.call(BASE+0x10c4ad4,a)==0x34567000+i*8
 assert u.call(BASE+0x1158508,a)==0x45678000+i*8
 notify.clear();u.call(BASE+0x2b68ef4,a,env,b,fargs=(float(t),))
 expected={0x268:max(F(0),min(F(15),lerp(av[2],bv[2],t))),0x1e8:lerp(av[3],bv[3],t),0x208:lerp(av[0],bv[0],t),0x2a8:lerp(av[1],bv[1],t)}
 for off,v in expected.items():assert bytes(u.mu.mem_read(obj+off,4))==struct.pack('<f',v),(i,hex(off),u.rf32(obj+off),v)
 current=en if t==0 else prev
 assert u.mu.mem_read(obj+0x1a8,1)[0]==current
 assert u.ru32(obj+0x7d0)==(0 if t==0 else 4)
 assert u.mu.mem_read(obj+0x68,1)[0]==(0 if current and expected[0x2a8]<expected[0x1e8] else 1)
 assert all(z==obj+0x30 for z in notify)
u.wq(env+0x2ac8,0);u.call(BASE+0x2b68ef4,a,env,b,fargs=(.5,))
out={'cases':1024,'typed_getter_assertions':4096,'original':['0x71010c4ad4','0x71010c4c20','0x7101158508','0x7102b68ef4'],'fields_byte_match':True,'arithmetic_stubs':[], 'boundaries':['35e553c shader-program rebuild output sink (not executed)','synthetic local fields with set/inheritance flags=1; inherited resource walk not executed'],'external_services':sorted(set(u.plt_stubbed)),'null_dof_return':True,'limits':['DOF rendering/pixel math is not this test','object registration/constructor naming read only']}
(ROOT/'analysis/completion/r8/renderparam_dof_emu.json').write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps(out,indent=2))
