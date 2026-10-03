"""r7 fx: nn::vfx emitter transform 080e4cc, original no-stub execution.
SDK nn::util numeric constant imports are bound by exact dynamic symbol names.
Comparison: independent float32/FMA SRT polynomial implementation; synthetic field inputs.
"""
import ctypes,json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm64_const import *
from r5_player_libm_emu import symbols
ROOT=Path(__file__).resolve().parents[2]
BASE,SDKBASE,HEAP,STACK,END=0x7100000000,0x7400000000,0x20000000,0x10000000,0x30000000
F=np.float32
crt=ctypes.CDLL('ucrtbase'); crt.fmaf.argtypes=[ctypes.c_float]*3; crt.fmaf.restype=ctypes.c_float
MA=lambda a,b,c:F(crt.fmaf(float(a),float(b),float(c)))
def tags(d):
 mod=struct.unpack_from('<I',d,4)[0]; i=mod+struct.unpack_from('<i',d,mod+4)[0]; t={}
 while True:
  k,v=struct.unpack_from('<qQ',d,i); i+=16
  if not k:return t
  t.setdefault(k,v)
class VM:
 def __init__(self):
  d=(ROOT/'extracted/exefs/main.reloc.img').read_bytes(); sdk=(ROOT/'extracted/exefs/sdk.img').read_bytes(); ss=symbols(sdk)
  self.mu=m=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
  for addr,raw in ((BASE,d),(SDKBASE,sdk)):
   m.mem_map(addr,(len(raw)+0xffff)&~0xffff);m.mem_write(addr,raw)
  for addr,size in ((HEAP,0x100000),(STACK,0x100000),(END,0x1000)):m.mem_map(addr,size)
  m.reg_write(UC_ARM64_REG_CPACR_EL1,0x300000)
  t=tags(d); self.imports={}
  for tab,size in ((t.get(7,0),t.get(8,0)),(t.get(23,0),t.get(2,0))):
   for i in range(tab,tab+size,24):
    off,inf,ad=struct.unpack_from('<QQq',d,i);no,_,_,sh,val,_=struct.unpack_from('<IBBHQQ',d,t[6]+(inf>>32)*24)
    name=d[t[5]+no:d.index(b'\0',t[5]+no)].decode()
    if not sh and name.startswith('_ZN2nn4util6detail') and name in ss and any(k in name for k in ("Coefficients","Float","SinCosSampleTable","AngleIndexHalfRound")):
     m.mem_write(BASE+off,struct.pack('<Q',SDKBASE+ss[name][0]+ad));self.imports[name]=hex(BASE+off)
  self.const={n:np.frombuffer(sdk[v:v+s],dtype='<f4').tolist() for n,(v,s) in ss.items() if n.startswith('_ZN2nn4util6detail') and ('Coefficients' in n or 'Float' in n)}
 def q(self,a,x):self.mu.mem_write(a,struct.pack('<Q',x))
 def w(self,a,x):self.mu.mem_write(a,struct.pack('<I',x&0xffffffff))
 def fs(self,a,x):self.mu.mem_write(a,struct.pack('<%df'%len(x),*map(float,x)))
 def call(self,fn,*args,fargs=()):
  for reg,v in zip((UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5,UC_ARM64_REG_X6,UC_ARM64_REG_X7),args):self.mu.reg_write(reg,v)
  for reg,v in zip((UC_ARM64_REG_S0,UC_ARM64_REG_S1,UC_ARM64_REG_S2),fargs):self.mu.reg_write(reg,struct.unpack('<I',struct.pack('<f',float(v)))[0])
  self.mu.reg_write(UC_ARM64_REG_SP,STACK+0xf0000);self.mu.reg_write(UC_ARM64_REG_LR,END)
  self.mu.emu_start(fn,END,count=200000)
  return self.mu.reg_read(UC_ARM64_REG_X0)

def sincos(v,cn):
 inv=F(cn['_ZN2nn4util6detail16Float1Divided2PiE'][0]); pi=F(cn['_ZN2nn4util6detail7FloatPiE'][0]); tp=F(cn['_ZN2nn4util6detail8Float2PiE'][0]); hp=F(cn['_ZN2nn4util6detail15FloatPiDivided2E'][0])
 a=F(F(v)*inv); k=F(int(F(a+F(.5 if a>=0 else -.5)))); v=MA(-k,tp,F(v)); pos=v>hp
 if pos:v=F(pi-v)
 neg=v<F(-hp)
 if neg:v=F(-pi-v)
 x=F(v*v)
 def poly(c):
  a=MA(-x,F(c[0]),F(c[1]));a=MA(x,a,F(-c[2]));a=MA(x,a,F(c[3]));a=MA(x,a,F(-c[4]));return MA(x,a,F(1))
 s=F(v*poly(cn['_ZN2nn4util6detail15SinCoefficientsE']));c=poly(cn['_ZN2nn4util6detail15CosCoefficientsE'])
 if pos or neg:c=F(-c)
 return s,c

