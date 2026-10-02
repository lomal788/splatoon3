# 카메라 연출과 손맛(조작감) — 목차

담당: [camera]. 작업 지침은 [../../분석.txt](../../분석.txt), 공용 규칙은 [../README.md](../README.md)·[../tools.md](../tools.md).

분량이 커서 세 문서로 나눴습니다. 이 문서에는 전체 요약, 자료 위치, 공통 수학 도구(난수·bias 곡선·사인표·sead 곡선)를 둡니다. 함수 주소는 main NSO를 0x7100000000에 올린 기준입니다.

| 문서 | 내용 | 상태 |
|---|---|---|
| [aim_swerve.md](aim_swerve.md) | 슈터 조준 흔들림(발사 방향 분산), 연사 타이머, PreDelay, 난수, 블래스터·SpChariot·듀얼·Diffusion | 분석 진행. 핵심 계산 [판독] + 재구현 검증. Diffusion Bias/Swerve 무효 [판독: asm], 듀얼·스피너 [판독-부분/미확정] |
| [player_camera.md](player_camera.md) | 3인칭 플레이어 카메라: 리그(거리·높이·고각), FOV, 감도, 스틱 응답, 피치 범위, 수직 추종, 최종 출력, 대체 리그 발동 조건, 자이로, 형상 질의, 리셋 호출자 | 분석 진행. 기본 경로·대체 리그 조건·반전 설정(원본 에뮬)·붐 질의→거리 비율·슈퍼점프 비행 중 처리 [판독], 자이로·사망 카메라(포즈 메시지까지) [판독-부분], 질의 형상·사망 화면 카메라 [미확정] |
| [shake_rumble.md](shake_rumble.md) | 카메라 쉐이크(CameraModuleParam.Rumble), 컨트롤러 진동(bnvib), ELink 연결, CameraAnimation, 히트 피드백 연결점 | 분석 진행. 쉐이크 계산·적용(카메라 위치, 월드)·gain(거리 감쇠 15/25)·코드 직접 쉐이크 [판독], bnvib 디코드 [추정] |

"분석 완료"·"웹 구현 완료"·"동작 검증 완료"는 다른 상태입니다. 웹 구현은 없습니다. 이 문서의 검증은 전부 **재구현 계산과 합성 테스트**이고 원본 실행 검증은 없습니다.

## 1. 확정 수준 요약

