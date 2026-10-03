# 플레이어 애니메이션 상태머신 — ASB(v0x410)와 커맨드 요청

[목차](model_character.md) · 조립·클립 일반은 [player_assembly.md](player_assembly.md), 게임 쪽 상태 번호는 [../player/player_state.md](../player/player_state.md).

상태: **판독 진행 중**. ASB 헤더·커맨드·노드 목록·자식 목록은 두 파일 전수로 읽었다(아래 도구). 3차 작업에서 엔진 AS 노드 생성 루프(0x71039b17f8)·프레임 전진(0x71039ab2c4)·끝 프레임(0x71039d44ac)·전환 블렌드(0x710399728c)·FloatBlend(0x71039c890c)·블랙보드 공급(0x710246cb58)을 판독했다(§2.5, §4.1~§4.5). 디컴파일 `analysis/decomp/render/r4_asnode.c`, `r4_asnode2.c`, 노드 vtable 표 도구 `PY web/tools/render_asnode_vt.py`. 원본 실행 검증은 없다.

- **갱신(2026-10-03, r5):** 클립 이름 해석기 0x710244d0b0 의 후보 순서와 대체 규칙을 원본 실행으로 확정했다(§3.1, 2210/2210). 그 밖의 절은 여전히 판독만 했다.

## 1. 개요

- 플레이어 애니는 엔진의 AS(Animation Sequence) 시스템이 재생한다. 리소스는 `SplPlayer.pack.zs` 안 `AS/SplPlayer.root.asb`(사람 모델용)와 `AS/SplPlayerSquid.root.asb`(오징어 모델용) 두 개 [데이터]. 문자열 `AS/SplPlayer.root.asb`·`AS/SplPlayerSquid.root.asb`는 0x710243d01c 가 로드한다 [판독].
- 게임 코드는 상태 번호 → 상태 표(0x7105630270)의 이름 → **ASB 커맨드 이름**으로 요청한다(`0x710399e340(-1,-1, AS, &name, 슬롯, …)`). 즉 ASB 커맨드 = 게임 상태 이름 [데이터: 286개 중 284개 이름 일치, `web/tools/state_verify.py`].
- 커맨드는 노드 트리의 루트를 가리키고, 트리는 블랙보드 값(무기 종류, 점프 변형, 이동 속도 비율 등)으로 실제 클립을 고른다.
- 블렌드(보간) 프레임은 ASB가 아니라 **게임 상태 표의 값**을 요청 때 슬롯+0xdc 에 넣는다 [판독: 0x7102451a90].

## 2. 파일 구조 [데이터 + 추정]

도구: `PY web/tools/state_asb.py <x.asb> [--tree] [--json out]`. 트리 출력 `analysis/state/asb_SplPlayer_tree.txt`(656줄), `asb_SplPlayerSquid_tree.txt`.

### 2.1 헤더 (u32 × 26, 리틀 엔디언)

| 오프셋 | 사람 | 오징어 | 의미 |
|---|---|---|---|
| +0x00 | `ASB ` | | 매직 [데이터] |
| +0x04 | 0x410 | 0x410 | 버전 [데이터] |
| +0x08 | 0 | 0 | 파일 이름(문자열 풀 오프셋 0 = `SplPlayer.root`) [데이터] |
| +0x0c | 235 | 26 | 커맨드 수 [데이터: 커맨드 표 길이와 일치] |
| +0x10 | 394 | 41 | 노드 수 [데이터: 노드 표 끝 = +0x30] |
| +0x14 | 5 | 1 | [추정] 이벤트 수 |
| +0x18 | 2 | 0 | [추정] 보조 슬롯(레이어) 수 — 게임은 사람 ASB에 슬롯 0/1 을 씀 |
| +0x1c | 20 | 6 | 노드 파라미터 레코드 수(레코드 표 +0x38, 0x18 B) [판독: 0x71039d452c] |
| +0x20 | 0xaed4 | 0x1258 | 로컬 블랙보드 [데이터: 이름 목록 위치] |
| +0x24 | 0xb41c | 0x130c | 문자열 풀 [데이터] |
| +0x30 | 0x6034 | 0xaa4 | 노드 본문 시작 = 노드 표 끝 [데이터] |
| +0x38 | 0xab98 | | 노드 파라미터 레코드 표(0x18 B = {u32 타입, u32 값 위치, GUID}) [판독] |
| +0x3c | 0xab48 | | 노드별 레코드 색인표(노드 표 +0x10 의 u16 이 시작) [판독] |
| +0x44 / +0x48 | 34 / | | 실수 파라미터 표 개수 / 위치(§2.7) [판독] |
| 그 밖(+0x28, +0x2c, +0x34, +0x40, +0x4c..) | | | 미확정(이벤트 표 등) |

### 2.2 커맨드 (0x68부터, 0x2C B)

| 오프셋 | 내용 |
|---|---|
| +0x00 | 이름(문자열 풀 오프셋) |
| +0x04 | 0 |
| +0x08 | f32 −1.0 (전 항목 동일) |
| +0x0c..+0x14 | 0 |
| +0x18 | GUID 16 B |
| +0x28 | 루트 노드 번호 |

### 2.3 노드 (커맨드 표 뒤, 0x24 B)

| 오프셋 | 내용 |
|---|---|
| +0x00 | u16 종류 |
| +0x02 | u8 파라미터 레코드 수(플래그 0x101/0x102 의 하위 바이트) + u8 0x01 [판독: 0x71039d452c] |
| +0x04 | 0 |
| +0x08 | 본문 오프셋 |
| +0x0c | 미확정 |
| +0x10 | u16 레코드 색인 시작(헤더 +0x3c 표) [판독]. 레코드 타입 0 = 이 노드의 블렌드 프레임(예: Emote_@ 10, Demo_*_Making 24, 오징어 36 = bb `DirectAnimBlendFrm`), 타입 3 = 진입 때 애니가 없으면 inst 플래그 0x20 |
| +0x14 | GUID |

### 2.4 노드 본문 공통 — 자식 목록

본문 안에 `(n | n<<24, n<<8 | n<<24, 항목 오프셋 × n)` 이 나오면 자식 목록이다. 각 항목의 **마지막 u32 = 자식 노드 번호**, 앞 단어는 분기 값(문자열 풀 오프셋·정수 등) [데이터: 모든 트리가 범위 안 노드로 닫힘, 추정: 항목 의미].

값 참조: `0x80000000 | i`(상위 비트 1) = 블랙보드 참조. 상위 4비트 0x8/0xa/0xd/0xe 가 종류별로 쓰인다(문자열·bool 0x8, 정수 0xa, 실수 0xd/0xe) [추정].

### 2.5 노드 종류

엔진 노드 생성 루프 0x71039b17f8 이 노드 표 u16 종류에서 1 을 빼 25칸 점프표(0x7104af3260, 기준 0x71039b20dc)로 분기하고, 종류마다 다른 vtable 을 단 객체를 만든다 [판독]. vtable 은 `PY web/tools/render_asnode_vt.py` 로 출력. 종류 5·15 는 같은 vtable(0x7105742570, 0x18 B)을 공유하는 빈 노드이고, vt+0x28 이 0x71039c25b8 인 "애니 잎" 그룹은 {3, 11, 13, 18, 24} 이다 [판독].

