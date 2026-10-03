"""r8 native contact impulse -> engine contact point -> target player bend.
Executes original3c58fe4 and helpers/collection; external native manifold decode,
body-id lookup/material lookup/allocation and game tag classification are isolated.
No original or runtime implementation files are changed.
"""
import struct,json,random,math
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,BASE,STUB
u=UC();m=u.mu
wq=lambda a,v:m.mem_write(a,struct.pack('<Q',v))
wu=u.u32;wf=u.f32
rq=lambda a:struct.unpack('<Q',m.mem_read(a,8))[0]
rf=u.rf32
collector=u.alloc(0x28);ctx=u.alloc(0x240);cfg=u.alloc(0x40);table=u.alloc(0x46000);entry=u.alloc(0x20);entryarr=u.alloc(8)
world=u.alloc(0x850);wvt=u.alloc(0x300);worldref=u.alloc(8)
bodies=[u.alloc(0xc0) for _ in range(2)];rbcs=[u.alloc(0x310) for _ in range(2)];filters=[u.alloc(0x20) for _ in range(2)]
collection=u.alloc(0x180);list1=u.alloc(0x200);list2=u.alloc(0x200);bitset=u.alloc(8);pool=u.alloc(0x20)
event=u.alloc(0x60);cache=u.alloc(0x20);keys=u.alloc(8);manifold=u.alloc(0x90);points=[u.alloc(0x80) for _ in range(8)]
target=u.alloc(0x260);param=u.alloc(0x70);pair=u.alloc(0x50);contact=u.alloc(0x20);pairpoint=u.alloc(0x10);pointrecord=u.alloc(0x10)
wq(collector,BASE+0x57566f8);wq(collector+0x10,cfg);wq(collector+0x18,ctx);wq(ctx+0xc0,world);wq(cfg+0x18,table)
wq(world,wvt);wq(wvt+0x118,STUB+0x500);wq(worldref,world);wq(cfg+8,pool);wq(cfg+0x10,pool)
# Synthetic matching layer4/group0 pair registration. Real3c584f0/3c4cc04/3c4d1c0 execute.
pairslot=table+8+4*0x27e0+4*0x160
wu(pairslot,1);wq(pairslot+8,entryarr);wq(entryarr,entry);wq(entry,collection)
wu(entry+8,4);wu(entry+0xc,1);wu(entry+0x10,0);wu(entry+0x14,1);wu(entry+0x18,1)
for i in range(2):
 wq(bodies[i]+0x98,rbcs[i]);wq(rbcs[i]+0x180,filters[i]);wu(filters[i]+8,4)
 wq(bodies[i]+0x78,STUB+0x900+i*8)
wu(collection+0x28,16);wq(collection+0x30,list1);wu(collection+0x38,16);wq(collection+0x40,list2);wu(collection+0x18,1);wq(collection+0x20,bitset)
wq(event+8,0);wq(event+0x10,1);wq(event+0x18,cache)
wq(contact+0x10,pair);wq(pair+0x38,pairpoint);wq(target+0x1c8,param);wq(target+0x180,STUB+0x980);m.mem_write(param+0x5c,b'\1');wf(param+0x4c,.005)
allocated=[];captured=[]
def ret(v=None):
 if v is not None:m.reg_write(UC_ARM64_REG_X0,v)
 m.reg_write(UC_ARM64_REG_PC,m.reg_read(UC_ARM64_REG_LR))
def hook(mu,pc,n,_):
 if pc==STUB+0x500:
  ret(bodies[mu.reg_read(UC_ARM64_REG_X1)&1])
 elif pc==BASE+0xa4a510:
  dest=mu.reg_read(UC_ARM64_REG_X2);m.mem_write(dest,bytes(m.mem_read(manifold,0x80)));ret()
 elif pc==BASE+0x3b1c8fc:
  p=points[len(allocated)];allocated.append(p);m.mem_write(p,b'\xcc'*0x80);wq(p+0x70,rbcs[0]);wq(p+0x78,rbcs[1]);ret(p)
 elif pc in [BASE+0x9b0254,BASE+0x9b0278]:ret(keys)
 elif pc==BASE+0x12ac5e0:ret(0)
 elif pc==BASE+0x3c5a604:ret() # Character-specific pair preparation excluded.
 elif pc==BASE+0x12d3e10:ret(int(mu.reg_read(UC_ARM64_REG_X1)==BASE+0x58e88b0))
 elif pc==BASE+0x1e3422c:
  cp=mu.reg_read(UC_ARM64_REG_X1);jp=mu.reg_read(UC_ARM64_REG_X2);kind=mu.reg_read(UC_ARM64_REG_X3)
  captured.append((bytes(m.mem_read(cp,12)),bytes(m.mem_read(jp,12)),kind));ret()
