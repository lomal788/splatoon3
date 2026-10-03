"""Original AS request/firsttick connected probe; resource/binder metadata fixtures only."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *
from r5_gfx_stage_emu import Emu,BASE,RET
FRAME=6.;LOOP=False
E=Emu();mu=E.mu
node=E.alloc(0x20);body=E.alloc(0x60);mgr=E.alloc(0x80);raw=E.alloc(0x100);nt=E.alloc(0x24);slot=E.alloc(0x300);inst=E.alloc(0xc0);entry=E.alloc(0x40);meta=E.alloc(0x200);out=E.alloc(0xc0);events=E.alloc(0xc0);H=E.alloc(0xc0);binder=E.alloc(0x10);bvt=E.alloc(0xf0);AS=E.alloc(0x200);desc=E.alloc(0x48);rm=E.alloc(0x20);rmvt=E.alloc(0x250);dbg=E.alloc(0x100);dvt=E.alloc(0x30);dbgptr=E.alloc(8);rng=E.alloc(16);cmdrec=E.alloc(0x20);name=E.alloc(8);mtable=E.alloc(0x48);pool=E.alloc(0x80);fbuf=E.alloc(0xc0);blend=E.alloc(0x80);obinder=E.alloc(0x10);ovt=E.alloc(0xf0);guard=E.alloc(8);token=E.alloc(8);seen=[];fault=[];trace=[]
for off in range(0x100,0x130,4):mu.mem_write(RET+off,struct.pack('<I',0xd65f03c0))
E.w(node,'Q',BASE+0x5743410);E.w(node+8,'HH',3,0);E.w(node+0x10,'QQ',mgr,body);E.w(mgr+8,'Q',raw);E.w(mgr+0x18,'Q',nt);E.w(raw+0x10,'I',1);E.w(raw+0x24,'I',0x40);mu.mem_write(raw+0x40,b'ToSquid\0');E.w(nt,'IIf',3,0,1.);E.w(slot+0x98,'Q',meta);E.w(slot+0x170,'I4xQ',1,entry);E.w(inst+0x58,'hh',-1,-1);E.w(inst+0x91,'B',0xff);E.w(inst+0x92,'B',0);E.w(inst+0xa4,'f',-1);E.w(inst+0xac,'f',-1);E.w(inst+0x6c,'6f',1,1,1,1,1,1);E.w(inst+0x84,'fff',1,1,1);E.w(entry,'I',1);E.w(slot+0xd4,'ff',1.,1.);E.w(slot+0x48,'Q',out);E.w(slot+0x68,'Q',events);E.w(slot+0x58,'Q',H);E.w(H+8,'Q',node);E.w(H+0x30,'Q',inst);E.w(H+0x28,'4h',0,-1,-1,-1);E.w(H+0x91,'B',0);E.w(slot+0x20,'Q',rm);E.w(slot+0x38,'Q',binder);E.w(binder,'Q',bvt);E.w(bvt+0x18,'Q',RET+0x104);E.w(bvt+0x20,'Q',RET+0x100);E.w(bvt+0x28,'Q',RET+0x108);E.w(bvt+0xe0,'Q',RET+0x10c);E.w(slot+0x10,'Q',raw+0x40);E.w(slot+0x1d8,'I',1);E.w(slot+0xe4,'III',0,1,0);E.w(slot+0xf8,'f',-1);E.w(rm,'Q',rmvt);E.w(rm+0x10,'Q',mgr);E.w(rmvt+0x180,'Q',RET+0x110);E.w(rmvt+0x188,'Q',RET+0x114);E.w(dbg,'Q',dvt);E.w(dvt+0x20,'Q',RET+0x118);E.w(dbgptr,'Q',dbg);E.w(BASE+0x5790698,'Q',dbgptr);E.w(BASE+0x599d220,'Q',dbg);E.w(BASE+0x5997950,'Q',rng);E.w(rng,'4I',1,2,3,4);E.w(AS+0x18,'I4xQ',1,desc);E.w(desc,'Q',slot);E.w(AS+0x48,'Q',rm);E.w(name,'Q',raw+0x40);E.w(rmvt+0x1d0,'Q',RET+0x11c);E.w(desc+0x43,'B',0xff);E.w(meta+0x18,'I4xQ',1,mtable);E.w(mtable+0x20,'4I',*[0xffffffff]*4);E.w(AS+0xc8,'Q',pool);E.w(desc+0x20,'4I',*[0xffffffff]*4);E.w(slot+0x50,'Q',fbuf);E.w(slot+0x60,'Q',blend);E.w(AS+0x28,'Q',obinder);E.w(obinder,'Q',ovt);E.w(ovt+0xa0,'Q',RET+0x120);E.w(ovt+0xe8,'Q',RET+0x124);E.w(guard,'B',1);E.w(token,'Q',BASE+0x57419d0);E.w(BASE+0x57a7b10,'QQ',guard,token);E.w(rmvt+0x40,'Q',RET+0x128)
def hook(mu,a,size,u):
 if RET+0x100<=a<RET+0x130:
  x=[mu.reg_read(UC_ARM64_REG_X0+i) for i in range(4)];ret=0
  if a==RET+0x100:mu.reg_write(UC_ARM64_REG_S0,struct.unpack('<I',struct.pack('<f',FRAME))[0]);seen.append('binderFrameCountMetadata')
  elif a==RET+0x104:seen.append('binderAnimIndex0')
  elif a==RET+0x108:ret=int(LOOP);seen.append('binderLoopMetadata')
  elif a==RET+0x10c:ret=raw+0x40;seen.append('binderClipName')
  elif a==RET+0x110:ret=node;mu.mem_write(x[2],struct.pack('<Q',cmdrec));seen.append('resourceCommandNode')
  elif a==RET+0x114:seen.append('resourceCommandIndex0')
  elif a==RET+0x118:seen.append('debugdisabled')
  elif a==RET+0x11c:seen.append('resourceTransitionMetadataNone')
  elif a==RET+0x120:seen.append('outputCapacity0')
  elif a==RET+0x124:seen.append('outputClear')
  elif a==RET+0x128:ret=raw+0x40;seen.append('resourceStringByIndex0')
  mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
 elif a==BASE+0x3e99ef0:
  x=mu.reg_read(UC_ARM64_REG_X0);mu.reg_write(UC_ARM64_REG_X0,0 if mu.mem_read(x,1)[0]&1 else 1);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));seen.append("PLTguardAcquire")
 elif a==BASE+0x3e99f00:
  x=mu.reg_read(UC_ARM64_REG_X0);mu.mem_write(x,b"\x01");mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));seen.append("PLTguardRelease")
 elif a==BASE+0x3e99f20:
  x=[mu.reg_read(UC_ARM64_REG_X0+i) for i in range(3)];mu.mem_write(x[0],bytes(mu.mem_read(x[1],x[2])));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR));seen.append('PLTmemcpy')
 elif a in [BASE+p for p in (0x39d3608,0x39bc994,0x39bcdbc,0x39d3b10,0x39d3dcc,0x39ab2c4)]:trace.append(dict(pc=hex(a),cur=E.r(entry+4,'f')[0],flags=E.r(entry,'I')[0],x4=mu.reg_read(UC_ARM64_REG_X4)))
def invalid(mu,access,a,size,value,u):fault.append(dict(pc=hex(mu.reg_read(UC_ARM64_REG_PC)),addr=hex(a),access=access,lr=hex(mu.reg_read(UC_ARM64_REG_LR))));return False
mu.hook_add(UC_HOOK_CODE,hook);mu.hook_add(UC_HOOK_MEM_INVALID,invalid)
steps=[]
for fn,args,fp in [(0x399e340,[AS,name,0,0,0,0],[-1.,-1.]),(0x399f848,[AS,0,0,0], [1.])]:
 try:E.call(BASE+fn,args,fp);steps.append(dict(fn=hex(fn),pc=hex(mu.reg_read(UC_ARM64_REG_PC)),cur=E.r(entry+4,'f')[0],prev=E.r(entry+8,'f')[0],reported=E.r(slot+0x104,'f')[0],entry=bytes(mu.mem_read(entry,64)).hex()))
 except Exception as ex:steps.append(dict(fn=hex(fn),error=str(ex),pc=hex(mu.reg_read(UC_ARM64_REG_PC))));break
j=dict(steps=steps,trace=trace,stubs=seen,faults=fault)
Path('analysis/completion/r8/as_request_tick_probe.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');print(json.dumps(j,indent=2))
