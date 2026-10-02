# 플레이어 캐릭터 조립 — 모델 선택, 파츠 결합, 스켈레톤, 애니메이션

[목차](model_character.md)

## 1. 기능 개요

플레이어(액터 `SplPlayer`)는 모델 타입(잉클링/옥토링 × 성별)에 따라 몸 모델을 고르고, 커스터마이즈(머리·눈썹·하의)와 기어(머리·옷·신발), 탱크, 무기 모델을 몸 스켈레톤에 붙여 그립니다. 오징어/문어 형태는 별도 모델로 바꿔 그립니다.

## 2. 자료

| 자료 | 내용 [데이터] |
|---|---|
| `Pack/Actor/SplPlayer.pack.zs` | `PlayerFullModel`: `ValidModelTypes [SquidF, SquidM, OctopusF, OctopusM]`, `SquidControllerSetPath`; `PlayerCustom{HandleNum 64, HasWeapon true}`; `AS/SplPlayer.root.asb`(54,923 B), `AS/SplPlayerSquid.root.asb`(5,685 B) |
| RSDB `HairInfo`(27행) / `EyebrowInfo`(8) / `BottomInfo`(14) | 행 키 = 모델 이름 접두(`Har_SQD000` 등), `IsSquid`, `Id`, `Order`, BottomInfo `AlphaMaskF/M`, `VariationNum` |
| RSDB `GearInfoHead`(57) / `Clothes`(91) / `Shoes`(56) | 행 키 = 모델 이름(`Hed_CAP000`), `IsUnisex`, `HarnessType`(S/M/L), `IsThinHarness`, `IsHideHarness`, `AlphaMaskF/M`, `HeadParamSetPath` |
| RSDB `TankInfo`(8) | `Tnk_000` → `Work/Actor/PlayerTank.engine__actor__ActorParam.gyml` 등 |
| 파츠 액터 팩 | `Har_*`(Phive/Cloth `*.bphcl` 천 물리, `GearHairParent`), `Shs_*`(`MirrorModel` 컴포넌트), `Hed_*`(`GearHeadParamSet`: `HairArrange`·`ManualBindSRT`) |

열거형 `spl::PlayerModelType` = `SquidF , SquidM , OctopusF , OctopusM , Rival` (0..4) [데이터: main 문자열].

## 3. 모델 선택 — 0x7102656ac8 [판독]

입력: 객체 `+0x14` = PlayerModelType, `[3]`(+0x18) = 파츠 종류(0..4). 출력: 모델 리소스(로드 실패 시 0). 파일 경로는 `"Model/%s.bfres"`. 두 이름을 받는 0x7102657a4c(파일, 모델 이름)와 세 이름을 받는 0x7102657260(파일, 모델 이름, 추가 로드 파일)을 씁니다.

| 타입 \ 파츠 | 0 몸 | 1 오징어형 | 2 `_Hlf` | 3 SuperHook | 4 잉크레일 |
|---|---|---|---|---|---|
| SquidF | Player00 | 파일 Player_Squid, 모델 `Squid` | Player00_Hlf | Player00_SuperHook | Obj_InkRailPlayer |
| SquidM | Player01 (+Player00) | Player_Squid/`Squid` | Player00_Hlf | 파일 Player00_SuperHook, 모델 `Player01_SuperHook` | Obj_InkRailPlayer |
| OctopusF | Player02 (+Player00) | Player_Octopus/`Octopus` | Player02_Hlf | Player02_SuperHook (+Player00_SuperHook) | Obj_InkRailOctPlayer |
| OctopusM | Player03 (+Player01, +Player00) | Player_Octopus/`Octopus` | Player02_Hlf | 파일 Player02_SuperHook, 모델 `Player03_SuperHook` (+Player00_SuperHook) | Obj_InkRailOctPlayer |
| Rival | Player02 (+Player00) | Rival_Octopus (+Player_Squid) | Player02_Hlf | Player02_SuperHook (+Player00_SuperHook) | Obj_InkRailOctPlayer |

