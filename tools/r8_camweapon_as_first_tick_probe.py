"""AS entry/enter/first tick probe. Core original routines; binder metadata boundary explicit."""
from pathlib import Path
import struct,json
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
E=Emu();mu=E.mu;node=E.alloc(0x20);body=E.alloc(0x50);mgr=E.alloc(0x60);raw=E.alloc(0x80);nt=E.alloc(0x24);slot=E.alloc(0x300);ctx=E.alloc(0x40);inst=E.alloc(0xc0);entry=E.alloc(0x40);meta=E.alloc(0x200);out=E.alloc(0x80);rctx=E.alloc(0x40);binder=E.alloc(0x10);bvt=E.alloc(0xf0);seen=[];fault=[]
E.w(node,'Q',BASE+0x5743410);E.w(node+8,'HH',3,0);E.w(node+0x10,'QQ',mgr,body);E.w(mgr+8,'Q',raw);E.w(mgr+0x18,'Q',nt);E.w(raw+0x10,'I',1);E.w(nt,'IIf',3,0,1.);E.w(slot+0x98,'Q',meta);E.w(slot+0x170,'I4xQ',1,entry);E.w(ctx+8,'Q',slot);E.w(ctx+0x20,'f',1.);E.w(ctx+0x2d,'B',1);E.w(inst+0x58,'hh',-1,-1);E.w(inst+0x92,'B',0);E.w(inst+0xa4,'f',-1);E.w(inst+0xac,'f',-1);E.w(inst+0x80,'f',1);E.w(entry,'I',1);E.w(slot+0xd4,'f',1.);E.w(out+8,'I',0);E.w(rctx+8,'QQ',out,slot);E.w(rctx+0x20,'f',1.);E.w(slot+0x38,'Q',binder);E.w(binder,'Q',bvt);E.w(bvt+0x20,'Q',RET+0x100);mu.mem_write(RET+0x100,struct.pack('<I',0xd65f03c0))
def hook(mu,a,size,u):
 if a==RET+0x100:mu.reg_write(UC_ARM64_REG_S0,struct.unpack('<I',struct.pack('<f',6.))[0]);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));seen.append('binderFrameCount6')
def invalid(mu,access,a,size,value,u):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),addr=hex(a),access=access));return False
mu.hook_add(UC_HOOK_CODE,hook,begin=RET+0x100,end=RET+0x100);mu.hook_add(UC_HOOK_MEM_INVALID,invalid)
steps=[]
for fn,args,fp in [(0x39bc994,[node,ctx,inst,entry,0,0],[6.]),(0x39bcdbc,[node,entry,ctx,inst,1],[]),(0x39d3b10,[node,ctx,inst],[]),(0x39d3dcc,[node,rctx,inst],[])]:
 try:
  E.call(BASE+fn,args,fp);steps.append(dict(fn=hex(fn),pc=hex(mu.reg_read(UC_ARM64_REG_PC)),entry=bytes(mu.mem_read(entry,64)).hex(),report=E.r(rctx+0x24,'f')[0],inst=bytes(mu.mem_read(inst,0xc0)).hex()))
 except Exception as ex:steps.append(dict(fn=hex(fn),error=str(ex),pc=hex(mu.reg_read(UC_ARM64_REG_PC))));break
outj=dict(steps=steps,seen=seen,faults=fault)
Path('analysis/completion/r8/as_first_tick_probe.json').write_text(json.dumps(outj,indent=2)+'\n',encoding='utf8');print(json.dumps(outj,indent=2))
