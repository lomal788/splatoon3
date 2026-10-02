# 스테이지 렌더링 — 대전 로비(Fld_VSLobby / 씬 LobbyVersus) 기준

맵 모델을 원본처럼 그리기 위한 명세입니다. 데이터 연결(씬 → 렌더링 파라미터 → env → 베이크), 맵 재질 셰이더 식(역번역), 광원·그림자·안개·잉크 표시, 웹 근사안을 다룹니다. 확정 수준 표기는 [README](../README.md)를 따릅니다. 셰이더 식은 원본 SASS를 Ryujinx 번역기로 옮긴 GLSL을 판독한 것입니다([shaders.md §2](shaders.md)).

관련 문서: [shaders.md](shaders.md)(Hoian_UBER 구조·BlitzUBO0), [team_color.md](team_color.md)(Ink 색과 주 광원), [../paint/paint_and_score.md](../paint/paint_and_score.md)(도색 텍스처), [../gimmick/collision_mesh.md](../gimmick/collision_mesh.md)(충돌 메시).

## 1. 결론 요약

| 항목 | 결론 | 수준 |
|---|---|---|
| 데이터 연결 | 씬 `LobbyVersus` → `SceneGfxFieldEnv` → `EnvSetDay` = `LobbyVersusLockerTest.RenderingDay` → `CustomGSysEnvSet` = genv `VSLobby`(장면 `VSLobby_Day`). 베이크 = `SceneBake.Day` → `Bake/Scene/LobbyVersus_Day.bkres.zs`(§2) | [데이터] |
| 렌더러 구성 | gsys 장면 설정 `Common`: **포워드**(g_buffer false) + Z 프리패스, 깊이 그림자 캐스케이드 2(near 1.5/20, far 60), 투영 그림자 2, masked light, 반사(큐브맵), DOF·블룸·HDR·색 보정 켬, SSAO·데칼·필터 AA 끔(§3) | [데이터] (패스 실행 순서는 [추정]) |
| 렌더링 파라미터 적용 | 0x7102b5fe88(t, 세트A, 세트B)가 하위 적용 함수를 고정 순서로 호출, 값은 `lerp(B, A, t)`(시간대 전환 보간). 정적 씬에서는 A=B(§4) | [판독] |
| MainLight → DirectionalLight | 0x7102b607c4: env 첫 DirectionalLight `DiffuseColor(+0x128) = Color`, `Intensity(+0x1a0) = Intens`. 0x7102b60ea0: `Direction(+0x1c0) = (−sin Lon·cos Lat, −sin Lat, −cos Lon·cos Lat)`(도 단위). **팀색 Ink 입력 경로의 [추정]이 해소됨**(접근자 경유가 아니라 직접 기록) | [판독] |
| 맵 재질 셰이더 | Fld_VSLobby 계열 64재질 → 프로그램 23종, 전부 정적 옵션 불일치 0. 주력 1689/917(베이크), 1714/946(베이크+도색). 식 전체 §5 | [데이터]+[판독] |
| 베이크 | bkres = SARC{`bkdat.byaml`, `textures.bntx`}. AO/그림자 = BC5(R=AO, G=그림자), 빛 = BC6H(rgb, 셰이더가 `rgb·a·32`). 재질별 `TexcoordScale/Offset` = `gsys_bake_st0/1`, UV = `_u1`(§6) | [데이터]+[판독] |
| BakeShadow 파라미터 | 0x7102b67bc4 → BlitzUBO0 [36].x = −ShOff·ShScale, [36].y = ShScale, [37].x = AOScale, [37].y = −AOOff·AOScale, [37].w = AOMainLightOcclude(§6.3) | [판독] |
| 잉크(맵) 표시 | 도색 텍스처 `cBlitzWallPaintGrid` 를 **런타임 생성 정점 속성** `_pu0/_pu1/_pu2`(bfres 에 없음)로 샘플. 잉크면 알베도·거칠기·법선·반사를 잉크 재질로 교체(§7) | [판독] |
| 잉크 표면 애니 | 0x7102c2036c → BlitzUBO0 [20] = (clamp01(Thickness.Base+A·sin(P·f)), clamp01(Thickness.BaseWall+…), max(0, Mottari.Base+…), f/60), f = GameFrame(+0x148) | [판독] |
| 동적 광원 | 셰이더: BlitzUBO2 의 XZ 20×20 격자(셀당 광원 4개, 8비트 인덱스, 최대 30개)로 점/스포트광 누적. 감쇠 `pow(clamp(1−d·k), e)`, 스포트 `pow(clamp((−L·D − c)/(1−c)), e2)`(§8) | [판독] (CPU 기록자 [미확정]) |
| 정정 | `cPrefilEnvMapArray` 의 4번째 좌표는 **밉이 아니라 큐브 배열 층**: 층 = roundEven(5.5 − 5.5·cos(π·거칠기)) ∈ 0..11, 잉크는 층 12 고정(§5.4). [shaders.md §3.2](shaders.md) 정정 | [판독] |

## 2. 자료와 데이터 연결

### 2.1 씬 → 파라미터 [데이터]

`Pack/Scene/LobbyVersus.pack.zs`(풀어 둔 것 `analysis/gfx4/scene_LobbyVersus/`):

```
Scene/LobbyVersus.engine__scene__SceneParam
  SceneBake        → Gyml/LobbyVersus.game__gfx__parameter__SceneBake   { SceneBakeSource.Day = Bake/Source/Scene/LobbyVersus_Day }
  SceneGfxFieldEnv → Gyml/LobbyVersus.game__gfx__parameter__FieldEnv    { EnvSetDay = LobbyVersusLockerTest.RenderingDay, EnvSetRich = [Customize.RenderingRich] }
  StartupMap       → Banc/Lby_Lobby00.bcett (배치, Fld_VSLobby Hash 4825244811554112121)
RenderingDay(LobbyVersusLockerTest):
  CustomGSysEnvSet { GEnvName = Env/VSLobby/VSLobby.genv, SceneEnvName = VSLobby_Day }
```

