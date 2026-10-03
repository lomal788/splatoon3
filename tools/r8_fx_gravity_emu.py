"""r8: original EmitterData+B5C writer and particle gravity consumer.
Original whole 08244c4, optional field addons disabled; air=1 avoids SDK powf.
Synthetic particle/matrix inputs + original emitter-data records. No code patch/stubs.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
from r7_fx_transform_emu import VM,F,MA,HEAP,STACK,END
ROOT=Path(__file__).resolve().parents[2]

def main():
 sys.stdout.reconfigure(encoding='utf-8'); vm=VM(); rng=random.Random(20261003)
 E,R,ER,A,M0,M1,M2,P,V,PIN,VIN=[HEAP+i*0x2000 for i in range(11)]
 vm.q(E+0xb0,R);vm.q(E+0x250,ER);vm.q(ER+0x18,R+0x70)
 vm.q(E+0x1f8,A);vm.q(E+0x220,M0);vm.q(E+0x228,M1);vm.q(E+0x230,M2)
 vm.fs(R+0xe0,[1]);vm.mu.mem_write(ER+3,b'\0')
 plans=[]
 for mode in (0,1):
  for follow in (0,1,2):
   for scale in (-1.,-0.,0.,.001,1.,4.):
    for k in range(64):
     mat=np.asarray([[rng.uniform(-3,3) for _ in range(3)] for _ in range(3)],dtype='<f4')
     if k%16==0:mat[:,k//16%3]=0
     plans.append((mode,follow,F(scale),[F(rng.uniform(-10,10)) for _ in range(3)],F(rng.choice([0.,.5,1.,2.])),F(rng.uniform(0,2)),[F(rng.uniform(-10,10)) for _ in range(4)],[F(rng.uniform(-2,2)) for _ in range(4)],mat,'synthetic'))
 raw=(ROOT/'analysis/assets_work/r6/static.vfxb').read_bytes()
 fields=json.loads((ROOT/'analysis/vfx/emitters_v46_fields.json').read_text(encoding='utf-8'))
 sources=[]
 for name,rec in fields.items():
  off=int(rec['off'],16); b=raw[off:off+0xef0]
  sc=struct.unpack_from('<f',b,0xb5c)[0];g=struct.unpack_from('<3f',b,0xb60);mode=b[0xb39];follow=b[0xa93]
  sources.append({'name':name,'offset':hex(off),'scale_bits':hex(struct.unpack_from('<I',b,0xb5c)[0]),'mode':mode,'follow':follow})
  plans.append((mode,follow,F(sc),list(map(F,g)),F(1),F(1),list(map(F,[1,2,3,0])),list(map(F,[.1,.2,.3,0])),np.eye(3,dtype='<f4'),name))
 bad=[];writer_ok=0;fields_ok=0
 for j,(mode,follow,sc,g,dt,life,pin,vin,mat,label) in enumerate(plans):
  # Exact original inline writer; ER+10 points to EmitterData, x10=E+760.
  vm.q(ER+0x10,R);vm.fs(R+0xb5c,[sc]);vm.mu.reg_write(UC_ARM64_REG_X8,ER);vm.mu.reg_write(UC_ARM64_REG_X10,E+0x760)
  vm.mu.emu_start(0x710080da10,0x710080da1c,count=3)
  writer_ok+=bytes(vm.mu.mem_read(E+0x7fc,4))==struct.pack('<f',sc)
  vm.fs(R+0xb60,g);vm.mu.mem_write(R+0xb39,bytes([mode]));vm.mu.mem_write(R+0xa93,bytes([follow]));vm.fs(E+0x50,[dt]);vm.fs(A+0xc,[life]);vm.fs(PIN,pin);vm.fs(VIN,vin)
  for addr,row in zip((M0,M1,M2),mat):vm.fs(addr,list(row)+[0])
  for addr,row in zip((E+0x4a0,E+0x4b0,E+0x4c0),mat):vm.fs(addr,list(row)+[0])
  vm.call(0x71008244c4,P,V,HEAP+0x18000,HEAP+0x1a000,E,0,PIN,VIN,fargs=(.5,))
  pos=[F(pin[i]+F(vin[i]*F(dt*life))) for i in range(4)]
  vel=vin[:]
  if sc>0:
   gv=[F(sc*x) for x in g]
   if mode==0:acc=gv
   elif follow==1:
    cols=[]
    for c in range(3):
     col=list(mat[:,c]);sq=[F(x*x) for x in col];mag=F(np.sqrt(F(F(sq[2]+sq[0])+sq[1])))
     cols.append([F(x*F(F(1)/mag)) for x in col] if mag>0 else [F(0)]*3)
    acc=[MA(col[2],gv[2],MA(col[1],gv[1],F(col[0]*gv[0]))) for col in cols]
   else:acc=[MA(row[2],gv[2],MA(row[1],gv[1],F(row[0]*gv[0]))) for row in mat]
   vel=[F(vin[i]+F(acc[i]*dt)) for i in range(3)]+[F(0)]
  actual=bytes(vm.mu.mem_read(P,16))+bytes(vm.mu.mem_read(V,16));expected=np.asarray(pos+vel,dtype='<f4').tobytes()
  fields_ok+=sum(a==b for a,b in zip(struct.unpack('<8I',actual),struct.unpack('<8I',expected)))
  if actual!=expected and len(bad)<8:bad.append({'case':j,'label':label,'mode':mode,'follow':follow,'matrix':mat.tolist(),'actual':list(struct.unpack('<8f',actual)),'expected':list(map(float,pos+vel))})
 # NaN in original B.LE/B.GT skips gravity (unordered NZCV=0011).
 vm.fs(E+0x7fc,[float('nan')]);vm.mu.mem_write(R+0xb39,b'\0');vm.fs(VIN,[1,2,3,4]);vm.call(0x71008244c4,P,V,HEAP+0x18000,HEAP+0x1a000,E,0,PIN,VIN,fargs=(.5,))
 nan=list(struct.unpack('<4f',vm.mu.mem_read(V,16)));assert nan==[1.,2.,3.,4.]
 result={'writer':'0x710080da10..da1c','consumer':'0x71008244c4','cases':len(plans),'writer_ok':writer_ok,'f32_fields':8*len(plans),'fields_ok':fields_ok,'mismatch':8*len(plans)-fields_ok,'original_data_cases':len(sources),'original_data_inputs':sources,'nan_air_one':{'gravity_skipped':True,'velocity':nan},'stubs':[],'scope':'whole function; air=1, optional field addons ER+3=0; synthetic particle/transform; no entire renderer','examples':bad}
 (ROOT/'analysis/completion/r8/fx_gravity_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='original_data_inputs'},ensure_ascii=False,indent=2))
 if result['mismatch']:raise SystemExit(1)
if __name__=='__main__':main()
