"""r8 real default bkdat -> sampler/uniform binding. Synthetic model SDK interface only."""
from pathlib import Path
import struct,json,random
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
R=Path(__file__).resolve().parents[2];e=Emu();mu=e.mu;calls=[];s={}
def cs(a):
 b=bytearray()
 for n in range(4096):
  c=mu.mem_read(a+n,1)[0]
  if not c:return bytes(b)
  b.append(c)
 raise AssertionError('long string')
def ret(v=0):mu.reg_write(UC_ARM64_REG_X0,v&((1<<64)-1));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
fakes={n:RET+0x100+i*4 for i,n in enumerate(['rtti','count','name','uniform','dataCount','dataElement'])}
for a in fakes.values():mu.mem_write(a,bytes.fromhex('c0035fd6'))
def hook(mu,a,z,u):
 x=[mu.reg_read(UC_ARM64_REG_X0+i) for i in range(4)]
 if a==BASE+0x83d2f0:ret(e.alloc(max(x[0],16)));calls.append('malloc')
 elif a==BASE+0x3e99f10:mu.mem_write(x[0],bytes([x[1]&255])*x[2]);ret(x[0]);calls.append('memset')
 elif a==BASE+0x3e99f20:mu.mem_write(x[0],bytes(mu.mem_read(x[1],x[2])));ret(x[0]);calls.append('memcpy')
 elif a==BASE+0x3e99fe0:ret(len(cs(x[0])));calls.append('strlen')
 elif a==BASE+0x3e9a100:
  p=bytes(mu.mem_read(x[0],x[2]));q=bytes(mu.mem_read(x[1],x[2]));ret((p>q)-(p<q));calls.append('memcmp')
 elif a==fakes['rtti']:ret(1)
 elif a==fakes['count']:ret(1)
 elif a==fakes['name']:ret(s['name'])
 elif a==fakes['uniform']:s['uniform'].append({'material':x[1],'parameter':x[2],'vec_bits':bytes(mu.mem_read(x[3],16)).hex()});ret()
 elif a==fakes['dataCount']:ret(1)
 elif a==fakes['dataElement']:ret(s['data'])
 elif BASE+0x3e99000<=a<BASE+0x3e9e000:raise AssertionError(('unexpected PLT',hex(a)))
mu.hook_add(UC_HOOK_CODE,hook)
e.reset_heap();e.w(BASE+0x59975c0,'Q',0)
m=e.call(BASE+0x344af54,[0,31,0]);assert m.reg_read(UC_ARM64_REG_PC)==RET
cfg=m.reg_read(UC_ARM64_REG_X0);assert cfg
rows=[]
for k in range(2):
 p=cfg+8+k*0x78;rows.append({'sampler':cs(e.r(p+8,'Q')[0]).decode(),'uniform':cs(e.r(p+0x40,'Q')[0]).decode(),'data_type':e.r(p+0x70,'I')[0],'binding_space':e.r(p+0x74,'I')[0]})
assert e.r(cfg+0x12c8,'I')[0]==2 and rows==[{'sampler':'bake0','uniform':'gsys_bake_st0','data_type':3,'binding_space':0},{'sampler':'bake1','uniform':'gsys_bake_st1','data_type':4,'binding_space':0}],rows
# Actual SDK slot table initializer + original registry, not a reconstructed lookup.
table=e.alloc(16);heap=e.alloc(8);m=e.call(BASE+0x3ccfa2c,[table,heap]);assert m.reg_read(UC_ARM64_REG_PC)==RET
for k in range(2):m=e.call(BASE+0x3ccfcd4,[table,cfg+8+k*0x78]);assert m.reg_read(UC_ARM64_REG_X0)==1 and m.reg_read(UC_ARM64_REG_PC)==RET
e.w(BASE+0x59a3df8,'Q',table);e.w(BASE+0x580f810,'B',1)
registered=[]
for k in (2,3):
 p=e.r(table+8,'Q')[0]+k*0x78;registered.append({'slot':k,'sampler':cs(e.r(p+8,'Q')[0]).decode(),'uniform':cs(e.r(p+0x40,'Q')[0]).decode()})
def cstr(v):
 p=e.alloc(len(v)+1);mu.mem_write(p,v.encode()+b'\0');return p