- 로비는 낮(Day) 세트 하나만 씁니다(Night/Sunset/BigRun 베이크 비어 있음).
- `Customize.RenderingRich` 는 로커 꾸미기 화면용으로 보입니다 [추정].

### 2.2 RenderingDay 값 (로비) [데이터]

| 경로 | 값 |
|---|---|
| Lighting.MainLight | Color (0.6706, 0.8510, 1.0), Intens 10, Latitude 34.5, Longitude −3 → 방향 (0.0431, −0.5664, −0.8230)(§4.2 식) |
| Lighting.DynamicLight.GridSize | (10, 1, 10) |
| Lighting.EnvMap | Type Illuminate, CapturePos (−5.0018, 1.1255, −5.6246), IlluminateEnvMap.LightArray[0] = {Intensity 6000, Latitude 67.5, LongitudeFromMainLight 315}, [1] = {3000, 80, 180}, 이하 Longitude 만 지정, RoughnessOffset 0.03 |
| Lighting.SkySphere | Sky_Daytime00, EmissionIntensInEnvMap 80, ExposureNotInEnvMap 2.0, SaturationInEnvMap 0.4, Offset (−15,0,0), Scale 1.1 |
| Fog.DepthFog | Color (0.749, 0.765, 0.698, A 0.25), Start 10, End 1000, ScatteringCoeff 0.3125 |
| Fog.HeightFog | Color (0.098, 0.129, 0.141, A 0.6875), Start 15, End 90 |
| PostEffect.ColorGrading | Enable, Value 1.0625, CurveColorR/G/B = Hermit2D 2점(아래) |
| PostEffect.DOFGaussian | Start 484, End 900, Level 0.5, FarCancel 20 |
| PostEffect.HDRExposure | ManualExposure, Value 1.0 |
| Shadow.BakeShadow | AOIntensOffset 0.125, AOIntensScale 1.0625, AOMainLightOcclude 0.03125, ShadowIntensOffset 0.71875, ShadowIntensScale 1.875 |
| Shadow.ProjShadow | Density 0(구름 그림자 없음), Scale (0.05, 0.05) |

ColorGrading 곡선 `Data` 6개 = (x0, y0, 기울기0, x1, y1, 기울기1)로 보이는 Hermite 2점 [추정 — 해석 코드 미판독]: R (0,0,0.7648)→(1,1,0.2668), G (0,0,0.5099)→(1,1,0.2549), B (0,0,0.6168)→(1,1,0.3585).

RenderingDay 구조 오프셋(방문 함수 디컴파일 `analysis/decomp/gfx4/g3_visitors.c`, 추출 `web/tools/gfx4_visitor_fields.py`) [판독]: MainLight {Color +0x30, CubeMapIntens +0x40, Intens +0x44, Latitude +0x48, Longitude +0x4c, IsUseCubeMapIntens +0x50}, DepthFog {Color +0x30, End +0x40, ScatteringCoeff +0x44, Start +0x48}, HeightFog {Color +0x30, Dir +0x40, End +0x4c, Start +0x50}, DynamicLight {GridOffset +0x30, GridSize +0x3c}, ColorGrading {CurveColorB +0x30, G +0x50, R +0x70, HDRTint +0x90, Hue +0xa0, Saturate +0xa4, Value +0xa8, Enable +0xac}, SkySphere {ActorName +0x30, Color0 +0x38, EmissionIntensInEnvMap +0x48, ExposureNotInEnvMap +0x4c, Offset +0x50, Rotate +0x5c, SaturationInEnvMap +0x60, Scale +0x64, Enable +0x68}, LightArray 원소 {Intensity +0x30, Latitude +0x34, LongitudeFromMainLight +0x38}, DOFGaussian {End +0x30, FarCancel +0x34, Level +0x38, Start +0x3c}, ManualExposure {Value +0x30}, BakeShadow {AOOff +0x30, AOScale +0x34, AOMainLightOcclude +0x38, ShOff +0x3c, ShScale +0x40}. 필드마다 "설정됨" 플래그 바이트가 있고 없으면 `$parent` 로 올라가 찾습니다(디컴파일의 상속 반복문, `web/tools/gfx4_fold.py` 로 접어 읽음).

### 2.3 env (genv) [데이터]

`Env/VSLobby.Nin_NX_NVN.genvb`(씬 팩 안, SARC) = `vslobby.bgenv` + `vslobby_day.baglenv`(AAMP). 이름 해시는 `web/tools/gfx4_aamp_names.py`·`gfx4_aamp_names2.py` 로 사전 공격해 `analysis/gfx4/aamp_names.txt` 에 모았고 `PY web/tools/gfx4_aamp.py <파일>` 로 덤프합니다(덤프 `analysis/gfx4/env/VSLobby/vslobby_day.txt`).

- `VSLobby_Day` 에는 **SpotLightRig 8개만** 있습니다(나머지 목록 비어 있음). 주 광원·안개 등은 기본 env(`Env/Default.genvb`, 덤프 `analysis/render/env/Default/day/`)의 객체에 RenderingDay 가 값을 써 넣습니다(§4).
- SpotLightRig 필드: `ModelName` = Fld_VSLobby, 이름 해시 0xc32f024e(뼈 이름으로 보임 [추정]) = `Dynamic_SpotLightA..H`(Fld_VSLobby 뼈 1~8, 위치 예 A (−25.61, 12.16, 4.78)), `enable`, `Intensity`, `Color`, `ColorOffset`, `SpecularColor`, `Radius`, `RadiusOffset`, `DampParam`, `Offset`, `Direction`, `Angle`(라디안으로 보임), `AngleDamp`, 이름 미상 f32 4개. 켜진 것: Rig1(Intensity 10, Radius 13, DampParam 0.31, Angle 2.95, AngleDamp 1.72), Rig2(15, 12, 0.69, 2.88, 1.42), Rig5~7(덤프 참조). Rig0/3/4 는 enable false.
- 기본 env 낮(참고): DirectionalLight0 `Main`(DiffuseColor 1, Intensity 4, Direction (−0.3,−0.7,−0.6)), Fog0 `FogTPS`(깊이 50~700), Fog1 `Fog_Y0`(높이 40~400), Projector `CroudProjector`(구름 그림자 투영), AutoExposure(IsEnable, RangeMin 2.5, RangeMax 3.0), bloom(luminance_intensity 3, clamped_luminance 5, threshold_range 1, intensity 1, color1..4), dof, bgsdw(depth_shadow_parameter_0 light Main/DirectionalLight, projection_shadow_0 CroudProjector density 0.9).