def expected(vals,seed,cn):
 states=[];u=seed
 for _ in range(6):states.append(F(F(u)*F(2**-32)));u=(u*0x41c64e6d+0x3039)&0xffffffff
 rotations=[F(F(vals[6+i])+F(F(vals[9+i])*F(F(states[i]+states[i])-F(1)))) for i in range(3)]
 T=[F(F(vals[i])+F(F(vals[3+i])*F(F(states[3+i]+states[3+i])-F(1)))) for i in range(3)]
 sx,cx=sincos(rotations[0],cn);sy,cy=sincos(rotations[1],cn);sz,cz=sincos(rotations[2],cn)
 C0=[F(cz*cy),F(sz*cy),F(-sy)]
 C1=[F(F(F(cz*sy)*sx)-F(sz*cx)),F(F(F(sz*sy)*sx)+F(cz*cx)),F(cy*sx)]
 C2=[F(F(F(cz*sy)*cx)+F(sz*sx)),F(F(F(sz*sy)*cx)-F(cz*sx)),F(cy*cx)]
 cols=[C0,C1,C2,T]; sc=vals[12:15]
 scaled=[[F(x*F(sc[i])) for x in cols[i]] for i in range(3)]+[T]
 return cols,scaled,u

def main():
 sys.stdout.reconfigure(encoding='utf-8');vm=VM();rng=random.Random(20261007); E,R=HEAP,HEAP+0x2000;vm.q(E+0xb0,R)
 ok=bad=0;examples=[]
 plans=[[0.]*12+[1.,1.,1.],[1.,2.,3.,0.,0.,0.,.2,.3,.4,0.,0.,0.,2.,3.,4.]]
 plans += [[rng.uniform(-20,20) for _ in range(6)]+[rng.uniform(-12,12) for _ in range(6)]+[rng.uniform(-2,4) for _ in range(3)] for _ in range(400)]
 fields=json.loads((ROOT/"analysis/vfx/emitters_v46_fields.json").read_text(encoding="utf-8"))
 rawpath=ROOT/"analysis/assets_work/r6/static.vfxb"; raw=rawpath.read_bytes(); original_inputs=[]
 for name,e in fields.items():
  off=int(e["off"],16); rawname=raw[off+0x10:off+0x50].split(b"\0")[0].decode("utf-8")
  assert rawname==name.rsplit("/",1)[1],(name,rawname)
  vals=struct.unpack_from("<15f",raw,off+0xab0);plans.append(vals)
  original_inputs.append({"emitter":name,"offset":hex(off),"SRT_f32_bits":[f"{v:08X}" for v in struct.unpack_from("<15I",raw,off+0xab0)]})
 for k,vals in enumerate(plans):
  vals=list(map(F,vals));seed=rng.getrandbits(32);vm.fs(R+0xab0,vals);vm.w(E+0xbc,seed);vm.call(0x710080e4cc,E)
  cols,sc,u=expected(vals,seed,vm.const)
  got=bytes(vm.mu.mem_read(E+0x2e0,128)); actual=np.frombuffer(got,dtype='<f4').reshape(8,4)
  exp=np.array(sc+cols,dtype='<f4');g=actual[:,:3].tobytes();b=exp.tobytes();rseed=struct.unpack('<I',vm.mu.mem_read(E+0xbc,4))[0]
  if g==b and u==rseed:ok+=1
  else:
   bad+=1
   if len(examples)<8:examples.append({'case':k,'vals':list(map(float,vals)),'seed':seed,'actual':actual[:,:3].tolist(),'expected':exp.tolist(),'seedMatch':u==rseed})
 result={'function':'0x710080e4cc','cases':len(plans),'original_data_SRT_cases':len(fields),'original_data_source':str(rawpath.relative_to(ROOT)),'original_data_inputs':original_inputs,'ok':ok,'bad':bad,'compare':'24 active matrix f32 lanes + final RNG word; padding lanes excluded','stubs':[],'SDK_numeric_imports':vm.imports,'examples':examples}
 (ROOT/'analysis/completion/r7/fx_transform_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()