| 항목 | 결론 | 수준 |
|---|---|---|
| 슈터 흔들림 = 조준 방향을 **월드 Y축으로만** 회전 (수평 분산) | 0x7102583bac~0x7102583c64 | [판독] |
| 흔들림 각 = DegSwerve(도) × bias 곡선(2r−1), bias = max(누적 bias, 점프 bias) | 0x7102583a9c~0x7102583ba4 | [판독] |
| 난수 = 발사마다 새로 시드하는 sead::Random(xorshift128), getF32 1회 | 0x71025839d4~0x7102583ab4 | [판독] |
| 시드 입력 = 전역 프레임 카운터 + 전역 4정수 | 전역 의미 | [추정] |
| 누적 bias: 발사 후 +Kf(상한 Max), 트리거를 놓고 타이머가 대기 상태면 −Decrease, 하한 Min | 0x71025843e0, 0x71025830d0 | [판독] |
| 점프 흔들림: 점프 시 카운터=Jump_DegBiasEndFrame, 공중(공중 프레임 ≥ 4)이면 1, 접지면 2씩 감소, (End−DecreaseStart) 구간 선형 복귀 | 0x7102580c4c, 0x7102580f98, 0x71025830d0 | [판독] (본체+0xc0 = 공중 프레임 의미는 [추정 — 강함]) |
| 연사 타이머(RepeatFrame) 위상 누적 방식 | 0x7102551530 | [판독] |
| 플레이어 카메라 리그: p(−1..1)별 3점 베지어 4개(H,F,D,S) + 고각 회전 | 0x71024d6e84 | [판독] (기본 경로) |
| FOV 55°, near 0.2, far 2000 | 0x71024d6598 | [판독] |
| 감도(−5..+5) → yaw/pitch 속도 | 0x71024d6598, 0x71024e0178 | [판독] (UI 값↔세이브 값 대응 [추정]) |
| 수평은 즉시, 주시점 높이만 지연 추종 | 0x71024d9ae8 | [판독] (비율 변수 의미 [추정]) |
| 벽/지형 회피 | PlayerCamera 내장 질의 Q(this+0x1d0)로 피벗→리그 카메라 붐을 두 번 질의(피벗 근처·단축). 적중 거리 Q+0x54 → 목표 비율 this+0x14c8(막히면 즉시, 풀리면 천천히) → 평활 비율 +0x14c4 → `pos = 피벗 + dir·len·비율` ([player_camera.md §6.8](player_camera.md)) | 경로·식 구조 [판독], 줄어들 때 rate·복귀 속도 세부 [판독-부분], 형상·반경 [미확정] |
| 반전 설정 IsReverseUD/LR | 오른쪽 스틱 기록 0x71024a73b8이 세이브 +0x4001(상하)/+0x4002(좌우)로 부호 반전, 자이로에는 미적용, 차이값은 '원시 − 지난 기록값'(특이점) | [판독]+[실행(에뮬) 4 PASS] |
| 슈퍼점프 비행 중 카메라 | 별도 카메라 없음. this+0x1920 = PlayerDokanWarp 단계로 오징어 블렌드·붐 질의 생략·착지 방향 자동 yaw | [판독] (단계 이름 [추정]) |
| 사망 카메라 | 사망 대기(T+8) 시작 프레임에 Pos/At/ShotDirXZ 메시지를 연결 액터로 1회 전송, 화면 카메라는 받는 쪽 | [판독], 받는 쪽 [미확정] |
| 카메라 쉐이크 = Axis × curve(frame) × gain × Scale, 살아 있는 쉐이크 합을 카메라 **위치(월드)**에 더함 | 0x71010182e8, 0x7101010150 | [판독] |
| 쉐이크 gain = DistanceAttenuate≥1이면 1−clamp((d−15)/10), 아니면 1 | 0x710137b000, 0x710130d3a8, RumbleModuleParam | [판독]+[데이터] |
| 대체 리그 7종 + 오징어 블록 발동 조건(NiceBall·Jetpack·IkuraShoot·다운·GrindRail·Pipeline·오징어) | 0x71024d9ae8 2585~3060행 | [판독] (상태 이름 일부 [추정]) |
| 블래스터 = 슈터 흔들림 경로 공유, 서서 쏘면 정면 | 컴포넌트 목록·넷 열거·WeaponBlaster 슬롯 8 | [판독]+[데이터] |
| SpChariot 흔들림 = 슈터와 같은 시드·bias 곡선·Y축 회전(점프 흔들림 없음), Diffusion CenterDegreeBias/Swerve는 결과 무효 | 0x710259b7bc, 0x7102897640 asm | [판독] |
| 진동 bnvib 헤더·샘플 구조 | 115개 크기 일치 | [데이터], 주파수 코드식 [추정] |
| ELink 에셋별 CameraRumbleName/CtrlRumbleName 매핑 | effect_sound 파서 출력 재가공 | [데이터] |

## 2. 원본·자료 위치

