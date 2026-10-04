"""Independent axis-plane expected bits for the real-mesh native query probe.
--authored validates source raw Entity masks and actual PhiveConfig collections.
--descriptor validates the original non-mask source reader/config/full factory;
--competition sixteen closest-plane competitions and original f32 contact order;
--stage-filter actual RSDB tags -> original whole activation functor and flush.
Data-to-layout adapters, transform/world bootstrap remain explicit fixtures.
These probes do not execute a complete actor-resource loader or stage frame.
"""
import json,struct,argparse
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'analysis/camera_100_r10/boom'
ap=argparse.ArgumentParser();ap.add_argument('--authored',action='store_true');ap.add_argument('--descriptor',action='store_true');ap.add_argument('--competition',action='store_true');ap.add_argument('--stage-filter',action='store_true');ap.add_argument('--actor-source',action='store_true');args=ap.parse_args()
if args.actor_source:args.stage_filter=True
if args.stage_filter:args.competition=True
filename='mesh_query_actor_source.json' if args.actor_source else 'mesh_query_stage_filter.json' if args.stage_filter else 'mesh_query_competition.json' if args.competition else 'mesh_query_descriptor.json' if args.descriptor else 'mesh_query_authored.json' if args.authored else 'mesh_query_attempt2.json'
source=json.loads((D/filename).read_text(encoding='utf-8'));bad=[];rows=[]
f=np.float32;fields=0
for row in source['cases']:
 planeY=row['plane_y'] if args.competition else row['center'][1]
 h=f(abs(f(f(row['start'][1])-f(planeY))));length=f(abs(f(f(row['end'][1])-f(row['start'][1]))))
 distance=f(h-f(.3));fraction=f(distance/length)
 expected=struct.pack('<5f',fraction,distance,0.,1.,0.)
 actual=struct.pack('<5f',row['fraction'],row['distance'],*row['normal'])
 ok=actual==expected and row['hit']==1 and row['error'] is None and row['iterator_error'] is None
 fields+=5
 if args.competition:
  # Reuse original094ae10 source operation order (sphere_quad_toi §6):
  # contact = f32(f32(start+f32(delta*t))-f32(radius*normal)).
  # Snapping contact.Y to authored planeY was a failed 1-ULP assumption.
  point=[f(f(f(a)+f(f(f(b)-f(a))*fraction))-f(f(.3)*f(n))) for a,b,n in zip(row['start'],row['end'],(0.,1.,0.))]
  expected+=struct.pack('<3f',*point);actual+=bytes.fromhex(row['point_bytes'])[:12]
  ok=ok and actual==expected and len(row['distinct_y'])>=2;fields+=3
 rr=dict(triangle=row.get('triangle'),expected=expected.hex(),actual=actual.hex(),pass_=ok,entry_flags=row['point_entry_flags']);rows.append(rr)
 if not ok:bad.append(rr)
out=dict(source=filename,scope=source['scope'],verificationScope='Independent selected horizontal-plane expected f32 bits; contact uses original094ae10 operation order. This is not general arbitrary-mesh geometry verification.',cases=len(rows),f32_fields=fields,mismatch_count=len(bad),mismatches=bad,rows=rows,body_userdata_matches=source['body']==source['native_userdata'],native_filter_getter=source['filter_getter'],native_vt=source['body_vt'],null=source['null_calls'],auto=source['auto_pages'],faults=source['faults'])
(D/('mesh_query_actor_source_verify.json' if args.actor_source else 'mesh_query_stage_filter_verify.json' if args.stage_filter else 'mesh_query_competition_verify.json' if args.competition else 'mesh_query_descriptor_verify.json' if args.descriptor else 'mesh_query_authored_verify.json' if args.authored else 'mesh_query_verify.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ('cases','f32_fields','mismatch_count','body_userdata_matches','native_filter_getter','native_vt','null','auto','faults')},ensure_ascii=False))
