# [fx] 이펙트·효과음 구현 기록

담당 폴더: `games/splatoon3/client/fx/`, `games/splatoon3/client/audio/`.
근거 문서: [effect_sound/effect_sound.md](../effect_sound/effect_sound.md), [xlink_format.md](../effect_sound/xlink_format.md), [sound_resources.md](../effect_sound/sound_resources.md), [effect_resources.md](../effect_sound/effect_resources.md), [camera/shake_rumble.md](../camera/shake_rumble.md)(슈터 진동·쉐이크 없음 → 구현 안 함), [graphics/team_color.md](../graphics/team_color.md).
이번 작업의 추가 분석: 그룹 제한기 4종 정렬 비교(`analysis/decomp/fx/limiter.c`, `limiter_cmp.c`), 착탄 벽·바닥 행렬(`analysis/decomp/network/net_player.c` 0x71027b877c 본문), 플레이어 SLink/ELink 액션 슬롯 트리거 표(아래 §1.6). `analysis/notes/SHARED.md` 의 `[fx impl]` 줄.

상태(2026-10-02): 시험 사격장 1인 연습에서 실제 이벤트(weapon·physics·range)로 발사음·착탄음(インクヒット)·발소리/점프·착지·변신·헤엄 소리, 머즐 플래시·탄·바닥/벽 착탄 이펙트가 나온다. 개발 서버 헤드리스(사격 200프레임·점프·오징어 이동)에서 콘솔 오류 0, 앱 루프 정상.

## 1. 구현한 것

### 1.1 파일

| 파일 | 내용 | 원본 근거 |
|---|---|---|
| `audio/xlink.ts` | XLink2 사용자 실행기(ELink·SLink 공용, DOM 없음): 키 이진탐색 대응(키 → 최상위 콜 테이블), Switch(조건 없는 자식 즉시 선택, 액션 슬롯 감시), Random/Random2(직전 선택 제외), Blend(전부), Sequence(끝나면 다음), Grid, duration 반복, 값 해석(Random·RandomNPow·WeightMin/Max·Curve), 액션 슬롯(변경·넘겨받기 bit0·시작 bit2·종료 bit3·프레임 범위·매 프레임 calc), 속성 트리거 | xlink_format.md §3.6~4.4: 0x710389e6e8, 0x71038978bc, 0x71038925a0, 0x7103892874, 0x710388f59c, 0x7103897644, 0x71038909a4, 0x710389250c, 0x7103888b04, 0x71038964b8, 0x7103896874, 0x7103895f64 |
| `audio/alto.ts` | Alto 감쇠: AROC(Rational/Linear/Power, mix), AUDC(거리 우선순위), AADR(음원 지향성), AACL 컬링 식, 그룹 제한기 정렬 | sound_resources.md §4.2.1~4.2.5, 제한기 0x71038477b0 → vtable 0x7105734878/8b8/8f8/938 (이번 판독 §1.5) |
| `audio/sound.ts` | WebAudio 재생기(SLink sink): Volume·Pitch(재생 비율)·Delay(프레임)·감쇠 세트·DistCoef·지향성·그룹 제한, 청자 이동에 따라 매 프레임 감쇠 재계산 | sound_resources.md §4.2.2, §5 |
| `audio/hiteffect.ts` | HitEffectConfig 셀 조회(`행___반응_대상`, 없으면 `_Default`), E2 종류(Splash 0/Hit 1/SplashWater 2) | 로더 0x71027b5980 |
| `audio/data.ts` | effect/·sfx/·common 번들에서 XLink 사용자, HitEffectConfig(`hit_effect.json`), 감쇠 세트, 소리 버퍼, 이미터 값·텍스처·프리미티브 수집. 번들 전·없을 때 `fx/fallback.json` | — |
| `audio/read.ts` | 이벤트 수집(스텝별 프레임 번호 유지), shared `player`·`camera` 읽기, SubjectiveType, 플레이어 XLink 속성 근사, Damage 결과 → 반응 열 | — |
| `audio/index.ts` | 이벤트 → SLink: Fire(발사 컬링 600), BulletHit/Damage(히트 컬링 400, S1 집계 AggregateNum·S2 즉시), 플레이어 액션 슬롯, 표적 Break/ダメージ | effect_sound.md §3.2·§3.5 |
| `audio/selftest.mjs` | 합성 검증 51항목(§4) | — |
| `fx/particles.ts` | nn::vfx 파티클(인스턴스 메시 + 셰이더): 방출(시작·간격·무한 방출·수명 난수), GPU_TIME 운동식, 스케일·알파·색 키, 회전(초기·난수·추가·regist), POLYGON_XY/XZ·카메라/Y 빌보드, 프리미티브(G3PR) 형상, follow ALL/NONE | effect_resources.md §2.2.3~2.2.5 (0x710081c0b8, 0x710081b784, 0x710081e3e4, 정점 셰이더 1940) |
| `fx/inkaction.ts` | 무기 InkAction → ELink 액션 슬롯 `State[0]`: 즉시/보류, 같은 프레임 FireImpact 뒤 무시, 보류 적용 | 0x7102864104, 0x710286540c |
| `fx/splash.ts` | 착탄 분류(벽 n.y ≤ 0.64144969, θ = atan2(|v̂×n|, v̂·n), a = π/2 − |π/2 − θ|, 30°/60°), 바닥 행렬·벽 행렬(디컴파일 그대로) | 0x71027b877c, 0x71018b4f74 |
| `fx/index.ts` | 이벤트 → 탄 파티클(OneEmitter `WpShtrBullet1Emit`), 머즐 플래시(ELink `WeaponShooterNormal`), 착탄 E2 코드 파티클·E1 집계(ELink `HitEffect`), 플레이어 ELink(`SplPlayer` — 자료 있을 때), 표적 ELink `Break` | effect_sound.md §3.2~3.5 |
| `fx/fallback.json` | 개발용 기본 자료(분석 산출물 사본): SLink `WeaponShooterNormal`, ELink `WeaponShooterNormal`·`HitEffect`, 이미터 30개 값과 텍스처 이름. 번들 자료가 같은 이름을 덮어쓴다 | `analysis/effect_sound/*_users.json`, `vfx_emitter46.py fields` |

