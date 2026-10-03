"""Locate controller field loads followed by vtable38 virtual call, original executable only."""
import sys,json,numpy as np
from pathlib import Path
B=0x7100000000
w=np.fromfile('extracted/exefs/main.img',dtype='<u4');starts=np.load('analysis/camera/func_starts.npy')
L=lambda x,o:(x&0xfffffc00)==(0xf9400000|((o//8)<<10))
res=[]
for off in [0xf8,0x108]:
 for i in np.nonzero(L(w,off))[0]:
  dest=int(w[i]&31);vtreg=None
  for j in range(i+1,min(i+24,len(w))):
   x=int(w[j])
   if L(x,0) and ((x>>5)&31)==dest:vtreg=x&31
   if vtreg is not None and L(x,0x38) and ((x>>5)&31)==vtreg:
    fnreg=x&31
    for k in range(j+1,min(j+10,len(w))):
     z=int(w[k])
     if (z&0xfffffc1f) in [0xd63f0000,0xd61f0000] and ((z>>5)&31)==fnreg:
      f=int(starts[np.searchsorted(starts,i*4,'right')-1]);res.append({'load':hex(B+int(i)*4),'slot':hex(B+j*4),'call':hex(B+k*4),'fstart':hex(B+f),'off':hex(off)});break
p=Path('analysis/completion/r8/listener_vcalls.json');p.write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
print('candidates',len(res));print(json.dumps(res,indent=2))