### 2.4 배치 광원 [데이터 + 판독]

`Banc/Lby_Lobby00` 에 `GfxSpotLight` 20, `GfxPointLight` 11, `GfxPointLightDynamic` 2(모두 `Layer: Day`). 크기는 배치 `Scale`, 파라미터:

| 타입 | Banc 파라미터 | 구조(0x7102b9e7ac 방문, 기본값 0x7104aa2a60) |
|---|---|---|
| `spl__gfx__LocatorSpotLightBancParam` | DiffuseColor, Intensity, DistDamp, AngleDamp, IsEnable, DebugDisplay | AngleDamp +0x30(기본 1.0), DiffuseColor +0x34((0,0,0,1)), DistDamp +0x44(1.2), Intensity +0x48(1.0), DebugDisplay +0x4c, IsEnable +0x4d(true) [판독] |
| `spl__gfx__LocatorPointLightBancParam` | DiffuseColor, Intensity, DampParam | 방문 함수 0x7102b9d88c 근처(미디컴파일) |

예: GfxPointLight (−30.28, −0.47, −0.39) Scale 8.48, Intensity 8, DampParam 1.5 / GfxPointLightDynamic (−21.62, 10.04, −10.67) Scale 4.83, Intensity 18.1 / GfxSpotLight (−9.79, 6.16, −19.26) Scale (10.30, 4.44, 10.30), Intensity 30, DistDamp 0.42, AngleDamp 3.26.

`GfxPointLight`/`GfxSpotLight`(Dynamic 아님)가 런타임 광원인지 베이크 전용인지는 [미확정]입니다. 이름 `GfxPointLightDynamic` 문자열만 main 에 있고(0x710104a86c, 0x7101d27a98 가 참조) 나머지 두 이름은 없습니다 → 정적 두 종류는 베이크(라이트맵)에만 기여할 가능성이 큽니다 [추정].

## 3. 렌더러 구성 (gsys 장면 설정) [데이터]

`Shader/Sample.Nin_NX_NVN.release.sarc` 안 `gsys.bgmsconf`(AAMP). 설정 이름 배열 `Common, MiniMap, Snapshot, Customize`. 대전·로비는 `Common` 으로 봅니다 [추정]. 덤프 `analysis/gfx4/gsys_bgmsconf_common.txt`.

| 키 | Common |
|---|---|
| g_buffer / z_pre_pass / geometry_culling_z_pre_pass | false / true / true → **포워드 셰이딩**(재질 셰이더가 최종 색까지 계산, §5와 일치) |
| create_depth_shadow, depth_shadow_cascade_num_0 | true, **2** |
| depth_shadow_near_0_0..3, depth_shadow_far_0 | 1.5, 20, 250, 16 / 60 (캐스케이드 경계로 보임: [1.5, 20], [20, 60] [추정]) |
| depth_shadow_clip_plane_0/1 | (0,1,0,−10), (0,−1,0,−150) |
| 깊이 그림자 맵 크기·형식(이름 미복원 해시) | 2048, `Depth_32`; 그림자 프리패스 버퍼 `R32_G32_float`(셰이더가 .xy 사용과 일치) [추정: 이름 해시 미복원] |
| projection_shadow_num | 2 |
| create_masked_light / create_reflection | true / true |
| create_dof / create_bloom / create_hdr / create_color_correction | 모두 true |
| create_ssocclusion / create_decal / create_shadow_mask / create_filter_aa / create_light_map / create_light_probe | 모두 false |
| linear_lighting_enable | true(선형 공간 조명) |
| 출력 크기(해시 0x7cb9885b / 0xa2d5f3e7) | 1280 / 720 |

패스 순서(재질 셰이더 입력에서 역산) [추정]: 깊이 그림자(캐스케이드 2) → Z 프리패스 → 그림자 프리패스(화면 공간, `cGSysShadowPrePass` .xy) → 불투명 포워드(Hoian_UBER, 베이크·SH·동적광·안개 포함) → 반투명(`gsys_render_state_mode translucent`, `gsys_pass seal` 등) → 후처리(블룸 → DOF → `HDRCompose`: 블룸 합성·색 보정·톤매핑·감마·비네트). 후처리 셰이더는 `Hoian_ProcHDRCompose.sharcb` 프로그램 `HDRCompose`(매크로 HDR_BLOOM_COMPOSE 0..2, HDR_COLOR_CORRECTION 0..1, HDR_TONEMAPPING 0..5, HDR_GAMMA 0..2, VIGNETTE_SHAPE 0..2) — 324조합 역번역을 `analysis/gfx4/sharc/hdrcompose/` 에 두었으나 **어느 변형을 쓰는지·식 판독은 [미확정]**.

## 4. 렌더링 파라미터 적용 — 0x7102b5fe88 [판독]

