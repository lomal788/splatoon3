# 스펀지 (Sponge_VS 계열 / spl::Sponge)

잉크를 맞으면 부풀거나 줄어드는 블록입니다. 목차는 [stage_gimmicks.md](stage_gimmicks.md). 표기 규칙은 [inkrail.md](inkrail.md) 머리말과 같습니다.

## 1. 사용자에게 보이는 동작

- 스펀지는 배치 데이터에서 팀(Alpha/Bravo)이 정해져 있습니다. **같은 팀 잉크**를 맞으면 커지고(배율 `FriendDamageCf`), **다른 팀 잉크**를 맞으면 작아집니다 [판독].
- 크기는 1.0(최소)~`Scale_Max` 사이이고, 목표 크기로 바로 바뀌지 않고 보간·속도 제한을 거쳐 커집니다. 이미 최대 크기일 때 같은 팀 잉크를 맞으면 작은 흔들림(지글)이 더해집니다.
- 최대치에 닿으면 애니 "Max"를 재생합니다.

## 2. 자료

| 항목 | 위치 |
|---|---|
| 배치 | Banc `SpongeSmall_3p0_VS`, `SpongeSmall_VS`, `SpongeTall_4p5_VS` + `spl__SpongeBancParam {Type, SafePosLinks, LinkedSponges, IsDefaultMax}` [데이터] |
| 액터 상속 | `SpongeSmall_3p0_VS` → `SpongeSmall_VS` → `Sponge_VS` → `SpongeParent` → `ObjParent`; `SpongeTall_4p5_VS` → `SpongeParent` (팩 해제본 `analysis/gimmick/pack/Sponge*`) |
| 클래스 | `spl::Sponge` vtable `0x7105616778`(54슬롯), getName `0x710220dd94` [판독] |
| 충돌 | 강체 Kinematic, LayerEntity Ground / SubLayer GroundObject, 재질 프리셋 `Sponge`(UserShapeTag Sponge) [데이터] |
| 슈퍼점프 | `spl__SuperJumpDisplacerParam {UseCustomDangerousArea, UseCustomSafePos}` → 착지 보정 콜백 `0x710220dea4`가 **스펀지 팀과 다른 팀**이면 가장 가까운 `SafePosLinks` 위치, 같은 팀이면 스펀지 윗면 뼈 `step_main` 위치를 후보로 냄 [판독, §4.4] |
| 피해 배율 | DamageRateInfo 열 `Sponge_Versus`: 슈터 1.0, Shooter_Short 1.0, TripleMiddle 1.2, TripleQuick 1.1, 블래스터 1.5, 차저 2.0, Bomb/Suction/Trap 2.0, Fizzy 2.4, Torpedo 3.0, RollerCore 0.344, Bomb_DirectHit 0.0 [데이터] |
| 네트워크 | `Sponge_VS.game__NetParam`: MapObject, `spl::SpongeNetState`, `$parent Work/Net/SpongeInfo.game__NetEnlReplicaParam` [데이터] |

### 2.1 spl__SpongeParam

리플렉션 `analysis/gimmick/param_reflect/spl__SpongeParam.json`(방문 `0x71020e2178`, 생성자 `0x71020e20b4`). 생성자 기본값은 도구가 전부 0으로 읽었으나 상수 추적 한계일 수 있어 **기본값은 쓰지 않습니다**. VS 3종은 아래처럼 데이터에 모든 사용 필드가 있습니다. `$parent` 필드 단위 덮어쓰기는 [bullet]이 판독한 조회 규칙 [판독].

