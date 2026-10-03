"""Original XLNK common-loader metadata prefix, actual two v0 files.
No patched code/stubs; stops before debug logging/relocation. Independent raw mask counts.
"""
import hashlib,json,struct
from pathlib import Path
from unicorn.arm64_const import *
from r7_fx_transform_emu import VM,HEAP,STACK
from effect_xlink import load_bytes
ROOT=Path(__file__).resolve().parents[2]
def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def u64(b,p):return struct.unpack_from('<Q',b,p)[0]
def main():
 vm=VM();vm.mu.mem_map(HEAP+0x100000,0x400000)
 C,P,S,B=HEAP,HEAP+0x1000,HEAP+0x2000,HEAP+0x10000
 examples=[];cases=0
 for kind,rel in [('ELink','ELink2/elink2.Product.100.belnk.zs'),('SLink','SLink2/slink2.Product.100.bslnk.zs')]:
  raw=load_bytes(str(ROOT/'extracted/romfs'/rel));n=u32(raw,0x48);pdt=((0x60+4*n+7)&~7)+8*n
  size=u32(raw,pdt);p=pdt+size;asset=0;records=u32(raw,0x10)
  for _ in range(records):
   k=u64(raw,p).bit_count();asset+=k;p+=8+4*k
  assert p==u64(raw,0x18)
  trig=0
  for _ in range(u32(raw,0x14)):
   k=u32(raw,p).bit_count();trig+=k;p+=4+4*k
  assert p==u64(raw,0x20) and asset==u32(raw,0x0c)
  vm.mu.mem_write(B,raw);vm.w(P,u32(raw,pdt+4));vm.w(P+4,u32(raw,pdt+8));vm.w(P+8,u32(raw,pdt+16));vm.w(P+0x40,size)
  first=None
  for count in [asset,0,1,0xffffffff]:
   vm.w(B+0xc,count);vm.mu.mem_write(C,b'\xaa'*0xa0)
   for reg,x in zip([UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3],[C,B,P,S]):vm.mu.reg_write(reg,x)
   vm.mu.reg_write(UC_ARM64_REG_SP,STACK+0xf0000)
   vm.mu.emu_start(0x71038945a8,0x710389473c,count=1000)
   assert vm.mu.reg_read(UC_ARM64_REG_PC)==0x710389473c
   got=bytes(vm.mu.mem_read(C,0xa0));assert u32(got,0)==count
   ptrs=[u64(got,o)-B if u64(got,o) else None for o in range(0x28,0x80,8)]
   assert ptrs[0]==pdt+size and ptrs[1]==u64(raw,0x18) and ptrs[2]==u64(raw,0x20)
   if first is None:first=got[4:]
   else:assert got[4:]==first
   cases+=1
  examples.append({'kind':kind,'path':rel,'sha256_decompressed':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'asset_records':records,'asset_values':asset,'overwrite_records':u32(raw,0x14),'overwrite_values':trig,'total_including_overwrite':asset+trig,'numUserParam':u32(raw,pdt+4),'parameter_define_size':size,'asset_table':pdt+size,'overwrite_table':u64(raw,0x18),'loader_offsets':ptrs})
 result={'original_prefix':['0x71038945a8','0x710389473c exclusive'],'metadata_cases':cases,'mismatch':0,'stubs':[],'scope':'metadata setup prefix only; resource bytes original; relocation/user binding not executed; numResParam perturbation never changes other fields','files':examples}
 (ROOT/'analysis/completion/r8/xlink_count_emu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
