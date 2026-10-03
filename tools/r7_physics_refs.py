"""r7 physics read-only scans of original main.reloc.img: call targets and data function pointers."""
import argparse, struct, sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
B=0x7100000000
R=Path(__file__).resolve().parents[2]
m=(R/'extracted/exefs/main.reloc.img').read_bytes()
w=np.frombuffer(m[:0x3e9df50&~3], dtype='<u4')
p=argparse.ArgumentParser();p.add_argument('mode',choices=['call','ptr']);p.add_argument('addresses',nargs='+');a=p.parse_args()
if a.mode=='call':
    ids=np.nonzero((w&0x7c000000)==0x14000000)[0]
    imm=(w[ids]&0x3ffffff).astype(np.int64);imm=np.where(imm&(1<<25),imm-(1<<26),imm)
    to=B+ids.astype(np.int64)*4+imm*4
    for val in a.addresses:
        target=int(val,16);pos=ids[to==target]
        print(hex(target), 'refs',len(pos))
        for k in pos:print(hex(B+int(k)*4),'BL' if int(w[k])&0x80000000 else 'B')
else:
    q=np.frombuffer(m[:len(m)&~7],dtype='<u8')
    for val in a.addresses:
        target=int(val,16);pos=np.nonzero(q==target)[0]
        print(hex(target),'data refs',len(pos))
        for k in pos:print(hex(B+int(k)*8))
