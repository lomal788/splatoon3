# 그래픽·모델·캐릭터 — 목차와 요약

Splatoon 3 v0의 모델(FRES v10)·텍스처(BNTX)·재질·팀 컬러·플레이어 캐릭터 조립·스켈레톤/애니메이션을 웹(three.js glTF)으로 옮기기 위한 명세입니다. 확정 수준 표기는 [README](../README.md)를 따릅니다. 작업 지침은 [../../분석.txt](../../분석.txt).

| 하위 문서 | 내용 |
|---|---|
| [formats_bfres_bntx.md](formats_bfres_bntx.md) | FRES v10·BNTX 4.1 구조, 변환 도구, glTF 변환 규칙, Hoian_UBER 재질 슬롯·옵션·renderInfo, 샘플 변환 결과 |
| [team_color.md](team_color.md) | 팀 컬러 계산 전체(데이터 → 4세트 → 14색 → 재질 파라미터), 공식·상수·주소, 재구현 코드와 기대값 |
| [player_assembly.md](player_assembly.md) | 플레이어 모델 선택(잉클링/옥토링·성별), 머리카락·눈썹·기어·하의·탱크·무기 결합 규칙, 인간/오징어 모델과 애니메이션, 웹 조립 알고리즘 |
| [shaders.md](shaders.md) | BFSHA/SHARCB/BNSH 해독: Hoian_UBER 슬롯·옵션 기본값·Mat 블록·재질별 프로그램·팀색 혼합식·UV 선택, 도색 GPU 스탬프, UI MeterAction |

## 1. 기능 개요 (사용자에게 보이는 것)

- 플레이어는 몸(Player00~03) + 머리카락 + 눈썹 + 하의 + 옷 + 신발 + 모자 + 잉크 탱크 + 무기를 따로 가진 모델을 한 스켈레톤에 붙여 그립니다. 오징어/문어 형태는 별도 모델(Player_Squid/Player_Octopus)입니다.
- 머리카락·눈썹·잉크 탱크·무기의 잉크 부분·오징어 몸은 팀 색으로 칠해집니다. 팀 색은 데이터(TeamColorDataSet)의 한 색에서 런타임에 14가지 변형 색을 계산해 재질 파라미터로 넣습니다.
- 눈 색·피부 색·눈 깜빡임·입 모양은 재질/가시성 애니메이션의 프레임으로 고릅니다.

## 2. 분석 대상과 자료

