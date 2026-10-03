"""r7 physics: find bphsh resource +38 count / +40 pointer readers with same base register."""
import numpy as np,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[2];B=0x7100000000
w=np.fromfile(R/'extracted/exefs/main.reloc.img',dtype='<u4',count=0x3e9df50//4)
# Exact unsigned-offset encodings, independent of Rt/Rn.
mask=0xfffffc00
N=np.nonzero((w&mask)==(0xb9400000|((0x38//4)<<10)))[0]
P=np.nonzero((w&mask)==(0xf9400000|((0x40//8)<<10)))[0]
for n in N:
    b=(int(w[n])>>5)&31
    for j in P[np.searchsorted(P,max(0,n-30)):np.searchsorted(P,n+31)]:
        if ((int(w[j])>>5)&31)==b:
            print(hex(B+int(n)*4),hex(B+int(j)*4),'base',b)
