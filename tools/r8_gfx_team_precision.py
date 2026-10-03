"""r8 Original team-color arithmetic instructions: exhaustive fused opcode inventory."""
from pathlib import Path
import json,sys,capstone
import xref,func_lookup
R=Path(__file__).resolve().parents[2];m=xref.load_img();starts,rows=func_lookup.load();cs=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);out=[]
for s in ['11743a0','1174534','1188334','1174afc','1176830']:
 a=int(s,16);r=func_lookup.lookup(starts,rows,a+xref.BASE);ins=list(cs.disasm(m[a:a+r[1]],a+xref.BASE));f=[hex(i.address)+' '+i.mnemonic+' '+i.op_str for i in ins if i.mnemonic.startswith(('fmadd','fmsub','fnmadd','fnmsub','fmla','fmls'))];out.append({'address':s,'size':r[1],'instructions':len(ins),'fused':f,'calls':[hex(i.address)+' '+i.op_str for i in ins if i.mnemonic=='bl']})
(R/'analysis/completion/r8/graphics_team_precision.json').write_text(json.dumps({'original':'extracted/exefs/main.reloc.img','functions':out,'limits':'callee libm approximation not covered; separate f32 arithmetic confirmed only within these five functions'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('original instructions',sum(x['instructions'] for x in out),'fused',sum(len(x['fused']) for x in out))
