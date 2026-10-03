"""r7 graphics: agl Hermit2D original table[7] (358CFE0) vs independent f32 math.
Valid increasing X keys (2..7); no functions are stubbed. Data=(X,Y,normalized tangent).
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from r5_gfx_stage_emu import Emu,fbits
ROOT=Path(__file__).resolve().parents[2]
F=np.float32
FN=0x710358cfe0

def expected(data,t):
 data=list(map(F,data));t=F(t);n=len(data)//3
 if t<=data[0]:return data[1]
 if t>=data[(n-1)*3]:return data[(n-1)*3+1]
 for j in range(1,n):
  if data[j*3]>t:
   x0,y0,m0=data[(j-1)*3:j*3];x1,y1,m1=data[j*3:j*3+3]
   u=F(F(t-x0)/F(x1-x0))
   twice=F(u+u);twoSq=F(u*twice);twoCube=F(u*twoSq)
   threeU=F(u*F(3));threeSq=F(u*threeU)
   h00=F(F(twoCube-threeSq)+F(1));h01=F(threeSq-twoCube)
   sq=F(u*u);cube=F(u*sq);h10=F(u+F(cube-twoSq));h11=F(cube-sq)
   q=F(F(y1*h01)+F(y0*h00));q=F(F(m0*h10)+q);q=F(F(m1*h11)+q)
   return q
 raise ValueError('no valid segment')

def main():
 sys.stdout.reconfigure(encoding='utf-8');e=Emu();head=e.alloc(16);dptr=e.alloc(128)
 e.mu.mem_write(head,bytes([7,0,0,6])+b'\0'*12)
 setting=ROOT/'analysis/gfx4/scene_LobbyVersus/Gyml/LobbyVersusLockerTest.game__gfx__parameter__RenderingDay.bgyml.json'
 curves=json.loads(setting.read_text(encoding='utf-8'))['PostEffect']['ColorGrading']
 plans=[];original=[]
 for c in ('CurveColorR','CurveColorG','CurveColorB'):
  data=curves[c]['Data'];assert curves[c]['Type']=='Hermit2D'
  for t in [F(i)/F(7) for i in range(8)]+[F(-1),F(2),np.nextafter(F(0),F(1)),np.nextafter(F(1),F(0))]:plans.append((data,t,c))
 rng=random.Random(20261003)
 for _ in range(200):
  xs=sorted(rng.sample(range(-120,121),rng.randint(2,7)));data=[]
  for x in xs:data.extend([x/8,rng.uniform(-4,4),rng.uniform(-5,5)])
  ts=[xs[0]/8-1,xs[-1]/8+1]+[x/8 for x in xs]+[rng.uniform(xs[0]/8,xs[-1]/8) for _ in range(4)]
  plans.extend((data,t,'synthetic') for t in ts)
 ok=bad=0;examples=[]
 for data,t,source in plans:
  e.mu.mem_write(head+3,bytes([len(data)]));e.w(dptr,f'{len(data)}f',*data)
  e.call(FN,x=(head,dptr),s=(t,));actual=e.mu.reg_read(UC_ARM64_REG_S0);want=fbits(expected(data,t))
  if actual==want:ok+=1
  else:
   bad+=1
   if len(examples)<8:examples.append({'source':source,'data':data,'t':float(t),'got':f'{actual:08X}','want':f'{want:08X}'})
  if source!='synthetic' and 0<=F(t)<=1:original.append({'curve':source,'t':float(t),'value':e.rbits(actual),'bits':f'{actual:08X}'})
 result={'function':hex(FN),'table':'0x71057215e8[7]','ok':ok,'bad':bad,'cases':len(plans),'original_cases':36,'stubs':[],'inputs':str(setting.relative_to(ROOT)),'scope':'valid increasing X, 2..7 keys, endpoints/knots/outside and random segments; finite f32','original_samples':original,'examples':examples}
 (ROOT/'analysis/completion/r7/graphics_hermit2d_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ('function','ok','bad','cases','original_cases','stubs','examples')},ensure_ascii=False,indent=2))
 if bad:raise SystemExit(1)

from unicorn.arm64_const import UC_ARM64_REG_S0
Emu.rbits=staticmethod(lambda w:struct.unpack('<f',struct.pack('<I',w))[0])
if __name__=='__main__':main()
