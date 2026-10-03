"""r9 original hcl effective damping + Verlet integration, independent f32 pipeline.
No pow/math stub. SDK pow-like helper 8A63E0 and DC42A0/EE41F0 run native.
Only allocator/free, no force/profiler, ReferSymbol fixture; synthetic legal objects.
"""
import sys,struct,json,random
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import STUB,END
F=np.float32; U=lambda x:struct.unpack('<I',struct.pack('<f',float(x)))[0]
B=lambda x:F(struct.unpack('<f',struct.pack('<I',int(x)&0xffffffff))[0])
S=lambda x:x-(1<<32) if x&0x80000000 else x
A=lambda a,b:F(F(a)+F(b));D=lambda a,b:F(F(a)-F(b));M=lambda a,b:F(F(a)*F(b));V=lambda a,b:F(F(a)/F(b))
def pow_native_math(base,exponent):
 # Scalar expression of original four-lane log/exp polynomial, every op rounded f32.
 x=F(base); sub=x<B(0x00800000);x=M(x,B(0x4b000000)) if sub else x
 zbits=(U(x)+0xc0cb0000)&0xff800000
 k=M(F(S(zbits)),B(0x34000000));k=A(F(-23) if sub else F(0),k)
 z=B((U(x)-zbits)&0xffffffff);h=V(F(1),A(z,F(1)));r=M(D(z,F(1)),h)
 err=M(h,A(M(-D(z,F(1)),r),D(D(z,F(1)),A(r,r))))
 r2=M(r,r)
 p=A(M(r2,B(0x3e049000)),B(0x3e1163fe));p=A(M(r2,p),B(0x3e4cd0bb));p=A(M(r2,p),B(0x3eaaaaa8))
 t=A(M(r2,err),M(r,M(r,A(F(0),M(r,A(err,err))))))
 # retain the two separately rounded compensation terms from native log polynomial
 t=A(M(p,t),err);t=A(M(M(r,r2),p),t)
 hi=M(k,B(0x3eb17218));sumhi=A(hi,r);corr=D(r,D(sumhi,hi));t=A(corr,t)
 low=A(t,M(k,B(0xb082e308)));logx=A(A(sumhi,sumhi),A(low,low));y=M(F(exponent),logx)
 n=A(A(M(y,B(0x3fb8aa3b)),B(0x4b400000)),B(0xcb400000));ni=int(n)
 rem=A(A(y,M(n,B(0xbf317200))),M(n,B(0xb5bfbe8e)))
 pe=A(M(rem,B(0x3ab52000)),B(0x3c09383f));pe=A(M(rem,pe),B(0x3d2aad87));pe=A(M(rem,pe),B(0x3e2aaa19));pe=A(M(rem,pe),B(0x3efffffa));pe=A(M(rem,pe),F(1));pe=A(M(rem,pe),F(1))
 # The last native sequence is 1 + rem * (1 + rem * polynomial).
 out=pe
 adjust=0 if ni>0 else 0x83000000
 out=M(out,B((adjust+0x7f000000)&0xffffffff));out=M(out,B(((ni<<23)-adjust)&0xffffffff))
 if y>B(0x42b170a4):out=B(0x7f7fffee)
 if y<B(0xc2aea8f6):out=F(0)
 return out

