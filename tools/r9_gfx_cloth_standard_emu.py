"""Original StandardLinkConstraint D47BD0; independent f32 correction and ARM estimate."""
import sys,struct,json,random,math
from pathlib import Path
import numpy as np
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from gfx4p_bphcl import open_bphcl,tree
from network_uc import END
F=np.float32;U=lambda v:struct.unpack('<I',struct.pack('<f',float(v)))[0];B=lambda v:F(struct.unpack('<f',struct.pack('<I',v&0xffffffff))[0])
M=lambda a,b:F(F(a)*F(b));A=lambda a,b:F(F(a)+F(b));D=lambda a,b:F(F(a)-F(b))
def rsqrte(v):
 bits=U(v);exp=(bits>>23)&255
 if v==0:return F(float('inf'))
 assert 0<exp<255
 a=((bits>>16)&127)|128 if exp&1 else ((bits>>15)&255)|256
 a=2*a+1 if exp&1 else 4*(a//2)+2;b=512
 while a*(b+1)*(b+1)<(1<<28):b+=1
 res=(b+1)//2;return B((((380-exp)//2)<<23)|((res&255)<<15))
def expected(pa,pb,wa,wb,rest,stiff,scalar):
 if not scalar>0:return pa,pb
 delta=np.array([D(pb[k],pa[k]) for k in range(4)],dtype='<f4')
 sq=A(A(M(delta[0],delta[0]),M(delta[1],delta[1])),M(delta[2],delta[2]))
 est=rsqrte(sq)
 inv=F(0) if sq<=0 else M(est,F((3-float(sq)*float(M(est,est)))*.5))
 length=M(sq,inv);q=M(M(D(length,rest),stiff),scalar)
 diff=np.array([M(M(delta[k],inv),q) for k in range(4)],dtype='<f4')
 aa=np.array([A(pa[k],M(diff[k],wa)) for k in range(4)],dtype='<f4');bb=np.array([D(pb[k],M(diff[k],wb)) for k in range(4)],dtype='<f4')
 return aa,bb

def main():
 sys.stdout.reconfigure(encoding='utf-8');e=GUC();rng=random.Random(0xd47bd0)
 tls=e.alloc(0x80);hc=e.alloc(0x400);e.mu.reg_write(UC_ARM64_REG_TPIDR_EL0,tls);e.wq(tls+0x68,hc)
 c=e.alloc(0x40);ln=e.alloc(12);sim=e.alloc(0x50);data=e.alloc(0x60);parts=e.alloc(0x20);pos=e.alloc(0x20)
 e.wq(c+0x28,ln);e.u32(c+0x30,1);e.wq(sim+0x18,data);e.wq(data+0x40,parts);e.wq(sim+0x20,pos)
 plans=[];raw=tree(open_bphcl('analysis/render/bphcl/Har_SQD000_F.bphcl'),14);asset=[]
 for nv in raw['namedVariants']:
  v=nv.get('variant') or {}
  for cd in v.get('clothDatas',[]):
   for sc in cd['simClothDatas']:
    for cs in sc['staticConstraintSets']:
     if cs.get('$type')=='hclStandardLinkConstraintSet':
      for link in cs['links']:
       wa=F(sc['particleDatas'][link['particleA']]['invMass']);wb=F(sc['particleDatas'][link['particleB']]['invMass']);st=F(link['stiffness']);eff=M(st,A(wa,wb))
       assert U(eff)==0x3f800000
       asset.append({'cloth':cd['name'],'A':link['particleA'],'B':link['particleB'],'invMassBits':[f'{U(wa):08X}',f'{U(wb):08X}'],'stiffnessBits':f'{U(st):08X}','effectiveKBits':f'{U(eff):08X}'})
       plans.append((wa,wb,F(link['restLength']),st,F(1)))
 plans.extend((F(rng.uniform(0,3)),F(rng.uniform(0,3)),F(rng.uniform(0,.9)),F(rng.uniform(0,1)),F([0,-.5,.25,1,2][i%5])) for i in range(1024))
 for i,(wa,wb,rest,stiff,scalar) in enumerate(plans):
  pa=np.array([rng.uniform(-2,2) for _ in range(4)],dtype='<f4');pb=np.array([rng.uniform(-2,2) for _ in range(4)],dtype='<f4')
  e.mu.mem_write(ln,struct.pack('<HHff',0,1,float(rest),float(stiff)));e.f32(parts+4,wa);e.f32(parts+0x14,wb);e.mu.mem_write(pos,pa.tobytes()+pb.tobytes())
  e.call(0x7100d47bd0,c,sim,fargs=(float(scalar),));aa,bb=expected(pa,pb,wa,wb,rest,stiff,scalar)
  got=bytes(e.mu.mem_read(pos,32));want=aa.tobytes()+bb.tobytes()
  assert got==want,(i,'bits',np.frombuffer(got,dtype='<f4').tolist(),np.frombuffer(want,dtype='<f4').tolist())
  assert e.mu.reg_read(UC_ARM64_REG_PC)==END
 bendln=e.alloc(20);e.wq(c+0x28,bendln);bendplans=[];bendasset=[]
 for nv in raw['namedVariants']:
  for cd in (nv.get('variant') or {}).get('clothDatas',[]):
   for sc in cd['simClothDatas']:
    for cs in sc['staticConstraintSets']:
     if cs.get('$type')=='hclBendLinkConstraintSet':
      for link in cs['links']:
       wa=F(sc['particleDatas'][link['particleA']]['invMass']);wb=F(sc['particleDatas'][link['particleB']]['invMass']);lo=F(link['bendMinLength']);hi=F(link['stretchMaxLength']);kb=F(link['bendStiffness']);ks=F(link['stretchStiffness'])
       assert U(M(kb,A(wa,wb)))==0x3f800000 and U(M(ks,A(wa,wb)))==0x3f800000
       bendasset.append({'cloth':cd['name'],'A':link['particleA'],'B':link['particleB'],'bendKBits':f'{U(M(kb,A(wa,wb))):08X}','stretchKBits':f'{U(M(ks,A(wa,wb))):08X}'})
       bendplans.append((wa,wb,lo,hi,kb,ks,F(1)))
 bendplans.extend((F(rng.uniform(0,3)),F(rng.uniform(0,3)),F(.25),F(1),F(rng.uniform(0,1)),F(rng.uniform(0,1)),F([0,-.5,.25,1,2][i%5])) for i in range(2048))
 for i,(wa,wb,lo,hi,kb,ks,scalar) in enumerate(bendplans):
  pa=np.array([rng.uniform(-2,2) for _ in range(4)],dtype='<f4');delta=np.array([rng.uniform(-1,1) for _ in range(4)],dtype='<f4');delta[:3]*=F([0,.1,.5,2,4][i%5]);pb=np.array([A(pa[k],delta[k]) for k in range(4)],dtype='<f4');dd=np.array([D(pb[k],pa[k]) for k in range(4)],dtype='<f4')
  e.mu.mem_write(bendln,struct.pack('<HHffff',0,1,float(lo),float(hi),float(kb),float(ks)));e.f32(parts+4,wa);e.f32(parts+0x14,wb);e.mu.mem_write(pos,pa.tobytes()+pb.tobytes())
  e.call(0x7100d1c354,c,sim,fargs=(float(scalar),))
  if scalar>0:
   sq=A(A(M(dd[0],dd[0]),M(dd[1],dd[1])),M(dd[2],dd[2]));est=rsqrte(sq);inv=F(0) if sq<=0 else M(est,F((3-float(sq)*float(M(est,est)))*.5));length=M(sq,inv)
   q=M(D(M(max(F(0),D(length,hi)),ks),M(max(F(0),D(lo,length)),kb)),scalar)
   diff=np.array([M(M(dd[k],inv),q) for k in range(4)],dtype='<f4');aa=np.array([A(pa[k],M(diff[k],wa)) for k in range(4)],dtype='<f4');bb=np.array([D(pb[k],M(diff[k],wb)) for k in range(4)],dtype='<f4')
  else:aa,bb=pa,pb
  assert bytes(e.mu.mem_read(pos,32))==aa.tobytes()+bb.tobytes(),(i,'bend bits')
  assert e.mu.reg_read(UC_ARM64_REG_PC)==END
 assert not e.plt_stubbed,e.plt_stubbed
 out={'date':'2026-10-03','original':['D47BD0 whole','D1C354 whole'],'cases':len(plans),'mismatch':0,'native_ASM_RSQRT_estimate':'independent integer ARM-style estimate + single Newton refinement','asset_links':asset,'asset_effective_K_one':len(asset),'bend_cases':len(bendplans),'bend_asset_links':bendasset,'fixtures':['synthetic valid objects; profiling context null'],'stubs':[],'boundary':'Standard/Bend weighted coefficient and correction; no exporter history or final full pose'}
 (Path(__file__).resolve().parents[2]/'analysis/completion/r9/graphics_cloth_standard_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ('asset_links','bend_asset_links')},ensure_ascii=False))
if __name__=='__main__':main()
