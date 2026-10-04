"""Compiled GameRumble manager, game-handle and selected voice virtual route audit.
Read original relocated image only. No runtime arithmetic pointer impossibility claim.
"""
import json, struct, sys, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from xref import load_idx, refs_to, BASE, TEXT_END
from func_lookup import load, lookup
from disasm import disasm
img=(ROOT/'extracted/exefs/main.reloc.img').read_bytes()
adrp=load_idx();starts,rows=load()
words=np.frombuffer(img[:TEXT_END&~3],dtype='<u4')
sites=np.nonzero((words&0x7c000000)==0x14000000)[0]
imm=words[sites].astype(np.int64)&0x3ffffff
imm=np.where(imm&(1<<25),imm-(1<<26),imm)
targets=BASE+sites*4+imm*4
def caller(site):
 r=lookup(starts,rows,site)
 return {'site':hex(site),'enclosing_function':hex(r[0]),'enclosing_size':r[1]}
def references(off):
 addr=BASE+off;ptr=[];at=img.find(struct.pack('<Q',addr))
 while at>=0:ptr.append(hex(BASE+at));at=img.find(struct.pack('<Q',addr),at+1)
 return {'B_BL':[caller(BASE+int(x)*4) for x in sites[targets==addr]],'all_byte_literal_pointers':ptr,
         'ADRP_ADD_LDR':[dict(caller(BASE+x),kind='memory' if k else 'address') for x,k in refs_to(off,adrp)]}
def qword(off):return struct.unpack_from('<Q',img,off)[0]
manager=[{'slot':hex(i),'function':hex(qword(0x55783c0+i))} for i in range(0,0x150,8)]
voice=[{'slot':hex(i),'function':hex(qword(0x5759658+i))} for i in range(0,0x88,8)]
audited=[0x130f0b8,0x1010f14,0x130fe58,0x3c7cdf4,0x3c7ad3c,0x3c7ced0]
allrefs={hex(BASE+x):references(x) for x in audited}
assert [len(allrefs[hex(BASE+x)]['B_BL']) for x in audited[:5]]==[3,3,1,1,1]
assert all(not allrefs[hex(BASE+x)]['all_byte_literal_pointers'] and not allrefs[hex(BASE+x)]['ADRP_ADD_LDR'] for x in audited[:5])
assert not {BASE+x for x in audited[:5]} & {int(x['function'],16) for x in manager+voice}
assert qword(0x57a9810)==BASE+0x5759648
assert qword(0x57954c0)==BASE+0x582a710 and qword(0x57954b8)==BASE+0x59a3790
selected_slots={'0x10':'existing-player mute flags only,3C7DC8C',
 '0x18':'speed write voice70, existing SDKplayerD0 speed if positive,3C7DCE8',
 '0x28':'existing voice state<=2 delay/arm; state1 or2,3C7B7E4',
 '0x30':'existing SDKplayerD0 loop flag,3C7DD04',
 '0x38':'existing SDKplayerD0 IsLoop,3C7DD28; not validity or IsPlaying',
 '0x60':'existing SDKplayerD0 speed reset1,3C7DD94',
 '0x68':'alloc/load SDKplayerD0 from params18 bytes/20 length,3C7DDA8',
 '0x70':'existing SDKplayerD0 SetCurrentPosition/SetPlaySpeed/Play,3C7DE9C',
 '0x78':'existing SDKplayerD0 stop,3C7DEE4'}
blocks={}
for label,lo,hi in [('game_handles_init',0x130e6b4,0x130e73c),('kind0_params',0x130ff34,0x130ff84),
 ('voice_ctor_pool0',0x3c7c4bc,0x3c7c5e8),('voice_arm',0x3c7b7e4,0x3c7b840),
 ('voice_load',0x3c7dda8,0x3c7de9c),('voice_sdk_play',0x3c7de9c,0x3c7dee4)]:
 blocks[label]=[{'address':hex(BASE+p),'instruction':s,'annotation':n} for p,s,n in disasm(img,lo,end=hi)]
out={'date':'2026-10-03','image':'extracted/exefs/main.reloc.img','image_sha256':hashlib.sha256(img).hexdigest(),
 'manager':{'singleton':hex(BASE+0x582a710),'constructor':hex(BASE+0x130e3d8),'live_vtable':hex(BASE+0x55783c0),
            'name':'GameRumble','slots':manager,'global_GOT_references':references(0x57954c0)},
 'game_handles':{'initializer':hex(BASE+0x130e5f4),'count':32,'size':0x68,
                 'first_two_qwords':'intrusive list links, initially0; no vtable',
                 'voice_pointer_offset':'0x40','generation_offset':'0x48'},
 'backend':{'singleton':hex(BASE+0x59a3790),'constructor':hex(BASE+0x3c7bd8c),
            'global_GOT_references':references(0x57954b8),'game_start_kind':0,
            'pool_offset':'0x18','pool0_constructor_vtable_GOT':hex(BASE+0x57a9810),
            'pool0_vtable':hex(BASE+0x5759658),'slots':voice,'slot_contracts':selected_slots},
 'start_references':allrefs,'original_instruction_blocks':blocks,
 'scope':'Ordinary ID40 shooter named ELink admission and compiled GameRumble/handle/voice call contract, with all known-address B/BL/pointer/materialization references.',
 'limits':['No arbitrary runtime-calculated address impossibility proof','No active original game trace or hardware output','No analysis of actual other weapons, UI behavior or specials']}
dest=ROOT/'analysis/camera_100_r10/shake/vtable_audit.json'
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manager_slots':len(manager),'voice_slots':len(voice),'game_handles':32,
 'named_start_to_backend_single_callers':{k:[r['site'] for r in v['B_BL']] for k,v in allrefs.items()},
 'manager_global_readers':len(out['manager']['global_GOT_references']['ADRP_ADD_LDR']),
 'backend_global_readers':len(out['backend']['global_GOT_references']['ADRP_ADD_LDR']),
 'result':'PASS assertions','scope':out['scope']},ensure_ascii=False))