| 종류 | 이름(웹 권장) | 본문·동작 | 근거 |
|---|---|---|---|
| 2 | `StringSelector` | 블랙보드 문자열 + (case 문자열, 자식), 기본 `その他` | [데이터] |
| 3 | `SkeletalAnim` | 클립 이름(또는 bb 참조). 끝 프레임 vt+0x38 = 0x71039d44ac(§4.2). 본문에 **부착 목록**(§2.8) | [판독] |
| 6 | `FloatBlend` | 실수 입력 x + 자식마다 [lo, hi] 구간, §4.4 | [판독: 0x71039c890c] |
| 7 | `Sequence`(웹 권장 이름) | 현재 자식 완료→다음, 본문+14로 같은 틱/다음 틱 진행; 실제 자식84→81 아래 Emote 잎 | [판독] (2026-10-03 r8, [노드 제어](asb_node_runtime.md) §3~§7) |
| 8 | `IntSelector` | bb 정수 + (정수, 자식) | [추정] → 선택 규칙 [실행] (표 아래, 2026-10-03) |
| 9 | `Simultaneous` | 자식 n개 동시. 끝 프레임 vt+0x38 = 0x71039d30e4 | [추정: 이름] |
| 10 | `Event` | u32 이벤트 번호(사람 0~4, 오징어 0 — 헤더 +0x14 의 5/1 과 일치). 잎 노드의 부착 목록으로 붙음. 발화 처리 0x71039c6d98 | [판독+데이터], 발화 구간 [실행]+[판독] (2026-10-03 r8, [이벤트 전용 문서](asb_event_runtime.md) §3~§10) |
| 11 | `MaterialAnim` | 재질 애니 이름(애니 잎) | [데이터] |
| 12 | `FrameController` | 잎 노드에 붙어 재생 구간·속도를 덮어씀, §4.3 | [판독: 0x71039c9140] |
| 13, 24 | 애니 잎(종류 미상) | 이 두 ASB 에 없음 | [판독: vtable 그룹] |
| 18 | `VisibilityAnim` | 가시성(뼈) 애니 이름(애니 잎) | [데이터] |
| 19 | `InitialFrame` | u32 방식 1..7: 1/2/6/7 = 이전에 재생한 같은 애니의 프레임을 이어받음, +0x20/+0x28 bool. 사람 263 은 방식 3(난수 경로 있음) | [판독: 0x71039c9fcc], 방식 3 난수 구간식 [실행]+[판독] (2026-10-03 r8, [전용 문서](asb_initial_frame.md) §3~§10) |
| 21 | `BoolSelector` | bb bool + 자식 2개(`WaitHold_Nrml` ↔ `Wait`) | [추정] → 선택 규칙 [실행] (표 아래, 2026-10-03) |
| 5, 15 | 빈 노드 | 공유 vtable, 이 파일에 없음 | [판독] |

이름은 데이터 모양·동작으로 붙인 웹 권장 이름이다. 참고: TotK ASB 의 공개 노드 열거에 1 을 더한 번호가 위 관찰(애니 잎 그룹·빈 노드 쌍 포함)과 모두 맞는다 [추정: 외부 자료 대응, 이 바이너리에는 노드 이름 문자열이 없음].

- **선택 규칙 확정(2026-10-03) [실행]+[판독]:** 선택 노드는 자식 번호를 vt+0xe0 으로 고른다.
  - 종류 21 `BoolSelector`(vt 0x7105742278, +0xe0 = 0x71039c46c8): 값 슬롯(본문+0)을 0x71039982bc 로 읽어 `값 != 0` 이면 **자식 0**, 아니면 **자식 1** 이다. 상수 경로 6건·블랙보드 경로 4건 원본 실행 일치.
  - 종류 8 `IntSelector`(vt 0x7105743028, +0xe0 = 0x71039cda20): 자식 수 n = 본문+0x18(u8)이다. 앞 n−1 개 자식의 case 값(본문+0x19 시작 색인 → 본문+0x20 오프셋 표 → 값 슬롯)과 차례로 비교해 처음 같은 번호를 고른다. 같은 것이 없으면 **마지막 자식(n−1)**이 기본이다. 마지막 자식의 case 값은 비교하지 않는다. 상수 경로 120건 원본 실행 일치.
  - 두 함수 모두 넷째 인자가 있으면 값 바이트가 직전(인스턴스 +0xb4)과 달라졌는지 기록하고 +0xb4 를 갱신한다 [판독].
  - 재평가: 공통 선택 진입 0x71039ce4dc 는 인스턴스 +0x98(직전 자식 번호)이 −1 이 아니고 `인자2+0xd0 == 인스턴스+0xa0` 이면 다시 고르지 않고 직전 번호를 쓴다. 다르면 vt+0xe0 으로 다시 고른다 [판독]. +0xd0/+0xa0 이 무엇의 세대 값인지는 [미확정].
  - 검증: `PY web/tools/r5_gfx_char_boolsel_emu.py` → `analysis/completion/r5/gfx_char_boolsel_emu.json`, **130/130 일치**. 스텁은 블랙보드 경로의 문맥+0x20 vt+0x130(이름→순번)과 문맥+0x28 vt+0x148(값 주소)뿐이다. 실수 파라미터 표 경로와 IntSelector 블랙보드 경로는 실행하지 않았다.

사람 ASB 노드 분포: 3 ×313, 6 ×34, 21 ×12, 2 ×11, 8 ×9, 10 ×5, 9/11/12/18 ×2, 7/19 ×1. 오징어: 3 ×26, 9 ×6, 11 ×6, 10/12/18 ×1 [데이터].

### 2.6 블랙보드 이름 [데이터], 종류 배정 [추정]

`DirectAnimName, WeaponCategory, WeaponDetail`(문자열 3), `JumpVarID`(정수), `MoveSpeedRt, StainFrm, WalkAnimSpeed, StartLaunchLandingBlendRt, ShotPitRt, StringerTiltDeg, NiceBallDamageBlendRt`(실수 7 — 사람 ASB), `EquipWeaponMain`(bool). 오징어 ASB 는 실수가 10개로 `DirectAnimBlendFrm, DirectAnimStartFrm, DirectAnimEndFrm` 이 더 있다 [데이터]. 블랙보드 헤더 = 타입 6개 × (개수, 시작 순번, 이름 오프셋) [판독].

### 2.7 값 슬롯 — 상수 / 블랙보드 / 실수 파라미터 [판독: 0x7103997de0]

노드 본문의 값은 `[u32 태그][상수]` 8 B 다(함수에는 상수 주소를 넘김).

| 태그 | 의미 |
|---|---|
| ≥ 0 | 상수 그대로 |
| 0x8…… / 0xa…… | 블랙보드 참조. 하위 비트 = **그 슬롯이 요구하는 타입 안에서의 순번** |
| 0xd…… / 0xe…… | 실수 파라미터 표(헤더 +0x48, 개수 +0x44, 사람 34) 참조 |

