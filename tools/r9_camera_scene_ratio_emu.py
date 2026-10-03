from pathlib import Path
import json,struct,random
import numpy as np
from network_uc import UC,BASE as B,END,STACK
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
from r6_camweapon_seed_emu import tag_data,setup_tags
E=UC();mu=E.mu;S=E.alloc(0x400);N=E.alloc(128);R=E.alloc(8);G=E.alloc(0x15000);Bundle=E.alloc(0x6600);Loc=E.alloc(0x100);fault=[];sceneCalls=0

def w(a,f,*x):mu.mem_write(a,struct.pack('<'+f,*x))
def r(a,f):return struct.unpack('<'+f,mu.mem_read(a,struct.calcsize('<'+f)))
def regs(d):
 for k,v in d.items():mu.reg_write(globals()['UC_ARM64_REG_'+k.upper()],v)
def run(a,z,d):
 regs(dict(sp=STACK+0xe0000,x29=STACK+0xe8000,x30=END,**d));mu.emu_start(B+a,B+z,count=100000);assert mu.reg_read(UC_ARM64_REG_PC)==B+z

def hook(mu,pc,n,u):
 global sceneCalls
 if pc==B+0x1323040:sceneCalls+=1;mu.reg_write(UC_ARM64_REG_X0,S);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
def inv(mu,a,ad,sz,val,u):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),address=hex(ad)));return False
mu.hook_add(UC_HOOK_CODE,hook);mu.hook_add(UC_HOOK_MEM_INVALID,inv)
rows,tags,bits=tag_data();setup_tags(E,rows,tags,bits)
tag=tags.index('Scene_Coop');w(B+0x58e9270,'iB3x',tag,1);w(B+0x58e9278,'Q',B+0x497bab2);w(B+0x58e42f8,'Q',G);w(G+0xc8,'Q',Bundle);w(Bundle+0x6538,'Q',Loc);w(S+0x2d8,'Q',N);w(S+0x2e8,'Q',N)
counts=dict(actual_tag_rows=0,global_mode=0,ratio=0);examples=[]
for idx,row in enumerate(rows):
 if row[0]!='Work/Scene/':continue
 name=row[1];mu.mem_write(N,name.encode()+b'\0');w(S+0x2f0,'i',len(name)+1);w(R,'i',idx)
 run(0x2b5662c,0x2b566e4,dict(x19=S,x24=R,x22=tag,x23=B+0x599b420,x26=0x400001))
 actual=bool(bits[(idx*len(tags)+tag)//8] & (1<<((idx*len(tags)+tag)%8)));want=actual or name=='LobbyCoop';got=r(B+0x58e87cc,'B')[0];assert got==int(want),(idx,name,got,want)
 for localkind in [0,1,2,3]:
  w(Loc+0x34,'i',localkind);mu.mem_write(G+0x143d0,b'\xa5');run(0x2643cf4,0x2643d9c,dict(x0=G));got2=r(G+0x143d0,'B')[0];want2=int(want or (name=='LobbyLocal' and localkind==2));assert got2==want2,(name,localkind,got2,want2);counts['global_mode']+=1
 counts['actual_tag_rows']+=1
 if name in ['LobbyVersus','LobbyCoop','LobbyLocal']:examples.append(dict(name=name,row=idx,tagSceneCoop=actual,sceneFlag=int(want)))
# New original ratio block: B73c regular gravity/jump + B754 wall-charge impulse; C constants +e8 is jump initial .115.
C=E.alloc(0x2000);P=E.alloc(0x1000);mu.mem_write(B+0x58bbc60,struct.pack('<f',.115));rng=random.Random(903);F=np.float32
for j in range(4096):
 a=F(rng.uniform(-.6,.3));v=F(rng.uniform(0,.25));w(P+0x73c,'f',a);w(P+0x754,'f',v);run(0x24dd9ec,0x24dda08,dict(x8=P,x28=B+0x58bbb78));want=F(min(F(F(a+v)/F(.115)),F(1)));got=mu.reg_read(UC_ARM64_REG_S8)&0xffffffff;assert got==struct.unpack('<I',struct.pack('<f',want))[0];counts['ratio']+=1
out=dict(pass_counts=counts,examples=examples,scene_supplier_stub_calls=sceneCalls,faults=fault,null_calls=0,auto_pages=0,mismatches=0,scope='new gsetting scene flag2b5662c..566e4 includes native tag table bit predicate; tag name lookup metadata oldproof reused; new2643cf4..3d9c G143d0 writer inclLobbyLocal2; new24dd9ec..dda08 ratio only, rest camera branch not executed')
Path('analysis/completion/r9/camera_scene_ratio_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))