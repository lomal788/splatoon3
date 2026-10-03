"""Existing native input/ink/timer blocks -> JS port fixtures. No new analysis claim."""
import json,random,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r7_player_walk_emu import Harness,ROOT
from weapon_ink_emu import Emu,FN_CONSUME,FN_RATE,FN_STOP,FN_TIMER,f2u,F

def main():
 sys.stdout.reconfigure(encoding="utf-8");out={"input":[],"countdown":[],"consume":[],"rate":[],"stop":[],"timer":[],"limits":["InputSender+54 and three boundary bools injected; normal main branch","Offline/no gear40; no partial6d8; PLT ret0; no full scheduler/TOI/renderer"]}
 rnd=random.Random(0x2492120);h=Harness();e=h.e;m=e.mu;B=h.body
 def q(a,v):m.mem_write(a,struct.pack("<Q",v))
 def byte(a,v):m.mem_write(a,bytes([v]))
 sender=e.alloc(0x100);side=e.alloc(0x100);vt=e.alloc(0x200);stub=e.alloc(0x10)
 q(B+0xa890,sender);q(B+0xa678,side);q(h.weapon,vt);q(vt+0x130,stub);m.mem_write(stub,bytes.fromhex("c0035fd6"));ctx={}
 def hook(mu,a,s,u):
  v=ctx["ink"] if a==stub else ctx["deny"] if a==0x71024c9324 else ctx["side"]
  mu.reg_write(UC_ARM64_REG_W0,v);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 for a in [stub,0x71024c9324,0x710268662c]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for i in range(768):
  prev=rnd.choice([-2147483648,-1,0,1,7,2147483647]);fire=rnd.randrange(2);block=rnd.randrange(7);ink=rnd.randrange(4);deny=rnd.randrange(4);mode=rnd.randrange(5);sideok=rnd.randrange(4);rtime=rnd.choice([-1,0,1,7]);atime=rnd.choice([-1,0,1,7]);rflag=rnd.randrange(2);aflag=rnd.randrange(2)
  for off in [0x532,0x533,0x534,0x535,0x788,0x784,0x4f0,0x528]:byte(B+off,0)
  if block:byte(B+[0x532,0x533,0x534,0x535,0x788,0x784][block-1],1)
  e.u32(B+0x4d0,prev&0xffffffff);e.u32(B+0x4e0,rtime&0xffffffff);e.u32(B+0x518,atime&0xffffffff);byte(B+0x4f0,rflag);byte(B+0x528,aflag);e.u32(side+0x38,mode);byte(sender+0x54,fire);byte(B+0x530,1);byte(B+0x531,1);ctx.update(ink=ink,deny=deny,side=sideok)
  m.reg_write(UC_ARM64_REG_X23,B);m.reg_write(UC_ARM64_REG_X29,0x100ef000);m.reg_write(UC_ARM64_REG_SP,0x100ee000);q(0x100ef000-0x38,B)
  m.emu_start(0x71024a0ce0,0x71024a0ec8,count=500);assert m.reg_read(UC_ARM64_REG_PC)==0x71024a0ec8
  got=struct.unpack("<i",m.mem_read(B+0x4d0,4))[0];latch=int.from_bytes(m.mem_read(B+0x530,2),"little")
  out["input"].append({"previous":prev,"sender":bool(fire),"gate":{"blocked":bool(block),"inkBlocked":bool(ink&1),"rFrames":rtime,"rFlag":bool(rflag),"aFrames":atime,"aFlag":bool(aflag),"denied":bool(deny&1),"sideMode":mode,"sideAllowed":bool(sideok&1)},"frames":got,"clearLatches":latch==0})
 for v in [-2147483648,-1,0,1,2,2147483647]+[rnd.randint(-100,2000) for _ in range(256)]:
  e.u32(B+0xab4,v&0xffffffff);m.reg_write(UC_ARM64_REG_X23,B);m.reg_write(UC_ARM64_REG_X22,B+0xad0);m.reg_write(UC_ARM64_REG_SP,0x100ee000);m.reg_write(UC_ARM64_REG_W8,0);m.reg_write(UC_ARM64_REG_W9,0);m.emu_start(0x710249fcb0,0x710249fdc0,count=100)
  out["countdown"].append({"input":v,"result":e.ru32(B+0xab4)})
 del h,e,m
 em=Emu()
 for i in range(384):
  cost=F(.0092 if i<32 else rnd.uniform(0,.05));ink=F(rnd.choice([0,1,float(cost)+rnd.uniform(-2e-5,2e-5),rnd.uniform(-.01,1)]));em.setup_body(ink,0,0,600,180,40);em.wf(em.body+0x6b8,3);em.wf(em.body+0x6bc,1)
  ret,_=em.run(FN_CONSUME,x=(em.body+0x698,em.winfo_holder,1,0),s0=cost)
  out["consume"].append({"ink":float(ink),"cost":float(cost),"ok":bool(ret&1),"bits":em.r32(em.body+0x698),"cleared":[em.r32(em.body+0x6b8),em.r32(em.body+0x6bc)]})
 for i in range(128):
  stealth=0 if i%2==0 else 1;sf=rnd.choice([600,410,220]);tf=rnd.choice([180,148.5,117]);em.setup_body(.5,0,stealth,sf,tf,40);em.uc.reg_write(UC_ARM64_REG_X4,em.body+0xa5d8);_,rate=em.run(FN_RATE,x=(em.body+0x698,em.pp,em.body+0x9218,em.body+0xbd4));out["rate"].append({"stdFrames":sf,"stealthFrames":tf,"stealth":stealth,"bits":f2u(rate)})
 for i in range(128):
  cur=rnd.randint(-50,50);frames=rnd.randint(0,90);ok=rnd.randrange(2);sq=rnd.randrange(2);em.setup_body(1,0,0,600,180,40);off=0x6b0 if sq else 0x6a8;em.w32(em.body+off,cur);em.w32(em.body+0x6b4,0x12345);em.w64(em.owner+0x108,em.body);em.run(FN_STOP,x=(em.owner,frames,ok,sq));out["stop"].append({"current":cur,"frames":frames,"ok":bool(ok),"squid":bool(sq),"stop":em.rs32(em.body+off),"hold":em.rs32(em.body+0x6b4)})
 for i in range(256):
  vals=[float(F(rnd.uniform(0,2))),float(F(rnd.uniform(0,7))),rnd.randint(0,4),rnd.randint(-2,3),rnd.randint(-2,3),rnd.randint(-2,3),rnd.choice([1,4,999]),rnd.randrange(2)];rep=rnd.choice([1,2,6,11]);a=em.timer;em.wf(a,vals[0]);em.wf(a+4,vals[1])
  for k,o in enumerate([8,12,16,20,24]):em.w32(a+o,vals[2+k])
  em.uc.mem_write(a+28,bytes([vals[7]]));ret,_=em.run(FN_TIMER,x=(a,rep));out["timer"].append({"input":vals,"repeat":rep,"due":bool(ret&1),"bits":[em.r32(a),em.r32(a+4)],"fields":[em.rs32(a+o) for o in [8,12,16,20,24]]})
 target=ROOT/'web/games/splatoon3/tests/weapon_port_fixture.json';target.write_text(json.dumps(out,ensure_ascii=False,separators=(",",":")),encoding="utf-8");print(json.dumps({k:len(v) for k,v in out.items() if k!="limits"}))
if __name__=="__main__":main()