실수 파라미터 표 항목(0x20 B) = {내부 bb 순번, 변화율 제한(/dt), 모드(1 = 각도), 초기값, scale, offset, min, max}, 결과 = `clamp(offset + scale × 변화율 제한을 거친 bb 값, min, max)`. 사람 표의 내부 순번 0/1/4/5/6 = MoveSpeedRt [0..1], StainFrm [0..600], ShotPitRt [−1..1], StringerTiltDeg [0..90, 모드 1, 90/프레임], NiceBallDamageBlendRt [데이터].


**r8 정정(2026-10-03)**: rate0은 새 값 즉시 갱신, mode1은 도 단위·mode2는 라디안 각도 감기다. 새3997c10 원본2048/2048, 기존3997de0 전체 캐시/반환1536/1536 비트 일치로 확인했다. 정확한 식·스텁·한계는 [asb_float_parameter.md §3~§11](asb_float_parameter.md). 기존 참조태그 판독 성과를 새 확정으로 재계상하지 않았다.

### 2.8 부착 목록 — Event·FrameController·InitialFrame 이 붙는 곳 [판독+데이터]

종류 10/12/19 는 커맨드 트리의 자식이 아니라 **애니 잎(3/11/18) 본문의 부착 목록**으로 붙는다: `u8 이벤트 수, u8 0, u8 제어 수, u8 제어 시작 | 오프셋[n] → u32 노드 번호`. 엔진: 이벤트 루프 0x71039bc060(→0x71039c6d98), 진입·전진 0x71039bc994/0x71039bcdbc 가 제어 그룹에서 종류 12 를 찾아 0x71039c9ac4/0x71039c94e0, 종류 19 는 0x71039c9fcc.

| ASB | 잎 노드 | 붙은 노드 |
|---|---|---|
| 사람 | ToHumanStandby_*(58~60, 171), Emote_@ / _EdWait(78, 79) | Event 172, 180, 265 |
| 사람 | Shop_Wait_Rllr/Nrml/Strn(262, 287, 288) | Event 285, 289 + InitialFrame 263 |
| 사람 | TurnLeft/RightWall_SuperHook(389, 390) | FrameController 391, 392 |
| 오징어 | 36/37/38(DirectAnimName 스켈/재질/가시성) | Event 40 + FrameController 39 |

## 3. 클립 이름 치환 — `_Nrml` 과 `@` [판독]

ASB 안 클립 이름은 `WaitHold_Nrml`, `Shoot_Nrml`, `Emote_@` 처럼 **자리표시자**를 쓴다. bfres 에는 `WaitHold_Nrml` 이 없고 `WaitHold_Shtr`, `WaitHold_Rllr` … 가 있다(Player00 의 `_Nrml` 클립은 `Jump_Nrml00*` 3개뿐) [데이터].

0x710244d0b0 이 AS 변형 키 `WeaponVariation`, `EmoteVariation`, `AnimationDriven` 을 다루며, 문자열 치환 함수 0x710351c964 에 (패턴, 치환값)을 넘긴다 [판독]:

| 패턴 | 치환값 | 기본값 |
|---|---|---|
| `Nrml` | 무기 변형 문자열(this+0x18 / this+0x10) | `Shtr` |
| `@` | 이모트 변형(this+0x20) | `Win01` |

같은 함수에 무기 분류 문자열 `BBll, Slsh, Glng, Spnr, Brush→Brsh, Twins→Mnvr, Umbrella→Shlt` 이 나온다(무기 클래스명 → 애니 약어 대응으로 보임) [판독: 문자열, 추정: 대응]. 전체 대응 표는 [미확정].

- **정정(2026-10-03):** 위 문자열 쌍은 무기 클래스명 → 약어 대응표가 아니다. 원래 이름의 문자열을 바꿔 다시 찾는 **대체 후보 사슬**이다(§3.1). 이유: 0x710244d0b0 전체 디컴파일(`analysis/decomp/r5_gfx_char/binder.c` 640행~)과 원본 실행 2210/2210 일치.

웹 규칙: `clipName = asbName.replace('Nrml', weaponAbbr || 'Shtr').replace('@', emoteVar || 'Win01')`. 치환 결과 클립이 없을 때의 대체 규칙은 [미확정].

- **정정(2026-10-03):** 위 웹 규칙은 근사다. 원본 규칙은 §3.1의 후보 순서이고, 대체 규칙도 §3.1에서 확정했다 [판독]+[실행].

### 3.1 이름 해석 순서와 대체 규칙 — 0x710244d0b0 [판독]+[실행]

**해석기 객체.** 사람 AS 래퍼(0x5e8 B, 생성 0x710244e18c) +0x40 에 해석기가 있다. vtable 은 0x71056328f8 이고, 슬롯 2 가 0x710244d0b0 이다. 해석기 필드는 다음과 같다.

| 해석기 기준 | 래퍼 기준 | 내용 | writer |
|---|---|---|---|
| +0x08 | +0x48 | 바인더(vt 0x7105632770). 슬롯 3 0x710244b414 = 이름 → 애니 순번(종류 0 스켈레탈, 1/2 재질, 3 가시성) | 0x710243d01c |
| +0x10 | +0x50 | WeaponCategory 문자열 | 0x71024477b4 (`래퍼[10] = *cat`) |
| +0x18 | +0x58 | WeaponDetail 문자열 | 0x71024477b4 (`래퍼[11] = *detail`) |
| +0x20 | +0x60 | 이모트 변형 문자열 | 미추적 |
| +0x28~+0x38 | | 결과 이름 고리 버퍼(항목 0x58 B, 0x710244dfc4) | 해석기 |
| +0x1a8/+0x1b0 | | 직전 입력 이름(캐시) | 해석기 |
| +0x1f8/+0x1f9/+0x1fa/+0x1fc | | 직전 키 플래그(Weapon/Emote/종류 바이트/무효화) | 해석기 |

같은 0x71024477b4 가 사람 래퍼 +0x250/+0x258(두 번째 해석기, 슬롯 1용으로 보임 [추정])에도 같은 두 문자열을 쓴다. 블랙보드 문자열 `WeaponCategory`(0x710497b31a)·`WeaponDetail`(0x71048c5831)에도 같은 값을 쓴다 [판독].

**값의 출처.** 무기 갱신 0x7102491758 이 무기 객체 vt+0x230(슬롯 70)으로 두 문자열을 받아 0x71024477b4 로 넘긴다(호출 0x7102491940). `spl::WeaponShooter`(vt 0x7105652468) 슬롯 70 = 0x710289bffc 는 두 문자열 모두에 `"Shtr"`(0x71048e13bd)를 4글자 이내로 복사한다. 따라서 **슈터는 WeaponCategory = WeaponDetail = `Shtr`**이다 [판독]. 다른 무기 클래스(예: `spl::WeaponBrush` vt 0x7105650548 슬롯 70 = 0x7102875d4c)의 값은 이번에 읽지 않았다.

**해석 순서.** 입력은 (원래 이름 N, 키 목록 K, 종류 바이트 k)이다. 바인더 조회 함수에는 `k ^ 1` 이 종류로 넘어간다. 후보는 매번 **원래 이름 N 에서 새로 치환**한다(누적 치환이 아님). 각 후보는 63자에서 자른다. 처음으로 찾은 후보를 돌려준다.

