"""Visual gap audit: native display entry block + p1385 VAT data. Not native GPU execution."""
import sys,json,math,struct,hashlib,itertools
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC
sys.path.insert(0,str(Path(__file__).resolve().parent))
from weapon_ink_emu import Emu
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/visual_gap'
sys.stdout.reconfigure(encoding='utf-8')
e=Emu();sm=e.alloc(0x300);human=e.alloc(0x40);squid=e.alloc(0x40);own=e.alloc(0x200);info=e.alloc(0x1000);rail=e.alloc(0x200)
stop=[]
def boundary(uc,addr,size,ud):
 if addr in (0x710243e460,0x710243e464,0x710243e488):stop.append(addr);uc.emu_stop()
e.uc.hook_add(UC_HOOK_CODE,boundary)
cases=[]
for hidden,human_on,squid_on,f0,model in itertools.product([0,1],[0,1],[0,1],[0,60,61,90],[0,4]):
 e.uc.mem_write(sm,bytes(0x300));e.uc.mem_write(e.body,bytes(0xb000));e.w64(sm+8,human);e.w64(sm+0x10,squid);e.w64(sm+0x20,own);e.w64(own+0x108,e.body);e.w64(e.body+8,info);e.w64(e.body+0xa668,rail);e.w32(rail+0x1b8,0xffffffff)
 e.w32(human+8,0 if human_on else 0xffffffff);e.w32(squid+8,0 if squid_on else 0xffffffff);e.w32(sm+0xf0,f0);e.w32(info+0x7a0,model);e.uc.mem_write(e.body+0x7a0,bytes([hidden]));e.uc.mem_write(sm+0xf6,b'\x01')
 before=len(stop);e.run(0x710243e2dc,x=(sm,0));assert len(stop)==before+1
 hlf=bool(human_on and f0>=61 and model!=4 and not hidden);body=bool(human_on and not hlf and not hidden)
 expected=[int(body),int(hlf),int(bool(squid_on and not hidden)),0];got=[e.uc.mem_read(sm+off,1)[0] for off in [0xf4,0xf5,0xf6,0xf8]];assert got==expected,(hidden,human_on,squid_on,f0,model,got,expected);assert e.uc.mem_read(sm+0xf7,1)==b'\x01'
 cases.append({'hidden':hidden,'human':human_on,'squid':squid_on,'f0':f0,'modelType':model,'flags':got,'boundaryPC':hex(stop[-1])})
assert not e.calls and not e.faults
native={'function':'0x710243e2dc','scope':'entry through ordinary/invalid-rail display branch; stopped at e460/e464 before counter/material-reset/secondary shading','cases':len(cases),'bad':0,'PLT_calls':len(e.calls),'faults':len(e.faults),'fixtures':'SM/wrappers/body/type and invalid rail handle supplied; B7a0 injected, producer not run','rows':cases}
(OUT/'display_gate.json').write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding='utf-8')
a=np.load(ROOT/'analysis/effect_sound/tex_float/bulletcmn_vsp.npy');bad=[];length=[]
for i,x in enumerate(a[:,:,3].flat):
 v=float(x);h=int(np.float16(v).view(np.uint16));av=abs(v);assert av>0 and math.isfinite(v)
 lg=math.log2(av);exp=math.trunc(lg)-(lg<0);restored=((exp+15)<<10)+math.trunc((2**(-exp)*av)*1024-1024)+(0x8000 if v<0 else 0)
 if restored!=h:bad.append(i)
 j=(h-0x400 if h<0x8000 else 0x8400-h)+0x77ff;z=(2*j)*(-1.6276572e-5)+.999983728;assert abs(z)<=1
 c=abs(z);theta=(((-.0187293*c+.0742610022)*c-.2121144)*c+1.5707288)*math.sqrt(1-c)
 if z<0:theta=math.pi-theta
 phi=j*3.88322115;n=[math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),z];length.append(abs(sum(k*k for k in n)-1))
assert not bad
shader={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['p1385.vert','p1385.frag','p1385.options.txt']}
vat={'level':'shader [read] + actual texture [data]; calculations [reimplementation], NOT original GPU execution','program':1385,'variation':5583,'texture':'bulletcmn_vsp','shape_H_W_RGBA':list(a.shape),'half_restore_matches':a.shape[0]*a.shape[1],'half_bad':len(bad),'normal_length2_max_error_double_reimplementation':max(length),'shader_sha256':shader,'unresolved':'frag location2.w read with no corresponding vertex export in tool output; actual stage default/link binding not established. k UBO12.x producer remains.'}
(OUT/'p1385_evidence.json').write_text(json.dumps(vat,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'native_display':{'cases':len(cases),'bad':0,'calls':0,'faults':0},'p1385_texture':list(a.shape),'half_matches':vat['half_restore_matches'],'GPU_executed':False},ensure_ascii=False))
