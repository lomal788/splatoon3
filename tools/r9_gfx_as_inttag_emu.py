"""New IntSelector blackboard/override branches; typed provider API fixture explicitly logged."""
import sys,struct,json,random
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
from network_uc import STUB,END
R=Path(__file__).resolve().parents[2];e=GUC();rng=random.Random(0x39cda20);log=[];values={}
ctx=e.alloc(0x40);a=e.alloc(16);b=e.alloc(16);va=e.alloc(0x200);vb=e.alloc(0x200);e.wq(a,va);e.wq(b,vb);e.wq(ctx+0x20,a);e.wq(ctx+0x28,b);e.wq(va+0x120,STUB+0x800);e.wq(vb+0x138,STUB+0x808)
val=e.alloc(4);node=e.alloc(0x30);res=e.alloc(0x20);body=e.alloc(0x80);tbl=e.alloc(0x100);inst=e.alloc(0x100);changed=e.alloc(4);e.wq(node+0x10,res);e.wq(node+0x18,body);e.wq(res+8,tbl)
chain=e.alloc(0x40);row=e.alloc(0x40);e.wq(inst+0x60,chain);e.wq(chain+8,0);e.wq(chain+0x18,row);e.u32(chain+0x20,1);e.wq(row+8,chain+0x10)
def hook(mu,a,s,u):
 if a==STUB+0x800:
  ix=mu.reg_read(UC_ARM64_REG_X2)&0xffff;log.append(('index',ix));mu.reg_write(UC_ARM64_REG_X0,ix)
 elif a==STUB+0x808:
  ix=mu.reg_read(UC_ARM64_REG_X1)&0xffff;log.append(('value',ix));e.u32(val,values[ix]);p=mu.reg_read(UC_ARM64_REG_X2)
  if p:e.mu.mem_write(p,bytes([7]))
  mu.reg_write(UC_ARM64_REG_X0,val)
e.mu.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x800,end=STUB+0x808)
counts={'typed':0,'override':0,'override_miss':0};nibble={}
for k in range(1536):
 n=2+k%5;cv=[rng.randint(-9,9) for j in range(n)];x=rng.randint(-10,10);values.clear();values[0x123]=x&0xffffffff
 mode=k%3;nb=[8,9,10,11,12,13,14,15][(k//3)%8];tag=(nb<<28)|0x123
 if mode:tag|=0x1000000
 e.u32(body,tag);e.u32(body+4,0x7fffffff);e.mu.mem_write(body+0x18,bytes([n,0]));e.u32(inst+0xb4,7);e.wq(row+0x18,body+4 if mode==1 else body+0xc);e.u32(row+0x30,x)
 for j,c in enumerate(cv):e.u32(body+0x20+4*j,j*16);e.u32(tbl+j*16,0);e.u32(tbl+j*16+4,c)
 actualx=x if mode!=2 else 0;want=n-1
 for j,c in enumerate(cv[:-1]):
  if c==actualx:want=j;break
 log.clear();e.call(0x71039cda20,node,ctx,inst,changed)
 assert e.mu.reg_read(UC_ARM64_REG_PC)==END
 got=e.mu.reg_read(UC_ARM64_REG_X0)&0xffffffff;assert got==want,(k,mode,hex(tag),got,want)
 assert log==([('index',0x123),('value',0x123)] if mode==0 else []),(k,log)
 fl=bytes(e.mu.mem_read(changed,1))[0];assert fl==int(mode!=0),(k,'changed',fl)
 counts[['typed','override','override_miss'][mode]]+=1;nibble[str(nb)]=nibble.get(str(nb),0)+1
out={'date':'2026-10-03','original':'39CDA20 whole','cases':sum(counts.values()),'groups':counts,'high_nibbles':nibble,'mismatch':0,'fixtures':['ctx20 vt120 typed int identifier low16 passthrough','ctx28 vt138 integer value + change byte7 supplied'],'boundary':'original selector branches/linked override lookup/cache flag exact; upstream typed blackboard producer not executed','unhandled_plt':e.plt_stubbed}
assert not e.plt_stubbed
(R/'analysis/completion/r9/graphics_as_inttag_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
