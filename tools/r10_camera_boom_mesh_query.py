"""r10 real native TAG0 mesh -> original Entity concrete body -> camera sphere query.

Default: body descriptor/world bootstrap are explicit fixtures; actual TAG0.
--authored: actual PhiveConfig named masks and original FieldParent raw defaults.
--descriptor: also whole original config/provider copy, original MotionType enum,
FieldParent Mass/Inertia/base reader and whole Entity factory finish.
--competition: sixteen selected rays with two to five distinct authored planes.
--stage-filter: additionally actual RSDB actor tags -> whole Ground enable
functor12ea8c4/setter3af43a4/queued-action flush3b07b8c. The data-to-runtime-layout
adapters, packet storage and world/body transform bootstrap remain explicit.
--actor-source: actual Banc parser/defaults/matrix and original Default helper
factory3a02800/VT55762a8/descriptor consumer12d71f8; transform is authored,
while world/query-holder layout and whole actor/frame execution remain separate.
Only mutex wrapper callbacks use the existing original RET callback. This is
not an actual whole Lby_Lobby00 frame or all stage actors.
"""
import json, struct, hashlib, argparse
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from r8_physics_native_uc import init_native, make_world
from collision_mesh import load_blobs, analyze
from r10_camera_boom_entity_mask import native_config_masks, native_field_param
from r10_camera_boom_config_full import native_config_full
from r10_camera_boom_competition import select_cases
from r10_camera_boom_actor_source import actual_ground_tag_enable
from r10_camera_boom_banc_source import native_banc_matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/camera_100_r10/boom'
ap=argparse.ArgumentParser();ap.add_argument('--authored',action='store_true');ap.add_argument('--descriptor',action='store_true');ap.add_argument('--competition',action='store_true');ap.add_argument('--stage-filter',action='store_true');ap.add_argument('--actor-source',action='store_true');args=ap.parse_args()
if args.actor_source:args.stage_filter=True
if args.stage_filter:args.competition=True
if args.competition:args.descriptor=True
if args.descriptor:args.authored=True
u,errors=init_native();W,WD,A,ee=make_world(u,mode=1);errors+=ee
R=u.alloc(0x500);E=u.alloc(0x500);WB=u.alloc(0x400);CF=u.alloc(0x500);Settings=u.alloc(0x40)
u.wq(0x710599dfa8,R);u.wq(R+0xe8,E);u.wq(R+0x18,CF);u.wq(CF+0x48,Settings);u.w32(Settings+8,0xffffffff)
authored={}
if args.authored:
 if args.descriptor:
  CF,config=native_config_full(u,R);authored['whole_config']=config
  assert config['error'] is None and config['allMotionPropertiesMatch']
 else:
  CF,config=native_config_masks(u,R);authored['config']=config
  assert len(config)==5 and all(row['error'] is None and row['match'] for row in config)
u.wq(E,0x7105748188);u.wq(E+0xb8,WB);u.wq(E+0x10,CF);u.wq(WB+0xc0,W);u.wf(E+0x21c,.01)
VT=u.alloc(0x90)
for off in (0x18,0x20,0x28,0x30):u.wq(VT+off,0x7103c49f00)
u.wq(WB,VT)
errors.append(['actualFilterProvider',u.call(0x7103b1ab5c,0)]);Provider=u.x(0)
u.wq(WB+0x28,Provider)
# Entity-world query wrapper is a distinct backend (3c4579c), not the
# provider's own 57564d8 body-pair backend. Both are original vtables.
FB=u.alloc(0x28);u.wq(FB,0x7105756560);u.wq(FB+8,0xffffffff);u.wq(FB+0x10,1);u.w8(FB+0x18,4);u.wq(FB+0x20,Provider);u.wq(WB+0x110,FB)
tables=json.loads((ROOT/'analysis/completion/r7/physics_table_emu.json').read_text(encoding='utf-8'))['tables']
if args.descriptor:
 err=u.call(0x7103b1ae90,Provider,CF);copy=[]
 for table,ao,bo in zip(tables,(0x10,0x90,0x110),(0x190,0x210,0x290)):
  for ofs,key in ((ao,'allow'),(bo,'block')):
   actual=list(struct.unpack('<29I',u.mu.mem_read(Provider+ofs,29*4)));expected=table['items']['Default'][key]
   copy.append({'table':table['name'],'key':key,'actual':actual,'expected':expected,'match':actual==expected})
 authored['native_provider_copy']={'error':err,'rows':copy,'fields':174,'match':err is None and all(x['match'] for x in copy)}
 assert authored['native_provider_copy']['match']
