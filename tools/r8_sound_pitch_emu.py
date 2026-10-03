"""r8 original group/voice pitch composition. All arithmetic functions run with no stubs.
Synthetic parameter blocks; no SDK voice delivery / waveform playback execution claim.
"""
import json,struct,sys,itertools
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC
ROOT=Path(__file__).resolve().parents[2];F=np.float32
u=UC();mu=u.mu;g=u.alloc(0x180);parent=u.alloc(0x180);handle=u.alloc(0x40);v=u.alloc(0x240);dyn=u.alloc(0x80)
def p(a,x):mu.mem_write(a,struct.pack('<Q',x))
def f(a,x):mu.mem_write(a,struct.pack('<f',float(x)))
def i(a,x):mu.mem_write(a,struct.pack('<I',x&0xffffffff))
def read(a):return bytes(mu.mem_read(a,4))
cases=0;clamps=0
vals=[-2.,-0.,0.,.25,.7,1.,1.25,2.]
# Each group composes local then automated then parent. Voice local x spatial x dynamic x group.
for a,b,c,d,e in itertools.product(vals,repeat=5):
 mu.mem_write(g,b'\0'*0x180);mu.mem_write(parent,b'\0'*0x180);mu.mem_write(v,b'\0'*0x240);mu.mem_write(dyn,b'\0'*0x80)
 f(g+0x9c,a);f(g+0xdc,b);f(parent+0x11c,c);mu.mem_write(g+0x79,b'\1');p(g+0x50,handle);p(handle+0x20,parent)
 u.call(0x710383836c,g);gp=F(F(F(a)*F(b))*F(c));assert read(g+0x11c)==struct.pack('<f',gp)
 f(v+0x3c,d);f(v+0x7c,e);f(dyn+0x14,1.25);p(v+0xd8,dyn);p(v+0xd0,g)
 # Negative filter kinds default during composition; other fields are synthetic zeros.
 i(v+0x44,-1);i(v+0x48,-1);i(v+0x84,-1);i(v+0x88,-1);i(dyn+0x1c,-1);i(dyn+0x20,-1);i(g+0x124,-1);i(g+0x128,-1)
 u.call(0x710383df38,v);raw=F(F(F(F(d)*F(e))*F(1.25))*gp);expected=F(0) if raw<=0 else raw
 assert read(v+0x13c)==struct.pack('<f',expected),(a,b,c,d,e,read(v+0x13c),expected)
 assert struct.unpack('<I',read(v+0x144))[0]==1 and struct.unpack('<I',read(v+0x148))[0]==3
 cases+=1;clamps+=int(raw<=0)
out={'cases':cases,'mismatches':0,'pitch_clamps_to_zero':clamps,'stubs':[],'functions':['383836c group local*automation*parent via37ded4c/37debc0','383df38 voice local*spatial*dynamic*group then nonpositive clamp'],'precision':'f32 after each MUL, original no FMA','scope':'synthetic group/voice blocks; original full composition, SDK playback command not executed; optional per-channel arrays null'}
(ROOT/'analysis/completion/r8/sound_pitch_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