| 오프셋 | 필드 | 플래그 | SpongeParent | Sponge_VS | SpongeSmall_VS | SpongeSmall_3p0_VS 최종 | SpongeTall_4p5_VS 최종 |
|---|---|---|---|---|---|---|---|
| +0x5c | Scale_Max | 0x70 | 6.0 | | 4.5 | **3.0** | **2.25** |
| +0x68 | ScaleDamageForMax | 0x71 | 3600 | 10000 | 5000 | **5000** | **3500** |
| +0x34 | FriendDamageCf | 0x72 | 1.5 | 2.0 | | **2.0** | **3.0** |
| +0x48 | Scale_AnimMin | 0x73 | 0.5 | | | 0.5 | 0.5 |
| +0x44 | Scale_AnimMax | 0x74 | 8.0 | | | 8.0 | 8.0 |
| +0x40 | Scale_AnimFrameOffset | 0x75 | -2.0 | | | -2.0 | -2.0 |
| +0x4c | Scale_Bias | 0x76 | 0.5 | | | 0.5 | 0.5 |
| +0x58 | Scale_Kp | 0x77 | 0.8 | 1.0 | | **1.0** | **1.0** |
| +0x50 | Scale_Kd | 0x78 | 0.9 | 0.0 | | **0.0** | **0.0** |
| +0x54 | Scale_Kf | 0x79 | 0.25 | | | 0.25 | **0.15** |
| +0x60 | Scale_MaxVelH | 0x7a | 0.3 | 0.3 | | 0.3 | 0.3 |
| +0x64 | Scale_MaxVelL | 0x7b | 0.3 | 0.3 | | 0.3 | 0.3 |
| +0x30 | EmissionAnim_DurationFrame | 0x7c | 60 | | | 60 | 60 |
| +0x38 | Jiggle_ScalePerDamage | 0x7d | 0.025 | | | 0.025 | 0.025 |
| +0x6c | IsUseStepSink | 0x7e | true | true | | true | **false** |
| +0x6d | IsVersus | 0x6e | | true | | true | true |
| +0x3c | ModelType | 0x6f | | | | (기본) | **"Tall"** |

`ModelType`은 열거형 `spl::SpongeModelType`이며 도구가 bool로 잘못 표시했습니다. 값 = Normal(0), Tall(1), Rectangle(2), VSRectangle(3) **[판독 — 정보 함수 `0x71020e4a50`의 값 문자열]**. 이 값을 쓰는 코드는 확인하지 않았습니다. `SpongeSmall_VS`는 Kaisou03·Upland03 트리컬러 레이어에만 있고 `IsDefaultMax: true`(sLin = Scale_Max로 시작, 실제 크기는 동역학으로 자람 — §4.3 [판독])입니다.

`spl__SpongeStepSinkParam`(방문 `0x71020e4f9c`): SpongeParent 데이터 `StepSink_AdditionalColSink 0.05, AirFrame 10, Bias 0.75, InfluenceDistance 2.5, Kd 0.8, Kf 0.1, Kp 0.0, MaxSink 0.15, PaddingXZ 0.5, RotBias 0.5, RotDegH 3.0, RotDegL 0.0` — 위에 선 플레이어 쪽으로 눌리는 표현. 소비 함수(`0x7102215670` 등)는 미판독 **[미확정]**.

### 2.2 spl::Sponge 필드 (기준 = spl::Sponge this) [판독]

| 오프셋 | 의미 | writer | reader |
|---|---|---|---|
| +0x108 | 애니 상태머신: Wait / PlayerWait / EnemyWait / DamageShot (`0x710220e294` 등록) | `0x7102217f94`(같은팀 1, 적 2) | |
| +0x150 | 스펀지 팀(0/1, 3·-1 중립) | 배치, `0x7102218748` | 피해 처리 |
| +0x178 | 선형 목표 크기 sLin ∈ [1, Scale_Max] | `0x7102217f94` | `0x7102212b64` |
| +0x180 | 보간 목표 target | `0x7102212b64` | 같음 |
| +0x184 | 크기 속도 vel | `0x7102212b64` | 같음 |
| +0x188 | 현재 크기 cur (>=1) | `0x7102212b64`, 지글 `0x7102217f94` | 표시·충돌 |
| +0x19c | 중립 첫 피격 연출 플래그 | `0x7102217f94` | |
| +0x880 | SpongeParam 객체 | | |
| +0x898 | 피해 수신 큐 | | `0x7102212b64` 앞부분 |

## 3. 호출 흐름 [판독]