- 괄호 "+X" = 함께 로드하는 추가 bfres. Player01·02는 87뼈 순서가 Player00과 같고(덤프 비교 [데이터]) 자기 스켈레탈 애니는 37/31개뿐, Player00은 1,044개 → 추가 파일은 **애니 공유 소스**로 봅니다 [추정: 이름과 뼈 동일성]. Player01 클립 37개 중 35개는 Player00에도 같은 이름이 있음(성별 덮어쓰기 [추정]).
- SuperHook bfres는 모델 5개(`Player00_SuperHook`, `_Point`, `_Scarf`, `_Tentacle`, `Player01_SuperHook`)를 한 파일에 담음 [데이터].
- 파츠 2 `_Hlf` 내용 [데이터]: `Player00_Hlf.bfres.zs` 306 KB(몸 Player00 은 12 MB), 모델 1개 · 뼈 79개(몸 87개에서 `nw4f_root`·`Root_Model`·`Mouth00~04_Model` 등 입 모양 뼈 제외) · 셰이프 3개(`Body`, `Eye`, `Eyelids`, LOD 3단) · 재질 애니 `Color_Eye` 1개, 스켈레탈 애니 없음. 얼굴·입·치아·Inner 셰이프가 없는 축소 몸이다. 리소스 사전 로드 0x7101455640 이 파츠 0~4 를 로드해 홀더 **+0x20(몸) / +0x38(오징어형, 파츠1) / +0x28(`_Hlf`, 파츠2) / +0x30(SuperHook) / +0x48(InkRail)** 에 둔다 [판독: 0x71014556b8 w19=1, 0x71014556cc w28=2 → 0x7101455838 `+0x28`(파츠2), 0x7101455848 `+0x38`(파츠1)]. 정정: 이전 판의 "+0x28 오징어형, +0x38 `_Hlf`"는 순서를 바꿔 읽은 것이다. **용도 = 사람↔오징어 변신 과도기 모델**(원거리·저부하용 아님) — §5.4 [판독].

## 4. 커스터마이즈·기어 → 모델 파일 [데이터]

| 종류 | 규칙 | 근거 |
|---|---|---|
| 머리카락 | `<HairInfo 행>_F` / `_M` (Har_OCT_RVL000/001은 `_F`만) | 27행 전부 파일 존재 |
| 눈썹 | `<EyebrowInfo 행>_F` / `_M` | 8행 |
| 하의 | `<BottomInfo 행>_F` / `_M` | 14행 |
| 머리·옷·신발 기어 | `IsUnisex`면 `<행>`, 아니면 `<행>_F`/`_M` | Head 56+1, Clothes 58+33, Shoes 56 전부 일치 |
| 탱크 | TankInfo `SpecActor` 액터의 ModelInfo `Fmdb`(예 `Tnk_Simple`) | PlayerTank 팩 |
| 무기 | `WmnG_<무기>` 액터 → ModelInfo `Work/Model/Weapon/Wmn_Shooter_NormalT/...fmdb` → `Model/Wmn_Shooter_NormalT.bfres` | WmnG_Shooter_Normal_00 팩 |

`_F`/`_M` 선택이 모델 타입의 F/M을 따른다는 것은 [추정](이름 규칙). 코드에서 접미사를 붙이는 곳은 찾지 않았습니다.

## 5. 스켈레톤·애니메이션

### 5.1 몸 스켈레톤 [데이터]

Player00 87뼈: `nw4f_root > Root > Skl_Root > (Spawner_Root, Spine_1..3 > Clavicle/Arm/Elbow/Wrist/Finger×15/Weapon_L·R, Neck > Head > Ear/Cheek/Eyeblow/Intercostal/Mouth, Tank_Root), Waist > Leg/Knee/Ankle/Toe`, 그리고 `nw4f_root > Root_Model > Mouth00..04_Model`. 바인드: Skl_Root (0, 0.8243, 0), Head (0, 1.2523, 0), Weapon_R (−0.7321, 1.0949, −0.02), Tank_Root (0, 1.1498, −0.144) — 단위 m [추정: 키 ~1.72].

셰이프 16개: Body/Face/Inner/Eye/Eyelids/Tooth 와 입 모양 5벌(Mouth00~04 × M_Face/M_TeamColor). 입 모양은 `Mouth0N_Model` 뼈 가시성 애니(가시성 애니 506개)로 고릅니다 [데이터].

### 5.2 재질 애니로 고르는 외형 [데이터]

| 클립 | 프레임 | 대상 | 의미 |
|---|---|---|---|
| `Color_Eye` | 21 | M_Eye `_a0` 텍스처 패턴 `M_Eye_Alb.00~.21` | 눈 색 = 프레임 번호 [추정: 프레임=색 인덱스] |
| `Color_Skin` | 9 | M_Body·M_Face `const_color0..2`, `scattering_color`, `transmission_rate`, `edge_transmission_power` 커브 | 피부 톤 |
| `Blink` | 8 | M_Eyelids `_o0` 패턴 `M_Eyelids_Opa.0~3` | 깜빡임 |
| `Eye_Scroll` | 360 | M_Eye `tex_mtx0` | 눈동자 이동 |

### 5.3 클립 이름과 상태머신

