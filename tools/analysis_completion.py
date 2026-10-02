"""Source-anchored audit inventory for the Lby_Lobby00 solo scope. No game writes."""
from pathlib import Path
import argparse, collections, hashlib, json, re, subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/completion'
AREAS={'player':'이동','physics':'물리·충돌','weapon':'탄·무기','camera':'카메라·조준','combat':'피격·판정','range':'표적·사격장','paint':'도색','graphics':'그래픽','effect_sound':'이펙트·효과음','ui':'HUD','gimmick':'물리·충돌'}
IMPL={'이동':['physics'],'물리·충돌':['physics','assets','weapon'],'탄·무기':['weapon'],'카메라·조준':['camera'],'피격·판정':['weapon','range'],'표적·사격장':['range'],'도색':['paint','assets'],'그래픽':['render','assets'],'이펙트·효과음':['fx','assets'],'HUD':['range','weapon']}
ORDER={k:i for i,k in enumerate(['이동','카메라·조준','탄·무기','물리·충돌','피격·판정','표적·사격장','도색','그래픽','이펙트·효과음','HUD'])}
RX=re.compile(r'\[미확정\]|\[추정[^\]]*\]|미판독|미해독|미발견|미추적|미확인|미검증|미탐색|미정|못 찾|못 봄')
ADDR=re.compile(r'0x71[0-9a-fA-F]{8}')
EXCLUDE_DOCS={'paint/special_gauge.md','paint/turf_result.md','ui/ui_minimap.md','ui/ui_vs_maintv_elements.md'}

def clean(s):
 return s.strip().replace('|',' / ').replace('\n',' ').replace('`','').replace('**','')
def table_text(s):
 # Source snippets may contain relative links or a link cut at the excerpt limit.
 # Preserve the wording as plain table text; only generated source links are active.
 s=re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', clean(str(s)))
 return s.replace('[','［').replace(']','］')
def protected():
 fs=[]
 for p in ['web/games','web/scripts','web/docs/impl']:
  fs += [f for f in (ROOT/p).rglob('*') if f.is_file()]
 fs += [ROOT/'web/package.json']
 return {f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(fs) if f.exists()}
