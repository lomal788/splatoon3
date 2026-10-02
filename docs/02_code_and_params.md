# 02. 코드 구조와 파라미터 리플렉션

main NSO의 상태(심볼 유무), 데이터 → 코드로 가는 경로 두 가지(파라미터 리플렉션, 클래스 이름 → vtable), 그리고 그 판독 도구를 정리합니다.

주소는 모두 main을 0x7100000000에 올렸을 때의 가상 주소입니다.

## 1. main NSO [데이터]

| 항목 | 값 |
|---|---|
| 세그먼트 | text 0x7100000000+0x3e9df50, rodata 0x7103e9e000+0x14e9ae4, data 0x7105388000+0x432cb0, bss ~0x71059acfa8 |
| 동적 심볼 | 1,147개 중 정의된 것 39개(`nnMain`, `malloc` 등 SDK 진입점뿐) |
| RTTI | Itanium typeinfo 이름 4,457개. 전부 `nn`, `grpc`, Havok(`hk*`), `pead` 같은 라이브러리. **게임 클래스(`spl::`, `game::`)의 typeinfo는 없음** |
| 재배치 | RELATIVE 416,736, ABS64 7,124, JUMP_SLOT 1,031, GLOB_DAT 52 |

게임 코드는 이름이 전혀 없습니다. 대신 아래 두 경로로 데이터 이름에서 코드 위치를 찾을 수 있습니다.

## 2. 파라미터 리플렉션 [판독]

GameParameterTable의 `$type` 하나(예: `spl__BulletSimpleMoveParam`)는 코드의 구조체 하나에 대응합니다. 이 구조체마다 다음 두 함수가 있습니다.

### 2.1 방문 함수 (visitor)

필드마다 같은 모양의 블록을 반복합니다. `spl::BulletSimpleMoveParam` 방문 함수 @ `0x710153bee0`의 첫 블록:

```
add  x8, x0, #0x54            ; 필드 주소 = this + 0x54
add  x9, x23, #0x10           ; 타입 디스크립터 (x23 = [GOT 0x7105790320] = 0x710553d320 → f32)
stp  x9, x8, [x29,#-0x10]
add  x8, x20, #0x58           ; "값이 설정됨" 플래그 바이트 = this + 0x58 + 필드 순번
str  wzr, [sp,#0x20]          ; 필드 순번 0
adrp/add x9, "SpawnSpeed"     ; 필드 이름
...
blr  [[x19]]                  ; 방문자 콜백 호출, 1이 아니면 중단
```

여기서 필드 이름·오프셋·타입·순번을 모두 읽을 수 있습니다. 타입 디스크립터는 다음 셋을 확인했습니다.

| 디스크립터 | 타입 | 근거 |
|---|---|---|
| `0x710553d320` | f32 | 데이터 값이 실수인 필드(SpawnSpeed 등) 779개 |
| `0x710553d550` | s32 | `*Frame` 필드 등 474개 |
| `0x710553dfb8` | bool | `GuideYMinusZero`, `DamageLinear` 등 34개 |

배열·하위 구조체·열거형·커브·벡터 필드는 디스크립터가 다르거나 이 패턴을 따르지 않아 도구가 `None`으로 남깁니다 **[미확정]**.

### 2.2 생성자 (기본값)

방문 함수 주소가 들어 있는 vtable을 찾고, 그 vtable을 `this`에 저장하는 함수가 생성자(팩토리)입니다. 생성자는 상수를 필드에 직접 씁니다. `spl::BulletSimpleMoveParam` 팩토리 @ `0x710153bdd4` (vtable `0x710558f228`, 객체 0x68 바이트):

```
str  x8(=0x3d8f5c29_3eb851ec), [x0,#0x30]   ; +0x30 BrakeAirResist 0.36, +0x34 BrakeGravity 0.07
str  w8(=4), [x0,#0x38]                     ; +0x38 BrakeToFreeStateFrame 4
stur x8(=0xbe19999a_3e7126e9), [x0,#0x3c]   ; +0x3c BrakeToFreeVelocityXZ 0.2355, +0x40 BrakeToFreeVelocityY -0.15
stur x8(=0x3c83126f_3ca3d70a), [x0,#0x44]   ; +0x44 FreeAirResist 0.02, +0x48 FreeGravity 0.016
stur x8(=0x0000000a_41200000), [x0,#0x4c]   ; +0x4c GoStraightStateEndMaxSpeed 10.0, +0x50 GoStraightToBrakeStateFrame 10
str  w8(=0x40000000), [x0,#0x54]            ; +0x54 SpawnSpeed 2.0
str  xzr, [x0,#0x58]; strh wzr, [x0,#0x60]  ; 설정됨 플래그 10바이트 0
```

### 2.3 자동 판독 도구

- `web/tools/param_reflect.py <필드명...>`: 필드 이름들의 참조가 가장 많이 모인 함수를 방문 함수로 보고 필드 표를 만든 뒤, vtable → 생성자를 찾아 상수 추적으로 기본값을 읽습니다.
- `web/tools/param_reflect_batch.py <접두어...>`: `analysis/param_types_in_data.json`의 타입 중 접두어에 맞는 것을 모두 처리해 `analysis/param_reflect/<타입>.json`에 저장합니다. 데이터에 필드가 하나라도 있는 154종을 처리했습니다(`analysis/param_reflect_batch.log`).