- Player00 스켈레탈 클립 이름은 `<동작>_<무기 분류>` 형식: 무기 분류 약어 `Shtr Rllr Chrg Slsh Spnr Mnvr Shlt Blst Brsh Strn Sber` 등(예 `WaitHold_Shtr`, `Shoot_Shtr`, `RunShoot_Shtr`, `JumpShoot_Shtr00_St`) [데이터].
- ASB(`ASB `, 버전 u32 0x410) 구조를 판독했다 → **[anim_state_machine.md](anim_state_machine.md)**. 커맨드(사람 235·오징어 26) = 게임 상태 이름(상태 표 0x7105630270, 284/286 일치 [데이터]), 노드 트리(스켈레탈/재질/가시성 애니, 문자열·정수·bool 선택, 실수 블렌드, 동시·순차)로 클립을 고른다 [데이터+추정].
- 정정(이전: "`상태 + "_" + WeaponCategory` [추정]"): ASB 안 클립 이름은 `WaitHold_Nrml`·`Emote_@` 처럼 자리표시자를 갖고, 0x710244d0b0 이 `Nrml` → 무기 변형 문자열(기본 `Shtr`), `@` → 이모트 변형(기본 `Win01`)으로 치환한다(0x710351c964) [판독]. 커맨드 이름과 클립 이름은 다를 수 있다(예 오징어 `PreDive` → `Sqd_Tremble`, `Somersault` → `Sqd_JumpRoll`).
- 블렌드 프레임은 ASB가 아니라 상태 표 값(예 오징어 Wait 10, ToSquid 2/0)이 요청 시 슬롯+0xdc 로 들어간다 [판독: 0x7102451a90].
- 인간↔오징어 [판독] — [../player/player_state.md §6](../player/player_state.md): 오징어 되기 = 상태 0x82(사람 ASB 커맨드 `ToSquid` → 클립 `ToSquid` 6프레임) → 활성 클립 `end < cur + 3` 이 되는 프레임에 0x84(오징어 ASB `ToSquid` → `Sqd_ToSquid` 13프레임, 블렌드 0) → `Wait`(`Sqd_Wait`)/`Walk`. 사람 되기 = 0x91(오징어 `ToHuman` → `Sqd_ToHuman` 3프레임, 블렌드 0) → 같은 조건으로 0x92(사람 `ToHuman` 30프레임). 재생 ASB(SM+0x18)는 0x84/0x92 진입 프레임에 바뀐다. 이때 상태 플래그 bit3 이 켜져 있어 이전 모델 ASB는 정지하지 않고 래퍼+0x38=1 로 표시만 한다. `Sqd_ToHuman` 8/60초(이전 재구현 렌더)에서 오징어가 ~0.01로 줄어드는 것은 3프레임 클립 끝 이후 값이라 이번 판독과 모순되지 않음. 화면 모델 선택은 §5.4, 끝 프레임·판정 순서(end = FSKA FrameCount, 판정은 틱 전 cur)는 [anim_state_machine.md §4.2](anim_state_machine.md) [판독]. `Exit_ToHuman` 은 상태 0xf2(사람 `WorldAppear`) 클립이고, 바로 앞 0xf1(오징어 `WorldAppear`)은 `Sqd_Exit_ToHuman` [데이터].

### 5.4 화면에 그릴 모델 선택 — 몸 / `_Hlf` / 오징어 / 잉크레일 [판독]

경로: 상태기계 표시 플래그 0x710243e2dc → 홀더 0x71014595b0(+0x60 몸, +0x61 `_Hlf` 슬롯, +0x62 오징어, +0x63 잉크레일) → 그리기 제출 0x7101459284(플래그 켜진 모델만 씬 목록에 넣음, 모델+0x281 |= 2; 호출 경로 플레이어 vt 0x71056300f8 → 0x710243a434). 같은 플래그로 0x7101459494 가 표시 모델 목록을 만든다. 디컴파일 `analysis/decomp/render/r4_disp.c`, `r4_holder*.c`.