```
apply(t, A, env, B):            // 값 = lerp(B값, A값, t)  (일부는 t 를 [0,∞) 로 자름)
  0x7102b5ff94  주 광원: env 첫 DirectionalLight(타입 ID *0x7105999180, RTTI 확인) 가 있으면
                  0x7102b607c4  DL+0x128 DiffuseColor = MainLight.Color ; DL+0x1a0 Intensity = MainLight.Intens
                  0x7102b60ea0  DL+0x1c0 Direction = (−sin(Lon)·cos(Lat), −sin(Lat), −cos(Lon)·cos(Lat))   // 도 → ×0.017453292
                  0x7102b6157c  MainLight 색·세기를 이벤트(vt 0x71055648b0)로 수신자들에게 전달
  0x7102b61c20  DynamicLight(Grid) → 0x71010be03c(전역 *0x7105812ac0 의 env별 격자 설정 레코드에 GridOffset/GridSize 기록)
  0x7102b63334  env 의 두 번째 같은 타입 객체(+0x128..: Lighting 하위 값) 
  0x7102b63ce4  안개: DepthFog·HeightFog·RadialFog → 구조체(아래)를 이벤트(vt 0x710555da58)로 전달
  0x7102b66c54  env+0x2800 객체(+0x5ac/+0x5b0/+0x440/+0x360/+0x364/+0x400/+0x404/+0x380/+0x384/+0x420)
  0x7102b67bc4  BakeShadow → BlitzUBO0 [36]/[37] (§6.3)
  (vt+0x88 == 1) 0x7102b68ef4  env+0x2ac8 객체(자동 노출 계열로 보임 [추정])
  0x7102b699c0, 0x71011554a4, 0x710115567c, 0x7102b60200  (미판독)
```

- 호출자 0x7102b5c250(→0x7102b5c4a8). t 의 출처(시간대 전환 진행도)는 [미확정]. 로비는 낮 세트 하나라 A=B 로 두면 됩니다.
- 안개 구조체(0x7102b63ce4, 판독 일부): `DepthColor.rgba`, `−Start/(End−Start)`, `1/(End−Start)`(|End−Start| ≥ 0.01 로 보정), `ScatteringCoeff`, RadialFog 값들(+0x50 은 `1/exp2(2x)`), `HeightColor.rgba`, `normalize(HeightFog.Dir)`, `1/(End−Start)`, `−Start/(End−Start)`. 이것이 Env UBO 의 어느 칸으로 가는지(수신자)는 [미확정] — §5.5 의 셰이더 식과 형태가 맞습니다.
- 주 광원 값의 출처가 RenderingDay 라는 점이 확정되어, [team_color.md §5.3](team_color.md)의 Ink/InkBright 입력은 로비에서 `Intensity 10`, `DiffuseColor (0.6706, 0.8510, 1.0)` 입니다(기본 env 의 4.0/1.0 을 덮음).

## 5. 맵 재질 셰이더 (Hoian_UBER)

### 5.1 재질 → 프로그램 [데이터]

`Model/Fld_VSLobby.bfres.zs` 안 모델 5개(FldBG_LobbyDV, FldObj_DoorLobby, Fld_VSLobby, Fld_VSLobbyScreen, Obj_VSLobbyScreenSignage), 재질 64개. 덤프 `analysis/gfx4/raw/Fld_VSLobby.dump.json`(bfres2gltf `dump`), 요약 `analysis/gfx4/vslobby_materials.txt`. `PY web/tools/gfx4_stage_programs.py <덤프> analysis/gfx4/programs` 로 [shaders.md §3.5](shaders.md) 절차를 적용해 **64재질 전부 정적 옵션 불일치 0**(목록 `analysis/gfx4/programs/index.tsv`, GLSL 같은 폴더).

| 프로그램 | 재질 예 | 특징 |
|---|---|---|
| 1689 | BarUnique00, BigScreen, LockerSet00, ExitDoor 등 | 베이크(bake_shadow_type 2, bake_light_type 0) + 거칠기·금속 맵 |
| 917 | mLobbyFloor*, Sofa, TrussYellow 등 | 베이크 + 거칠기 맵 |
| **1714** | LobbyFloorConcrete, RampRubber, mLobbyWoodBox | 베이크 + **도색(blitz_paint_type 1)** + 거칠기·금속 |
| **946** | Wall02, mLobbyFloorRubber | 베이크 + 도색 + 거칠기 |
| 4194/4206/4467/4304/4534/4538/4540/4782 | 표지·식물·철망 | `gsys_render_state_mode mask`(알파 테스트) |
| 5284, 5110 | LobbySign02, Water00 | translucent |
| 5408 | Glass | mask + blitz_rendering_mode 3 |
| 2499/2250/3611/3608 | 발광(emission) 재질 | |
| 205/328/105/366/587/480/776/1519 | 천장 발광·정점색 그림자 등 | |
| 249/243/1293/337 | 사이니지(blitz_calc_color 네트워크, [shaders.md §3.6.4](shaders.md)) | |

공통 renderInfo: `gsys_static_depth_shadow 1`(대부분), `gsys_dynamic_depth_shadow 0`, `gsys_cube_map 1`, `gsys_env_obj_set TPS`, `gsys_priority_hint field_wall`, `spl_model_type 1`. 베이크 샘플러 `_b0 = bake0`, `_b1 = bake1` 에 자리표시 텍스처 `BakeDummy00`/`LightBakeDummy00` 가 꽂혀 있고 런타임에 bkres 텍스처로 바뀝니다 [추정: 교체 코드 미판독, 이름·형식 일치].

### 5.2 정점 셰이더 (1714) [판독]

```glsl
uvMat  = tex_mtx0 · _u0                                  // 알베도·노멀·거칠기 UV
uvBake0 = _u1 * gsys_bake_st0.xy + gsys_bake_st0.zw     // AO/그림자 (bkres TexcoordScale/Offset)
uvBake1 = _u1 * gsys_bake_st1.xy + gsys_bake_st1.zw     // 빛
paintUV  = _pu0 + col_paint_uv_offset.xyxy               // vec4: xy / zw 두 후보
paintSel = _pu1.x                                        // < 0 이면 zw
paintT   = ShpMtx(3x3) · _pu2.xyz                         // 도색 법선 기저(탄젠트)
worldPos = ShpMtx · _p0 ; N, T = ShpMtx · _n0/_t0 (정규화)
viewZ    = Context[2] · worldPos                          // 그림자 페이드에 사용
projShadowUV = Context[35..37] · worldPos                 // 투영(구름) 그림자
```

