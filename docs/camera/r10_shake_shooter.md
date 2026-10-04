# 카메라 흔들림 수명과 일반 슈터 발사·명중 — r10

분석일: 2026-10-03. 대상: Splatoon 3 v0, Lby_Lobby00 1인 연습, 스플래시슈터 ID40. 원본 분석 및 MD 반영만 수행했다. 고정 inventory의 질문 2·25·26·27·28을 유지한다. 기존 r5/r8/r9 결과는 재사용으로 구분하며 새 실행 수에 더하지 않는다.

## 1. 기능 개요와 사용자에게 보이는 동작

일반 슈터 발사와 명중에 카메라 흔들림·패드 진동을 무조건 추가하면 원본과 달라진다. [데이터]+[판독] `WeaponShooterNormal` 5개 leaf와 일반 `Shooter` 행이 선택하는 `HitEffect` E1 키에는 `CameraRumbleName`과 `CtrlRumbleName`이 비어 있다. 원본 ELink 시작 함수의 40개 에셋 입력 실행에서도 일반 슈터·표적 에셋은 흔들림/진동을 시작하지 않았다. 이는 렌더/사운드/조준 흔들림 자체의 부재를 뜻하지 않는다. 총구 이펙트·히트마커·탄의 흔들림은 각 경로에 그대로 존재한다.

카메라 흔들림이 시작된 경우 [실행] 곡선은 현재 프레임으로 계산하고 카운터를 증가시킨 뒤, **종료 여부를 다시 검사한 결과만** 최종 카메라 위치에 합산한다. 루프 이벤트의 소유자가 사라지면 즉시 무효화한다. 종료 직전 프레임에 임의의 페이드 보간을 넣지 않는다.

| 고정 질문 | r10 결론/수준 | 전체 상태의 권고 |
|---|---|---|
| 2: BNVIB 디코더·활성 포저 연결 | r5 BNVIB 115개/30,240샘플·r8 포저 연결 재사용. r10 흔들림 수명 4,424개 검사 추가 [실행]+[판독]+[데이터] | 본래 질문은 기존 근거 정정으로 해소. SDK 기기 출력까지 새로 검증했다는 뜻은 아님 |
| 25: 슈터 직접 호출만 보고 진동 없음, 가상 경로 미검증 | 실제 GameRumble42 slot·게임 handle32개 구조·선택된 voice17 slot 및 전체130FFFC576개+arm70/speed20 실행, §8 [실행]+[판독]+[데이터] | ID40 이름 기반 시작과 실제 가상 경로에서 해소 권고. 임의 산술 함수 주소 전면 부재나 SDK 기기 출력 증명으로 확대하지 않음 |
| 26: 이름에 Focused가 있으면 자기 플레이어 시점 전용이라는 추정 | Enum0/1/2, 실제 Switch 조건, 시점 선택→메시지→body→5 user writer 996개 실행 [실행]+[판독]+[데이터] | 해소. 이름의 접미사가 필터는 아니며, 실제 SubjectiveType==0 조건이 현재 선택한 시점 플레이어를 뜻함 |
| 27: 자기 탄 명중 rumble/shake ELink를 못 찾음 | ID40 selector 및 Shooter 17개 셀→HitEffect 15 leaf 전수. 일반 선택 키의 두 이름 공백 [판독]+[데이터] | ID40 일반 표적 명중 범위에서 해소 |
| 28: 발사 직접 진동 없음, 명중 ELink 미확정 | 발사 5 leaf, 표적 10+10 leaf, HitEffect 15 leaf, 원본 admission 40개 [실행]+[판독]+[데이터] | 같은 범위에서 해소. 다른 무기·특수 동작으로 확대하지 않음 |

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 역할 |
|---|---|
| `extracted/exefs/main.reloc.img` | 원본 AArch64 명령 및 재배치된 vtable/주소. 읽기 전용 |
| `extracted/romfs/XLink/ELink2.Product.100.belnk.zs` | 원본 ELink. 없으면 동일 추출 캐시 `analysis/effect_sound/elink2.Product.100.belnk` 사용 |
| [data_audit.json](../../../analysis/camera_100_r10/shake/data_audit.json) | r10에 원본 ELink 재파싱, 원본 uncompressed SHA256, 원본 데이터/콜그래프 전수 기록 |
| [native_emu.json](../../../analysis/camera_100_r10/shake/native_emu.json) | 원본 Unicorn 실행 결과, SDK/캡처 경계 |
| [focused_native.json](../../../analysis/camera_100_r10/shake/focused_native.json), [subjective_selector.c](../../../analysis/camera_100_r10/shake/subjective_selector.c) | 실제 시점 분류 producer 275E99C·메시지 receiver 234F518·5 user property writer 원본 실행/새 디컴파일 |
| [vtable_audit.json](../../../analysis/camera_100_r10/shake/vtable_audit.json), [voice_native.json](../../../analysis/camera_100_r10/shake/voice_native.json) | 실제 GameRumble/handle/선택 voice의 가상 경로·SDK 명칭 확인 및666개 원본 실행 |
| [rumble_vtable.c](../../../analysis/camera_100_r10/shake/rumble_vtable.c), [rumble_voice.c](../../../analysis/camera_100_r10/shake/rumble_voice.c), [rumble_base_slots.c](../../../analysis/camera_100_r10/shake/rumble_base_slots.c) | 새 manager RTTI/명칭·원본 voice pool 생성/선택/가상 메서드·tick·기본 wrapper 디컴파일 |
| [lifetime.c](../../../analysis/decomp/r10_camera_shake/lifetime.c), [update.asm](../../../analysis/camera_100_r10/shake/update.asm), [focused.c](../../../analysis/decomp/r10_camera_shake/focused.c) | 새 디컴파일/원본 명령 |
| [shake_rumble.md](shake_rumble.md) §3·4·7·11 | 기존 Module, BNVIB, r8 Rumble 계산·포저 근거 재사용 |
| [hit_effect_pipeline.md](../combat/hit_effect_pipeline.md) §3·6·10 | r8 request→selector→E1/E2 emitter/Subjective 세대 검사의 기존 실행 근거 |
| `analysis/combat/rsdb/WeaponInfoMain.json`, `analysis/combat/HitEffectConfig.json` | ID40 행, Shooter 셀 원본 데이터 추출 |
| `analysis/combat/r6_hiteffect_emu.json` | ID40 normal/critical 행 선택 원본 실행의 기존 결과 재사용 |

