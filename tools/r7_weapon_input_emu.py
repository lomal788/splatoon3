"""R7 local shooter input counter writer and countdown blocks. Boundary stubs explicit."""
import itertools,json,random,struct,sys
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r7_player_walk_emu import Harness,ROOT

def main():
 sys.stdout.reconfigure(encoding='utf-8');h=Harness();e=h.e;m=e.mu;B=h.body
 def q(a,v):m.mem_write(a,struct.pack('<Q',v))
 def b(a,v):m.mem_write(a,bytes([v]))
 sender=e.alloc(0x100);side=e.alloc(0x100);vt=e.alloc(0x200);stub=e.alloc(0x10)
 q(B+0xa890,sender);q(B+0xa678,side);q(h.weapon,vt);q(vt+0x130,stub);m.mem_write(stub,bytes.fromhex('c0035fd6'))
 ctx={}
 def hook(mu,a,s,u):
  v=ctx['inkblock'] if a==stub else ctx['deny'] if a==0x71024c9324 else ctx['sideok']
  mu.reg_write(UC_ARM64_REG_W0,v);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 for a in [stub,0x71024c9324,0x710268662c]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 cases=0;mis=[];samples=[]
 for fire,blockkind,inkblock,deny,mode,sideok,prev in itertools.product([0,1],range(7),[0,1],[0,1],[0,1,2,3,4],[0,1],[0,1,7]):
  for off in [0x532,0x533,0x534,0x535,0x788,0x784,0x4f0,0x528]:b(B+off,0)
  if blockkind:b(B+[0x532,0x533,0x534,0x535,0x788,0x784][blockkind-1],1)
  e.u32(B+0x4d0,prev);e.u32(B+0x4e0,0);e.u32(B+0x518,0);e.u32(side+0x38,mode);b(sender+0x54,fire);b(B+0x530,1);b(B+0x531,1)
  ctx.update(inkblock=inkblock,deny=deny,sideok=sideok)
  m.reg_write(UC_ARM64_REG_X23,B);m.reg_write(UC_ARM64_REG_X29,0x100ef000);m.reg_write(UC_ARM64_REG_SP,0x100ee000);q(0x100ef000-0x38,B)
  m.emu_start(0x71024a0ce0,0x71024a0ec8,count=500)
  assert m.reg_read(UC_ARM64_REG_PC)==0x71024a0ec8
  okmode=mode in (0,3) or mode==2 and sideok
  expected=prev+1 if fire and not blockkind and not inkblock and not deny and okmode else 0
  latch=0 if deny or not okmode else 0x0101
  got=(e.ru32(B+0x4d0),int.from_bytes(m.mem_read(B+0x530,2),'little'))
  if got!=(expected,latch):mis.append({'input':[fire,blockkind,inkblock,deny,mode,sideok,prev],'got':got,'expected':[expected,latch]})
  cases+=1
 offsets=[0xae0,0xae4,0xae8,0xaec,0xab4,0xab8,0xabc,0xac0,0xac4,0xac8,0xacc]
 rng=random.Random(0x249fcb0);timer_cases=0;timer_mis=[]
 for i in range(1030):
  values=[[-2147483648,-1,0,1,2,2147483647][i%6] for _ in offsets] if i<6 else [rng.randint(-100,2000) for _ in offsets]
  for off,v in zip(offsets,values):e.u32(B+off,v&0xffffffff)
  m.reg_write(UC_ARM64_REG_X23,B);m.reg_write(UC_ARM64_REG_X22,B+0xad0);m.reg_write(UC_ARM64_REG_SP,0x100ee000);m.reg_write(UC_ARM64_REG_W8,0);m.reg_write(UC_ARM64_REG_W9,0)
  m.emu_start(0x710249fcb0,0x710249fdc0,count=100)
  got=[e.ru32(B+off) for off in offsets];expected=[max(v,1)-1 for v in values]
  if got!=expected:timer_mis.append({'input':values,'got':got,'expected':expected})
  timer_cases+=1
 out={'input_writer':'0x71024a0ce0..0x71024a0ec8','input_cases':cases,'input_mismatches':mis[:10],'timer_block':'0x710249fcb0..0x710249fdc0','timer_cases':timer_cases,'timer_fields':len(offsets)*timer_cases,'timer_offsets':[hex(x) for x in offsets],'timer_mismatches':timer_mis[:10],'stubs':{'inkaction vt+0x130':'main-input block bool','0x71024c9324':'global/action input deny bool','0x710268662c':'side-step mode2 allow bool'},'limits':['Normal main shooter branch; no special weapon activation','InputSender+54 is injected; prior priority list update not run','R/A action counter flags fixed zero; 532..535 block flag consumption is tested','Full 249f494/main firing frame not executed; a90/adc and 4d4 writer not established by this block']}
 (ROOT/'analysis/completion/r7/weapon_input_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False));assert not mis and not timer_mis
if __name__=='__main__':main()
