"""Original SDK NVN dispatch/viewport/swizzle command encoding.

SDK RELATIVE relocations applied only in RAM. Debug-init guard is supplied to
skip system debugger initialization; fallback dispatch chosen by synthetic BSS.
Actual game viewport calls then run actual SDK functions without API stubs.
Encoded command words are tested, not executed on Maxwell/GPU/present display.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm64_const import *

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
ns={'__file__':str(ROOT/'web/tools/r8_combat_rate_rows_emu.py')}
exec((ROOT/'web/tools/r8_combat_rate_rows_emu.py').read_text(encoding='utf8').split('\nh=H(')[0],ns)
H,R=ns['H'],ns['R'];B=R.BASE;S=0x7400000000;F=np.float32
def packf(v):return struct.pack('<'+'f'*len(v),*map(float,v))
d=bytearray((ROOT/'extracted/exefs/sdk.img').read_bytes())
mo=struct.unpack_from('<I',d,4)[0];dy=mo+struct.unpack_from('<i',d,mo+4)[0];tags={};p=dy
while True:
    t,v=struct.unpack_from('<qQ',d,p);p+=16
    if not t:break
    tags.setdefault(t,v)
relative=0;defined_symbol_relocs=0
for a,n in [(tags.get(7,0),tags.get(8,0)),(tags.get(23,0),tags.get(2,0))]:
    for p in range(a,a+n,24):
        off,inf,add=struct.unpack_from('<QQq',d,p)
        if (inf&0xffffffff)==0x403:struct.pack_into('<Q',d,off,S+add);relative+=1
        elif (inf&0xffffffff) in [0x401,0x402,0x101]:
            sym=inf>>32
            no,info,other,section,value,size=struct.unpack_from('<IBBHQQ',d,tags[6]+sym*24)
            if section:
                struct.pack_into('<Q',d,off,S+value+(add if (inf&0xffffffff)==0x101 else 0));defined_symbol_relocs+=1
class E(H):
    def _allowed(self,a):return S<=a<S+len(d) or super()._allowed(a)
e=E([B+0x358b9d0]);e.executed=set();e.sdklog=Counter();e.stublog=Counter()
e.mu.mem_map(S,(len(d)+0xffff)&~0xffff);e.mu.mem_write(S,bytes(d))
def no_null(mu,access,a,size,value,user):
    if a<0x400000:raise RuntimeError(f'null read {a:#x} at {mu.reg_read(UC_ARM64_REG_PC):#x}')
e.mu.hook_add(UC_HOOK_MEM_READ,no_null)
counts=Counter();catalog=[]
for i in range(0x214):
    q=0xb1d9e3+struct.unpack_from('<I',d,0xb212f8+i*4)[0]
    name=bytes(d[q:q+128]).split(bytes([0]))[0].decode()
    catalog.append({'api':name,'index':i,'sdk_function':hex(struct.unpack_from('<Q',d,0xcd2bc0+i*8)[0]-S),'name_offset':hex(q)})
api={r['api']:S+int(r['sdk_function'],16) for r in catalog}
# No debugger/system initialization claim: its already-initialized guard is
# supplied. Current table pointer and SDK profile override selector are zero.
e.w32(S+0xd99f94,1)
for name in ['CommandBufferSetViewport','CommandBufferSetViewportSwizzles','CommandBufferSetScissor','CommandBufferSetDepthRange','CommandBufferInitialize','CommandBufferBeginRecording','QueuePresentTexture','WindowSetCrop','DeviceSetWindowOriginMode']:
    p=e.alloc(len(name)+4);e.mu.mem_write(p,('nvn'+name).encode()+b'\0')
    e.call(S+0x4e9820,[p]);assert e.mu.reg_read(UC_ARM64_REG_X0)==api[name]
    counts['bootstrap_named_fallback']+=1
assert e.r64(S+0xd9c5e8)==S+0xcbaa78

cmd=e.alloc(0xa0);device=e.alloc(0x1a30);packet=e.alloc(0x1000);control=e.alloc(0x1000)
for flag in [0,1,2,255]:
    e.mu.mem_write(device+0x1a18,bytes([flag]));e.mu.mem_write(cmd,b'\xa5'*0xa0)
    e.call(api['CommandBufferInitialize'],[cmd,device]);assert e.mu.reg_read(UC_ARM64_REG_X0)==1
    assert e.r64(cmd+0x60)==device and e.mu.mem_read(cmd+0x15,1)[0]==(flag&1)
    e.w64(cmd,packet);e.w64(cmd+8,packet+0x1000);e.w64(cmd+0x20,control);e.w64(cmd+0x28,control+0x1000)
    e.call(api['CommandBufferBeginRecording'],[cmd]);assert e.mu.mem_read(cmd+0x11,2)==b'\x01\x00'
    assert e.r64(cmd+0x20)==control+16
    assert bytes(e.mu.mem_read(control,16))==bytes(d[0xaa3b70:0xaa3b80])
    counts['command_init_begin']+=1

swz=e.alloc(32);swizzle_examples=[]
for first in [0,1,15]:
    for values in [(0,2,4,6),(1,3,5,7),(6,4,2,0),(8,9,10,11)]:
        for number in [0,1,2]:
            e.mu.mem_write(swz,struct.pack('<8I',*(values*2)));e.w64(cmd,packet);e.w64(cmd+8,packet+0x1000)
            e.call(api['CommandBufferSetViewportSwizzles'],[cmd,first,number,swz])
            packed=sum((v&7)<<(4*i) for i,v in enumerate(values));expect=[]
            for i in range(number):expect += [0x20010000 | ((0xa18+(first+i)*0x20)//4),packed]
            assert e.r64(cmd)==packet+8*number
            assert bytes(e.mu.mem_read(packet,8*number))==struct.pack('<'+'I'*len(expect),*expect)
            if first==0 and number==1:swizzle_examples.append({'inputs':values,'words':list(map(hex,expect))})
            counts['swizzle_packet']+=1

# Actual main wrapper -> actual SDK Scissor/Viewport/DepthRange writers.
rect=e.alloc(0x40);target=e.alloc(0x30);draw=e.alloc(0xc0)
e.w64(draw+0xb8,cmd);e.mu.mem_write(rect+0x1c,packf([0,1]))
e.mu.mem_write(target+8,packf([1280,720,0,0,1280,720]))
for cell,name in [(0x57d6090,'CommandBufferSetScissor'),(0x57d6078,'CommandBufferSetViewport'),(0x57d60a0,'CommandBufferSetDepthRange')]:e.w64(B+cell,api[name])
packet_examples=[]
for origin in [0,1,2]:
    e.w32(device,origin);e.w32(device+4,0)
    for l,t,r,b in [(0,0,1280,720),(13.25,11.5,200.75,150.125)]:
        for posture in [0,1,2,3,4,5,6,0xffffffff]:
            e.mu.mem_write(rect+8,packf([l,t,r,b]));e.w32(rect+0x18,posture)
            e.w64(cmd,packet);e.w64(cmd+8,packet+0x1000);e.w64(cmd+0x60,device)
            e.call(B+0x358b9d0,[rect,draw,target])
            words=struct.unpack('<19I',e.mu.mem_read(packet,76));assert e.r64(cmd)==packet+76
            assert words[3]==0x20020280 and words[6]==0x20020283 and words[9]==0x20020300
            width=(b-t) if posture in [1,2] else (r-l)
            height=(r-l) if posture in [1,2] else (b-t)
            # Viewport integer rounding comes before SDK half-scale. Derive
            # integer width/height directly from encoded positive scale words.
            xscale=struct.unpack('<f',struct.pack('<I',words[4]))[0]
            yscale=struct.unpack('<f',struct.pack('<I',words[5]))[0]
            assert xscale>0 and yscale!=0
            assert (yscale<0)==(origin==1)
            if l==0:
                assert xscale==width*.5 and abs(yscale)==height*.5
            if l==0 and posture==0:packet_examples.append({'device_origin':origin,'words':list(map(hex,words))})
            counts['game_wrapper_to_original_sdk_packets']+=1
out={'counts':dict(counts),'total':sum(counts.values()),'mismatches':0,'SDK_relative_relocations_in_RAM':relative,'SDK_defined_symbol_relocations_in_RAM':defined_symbol_relocs,'scope':'original SDK bootstrap fallback with supplied debug-init guard, command initialize/begin, swizzle packets, actualmain358b9d0→SDKscissor/viewport/depth packets; no native GPU/context default swizzle/present display or live device posture','SDK_stubs':dict(e.sdklog),'non_SDK_stubs':{hex(k):v for k,v in e.stublog.items()},'supplied_SDK_state':{'D99F94':1,'D99FB0':0,'D99F60':0},'swizzle_examples':swizzle_examples,'viewport_packet_examples':packet_examples}
(ROOT/'analysis/camera_100_r10/posture/sdk_nvn_native.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
(ROOT/'analysis/camera_100_r10/posture/sdk_nvn_api_catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
