# 슈터 총구 시각 부착·내적 입력 경계 r9 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

사격 중 총구 플래시의 위치·방향·롤·크기는 현재 손과 총의 뼈 포즈를 따라야 한다. 웹은 기존 탄 생성 위치/방향 대체 경로 앞에 실제 `Weapon_R → Root → Muzzle` 행렬 공급을 연결했다. 총탄의 시작 위치·판정은 바꾸지 않았다.

**[판독]+[데이터]** 원본 시각 부착의 `Muzzle`과 **[실행: 부분]** `MuzzleShotDirXZDot` 계산 명령 블록은 별도 근거다. 내적 계산이 선택하는 뼈를 `Muzzle`이라고 확정할 근거는 아직 없다. 두 경로를 합치지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `Lby_Lobby00`, `Shooter_Normal_00`, `WeaponShooterNormal`만 대상으로 했다. 먼저 SHARED/FUNCS 및 `decomp_index.py 2578c34`, `decomp_index.py 2448878`를 확인했다. 기존 `analysis/decomp/effect_sound/fx_batch3.c`, 캐릭터 파츠 조립 판독 및 ELink 원시 자료를 재사용했다.

| 자료 | 확인한 범위 |
|---|---|
| [기존 발사 흐름 §3.2](effect_sound.md#32-발사-판독), [조립 §6](../graphics/player_assembly.md) | ELink `WpShtrMzfNml`의 Bone=`Muzzle`; 몸 `Weapon_R` 및 무기 Root 부착 |
| 실제 `assets/weapons/Shooter_Normal_00/model.glb` | Root/Muzzle 두 뼈와 원본 변환 데이터 |
| [새 디컴파일](../../../analysis/port_graphics_r9/muzzle_native.c) | `0f54d68`, `35015b4`가 파일명 버퍼를 쓰는 함수라는 반증 |
| [원본 실행 기록](../../../analysis/port_graphics_r9/muzzle_heading_emu.json), [도구](../../tools/muzzle_heading_r9_emu.py) | `2579244..25792c8` 계산·holder 기록만 실행 |
| [실제 웹 공급 이전](../../../analysis/port_graphics_r9/muzzle_before.json) | 뼈는 존재했지만 shared muzzle 공급은 null |

주소 표기는 main 기준 하위 주소이며 실행 베이스는 `0x7100000000`이다. 키 파일은 읽지 않았다.

## 3. 진입점과 전체 호출 흐름

원본 시각 경로 **[판독]+[데이터]**:

```text
WeaponShooterNormal 모델 초기화 289bd80 부근
  몸 모델에서 Weapon_R 검색 → +3b8
  무기 모델(+5e0)에서 Muzzle 검색 → +3bc
FireImpact/FireOn ELink 자산 WpShtrMzfNml
  Bone=Muzzle, 기존 이벤트 인계 규칙 → 해당 시각 부착 행렬
```

내적 reader **[판독]**:

```text
2578c34의 this는 x19에 유지
  this+88가 가리키는 객체
  +3c4 halfword = 모델 목록 인덱스
  +3c6 halfword = 뼈 인덱스
  +5e8 → +40 목록 → 선택 모델 vt+78 → 행렬
  2579244..92c8: −X축의 XZ 성분 → 정규화 → D와 내적
  +100 holder+60에 f32 기록
  25792cc 이후 holder의 callback/ELink 전달은 이번 실행 범위 밖
```

**2026-10-03 정정:** 종전 문서의 `+3c4/+3c6=머즐 뼈` 해석은 유지할 수 없다. 정상 슈터의 명시적인 Muzzle 검색은 `+3bc`를 쓴다. `0f54d68→35015b4`는 리소스 이름에서 확장자 앞까지를 SafeString 버퍼에 복사하며 뼈 번호 writer가 아니다. 같은 오프셋의 다른 무기·다른 객체를 원본 슈터 근거로 대체하지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 / 필드 | writer·reader / 수준 | 웹 대응 |
|---|---|---|
| NormalShooter 모델 +5e0, +3bc | `289bd80`의 `Muzzle` 검색 [판독] | 실제 exported `part:Muzzle` |
| reader의 this+88 대상 +3c4/+3c6 | reader `2579218..9240` [판독]; 실제 타입/writer 미확정 | 웹 내적 입력에 연결하지 않음 |
| body(+108)+538 vec3 | 기존 `2458630` writer, camera+1a4 사본 [판독] | 실제 supplier 확인이 필요한 내적 D |
| holder+60 f32 | `25792c8` STR [실행: 부분] | 테스트 fixture `expectedBits` |
| exported Muzzle local translation | `(0, 0.187240824, 0.692283332)` 웹 단위 [데이터] | GLB 뼈 자체 사용; 별도 offset 상수 중복 없음 |
| 웹 `MuzzlePose` | `{owner,frame,source,matrix[16]}` | source=`Weapon_R/Root/Muzzle`; matrix는 column-major |

원본 행 우선 3×4와 Three의 column-major 4×4를 혼동하지 않는다. 뼈 축을 단위벡터로 다시 만들어 롤이나 비등방 스케일을 지우지 않는다.

## 5. 상태 전이와 전체 수명

**웹 반영:** PlayerView가 실제 무기 스켈레톤에서 `part:Muzzle`을 찾는다. 렌더 view update에서 `player.draw(alpha)` 뒤 뼈 월드 행렬을 복사해 shared에 기록한다. FX view는 owner가 같은 행렬을 선택한다. 이벤트 생성 및 follow callback마다 복사본을 받는다.

모델/뼈/소유자가 없으면 기존 명시적 대체 경로를 유지하고 진단한다. 뷰 해제 또는 공급 불가 시 shared muzzle을 제거한다. 다른 액터의 행렬을 재사용하지 않는다. 숨은 상태의 재질·뼈 전체 갱신 계약은 별도 [표시 문서](../graphics/character_display_r8.md)에 남는다.

## 6. 계산식·조건·상세 의사코드

내적 격리 reader **[실행: 부분]+[판독]**:

```text
len = f32(sqrt(f32(f32(M00*M00 + 0) + M20*M20)))
v = (−M00, 0, −M20)
if len > 0:
    k = f32(1 / len)
    v = f32(k * v)       // 각 성분의 원본 연산 순서 유지
dot = f32(f32(f32(v.x*D.x) + f32(v.y*D.y)) + f32(v.z*D.z))
```

**D를 재정규화하지 않는다.** 길이0이면 나눗셈을 하지 않는다. signed zero·underflow를 포함한 유한 입력을 비트 비교했다. 무한대/NaN·caller·실제 행렬 producer는 이 검증 범위에 포함하지 않는다.

웹 시각 행렬 소비:

```text
o = (e12,e13,e14)
x = (e0,e1,e2); y = (e4,e5,e6); z = (e8,e9,e10)
if PositionY exists: copied.o += copied.y * PositionY
```

기존 이미터 SRT는 이어서 적용한다. provider 행렬을 직접 수정하지 않아 매 프레임 offset이 누적되지 않는다. `nativeHeadingDotReader`는 검증용 함수이며 실제 `muzzleDot`의 뼈 공급을 확정한 구현으로 사용하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

손 포즈는 실제 슈터 `Shtr/Shtr` ASB skeletal leaf를 따른다. Root는 몸 `Weapon_R`에 붙고 Muzzle은 Root의 자식이다. `WpShtrMzfNml/SplashCorn`과 `/Flash`가 공급 행렬을 사용한다. 기존 known shader/color/alpha/SRT 경로는 유지한다.

FireImpact↔FireOn의 이벤트 인계, Delay curve `(0.75→2, 1→0)`, SplashCorn 5프레임/Flash 7프레임 방출 간격은 기존 원본 근거를 재사용했다. 총탄 6프레임 간격과 이미터 간격을 같게 만들지 않는다. 발사 소리와 카메라를 바꾸는 작업은 하지 않았다.

## 8. 다른 기능과의 상호작용

시각 총구 위치와 탄의 물리 생성 위치는 별도다. `2552170` 등 탄 생성 계약을 Muzzle 행렬로 덮어쓰지 않는다. owner 검사는 로컬 재생 액터와 뼈 pose를 결합하는 웹 경계다. 보간된 렌더 행렬을 core 물리/도색/피격 입력으로 보내지 않는다.

ELink의 내적·Delay 평가 시점과 core→render→FX 순서 전체의 원본 프레임 동등성은 남은 질문이다. 행렬 연결만으로 전부 해소했다고 기록하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

| 파일 | 책임 |
|---|---|
| `client/render/player.ts` | 실제 Muzzle 뼈 발견, 현재 월드 행렬 공급 |
| `client/render/index.ts` | draw 뒤 owner/frame 포함 pose publish 및 해제 |
| `client/fx/muzzle.ts` | pose 검증·행렬 복사, 검증된 격리 내적 함수 |
| `client/fx/index.ts` | 실제 pose 우선, 기존 명시적 fallback, 이벤트 부착 |
| `tests/muzzle_pose.test.mjs` | 원본 bit fixture·actual GLB 뼈·FxSystem offset/소유권 검증 |

재현 명령 및 실패는 [r9 명령 기록](../../../analysis/port_graphics_r9/commands.md)에 모았다. 임시 파일도 프로젝트 안에 저장한다.

## 10. 검증 코드·실행 결과·기대값

- `python web/tools/muzzle_heading_r9_emu.py`: 원본 명령 블록 **2,048/2,048**, 불일치0, 외부 호출0. 합성 행렬/리그/body/holder 메모리를 공급했고 실제 선택 producer와 callback은 실행하지 않았다.
- Node 머즐 테스트 **4/4**: 비트 일치, owner·roll·scale·복사, actual exported Muzzle의 animated hand 부착, 실제 FxSystem의 PositionY 비누적.
- 실제 웹 GPU·발사/변신 연속 검증과 실패 기록은 [r9 웹 결과](../../../analysis/port_graphics_r9/browser_verification.json), [요약](../port/graphics_priority_r9.md)에 기록한다. 원본 NVN GPU 또는 동일 원본 프레임의 픽셀 비교가 아니다.

새 디컴파일은 Git Bash의 `full_decomp.sh`로 `0f54d68`, `35015b4` 두 함수를 처리했다. `sh` PATH 실패와 처음 잘못된 상대 경로·JSON import 실패도 명령 기록에 남긴다. 병렬 담당자의 읽기 명령은 도구의 Windows sandbox 설정 충돌로 **실행 전 실패**했으며 원본 디컴파일 실패와 구분한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 미확정 | 시도와 막힌 곳 | 다음에 볼 곳 |
|---|---|---|
| 내적의 실제 선택 뼈·this+88 타입 | x19가 끝까지 this임과 최종 read가 flag40/80 분기 밖임 확인. 0f54d68 이름 복사 반증. STRW+3c4/STRX+3c0/packed STP 조사에서 다른 무기 후보를 찾았지만 정상 슈터 타입 증거 없음 | `2578c34` caller/xref → this+88 assignment → 실제 vtable/class → +3c4/+3c6 writer |
| +3c4 packed writer | `287d6d0,2889664,288dd90,2894584,28e94c8` 주변 저장 후보. `2894584`의 M_Umbrella_Close는 범위 밖이며 슈터에 대입 금지 | 실제 클래스가 확인된 뒤 해당 writer로 좁힐 것 |
| 원본 전체 Delay/부착 프레임 순서 | 시각 Bone 계약과 reader 식 확보; 실제 ELink calc 큐 평가와 pose producer 미연결 | slot19/무기 ASB→행렬 갱신→ELink calc 소비 순서 |
| 원본 최종 그래픽 일치 | 선택 emitter/shader/뼈 연결만 검증 | native SPP/cube/BRDF/VAT 및 동일 Lby 원본 캡처 |

기존 고정 FX 질문 전체를 확정/반영 확인으로 올리지 않는다. 웹 내적 대체는 남은 차이다.
