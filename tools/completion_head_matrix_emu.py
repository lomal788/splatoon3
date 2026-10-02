"""원본 PlayerCustomHead ManualBindSRT 결합 실행. 외부 모델 슬롯은 명시한 스텁만 사용."""
import ctypes, json, random, struct
from pathlib import Path
from network_uc import UC, STUB
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X1
ROOT=Path(__file__).resolve().parents[2]
F=0x71026e613c
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
crt=ctypes.CDLL('ucrtbase'); crt.fmaf.argtypes=[ctypes.c_float]*3; crt.fmaf.restype=ctypes.c_float
fma=lambda a,b,c:crt.fmaf(a,b,c)
pack=lambda a:struct.pack('<12f',*a)
u=UC(); m=u.mu
head=u.alloc(0x500); owner=u.alloc(0x400); vt=u.alloc(0x240); body=u.alloc(0x80)
arr=u.alloc(8); ref=u.alloc(8); bone=u.alloc(16); bvt=u.alloc(0x100); target=u.alloc(0x400); inp=u.alloc(0x40)
wq=lambda a,x:m.mem_write(a,struct.pack('<Q',x))
wq(head+0x10,owner); wq(owner,vt); wq(vt+0x1f8,STUB+0x504)
wq(head+0x110,body); wq(body+0x40,arr); wq(arr,ref); wq(ref,bone); wq(bone,bvt); wq(bvt+0x78,STUB+0x500)
wq(head+0x3f0,target)
m.mem_write(head+0x3bc,b'\xff'*16)
state={}
def hook(mu,addr,size,data):
    if addr==STUB+0x500:
        mu.mem_write(mu.reg_read(UC_ARM64_REG_X1),pack(state['B']))
m.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x500,end=STUB+0x504)
def calc(B,S,fused=True):
    out=[]
    for r in range(3):
        b=B[4*r:4*r+4]
        for c in range(4):
            p=f32(S[c]*b[2])
            p=fma(S[4+c],b[0],p) if fused else f32(f32(S[4+c]*b[0])+p)
            p=fma(S[8+c],b[1],p) if fused else f32(f32(S[8+c]*b[1])+p)
            out.append(f32((b[3] if c==3 else 0.0)+p))
    return out
rng=random.Random(0x26e613c)
I=[1,0,0,0,0,1,0,0,0,0,1,0]
B_identity_in_getter_layout=[0,0,1,0,1,0,0,0,0,1,0,0]
cases=[('identity',B_identity_in_getter_layout,I),('translation',B_identity_in_getter_layout,[1,0,0,2,0,1,0,3,0,0,1,4]),('zero',B_identity_in_getter_layout,[0]*12)]
for i in range(256):
    cases.append((f'random-{i}',[f32(rng.uniform(-8,8)) for _ in range(12)],[f32(rng.uniform(-4,4)) for _ in range(12)]))
results=[]; sequential_diff=0
for name,B,S in cases:
    state['B']=B; m.mem_write(head+0x380,pack(S)); m.mem_write(inp,pack(I)); m.mem_write(target+0x280,b'\xa4')
    u.call(F,head,inp)
    got=bytes(m.mem_read(target+0x238,48)); expected=pack(calc(B,S))
    assert got==expected,(name,got.hex(),expected.hex())
    assert bytes(m.mem_read(target+0x280,1))==b'\xa4'
    separate=pack(calc(B,S,False)); sequential_diff+=got!=separate
    if len(results)<4:results.append({'case':name,'output_bits':list(struct.unpack('<12I',got)),'output':list(struct.unpack('<12f',got))})
# Body pointer absent branch leaves target matrix untouched, but owner transform submit is still reached.
wq(head+0x110,0); sentinel=bytes(range(48)); m.mem_write(target+0x238,sentinel); u.call(F,head,inp)
assert bytes(m.mem_read(target+0x238,48))==sentinel
out={'function':hex(F),'matrix_cases':len(cases),'bit_matches':len(cases),'body_absent_cases':1,'sequential_f32_different_cases':sequential_diff,'stubs':['owner.vt+0x1f8: ret','body bone.vt+0x78: supplied raw 12 f32'],'disabled_paths':['pack/rope bone update: indices -1','model callbacks and object list: null/zero','copy-pair loop: count zero'],'limits':['supplied bone get layout only; actual bone get producer and render scheduling not executed','HairArrange map and cloth solver not executed'],'examples':results}
p=ROOT/'analysis/completion/graphics_head_matrix_emu.json'; p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['function','matrix_cases','bit_matches','body_absent_cases','sequential_f32_different_cases']},ensure_ascii=False))
