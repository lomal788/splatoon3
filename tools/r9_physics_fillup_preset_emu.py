"""Whole original PhiveConfig loader with raw original BYML; probes FillUpPlayer mask registration, not scene instantiation."""
import struct,json,hashlib
from pathlib import Path
from r8_physics_native_uc import PhysicsUC
from spl_data import unzs,byml
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
u=PhysicsUC();u.wq(0x71059975c0,0);raw=unzs(Path('extracted/romfs/Phive/Config/PhiveConfig.byml.zs').read_bytes());data=byml(raw);P=u.alloc(len(raw));u.mu.mem_write(P,raw);CF=u.alloc(0x8000);trace=[];allocs=[];Heap=u.alloc(0x100);HeapVT=u.alloc(0x100);Alloc=u.alloc(16);u.mu.mem_write(Alloc,bytes.fromhex("c0035fd6"));u.wq(Heap,HeapVT);u.wq(HeapVT+0x30,Alloc);HeapState=u.alloc(16);u.mu.mem_write(HeapState,bytes.fromhex("c0035fd6"));u.wq(HeapVT+0xb0,HeapState);Parent=u.alloc(0x100);u.wq(Parent,HeapVT);u.wq(Heap+0x38,Parent)
def boundary(mu,a,size,arg):
 if a==0x7103513f3c:ret=Heap;allocs.append(dict(kind="configHeapCreate",size=mu.reg_read(UC_ARM64_REG_X0)))
 elif a==HeapState:ret=0;allocs.append(dict(kind="heapStateQuery",object=hex(mu.reg_read(UC_ARM64_REG_X0))))
 else:
  n=mu.reg_read(UC_ARM64_REG_X1);al=mu.reg_read(UC_ARM64_REG_X2);ret=u.alloc(n,max(16,abs(al if al<1<<31 else al-(1<<32))));allocs.append(dict(kind="heapAllocate",size=n,alignment=al))
 mu.reg_write(UC_ARM64_REG_X0,ret);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
u.mu.hook_add(UC_HOOK_CODE,boundary,begin=0x7103513f3c,end=0x7103513f3c);u.mu.hook_add(UC_HOOK_CODE,boundary,begin=Alloc,end=Alloc);u.mu.hook_add(UC_HOOK_CODE,boundary,begin=HeapState,end=HeapState)
def capture(mu,a,size,arg):
 if a==0x7103b13cb0:
  trace.append(dict(writer=hex(a),descriptor=hex(mu.reg_read(UC_ARM64_REG_X28)),registers=[hex(mu.reg_read(r)) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X20,UC_ARM64_REG_X21,UC_ARM64_REG_X22,UC_ARM64_REG_X23,UC_ARM64_REG_X24,UC_ARM64_REG_X25)],mask=hex(mu.reg_read(UC_ARM64_REG_X23))))
u.mu.hook_add(UC_HOOK_CODE,capture,begin=0x7103b13cb0,end=0x7103b13cb0);e=u.call(0x7103b0f3d8,CF,P,0,count=30000000)

tagRows=data['UserShapeTagMaskCollection'];tagNames={x['ComponentName']:x['MaskValue'] for x in tagRows};maskTables={key:{x['ComponentName']:x['MaskValue'] for x in data[key]} for key in ('LayerHitMaskEntityCollection','SubLayerHitMaskEntityCollection','LayerHitMaskSensorCollection','SubLayerHitMaskSensorCollection')};bad=[];fields=0;rows=[]
for i,row in enumerate(tagRows):
 actual=u.rq(u.rq(CF+0x88)+8*i);expected=row['MaskValue'];fields+=1
 if actual!=expected:bad.append(dict(kind='tag',i=i,actual=actual,expected=expected))
layerRows=data['LayerHitMaskEntityCollection']
for i,row in enumerate(layerRows):
 actual=u.r32(u.rq(CF+0x48)+4*i);expected=row['MaskValue'];fields+=1
 if actual!=expected:bad.append(dict(kind='entityLayer',i=i,actual=actual,expected=expected))
for i,row in enumerate(data['MaterialPresetCollection']):
 D=int(trace[i]['descriptor'],16);mask=0
 for tag in row['UserShapeTagMask']:mask|=tagNames[tag]
 actual=[u.rq(D+0x10),u.r8(D+0x18)];expected=[mask,1]
 for key,off in (('LayerHitMaskEntity',0x20),('SubLayerHitMaskEntity',0x28),('LayerHitMaskSensor',0x30),('SubLayerHitMaskSensor',0x38)):
  actual+=[u.r32(D+off),u.r8(D+off+4)];name=row[key];expected+=[maskTables[key+'Collection'].get(name,0),int(bool(name))]
 rr=dict(i=i,name=row['ComponentName'],descriptor=hex(D),actual=actual,expected=expected,raw=bytes(u.mu.mem_read(D,0x40)).hex());rows.append(rr);fields+=len(expected)
 if actual!=expected:bad.append(rr)
out=dict(scope='Whole original PhiveConfig loader+raw originalBYML;49tag/50entityLayer/108preset registration integer-field verification; scene/authorintent outside',cases=1,fields=fields,tag_rows=49,layer_rows=50,preset_rows=108,bad_count=len(bad),bad=bad,fillup=rows[61],rows=rows,error=e,config_sha256=hashlib.sha256(raw).hexdigest(),allocator_boundary=allocs,runtime=dict(null={str(k):v for k,v in u.null_calls.items()},nullwrite={str(k):v for k,v in u.null_writes.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,libm=u.libm_used));Path('analysis/completion/r9/physics_fillup_preset_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ('bad','rows','allocator_boundary')},ensure_ascii=False,indent=2))
if e or bad or u.null_calls or u.auto_pages or u.faults:raise SystemExit(1)
