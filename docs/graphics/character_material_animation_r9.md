# 캐릭터 재질 애니메이션·오징어 눈 패턴·몸 잉크 공급 — r9

2026-10-03 · Splatoon 3 v0, Lby_Lobby00 1인 연습. 원본 곡선·원본 데이터와 웹의 실제 공급 경계를 구분한다. 기존 r2/r8의 잠영 표시 실행을 이번 신규 실행 건수에 더하지 않는다.

## 1. 기능 개요와 사용자에게 보이는 동작

**[데이터]** 오징어 `Sqd_Wait`와 `Sqd_Surprise`에는 ASB type11 재질 잎이 있다. 이 잎은 눈의 색·노멀·거칠기 텍스처 패턴과 `tex_mtx0` 원시 SRT 채널을 공급한다. 눈의 형태와 광택이 뼈 포즈만 바꿨을 때와 달라지는 경로다.

**[실행]** 실제 선택 FMAA 곡선을 원본 `088e380`/`088e4b0`로 1,212회 실행했으며, 웹의 f32 계산과 모든 출력 비트가 일치했다. 초기화된 피부색 홀더 `14522b0`의 범위 검사·프레임 기록·갱신 호출을 67회 확인했다. 이는 원본 전체 ASB·렌더러나 Switch GPU 픽셀 일치를 뜻하지 않는다.

**[미확정]** 몸 잉크 세기는 type11 변신 잎의 즉시값이 아니다. 현재 core에는 원본 `B+cb8` 몸 잉크 입력이 없다. `swimming`, 오징어 상태 또는 변신 비율을 CP 세기로 대체하지 않았다. 실제 피부색 선택값과 비항등 SRT→Mat 행렬도 이번에 완전히 닫히지 않았다.

**2026-10-03 r9 추가 정정 [실행]:** 위 “비항등 SRT→Mat” 미확정 중 Maya·회전0의 출력6lane은 이후 원본313건 실행으로 확정했다. 당시 조사 경로와 남은 전체 upload·다른 회전/모드는 보존한다. [character_texsrt_r9](character_texsrt_r9.md)를 참조한다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치·확정 수준 |
|---|---|
| ARM 원본 | `extracted/exefs/main.reloc.img`, BASE `0x7100000000`, SHA256 `39a8c94826d84b6106f112f2db16f7b2e2743bc6afd72054534a7708a9848a41` |
| 실제 FRES | `extracted/romfs/Model/Player00.bfres.zs`, `Player_Squid.bfres.zs`, `Player00_Hlf.bfres.zs` [데이터] |
| 원시 추출 | [material_channels.proposed.json](../../../analysis/port_graphics_r9/material_anim/material_channels.proposed.json), 각 압축·해제 SHA256 포함 |
| 추출 도구 | [material_animation_r9_extract.py](../../tools/material_animation_r9_extract.py), 기존 BfresLibrary/Dump를 데이터 reader로 사용 |
| 원본 실행 | [material_animation_r9_emu.py](../../tools/material_animation_r9_emu.py), [native_summary.json](../../../analysis/port_graphics_r9/material_anim/native_summary.json) |
| 웹 fixture | [원시 채널](../../games/splatoon3/tests/fixtures/material_animation_r9_channels.json), [원본 실행 출력](../../games/splatoon3/tests/fixtures/material_animation_r9_native.json) |
| 신규 SDK 조사 | [material_sdk.c](../../../analysis/port_graphics_r9/material_anim/material_sdk.c), [material_curve.c](../../../analysis/port_graphics_r9/material_anim/material_curve.c), [material_apply.c](../../../analysis/port_graphics_r9/material_anim/material_apply.c) |
| 원본 generic reader C | [native_curve_readers.c](../../../analysis/port_graphics_r9/material_anim/native_curve_readers.c), `088e380`/`088e4b0` [판독] |
| 명령·실패 | [commands.md](../../../analysis/port_graphics_r9/material_anim/commands.md) |

SHARED/FUNCS 및 `decomp_index.py --no-build`를 먼저 확인했다. `243e2dc`, `2448878`, `10ff640`, `1103270`, `110513c`, `14522b0`, `36751a4`는 기존 C·판독을 재사용했다. 이번 선택 파일의 실제 Switch 재질 애니메이션 signature는 **FMAA**다. FSHU/FSMA라는 일반 명칭으로 실제 블록 형식을 바꾸어 기록하지 않는다.

## 3. 진입점과 전체 호출 흐름

