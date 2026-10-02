"""Original instruction checks for solo bullet permit branches and camera factory.
Writes only analysis/completion/camera_weapon_original.json. Whole runtime is not emulated.
"""
import json, struct, sys, random
import numpy as np
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, END
ROOT=Path(__file__).resolve().parents[2]

def w64(e,a,v): e.mu.mem_write(a,struct.pack('<Q',v))
def r64(e,a): return struct.unpack('<Q',e.mu.mem_read(a,8))[0]
def permit():
    e=UC(); a=e.alloc(0x200); b=e.alloc(0x400); info=e.alloc(0xb0)
    w64(e,0x71058e0460,a); w64(e,0x710580e5e8,b); w64(e,0x710580e340,0)
    e.u32(a+0xc8,0); e.u32(b+0x2c0,0)
    rows=[]
    for local,speed,manager_null in [(1,0,True),(1,2.2,True),(1,-1,True),(0,-1,True),(0,0,True),(0,2.2,True),(1,0,False),(1,2.2,False),(0,-1,False)]:
        w64(e,0x710580e340,0 if manager_null else b)
        e.mu.mem_write(info+0x6d,bytes([local])); e.f32(info+0x48,speed)
        got=e.call(0x71016e3af4,0,0,info)
        assert e.mu.reg_read(UC_ARM64_REG_PC)==END
        expected=1
        assert got==expected,(local,speed,got)
        rows.append({'local':local,'speed':speed,'manager_null':manager_null,'original':got,'expected':expected})
    return rows

def camera(config=None):
    e=UC(); camera=e.alloc(0x1978); qmeta=e.alloc(0x300); shape=e.alloc(0x100)
    captured=[]; calls=[]
    w64(e,0x71059975c0,0); w64(e,0x710599dfa8,0)
    if config is not None:
        g=e.alloc(0x100); cfg=e.alloc(0x300); w64(e,0x710599dfa8,g); w64(e,g+0xe8,cfg); e.f32(cfg+0x21c,config)
    w64(e,r64(e,0x7105791bd0),0) # constant setup special global condition off
    def hook(mu,addr,size,ud):
        x0=mu.reg_read(UC_ARM64_REG_X0)
        if addr==0x710083d2f0:
            val=camera; calls.append({"function":hex(addr),"stub":"malloc","return":hex(val)})
        elif addr==0x7103a62e78:
            val=qmeta; calls.append({'function':hex(addr),'stub':'query allocator','return':hex(val)})
        elif addr==0x7103a72e1c:
            raw=bytes(mu.mem_read(x0,0x30)); captured.append(raw)
            val=shape; calls.append({'function':hex(addr),'stub':'shape/query wrapper allocation','return':hex(val)})
        elif 0x7103e99000<=addr<0x7103e9e000:
            val=camera if x0==0x1978 else 0
            calls.append({'function':hex(addr),'stub':'malloc or TLS','x0':hex(x0),'return':hex(val)})
        else: return
        mu.reg_write(UC_ARM64_REG_X0,val); mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
    e.mu.hook_add(UC_HOOK_CODE,hook)
    got=e.call(0x71024d5c6c,0)
    assert got==camera and e.mu.reg_read(UC_ARM64_REG_PC)==END
    assert r64(e,camera+0x68)==camera+0x3c
    assert len(captured)==1
    radius=struct.unpack_from('<I',captured[0],0x2c)[0]
    expected=struct.unpack("<I",struct.pack("<f",0.3 if config is None or config<=0.3 else config))[0]
    assert radius==expected,(config,hex(radius),hex(expected))
    return {'config_plus21c':config,'camera_plus68':'self+0x3c','shape_descriptor_hex':captured[0].hex(),'radius_bits':f'{radius:08x}','radius':struct.unpack('<f',struct.pack('<I',radius))[0],'stubs':calls,'scope':'Original factory body and constant init, not shape solver or allocation routines.'}

def basis():
    e=UC(); obj=e.alloc(0x1978); w64(e,obj+0x60,obj+0x30); w64(e,obj+0x68,obj+0x3c)
    F=np.float32
    def cross(a,b): return [F(F(a[1]*b[2])-F(a[2]*b[1])),F(F(a[2]*b[0])-F(a[0]*b[2])),F(F(a[0]*b[1])-F(a[1]*b[0]))]
    def normal(v):
        length=F(np.sqrt(F(F(F(v[0]*v[0])+F(v[1]*v[1]))+F(v[2]*v[2]))))
        return [F(x*F(F(1)/length)) for x in v] if length>0 else v
    rnd=random.Random(71024)
    cases=[([0,0,0],[0,0,1]),([0,0,0],[0,1,0]),([0,0,0],[0,-1,0]),([1,2,3],[1,2,3])]
    cases += [([rnd.uniform(-20,20) for _ in range(3)],[rnd.uniform(-20,20) for _ in range(3)]) for _ in range(256)]
    previous=[F(1),F(0),F(0),F(0),F(1),F(0),F(0),F(0),F(1)]
    rows=[]
    for pos,at in cases:
        pos=list(map(F,pos));at=list(map(F,at))
        for i in range(3): e.f32(obj+0x30+i*4,pos[i]); e.f32(obj+0x70+i*4,at[i])
        before=struct.pack('<9f',*previous); e.mu.mem_write(obj+0x3c,before)
        z=normal([F(a-b) for a,b in zip(pos,at)])
        valid=(pos!=at and abs(float(z[1]))<=struct.unpack('<f',struct.pack('<I',0x3f7ffffe))[0])
        if valid:
            x=normal(cross([F(0),F(1),F(0)],z)); y=cross(z,x); expected=x+y+z
        else: expected=previous
        e.mu.reg_write(UC_ARM64_REG_X19,obj); e.mu.reg_write(UC_ARM64_REG_S15,0x3f800000)
        e.mu.reg_write(UC_ARM64_REG_SP,0x100f0000)
        e.mu.emu_start(0x71024df4e8,0x71024df6d4,count=10000)
        got=bytes(e.mu.mem_read(obj+0x3c,36)); ref=struct.pack('<9f',*expected)
        assert e.mu.reg_read(UC_ARM64_REG_PC)==0x71024df6d4
        assert got==ref,(pos,at,got.hex(),ref.hex())
        rows.append({'pos':list(map(float,pos)),'at':list(map(float,at)),'updated':valid,'original_bits':got.hex(),'reference_bits':ref.hex(),'match':True})
        previous=expected
    return rows

def main():
    result={'permit':permit(),'basis':basis(),'camera':[camera(x) for x in (None,0.05,0.3,0.6)]}
    path=ROOT/'analysis/completion/camera_weapon_original.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS permit 9/9, basis 260/260 bit exact, camera factory 4/4 +0x68 and radius descriptor; '+str(path))
if __name__=='__main__': main()