for pc in [STUB+0x500,BASE+0xa4a510,BASE+0x3b1c8fc,BASE+0x9b0254,BASE+0x9b0278,BASE+0x12ac5e0,BASE+0x3c5a604,BASE+0x12d3e10,BASE+0x1e3422c]:m.hook_add(UC_HOOK_CODE,hook,begin=pc,end=pc)
f=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
rng=random.Random(0x60544);passes=0;positive=0;bend=0
values=[0.,-0.,-1.,1e-20,1.,37.125,float('nan'),float('inf')]
for count in range(5):
 for status in range(6):
  for case in range(64):
   vals=[values[(case+i)%len(values)] if case<8 else f(rng.uniform(-1000,1000)) for i in range(4)]
   normal=[f(rng.uniform(-1,1)) for _ in range(3)];pos=[f(rng.uniform(-30,30)) for _ in range(12)];depth=[f(rng.uniform(-.4,.2)) for _ in range(4)]
   wu(manifold,count);m.mem_write(manifold+0x10,struct.pack('<3f',*normal));m.mem_write(manifold+0x30,struct.pack('<4f',*depth))
   for i in range(4):m.mem_write(manifold+0x40+16*i,struct.pack('<3f',*pos[3*i:3*i+3]))
   m.mem_write(cache+4,bytes([count]));m.mem_write(event+0x20,bytes([status]));m.mem_write(event+0x30,struct.pack('<4f',*vals))
   for a in [collection+8,collection+0xc,collection+0x10,ctx+0xb8]:wu(a,0)
   m.mem_write(bitset,b'\0'*8);allocated.clear();captured.clear()
   u.call(BASE+0x3c58fe4,collector,worldref,event)
   selected=[i for i in range(count) if vals[i]>0 or math.isnan(vals[i])] if status in [0,1,3,4] else []
   assert len(allocated)==len(selected),(count,status,vals,len(allocated),selected)
   assert u.ru32(collection+8)==len(selected)
   for k,i in enumerate(selected):
    p=allocated[k];assert bytes(m.mem_read(p+0x60,4))==struct.pack('<f',vals[i]);assert rq(list1+16*k)==p
    assert u.ru32(p+0x64)=={0:0,1:1,3:2,4:4}[status]
    assert bytes(m.mem_read(p,12))==struct.pack('<3f',*pos[3*i:3*i+3]);assert bytes(m.mem_read(p+0xc,12))==struct.pack('<3f',*normal)
    positive+=1
    # Original target consumes the exact producer point; game Actor_Player tag is isolated.
    for flip in [0,1]:
     wq(pairpoint,pointrecord);wq(pointrecord,p);m.mem_write(pointrecord+8,bytes([flip]));m.mem_write(pairpoint+8,b'\0\0');captured.clear();u.call(BASE+0x21f0348,target,contact)
     assert len(captured)==1;cp,jp,kind=captured[0];assert kind==1
     cn=[f(pos[3*i+j]+f(depth[i]*normal[j])) if flip else pos[3*i+j] for j in range(3)]
     jv=[f(f(vals[i]*f(.005))* (-normal[j] if flip else normal[j])) for j in range(3)]
     assert cp==struct.pack('<3f',*cn),(cp,cn)
     assert jp==struct.pack('<3f',*jv),(jp,jv)
     bend+=1
   passes+=1
out={'contact_impulse_event':{'pass':passes,'positive_points':positive,'mismatch':0},'target_player_bend':{'pass':bend,'mismatch':0},'original':['3c58fe4','3c584f0','3c4cc04','3c4d1c0','3c59dd0','3c59ec4','3c5a410','3c5a0e4','3c5a2a0','3c4d040','3c4d140','3a60c74','21f0348'],'boundaries':['synthetic body pairs/layer4-group0 collection registration; actual3c584f0/3c4cc04 original path','native manifold reconstruction0a4a510, world body lookupvt118, allocation3b1c8fc, material lookup/shape-key decode isolated','character-specific pair callback3c5a604 ret; no actual Havok solving/event creation/physical player collision','target Actor_Player tag lookup isolated, exact original vector arithmetic and call parameters tested; downstream BendCalculator excluded because existing r5 fullproof','status0/1/3/4 mappings and positive/zero/negative/NaN/+inf tested; original fcmp/b.ls passes unordered NaN; no gameplay sub weapon action']}
Path('analysis/completion/r8/range_contact_impulse_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))