| 자료 | 위치 |
|---|---|
| 원본 | `c:/dev/splatoon3/original/` (읽기 전용) |
| main 이미지 | `extracted/exefs/main.img`, `main.reloc.img` |
| 디컴파일 | `analysis/decomp/camera/batch1.c` (190함수), `batch2.c` (7함수), `camui_batch3.c`(13), `camui_full1.c`(7, 전체 분석 프로젝트) — 그 밖에 다른 담당이 먼저 만든 `state/state_aux.c`(0x71024c8ee8), `life/batch1.c`(0x71024b1ae0), `gauge/gauge_batch1.c`(0x710249cb60) 참조 |
| 디스어셈블 발췌 | `analysis/camera/shot_7102583008.asm`, `ws_init.asm` |
| 파라미터 | `extracted/params/Component/GameParameterTable/Weapon*.json`, `analysis/param_reflect/spl__WeaponShooterParam.json` |
| 싱글턴 파라미터 | `analysis/camera/SingletonParam/` (`Pack/SingletonParam.pack.zs` 해제본: `game__CameraModuleParam`, `game__RumbleModuleParam`) |
| 진동 패턴 | `analysis/camera/rumble_bnvib/` (`Rumble/Common.bnvib.sarc.zs` 해제본 115개) |
| 산출물 | `analysis/camera/shooter_swerve_table.{md,json}`, `camera_rumble_samples.json`, `bnvib_summary.json`, `rumble_map.json` |

## 3. 도구

모두 `c:/dev/splatoon3`에서 `PY=.venv/Scripts/python`, 출력에 한글이 있으므로 `PYTHONIOENCODING=utf-8`을 붙입니다.

| 도구 | 용도 |
|---|---|
| `web/tools/camera_swerve.py table/selftest/sim` | 흔들림·연사 재구현, 무기 표, 합성 검사 |
| `web/tools/camera_rig.py table/sens/selftest` | 카메라 리그·피치 매핑·감도 재구현 |
| `web/tools/camera_shake.py rumble/bnvib/selftest` | sead 곡선 평가, 카메라 쉐이크 샘플, bnvib 헤더 |
| `web/tools/camera_rumble_map.py [접두어]` | ELink 진동/쉐이크 파라미터 추출 |
| `web/tools/camera_ldscan.py` | 같은 베이스로 여러 오프셋을 읽는 구간 찾기 |
| `web/tools/camera_fieldreaders.py <param_reflect json>` | "설정됨 플래그 ldrb + 값 ldr" 쌍으로 파라미터 필드 리더 함수 찾기 |
| `web/tools/camera_funcs.py build/range/at` | BL 대상 + 데이터 포인터로 함수 시작 후보 색인 |

`camera_fieldreaders.py`는 다른 영역에도 쓸 수 있습니다. 파라미터 필드는 항상 "설정됨 플래그"(`param+flag_offset`)를 먼저 읽기 때문에 `ldrb #flag`와 `ldr #off`가 가까이 붙는 위치가 곧 리더입니다.

## 4. 공통 수학 도구

### 4.1 sead::Random (xorshift128) [판독]

흔들림은 **발사마다 새 난수기**를 만들어 한 번만 뽑습니다. `GetSystemTick` 호출(0x71025839d4)이 남아 있지만 결과는 쓰지 않습니다. 기본 생성자(틱으로 시드)가 인라인된 뒤 명시 시드로 덮인 흔적으로 봅니다 [추정].

```
M = 0x6C078965                     // u32 산술
s0 = F + (a + b) * 0x89            // F = max([*0x710580e758]+0x148, 0), a,b,c,d = [*0x7105850620]+0x124/0x128/0x12c/0x130
X = M*(s0 ^ s0>>30) + 1
Y = M*(X ^ X>>30) + (c + b)*0x1C1 + 2
Z = M*(Y ^ Y>>30) + (d + c)*0x233 + 3
W = M*(Z ^ Z>>30) + (d + a)*0x3DF + 4
if (X|Y|Z|W) == 0: X = 1, W = 0x48077044      // sead 기본 상태의 X, W
// getU32
t = X ^ (X << 11); X,Y,Z = Y,Z,W; W = W ^ (W>>19) ^ t ^ (t>>8)
// getF32
f = asFloat(0x3F800000 | (W >> 9)) - 1.0       // [0, 1)
```

