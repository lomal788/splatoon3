"""Original v46 emitter render-state builder and follow shader-key builder.
Only native NVN endpoints are recorded stubs; descriptor translation remains original.
"""
import sys,struct,json,itertools,random,re
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC,BASE,STUB
from vfx_emitter46 import emitters
import effect_vfxb as V
u=UC();mu=u.mu
out=u.alloc(0x200);res=u.alloc(0xef0);er=u.alloc(0x480);key=u.alloc(0x20)
def ptr(a,x):mu.mem_write(a,struct.pack('<Q',x))
ptr(er+0x10,res)
src=Path('analysis/decomp/vfx/vfx_lib_02.c').read_text(encoding='utf-8')
bind={int(a,16):name for a,name in re.findall(r'DAT_710([0-9a-f]+) = \(\(\*\(code \*\)param_2\)\(param_1,"([^"]+)"\)',src)}
# More robust independent string/assignment reader for the original binder.
bind={int(m.group(1),16):m.group(2) for m in re.finditer(r'DAT_710([0-9a-f]+) = [^\n]+\(param_1,"([^"]+)"\)',src)}
slots=[0x57d5be0,0x57d5be8,0x57d5bf0,0x57d5bf8,0x57d5c58,0x57d5c60,0x57d5c90,0x57d5c98,0x57d5da8,0x57d5db0,0x57d5db8,0x57d5dc8,0x57d5dc0,0x57d5dd0,0x57d5dd8,0x57d5d60,0x57d5d68,0x57d5d70,0x57d5d78,0x57d5d80,0x57d5ca8,0x57d5cb0,0x57d5cb8,0x57d5cc0]
callbacks={STUB+0x500+i*4:bind[s] for i,s in enumerate(slots)}
for i,s in enumerate(slots):ptr(BASE+s,STUB+0x500+i*4)
trace=[]
def hook(m,a,z,_):
 name=callbacks[a];trace.append((name,tuple(m.reg_read(r)&0xffffffff for r in [UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4])))
mu.hook_add(UC_HOOK_CODE,hook,begin=STUB+0x500,end=STUB+0x500+len(slots)*4-1)
factors=[1,2,3,4,9,10,5,6,7,8,97,98,99,100,11,16,17,18]
rgb_src=[6,6,6,0,5,1];dst=[7,1,1,2,1,7];alpha_src=[1,1,1,0,5,1];eq=[0,0,2,0,0,0]
def get(name):return [args for n,args in trace if n==name]
checks=0
for mode,depth,test,write,cull in itertools.product(range(6),range(8),range(2),range(2),range(3)):
 data=bytearray(0xef0);data[0xbd8:0xbe0]=bytes([1,test,depth,write,0x55,0xaa,mode,cull]);mu.mem_write(res,bytes(data));mu.mem_write(out,b'\0'*0x200);trace.clear()
 u.call(BASE+0x82804c,out,0,res+0xbd8)
 assert get('nvnColorStateSetBlendEnable')[0][1]==1
 assert get('nvnBlendStateSetBlendFunc')[0]==(factors[rgb_src[mode]],factors[dst[mode]],factors[alpha_src[mode]],factors[dst[mode]])
 assert get('nvnBlendStateSetBlendEquation')[0][:2]==(eq[mode]+1,eq[mode]+1)
 assert get('nvnDepthStencilStateSetDepthTestEnable')[0][0]==test
 assert get('nvnDepthStencilStateSetDepthWriteEnable')[0][0]==write
 assert get('nvnDepthStencilStateSetDepthFunc')[0][0]==depth+1
 assert get('nvnDepthStencilStateSetStencilTestEnable')[0][0]==0
 assert get('nvnPolygonStateSetCullFace')[0][0]==[0,2,1][cull]
 checks+=1
# All nonzero boolean encodings, including arbitrary ignored bytes.
rng=random.Random(82804)
for i in range(256):
 data=bytearray(rng.randbytes(0xef0));data[0xbd8]=rng.randrange(256);data[0xbd9]=rng.randrange(256);data[0xbda]=rng.randrange(8);data[0xbdb]=rng.randrange(256);data[0xbde]=rng.randrange(6);data[0xbdf]=rng.randrange(256)
 mu.mem_write(res,bytes(data));trace.clear();u.call(BASE+0x82804c,out,0,res+0xbd8)
 assert get('nvnColorStateSetBlendEnable')[0][1]==(data[0xbd8]!=0)
 assert get('nvnDepthStencilStateSetDepthTestEnable')[0][0]==(data[0xbd9]!=0)
 assert get('nvnDepthStencilStateSetDepthWriteEnable')[0][0]==(data[0xbdb]!=0)
 assert get('nvnPolygonStateSetCullFace')[0][0]==(2 if data[0xbdf]==1 else 1 if data[0xbdf]==2 else 0)
 checks+=1
want=['WpShtrBullet1Emit','CmnFloorSplash1Emit','CmnFloorSplashNear1Emit','CmnFloorSplashDist1Emit','CmnWallSplash1Emit','WpShtrMzfNml']
v=V.Vfxb('analysis/completion/r8/static.vfxb');actual=[]
for es,n,d,parent,bo,em in emitters(v,want):
 mu.mem_write(res,v.d[bo:bo+0xef0]);trace.clear();u.call(BASE+0x8182f4,er,0)
 actual.append({'eset':es,'emitter':n,'render_hex':v.d[bo+0xbd8:bo+0xbe8].hex(),'trace':trace.copy()})
# The whole original shader-key builder has no external calls.
follow_cases=0
for follow in [0,1,2,3,127,128,255]:
 for i in range(128):
  mu.mem_write(res,b'\0'*0xef0);mu.mem_write(res+0xa93,bytes([follow]));mu.mem_write(key,b'\0'*0x20)
  u.call(BASE+0x81a6f0,key,er)
  assert u.ru32(key+8)&0xe00==({0:512,1:2048,2:1024}.get(follow,0))
  follow_cases+=1
result={'render_synthetic_cases':checks,'actual_render_emitters':len(actual),'actual':actual,'follow_cases':follow_cases,'follow_key_masks':[512,2048,1024],'mismatches':0,'native_endpoint_stubs':list(callbacks.values()),'scope':'whole original082804c and its descriptor/translation helpers, actual08182f4 caller, whole081a6f0; NVN backend recorded only, no rasterization'}
Path('analysis/completion/r8/vfx_state_emu.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='actual'}))