def dictionary(v):
 d=e.alloc(0x30);name=e.alloc(len(v)+3);e.w(name,'H',len(v));mu.mem_write(name+2,v.encode()+b'\0');e.w(d+8,'iH',-1,1);e.w(d+0x18,'i',-1);e.w(d+0x20,'Q',name);return d
rng=random.Random(8831);results=[]
for k in range(32):
 typ=3+k%2;name=cstr('Fld_VSLobbyMat_%d'%k);s['name']=name;s['uniform']=[]
 m=e.call(BASE+0xf7694c,[name,0]);h=m.reg_read(UC_ARM64_REG_X0)&0xffffffff;assert h
 data=e.alloc(0xa0);dh=e.alloc(8);di=e.alloc(4);modeldata=e.alloc(64);mh=e.alloc(8);matdata=e.alloc(0x28);tex=e.alloc(0x98);texlist=e.alloc(8)
 e.w(data+8,'QQII',dh,di,1,1);e.w(dh,'Q',0x1234567812345678);e.w(di,'I',0);e.w(data+0x20,'I4xQ',1,modeldata);e.w(data+0x40,'I4xQ',1,texlist);e.w(texlist,'Q',tex);e.w(data+0x90,'II',typ,0)
 e.w(modeldata,'QII',mh,1,1);e.w(modeldata+0x10,'I4xQ',1,matdata);e.w(modeldata+0x20,'I',7);e.w(modeldata+0x28,'i',1);e.w(mh,'II',h,0)
 vec=[rng.random() for i in range(4)];e.w(matdata,'ffffIii',*vec,0,0,0);e.w(tex+0x88,'QQ',0x9988776600000000+k,0x778899aa00000000+k)
 model=e.alloc(0x160);vt=e.alloc(0x160);material=e.alloc(0x80);resmat=e.alloc(0xb0);paramholder=e.alloc(8);paramroot=e.alloc(0x30);handles=e.alloc(8);handles2=e.alloc(8);record=e.alloc(0x18);mgr=e.alloc(0x70);resource=e.alloc(8);rvt=e.alloc(0x38)
 e.w(model,'Q',vt);e.w(vt,'Q',fakes['rtti']);e.w(vt+0xc8,'Q',fakes['count']);e.w(vt+0xd8,'Q',fakes['name']);e.w(vt+0x158,'Q',fakes['uniform']);e.w(model+0x132,'H',1);e.w(model+0x148,'Q',material)
 e.w(material,'Q',resmat);e.w(resmat+0x38,'Q',dictionary('bake%d'%(typ-3)));e.w(resmat+0x10,'Q',paramholder);e.w(paramholder,'Q',paramroot);e.w(paramroot+0x28,'Q',dictionary('gsys_bake_st%d'%(typ-3)));e.w(resmat+0xa0,'H',0);e.w(material+0x50,'QQ',handles,handles2)
 e.w(record,'QQI',model,0x1234567812345678,7);e.w(mgr+0x58,'I4xQI',1,record,1);e.w(resource,'Q',rvt);e.w(rvt+0x28,'QQ',fakes['dataCount'],fakes['dataElement']);s['data']=data
 m=e.call(BASE+0x3ccadd0,[mgr,resource]);assert m.reg_read(UC_ARM64_REG_PC)==RET and m.reg_read(UC_ARM64_REG_X0)==1,(k,m.reg_read(UC_ARM64_REG_X0))
 assert e.r(handles,'Q')[0]==0x9988776600000000+k and e.r(handles2,'Q')[0]==0x778899aa00000000+k
 assert s['uniform']==[{'material':0,'parameter':0,'vec_bits':struct.pack('<ffff',*vec).hex()}],(k,s['uniform'])
 results.append({'type':typ,'textures_match':True,'uniform_bits_match':True})
out={'factory':rows,'registered_slots':registered,'binding_cases':len(results),'mismatch':0,'executed':['344af54 case31','3ccfa2c','3ccfcd4','3ccadd0','3ccaf2c','3ccbc7c','3ccb7e4','0f7694c'],'stubs':sorted(set(calls))+['synthetic SDK RTTI=true,material count/name,uniform sink,resource DataElements count/getter'],'limits':'synthetic one material/model per case; original hash/dictionaries/registry/filter/handle writes executed; GPU and actual full scene not executed'}
(R/'analysis/completion/r8/graphics_bake_binding_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('factory2 slot2 binding32 mismatch0')