```
vt18 0x7102212b64 (매 프레임)
  1) 이번 프레임 피해 목록 순회 → 0x7102217f94(damage, sponge, attackerTeam)
  2) 크기 동역학(§4.2)
  3) |vel| >= 1.1920929e-05 이면 0x7102212470/0x7102212560/0x71022127c0 (충돌·모델 갱신 [추정])
  4) 강체 위치 갱신, StepSink(IsUseStepSink) 처리
```

피해 처리가 같은 갱신 함수 앞부분에서 일어나므로 "피해 → 같은 프레임 크기 갱신" 순서가 확정입니다 [판독].

## 4. 계산

### 4.1 피해 → 선형 목표 (`0x7102217f94`, `0x7102218920`) [판독]

```
delta = (Scale_Max - 1) * (damage / ScaleDamageForMax)
if sponge.team ∉ {3,-1} and attacker == sponge.team: delta *= FriendDamageCf
if sponge.team == 3 (중립):
    attacker == 0 일 때만: 팀 설정 0x7102218748(team 0) 후 sLin += delta, 첫 연출
else if attacker == sponge.team: sLin += delta
else:                            sLin -= delta
sLin = (sLin >= 1) ? min(sLin, Scale_Max) : 1
atMax(v) = (-0.001 <= v-Max) and (v-Max < 0.001 or v-Max == 0.001)   // 원본 비교 그대로
if atMax(새 sLin) and not atMax(이전 sLin): 애니 "Max"
if atMax(새 sLin): cur += min(damage * 0.0016666667 * Jiggle_ScalePerDamage, 0.25)   // 최대치일 때만 지글, 0.0016666667 = 1/600
애니 상태 = (attacker == team) ? PlayerWait(1) : EnemyWait(2)
```

중립 분기에서 공격 팀 0만 처리하는 것은 판독 그대로이며 VS 배치는 모두 팀이 있어 이 분기를 타지 않습니다 [데이터].

### 4.2 크기 동역학 (`0x7102212b64`) [판독]

```
r  = (sLin - 1) / (Scale_Max - 1)
r' = bias(r, Scale_Bias)                       // inkrail.md §7.4, 0.5면 항등
if Scale_Kf > 0:
    nt = (Scale_Max - 1) * r' + 1
    target = (Scale_Kf < 1) ? target + (nt - target) * Scale_Kf : nt
vel = vel * Scale_Kd
vel = vel + (target - cur) * Scale_Kp
mv  = (조건 X) ? Scale_MaxVelL : Scale_MaxVelH
if mv >= 0: vel = min(vel, mv)                 // 위쪽(성장)만 제한
else:       vel = max(vel, -mv)
cur = vel + cur ; if cur < 1: cur = 1
```

- 속도 제한이 **한쪽만** 걸리는 것은 원본 그대로입니다(양수 mv면 축소 속도는 무제한) [판독]. 정리하지 마세요.
- "조건 X" = this+0x890 객체의 +0x80 값이 3 또는 4 — 그 객체·값의 정체는 **[미확정]**. VS 데이터는 L=H=0.3이라 결과에 영향이 없습니다.

### 4.3 시작 상태·Type·크기 → 충돌/모델/도색 [판독]

`spl__SpongeBancParam`(배치 인스턴스 파라미터, 스펀지 this+0x890; 방문 `0x71020deb24`/`0x71020dec5c`):

| 오프셋 | 필드 | 타입 | 플래그 바이트 | reader |
|---|---|---|---|---|
| +0x80 | Type | `spl::SpongeType` A~G(0~6) | +0x86 | `0x7102211c0c` |
| +0x84 | IsDefaultMax | bool | +0x88 | `0x7102211c0c` |
| +0x85 | IsGroundPaint | bool | +0x87 | `0x7102212560` |
| +0x30 (플래그 +0x89) | LinkedSponges | 링크 배열 | +0x89 | `0x71022178ac` → 연결 액터 목록 this+0x3b0(개수 +0x3c0) |
| +0x58 (플래그 +0x8a) | SafePosLinks | 링크 배열 | +0x8a | 개수로 풀 할당 `0x710220e294`(this+0x830/+0x838/+0x840, 항목 0x18 B), 목록 채움 `0x71022178ac` → this+0x818(개수 +0x828), 소비 `0x710220dea4` |