```
if "WeaponVariation" ∈ K:
    try N.replace("Nrml", WeaponDetail)        # 해석기+0x18
    try N.replace("Nrml", WeaponCategory)      # 해석기+0x10
if "EmoteVariation" ∈ K:
    try N.replace("@", 이모트 변형)             # 해석기+0x20
    try N.replace("@", "Win01")
for (a, b) in [("BBll","Slsh"), ("Glng","Spnr"), ("Brush","Brsh"), ("Twins","Mnvr"), ("Umbrella","Shlt"), ("Nrml","Shtr")]:
    try N.replace(a, b)
return N                                        # 모두 실패: 원래 이름 그대로
```

`AnimationDriven` 키는 해석기 +0x1fb 플래그만 세운다. 직전 호출과 키 플래그·종류·이름이 모두 같고 +0x1fc 가 0 이면 다시 찾지 않고 캐시를 돌려준다 [판독].

**모든 후보가 실패할 때.** 해석기는 원래 이름(`…_Nrml`)을 돌려준다. 바인더가 다시 실패하면 스켈레탈 잎 진입 0x71039d3608 은 재생 엔트리를 만들지 않는다. 인스턴스 +0x92(엔트리 번호)에는 아무것도 쓰지 않는다(찾았을 때만 기록; 디버그 출력(`Slot[%s]` 문자열 함수, r4_asnode.c 1300행 부근)은 +0x92 < 0 이면 프레임 정보를 생략한다). 인스턴스 +0x96 에 bit0 을 세우고, 노드 레코드 중 타입 3 이 있으면 0x20 도 세운다(0x71039d3a14). 레코드 타입 3 이 없으면 `"%s.as"` 형식 문자열을 지역 버퍼에 만든 뒤 bit0 만 세운다. bit0 은 부모 노드로 올라가는 "끝남" 표시다(예: FloatBlend 진행 0x71039c8d30 의 `if (child == 0 || child.flags & 1) self.flags |= 1`, r4_asnode.c 954행) [판독]. 즉 **다른 동작 클립으로 바꿔 재생하는 대체는 없다.** 그 잎이 최종 포즈에 주는 기여(가중 0인지, 바인드 포즈인지)는 포즈 합성 0x71039cd350 을 읽지 않아 [미확정]이다.

**`WalkBackHold_Shtr` 사례.** `WalkBackHold` 커맨드의 잎은 `WalkBackHold_Nrml` 하나다(노드 122). 슈터 값으로 조회하는 순서는 `WalkBackHold_Shtr`(Detail) → `WalkBackHold_Shtr`(Category) → (사슬 앞 5개는 일치 문자열이 없어 `WalkBackHold_Nrml` 그대로) → `WalkBackHold_Shtr` → 반환 `WalkBackHold_Nrml` 이다. Player00 에는 이 클립이 없으므로 위의 "모두 실패" 경로를 탄다 [실행: 원본 해석기 + Player00 클립 1044개 집합].

**도달 여부.** `WalkBackHold` 를 쓰는 상태는 0x46(슬롯 1)과 0x66(슬롯 0)이다.
- 0x66 은 뒤 걷기 선택 0x710244a930 에서 무기 종류 K == 0x16 일 때만 반환된다. 그 밖의 무기는 기본 0x69 `WalkBackShoot` 이다.
- 0x46 은 슬롯 1 대응 0x710244ab70 에서 사분면(B+0x720) == 1 이고 슬롯 0 상태 == 0x66 일 때만 나온다(0x710244afc8~0x710244afdc).
- 사람 상태 코드(0x7102430000~0x71024d0000)에서 상수 0x46/0x66 을 쓰는 곳은 이 두 곳과 SM+0xf0 상한(0x7102440910)뿐이다 [판독: 명령 스캔].

따라서 **슈터(K ≠ 0x16)는 사격장에서 `WalkBackHold` 를 요청하지 않는다.** 뒤로 걸으면 0x69 `WalkBackShoot` 이고, 클립은 `WalkBackShoot_Shtr`/`RunBackShoot_Shtr`(노드 17 FloatBlend, 둘 다 Player00 에 있음)이다 [판독+데이터]. 슈터 K 의 정확한 값은 [추정: player_state.md 의 1/2/8]이지만, 0x16 은 10+스페셜 열거 쪽이라 메인 무기 값이 아니다.

**검증.** `PY web/tools/r5_gfx_char_clipname_emu.py` → `analysis/completion/r5/gfx_char_clipname_emu.json`.
- 원본 0x710244d0b0 을 unicorn 으로 실행했다. 문자열 치환 0x710351c964 와 캐시 0x710244dfc4 도 원본 그대로 실행했다. PLT 는 memcpy/memmove/memcmp/strlen 만 파이썬으로 처리했다.
- 스텁은 바인더 조회(vt+0x18) 하나다. 넘어온 이름을 기록하고, 주어진 클립 집합에 있으면 0, 없으면 −1 을 돌려준다.
- 비교 대상은 판독으로 독립 작성한 후보식(`resolve`)이다. 조회한 이름의 순서·종류 인자·최종 반환 이름이 모두 같아야 일치로 센다.
- 실제 사람 ASB 잎 이름 전부 × 키 조합 5종 × (Shtr, Shtr, Win01) × Player00 클립 집합, 그리고 합성 이름 8종 × 변형 3벌 × 키 5종 × "후보 k 번째만 존재" × 종류 바이트 0/1: **2210/2210 일치** [실행].
- 실행하지 않은 범위: 실제 바인더 사전 조회(0x710244b414 → 0x71036c29ec), 잎 진입 0x71039d3608, ASB 노드에서 키 목록이 만들어지는 경로.

## 4. 게임 → ASB 연결 [판독]

```
상태기계 SM(본체+0xa8c8)
  SM+0x08 사람 래퍼 { AS 객체, 슬롯 0 = 전신, 슬롯 1 = 보조(상체) }
  SM+0x10 오징어 래퍼
  SM+0x18 활성 래퍼
요청(0x7102451a90 슬롯0 / 0x71024521b0 슬롯1):
  name = 상태표[state].human or .squid
  slot.blendFrames(+0xdc) = 상태표 블렌드 값(또는 0/2/4/8 덮어쓰기)
  slot.rate(+0xd4) = 1.0, 이후 0x7102450510 이 요청 속도(rate)로 다시 씀
  0x710399e340(-1, -1, AS, &name, 슬롯, 0, 0, 0)
진행 조회: 슬롯+0x30(현재 프레임), 0x710245064c(끝 프레임, 노드 vt+0x38)
```

두 모델 전환(ToSquid/ToHuman)은 [../player/player_state.md §6](../player/player_state.md) — 사람 ToSquid 클립이 끝나기 3프레임 전에 오징어 ASB 로 넘어간다.

### 4.1 재생 엔트리와 프레임 전진 [판독]

애니 잎 진입(종류 3 vt+0xa8 = 0x71039d3608)이 슬롯 엔트리 표(슬롯 +0x178, 0x40 B, 번호 inst+0x92)에 엔트리를 만든다(0x71039bc994).