### 1.2 이벤트 처리(프레임 단위)

뷰 `update` 는 렌더 프레임마다 불리고 그 사이 고정 스텝이 여러 번 돌 수 있다. `read.ts` 의 수집기가 `EventQueue.clear` 직전 목록을 보관해 **이벤트마다 발생 프레임**을 붙이고, fx·audio 는 프레임 순서대로 처리한다(§5 조정 요청 1). 뷰 `update` 는 try/catch 로 감싸 절대 예외를 내지 않는다.

| 이벤트 | 소리 | 이펙트 |
|---|---|---|
| `Fire` | 카메라에서 600 초과면 생략(`R² < d²`). 키 = `VariableShotRepeatStartFrame > 0 ? (FireOn/FireImpact) : "Fire"`(스플래시 슈터 0 → `Fire`), SubjectiveType(본인/아군/적) → SLink `WeaponShooterNormal` | InkAction FireImpact(같은 프레임 중복은 무시) |
| `FireImpact`/`FireOn`/`FireOff` | — | `InkActionState` → ELink `State[0]` 액션 변경 → `マズルフラッシュ`(`WpShtrMzfNml`, 뼈 Muzzle, Delay = Curve(MuzzleShotDirXZDot)). FireImpact↔FireOn 은 넘겨받기라 **연사 중 재발생 없음**, FireOff 에서 방출 중지 |
| `BulletSpawn`/`BulletDie` | 탄 속도 추적 | 탄마다 `WpShtrBullet1Emit/ball` 하나(follow ALL, 탄 위치를 렌더 보간), 소멸 시 즉시 제거. 팀 −1·3 무시 |
| `BulletHit` | 히트 컬링 400. 셀 `Shooter___Constant_Default`(물이면 `_Water`) S2 `インクヒット`: AggregateNum 1, Velocity = |v|, IsPaintable, SubjectiveType(공격자) | E2 Splash → 벽(n.y ≤ 0.64144969: `Cmn(Np)WallSplash1Emit`, 벽 행렬) / 바닥(θ 분류 → `Cmn(NP)FloorSplash(Near/Dist)1Emit`, 바닥 행렬, 속도 0 이면 kind 0·고정 행렬) |
| `Damage`(range) | `result` → 반응 열(4 Invincible, 5 Armored, 6 Damaged, 7 Cure, 0 없음), 행 `Shooter`/`Shooter_CriticalHit`, 같은 프레임 `BulletHit`(같은 target)에서 속도·팀. S1(`ヒット` 등) 프레임 집계 → AggregateNum, S2(`インク被弾`) 즉시. 표적 SLink `ダメージ` [추정] | E1(`HitEffective` 등) 집계 → ELink `HitEffect`, E2 `Hit` → `WpCmnHit`(Y = 법선) |
| `Break`(range) | 표적 SLink `Break` | 표적 ELink `Break`(사용자 자료가 있을 때) |
| `Jump`/`Land`/`ToSquid`/`ToHuman`/`Swim`(physics) | SLink `Player_<Subjective>`·`PlayerFoot` 액션 슬롯(§1.6) | ELink `SplPlayer` 같은 슬롯(자료 없음 → 기록만) |