- F: 전역 객체(GOT 0x7105790610 → 0x710580e758)의 +0x148. 0x710126bc10에서 0으로 초기화, 0x7101442f10에서 다른 객체로 복사됩니다. 프레임 카운터로 추정합니다 [추정]. 네트워크 동기 프레임 번호일 가능성이 높아 [network] 확인이 필요합니다.
- a..d: 전역 객체(GOT 0x7105797f18 → 0x7105850620)의 +0x124~+0x130. [bullet]이 탄별 난수에서 같은 객체의 +0x120을 쓴다고 기록했습니다(SHARED). 세션 공통 시드로 추정합니다 [추정].
- 결과: 같은 프레임·같은 시드면 모든 클라이언트가 같은 흔들림을 얻습니다. 플레이어별 값은 시드에 들어가지 않습니다 [판독]. 같은 프레임에 두 플레이어가 쏘면 같은 r을 씁니다 [판독 결과로부터의 추정].

웹: `Math.imul`과 `>>> 0`으로 u32 산술, `Float32Array`/`DataView`로 비트 변환. 재구현 `camera_swerve.py seed_state/rand_f32`.

### 4.2 bias 곡선 [판독]

원본이 여러 곳에서 같은 인라인 코드를 씁니다(흔들림 0x7102583ad8, 스틱 응답 0x71024e0178, 감속 곡선 등). Perlin bias와 같습니다.

```
bias(u, b):
  if |b - 0.5| <= 0.001: return u                  // (b-0.5 < -0.001 || b-0.5 > 0.001) 가 아니면
  if |u| < 0.001: return 0
  if b < 0.001: return |u| < 0.999 ? 0 : 1.0       // 부호 없음 (원본 그대로)
  p = expf(logf(|u|) * (logf(b) * -1.442695))      // = |u|^(-log2 b)
  return u < 0 ? -p : p
```

`logf`/`expf`는 SDK libm 임포트(PLT 0x7103e9c2a0/0x7103e9be20, `web/tools/paint_imports.py`로 확인)입니다. 웹에서는 `Math.log/Math.exp` 뒤 `Math.fround`를 씁니다. libm과 JS의 마지막 비트 차이는 [미확정]입니다.

### 4.3 sead 사인/코사인 표 [데이터]+[판독]

각도→(sin, cos)는 표 보간입니다. 표 0x7104aa5b5c, 256항목 × (sin_k, sin_{k+1}−sin_k, cos_k, cos_{k+1}−cos_k), f32.

```
v  = (int64) f32(rad * 6.8356525e8)      // 2^32/2π, fcvtzs (0 방향 절삭)
i  = (v >> 24) & 0xFF
fr = (v & 0xFFFFFF) * 5.9604645e-8       // 2^-24
sin = T[i].s + T[i].ds * fr ;  cos = T[i].c + fr * T[i].dc
```

선형 보간이라 최대 오차는 약 7.5e-5입니다. 웹에서 비트 일치가 필요하면 표를 그대로 추출해 씁니다(`camera_swerve.py sincos_idx`가 main.img에서 읽음).

### 4.4 sead 곡선 평가 [판독]

`Linear, Hermit, Step, Sin, Cos, SinPow2, Linear2D, Hermit2D, Step2D, NonuniformSpline, Hermit2DSmooth, Hermit2DSplit` (문자열 0x710493e6b9). 평가 함수 표 0x7105738610:

| 타입 | 함수 | 계산 (`d`=Data, `n`=개수) |
|---|---|---|
| Linear | 0x71038c8990 | t<0 → d[0]; x=(n−1)t, i=⌊x⌋; i<n−1 ? lerp(d[i],d[i+1],x−i) : d[n−1] |
| Hermit | 0x71038c89f0 | n 홀수 → 0. 키 (값, 접선) 쌍 n/2개 균등. x=(n/2−1)t, f=x−i: h00·d[2i]+h10·d[2i+1]+h01·d[2i+2]+h11·d[2i+3]. **접선은 구간 정규 단위**. 끝 넘으면 d[2(n/2−1)] |
| Step | 0x71038c8ad0 | d[⌊clamp(t,0..1)·(n−1)⌋] |
| Sin | 0x71038c8b00 | sin(d[0]·t·2π)·d[1] |
| Cos | 0x71038c8b40 | cos(d[0]·t·2π)·d[1] |
| SinPow2 | 0x71038c8b80 | sin²(d[0]·t·2π)·d[1] |
| 2D 계열 | 0x71038c8bd0~ | 미판독 [미확정] (NonuniformSpline 칸은 null) |

