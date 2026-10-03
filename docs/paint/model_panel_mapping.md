# 시각 지형의 삼각형 → ColPaint 패널 → 도색 속성

## 1. 기능 개요

원본은 BFRES 시각 삼각형을 별도로 읽고 충돌에서 만들어진 ColPaint 패널에 배정한다. 가까운 충돌 삼각형을 하나 임의 선택하는 방식이 아니다. 후보 옥트리·방향·면적·깊이 우선순위와 이음매 삼각형 후처리를 거쳐 시각 정점의 `_pu0/_pu1/_pu2`를 만든다 [판독]. 패널 비교4096건과 새 삼각형 후처리384개 입력(3456정점)을 원본 실행으로 대조했다 [실행].

## 2. 원본 자료

기존 미판독 `analysis/decomp/paint4/colpaint_r0.c`, `colpaint_r1.c`, `colpaint_r2.c`; 새 `analysis/decomp/r8_graphics/paint_model_callbacks.c`, `paint_model_decode.c`, `paint_shape_transform.c`. SHARED/FUNCS/decomp_index와 실제 prologue/가상함수 표를 대조했다. r7의 writer4096건·삼각형 없는 사슬1200건은 기존 근거로 재사용하며 신규 성과로 재계상하지 않는다.

## 3. 실제 호출 경로 [판독]

2bcb6b0의 작업+86C6F0 = ColPaintMeshSetupper. 2bd00a4(TargetModelList)→BuildMeshModel 구성→2be2b8c(패널 관리자)→2bdde10(후보 공간목록)→2be5600(시각 삼각형 순회)→2be54f8(배정)→2bdec2c/2be135c/2bdfb18(후보 선택). 선택되면 triangle+10=panel, setupper vt60=2be7d28→2bee2e8가 패널 mapBox(+3C..50)를 넓힌다. 정점 인접 삼각형 목록을 채운 뒤2be50fc→2be2de4가 속성 작성과 삼각형 후처리를 수행한다.

**클래스 슬롯 정정**: setupper vt58=2bcf540는 +18의 작업모델 getter, vt60은 패널 mapBox 투영이다. BuildMeshModel(vt567C850)의 vt58=2bd06a8/60=2bd07e8은 각각 정점/삼각형 배열 할당이다. 서로 다른 클래스의 같은 슬롯을 같은 뜻으로 읽지 않는다.

## 4. BFRES 입력 [판독]

BuildMeshModel+10/+18=shape수/32B배열. shape={삼각형수0,24B배열8,정점수10,80B배열18}. triangle={정점index0/4/8,부가필드C,panel10}; vertex={world xyz0/4/8,flagC,인접삼각형수10/용량14/목록18}.

2bd108c는 BFRES `_p0` ResDict를 실제 조회해 버퍼·크기·stride·offset·format을 얻는다. 2bd1298는1188978로 xyz를 읽는다. 지원 format1805는f32 xyz,1505는half3(원본 exponent0은 부호있는0으로 처리),E02는각10bit signed/511를 -1하한으로 제한한다. 미지원 format은 원본 s0/s1/s2를 그대로 반환하므로 임의0 fallback을 넣지 않는다. 실제 명령에서 세 성분 반환을 확인했으며 디컴파일의 단일float 반환과 '이전 param_2/3' 표기는 타입추론 오류다. 세 성분 중 NaN이면 xyz모두0.

모델 byte8이 참이면11087b0로 얻은 shape 3×4를 먼저 적용하며, 이어 항상 BuildMeshModel vt78(+50)의 root3×4를 적용한다. multiply 세 개→add 두 개→translation add 순서, FMA로 합치지 않는다. 11087b0는 shape byte5A!=0이면 단위, 그 밖 일반모델은 skeleton 슬롯+18의 bone54×60 기록을 변환한다. 별도 Obj_Goal 분기는 원본에 보존되어 있으나 연습장 지형 입력이 아니다. 2bd14c4는 submesh의 **u16 인덱스 세 개+baseVertex(+30)**를 읽고2bd0990가 index3개를 triangle24B에 쓴다.

## 5. 재질 힌트·질의 [판독]

