# 플레이어 애니메이션 상태머신 — ASB(v0x410)와 커맨드 요청

[목차](model_character.md) · 조립·클립 일반은 [player_assembly.md](player_assembly.md), 게임 쪽 상태 번호는 [../player/player_state.md](../player/player_state.md).

상태: **판독 진행 중**. ASB 헤더·커맨드·노드 목록·자식 목록은 두 파일 전수로 읽었다(아래 도구). 3차 작업에서 엔진 AS 노드 생성 루프(0x71039b17f8)·프레임 전진(0x71039ab2c4)·끝 프레임(0x71039d44ac)·전환 블렌드(0x710399728c)·FloatBlend(0x71039c890c)·블랙보드 공급(0x710246cb58)을 판독했다(§2.5, §4.1~§4.5). 디컴파일 `analysis/decomp/render/r4_asnode.c`, `r4_asnode2.c`, 노드 vtable 표 도구 `PY web/tools/render_asnode_vt.py`. 원본 실행 검증은 없다.

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
| 7 | `Sequence` | 자식 2개(`Emote_@` → `Emote_@_EdWait`) | [추정] |
| 8 | `IntSelector` | bb 정수 + (정수, 자식) | [추정] |
| 9 | `Simultaneous` | 자식 n개 동시. 끝 프레임 vt+0x38 = 0x71039d30e4 | [추정: 이름] |
| 10 | `Event` | u32 이벤트 번호(사람 0~4, 오징어 0 — 헤더 +0x14 의 5/1 과 일치). 잎 노드의 부착 목록으로 붙음. 발화 처리 0x71039c6d98 | [판독+데이터], 발화 구간 [미확정] |
| 11 | `MaterialAnim` | 재질 애니 이름(애니 잎) | [데이터] |
| 12 | `FrameController` | 잎 노드에 붙어 재생 구간·속도를 덮어씀, §4.3 | [판독: 0x71039c9140] |
| 13, 24 | 애니 잎(종류 미상) | 이 두 ASB 에 없음 | [판독: vtable 그룹] |
| 18 | `VisibilityAnim` | 가시성(뼈) 애니 이름(애니 잎) | [데이터] |
| 19 | `InitialFrame` | u32 방식 1..7: 1/2/6/7 = 이전에 재생한 같은 애니의 프레임을 이어받음, +0x20/+0x28 bool. 사람 263 은 방식 3(난수 경로 있음) | [판독: 0x71039c9fcc], 방식 3 = 무작위 시작 [추정] |
| 21 | `BoolSelector` | bb bool + 자식 2개(`WaitHold_Nrml` ↔ `Wait`) | [추정] |
| 5, 15 | 빈 노드 | 공유 vtable, 이 파일에 없음 | [판독] |

이름은 데이터 모양·동작으로 붙인 웹 권장 이름이다. 참고: TotK ASB 의 공개 노드 열거에 1 을 더한 번호가 위 관찰(애니 잎 그룹·빈 노드 쌍 포함)과 모두 맞는다 [추정: 외부 자료 대응, 이 바이너리에는 노드 이름 문자열이 없음].

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

웹 규칙: `clipName = asbName.replace('Nrml', weaponAbbr || 'Shtr').replace('@', emoteVar || 'Win01')`. 치환 결과 클립이 없을 때의 대체 규칙은 [미확정].

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
- 예(사람 ToSquid, FrameCount 6, rate 1, dt 1): 요청 프레임 S 의 틱 뒤 cur = 1 → S+4 프레임 처음에 cur = 4, `4 + 3 > 6` → 0x84(오징어 ToSquid). 화면에 나가는 사람 클립 프레임은 1, 2, 3, 4 [판독 기반 계산]. ±1 문제의 답: end 는 FrameCount, 판정은 틱 전 cur.
- 래퍼 +0x5d7(슬롯 0) / +0x5d8(슬롯 1)이 켜지면 그 틱 동안 슬롯 rate 를 0 으로 두고 되돌린다(일시정지). dt(SM+0x204) 설정은 vtable 0x7105630208 의 0x710243a45c, 기본값 [미확정].

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

사람 34개 [데이터]: 26개 (0,1)/(0,1), ShotPitRt 4자식 1개 (−1,0)/(−1,0)/(0,1)/(0,1), Stringer 7개 (0,90)/(0,90). 본문+8 은 전부 0 → **선형**. 두 자식의 프레임 동기화(0x71039bcb9c)는 [미확정].

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