호출부(0x71010182e8, 0x71024d9ae8)는 **타입 0~2만 t를 MaxX로 나눕니다**. Sin/Cos/SinPow2는 프레임 값을 그대로 받으므로 d[0]은 "프레임당 주기 수"입니다. 곡선 구조체: +0 타입(u32), +4 MaxX(f32), +8 개수(u8), 데이터 포인터는 별도(CameraRumbleParam 기준 +0x48).

## 5. 다른 영역과의 경계

- 슈터 탄 비행·데미지·도색은 [bullet]/[combat]/[paint]. 이 영역은 탄 생성 **방향**까지만 다룹니다.
- 플레이어 상태(점프, 착지, 오징어/인간 전환)를 판정하는 코드는 [player]. 흔들림·카메라는 그 결과 플래그만 읽습니다.
- 이펙트·사운드·ELink 파서는 [effect_sound]. 진동/쉐이크 매핑은 그 출력 `analysis/effect_sound/elink2_users.json`을 읽기만 했습니다. ELink 파일 파라미터 `CameraRumble`(정수)의 소비처는 [effect_sound]/[fx]와 조율 중입니다(SHARED.md).
- 대전 맵(미니맵) 카메라는 [../ui/ui_minimap.md](../ui/ui_minimap.md).
- HUD 히트마커는 [ui]. [shake_rumble.md §6](shake_rumble.md#6-히트-피드백-연결점) 참고.

## 6. 공용 문서 반영 제안

- `tools.md`에 `camera_fieldreaders.py`(필드 리더 찾기)와 `camera_funcs.py`(함수 시작 색인)를 추가하면 다른 영역이 같이 쓸 수 있습니다.
- `02_code_and_params.md` §2에 "필드 읽기는 설정됨 플래그 → 부모 체인" 규칙([bullet] SHARED)과 "리더 찾기 = ldrb #flag + ldr #off 근접" 요령을 추가 제안합니다.
- README 기능 표의 카메라 행 링크는 이미 이 문서를 가리킵니다. 상태 칸의 "자이로·벽 회피·특수 카메라 미확정"은 2026-10-02 [camui] 기준 "대체 리그 조건·쉐이크 적용·자이로(부분)·형상 질의 존재·리셋 호출자 판독, 반전 설정·질의 효과·슈퍼점프 카메라 미확정"으로 바꾸기를 제안합니다(README는 공용이라 직접 고치지 않음).
- `tools.md` 영역 도구 표 UI 행에 `ui_animcmd_emu.py`, `ui_minimap.py`, `ui_vcall_scan.py`(가상 호출 슬롯 공존 스캔 — 다른 영역도 사용 가능) 추가를 제안합니다.
- 2026-10-02 [camrest]: 카메라 행에 `camera_stick_emu.py`(오른쪽 스틱 기록·반전 원본 에뮬), UI 행에 `ui_animorder_emu.py`(TraceGauge→setFrame→레이아웃 애니 적용 루프 원본 에뮬), `ui_minimap_shader.py`(미니맵 재질 Hoian_UBER 프로그램 역번역), `ui_minimap.py cam`(맵 카메라 기저 재구현) 추가를 제안합니다. README 카메라 행 상태는 "반전 설정·붐 질의 효과·슈퍼점프 카메라 판독, 질의 형상·사망 화면 카메라 미확정"으로 바꾸기를 제안합니다.