| 자료 | 위치 |
|---|---|
| 모델 | `extracted/romfs/Model/*.bfres.zs` 1,283개 (FRES v10, 텍스처 내장) |
| 셰이더 | `extracted/romfs/Shader/Hoian_UBER.Product.100.product.Nin_NX_NVN.bfsha.zs` — 컨테이너 해독·재질별 프로그램 GLSL 역번역 [shaders.md](shaders.md), 산출물 `analysis/shader/` |
| 표 | `RSDB/{TeamColorDataSet,TeamColorOffset,HairInfo,EyebrowInfo,GearInfoHead,GearInfoClothes,GearInfoShoes,BottomInfo,TankInfo,LODThreshold,InkTexInfo}` → JSON 사본 `analysis/graphics/rsdb/` |
| 싱글턴 | `Pack/SingletonParam.pack.zs`: `game__gfx__parameter__TeamColorHueDirPeak`, `game__gfx__InkColorCorrection` |
| 액터 | `Pack/Actor/SplPlayer.pack.zs`(PlayerFullModel, AS/*.asb), `Har_*/Eyb_*/Btm_*/Clt_*/Hed_*/Shs_*`, `PlayerTank*`, `WmnG_*` |
| 코드 | main NSO(심볼 없음). 디컴파일 `analysis/decomp/graphics/model_teamcolor_{1,2,3}.c` |
| 변환 산출물 | `analysis/graphics/web/<모델>/` (glb + tex/*.png + meta), 렌더 `analysis/graphics/shots/`, 로드 검증 `analysis/graphics/verify/` |

## 3. 전체 흐름 (원본)

```
[로딩]  PlayerModelType(SquidF/SquidM/OctopusF/OctopusM/Rival) × 파츠
          → 0x7102656ac8 : "Model/%s.bfres" 파일·모델 이름·추가 애니 소스 결정          [판독]
        Hair/Eyebrow/Bottom/Gear 행 이름 → Model/<행>[ _F|_M ].bfres                   [데이터]
[결합]  파츠 뼈 ↔ 몸 뼈 이름 쌍 조회(Head_Root↔Head 등) 0x71026ddd58/0x71026e2450       [판독]
        무기: 몸 모델의 "Weapon_R"/"Weapon_L" 뼈 인덱스 0x71028754d0/0x710288030c          [판독]
[팀색]  TeamColorDataSet → 0x7101176830 → 4세트 × 14색(0x71011743a0/0x7101174534)       [판독]
        재질 방문 0x7101104258 / 0x71011045e0 → 0x7101103490 가 Hoian_UBER 재질에 씀      [판독]
[매 프레임] 스켈레탈 애니(ASB 상태머신이 이름 선택) → 몸 뼈 → 파츠 뼈 동기화 → 그리기   [추정: 순서]
```

### 3.1 어느 TeamColorDataSet 행을 쓰는가 — 로비·사격장 (2026-10-03 r6) [판독]+[실행]

- 팀색 관리자(*0x7105818920) 초기화 0x71011776a0 가 RSDB `TeamColorDataSet`(표 5번) 행 이름 → 번호 트리(+0xb80, 키 = 이름의 CRC16 표 해시 0x7101179f90, 표 0x7104a98728)를 만든다. 그다음 0x7101179448 로 선택 상태(+0x928)를 초기화한다. 초기 행은 `0x7101179c80(표, 열 0xc, 값 0)` 이다. 열 0xc 는 `Tag` 이고(열 0 = 행 이름, 리플렉션 필드 순서로 12번째, 행 구조 +0x88), 값 0 은 `VersusRegular` 다. 이 함수는 조건에 맞는 행 수 n 을 세고, 전역 sead::Random(*0x7105997950, xorshift128)의 다음 u32 r 로 `(r · n) >> 32` 번째 행을 고른다. 없으면 `YellowPurple` 이다. 이 행의 해시를 +0x934 에 두고 0x7101176830(+0x2b8, 행, swap = +0x936)으로 4세트를 만든다.
- 씬마다(gfx 씬 준비 0x7102ba9730 → 0x7101178030): 게임 데이터 플래그로 분류를 정한다. 분류는 `Scene_Versus` → 0, `Scene_Coop` → 1, `Scene_Mission` → 2, 없음 → 3 이다(0x71011795b0; 플래그 이름은 정적 초기화 0x7102b582d0 가 넣는 문자열 [실행: player_initemu]). 선택기 번호는 0x7101179a24(분류, 씬 이름)가 정한다(+0x128 이면 8). 대전 로비 씬 `LobbyVersus` 는 분류 3 에서 이름이 `PlayerMake`/`Plaza`/`LobbyCoop`/`LobbyLocal`/`DayChange`/`Boot` 어디에도 맞지 않으므로 **선택기 0**(전역 0x71058e87dc 가 참이면 5)이다.
- 선택기 0(0x7101179fd0): 현재 행의 Tag 가 0(VersusRegular) 또는 1(VersusOption)이면 그대로 둔다. 아니면 위와 같은 무작위 VersusRegular 행으로 바꾸고 swap = 0 으로 둔다. 선택기 5(0x710117aec0)는 씬 실행 정보의 `TeamColorSet` 문자열 행이고, 6(`PlayerMake`)은 `WarmingUpYellowBlue`, 7(`Plaza`)은 `YellowBlue` 고정이다.
- **swap(+0x936)은 항상 0**이다. 쓰는 곳은 생성자 0x7101177314(0)와 선택기들의 `+0xe = 0` 뿐이다 [판독: strb 스캔 + 선택기 디컴파일]. 따라서 세트 0 = Alpha 색, 세트 1 = Bravo 색이다.
- 결론: 사격장 몸 잉크 색 행은 **부팅 때 VersusRegular 10행(BlueYellow, GreenPurple, LimegreenPurple, OrangeBlue, OrangePurple, PinkGreen, TurquoisePink, TurquoiseRed, YellowBlue, YellowPurple) 중 균등 무작위 1개**다. 직전 대전 색이 VersusRegular/VersusOption 이면 그 색이 로비에 남는다. 웹의 OrangeBlue 고정은 가능한 값 중 하나일 뿐이다. 플레이어가 어느 세트(팀)를 쓰는지는 이 절 범위 밖이다(플레이어 팀 번호).
- 검증: `PY web/tools/r6_gfx_char_teamcolor_emu.py` → `analysis/completion/r6/gfx_char_teamcolor_emu.json`. 원본 0x7101179a24 를 분류 4 × 씬 이름 9 × 플래그 조합 32 = **1152/1152**, 해시 0x7101179f90 **5/5**, 선택기 0 0x7101179fd0 을 현재 행 4 × Tag(없음, 0~9) × 무작위 결과 3 = **132/132** 로 판독식과 비교했다. 스텁: 선택기 0 에서 RSDB 조회 0x710140946c(합성 행)와 0x7101179c80(호출 인자 기록, 합성 이름)을 대신했다. 0x71011795b0(게임 데이터 플래그)과 0x7101179c80 의 행 순회·난수 식은 실행하지 않았다(식은 [판독]).

## 4. 확정한 핵심 사실 (요약, 근거는 하위 문서)

| 사실 | 수준 |
|---|---|
| FRES는 v10(`+8 u32 0x000a0000`). BfresLibrary(소스 복사본)로 샘플 14개 전부 오류 없이 읽힘. 회전 EulerXYZ = Rz·Ry·Rx, 파일 역바인드 행렬과 오차 ≤5e-7 | [실행] |
| 텍스처는 bfres 안 ExternalFiles `textures.bntx`(BNTX 4.1). 자체 파이썬 디코더로 샘플 11개 모델 212장 모두 PNG 변환(실패 0) | [실행] |
| 샘플 재질 36개 전부 셰이더 `Hoian_UBER/hoian_uber`. 슬롯 `_a0`=Alb, `_n0`=Nrm, `_r0`=Rgh, `_m0`=Mtl, `_ao0`=Ao, `_e0`=Emm, `_op0`=Opa, `_su0`=Tcl(팀 색 치환 마스크, 셰이더 심볼 cTexSubstitution), `_cp0`=2cl(cTexCompPaint), `_t0`=Trm(투과). 36재질 모두 Product bfsha 의 프로그램 번호까지 확정 | [데이터] ([shaders.md §3](shaders.md)) |
| 팀색 혼합: `team_color_map_type` 2 → `mix(albedo, my_team_color, clamp(Tcl.r + team_color_blend_alpha))`, 3 → `mix(albedo_color, my_team_color, clamp(team_color_blend))`. UV: `texcoord_select = 2` → `_u2` + `tex_mtx1` | [판독: 셰이더 역번역] |
| 팀색 14종 이름·순서와 계산식(HSV 오프셋, HueDirPeak 반전, Model 보정) | [판독] |
| 재질에 쓰는 팀색 파라미터와 인덱스 대응(my_team_color=Model 등) | [판독] |
| 모델 타입 → Player00(SquidF)/01(SquidM)/02(OctopusF, Rival)/03(OctopusM). 01~03은 Player00(03은 Player01도) 애니를 함께 로드. 87뼈 순서 동일 | [판독]+[데이터] |
| 파츠 뼈는 몸 뼈 이름을 그대로 쓰고 파츠 모델 공간 = 몸 공간 − 부착 뼈 바인드 위치. 머리카락·눈썹 루트 `Head_Root`↔`Head` | [데이터]+[판독: 이름 쌍] |
| 무기 `Root`는 `Weapon_R`의 전체 변환(회전 포함)을 따르고, 모자 `Root`는 머리 위치만 평행이동한 공간 | [실행: 재구현 렌더로 판별] — 원본 코드 경로는 [추정] |
| 정정(2026-10-03): 무기 `Root` = `Weapon_R` 월드 행렬(슈터 슬롯 49 0x710289beb8 → 0x7100f735b0). 모자 = `Head` 월드 · P(열 치환 [2,0,1]) · ManualBindSRT 이며, 바인드에서 Head·P = I 라 평행이동처럼 보였을 뿐 머리 회전을 따른다 | 무기 [실행] 403/403, 모자 [실행] 259/259 + [데이터] — [player_assembly.md §6.1](player_assembly.md) |
| 클립 이름 해석: 무기 변형(Detail → Category) → 이모트 → `Win01` → 대체 사슬 6개 → 원래 이름. 모두 없으면 그 잎은 재생 엔트리 없음. 슈터는 Category = Detail = `Shtr` | [실행] 2210/2210 — [anim_state_machine.md §3.1](anim_state_machine.md) |
| ASB 선택 노드: BoolSelector 참 → 자식 0, IntSelector 앞 n−1 case 비교·없으면 마지막 자식 | [실행] 130/130 — [anim_state_machine.md §2.5](anim_state_machine.md) |
| 눈 색 = `Color_Eye` 프레임 번호(0 <= 번호 < FrameCount 만 반영, `M_Eye_Alb.21` 은 닿지 않음) | [실행] 88/88 + [데이터] — [player_assembly.md §5.2](player_assembly.md) |
| 몸 표시 스프링: "몸만 보임" 0→1 이고 직전 프레임에 무엇이든 보였을 때 발동, X·Z 1 + 1.5x / Y 1 + x | [실행] 14400/14400, 축 [판독] — [player_assembly.md §5.4](player_assembly.md) |
| 신발은 왼발 모델 1개를 미러해 오른발에 씀(`MirrorModel` 컴포넌트, 몸 `_R` 뼈 행렬의 회전부 부호 반전) | [데이터]+[판독: 0x71026f1000] |
| 로비 팀색 행 = 부팅 때 VersusRegular 10행 중 sead::Random 균등 선택(로비는 선택기 0 이 유지), swap 항상 0 | [실행] 1152/1152·132/132 + [판독] — §3.1 |
| HairArrange = 머리카락 id × 10000 + 변형 키로 모자 맵 조회, 바뀔 때만 뼈 로컬 S·R·T 와 애니 가중(AnimReduceRt) 적용 | [실행] 60/60 — [player_assembly.md §6.1](player_assembly.md) |
| GearAlphaMask 결과는 `M_Body` 재질 샘플러 `_o0`(셰이더 `_op0` cTexOpacity)로 들어감 | [판독]+[데이터] — [player_assembly.md §6.1](player_assembly.md) |
| 탱크 잔량 Gauge 프레임 = (1 − r)·100, r 은 0.5/0.6 추종, 잉크 부족 60프레임 `InkShortage` 반복 | [판독]+[데이터] — [player_assembly.md §6.1](player_assembly.md) |
| ToSquid `_Hlf` = 요청 뒤 4번째 프레임(S+3) 한 프레임, JumpVarID = 점프마다 1·2 교대 | [판독] — player_assembly §5.4, anim §4.6 |

## 5. 웹 구현 구성요소 (웹 권장 이름 — 원본 이름 아님)

| 모듈 | 책임 | 상세 |
|---|---|---|
| `AssetPipeline`(빌드 시) | bfres.zs → glb + png, 결합 텍스처(mr/ba) 생성, meta | [formats_bfres_bntx.md §6](formats_bfres_bntx.md) |
| `ModelLoader` | glb 로드, 메시·뼈·클립·재질 extras 노출 | three `GLTFLoader` |
| `HoianMaterial` | glTF PBR 근사 + 팀색 혼합·UV 선택은 원본 식(셰이더 청크) | [formats §5](formats_bfres_bntx.md), [team_color.md §7.3](team_color.md), [shaders.md §3.8](shaders.md) |
| `TeamColorService` | TeamColorDataSet 행 → 4세트×14색, 재질 파라미터 | [team_color.md](team_color.md), 코드 `web/tools/graphics_verify/teamcolor.mjs` |
| `PlayerModelAssembler` | 모델 타입·장비로 파일 선택, 파츠 뼈 바인딩(몸 뼈 공유), 미러 신발, 하네스 가시성 | [player_assembly.md §6](player_assembly.md) |
| `PlayerAnimator` | ASB 평가(노드 종류·FloatBlend·FrameController), 프레임 전진(end = FrameCount), 전환 블렌드(ease-in-out 2차), 블랙보드 공급 | [anim_state_machine.md §2.5, §4](anim_state_machine.md) |
| `PlayerModelVisibility` | 몸 / `_Hlf`(변신 과도기 29프레임) / 오징어 / 잉크레일 중 그릴 모델 선택, 같은 프레임 한 모델 | [player_assembly.md §5.4](player_assembly.md) |

구현 순서: ① 파이프라인으로 몸·파츠·무기 glb 생성 → ② 몸만 로드·클립 재생 → ③ 파츠 결합(검증 페이지와 같은 알고리즘) → ④ 팀색 계산·재질 적용 → ⑤ 오징어 모델·전환 → ⑥ 눈/피부/입 재질·가시성 애니.

## 6. 수행한 검증 (요약)

| 검증 | 방법 | 결과 | 구분 |
|---|---|---|---|
| FRES v10 판독 | BfresLibrary 덤프 14개 | 오류 0 | 실행(라이브러리) |
| 회전 규약 | 계산 바인드 × 파일 역바인드 | 최대 오차 4.9e-7 (Player00) | 실행 |
| glb 구조 | three GLTFLoader(node) 10개 모델 | 메시·정점·삼각형 수 meta와 일치, 바인드 스킨 오차 ≤2.2e-7, 클립 길이 일치, 오류 0 | 재구현 로드 |
| 조립·애니 | 헤드리스 chromium 렌더 15장 | 머리카락·눈썹·옷·하의·양쪽 신발·탱크·무기·모자 정상 위치, Wait/Run/Shoot_Shtr/WaitHold_Shtr 포즈에서 손에 무기 | 재구현 렌더(원본 화면과 직접 비교는 안 함) |
| 팀색 | JS 재구현으로 OrangeBlue 4세트×14색 + 경계 4종 | 값 표 [team_color.md §8](team_color.md) | 재구현 계산(원본 실행 대조 없음) |

원본 실행 대조는 하지 않았습니다(에뮬레이터 없음).

- **정정(2026-10-03):** 이후 unicorn 원본 실행 대조를 했다. 모자 행렬 259/259, 무기 부착 403/403, 클립 이름 해석 2210/2210, 선택 노드 130/130, 눈 색 88/88, 몸 스프링 14400/14400 이다. 명령과 스텁 범위는 [solo_graphics_audit.md](solo_graphics_audit.md) 검증 기록에 있다. 렌더 결과는 원본 셰이더가 아니라 근사입니다. 셰이더 역번역([shaders.md](shaders.md))으로 팀색 혼합식·UV 선택은 원본 식을 얻었지만, 검증 페이지(`graphics_verify/view.html`)에는 아직 반영하지 않았습니다.

## 7. 남은 미확정 (요약)

- (해소) Hoian_UBER 옵션 기본값·슬롯 의미·팀색 혼합식·UV 선택 — [shaders.md](shaders.md). 남은 것: 조명 블록(Context/Env/BlitzUBO0..2) 레이아웃, `blitz_calc_color` ID 전체 의미, `_MAi`/`_Fxm` 채널별 쓰임.
- (해소) 팀색 Ink(9)/InkBright(10): 입력 = 활성 env DirectionalLight(DiffuseColor·Intensity) + 하늘 SH, SSS 기본 0.1/0.5 — [team_color.md §5.3](team_color.md). 값은 스테이지 조명 의존, MainLight 경로는 [추정].

- **2026-10-03 정정:** 위 MainLight 경로 [추정]은 기존 stage_rendering §4의 직접 기록 [판독]으로 해소됐다. 값 경로와 하늘 SH runtime 미확정은 구분한다. [solo_graphics_audit.md §8](solo_graphics_audit.md).
- (해소) BlitzUBO0 레이아웃(팀 세트 Ink/InkBright 등)·`blitz_calc_color` ID 대부분 — [shaders.md §3.9, §3.6.4](shaders.md). 남은 것: BlitzUBO1/2·Context·Env 블록.
- (대부분 해소) ASB: 노드 종류 10/12/19 = Event/FrameController/InitialFrame, 끝 프레임 = FSKA FrameCount, 블렌드 곡선, 블랙보드 공급 — [anim_state_machine.md](anim_state_machine.md). 남은 것: Event 발화 구간, 다층 포즈 합성, 일부 블랙보드 출처.
- (대부분 해소) 머리카락 천 물리 상수(입자·질량·중력·감쇠·링크 강성·실행 순서) — [hair_cloth.md](hair_cloth.md), 도구 `gfx4p_bphcl.py`. 남은 것: 게임 쪽 스텝 dt·컬링. 모자 ManualBindSRT 행렬식 해소, HairArrange(맵 = 모자 객체+0x360으로 정정) 뼈 적용식 미확정 — [player_assembly.md §6.1](player_assembly.md).
- (해소) 신발 미러(회전부 부호 반전 = X 미러), 하네스 선택식. GearAlphaMask: 컨테이너 등록 구조·몸 셰이더 알파 테스트식 판독, 재질 슬롯 연결(0x7102b8c668) 미확정.
- LOD: 임계 표 선택·기록 판독, 필드 순서 정정(기록 = [Start, 2Start−End, 1/(End−Start)]) — [formats_bfres_bntx.md §7.1](formats_bfres_bntx.md). 거리 계산 소비처 미확정.
- (해소) 화면 모델 선택(사람/`_Hlf`/오징어/잉크레일)과 전환 프레임 — [player_assembly.md §5.4](player_assembly.md).
- (2026-10-03 해소) 무기 부착식, 모자 결합식(Head · P · ManualBindSRT), 클립 이름 대체 규칙, 눈 색 프레임 규칙, 스프링 트리거·축, 머리카락 천 46팩 상수표 — 위 §4 표와 각 하위 문서.
- (2026-10-03 미확정 유지) HairArrange 맵 소비자, GearAlphaMask 재질 슬롯 결합, LOD 레코드 reader, 기본 장비 결정 지점, 엔트리 없는 애니 잎의 포즈 기여, ToSquid 쪽 `_Hlf` 시작 프레임. 시도와 다음 주소는 [player_assembly.md §6.1·§8](player_assembly.md), [anim_state_machine.md §6](anim_state_machine.md), [solo_graphics_audit.md §11](solo_graphics_audit.md).
- (2026-10-03 r6) 해소: HairArrange 소비자·적용식([실행]), GearAlphaMask 재질 슬롯, 로비 팀색 행·swap([실행]), ToSquid `_Hlf` 시작 프레임, JumpVarID, 탱크 표시식. 남은 것: 마스크 합성 셰이더 식, LOD 레코드 reader, 천 스텝 dt, 기본 장비의 −1 해석, 엔트리 없는 잎의 포즈 기여, 오징어 몸 절차 변형 식 — 각 하위 문서 미확정 표.

각 항목의 근거와 필요한 추가 자료는 하위 문서 §미확정에 있습니다.

## 8. 도구·산출물

| 경로 | 내용 |
|---|---|
| `web/tools/graphics_bfres2gltf/` | C# 변환기(mpj 복사본 + Hoian 재질 분기 `BuildMaterialHoian`, `--clip`). BfresLibrary 소스 복사본 `oss/`. 빌드 결과 `analysis/graphics/build/bin/Release/net7.0/graphics_bfres2gltf.exe` |
| `web/tools/graphics_bntx.py` | BNTX 디코더(mpj 복사본 + .zs/.bfres 내장 BNTX 읽기, `_Nrm` 노멀 Z 재구성) |
| `web/tools/graphics_convert.py` | 모델 이름 하나 → raw bfres, tex png, glb, 결합 텍스처 |
| `web/tools/graphics_blcallers.py` | BL/B 호출자 검색 |
| `web/tools/graphics_verify/` | `teamcolor.mjs`(팀색 재구현), `teamcolor_test.mjs`, `check.mjs`(three 로드 검증), `view.html`+`shot.mjs`(헤드리스 조립 렌더). three·playwright-core·chromium은 `c:/dev/mpj/web/node_modules`·`%LOCALAPPDATA%/ms-playwright` 것을 읽기 전용으로 사용 |
| `analysis/graphics/scan_packs.py`, `bind_compare.py` | 액터 팩 문자열 검색, 파츠/몸 바인드 비교 |
| `web/tools/graphics_verify/teamcolor_ink_test.mjs` | Ink/InkBright 조명 민감도 표(→ `analysis/render/teamcolor_ink_*.json`) |
| `web/tools/graphics_bntx_fmtscan.py` | BNTX 형식별 텍스처 찾기 + imageSize 로 텍셀당 바이트 역산 |
| `web/tools/render_aamp.py` | AAMP(.baglenv 등, CRC32 이름) 덤프 — env DirectionalLight 값 |
| `web/tools/render_asnode_vt.py` | AS 노드 종류 1~25 vtable 슬롯 표 |
| `web/tools/render_ubo_layout.py`, `render_storescan.py`, `render_bytescan.py` | 멤버 선언식 UBO 레이아웃 원본 실행 추출, 오프셋 저장/적재 패턴 스캔, ldrb/strb 오프셋 스캔 |
| `analysis/decomp/render/`, `analysis/render/` | 3차 [render] 디컴파일·산출물(BlitzUBO0 표, calc_color ID 표, ASB 사본, env 덤프, bphcl 샘플) |
| `web/tools/r5_gfx_char_uc.py` | r5 하네스 공용(network_uc + PLT memcpy/memcmp/strlen/sqrtf 처리, 그 밖 PLT 는 0 반환 스텁으로 기록) |
| `web/tools/r5_gfx_char_clipname_emu.py`, `r5_gfx_char_attach_emu.py`, `r5_gfx_char_eye_emu.py` | 원본 실행 하네스(클립 이름 해석·무기 부착·스프링·눈 색). 결과 `analysis/completion/r5/gfx_char_*_emu.json` |
| `web/tools/r5_gfx_char_bphcl_batch.py` | Har 팩 전체 bphcl 천 상수 요약 → `analysis/completion/r5/gfx_char_bphcl_all.json` |
| `web/tools/r6_gfx_char_teamcolor_emu.py`, `r6_gfx_char_hairarrange_emu.py` | r6 원본 실행 하네스(팀색 선택기·HairArrange 적용). 결과 `analysis/completion/r6/gfx_char_*_emu.json` |
| `web/tools/r6_gfx_char_opscan.py`, `r6_gfx_char_lodscan.py`, `r6_gfx_char_cfgpath.py` | 명령 패턴 전수 검색(함수별), LOD 레코드 reader 후보 검색, 함수 안 경로·쓰기 검사 |
| `analysis/decomp/r6_gfx_char/` | r6 디컴파일(팀색 선택기, 텍스처 관리자 0x710103f434, AS 노드, HairArrange, 오징어 절차 변형, 탱크, 세이브 기본값) |
| `analysis/decomp/r5_gfx_char/` | r5 디컴파일(바인더·해석기, 무기 부착, 눈·피부 색, 세이브 커스텀, 홀더 +0xe8/+0xf0, 텍스처 관리자) |