### 1.3 소리 (Alto)

- 청자 = shared `camera.pos`(없으면 three 카메라). 정규화 거리 `d = 거리 / DistCoef`(문서 권고 가정, §3). 이득 = Volume × AROC 볼륨(d) × AADR 지향성(음원 +Z = 발사 방향). 자기 발사음은 총구 뒤 → 0.8배(WeaponMuzzle 80°/140°/0.8).
- 감쇠 세트는 `sfx.json attenuation`(refs + curves)을 AttnSet 으로 바꿔 쓴다. 없으면 sound_resources.md §4.2 표 값.
- 그룹 제한(AGST GRP [0x16] 종류, [0x17] 개수): 이번 판독(§1.5) 정렬 규칙으로 정렬해 앞 limitCount 개만 남긴다. 무기 그룹(`Weapon_*`)은 제한 없음.
- 값 난수는 원본 xorshift 순서를 맞추지 않는다(연출값, 문서 허용).

### 1.4 파티클

- 이미터 값 = `emitters.json emitterSets[*].fields`(= `vfx_emitter46.py fields`). 텍스처 = 첫 샘플러(`textures[0]`)의 R 채널을 마스크로, 프리미티브 = `primitive.file` GLB 의 첫 메시.
- 정점: `(pos + 0.5·pivotOffset)·scale` → 회전(rotType 4 = Ry·Rz·Rx, 6 = Rz·Rx·Ry) → `+ P(t)` → 탄생(또는 follow ALL 이면 현재) 이미터 행렬. POLYGON_XZ 는 로컬 Y → −Z(Rx −90°).
- 색 = 팀 색 × color0(ANIM 키, FIXED 는 1) × colorScale, 알파 = clamp(alpha0 × 마스크). 일반 알파 블렌딩, 깊이 쓰기 없음.
- 팀 색 = graphics/team_color.md §8 OrangeBlue **Original**(선형). `teamColors` 자료나 shared `teamColors` 가 있으면 그것.

### 1.5 이번 판독: 그룹 제한기 4종 [판독]

`0x71038477b0(type)` 이 만드는 객체의 vtable 슬롯 5(연결 목록)·6(배열 칵테일 정렬)이 보이스를 정렬하고, 비교 함수는:

| 종류 | 정렬 함수 | 비교 | 결과(앞쪽이 남음 [추정]) |
|---|---|---|---|
| 1 | 0x7103847950 / 0x7103847a84 | 0x7103848c88 = `int(pB·255) − int(pA·255)`, 같으면 `A.+8 − B.+8` | 우선순위 높은 것, 같으면 +8 작은 것(먼저 시작) |
| 2 | 0x7103847c6c / 0x7103847da0 | 같은 우선순위 비교, 같으면 `B.+8 − A.+8` | 같으면 나중 것 |
| 3 | 0x7103847f84 / 0x7103848070 | 0x7103848e34: `~(+8)` 비교 먼저, 같으면 우선순위 | +8 작은 것 |
| 4 | 0x71038481f4 / 0x71038482e0 | 0x7103849000: `+8` 비교 먼저, 같으면 우선순위 | +8 큰 것 |

우선순위 p = `+0xc4 × +0xcc × (+0x210 객체 +0x18 또는 +0x180 vt+0x38)`. 웹은 `Priority × AUDC 거리 우선순위`로 둔다 [추정]. +8 = 시작 순번 [추정]. 슬롯 7 은 종류 번호(1~4), 슬롯 4 는 0x20001~0x20003.

### 1.6 플레이어 소리·이펙트 = 액션 슬롯 [데이터 + 판독 규칙]

