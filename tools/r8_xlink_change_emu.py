"""r8 whole original new-action start/end/transfer control; emit and event rebind are explicit boundaries."""
from pathlib import Path
import json,itertools
src=Path('web/tools/r6_range_xlink_emu.py').read_text(encoding='utf-8').split('\nDMG =')[0]
ns={'__name__':'r8_change_prefix','__file__':str(Path('web/tools/r6_range_xlink_emu.py').resolve())};exec(compile(src,'r8_change_prefix','exec'),ns)
h=ns['H']();mu=h.mu;BIND=0x7103890444;mu.mem_write(BIND,ns['RET']);bind=[]
def bh(mu,a,s,u):bind.append(mu.reg_read(ns['UC_ARM64_REG_X0']))
mu.hook_add(ns['UC_HOOK_CODE'],bh,begin=BIND,end=BIND)
regs=[ns['UC_ARM64_REG_X0'],ns['UC_ARM64_REG_X1'],ns['UC_ARM64_REG_X2'],ns['UC_ARM64_REG_X3'],ns['UC_ARM64_REG_X4']]
cases=0;bad=[]
for nf,of,fi,live,stale,match,frame,loop,crc in itertools.product(range(32),[0,8,9,12],[0,1],[0,1],[0,1],[0,1],[2,3,4,7,8],[0,1],[0,1]):
 h.nxt=ns['HEAP'];h.emits=[];bind.clear()
 C=h.alloc(0x40);I=h.alloc(0x60);Y=h.alloc(0x40);U=h.alloc(0x40);V=h.alloc(0x40);R=h.alloc(0xc0);RB=h.alloc(0x40);T=h.alloc(0x50);SH=h.alloc(0x20);S=h.alloc(0x50);OA=h.alloc(0x20);NA=h.alloc(0x20)
 h.w64(C+8,I);h.w64(I+0x38,Y);h.w64(Y+0x18,U);h.w64(U,V)
 for off in [0x10,0x20,0x28]:h.w64(V+off,ns['STUB']+off)
 h.w64(U+0x20,R);h.w64(R+8,RB);h.w32(RB+0x1c,2);h.w8(R+0xb0,1);h.w64(R+0x48,T)
 h.w64(C+0x10,SH);h.w64(SH+8,S);h.w64(C+0x30,OA);h.w16(OA+8,0);h.w32(OA+0xc,0);h.w16(NA+8,1);h.w32(NA+0xc,1)
 Q=h.alloc(0x40);QQ=h.alloc(0x40);UR=h.alloc(0x90);CT=h.alloc(0x60);AT=h.alloc(0x10);NAME=h.alloc(0x10)
 h.q_ret=Q;h.w64(Q,V);h.w64(Q+0x10,QQ);h.w64(QQ+0x20,UR);h.w64(UR+0x28,CT);h.w32(UR+0x78,2);h.w64(UR+0x80,AT);h.w8(AT+2,2*loop);h.w8(AT+10,2*loop)
 h.w64(T+8,CT);h.w64(T+0x28+8,CT if match else CT+0x30);h.w32(T+0x10,3);h.w32(T+0x18,8);h.w16(T+0x1c,of);h.w64(T+0x20,0x7000)
 h.w32(T+0x28+0x10,3);h.w32(T+0x28+0x18,8);h.w16(T+0x28+0x1c,nf);h.w64(T+0x28+0x20,0x7001)
 if nf&16 and not nf&12:h.w64(T+0x28+0x10,NAME)
 h.w8(S+0x24,fi);HD=h.alloc(0x60);h.w32(HD+0x20,99);h.w32(S+0x18,98 if stale else 99);h.w64(S+0x10,HD if live else 0)
 mu.reg_write(ns['UC_ARM64_REG_SP'],ns['STACK']+0xf0000);mu.reg_write(ns['UC_ARM64_REG_X30'],ns['END'])
 for r,x in zip(regs,[C,NA,frame,U,crc]):mu.reg_write(r,x)
 mu.emu_start(0x7103896874,ns['END'],count=200000)
 kind=1 if nf&4 else 2 if nf&8 else 3 if nf&16 else 0
 eligible=kind==1 or kind==3 and crc==0 or kind==0 and ((3<=frame<8) if loop else frame==3)
 search=bool(nf&1 and match and (eligible or kind==0))
 transfer=search and bool(fi);oldmark=search and (fi or (of&12)==8)
 emits=([1] if eligible and not transfer else [])+([0] if not oldmark and (of&12)==8 and (not of&1 or not fi) else [])
 newfi=int(eligible or transfer);oldfi=1 if oldmark and (of&12)==8 else fi
 moved=bool(transfer and live and not stale)
 actual=[e['idx'] for e in h.emits]
 okay=actual==emits and h.r8(S+0x24)==(1 if 0 in emits else oldfi) and h.r8(S+0x25)==int(oldmark) and h.r8(S+0x28+0x24)==newfi and h.r32(C+0x24)==frame and h.r32(C+0x28)==frame and h.r64(C+0x30)==NA and bool(bind)==moved
 argsok=all(e['x1']==0 and e['x3']==0x7000+e['idx'] and e['x4']==(CT if e['idx']==0 or match else CT+0x30) for e in h.emits)
 if not okay or not argsok:bad.append({'input':[nf,of,fi,live,stale,match,frame,loop,crc],'actual':actual,'expected':emits,'fields':[h.r8(S+0x24),h.r8(S+0x25),h.r8(S+0x28+0x24)],'expectedfields':[oldfi,int(oldmark),newfi],'bind':len(bind),'moved':moved});break
 cases+=1
out={'function':'0x7103896874','new_cases':cases,'mismatches':len(bad),'examples':bad[:2],'stubs':['3899c68 emit argument recorder','3890444 event rebind records call only','accessorvt10 syntheticQ, vt20 returnsfalse (nooverwriteproperty)'],'scope':'32lowflags/start-endpriority/rangeboundaries/previousnameemptyCRC/bit0 matching fired andunfiredold/live-stalehandle transfer/endcancel with backendHD28=0; rebindbackend andnamedoverwriteproperty excluded'}
Path('analysis/completion/r8/xlink_change_emu.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));assert not bad
