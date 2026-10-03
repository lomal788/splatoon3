# FillUp 바닥 대체 탐색·호출자 (r9, 2026-10-03)

## 1. 개요

**[판독]+[실행: query 입력 공급 fixture]** 원본 `24f8f58`의 FillUp/Water/Slide 후보는 오프셋이 0이면 실패하고, 그 외 ±80° 위치에서 바닥을 찾는 `24f9384`를 실행한다. 이 helper는 초기 각도에서 query가 성공하면 3번 이분 탐색한다. 양쪽 성공·각도 크기가 동률이면 음수 각도 쪽이다. 작성 목적 “구멍 메우기”는 별도 미확정이다.

## 2. 원본·파일

새 `analysis/decomp/r9_physics/fillup_fallback_callers.c`:24f9384(1584 B),24626b0(636 B),24f99b4(1804 B). 기존 `move_full_main.c`:2475a54 메인, 기존 bb_phive2.c:12d8dcc iterator. 새 함수는 notes/index/lookup 확인 후 full_decomp exit0/INDEX6157, 기존 함수는 재디컴파일하거나 새 확정으로 집계하지 않았다.

도구 `r9_physics_fillup_fallback_emu.py`,`r9_physics_fillup_parent_emu.py`; 결과 `analysis/completion/r9/physics_fillup_fallback_emu.json`,`physics_fillup_parent_emu.json`.

## 3. 진입·호출자 **[판독]**

`24f9384(context, angleOut, posOut; s0=angle)`의 context는 `(P, basePosPtr, offsetPtr, distancePtr)` 32 B다. helper가 **24f8f58을 재귀호출하지 않는다**. 직접 P+0x2770 query→3a5f36c→12d8dcc를 실행한다.

- 24626b0→2462830:source위치27c8c98로 가져온좌표를distance 10/offset 0/outputNULL/adjust0으로 아래 검사하고false면27c8dc4 위치로 바꾼다. 외부객체·상태의 전체 생명주기 의미는 이름만으로 단정하지 않는다.
- 2475a54 메인의 BL2478ac8/247913c:offset 0,높이보정거리,후보 좌표 output. 첫 구간은 전후높이 차가±FLT_EPS 이내거나최대4회이면 반복종료. 두 번째 구간은adjust 1 성공때 후보복사.
- 2479784:현재기준좌표+G58bc16c를ray시작으로,후보XZ−기준XZ를offset으로distance 2*G58bc16c/adjust 1 검사. false면기준위치복원;true면후보를복사하고G58bc174.high로 보간한다. 기존메인의전체행동상태해석은재사용/부분범위와구분한다.
- 24f99b4→24fa06c:앞방향query에서비바닥접촉첫후보를잡은뒤수평face normal을normalize*.6 더한 위치에서distance 50/offset 0/adjust 1 아래검사. 성공이면2번째출력에기존벽후보위치를보낸다.

**정정(2026-10-03):** 이전root기록의2475898 attribution은func_lookup가앞function으로잘못 귀속한 결과다. 기존move_full_main의2475a54가실제상위메인이며BL3곳의ARM명령으로확인했다. state_core의2475898은별도 cleanup이며해당 BL을포함하지않는다.

## 4. 데이터·각도·lookup

첫각도±`0x3fb2b8c2`=1.3962634658813477rad(80°). angle*`0x4e22f983`를f32로계산하고FCVTZS int64,상위8bit에해당하는256행 sin/cos lookup(`4aa5b5c`,행16 B)을선택한다. 낮은24bit/2^24로행의sin/deltaSin/cos/deltaCos를각각f32선형보간한다. host sin/cos와같다고가정하지않는다.

ray source는 base+Y축회전offset, endY=sourceY−distance, endXZ=sourceXZ+distance*(-0.0)이다. 0곱·부호0도원본 명령대로보존한다.

## 5. iterator·접촉수명 **[판독]+[실행]**

원본 `12d8dcc`는mode0/1이면 count+8/array+30,mode2·a4=0이면count+c/array+40,mode2·a4!=0이면linkedlist다. 연결 offset=List+7c,처음노드=List+70−offset,sentinel=List+68−offset,next=node+offset+8의pointer−offset.

배열은C+68bit2 또는Entry+8bit1이있으면제외한다. linked는여기에**C+68 bit8 필요**조건이추가된다. 처음항목부터같은 조건을적용하는원본 iterator와이후반복명령을전체함수에서실행했다. Entry bit0으로 C+4높이 또는C+4+C+30*C+10을선택하며 같은높이는먼저본후보를유지한다.

## 6. fallback·선택식 **[판독]+[실행]**

```text
angle = +/-80deg
if query(rotated offset(angle)) == false: return false
output = highest eligible contact at that ray, when any
angleOut = angle; low = 0; high = abs(angle)
repeat 3:
    mid = F(F(low+high)*.5), with sign of original direction
    if query(mid):
        output = highest eligible contact at that ray, when any
        angleOut = signed(mid); high = mid
    else: low = mid
return true
```

**helper에는  normalY한계·Water/Slide/FillUp/KeepOut 태그 검사가 없다.** query success 자체로이분 성공을판정하며,내부높이선택은원본 iterator의제외조건만따른다. Nativequery가true인데모든항목이제외되면helper는true를반환하고출력좌표는이전에있던값을유지한다. 그럴듯하게false로고치지않는다.