플레이어 xlink 키(`イカに変身`, `ヒトのジャンプ` 등)는 main·romfs 어디에도 UTF-8 문자열로 없다(전수 검색). 대신 **사용자 데이터의 액션 트리거**가 이 키들을 가리킨다(범위는 양끝 포함):

| 슬롯 → 액션 | SLink `Player_Focused` | SLink `PlayerFoot` | ELink `SplPlayer` |
|---|---|---|---|
| `SklAnim_Human` → `ToSquid` | `イカに変身`(f0) | — | `イカへ変身`(f2) |
| `SklAnim_Human` → `ToHuman` | `ヒトに変身`(시작) | — | `イカから半イカ_頭`(f10) |
| `SklAnim_Squid` → `Sqd_Walk` | `イカで泳ぐ単発音`(f10, f60) | — | `イカダッシュ移動線` |
| `SklAnim_Squid` → `Sqd_ToSquid`/`Sqd_ToHuman` | `ヒト状態からインクに潜る`(시작+넘겨받기) / — | — | `イカへ変身：もぐる`(f1) / `イカから半イカ` |
| `State` → `Human_JumpSt`/`Human_JumpEd` | `スフィアでジャンプ`/`カニで着地`(특수 모델) | `ジャンプ`(f0~1) / `着地`(f2) | `ヒトのジャンプ`(f0) / `ヒトの着地`(f3) |
| `State` → `Squid_JumpSt` | `インクからジャンプする`, `InkLand_Neutral` | — | `イカのジャンプ`, `イカのジャンプ飛沫軌跡` |
| `State` → `Squid_Move` | — | — | `イカ移動` |

웹 대응 [추정: 이름 대응]: `Jump` → State `Human_JumpSt`/`Squid_JumpSt`, `Land` → `Human_JumpEd`/`Squid_JumpEd`, `ToSquid` → SklAnim_Human `ToSquid`(+ Sqd_ToSquid), `ToHuman` → `ToHuman`(+ Sqd_ToHuman), 오징어 상태에서 `swimming && 수평속도 > 0.001` 이면 SklAnim_Squid `Sqd_Walk`, 아니면 `Sqd_Wait`(physics 의 Swim 조건과 같음). 이벤트에 `slot`·`action` 이 있으면 그것을 그대로 쓴다. 액션 프레임은 게임 프레임마다 1 증가(애니 반복·속도 미반영).
속성(근사): SubjectiveType, TransformType(Human/Squid), GndPaintTeamType(PlayerStepPaint cls: 0/1 OnFriend, 2/3 OnEnemy, 4/5 OnNeutral), FieldAngleType(접지 Plane/공중 Air), GndMaterial(발밑 충돌 재질 이름), MoveVelXZ, FallVelY(−v.y), SquidStealth(swimming), TroubleType Normal, IsCoopFloat False, SpecialType NoSpecial.
※ assets 의 `sfx.json events`(이벤트 → 키 직접 방출)는 쓰지 않는다 — 원본 데이터상 이 키들은 액션 트리거로 나온다.

## 2. 원본과 다른 점

