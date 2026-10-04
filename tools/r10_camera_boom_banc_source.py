"""Actual Fld_VSLobby Banc row -> original omitted SRT defaults and create-info.

Reuses r6 Banc matrix producer and SDK sinf/cosf. Original caller initializer
3cfdca4..cd4 executes with documented context-register/stack adapters, then
whole original Banc entry parser3d03768 consumes the actual source container.
This is not execution of the whole section/actor/physics resource loader.
"""
import json,hashlib,struct
from pathlib import Path
import spl_data
from r6_player_uc import PUC,STACK,STACK_SZ,LIBM1
from r5_player_libm_emu import Sdk
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/camera_100_r10/boom'
PATH=ROOT/'analysis/range/pack_LobbyVersus/Banc/Lby_Lobby00.bcett.byml'

def native_banc_matrix(u):
 raw=PATH.read_bytes();data=spl_data.byml(raw)
 selected=[(i,a) for i,a in enumerate(data['Actors']) if a['Gyaml']=='Fld_VSLobby']
 assert len(selected)==1
 index,actor=selected[0]
 src=u.alloc(len(raw));u.mu.mem_write(src,raw)
 by=spl_data.Byml(raw);holder=u.alloc(16);result=u.alloc(8)
 u.wq(holder,src);u.wq(holder+8,src+by.root_off)
 name=u.alloc(8);u.mu.mem_write(name,b'Actors\0')
 errors=[['nativeFindActors',u.call(0x71037d21fc,holder,result,name)]]
 assert u.r8(result+4)==0xc0
 u.wq(holder+8,src+u.r32(result))
 errors.append(['nativeSelectActor',u.call(0x71037d204c,holder,result,index)])
 assert u.r8(result+4)==0xc1
 u.wq(holder+8,src+u.r32(result))
 # Execute actual initializer before its parser call. x19/x23 are original
 # entry+18/+48, x24/w26 come from actual static constant via GOT5790808.
 sp=STACK+STACK_SZ-0x10000;entry=sp+0xa0;frame=sp+0x400
 u.mu.reg_write(UC_ARM64_REG_SP,sp);u.mu.reg_write(UC_ARM64_REG_X29,frame)
 for reg in (UC_ARM64_REG_X10,UC_ARM64_REG_X25):u.mu.reg_write(reg,0x7105790000)
 u.mu.emu_start(0x7103cfdbe8,0x7103cfdbf0,count=4)
 const=u.x(10)
 u.mu.reg_write(UC_ARM64_REG_X24,u.rq(const));u.mu.reg_write(UC_ARM64_REG_W26,u.r32(const+8))
 u.mu.reg_write(UC_ARM64_REG_X19,entry+0x18);u.mu.reg_write(UC_ARM64_REG_X23,entry+0x48)
 u.mu.reg_write(UC_ARM64_REG_X9,src);u.mu.reg_write(UC_ARM64_REG_X8,src+u.r32(result))
 u.mu.reg_write(UC_ARM64_REG_X25,u.rq(0x71057901f8))
 u.mu.emu_start(0x7103cfdca4,0x7103cfdcd4,count=14)
 defaults=list(struct.unpack('<9f',u.mu.mem_read(entry,36)))
 errors.append(['nativeBancEntryParser',u.call(0x7103d03768,entry,holder)])
 parsed=list(struct.unpack('<9f',u.mu.mem_read(entry,36)))
 assert defaults==[0,0,0,0,0,0,1,1,1] and parsed==defaults and u.r8(entry+0x75)==1
 assert u.rq(entry+0x38)==actor['Hash']
 create=u.alloc(0x200);parent=u.alloc(48)
 # Existing r6 proves Lby section default parent+260 is this original matrix.
 u.mu.mem_write(parent,bytes(u.mu.mem_read(0x7104a98200,48)))
 sdk=Sdk();native_libm=[]
 def math_boundary(kind,val):
  out=sdk.call(kind,val);native_libm.append({'kind':kind,'input':val,'output_bits':hex(out)})
  return struct.unpack('<f',struct.pack('<I',out))[0]
 # Reuse the harness's single PLT boundary, replacing its math implementation
 # with actual SDK execution. An additional later hook would double-evaluate
 # cosf(cosf(0)); that failed attempt is retained separately.
 previous={kind:LIBM1[kind] for kind in ('sinf','cosf')}
 for kind in previous:LIBM1[kind]=lambda val,kind=kind:math_boundary(kind,val)
 try:errors.append(['nativeBancCreateMatrix',u.call(0x7103d03f4c,entry,create,parent)])
 finally:LIBM1.update(previous)
 values=list(struct.unpack('<15f',u.mu.mem_read(create+0x40,60)))
 xyz=values[:3];rot=values[3:12];mtx=[rot[0],rot[1],rot[2],xyz[0],rot[3],rot[4],rot[5],xyz[1],rot[6],rot[7],rot[8],xyz[2]]
 expected=struct.pack('<15f',0,0,0,1,0,0,0,1,0,0,0,1,1,1,1)
 actual=bytes(u.mu.mem_read(create+0x40,60))
 rec={'scope':__doc__,'source':str(PATH.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),
      'actorIndex':index,'actorData':actor,'omittedFields':[k for k in ('Translate','Rotate','Scale') if k not in actor],
      'initializer':'original3cfdca4..cd4; scale constant loaded through actual GOT5790808=4a98180',
      'initialSRT':defaults,'parsedSRT':parsed,'entryHash':str(u.rq(entry+0x38)),
      'createActualBits':actual.hex(),'createExpectedBits':expected.hex(),'createValues':values,'f32Fields':15,
      'mismatches':sum(actual[i:i+4]!=expected[i:i+4] for i in range(0,60,4)),
      'matrix34':mtx,'scale':values[12:15],'errors':errors,'SDKOriginalLibm':native_libm,
      'parentBoundary':'actual original constant4a98200; Lby identity section supplier3cfa6bc/3cfc140 established in r6 stage_misc5.1'}
 assert rec['mismatches']==0 and all(x[1] is None for x in errors)
 return mtx,rec

def main():
 u=PUC();_,out=native_banc_matrix(u)
 out.update(null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used)
 (OUT/'banc_source.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