`_pu0/_pu1/_pu2`(aPaintUV/aPaintUVSwitch/aPaintUVTangent, location 14/15/13)는 **bfres 정점 버퍼에 없습니다**(Fld_VSLobby VB 속성은 `_p0 _n0 _t0 _u0 _u1` 뿐, attribAssign 도 `<Default Value>`) → 런타임에 생성됩니다. 생성 코드는 [../paint/](../paint/) 의 ColPaint 아틀라스 작업(paint4)과 같은 것으로 보며 SHARED 로 조율 중입니다 [추정].

### 5.3 프래그먼트 — 재질 값 [판독]

```glsl
// 기본 재질
alb  = texture(cTexAlbedo, uvMat).rgb
nT   = (Nrm.xy, sqrt(1 - x² - y²)) ; N = normalize(T·nT.x + B·nT.y + Nv·nT.z)   // B = cross(Nv,T)·t.w
rgh  = max(texture(cTexRoughness).r, 1e-4) ; mtl = texture(cTexMetalness).r
diff = alb·(1 − mtl) ; F0 = mix(0.04, alb, mtl)
// 잉크(§7)면 alb/rgh/mtl/N/반사를 덮어씀
```

### 5.4 프래그먼트 — 조명 합성 [판독]

```glsl
V   = normalize(camPos − P)            // camPos = Context[11..13].w
NoV = max(dot(N,V), 1e-8)
brdf = texture(cEnvBRDFMap, vec2(NoV, rgh)).xy            // (scale, bias)
R    = reflect(−V, N) ; layer = roundEven(5.5 − 5.5·cos(π·rgh))      // 0..11
spec_env = texture(cPrefilEnvMapArray, vec4(R/maxabs(R), layer)).rgb · (F0·brdf.x + brdf.y)
hemiFix  = clamp(1.16 − d·(1 − clamp(−7·inkM, 0,1)) ... )   // 비잉크: 아래쪽 반사 감쇠(아래 주석)
// 베이크
bk0 = texture(cTexBakeAOShadow, uvBake0).xy               // x = AO, y = 그림자(1 = 빛 받음)
bkL = texture(cTexBakeLight, uvBake1) ; bakeLight = bkL.rgb · bkL.a · 32
occAO   = clamp(AOScale·(1 − bk0.x) − AOOff·AOScale)       // [37].x·(1−AO) + [37].y
occBake = clamp(ShScale·(1 − bk0.y) − ShOff·ShScale)       // [36].y·(1−S) + [36].x
dynSh   = max(1 − SPP.x, 1 − SPP.y) · clamp(viewZ + [36].z, 0, 1)   // SPP = cGSysShadowPrePass(화면 UV)
projSh  = Context[41].x · (1 − texture(cGSysProjection0, projUV).x)
shadow  = clamp(1 − (occAO·AOMainLightOcclude + dynSh + projSh + occBake), 0, 1)
ambOcc  = 1 − occAO
// 간접광
SH(N)   = max(0, SH9(N))   // Env[25..31] = cAr,cAg,cAb,cBr,cBg,cBb,cC (7×vec4)
indirect = diff'·bakeLight + SH(N)·diff' + spec_env           // diff' = diff·(1 − F0)
indirect += Σ 동적광(§8)
// 직접광(주 광원)
L = −Env[23].xyz ; Lc = Env[5].xyz ; NoL = clamp(dot(N, L))
direct = (GGX_spec(F0, rgh, N, V, L)·(1/4π) + diff/π) · (NoL·Lc + bakeLight) · shadow · hemiFix
col = ambOcc·indirect + direct + inkEmission
```

- GGX: D = α²/(π(…))형, α = rgh², 가시성 항 `1/((k + (1−k)NoL)(k + (1−k)NoV))`, k = (rgh·0.5+0.5)²·0.5, 프레넬 `exp2(VoH·(−5.55473·VoH − 6.98316))` — 원본 식은 역번역 파일 그대로(상수 0.0795774683 = 1/4π, 0.318309873 = 1/π).
- **베이크 빛이 간접(디퓨즈) 항과 직접광 항(NoL·Lc 와 합산) 두 곳에 들어갑니다.** 원본 식 그대로 둡니다(정리하지 말 것).
- `hemiFix`(temp_115) = 비잉크: `clamp(−(N_bent·L')·(1 − clamp(−7·(inkMax−0.3)))... + 1.16)` 형태로 반사 방향이 광원 반대일 때 줄이는 항, 잉크: 1.0. 정확한 식은 `analysis/gfx4/programs/Fld_VSLobby__LobbyFloorConcrete.frag` temp_126/temp_115.
- **정정**: 이전 판 [shaders.md §3.2](shaders.md)의 "`cPrefilEnvMapArray`(거칠기→밉)"은 큐브 **배열 층** 선택입니다(samplerCubeArray 의 4번째 좌표). 잉크 분기는 층 12, 명시 lod 0.

### 5.5 안개 [판독: 셰이더, 칸 의미는 §4 구조체와의 대응으로 추정]

```glsl
d     = |P − camPos|
// 높이 안개
hf    = clamp(dot(P, Env[14].xyz)·(−Env[15].x) + Env[14].w, 0, 1) · Env[13].w
col   = mix(col, Env[13].rgb, hf)
// 깊이 안개 + 산란
s     = clamp(d·Env[12].x + Env[11].w, 0, 1)                    // (d − Start)/(End − Start)
df    = clamp(1 − exp(−s·[53].x), 0, 1) · Env[10].w
scat  = pow(clamp(d·Context[15].x), [54].x) · exp2([54].y·(1 − dot(Vdir, Env[23])))
         · [55].rgb · clamp(shadow·(1−occAO)·[54].w + 1 − [54].w) · [54].z
fogC  = mix(Env[10].rgb, scat, [53].w)
out   = mix(col, fogC, df)
```

