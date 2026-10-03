# FillUp 태그의 실제 바닥 후보 소비자 (r9, 2026-10-03)

## 1. 기능 개요와 체감 동작

**[판독]+[실행: 분류 블록]** 플레이어의 아래쪽 바닥 탐색 함수 `24f8f58`는 접촉의 `UserShapeTag` **bit28 FillUp**을 읽는다. 최고 높이의 유효 접촉이 FillUp이면 일반 바닥 성공 경로를 선택하지 않고 대체 탐색으로 넘어간다. 그 태그가 플레이어용 충돌 벽과 함께 쓰이는 사실과, 제작자가 왜 해당 면을 넣었는지는 서로 다른 근거다. “구멍 메우기”라는 작성 목적은 여전히 **[미확정]**이다.

## 2. 원본·범위·자료

Splatoon3 v0, Lby_Lobby00 1인 연습. 코드: `0x71024f8f58` 1,068B, 정적 초기화 `0x71024f0bb0` 524B. 신규 decomp `analysis/decomp/r9_physics/fillup_contact_height.c`, `fillup_static_init.c`.

새 tool `web/tools/r9_physics_fillup_classifier_emu.py`, 결과 `analysis/completion/r9/physics_fillup_classifier_emu.json`, 최초 실패 `physics_fillup_classifier_first_failure.json`.

태그 이름·마스크는 원본 PhiveConfig의 분석 산출 `analysis/gimmick/PhiveConfig.json`과 대응한다. [collision_mesh.md](../gimmick/collision_mesh.md) §3.4.4에서 사격장 원본257배치/48팩/14bphsh/59재질행/118PhiveBYML의 FillUp0을 별도로 확인했다.

## 3. 진입점과 호출 흐름

**[판독]** `24f8f58(P, position, offset, output, adjustY; s0=distance)`는 P+2770의 원본 ray query를 구성하고 `3a5f36c`로 실행한 뒤 P+28b8 접촉 목록을 `12d8dcc` iterator로 순회한다. 이 query/iterator 함수는 기존 분석을 재사용했으며 새 검증으로 다시 집계하지 않는다.

새 직접 caller 원본 BL: `2462830`(시작24626b0), `2478ac8/247913c/2479784`(기존move_full_main의2475a54; 아래 날짜정정), `24fa06c`(시작24f99b4). 24626b0 경로는 거리10/offset0/outputNULL/adjust0으로 호출해 실패하면 대체 위치 getter27c8dc4를 선택한다. 24fa06c는 adjust1/출력vec3로 바닥 검사를 하여 성공 분기에서 좌표를 복사한다. 이 호출자 전체의 목적이나 상태를 이름만으로 명명하지 않는다.

## 4. 필드·상수·원본 태그

C=128B 접촉, E=16B iterator 항목, T=16B 재질행. C+38/C+48 중 E+8 bit0에 따라 상대 행을 선택하며, **T+8의u64 bit28**이 FillUp다. Body+180에 있는 필터 정보+8 bit28은 별개 필드다.

| 필드·마스크 | 내용·writer→reader |
|---|---|
| C+4 | 접점 높이 / 접촉 생성→24f90fc |
| C+10 | 법선Y / 접촉 생성→24f90e0 |
| C+30 | 반대쪽 높이 보정에 쓰는 거리 / 24f9108 |
| E+8 bit0 | 상대 행/법선 부호 선택 / 90e4~9140 |
| C+68 bit2, E+8 bit1 | array 다음 항목에서 제외하는 상태 / 91e8 이후 |
| T+8 mask 0x100004 | **Water(bit2) 또는 Slide(bit20)**이면 대체 탐색 / 914c |
| T+8 bit28 | **FillUp**이면 대체 탐색 / 91a8 |
| T+8 mask 0x08200000 | **Fence(bit25) 또는 KeepOut(bit27)**이면 낮춘 높이에서 재질의 / 9144,920c |
| G58bc7a0 | 법선Y 한계 `0x3f24360c`=.6414496898651123 / 24f0c84~90→24f9088 |
| −.35 | 재질의 높이 편향 `0xbeb33333` / 24f9214~23c |
| ±1.3962634 | 대체 탐색 각도 입력 `0x3fb2b8c2` 및 부호반전 / 9250 이후→24f9384 |

