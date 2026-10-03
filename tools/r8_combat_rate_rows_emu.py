"""r8 DamageRateInfo runtime row visitor+builder+lookup with actual compressed WeaponInfo tables.
Original code is not patched. SDK memory/string/guard/lock/allocation calls are boundary stubs.
"""
import json,struct,sys
from collections import Counter
from pathlib import Path
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
import respawn_emu as R
import spl_data
ROOT=Path(__file__).resolve().parents[2]
class H(R.Emu):
 def _allowed(self,a):return a==R.RETADDR or R.BASE<=a<R.PLT_LO
 def cstr(self,p):
  b=bytearray()
  for i in range(0x400000):
   c=self.mu.mem_read(p+i,1)[0]
   if not c:return b.decode('utf-8')
   b.append(c)
  raise ValueError('unterminated')
 def _block(self,mu,a,size,user):
  if a==0x710083d2f0:
   self.stublog[a]+=1;ret=self.alloc(mu.reg_read(UC_ARM64_REG_X0));mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  if a in [0x7103585094,0x7100000250]:
   self.stublog[a]+=1;mu.reg_write(UC_ARM64_REG_X0,0);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));return
  if self._allowed(a):self.executed.add(a);return
  if not R.PLT_LO<=a<R.PLT_HI:raise RuntimeError(f'unknown boundary {a:#x}')
  name=self._plt_name(a);x=[mu.reg_read(r) for r in [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3]];ret=0
  if name in ['memcpy','memmove']:mu.mem_write(x[0],bytes(mu.mem_read(x[1],x[2])));ret=x[0]
  elif name=='memset':mu.mem_write(x[0],bytes([x[1]&255])*x[2]);ret=x[0]
  elif name=='strlen':ret=len(self.cstr(x[0]).encode())
  elif name=='strcmp':
   a0=self.cstr(x[0]).encode();a1=self.cstr(x[1]).encode();ret=(a0>a1)-(a0<a1)
  elif name=='strncmp':
   a0=self.cstr(x[0]).encode()[:x[2]];a1=self.cstr(x[1]).encode()[:x[2]];ret=(a0>a1)-(a0<a1)
  elif name=='strncpy':
   b=self.cstr(x[1]).encode()[:x[2]];mu.mem_write(x[0],b+b'\0'*(x[2]-len(b)));ret=x[0]
  elif name=='malloc':ret=self.alloc(x[0]);mu.mem_write(ret,b'\0'*x[0])
  elif name=='free':pass
  elif name=='__cxa_guard_acquire':ret=1
  elif name=='__cxa_guard_release':mu.mem_write(x[0],b'\1')
  elif name=='__cxa_atexit':pass
  elif any(k in name for k in ['LockMutex','UnlockMutex','InitializeMutex','FinalizeMutex']):pass
  else:raise RuntimeError(f'unsupported SDK {a:#x} {name} x={x}')
  self.sdklog[name]+=1;mu.reg_write(UC_ARM64_REG_X0,ret&0xffffffffffffffff);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 def w64(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def w32(self,a,v):self.mu.mem_write(a,struct.pack('<I',v&0xffffffff))
 def r64(self,a):return struct.unpack('<Q',self.mu.mem_read(a,8))[0]
 def r32(self,a):return struct.unpack('<I',self.mu.mem_read(a,4))[0]
h=H([0x7101413a60]);h.executed=set();h.sdklog=Counter();h.stublog=Counter();h.heapobjects=[]
# actual manager creates descriptor names by original writes; allocator is SDK boundary.
mgr=h.alloc(0x40);h.call(0x7101424e88,[mgr,0]);descriptors=h.r64(mgr+0x18)
assert [h.cstr(h.r64(descriptors+i*0x28+8)) for i in [10,11,12]]==['WeaponInfoMain','WeaponInfoSub','WeaponInfoSpecial']
# DamageRateInfo uses *5790598 pointing at real manager object; pointed cell supplied because global init is not exercised.
manager_cell=h.alloc(8);h.w64(manager_cell,mgr);h.w64(0x7105790598,manager_cell)
empty=h.alloc(8);h.mu.mem_write(empty,b'Default\0');fallback=h.alloc(8);h.w64(fallback,empty);h.w64(0x7105790020,fallback)
rows_out=[];cases=0
from r6_combat_hiteffect_emu import EXI,HET
for cat,label in enumerate(['Main','Sub','Special']):
 d=spl_data.load(ROOT/f'extracted/romfs/RSDB/WeaponInfo{label}.Product.100.rstbl.byml.zs');by=spl_data.Byml(d);rows=by.root();base=h.alloc(len(d));h.mu.mem_write(base,d);rootacc=h.alloc(16);h.w64(rootacc,base);h.w64(rootacc+8,base+by.root_off);result=h.alloc(8)
 obj=h.alloc(0x200);idx=10+cat;off=0x118 if cat==0 else 0xd8;h.w64(descriptors+idx*0x28+0x20,obj)
 # persistent pool supports actual red-black insert for every row.
 pool=h.alloc(0x20);nodes=h.alloc(0x988*len(rows))
 for i in range(len(rows)):h.w64(nodes+i*0x988,nodes+(i+1)*0x988 if i+1<len(rows) else 0)
 h.w64(pool+8,nodes);h.w32(pool+0x1c,len(rows));h.w64(obj+off,pool)
 for i,r in enumerate(rows):
  h.call(0x71037d204c,[rootacc,result,i]);assert h.mu.reg_read(UC_ARM64_REG_W0)==1
  ra=h.alloc(16);h.w64(ra,base);h.w64(ra+8,base+h.r32(result));row=h.alloc(0x60);h.w64(row,empty);h.w64(row+8,empty)
  h.call(0x7101415c04,[row,ra]);wid=h.r32(row+0x54);assert wid==r['Id'];default=r.get('DefaultDamageRateInfoRow','Default');assert h.cstr(h.r64(row+8))==default
  h.call(0x7101413a60,[pool,0,row,0,0,0,0,0]);names=[default]*26
  for e in r.get('ExtraDamageRateInfoRowSet',[]):names[EXI.index(e['ExtraInfo'])]=e.get('DamageRateInfoRow','Default')
  for ex in list(range(28))+[0xffffffff,0x7fffffff]:
   h.call(0x7101a88920,[cat,wid,ex]);p=h.mu.reg_read(UC_ARM64_REG_X0);got=h.cstr(h.r64(p));expect=names[ex if ex<26 else 0];assert got==expect,(cat,wid,ex,got,expect);cases+=1
  if label=='Main' and r['__RowId']=='Shooter_Normal_00':rows_out.append({'category':cat,'weapon':r['__RowId'],'id':wid,'names':names})
  print(f'{label} row{i} id{wid}: OK',flush=True)
  if '--probe' in sys.argv:break
 if '--probe' in sys.argv:break
# New/reused node lifecycle and 64-byte inline string boundaries, no extra rows.
string_cases=0;pool=h.alloc(0x20);node=h.alloc(0x988);h.w64(pool+8,node);h.w32(pool+0x1c,1);row=h.alloc(0x60);h.w32(row+0x54,1234)
for length in [0,1,62,63,64,65,127,1000]:
 text='X'*length;p=h.alloc(length+1);h.mu.mem_write(p,text.encode()+b'\0');h.w64(row+8,p);h.call(0x7101413a60,[pool,0,row,0,0,0,0,0]);actualnode=h.r64(pool)
 for ex in range(26):
  stringptr=h.r64(actualnode+0x98+ex*0x58);got=h.cstr(stringptr);assert got==text[:63];string_cases+=1
out={'cases':cases,'mismatches':0,'string_boundary_cases':string_cases,'functions':['1424e88','37d204c','1415c04','1413a60','1a88920'],'SDK_stubs':dict(h.sdklog),'non_SDK_stubs':{hex(k):v for k,v in h.stublog.items()},'executed_blocks':len(h.executed),'examples':rows_out,'supplied_globals':['manager-cell alias5790598','default string5790020'],'scope':'actual BYML row visitor and builder output plus original category/ExtraInfo reader; SDK allocation/locks synthetic; global startup not executed'}
(ROOT/'analysis/completion/r8/combat_rate_rows_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
