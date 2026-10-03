"""Read-only original camera evidence audit; no hardware/native game execution."""
from pathlib import Path
import hashlib,json,re,struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/mouse_camera/native'
OUT.mkdir(parents=True,exist_ok=True)
BASE=0x7100000000
raw=(ROOT/'extracted/exefs/main.reloc.img').read_bytes()
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
def q(a):return struct.unpack_from('<Q',raw,a-BASE)[0]
def text(a):return raw[a-BASE:raw.index(b'\0',a-BASE)].decode('utf-8')
def getname(fn):
    v=list(md.disasm(raw[fn-BASE:fn-BASE+12],fn))
    assert len(v)==3 and [x.mnemonic for x in v]==['adrp','add','ret']
    page=int(v[0].op_str.split('#')[-1],16)
    off=int(v[1].op_str.split('#')[-1],16)
    return text(page+off),hex(page+off)
rows=[]
for off,tag,vt,fn in [(0x1930,0x58c0c08,0x563ea38,0x268aa70),(0x1940,0x58c0080,0x563db40,0x2656038),(0x1948,0x58bd5d0,0x5635660,0x2530cc0),(0x1950,0x58c0608,0x563e1b0,0x2674798)]:
    assert q(BASE+vt)==BASE+fn
    nm,sp=getname(q(BASE+vt+16))
    ins=list(md.disasm(raw[fn:fn+80],BASE+fn))
    addtag=[i for i in ins if i.mnemonic=='add' and i.op_str.startswith('x8, x8,')]
    assert any(int(i.op_str.split('#')[-1],16)==(tag&0xfff) for i in addtag)
    rows.append({'camera_offset':hex(off),'tag':hex(BASE+tag),'vtable':hex(BASE+vt),'type_check':hex(BASE+fn),'name_getter':hex(q(BASE+vt+16)),'name':nm,'name_string':sp})
for label,start,end in [('auto_override',0x24e35f4,0x24e3898),('type_bind',0x23555f0,0x2355d74),('ordinary_rate',0x24e2fe8,0x24e3394)]:
    body='\n'.join(f'{i.address:#x} {i.mnemonic} {i.op_str}' for i in md.disasm(raw[start:end],BASE+start))+'\n'
    (OUT/(label+'.asm.txt')).write_text(body,encoding='utf-8')
result={'level':'[판독]+[데이터], raw ARM/data audit; no new Unicorn execution','source':'extracted/exefs/main.reloc.img','source_sha256':hashlib.sha256(raw).hexdigest(),'bindings':rows,'whole_inventory_promotions':0,'reused_original_evidence':['analysis/completion/r8/camera_jump_dokan_emu.json','analysis/completion/r9/camera_reset_module_emu.json','web/docs/camera/solo_completion.md'],'implementation_changed':False}
(OUT/'type_identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'bindings':rows,'mismatches':0,'new_native_execution':0},ensure_ascii=False))