값 목록 `A , B , C , D , E , F , G`는 정보 함수 `0x71020dffec`에서 확인 [판독].

```
// 0x7102211c0c 시작/리셋
cur(+0x188) = 1; target(+0x17c,+0x180) = 1; +0x18c = 1; vel(+0x184) = 0
sLin(+0x178) = IsDefaultMax ? Scale_Max : 1.0        // 최대 크기로 시작하면 목표만 최대, 실제 크기는 §4.2 동역학으로 자람
team(+0x150) = 3; 액터 팀이 0/1이면 그 팀
(액터 팀 중립 && IsDefaultMax): team = 0 (액터 +0x4d0 != 2 이면 액터 팀도 0)
애니 "Scale" + Type 문자: A→"ScaleA", B→"ScaleB", … G→"ScaleG", 그 밖 → "" (애니 플레이어 +0x158)
0x7102212470(충돌), 0x7102212560(바닥 도색), 0x71022127c0 호출

// 0x7102212470 충돌 박스 (매 프레임 |vel| >= 1.1920929e-05 일 때도 호출, §3)
h0 = 형상 "Main" 박스의 초기 HalfExtents(+0x190..+0x198, 생성 시 Phive 형상 +0xd8에서 복사)
h  = cur * h0                                        // 세 축 같은 배율
sink = IsUseStepSink ? 0x7102218c94(StepSink) : 0
박스 +0x1f8 ← h ; 박스 +0x200 ← (h.x, h.y - sink*0.5, h.z)
[+0x1e8]+0x280 = vel * 60                            // 크기 변화 속도(초당) — 물리 쪽 전달 [용도 추정]
```

- 데이터: `SpongeParent` ShapeParam Box "Main" HalfExtents (0.5, 0.5, 0.5) 프리셋 `SplActualPlayerThrough`, Box "Sink" 프리셋 `SplActualPlayerOnly`; `SpongeTall` Main·Sink 모두 (0.5, 1.0, 0.5) [데이터]. +0x1f8/+0x200과 Main/Sink의 대응은 생성 순서로 본 **[추정]**.
- 이전 판의 "형상 스케일 축 [미확정]"은 **세 축 균등 배율**로 해소합니다.
- 박스 중심(2026-10-02 3차 판독, 갱신 `0x7102212b64` 후반): 매 프레임 모델 뼈 **`root_sub`**(인덱스 this+0x1b0 = (뼈 번호<<16)|모델 번호, 초기화 `0x710220e294`가 이름 `0x71048e101f` "root_sub"로 검색)의 월드 위치 b를 액터 국소 좌표로 바꿔 박스 중심에 씁니다.
  ```
  R = 액터 회전(+0x298..+0x2b8, 열 우선), T = 액터 위치(+0x28c..+0x294)
  c = Rᵀ · (b − T)
  Main 박스(+0x1f8) 중심(+0xe8..+0xf0) = c
  Sink 박스(+0x200) 중심 = (c.x − sink·0·0.5, c.y − sink·0.5, c.z − sink·0·0.5)      // sink = 0x7102218c94
  ```
  즉 박스 중심은 코드에서 고정하지 않고 **Type별 애니 "ScaleA~G"가 움직이는 `root_sub` 뼈를 따라갑니다** [판독]. 바닥 고정 여부는 애니 데이터에 달렸고, 이 저장소의 `Model/Obj_Sponge.bfres.zs`는 2바이트 자리표시(추출 생략)라 확인하지 못했습니다 **[미확정 — 애니 데이터 필요]**. 데이터 정황: SafePosLinks 로케이터 Y가 스펀지 Translate Y와 같고(예 Yagara (-12,7.5,44.5) ↔ (-16.5,7.5,46.5)), IsGroundPaint 오프셋이 −0.1 − cur·h0.y라 액터 원점 = 바닥면으로 보는 것이 자연스럽습니다 **[추정]**. 웹은 애니가 없으면 `c = (0, cur·h0.y, 0)`(바닥 고정)을 임시값으로 쓰고, 애니 확보 후 뼈 위치로 교체하세요.
