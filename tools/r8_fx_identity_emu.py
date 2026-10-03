"""r8 actual init_array identity writer124f5f0→original HitEffect floor consumer.
Whole original init function plus original SDK trivial IP/error constructors. Final emission captured.
"""
import json,struct,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s={'__file__':str(ROOT/'web/tools/r8_hiteffect_consume_emu.py')}
source=(ROOT/'web/tools/r8_hiteffect_consume_emu.py').read_text(encoding='utf-8');head,tail=source.split('\ne=E(',1);exec(head,s)
E,R=s['E'],s['R'];Counter=s['Counter'];UC_ARM64_REG_PC=s['UC_ARM64_REG_PC']
class I(E):
 def _block(self,mu,a,size,user):
  if R.PLT_LO<=a<R.PLT_HI:
   name=self._plt_name(a)
   if name in ['_ZN2nn3err18ErrorResultVariantC1Ev','_ZN2nn3ldn15MakeIpv4AddressEhhhh']:
    self.mathlog[name]+=1;mu.reg_write(UC_ARM64_REG_PC,self.sdkbase+self.syms[name][0]);return
  super()._block(mu,a,size,user)
s['I']=I;exec('\ne=I('+tail.split('# queue copy/formula')[0],s);e=s['e'];G=s['G'];W=s['W'];req=s['req'];packet=s['packet'];pool=s['pools'][0]
# Verify actual dynamic INIT_ARRAY membership and order from raw MOD0 and relocated pointers.
raw=(ROOT/'extracted/exefs/main.raw.img').read_bytes() if (ROOT/'extracted/exefs/main.raw.img').exists() else (ROOT/'extracted/exefs/main.img').read_bytes()
img=(ROOT/'extracted/exefs/main.reloc.img').read_bytes();mod0=struct.unpack_from('<I',raw,4)[0];dyn=mod0+struct.unpack_from('<i',raw,mod0+4)[0];tags={}
while True:
 t,v=struct.unpack_from('<qQ',raw,dyn);dyn+=16
 if not t:break
 tags.setdefault(t,v)
arr=[struct.unpack_from('<Q',img,tags[25]+i*8)[0] for i in range(tags[27]//8)];index=arr.index(0x710124f5f0);copyindex=arr.index(0x71012541c0);assert index<copyindex
identity=[0x3f800000 if i in [0,4,8] else 0 for i in range(9)];expected=struct.pack('<9I',*identity);rng=random.Random(20261003);initcases=0
for k in range(128):
 # Arbitrary old36-byte contents, even NaN payloads: exact original stores replace all nine words.
 e.mu.mem_write(0x71058237b0,struct.pack('<9I',*[rng.getrandbits(32) for i in range(9)]));e.call(0x710124f5f0,[]);assert bytes(e.mu.mem_read(0x71058237b0,36))==expected;initcases+=1
# Reuse verified normal request setup, actual init→wholecontroller floor velocity0 branch.
cases=0;examples=[]
for paint in [0,1]:
 for k in range(512):
  pos=[struct.unpack('<f',struct.pack('<f',rng.uniform(-400,400)))[0] for i in range(3)];b=packet(1,0,0,paint,(0,1,0),(0,0,0));struct.pack_into('<3f',b,0,*pos);e.mu.mem_write(req,bytes(b));e.call(0x71027b4704,[G,req]);node=e.r64(G+0x50)-0x60;e.events=[];e.emitters=[];e.call(0x71027b877c,[W,node,1]);assert len(e.emitters)==1
  expect=struct.pack('<12f',1,0,0,pos[0],0,1,0,pos[1],0,0,1,pos[2]);got=bytes.fromhex(e.emitters[0]['matrix_hex']);assert got==expect,(paint,k,e.emitters,pos)
  if k==0:examples.append({'paint':paint,'position':pos,'matrix_hex':got.hex(),'slot':e.emitters[0]['slot']})
  e.w64(G+0x50,G+0x50);e.w64(G+0x58,G+0x50);e.w32(G+0x60,0);e.w64(node,e.r64(G+0x68));e.w64(G+0x68,node);cases+=1
out={'init_cases':initcases,'floor_matrix_cases':cases,'float32_words':cases*12+initcases*9,'mismatches':0,'writer':'0x710124f5f0','matrix':'0x71058237b0','init_array':{'address':hex(R.BASE+tags[25]),'bytes':tags[27],'index':index,'writer_pointer_address':hex(R.BASE+tags[25]+index*8),'copy12541c0_index':copyindex},'identity_words_hex':[f'{x:08x}' for x in identity],'examples':examples,'SDK_original':dict(e.mathlog),'SDK_stubs':dict(e.sdklog),'non_SDK_stubs':{hex(k):v for k,v in e.stublog.items()},'captured_boundaries':dict(e.capture_counts),'null_reads':0,'scope':'Full native init function and nativeSDK pure dependencies→original whole controller with originalShooter config fixture; floor matrix all12f32 independent bitmatch. MainSDK code patches0. Does not execute full bootstrap/GPU/audio/other positive-velocity branches; backend137f558 captured.'}
(ROOT/'analysis/completion/r8/fx_identity_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
