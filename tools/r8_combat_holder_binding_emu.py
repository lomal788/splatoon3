"""r8 original RefHitPointHolder reflection, complete mask block and receiving mask selector.
Mask block is explicit partial entry inside1e3d69c, not claimed whole component init.
"""
from pathlib import Path
import json,struct,random
src=Path('web/tools/r8_combat_enum_emu.py').read_text(encoding='utf-8').split('\ne=Meta(')[0]
ns={'__name__':'r8_mask','__file__':str(Path('web/tools/r8_combat_enum_emu.py').resolve())};exec(compile(src,'r8_mask','exec'),ns)
M=ns['Meta'];K=ns;RG=lambda i:ns['UC_ARM64_REG_X0']+i
# Constants X regs are sequential in Unicorn through X28; explicit lookup avoids assumptions.
RG=lambda i:ns['UC_ARM64_REG_X'+str(i)]
e=M([0x7101e3d69c,0x7101e4476c,0x7101a82330]);mu=e.mu
F=0x10001000
names=['Main','Armor','Head','Body','Tail','Main','main','日本語']+[f'Name{i}' for i in range(32)]
def setup(hnames,refs):
 e.heap=0x20000000;H=e.alloc(0x400);MASK=e.alloc(0x20);P=e.alloc(0xc0);arr=e.alloc(8*max(1,len(hnames)));node=P+0x68;ptr=e.alloc(8*max(1,len(refs)));objects=[]
 e.w32(H+0x30,len(hnames));e.w64(H+0x38,arr);e.w64(F-0x30,H)
 for i,s in enumerate(hnames):
  N=e.alloc(0x100);B=e.alloc(0x100);mu.mem_write(B,s.encode()+b'\0');e.w64(N+8,B);e.w32(N+0x10,64);e.w64(N+0x58,N+0x80);e.w64(arr+8*i,N);objects.append(N)
 e.w64(node+0x10,0);e.w64(node+0x18,ptr);e.w32(node+0x24,len(refs))
 for i,s in enumerate(refs):
  B=e.alloc(0x100);mu.mem_write(B,s.encode()+b'\0');e.w64(ptr+8*i,B)
 e.w32(MASK,0)
 return H,MASK,P,objects
cases=0
rng=random.Random(913)
for _ in range(1300):
 hn=rng.sample(names,rng.randrange(0,41));refs=rng.choices(names+['Missing',''],k=rng.randrange(0,7));H,mask,P,objs=setup(hn,refs)
 mu.reg_write(RG(29),F);mu.reg_write(RG(23),mask);mu.reg_write(RG(28),P);mu.reg_write(ns['UC_ARM64_REG_SP'],0x10180000)
 start=0x7101e3fb20 if refs else 0x7101e3fb00
 mu.emu_start(start,0x7101e3fb5c,count=200000)
 want=(0xffffffff if hn else 0) if not refs else 0
 for s in refs:
  if s in hn:want|=1<<(hn.index(s)&31)
 actual=struct.unpack('<I',mu.mem_read(mask,4))[0];assert actual==want,(hn,refs,actual,want)
 cases+=1
# Reflection visitor captures original descriptor; no fabricated field-name mapping.
class V(M):
 def _block(self,mu,a,s,u):
  if a==0x30000080:
   d=mu.reg_read(RG(1));self.desc.append((self.cstr(struct.unpack('<Q',mu.mem_read(d,8))[0]),struct.unpack('<Q',mu.mem_read(d+0x28,8))[0]-self.obj));mu.reg_write(RG(0),0);mu.reg_write(ns['UC_ARM64_REG_PC'],mu.reg_read(ns['UC_ARM64_REG_LR']));return
  super()._block(mu,a,s,u)
v=V([0x7101a82330]);v.desc=[];v.obj=v.alloc(0xc8);vis=v.alloc(0x20);vt=v.alloc(0x20);v.w64(vis,vt);v.w64(vt,0x30000080);v.call(0x7101a82330,[v.obj,vis]);assert ('RefHitPointHolder',0x68) in v.desc,v.desc
# Entire receiver listener through local-only return (dc=0), actual tree/mask scan, holder backend stubs record selection.
selected_cases=0
for n,maskidx,cure in [(n,m,c) for n in [0,1,2,7,32,37] for m in [0,1,2,0x80000000,0xffffffff,0xAAAAAAAA] for c in [0,1]]:
 H,MASK,P,objs=setup([f'Holder{i}' for i in range(n)],[]);L=e.alloc(0x30);R=e.alloc(0x20);INFO=e.alloc(0x50);S=e.alloc(0x70);SN=e.alloc(0x100);TREE=e.alloc(0x50);SEND=e.alloc(0x30);VT=e.alloc(0x60)
 mu.mem_write(SN,b'Main\0');e.w64(S+8,SN);e.w32(S+0x10,64);e.w64(L+8,H);e.w64(L+0x10,S);e.w64(H+0x98,TREE);e.w64(TREE+0x20,SN);e.w32(TREE+0x28,maskidx if maskidx<0x80000000 else maskidx-0x100000000);e.w32(R+4,7 if cure else 6);e.w64(SEND,VT);e.w64(VT+0x20,0x30000080)
 calls=e.call(0x7101e4476c,[L,R,INFO,SEND]);fn=0x7101a89790 if cure else 0x7101a89524
 selected=[x[2][0] for x in calls if x[0]==fn];want=[o+0x80 for i,o in enumerate(objs) if maskidx>>(i&31)&1]
 assert selected==want,(n,maskidx,cure,selected,want);selected_cases+=1
out={'reflection':'0x7101a82330','descriptor':v.desc,'maskblock':'0x7101e3fb00/20..fb5c inside1e3d69c','mask_cases':cases,'listener':'0x7101e4476c','listenercases':selected_cases,'mismatches':0,'stubs':'reflection visitor records descriptor; HP accumulate/cure boundary records target, sender vt20 returns0, dc0 disables networksend; mask blocknostub','scope':'RefHitPointHolder name binding and mask consumer, notwholeDamageHelperinit/globalnetwork'}
Path('analysis/completion/r8/combat_holder_binding_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