| 엔트리 | 내용 |
|---|---|
| +0x00 | 플래그(bit1 반복, bit3 한 번 건너뜀) |
| +0x04 / +0x08 | cur / prev |
| +0x0c | rate (1.0, FrameController 가 덮음) |
| +0x10 | 최소 프레임 |
| +0x14 | **end = (f32) FSKA FrameCount** |
| +0x20 | loopStart |
| +0x24 | 누적 |
| +0x28 | endOverride (−1 = 없음) |
| +0x34 | animIdx |

`end` 출처: 진입 함수가 애니 바인더(0x710243d01c 가 만드는 0x10 B, vtable 0x7105632770)의 슬롯 4 0x710244b55c 로 받은 `scvtf(*(s32*)(res+0x40))`(스켈레탈) — FSKA 의 FrameCount(+0x40). 반복 여부는 슬롯 5 0x710244b614 = `res+4 bit2`(FSKA Looping 플래그) [판독 + 데이터: BfresLibrary v9+ FSKA 배치와 일치]. 즉 **끝 프레임 = FrameCount (FrameCount−1 아님)**.

전진 0x71039ab2c4 (0x71039bcdbc 가 `dt × 슬롯 rate(+0xd4)` 로 호출):

```
if (e.flags & 8) { e.flags &= ~0x18; return }          // 한 번 건너뜀(진입 직후 등)
e.prev = e.cur
f = round4(e.cur + e.rate * dt * slotRate)             // round4(x) = round(x*1e4)/1e4
stop = e.endOverride < 0 ? e.end : e.endOverride
e.cur = f
if (f >= e.end) {
  if (!loop && f >= stop) e.cur = stop                  // 비반복: end 에서 멈춤
  else if (e.end > e.loopStart) {
    len = e.end - e.loopStart
    e.cur = round4(f - (f >= 2*len ? len*trunc(f/len) : len))
  } else e.cur = stop
}
```

### 4.2 끝 프레임 조회와 한 프레임 안의 순서 [판독]

- 끝 프레임: 0x710245064c → 활성 노드 vt+0x38. 종류 3 = 0x71039d44ac 가 `entries[inst+0x92].end` 반환, 기본 0x71039bd93c 는 활성 자식(inst+0x91, +0x8[4]/+0x30[4])에게 넘긴다.
- 게임이 보는 cur: 슬롯 처리 0x7103996d84 가 먼저 전진(0x71039ccc4c → 종류 3 vt+0xb0 → 0x71039bcdbc)하고, 다음에 보고(0x71039cd350 → vt+0xc8 0x71039d3dcc 가 entry.cur 를 씀) → 슬롯 +0x104. 래퍼 갱신 0x71024507a8 이 엔진 틱 0x710399f848 뒤에 `래퍼+0x30[i] = 슬롯i+0x104` 로 복사(0x7102450c94~0x7102450d68).
- 순서: 상태기계 0x710243e7d0 의 0x710243ea00~ea30 이 `cur = 래퍼+0x30[slot]`, `end = 0x710245064c`, `cur + 3 > end` 면 다음 단계 → 함수 끝(0x7102440d6c/0x7102440d78)에서 사람·오징어 래퍼 모두 0x71024507a8(dt = SM+0x204) 로 틱. **판정은 직전 프레임에 전진을 마친 cur 로 한다.**
- 커맨드 요청 프레임: 0x710399e340 → 진입(cur = 0, 0x71039bcdbc 를 인자5 = 1 로 불러 전진 없음) → 0x710399ec94 → 0x7103997558 보고. 같은 프레임 뒤쪽 틱에서 전진해 cur = 1 [판독: 경로, 실행 검증 없음].
  - **정정(2026-10-03 r8) [실행:범위]:** 위의 “실행 검증 없음”은 기본 kind3·FrameController/InitialFrame 부착 없음인 요청→첫 tick→슬롯/래퍼 보고 연결에 대해 해소했다. 원본399E340 요청은 cur0/prev−1·slot1040으로 진입·보고하고39BCDBC의x4=1 경로에서 전진39AB2C4를 호출하지 않는다. 이어 원본399F848 첫 tick은x4=0→39AB2C4 전진→39D3DCC 보고를 수행한다. 원본2450C94..2450D6C 복사 구간도 wrapper30=slot104에 일치했다. ToSquid6/rate1/dt1 기본 사례는0→1이며, 요청·첫 tick 각1,025건과래퍼복사1,025구간/9,225개 f32필드가 bit mismatch0이었다. [as_request_first_tick.md §3~§11](as_request_first_tick.md)에 메타데이터·output capacity0·guard/memcpy 경계를 기록했다.
  - **실행 범위:** 24507A8 전체·상태 전환 predicate·실제 클립 로더·출력 포즈 합성은 실행하지 않았다. 연속 두 번째 tick은 slot168 pool pointer fixture가 없어3997080에서 실패했고 성공 건수에 포함하지 않았다. 아래 S+4 및 화면 프레임1..4 예는 기존 판독 기반 계산이며 이번 첫 tick 실행만으로 전체 수명/화면 검증으로 올리지 않는다. 전체 혼합 질문은 조사중이다.
- 예(사람 ToSquid, FrameCount 6, rate 1, dt 1): 요청 프레임 S 의 틱 뒤 cur = 1 → S+4 프레임 처음에 cur = 4, `4 + 3 > 6` → 0x84(오징어 ToSquid). 화면에 나가는 사람 클립 프레임은 1, 2, 3, 4 [판독 기반 계산]. ±1 문제의 답: end 는 FrameCount, 판정은 틱 전 cur.
- 래퍼 +0x5d7(슬롯 0) / +0x5d8(슬롯 1)이 켜지면 그 틱 동안 슬롯 rate 를 0 으로 두고 되돌린다(일시정지). dt(SM+0x204) 설정은 vtable 0x7105630208 의 0x710243a45c, 기본값 [미확정].
  - **정정(2026-10-03 r8) [실행]+[판독]:** SM+204 기본값은 **1.0f(3F800000)**, +208=0이다. 기존 생성자24397BC의 실제entry부터2439D08 actor778 연결까지 실행했다. 더럽힌 allocation24건 모두 원본store2439D00이1.0/0을 쓰고 같은 SM을 연결했다. 실제 PlayerVT562FF08+300=243A45C로 엔진 phase whole/prefix512건도 dt×actor4D8 및 gate에 일치했다. 모델 생성/메모리 서비스가 실행 경계이며 라이브 phase dt=1·actor 배율 기본1까지 확정한 결과는 아니다. 도구 `r8_camweapon_sm_dt_emu.py`, 근거 `analysis/completion/r8/sm_dt_support.md`·`sm_dt_emu.json`. 이 단일 기본값 질문은 해소하고 §6 블랙보드 공급 전체 묶음은 남긴다.
  - **추가(2026-10-03 r6) [판독]:** 0x710243a45c 는 `플레이어+0x778(SM)+0x204 = s0` 한 줄이다. 이것을 담은 칸은 0x7105630208 = 플레이어 vtable +0x300 이다. main 전체에서 `ldr x,[x,#0x300]; blr` 16곳 중 액터 갱신 0x7100f76a78(0x7100f76c04)과 0x7100f76f78(0x7100f77174)이 부른다. 둘 다 액터 +0x4cc bit1 일 때만 부르며(플레이어 초기화가 +0x4cc |= 0xfa), 넘기는 값은 같은 프레임 AS 틱(0x710399f848)에 넘기는 `단계 정보+4 × 액터+0x4d8` 이다(0x7100f76bac/0x7100f77120 `fmul`). 즉 **SM+0x204 = 엔진 단계 dt × 액터 시간 배율**이다. 단계 정보 +4 의 실행 중 값(정상 1.0 으로 보임)과 +0x4d8 기본값은 [미확정]이다.

