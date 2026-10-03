"""Game knockback original→actual queue RTTI/copy→Impact receiver→velocity update.
No original code patched. Original Q callback is RET, not a synthetic callback.
Synthetic world/body surrounding object; SDK RTTI guards are boundary stubs.
"""
import json,struct,random,sys
from pathlib import Path
from collections import Counter
import numpy as np
from unicorn.arm64_const import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/tools'))
# Reuse SDK boundary harness and independent arithmetic reference without running their suites.
g={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec(compile(Path(g['__file__']).read_text(encoding='utf-8').split('\nh=H(')[0],g['__file__'],'exec'),g)
H=g['H'];h=H([0x7101413a60]);h.executed=set();h.sdklog=Counter();h.stublog=Counter();h.heapobjects=[]
g2={'__file__':str(ROOT/'web/tools/r8_combat_impact_emu.py')}
s=Path(g2['__file__']).read_text(encoding='utf-8').split('\nr=Run();')[0].replace('M(F(1),F(-.016666668))','M(F(30),F(-.016666668))')
exec(compile(s,g2['__file__'],'exec'),g2)
F=g2['F'];M=g2['M'];A=g2['A'];bits=g2['bits'];Run=g2['Run']
class Adapter:
 def alloc(self,n):return h.alloc(n)
 def f32(self,a,x):h.mu.mem_write(a,struct.pack('<f',x))
 def u32(self,a,x):h.w32(a,x)
 def call(self,fn,*args,fargs=()):
  for reg,v in zip([UC_ARM64_REG_S0,UC_ARM64_REG_S1,UC_ARM64_REG_S2,UC_ARM64_REG_S3],fargs):h.mu.reg_write(reg,struct.unpack('<I',struct.pack('<f',v))[0])
  h.call(fn,list(args))
a=Adapter();r=Run.__new__(Run);r.u=a;r.mu=h.mu
for name,size in [('data',0x80),('comp',0x80),('input',0x30),('v',0x30),('step',0x80),('ctx',0x20),('body',0x80),('state',0x80),('kind',0x30),('output',0x80)]:setattr(r,name,h.alloc(size))
for aa,bb in [(r.comp+0x28,r.data),(r.data,r.output),(r.step+0x58,r.ctx),(r.ctx+8,r.body),(r.body+0x40,r.state),(r.state+0x28,r.kind)]:h.w64(aa,bb)
h.w32(r.state+0x40,3);h.w32(r.kind+8,0)
# Actual original Impact factory replaces supplied component/data. Allocator wrapper is a boundary.
a.call(0x71012a95f0,0);r.comp=h.mu.reg_read(UC_ARM64_REG_X0);r.data=h.r64(r.comp+0x28);h.w64(r.data,r.output)
assert h.r64(r.comp)==0x7105574708 and h.r32(r.data+0x14)==0x7fc00000
# Startup numeric writer only, prior debug/network initialization excluded.
h.mu.emu_start(0x71012ad708,0x71012ad754,count=100)
defaults=list(struct.unpack('<3f',h.mu.mem_read(0x7105826cd8,12)));assert defaults==[60.,30.,30.]
B=h.alloc(0xb000);actor=h.alloc(0x600);entity=h.alloc(0x40);Q=h.alloc(0x9a0);cfg=h.alloc(0x100);unused=h.alloc(0x20);bodylink=h.alloc(0x2700);vin=h.alloc(0x20);phys=h.alloc(0x30)
h.w64(cfg+0x18,unused)
# Reused original constructor Q block builds16-node88B freelist/default callbacks.
h.mu.reg_write(UC_ARM64_REG_X0,Q);h.mu.reg_write(UC_ARM64_REG_X20,cfg);h.mu.emu_start(0x71012e8f68,0x71012e9054,count=300)
assert h.r64(Q)==0x7105576e60 and h.r64(Q+0x928)==0x7105576ea8 and h.r32(Q+0xc)==16
components=h.alloc(0x50);component_array=h.alloc(8);h.w32(components+0x30,1);h.w64(components+0x38,component_array);h.w64(component_array,r.comp);h.w64(unused+0x10,components)
# Actual Q initializer performs original name+RTTI component search and writes Q990.
h.mu.reg_write(UC_ARM64_REG_X8,unused);h.mu.reg_write(UC_ARM64_REG_X21,Q);h.mu.emu_start(0x71012e9054,0x71012e9074,count=20000);assert h.r64(Q+0x990)==r.comp and h.r64(Q+0x998)==0
h.w64(B+8,actor);h.w64(actor+0x510,entity);h.w64(entity+0x20,Q);h.w64(B+0xa6c0,bodylink);h.w64(phys+0x10,unused);h.w32(0x71059975c0,0);h.mu.mem_write(0x71058bbb9a,b'\0')
rng=random.Random(0x12ad660);plans=[]
for i in range(1024):
 vec=[F(rng.uniform(-.48,.48)) for _ in range(3)] if i%23 else [F(0)]*3
 plans.append((vec,F(rng.choice([0,.01,.5,1,2])),F(rng.choice([0,.01,.5,1,2])),rng.randrange(7),rng.randrange(2),F(rng.choice([1/60,1/120,.2,1]))))
fields=0
for i,(vec,t,t2,kind,reject,dt) in enumerate(plans):
 # Decay marker NaN is original Impact ctor default; no arbitrary decay factor.
 h.mu.mem_write(r.data+8,b'\0'*0x60);a.f32(r.data+0x14,float('nan'));r.vec(vin,vec)
 a.call(0x71024c8318,B+0xa5f9,vin,kind,reject,fargs=(t,t2))
 assert h.r32(Q+8)==1
 msg=h.r64(h.r64(Q+0x10));want=[M(M(v,60),60) for v in vec]
 assert bytes(h.mu.mem_read(msg+0x40,12))==b''.join(map(bits,want))
 assert h.r32(msg+0x58)==kind and bytes(h.mu.mem_read(msg+0x5c,8))==b''.join(map(bits,[t,t2])) and h.mu.mem_read(msg+0x6d,1)[0]==reject
 # Original consumer performs real receiver then original destructor/freelist recycle.
 a.call(0x71012eb680,Q,phys)
 assert h.r32(Q+8)==0
 actual_receiver=bytes(h.mu.mem_read(r.data+8,0x60));n=g2['ln'](want);a.f32(r.data+0x20,0)
 # The standalone independent receiver reference handles exact normalized accumulation.
 r.receiver(([0]*3,[0]*3),want,t,t2,kind,reject,[0]*4,0,0)
 assert bytes(h.mu.mem_read(r.data+8,0x60))==actual_receiver,('queue receiver',i)
 imp=r.read(r.data+8,3);rej=r.read(r.data+0x24,3);strength=r.read(r.data+0x20,1)[0]
 out,state=r.update((imp,rej,float('nan'),t if n>0 else 0,t2 if n>0 else 0,strength,r.read(r.data+0x30,4),[0]*3,[0]*3,[0]*3,[0]*3,dt,[0,1,0]))
 fields+=3+25
# Expired-hold strength uses original default30; independent reference above now30.
r.update(([10,0,0],[0]*3,float('nan'),1,0,1,[0]*4,[0]*3,[0]*3,[0]*3,[0]*3,F(1/60),[0,1,0]));strength=r.read(r.data+0x20,1)[0];assert bits(strength)==bits(F(1)-g2['D'](F(1/60),M(F(30),F(.016666668))))
out={'cases':len(plans),'f32_update_fields':fields,'mismatch':0,'startup_f32':defaults,'strength_after_expired_hold_step':strength,'original_chain':['24c8318','12eb378','12d53f8','12eb680','12ad75c','12adb58','12eb0a0','12a95f0'],'original_ctor_prefix':'12e8f68..12e9074','SDK_stubs':dict(h.sdklog),'non_SDK_stubs':{hex(k):v for k,v in h.stublog.items()},'original_callback':'5576ea8+0→12ebbfc RET','scope':'synthetic player/entity/body context; mode3 Impact component path; final solver excluded; original globals numeric startup executed; runtime overrides not asserted'}
(ROOT/'analysis/completion/r8/combat_knockback_chain_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
