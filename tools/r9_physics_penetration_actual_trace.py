"""r9 generic overlap recovery whole-function trace. Original allocator/TLS environment initialized; independent EPA formula comparison not yet claimed."""
import json,struct,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import init_native
u,init=init_native();Q=u.alloc(0x80);O=u.alloc(0x40);P=u.alloc(0x40);VA=u.alloc(0x100);VB=u.alloc(0x100);records=[];counts={hex(p):0 for p in (0x7100ae7b34,0x7100ae9b14,0x7100ae7fd0,0x7100ae892c,0x7100ae926c,0x7100ae9840,0x7100ae9498,0x7100ae8e80,0x7100ae8af8)}
def hook(mu,pc,size,data):
 counts[hex(pc)]+=1
 if pc in (0x7100ae7b34,0x7100ae9b14,0x7100ae7fd0):
  a=mu.reg_read(UC_ARM64_REG_X0);sz=0xe0 if pc==0x7100ae7b34 else 0x100
  records.append(dict(pc=hex(pc),x=[mu.reg_read(globals()[f'UC_ARM64_REG_X{i}']) for i in range(8)],descriptor=bytes(mu.mem_read(a,sz)).hex()))
for pc in counts:u.mu.hook_add(UC_HOOK_CODE,hook,begin=int(pc,16),end=int(pc,16))

exec(Path('web/tools/r9_physics_penetration_plane_emu.py').read_text(encoding='utf-8-sig').split('u=PhysicsUC();D=')[0],globals());plane_ref=ref
exec(Path('web/tools/r9_physics_penetration_barycentric_emu.py').read_text(encoding='utf-8-sig').split('u=PhysicsUC();D=')[0],globals());bary_ref=ref
pending=[];callback_records=[];callback_bad=[];dynamic_lr=set()
def math_capture(mu,pc,size,data):
 if pc in (0x7100ae926c,0x7100ae9590):
  D=mu.reg_read(UC_ARM64_REG_X0);j=mu.reg_read(UC_ARM64_REG_X1);ids=[bytes(mu.mem_read(D+0xd60+j*16+k*4+2,1))[0] for k in range(3)];vv=[list(map(f,struct.unpack('<4f',bytes(mu.mem_read(D+0x8d0+k*16,16))))) for k in ids];lr=mu.reg_read(UC_ARM64_REG_X30)
  if pc==0x7100ae926c:
   origin=list(map(f,struct.unpack('<4f',bytes(mu.mem_read(D+0x90,16)))));bias=list(map(f,struct.unpack('<4f',bytes(mu.mem_read(D+0xa0,16)))));err=f(u.rf(D+0xb0));hi,lo,inv,margin,distance,nn=plane_ref(*vv,origin,bias,err);want=struct.pack('<8d3f4fB',*(hi+lo),float(inv),float(margin),float(distance),*map(float,nn),1);loc=[(D+0x2be0+j*32,32),(D+0x3be0+j*32,32),(D+0x2560+j*4,4),(D+0x2960+j*4,4),(D+0x2760+j*4,4),(D+0x1d60+j*16,16),(D+0x2b60+j,1)];kind='plane';fields=16
  else:
   P=mu.reg_read(UC_ARM64_REG_X2);O=mu.reg_read(UC_ARM64_REG_X3);S=mu.reg_read(UC_ARM64_REG_X4);point=list(map(f,struct.unpack('<4f',bytes(mu.mem_read(P,16)))));weights,signed,mask,chosen=bary_ref(*vv,point);want=p4(weights)+p4(signed);loc=[(O,16),(S,16)];kind='barycentric';fields=8
  pending.append((lr,want,loc,dict(kind=kind,lr=hex(lr),j=j,vertices=ids,fields=fields)))
  if lr not in dynamic_lr:dynamic_lr.add(lr);u.mu.hook_add(UC_HOOK_CODE,math_capture,begin=lr,end=lr)
 elif pending and pending[-1][0]==pc:
  lr,want,loc,rec=pending.pop();actual=b''.join(bytes(mu.mem_read(ptr,n)) for ptr,n in loc);rec.update(actual=actual.hex(),reference=want.hex(),pass_bits=actual==want);callback_records.append(rec)
  if actual!=want:callback_bad.append(rec)
for pc in (0x7100ae926c,0x7100ae9590):u.mu.hook_add(UC_HOOK_CODE,math_capture,begin=pc,end=pc)

cube=list(itertools.product((-1.,1.),repeat=3));point=[(0.,0.,0.)];tri=[(-1.,0.,-1.),(1.,0.,-1.),(0.,0.,1.)];res=[]
for name,av,bv,org,delt in [('cube-cube',cube,cube,(.5,.3,.1),(1.,0.,0.)),('cube-point',cube,point,(.5,.3,.1),(1.,0.,0.)),('point-point',point,point,(0.,0.,0.),(1.,0.,0.)),('tri-point',tri,point,(0.,0.,0.),(0.,1.,0.)),('cube-touch',cube,cube,(2.,0.,0.),(-1.,0.,0.))]:
 for pp,vv in ((VA,av),(VB,bv)):u.mu.mem_write(pp,struct.pack('<'+'f'*len(vv)*3,*sum((list(v) for v in vv),[])))
 u.mu.mem_write(Q,struct.pack('<4f',*delt,0.))
 for j,v in enumerate(((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(*org,0.))):u.mu.mem_write(Q+0x10+j*16,struct.pack('<4f',*v))
 u.mu.mem_write(Q+0x50,struct.pack('<6f',.001,.001,0.,0.,.5,.5));u.w32(Q+0x68,256);u.w32(Q+0x6c,0)
 for initial in (False,True):
  u.mu.mem_write(O,bytes(64));u.wf(O,1.);u.mu.mem_write(P,bytes(64));records.clear();before=dict(counts);e=u.call(0x7100aec920,VA,len(av),VB,len(bv),Q,O,P if initial else 0,0,count=10000000)
  r=dict(name=name,initial=initial,error=e,ret=u.x(0),out=bytes(u.mu.mem_read(O,64)).hex(),init=bytes(u.mu.mem_read(P,64)).hex(),calls={k:v-before[k] for k,v in counts.items()},records=records.copy());res.append(r);print({k:v for k,v in r.items() if k not in ('records','out','init')})
r=dict(scope="whole original generic recovery actualplane/barycentric producer trace",callback_count=len(callback_records),callback_fields=sum(x["fields"] for x in callback_records),callback_bad_count=len(callback_bad),callback_records=callback_records,callback_bad=callback_bad,init_errors=init,results=res,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed)
Path('analysis/completion/r9/physics_penetration_actual_trace.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('runtime',u.null_calls,u.auto_pages,u.faults)


print("callbacks",len(callback_records),sum(x["fields"] for x in callback_records),len(callback_bad));print("firstcb",callback_bad[:1])