```
// (a) 0x710243e7d0 끝 — 과도기 카운터 SM+0xf0
if state in 0x82..0x84: f0 += 10
else: 상태표 플래그 bit17 → f0 = min(f0, 70), bit18 → min(f0, 83); f0 = max(f0, 1) - 1
// 다른 쓰기: ToSquid 요청 때 max(f0, 30), 0x91 진입 90, 0x86→0x96 140, 0xe9/0xea 107, 본체+0x785 이면 상한 64

// (b) 0x710243e2dc(SM, dead = 본체+0xa650→+0x31) — 래퍼 틱 뒤
humanOn = SM.humanWrap.cmd(+8) != -1        // 래퍼 정지 0x710244ea40 이 +8 = -1
squidOn = SM.squidWrap.cmd != -1
if 잉크레일 탑승(본체+0xa668 핸들 유효 && 그 상태(+0x24) ∉ 7..11): body = hlf = squid = 0, rail = 1
elif 본체+0x7a0(byte, 의미 [미확정]): 전부 0
else:
  hlf   = humanOn && f0 >= 61 && modelType != Rival
  body  = humanOn && !hlf
  squid = squidOn; rail = 0
  if !body && !hlf && !dead: f0 = (state == 0x96) ? 140 : 90
// 표시가 1→0 이 된 모델은 재질 thr_comp_paint_intens_alpha/bravo/charlie 를 NaN 으로 리셋
// (SM+0x1b0 몸, +0x1b8 _Hlf, +0x1c0 SuperHook, +0x1c8 오징어)

// (c) 홀더 0x71014595b0
if 숨김 타이머(본체 +0xde0>0 | (+0xdf0>0 & +0xe04>0) | (+0xe0c>0 & +0xe1c>0)): 전부 0
elif 본체+0xd60 > 0: squid = rail = 0 (body/hlf 는 직전 값)
elif 생존 && 본체+0xd5c <= 0 && !전역 0x71058bbb9a && !본체+0xa5f4:
  (body, hlf, squid, rail) = SM 플래그
  if 특수 0x1a(Chariot) 사용 중: squid = 0
  if 특수 0xf(SuperHook) 사용 중 && body: body = 0, hlf = 1   // 이때 +0x61 슬롯은 SuperHook 모델(홀더 +0x30)을 그림
  if (body || hlf) && squid:
     if state ∈ {0x91..0x98, 0xad, 0xae, 0xf1, 0xf2} && !(activeWrap.cur == 0 && prevState ∈ 0x82..0x84): squid = 0
     else: body = hlf = 0
else: 전부 0
// "특수 사용 중" = !본체+0x926c && ((+0x678 && +0x678 == +0x688) || (+0x588 && +0x588 == +0x598)) && 본체+0x65c == id
```

- **전환 프레임**: 같은 프레임 안 순서가 상태 갱신(0x710248c97c) → 래퍼 틱 → 표시 결정(0x710248dd94 → 0x710249648c → 0x710243e2dc → 0x71014595b0)이다. 0x84(오징어 ToSquid) 진입 프레임에는 사람 래퍼가 bit3 으로 유지되어 humanOn·squidOn 이 모두 참이지만, (c) 의 마지막 규칙이 한쪽만 남기므로 **두 모델이 한 프레임에 같이 보이는 일은 없다** — 사람 숨김·오징어 표시는 0x84/0x92 진입 프레임에 동시에 바뀐다 [판독]. 그리기 제출이 같은 프레임 뒤 단계라는 것은 [추정]. `cur == 0` 예외는 프레임이 진행되지 않을 때만 걸린다고 본다 [추정].
- **`_Hlf` 표시 구간**: ToHuman(0x92) 진입 때 f0 = 90 → 매 프레임 −1 → 89..61 의 **29프레임 동안 `_Hlf`**, 이후 몸(ToHuman 클립은 30프레임). 0x95 ToHuman_WallJump 는 bit17 상한 70 → 9프레임. 공격·이동 계열(bit17) 상태로 넘어가면 빨리 끝난다. ToSquid(0x82)는 f0 가 30 에서 +10 씩 올라 61 이상이 되는 4번째 프레임부터 `_Hlf` — 0x84 전환 프레임과의 ±1 관계는 [미확정]. Rival(타입 4)은 `_Hlf` 를 쓰지 않는다.
- `_Hlf`·SuperHook 뼈는 몸에서 복사한다(0x7101459154: 몸 vt+0x78 get → vt+0x70 set) [판독].
- 몸만 보이는 상태로 바뀌는 순간 스프링 0x71014586a0: x = −0.03, v += 0.02, 매 프레임 `v = (v − 0.2x)·0.8; x += v`, 몸·`_Hlf` 모델 +0x268/+0x270 = 1 + 1.5x, +0x26c = 1 + x [판독]. 이 세 값이 축별 스케일(튀어나오는 연출)이라는 것은 [추정].
- 계산(애니) 플래그 0x71014585b4: +0x64(사람) = body || hlf, +0x65(오징어) = squid, 아무것도 안 보이면 둘 다 1. 상태 0x91..0x98 이거나 특수 0x1a 면 사람 계산, 0x82..0x84 면 오징어 계산을 켠다 [판독, 용도 추정].
- 정정: 표시 후보로 보았던 0x710389d410 은 모델 가시성이 아니라 **XLink 유저(사운드·이펙트) 켜기/끄기**다(모델+0xf8 bit1, xlink 코어 0x710389e90c 계열; 대상 `PlayerVoice_%s`, `Player_Focused/Friend/Enemy`, `PlayerFoot` 유저). 그것을 부르는 0x71026bb0a0 은 씬 이름이 `"PlayerMake"` 일 때만 호출된다(0x710248cffc) [판독].