`SHARED.md`, `FUNCS.tsv`, `decomp_index.py`를 먼저 확인했다. 이미 저장된 `r4_model_flags.c`, r8 life/XLink, r5 BNVIB·r8 rumble 결과를 다시 디컴파일/재실행해서 새 성과로 세지 않았다.

## 3. 진입점과 전체 호출 흐름

### 3.1 일반 스플래시슈터 ID40 [판독]+[데이터]

```text
발사 → WeaponShooterNormal ELink leaf 5개 → 137b000
      CameraRumbleName="", CtrlRumbleName="" → 두 start 호출 없음

탄의 hit request → 16d9c60 → 28fed18(category=0, weaponID=40, extraInfo)
      WeaponInfoMain[40].DefaultHitEffectorType=Shooter
      ExtraHitEffectorInfoSet=[] → extraInfo=17(CriticalHit)도 Shooter
      → 27b4704 / 27b7938 / 27b877c → 27b4aa4
      → Shooter___<result>_<context> 셀
      → E1: HitEffective / HitInvalid / HitInvalidKebaInk → HitEffect ELink → 137b000
      → E2: Hit / Splash / SplashWater / HitBlowerInhole → 원본 code emitter 137f558
```

대미지를 받은 일반 표적의 `Shooter___Damaged_Default` E1은 `HitEffective`다. E2는 `Hit`이다. E1 원본 데이터의 두 rumble 이름이 모두 비었다. E2는 같은 ELink 키를 찾는 경로가 아니라 원본 code emitter 경로다. 요청의 owner/target·instance 세대 검사는 기존 r8 전체 consumer 실행 근거를 재사용하며 이번 admission 테스트가 이를 다시 실제 게임에서 검증한 것은 아니다.

### 3.2 흔들림 [판독]+[실행]

```text
ELink 137b000 → CameraRumbleName 비어 있지 않음
 → CameraModule 1010f14(name) : 첫 finished slot 재사용
 → 매 프레임 1010150
 → slot마다 10182e8(currentFrame curve → output → owner → counters)
 → slot마다 1018b4c(isFinished) → 아직 유효한 output 합산
 활성 Spectator/player 포즈 getter → 1017d5c → 27600c8 (기존 r8)
 → Module+0xD4의 입력 pose
 → 위의 shake 갱신/finished 필터 → pose를 Module+0x144로 복사
 → output XYZ를 world position에 직접 더함 → 1017434(logical projection)
```

패드 진동 시작 함수 `130f0b8`는 별도다. camera shake와 BNVIB 파형을 한 상태 객체로 합치지 않는다.

## 4. 구조체·필드·상수·열거형 표

### 4.1 `ShakeInstance` (0x48B) [판독]