정정(2026-10-03): 초기 raw image의 G58bc7a0=0은 런타임 값이 아니다. 정적 초기화 원본이 위 값을 기록한다. 또한 0x100004를 PlayerDead, 0x08200000를 PlayerUnsafe로 임의 이름 붙일 수 없다. 실제 ComponentName은 위 표다.

## 5. 상태 전이와 수명

원본은 position+offset에서 거리 s0만큼 아래로 query를 만들고 ray 설정 P+2884=8, P+286c=1, P+2868 |=0xc를 쓴다. 접촉 후보 중 법선 조건을 통과하고 이전 최고보다 높은 항목만 최종 분류를 덮어쓴다. 같은 높이는 먼저 본 후보를 유지한다.

높이가 갱신될 때 adjustY bit0이면 output.y도 먼저 갱신한다. 분류가 FillUp/Water/Slide여도 이 기록 순서를 생략하지 않는다.

최종 Fence/KeepOut 후보이면 height−.35로 위치Y를 낮추고, 남은 query 길이에서 `max(oldPositionY−newPositionY,0)`를 뺀 뒤 다시 query한다. 해당 재진입 횟수에 이 함수 내부의 임의 상한은 없다.

## 6. 계산식과 상세 의사코드

**[판독]+[실행: array 분류 구간]**

```text
found=0; disallowed=0; retry=0; highest=-FLT_MAX
for eligible C,E in source iterator order:
    signedNy = E.side ? C.normalY : -C.normalY
    if signedNy < f32(.6414496898651123): continue
    h = E.side ? C.pointY : f32(C.pointY + f32(C.distance*C.normalY))
    if highest >= h: continue
    if adjustY: output.y = h
    tag = (E.side ? C.rowB : C.rowA).u64Tag
    retry = (tag & (Fence|KeepOut)) != 0
    disallowed = (tag & (Water|Slide)) != 0 ? 1 : ((tag >> 28) & 1)
    found=1; highest=h
invalid = disallowed | retry | (found ^ 1)
if retry & invalid:
    newY=f32(highest + f32(-.35))
    remaining=f32(remaining - max(f32(oldY-newY),0))
    query_again(newY, remaining)
elif invalid==0: return true
else: fallback()
```

**[판독]** fallback에서 offset=(0,0,0)이면 false를 반환한다. 그 외에는 원본 `24f9384`를 각도 +1.3962634/−1.3962634로 두 번 호출한다. 한쪽만 성공하면 해당 출력을, 양쪽 모두 성공하면 각도 비교로 선택한 출력을 저장하고 성공 여부의 OR을 반환한다. 초기 분류 블록 실행에는 이 각도 보조 함수를 포함하지 않았다. 이후 새 [fillup_fallback.md](fillup_fallback.md) §3~11에서 원본 helper4096/112810필드·parent2048/76924필드의 독립 비트0bad를 확인했다(query 결과 공급 fixture 경계 명시). helper에 normal/tag 검사는 없으며 초기 성공 후3이분한다.

## 7. 표현·카메라와의 연결

성공·대체 위치는 플레이어의 위치 후보에 영향을 주므로 접지와 이동 체감에 연결된다. 이 함수는 직접 이펙트·효과음·카메라를 선택하지 않는다. FillUp이면 물리 접촉 자체가 사라진다고 해석할 수 없다. 형상 행 필터와 이 게임 측 바닥 후보 분류는 서로 다른 단계다.

## 8. 상호작용과 범위

