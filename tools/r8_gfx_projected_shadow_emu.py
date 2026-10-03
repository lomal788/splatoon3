"""Original ProjShadow typed apply and native matrix/density uniform consumer."""
import json, random, struct, sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import BASE
ROOT=Path(__file__).resolve().parents[2]; F=np.float32
u=GUC(); rg=random.Random(0x2800)
env=u.alloc(0x2b00); obj=u.alloc(0x600); a=u.alloc(0x80); b=u.alloc(0x80)
projs=[]
for w in (a,b):
 r=u.alloc(0x200);h=u.alloc(0x160); sh=u.alloc(0x80);p=u.alloc(0x80)
 u.wq(w,BASE+0x5564930);u.wq(w+8,h);u.wq(h+0x158,r);u.wq(r+0x78,sh)
 u.mu.mem_write(r+0x82,b'\1');u.wq(sh+0x38,p);u.mu.mem_write(sh+0x40,b'\1');u.mu.mem_write(p+0x54,b'\1'*6);projs.append(p)
u.wq(env+0x2800,obj)
mp={0x30:[0x5ac,0x5b0],0x34:[0x440],0x38:[0x420],0x3c:[0x360],0x40:[0x364],0x44:[0x380],0x48:[0x384],0x4c:[0x400],0x50:[0x404]}
def mix(a,b,t): return F(b+F(F(a-b)*t))
for i in range(1024):
 vals=[[F(rg.uniform(-100,100)) for _ in range(9)] for j in range(2)]
 t=F([0,1,.5,-.5,2][i%5]); prior=bytes(rg.randrange(256) for _ in range(0x600));u.mu.mem_write(obj,prior)
 for p,arr in zip(projs,vals):u.mu.mem_write(p+0x30,struct.pack('<9f',*arr))
 want=bytearray(prior)
 for j,(src,dsts) in enumerate(mp.items()):
  for dst in dsts:struct.pack_into('<f',want,dst,mix(vals[0][j],vals[1][j],t))
 u.call(BASE+0x2b66c54,a,env,b,fargs=(float(t),))
 assert bytes(u.mu.mem_read(obj,0x600))==want,('apply',i)
 # Direct-resource apply is a separate native consumer, not a reimplementation.
 want=bytearray(prior);u.mu.mem_write(obj,prior)
 for j,(src,dsts) in enumerate(mp.items()):
  for dst in dsts:struct.pack_into('<f',want,dst,vals[0][j])
 u.call(BASE+0x1152ed8,a,env)
 assert bytes(u.mu.mem_read(obj,0x600))==want,('direct',i)
u.wq(env+0x2800,0);u.call(BASE+0x2b66c54,a,env,b,fargs=(.5,));u.call(BASE+0x1152ed8,a,env);u.wq(env+0x2800,obj)
par=u.alloc(0x100);ctx=u.alloc(0x20);vr=u.alloc(0x100);frame=u.alloc(0x1600);mgr=u.alloc(0x30);pool=u.alloc(0xd00);slice=u.alloc(0x60);ubo=u.alloc(0x1b0);blank=u.alloc(0x50)
u.wq(par+0xd8,ctx);u.wq(ctx,env);u.wq(ctx+8,vr);u.wq(env+0xf08,frame);u.wq(BASE+0x5999e38,mgr);u.wq(mgr+0x18,pool);u.wq(pool+0xca0,slice);u.wq(BASE+0x5999230,blank)
for off in [0x20,0x40]:u.wq(blank+off,0x77000000+off)
for off in [0x28,0x40,0x58,0xb8]:u.wq(vr+off,0x88000000+off)
binds=[];services=[]
def hook(mu,pc,n,ctx):
 if pc==BASE+0x37af558:
  binds.append((mu.reg_read(UC_ARM64_REG_X1),mu.reg_read(UC_ARM64_REG_X2)))
 elif pc==BASE+0x0837ac0:
  assert mu.reg_read(UC_ARM64_REG_X3)==0x1b0;mu.reg_write(UC_ARM64_REG_X0,ubo);services.append('uniform allocator')
 elif pc==BASE+0x3e9aa00:
  mu.reg_write(UC_ARM64_REG_X0,1);services.append('TLS core index fixture')
 else:return
 mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
u.mu.hook_add(UC_HOOK_CODE,hook)
identity=b''.join(u.mu.mem_read(BASE+x,16) for x in [0x4997c90,0x4998180,0x4997170])
for i in range(1024):
 count=i%2;enabled=(i>>1)%2;density=F([-.1,0.,.25,1.,2.,100.][i%6]);factor=F(rg.uniform(-2,3));matrix=bytes(rg.randrange(256) for _ in range(48));viewmatrix=bytes(rg.randrange(256) for _ in range(64))
 u.u32(env+0x27f8,count);u.mu.mem_write(obj+0x5b8,bytes([enabled]));u.f32(obj+0x5ac,density);u.f32(obj+0x4e8,factor);u.mu.mem_write(obj+0x530,matrix);u.mu.mem_write(env+0x2240,viewmatrix);u.mu.mem_write(ubo,bytes(0x1b0));binds.clear()
 u.call(BASE+0x37ab8e0,0,par)
 want=F(F(max(0,min(1,float(factor))))*F(max(0,min(1,float(density))))) if count else F(0)
 assert bytes(u.mu.mem_read(ubo+0x110,48))==(matrix if count else identity),(i,'matrix')
 assert bytes(u.mu.mem_read(ubo+0xd0,64))==viewmatrix
 assert bytes(u.mu.mem_read(ubo+0x1a0,4))==struct.pack('<f',want),(i,'density',u.rf32(ubo+0x1a0),want)
 assert (0xe,0x88000058 if count and enabled else 0x77000040) in binds
 assert u.rq(slice+0x10)==ubo and u.rq(slice+0x40)==0x1b0
assert set(u.plt_stubbed)<={'_ZN2nn2os11GetTlsValueENS0_7TlsSlotE'},set(u.plt_stubbed)
out={'date':'2026-10-03','blend_apply':1024,'direct_apply':1024,'native_uniform_consumer':1024,'mismatch':0,'whole_target_bytes':0x600,'native':['7102b66c54','7101152ed8','71037ab8e0'],'null_target_return':True,'arithmetic_or_field_writer_stubs':[],'services':sorted(set(services))+['37af558 texture-binding output sink'],'unknown_PLT':sorted(set(u.plt_stubbed)-{'_ZN2nn2os11GetTlsValueENS0_7TlsSlotE'}),'TLS_helper_hooks':len(u.plt_stubbed),'limits':['local resource set flags=1; inheritance walk not executed','scene env2800 target constructor/type/creation unresolved','shadow matrix producer and factor4e8 producer unresolved','GPU shader/pixels not executed','NaN/inf not tested']}
(ROOT/'analysis/completion/r8/projected_shadow_emu.json').write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps(out,indent=2))