원본 재질 `paint_build_option`: Independent1, Fit2, DisableReplaceUVWarp3, 없거나미일치0(2beaac0). 2bea93c는 build option2/3을 우선하고, 나머지 `paint_prior_face`의 OnlyWall4/TriangleDir5/ThinTriangleFloor6을 읽는다. 2bea6a0는 XPlus/XMinus/YPlus/YMinus/ZPlus/ZMinus를 원본 방향분류기에 넣고 그 밖에는0xFF를 쓴다.

2bdec2c는 세 변 길이·각의sin으로 최소 높이h와 최장변L, h/L(L>1e-5)을 구한다. 방향0xFF이면 실제 cross 법선과 면적을 만든다. mode5가 아니고 `(h<.3 && h/L<.15)||(h<.1 && h/L<.3)`이면 가는 삼각형 분기: 면적<=.1 또는 비율<=.005는slender1, 나머지2. 최장변의 끝 두 정점을 선택한다. 삼각형 중심과 최대정점거리의 구로 질의한다.

slender1이 아니면 같은42방향을 먼저 질의한다. 결과없으면 모든방향, 결과있으면 이웃 방향을 추가 검사한다. 아직 후보도 없고query+50이 거짓이면 radius+1로 확장한다. +50은 콜백에 도달하면 참이므로 '선택 성공'과 같은 플래그가 아니다. mode4는 callback에서 벽방향24..31만 허용한다.

## 6. 후보 우선순위 [판독]+[실행]

2be135c는 각 후보 패널의 방향 평면으로 세 정점을 투영한다. 일반삼각형은 후보 box u/v ±.1, depth ±.2; 가는삼각형 mode2의 선분경우 u/v와depth±.01, 다른모드는±.1/±.2다. 사각형과 투영 삼각형의 overlapArea는2c0e594→118b6b0로 구한다. 가는삼각형은 최장변을 사각형과 clip하여 길이도 구한다.

| 우선순위(작을수록 앞) | 일반삼각형 |
|---:|---|
| 0 | 세 정점 모두 box안, query 법선과 후보 대표법선 dot>.99 |
| 1 | 일부 정점안/overlap>.1인 강한 후보, dot>.99 |
| 2/3 | 위 두 경우에서 dot조건실패, 인접 elevation군 차<2이며 수평법선 dot>.99(수직특수방향40/41제외) |
| 4 | 일부 정점안/overlap 후보, 위 방향조건 실패 |
| 5 | 정점안0·강한overlap아님, fallback허용(query+51), dot>.99 |
| 6/7 | 같은fallback에서 인접 수평방향조건 성립/불성립 |

정점안0이지만 overlap>.1 및dot>.99이면 우선순위1로 들어간다. query+52가 참이면 겹치는 면적을 panel+1D8에 누적하고 선택은 하지 않는다. 가는삼각형은 query+52에서 바로 반환한다.

가는삼각형: 양끝 모두box안→8. 적어도한끝안 또는 clip길이>0이면9/10. 원본 끝점순서에서 minDepth<depthA<maxDepth<=depthB이고 depthB>minDepth일때9,그밖10(끝점 순서를 임의 정렬하지 않는다). 아무것도 안 겹치면fallback허용때11,아니면후보제외. slender2는 overlapArea도 계산하고 slender1은0이다.

2bdfb18의 결과32B={panel,Nxyz,priority,overlapArea,clippedLength}. 우선priority 작은것; 동률은 다음 순서를 따른다. delta는모두새값−기존값이다.

- slender1/2+mode6: 새N.y>기존N.y일때만 교체.
- 다른slender: 면적 delta>.001 채택,<=−.001거부; 이어길이같은문턱; 이어중심의패널depth거리 delta<−.05채택,>=.05거부; 나머지새N.y가클때채택.
- 일반 같은방향: depth거리 delta<−.05/ >=.05를 먼저 적용, 이어면적·길이.
- 일반 다른방향: query법선dot delta>2^-23채택,<=−2^-23거부, 나머지면적·길이.

최종 완전동률은 기존후보를 유지한다. 4096/4096 원본 비교 결과32B가 독립 f32 재구현과 일치(스텁없음).