def collect():
 rows=[]; docs=ROOT/'web/docs'
 files=[]
 for d in AREAS:
  files += sorted((docs/d).glob('*.md')) if d!='gimmick' else [docs/'gimmick/collision_mesh.md']
 files+=sorted((docs/'impl').glob('*.md'))
 for f in files:
  rel=f.relative_to(docs).as_posix(); lines=f.read_text(encoding='utf-8-sig').splitlines()
  headings=[]; unknown=False; impl_diff=False; area=AREAS.get(rel.split('/')[0])
  if area is None:
   area={'assets':'그래픽','physics':'이동','camera':'카메라·조준','weapon':'탄·무기','range':'표적·사격장','paint':'도색','render':'그래픽','fx':'이펙트·효과음'}[f.stem]
  for i,line in enumerate(lines,1):
   if line.startswith('#'):
    n=len(line)-len(line.lstrip('#')); title=line[n:].strip()
    headings=[x for x in headings if x[0]<n]+[(n,title)]
    if n==2:
     unknown='미확정' in title
     impl_diff=(rel.startswith('impl/') and ('원본과 다른' in title or '미확정' in title))
    continue
   table=line.strip().startswith('|') and not re.match(r'^\|[\s:|\-]+\|$',line.strip())
   if table and any(line.strip().startswith('| '+s+' |') for s in ['항목','파일','검증','번들']): continue
   if not (RX.search(line) or ((unknown or impl_diff) and (table or line.startswith('- ')))): continue
   if not line.strip() or line.strip().startswith('```'): continue
   h=headings[-1][1] if headings else '문서 본문'
   sec=re.match(r'(\d+(?:\.\d+)*)',h); section='§'+sec.group(1) if sec else h
   historical=(('해소' in line or '정정' in line) and not re.search(r'남은|남음|여전히|미추적|미판독|미발견|writer.*미확정',line))
   outside=rel in EXCLUDE_DOCS
   # Keep mixed rows: exclude only clearly exclusive modes/content.
   if not outside and re.search(r'미니맵|나와바리 승패|승리팀|리스폰 지점 선택|pia |호스트 이전',line) and not re.search(r'이동|탄|Lby|로비|연습|카메라',line): outside=True
   raw=clean(line); cells=[clean(c) for c in line.strip().strip('|').split('|')] if table else []
   item=cells[0] if cells else raw
   if len(item)>240: item=item[:237]+'…'
   context=' '.join(lines[max(0,i-3):min(len(lines),i+2)])
   addrs=list(dict.fromkeys(ADDR.findall(line)))
   if not addrs: addrs=list(dict.fromkeys(ADDR.findall(context)))
   nextwhere='; '.join(addrs) if addrs else '주소 미탐색 — '+section+'의 필요 근거/호출자 추적'
   if cells and len(cells)>1: nextwhere += ' — '+clean(cells[-1])[:250]
   level='[미확정]' if ('미확정' in line or RX.search(line) and not '추정' in line) else '[추정]'
   if historical: level='기존 해소 표기(원문 근거 재사용)'
   implfiles=[rel] if rel.startswith('impl/') else ['impl/'+x+'.md' for x in IMPL[area]]
   status='범위 밖' if outside else ('기존 해소 표기' if historical else '대기')
   rows.append(dict(id=f'{rel}:L{i}',area=area,item=item,level=level,source=rel,line=i,section=section,next=nextwhere,impl=implfiles,web=raw[:260] if rel.startswith('impl/') else '확정 후 해당 구현 기록의 근사/미확정을 대조',priority=('P0' if area in ['이동','카메라·조준','탄·무기','물리·충돌','피격·판정','그래픽','HUD'] else 'P1'),status=status,raw=line))
 # Required visible HUD paths are missing from general battle-HUD documents.
 for item,nxt in [('사격장 잉크 게이지 값·표시·회복 정지·부족 표시','0x7102492120; 0x710342eb10; InkTank/InkGauge 문자열·로비 HUD'),('사격장 조준점 위치·거리 보정·히트마커 발생/종료 조건','0x71017504f4; 0x7101763310; WpShtrHitMarker/照準 문자열')]:
  rows.append(dict(id='coverage:'+item,area='HUD',item=item,level='[미확정]',source='ui/ui_hud.md',line=1,section='§1/§11 범위 누락 점검',next=nxt,impl=['impl/weapon.md','impl/range.md','impl/fx.md'],web='게이지・조준점・히트마커의 원본 소비 경로 확보 후 반영',priority='P0',status='대기',raw=item))
 return sorted(rows,key=lambda x:(x['priority'],ORDER[x['area']],x['source'],x['line']))