| offset | 타입/의미 | writer → reader |
|---|---|---|
| +00 | SafePtr handle 포인터, 0이면 무효 | 1010f14 / 10182e8 owner 실패 → update, loop/finished getter |
| +08 | u32 parameter handle generation | start → `handle+0xC` 비교 |
| +10 | u32 instance serial | start가 Module+128의 현재 값을 저장 → 외부 event handle |
| +14 | s32 frame | start=0, update++, loop reset → curve 및 finished |
| +18 | s32 elapsed | start=0, update++ → frameLimit 검사 |
| +1C/+20/+24 | f32 world-position 가산 출력 XYZ | 10182e8 → 1010150 합산 |
| +28 | f32 gain | start=1, ELink start 조정 → gain×Scale |
| +2C | s32 frameLimit | start=-1, ELink 양수 프레임 지정 → `limit>=1 && elapsed>=limit` |
| +30 | u8 followOwner | start=0, ELink=1 → 루프 소유자 확인 |
| +38 | event owner 포인터 | ELink `entry+0x30` → owner+20 generation |
| +40 | u32 event owner generation | ELink → owner+20 비교 |

parameter object의 Curve/IsLooped/Axis/Scale explicit flag는 각각 `+61/+62/+63/+64`, 값은 Curve +38..48, Axis +50..58, Scale +5C, IsLooped +60이다. explicit flag=0이면 유효한 parent SafePtr `+18/+20`를 따라 값을 찾는다. parent 유효 조건/타입 확인을 원본 함수가 수행한다. 서로 다른 객체의 `+20`은 같은 의미가 아니다.

### 4.2 `SubjectiveType` [실행]+[판독]+[데이터]

`148b2b8`은 원문 `Focused , Friend , Enemy`를 토큰화한다. `148a784`가 각각 숫자 **0/1/2**를 등록한다. 전역 descriptor는 `58c1598`, 등록 list는 `58c1580`, count는 `58c1590`이다.

`26b8934`는 사용자별 property 이름 `SubjectiveType`을 찾고 user+**B8**에 `(propertyIndex<<1)|1`을 기록한다. **이 packed index는 SubjectiveType의 현재 값이 아니다.** 사용자들의 초기 numeric property 배열 user+80은 0으로 채운다. 0 초기값만으로 모든 실제 플레이어가 영구 Focused라고 판단하면 안 된다.

2026-10-03 추가 확정: 실제 현재 값 writer를 연결했다. 기존 캐시 `ui/hud_batch2.c`의 **275DF84**는 선택 시점 번호를 PlayerManager+**D470/D474**에 함께 저장하고, 각 플레이어에게 `6C2B6A01` 메시지를 보낸다. 새 판독 **275E99C**가 payload+44를 다음처럼 만든다. 초기 payload 값은 **2(Enemy)**다.

| 조건 | payload+44 / SubjectiveType |
|---|---|
| 선택 번호가 유효하고, 팀 getter 결과가 -1/3이 아니며 actor+798 플레이어 번호==선택 번호 | 0 Focused |
| 위의 유효 조건에서 번호가 다르지만 actor+668 팀==선택 시점의 팀 | 1 Friend |
| 위의 유효 조건에서 번호·팀 모두 다름 | 2 Enemy |
| 선택 번호 음수 또는 팀 getter 결과 -1/3 | 초기값2를 보존. 번호가 우연히 같더라도 0을 쓰지 않음 |

`275E99C`의 별도 payload+40은 가시성/활성 플래그다. view+391이면0, 아니면 view+280==0에서 번호일치 여부, ==1에서1, 나머지는 직전 body+1054다. **이 플래그와 SubjectiveType 값은 서로 다른 필드**다.

실제 **234F518** 메시지 `6C2B6A01` receiver가 payload+40→body+1054, payload+44→body+**1058** 및 PlayerXLink root+**2F0**로 복사하고 body+F58=1을 세운다. 원본 RTTI도 실행해 이 메시지 타입 검사를 확인했다. root+2F0의 초기값2는 생성 경로 **2439E94**에서 확인했다.

이후 PlayerModel **2515488**의 명령 **251589C..2515960**이 body+1058을 root의 +1D8(PlayerVoice), +200(Player_Focused), +278(PlayerFoot), +2A0(SplPlayer ELink), +2C8(PlayerShotGuide)의 **user+80[0]**에 복사한다. 이전 값과 다를 때만 user+70의 dirty bit0을 OR한다. 다른 property 값과 dirty 상위 비트는 보존한다. 따라서 **현재 선택 시점 번호와 같은 플레이어의 원본 ELink SubjectiveType이 Focused0**이며, `Focused` 이름 접미사는 이 전달 경로를 대신하지 않는다.

