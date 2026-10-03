"""r8: new caller/producer blocks for B210/B1f8/B1e0/B26c/B274.
Only named original instruction ranges run; synthetic records, no Havok step claimed.
Slerp formula/tables are previously validated r5, reused; caller gate/state is new.
"""
import json,struct,random,sys
from pathlib import Path
import numpy as np
from r6_player_uc import PUC,RET_MAGIC,STACK,STACK_SZ
from r5_player_lerpdir_emu import lerp_dir
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
R=Path(__file__).resolve().parents[2];sys.stdout.reconfigure(encoding='utf-8')
F=lambda v:float(np.float32(v));A=lambda a,b:F(F(a)+F(b));S=lambda a,b:F(F(a)-F(b));M=lambda a,b:F(F(a)*F(b));pk=lambda v:struct.pack('<'+'f'*len(v),*v)
u=PUC();m=u.mu;B=u.alloc(0xaa00);PC=u.alloc(0xe400);IM=u.alloc(0x60);D=u.alloc(0x80);frame=u.alloc(0x300);sp=STACK+STACK_SZ-0x20000;u.wq(B+0xa690,PC);u.wq(PC+0xe360,IM);u.wq(IM+0x28,D)
s={'stop':set(),'sl_calls':0}
def hk(mu,a,z,d):
 if a in s['stop']:mu.reg_write(UC_ARM64_REG_PC,RET_MAGIC)
 if a==0x71024ae4b4:s['sl_calls']+=1
m.hook_add(UC_HOOK_CODE,hk)
def run(a,ends,regs):
 s['stop']=set(ends);m.reg_write(UC_ARM64_REG_SP,sp);m.reg_write(UC_ARM64_REG_X29,frame+0x100);m.reg_write(UC_ARM64_REG_LR,RET_MAGIC)
 for reg,v in regs.items():m.reg_write(reg,v)
 m.emu_start(a,RET_MAGIC,count=200000)
 assert m.reg_read(UC_ARM64_REG_PC)==RET_MAGIC
out={'scope':__doc__,'cases':{},'fields':{},'mismatches':[]};rng=random.Random(381)
def chk(k,a,v):
 out['cases'][k]=out['cases'].get(k,0)+1;out['fields'][k]=out['fields'].get(k,0)+len(v)
 got=bytes(m.mem_read(a,len(v)*4));ex=pk(v)
 if got!=ex:out['mismatches'].append({'kind':k,'got':got.hex(),'exp':ex.hex()})
for i in range(2000):
 vals=[[F(rng.uniform(-3,3)) for _ in range(3)] for __ in range(6)]
 for off,v in zip((0x234,0x240,0x204,0x4bc),vals[:4]):m.mem_write(B+off,pk(v))
 for off,v in zip((8,0x24),vals[4:]):m.mem_write(D+off,pk(v))
 dt=struct.unpack('<f',struct.pack('<I',0x3c888889))[0]
 exp=[S(A(A(vals[0][j],vals[1][j]),vals[2][j]),A(M(M(A(vals[4][j],vals[5][j]),dt),dt),vals[3][j])) for j in range(3)]
 run(0x71024836c4,(0x71024837bc,),{UC_ARM64_REG_X20:B+0x180,UC_ARM64_REG_X28:B});chk('accumulator_start',B+0x210,exp)
 assert bytes(m.mem_read(B+0x204,12))==b'\0'*12
 vals=[[F(rng.uniform(-3,3)) for _ in range(3)] for __ in range(7)]
 for off,v in zip((0x10,0x40,0xe4,0x12c,0x108,0x210),vals[:6]):m.mem_write(B+off,pk(v))
 if i%4==0:vals[5]=[0.,0.,0.];m.mem_write(B+0x210,pk(vals[5]))
 m.mem_write(D+0x40,pk(vals[6]));g=i%2
 exp=[S(S(S(vals[0][j],vals[1][j]),A(vals[6][j],A(vals[2][j],vals[3][j]))),vals[4][j]) if g else S(S(vals[0][j],vals[1][j]),A(vals[6][j],A(vals[2][j],vals[3][j]))) for j in range(3)]
 u.wq(sp+0xc0,B+0x10)
 run(0x71024ae4b8,(0x71024ae570,),{UC_ARM64_REG_X25:PC+0xaaf8,UC_ARM64_REG_X23:B+0xe4,UC_ARM64_REG_X19:B+0x180,UC_ARM64_REG_W27:g});chk('residual_displacement',B+0x1f8,exp)
 chk('conditional_accumulation',B+0x210,[A(vals[5][j],exp[j]) for j in range(3)] if any(vals[5]) else vals[5])
 fr=[F(rng.uniform(-2,2)) for _ in range(3)];to=[F(rng.uniform(-2,2)) for _ in range(3)];cliff=F(rng.choice((0,.01,.011,.5)))
 m.mem_write(B+0x1e0,pk(fr));m.mem_write(B+0x180,pk(to));u.wf(B+0xa7c,cliff);gate=cliff<=u.rf(0x71058bbeac) or fr[1]<=to[1]
 exp=list(map(float,lerp_dir(F(.15),fr,to,None))) if gate else fr
 run(0x71024ae474,(0x71024ae4b8,),{UC_ARM64_REG_X26:B+0xa68,UC_ARM64_REG_X19:B+0x180});chk('smooth_normal_gate',B+0x1e0,exp)