else:
 for table,ao,bo in zip(tables,(0x10,0x90,0x110),(0x190,0x210,0x290)):
  for ofs,key in ((ao,'allow'),(bo,'block')):u.mu.mem_write(Provider+ofs,struct.pack('<29I',*table['items']['Default'][key]))
Codec=u.alloc(0x20);u.wq(Codec,0x7105755ee8);u.wq(Codec+8,0xffffffff);u.wq(Codec+0x10,1);u.wq(WB+0xd0,Codec)
Stage=u.alloc(0x120);Points=u.alloc(0x8000);u.wq(CF+8,Stage);u.w32(Stage+0x10,256);u.wq(Stage+0x18,Points);u.w32(Stage+0x20,0x7fffffff);u.w32(Stage+0x28,0x7fffffff)
u.wq(0x710580e340,0)
name,raw=load_blobs(ROOT/'extracted/romfs/Pack/Actor/Fld_VSLobby.pack.zs')[0]
P=u.alloc(len(raw));u.mu.mem_write(P,raw);O=u.alloc(0x100)
trace=[]
def watch(mu,pc,size,ud):
 trace.append(dict(pc=hex(pc),args=[hex(mu.reg_read(UC_ARM64_REG_X0+i)) for i in range(6)]))
for pc in (0x7103af344c,0x7103af593c,0x7103af6f88,0x7103c4e8c4,0x71009c78f0,0x7103c570c4,0x7103c57d04,0x7103ad6a70,0x71009372cc,0x7100936ee8,0x7100997078,0x7103c5606c,0x71012ac5e0,0x71012acb38,0x7100a492e8,0x7100adb134,0x71009af088,0x7103a5f36c,0x7103c37498,0x7103b19308,0x7103c56d08):
 u.mu.hook_add(UC_HOOK_CODE,watch,begin=pc,end=pc)
errors.append(['actualTAG0attach',u.call(0x7103a715b4,O,P,len(raw),0,count=5000000)])
H=u.rq(O+0x70)
errors.append(['originalMeshWrapper',u.call(0x7103a70974,O,0)]);G=u.x(0)
D=u.alloc(0x140);Nm=u.alloc(32);u.mu.mem_write(Nm,b'actual_mesh_fixture\0');u.wq(D+8,Nm);u.wq(D+0x10,G)
u.mu.mem_write(D+0x18,struct.pack('<12f',1,0,0,0,0,1,0,0,0,0,1,0))
if args.actor_source:
 matrix,banc=native_banc_matrix(u);authored['banc_source']=banc
 u.mu.mem_write(D+0x18,struct.pack('<12f',*matrix))