```text
기존 원본 ASB 선택 → type11 잎 이름/시간
  실제 Player_Squid FMAA Sqd_Wait / Sqd_Surprise
  원시 frame/key/type/scale/offset → generic curve reader 088e380 또는 088e4b0
  이번 웹: materialClipInfo → Wrapper의 type11 프레임 정보
          sampleOrdinaryMaterialLeaves → byte-offset parameter patch / texture-name patch
          bindMaterialChannels → 실제 MeshStandardMaterial와 Hoian hUV0

몸 잉크의 별도 기존 경로:
  슬롯19 B+cb8 writer → SM243e2dc 부호/팀 선택
  → 2448878 표시 모델별 binder → VT555fcd0+10 = 10ff640
  → 1103270 → 110513c 원본 CompPaint 재질 쓰기

피부색의 별도 기존 경로:
  플레이어 정보+844 → 초기화24719d4의24743d4 부근 → 홀더14522b0
  → Color_Skin의 정지 프레임/재질 갱신
```

**[판독: 기존]** 몸 잉크·피부색 경로는 [player_assembly §5.2](player_assembly.md#52-재질-애니로-고르는-외형-데이터), [ink_visual_path](ink_visual_path.md), [squid_ink_visibility_r2](squid_ink_visibility_r2.md)를 재사용한다.

**[미확정]** 신규 SDK 조사 `3673fd0→089e488/089e5c4`와 `0891688`에서 float reader 호출 및 weight-buffer 쓰기를 찾았으나, 이것을 FMAA type11의 전체 typed 재질 적용 경로로 확정하지 않는다. 특히 `089e5c4`는 첫 값에 `1−후속값의 합`을 쓰는 구조다. 주소가 근처라는 이유만으로 TexSrt writer라고 명명하지 않는다.

## 4. 구조체·필드·상수·열거형 표

아래 descriptor 기준은 원본 generic curve 객체다. 파일 FMAA 헤더와 서로 다른 객체다.

| 오프셋/값 | 타입·의미 | writer → reader |
|---|---|---|
| curve+0/+8 | frame/key 데이터 포인터 | 실제 raw frame/key 추출 → 원본 reader |
| +10/+12 | u16 flags/key 수 | 원본 descriptor → 검색·평가 함수 |
| +14 | u32 target byte offset | 실제 curve Target → parameter patch의 원시 위치 |
| +18/+1c | f32 시작/끝 프레임 | descriptor → Clamp 경계 |
| +20/+24 | f32 scale/offset 또는 int offset union | descriptor → 전체 다항식 후처리/StepInt |
| +28 | delta union | 이번 Clamp 표본에 wrap delta를 사용하는 경우 없음 |
| flags bits0..1/2..3/4..6 | frame type/key type/curve type | Single·Decimal10x5·Byte / Single·Int16·SByte / Cubic·Linear·StepInt |
| TexSrt byte0/4/8/c/10/14 | mode/scaleX/scaleY/rotation/translateX/translateY | raw FMAA patch → `patchTexSrt`; 행렬은 별도 |
| skin holder+38 | s32 선택 피부색 번호 | `14522b0` 범위 안에서만 기록 |
| skin anim+1c | f32 정지 프레임 | `14522b0` → 애니 적용·모델 갱신 호출 |
| B+cb8 | f32 부호를 가진 몸 잉크 세기 | 슬롯19 → SM/binder; 웹 입력 미공급 |
| binder+8/c/10 | 팀별 세기 캐시 | 표시 off에서 NaN reset → 다음 setter 비교; 실제 GPU uniform과 동일 객체 아님 |

**[데이터]** raw StepInt `offset`은 reader dump에서 int 비트를 float로 표시할 수 있다. `Sqd_Surprise` `_r0`의 실제 offsetInt=9를 `1.3e-44` float 표시에서 정수0으로 바꾸면 잘못된 텍스처를 선택한다. 추출 도구는 offsetInt를 별도로 보존한다.

## 5. 상태 전이와 전체 수명

**[데이터]** 사람 ASB의 실제 type11 잎은 Emote 계열 두 개이며, 일반 `ToSquid`/`ToHuman`의 type11 잎은 없다. 원시 Player00 FMAA `ToHuman` 클립 자체는 존재하지만 눈·눈꺼풀 채널이다. 파일에 클립이 존재한다는 사실을 일반 ASB의 활성 잎으로 승격하지 않는다.

오징어 ASB에는 `Sqd_Surprise`, `Sqd_Wait`, Injection 계열과 직접 BB 이름 선택이 있다. 이번 일반 runtime 채널 bank는 실제 채널이 있는 `Sqd_Wait`, `Sqd_Surprise`, `Sqd_Blink`를 포함한다. Injection의 기존 bake에는 빈 자료가 있으며, 직접 BB 이름·특수 상태 전체 재질 처리는 완료로 세지 않는다.

웹 binder는 한 개의 full-weight type11 잎만 실행한다. 잎 없음은 이전 재질을 유지한다. 다중·가중 잎, 누락 클립/텍스처, 비유한 시간 또는 미지원 curve 모드는 진단하고 기존 값 보존한다. 원본 material blend 식을 일반 lerp로 대신하지 않는다. `dispose`는 자신의 hook·재질 슬롯을 복원하며 resolver가 소유한 텍스처를 파괴하지 않는다. 늦게 끝난 async load는 해제된 binding에 기록하지 않는다.

**[실행: 초기화된 홀더만]** `14522b0`는 `0≤signed idx<FrameCount`인 경우만 새 idx와 f32 프레임을 쓴다. 범위 밖은 기존 프레임을 유지한다. 이 실행에서는 이미 생성된 애니 객체를 공급했고, 첫 생성/실제 세이브/머리카락·눈썹 갱신은 실행하지 않았다.

## 6. 계산식·조건·상세 의사코드

**[실행]+[판독]** Clamp curve의 각 연산은 f32다. Cubic·Linear의 명령은 FMUL/FADD이며 FMA로 합치지 않는다. `F(x)=f32(x)`로 두면:

```text
frame = F(clamp(F(input), F(start), F(end)))
k = 마지막 keyFrame[k] ≤ frame인 구간
t = F(F(frame − F(keyFrame[k])) * F(1 / F(nextFrame − keyFrame[k])))
Cubic  value = F(F(F(k0) + F(t*F(k1))) + F(t*F(t*F(F(k2)+F(t*F(k3))))))
Linear value = F(F(k0) + F(t*F(k1)))
마지막 key에서는 value=F(k0)
float output = F(F(value*F(scale)) + F(offset))
StepInt output = s32(key0 + offsetInt)
```

나눗셈으로 t를 바로 구하지 않는다. **역수를 f32로 반올림한 뒤 곱한다.** scale=0을 scale=1로 보정하지 않는다. 실제 raw 곡선 키·분수 시간·구간 중간·key 경계·end 뒤 표본이 1,212개 원본 출력과 일치했다.

**[데이터]+[실행]** `Sqd_Surprise` frame3은 `_a0=M_Eye_Alb.3`, `_n0=M_Eye_Nrm.3`, `_r0=M_Eye_Rgh.3`를 선택한다. `tex_mtx0` mode는 Maya0, rotation0이며, scale·translation은 실제 Cubic 곡선이다. `Sqd_Wait`의 같은 SRT 채널은 scale(1,1), rotation0, translation(0,0)이다. 비항등 SRT를 그대로 ThreeTexture.matrix 규약으로 바꾸는 식은 공급하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

**[데이터]** 원본 raw 재질 애니메이션 수는 Player00 644, Player_Squid 15, Player00_Hlf 1이다. 이번 bank에는 human6/squid3/hlf1 선택 클립의 실제 raw 채널과 기준 재질을 담았다. 원본 전체 660클립의 runtime 적용 완료가 아니다.

기존 `data/anim_material.json`은 정수 프레임 bake다. 이번 native 식의 분수 시간 재현에는 raw key/scale/offset을 보존하는 bank가 필요하다. 오징어 패턴 12개(Alb/Nrm/Rgh 각각0~3)는 모두 기존 catalog의 `tex/squid` 에셋에 이미 있다. 원본 텍스처 이름·실제 재질 이름으로 결합하며, 사람·오징어 `M_Eye`를 같은 전역 이름으로 합치지 않는다.

웹의 Alb/Normal 패턴은 현재 Three 재질의 같은 슬롯을 교체하며 UV는 Hoian `hUV0`를 읽는다. Roughness 패턴은 원본 단일 채널 R을 별도 live sampler로 읽는다. 기존 glTF 변환의 roughness→G/metallic→B 합성 텍스처와 혼동하지 않는다. 이 연결은 실제 재질 공급이며, 원본 normal decode·모든 shader 픽셀 일치까지 추가 확정한 것은 아니다.

몸·얼굴 static CP=0과 `_Hlf` M_Body CP=.03은 서로 다르다. 이번 작업은 `_Hlf`의 실제 static 값을0으로 통일하지 않았다. `_Hlf`의 비영 CP readiness 경계는 기존 character material 진단으로 남는다. 이 문서에서 이펙트·소리·카메라의 새 공급을 주장하지 않는다.

## 8. 다른 기능과의 상호작용

잠영의 hidden/모델 전환과 몸 잉크 세기·눈 패턴은 별도 수명이다. hidden 시 래퍼 진행을 끊거나 wrapper를 stop하지 않는다. 실제 모델 표시와 binder cache reset은 [character_display_r8](character_display_r8.md)에 기록되어 있다. 숨김 중 mesh pose·GPU 재질 갱신 전체를 이번 curve test 통과로 검증했다고 주장하지 않는다.

기존 피부색 초기화 reader는 플레이어 정보+844를 읽는다. 기존 세이브 커스텀 구획 ctor의 SkinColor/EyeColor 0은 [player_assembly §5.2](player_assembly.md#52-재질-애니로-고르는-외형-데이터)에 이미 판독되어 있다. 그 값이 현재 Lby 플레이어의 +844/+848로 공급되는 전체 경로·실제 선택값을 이번에 확보한 것은 아니므로, 웹 피부 프레임0을 원본 현재 캐릭터의 값이라고 만들지 않는다.

## 9. 웹 포팅 구조와 구현 순서

| 책임 | 실제 새 모듈/API |
|---|---|
| raw curves/패치 | [material_channels.ts](../../games/splatoon3/client/render/anim/material_channels.ts): `sampleNativeMaterialCurve`, `sampleMaterialClip`, `sampleOrdinaryMaterialLeaves` |
| type11 frame 정보 | `materialClipInfo(group,name)` → `{frames,loop}` 또는 null. FSKA 정보와 구분 |
| 실제 재질 공급 | [material_binding.ts](../../games/splatoon3/client/render/anim/material_binding.ts): `bindMaterialChannels(targets,group,consume?)` |
| typed SRT | `patchTexSrt(base,offsets)`. 원본 packed8 Mat row 공급은 별도 `setHoianTexMatrix` API |
| 피부 index reader | `nativeSkinIndex(previous,index,frameCount)`; 실제 upstream index는 별도 입력 |

`MaterialChannelTarget`은 `{material,fres,tex}`다. binder의 `ready`를 재질 준비에 포함하고, 실제 해당 모델 래퍼 잎을 `apply(leaves)`로 전달한다. native bank 없으면 기존 자료의 정수 frame bake를 원본 fractional 채널이라고 명명하지 않는다. `consume(target,name,offsets)` 콜백은 typed GPU 소비자가 실제 처리한 경우만 true를 반환한다. 미연결 SRT/scalar/color는 `stats.unsupported`에 남는다.

눈 패턴 연결과 body CP 입력 연결을 독립 변경으로 취급한다. 이번 모듈은 `swimming`을 입력으로 받지 않으며 CP 세기를 만들지 않는다. 부모 통합의 실제 변경·브라우저 검증은 해당 root 명령 기록과 포팅 상태 표에서 별도 집계한다.

**2026-10-03 실제 웹 통합:** `player.ts`가 native raw bank의 모델별 group을 binding하고, `slot.ts`의 type11 frame 정보에 `materialClipInfo`를 연결한다. typed consumer는 raw TexSrt를 `patchTexSrt`→`setHoianMaterialTexSrt`로 공급한다. Maya·회전0은 [신규 converter 실행 근거](character_texsrt_r9.md)로 지원되고, 다른 mode/회전·scalar/color·몸 CP는 미지원 진단을 유지한다.

## 10. 검증 코드·실행 결과·기대값

| 검증 | 실제 결과·범위 |
|---|---|
| `.venv/Scripts/python.exe web/tools/material_animation_r9_extract.py` | .NET build 0경고/0오류, 실제 raw 선택10클립·기준 재질 추출. 원본/웹 에셋 write 없음 |
| `.venv/Scripts/python.exe web/tools/material_animation_r9_emu.py` | generic curve1,212 + initialized skin67, fault0/PLT stub0 |
| `node --test …/material_animation.test.mjs …/material_binding.test.mjs` | **8/8 PASS**. 원본 curve 비트/skin bounds, 실제 raw texture 선택·실제 Three material 슬롯/UV hook, missing·weighted·dispose·typed callback 경계 |
| `npm run typecheck` (`C:/dev/splatoon3/web`) | PASS. 전체 게임 타입 검사이며 native/GPU 실행 검증 아님 |
| 부모 실제 Lby [browser_verification.json](../../../analysis/port_graphics_r9/browser_verification.json) | 12phase/87display trace/PASS, page error0/GL0. drySquid60에서 실제 `Sqd_Wait` type11 frame49 weight1에 적용35. loaded squid의 제어된 `Sqd_Surprise` frame3은 적용36/세 패턴공급3/rawSrtUnbound=false/UV matrix verified=true. 자연스러운 Surprise state trigger·가중혼합 검증 아님 |

curve 수학은 스텁 없이 원본으로 실행했다. 피부 홀더에서는 `1262c18`, `3673874`, `3674288`, `3673fd0` 네 apply/update callback을 capture로 대체하고 순서 `anim_apply→model_flags→model_material→model_skeletal`를 확인했다. 생성된 FMAA/모델 handle은 합성이다. 피부 raw 채널의 실제 GPU 적용은 실행하지 않았다.

binding 검사는 실제 Three 클래스에 sampler/slot/hook을 공급하는 합성 검사다. Switch GPU·게임 전체 실시간 프레임이 아니다. 전체 테스트·actual Lby 브라우저 실행은 부모가 별도로 수행한다. 실패한 명령과 SDK 탐색에서 미해소한 지점은 [commands.md](../../../analysis/port_graphics_r9/material_anim/commands.md)에 보존한다.

부모의 최초 브라우저 coverage에서는 dry20의 `Sqd_Wait` type11 weight=.92와 `Sqd_ToSquid` type3 weight=.08이었고, 지원조건에 도달하지 않아 적용0이었다. 원본 type11 혼합식을 추측해 가중치를 합치지 않고, 실제 dry60에서 weight1까지 진행해 지원 경로를 검증했다. weighted unsupported 기록은 제거하지 않는다. 최초 한 번 squid hidden 이전 draw coverage가 부족해 7candidate compile assertion도 실패했고, 다음 실행에서 실제7개 모두 ready/compiled/ordinaryConsumer를 확인했다.

**부모 추가 연결 검증(2026-10-03):** actual controlled `Sqd_Surprise` frame3의 원본 curve7개와 native Maya callback1회를 별도로 실행해 텍스처3개 선택과 실제 웹 UV6lane의 일치를 확인했다. [controlled_surprise_native.json](../../../analysis/port_graphics_r9/controlled_surprise_native.json). generic1,212/SRT313 표본에 없는 입력이며 정상 state trigger·가중 mixing·전체 typed apply/upload/GPU를 확정한 결과는 아니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 남은 이유·시도·다음 근거 |
|---|---|
| 몸 잉크 B+cb8 실제 공급 | 기존 슬롯19 writer와 SM/binder 판독은 있으나 current core에 대응 입력 없음. 상태·swimming 즉시값 금지. 다음: 슬롯19 param24의 `c9xx..cexx`, `248cf7c` write와 HP/변신/예산 branch, 실제 PlayerBehavior capture |
| 비항등 TexSrt→Mat | 첫 조사에서는 SDK 주변 `3673fd0`, `089e488/5c4`, `08a1c74`까지 읽고 writer를 확정하지 못했다. **2026-10-03 정정 [실행]:** callback 설치088f308→088efb0→Maya088f3d0 발견, 실제SDK 데이터로 Maya·회전0·출력6lane313건 비트 일치. [상세 원본·지원 경계](character_texsrt_r9.md). nonzero/다른mode/전체Mat upload는 여전히 미확정 |
| 피부/눈색 현재 선택 입력 | index bounds/원시 Color_Skin9/기존 save field ctor0은 확보. 현재 연습 플레이어 info+844/+848 source 미연결. 다음: custom save→PlayerInfo 복사 caller·실제 선택 설정 |
| native multi-leaf material blend | ASB weight는 전달되나 typed material mixing 규칙 미해소. raw 단일 leaf만 지원; 여러 개나 weight≠1은 기존 값 보존 |
| 전체 type11 적용/특수 클립 | 실제 ordinary squid 두 클립 우선. 사람 Emote template, Injection/직접BB 이름, 첫 init·hair/eyebrow 갱신 및 전체 SDK 적용 미검증 |
| 원본 normal decode/GPU 픽셀 | 같은 Three normal 슬롯·UV 공급까지 검사. 전체 native normal packing·shader·텍스처 압축 및 최종 픽셀 일치는 별도 원본 shader/GPU 근거 필요 |

이번 신규 근거를 기존 전체 캐릭터·CompPaint·그래픽 inventory 항목의 전체 완료로 승격하지 않는다. 고정 분모와 포팅 상태 집계는 부모가 유지한다.