원본 실행 972개 연속 producer→receiver→5 user copy 및 음수/알 수 없는 팀24개에서 불일치0, null read0, 원본 코드 patch0. profile의 virtual20/28은 합성 입력이고 virtual28은 원본 Team getter가 해석하는 직접 팀 참조 `D0000001+team`을 반환한다. Team 생성/해석 **146CB20/146D164**는 원본이다. actor+798/668·선택 번호·팀은 이 테스트의 입력이며 Lby_Lobby00 전체 초기화나 메시지 큐의 실제 tick 지연을 실행했다고 주장하지 않는다.

## 5. 상태 전이와 전체 수명

### 5.1 시작과 재사용 [판독]

`1010f14`는 mutex 아래에서 parameter name을 `1012e04`로 조회한다. 없거나 빈 슬롯이 없으면 `(slot=0, serial=0)`을 반환한다. 슬롯 배열은 Module+138, 수는 +130, stride 0x48이다. `1018b4c`가 true인 **첫 슬롯**을 선택한다.

새 SafePtr와 generation을 저장하고 `serial=Module+128`, 그 뒤 Module+128을 증가시킨다. frame/elapsed는 0, gain=1, frameLimit=-1, follow=0을 쓴다. start가 이전 output XYZ·owner pointer/generation까지 전부 0으로 지우지는 않는다. 다음 update가 유효 슬롯의 출력을 덮어쓴다.

### 5.2 유지와 종료 [실행]+[판독]

1. 유효 parameter의 현재 frame으로 XYZ를 계산한다.
2. follow=1인 **루프**일 때 owner==0 또는 owner+20 세대 불일치면 instance+00을 즉시 0으로 만든다.
3. frame++, elapsed++를 수행한다. 무효 슬롯도 카운터는 증가한다.
4. 여전히 유효한 루프이며 `f32(frame)>=MaxX`면 frame=0이다.
5. Module은 update 후 finished를 다시 검사하고 true인 슬롯의 출력을 합산하지 않는다.

비루프에서는 owner 소실만으로 취소하지 않는다. frameLimit은 loop 여부보다 먼저 적용된다. 루프 owner가 만료되었을 때 별도의 loop-fade 기간을 계산하는 명령은 이 경로에 없다.

### 5.3 이전 문서 정정 (2026-10-03)

기존 결론을 지우지 않고 다음 정정을 유지한다.

| 이전 표현 | 정정 근거/결론 |
|---|---|
| `1018998`을 비루프 종료 검사로 설명 | 새 전체 디컴파일+실행: **isLooped**. finished는 **1018b4c**다 |
| `curve * gain * Scale`의 왼쪽 순서 | ASM 10185BC/10185C0/1018614: **curve × (gain × Scale)**. FootPaintEnemy frame1 1 ULP 차이로 확인 |
| 새 serial을 증가시킨 뒤 저장 | 1010F14: 이전 Module+128 값을 slot+10에 저장한 뒤 증가 |
| 마지막 계산 프레임이 그대로 카메라에 표시된다고 해석 | 1010150은 counter 증가 후 finished를 필터. MaxX=15 비루프의 computed frame14는 합산에서 탈락 |
| “자기 탄 명중 rumble 에셋을 찾지 못함” | HitEffect critical 4 leaf의 PresetDoka는 존재. **ID40가 고르는 일반 Shooter 키에는 없다**는 데이터/selector 결론으로 바꿈 |

## 6. 계산식·조건·상세 의사코드

`F`는 각 연산 뒤의 f32 반올림이다. [실행]+[판독]

```text
curveValue = originalLinearOrHermit(F(frame)/MaxX, Curve.Data)
strength   = F(curveValue * F(gain * Scale))
output[k]  = F(Axis[k] * strength)

isLooped(instance):
  invalid SafePtr or wrong generation or null pointee → false
  return effectiveInherited(IsLooped)

isFinished(instance):
  if frameLimit>=1 and elapsed>=frameLimit: return true
  if invalid SafePtr / wrong generation / null pointee: return true
  if effectiveInherited(IsLooped): return false
  return effectiveInherited(Curve.MaxX) <= F(frame)
```

이번 실행은 원본의 Linear/Hermit 9종을 사용한다. `SpinnerShooting`의 Sin은 다른 무기 범위라 신규 실행에서 제외했다. 원본 데이터 값·curve 식 전체는 [shake_rumble.md](shake_rumble.md) §3을 재사용한다.

ELink `137b000`의 CtrlRumble 호출 ABI는 **x0=manager, w1=category, x2=&name, w3=loop, s0=0f**다. 디컴파일 C에 보이는 float와 x0 인자 순서를 그대로 Python x-register 순서로 사용하지 않는다. 원본 ASM `137b4dc..4f4`는 stretch를 **max(stretch,0.01f)**로 클램프한 뒤 역수를 설정한다. 이 설정은 시작된 rumble handle이 있을 때만 수행한다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

### 7.1 원본 ELink 전수 [데이터]