- 모델은 스케일이 아니라 **Type별 애니 "ScaleA~G"의 프레임**으로 모양을 바꿉니다(갱신 `0x7102212b64` 후반):

```
frame = len(anim) * (cur - Scale_AnimMin) / (Scale_AnimMax - Scale_AnimMin) + Scale_AnimFrameOffset * (cur / Scale_Max)
      // VS 값: AnimMin 0.5, AnimMax 8.0, FrameOffset -2.0
```

  `len(anim)` = `0x710126022c(+0x158)`(애니 길이 [추정 — 함수 미판독]). 따라서 Type은 충돌에는 영향이 없고(충돌은 균등 배율) 표시 모양만 고릅니다 [판독].
- IsGroundPaint(`0x7102212560`): true이고 팀이 0/1이면 목록(+0x858)의 각 원소에 오프셋 (0, -0.1 - cur*h0.y, 0), 크기 (2*cur*h0.x, 2*cur*h0.z)를 씁니다 → 스펀지 바닥 면 크기의 팀 도색 영역 **[추정 — 원소 정체 미확인]**.

### 4.4 LinkedSponges · SafePosLinks [판독 — 2026-10-02 3차]

데이터: v0 대전 8개 스테이지의 스펀지 64개 전부 `LinkedSponges: []`, 52개가 `SafePosLinks` 2~3개(GeneralLocator, 스펀지와 같은 높이, 3~4.5 거리) [데이터 — 집계 스크립트, `extracted/params/Banc/*.json`].

- **SafePosLinks**: 링크된 로케이터 액터 핸들을 this+0x818 목록에 넣고(`0x71022178ac`), 스펀지가 SuperJumpDisplacer 컴포넌트(액터 컴포넌트 0x2e, 등록 `0x71014601b8`, 객체 vt `0x7105616958` 슬롯3 = `0x710220dea4`)에 착지 보정 후보로 등록됩니다.
  ```
  // 0x710220dea4(self, best*, q(질의 위치), team)
  if sponge.team(+0x150) != team and SafePos 개수(+0x828) > 0:
      cand = SafePos 중 |pos − q|² 최소(로케이터 +0x18 객체 +0x40..+0x48), extra = 0
  else:
      cand = 뼈 "step_main"(0x71048ea67d) 월드 위치
      extra: 박스 국소 좌표를 박스 반크기(+0x268..+0x270)로 나눈 정규화 좌표, 강체 값 +0x228
  if |cand − q|² < best.d²: best = {d², cand, 정규화 좌표, extra}
  ```
  → **적 팀 슈퍼점프 착지가 스펀지 근처면 가장 가까운 SafePos로, 같은 팀이면 스펀지 윗면(step_main)으로** [판독]. 질의 주체가 슈퍼점프 착지라는 것은 컴포넌트 이름 기준 **[추정]**, 질의를 부르는 쪽(거리 한계 등)은 [respawn]/[player] 소관 **[미확정]**.
- **LinkedSponges**: 연결 액터를 this+0x3b0 목록(개수 +0x3c0)에 넣고, 갱신 `0x7102212b64`가 큐(this+0x4a8, 항목 12 B = {8 B 값, s32 지연 프레임}, 지연 매 프레임 −1)에서 지연이 끝난 항목을 연결 스펀지마다 메시지로 보냅니다 [판독-부분]. 메시지 내용은 미판독이며 v0 대전 데이터가 비어 있어 **웹 대전 구현 불필요** [데이터].

## 5. 웹 포팅

