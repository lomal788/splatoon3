"""가상 호출 슬롯 스캔(전체 text, numpy): `ldr xA,[xB,#off]` 뒤 win 명령 안에 `blr xA`가 있는 위치를 찾아,
주어진 오프셋들이 모두 한 함수(func_starts 기준)에 모인 함수만 출력.
사용: ui_vcall_scan.py <바이트오프셋...> [--win 4] [--lo 주소 --hi 주소]"""
import argparse, numpy as np
R="C:/dev/splatoon3"; B=0x7100000000; TEXT_END=0x3e9df50
ap=argparse.ArgumentParser(); ap.add_argument('offs',nargs='+'); ap.add_argument('--win',type=int,default=4)
ap.add_argument('--lo',default='0x7100000000'); ap.add_argument('--hi',default=hex(B+TEXT_END))
a=ap.parse_args(); offs=[int(o,16) for o in a.offs]
w=np.fromfile(R+"/extracted/exefs/main.img",dtype='<u4',count=TEXT_END//4)
starts=np.load(R+"/analysis/camera/func_starts.npy")
blr=np.nonzero((w&0xFFFFFC1F)==0xD63F0000)[0]
per={}
for o in offs:
    idx=np.nonzero((w&0xFFFFFC00)==(0xF9400000|((o//8)<<10)))[0]
    rt=w[idx]&0x1F
    s=set()
    for k in range(1,a.win+1):
        j=idx+k; ok=j<len(w)
        m=ok.copy(); m[ok]=((w[j[ok]]&0xFFFFFC1F)==0xD63F0000)&(((w[j[ok]]>>5)&0x1F)==rt[ok])
        for x in j[m]: s.add(int(x))
    per[o]=s
lo=int(a.lo,16)-B; hi=int(a.hi,16)-B
fn={}
for o,s in per.items():
    for x in s:
        if not (lo<=x*4<hi): continue
        f=int(starts[np.searchsorted(starts,x*4,'right')-1])
        fn.setdefault(f,{}).setdefault(o,[]).append(B+x*4)
for f,d in sorted(fn.items()):
    if len(d)==len(offs):
        print(hex(B+f), ' '.join(f"{hex(o)}:{','.join(hex(v) for v in d[o])}" for o in offs))
