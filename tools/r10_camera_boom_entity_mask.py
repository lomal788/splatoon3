"""Original raw RigidBodyEntityParam -> authored numeric descriptor mask probe.

Actual PhiveConfig BYML readers/string buffer writer run. Raw param allocator/defaults
run; authored FieldParent scalar/string values are supplied by a documented BYML
adapter, not a claim of executing the whole actor/resource loader. Descriptor
non-mask fields/world bootstrap are fixtures. No Q/Ragdoll descriptor is reused.
"""
import json, hashlib, struct
from pathlib import Path
import spl_data
from r6_player_uc import PUC
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_PC, UC_ARM64_REG_LR

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/boom'

def cstr(u, value):
    raw=value.encode()+b'\0'; p=u.alloc(len(raw)); u.mu.mem_write(p,raw); return p

def fixture_allocator(u):
    """Explicit allocation-only boundary for the real native string writer ABI.

    351ffe0 does not support null allocator; retain first null attempt separately.
    No type, name comparison, config/mask, geometry or TOI callback is replaced.
    """
    obj=u.alloc(16);vt=u.alloc(0x38);callback=u.alloc(16)
    u.wq(obj,vt);u.wq(vt+0x30,callback);u.mu.mem_write(callback,struct.pack('<I',0xd65f03c0))
    calls=[]
    def allocate(mu,pc,size,context):
        requested=mu.reg_read(UC_ARM64_REG_X1);result=u.alloc(requested)
        calls.append({'size':requested,'result':hex(result)})
        mu.reg_write(UC_ARM64_REG_X0,result);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
    u.mu.hook_add(UC_HOOK_CODE,allocate,begin=callback,end=callback)
    return obj,calls

def native_config_masks(u, root):
    raw=spl_data.load(ROOT/'extracted/romfs/Phive/Config/PhiveConfig.byml.zs')
    expected=spl_data.byml(raw); src=u.alloc(len(raw));u.mu.mem_write(src,raw)
    cfg=u.alloc(0x520); u.wq(root+0x18,cfg)
    allocator,calls=fixture_allocator(u)
    # Config stores its string-writer allocator separately from parser arg6.
    # This is an explicit bootstrap field, not a whole config constructor run.
    u.wq(cfg+0x150,allocator)
    log=[]
    for name, arr, names in [('LayerHitMaskEntityCollection',0x40,0x388),('SubLayerHitMaskEntityCollection',0x50,0x3a8)]:
        holder=u.alloc(8);u.wq(holder,cstr(u,name))
        error=u.call(0x7103b17e1c,cfg,cfg+arr,cfg+names,src,holder,allocator)
        rows=[]
        if error is None:
            for i in range(u.r32(cfg+names)):
                rows.append({'name':u._cstr(u.rq(u.rq(cfg+names+8)+i*8)).decode(),'mask':u.r32(u.rq(cfg+arr+8)+i*4)})
        exp=[{'name':r['ComponentName'],'mask':r['MaskValue']} for r in expected[name]]
        log.append({'name':name,'error':error,'native_return':u.x(0),'rows':rows,'expected':exp,'match':rows==exp})
        if error:return cfg,log
    for name, off in [('LayerEntityCollection',0x318),('SubLayerEntityCollection',0x328)]:
        error=u.call(0x7103b16014,cfg,cfg+off,src,cstr(u,name),allocator)
        rows=[]
        if error is None:
            rows=[u._cstr(u.rq(u.rq(cfg+off+8)+i*8)).decode() for i in range(u.r32(cfg+off))]
        log.append({'name':name,'error':error,'rows':rows,'expected':expected[name],'match':rows==expected[name]})
        if error:return cfg,log
    log.append({'name':'allocationBoundary','error':None,'match':True,'calls':calls,'scope':'explicit allocator object.vt30 ABI; original351ffe0/string copy and all config/mask comparisons run'})
    return cfg,log

def native_field_param(u):
    path=ROOT/'analysis/r5_ui/bootup/Phive/RigidBodyEntityParam/FieldParent_Main.phive__RigidBodyEntityParam.bgyml'
    raw=path.read_bytes();data=spl_data.byml(raw)
    error=u.call(0x7103bb5c5c,0);R=u.x(0)
    rec={'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'data':data,'creator_error':error,'raw_param':hex(R),'supplied':[]}
    if error is not None:return R,rec
    # Native typedvisitor3bb5d98 supplies the offsets/flags. Only authored fields
    # are overridden; the four Default mask strings remain original ctor bytes.
    for key,off,flag in [('ShapeName',0x80,0xfa),('LayerEntity',0x70,0xfb),('SubLayerEntity',0x88,0xfc),('MotionProperty',0x78,0xfe)]:
        if key in data:u.wq(R+off,cstr(u,data[key]));u.w8(R+flag,1);rec['supplied'].append({'key':key,'offset':hex(off),'flag':hex(flag),'value':data[key]})
    rec['raw_vt']=hex(u.rq(R))
    rec['native_default_mask_names']={key:u._cstr(u.rq(R+off)).decode() for key,off in [('EnableLayerHitMask',0x60),('EnableSubLayerHitMask',0x68),('BlockableLayerHitMask',0x50),('BlockableSubLayerHitMask',0x58)]}
    return R,rec

def boundary(u):
    return {'null':{str(k):v for k,v in u.null_calls.items()},'null_writes':{hex(k):v for k,v in u.null_writes.items()},'auto':u.auto_pages,'faults':u.faults,'plt':u.plt_stubbed,'libm':u.libm_used}

def main():
    u=PUC();u.wq(0x71059975c0,0);root=u.alloc(0x300);u.wq(0x710599dfa8,root)
    cfg,config=native_config_masks(u,root)
    out={'scope':__doc__,'config':config}
    if all(row['error'] is None and row['match'] for row in config) and len(config)==5:
        R,raw=native_field_param(u);D=u.alloc(0x140)
        error=u.call(0x7103a403f4,0,D,R)
        values={hex(off):u.r32(D+off) for off in (0x88,0x8c,0xbc,0xc0,0xc4,0xc8)}
        expected={'0x88':3,'0x8c':1,'0xbc':0x1fffffff,'0xc0':0x7ffffff,'0xc4':0x1fffffff,'0xc8':0x7ffffff}
        out.update(raw_param=raw,descriptor_error=error,descriptor_return=u.x(0),descriptor=values,expected=expected,match=values==expected)
    out.update(boundary(u));OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'entity_mask_probe_attempt3.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('config','raw_param')},ensure_ascii=False))

if __name__=='__main__':main()