| 사용자/키 | leaf 수 또는 선택 범위 | CameraRumbleName / CtrlRumbleName |
|---|---|---|
| WeaponShooterNormal | 5 | 전부 빈 이름 |
| SighterTarget / SighterTargetBig | 10 / 10 | 전부 빈 이름 |
| HitEffect, 일반 Shooter E1 | HitEffective·HitInvalid·HitInvalidKebaInk | 두 이름 모두 빈 이름 |
| HitEffect, 모든 leaf | 15 | 카메라 이름은 15개 전부 빈 이름 |
| HitCritical / HitCriticalShield | 2 | camera 빈 이름 / PresetDoka.bnvib, gain1, pitch2 |
| HitMiddleCritical / HitMiddleCriticalShield | 2 | camera 빈 이름 / PresetDoka.bnvib, gain0.7, pitch1.8 |

`TargetMarker`의 오래된 `CtrlRumblePattern=10002` 값이 있어도 `137b000`은 유효 이름을 필요로 한다. 이름 대신 그 정수만 보고 진동을 생성하지 않는다. critical 4개 leaf의 발견은 일반 ID40의 critical 행 선택을 변경하지 않는다. 다른 무기의 실제 동작 분석은 수행하지 않았다.

### 7.2 Focused 이름과 실제 조건 [데이터]+[판독]+[실행] — live writer 해소(2026-10-03)

문자열 접미사가 필터의 본체가 아니다. 원본 `SplPlayer` leaf227 `スポナージャンプ移動線_Focused`는 parent58 Switch가 `SubjectiveType`을 감시하고 자식 조건이 `Equal Focused`다. CameraRumbleName은 FuwaStrong, DistanceAttenuate=0이다. 이 범위 밖 동작은 **조건 구조를 확인하는 데이터 예시**로만 사용한다.

범위와 가까운 leaf266 `イカ返しぶつける振動_00`는 이름에 Focused가 없지만 parent98 `イカ返しぶつける振動`의 Switch 조건은 동일하게 `SubjectiveType==Focused`다. FuwaWeak와 PresetDoka.bnvib(gain0.6, pitch0.8)를 가진다. 따라서 이름만 검사하는 웹 규칙은 원본 조건을 놓친다. 실제 해당 벽 충돌 이벤트의 발행 시점/지형에서의 도달성은 이번 자료만으로 추가 확정하지 않는다.

HitEffect의 Subjective producer `27b5430`은 기존 [판독]: owner==PM+D474이면 Focused0, negative owner는 Enemy2, 나머지는 조회한 플레이어 팀에 따라 Friend1/Enemy2다. **PM+D470의 local gate와 D474의 subjective gate는 다른 값**이다. 이를 SplPlayer의 실제 value writer로 대신 제시하지 않는다.

## 8. 다른 기능과의 상호작용

### 8.1 ELink 소유자·지연/루프 [판독]

`137b000`은 external entry가 처음 생성될 때 nonempty CameraRumbleName을 검사해 start한다. 시작 시 거리 gain과 선택적인 양수 frameLimit을 쓰고 follow=1, owner=event entry+30 및 generation=owner+20을 저장한다. 이 함수의 지속 갱신 부분은 Ctrl gain/pitch·거리/이미터 갱신 경로이며 camera gain을 매 프레임 재계산하는 명령은 없다. owner 사라짐은 §5의 루프 취소에 연결된다.

원본 XLink container delay/loop 선택과 실제 게임 tick의 event 발행 순서는 기존 effect_sound XLink 문서의 근거를 사용해야 한다. 이번 테스트의 resource-loop fixture나 파라미터 getter 캡처를 실제 이벤트 전체 수명 실행으로 확대하지 않는다. 흔들림의 거리 기준 위치는 기존 Module의 **흔들림을 적용한 활성 lookAt**이다.

### 8.2 직접/가상 rumble 주소 조사 [판독]

원본 text 0..3E9DF50을 B/BL로 전수 조사하고, 재배치 이미지의 **모든 byte 위치**에서 아래 64비트 주소를 검색했으며, 저장된 ADRP+ADD/LDR 주소 구성 index도 조회했다.

| 시작 주소 | B/BL 호출 위치 | 포인터 모든 위치 / aligned / ADRP |
|---|---|---|
| 130F0B8, controller rumble start | 137B4B4 ELink, 24B17BC UI button, 2DA130C ZLZR UI | 0 / 0 / 0 |
| 1010F14, camera shake start | 137B13C ELink, 25C42B0 Spinner, 275DDFC FootPaintEnemy | 0 / 0 / 0 |