def main():
 sys.stdout.reconfigure(encoding='utf-8');e=GUC();rng=random.Random(0xcffc88)
 a=e.alloc(16);b=e.alloc(16);bad=[]
 for i in range(4096):
  base=F([.999,1,.5,.999999,1.5][i%5] if i<32 else rng.uniform(.001,1.8));exp=F([0,1/60,1/30,4/60,-1/60][i%5] if i<32 else rng.uniform(-.2,.4))
  e.mu.mem_write(a,struct.pack('<4f',*[float(base)]*4));e.mu.mem_write(b,struct.pack('<4f',*[float(exp)]*4));e.call(0x71008a63e0,a,b)
  got=e.mu.reg_read(UC_ARM64_REG_S0)&0xffffffff;expected=U(pow_native_math(base,exp))
  if got!=expected:
   bad.append({'i':i,'base':float(base),'exponent':float(exp),'got':hex(got),'expected':hex(expected)})
   if len(bad)>8:break
 print(json.dumps({'helper_cases':i+1,'bad':bad},ensure_ascii=False))
 if bad:raise SystemExit(1)
 # Native operator init and force-free integration: real helper/math, explicit memory fixtures.
 tls=e.alloc(0x100);hc=e.alloc(0x400);router=e.alloc(0x100);arena=e.alloc(0x60);scratch=e.alloc(0x400)
 e.mu.reg_write(UC_ARM64_REG_TPIDR_EL0,tls);e.wq(tls+0x68,hc);e.wq(hc+0x3d0,router);e.wq(router+0x10,arena);e.wq(arena+8,1)
 e.wq(0x71057d7088,STUB+0x820);e.wq(0x71057d7090,STUB+0x828)
 def alloc_hook(mu,a,size,user):
  if a==STUB+0x820:mu.reg_write(UC_ARM64_REG_X0,scratch)
 e.mu.hook_add(UC_HOOK_CODE,alloc_hook,begin=STUB+0x820,end=STUB+0x828)
 def invalid(mu,access,address,size,value,user):print('invalid',hex(mu.reg_read(UC_ARM64_REG_PC)),hex(address));return False
 e.mu.hook_add(UC_HOOK_MEM_INVALID,invalid)
 sim=e.alloc(0x300);data=e.alloc(0x300);parts=e.alloc(16*9);cur=e.alloc(16*9);prev=e.alloc(16*9);op=e.alloc(0x70);cfg=e.alloc(0x30);ctx=e.alloc(0x20);world=e.alloc(0x128);ci=e.alloc(0x200);cd=e.alloc(0x100);arr=e.alloc(8)
 e.wq(sim+0x18,data);e.wq(data+0x40,parts);e.wq(sim+0x20,cur);e.wq(sim+0x30,prev)
 e.wq(op+0x50,cfg);e.u32(op+0x20,0x7fffffff);e.wq(ctx+8,world);e.wq(ctx+16,ci);e.wq(ci+0x40,arr);e.wq(arr,sim);e.wq(ci+0x18,cd)
 examples=[];steps=0
 for i in range(1024):
  dt=F([1/60,1/30,4/60,-1/60][i%4] if i<32 else rng.uniform(.002,.2));damp=F([0,.001,.5,1,1.2,-.2][i%6] if i<32 else rng.uniform(-.1,1.2));sub=1+i%4;scale=F([.5,1,2][i%3]);kind=1 if i%5==0 else 2;n=1+i%9
  effective=V(dt,M(F(1) if kind==1 else scale,F(sub)))
  grav=np.array([0,-9.81,0,0],dtype='<f4') if i%2==0 else np.array([rng.uniform(-10,10) for _ in range(4)],dtype='<f4')
  e.mu.mem_write(data+0x20,grav.tobytes());e.f32(data+0x30,damp);e.u32(sim+0x140,kind);e.f32(sim+0x144,scale);e.f32(sim+0x50,0);e.f32(sim+0x54,.31);e.mu.mem_write(cfg+0x28,bytes([sub]));e.f32(ctx,dt)
  e.call(0x7100dc42a0,op,ctx);co=F(0) if damp>=1 else F(1) if damp==0 else pow_native_math(D(F(1),damp),effective)
  assert e.ru32(sim+0x54)==U(co),(i,'coefficient',e.ru32(sim+0x54),U(co))
  assert e.ru32(sim+0x50)==U(effective),(i,'dt',e.ru32(sim+0x50),U(effective))
  positions=np.array([[rng.uniform(-5,5) for _ in range(4)] for j in range(n)],dtype='<f4');old=np.array([[rng.uniform(-5,5) for _ in range(4)] for j in range(n)],dtype='<f4')
  props=np.array([[.7142857313156128,1.399999976158142,.05,.5] if j<n-2 else [0,0,.05,.5] for j in range(n)],dtype='<f4')
  e.mu.mem_write(cur,positions.tobytes());e.mu.mem_write(prev,old.tobytes());e.mu.mem_write(parts,props.tobytes());e.u32(sim+0x28,n)
  e.call(0x7100ee41f0,0,sim,fargs=(float(effective),))
  expected=np.empty_like(positions);dt2=M(effective,effective)
  for j in range(n):
   for c in range(4):
    accel=M(A(F(0),M(grav[c],props[j,0])),props[j,1]);delta=M(co,D(positions[j,c],old[j,c]));expected[j,c]=A(A(positions[j,c],delta),M(dt2,accel))
  got=bytes(e.mu.mem_read(cur,n*16));gotprev=bytes(e.mu.mem_read(prev,n*16))
  assert got==expected.tobytes(),(i,'integrate',np.frombuffer(got,dtype='<f4').reshape(n,4).tolist(),expected.tolist())
  assert gotprev==positions.tobytes(),(i,'prev')
  assert e.mu.reg_read(UC_ARM64_REG_PC)==END
  if i<12:examples.append({'dt':float(dt),'substeps':sub,'timeScale':float(scale),'instanceKind':kind,'effectiveDt':float(effective),'damping':float(damp),'coefficientBits':f'{U(co):08X}','particles':n})
  steps+=1
 assert set(e.plt_stubbed)<={'_ZN2nn4util11ReferSymbolEPKv'},set(e.plt_stubbed)
 out={'date':'2026-10-03','original':['8A63E0','DC42A0','D00038','EE41F0'],'helper_cases':4096,'coefficient_and_integrate_cases':steps,'mismatch':0,'SDKmath_stub':False,'fixtures':['synthetic hcl objects/force count0/profiler null','scratch allocation and free callbacks','nn::util ReferSymbol no-op via PLT'],'plt_fixtures':sorted(set(e.plt_stubbed)),'boundary':'exact damping and force-free integrate, constraints/collisions/complete final bone pose excluded','examples':examples}
 (Path(__file__).resolve().parents[2]/'analysis/completion/r9/graphics_cloth_damping_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))

if __name__=="__main__":main()