| 항목 | 차이 | 이유 |
|---|---|---|
| 청자 위치 | 카메라 위치. 원본 리스너 `TargetOffset`(카메라~주시점 사이, 지향성 원뿔 40/90°) 미적용 | 리스너 계산 코드 미판독 |
| 패닝 | 청자 오른쪽 축 성분으로 StereoPanner | 원본 스피커 배분 식 미판독(웹 근사) |
| 필터·FarFx | AROC 필터 값·FarFx 버스(리버브) 미적용 | 필터 값 → 컷오프 변환 미판독, I3DL2 리버브 대응 노드 없음 |
| 정지 페이드 | 10 ms 램프 | 원본 페이드 시간 미확인(클릭 방지) |
| AACL 컬링 | 볼륨에 곱하지 않음, 정지 안 함 | +0x50 = 0, 정지 조건 플래그(+0x48 bit6) 미확인 |
| xlink calc 큐 | 원샷 즉시 재생, 액션·속성 트리거·Sequence·duration 만 프레임/종료 콜백 | effect_sound.md §6 권고 |
| 탄 ball | 프리미티브 `BulletShtr.glb` 형상만, VAT(`bulletshtr_vsp` 정점 애니) 미적용. 프리미티브가 없으면 구 근사 | VAT A 채널 의미 미판독 |
| 분열 탄(`Splash`) | `WpShtrBullet1Emit` 로 그림 | 슬롯 0xA00(두 번째 WpShtrBullet1Emit) 사용 탄 종류 미확인 [추정] |
| 벽 낙하 방울(`WallDrop`) | 그리지 않음 | 파티클 슬롯 미확인 |
| 색 조합(Combiner) | 색 = 팀색 × color0 × colorScale, 알파 = alpha0 × 텍스처 R. color1/alpha1·법선 텍스처·프레넬·소프트 파티클 미적용, FIXED color0 = 1 | 프래그먼트 셰이더·Render/Combiner 바이트 미판독 |
| 빌보드 0/2/5 | 0 카메라, 2 Y축, 5(VelLook) 는 카메라 빌보드 | nn::vfx 열거 순서 [추정], VelLook 미구현 |
| 형상(volumeType) | 점(0)만 + positionRandom | 형상 함수 미판독(대상 이미터는 전부 0) |
| 페이드 인/아웃(이미터) | 미적용 | 대상 이펙트 수명이 짧아 생략 |
| 총구 위치 | shared `muzzle` 이 없으면 마지막 발사 위치 + 플레이어 이동량, 축 = 발사 방향(+Z) | Muzzle 뼈 행렬을 받을 경로 없음(§5 요청 2) |
| MuzzleShotDirXZDot | `dot(normalize(발사 방향 XZ), camera.rigForward)`. 원본은 뼈 −X 축 XZ | 뼈 행렬 없음 |
| 무기 FireOn/FireOff 이벤트가 없을 때 | 사격 버튼으로 대신(현재 weapon 이 보내므로 쓰이지 않음) | — |
| 플레이어 액션 프레임 | 게임 프레임 카운트(애니 속도·반복 없음) → `イカで泳ぐ単発音`(f10/60)은 Sqd_Walk 진입 뒤 한 번씩 | 애니 상태 이름·프레임은 render 담당(§5 요청 3) |

## 3. 미확정·추가 분석 필요

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| DistCoef 결합 | `d = 거리/DistCoef` 가정 | 게임 감쇠 확장(음원 +0x50) +4 를 채우는 코드(sound_resources.md §4.2.6) |
| 컬링 n(팀별 구조체 +0x10) | 0 으로 둠(R = 600/400) | 0x71027e22bc / 0x71027e24a8 의 n 의미 |
| 제한기 "앞쪽이 남음", +8·우선순위 필드 | [추정] | 제한기 적용부(정렬 뒤 정지 루프) |
| S1/S2 SubjectiveType 기준 | 공격자로 둠 | req+0x34 를 채우는 코드 |
| AggregateNum 묶는 기준 | 같은 프레임·같은 S1 키 | 0x71027b7938 |
| 반응 열 Constant = 지형 | 문서 [추정] 그대로 | 반응 열을 고르는 호출자 |
| 플레이어 액션 이름 대응 | 이벤트 이름 → 애니/상태 이름 [추정] | 원본 애니 상태기계(render) |
| 표적 `ダメージ` SLink | 방출 코드 미확인 | SighterTarget 피격 처리 |
| 이펙트 팀 색 변형 | Original | ELink ForceTeam·셰이더 팀색 uniform |
| 바닥 속도 0 고정 행렬 | 단위 회전 | bss 0x71058237b0 초기화 |
| POLYGON_XZ 축 | 로컬 Y → −Z(벽 행렬의 −Z = 법선과 맞물림) [추정] | 정점 셰이더 billboard 분기 |

## 4. 검증

