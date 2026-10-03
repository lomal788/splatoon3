from pathlib import Path
import numpy as np
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
D=Path('extracted/exefs/main.reloc.img').read_bytes();W=np.frombuffer(D[:0x3e00000],'<u4');md=Cs(CS_ARCH_ARM64,CS_MODE_ARM);md.skipdata=True
c=np.flatnonzero((((W&0xffc00000)==0x79400000)&(((W>>10)&0xfff)==13))|(((W&0xffc00000)==0x39400000)&(((W>>10)&0xfff)==26)))
for ix in c:
 if ix*4<0x900000 or ix*4>0xb30000:continue
 reg=int(W[ix]&31);end=min(ix+10,len(W));ins=list(md.disasm(D[ix*4:end*4],0x7100000000+int(ix)*4));txt='\n'.join(f'{x.address:#x} {x.mnemonic} {x.op_str}' for x in ins)
 if any((x.mnemonic in ('tbz','tbnz') and x.op_str.startswith('w'+str(reg)+', #5')) or (x.mnemonic in ('tst','and') and x.op_str.endswith('#0x20')) for x in ins):print(txt+'\n')