u.w32(D+0x78,0xffffffff);u.w32(D+0x80,0);u.w32(D+0x88,3);u.w32(D+0x8c,0);u.wf(D+0x90,10000.)
for off in (0x94,0x98,0x9c):u.wf(D+off,1)
for off in (0xbc,0xc0,0xc4,0xc8):u.w32(D+off,0xffffffff)
if args.authored:
 Param,rec=native_field_param(u);authored['raw_param']=rec
 if args.descriptor:
  data=rec['data']
  # Original enum string table and original FieldParent data; not assumed IDs.
  err=u.call(0x7103a16f9c); enum=u.x(0)
  names=[u._cstr(u.rq(enum+i*8)).decode() for i in range(3)]
  assert err is None and data['MotionType'] in names
  u.w32(Param+0xbc,names.index(data['MotionType']));u.w8(Param+0xfd,1)
  u.wf(Param+0xb4,data['Mass']);u.w8(Param+0x100,1)
  for lane,axis in enumerate(('X','Y','Z')):u.wf(Param+0xa8+lane*4,data['InertiaTensorScale'][axis])
  u.w8(Param+0x102,1)
  if args.actor_source:
   err=u.call(0x7103a02800,0);RawConsumer=u.x(0)
   authored['native_helper']={'factory_error':err,'factory':'0x7103a02800','VT':hex(u.rq(RawConsumer)),
       'descriptor_slot20':hex(u.rq(u.rq(RawConsumer)+0x20)),'shape_predicate_slotA0':hex(u.rq(u.rq(RawConsumer)+0xa0)),
       'scope':'Actual original Default factory, game helper and whole descriptor consumer. Actor+8 binding remains null here; source-chain actor binding is separately read.'}
   assert err is None and u.rq(RawConsumer)==0x71055762a8
   err=u.call(0x71012d71f8,RawConsumer,D,Param)
  else:
   RawConsumer=u.alloc(16);u.wq(RawConsumer,0x71057444d0)
   err=u.call(0x7103a3f2dc,RawConsumer,D,Param)
  authored['base_descriptor']={'error':err,'return':u.x(0),'enum_names':names,'raw_MotionType_index':names.index(data['MotionType']),
   'consumer':'original Default factory VT55762a8/12d71f8' if args.actor_source else 'original stack consumer VT57444d0/+8=0 from3aeca74','D80':u.r32(D+0x80),'D84':u.r32(D+0x84),'D90':u.rf(D+0x90),
   'D94_98_9c':[u.rf(D+o) for o in (0x94,0x98,0x9c)],'Da4':u.rf(D+0xa4),'D7c':u.r8(D+0x7c),'Db8':u.r8(D+0xb8)}
  assert err is None and u.x(0)==1
 if not args.actor_source:err=u.call(0x7103a403f4,0,D,Param)
 authored.update(descriptor_error=err,descriptor_return=u.x(0),descriptor={hex(off):u.r32(D+off) for off in (0x88,0x8c,0xbc,0xc0,0xc4,0xc8)})
 assert err is None and u.x(0)==1
errors.append(['originalEntityConcreteFactory',u.call(0x7103af30fc if args.descriptor else 0x7103af344c,D,0,count=10000000)]);B=u.x(0)
scope=__doc__
if args.authored:scope='Actual PhiveConfig mask/name readers and FieldParent Ground/Ground/native Default strings->3a403f4->original Entity/native userdata->actual TAG0 mesh query. Eight horizontal interior probes; non-mask descriptor fields, body transform/world query bootstrap and BYML-to-raw adapter remain explicit fixtures; no whole actor loader/frame execution.'
if args.descriptor:scope='Actual whole PhiveConfig reader+native provider copy; actual FieldParent MotionType/Mass/Inertia/raw named masks->original3a3f2dc/3a403f4->full3af30fc body factory/native userdata->actualTAG0 terrain broadquery. BYML-to-raw adapter, body transform/world query bootstrap remain explicit fixtures; whole actor loader/frame is not executed.'
if args.competition:scope+=' Multiple distinct camera-enabled authored horizontal planes compete on16 selected vertical rays; independent closest-plane verifier preserves original f32 contact reconstruction, not plane snapping.'
if args.stage_filter:scope+=' Actual Fld_VSLobby RSDB row833 and original tag-name/membership/functor/setter/whole queued-action flush supply ShapeTag enable bit28; runtime holder layouts and preallocated packet remain adapters.'
if args.actor_source:
 scope=scope.replace('body transform/world query bootstrap remain explicit fixtures','world/query-holder bootstrap remain explicit fixtures')
 scope+=' Actual Banc Fld_VSLobby row35 with omitted T/R/S consumes original caller defaults, whole entry parser and original create-info matrix producer/SDK sinf+cosf. Its identity Mtx34 is supplied into D via an explicit create-info-to-body adapter. Actual Default helper3a02800/VT55762a8 and whole12d71f8 consume the authored Entity parameters; Actor+8 binding is null in this probe. Resource references, component/bodyset/helper identity and general frame order are separately read. Actual slot68 lifecycle dispatcher and authored-pose-to-body initial writer remain unresolved; no whole actor/frame execution is claimed.'
