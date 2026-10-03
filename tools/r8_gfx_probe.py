"""Read-only original source helper; optional output stays under analysis/completion/r8."""
import sys,re,struct,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web/tools'))
import xref,disasm,func_lookup
starts,rows=func_lookup.load()
def norm(q):
 v=int(q,16);return v-0x7100000000 if v>=0x7100000000 else v
def fn(off):
 r=func_lookup.lookup(starts,rows,off+0x7100000000);return hex(r[0]) if r else None
if sys.argv[1]=='body':
 s=(ROOT/sys.argv[2]).read_text(encoding='utf-8'); parts=re.split(r'(?=// ==== )',s)
 for a in sys.argv[3:]:
  p=next(p for p in parts if p.startswith('// ==== 710'+a)); hdr=p.split('\n  \n',1);p=hdr[-1];p=re.sub(r'^\s*(?:[a-zA-Z][a-zA-Z_0-9]*(?:\[[^]\n]*\])?) = 0;\n','',p,flags=re.M);print('// '+a+'\n'+p)
elif sys.argv[1]=='bl':
 import numpy as np
 m=xref.load_img(); w=np.frombuffer(m[:xref.TEXT_END&~3],dtype='<u4'); pos=np.nonzero((w&0xfc000000)==0x94000000)[0];imm=w[pos]&0x3ffffff;imm=imm.astype('int64');imm=np.where(imm&0x2000000,imm-0x4000000,imm);dst=pos*4+imm*4
 for a in sys.argv[2:]:
  print(a,[(hex(int(o)+0x7100000000),fn(int(o))) for o in pos[dst==norm(a)]*4])
elif sys.argv[1]=='vt':
 m=xref.load_img();o=norm(sys.argv[2]);n=int(sys.argv[3],0) if len(sys.argv)>3 else 16
 for i in range(n):
  v=struct.unpack_from('<Q',m,o+i*8)[0];print(hex(o+0x7100000000+i*8),hex(v),fn(v-0x7100000000) if 0x7100000000<=v<0x7103e9df50 else '')
elif sys.argv[1]=='globals':
 m=xref.load_img()
 for a in sys.argv[2:]:
  q=norm(a)+0x7100000000;n=struct.pack('<Q',q);p=0;out=[]
  while (p:=m.find(n,p))!=-1:out.append(hex(p+0x7100000000));p+=8
  print(a,out)