### 4.3 FrameController (종류 12) [판독: 0x71039c9140, 값 목록 vt+0x98 0x71039c9ccc]

| 본문 | 대상 |
|---|---|
| +0x00 | rate → entry +0x0c |
| +0x08 | 시작 / loopStart |
| +0x10 | end (−1 이면 FrameCount) |
| +0x18 | u32 모드: 1/3/4 = 반복, 2 = 1회, 0 = 클립 자체 플래그 |
| +0x2c / +0x34 | 반복 횟수(있으면 endOverride = end × n) |
| +0x54 | 반복 끝 |

오징어 39: rate 1.0, start = bb `DirectAnimStartFrm`, end = bb `DirectAnimEndFrm`(기본 −1) [데이터].

### 4.4 FloatBlend (종류 6) [판독: 0x71039c890c]

```
x = 값 슬롯(보통 실수 파라미터 표 §2.7)
자식 항목마다 [lo(+4), hi(+0xc)]
i = lo <= x < hi 인 첫 자식
if (자식 i, i+1 구간이 겹침) {
  w = (x - max(lo_i, lo_i1)) / (min(hi_i, hi_i1) - max(lo_i, lo_i1))
  if (w < 0.01) w = 0; if (w > 0.99) w = 1
  if (본문+8 == 1) w = smoothstep(smoothstep(w))
  pose = mix(child_i, child_i1, w)
} else 범위 밖: 마지막 자식(또는 0번)만
```

사람 34개 [데이터]: 26개 (0,1)/(0,1), ShotPitRt 4자식 1개 (−1,0)/(−1,0)/(0,1)/(0,1), Stringer 7개 (0,90)/(0,90). 본문+8 은 전부 0 → **선형**. **정정(2026-10-03 r8):** 두 자식의 정규화 진행률 전달과 원본 프레임 소비는 [노드 제어](asb_node_runtime.md) §3~§10에서 [판독]+[실행]으로 확정했다.
  - **정정(2026-10-03 r6) [판독]:** 다음 주소로 적었던 0x71039bcb9c 는 동기화 함수가 아니다. 잎 노드의 부착 목록에서 첫 InitialFrame(종류 0x13)·첫 FrameController(종류 0xc) 번호를 인스턴스 +0x58/+0x5a 에 두고, 나머지 부착을 목록에 넣는 수집 함수다(조건: 부착 레코드 +0xf4 bit1 이면 0x71039bc378 필터). 자식 동기화는 여전히 [미확정]이고 다음에 볼 곳은 FloatBlend 진행 0x71039c8d30 이다.

### 4.5 상태 전환 블렌드 [판독: 0x710399728c]

```
B = 노드 레코드 타입0 값(>= 0) 이 있으면 그것, 없으면 slot.blendFrames(+0xdc)   // 0x7103997358, 0x71039d452c
if (B < 0.01 || slot.res+0x100 == 1) 즉시(w = 1)
else { t = 0; step = 1/B }
매 틱: t += step * dt                         // 슬롯 rate 를 곱하지 않은 원 dt
   w = slot.linear(+0x192) ? t : (t < 0.5 ? 2t² : 1 - 2(1-t)²)   // 기본은 ease-in-out 2차
   f = 1 - (1-w)/(1-wPrev)                     // +0x18c, 직전 출력 대비 증분 계수
   t >= 1 → 블렌드 끝
```

이전 애니는 최대 4층(holder +0x8[4])까지 계속 재생되며 `(1−w)` 로 줄어든다고 본다 [추정]. 포즈 합성 자체(0x71039cd350, 0x71039be4a0, 0x71039bf1b8)는 [미확정].
  - **추가(2026-10-03 r6) [판독]:** 0x71039cd350 은 포즈를 섞지 않는다. 층(인스턴스 +0x8[4] 자식, +0x30[4] 가중 블록)마다 다음을 한다.
    - 블록 +0x74/+0x80/+0x8c(가중 3채널) = 부모 값 × 블록 +0x6c/+0x78/+0x84 로 내려보낸다.
    - 자식 vt+0x68(보고)을 부른다.
    - 자식 블록 +0xa8 > 0 이면 `Σ(+0xa8 · +0x6c) / Σ(+0x6c)` 를 인스턴스 +0xa8 에 쓴다.
    - 활성 층(+0x91)의 현재 프레임을 인자+0x24 로 올린다.
    
    즉 이 함수는 가중치 전파와 진행률 보고다. 엔트리 없는 잎은 블록 +0xa8 이 0 이라 진행률 평균에서 빠진다. 그 잎의 가중치가 최종 포즈 샘플러에서 어떻게 쓰이는지(정규화 여부)는 여전히 [미확정]이다.
  - 0x71039be4a0 은 전환 때 이전/다음 커맨드를 층 0~3 에 배정하고 가중 (1−w, w)를 적는 함수다(빈 층은 0x71039bbe40 으로 새로 만들고 +0x91 = 활성 층) [판독]. 0x71039bf1b8 은 인자 s0 < 0 이면 인스턴스 +0xa8 을 +0xac 로 옮기고, 부착 레코드를 초기화한 뒤 전역 sead::Random(*0x7105997950) 다음 u32 를 인자3+0x28 에 쓴다 [판독]. InitialFrame 방식 3(무작위 시작)과의 연결은 [미확정]이다.

### 4.6 블랙보드 값 공급 [판독: 0x710246cb58]

상태기계 0x710243e7d0 의 0x71024404d4 에서 호출. 사람·오징어 래퍼 둘 다에 `AS+0x40` 의 vt+0x38(실수)/+0x40(bool)/+0x28(문자열)로 쓴다.

