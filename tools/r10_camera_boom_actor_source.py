"""Actual RSDB actor tags -> original Ground ShapeTag enable supplier.

The runtime RSDB string-list/bit-matrix and Actor+348/+80/+128 holders are
explicit data-to-layout adapters. Original name lookup38c4a00 is reused from
r6; original membership38c4ed0 and whole functor12ea8c4 execute. No tag-return
or body/filter boolean callback is replaced. This is not a whole actor loader.
"""
import hashlib,json
from pathlib import Path
import spl_data
from r6_player_uc import PUC

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/camera_100_r10/boom'
PATH=ROOT/'extracted/romfs/RSDB/Tag.Product.100.rstbl.byml.zs'

def native_actor_tags(u):
 raw=spl_data.load(PATH);data=spl_data.byml(raw)
 rows=[data['PathList'][i:i+3] for i in range(0,len(data['PathList']),3)]
 tags=data['TagList'];bits=bytes.fromhex(data['BitTable']['__binary'])
 names=u.alloc(8*len(tags))
 for i,t in enumerate(tags):
  p=u.alloc(len(t.encode())+1);u.mu.mem_write(p,t.encode()+b'\0');u.wq(names+i*8,p)
 obj=u.alloc(0x100);bt=u.alloc(len(bits));u.mu.mem_write(bt,bits)
 u.w32(obj+0x60,len(tags));u.wq(obj+0x68,names);u.wq(obj+0x70,bt)
 manager=u.alloc(0x200);u.wq(manager+0x30,obj);u.wq(0x71059a9d10,manager)
 name_results=[]
 for name in ('Actor_MapParts_KeepOut','Actor_Lift_KeepOut'):
  p=u.alloc(len(name)+1);u.mu.mem_write(p,name.encode()+b'\0');h=u.alloc(8);u.wq(h,p)
  err=u.call(0x71038c4a00,obj+0x50,h)
  name_results.append({'name':name,'error':err,'actual':u.x(0),'expected':tags.index(name),'match':err is None and u.x(0)==tags.index(name)})
 group=next(i for i,r in enumerate(rows) if r==['Work/Actor/','Fld_VSLobby','.engine__actor__ActorParam.gyml'])
 rec={'source':str(PATH.relative_to(ROOT)),'sha256_decompressed':hashlib.sha256(raw).hexdigest(),
      'row_count':len(rows),'tag_count':len(tags),'bit_count':len(bits)*8,'bit_bytes':len(bits),
      'Fld_VSLobby_row':group,'Fld_VSLobby_path':rows[group],
      'native_name_lookup':name_results,'scope':__doc__}
 return obj,rows,tags,bits,rec

def actual_ground_tag_enable(u,B,LP):
 obj,rows,tags,bits,rec=native_actor_tags(u)
 actor=u.alloc(0x400);module=u.alloc(0x100);param=u.alloc(0x140);holder=u.alloc(8);functor=u.alloc(16)
 u.wq(actor+0x348,module);u.wq(module+0x80,param);u.w32(param+0x128,rec['Fld_VSLobby_row'])
 u.wq(holder,actor);u.wq(functor,0x7105576db8);u.wq(functor+8,holder)
 packet=u.alloc(0x140);u.wq(B+0x80,packet)
 # Native lazy caches start unresolved, so the whole original name lookup and
 # membership paths run rather than supplied true/false tag booleans.
 for flag in (0x71058e8c14,0x71058e8c74):u.w8(flag,0)
 before=u.r32(LP+8);err=u.call(0x71012ea8c4,functor,B)
 rec.update(functor_error=err,packet_D4=u.r32(packet+0xd4),packet_C4=u.r8(packet+0xc4),
            LP8_before=hex(before),body_flags=hex(u.rq(B+0x88)),
            native_cached_indices={'mapParts':u.r32(0x71058e8c10),'lift':u.r32(0x71058e8c70)})
 group=rec['Fld_VSLobby_row']
 rec['authored_exclusions']={t:bool((bits[(group*len(tags)+tags.index(t))>>3]>>((group*len(tags)+tags.index(t))&7))&1)
                             for t in ('Actor_MapParts_KeepOut','Actor_Lift_KeepOut')}
 err=u.call(0x7103b07b8c,packet,B,0,count=10000000)
 rec.update(flush_error=err,LP8_after=hex(u.r32(LP+8)),packet_C4_after=u.r8(packet+0xc4),
            packet_storage_boundary='explicit preallocated queued-action packet; original functor, setter and whole packet flush execute')
 assert rec['functor_error'] is None and err is None
 assert rec['packet_D4']==0x1000000 and rec['packet_C4']==1 and u.r32(LP+8)==before|0x10000000
 return rec

def main():
 u=PUC();obj,rows,tags,bits,rec=native_actor_tags(u)
 names=('Fld_VSLobby','Mpt_KeepOutPlayer','Mpt_KeepOutEnemy','Lft_KeepOutPlayer','Lft_KeepOutEnemy')
 selected=[next(i for i,r in enumerate(rows) if r[0]=='Work/Actor/' and r[1]==n) for n in names]
 group=u.alloc(4);tag=u.alloc(4);checks=[]
 for row in selected:
  for t in range(len(tags)):
   u.w32(group,row);u.w32(tag,t);err=u.call(0x71038c4ed0,obj,group,tag);actual=u.x(0)
   expected=(bits[(row*len(tags)+t)>>3]>>((row*len(tags)+t)&7))&1
   checks.append({'row':row,'actor':rows[row][1],'tag':tags[t],'actual':actual,'expected':expected,'error':err,'match':err is None and actual==expected})
 for g,t in ((0xffffffff,0),(0,0xffffffff),(0x80000000,0),(0,0x80000000)):
  u.w32(group,g);u.w32(tag,t);err=u.call(0x71038c4ed0,obj,group,tag)
  checks.append({'row':g,'tag':t,'actual':u.x(0),'expected':0,'error':err,'match':err is None and u.x(0)==0})
 rec.update(cases=len(checks),mismatches=sum(not r['match'] for r in checks),rows=checks,
            null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used)
 (OUT/'actor_tag_membership.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:rec[k] for k in ('row_count','tag_count','bit_bytes','Fld_VSLobby_row','cases','mismatches','native_name_lookup','null','auto','faults','plt','libm')}))

if __name__=='__main__':main()