결과 JSON의 `classes[]`는 같은 방문 함수를 쓰는 vtable마다 하나씩입니다. 같은 파라미터 구조체가 다른 객체 안에 박혀 생성되는 경우(예: BulletSimpleMoveParam의 두 번째 vtable `0x71056564b0`, 생성 함수 `0x71028f003c`)는 생성자에서 값을 다른 경로로 쓰기 때문에 `unwritten`이 나옵니다. 이 값은 이번에 쓰지 않았습니다.

**알려진 한계** ([gimmick/stage_gimmicks.md](gimmick/stage_gimmicks.md) §9에서 보고):
- 커브 같은 비기본 타입 필드 뒤에서는 오프셋 대응이 꼬일 수 있습니다. 해당 구조체는 방문 함수를 직접 읽어 확인하세요.
- 열거형 필드가 bool 디스크립터처럼 보일 수 있습니다(디스크립터만으로 타입을 단정하지 말 것).
- "설정됨 플래그" 번호는 구조체마다 기준이 달라서, 다른 구조체의 같은 플래그 오프셋을 같은 필드로 보면 안 됩니다. 항상 기준 객체를 명시하세요.

**검증 범위**: 상수 추적은 직선 코드의 mov/movk/fmov/str만 따라갑니다. 분기나 함수 호출 뒤에 쓰는 값은 놓칠 수 있습니다. 슈터 관련 타입은 생성자 디스어셈블을 직접 읽어 도구 출력과 맞춰 봤습니다([shooter_bullet.md](weapon/shooter_bullet.md) §4).

## 3. 클래스 이름 → vtable [판독]

Behavior 컴포넌트의 `ClassName`(예: `spl::BulletShooterBase`)과 같은 문자열을 main에서 찾으면, 그 문자열 주소를 반환만 하는 3명령짜리 함수가 하나 나옵니다(`adrp; add x0; ret`). 이 함수 포인터가 들어 있는 테이블이 그 클래스의 메인 vtable이고, 이 함수는 항상 **슬롯 2**(getName)입니다. 바로 다음 함수(`mov w0, #크기; ret`, 슬롯 4)가 객체 크기를 반환합니다.

`web/tools/class_info.py <클래스명...> --diff`로 여러 클래스의 vtable을 나란히 비교할 수 있습니다.

| 클래스 | vtable | 슬롯 | 객체 크기 | 생성 함수 |
|---|---|---|---|---|
| `spl::BulletSimple` | `0x71055a59a8` | 81 | — | `0x7101766d10` |
| `spl::BulletShooterBase` | `0x71055a5030` | 109 | 0x1230 | `0x710174e644` |
| `spl::BulletShooterSakePillar` | `0x71055a5420` | 109 | — | `0x710175657c` |
| `spl::BulletSplashShooter` | `0x71055af4c8` | 108 | — | `0x71018117dc` |

`BulletShooterBase`와 `BulletSimple`의 0~80번 슬롯은 대부분 같아서 같은 탄 기반 클래스를 상속한 것으로 보입니다 **[추정 — vtable 공유]**.

## 4. 열거형 이름 문자열 [데이터]

`spl::<열거형>` 이름 바로 뒤에 `값0 , 값1 , ...` 형식의 문자열이 이어서 저장됩니다. 예: `spl::BulletMoveState` → `GoStraight , Brake , Free` (`0x71048a26dc`). 문자열 순서가 곧 정수 값입니다. sead 열거형 분할 함수 `0x710127856c`로 확인했습니다 **[판독]** ([network/network.md](network/network.md)).

## 5. 공통 규칙

### 5.1 기어 Low/Mid/High 보간 [실행(에뮬)+판독]

기어 효과는 모두 같은 식입니다. 플레이어 이동 속도(`0x710265df40` 등)와 스페셜 증가량(`0x7102663808`)에서 각각 확인했습니다.

```
AP = min(mainAP[id] + subAP[id], 57)          // 능력 id별 AP 배열, 집계 0x710265ca78
p  = clamp01(AP·(3.3 − 0.027·AP) / 100)
s  = (Mid − Low) / (High − Low)
k  = |s − 0.5| ≤ 0.001 ? p : |p|^(−log2 s)    // = p^(log s / log 0.5)
값 = Low + (High − Low)·k
```

원본 함수 3개를 unicorn으로 실행한 값과 재구현이 731건 비트 단위로 일치합니다([player/gear_skills.md](player/gear_skills.md)). 기어 개수에서 AP 배열을 만드는 집계(`0x710265ca78`)는 일부만 판독했습니다 **[미확정]**.

### 5.2 bss 상수

플레이어 관련 상수 상당수는 rodata가 아니라 bss에 있고, 정적 초기화 함수가 실행 중에 채웁니다. 디컴파일에서 `DAT_71059…` 값이 0으로 보이면 이 경우입니다. 정적 초기화 8,057개를 에뮬로 실행해 2,530개 값을 뽑아 두었습니다(`web/tools/player_initemu.py`, `player_annot.py`).

## 6. 넷 타입 등록 [판독]

데이터 이름 → 코드로 가는 세 번째 경로입니다. 넷 이벤트·상태 타입 348종(이벤트 289, 상태 59)이 등록 함수 `0x71012f8808`/`0x71012f8db8`로 이름 해시와 vtable을 등록하고, 공통 vtable 슬롯 12 = write, 13 = read입니다. 목록은 `analysis/network/nettypes.tsv` — [network/03_serialization.md](network/03_serialization.md).

## 7. Ghidra

프로젝트 `c:/dev/splatoon3/ghidra_proj/spl3_main`(`web/tools/ghidra_main_import.sh`로 생성). 함수 목록은 `analysis/functions/main.nso.tsv`에 내보냅니다.