Env[10] = DepthFog 색(a = 최대 농도 A), Env[11].w/[12].x = −Start/(End−Start), 1/(End−Start), Env[13] = HeightFog 색, Env[14].xyz = HeightFog 방향 [추정: §4 안개 구조체의 값 형태와 일치, 실제 복사 코드 미판독]. BlitzUBO0 [53]~[55]의 기록자는 [미확정](후보 0x7102c5a3c8 이 holder+0x13e8 기록 — 다른 에이전트가 디컴파일 `analysis/decomp/phys4/p4_world_ctrl.c` 에 둠).

## 6. 베이크 (bkres)

### 6.1 형식 [데이터]

`Bake/Scene/LobbyVersus_Day.bkres.zs` = zstd → SARC(9.7 MB):

| 파일 | 내용 |
|---|---|
| `bkdat.byaml` | `{Version 7, ExternalTexture false, DataElements[]}` |
| `textures.bntx` | `0_bktex0` BC5_UNORM 2299×1777 mip 12 (comp RG01) / `1_bktex0` BC6H_UFLOAT 1532×1184 mip 11 (comp RGB1) |

`DataElements[k] = {BindingSpace 0, DataType, TextureNames[], ModelElements[]}`: DataType **3 = AO/그림자(→ `_b0` cTexBakeAOShadow)**, **4 = 빛(→ `_b1` cTexBakeLight)** [추정: 형식(BC5 2채널 / BC6H HDR)과 셰이더 사용(.xy / .rgb·a·32) 일치]. `ModelElements[] = {Guid, ModelName, OriginalMaterialCount, MaterialElements[]}`, `MaterialElements[] = {MaterialName, OriginalMaterialIndex, TexcoordScale{X,Y}, TexcoordOffset{X,Y}, TextureIndex}`.

- `Guid = "<배치 Hash>_<액터 안 모델 번호>"`: Fld_VSLobby 배치 Hash 4825244811554112121 → `_0` = Fld_VSLobby(47/50재질), `_1` = FldBG_LobbyDV(3/8). DObj_FldObj_DoorLobby(15205139476108028325) `_0` = FldObj_DoorLobby 등 [데이터]. 같은 bfres 를 여러 번 배치하면 배치마다 다른 UV 영역을 가집니다.
- 베이크가 없는 재질(MaterialElements 에 없는 것)은 bake 옵션이 꺼진 재질과 일치합니다(Glass·발광 등) [데이터 일부 확인].

### 6.2 적용 [판독: 셰이더]

`gsys_bake_st0 = (ScaleX, ScaleY, OffsetX, OffsetY)` (DataType 3 원소), `gsys_bake_st1` = DataType 4 원소, UV = `_u1`(VB `Format_16_16_UNorm`). 식은 §5.2/§5.4. 빛 텍스처는 BC6H 라 a = 1 → `bakeLight = rgb·32`.

### 6.3 BakeShadow → BlitzUBO0 [판독: 0x7102b67bc4]

| UBO | 값 | 로비 |
|---|---|---|
| [36].x (holder+0x1000) | −lerp(ShOff·ShScale) | −1.34765625 |
| [36].y (+0x1004) | lerp(ShScale) | 1.875 |
| [36].z (+0x1008) | 활성 env `*(env+0x1338)+0x7c8` (0x7101110750) — 동적 그림자 페이드 거리로 보임 [추정] | 미상 |
| [37].x (+0x1048) | lerp(AOScale) | 1.0625 |
| [37].y (+0x104c) | −lerp(AOOff·AOScale) | −0.1328125 |
| [37].w (+0x1054) | lerp(AOMainLightOcclude) | 0.03125 |

즉 `occBake = clamp(1.875·(1 − S) − 1.3477)` = S < 0.281 일 때만 그림자, `occAO = clamp(1.0625·(1 − AO) − 0.1328)`.

### 6.4 웹 변환 [제안]

- `bkdat.byaml` → JSON(Guid·재질 → st0/st1). `textures.bntx` → BC5 는 RG 8비트 PNG/KTX2, BC6H 는 **KTX2(BC6H 그대로, WebGL `EXT_texture_compression_bptc`)** 또는 RGB 반정밀 float(.bin) — 웹에서 `rgb·32` 를 그대로 적용.
- 배치 Hash 로 Guid 를 맞추고, 재질 이름으로 `MaterialElements` 를 찾아 셰이더 uniform `bakeSt0/bakeSt1` 에 넣습니다.

## 7. 맵 위 잉크 [판독: 셰이더 1714]

```glsl
uv   = (paintSel < 0) ? paintUV.zw : paintUV.xy ; uv.y = 1 − uv.y
c    = texture(cBlitzWallPaintGrid, uv).rgb               // 팀 0/1/2 잉크량([shaders.md §4.4])
m    = max(c.r, c.g, c.b) ; inkM = m − [21].w(0.3)
team = 원-핫(c.ch ≥ m − 1e-4)                             // 최대 채널
ink  = min(clamp(inkM)·1000, 1) > 0.5                      // m > 0.3005
if (ink) {
  Ink, InkBright = 선택 팀의 BlitzUBO0 [3]/[4](팀0), [10]/[11](팀1), [62]/[63](팀2)
  alb  = mix(InkBright·InkRimIntensity, Ink, clamp(inkM·InkRimBlendCoef))      // [45].y/.z
  rgh  = InkUBOParam.Roughness([18].x) ; mtl = 0
  // 잉크 법선: 이웃 두 텍셀(오프셋 Mottari·[22].zw)과의 차분 × InkNormalIntensity([18].y)
  g    = (Σ team·(c − c_dv), Σ team·(c − c_du)) · [18].y
  Nink = normalize(Nv + T_paint·g.y + B_paint·g.x)        // T/B = _pu2 기저
  N    = mix(N_mat, Nink, mix([20].y, [20].x, clamp(Nv.y)))   // 바닥=Thickness.Base, 벽=BaseWall
  반사: 큐브 층 12, F0 = Fresnel([19].x), 비등방 Nv 혼합 [19].z
  inkEmission = alb · [18].z                               // env 접근자 "Ink"(ID 0x5e)
}
```