## 6. 파츠 결합

### 6.1 원본에서 확인한 것

- 눈썹: 몸 `Head`, `Head_Intercostal`, `Head_Eyeblow_L/R` ↔ 눈썹 모델 `Head_Root`, `Head_Intercostal`, `Head_Eyeblow_L/R` 뼈 인덱스 쌍을 조회해 저장(+0x318~+0x334) — 0x71026ddd58 [판독].
- 머리카락: 몸 `Head`, `Root`, `Spine_3` ↔ 머리카락 `Head_Root`, `Spine_3` (+0x33c~+0x34c) — 0x71026e2450 [판독]. 머리카락 고유 뼈(`Front_*`, `Hair_*_L/R`, `Nape_1`)는 천 물리(`Phive/Cloth/Har_*.bphcl`, `ClothCullingParam.CullFrame 4`)가 움직임 [데이터], 형식·웹 대체는 아래 "머리카락 천 물리" 항목.
- 무기: 무기 초기화 함수가 몸 모델(+0x110)에서 `"Weapon_R"`(+0x3b8), 쌍권총류는 `"Weapon_L"`(+0x3bc)도 조회 — 0x71028754d0, 0x710288030c [판독]. 무기 모델 뼈 `Root`, `Muzzle`(발사구, Root 기준 (0, 0.1872, 0.6923)).
- 탱크(하네스) — 0x71026f8f38(뼈 가시성 vt+0x90) [판독]: `show = !src+0x6ac`, `thin = src+0x6ad`, `type = src+0x6a8`(→ +0x18c0/+0x18c1/+0x182c, 쓰기 0x7102493d18). `Harness_{S,M,L}` = show && type == {0,1,2} && !thin, `Harness_{SF,MF,LF}` = show && type == {0,1,2} && thin, `Harness_Hide` = !show. 0x71026f5808 은 뼈 인덱스 조회만(S +0x1814, M +0x1818, L +0x181c, SF +0x1820, MF +0x1824, LF +0x1828, Hide +0x18bc). 필드 ↔ GearInfoClothes 이름(+0x6a8 HarnessType, +0x6ac IsHideHarness, +0x6ad IsThinHarness) 대응은 [추정: 이름·형식].
- 신발: 액터 `Shs_*`에 `MirrorModel{Fmdb: 같은 모델}` 컴포넌트 → 모델은 왼발(`Leg_2_L, Ankle_Assist_L, Ankle_L, Toe_L`)만 있고 오른발은 미러 [데이터]. 구현 [판독]: 오른발 = 같은 Fmdb 의 두 번째 인스턴스(컴포넌트 +0x60, 미러 플래그 +0xa0; 왼발 +0x18/+0x58). 0x71026f09f4 가 신발 뼈 `*_L` → `*_R` 로 몸 뼈 쌍을 조회하고, 0x71026f1000 이 몸 `_R` 뼈 행렬을 복사한 뒤 0x7100f63364 로 3×4 행렬의 **회전부 9개 부호만 반전**(평행이동 유지, R·(−I)). Player00 바인드에서 R_R = −S·R_L(S = diag(−1,1,1))이 오차 0 으로 성립 → 결과는 정확한 X 미러이고 §6.3 의 mirrorX 결합식과 수학적으로 같다 [판독 + 데이터 계산]. 웹: `rightSkin = boneR_world · diag(−1,−1,−1) · invBindL`, 감김 방향 반전. `RightFmdb` 는 Shs 56개 팩 모두 없음 [데이터].
- 모자: `GearHeadParamSet`의 `ManualBindSRT[V<변형>_<머리>]`(Scale/Translate/Rotate)로 머리 모양마다 모자 위치를 보정하고, `HairArrange[V].PresetMap[<머리>]` → `HairArrangeParam.BoneParamArray[{BoneName(ScalerA..C, Knot_1...), Scale, Rotation, Transform, AnimReduceRt}]`로 모자 아래 머리카락 뼈를 조정 [데이터].
  - ManualBindSRT 적용 0x71026e4e80 [판독]: 키 `"V%d_%s"`(변형 번호, 머리카락 행 이름에서 앞 `Har_` 를 뺀 것), 행렬 = **T · Rz · Ry · Rx · S**(각도는 도, ×0.017453292), 모자 객체 +0x380 에 3×4 로 저장, 키가 없으면 단위행렬. SRT 구조체: Rotate +0x30, Scale +0x3c, Translate +0x48. 같은 함수의 switch(0..4)가 +0x3b0/+0x3b1 에 쓰는 값의 의미와, 이 행렬이 §6.3 모자 결합의 어느 단계에 곱해지는지는 [미확정].
  - HairArrange: 0x71026e44a0 이 PresetMap 을 **모자 객체(`spl::PlayerCustomHead`, vt 0x7105641998 슬롯 8)** +0x360 맵(키 = 머리카락 id + 변형×10000, 변형 수 = 모자+0x3b8 ← GearInfo 행 +0x74)에 적재 [판독]. 정정: 이전 판의 "홀더+0x360" 은 모자 객체다. BoneParam 오프셋 BoneName +0x30, AnimReduceRt +0x38(기본 1.0), Rotation +0x3c, Scale +0x54, Transform +0x60. `ldr #0x360` 은 main 플레이어 영역에서 적재 함수 안(0x71026e4d0c)뿐이라 맵은 포인터(`add #0x360`: 0x71026e4728, 0x71026e5cfc)로 넘겨 읽는 것으로 보인다. 뼈 적용 후보 = 모자 vt 슬롯 49 **0x71026e613c**(+0x380/+0x390/+0x3a0 = ManualBindSRT 행렬을 읽는 유일한 함수 [판독: 적재 패턴 스캔]), 15 0x71026e5e00, 11 0x71026e5ccc 와 머리카락 vt 0x71056416f8 슬롯 48~51(0x71026e2bdc, 0x71026e3118, 0x71026e3728, 0x71026e382c). 디컴파일은 `analysis/decomp/gfx4/p_batch1.c` 에 받아 두었고 **읽지 않았다** — 적용식·ManualBindSRT 와의 결합 순서는 [미확정].
