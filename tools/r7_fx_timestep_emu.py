"""r7 fx: active no-emission original emitter update dt writer/age accumulator.
No callbacks, particles, child emitters, fields or function stubs. Full 081c0b8 executes.
"""
import json,random,struct,sys
from unicorn import UC_HOOK_MEM_WRITE,UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *
from r7_fx_transform_emu import VM,F,ROOT,HEAP

def main():
 sys.stdout.reconfigure(encoding='utf-8');vm=VM();m=vm.mu;E,R,ES,ER,CTX=[HEAP+x for x in (0,0x2000,0x4000,0x6000,0x8000)]
 writes=[];m.hook_add(UC_HOOK_MEM_WRITE,lambda mu,access,a,s,v,ud:writes.append(hex(mu.reg_read(UC_ARM64_REG_PC))) if a==E+0x50 else None)
 m.hook_add(UC_HOOK_MEM_UNMAPPED,lambda mu,access,a,s,v,ud:print('FAULT',hex(mu.reg_read(UC_ARM64_REG_PC)),hex(a)) or False)
 for a,n in ((E,0x1000),(R,0x1000),(ES,0x1000),(ER,0x1000),(CTX,0x100)):m.mem_write(a,bytes(n))
 vm.q(E+0xb0,R);vm.q(E+0x250,ER);vm.q(E+0x80,ES);vm.q(ER+0x10,R);vm.q(ER+0x18,R+0x70);vm.w(E+0xae8,1);vm.w(E+0x240,1);vm.q(E+0xc0,HEAP+0x9000);m.mem_write(HEAP+0x9000,bytes(0x40))
 m.mem_write(R+0xa92,b"\1");vm.w(ER+0x460,300);vm.fs(E+0x70,[1,1,1]);vm.fs(E+0x50,[1]);vm.fs(R+0xae0,[1,1,1]);vm.fs(E+0x460,[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);m.mem_write(E+1,b'\1')
 age=F(0);ok=bad=0;examples=[];rnd=random.Random(2026100703)
 inputs=list(map(F,[1,.5,2,0,.125,.25]))+[F(rnd.choice([.125,.25,.5,1,2])) for _ in range(300)]
 for dt in inputs:
  ret=vm.call(0x710081c0b8,E,0,0,0,0,CTX,0,fargs=(dt,));age=F(age+dt)
  gd=bytes(m.mem_read(E+0x50,4));ga=bytes(m.mem_read(E+0x4c,4));match=gd==struct.pack('<f',dt) and ga==struct.pack('<f',age)
  if match:ok+=1
  else:
   bad+=1
   if len(examples)<5:examples.append({'dt':float(dt),'gotdt':struct.unpack('<f',gd)[0],'gotage':struct.unpack('<f',ga)[0],'age':float(age),'return':ret})
 out={'function':'0x710081c0b8','ok':ok,'bad':bad,'dt_writer_pc':sorted(set(writes)),'stubs':[],'scope':'active GPU_TIME emitter, no emission/particles/children/callbacks; dt copied +50, age +4C accumulates','examples':examples}
 (ROOT/'analysis/completion/r7/fx_timestep_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()


