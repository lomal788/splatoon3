"""[r5 physics] 객체 필드 → vtable 슬롯 호출 사슬 스캔.
`ldr xA,[xB,#fld]` → (win 안) `ldr xC,[xA]` → `ldr xD,[xC,#slot]` → `blr xD` 를 main 전체 text 에서 찾는다.
사용: r5_physics_chainscan.py <fld> <slot> [--win 8]"""
import argparse, numpy as np
R="C:/dev/splatoon3"; B=0x7100000000; TEXT_END=0x3e9df50
ap=argparse.ArgumentParser(); ap.add_argument('fld'); ap.add_argument('slot'); ap.add_argument('--win',type=int,default=8)
a=ap.parse_args(); fld=int(a.fld,16); slot=int(a.slot,16)
w=np.fromfile(R+"/extracted/exefs/main.img",dtype='<u4',count=TEXT_END//4)
starts=np.load(R+"/analysis/camera/func_starts.npy")
def ldr64(off): return (w&0xFFFFFC00)==(0xF9400000|((off//8)<<10))
i1=np.nonzero(ldr64(fld))[0]
L0=ldr64(0); LS=ldr64(slot); BLR=(w&0xFFFFFC1F)==0xD63F0000
for i in i1:
    A=int(w[i]&31)
    for j in range(i+1,min(i+a.win,len(w))):
        if L0[j] and ((w[j]>>5)&31)==A:
            C=int(w[j]&31)
            for k in range(j+1,min(j+a.win,len(w))):
                if LS[k] and ((w[k]>>5)&31)==C:
                    D=int(w[k]&31)
                    for m in range(k+1,min(k+a.win,len(w))):
                        if BLR[m] and ((w[m]>>5)&31)==D:
                            f=int(starts[np.searchsorted(starts,i*4,'right')-1])
                            print(hex(B+f), hex(B+i*4), hex(B+m*4)); break
                    break
            break
