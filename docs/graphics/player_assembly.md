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
  - **추가 판독(2026-10-03):** AS 바인더(vt 0x7105632770) 슬롯 3 0x710244b414 는 이름으로 애니를 찾을 때 애니 리소스 목록(바인더+8 → +0x58, 개수 +200, 배열 +0xd0)을 앞에서부터 돌고 **처음 찾은 파일**의 순번(앞 파일들의 애니 수를 더한 값)을 돌려준다. 스켈레탈은 파일 +0x20→+0xe2, 가시성은 +0xe8 개수를 더한다 [판독: `analysis/decomp/r5_gfx_char/binder.c`]. 따라서 여러 bfres 가 한 바인더의 애니 원본으로 쓰이고, 같은 이름은 목록 앞쪽 파일이 이긴다. 2026-10-03 r8 **추가 확정 [실행]+[판독]:** 2656ac8→2656870/2657260의 실제 배열은 몸 타입 0..4 순서로 `[Player00]`, `[Player01,Player00]`, `[Player02,Player00]`, `[Player03,Player01,Player00]`, `[Player02,Player00]`다. SDK 366f140→366f280은 입력 배열 순서대로 바인더+0xD0에 복사한다. 따라서 자기 파일 클립이 우선하고 뒤 파일은 같은 바인더의 애니 공유 소스다. 기존 추정은 이 원본 순서로 정정한다.
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

**정정(2026-10-03 r8) [실행]+[판독]:** 실제 26fd010은 `(modelType | 2)==3`이면 `_M`, 나머지는 `_F`다. 타입 0/2/4는 F,1/3은 M. 기어 IsUnisex는 접미사를 생략한다. 홀더+34 writer144f9a0와 caller1450cc4까지 연결했다. [전용 문서](part_suffix_runtime.md) §3~§10, 원본240/240.

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

