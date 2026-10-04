"""Independent original Entity named-mask resolver checks, including failure writes.

The source collections are actual BYML. The raw class creator/RTTI resolver run;
the BYML-to-raw authored string adapter and memory allocator are explicit.
No claim of booting a complete actor or whole stage frame is made.
"""
import json, random
from pathlib import Path
import spl_data
import param_reflect
from r6_player_uc import PUC
from r10_camera_boom_entity_mask import cstr, native_config_masks, native_field_param, boundary

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'analysis/camera_100_r10/boom'
FIELDS=[('LayerEntity',0x70,0xfb,0x88,'LayerEntityCollection'),
        ('SubLayerEntity',0x88,0xfc,0x8c,'SubLayerEntityCollection'),
        ('EnableLayerHitMask',0x60,0x103,0xbc,'LayerHitMaskEntityCollection'),
        ('EnableSubLayerHitMask',0x68,0x104,0xc0,'SubLayerHitMaskEntityCollection'),
        ('BlockableLayerHitMask',0x50,0x105,0xc4,'LayerHitMaskEntityCollection'),
        ('BlockableSubLayerHitMask',0x58,0x106,0xc8,'SubLayerHitMaskEntityCollection')]

def main():
    u=PUC();u.wq(0x71059975c0,0);root=u.alloc(0x300);u.wq(0x710599dfa8,root)
    cfg,config=native_config_masks(u,root)
    assert len(config)==5 and all(x['error'] is None and x['match'] for x in config)
    source=spl_data.byml(spl_data.load(ROOT/'extracted/romfs/Phive/Config/PhiveConfig.byml.zs'))
    dictionaries={k:({name:i for i,name in enumerate(v)} if 'HitMask' not in k else {r['ComponentName']:r['MaskValue'] for r in v})
                  for k,v in source.items() if k in {f[4] for f in FIELDS}}
    defaults={'LayerEntity':'Ground','SubLayerEntity':'Ground', **{f[0]:'Default' for f in FIELDS[2:]}}
    cases=[]
    def run(label,names,missing_config=False,inherited=False,wrong_parent=False):
        raw,rec=native_field_param(u)
        for key,off,flag,dst,collection in FIELDS:
            u.wq(raw+off,cstr(u,names[key]));u.w8(raw+flag,1)
        if inherited or wrong_parent:
            parent=raw
            if wrong_parent:
                assert u.call(0x7103ba35d8,0) is None;parent=u.x(0)
            assert u.call(0x7103bb5c5c,0) is None;child=u.x(0)
            control=u.alloc(16);u.wq(control,parent);u.w32(control+0xc,37)
            u.wq(child+0x10,1);u.wq(child+0x18,control);u.w32(child+0x20,37);raw=child
            # Wrong-class parent is rejected, so the native child defaults apply.
            if wrong_parent:names={'LayerEntity':'NoHit','SubLayerEntity':'Unspecified',**{f[0]:'Default' for f in FIELDS[2:]}}
        D=u.alloc(0x140);u.mu.mem_write(D,b'\xef\xbe\xad\xde'*0x50)
        if missing_config:u.wq(root+0x18,0)
        error=u.call(0x7103a403f4,0,D,raw);ret=u.x(0)
        u.wq(root+0x18,cfg)
        expected={hex(f[3]):0xdeadbeef for f in FIELDS};expected_ret=1
        if missing_config:expected_ret=0
        else:
            for key,off,flag,dst,collection in FIELDS:
                if names[key] not in dictionaries[collection]:expected_ret=0;break
                expected[hex(dst)]=dictionaries[collection][names[key]]
        actual={hex(f[3]):u.r32(D+f[3]) for f in FIELDS}
        cases.append({'case':label,'input':names,'error':error,'return':ret,'expected_return':expected_ret,
                      'actual':actual,'expected':expected,'match':error is None and ret==expected_ret and actual==expected})
    for field in FIELDS:
        for name in dictionaries[field[4]]:
            names=dict(defaults);names[field[0]]=name;run(field[0]+':'+name,names)
    rng=random.Random(0x1003)
    for i in range(128):
        names={f[0]:rng.choice(list(dictionaries[f[4]])) for f in FIELDS};run('combination'+str(i),names)
    for field in FIELDS:
        names=dict(defaults);names[field[0]]='__missing_r10_name__';run('missing:'+field[0],names)
    run('config missing',dict(defaults),missing_config=True)
    run('inherited actual Entity parent',dict(defaults),inherited=True)
    run('wrong-class Ragdoll parent',dict(defaults),wrong_parent=True)
    out={'scope':__doc__,'cases':len(cases),'u32_descriptor_fields':len(cases)*6,'mismatches':[x for x in cases if not x['match']],
         'rows':cases,'config_result':[{'name':x['name'],'match':x['match'],'count':len(x.get('rows',[]))} for x in config],**boundary(u)}
    (OUT/'entity_mask_verify.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Original class identity + instruction-derived visitor evidence for Q correction.
    assert u.call(0x7103ba35d8,0) is None;Q=u.x(0); assert u.call(0x7103ba7548) is None
    image=param_reflect.load_img();fields,end=param_reflect.parse_visitor(image,0x3ba38e0)
    correction={'date':'2026-10-03','withdrawn':'3b2ad14 compact Q -> Entity descriptor mask connection',
        'creator':'0x7103ba35d8','allocation_bytes':0x88,'actual_vtable':hex(u.rq(Q)),
        'getName':'0x7103ba7548','actual_name':u._cstr(u.x(0)).decode(),
        'visitor':'0x7103ba38e0','fields':fields,'type_f32':'0x710553d320/VT553d330',
        'consumer':'0x7103b2ad14 (Ragdoll descriptor)', 'actualEntityResolver':'0x7103a403f4',
        'source':'ragdoll_param_correction.c; original visitor literal/register/field instructions',**boundary(u)}
    (OUT/'ragdoll_correction.json').write_text(json.dumps(correction,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False))

if __name__=='__main__':main()