| 이름 | 값 |
|---|---|
| MoveSpeedRt | SM+0xe0. 0x7102446dfc 에서 `e0 += k·(목표 − e0)`, 주 경로 k = 0.2, 목표 = clamp((SM+0xd4 − 0.027)/0.023, 0, 1)(SM+0xd4 = 0x710246d060 속력). 사람 이동 상태 0x5e~0x81 이 아니면 0. 다른 분기 [부분 판독]. 7차 보완(2026-10-03): 슈터 WalkDamage에서는 목표 0, 앞·뒤/옆 걷기의 AS 슬롯 rate는 서로 다른 상수와 SM+0xe4=1.25를 사용한다. [player_state.md §6.3.1](../player/player_state.md) [실행]+[판독]. |
| StartLaunchLandingBlendRt | min(SM+0x110/60, 1). SM+0x110 은 매 프레임 −1, 상태 0xbf 끝에 120(0x710244240c). ASB 는 참조하지 않음 [데이터] |
| EquipWeaponMain | 본체+0x588 무기 분류의 +0xd0/+0xd4 ≠ 0 |
| ShotPitRt | 0x71024c9824 결과에 따라 본체+0x538 객체 +0x48/+0x44/+0xc 중 하나 |
| StringerTiltDeg | 무기 분류 0xa 일 때만 본체+0xa780→+0xa0 |
| NiceBallDamageBlendRt | 스페셜 0x12 일 때 본체+0xa5b0→+0x310 의 (+0x84/+0x80) 비율의 지수 변환 [부분 판독] |
| WeaponCategory / WeaponDetail | 0x71024477b4 가 인자 문자열 저장(+0x250/+0x258) 후 기록. 호출자 4곳의 값 [미확정]. **정정(2026-10-03):** 0x71024477b4 는 사람 래퍼 +0x50/+0x58(해석기 +0x10/+0x18)과 +0x250/+0x258 에 쓴다. 무기 갱신 0x7102491758 이 무기 vt+0x230 으로 값을 받는다. 슈터(`spl::WeaponShooter` 슬롯 70 0x710289bffc)는 둘 다 `Shtr` [판독] — §3.1. 나머지 호출자 0x710249cfc8·0x71024bb548 와 다른 무기 클래스의 값은 [미확정] |
| JumpVarID | 0x710243dcf8, 0x710244128c 가 기록, 출처 [미확정]. **확정(2026-10-03 r6) [판독]:** 값은 활성 래퍼(SM+0x18)+0x10 의 정수이고 블랙보드 vt+0x30 으로 같이 쓴다. 초기화 0x710243dcf8(0x710243e0a4)이 0 으로 둔다. 상태 적용 0x710244128c 는 새 상태 S ∈ 0x99..0xa9 일 때만 고친다. (1) 본체+0x1054 == 0 이면 SM+0xd4(속력) ≤ 0.03, 아니면 본체+0x47c ≤ 0.5 일 때 0. (2) 메인 무기 종류 K(B+0x588 == B+0x590 이면 B+0x658, 아니면 B+0x65c)가 {4,5,6,7,9,10,11,13,16,17,19,20,21,22,24,25,29,30}(마스크 0x0637b2ef, K−4 < 27)이면 0. (3) 그 밖에는 이전 상태 C(SM+0xc8)와 S 로 "유지/새로"를 고른다. C ∈ {0x99,0x9a} 이면 S ∈ {0x99,0x9a} 또는 0x9b..0x9f 일 때 유지, C ∈ 0x9b..0x9f 이면 S ∈ 0xa6..0xa9 또는 0x9b..0x9f 일 때 유지, C ∈ 0xa0..0xa5 이면 S ∈ 0xa0..0xa5 일 때 유지, 그 밖에는 C·S 둘 다 0xa6..0xa9 일 때 유지한다. 나머지는 "새로"다. "새로" = `이전 % 2 + 1`(0→1, 1→2, 2→1, **난수 아님**)이고, S == 0x9a 이고 SM+0x200 < 0x5b 이면 0 이다. 슈터(K = 1/2/8 [추정])는 (2)에 걸리지 않으므로 이동 점프마다 1·2 를 번갈아 쓴다 |
| DirectAnimName | 0x71024525c4(호출 0x710244850c) |
| StainFrm | 유일한 쓰기 0x710248c8d8 이 0.0 |
| WalkAnimSpeed | main 문자열에 없고 두 ASB 어느 노드도 참조 안 함 → 웹에서 생략 가능 [데이터] |

## 5. 웹 포팅

| 모듈 | 책임 |
|---|---|
| `AsbLoader` | `state_asb.py --json` 출력(커맨드·노드·자식)을 빌드 시 JSON 으로 변환 |
| `AsbEvaluator` | 커맨드 → 트리 평가: Selector 는 블랙보드 값으로 자식 하나, FloatBlend 는 §4.4 구간 가중, Simultaneous 는 동시 재생, Sequence 는 순차. 잎의 부착 목록(§2.8) 처리: FrameController 로 구간·rate 덮어쓰기, Event 발화, InitialFrame |
| `AnimSlot` | 슬롯 0/1. 엔트리(§4.1)로 cur/end/rate 관리, round4 전진, 비반복은 end(=FrameCount)에서 정지. 전환 블렌드는 §4.5(기본 ease-in-out 2차, 원 dt) |
| `AnimBlackboard` | §4.6 공급 규칙, 실수 파라미터 표(§2.7)의 변화율 제한·clamp |
| `ClipNameResolver` | `Nrml`/`@` 치환. 원본 후보 순서(Detail → Category → 이모트 → `Win01` → 사슬 6개 → 원래 이름)는 §3.1. 모두 없으면 그 잎은 재생 엔트리 없음 |

갱신 순서(원본과 같게): 상태기계 판정(직전 cur 사용) → 블랙보드 공급(0x710246cb58) → 사람·오징어 래퍼 틱(전진 → cur 복사). 요청 프레임에는 cur = 0 으로 진입 후 같은 프레임 틱에서 1 이 된다.

검증 기대값(데이터): 오징어 `Wait` → `Sqd_Wait`(스켈레탈 120f 반복) + `Sqd_Wait`(재질); 사람 `WalkHold` → BoolSelector → FloatBlend(`WalkHold_<무기>`, `RunHold_<무기>`) 또는 `Walk`/`Run`.

## 6. 미확정과 필요한 근거