out=dict(scope=scope,authored_mask_enabled=args.authored,authored=authored,source=name,sha256=hashlib.sha256(raw).hexdigest(),world=hex(W),owner=hex(O),native_shape=hex(H),shape=hex(G),body=hex(B),errors=errors,trace=trace)
if B:
 backend=u.rq(B+0x90);handle=u.rq(backend+8);NB=u.rq(W+0x38)+(handle&0xffffff)*0xc0;LP=u.rq(B+0x180)
 if args.stage_filter:
  out['native_stage_filter']=actual_ground_tag_enable(u,B,LP)
 out.update(body_vt=hex(u.rq(B)),native_handle=hex(handle),native_userdata=hex(u.rq(NB+0x98)),filter_getter=hex(u.rq(u.rq(B)+0x90)),lp_bytes=bytes(u.mu.mem_read(LP,0x40)).hex(),native_body_bytes=bytes(u.mu.mem_read(NB,0xc0)).hex())
 out['getter_error']=u.call(u.rq(u.rq(B)+0x90),B);out['getter_return']=hex(u.x(0))
 hp=u.alloc(8);u.wq(hp,handle);errors.append(['addActualNativeMesh',u.call(0x71009c6a70,W,hp,1,0,0)])
 errors.append(['originalCameraFactory',u.call(0x71024d5c6c,0,count=2000000)]);C=u.x(0);out['camera']=hex(C)
 u.mu.reg_write(UC_ARM64_REG_X19,C);u.mu.reg_write(UC_ARM64_REG_X8,0x3f80000000000000);u.mu.reg_write(UC_ARM64_REG_W25,0x3f800000)
 u.mu.emu_start(0x71024d6d94,0x71024d6dc8,count=40)
 _,mesh,ph=analyze(raw);tri=mesh['pos'][mesh['tri']];ns=np.cross(tri[:,1].astype(float)-tri[:,0],tri[:,2].astype(float)-tri[:,0]);ar=np.linalg.norm(ns,axis=1)
 centers=tri.mean(axis=1)
 # Select a large horizontal authored face well inside the loaded terrain.
 choices=[i for i in range(len(tri)) if ar[i]>10 and abs(ns[i,1])/ar[i]>.9999 and ph['filters'][int(mesh['tag'][i])]&128]
 choices.sort(key=lambda i:-ar[i]);cases=[]
 specs=select_cases(mesh,ph) if args.competition else [dict(triangle=i,center=centers[i].tolist(),start=(centers[i]+np.array([0,3,0],np.float32)).tolist(),end=(centers[i]-np.array([0,3,0],np.float32)).tolist()) for i in choices[:8]]
 for spec in specs:
  p0=np.array(spec['start'],np.float32);p1=np.array(spec['end'],np.float32);Q=C+0x1d0
  u.mu.mem_write(Q+0x10,struct.pack('<3f',*p0));u.mu.mem_write(Q+0x1c,struct.pack('<3f',*p1));u.w32(Q+0xf8,u.r32(Q+0xf8)|0xc)
  err=u.call(0x7103a5f36c,Q,count=10000000);ret=u.x(0)
  row=dict(**spec,error=err,hit=ret,result_bytes=bytes(u.mu.mem_read(Q+0x40,0x20)).hex(),fraction=u.rf(Q+0x50),distance=u.rf(Q+0x54),query_bytes=bytes(u.mu.mem_read(Q,0x150)).hex())
  if 'triangle' in spec:
   i=spec['triangle'];row.update(key=int(mesh['key'][i]),tag=int(mesh['tag'][i]))
  if ret==1:
   L=u.rq(C+0x318);It=u.alloc(0x48);u.mu.reg_write(UC_ARM64_REG_X8,It);row['iterator_error']=u.call(0x71012d8dcc,L);First=u.rq(It+8);pt=u.rq(First);row.update(iterator_bytes=bytes(u.mu.mem_read(It,0x48)).hex(),point_bytes=bytes(u.mu.mem_read(pt,0x80)).hex(),normal=list(struct.unpack('<3f',u.mu.mem_read(pt+0xc,12))),point_entry_flags=hex(u.rq(First+8)))
  cases.append(row)
  if err:break
 out['cases']=cases
out.update(null_calls={str(k):v for k,v in u.null_calls.items()},null_writes={hex(k):v for k,v in u.null_writes.items()},auto_pages=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,os=u.os_calls)
OUT.mkdir(parents=True,exist_ok=True);(OUT/('mesh_query_actor_source.json' if args.actor_source else 'mesh_query_stage_filter.json' if args.stage_filter else 'mesh_query_competition.json' if args.competition else 'mesh_query_descriptor.json' if args.descriptor else 'mesh_query_authored.json' if args.authored else 'mesh_query_attempt2.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out.get(k) for k in ('body','body_vt','native_userdata','getter_return','errors','null_calls','auto_pages','faults')}|{'cases':len(out.get('cases',[])),'hits':sum(x['hit']==1 for x in out.get('cases',[]))},ensure_ascii=False))