정상 compiled vtable/function-pointer 경로가 이 주소를 직접 보유하지 않는다는 근거다. 기존 “BL 목록에 슈터가 없음”보다 강한 정적 근거지만, runtime 산술로 만들어지는 주소·외부 SDK 내부 진동까지 불가능하다고 증명한 것은 아니다. static absence의 범위와 실제 `137b000` admission의 양성/음성 데이터 조건을 함께 사용한다.

### 8.3 실제 GameRumble·handle·voice 가상 경로 [판독]+[데이터]

`GOT57954C0`은 함수가 아니라 singleton cell582A710의 주소다. 원본 `130E3D8` 생성자는 0x1A0B 객체를 만들고 최종 vtable55783C0을 기록한다. 이 표의 **42 slot**을 읽었다. +18/+20은 RTTI 검사/반환, +C0은 `GameRumble` 명칭이고, +108은 초기화130E5F4, +110은 기존 tick130EE98, +120은 teardown130ED9C다. 기본 slot+28/+58/+B0의 wrapper도 각각 초기화/tick/posttick에 연결한다. controller named start130F0B8 또는 handle start130FE58을 이 vtable에 저장하지 않는다. generic GameBehavior의 optional delegate hook을 임의의 새로운 슈터 시작 호출로 해석하지 않는다.

게임 rumble handle은 **가상 함수가 없는 0x68B 목록 노드32개**다. `130E5F4`가 첫 두 qword를 0으로 만들고 intrusive list 링크로 연결한다. +40은 voice, +48은 그 세대다. 별도의 handle vtable에서 진동을 시작한다는 가설은 이 객체 구조와 맞지 않는다.

```text
130F0B8 named start → 130FE58 (직접 호출130F418 한 곳)
 → 이름으로 원본 BNVIB resource tree lookup, 없으면 voice=0
 → params.kind=0 → 3C7CDF4 (직접 호출130FF68 한 곳)
 → 3C7CED0 pool+18 선택 (직접 호출3C7CE30 한 곳)
 → 3C7AD3C setup (직접 호출3C7CE40 한 곳)
 → 실제 voiceVT5759658 +68=3C7DDA8 원본 byte/length를 SDK Load에 전달
 → 실제 voiceVT+28=3C7B7E4 지연/arm, +30=3C7DD04 loop 지정
 → voice tick3C7B0E8가 +70=3C7DE9C SDK Play
```

`3C7BD8C`의 원본 pool0 생성 block3C7C4BC..5E8은 0xD8B voice의 vtable을 **5759658**에 고정하고 backend+18의 배열에 넣는다. kind1 pool의 다른 vtable도 존재하지만 game named start의 kind0 선택을 바꾸지 않는다. 선택된 표의17 slot에서 delay/loop/speed/stop은 이미 resource가 선택된 voice를 조작한다. 원본 handle/allocator/setup 시작5주소의 전체 B/BL·모든 byte 포인터·ADRP 주소 구성 기록은 [vtable_audit.json](../../../analysis/camera_100_r10/shake/vtable_audit.json)에 보존했다. manager GOT reader8곳, backend GOT reader17곳을 기록했으며 범위 밖 UI의 시작3곳은 식별만 했다.

고정25의 실제 “가상 호출 경로 미확인”은 이 이름 기반 시작 계약·선택된 원본 vtable·일반 ID40 ELink admission으로 해소를 권고한다. 기존의 “모든 가정적인 runtime 산술 함수 포인터의 부재까지 증명해야 함”은 고정 질문보다 넓은 주장이다. 이를 원본의 발견된 경로처럼 만들거나 전체 기기 출력의 부재로 승격하지 않는다.

### 8.4 voice+38은 IsLoop: 정정(2026-10-03) [실행]+[판독]

초기 handle update 판독에서 voice virtual+38을 유효/재생 상태 검사처럼 설명했다. **실제5759658+38=3C7DD28은 SDK `VibrationPlayer::IsLoop`**다. PLT3E9DDD0의 원본 심벌을 확인했다. `IsPlaying`은 별도 +58=3C7DD54→3E9DDE0이며 voice tick에서 사용한다. 기존 r8 gain/pitch 유한 실행 수는 그대로 재사용하되 virtual+38의 합성 true 입력은 **loop=true 조건**이었다고 경계를 정정한다.

전체130FFFC를 실제 vtable로 실행하면 category mute flags 적용과 follow-owner 만료 처리는 **loop일 때만** 진행한다. 비루프는 이 두 분기를 건너뛰며 아래 gain/pitch writes는 계속한다. owner 만료 시 state1/2는 +78의 SDKStop 후6, state3/4는 fade 상태5, state5/6는 재설정하지 않는다. +10 flags의0→nonzero 전환은 state3..5에서 SDKStop, nonzero→0은 SDKPlay에 연결한다. 이 테스트는 이전 flags0 조건이다.