def render(rows):
 active=[x for x in rows if x['status'] not in ('범위 밖','집계 제외')]
 total=len(active); counts=[]
 for area in ORDER:
  rs=[x for x in active if x['area']==area]; confirmed=sum(x['status']=='확정' for x in rs); blocked=sum(x['status']=='확정 불가' for x in rs)
  counts.append(f'| {area} | {len(rs)} | {confirmed} | {blocked} | {confirmed/len(rs)*100 if rs else 0:.2f}% |')
 s='# Lby_Lobby00 1인 연습 — 분석 완료 점검\n\n작성일: 2026-10-02; 갱신일: 2026-10-03 (Asia/Seoul). **분석 전체 100%는 아직 달성하지 않았다.**\n\n'
 s+='## 1. 범위와 집계 규칙\n\n'
 s+='플레이어가 보거나 느끼는 이동・충돌・스플래시슈터・표적・도색・카메라・그래픽・이펙트/효과음・사격장 HUD를 대상으로 한다. 네트워크, 다른 무기, 서브/스페셜 실제 동작, 랭크/연어런/스토리/메뉴는 제외한다.\n\n'
 s+='이 표의 단위는 **출처 문서의 항목/문장 1개**다. 동일 질문의 문서별 반복도 출처를 놓치지 않기 위해 각각 보존했다. 따라서 비율은 질문 기록의 처리율이며 게임 전체 파악도의 추산이 아니다. 혼합 문장은 모든 하위 미확정이 해소되어야 확정으로 바꾼다. 분모는 아래 본표의 '+str(total)+'개이며 범위 밖 부록은 제외한다. 기존 해소 표기는 재분석 금지: 기존 근거 확인 및 문서 연결이 끝나기 전에는 분자에 넣지 않는다. [재구현]/합성 테스트/[추정]은 분자에 넣지 않는다.\n\n'
 s+='[실행] 원본 Unicorn와 재구현 비트 일치, [판독] 원본 명령/원본 셰이더 식 확인, [데이터] 원본 데이터 확인만 `확정`이다. `확정 불가`는 시도・불가 사유・다음 근거가 기록된 경우에만 사용하며 **근거 확정률에는 넣지 않는다**. `대기/부분 확정/조사 중`은 미완료다. `범위 밖` 판정도 적용 조건이 불명확하면 재검토한다.\n\n'
 s+='## 2. 영역별 확정률\n\n| 영역 | 항목 수 | 확정 | 확정 불가 | 원본 근거 확정률 |\n|---|---:|---:|---:|---:|\n'+'\n'.join(counts)+'\n\n'
 s+='## 3. 우선순위 목록\n\nP0는 이동・조준・탄・판정・화면・HUD, P1은 표적 수명・도색・이펙트/효과음이다. 같은 우선순위는 표의 순서대로 확인한다. 본표에는 역사적 해소/정정 표기도 포함하여 잔여 미확정과 구분한다. 주소가 없는 곳은 발견한 것처럼 채우지 않았다. 전체 원문/안정 ID는 `analysis/completion/inventory.json`에 보존한다.\n\n'
 head='| 영역 | 항목 | 현재 수준 | 근거 문서(§) | 다음에 볼 곳(주소·함수) | 웹 반영 필요(impl 파일) | 우선순위 | 상태 |\n|---|---|---|---|---|---|---|---|\n'
 def row(x):
  src=f"[{x['source']}]({x['source']}) {x['section']} (초기 L{x['line']})"
  if x.get('evidence'): src += ' — 확인: '+re.sub(r'([A-Za-z0-9_/-]+\.md)',lambda m:f'[{m[1]}]({m[1]})' if (ROOT/'web/docs'/m[1]).exists() else m[1],table_text(x['evidence']))
  web='; '.join(f'[{p}]({p})' for p in x['impl'])+' — '+table_text(x['web'])
  return '| '+' | '.join([x['area'],table_text(x['item']),x['level'],src,table_text(x['next']),web,x['priority'],x['status']])+' |'
 s+=head+'\n'.join(row(x) for x in active)+'\n\n'
 s+='## 4. 범위 밖으로 분리한 기록\n\n스페셜 게이지 실제 동작, 나와바리 결과, 미니맵・대전 전용 UI는 이번 분석을 진행하지 않는다. 문서 제목/문장에 의한 1차 분리이며 로비 공용 소비 경로가 발견되면 본표로 옮긴다.\n\n'+head+'\n'.join(row(x) for x in rows if x['status']=='범위 밖')+'\n\n'
 s+='## 4.1 분석 질문이 아닌 범례 (분모 제외)\n\n'+head+'\n'.join(row(x) for x in rows if x['status']=='집계 제외')+'\n\n'
 s+='## 5. 수행 기록과 정정\n\n상세 명령/성공・실패・스텁・검증 한계는 [completion_run.md](completion_run.md)에 기록한다. 원본 및 웹 소스/impl는 변경하지 않는다.\n'
 (ROOT/'web/docs/analysis_completion.md').write_text(s,encoding='utf-8')
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'total_records':len(rows),'in_scope':total,'outside':sum(x['status']=='범위 밖' for x in rows),'excluded':sum(x['status']=='집계 제외' for x in rows),'areas':{a:sum(x['area']==a for x in active) for a in ORDER}},ensure_ascii=False))

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['inventory','render','verify']); a=ap.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
 if a.mode=='inventory':
  if (OUT/'inventory.json').exists(): raise SystemExit('Existing inventory preserved: use render')
  (OUT/'protected_before.json').write_text(json.dumps(protected(),indent=2),encoding='utf-8'); render(collect())
 elif a.mode=='render': render(json.loads((OUT/'inventory.json').read_text(encoding='utf-8')))
 else:
  before=json.loads((OUT/'protected_before.json').read_text()); after=protected(); changed=[p for p in before if before[p]!=after.get(p)]; added=sorted(set(after)-set(before)); print(json.dumps({'protected_files':len(before),'changed':changed,'added':added},ensure_ascii=False)); (OUT/'protected_verify.json').write_text(json.dumps({'protected_files':len(before),'changed':changed,'added':added},indent=2),encoding='utf-8'); raise SystemExit(bool(changed or added))
if __name__=='__main__': main()