## 7. 정점과 삼각형의 UV 후처리 [판독]+[실행]

2be2de4는 각정점에 인접한 서로다른panel 최대6개를 목록순으로 모은다. 1개면 두UV같게/그panel접선. 2개이상이면panel id(+10)오름차순으로 안정정렬한 첫2개로두UV,첫panel접선. panel개수가2가아니면vertexflag2. baseDir(+54)가floor방향(28또는<8)인데effectiveDir(+38)가그렇지않으면flag4; 그panel pattern+9C가7/8이면flag8도켠다.

두UV의 U/V중 하나가±.005밖이면flag1,자기switch0;두번째panel삼각형의다른정점이flag1이아니면그정점switch−1을쓴다.

삼각형후처리: 모드!=3이고 세정점모두flag1이면 세UV를한panel로통일한다. 기본은triangle+10의panel. 어느변길이<.3이면2be3ed8이세정점 인접삼각형중배정panel이있고면적이가장큰삼각형을선택(동률첫것,면적0초기값엄격비교),그panel사용. 세정점에같은UV두개와그panel접선을다시쓴다. 이분기는최대삼각형없음의null보정이없어원본동작그대로남긴다.

별도bulk조건: flag4정점수>70 **그리고** flag8정점수>50,삼각형중어느정점flag(1|8)==9. 각정점인접panel중baseDir가floor(28또는<8)를찾으면해당panel로세정점통일한다. 짧은변일때최대인접삼각형이있으면그panel로다시교체. 이bulk분기는판독확정이며이번실행검증밖이다.

mapBox를늘리는2bee2e8은선택삼각형세정점의42방향 dot값을기존+3C..50 min/max에합친다. 따라서독립pattern인식의입력mapBox는시각메시투영에서생긴다.

## 8. 셰이더까지의 연결

후처리의 writer와 `_pu0/_pu1/_pu2` 포맷/바이트 쓰기는 colpaint_atlas §7.2의 기존원본검증을재사용한다. shader는 switch<0일때UV.zw,그밖xy를고르고offset뒤Y를1−Y로하여도색텍스처를샘플한다. 이번새판독은 BFRES입력→panel배정→이음매후처리의남은 연결을해소한다. 완전한지형패널연결·pattern·group·전체GPU잉크조명은각각별도질문이며임의확정하지않는다.

## 9. 웹 반영 필요

impl/paint.md/impl/assets.md/impl/render.md: 충돌오버레이표시대신시각지형정점에원본패널선택·두UV/switch/접선을공급한다. 두클래스vt58/60혼동을고치고삼각형후처리의mode3예외·짧은변.3·UV.005·최대인접면적·엄격동률을보존한다. 지면셰이딩전체가확정된것으로확대하지않는다. 구현·impl은변경하지않았다.

## 10. 실행 검증

r8_gfx_paint_mesh_emu.py→paint_display_mesh_emu.json: 실제setuppergetter2bcf540→원본2be2de4(삼각형4개·정점9개),42방향·모드0/3·짧은/긴변 **384입력/3456정점 UV·접선바이트일치**. sinf/cosf는별도원본SDK에서실행;합성getter스텁은제거했다. normal모드의세정점통일/모드3유지/최대인접panel을실행했다. 원본2bdfb18은4096건nostub32B일치. 이전추가리프2be3ccc/2be3ed8 각각1024nostub는graphics_paint_event_emu.json에기록한다.

합성유효배열을입력했으며 실제로비전체model/atlas를빌드하거나GPU화면을실행하지않았다. 패널후보의옥트리순회전체실행은하지않았고그조건은원본판독수준이다.

## 11. 정정·미확정

2026-10-03 r8: 기존'삼각형→panel/후처리 미판독'을위원본판독과새실행으로해소한다. setuppervt60를모델레코드공급자로본메모는2bee2e8 mapBox callback으로정정한다. 첫후처리실행은384/384성공;읽기명령의잘못된PowerShell wildcard와경로는commands에기록했다. det0 UV생산가능성·전체Lby수치atlas·GPU포맷열거이름·offsetwriter·최종잉크조명은별도미확정이고근거없는대체값을쓰지않는다.
