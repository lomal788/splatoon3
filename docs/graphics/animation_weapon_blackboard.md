# 슈터 애니메이션 무기 이름 공급 — v0 r8, 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행: 호출 구간] 사람 애니메이션의 WeaponCategory/WeaponDetail은 무기 선택이 바뀌거나 재시작하는 경로에서 원본 무기 getter로 공급된다. 일반 슈터는 둘 다 `Shtr`이며 활성 무기가 없어지는 분기는 둘 다 **빈 문자열**을 공급한다. 기존 r7 `anim_state_machine.md:L250`의 네 호출자 값 질문을 해소한다. 발사·이동 애니 전체 포즈 합성을 검증했다는 뜻은 아니다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon3 v0 main.reloc.img. 새 `analysis/decomp/r8_combat/animation_weapon_sources.c`:2491758/24BB240 전체함수. 기존 reset249CB60(gauge_batch1.c), sink24477B4(state_core.c), WeaponShooter289BFFC(camera/batch1.c)는 재사용한다. `web/tools/r8_graphics_weapon_category_sources_emu.py`, 결과 `analysis/completion/r8/graphics_weapon_category_sources_emu.json`.

## 3. 진입점과 전체 호출 흐름

[판독] BLcaller 전수조회는 아래 **4곳**이다. 마지막은 tail B이며 무기 getter 반환 값과 끝의 인자 복원을 읽었다.

| caller | 값의 원본 출처 | 호출 조건·갱신 |
|---|---|---|
| 2491940(2491758) | 선택 holder의 vt90→무기 vt230 | selected holder가 직전과 다르고 nonnull, T+105=0, 실제 무기가nonnull이면 getter→두문자열 전달 |
| 24919C8(2491758) | holder 문자열 buffer를 직접0으로 지움 | 선택 holder가 바뀌어 null이면 두buffer 첫byte 및 capacity−1을0으로 하고 빈문자열 전달 |
| 249CFC8(249CB60) | reset 입력의 holder vt90→무기 vt230 | 해당 reset 분기의 w20 조건과 holder/무기nonnull이면 getter→두문자열 전달. 관련 reset 전체조건은 기존 player_life 근거를 따른다 |
| 24BB548(24BB240 tail B) | param8 holder vt90→무기 vt230 | holder/무기nonnull이면 getter→두문자열→24477B4 tail B. null이면 이 공급을 생략 |

2491758은24C9824의 선택 bool에 따라 holder+8 또는+10을 선택한다. 선택이 같으면 문자열을 갱신하지 않는다. 24C9824의 전체 상태 의미는 이 네 값 질문에 합쳐 확정하지 않는다. 24BB240은 중간에도2491758을 호출한 뒤 별도 마지막 이름 공급을 수행한다.

## 4. 구조체·필드·상수·열거형 표

holder H+20/H+78은 getter의 두 SafeString 객체, 각각 H+28/H+80이 buffer pointer이고 H+30/H+88은capacity다. sink는 H+28/H+80의pointer를 인자 object를 통해 받는다. 실제 WeaponShooterVT5652468+230=289BFFC; 원본 문자열48E13BD=`Shtr`. 이 클래스·문자열의 기존 r5 판독은 재사용이며 새 호출경로가 신규 근거다.

## 5. 상태 전이와 수명

새 holder nonnull→원본 getter 공급, null→빈문자열 공급, holder가같음→기존 값 유지. reset/별도종료경로의 null은 빈문자열 공급이 아니라 호출생략이다. 실행되는 네 source와 skip의 차이를 유지한다. 실제 holder 선택/actor 생성은 실행fixture로 공급한 경계다.

## 6. 계산식·조건·의사코드

[판독]+[실행] 원본 슈터 getter는각buffer에 `Shtr[:min(4,capacity−1)]`를 복사하고 바로뒤0을 쓴다. 각 caller는capacity−1 byte도0으로 보장한다. clear는첫byte0이어서 두 값 모두빈문자열이다. capacity는 양수인원본객체 계약이며0/음수buffer를 유효입력으로 가정하지 않는다.

## 7. 애니메이션·데이터 연결

기존24477B4는 사람 wrapper+50/+58 및+250/+258의두해석기에같은pointer를쓰고dirty23C/43C=1, 블랙보드WeaponCategory/WeaponDetail에도같은값을쓴다. 기존244D0B0는 Nrml을Detail→Category 순으로 치환한다. 이 sink/클립대체2210건은기존확정근거를재사용한다. 다른무기의Category/Detail 값은이번범위밖이며해소했다고하지않는다.

## 8. 다른 기능과의 상호작용·정정

2026-10-03: 기존 “슈터Shtr만해소,나머지caller249CFC8/24BB548미확정”을 새전체caller판독+네구간실행으로해소했다. **24919C8은 getter가아니라empty 공급**이라는별도동작을확인했다. func_lookup24BB240은앞함수24BB0E8을반환했으므로실제24BB240 prologue를확인후디컴파일했다. tail B를BL검색에누락하지않는다.

## 9. 웹 포팅 구조와 구현 순서

impl/render.md·assets.md에필요: 일반슈터이름은Shtr/Shtr로두해석기와BB에동시에공급하고, 선택holder null전환은empty/empty로원본대로갱신한다. reset/종료caller가null이면갱신을생략한다. 이전name을상시Shtr로고정해clear상태까지덮어쓰지않는다. 이번작업에서는코드/impl변경0.

## 10. 검증 코드·명령·결과·기대값

SHARED/FUNCS/decomp_index--no-build/func_lookup/bl_callers/disasm→새2함수full_decomp exit0. `.venv/Scripts/python.exe web/tools/r8_graphics_weapon_category_sources_emu.py` exit0. 네caller원본dataflow block각256=**1024사례**가독립문자열절삭/empty기대와일치, nullread/nullcall/automap/fault/PLTstub0. capacity1/2/4/5/8/64 및detail random1..64,초기buffer쓰기흔적포함.

원본WeaponShooterVT의실제230getter를실행했고외부문자열복사는하네스의memcpy동등경계다. selectedWeapon pointer와holder buffer가fixture이며4전체caller함수의모든sideeffect를실행한것이아니다. 24477B4 또는마지막tail epilogue앞에서명시적중단했다. source조건/끝인자복원은전체caller판독으로확정한다. 다른무기의getter·전체ASB포즈·renderer를이실행으로검증하지않는다.

실패보존: r5_gfx_char_name_emu.py없는파일조회→실제r5_gfx_char_clipname_emu.py로정정. 원본buffer/default크기를이randomfixture로확정하지않는다. 원본실행codepatch0.

## 11. 미확정과 다음에 필요한 근거

네caller의범위내값질문은해소했다. actualholder 선택predicate24C9824 전체상태, 모든caller의게임수명sideeffect, 이후BB→ASB다층pose→GPU전체프레임은별도미확정 inventory항목이다. 다른무기값은범위밖이다. 기존블랙보드공급복합행L277은MoveSpeedRt·전체갱신등남은질문을포함하므로이번한source검증으로승격하지않는다.