**눈 색·피부 색 번호 → 재질 애니 프레임 [판독]+[실행].** 정정(2026-10-03): 위 표의 "프레임 = 색 인덱스 [추정]"을 확정으로 바꾼다.
- 플레이어 초기화 0x71024719d4 가 플레이어 정보의 피부 색(+0x844)으로 0x71014522b0 을, 눈 색(+0x848)으로 0x710145249c 를 부른다(0x71024743d4~0x71024743e8). 홀더(+0x1b8) 쪽 별도 모델에는 0x7101456e48(피부)·0x7101456f5c(눈, 두 모델)를 부른다 [판독].
- 0x710145249c(홀더, idx): 처음 한 번 애니 객체(홀더+0x48, 종류 0xd)에 `Color_Eye` 를 붙이고 프레임 0·속도 1 로 만든 뒤 속도를 0 으로 둔다. 그다음 `0 <= idx < FrameCount(Color_Eye)` 일 때만 홀더+0x3c = idx, 애니+0x1c(프레임) = (f32)idx 로 쓰고 모델 재질을 갱신한다. 범위 밖이면 아무것도 바꾸지 않는다(이전 프레임 유지, 처음이면 0). FrameCount 는 0x71036751a4 가 FMAA +0x58 에서 읽는다 [판독].
- 피부(0x71014522b0, 종류 0xe, `Color_Skin`)도 같은 꼴이다. 범위 안이면 홀더+0x38 = idx 로 쓰고, 추가로 머리카락·눈썹 쪽 0x71026e14b4/0x71026d891c 를 부른다(내용 미독) [판독].
- 데이터: Player00 `Color_Eye` 는 FrameCount 21 이고, 패턴 키는 프레임 0..21 에 `M_Eye_Alb.00`..`.21` 이 있다. 따라서 **쓸 수 있는 눈 색은 0..20 이고 `M_Eye_Alb.21` 은 닿지 않는다** [데이터+실행]. impl/assets §5 의 "`.21` 이 Player00 에 없음" 문제는 원본에서도 쓰이지 않는 키다.
- 검증: `PY web/tools/r5_gfx_char_eye_emu.py` → `analysis/completion/r5/gfx_char_eye_emu.json`. 원본 0x710145249c 와 0x71036751a4 를 실행했다. FrameCount 21/22/1/8 × idx(−3..FrameCount+3, ±2³¹)에서 판독식과 **88/88 일치**했다. 스텁은 0x7101262c18(애니 적용)과 0x7103673874/0x7103674288/0x7103673fd0(재질 갱신)이며, 호출 여부만 기록했다. 첫 진입 초기화 경로는 실행하지 않았다.
- 플레이어 정보 +0x844/+0x848 의 값 출처(세이브·플레이어 만들기)는 [미확정]이다. 저장 키 `SkinColor`/`EyeColor` 가 0x7102a67b94 등 세이브 기록 함수에 있지만 기본값은 찾지 못했다.
  - **추가(2026-10-03 r6) — 세이브 커스텀 구획의 기본값 [판독]:** 0x7102a67b94 는 vtable 0x7105665240 의 슬롯 19 다. 같은 vtable 의 슬롯 2 0x7102a66e28 이 필드를 초기값으로 채우고, 슬롯 18 0x7102a66e54 가 키로 읽는다. 키는 필드 이름의 murmur3_32(시드 0)이고, main 문자열과 대조해 16개 모두 맞췄다. 초기값은 아래와 같다.

    | 오프셋 | 이름 | 슬롯 2 초기값 |
    |---|---|---|
    | +0x48 | ModelType | 0 (읽을 때 < 5 만 받음) |
    | +0x4c | WeaponId | −1 |
    | +0x50 / +0x54 | GearHeadId / GearHeadVariationId | −1 / 0 |
    | +0x58 / +0x5c | GearClothesId / GearClothesVariationId | −1 / 0 |
    | +0x60 / +0x64 | GearShoesId / GearShoesVariationId | −1 / 0 |
    | +0x68 | HairId | 0 |
    | +0x6c / +0x70 | BottomId / BottomVariation | 0 / 0 |
    | +0x74 / +0x78 | SkinColor / EyeColor | 0 / 0 |
    | +0x7c / +0x80 | Eyebrow / CoopSkin | 0 / 0 |
    | +0x84 | WinEmote | −1 |

    슬롯 2 가 "새 세이브의 초기값" 경로라는 것은 [추정: vtable 위치와 내용]이다. 기어·무기 −1 이 어떤 모델로 풀리는지는 [미확정]이다(다음: 플레이어 정보 +0x844 등을 채우는 함수에서 −1 처리, `PlayerMake` 씬).

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
elif 본체+0x7a0(byte, 의미 [미확정]): 전부 0 // 2026-10-03 아래 정정 참조
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
- **2026-10-03 잠영 표시 정정/실행 보완:** 위 B7a0의 의미 미확정은 r8 [player_state §6.1.4](../player/player_state.md#614-b7a0-지연된-판정값의-producer--8차-판독)의 ordinary ally squid+특수 candidate 지연 writer로 해소되어 있다 [판독]. 표시 reader243e2dc의 ordinary/invalid-rail 진입 블록을 신규64경우 실행하여 B7a0 켜짐→body/hlf/squid/rail 모두0과 꺼짐의 Hlf threshold/type 조건을64/64 확인했다 [실행-부분]. producer/그 뒤 counter·NaN reset/holder/GPU는 이 실행 범위에 넣지 않았다. 웹 PlayerSnap/draw에는 B7a0 숨김 입력이 없다. 자세한 근거는 [ink_visual_path §6.3](ink_visual_path.md#63-숨김-gate--신규-원본-실행진입-블록).

- **2026-10-03 r2 정밀화 [판독]+[실행]:** 위 의사코드의 “재질을 NaN으로 리셋”은 **바인더 캐시와 실제 setter 인자를 구분하지 않은 표현**이다. off 경로는 캐시 3칸에 `0x7fc00000`을 쓰지만 재질 setter의 S0에는 **0.0**을 전달한다. whole SM 2,048건에서 reset 11,136회·후속 stain 128회를 구분해 확인했다(재질 setter 4개는 capture/return fixture). ordinary 후보 생산 블록 10,800건·whole holder 4,096건·수동 연결 272프레임도 일치했다. `B+d60>0`은 오징어/레일만 끄고 몸/`_Hlf`의 이전 플래그를 보존한다. 앞선 entry64 결과는 유지하되 이 새 범위와 중복 계상하지 않는다. StepPaint/Phive 입력 공급·전체 슬롯19·실제 GPU 표시는 미확정이다. [상세 실행 경계와 정정](squid_ink_visibility_r2.md#6-계산식조건상세-의사코드).

- **`_Hlf` 표시 구간**: ToHuman(0x92) 진입 때 f0 = 90 → 매 프레임 −1 → 89..61 의 **29프레임 동안 `_Hlf`**, 이후 몸(ToHuman 클립은 30프레임). 0x95 ToHuman_WallJump 는 bit17 상한 70 → 9프레임. 공격·이동 계열(bit17) 상태로 넘어가면 빨리 끝난다. ToSquid(0x82)는 f0 가 30 에서 +10 씩 올라 61 이상이 되는 4번째 프레임부터 `_Hlf` — 0x84 전환 프레임과의 ±1 관계는 [미확정]. Rival(타입 4)은 `_Hlf` 를 쓰지 않는다.
  - **확정(2026-10-03 r6) [판독]:** ToSquid 요청은 상태기계 0x710243e7d0 안 0x7102440e6c(0x82)·0x7102440ef0(0x82/0x83 `cinc`) 두 곳이고, 둘 다 0x7102440e70 으로 모여 0x7102447bfc 로 요청한 뒤 `f0 = (s32) max((f32) f0, 30.0)`(0x7102440e80~0x7102440eb0)를 쓴다. 그다음 0x7102440488 로 가서 같은 함수 끝의 과도기 갱신 블록(0x710244089c~0x7102440968: 상태 0x82..0x84 이면 `f0 += 10`)을 반드시 지난다. 제어 흐름 검사 `PY web/tools/r6_gfx_char_cfgpath.py 0x710243e7d0 10940 0x7102440e80 0x710244089c --write-off 0xf0` 결과, 0x7102440e80 에서 함수 끝까지 0x710244089c 를 지나지 않는 경로는 없고, 그 사이 SM+0xf0 쓰기는 max(30) 한 곳뿐이다. 그 사이에 부르는 0x7102442354 의 SM+0xf0 쓰기(0x7102442990/0x7102442bdc = 0x40)는 상태 0xbc~0xbe 요청 뒤에만 있다.
  - 따라서 요청이 그 프레임에 받아들여져 SM+0xc8 = 0x82 가 되면, 요청 프레임 S 의 f0 = max(f0, 30) + 10 = 40(직전 f0 ≤ 30 일 때)이다. 이어서 S+1 = 50, S+2 = 60, S+3 = 70 이다. 표시 결정(0x710243e2dc)은 같은 프레임의 상태 갱신 뒤에 돌므로 **`_Hlf` 는 S+3 한 프레임**이다. S+4 에 0x84(오징어 ToSquid, 클립 FrameCount 6 기준 §4.2 판정)로 넘어가면 (c) 규칙이 사람 쪽을 끄므로 오징어만 보인다. 0x7102447bfc 가 요청을 미루는 경우(SM+0x1d4 지연 요청)는 이 계산에 넣지 않았다.
- `_Hlf`·SuperHook 뼈는 몸에서 복사한다(0x7101459154: 몸 vt+0x78 get → vt+0x70 set) [판독].
- 몸만 보이는 상태로 바뀌는 순간 스프링 0x71014586a0: x = −0.03, v += 0.02, 매 프레임 `v = (v − 0.2x)·0.8; x += v`, 몸·`_Hlf` 모델 +0x268/+0x270 = 1 + 1.5x, +0x26c = 1 + x [판독]. 이 세 값이 축별 스케일(튀어나오는 연출)이라는 것은 [추정].
  - **정정·확정(2026-10-03):** 스프링 0x71014586a0 전체를 원본 실행으로 확인했다 [실행]. 상태는 홀더 +0xa0(직전 "몸만" 플래그), +0xa1(직전 "무엇이든 보임"), +0xa4 = x, +0xa8 = v, +0xac(발동 기록)이다.
    ```
    x_old = x
    if 본체+0xa650→+0x30 || +0x31:          # 죽음 계열 플래그
        a0 = a1 = 0; x = v = 0; x_old != 0 이면 아래 기록(x = 0 → 스케일 1)
        return
    bodyOnly = body(+0x60) && !hlf(+0x61) && !squid(+0x62)
    if a0 != bodyOnly:
        a0 = bodyOnly
        if bodyOnly && a1:                   # 직전 프레임에 무엇이든 보였을 때만
            ac = 1; x = −0.03; v += 0.02
    a1 = body || hlf || squid
    v = (v + x·(−0.2))·0.8;  x = x + v       # f32, 곱·덧셈 분리(FMA 아님)
    if |x − 1| ≤ 0.001 && |v| ≤ 0.0001: x = 1, v = 0   # 평형 0 근처에서는 성립하지 않는 분기
    if x != x_old:
        sY = x + 1; sXZ = sY + 0.5·x
        몸(+0x20) 모델: +0x268 = sXZ, +0x26c = sY, +0x270 = sXZ, +0x280 |= 1
        SuperHook 사용 중(본체+0x65c == 0xf 이고 특수 사용 조건)이면 +0x30 모델, 아니면 _Hlf(+0x28) 모델에 같은 값
    ```
    - 트리거 정정: "몸 표시 0→1"이 아니라 **"몸만 보임"이 0→1 이 되고 직전 프레임에 어떤 모델이든 보였을 때**다. `_Hlf` → 몸, 오징어 → 몸은 발동한다. 아무것도 안 보이다가 몸이 나타나는 경우(예: 숨김 타이머 해제)는 발동하지 않는다.
    - 축: 모델 +0x268/+0x26c/+0x270 은 모델 루트 행렬의 X/Y/Z 축 스케일이다. 근거: 모델 루트 행렬 설정 0x7100f735b0 이 3×4 행렬의 열0/열1/열2 길이를 같은 세 칸에 쓴다 [판독]. 따라서 스프링은 **가로(X)·깊이(Z) 1 + 1.5x, 높이(Y) 1 + x** 다.
    - 검증: `PY web/tools/r5_gfx_char_attach_emu.py` → `analysis/completion/r5/gfx_char_attach_emu.json` "spring". 60개 열 × 240프레임에서 표시 플래그·죽음·SuperHook 슬롯을 무작위로 바꿨다. 홀더 상태(a0, a1, x, v)와 세 모델의 스케일 기록·미기록을 판독식과 비교해 **14400/14400 일치**했다(발동 93회). 외부 호출이 없는 함수라 스텁은 없다. 표시 플래그 producer(0x71014595b0)와 실제 프레임 순서는 실행하지 않았다.
- 계산(애니) 플래그 0x71014585b4: +0x64(사람) = body || hlf, +0x65(오징어) = squid, 아무것도 안 보이면 둘 다 1. 상태 0x91..0x98 이거나 특수 0x1a 면 사람 계산, 0x82..0x84 면 오징어 계산을 켠다 [판독, 용도 추정].
- **오징어 몸 절차 변형(2026-10-03 r6, 구조만 [판독]):** 오징어형 모델(홀더 +0x38)의 뼈는 스켈레탈 클립(`Sqd_*`) 위에 게임 코드가 한 번 더 움직인다.
  - 객체: 플레이어 +0x770(0x39f8 B, 생성자 0x7102639aa8, vtable 0x710563cfd8 은 소멸자 2칸뿐). 플레이어 초기화 0x71024397bc 가 만들고, 0x710263a3f4(객체, 오징어 모델, 모델 타입)로 뼈 번호를 찾는다. 타입 < 2(잉클링)는 `Sqd_root, Sqd_joint_root, Sqd_waist, Sqd_arm1~3_R, Sqd_legD1/D2, Sqd_legC1/C2, Sqd_legB1/B2, Sqd_legA1/A2, Sqd_arm1~3_L, Sqd_head0~2, Sqd_eye_L/R, Sqd_forehead`(+0x24~+0x7c)이고, 문어(타입 ≥ 2)는 표 0x710563cfe8 의 이름으로 +0x104~ 에 둔다. 번호 형식은 (모델 번호 | 뼈 번호 << 16), 없으면 0xffffffff 다.
  - 매 프레임: 플레이어 갱신 0x710243a4ec 가 0x710263b7d0(객체, 홀더+0x62 오징어 표시)을 부른다. 이 함수는 본체 위치·회전(+0x1c~+0x3c)으로 쿼터니언 차분을 만들어 +0x26f0~+0x27a0 상태(동역학)를 갱신한다. 리셋 조건(0x710245903c 참 && 오징어 미표시, 또는 본체+0x1054 == 0)이면 상태를 단위값으로 되돌리고 +0x2788 = (0.2, 0.2) 로 둔다. 홀더+0x65(오징어 계산)이면 0x710263dacc 가 뼈 로컬 변환을 쓴다(뼈 vt+0x68). 보조 0x710263f9dc/0x71026403e0 이 다리·팔 사슬을 처리한다.
  - 디컴파일 `analysis/decomp/r6_gfx_char/squid_bones.c`, `squid_ctrl.c`. 수식(상수·적분)은 **[미확정]**이다. 9 KB + 7.5 KB 함수라 이번에 다 읽지 못했다. 웹은 지금처럼 클립만 쓰면 이 변형이 빠진다.
- 정정: 표시 후보로 보았던 0x710389d410 은 모델 가시성이 아니라 **XLink 유저(사운드·이펙트) 켜기/끄기**다(모델+0xf8 bit1, xlink 코어 0x710389e90c 계열; 대상 `PlayerVoice_%s`, `Player_Focused/Friend/Enemy`, `PlayerFoot` 유저). 그것을 부르는 0x71026bb0a0 은 씬 이름이 `"PlayerMake"` 일 때만 호출된다(0x710248cffc) [판독].


## 6. 파츠 결합

### 6.1 원본에서 확인한 것

- 눈썹: 몸 `Head`, `Head_Intercostal`, `Head_Eyeblow_L/R` ↔ 눈썹 모델 `Head_Root`, `Head_Intercostal`, `Head_Eyeblow_L/R` 뼈 인덱스 쌍을 조회해 저장(+0x318~+0x334) — 0x71026ddd58 [판독].
- 머리카락: 몸 `Head`, `Root`, `Spine_3` ↔ 머리카락 `Head_Root`, `Spine_3` (+0x33c~+0x34c) — 0x71026e2450 [판독]. 머리카락 고유 뼈(`Front_*`, `Hair_*_L/R`, `Nape_1`)는 천 물리(`Phive/Cloth/Har_*.bphcl`, `ClothCullingParam.CullFrame 4`)가 움직임 [데이터], 형식·웹 대체는 아래 "머리카락 천 물리" 항목.
- 무기: 무기 초기화 함수가 몸 모델(+0x110)에서 `"Weapon_R"`(+0x3b8), 쌍권총류는 `"Weapon_L"`(+0x3bc)도 조회 — 0x71028754d0, 0x710288030c [판독]. 무기 모델 뼈 `Root`, `Muzzle`(발사구, Root 기준 (0, 0.1872, 0.6923)).
  - **정정(2026-10-03):** 0x71028754d0 은 `spl::WeaponBrush`(vt 0x7105650548 슬롯 15), 0x710288030c 는 `spl::WeaponManeuver`(vt 0x7105650f88 슬롯 15)다. 슈터는 `spl::WeaponShooter`(vt 0x7105652468, 75슬롯)다. 세 클래스는 모자(`spl::PlayerCustomHead`)와 같은 부품 기반 클래스를 공유한다. 슬롯 15 = 뼈 조회, 슬롯 49 = 행렬 갱신, 슬롯 70 = 애니 변형 문자열이다 [판독: vtable 비교].
  - 슈터 슬롯 15 0x710289bd80: 몸 모델 목록(+0x110→+0x40)에서 `Weapon_R` 를 찾아 +0x3b8 = (모델 번호 | 뼈 번호 << 16)으로 저장한다. 못 찾으면 0xffffffff 다 [판독].
  - **슈터 슬롯 49 0x710289beb8 (무기 부착식) [판독]+[실행]:** 몸 포인터(+0x110)가 있으면 몸 모델[+0x3b8 하위 16비트]의 뼈 get(vt+0x78, 뼈 번호 = +0x3ba)으로 3×4 행렬 B 를 받는다. 이를 그대로 무기 모델(+0x10)의 루트 행렬로 넣는다(0x7100f735b0). 그다음 0x7100f72b7c(1.0, 모델)로 모델을 갱신한다. 몸이 없으면 갱신만 한다. **오프셋·축 치환이 없다.** 즉 무기 `Root` = `Weapon_R` 뼈의 월드 변환(회전 포함)이며, §6.3 의 `full` 방식이 원본과 같다.
  - 0x7100f735b0(모델 루트 행렬 설정): B 를 행 우선 3×4(평행이동 = [3],[7],[11])로 읽는다. 열0·열1·열2 길이를 축 스케일로 모델 유닛(컴포넌트 1 vt+0xc8) +0x268/+0x26c/+0x270 에 쓰고 +0x280 |= 1 로 표시한다. 열0·열2 를 정규화하고(길이 0 이면 그대로), Y 축은 열2 × 열0 으로 다시 만든다. 회전 3×3 은 행 우선으로 모델 +0x298..+0x2b8, 평행이동은 +0x28c..+0x294 에 쓴 뒤 vt+0x1f8 로 꼬리 호출한다. 곱·뺄셈은 모두 분리 f32 다(FMA 없음, 0x7100f7374c~0x7100f737a0) [판독].
  - 검증: `PY web/tools/r5_gfx_char_attach_emu.py` → "weapon_attach". 원본 0x710289beb8 + 0x7100f735b0 을 실행했다. 단위·바인드 실측(Weapon_R 바인드 회전)·스케일 0·무작위 회전×스케일×평행이동 400개, 총 403건에서 모델 +0x28c..+0x2b8 과 유닛 +0x268..+0x270 이 판독식과 **403/403 비트 일치**했다. 뼈 get 호출의 (모델 객체, 뼈 번호)도 +0x3b8/+0x3ba 와 일치했다. 몸 포인터 없음 1건은 행렬을 바꾸지 않고 갱신만 불렀다. 스텁은 뼈 get(합성 행렬 공급), 무기 모델 vt+0x1f8, 0x7100f72b7c, 컴포넌트 vt+0xc8 이다. 실제 뼈 행렬 producer 와 무기 슬롯 49 의 호출 시점은 실행하지 않았다.
  - 슬롯 70 0x710289bffc: WeaponCategory/WeaponDetail 에 둘 다 `Shtr` 를 쓴다 → [anim_state_machine.md §3.1](anim_state_machine.md).
  - `Muzzle` 뼈: 무기 모델 안의 뼈라서 무기 루트를 따라간다(무기 쪽 코드가 따로 옮기지 않음) [판독: 슬롯 49 는 루트만 설정]. 머즐 이펙트는 ELink `Bone Muzzle` 로 이 뼈에 붙는다 [데이터: effect_sound.md §3]. 탄 생성 위치가 이 뼈를 쓰는지는 이 문서 범위 밖이다(weapon 문서).
- 탱크(하네스) — 0x71026f8f38(뼈 가시성 vt+0x90) [판독]: `show = !src+0x6ac`, `thin = src+0x6ad`, `type = src+0x6a8`(→ +0x18c0/+0x18c1/+0x182c, 쓰기 0x7102493d18). `Harness_{S,M,L}` = show && type == {0,1,2} && !thin, `Harness_{SF,MF,LF}` = show && type == {0,1,2} && thin, `Harness_Hide` = !show. 0x71026f5808 은 뼈 인덱스 조회만(S +0x1814, M +0x1818, L +0x181c, SF +0x1820, MF +0x1824, LF +0x1828, Hide +0x18bc). **이름 대응 정정(2026-10-03 r8) [판독]:** GearInfoClothes 파서 13b7ab4/13b9a84는 HarnessType→행+0x50, IsHideHarness→+0x78, IsThinHarness→+0x79다. 옷 파라미터 초기화 26da26c가 각각 객체+0x6A8/+0x6AC/+0x6AD로 직접 복사한다. 따라서 위 대응은 필드 이름 등록→파서→writer→기존 reader 연결로 확정한다. 2493d18은 별도 함수 시작이 아니라 249257c 내부 store다.
- **탱크 잉크 잔량 표시·잉크 부족 점멸(2026-10-03 r6, [r5 ui→gfx_char] 요청) [판독]+[데이터]:** 액터 `PlayerTank`(`spl::PlayerCustomTank`, vtable 0x7105642e48), 모델 `Tnk_Simple`, AS `PlayerTank.root.asb`.
  - ASB [데이터]: 커맨드 5개. `Gauge` = Simultaneous(스켈레탈 `Gauge` + 재질 `Gauge`) 슬롯 0, `InkShortage` 슬롯 1, `InkShortageGauge` 슬롯 2, `InkLock` 슬롯 3, `SubMarker` 슬롯 4. `Tnk_Simple` 클립 [데이터]: 스켈레탈 `Gauge` 100f·재질 `Gauge`(M_Glass `multi_normal_weight`) 100f, `InkLockGauge`(M_Body `tex_mtx1`) 100f, `InkShortage`(M_Glass `emission_intensity`·`tex_mtx1`) **45f 반복**, `InkShortageGauge.fmab`(M_Glass `tex_mtx1`) 100f, `SubMarkerGauge`(M_BombLine `tex_mtx0`) 100f. 반복은 `InkShortage` 하나다.
  - 초기화(슬롯 15 0x71026f6814, 일반 탱크 = 플래그 +0x539~+0x53f 모두 0): `Gauge`·`InkLock`·`SubMarker` 를 요청하고 재생 속도를 0 으로 둔다(엔트리 +0xd4 = 0). 이후 프레임은 코드가 직접 정한다.
  - 매 프레임(로컬 플레이어): 플레이어 갱신 0x7102483134 의 0x710248b300 이 0x71026fb6d0(탱크, s0 = 서브 잉크 비용 = 본체+0x678 vt+0x68 또는 0, s1 = 잉크 잔량 본체+0x698, s2 = 본체+0x69c, …)을 부른다. 원격 플레이어 경로(0x710248aa20~0x710248aa78)는 본체+0x698 = 본체+0x698 + (본체+0x6a0 − 본체+0x698)·0.1 로 먼저 보간한 뒤 같은 식을 쓴다.
    ```
    if 탱크+0x538: r = +0x520 = 잔량, +0x524 = s2, +0x538 = 0      # 첫 프레임
    k = (r < 잔량) ? 0.5 : 0.6                                   # 상수 0x71058c7118/0x71058c711c [실행: 정적 초기화 0x71026f5020]
    r = r + (잔량 − r)·k                                          # f32, fsub·fmul·fadd 분리
    Gauge 프레임 = (1 − r ≥ 0) ? (1 − r)·100 : 0                # 0x71026fa8a0 (가득 = 프레임 0)
    L = s2;  if L ≤ +0x524: L = max(max(L, 잔량), +0x524 − 0.1)   # 0x71058c7120 = 0.1
    +0x524 = L;  InkLock 프레임 = max(1.05 − L, 0)·100
    +0x528 = 서브 비용;  InkShortageGauge 프레임 = (1 − +0x528)·100
    SubMarker 프레임 = +0x534·100,  호출자가 함수 뒤에 +0x534 = 서브 비용 (한 프레임 늦은 값)
    ```
  - 잉크 부족 점멸: 슈터 잉크 부족 처리(0x71025823b0 안 0x7102585934)가 `탱크+0x4c0 = max(탱크+0x4c0, 60)` 을 쓴다(60 = 0x71058c7128). 같은 곳에서 본체+0x6ac = max(요청+0x60, 30) 도 쓰지만, 탱크 점멸은 +0x4c0 이 정한다. 탱크 슬롯 18 0x71026f8280 이 매 프레임 +0x4c0/+0x4c4 를 `max(x, 1) − 1` 로 줄인다. 0x71026fb6d0 은 +0x4c0 > 0(또는 서브용 +0x4c4 > 0)이 되는 순간 +0x52c/+0x52d 를 세우고, 타이머가 60 이상이면 xlink 이벤트 `TankEmpty`(탱크+0x18d0 vt+0x18)를 보낸다. 같은 조건에서 `InkShortage`(슬롯 1, 45f 반복 발광)와 `InkShortageGauge`(슬롯 2)를 요청하고, 타이머가 끝나면 슬롯 1 을 멈춘다(0x710399f41c). 즉 **마지막 잉크 부족 사격에서 60프레임 동안 `InkShortage` 재질 애니가 반복 재생**된다 [판독]. +0x52c/+0x52d 의 정확한 가장자리 조건 일부(인자 w4/w5)는 [미확정]이다.
  - 디컴파일 `analysis/decomp/r6_gfx_char/tank.c`, `tank2.c`.
- 신발: 액터 `Shs_*`에 `MirrorModel{Fmdb: 같은 모델}` 컴포넌트 → 모델은 왼발(`Leg_2_L, Ankle_Assist_L, Ankle_L, Toe_L`)만 있고 오른발은 미러 [데이터]. 구현 [판독]: 오른발 = 같은 Fmdb 의 두 번째 인스턴스(컴포넌트 +0x60, 미러 플래그 +0xa0; 왼발 +0x18/+0x58). 0x71026f09f4 가 신발 뼈 `*_L` → `*_R` 로 몸 뼈 쌍을 조회하고, 0x71026f1000 이 몸 `_R` 뼈 행렬을 복사한 뒤 0x7100f63364 로 3×4 행렬의 **회전부 9개 부호만 반전**(평행이동 유지, R·(−I)). Player00 바인드에서 R_R = −S·R_L(S = diag(−1,1,1))이 오차 0 으로 성립 → 결과는 정확한 X 미러이고 §6.3 의 mirrorX 결합식과 수학적으로 같다 [판독 + 데이터 계산]. 웹: `rightSkin = boneR_world · diag(−1,−1,−1) · invBindL`, 감김 방향 반전. `RightFmdb` 는 Shs 56개 팩 모두 없음 [데이터].
- 모자: `GearHeadParamSet`의 `ManualBindSRT[V<변형>_<머리>]`(Scale/Translate/Rotate)로 머리 모양마다 모자 위치를 보정하고, `HairArrange[V].PresetMap[<머리>]` → `HairArrangeParam.BoneParamArray[{BoneName(ScalerA..C, Knot_1...), Scale, Rotation, Transform, AnimReduceRt}]`로 모자 아래 머리카락 뼈를 조정 [데이터].
  - ManualBindSRT 적용 0x71026e4e80 [판독]: 키 `"V%d_%s"`(변형 번호, 머리카락 행 이름에서 앞 `Har_` 를 뺀 것), 행렬 = **T · Rz · Ry · Rx · S**(각도는 도, ×0.017453292), 모자 객체 +0x380 에 3×4 로 저장, 키가 없으면 단위행렬. SRT 구조체: Rotate +0x30, Scale +0x3c, Translate +0x48. 같은 함수의 switch(0..4)가 +0x3b0/+0x3b1 에 쓰는 값의 의미와, 이 행렬이 §6.3 모자 결합의 어느 단계에 곱해지는지는 [미확정].

  - **2026-10-03 추가 판독·실행:** 이전 문장의 결합 순서 미확정 중 모자 슬롯49의 실제 소비식은 [solo_graphics_audit.md §6](solo_graphics_audit.md)에 확정했다(259/259 비트 일치). 위 +0x3b0/+0x3b1 의미는 여전히 미확정.
  - **모자 행렬식(보완 문서에서 옮김, 2026-10-03) [실행]+[판독]+[데이터]:** 모자 슬롯 15 0x71026e5e00 이 몸에서 `Head` 뼈를 찾아 모자 +0x350/+0x352 에 모델·뼈 번호를 둔다. GearHeadParamSet 이 있으면 0x71026e4e80 으로 ManualBindSRT(+0x380)를 다시 만든다. 슬롯 49 0x71026e613c 는 입력 변환을 소유 모델에 넘긴 뒤(vt+0x1f8, 저장 순서 `[0,1,2,3,6,9,4,7,10,5,8,11]`, 소유 모델 +0x28c), 몸 `Head` 뼈 get(vt+0x78)으로 B 를 받는다. S = 모자+0x380 과 결합해 모자 모델(+0x3f0) +0x238 에 쓴다. 몸 포인터(+0x110)가 0 이면 이 계산을 건너뛴다.
    ```
    for r = 0..2:                      # B = 뼈 get 결과(행 우선 3×4), S = ManualBindSRT
      b = B[4r : 4r+4]
      for c = 0..3:
        p = f32(S[c] · b[2])
        p = fma32(S[4+c], b[0], p)     # SIMD FMLA = 융합
        p = fma32(S[8+c], b[1], p)
        O[4r+c] = f32(p + (c == 3 ? b[3] : 0))
    ```
    행렬로 쓰면 **O = [B·P | t_B] · [S | t_S]** 이고, P 는 열 치환(새 열0 = B 열2, 새 열1 = B 열0, 새 열2 = B 열1)이다. 근거: 0x71026e61d0~0x71026e61fc 가 B 각 행의 앞 세 값을 `[2,0,1]` 순서로 재배치하고, 0x71026e6214~0x71026e6260 이 `FMUL → FMLA → FMLA → FADD`, 0x71026e6280/6284 가 기록한다 [판독]. 실행 검증은 `PY web/tools/completion_head_matrix_emu.py` 259/259 비트 일치, 몸 포인터 없음 1/1 이다(곱·덧셈을 분리 f32 로 하면 254/259 건이 다름) [실행]. 스텁 범위는 [solo_graphics_audit.md](solo_graphics_audit.md) 검증 기록에 있다.
    - B 가 뼈의 **월드 행렬(행 우선 3×4)**이라는 것은 같은 뼈 get(vt+0x78) 결과를 무기 슬롯 49 가 그대로 무기 루트로 쓰는 것에서 판독했다(위 무기 항목, 403/403 실행) [판독].
    - 계산 뒤에는 pack/rope 보정(뼈 번호 −1 이면 생략), 모자 모델 객체 갱신, 모자 +0x348 개 인덱스 쌍의 행렬 복사가 이어진다. 모자 모델 +0x280 bit0 은 갱신 중에 세우고 끝에서 지운다 [실행]. +0x348/+0x3e4 의 게임 의미는 [미확정].
    - Player00 바인드에서 `Head` 월드 회전 × P = 단위행렬이다(오차 0) [데이터: `analysis/graphics/bind_compare.py` 의 `worlds('Player00')`]. 따라서 바인드 자세에서는 모자가 똑바로 서고, **머리가 회전하면 모자도 같이 회전한다.**
  - HairArrange: 0x71026e44a0 이 PresetMap 을 **모자 객체(`spl::PlayerCustomHead`, vt 0x7105641998 슬롯 8)** +0x360 맵(키 = 머리카락 id + 변형×10000, 변형 수 = 모자+0x3b8 ← GearInfo 행 +0x74)에 적재 [판독]. 정정: 이전 판의 "홀더+0x360" 은 모자 객체다. BoneParam 오프셋 BoneName +0x30, AnimReduceRt +0x38(기본 1.0), Rotation +0x3c, Scale +0x54, Transform +0x60. `ldr #0x360` 은 main 플레이어 영역에서 적재 함수 안(0x71026e4d0c)뿐이라 맵은 포인터(`add #0x360`: 0x71026e4728, 0x71026e5cfc)로 넘겨 읽는 것으로 보인다. 뼈 적용 후보 = 모자 vt 슬롯 49 **0x71026e613c**(+0x380/+0x390/+0x3a0 = ManualBindSRT 행렬을 읽는 유일한 함수 [판독: 적재 패턴 스캔]), 15 0x71026e5e00, 11 0x71026e5ccc 와 머리카락 vt 0x71056416f8 슬롯 48~51(0x71026e2bdc, 0x71026e3118, 0x71026e3728, 0x71026e382c). 디컴파일은 `analysis/decomp/gfx4/p_batch1.c` 에 받아 두었고 **읽지 않았다** — 적용식·ManualBindSRT 와의 결합 순서는 [미확정].

  - **2026-10-03 정정:** 위 후보 디컴파일을 읽었다. 26e613c는 ManualBindSRT 결합, 26e5ccc는 맵 소멸자다. 26e5cfc의 add+360은 적용 근거가 아니므로 HairArrange 실제 소비자는 계속 [미확정]. [solo_graphics_audit.md §8·11](solo_graphics_audit.md).
  - **r5 추가 조사(2026-10-03), 여전히 [미확정]:** 맵 구조를 판독했다. 0x71026e44a0 이 머리카락 행마다 `"Har_%s"` 이름으로 머리카락 id 를 찾고 키 = id + 변형×10000 을 만든다. 노드(0x38 B, vt 0x7105641c10)의 +0x20 = 키, +0x28 = HairArrangeParam 리소스(참조 수 +0x16c)이고, 삽입은 0x7101415864 다. 맵 머리는 +0x360(루트), +0x368(빈 노드 목록), +0x370(노드 풀), +0x378(개수), +0x37c(용량)이다 [판독].
    - 시도 1: 0x71026c0000~0x7102720000 에서 `ldr [x, #0x360/#0x368/#0x370/#0x378]` 와 `add #0x360` 를 전수 검색했다. 모자 객체에 대한 것은 적재(0x71026e44a0)와 소멸(0x71026e5ccc)뿐이다. 0x71026e2b68/0x71026e2b70 은 머리카락 객체 자신의 +0x358 행렬(NaN = 없음) 복사라 무관하다.
    - 시도 2: 키를 만드는 상수 10000(`mov #0x2710`)을 0x7102400000~0x7102800000 에서 찾았다. 플레이어 커스텀 쪽은 적재 함수(0x71026e4cac)뿐이다. 0x7102493a80 등은 기어 id % 10000 == 20 검사라 무관하다.
    - 다음에 볼 곳: (a) 맵 루트를 인자로 받는 sead 트리 조회 함수 — 0x7101415864 와 짝인 find 의 호출자, (b) HairArrangeParam 리소스 +0x158 이하(BoneParamArray) reader, (c) 머리카락 객체 +0x390 의 0x14 B 항목 배열(초기화 0x71026e2450 끝: 항목 = {s32 −1, 0, 0}, 첫 항목 +0xc = 1.0)의 writer.
  - **확정(2026-10-03 r6) — HairArrange 소비자와 적용식 [실행]+[판독]:** r5 의 검색 범위(0x71026c0000~0x7102720000) 밖, 모델 홀더 영역에 소비자가 있었다. main 전체에서 `mov #0x2710` 와 `ldr [x, #0x360]` 이 한 함수에 같이 있는 곳을 찾았다(`PY web/tools/r6_gfx_char_opscan.py movz:0x2710 ldr64:0x360 --all`). 결과는 0x71026e44a0(적재)·0x7101454544·0x7102483134·0x7100329528 이고, 0x7101454544 가 소비자다.
    - **정정:** 맵 키는 `머리카락 id × 10000 + 변형 번호`다. r5 의 "id + 변형×10000"은 순서를 바꿔 적은 것이다. 적재 0x71026e4cac 는 `(HairInfo 행 +0x10) × 10000 + w21` 이고, 소비 0x7101454600~0x710145460c 는 `머리카락+0x11c × 10000 + 모자+0x120` 이다. 머리카락 +0x11c 가 id 라는 근거는 0x71026e0f9c 가 +0x11c == 0x21 일 때만 전용 뼈 5개 가시성을 바꾸는 것이다.
    - 0x7101454544(홀더): 홀더 +0x210/+0x1f8 중 종류(+0x24) == 4 인 슬롯에서 모자 객체(+8)를, +0x110/+0xf8 에서 머리카락 객체(+8)를 고른다. 모자가 없으면 빈 리소스를 넘긴다. 모자가 있으면 모자 +0x360 트리를 키로 찾아 노드 +0x28(HairArrangeParam 리소스, 참조 수 +0x16c 증가)을 0x71026df354(머리카락, &리소스, 0)에 넘긴다 [판독].
    - 호출 시점: 플레이어 갱신 0x710243a4ec 의 0x710243a75c~0x710243a7cc 다. 홀더 +0x64(사람 계산) 일 때만 부른다. 플레이어+0x510→+0x70 컬링 레코드가 없으면 매 프레임 부르고, 있으면 `전역 0x7105827e20 +0xf0(프레임 카운터) % 레코드+0x28 == 레코드+0x2c` 인 프레임에만 부른다. 레코드 +0x28 은 `ClothCullingParam.CullFrame`, +0x2c 는 0x71012571f8 이 나눠 주는 순번이다(0x71012e9b28, [hair_cloth.md §5](hair_cloth.md)) [판독]. 다른 호출자 0x710230c548 도 있다(맥락 미독).
    - 0x71026df354(머리카락, &res, force): 머리카락 +0x350 의 현재 리소스와 BoneParamArray(+0x158)가 같고 force == 0 이면 아무것도 하지 않는다. **즉 매 프레임이 아니라 바뀔 때만 적용한다.** 다르면 0x71026df464 로 이전 적용을 되돌린다. 캐시 트리 +0x318 의 뼈마다 저장한 바인드(+0x48)를 vt+0x50 으로 다시 쓰고 애니 가중을 1.0 으로 둔다. 그다음 +0x350 = res 로 바꾸고 0x71026df700 으로 적용한다.
    - 0x71026df700(적용) — BoneParam 마다(부모 상속 사슬 +0x6c~+0x70 플래그 처리 후):
      ```
      bone = 머리카락 모델(+0x3a0) 뼈 이름(+0x30) 조회(vt+0x40)       # 없으면 건너뜀
      (B, S_bind) = 캐시(+0x318, 이름 키)에 있으면 그 값, 없으면 vt+0x68 로 바인드 로컬을 읽어 캐시에 넣음
      S' = S_bind ⊙ max3(Scale(+0x54,+0x58,+0x5c), 0.01)       # 각 성분이 0.01 이하면 0.01
      x,y,z = Rotation 라디안(+0x48,+0x4c,+0x50)                  # 데이터는 도(예 −5.0)
      N = Rz(z)·Ry(y)·Rx(x)                                        # 행: (cy·cz, sx·sy·cz − sz·cx, sx·sz + sy·(cx·cz)) …
      R' = B_rot · N                                                # 열마다 FMLA 융합(0x71026e0bec~0x71026e0c38)
      t' = t_bind + (Tx, Ty, Tz)   (Transform +0x60/+0x64/+0x68)
           단 머리카락 +0x338 && 이 뼈 == (+0x348 모델, vt+0xa0 결과 == +0x34a) 이면 t' = t_bind + (Ty, Tz, Tx)
      bone vt+0x50(R'|t', S')                                       # 뼈 로컬 변환
      애니 바인드가 있으면 그 뼈의 스켈레탈 애니 가중(+0xa4) = AnimReduceRt(+0x38)
      ```
    - 라디안 값: Rotation 필드 형식(0x7105571cc8 계열)의 적용 함수 0x710124ea4c 가 `도 × 0.017453292` 를 따로 저장한다 [판독]. 이 저장 위치가 BoneParam +0x48 이라는 것은 [추정: 오프셋 배치]이다.
    - 검증: `PY web/tools/r6_gfx_char_hairarrange_emu.py` → `analysis/completion/r6/gfx_char_hairarrange_emu.json`. 원본 0x71026df700·0x71026e12e4·0x71026e3a28·0x71038b6944·0x71026e0f9c 를 실행했다. BoneParam 1~4개 × 60건(회전 ±3.2 rad, 스케일 0/0.01/−1 경계 포함, +0x338 경로 20건)에서 vt+0x50 에 넘어간 3×4 행렬과 스케일이 판독식과 **60/60 f32 비트 일치**했다. 스텁은 뼈 vt+0x40/+0x68/+0x50/+0xa0(파이썬)과 PLT sinf/cosf(파이썬 math 를 f32 로 반올림, SDK libm 아님)다. 애니 가중 경로(액터+0x208)와 부모 상속 사슬은 실행하지 않았다.
    - 머리카락 +0x390 항목 배열은 HairArrange 와 관계없다. 이 경로에서 쓰지 않는다 [판독].
- 머리카락 천 물리 [데이터]: `Phive/Cloth/Har_*.bphcl` = "Phive" 헤더 + Havok TAG0(SDKV 20210100) `hclClothContainer`. Har 팩 54개 중 46개에 있고 `_F`/`_M` 이 같은 파일. 예 SQD000: 천 `Cloth_Hair_L/R`, `Cloth_Rear`, 입자 뼈 `Hair_1..4_L/R`, `Nape_1`; 충돌 캡슐 `Collidable_Head_Root_1`, `Collidable_Spine_3`; 제약 Standard/Bend/Stretch Link, LocalRange, Volume; gravity, SpringGravity0; `hclBoneSpaceSkinPOperator`. `ClothCullingParam.CullFrame 4`, ControllerSet ClothList `"Default"`, 클래스 `spl::PlayerCustomHair`. **상수 해독 완료 → [hair_cloth.md](hair_cloth.md)**: `collision_tag0.py` 실패 원인 = TBDY 멤버 flags 0x80 일 때 붙는 packed 정수 1개 미처리. 새 도구 `web/tools/gfx4p_bphcl.py` 로 덤프 [실행]. SQD000 `Cloth_Hair_R/L`: 입자 9(고정 2), 질량 0.714286, 반경 0.05, 마찰 0.5, 중력 (0,−9.81,0), 감쇠 0.001/s, subSteps 1·반복 1, 실행 순서 LocalRange→Transition→Standard→Bend×2→Stretch, LocalRange k 0.8 [데이터]. 샘플 `analysis/render/bphcl/Har_SQD000_F.bphcl`. 웹 대체: hair_cloth.md §4 의 PBD 근사 [추정 — 원본 동등성 미보장]. 46개 팩 전체 상수 표는 [hair_cloth.md §3.3](hair_cloth.md)(2026-10-03, [데이터]).
- 몸 가림: 기어 `AlphaMaskF/M` → `GearAlphaMask` 텍스처 `<이름>_Opa` [판독: 0x7102b8ca48]. 기어가 바뀔 때 0x71024950cc(0x710249257c 안)가 이전 마스크를 해제(0x7102b8cc08)하고 새 마스크를 조회해 홀더+0xe8 텍스처 컨테이너에 등록 [판독]. 재질 슬롯 바인딩은 [미확정] — 후보 ① 몸 재질 `_op0`(cTexOpacity, UV0) 교체(샘플러 이름으로 텍스처를 바꾸는 0x71011805b4/0x71011807c8 존재) [추정], ② 셰이더 심볼 cAlphaCutTexture(gsys_user5)는 몸 프로그램이 쓰지 않음.
  - 추가 판독(gfx4): 컨테이너 = 0x7102b8c868 이 만들어 홀더(컴포넌트 0x37)+0xe8 에 저장(0x7101456850). 0x7102b8ca48 은 전역 GearAlphaMask 레지스트리(*0x7105793a00, +0x60 트리 = 이름 해시 키, 0x7102b8d04c 가 아카이브 텍스처마다 0xe0 B 항목 적재)에서 `<이름>_Opa` 를 찾아, 풀(+0xb08, 개수 +0xb00/상한 +0xb18)에서 항목을 꺼내 +0xaf0 목록 앞에 잇고 +0x2b8 트리(키 = 해시 +0x20, 개수 +0x2c0, 잠금 +0x2e8)에 넣는다. 등록이 바뀌면 호출자 0x710249257c 가 홀더+0xf0 = 현재 프레임+1 로 표시한다 [판독]. 컨테이너 +0x2b8 을 읽는 다른 함수는 0x7102b8c668(호출자 0x7102b8c800)뿐이고 내용은 미독 [미확정]. 0x71011805b4 호출자 중 커스텀 파츠 쪽 0x71026da7e0 은 `M_body` 의 `_a0`(알베도) 교체라 마스크가 아니다 [판독: 문자열].

  - **2026-10-03 정정:** 2b8c668/800을 판독한 결과 둘은 소멸/메모리 해제다. 재질 샘플러 연결 후보에서 제외한다. 실제 GearAlphaMask 적용 슬롯은 계속 [미확정]. [solo_graphics_audit.md §8](solo_graphics_audit.md).
  - **r5 추가 판독(2026-10-03):** 컨테이너가 GPU 쪽으로 넘어가는 길을 찾았다. 슬롯 결합은 여전히 [미확정]이다.
    - 홀더 갱신 0x7101458400: 몸·오징어형·SuperHook 모델 재질을 갱신한 뒤, `홀더+0xf0 <= 현재 프레임(*0x71059a37c8 +0x4bc)` 이면 컨테이너(홀더+0xe8)를 전역 텍스처 컨테이너 관리자(GOT 0x7105791fd8 → 0x710580f6f8, 생성 0x71010410e0)의 대기 목록(+0x2d0, 잠금 +0x308, 개수 +0x2e0, 연결 오프셋 +0x2e4 = 0xae0)에 넣는다. 이미 있으면 다시 넣지 않는다. 그 뒤 홀더+0xf0 = −1 로 둔다 [판독].
    - 관리자 프레임 콜백 0x71010413f8: 환경 조건(0x71010f6f34(4/9/7) 등) 아래에서 대기 목록의 컨테이너마다 0x710103f434(컨테이너, 명령 버퍼로 보임 [추정])를 부르고 목록을 비운다 [판독].
    - 홀더 준비 확인 0x7101457a18 은 다른 모델이 모두 준비되면 0x710103f34c(컨테이너)가 참이어야 준비 완료로 본다 [판독].
    - 마스크 출처 [데이터]: GearInfoHead 는 AlphaMask 가 전부 비어 있다(57행). 옷(`Clt_00`, `Clt_02`, `Clt_00_big` 등), 신발(`Shs_00`~`Shs_05`), 하의(`Btm_00`~`Btm_07`, `Btm_00_M`)에만 있다. 텍스처 원본은 `Model/GearAlphaMask.bfres.zs` 다. 몸 재질 `M_Body` 의 `_op0` 텍스처 이름은 `M_Body_Opa` 다(마스크 이름과 다름) [데이터: Player00 변환 meta].
    - 다음에 볼 곳: 0x710103f434(대기 컨테이너 처리), 컨테이너 +0x2b8 트리를 이름 해시로 조회하는 함수의 호출자, 몸 재질 `_op0` 샘플러를 바꾸는 코드(0x71011805b4/0x71011807c8 호출자 중 플레이어 쪽).
  - **확정(2026-10-03 r6) — 재질 슬롯 = M_Body 의 재질 샘플러 `_o0`(셰이더 `_op0` = cTexOpacity) [판독]+[데이터]:**
    - 컨테이너 생성 0x7102b8c868 은 대상 재질 이름 `"M_Body"` 를 쓴다.
    - 0x710103f434(컨테이너, 명령 버퍼)는 컨테이너 +0x558/+0x55a 크기의 작업 텍스처 `work_tex0`/`work_tex1` 두 장을 만든다. 둘 다 +0x320 값으로 초기화한다(0x7101189410). 그다음 셰이더 프로그램(옵션 `ENABLE_SRT=0, FILTER_TYPE=4, IS_ARRAY=0`, 아카이브 `*0x71058161a0 +0x20[*0x71055641a8]`)으로 +0x2b8 트리의 마스크를 키 순서대로 하나씩 그린다. 이전 결과(첫 번은 컨테이너 +0x3e8 텍스처, +0x3e0 bit0 이면 전역 `*0x7105999230 +0x58`)와 마스크 항목 텍스처(항목 +0x70)를 함께 묶고, 두 작업 텍스처를 번갈아 쓴다. 마지막 결과를 `FUN_71011805b4(컨테이너+0x310 재질 목록, 개수 +0x318, "_o0", 컨테이너+0x5e0)` 로 재질 샘플러 `_o0` 에 넣는다. 함께 `**(+0x640) = 0`, `+0x670 = +0x580` 을 쓴다.
    - 따라서 r5 가 찾던 "+0x2b8 을 읽는 함수"는 0x710103f434 다.
    - 데이터: Player00 `M_Body` 의 samplerAssign 은 `_op0 → _o0`(재질 샘플러 `_o0` = 텍스처 `M_Body_Opa`)이다 [데이터: `analysis/r6_gfx_char/dump_Player00.json`]. 몸 셰이더의 `a = texture(cTexOpacity, uv0).x · in_attr2.w; a < ref 이면 discard`(위 항목)가 이 텍스처를 읽는다. 이로써 "연결 자체는 [추정]" 이던 부분이 [판독]이 되었다. 같은 `_o0` 를 쓰는 `M_Eyelids` 는 컨테이너 대상 이름이 `M_Body` 라 대상이 아니다 [판독: 이름].
    - **[미확정]으로 남은 것:** 마스크끼리·원본 `M_Body_Opa` 와 합치는 연산이다. 위 셰이더 `FILTER_TYPE 4` 의 실제 식이 필요하다. Hoian_Proc `SimpleFilter`(FILTER_TYPE 0~6,8,9)는 옵션 3개 조합이 아니라 다른 아카이브로 보인다. agl_resource sharcb 7개에서는 문자열 `ENABLE_SRT` 를 찾지 못했다. 다음: 0x71058161a0 에 아카이브를 등록하는 코드에서 파일 이름을 찾고, 그 프로그램을 역번역한다.
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

- **정정(2026-10-03):** 무기 `full` 은 원본 슬롯 49 와 같다 [실행: 403/403]. 모자 `translate` 는 원본과 다르다. 원본은 `모자 월드 = Head 월드 · P · ManualBindSRT` 다(§6.1, [실행]+[데이터]). 바인드 자세에서는 Head·P = I 라 `translate` 와 같아 보였을 뿐이다. 웹은 표의 Hed_* 행을 `bodyBone(Head) · P · SRT`(P 는 위 열 치환)로 바꿔야 한다.

무기 full / 모자 translate는 렌더로 고른 것입니다 [실행: 재구현 렌더]: `Shoot_Shtr`에서 full이면 총구가 앞을 향하고 손잡이가 손에 있음, translate면 총이 세워짐(`scene_assembled_clip_Shoot_Shtr_frame_0_attach_{full,translate}.png`). 모자는 translate면 머리에 씌워지고 full이면 얼굴 앞으로 돌아감(`scene_assembled_hat_1_hatattach_{translate,full}.png`). 원본 코드 경로는 [추정], ManualBindSRT 보정(행렬식은 §6.1)은 아직 넣지 않음.

### 6.4 갱신 순서 (웹)

```
매 프레임: mixer.update(dt) → body.updateMatrixWorld() → (파츠 뼈가 몸 뼈 객체를 직접 공유하므로 추가 동기화 없음)
            → 머리카락 고유 뼈(천 물리 대신 정지) → render
```
원본은 파츠별 뼈 인덱스 쌍으로 행렬을 복사하는 구조로 보입니다(쌍 조회만 판독) [추정]. 공유 방식과 결과가 같도록 위 inverse 식을 썼습니다.

### r8 귀 플래그·SRT 필드 정정 (2026-10-03)

기존 §6.1의switch0..4는 실제 `ManualBindSRT.HideEar`이며2는`HairInfo.IsLong`자동조건이다. `Ear_L/Ear_R` index writer144f9a0→consumer1454330의고정행렬·보조벡터(0.65,0.8,1)를확인하고새2048입력원본비트일치를확보했다 [실행]+[판독]. ManualBindSRT명명필드는+30 HideEar,+34 Rotation,+40 Scale,+4C Translate로정정한다. HairInfo fallback SRT구조와혼동한이유를 [ear_hiding.md](ear_hiding.md) §4~§11에기록했다. 기존모자행렬결합259건은 재계상하지않는다.

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
| ↳ 갱신(2026-10-03 r6) | ToSquid 쪽 `_Hlf` 시작 프레임 해소(§5.4: 요청 프레임 S 에 f0 = 40, `_Hlf` 는 S+3 한 프레임) [판독]. 숨김 필드 의미는 [미확정] |
| ~~천 물리 상수~~ | 해소: [hair_cloth.md](hair_cloth.md)(gfx4p_bphcl.py). 남은 것: 게임 쪽 스텝 dt·CullFrame 적용(머리카락 vt 슬롯 48~51), Havok 런타임 식, 다른 Har 상수 |
| ↳ 갱신(2026-10-03 r6) | 슬롯 48/50/51 판독: 48 = 공통 갱신 0x71026ed214 + `Har_SQD004` 의 `Back_1~4` 뼈 보정, 50 = 모델 행렬 설정, 51 = 공통 0x71026ee2f8 + 플래그. dt 는 없다. CullFrame 적용 레코드는 찾음([hair_cloth.md §5](hair_cloth.md)). 스텝 dt 는 [미확정] |
| HairArrange 적용 | 맵은 모자 객체+0x360(정정). 후보 함수 디컴파일 `analysis/decomp/gfx4/p_batch1.c`(모자 vt 슬롯 49 0x71026e613c 등) 미독 — 적용식·ManualBindSRT 결합 순서 [미확정] |
| ↳ 갱신(2026-10-03) | ManualBindSRT 결합식은 해소(§6.1 모자 행렬식, [실행]). HairArrange 맵 소비자는 [미확정] — 시도·다음 주소는 §6.1 r5 항목 |
| ↳ 해소(2026-10-03 r6) | HairArrange 소비자 0x7101454544 → 0x71026df354 → 0x71026df700, 키 = 머리카락 id × 10000 + 변형(정정), 바뀔 때만 뼈 로컬 S·R·T 적용과 애니 가중 = AnimReduceRt. [실행] 60/60 비트 일치(§6.1) |
| ~~신발 미러~~ | 해소: 회전부 부호 반전 = X 미러(§6.1) |
| ~~하네스 선택식~~ / GearAlphaMask 슬롯 | 하네스 해소(§6.1, 필드 이름 대응만 추정). GearAlphaMask: 컨테이너 등록 구조·몸 셰이더 알파 테스트식 판독(§6.1). 남은 것: +0x2b8 을 읽는 0x7102b8c668(호출자 0x7102b8c800) → 재질 샘플러 연결 |
| ↳ 갱신(2026-10-03) | 0x7102b8c668/800 은 소멸자(정정). 컨테이너 → 전역 관리자 대기 목록(0x7101458400) → 프레임 콜백 0x71010413f8 → 0x710103f434 경로 판독. 재질 슬롯 결합은 [미확정], 다음 주소 §6.1 |
| ↳ 해소(2026-10-03 r6) | 재질 슬롯 = `M_Body` 재질 샘플러 `_o0`(셰이더 `_op0` cTexOpacity), 0x710103f434 가 마스크를 작업 텍스처에 합쳐 넣음 [판독]+[데이터]. 마스크 합성 연산(셰이더 FILTER_TYPE 4)은 [미확정] |
| ~~무기 부착~~ | 해소(2026-10-03): 슈터 슬롯 49 = Weapon_R 월드 행렬을 무기 루트로(§6.1, [실행] 403/403) |
| ~~모자 결합 방식~~ | 해소(2026-10-03): Head 월드 · P · ManualBindSRT(§6.1, [실행]+[데이터]). 웹 `translate` 는 정정 대상(§6.3) |
| ~~눈 색 프레임~~ | 해소(2026-10-03): 프레임 = 번호, 0 <= 번호 < FrameCount 만 반영(§5.2, [실행] 88/88). 번호의 출처(세이브)는 [미확정] |
| ~~스프링 트리거·축~~ | 해소(2026-10-03): §5.4 정정 항목([실행] 14400/14400, 축은 [판독]) |
| 기본 장비 | [미확정]. v0 데이터에 초기 장비 표시 없음(HowToGet 은 Shop/Impossible/Other 뿐, FST 행은 `Hed_FST000` 만). 세이브 기록 0x7102a67b94(커스텀 +0x48~+0x80, 키는 해시)는 기록만 하고 기본값을 정하지 않는다. 다음: 세이브 구조 생성자(0x7102a67b94 의 param_1 타입)와 플레이어 만들기 씬(`PlayerMake`) 쪽 기본값 |
| ↳ 갱신(2026-10-03 r6) | 세이브 커스텀 구획 초기값(슬롯 2 0x7102a66e28) 판독: 기어·무기 −1, HairId·BottomId·Eyebrow·SkinColor·EyeColor 0, ModelType 0(§5.2 표). −1 이 어떤 장비로 풀리는지는 [미확정] |
| ~~`_Hlf` 용도~~, `_F/_M` 접미사 코드 | `_Hlf` 기존 해소(§3, §5.4). `_F/_M`은 2026-10-03 r8 [실행]+[판독] ([접미사 문서](part_suffix_runtime.md))로 해소 |
| ToSquid 쪽 `_Hlf` 시작 프레임 | [미확정]. §4.2 순서와 SM+0xf0 규칙만으로 계산하면 요청 프레임 S 에서 f0 = 40, S+3 에 70 이 되어 `_Hlf` 가 S+3 한 프레임, S+4 에 0x84 오징어로 넘어간다. 다만 ToSquid 요청 때 `max(f0, 30)` 을 쓰는 지점과 같은 프레임의 +10 순서를 명령으로 확인하지 못했다. 다음: 0x710243e7d0 의 0x82 요청 경로에서 SM+0xf0 쓰기 |
| ↳ 해소(2026-10-03 r6) | §5.4 확정 항목: max(f0, 30) 다음 같은 프레임 끝에서 +10 이 반드시 지남(제어 흐름 검사) [판독]. 요청 지연(SM+0x1d4) 경우는 계산에 넣지 않음 |
| 오징어 몸 절차 변형(2026-10-03 r6 추가) | 객체 플레이어+0x770·뼈 표·호출 순서 판독(§5.4). 동역학 식 0x710263b7d0/0x710263dacc 는 [미확정] — 디컴파일 `analysis/decomp/r6_gfx_char/squid_ctrl.c` |
| 탱크 잔량 표시·잉크 부족 점멸(2026-10-03 r6 추가) | 해소(§6.1): Gauge 프레임 = (1 − r)·100, r 은 0.5/0.6 지수 추종, 부족 시 60프레임 `InkShortage` 반복 [판독]+[데이터]. +0x52c/+0x52d 가장자리 조건 일부 [미확정] |


### r8 추가 검증과 한계 (2026-10-03)

`web/tools/r8_gfx_binder_order_emu.py`는 원본 2656ac8/2656870/2657260을 실행하여 타입 5×파트 5의 **25 경로**에서 기본 파일·모델과 SDK 바인더 입력 배열을 기록했다. 몸 5개 배열은 판독식과 모두 일치했다. 결과 `analysis/completion/r8/graphics_binder_order.json`. 스텁은 모델 factory 2657a4c, 리소스 로더 37b2b28와 RTTI true, 경로 formatter 0f44d60, 배열을 기록하는 SDK 진입 366f140, 초기화 guard다. SDK 배열 저장 366f280은 `analysis/decomp/r8_graphics/char_suffix_binder.c`에서 별도로 판독했다. BFRES 파싱·포즈 바인딩·로드 실패·최종 렌더를 실행한 것은 아니다. 최초 실행은 초기화 guard 외부 호출 PC 3e99ec0에서 UC_ERR_FETCH_UNMAPPED로 실패했고 guard를 명시적 스텁으로 둔 뒤 25 경로 실행에 성공했다.

하네스 이름 연결 근거는 기존 `analysis/decomp/graphics/model_teamcolor_1.c`의 13b7ab4 및 새 `analysis/decomp/r8_graphics/char_parts_loader.c`의 13b9a84, `char_body_params.c`의 26da26c다. 이름 연결을 새로 판독했으며 기존 뼈 가시성 실행 성과를 다시 계상하지 않았다. `_F/_M` 본문26fd010과 모델 타입 writer/caller 연결은 [접미사 전용 문서](part_suffix_runtime.md)에서 해소했다. Cloth·전체 포즈 합성은 계속 조사 중이다.


### 2026-10-03 웹 반영 r8 후속 — 기존 결론 보존

[현재 반영/검증](../port/character_graphics_r8.md), [재질 소비](character_material_r8.md), [표시 공급](character_display_r8.md)를 우선한다. 기존 '이번 작업은 분석만/구현하지 않음'은 해당 회차 기록이다. r8은 실제 네 캐릭터 재질, RGBA 강도, B7a0 지연 숨김/SM/holder, Shtr/Shtr를 웹에 연결했고 전체304/304·typecheck/build·Lby12단계를 검증했다. live 재질/전체 pose·원본 GPU/Phive 동등성을 완료로 승격하지 않는다.


## 재질·눈 패턴·총구 그래픽 r9 — 2026-10-03

[현재 반영·검증·다음 지시](../port/graphics_priority_r9.md): 탱크/하네스/병의 native 재질·owner texture, raw type11 눈 채널, [Maya0/rotation0 UV6lane](character_texsrt_r9.md), [실제 Muzzle 시각 행렬 및 내적 정정](../effect_sound/muzzle_attachment_r9.md)을 웹과 MD에 반영했다. FMAA 원본1,212/피부 홀더67/SRT313/내적 격리블록2,048, 선택 GLSL↔웹GPU448건은 각각 범위가 다른 검증이며 원본 NVN/전체프레임 일치가 아니다.

고정 원본556/986=56.39%·그래픽102/204=50.00%, port13/62=20.97%(일부37/차이9/원본미확정3)·GR0/10/일부7/10 유지. 신규 부분 근거를 기존 복합 질문 전체 확정으로 승격하지 않았다. 몸CP/skin idx·weighted type11/type18·다른 SRT mode/rotation·cube/BRDF/SPP·잠영 파문/Custom1/VAT·native 최종픽셀은 남는다. 최종 테스트·브라우저·보호 SHA와 실패는 r9 요약의 실행 기록을 따른다.
