"""New r8 original calc coverage: all low flag combinations, intervals and gates.
Reuses r6 structure/ref code without running or overwriting r6 output.
"""
import sys,json,itertools
from pathlib import Path
src=Path('web/tools/r6_range_xlink_emu.py').read_text(encoding='utf-8').split('\nDMG =')[0]
ns={'__name__':'r8_prefix','__file__':str(Path('web/tools/r6_range_xlink_emu.py').resolve())};exec(compile(src,'r6_prefix','exec'),ns)
h=ns['H']();ns['shared']=h
# Reuse the loaded original image. Every object is reset by alloc, no old r6 test is rerun.
start=src.index('def run(sc):');end=src.index('\ndef ref(sc):');run_src=src[start:end].replace('h = H()','h = shared\n    h.nxt = HEAP\n    h.emits = []')
exec(compile(run_src,'r8_calc_run','exec'),ns)
run,ref=ns['run'],ns['ref'];cases=0;examples=[]
for flag,bit1,live,fired,s26,resource,frames in itertools.product(range(32),[0,1],[0,1],[0,1],[0,1],[False,True],[(-1,0),(0,0),(2,3),(3,4),(5,6),(7,8),(8,9),(9,4),(9,1)]):
 prev,cur=frames;sc={'prev':prev,'cur':cur,'res_param':resource,'trig':[dict(start=3,end=8,flag=flag,bit1=bit1,live=live,fired=fired,s26=s26)]}
 actual=run(sc);want=ref(sc)
 if actual!=want:examples.append({'input':sc,'actual':actual,'expected':want})
 cases+=1
 if examples:break
result={'function':'0x7103895f64','new_all_flag_gate_interval_cases':cases,'mismatches':len(examples),'examples':examples,'scope':'all low32flags+loopasset/resource/live/fired/nameCRCstate gates with finite3..8interval; entire original calc, emit/accessor boundary stubs, backend handle28=0','stubs':['3899c68 emit records arguments','resource accessorvt10 returns syntheticQ'],'existing_r6_28cases':'reused only, not rerun/recount'}
Path('analysis/completion/r8/xlink_action_calc_emu.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));assert not examples