- 잉크 판정 임계는 도색 스탬프와 같은 0.3([shaders.md §4.4](shaders.md)).
- [22].z/.w(텍셀 간격으로 보임)의 기록자는 [미확정]. 0x7102c1b5a4 가 [22].x/.y 를 쓰는 것만 확인(도색 영역 투영 크기).
- InkUBOParamDay 값: Roughness 0.05, Fresnel 0.015, InkIrradianceAnisotoropy 0.5, InkNormalIntensity 1.8, Thickness {Base 0.95, BaseWall 0.75, Anim {Amplitude 0.015625, WavePeriod 0.03125}}, Mottari {Base 1.75, Anim {0.0625, 0.08}}, SSS {InkRimIntensity 0.625, InkRimBlendCoef 0.875} [데이터]. Surface 구조 오프셋: Mottari +0x30, Thickness +0x38, InkNormalIntensity +0x40; Thickness {Anim +0x30, Base +0x38, BaseWall +0x3c}, Anim {Amplitude +0x30, WavePeriod +0x34} [판독: 0x71011b2b84 플래그 + 0x7102c2036c 읽기 순서].
- [20] = (clamp01(0.95 + 0.015625·sin(0.03125·f)), clamp01(0.75 + 0.015625·sin(0.03125·f)), max(0, 1.75 + 0.0625·sin(0.08·f)), f/60), f = GameFrame 정수 프레임(+0x148) [판독: 0x7102c2036c, 주기 단위는 라디안/프레임].

## 8. 동적 광원 (BlitzUBO2) [판독: 셰이더]

```glsl
cx = clamp(int((P.x − U2[0x226].x)·U2[0x227].x), 0, 19) ; cz = clamp(int((P.z − U2[0x226].z)·U2[0x227].z), 0, 19)
word = U2 의 (cz·20 + cx)번째 u32 ; if (word == 0xFFFFFFFF) 없음
for k in 0..3: i = (word >> 8k) & 0xFF ; if (i >= 30) break
   pos = U2[0x1CC0 + 16i], col = U2[0x1900 + 16i](rgb), att = U2[0x1AE0 + 16i](x = 1/반경로 보임, y = 지수)
   Ld = pos − P ; d = |Ld| ; L = Ld/d
   a  = pow(clamp(1 − att.x·d), att.y) · clamp(dot(N, L))
   if (U2[0x2080 + 16i] != 0) {  // 스포트
      sp = U2[0x1AE8 + 16i](x = cos 경계 c, y = 지수) ; D = U2[0x1EA0 + 16i]
      a *= pow(clamp((−dot(L, D) − sp.x)/(1 − sp.x)), sp.y) }
   indirect += col·a·(diff/π + spec_GGX(…)/4π)
```

- 격자 원점·역셀 크기 = BlitzUBO2 data[0x226]/[0x227]. RenderingDay `DynamicLight.GridSize (10,1,10)` 와 셀 20개 → 200×200 범위로 보임 [추정]. 셀당 최대 4개, 전체 최대 30개.
- CPU 기록자(BlitzUBO2 = `*0x7105810020 + 0x1398` 블록, [shaders.md §3.9](shaders.md))는 [미확정]. 후보: holder+0x35f8/0x3608(=0x1398+0x2260/0x2270)을 함께 쓰는 0x71029b6698, 0x71034da0c8, 0x71034dc9dc, 0x710369bf40(`render_storescan.py`).
- 감쇠 지수 ↔ 데이터(`DampParam`/`DistDamp`/`AngleDamp`), 반경 ↔ 배치 `Scale`/`Radius` 대응은 [추정](이름이 맞을 뿐 복사 코드 미판독).

## 9. 웹 포팅 (three.js) — 근사안

| 원본 | 웹 | 수준 |
|---|---|---|
| 포워드 Hoian_UBER 프로그램(1689/917/1714/946) | `MeshStandardMaterial` + `onBeforeCompile` 로 §5 식 이식(베이크 두 장, 잉크 분기). 최소안: map/normalMap/roughnessMap/metalnessMap + `aoMap`(BC5.R 를 occAO 식으로 변환) + `lightMap`(bakeLight·32) | 식은 원본, 합성은 근사 |
| 주 광원 | `DirectionalLight` 방향 = −(0.0431, −0.5664, −0.8230) 쪽에서 비춤(§4 식), 색 (0.6706,0.8510,1.0), 세기 10(선형). three 물리 조명 단위와 다르므로 노출로 맞춤 | 값 [판독] |
| SH 환경광(Env[25..31]) | 원본 송신원 [미확정]. 근사: CapturePos(−5.00, 1.13, −5.62)에서 `CubeCamera` 로 하늘(Sky_Daytime00)+맵을 찍고 `LightProbeGenerator.fromCubeRenderTarget` → `LightProbe` | 근사 |
| 반사 `cPrefilEnvMapArray`(12 거칠기 층) | 같은 큐브 → `PMREMGenerator`(거칠기→밉). 층 = roundEven(5.5−5.5cos(πr)) 대신 three 기본 매핑 | 근사 |
| 베이크 | §6.4 | 원본 데이터 |
| 동적 그림자 | `DirectionalLight.shadow`(2048, 캐스케이드 대신 카메라 추종 박스 ~60) — 원본은 정적 메시가 대부분 `gsys_dynamic_depth_shadow 0` 이고 베이크 그림자를 씀 → 플레이어·움직이는 물체만 그림자 캐스터로 | 근사 |
| 동적 광원 | 켜진 SpotLightRig(뼈 위치) + GfxPointLightDynamic 을 `PointLight/SpotLight` 로. 감쇠는 셰이더 청크로 `pow(clamp(1−d/R), e)` | [추정] 대응 |
| 안개 | `scene.fog` 대신 셰이더 청크로 §5.5 식(깊이: Start 10/End 1000/A 0.25, 높이: 15/90/A 0.6875) | 식 [판독], 칸 대응 [추정] |
| 노출·색 보정 | ManualExposure 1.0 → `toneMappingExposure 1`. 톤매핑 변형 [미확정] → 우선 `NoToneMapping` + 색 보정 Hermite 곡선(§2.2)을 LUT 로, 결과 확인 후 조정 | 근사 |
| 잉크 | paint 영역의 도색 텍스처를 `cBlitzWallPaintGrid` 로, `_pu*` 는 paint4 결과로 생성 | §7 원본 식 |