- 머리카락 천 물리 [데이터]: `Phive/Cloth/Har_*.bphcl` = "Phive" 헤더 + Havok TAG0(SDKV 20210100) `hclClothContainer`. Har 팩 54개 중 46개에 있고 `_F`/`_M` 이 같은 파일. 예 SQD000: 천 `Cloth_Hair_L/R`, `Cloth_Rear`, 입자 뼈 `Hair_1..4_L/R`, `Nape_1`; 충돌 캡슐 `Collidable_Head_Root_1`, `Collidable_Spine_3`; 제약 Standard/Bend/Stretch Link, LocalRange, Volume; gravity, SpringGravity0; `hclBoneSpaceSkinPOperator`. `ClothCullingParam.CullFrame 4`, ControllerSet ClothList `"Default"`, 클래스 `spl::PlayerCustomHair`. **상수 해독 완료 → [hair_cloth.md](hair_cloth.md)**: `collision_tag0.py` 실패 원인 = TBDY 멤버 flags 0x80 일 때 붙는 packed 정수 1개 미처리. 새 도구 `web/tools/gfx4p_bphcl.py` 로 덤프 [실행]. SQD000 `Cloth_Hair_R/L`: 입자 9(고정 2), 질량 0.714286, 반경 0.05, 마찰 0.5, 중력 (0,−9.81,0), 감쇠 0.001/s, subSteps 1·반복 1, 실행 순서 LocalRange→Transition→Standard→Bend×2→Stretch, LocalRange k 0.8 [데이터]. 샘플 `analysis/render/bphcl/Har_SQD000_F.bphcl`. 웹 대체: hair_cloth.md §4 의 PBD 근사 [추정 — 원본 동등성 미보장].
- 몸 가림: 기어 `AlphaMaskF/M` → `GearAlphaMask` 텍스처 `<이름>_Opa` [판독: 0x7102b8ca48]. 기어가 바뀔 때 0x71024950cc(0x710249257c 안)가 이전 마스크를 해제(0x7102b8cc08)하고 새 마스크를 조회해 홀더+0xe8 텍스처 컨테이너에 등록 [판독]. 재질 슬롯 바인딩은 [미확정] — 후보 ① 몸 재질 `_op0`(cTexOpacity, UV0) 교체(샘플러 이름으로 텍스처를 바꾸는 0x71011805b4/0x71011807c8 존재) [추정], ② 셰이더 심볼 cAlphaCutTexture(gsys_user5)는 몸 프로그램이 쓰지 않음.
  - 추가 판독(gfx4): 컨테이너 = 0x7102b8c868 이 만들어 홀더(컴포넌트 0x37)+0xe8 에 저장(0x7101456850). 0x7102b8ca48 은 전역 GearAlphaMask 레지스트리(*0x7105793a00, +0x60 트리 = 이름 해시 키, 0x7102b8d04c 가 아카이브 텍스처마다 0xe0 B 항목 적재)에서 `<이름>_Opa` 를 찾아, 풀(+0xb08, 개수 +0xb00/상한 +0xb18)에서 항목을 꺼내 +0xaf0 목록 앞에 잇고 +0x2b8 트리(키 = 해시 +0x20, 개수 +0x2c0, 잠금 +0x2e8)에 넣는다. 등록이 바뀌면 호출자 0x710249257c 가 홀더+0xf0 = 현재 프레임+1 로 표시한다 [판독]. 컨테이너 +0x2b8 을 읽는 다른 함수는 0x7102b8c668(호출자 0x7102b8c800)뿐이고 내용은 미독 [미확정]. 0x71011805b4 호출자 중 커스텀 파츠 쪽 0x71026da7e0 은 `M_body` 의 `_a0`(알베도) 교체라 마스크가 아니다 [판독: 문자열].
  - 몸 셰이더 쪽 식(Player00 M_Body 프로그램 5549, `analysis/shader/hoian_uber/Player00__M_Body.frag` 384·496행) [판독: 역번역]: `a = texture(cTexOpacity(_op0), uv0).x * in_attr2.w; if (a < Mat.gsys_alpha_test_ref_value.x) discard;` (`enable_opacity_tex = 1`). 마스크가 `_op0` 에 들어간다면 기어가 덮는 몸 영역은 이 알파 테스트로 잘린다 — 연결 자체는 [추정].