| 항목 | 상태 / 필요한 것 |
|---|---|
| ~~노드 종류 10/12/19~~ | 해소: Event / FrameController / InitialFrame, 잎 노드 부착 목록(§2.5, §2.8). r8 정정(2026-10-03): Event 발화 구간은 [asb_event_runtime.md](asb_event_runtime.md) §6/§10에서 해소(점 2048·구간 2048 원본 실행). 남은 것: BAEV 파일 전체 섹션 및 InitialFrame 방식 3(점프표 0x7104af3296) |
| ~~블렌드 곡선, FloatBlend 가중~~ | 해소: §4.4, §4.5. 남은 것: 다층 포즈 합성(0x71039cd350, 0x71039be4a0, 0x71039bf1b8), FloatBlend 자식 프레임 동기화(0x71039bcb9c) |
| ↳ 갱신(2026-10-03 r6) | 0x71039cd350 = 층 가중 전파·진행률 보고(포즈 합성 아님), 0x71039bcb9c = 부착 수집(동기화 아님) — §4.4·§4.5 정정. 포즈 샘플러 쪽 정규화와 자식 동기화(0x71039c8d30)는 [미확정] |
| ~~끝 프레임·±1~~ | 해소: end = FSKA FrameCount, 판정은 틱 전 cur(§4.2). 요청 프레임 첫 틱 전진은 경로 판독만(실행 검증 없음) |
| ↳ 정정(2026-10-03 r8) | 기본 kind3/noattachment 요청→첫 tick→프레임 보고는 원본1,025건/9,225f32 bit0으로 보강(§4.2, [as_request_first_tick.md](as_request_first_tick.md)). 연속 두 번째 tick pool fixture 실패·복합 FrameController/InitialFrame·전체포즈는 남아 조사중 유지 |
| 블랙보드 공급 | 대부분 해소(§4.6). 남은 것: WeaponCategory/WeaponDetail 호출자 값(슈터는 `Shtr`/`Shtr` 로 해소, §3.1), JumpVarID 출처, MoveSpeedRt 나머지 분기·애니 rate 표(state_big_full.c 2725~2985행), SM+0x204 기본값 |
| ↳ 갱신(2026-10-03 r6) | JumpVarID 규칙 해소(§4.6), SM+0x204 writer = 엔진 액터 갱신이 플레이어 vt+0x300 으로 넘기는 dt × 액터+0x4d8(§4.2). 남은 것: 다른 무기의 Category/Detail, MoveSpeedRt 나머지 분기, 단계 dt 실행값 |
| ~~BoolSelector 자식 순서·IntSelector 기본~~ | 해소(2026-10-03): 참 → 자식 0, IntSelector 는 마지막 자식이 기본 [실행 130/130], §2.5. 남은 것: 재평가 세대 값(인자2+0xd0/인스턴스+0xa0) |
| ~~클립 이름 대체 규칙~~ | 해소(2026-10-03): 후보 순서·실패 시 엔트리 없음 [판독]+[실행 2210/2210], §3.1. 남은 것: 엔트리 없는 잎의 포즈 기여(0x71039cd350), 키 목록 출처(노드 → 해석기 인자) |
| 노드 표 +0x0c, 헤더 나머지 섹션 | 섹션별 덤프 비교 |
| 이벤트 AnimationEvent/AsNode/*.baev 연결 | baev 형식 판독 |

참고: `romfs/Sound/*.baatarc`, `*.bagst` 는 사운드 감쇠·그룹 설정이며 애니와 무관하다 [데이터: 경로 `/Sound/Attenuation/`, `/Sound/Group/`].

2026-10-03 7차 보완: §4.6 및 잔여 표의 MoveSpeedRt 나머지 분기·애니 rate 질문은 **슈터 범위에서 해소**했다. 걷기 5515 입력·1440 연속 프레임, 보조 선택과 NG 판정 각각 6640건, Jump_St 요청 1152건을 원본 실행과 대조했다. [player_state.md §6.3.1~§6.3.3 및 §11](../player/player_state.md)에 식·순서·스텁을 기록했다. 다른 무기의 Category/Detail·rate와 전체 애니 그래프 연결 실행은 별도 미확정이다.

2026-10-03 r8 추가: FloatBlend 동기화·Sequence 진행은 [asb_node_runtime.md](asb_node_runtime.md)에서 해소했다. 종전 §6의 포즈 합성/동기화 혼합 질문은 포즈 합성이 남아 있으므로 전체 완료로 올리지 않는다.

### 11.8 SM 기본 dt 실행 정정 — 2026-10-03 r8

[실행]+[판독] §4.2의 SM204 기본값 미확정은 생성자store2439D00·actor778 연결2439D08 원본prefix24건으로 해소했다. 실행 중 덮어쓰기는 실제setter512건과 기존r6producer를 대조했다. 명령·실패·실행 경계는 `analysis/completion/r8/sm_dt_support.md`·`sm_dt_emu.json`. 초단위1/60을 기본 SM 프레임dt로 쓰는 근사는 바꿔야 한다. 라이브 단계dt/actor시간배율 기본·다층pose 등은 미확정이며 전체블랙보드 질문을 승격하지 않는다.

### 4.6.1 WeaponCategory/Detail 네 호출자 값 — 2026-10-03 정정 [판독]+[실행:구간]

기존§4.6의네caller미확정은 [animation_weapon_blackboard.md](animation_weapon_blackboard.md) §3–10의새2491758/24BB240전체판독·네원본source구간1024건으로해소했다. 2491940/249CFC8/24BB548은선택된무기의실제vt230에서슈터Shtr/Shtr을받고,24919C8은선택holder null전환에서empty/empty를쓴다. null의호출생략과empty공급을구분한다. 기존r5슈터getter/sink/이름대체는재사용. 전체caller생명주기/다른무기/다층포즈는별도미확정유지하며복합L277을이결과로승격하지않는다.


### 11.9 요청→첫 tick 실행 보강 — 2026-10-03 r8

[실행:범위] camera_weapon 담당이 저장한 신규399E340→399F848 전체 경로와2450C94..2450D6C 원본복사 구간의1,025사례/9,225f32 대조를 §4.2에 연결했다. 기본 요청cur0→첫 tickcur1이며 entry/advance/traversal/report는원본을실행했다. §4.1의곱셈표기를실제f32순서로구체화하면 `step=f32(f32(dt*slotRate)*entryRate)`다. round4는FRINTA ties-away이며 NaN/Inf·역재생은검증하지않았다. end=FrameCount/상태판정틱전cur은기존근거재사용이다.

연속8tick 시도는두번째tick(slot168 pool fixture 누락, PC3997080)에서실패했다. 실패JSON은보존했고부분cur2 보고를전체성공으로세지않았다. FSKA/resource metadata 및output capacity0/clear·debugoff·guard/memcpy 경계와원본실행범위를 [as_request_first_tick.md §10~§11](as_request_first_tick.md)에명시했다. 커맨드요청순서의확정된하위결론을전체ASB포즈/상태기계의확정으로확대하지않는다. L276은조사중,신규완료항목수는증가시키지않는다. 웹코드·impl은변경하지않았다.


### 11.10 ASB 헤더 이벤트·이름 마스크 정정 — 2026-10-03 r9

[판독]+[실행]+[데이터] §2.1 header14의5/1은 이벤트 그룹 개수다. 신규39AFDFC getter→3DE0F6C의BAEV 파일 요청을 확인했다. header18의2/0은 보조 슬롯 수가 아니라 이름으로 뼈를 선택하는 마스크 그룹 개수이며 신규39AE15C/39AE544가12+8*n 가변 길이 그룹을 적용한다. 원본39AE5441,026건 호출·상태 일치와 원본 getter 실제 ASB2건은 [asb_header_runtime.md §3~§11](asb_header_runtime.md)에 기록했다. AS 슬롯 수·SDK 최종 포즈·헤더 나머지 섹션은 이 결과로 올리지 않는다.


### 11.11 r9 typed tag 정정 — 2026-10-03

§2.4의 “상위4비트8/A/D/E가 타입”은 보편 분기로 사용할 수 없다. 타입은 호출 reader가 정하고 공통 bit31=상수/참조, bit24=값칸 주소 override, float 상위2bit=3은 파라미터 표다 [판독]. 신규39CDA20의 이전 미실행 typed/override/miss를1536건 실행해 nibble8..F가 모두 정수 reader에서 같은typed API를 부름을 확인했다 [실행: 명시적getter fixture]. [asb_typed_tags.md §3~§10](asb_typed_tags.md). 기존float/string/bool 판독은 재사용이며 upstream 실제값·전체포즈 미확정은 유지한다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](../port/graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