원본 array/list iterator와 query 생성에 연결된다. 이번 신규 실행 범위는 array 분류의 실제 명령 구간 `907c`에서 success/fallback/requery 분기까지다. query 생성·linked iterator·±각도 fallback을 실행한 근거로 확대하지 않는다. 첫 array 항목은 원본 iterator에서 이미 선택된 상태라는 진입 조건을 명시한다. 다음 항목을 제외하는 조건은 원본 명령으로 실행했다.

## 9. 웹 반영 사항

향후 `impl/physics.md` 반영 시 tag bit28을 body 필터 flag bit28과 구분해야 한다. 바닥 후보 분류에서 Water/Slide/FillUp의 대체 경로와 Fence/KeepOut의 −.35 재질의를 구분하고, 모든 KeepOut을 일괄 바닥으로 취급하지 않아야 한다. Lby 정적 데이터의 FillUp은 0이므로 새 FillUp 지형을 추측해 만들면 안 된다. 이번 웹 코드·impl은 변경하지 않았다.

## 10. 실제 검증·실패

```text
.venv/Scripts/python.exe web/tools/decomp_index.py 0x71024f91a8 --no-build
.venv/Scripts/python.exe web/tools/func_lookup.py 0x71024f91a8
sh web/tools/full_decomp.sh analysis/decomp/r9_physics/fillup_contact_height.c 0x71024f8f58
sh web/tools/full_decomp.sh analysis/decomp/r9_physics/fillup_static_init.c 0x71024f0bb0
.venv/Scripts/python.exe web/tools/r9_physics_fillup_classifier_emu.py
```

**[실행: 블록]** 원본 정적 writer `24f0c84..94`가 `0x3f24360c`를 기록한다. 분류 `907c`에서 각 분기까지 **4,096사례/28,672개 정수·f32 필드**가 독립 계산과 비트 일치했다. 성공815, fallback2483, requery798. PLT/null/auto/fault는 모두0이다. 0접촉, 양쪽 side, 같은 높이, 제외 flag, 혼합 tag를 포함한다.

첫 참조는 법선 한계0을 기대해 2,196개 불일치(exit1)가 발생했다. 실패 JSON을 보존하고, snapshot이 원본 초기화를 마친 G=.64144969임을 확인했다. 원본 writer에 맞춰 참조를 수정한 뒤 불일치0(exit0)이다. 디버그9사례 중1개 불일치(exit1)도 같은 원인이다. query나 수학 callback을 성공 stub으로 대체하지 않았다. 신규 디컴파일은 두 파일 모두 exit0이고 각각 index6,125 및6,139였다.

## 11. 미확정과 다음 근거

**[미확정]** FillUp의 작성 목적 “구멍 메우기”를 증명할 원본 주석·제작 자료를 찾지 못했다. 이번 확인은 런타임의 바닥 후보 대체 판정이며 작성 목적의 근거가 되지 않는다. Lby 동적 shape 추가의 전체 경로와 각 caller의 전체 상태 수명은 추가 분석이 필요하다. linked iterator 조건과 fallback `24f9384`의 전체 식은 새 [fillup_fallback.md](fillup_fallback.md) §4~10에서 원본명령·독립 실행으로 해소했다(query 결과 합성 공급 경계 유지). 고정 질문 `collision_mesh.md:L148` 전체를 이 부분 결과로 승격하지 않는다. 다음 근거는 actor shape producer와 map 작성 metadata다. **정정(2026-10-03):** 초기 기록 “24f9384→24f8f58 재귀”는 새 helper 전체 원문에 없는 호출이다. helper가 직접 rayquery/iterator를 실행하며 parent로 재귀하지 않음으로 정정한다. 또한 초기2475898 caller attribution은 lookup의 앞함수 오귀속이었다; 기존2475a54 메인과 실제 BL3곳을 ARM으로 재확인했으므로 §3을 정정했다. 잘못된 초기기록의 이유와 새 근거는 fillup_fallback§3·11에 남겼다.