### 6.2 바인드 데이터에서 확인한 것 [데이터]

`analysis/graphics/bind_compare.py`(덤프 기반) 결과:

- 파츠 뼈 중 몸과 이름이 같은 뼈는 **회전이 몸 바인드와 같고 위치만 상수만큼 다름**: Clt·Btm은 Skl_Root 높이(0.8243), Shs는 Leg_2_L, Tnk는 Spine_3(1.0593), Eyb는 Head(1.2523). 즉 파츠 모델 공간 = 몸 공간 − 부착 뼈 바인드 위치.
- 머리카락·눈썹 `Head_Root` = 원점, 회전은 몸 `Head`와 같음.
- 모자 `Root`·무기 `Root` = 원점·단위 회전. 모자 정점은 세계축 기준(위=+y, 0.11~0.60), 무기 정점은 +z가 총구 방향.

### 6.3 웹 결합 알고리즘 (검증 페이지 `view.html`의 `attach()`)

```
입력: body(스켈레톤, bodyBind[name] = 바인드 월드), part glb, map(파츠 뼈→몸 뼈 이름), attachPart, mode, mirrorX
partBind[name] = 파츠 바인드 월드(SkinnedMesh boneInverses 의 역, 리지드는 노드 월드)
A = bodyBind[attachBody] · partBind[attachPart]⁻¹          // 파츠 공간 → 몸 공간
if mode == 'translate': A = 평행이동 성분만
if mirrorX: A = Scale(-1,1,1) · A   (attachBody 는 왼쪽 뼈 그대로, map 은 *_L → *_R)
스킨 메시마다:
  뼈 j 가 몸에 있으면(map 적용): bone = 몸 뼈, inverse = bodyBind[몸 뼈]⁻¹ · A
  없으면(머리카락 고유 뼈): 새 뼈를 (map된) 부모 아래 만들고 local = parentBind⁻¹ · A · partBind[j], inverse = partBind[j]⁻¹
  미러면 재질 side = BackSide (행렬식 음수로 감김 방향 반전)
리지드 메시(스킨 0): 몸 뼈 자식, matrix = bodyBind⁻¹ · A · partBind(노드) · (노드 기준 메시 변환)
```

| 파츠 | map | attachPart | mode |
|---|---|---|---|
| Har_*, Eyb_* | Head_Root→Head | Head_Root | full(=평행이동) |
| Clt_*, Btm_* | 같은 이름 | Skl_Root | full |
| Shs_* 왼발 / 오른발 | 같은 이름 / `*_L→*_R` | Leg_2_L | full / full+mirrorX |
| Tnk_* | 같은 이름 | Spine_3 | full |
| Wmn_* | Root→Weapon_R | Root | **full** (손 뼈 회전 포함) |
| Hed_* | Root→Head | Root | **translate** (머리 위치 평행이동, 이후 머리 회전 변화만 따라감) |