# Ground/air counters in all boundary crossings; apply actual B274 writer with entry D0 snapshot.
threshold=u.rs32(0x71058bbc20);out['air_break_threshold']=threshold
for count in (-3,0,1,2,3,4,5,9998,9999,10000):
 for orig in (0,1,3,4,5,44,9998,9999):
  for ground in (0,1):
   for flag in (0,1):
    c=count;d=count;k=orig;flat=F(rng.choice((0,.64,.64144969,1)))
    for off,v in ((0xc0,c),(0xd0,d),(0x268,k),(0x26c,k),(0x270,k)):u.w32(B+off,v)
    u.wf(B+0x1cc,flat);prev=d
    if ground:
     run(0x710246b384,(0x710246b414,0x710246b514),{UC_ARM64_REG_X1:B+0x180,UC_ARM64_REG_X2:B+0xc0,UC_ARM64_REG_W8:flag})
     ek=min(k,9998)+1;ec=0;ed=0 if flag else d;eg=0 if flag and flat>=u.rf(0x71058bbb60) else k+1
    else:
     run(0x710246b5bc,(0x710246b654,),{UC_ARM64_REG_X20:B+0xc0,UC_ARM64_REG_X19:B+0x180,UC_ARM64_REG_W7:flag})
     ec=min(c,9998)+1;ed=min(d,9998)+1;ek=0 if ec>=threshold else k;eg=k+1 if ec>=threshold else k
    out['cases']['ground_air_counter']=out['cases'].get('ground_air_counter',0)+1
    for off,exp in ((0xc0,ec),(0xd0,ed),(0x26c,ek),(0x270,eg)):
     out['fields']['ground_air_counter']=out['fields'].get('ground_air_counter',0)+1
     if u.rs32(B+off)!=exp:out['mismatches'].append({'counter':hex(off),'got':u.rs32(B+off),'exp':exp})
    u.wq(frame+0x100-0x90,B+0xc0)
    run(0x71024af328,(0x71024af350,),{UC_ARM64_REG_W8:prev,UC_ARM64_REG_W25:threshold,UC_ARM64_REG_X19:B+0x180})
    out['cases']['landing_flag']=out['cases'].get('landing_flag',0)+1
    if u.r8(B+0x274)!=int(prev>=threshold and ed<threshold):out['mismatches'].append({'landing_flag':True})
out.update(slerp_calls=s['sl_calls'],null_calls=sum(u.null_calls.values()),auto_pages=u.auto_pages,plt_stubbed=u.plt_stubbed,libm=u.libm_used)
(R/'analysis/completion/r8/player_contact_fields_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