원본 전체130FFFC **576개**(loop2×state6×follow2×owner3×mute2×category4), existing voice arm70개, speed20개가 불일치0/null0/patch0이었다. SDK IsLoop의 입력과 SDKPlay/Stop은 캡처 경계다. 새로운 BNVIB 파형이나 실제 패드의 출력 실행으로 세지 않는다.

## 9. 웹 포팅 구조와 구현 순서

이번 작업은 웹 코드에 적용하지 않았다. 기존 `impl/camera.md`는 읽기만 했다.

1. 일반 슈터 muzzle/target-hit에서 임의의 shake/rumble 추가 여부를 검토한다. 원본 key가 비었으면 이 경로의 카메라 흔들림을 생성하지 않는다.
2. camera shake slot을 event-owner와 독립된 instance로 유지한다. XYZ 합을 활성 pose의 **world position**에 직접 더한다. 원본 Module은 가산 전에 camera quaternion으로 이 벡터를 회전하지 않는다. 쿼터니언이나 조준 spread에 같이 더하지 않는다.
3. `Math.fround(curve * Math.fround(gain * scale))` 및 축별 f32 순서를 보존한다. 곡선 타입/원본 MaxX를 사용한다.
4. currentFrame 계산→loop owner 판정→frame/elapsed 증가→loop reset→finished 필터→합산 순서를 보존한다.
5. start가 첫 finished slot 및 이전 serial을 사용한다는 점을 재현한다. 이전 output/owner 필드를 start에서 임의로 초기화하지 않는다.
6. Focused는 에셋 이름 접미사로 판정하지 않고 ancestor Switch 조건을 평가한다. 현재 선택한 시점 플레이어 번호와 원본 팀/유효 조건으로 0/1/2를 만들고 실제 body+1058→5 user 전달 순서와 dirty bit0 변경 규칙을 재현한다. 가시성 플래그와 분리한다.
7. 패드 진동을 포팅할 경우 actual voice+38을 IsLoop로 사용한다. 비루프 owner에 루프 만료·category flags 분기를 무조건 적용하지 않는다. gain/pitch 갱신과 실제 SDK 출력 경계는 분리한다.

BNVIB 디코더·gain/pitch/거리 limiter 구현은 기존 [shake_rumble.md](shake_rumble.md) §7·11의 확정 식을 먼저 사용한다. controller SDK mixer의 최종 출력은 별도 경계다.

## 10. 검증 코드·실행 결과·기대값

재현 도구: [r10_camera_shake_emu.py](../../tools/r10_camera_shake_emu.py), [r10_camera_shake_data.py](../../tools/r10_camera_shake_data.py), [r10_camera_shake_focused_emu.py](../../tools/r10_camera_shake_focused_emu.py), [r10_camera_shake_vtable.py](../../tools/r10_camera_shake_vtable.py), [r10_camera_shake_voice_emu.py](../../tools/r10_camera_shake_voice_emu.py).

```powershell
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_data.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_emu.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_focused_emu.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_vtable.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_voice_emu.py
```

| 신규 검사 | 검사 수 | 결과 |
|---|---:|---|
| 전체 native isFinished/isLooped 정상·signed frame f32·frameLimit 경계 | 2,925 | 0 불일치 |
| SafePtr absent/stale/null pointee | 3 | 0 불일치 |
| parent explicit/inherit 및 generation 경계 | 32 | 0 불일치 |
| 전체 10182E8, 실제 Linear/Hermit 9종·4 owner 조건 연속 tick | 1,404 | 0 불일치 |
| 전체 1010150의 slot 갱신·finished 필터·두 output 합산 | 20 | 0 불일치 |
| 전체 137B000, WeaponShooterNormal/HitEffect/두 표적 leaf admission | 40 | 0 불일치 |
| 실제275E99C selector→234F518 receiver→251589C의5 user writer | 972 | 0 불일치 |
| Subjective 선택 번호 음수·profile index 음수·팀3 경계 | 24 | 0 불일치 |
| 실제 voiceVT 사용 전체130FFFC loop/mute/follow-owner/category | 576 | 0 불일치 |
| 이미 선택한 voice arm 및 SDKplayer speed writer | 70+20 | 0 불일치 |
| 합계 | **6,086** | **0 불일치, null read 0, 원본 코드 patch 0** |

입력 memory graph는 합성이다. typed parameter factory `100e6b4` 및 IsA와 원본 Linear/Hermit 함수는 실제 실행한다. allocator/mutex/guard는 SDK 경계다. Module 테스트는 active poser 없음, 합성 pose `(1,2,3,quat identity)` 및 renderer projection `1017434` 캡처 조건이며 임의 view 변환 전체 검증이 아니다. 부모 담당 r10 Module 전체/기기 행렬 검사는 별도 결과다.

