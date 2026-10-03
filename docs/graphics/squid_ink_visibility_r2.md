# 자기 잉크 잠영 표시 지연·재질 reset·모델 홀더 — 추가 원본 실행

2026-10-03 · Splatoon 3 v0, Lby_Lobby00 1인 연습. 분석만 수행했다. 웹 코드·impl·에셋·original은 변경하지 않았다.

## 1. 기능 개요와 사용자에게 보이는 동작

오징어로 변신하는 애니메이션과 자기 잉크에서 모델을 숨기는 판정은 서로 다른 경로다. 이 문서는 기존 [player_state §6.1.4](../player/player_state.md#614-b7a0-지연된-판정값의-producer--8차-판독)의 B7a0 producer 판독을 **원본 ARM 실행으로 보강**하고, 이전 [ink_visual_path §6.3](ink_visual_path.md#63-숨김-gate--신규-원본-실행진입-블록)에서 실행하지 않은 표시 함수의 counter·재질 reset·홀더를 연결한다.

**[실행: 입력 경계 명시]** ordinary 후보 생산 블록→B794/B798 지연→SM 표시 전체 함수→홀더 전체 함수를 이어 실행하면, 잠영 중 body/`_Hlf`/squid/rail 표시가 모두 꺼진다. `squid && swimming`으로 즉시 숨기는 것과 다르다. 자기 잉크 샘플러, 전체 플레이어 슬롯19, 실제 GPU 표시와 파문 이펙트까지 실행한 결과는 아니다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치·확정 수준 |
|---|---|
| ARM 원본 이미지 | `extracted/exefs/main.reloc.img`, BASE `0x7100000000`, SHA256 `39a8c94826d84b6106f112f2db16f7b2e2743bc6afd72054534a7708a9848a41` |
| 기존 producer 디컴파일 | `analysis/decomp/player/player_slot19.c`, 함수 `0x7102483134`, 6824~6905행. 중복 Ghidra 실행 없음 |
| 기존 표시·홀더 디컴파일 | `analysis/decomp/render/r4_disp.c`, `r4_holder.c`. 기존 판독 재사용 |
| 생성·재시작 | `analysis/decomp/player/player_components_vt.c`의 `245717c`, `analysis/decomp/life/batch1.c`의 `23547bc`. 기존 판독 재사용 |
| 신규 leaf 디컴파일 | `analysis/visual_gap_r2/squid/grind_leaf.c`, `0x7102531028` [판독] |
| 상수 입력 | `analysis/player/bss_consts_58bb000.json`의 기존 원본 정적 초기화 결과. 이번 새 발견으로 세지 않음 |
| 새 하네스·결과 | `web/tools/squid_visibility_r2_emu.py`, `analysis/visual_gap_r2/squid/native_visibility.json`, `commands.md` |

먼저 SHARED/FUNCS 및 `decomp_index.py --no-build`로 중복을 확인했다. 기존 writer 판독과 이전 entry64건을 새 실행 건수에 더하지 않았다. 고정 inventory의 전체 슬롯19 질문은 여전히 조사중이다.

## 3. 진입점과 전체 호출 흐름

**[판독: 기존 연결 + 신규 실행 보강]**

```text
245717c 생성 / 23547bc 재시작
  B794=0, B798=9999, B7a0=0
2483134 플레이어 행동 슬롯19
  248c16c ordinary 후보 블록
    2458cfc 아군 잉크 오징어 조건
      PlayerGrindRail VT5635660+110 → 2531028(+1f4 byte)
    248c250..c2e4 N/Noriginal 성분 일치 → w26
    ordinary && airFrames<T && wallChargeProgress<.25
    특수 후보 OR (이번 연속 실행에서는 inactive)
  248c5c0..c7dc 지연·age·B7a0 기록
  기존 같은 프레임 연결: 248dd94→249648c
    243e2dc SM 전체 표시 결정·counter·재질 reset
    14595b0 모델 홀더 전체 표시 결정
  243a434→1459284 그리기 제출 (이번 실행 범위 밖)
```

이번 하네스는 원본 `248c16c..c7dc` 블록을 실제 실행하며 내부 `2458cfc`, `2531028`도 원본으로 실행한다. 그 뒤 `243e2dc`, `14595b0`을 **하네스에서 순서대로 호출**한다. `249648c` 자체나 슬롯19 전체가 자동으로 이어졌다고 표현하지 않는다.

## 4. 구조체·필드·상수·열거형 표

기준 `B=PlayerBehavior+108의 본체`, `P=B+784`, `SM=상태기계`, `H=모델 홀더`, `G=PlayerGrindRail`.

| 필드 | 타입·뜻 | writer → reader |
|---|---|---|
| B+794 = P+10 | s32, 현재 판정 교체 대기 | 생성/재시작0, c5c0 tail → 같은 tail |
| B+798 = P+14 | s32, 현재 유지 경과. 생성/재시작9999 | c770/c7d8 → 이후 본체 소비자; 이 문서는 age 기록까지만 |
| B+7a0 = P+1c | u8, 지연된 잠영/특수 숨김 판정 | c6fc → SM243e2dc·기존 카메라/회복 소비자 |
| B+180..188 | vec3, 실제 지지 법선 N | 기존 접촉/이동 writer → c250 성분 비교·f의 N.y |
| B+198..1a0 | vec3, 원 지지 법선 | 기존 [player_state §7.3](../player/player_state.md) → c250 비교 |
| B+a74/a78 | f32, 모서리 미끄럼 계수 | 기존 접촉 정리 → c5ec/c708 max |
| B+c0 | s32, 공중 프레임 | 기존 접지 writer → ordinary 후보의 `<T` |
| G+1f4 | u8, grind rail 조건 getter 값 | 실제 생산자는 별도 → native2531028, vt+110 |
| SM+f4/f5/f6/f8 | u8, body/hlf/squid/rail | 243e2dc → H+60..63 |
| SM+f7 | u8, 직전 squid flag | 243e2dc 진입에서 이전 f6 복사 → squid off reset |
| SM+f0 | s32, 변신 카운터 | 상태/표시 writer → hlf ≥61; 아무 human 표시가 없고 dead=0이면90/상태96이면140 |
| SM+1b0/1b8/1c0/1c8 | ptr, body/hlf/공통 사람 파츠/squid의 칠 보완 binder | 기존 생성자 → reset·2448878 |
| binder+8/c/10 | f32[3], 팀별 칠 세기 **캐시** | off 시 `0x7fc00000` → 다음 setter 비교 |
| H+60/61/62/63 | u8, 제출할 최종 모델 플래그 | 14595b0 → 1459284 |

상수는 false 최소5/교체 후10, true 최소 `trunc(1+4*f)`/교체 후 `trunc(3+7*f)`, ordinary 상한3, 강제 상한1, 법선 epsilon=2^-23, wallCharge 임계.25다. [판독]+기존 [데이터], 신규 [실행]으로 소비 순서를 보강했다.

## 5. 상태 전이와 전체 수명

**[실행: 생성·재시작 write 블록512건]** 두 기존 경로 모두 B7a0=0, B794=0, B798=9999로 쓴다. 생성자/재시작 함수 전체를 이번에 재실행한 것은 아니다. 처음부터 candidate=true로 시작하고 delay=0이면 교체가 바로 가능하다. 이미 false를 유지한 경우와 초기 counter를 같게 가정하지 않는다.

**[실행: ordinary producer 10,800건 + tail8,192건]** 같은 판정이 계속되면 delay를1 줄이고 현재 판정의 최소치로 올린다. 반대 후보가 나타나면 현재 delay를 줄이는 동안 기존 B7a0를 유지하며 age가 증가한다. 교체할 때 age=0, 새로운 판정의 refill 값으로 delay를 채운다. 후보가 잠깐 깜빡이면 같은 판정 분기가 delay를 다시 최소치로 올리므로 단순한 연속 true 횟수 카운터로 바꾸지 않는다.

원본 법선 필드에 수치를 넣은 연속 실행 예시다. 평지 외 입력은 합성 경계이며 실제 Lby 프레임을 캡처한 값이 아니다. 시작은 hidden0/delay5/age0이고, frame0..7 false, 8..27 true, 28..47 false, 48..67 true다. index는0부터다.

| 입력 | f | 처음 숨김 | false 복귀 | 다시 숨김 | 교체 후 true delay |
|---|---:|---:|---:|---:|---:|
| N=(0,1,0), 원 법선 동일, 모서리0 | 0 | frame12 | frame28 | frame52 | 3 |
| N.y=.5, 원 법선 동일, 모서리0 | .5 | frame12 | frame30 | frame52 | 6 |
| N.y=2의 **합성 경계 입력** | -1 | frame12 | frame28 | frame52 | -4 |

마지막 행은 실제 정규화 표면 법선이라고 주장하지 않는다. 원본 f의 하한 clamp가 없고 refill이 음수가 될 수 있음을 보존하기 위한 경계 입력이다. 평지 f=0이면 false 안정 최소5→true 교체5회, true 안정 최소1→false 교체1회다. 상태·force 조건이 바뀌면 아래 식의 상한이 적용된다.

## 6. 계산식·조건·상세 의사코드

**[실행: finite 성분 경계4,096건]**

```text
sameNormal = 모든 xyz에 대해 -2^-23 <= f32(N.xyz-Noriginal.xyz) <= +2^-23
f = sameNormal ? min(1, f32(f32(1-N.y)+max(Ba74,Ba78))) : 1
// f 하한0 없음. f32 곱과 덧셈은 분리, FMA로 합치지 않음.
S = {82..90, aa..ac, ed, ee, 10c}

if candidate == oldHidden:
    minimum = oldHidden ? trunc(f32(f32(f*4)+1)) : 5
    delay = max(s32(delay-1), minimum)
    age = s32(age+1)
else:
    if state not in S: delay = trunc(min(f32(delay),3))
    force = B9210 || StartLaunch.b4 || (B782 && state==87)
            || InkRail.1e0 || debugForce || (upwardCondition && !candidate)
    if force: delay = trunc(min(f32(delay),1))
    delay = max(s32(delay-1),0)
    if delay > 0:
        age = s32(age+1)  // hidden 유지
    else:
        hidden = candidate
        delay = candidate ? trunc(f32(f32(f*7)+3)) : 10
        age = 0
```

ordinary producer 실행군은 특수 inactive/무효 rail·vehicle handle, warp kind0/1/2, StepPaint mode0..3, grind byte0/1, state85/88/91/aa/ed, air0/1/3/4/5, `PlayerParam+13c=60` 및 wallChargeFrame0을 공급했다. 이 조건군의 native 후보는 `state∈S && state!=88 && StepPaint.mode<2 && warp.kind∉{1,2} && !grind.byte1f4 && air<4`와 일치했다. **PlayerParam+13c=60은 하네스 입력이지 Lby의 실제 선택 값 신규 확정이 아니다.** wallCharge 전체 곡선·토관kind3·유효 특수 핸들은 기존 판독 수준으로 남긴다.

### 6.1 표시 reset의 NaN과 실제 setter 인자는 다르다

**2026-10-03 정밀화 [판독]+[실행: 호출 경계]:** 기존 “thr_comp_paint_intens를 NaN으로 reset” 표현은 캐시와 소비 값을 구분해야 한다. off된 모델 binder의 cache3칸에는 quiet NaN `0x7fc00000`을 쓰지만, 이어지는 vtable+10 setter의 ARM **S0 인자는 0.0**이다. GPU uniform 자체에 NaN을 넣으라는 이식 명세가 아니다.

순서는 body off→hlf off→squid off→human 전체 off일 때 공통 파츠이며 각각 팀0,1,2 순서다. native helper2448878은 그 뒤 별도로 실행되어 보이는 모델의 stain 값을 다시 갱신할 수 있다. 하네스는 LR로 reset callback과 후속 stain callback을 구분한다. reset11,136회 각각 캐시NaN과 S0=0/team0..2 순서를 확인했다. 후속 stain setter128회를 따로 기록해 setter fixture 호출은 총11,264회다. setter 구현/GPU upload는 fixture이다.

### 6.2 홀더는 별도 상위 gate와 이전 값 보존 분기가 있다

**[실행: whole14595b0 4,096건]**

- Bde0>0, Bdf0>=1 && Be04>0, Be0c>=1 && Be1c>=1이면 플래그4개를0으로 쓴다.
- **Bd60>0이면 H+62/+63만0으로 쓰고 H+60/+61의 이전 값을 보존한 채 반환한다.** 이를 항상4개 clear나 SM4개 copy로 단순화하지 않는다.
- 생존/표시 gate 및 B a5f4/debug gate를 통과하면 SM4개를 복사하고, 기존 특수1a/f·사람/오징어 동시 표시 해소를 실행한다.
- 인간 상태군91..98/ad/ae/f1/f2에서 both visible이면 보통 squid를 끈다. 단 cur=0 && 직전82..84 예외에서는 human 둘을 끈다. 나머지 상태 both visible도 human을 끈다.

이 항목들은 기존 판독을 실제 whole function으로 검증한 것이며, 생존·타이머·특수 활성의 상위 producer를 실행했다고 하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

기존 `_Hlf` threshold61·Rival type4 제외·같은 프레임 SM/holder 연결을 재사용한다. B7a0가 true면 살아 있는 squid AS 래퍼가 있어도 표시를0으로 만든다. AS 명령을 매 프레임 정지하거나 squid 모델을 없애는 동작으로 바꾸지 않는다. hidden이 풀리면 계속 살아 있는 래퍼의 표시가 다시 켜질 수 있다.

칠 보완 binder의 off reset은 다음 재등장 때 오래된 캐시를 재사용하지 않게 하는 경계다. 파문/잠영 잉크 표면 이펙트·ELink on/off·follow 행렬은 이번 실행에서 확인하지 않았다. 시각 추측으로 이름·크기·밝기를 채우지 않는다. 카메라와 회복의 B7a0 소비자는 기존 근거를 따른다.

## 8. 다른 기능과의 상호작용

StepPaint mode의 원본 채널 샘플·임계·법선 공급은 [player_state §9](../player/player_state.md)와 paint 원본을 따른다. 이 문서는 그 **결과 입력**부터 표시까지 실행했다. 원본 sampler/GPU atlas/Phive 접촉 전체를 닫은 것으로 세지 않는다.

지연된 B7a0와 즉시 swimming은 같은 값이 아니다. 현재 웹의 [impl/physics](../impl/physics.md) 기록은 fastStealth가 없으면 swimming 근사임을 명시하며, renderer PlayerSnap에는 B7a0가 없다. 이동·회복·카메라·표시가 필요에 따라 같은 native 판정 source를 소비하도록 이식해야 한다. 한 소비자에 맞춰 지연을 삭제하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

이 문서는 구현하지 않았으며 [port/ink_visuals](../port/ink_visuals.md)의 GR01/GR02/MOV04 차이를 보강한다.

1. core 플레이어 상태에 원본 대응 hiddenCandidate/hiddenDelay/hiddenAge/hiddenByte를 별도 보존한다. 생성·재시작 초기0/0/9999를 적용한다. 권장 이름은 원본 이름이 아니다.
2. 실제 groundN/originalN·StepPaint.mode·airFrames·모서리 계수·state·force 조건을 producer에 공급한다. 아직 없는 값을 임의 상수로 메우지 않는다.
3. 상태 갱신과 래퍼 틱 뒤 native 순서의 SM 표시 결정, counter reset, off binder reset을 수행한다. 캐시NaN과 material 입력0을 분리한다.
4. 별도 holder gate·이전 플래그 보존·both visible 해소를 적용한다. PlayerSnap에 최종 hidden/표시 정보를 전달하고 draw·파츠·탱크·무기 표시가 같은 판정을 사용하도록 한다.
5. 아래 native trace fixture로 첫 잠영·유지·나오기·재진입·1프레임 후보 깜빡임을 비교한다. 원본 ELink 잠영 파문과 shader 재질은 별도 확인 후 연결한다.

## 10. 검증 코드·실행 결과·기대값

재현 명령: `.venv/Scripts/python web/tools/squid_visibility_r2_emu.py`. 실제 마지막 실행 exit0, PLT0/fault0. 결과 [native_visibility.json](../../../analysis/visual_gap_r2/squid/native_visibility.json).

| 원본 실행 범위 | 사례 | 비교 결과·한계 |
|---|---:|---|
| 기존 생성/재시작 B7a0 필드 write블록 | 512 | 각 hidden0/delay0/age9999. whole constructor/restart 재분석 아님 |
| c250..c2e4 성분 일치 | 4,096 | epsilon 포함/초과 finite4096/4096; NaN/Inf 제외 |
| c5c0..c7dc 지연 tail | 8,192 | hidden/delay/age24,576필드 bit 일치. 이 군은 candidate/w26 입력 fixture |
| c16c..c7dc ordinary 후보·native helper·지연 | 10,800 | candidate/match와 hidden/delay/age 일치. helper/leaf stub0; 원 sampler·유효 특수 분기 밖 |
| 243e2dc whole 표시 함수 | 2,048 |4flags/counter/reset 순서·cacheNaN11,136 확인; invalidrail/CB8=0/4material setter fixture |
| 14595b0 whole 홀더 | 4,096 |16,384flags bit 일치, stub0. 모든 runtime gate 입력은 fixture |
| ordinary producer→whole SM→whole holder 연속 | 272프레임 |4시퀀스 시작/유지/종료/재진입/깜빡임. 하네스 순차 연결; wholeplayer/NVN/GPU 제외 |

기존 entry64 실행은 위 건수에 포함하지 않았다. 10,800건과272프레임은 원본 ordinary producer를 실행하므로 candidate/w26 주입 검증에서 진전했으나, raw GPU 잉크 sample부터 player whole frame까지 확정한 것은 아니다.

실패도 [commands.md](../../../analysis/visual_gap_r2/squid/commands.md)에 보존했다. 첫 기대값은 후속 stain helper의 S0=1 호출을 reset과 합쳐 실패했다. LR로 두 원본 호출 경로를 분리하여 수정했다. 확장 중 들여쓰기1회 오류, PowerShell에서 sh 미등록, Ghidra 미정의 leaf의 func_lookup 선행 함수 반환, wildcard 경로/생략0 상수 KeyError를 각각 기록했다. 원본 코드는 수정하지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 미확정 | 이유·시도·다음 근거 |
|---|---|
| 자기 잉크 실 sample→ordinary 입력 whole | StepPaint mode/법선/air 공급은fixture. 다음: 실제 player_state§9 sampler/ColPaint결과→2483134 whole 연결 |
| wallCharge·유효 rail/vehicle·kind3/warp 등 전체 후보 | 이번 ordinary군은 inactive 특수·param13c60/charge0 입력. 기존 writer판독은 유지. 다음 c2f0..c418 및유효 ActorHandle/provider |
| 재질 setter 실체·GPU upload/캐릭터 최종 shading | setter4개 capture/return만. 실제 S0=0과 캐시NaN은 확인. 다음 SM 생성자 binder vtable·1103270/110513c 재질 소비/프레임 |
| 전체 249648c/슬롯19·실시간 stage 제출 | 원본 세 단계는 하네스순차. 기존 caller판독만. 다음249648c→1459284/243a434 원본 실제 Actor/Scene 연결 |
| 잠영 표면 파문·튀는 잉크·ELink on/off | 모델 hide만으로 FX가 동일해지지 않음. 다음 SquidSwim/Stealth ELink 실제 이벤트와follow/runtime색 공급 |

고정986 inventory의 넓은 슬롯19·실모델/GPU 질문을 이 부분 결과로 전체 확정 승격하지 않는다. 완료율 변경은 parent의 기존 안정ID 전체 질문 감사에 맡긴다.




### 2026-10-03 웹 반영 r8 후속 — 기존 결론 보존

[현재 반영/검증](../port/character_graphics_r8.md), [재질 소비](character_material_r8.md), [표시 공급](character_display_r8.md)를 우선한다. 기존 '이번 작업은 분석만/구현하지 않음'은 해당 회차 기록이다. r8은 실제 네 캐릭터 재질, RGBA 강도, B7a0 지연 숨김/SM/holder, Shtr/Shtr를 웹에 연결했고 전체304/304·typecheck/build·Lby12단계를 검증했다. live 재질/전체 pose·원본 GPU/Phive 동등성을 완료로 승격하지 않는다.
