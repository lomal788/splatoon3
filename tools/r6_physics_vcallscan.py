"""[r6 physics] 범위 안에서 `ldr xD,[xC,#slot]` → (win 안) `blr xD` 가상 호출과, 같은 함수 안의 즉시 오프셋 접근을 함께 찾는다.
사용: r6_physics_vcallscan.py <lo> <hi> <slot> [--need off,off...]  (need: 함수 안에 #off 접근(ldr/str/add imm)이 있어야 출력)"""
import argparse, sys, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
R="C:/dev/splatoon3"; B=0x7100000000
ap=argparse.ArgumentParser(); ap.add_argument('lo'); ap.add_argument('hi'); ap.add_argument('slot')
ap.add_argument('--need',default=''); ap.add_argument('--win',type=int,default=6)
a=ap.parse_args(); lo=int(a.lo,16)-B; hi=int(a.hi,16)-B; slot=int(a.slot,16)
w=np.fromfile(R+"/extracted/exefs/main.img",dtype='<u4',count=hi//4+4)
starts=np.load(R+"/analysis/camera/func_starts.npy")
def fstart(i): return int(starts[np.searchsorted(starts,i*4,'right')-1])
LS=(w&0xFFFFFC00)==(0xF9400000|((slot//8)<<10)); BLR=(w&0xFFFFFC1F)==0xD63F0000
need=[int(x,16) for x in a.need.split(',') if x]
def has_off(i0,i1,off):
    seg=w[i0:i1]
    # ldr/str 64 unsigned imm, add imm, movz
    m=((seg&0xFFC00000)==0xF9400000)&(((seg>>10)&0xFFF)==off//8) if off%8==0 else np.zeros(len(seg),bool)
    m|=((seg&0xFFC00000)==0xF9000000)&(((seg>>10)&0xFFF)==off//8) if off%8==0 else False
    m|=((seg&0x7F800000)==0x11000000)&(((seg>>10)&0xFFF)==(off&0xFFF))&((((seg>>22)&1)==0) if off<0x1000 else (((seg>>22)&1)==1))
    m|=((seg&0x7F800000)==0x52800000)&(((seg>>5)&0xFFFF)==off)
    return bool(np.any(m))
res={}
for i in np.nonzero(LS[lo//4:hi//4])[0]+lo//4:
    D=int(w[i]&31)
    for m in range(i+1,i+a.win):
        if BLR[m] and ((w[m]>>5)&31)==D:
            f=fstart(i); res.setdefault(f,[]).append(i*4); break
for f,lst in sorted(res.items()):
    i0=f//4; nxt=int(starts[np.searchsorted(starts,f,'right')]) ; i1=nxt//4
    if need and not all(has_off(i0,i1,o if o<0x1000 else o) for o in need): continue
    print(hex(B+f), ' '.join(hex(B+x) for x in lst))
