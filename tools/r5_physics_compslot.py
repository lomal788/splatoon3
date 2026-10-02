"""[r5 physics] 액터 구성요소 표 인덱스 K(actor+0x200 개수, +0x208 배열) 의 구성요소 +0x20 객체에 대해
vtable 슬롯 호출(ldr xD,[xC,#slot]; blr xD)이 win 명령 안에 있는 함수를 찾는다.
패턴: cmp wN,#K → (가까이) ldr xA,[xB,#0x20] → ldr xC,[xA] → ldr xD,[xC,#slot] → blr xD
사용: r5_physics_compslot.py <K> <slot...> [--win 40]"""
import argparse, numpy as np
R="C:/dev/splatoon3"; B=0x7100000000; TEXT_END=0x3e9df50
ap=argparse.ArgumentParser(); ap.add_argument('k'); ap.add_argument('slots',nargs='+'); ap.add_argument('--win',type=int,default=40)
a=ap.parse_args(); K=int(a.k,0); slots=[int(s,16) for s in a.slots]
w=np.fromfile(R+"/extracted/exefs/main.img",dtype='<u4',count=TEXT_END//4)
starts=np.load(R+"/analysis/camera/func_starts.npy")
# cmp wN,#K = subs wzr,wN,#K : 0x7100001F | K<<10 | N<<5
cmpi=np.nonzero((w&0xFFFFFC1F)==(0x7100001F|(K<<10)))[0]
def ldr64(off): return (w&0xFFFFFC00)==(0xF9400000|((off//8)<<10))
L20=ldr64(0x20); L0=ldr64(0); BLR=(w&0xFFFFFC1F)==0xD63F0000
LS={s:ldr64(s) for s in slots}
for i in cmpi:
    for j in range(i+1,min(i+12,len(w))):
        if L20[j]:
            A=int(w[j]&31)
            # find ldr xC,[xA]
            for k in range(j+1,min(j+a.win,len(w))):
                if L0[k] and ((w[k]>>5)&31)==A:
                    C=int(w[k]&31)
                    for m in range(k+1,min(k+8,len(w))):
                        for s,L in LS.items():
                            if L[m] and ((w[m]>>5)&31)==C:
                                f=int(starts[np.searchsorted(starts,i*4,'right')-1])
                                print(hex(B+f), 'cmp',hex(B+i*4),'slot',hex(s),'at',hex(B+m*4))
                    break
            break