구현 순서 권장: (1) 맵 glb + 베이크 두 장 + 주 광원 + 고정 환경광 → (2) 잉크 분기 → (3) 안개·색 보정 → (4) 동적광·그림자.

## 10. 검증

| 항목 | 방법 | 결과 |
|---|---|---|
| 재질 → 프로그램 | 키 표 정적 옵션 전수 대조(`gfx4_stage_programs.py`) | 64/64 불일치 0 [데이터] |
| 주 광원 방향 | 0x7102b60ea0 식에 로비 값 대입 | (0.04313, −0.56641, −0.82300) [재구현 계산] |
| BakeShadow 칸 | 0x7102b67bc4 식에 로비 값 대입 | §6.3 표 [재구현 계산] |
| env AAMP 이름 | CRC32 사전 공격 | 320 해시 중 다수 복원, 오탐 제거 목록은 `gfx4_aamp_names2.py` 실행 결과 기준 수동 [실행: 자체 도구] |

원본 실행 대조·화면 비교는 하지 않았습니다. 셰이더 식은 역번역 판독이고, CPU 쪽 UBO 칸 대응 중 [추정] 표시는 복사 코드를 보지 않은 것입니다.

## 11. 미확정 — 다음에 볼 곳

| 항목 | 다음에 볼 곳 |
|---|---|
| Env UBO(gsys_environment 512 B) 칸 대응(주 광원 [5]/[23], 안개 [10..15], SH [25..31]) | 안개 이벤트(vt 0x710555da58)·주광 이벤트(vt 0x71055648b0) 수신자, gsys 환경 UBO 작성 함수 |
| 하늘 SH 송신원 | 0x710117649c 등록 이벤트 키, `IlluminateEnvMap`(LightArray 위도·경도 0x71011abdf4) 처리·큐브 캡처 → SH 투영 코드 |
| BlitzUBO2 광원 격자 기록자 | §8 후보 4개 |
| BlitzUBO0 [22].zw, [53]~[55] 기록자 | holder+0xcc0/0xcc4, +0x13e8(0x7102c5a3c8), +0x1430(0x7102553d60), +0x1478 |
| 톤매핑 변형·노출 계산 | HDRCompose 변형 선택 코드(env 접근자 ID 0x1c/0x1d "HDRCompose", 0x1e~0x20 "AutoExp"), 역번역 `analysis/gfx4/sharc/hdrcompose/` |
| 적용 함수 미판독분 | 0x7102b63334, 0x7102b66c54(env+0x2800), 0x7102b68ef4(env+0x2ac8), 0x7102b699c0, 0x71011554a4, 0x710115567c, 0x7102b60200 (`analysis/decomp/gfx4/g2_apply.c`) |
| 베이크 텍스처 교체 코드, GfxPointLight/SpotLight(비 Dynamic)의 런타임 사용 여부 | `bkdat` 로더(문자열 `TexcoordScale`·`DataElements` xref), 0x7101d259c0 |
| `_pu*` 정점 속성 생성 | paint4(ColPaint UV) |

## 12. 자료·도구

| 경로 | 내용 |
|---|---|
| `analysis/gfx4/scene_LobbyVersus/` | 씬 팩 해제(JSON 사본) |
| `analysis/gfx4/env/VSLobby/`, `analysis/gfx4/aamp_names.txt` | genv 해제·덤프, AAMP 이름 사전 |
| `analysis/gfx4/raw/Fld_VSLobby.{bfres,dump.json}`, `vslobby_materials.txt` | 맵 bfres 해제·덤프·재질 요약 |
| `analysis/gfx4/programs/` | 맵 재질 64개 프로그램 GLSL·옵션·index.tsv |
| `analysis/gfx4/bake/LobbyVersus_Day/` | bkres 해제(bkdat JSON, textures.bntx) |
| `analysis/gfx4/sharc/` | HDRCompose·agl 후처리/그림자/조명 sharcb 정보, HDRCompose 324조합 역번역 |
| `analysis/gfx4/gsys_bgmsconf_common.txt`, `env_accessors.tsv` | gsys 장면 설정, env 접근자 ID 0x01~0x65 ↔ 그룹(ZFog/YFog/Bloom/HDRCompose/AutoExp/ShadowPP/DynamicShadow/ProjShadow/DOF/ColorGrading/MainLight/Ink/GlobalWind/Resolution/RadialFog …) |
| `analysis/decomp/gfx4/g1.c, g2_apply.c, g3_visitors.c, g4_mainlight.c` (+`*_fold.c`) | 디컴파일 |
| `web/tools/gfx4_aamp_names.py`, `gfx4_aamp_names2.py`, `gfx4_aamp.py` | AAMP 이름 복원·덤프 |
| `web/tools/gfx4_stage_programs.py` | bfres 덤프 → 재질 프로그램 역번역 |
| `web/tools/gfx4_fold.py`, `gfx4_visitor_fields.py`, `gfx4_envaccessor_scan.py` | 상속 반복문 접기, 방문 함수 필드 추출, env 접근자 스캔 |