ELink의 asset parameter getter 38931B8/3892E08/3893040/389331C는 **이번에 읽은 원본 ELink/default 값**을 반환하는 경계다. rumble/shake start는 요청을 캡처하고 null handle을 반환하므로 파형 생성·기기 진동은 실행하지 않았다. no-distance fallback, 원본 형식 resource-loop 메타데이터 fixture 조건을 명시한다. 이 40개 admission은 실제 event dispatch/generation graph 전체 실행을 대신하지 않는다.

Subjective 테스트는 원본 selector 전체와 receiver 전체를 실행한다. 원본 클래스 메모리에 PlayerXLink/PlayerModel/body 포인터를 공급하고, graphics+1368 list를 null로 둔다. 251589C 블록은 x19=PlayerModel부터 실행하며 enclosing2515488의 애니메이션·렌더 전체 실행이 아니다. 프로필 virtual20/28은 선택 index와 직접 Team 참조의 합성 입력이다. 최초에 raw 팀 숫자0을 Team 참조처럼 공급한 시도는 profile virtual30의 미공급으로 PC0 호출이 났고, virtual30을 공급한 후에도 Team sentinel0 경로의 null118 read로 중단했다. 정상 직접 Team 참조 D0000001+team을 입력하도록 fixture를 고친 뒤996개가 null 없이 통과했다. 이 실패를 원본의 정상 플레이 동작으로 해석하지 않는다.

실제 실패도 기록한다: system Python은 zstandard 없음으로 실패해 venv를 사용했다. 최초 독립 식은 곱셈 결합순서를 잘못 써 FootPaintEnemy frame1 gain0.375에서 y `0EB6933B` 대 native `0DB6933B` 1 ULP 차이가 났다. 원본 ASM에 맞춰 `curve*(gain*Scale)`로 정정 후 전부 일치했다. 최초 CtrlRumbleName 캡처는 x3를 이름 포인터로 잘못 읽어 empty였고 x2 ABI로 정정했다. JSON의 NumPy bool은 Python bool로 변환했다. 추가 데이터 도구 첫 실행은 xref 함수 이름 import 오인으로 실패해 실제 `load_idx/refs_to`로 고쳤다. raw disasm의 `250` 위치 인자 및 xref `addr` subcommand 누락도 실패 후 정식 옵션으로 재실행했다. [commands.md](../../../analysis/camera_100_r10/shake/commands.md)에 명령·결과를 보존한다.

기존 재사용 검증: r5 BNVIB 115개 header/30,240 samples, r8 raw pose512, distance1,152·gain/pitch1,152·Limiter32 및 감소7, r6 hit-selector36,900. 이 수는 위 r10 합계에 포함하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 시도/막힌 지점 | 다음에 볼 곳 |
|---|---|---|
| 고정26 이전 미확정 기록 → **해소(2026-10-03)** | 최초 26BA104/generic26BBC60에는 writer가 없어 연결하지 못했다. 이후 cached234F518의6C2B6A01 receiver, cached275DF84 publisher, 새275E99C selector 및 cached2515488의body1058→5user 원본 block996개 실행으로 연결 | 에셋 switch 데이터+실제 값 producer까지 닫힘. 이 근거를 Lby_Lobby00 전체 초기화·큐 지연·벽 충돌 이벤트 도달성의 별도 완료로 확대하지 않음 |
| 고정25 이전 가상 경로 미확인 → **해소 권고(2026-10-03)** | 원본 GameRumble42 slot·handle32개(noVT)·kind0 voice17 slot과 생성/lookup/allocator/setup/arm/SDKPlay 경로를 연결. 실제voiceVT fullhandle576+arm70+speed20 실행으로 IsLoop 의미까지 정정 | ID40 compiled 이름 기반/실제 가상 경로의 근거. 가정적인 모든 runtime 산술 함수 주소의 부재나 원본 전체 기기 출력의 부재는 주장하지 않음 |
| SDK mixer·컨트롤러 실제 출력 | 기존 원본 BNVIB decoder·gain/pitch 실행 성공. 이번 start는 capture | 파형 instance 생성·mixer 최종 NN SDK 출력. camera viewport와 게임 내 rumble 요청 근거와 구분 |
| 실제 ELink delay와 event 전체 수명 | 원본 137B000과 owner cancellation은 확인. 합성 resource-loop/asset getter fixture, 실제 event dispatcher는 실행하지 않음 | effect_sound 원본 XLink delay·container scheduler와 Player event producer의 동일 tick 연결 |

이 남은 범위를 확정된 slot 계산이나 이름 조건으로 채우지 않는다. 고정 질문의 분모를 줄이지 않고 부분 결과는 부분으로 유지한다.