무기 full / 모자 translate는 렌더로 고른 것입니다 [실행: 재구현 렌더]: `Shoot_Shtr`에서 full이면 총구가 앞을 향하고 손잡이가 손에 있음, translate면 총이 세워짐(`scene_assembled_clip_Shoot_Shtr_frame_0_attach_{full,translate}.png`). 모자는 translate면 머리에 씌워지고 full이면 얼굴 앞으로 돌아감(`scene_assembled_hat_1_hatattach_{translate,full}.png`). 원본 코드 경로는 [추정], ManualBindSRT 보정(행렬식은 §6.1)은 아직 넣지 않음.

### 6.4 갱신 순서 (웹)

```
매 프레임: mixer.update(dt) → body.updateMatrixWorld() → (파츠 뼈가 몸 뼈 객체를 직접 공유하므로 추가 동기화 없음)
            → 머리카락 고유 뼈(천 물리 대신 정지) → render
```
원본은 파츠별 뼈 인덱스 쌍으로 행렬을 복사하는 구조로 보입니다(쌍 조회만 판독) [추정]. 공유 방식과 결과가 같도록 위 inverse 식을 썼습니다.

## 7. 검증 [실행: 재구현]

- `node web/tools/graphics_verify/shot.mjs <query>` (헤드리스 chromium, swiftshader). 결과 `analysis/graphics/shots/*.png`와 `.json`(bbox, 결합 뼈 대응 목록):
  - `scene_body` 바인드 bbox (−0.902, 0.014, −0.281)~(0.902, 1.723, 0.311)
  - `scene_assembled` T포즈 조립: 8파츠(머리카락 고유 뼈 11개 생성, 나머지 같은 이름 대응)
  - `scene_assembled_clip_Wait_frame_0`, `..._Shoot_Shtr_frame_0`, `..._Run_frame_10_yaw_60`, `scene_assembled_hat_1_clip_WaitHold_Shtr_frame_0`: 손에 무기, 양발 신발, 하네스 S만 표시
  - `scene_squid_clip_Sqd_Wait_frame_0`(팀색 몸), `scene_squid_clip_Sqd_ToHuman_frame_8`(축소)
- 콘솔 404 1건은 favicon 요청 [추정]; 텍스처 누락 0(meta 확인).
- 원본 화면과의 픽셀 비교는 하지 않았습니다. 셰이더·조명·천 물리·모자 보정이 없는 근사입니다.

## 8. 미확정과 필요한 근거

| 항목 | 필요한 것 |
|---|---|
| ASB 상태 그래프·클립 선택·블렌드 | 노드 종류·끝 프레임·블렌드 곡선·블랙보드 공급 판독 → [anim_state_machine.md](anim_state_machine.md) §2.5, §4. 남은 것은 거기 §6 |
| ~~인간↔오징어 표시 전환~~ | 해소: §5.4(같은 프레임에 한 모델만). 남은 것: ToSquid 쪽 `_Hlf` 시작 프레임과 0x84 전환의 ±1, 숨김 필드(+0xde0/+0xdf0/+0xe04/+0xe0c/+0xe1c/+0xd60/+0xd5c/+0xa5f4, 전역 0x71058bbb9a, 본체+0x7a0) 의미 |
| ~~천 물리 상수~~ | 해소: [hair_cloth.md](hair_cloth.md)(gfx4p_bphcl.py). 남은 것: 게임 쪽 스텝 dt·CullFrame 적용(머리카락 vt 슬롯 48~51), Havok 런타임 식, 다른 Har 상수 |
| HairArrange 적용 | 맵은 모자 객체+0x360(정정). 후보 함수 디컴파일 `analysis/decomp/gfx4/p_batch1.c`(모자 vt 슬롯 49 0x71026e613c 등) 미독 — 적용식·ManualBindSRT 결합 순서 [미확정] |
| ~~신발 미러~~ | 해소: 회전부 부호 반전 = X 미러(§6.1) |
| ~~하네스 선택식~~ / GearAlphaMask 슬롯 | 하네스 해소(§6.1, 필드 이름 대응만 추정). GearAlphaMask: 컨테이너 등록 구조·몸 셰이더 알파 테스트식 판독(§6.1). 남은 것: +0x2b8 을 읽는 0x7102b8c668(호출자 0x7102b8c800) → 재질 샘플러 연결 |
| ~~`_Hlf` 용도~~, `_F/_M` 접미사 코드 | `_Hlf` 해소(§3, §5.4). `_F/_M` 접미사 코드는 미확인 |
