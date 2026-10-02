"""[r6 physics] 인라인 functor vtable(slot2 = 자기 vtable 을 [x1] 에 쓰는 clone) 전수 → slot0 이 3x4 행렬 이동 성분(+0xc/+0x1c/+0x2c)을 쓰는 것만 출력.
액터+0x4e0 functor(0x7100f76f78 이 물리 행렬을 액터+0x28c 에 쓰기 직전 호출) 후보 찾기용."""
import struct, sys, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
B=0x7100000000
img=open('C:/dev/splatoon3/extracted/exefs/main.reloc.img','rb').read()
w=np.frombuffer(img[:0x3e9df50],dtype='<u4')
def adrp_page(ins,pc):
    immlo=(ins>>29)&3; immhi=(ins>>5)&0x7FFFF; v=((immhi<<2)|immlo)<<12
    if v&(1<<32): v-=1<<33
    return (pc&~0xFFF)+v
isadrp=(w&0x9F00001F)==0x90000008
cands=[]
for i in np.nonzero(isadrp)[0]:
    i=int(i); pc=B+i*4
    a1=int(w[i+1]); a2=int(w[i+2])
    if (a1&0xFFC003FF)!=0x91000108: continue      # add x8,x8,#imm
    if a2!=0xF9000028: continue                   # str x8,[x1]
    V=adrp_page(int(w[i]),pc)+((a1>>10)&0xFFF)
    off=V-B
    if off<0 or off+0x28>len(img): continue
    s2=struct.unpack_from('<Q',img,off+0x10)[0]
    if s2!=pc: continue
    s0=struct.unpack_from('<Q',img,off)[0]
    cands.append((V,s0))
print('functor vtables',len(cands))
def touches_translation(f):
    j=(f-B)//4; hits=set()
    for k in range(j,j+80):
        ins=int(w[k])
        if ins==0xD65F03C0: break
        # ldr/str s (32-bit fp) unsigned imm: 0xBD400000 / 0xBD000000
        if (ins&0xFF000000)==0xBD000000:
            off=((ins>>10)&0xFFF)*4
            if ((ins>>5)&31)==1: hits.add(off)
    return hits
for V,s0 in cands:
    h=touches_translation(s0)
    if {0xc,0x1c,0x2c}&h:
        print(hex(V),'slot0',hex(s0),sorted(hex(x) for x in h))
