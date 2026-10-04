"""Original ControllerSet defaults/factory and camera entry-normal consumer.

Only the initializer3a027c0..7fc fragment (before atexit) is run, then the
original factory delegate/whole helper factory. Camera consumer fragment is
24dddd0..24dde08. This is not whole actor/resource/world/frame execution.
"""
import hashlib,json,random,struct
from pathlib import Path
from unicorn.arm64_const import UC_ARM64_REG_SP,UC_ARM64_REG_X8
from r6_player_uc import PUC,STACK,STACK_SZ

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/camera_100_r10/boom'
u=PUC()
err=u.call(0x7103b8bcdc,0,count=3000000);param=u.x(0)
default={'error':err,'creator':'0x7103b8bcdc','VT':hex(u.rq(param)),
         'ClassName':u._cstr(u.rq(param+0x2d0)).decode(),
         'source':'original creator, raw ControllerSet child/parent data omit ClassName'}
assert err is None and default['ClassName']=='Default' and u.rq(param)==0x710574e0a8
u.mu.emu_start(0x7103a027c0,0x7103a027fc,count=30)
delegate=0x710599d560
factory={'name':u._cstr(u.rq(0x710599d558)).decode(),'delegateVT':hex(u.rq(delegate)),
         'factory':hex(u.rq(delegate+8)),'delegateEntry':hex(u.rq(u.rq(delegate)))}
err=u.call(u.rq(u.rq(delegate)),delegate,0);helper=u.x(0)
factory.update(error=err,helperVT=hex(u.rq(helper)),
               actorBindingSlot10=hex(u.rq(u.rq(helper)+0x10)),
               descriptorSlot20=hex(u.rq(u.rq(helper)+0x20)),
               shapePredicateSlotA0=hex(u.rq(u.rq(helper)+0xa0)))
assert err is None and u.rq(helper)==0x71055762a8
assert u.rq(u.rq(helper)+0x20)==0x71012d71f8 and u.rq(u.rq(helper)+0xa0)==0x7103a52554
rng=random.Random(101001)
normals=[(0.,1.,0.),(-0.,-1.,0.)]+[tuple(rng.uniform(-1,1) for _ in range(3)) for _ in range(62)]
point=u.alloc(0x70);entry=u.alloc(16);u.wq(entry,point)
sp=STACK+STACK_SZ-0x10000;rows=[]
for normal in normals:
 bits=struct.pack('<3f',*normal);u.mu.mem_write(point+0xc,bits)
 for flag in (0,1):
  u.w8(entry+8,flag);u.mu.reg_write(UC_ARM64_REG_SP,sp);u.mu.reg_write(UC_ARM64_REG_X8,entry)
  u.mu.emu_start(0x71024dddd0,0x71024dde08,count=30)
  actual=b''.join(bytes(u.mu.mem_read(sp+off,4)) for off in (0x68,0x70,0x7c))
  expected=bits if flag else b''.join(struct.pack('<I',struct.unpack('<I',bits[i:i+4])[0]^0x80000000) for i in (0,4,8))
  rows.append({'entryBit0':flag,'inputBits':bits.hex(),'actualBits':actual.hex(),'expectedBits':expected.hex(),'match':actual==expected})
out={'scope':__doc__,'controllerSetDefault':default,'helperFactory':factory,
     'normalConsumer':'bit0=1 keeps pointNormal; bit0=0 flips sign bit, including signed zero',
     'normalCases':len(rows),'normalF32Fields':len(rows)*3,'normalMismatches':sum(not x['match'] for x in rows),'normalRows':rows,
     'nativeCodeSha256':hashlib.sha256(bytes(u.mu.mem_read(0x71024dddd0,0x38))).hexdigest(),
     'null':{str(k):v for k,v in u.null_calls.items()},'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed,'libm':u.libm_used}
(OUT/'source_contract.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert out['normalMismatches']==0 and not u.null_calls and not u.auto_pages and not u.faults
print(json.dumps({k:out[k] for k in ('controllerSetDefault','helperFactory','normalCases','normalF32Fields','normalMismatches','null','auto','faults','plt','libm')}))
