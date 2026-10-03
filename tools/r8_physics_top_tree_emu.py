"""Original 09372cc topLevelTree traversal on original four meshes.
Section branch 093767c intercepted before section BVH/leaf cast: no TOI/solver claim.
Actual vector slab ops (including signed-int min/max of float bit patterns) compared bit-for-bit.
"""
import json,struct,random,sys
from pathlib import Path
from r5_gfx_char_uc import GUC
from network_uc import BASE as B
from collision_mesh import load_blobs
from collision_tag0 import open_bphsh
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_W8,UC_ARM64_REG_X8,UC_ARM64_REG_Q1,UC_ARM64_REG_Q4,UC_ARM64_REG_PC
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8')
def f(x):
 try:return struct.unpack('<f',struct.pack('<f',x))[0]
 except OverflowError:return float('-inf') if x<0 else float('inf')
def ib(x):return struct.unpack('<i',struct.pack('<f',x))[0]
def fb(x):return struct.unpack('<f',struct.pack('<i',x))[0]
def imn(a,b):return fb(min(ib(a),ib(b)))
def imx(a,b):return fb(max(ib(a),ib(b)))
def bounds(node,O,I,E,L):
 arr=struct.unpack_from('<24f',node);near=[];far=[];valid=[]
 for lane in range(4):
  lo=[];hi=[]
  for ax in range(3):
   mn=arr[ax*8+lane];mx=arr[ax*8+4+lane]
   a=f(I[ax]*f(f(mn-E[ax])-O[ax]));b=f(I[ax]*f(f(E[ax]+mx)-O[ax]))
   lo.append(imn(a,b));hi.append(max(a,b))
  n=imx(imx(lo[0],lo[1]),imx(lo[2],0.0));z=imn(imn(hi[0],hi[1]),imn(hi[2],L))
  near.append(n);far.append(z);valid.append(arr[4+lane]>=arr[lane] and z>=n)
 return near,far,valid
h=GUC();m=h.mu;m.mem_map(0x40000000,0x10000000);h.heap_next=0x40000000
ray=h.alloc(0x40);ext=h.alloc(16);ctx=h.alloc(0x200);listener=h.alloc(0x30);h.wq(ctx+0x148,listener)
s={'seen':[],'O':None,'I':None,'E':None,'L':1.,'checks':0,'mismatch':[]}
def hook(mu,a,z,d):
 if a==B+0x93767c:
  s['seen'].append(mu.reg_read(UC_ARM64_REG_W8));mu.reg_write(UC_ARM64_REG_PC,B+0x9373e8)
 elif a==B+0x9375d8:
  p=mu.reg_read(UC_ARM64_REG_X8);node=bytes(mu.mem_read(p,128));ne,fa,_=bounds(node,s['O'],s['I'],s['E'],s['L'])
  for reg,exp,key in ((UC_ARM64_REG_Q1,ne,'near'),(UC_ARM64_REG_Q4,fa,'far')):
   got=mu.reg_read(reg).to_bytes(16,'little');eb=struct.pack('<4f',*exp);s['checks']+=4
   if got!=eb:s['mismatch'].append({'type':key,'got':got.hex(),'exp':eb.hex()})
m.hook_add(UC_HOOK_CODE,hook,begin=B+0x9372cc,end=B+0x9378000)
rng=random.Random(0x9372cc);out={'files':[],'cases':0,'traversal_mismatches':[],'scope':__doc__}
try:
 for pack in ('Fld_VSLobby','Mpt_Fld_VSLobbyExterior','Fld_Yagara'):
  for name,raw in load_blobs(R/f'extracted/romfs/Pack/Actor/{pack}.pack.zs'):
   tf=open_bphsh(raw);t,offs=tf.item_offsets(1);root=tf.read(t,offs[0]);tree=root['topLevelTree'];nodes=tf.rel(tree['nodes']);nt=len(nodes)
   P=h.alloc(len(raw)+16);m.mem_write(P,raw);H=P+offs[0];h.wq(ctx+0x10,H)
   rel=struct.unpack_from('<q',raw,offs[0]+0x78)[0];no=offs[0]+0x78+rel;nraw=[raw[no+i*128:no+(i+1)*128] for i in range(nt)]
   fi={'pack':pack,'name':name,'nodes':nt,'sections':len(tf.rel(root['geometrySections'])),'cases':0,'selected_sections':0}
   for case in range(1200):
    O=[f(rng.uniform(-150,150)) for _ in range(3)];I=[f(rng.choice((-1,1))*10**rng.uniform(-1,2)) for _ in range(3)];E=[f(rng.choice((0,.1,.7,3,10))) for _ in range(3)];L=f(rng.choice((.01,.2,1,10,100)))
    s.update(O=O,I=I,E=E,L=L,seen=[]);m.mem_write(ray,struct.pack('<4f',*O,0));m.mem_write(ray+0x20,struct.pack('<4f',*I,0));m.mem_write(ext,struct.pack('<4f',*E,0));m.mem_write(listener+0x10,struct.pack('<2f',L,L))
    stack=[2];expected=[]
    while stack:
     v=stack.pop();idx=v>>1
     if v&1:expected.append(idx);continue
     node=nraw[idx];ne,fa,va=bounds(node,O,I,E,L);data=struct.unpack_from('<4I',node,0x60);leaf=int(node[0x70]!=0)
     stack.extend((data[i]<<1)|leaf for i in range(4) if va[i])
    h.call(B+0x9372cc,H+0x78,ray,ext,ctx,0,1)
    out['cases']+=1;fi['cases']+=1;fi['selected_sections']+=len(s['seen'])
    if s['seen']!=expected:out['traversal_mismatches'].append({'name':name,'case':case,'got':s['seen'],'expected':expected})
   out['files'].append(fi)
 out['status']='success'
except Exception as e:out.update(status='error',error=repr(e),pc=hex(m.reg_read(UC_ARM64_REG_PC)))
out.update(vector_fields=s['checks'],vector_mismatches=s['mismatch'],plt_stubbed=sorted(set(h.plt_stubbed)))
(R/'analysis/completion/r8/physics_top_tree_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='scope'},ensure_ascii=False))