parent는output Y를최고높이분류중에먼저갱신한다(adjust 1). 정상분류면true;Fence/KeepOut면높이−.35로base를내려남은거리에서max(oldY−newY,0)을빼고재질의;FillUp/Water/Slide/미발견이면offset 0검사후위helper양쪽을호출한다. 양쪽성공이면 `-negativeAngleOut <= positiveAngleOut`일때음수쪽선택(동률포함). 한쪽성공이면그쪽좌표,양쪽실패면직전output보존.

24f99b4의앞방향70query는blocking C+68bit1과상대tag를읽고 **0x18300004=Water|Slide|PlayerDead|KeepOut|FillUp** 접촉을제외한다. 그뒤nativeface normal3c4988c를구해진행방향dot>0이면최장거리후70남은거리에서distance+.5+.1을빼재질의한다. faceNormalY>=G58bc7a0이면직접성공좌표복사;그외첫벽후보에서수평normal*.6 위치의50아래검사로분기한다. 이caller 전체는판독이며caller의native query/faceNormal 전체를독립실행했다고주장하지않는다.

## 7. 체감·표현 연결

FillUp 태그는 물리contact필터와별도로이게임측위치후보를바꾼다. offset 0 아래검사에서는FillUp만이유일유효바닥이면false이며,offset이있는이동후보검사는좌우각도를낮춰대체좌표를선택할수있다. helper에tag재검사가없으므로FillUp접촉자체를항상없애는기능이라고설명하지않는다.

## 8. 실제경로·검증경계

전체 helper 4,096회와 parent 2,048회는**nativequery3a5f36c 결과만명시된합성공급**이며,실제형상캐스트hit을스텁없이검증한것이아니다. 원본 `24f8f58`/24f9384의분류·숫자·반복·출력·원본 `12d8dcc`는실제명령으로실행했다. query 수학·형상 필터·원본 태그 생산자는 이 시험의 증거가 아니다. 태그 생산은 [fillup_preset_runtime.md](fillup_preset_runtime.md) §3~6의 원본 설정 로더로 연결한다. 실제 PhiveConfig 등록 1,179정수 필드가 일치하며, FillUpPlayer(index61)는 tag `0x10000000`/유효1과 Entity mask `0x62`/유효1을 기록한다. 이 등록 실행은 native geometry query의 접촉 생성과 별도다. 실제 형상 적용 경로는 [fillup_dynamic_sources.md](fillup_dynamic_sources.md), 배치 자료는 [fillup_authored_data.md](../gimmick/fillup_authored_data.md)로 연결한다. Lby 정적48팩의 FillUp0 결과도 유지한다.

## 9. 웹 반영 필요

impl/physics.md:FillUp를보이지않는범용벽이름으로쓰지말고원본tag분류와ray후처리를분리한다. offset 0 실패,±80°초기+3이분,음수동률,helper태그/법선미검사,linkedbit8 조건,adjustY선갱신을유지한다. 모든query success를유효바닥으로바꾸거나빈후보를자연스럽게false로고치지않는다. 새원본데이터에없는LbyFillUpmesh를만들지않는다. 웹코드는미수정.

## 10. 명령·결과·실패

`python -X utf8 web/tools/r9_physics_fillup_fallback_emu.py`: **4096/112810필드 bit mismatch 0**;4iterator모드각1024. 원본lookup회전의ray6f32,3이분angle,높이/좌표/return/flags비교,null/auto/PLT/fault 0.

`python -X utf8 web/tools/r9_physics_fillup_parent_emu.py`: **2048/76924필드 bit mismatch 0**. 정상631/fallback1141/offset 0false276/retry321. 원본 분류→retry→helper두쪽→tie선택전체 제어; threshold원본staticwrite실행.null/auto/PLT/fault 0. 두새도구첫실행부터일치했다. 숫자 필드 집계 정정(2026-10-03): 초기108714/74876은출력12B와raycontainer를복합비교필드로센값이었다. outputXYZ를3scalar/raycontainer를0scalar로정의하여case당+1인112810/76924로바로잡았다. 원본출력·불일치수는변경없고반복실행하지않았다.

선행decomp_index24f9384/24626b0/24f99b4 없음,lookup1584/636/1804 B→full_decomp 새3함수 exit0/INDEX6157. linkediterator 기존bb_phive2재사용,ARM24f9384초반110+96a4이후145명령판독. callerBL ARM재확인. `rg analysis/decomp/r6_physics*`는PowerShell literalglob os123실패였으며기존bb_phive2 정확경로로읽었다.

## 11. 미확정·정정·다음근거

**[미확정]** authored “구멍 메우기” 목적과 동적 씬 생성 전체, 실제 Lby 지형의 native query 전체. 수치·분기·iterator·런타임 태그 제외/대체 규칙은 위 명세로 확정했다. query 결과를 합성 공급한 경계는 유지한다.

이전root문서§11의 “24f9384→24f8f58재귀”는새전본문으로철회하며,초기기록을날짜정정이력으로남긴다. 원본 FillUpPlayer의 태그/Entity mask 등록은 [fillup_preset_runtime.md](fillup_preset_runtime.md), 실제 형상 소비는 [fillup_dynamic_sources.md](fillup_dynamic_sources.md)로 보강했다. 다음 목적 근거는 원본 DCC 저작 소스·exporter 주석·제작자의 해당 태그 설명이다. 함수명이나 런타임 소비로 제작 목적을 만들지 않는다. 고정 질문 `gimmick/collision_mesh.md:L148`의 authored 목적이 남아 있으므로 조사중을 유지한다.