| 검증 | 방법 | 결과 |
|---|---|---|
| 합성 검증 | `node games/splatoon3/client/audio/selftest.mjs` (web/ 에서) | **51/51 PASS**. 착탄 분류 θ 10°/45°/80°/170°, 수직 낙하 180°, 스침 95.7° → Dist, 벽 경계 0.64144969/0.6414498, 벽 행렬(n=(0,0,−1) → 단위, −Z = n 3건), 바닥 행렬(Y = n, Z = 투영 진행 방향, |v·n|>0.99999 고정), AROC(WpMuzzleVol = `alto_aroc_models.txt` 값, CmnVol 1/d, CmnFlt), AUDC(CmnPrio_High/Low, cut 13.55), AADR(0°/110°/180°), 제한기 1·2, HitEffectConfig(원본·assets 형식), InkAction 순서·같은 프레임 무시, XLink(`effect_xlink_eval.py --selftest` 와 같은 항목: Fire×3·무음·Volume/Pitch 범위·Random2Pow 집중·머즐 Delay 커브·Grid 3·Random2 연속 중복 0) + インクヒット Blend/DistCoef 커브·インク被弾 Focused 무음·머즐 넘겨받기·PlayerFoot 着地 프레임 |
| 타입 | `npm run typecheck` | fx·audio 오류 0 |
| 실제 루프(헤드리스) | 개발 서버 + playwright(사격 버튼 200프레임, 점프, 오징어 이동) | 콘솔 오류 0. 이벤트 Fire 14·BulletHit 34 → 발사음 14(▶), インクヒット/飛沫 각 착탄마다, 머즐 ELink 방출 **1회**(연사 중 넘겨받기), 바닥 스플래시 34(θ 분류), `ジャンプ_石`·`FootLandInkFriend`·`イカに変身`·`イカで泳ぐ単発音_インク内`·`ヒトに変身` 재생 |
| 화면 | 시각 고정 렌더(uNow 고정) 캡처 | 바닥 Splash(Crown01pro)·Crown(Ripple01 고리, 바닥에 눕음)·벽 Splash·WpCmnHit 이 수명 키대로 커지고 사라짐 |
| 원본 실행 대조 | 없음 | — |

## 5. 조정 요청

1. **[조정] 스텝별 이벤트 전달** — `world.step` 이 앞 스텝 이벤트를 비워, 한 렌더 프레임에 스텝이 여러 번 돌면 뷰가 이벤트를 잃는다. 지금은 `client/audio/read.ts` 가 `EventQueue.clear` 를 감싸 보관한다(같은 World 에 하나). `View.step?(w)` 훅(스텝마다 호출)이나 렌더 프레임 동안의 이벤트 목록을 `app.ts` 가 넘겨 주면 이 감싸기를 지운다.
2. **[render] 총구 행렬** — `world.shared.set("muzzle", { pos, dir, mtx? })`(무기 모델 `Muzzle` 뼈의 월드 행렬). 머즐 플래시 위치·MuzzleShotDirXZDot(뼈 −X 축) 원본 계산에 필요.
3. **[render/physics] 애니·상태 이름** — 플레이어 XLink 는 액션 슬롯 `SklAnim_Human`/`SklAnim_Squid`/`State`(애니·상태 이름)로 소리·이펙트를 낸다. shared `player` 에 슬롯별 현재 애니 이름과 프레임(예 `anim: { SklAnim_Human: { name, frame }, … }`)이 있으면 이벤트 이름 대응(§1.6 [추정])을 원본 이름으로 바꾼다. 이벤트에 `slot`·`action` 필드를 붙여도 된다.
4. **[assets] ELink 사용자** — effect 번들에 ELink 사용자(`SplPlayer`, `WeaponShooterNormal`, `HitEffect`, `SighterTarget`·`SighterTargetBig`·`SighterTarget_TipsTrial`)를 `{ elink: { 이름: 사용자 덤프 } }` 로 넣어 주세요(지금 앞 셋 중 두 개는 `fx/fallback.json` 사본). 플레이어 ELink 가 가리키는 이미터셋(`PlayerJumpSmokeOnE` 등)의 emitterSets 도 필요.
5. **[assets] AGST 그룹 표** — `sfx.json` 에 `groups: { 그룹: { limiterType, limitCount } }`(GRP [0x16]/[0x17], `analysis/vfx/agst_grp_dump.txt`). 지금은 `audio/alto.ts DEFAULT_GROUPS` 의 일부 그룹만.
6. **[조정] DESIGN.md §4 이벤트 표** — 실제로 쓰는 필드 등록: `Fire`(+team, vel, bullet), `FireImpact/FireOn/FireOff` = InkAction **변경 알림**(규칙 적용 뒤), `BulletSpawn`(+owner, team, vel), `BulletHit`(+owner, team, vel, row, target, damage, surface "Water"), `Damage`(+result, attacker), `Break`(target, pos, user), 플레이어 이벤트(+slot/action 선택). shared 키 `muzzle`(render), `teamColors`(render, 선택) 등록.
7. **[render] 팀 색** — 이펙트가 쓰는 팀 색(선형 RGB, 팀 번호별)을 `world.shared.set("teamColors", { "0": [r,g,b], … })` 로 주면 render 와 같은 행을 쓴다(지금은 OrangeBlue Original 고정).
