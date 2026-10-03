"""r8 original LOD names, static queue and Mesh draw arguments; GPU/state boundaries explicit."""
import sys,json,struct,hashlib,gzip,zstandard
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
ROOT=Path(__file__).resolve().parents[2]
def F(x): return struct.unpack('<f',struct.pack('<f',x))[0]
def main():
 e=GUC(); rows=json.loads((ROOT/'analysis/graphics/rsdb/LODThreshold.json').read_text(encoding='utf-8')); byname={r['__RowId'].split('/')[-1].split('.')[0]:r for r in rows}
 rowkey=e.alloc(16);dest=e.alloc(0x108);buf=e.alloc(0x100);e.wq(dest+8,buf);e.u32(dest+0x10,0x100)
 names={}; nodes=[]
 for r in rows:
  e.wq(rowkey,e.cstr(r['__RowId']));e.call(0x71038c9e50,rowkey,dest);n=e._cstr(buf).decode();assert n==r['__RowId'].split('/')[-1].split('.')[0];h=e.call(0x7100f7694c,buf,0)&0xffffffff;assert h not in names;names[h]=n
  a=e.alloc(0x148);e.u32(a+0x20,h);e.wq(a+0x30,e.cstr(n));e.u32(a+0x38,0x100);nodes.append((h,a))
 def tree(ls):
  if not ls:return 0
  j=len(ls)//2;a=ls[j][1];e.wq(a+8,tree(ls[:j]));e.wq(a+0x10,tree(ls[j+1:]));return a
 mgr=e.alloc(0x50);e.wq(mgr+0x30,tree(sorted(nodes)))
 table=e.alloc(9*0x28);holder=e.alloc(0x28);e.u32(holder+0x10,9);e.wq(holder+0x18,table);e.wq(0x710599b420,holder)
 param=e.alloc(0x40);e.wq(table+0x140+0x20,param);e.wq(param+0x10,e.cstr('Work/Gyml'));e.wq(param+0x18,e.cstr('game__gfx__parameter__LODThreshold'));data=e.alloc(0x10)
 model=e.alloc(0x400);rec=e.alloc(0x80);resource=e.alloc(0x80);e.wq(model,0x7105727180);e.wq(model+0x100,resource);e.wq(model+0x38,rec);e.mu.mem_write(model+0x118,b'\1')
 state={'selected':None,'draw':[],'buffer':None};boundaries=[]
 def ret(mu,v=0):mu.reg_write(UC_ARM64_REG_X0,v);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 def hooks(mu,pc,size,unused):
  if pc==0x7100f44d60:
   obj=mu.reg_read(UC_ARM64_REG_X0);fmt=e._cstr(mu.reg_read(UC_ARM64_REG_X1)).decode();args=[e._cstr(mu.reg_read(r)).decode() for r in (UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4)];assert fmt=='%s/%s.%s.gyml';state['selected']=args[1];e.mu.mem_write(e.rq(obj+8),(fmt%tuple(args)).encode()+b'\0');ret(mu)
  elif pc==0x71013df5e4:
   p=mu.reg_read(UC_ARM64_REG_X1);path=e._cstr(e.rq(p)).decode();n=path.split('/')[-1].split('.')[0];assert n==state['selected'];r=byname[n];e.f32(data+8,r['EndDistFromBounding']);e.f32(data+12,r['StartDistFromBounding']);ret(mu,data)
  elif pc==0x71036ad36c:ret(mu,1) # unrelated shader/state binding accepted fixture boundary
  elif pc==0x710083d990:
   b=mu.reg_read(UC_ARM64_REG_X0);out=mu.reg_read(UC_ARM64_REG_X1);e.wq(out,0x90000000+b);e.wq(out+8,0x100000);state['buffer']=b;ret(mu)
  elif pc==0x710083db68:
   x=[mu.reg_read(r) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5,UC_ARM64_REG_X6,UC_ARM64_REG_X7)];x[3]=e.rq(x[3]);state['draw'].append(x);ret(mu)
 for p in (0x7100f44d60,0x71013df5e4,0x71036ad36c,0x710083d990,0x710083db68):e.mu.hook_add(UC_HOOK_CODE,hooks,begin=p,end=p)
 native=[]
 for nm in ('Player00','Player00_Hlf','Player01','Player02','Player02_Hlf','Player_Squid','Player_Octopus'):
  p=ROOT/'extracted/romfs/Model'/f'{nm}.bfres.zs';b=zstandard.ZstdDecompressor().decompress(p.read_bytes());q=lambda o:struct.unpack_from('<Q',b,o)[0];fmdl=0xf0;name=b[q(fmdl+8)+2:].split(b'\0')[0].decode();sh=q(fmdl+0x28);cnt=struct.unpack_from('<H',b,fmdl+0x6a)[0];lodmax=max(b[sh+j*0x60+0x5b] for j in range(cnt));native.append({'file':nm,'name':name,'shapeCount':cnt,'maxLod':lodmax,'compressed_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'raw':b,'shape':sh});assert name not in byname
 for n in list(byname)+[r['name'] for r in native]+['Fld_Test','FldBG_Test','Kbi_Test','Arbitrary_Far','Arbitrary']:
  e.wq(resource+8,e.cstr('xx'+n));state['selected']=None;e.mu.mem_write(rec,b'\0'*0x80);e.call(0x71010fe270,mgr,model)
  want=n if n in byname else ('SuffixFar' if n.endswith('_Far') else 'PrefixFld' if n.startswith('Fld_') else 'PrefixFldBG' if n.startswith('FldBG_') else 'PrefixKbi' if n.startswith('Kbi_') else 'Default');assert state['selected']==want,(n,state['selected'],want)
  r=byname[want];s=F(r['StartDistFromBounding']);a=F(s-F(F(r['EndDistFromBounding'])-s));inv=F(1/F(s-a)) if s!=a else 1;assert bytes(e.mu.mem_read(rec,12))==struct.pack('<fff',s,a,inv)
 # Queue uses original BfresModel shape getter; only shape/model metadata fixture.
 mi=e.alloc(0x40);views=e.alloc(0x7f0);shape=e.alloc(0x140);indices=e.alloc(2);shapePtrs=e.alloc(8);viewPtrs=e.alloc(8);entries=e.alloc(0x48);matview=e.alloc(8);matflags=e.alloc(12);queue=e.alloc(8);packet=e.alloc(0x30);ctx=e.alloc(0x300);drawmask=e.alloc(4);resShape=e.alloc(0x60);objShape=e.alloc(0x810);gpu=e.alloc(0x100);mesh=e.alloc(3*0x38);ubo=e.alloc(3*0x260)
 e.wq(model+0x30,mi);e.wq(model+0x28,indices);e.wq(model+0x190,shapePtrs);e.wq(shapePtrs,shape);e.mu.mem_write(model+0x20,struct.pack('<H',1));e.wq(shape,0x7105727f08);e.wq(shape+8,model);e.wq(shape+0x20,objShape);e.wq(objShape+8,resShape);e.wq(objShape+0x7f8,ubo);e.wq(resShape+0x18,mesh);e.mu.mem_write(mi+4,b'\1');e.wq(mi+0x18,viewPtrs);e.wq(viewPtrs,entries);e.wq(mi+0x28,matview);e.wq(mi+0x20,matflags);e.wq(views+0x200,queue);e.wq(ctx+0x20,gpu);e.u32(drawmask,1)
 queueCases=0;drawCases=0;dataSummary=[]
 for r in native:
  b=r['raw'];q=lambda p:struct.unpack_from('<Q',b,p)[0];sh=r['shape'];nm=q(sh+0x18);n=b[sh+0x5b];assert n==3;meshMeta=[]
  for j in range(n):
   p=nm+j*0x38;v=bytearray(b[p:p+0x38]);sdata=b[q(p):q(p)+8];sub=e.alloc(8);e.mu.mem_write(sub,sdata);ib=e.alloc(0x48);struct.pack_into('<Q',v,0,sub);struct.pack_into('<Q',v,0x10,ib);e.mu.mem_write(mesh+j*0x38,bytes(v));meshMeta.append((j,struct.unpack_from('<II',sdata),struct.unpack_from('<IIIIIH',b,p+0x20),ib))
  dataSummary.append({'name':r['name'],'bodyMeshCount':n,'meshIndexCounts':[m[1][1] for m in meshMeta]})
  for stage in range(3):
   for phase in range(4):
    for inst in (1,2,3):
     e.mu.mem_write(shape+0x18,bytes([0x30|(phase<<2)]));e.mu.mem_write(shape+0x12c,bytes([inst]));e.mu.mem_write(shape+0x129,b'\0');e.mu.mem_write(views+0x20c,b'\0'*4);e.mu.mem_write(entries,b'\0'*0x48);e.mu.mem_write(mi+8,b'\0'*4);e.mu.mem_write(matview,bytes([0,0,9,0])+struct.pack('<I',1));ep=bytearray(0x30);struct.pack_into('<III',ep,0x18,7,0,0xffffffff);ep[0x25]=stage;ep[0x26]=(stage+1)%3;struct.pack_into('<f',ep,0x28,-F(stage+.5));e.mu.mem_write(packet,bytes(ep));e.call(0x71036ab4e8,mi,views,model,packet+0x18)
     want=bytearray(0x48);struct.pack_into('<Q',want,8,shape);struct.pack_into('<f',want,4,-F(stage+.5));struct.pack_into('<I',want,0x10,1);struct.pack_into('<H',want,0x14,0xffff);want[0x17]=(phase<<2)|(stage<<4);assert bytes(e.mu.mem_read(entries,0x48))==want;assert e.rq(queue)==entries;assert struct.unpack('<I',e.mu.mem_read(views+0x20c,4))[0]==1;queueCases+=1
     e.mu.mem_write(ctx+0x36,bytes([phase]));e.mu.mem_write(ctx+0x35,b'\0');state['draw']=[];e.call(0x71036ba1a0,queue,1,ctx,drawmask,0xffff,0)
     m=meshMeta[stage];j,(suboff,subcount),meta,ib=m;offset,prim,shift,indexCount,firstV,subN=meta;assert len(state['draw'])==1;(x0,x1,x2,ga,x4,x5,x6,x7)=state['draw'][0];assert (x0,x1,x2,ga,x4,x5,x6,x7)==(gpu+8,prim,shift,0x90000000+ib+suboff,subcount,firstV,inst,0),(r['name'],stage,state['draw'],meta);drawCases+=1
  del r['raw']
 assert not e.plt_stubbed,e.plt_stubbed
 out={'date':'2026-10-03','name_parser_keys':len(rows),'name_selection_cases':len(byname)+len(native)+5,'queue_cases':queueCases,'draw_cases':drawCases,'mismatch':0,'native_models':native,'native_body_lods':dataSummary,'state_binding_stub':'36AD36C returns accepted shader/material fixture; excludes state binding proof','resource_services':['F44D60 snprintf','13DF5E4 RSDB row loader using original JSON','083D990 GPU buffer address getter','083DB68 final GPU draw command sink'],'LOD_algorithm_stubs':[],'GPU_executed':False,'dynamic_pose_executed':False,'plt_stubbed':e.plt_stubbed}
 (ROOT/'analysis/completion/r8/lod_draw_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:out[k] for k in ('name_parser_keys','name_selection_cases','queue_cases','draw_cases','mismatch','LOD_algorithm_stubs','GPU_executed')},ensure_ascii=False))
if __name__=='__main__':main()
