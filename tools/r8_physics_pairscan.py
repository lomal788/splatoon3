from pathlib import Path
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[2];B=0x7100000000;m=(R/'extracted/exefs/main.reloc.img').read_bytes();lo=0x3a00000;hi=0x3b40000
w=np.frombuffer(m[lo:hi],dtype='<u4');i=np.nonzero((w&0xffc00000)==0xa9000000)[0]
for k in i:
 z=int(w[k]);o=((z>>15)&127);o=(o-128 if o&64 else o)*8
 if o in (0xc8,0xd0,0x108,0x110) and ((z>>5)&31)!=31: print(hex(B+lo+int(k)*4),hex(o),'regs',z&31,(z>>10)&31,'base',(z>>5)&31)
