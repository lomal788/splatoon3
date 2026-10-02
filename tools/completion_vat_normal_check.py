"""p1383 VAT A의 half 비트 복원/방향 복호화 표본 대조. 원본 GPU 실행은 아님."""
import json,math,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
a=np.load(ROOT/'analysis/effect_sound/tex_float/bulletshtr_vsp.npy')
assert a.shape==(83,6,4),a.shape
rows=[]; maxerr=0; mismatch=[]
for i,v in enumerate(a[:,:,3].flat):
    v=float(v); h=int(np.float16(v).view(np.uint16)); av=abs(v)
    # 문서 p1383의 명령식. 샘플 값은 normal half이며 log2/exp2 재구현 대조만 수행.
    e=math.trunc(math.log2(av)); e-=math.log2(av)<0
    restored=((e+15)<<10)+math.trunc((2**(-e)*av)*1024-1024)+(0x8000 if v<0 else 0)
    if restored!=h:mismatch.append([i,h,restored])
    q=(h-0x400 if h<0x8000 else 0x8400-h)+0x77ff
    c=1.0-(2*q+1)/61438.0
    if abs(c)>1:raise ValueError((i,h,q,c))
    x=abs(c); theta=(((-0.0187293*x+0.0742610022)*x-0.2121144)*x+1.5707288)*math.sqrt(1-x)
    if c<0:theta=math.pi-theta
    phi=q*3.88322115
    n=[math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),c]
    err=abs(sum(t*t for t in n)-1); maxerr=max(maxerr,err)
    if len(rows)<6:rows.append({'half':hex(h),'value':v,'q':q,'normal_before_matrix':n})
assert not mismatch,mismatch[:3]
out={'level':'[판독] 셰이더식; 표본 계산은 [재구현]','source':'analysis/vfx/shader/p1383.vert:340-564','texture_shape':list(a.shape),'half_restore_matches':498,'half_restore_mismatches':len(mismatch),'normal_length2_max_error_double_reimplementation':maxerr,'note':'GPU log2/exp2/sin/cos/fma의 비트 일치는 검증하지 않음. acos 근사 다항식 때문에 길이는 정확한 1이 아님.','examples':rows}
(ROOT/'analysis/completion/fx_vat_normal_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['texture_shape','half_restore_matches','half_restore_mismatches','normal_length2_max_error_double_reimplementation']},ensure_ascii=False))