### 4.6 블랙보드 값 공급 [판독: 0x710246cb58]

상태기계 0x710243e7d0 의 0x71024404d4 에서 호출. 사람·오징어 래퍼 둘 다에 `AS+0x40` 의 vt+0x38(실수)/+0x40(bool)/+0x28(문자열)로 쓴다.

| 이름 | 값 |
|---|---|
| MoveSpeedRt | SM+0xe0. 0x7102446dfc 에서 `e0 += k·(목표 − e0)`, 주 경로 k = 0.2, 목표 = clamp((SM+0xd4 − 0.027)/0.023, 0, 1)(SM+0xd4 = 0x710246d060 속력). 사람 이동 상태 0x5e~0x81 이 아니면 0. 다른 분기 [부분 판독] |
| StartLaunchLandingBlendRt | min(SM+0x110/60, 1). SM+0x110 은 매 프레임 −1, 상태 0xbf 끝에 120(0x710244240c). ASB 는 참조하지 않음 [데이터] |
| EquipWeaponMain | 본체+0x588 무기 분류의 +0xd0/+0xd4 ≠ 0 |
| ShotPitRt | 0x71024c9824 결과에 따라 본체+0x538 객체 +0x48/+0x44/+0xc 중 하나 |
| StringerTiltDeg | 무기 분류 0xa 일 때만 본체+0xa780→+0xa0 |
| NiceBallDamageBlendRt | 스페셜 0x12 일 때 본체+0xa5b0→+0x310 의 (+0x84/+0x80) 비율의 지수 변환 [부분 판독] |
| WeaponCategory / WeaponDetail | 0x71024477b4 가 인자 문자열 저장(+0x250/+0x258) 후 기록. 호출자 4곳의 값 [미확정] |
| JumpVarID | 0x710243dcf8, 0x710244128c 가 기록, 출처 [미확정] |
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
| `ClipNameResolver` | `Nrml`/`@` 치환 |

갱신 순서(원본과 같게): 상태기계 판정(직전 cur 사용) → 블랙보드 공급(0x710246cb58) → 사람·오징어 래퍼 틱(전진 → cur 복사). 요청 프레임에는 cur = 0 으로 진입 후 같은 프레임 틱에서 1 이 된다.

검증 기대값(데이터): 오징어 `Wait` → `Sqd_Wait`(스켈레탈 120f 반복) + `Sqd_Wait`(재질); 사람 `WalkHold` → BoolSelector → FloatBlend(`WalkHold_<무기>`, `RunHold_<무기>`) 또는 `Walk`/`Run`.

## 6. 미확정과 필요한 근거

| 항목 | 상태 / 필요한 것 |
|---|---|
| ~~노드 종류 10/12/19~~ | 해소: Event / FrameController / InitialFrame, 잎 노드 부착 목록(§2.5, §2.8). 남은 것: Event 발화 구간(0x71039c6d98, 헤더 +0x20~+0x34 섹션), InitialFrame 방식 3(점프표 0x7104af3296) |
| ~~블렌드 곡선, FloatBlend 가중~~ | 해소: §4.4, §4.5. 남은 것: 다층 포즈 합성(0x71039cd350, 0x71039be4a0, 0x71039bf1b8), FloatBlend 자식 프레임 동기화(0x71039bcb9c) |
| ~~끝 프레임·±1~~ | 해소: end = FSKA FrameCount, 판정은 틱 전 cur(§4.2). 요청 프레임 첫 틱 전진은 경로 판독만(실행 검증 없음) |
| 블랙보드 공급 | 대부분 해소(§4.6). 남은 것: WeaponCategory/WeaponDetail 호출자 값, JumpVarID 출처, MoveSpeedRt 나머지 분기·애니 rate 표(state_big_full.c 2725~2985행), SM+0x204 기본값 |
| 노드 표 +0x0c, 헤더 나머지 섹션 | 섹션별 덤프 비교 |
| 이벤트 AnimationEvent/AsNode/*.baev 연결 | baev 형식 판독 |

참고: `romfs/Sound/*.baatarc`, `*.bagst` 는 사운드 감쇠·그룹 설정이며 애니와 무관하다 [데이터: 경로 `/Sound/Attenuation/`, `/Sound/Group/`].