```ts
interface SpongeState {            // spl::Sponge
  team: 0|1|3;                     // +0x150
  sLin: number; target: number;    // +0x178 / +0x180
  vel: number;  cur: number;       // +0x184 / +0x188
  anim: 'Wait'|'PlayerWait'|'EnemyWait'|'DamageShot';
}
function spongeFrame(s, p, hits /* [{damage, team}] */) {
  for (const h of hits) applyDamage(s, p, h);   // §4.1
  dynamics(s, p);                                // §4.2
  // 충돌 박스 HalfExtents = 형상 HalfExtents(Main) × cur (세 축 균등, §4.3), Sink 박스는 y에서 sink*0.5 뺌
  // 표시: anim "Scale"+Type, frame = §4.3 식
}
```

- 서버 권위: 크기는 충돌에 영향(발판)이므로 서버가 계산하고 넷 상태(`spl::SpongeNetState`)로 동기화. 비트 레이아웃은 [network] 표 참고.
- f32 연산은 `Math.fround`로 감쌀 것.
- 충돌은 균등 배율 박스, 모델은 Type별 Scale 애니 프레임(§4.3). 애니 클립 "ScaleA~G" 안의 본 변환은 [graphics] 도구로 확인 필요 **[미확정]**.

## 6. 검증 [재구현]

`PY web/tools/gimmick_stage.py sponge` — 0프레임에 같은 팀 피해 360(슈터 1발, 배율 1.0) 1회:

| 종류 | sLin | 프레임 0 cur | 1 | 2 | 3 | 7 |
|---|---|---|---|---|---|---|
| SpongeSmall_3p0_VS | 1.288 | 1.072 | 1.126 | 1.1665 | 1.1969 | 1.2592 |
| SpongeSmall_VS | 1.504 | 1.126 | 1.2205 | 1.2914 | 1.3445 | 1.4535 |
| SpongeTall_4p5_VS | 1.3857 | 1.0579 | 1.107 | 1.1488 | 1.1844 | 1.2806 |

연사(6프레임마다 같은 팀 360, 60프레임에 적 360 1회) — `(프레임, sLin, cur)`:

| 종류 | 6 | 30 | 54 | 60(적 피격) | 66 | 89 |
|---|---|---|---|---|---|---|
| SpongeSmall_3p0_VS | 1.576, 1.3216 | 2.728, 2.4652 | 3.0, 2.9986 | 2.856, 2.9637 | 3.0, 2.9112 | 3.0, 2.9999 |
| SpongeTall_4p5_VS | 1.7714, 1.3199 | 2.25, 2.212 | 2.25, 2.2492 | 2.1214, 2.2304 | 2.25, 2.1818 | 2.25, 2.2484 |

계산: Small_3p0 delta = 2·360/5000·2.0 = 0.288. Kp=1, Kd=0이라 cur는 매 프레임 target을 따라가고(성장 0.3/프레임 제한 안 걸림), target은 Kf 0.25 지수 보간 → 수렴 1.288. 원본 실행 비교는 없습니다.

## 7. 미확정

| 항목 | 이유 |
|---|---|
| SpongeParam 생성자 기본값 | 도구 상수 추적 0 — 생성자 직접 판독 필요(VS 데이터는 전 필드 있음) |
| Type A~G | **해소 [판독]** §4.3 — 애니 "ScaleA~G" 선택(표시 전용) |
| LinkedSponges, SafePosLinks 동작 | **해소 [판독]** §4.4 (SafePos = 적 팀 착지 대체 위치, Linked = 지연 메시지 전파, v0 데이터 비어 있음). 남은 것: 착지 질의 호출 쪽, Linked 메시지 내용 |
| StepSink(위에 선 플레이어로 눌림) 공식 | `0x7102215670`, `0x71022170a4` 미판독 |
| 크기 → 충돌 형상 반영 방식 | **해소 [판독]** §4.3 균등 배율, 박스 중심 = 뼈 `root_sub` 위치(액터 국소). 남은 것: ScaleA~G 애니의 root_sub 궤적(모델 파일이 이 저장소에 없음) |
| 팀이 바뀌는 경우(크기 1에서 적 피해 지속) | 이 문서 범위 코드에는 팀 변경 없음(중립 분기 제외) |
