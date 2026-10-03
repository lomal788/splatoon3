"""r8 entire original AlwaysTrigger calc + actual user force-request writer.
Reuse original image loader only; no r6 scenarios rerun. Emit/accessor/disable are explicit boundary stubs.
"""
from pathlib import Path
import json,itertools,struct
src=Path('web/tools/r6_range_xlink_emu.py').read_text(encoding='utf-8').split('\nDMG =')[0]
ns={'__name__':'r8_always_prefix','__file__':str(Path('web/tools/r6_range_xlink_emu.py').resolve())};exec(compile(src,'r8_always_prefix','exec'),ns)
h=ns['H'](); mu=h.mu
for fn in [0x710389c130,0x710389d410]:assert any(int(p[0],16)==fn for p in [x.split('\t') for x in Path('analysis/functions/main.nso.tsv').read_text().splitlines()[1:]])
regs=[ns['UC_ARM64_REG_X0'],ns['UC_ARM64_REG_X1']]
def call(fn,args):
 mu.reg_write(ns['UC_ARM64_REG_SP'],ns['STACK']+0xf0000);mu.reg_write(ns['UC_ARM64_REG_X30'],ns['END'])
 for r,x in zip(regs,args):mu.reg_write(r,x)
 mu.emu_start(fn,ns['END'],count=200000)
cases=0;bad=[]
for force,bit1,live,stale,qvalid,rvalid,index,n in itertools.product([0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1,2,0xffffffff],[0,1,3]):
 h.nxt=ns['HEAP'];h.emits=[]
 C=h.alloc(0x40);I=h.alloc(0x40);Y=h.alloc(0x40);U=h.alloc(0x40);V=h.alloc(0x40);R=h.alloc(0xc0);B=h.alloc(0x40);T=h.alloc(0x18*max(1,n));SH=h.alloc(0x20);S=h.alloc(0x28*max(1,n))
 h.w64(C+8,I);h.w64(I+0x38,Y);h.w64(Y+0x18,U);h.w64(U,V);h.w64(V+0x10,ns['STUB']+0x10);h.w32(U+0x18,index);h.w64(U+0x20,R);h.w64(U+0x28,R)
 h.w8(C+0x18,force);h.w8(R+0xb0,rvalid);h.w64(R+8,B);h.w32(B+0x28,n);h.w64(R+0x60,T);h.w64(C+0x10,SH);h.w64(SH+8,S)
 Q=h.alloc(0x40);QQ=h.alloc(0x40);UR=h.alloc(0x90);CT=h.alloc(0x30*max(1,n));AT=h.alloc(8*max(1,n))
 h.q_ret=Q
 if qvalid:h.w64(Q+0x10,QQ)
 h.w64(QQ+0x20,UR);h.w32(QQ+0x18,0);h.w64(UR+0x28,CT);h.w32(UR+0x78,n);h.w64(UR+0x80,AT)
 for i in range(n):
  h.w64(T+i*0x18+8,CT+i*0x30);h.w64(T+i*0x18+0x10,0x7000+i);h.w8(AT+i*8+2,2*bit1)
  hd=h.alloc(0x40);h.w32(hd+0x20,99);h.w64(S+i*0x28+0x10,hd if live else 0);h.w32(S+i*0x28+0x18,98 if stale else 99)
 call(0x710389c130,[C])
 want=list(range(n)) if rvalid and (force or qvalid and bit1) and (not live or stale) else []
 actual=[e['idx'] for e in h.emits];argsok=all(e['x1']==2 and e['x3']==0x7000+e['idx'] and e['x4']==CT+e['idx']*0x30 for e in h.emits)
 if actual!=want or not argsok or h.r8(C+0x18)!=(0 if rvalid else force):bad.append([force,bit1,live,stale,qvalid,rvalid,index,n,actual,want])
 cases+=1
assert not bad,bad[:3]
# Actual force-byte writer. Disable cleanup is outside this test and recorded separately.
mu.mem_write(0x710389d258,ns['RET']);disable=[]
def dh(mu,a,s,u):disable.append(mu.reg_read(ns['UC_ARM64_REG_X0']))
mu.hook_add(ns['UC_HOOK_CODE'],dh,begin=0x710389d258,end=0x710389d258)
active_cases=0
for bit,request,hasres,hasctrl in itertools.product([0,2],[0,1],[0,1],[0,1]):
 h.nxt=ns['HEAP'];O=h.alloc(0x100);M=h.alloc(0x80);R=h.alloc(0x80);C=h.alloc(0x40);disable.clear()
 h.w32(O+0xf8,0x84|bit);h.w64(O+0x38,M);h.w64(O+0xa0,R if hasres else 0);h.w64(R+0x60,C if hasctrl else 0)
 call(0x710389d410,[O,request]);go=(request^((bit&2)>>1))==0
 expected=(0x84|(0 if request else 2)) if go else 0x84|bit
 assert h.r32(O+0xf8)==expected
 assert h.r8(C+0x18)==int(go and request and hasres and hasctrl)
 assert bool(disable)==bool(go and not request)
 active_cases+=1
out={'always_function':'0x710389c130','whole_original_cases':cases,'mismatches':len(bad),'force_writer':'0x710389d410','force_writer_cases':active_cases,'stubs':['3899c68 emit argument recorder','accessorvt10 syntheticQ','389d258 disable cleanup boundary'],'scope':'entireAlwayscalc, 0/1/3triggers, twoownerbuffers/indexfallback, invalidresource forcepreservation, live/stalegeneration, force/nonforce and loopasset gating; actualuseractivation request gate andAlwaysC18 writer; backend event lifecycle excluded'}
Path('analysis/completion/r8/xlink_always_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
