"""Reuse r9 original whole PhiveConfig reader for r10 descriptor input probes.

Memory heap create/allocate/state are explicit allocator-only boundaries from
r9_physics_fillup_preset_emu.py. Config names, values, tables and preset readers
run as original instructions. This does not instantiate a stage actor/frame.
"""
import struct,hashlib
import spl_data
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_PC,UC_ARM64_REG_LR
from r10_camera_boom_entity_mask import ROOT

def native_config_full(u,root):
    raw=spl_data.load(ROOT/'extracted/romfs/Phive/Config/PhiveConfig.byml.zs');data=spl_data.byml(raw)
    src=u.alloc(len(raw));u.mu.mem_write(src,raw);cfg=u.alloc(0x8000);allocs=[]
    heap=u.alloc(0x100);vt=u.alloc(0x100);callback=u.alloc(16);state=u.alloc(16);parent=u.alloc(0x100)
    u.mu.mem_write(callback,bytes.fromhex('c0035fd6'));u.mu.mem_write(state,bytes.fromhex('c0035fd6'))
    u.wq(heap,vt);u.wq(vt+0x30,callback);u.wq(vt+0xb0,state);u.wq(parent,vt);u.wq(heap+0x38,parent)
    def allocate(mu,pc,size,context):
        if pc==0x7103513f3c:result=heap;allocs.append({'kind':'configHeapCreate','size':mu.reg_read(UC_ARM64_REG_X0)})
        elif pc==state:result=0;allocs.append({'kind':'heapStateQuery','object':hex(mu.reg_read(UC_ARM64_REG_X0))})
        else:
            n=mu.reg_read(UC_ARM64_REG_X1);al=mu.reg_read(UC_ARM64_REG_X2)
            result=u.alloc(n,max(16,abs(al if al<1<<31 else al-(1<<32))));allocs.append({'kind':'heapAllocate','size':n,'alignment':al})
        mu.reg_write(UC_ARM64_REG_X0,result);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
    for pc in (0x7103513f3c,callback,state):u.mu.hook_add(UC_HOOK_CODE,allocate,begin=pc,end=pc)
    error=u.call(0x7103b0f3d8,cfg,src,0,count=30000000);u.wq(root+0x18,cfg)
    motion=[]
    keys=['GravityScale','TimeScale','LinearDamping','MaxLinearSpeed','AngularDamping','MaxAngularSpeed']
    for i,original in enumerate(data['MotionPropertiesCollection']):
        at=u.rq(cfg+0x28)+i*32
        expected=struct.pack('<6f',*[original[k] for k in keys]);actual=bytes(u.mu.mem_read(at+8,24))
        name=u._cstr(u.rq(at)).decode()
        motion.append({'i':i,'name':name,'expected_name':original['ComponentName'],'actual':actual.hex(),'expected':expected.hex(),'match':name==original['ComponentName'] and actual==expected})
    return cfg,{'scope':__doc__,'source':'extracted/romfs/Phive/Config/PhiveConfig.byml.zs','sha256_decompressed':hashlib.sha256(raw).hexdigest(),
        'error':error,'allocator_boundary':allocs,'motionProperties':motion,'allMotionPropertiesMatch':len(motion)==u.r32(cfg+0x20) and all(x['match'] for x in motion)}
