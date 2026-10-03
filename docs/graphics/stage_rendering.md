# 스테이지 렌더링 — 대전 로비(Fld_VSLobby / 씬 LobbyVersus) 기준

**2026-10-03 첨부 화면 분석 정정 [판독]:** 원시 Maxwell와 분석용 Negate 괄호 보완 CLI로 기존 역번역의 부호 괄호 결함을 확인했다. p1714 BRDF.y는 **−roughness**이며, 잉크 SH는 최종N과 world-up을 혼합하고 다시 정규화하지 않는다. cube array 층12는 **implicit LOD+bias0**로 샘플하며 명시 mip0 고정이 아니다. 기존 설명은 당시 기록으로 보존한다. [원시 주소·정정 이유·보완 출력](reference_ink_surface.md#6-계산식조건상세-의사코드). 원본 GPU 픽셀은 미검증이다.

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
| 후처리 합성 HDRCompose (5차) | 게임 전용 `Hoian_ProcHDRCompose`(agl `hdr_compose` 아님)로 그린다. 픽셀 순서 = `HDR·노출 (+블룸)` → 톤매핑 → 색 보정 3D LUT → 비네트 → 감마. 톤매핑 6종·감마 3종·블룸 합성 3종 식 전부(§3.1). 변형 번호 선택 0x710112215c 와 플래그 기록 0x7103744058 을 원본 실행으로 확인(§3.2) | [판독]+[실행] |
| 톤매핑 종류 (5차) | HDR 객체(env+0x2ae0) +0x18 의 유일한 기록자 0x710121c240 이 **4**를 쓴다. 이 함수만 게임 HDRCompose 그리기 콜백(0x710112c604)을 설치하므로, 게임 HDRCompose 로 그리는 한 톤매핑은 4번 식이다(§3.2) | [판독] |
| 노출 (5차) | `cParam.x` = 수동 노출이면 `exp2(HDRExposure.ManualExposure.Value)`, 아니면 1.0. 최종 배율 = `cExposureTexture(0,0).w × cParam.x`. 수동이면 노출 텍스처는 기본 `White2D`(w = 1). **로비 = 2^1.0 = 2.0**(§3.3) | [판독] |
| 블룸 파라미터 (5차) | 적용 0x7102b699c0 → env+0x2ab8 객체. 로비 RenderingDay 에는 Bloom 블록이 없어 생성자 기본값(Enable true, Threshold 4.0, ThresholdRange 1.0, Intensity 1.0, ClampedLuminance 5.0)을 쓴다(§3.4). 합성 방식(+0x438)은 [미확정] | [판독] |
| 하늘 SH (5차) | 환경 큐브 → GPU `IrradianceCubeMapAllToSH`(MRT 7장 가산) → CPU 리드백 → 0x71010325d4 가 cAr..cC 7×vec4 로 변환 → 환경광 관리자 +0x4b8(0x70 B)을 gsys 뷰 레코드 +0x98/+0xa0 에 등록하고 SH 이벤트(키 0x710580e818)를 보낸다. 팀색 skyUp 은 이 이벤트로 갱신된다(§5.6) | [판독]+[실행] |
| 하늘 구 (5차) | Sky_Daytime00 `mSky` = 프로그램 25: `Emm.rgb·emission_color·emission_intensity·emission_intens_not_in_envmap + albedo_color`, `emission_intens_not_in_envmap = exp2(SkySphere.ExposureNotInEnvMap)`(로비 4.0), 큐브 캡처용 `emission_intens_in_envmap = EmissionIntensInEnvMap`(80)(§5.7) | [판독]+[데이터] |
| BlitzUBO0 [53]~[55] (5차) | 작성자 0x7101185af4(안개 이벤트 수신): [53] = (ScatteringCoeff, 1/(End−Start), ScatteringCoeff, RadialFog 값), [54]/[55] = 이벤트 +0x48/+0x38 vec4(§5.5) | [판독] |
| 정정 (5차) | 0x7102b61c20 은 DynamicLight 격자가 아니라 **DepthFog·OverlookDepthFog 보간 → 안개 관리자(*0x7105812ac0) 레코드**이고, 0x7102b63334 는 HeightFog 를 env 두 번째 agl `Fog` 객체(Start +0x128, End +0x148, Color +0x188)에 쓴다(§4) | [판독] |
| Env UBO 512 B 칸 대응 (6차) | 기록자 = gsys 0x71036b35c0(뷰마다) + 안개 0x71036b1300. 멤버 35개 선언(0x71036ae130 안)을 원본 실행해 오프셋을 얻었다: [0] Ambient, [1]/[2] Hemisphere 색, [4].xyz/[23].xyz 주광 방향, [4].w 세기, **[5] = Intensity·DiffuseColor**, [6] 둘째 색, [7..9] 둘째 방향광, **[10..21] agl Fog 4개(색, 방향, −S/(E−S), 1/(E−S), Damp)**, **[25..31] = 환경광 관리자 SH 0x70 B**(§5.5.1) | [실행]+[판독] |
| 하늘 SH 경로 (6차) | 로비의 환경광 객체 "Main" 은 기본 장면 gfx 경로(0x710121dbc0 → 0x71010bf36c)로 `+0x5c8 = 0`(캡처 경로)을 받는다. 대체 SH(주광 0.1·I·Diffuse)는 캡처 전 첫 송신에만 쓰이고, 그 뒤 **실행 중 렌더한 BaseCubeMap(256², RGBA16F)** 을 두 번 캡처해 투영한 SH 로 바뀐다. 큐브는 romfs 데이터가 아니라 장면을 그린 결과다(§5.6) | [판독] |
| 팀색 skyUp (6차) | 로비 주광(Intens 10, L*(Diffuse) 92.73)에서는 `t ≥ 9.27 > 6` 이라 r 이 Rate6 에서 포화해 **Ink/InkBright 가 skyUp 과 무관**하다. 0x7101174afc 원본 실행 500색×skyUp 5종 모두 비트 동일(대조군 t=4 는 485/500 달라짐) | [실행]+[판독]+[데이터] |
| HDRCompose 로비 변형 (6차) | BLOOM: 블룸 객체 +0x438 = agl bloom 파라미터 `finalblend`(Default env 값 1) → **가산(BLOOM 1)**. CC: +0x2410 bit4 는 생성 때 0x71035db354 가 켜고 끄는 코드가 없다 → **CC 1**. GAMMA: 장면+0x1c0 = gsys 장면 설정, +0xf00 = `linear_lighting_enable`(Common true) → 장면+0x523c bit4 가 꺼져 있으면 GAMMA 1(pow 1/2.2). bit4 출처는 [미확정] (§3.2) | [판독]+[데이터], 감마 일부 [미확정] |
| 그림자 설정 (6차) | gsys 설정 생성자 0x7103705fec 를 실행해 이름 해시를 복원했다. 동적 깊이 그림자 = 캐스케이드 2, **1024×1024**, 깊이 바이어스 `depth_shadow_polygon_offset 0.3`·`polygon_scale 5.0`, `depth_shadow_pcf_offset 0.5`(텍셀 → UV 0.5/1024), near/far 1.5·20·250·16 / 60. 정정: 2048·`Depth_32`·`R32_G32_float` 는 **정적 그림자**(`static_sdw_*`) 값이다(§3) | [실행]+[데이터]+[판독] |
| RadialFog (6차) | 필드 BlendFactor +0x30(0.0), Color +0x34(1, 0.95, 0.7, 1), Intens +0x44(1.0), LobeCtrl +0x48(1.0), ShadowInfluence +0x4c(0.0), SizeCtrl +0x50(5.0). 로비는 빈 블록 → BlendFactor 0 → **산란 항 꺼짐**(§4, §5.5) | [판독] |

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

**정정(2026-10-03, 7차):** 위 문장은 이전 기록입니다. `Data = (X0, Y0, M0, X1, Y1, M1)`은 원본 함수로 해소했습니다. M은 **구간 정규 좌표의 접선**이며, 실제 X 단위의 기울기처럼 `(X1−X0)`를 곱하지 않습니다. 로비는 X 간격이 1이라 두 해석이 같은 숫자를 내지만, 비단위 X 간격의 합성 입력도 실행해 이 차이를 확인했습니다. 전체 LUT 결과까지 확정한 것은 아닙니다.

### 2.2.1 ColorGrading Hermit2D 곡선 (7차) [실행]+[판독]+[데이터]

**2026-10-03 r2 추가 [실행-CPU]+[판독]+[데이터]:** 기존 Hermit2D 표본 확인에 이어 기본 mode0의 `35db354→115567c→35dc218` 원본 연쇄를 실제 로비 데이터와 128개 합성 입력으로 대조했다. 순서는 **HSV(0,1,1.0625)→RGB 8점 표본 선형 보간→Gamma(1,1,1,1)**, count3이다. used192B 계약에서 RGB·헤더·Gamma가 비트 일치했고 A 표본은 독립 대조에 넣지 않았다. 원본 LUT 좌표 공급 블록도128/128 일치했다. CB1 간접 분기표 누락을 보완해 셰이더를 재판독했으며, GPU LUT 픽셀·sampler·실제 최종 variant는 미확정이다. [ink_lighting_r2 §6·10·11](ink_lighting_r2.md).


이름·번호 연결 [판독]: ColorGrading 방문 함수는 R/G/B 곡선을 각각 +0x70/+0x50/+0x30에 넣습니다. 파라미터 곡선 래퍼(vtable 0x7105553c78, 슬롯 4 = 0x71010080B0)는 BYAML 로더 0x71038C7F28을 부릅니다. 이 로더는 0x71038C8FC8이 문자열 0x710493E6B9를 분리한 이름 표의 **+0x38(번호 7, 0부터 세므로 여덟째)**와 `Type`을 비교하며, 0x71038C8344에서 7을 만들어 0x71038C8228에서 곡선 +8에 기록합니다. 문자열 배열의 번호 7은 `Hermit2D`입니다.

적용 0x710115567C는 R 곡선의 type(+0x78)·Data 원소 수(+0x80)·Data 포인터(+0x88)를 읽어 색 보정 객체의 선택 곡선 레코드(`CC+0xFA0+slot×0x280`) +0x28(type)·+0x2B(원소 수), +0x80(Data 복사)에 넣습니다 [판독]. G/B는 같은 레코드 +0x40/+0x58 헤더를 씁니다. LUT 갱신 0x71035DC218은 종류 6에서 이 헤더(`CC+0xFC8/+0xFE0/+0xFF8`)의 type으로 점프표 **0x71057215E8**을 읽습니다. 번호 7의 포인터는 **0x710358CFE0**이며, 이번에 새로 판독·실행한 함수입니다. 이 연결을 다른 camera 곡선 함수 주소에 그대로 적용하지 않습니다.

ABI: S0 = 입력 t, X0 = 타입 헤더(type 바이트 +0, Data 원소 수 u8 +3), X1 = f32 Data 배열, 반환 S0. n = `floor(header[3]/3)`개의 `(X,Y,M)` 키입니다. 유효 데이터는 증가하는 X 키 2개 이상입니다. t≤첫 X면 첫 Y, t≥마지막 X면 마지막 Y를 반환합니다. 중간에서는 **다음 키 X>t인 첫 구간**을 선택합니다. `MaxX`로 나누는 명령은 이 reader에 없습니다.

```text
u = f32(f32(t−X0) / f32(X1−X0))
h00 = 2u³−3u²+1; h01 = 3u²−2u³
h10 = u³−2u²+u; h11 = u³−u²
Y = Y0*h00 + Y1*h01 + M0*h10 + M1*h11
```

연산은 원본의 FMUL/FADD/FSUB/FDIV 순서로 모두 f32입니다. **FMA는 없습니다.** 비트 대조 도구가 쓰는 정확한 결합 순서는 `twoSq=f32(u*f32(u+u))`, `twoCube=f32(u*twoSq)`, `threeSq=f32(u*f32(u*3))`, `sq=f32(u*u)`, `cube=f32(u*sq)`, h00=`f32(f32(twoCube−threeSq)+1)`, h01=`f32(threeSq−twoCube)`, h10=`f32(u+f32(cube−twoSq))`, h11=`f32(cube−sq)`입니다. 출력은 `f32(f32(M1*h11) + f32(f32(M0*h10) + f32(f32(Y1*h01)+f32(Y0*h00))))`입니다. 디컴파일의 `u*u*3`처럼 곱 결합을 바꾸면 비트가 달라질 수 있습니다.

로비의 원본 Data는 §2.2 JSON의 f32 값 그대로이며, LUT 갱신 입력 `t = f32(i/7)`의 원본 함수 출력은 다음과 같습니다. 표의 숫자는 표시만 9자리 반올림했으며 결과 JSON에 f32 비트가 있습니다.

| i | R | G | B |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 0.130998716 | 0.104448766 | 0.113857903 |
| 2 | 0.294183195 | 0.257711560 | 0.267257094 |
| 3 | 0.472613573 | 0.438181609 | 0.442272514 |
| 4 | 0.649350286 | 0.624252319 | 0.620979607 |
| 5 | 0.807453334 | 0.794316649 | 0.785453022 |
| 6 | 0.929983079 | 0.926768064 | 0.917768061 |
| 7 | 1 | 1 | 1 |

원본 전체 0x710358CFE0 실행은 **2,127/2,127 비트 일치**입니다. 로비 RGB 3곡선×12입력=36건, 합성 200곡선의 2~7개 비단위 X 간격·경계·내부 키·바깥 값·무작위 구간=2,091건입니다. 함수 스텁·SDK 대체 함수는 없습니다. 이 결과는 곡선 단독 reader이며, 파라미터 로더·적용 writer·GPU LUT 렌더를 실행한 것이 아닙니다. 음수 출력/1 초과를 이 reader에서 clamp하지 않습니다. 키가 정렬되지 않았거나 X가 중복된 잘못된 데이터의 안전성은 이번 검증 범위 밖입니다.


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
| 정정(2026-10-03, 6차): 위 행의 이름 | 0x7103705fec 실행으로 복원한 이름은 `static_sdw_width` 2048, `static_sdw_mip_level_num` 1, `static_sdw_depth_format_name` Depth_32, `static_sdw_shadow_map_format_name` R32_G32_float 이다. **정적 깊이 그림자**(`create_static_depth_shadow` true) 설정이고, 동적 깊이 그림자 텍스처는 `depth_shadow_tex_width/height` = **1024 × 1024** 다 [실행]+[데이터] |
| projection_shadow_num | 2 |
| create_masked_light / create_reflection | true / true |
| create_dof / create_bloom / create_hdr / create_color_correction | 모두 true |
| create_ssocclusion / create_decal / create_shadow_mask / create_filter_aa / create_light_map / create_light_probe | 모두 false |
| linear_lighting_enable | true(선형 공간 조명) |
| 출력 크기(해시 0x7cb9885b / 0xa2d5f3e7) | 1280 / 720 (6차: `base_reso_width` / `base_reso_height`) |

### 3.0 gsys 장면 설정 객체와 그림자 설정 (6차) [실행 + 데이터 + 판독]

장면+0x1c0 은 gsys 장면 설정 객체다. 0x71036c971c 가 `*(장면+0x1c0)` 의 +0xec0/+0xee0, +0x17a0/+0x17c0 을 읽어 렌더 상태에 복사하고, 0x7103751a78 이 +0x16a0 을 읽는다 [판독]. 이 객체의 생성자 0x7103705fec 를 unicorn 으로 실행해(`web/tools/r6_gfx_stage_cfgparams.py`) 값 오프셋마다 이름 해시를 얻었고, 생성자가 인라인으로 계산하는 crc32b 사슬을 추적해 이름을 복원했다. 복원한 이름은 zlib.crc32 로 다시 계산해 해시가 같은 것만 썼다. 결과는 `analysis/r6_gfx_stage/gsys_cfg_params.tsv`(고유 이름 약 175개, 해시가 남은 칸 일부)다.

- 스텁: 하위 객체 생성 등 bl 10종은 즉시 반환, 이름 문자열 형식화 0x7100f93144 는 파이썬 C 형식 변환으로 대체했다. 정적 SafeString 끝 0 쓰기는 전역이 초기화되지 않았으면 건너뛰었다. 실행은 0x710370c15c 에서 멈췄고(정적 초기화 안 된 전역 쓰기), 아래 값은 모두 그 앞에서 기록된 것이다.
- 값은 `gsys.bgmsconf` 의 `Common` 덤프다. 대전·로비가 `Common` 을 쓴다는 것은 여전히 [추정]이다.

| 값 오프셋 | 이름 | Common |
|---|---|---|
| +0x850 / +0x890 / +0x8b0 / +0x8d0 | `bloom` / `auto_exposure` / `hdr` / `color_correction` (패스 켜기 플래그, 0x7103744058 이 읽음) | 덤프에 없음(생성자 값) |
| +0xf00 | `linear_lighting_enable` | true |
| +0x16a0 | `depth_shadow_pcf_offset` | 0.5 (0x7103751a78 이 `0.5 / 텍스처 폭`, `0.5 / 높이` 로 UV 오프셋을 만든다 [판독]) |
| +0x16c0 / +0x16e0 | `depth_shadow_tex_width` / `_height` | 1024 / 1024 |
| +0x1700 | `depth_shadow_enable_bb_clip` | true |
| +0x1780 | `depth_shadow_near_far_margin` | 0.0 |
| +0x17a0 / +0x17c0 | `depth_shadow_polygon_offset` / `depth_shadow_polygon_scale` (이름은 후보 사전 대조로 복원) | 0.3 / 5.0 — 0x71036c971c 가 캐스케이드 4칸의 렌더 상태(+0x4e0..+0x4fc)에 그대로 복사 [판독] |
| +0x17e0..+0x1840 | `depth_shadow_refvalue_threshold_0..3` | −1 |
| +0x18c0..+0x1920 | `depth_shadow_near_0_0..3` | 1.5, 20, 250, 16 |
| (덤프) | `depth_shadow_cascade_num_0` / `depth_shadow_far_0` | 2 / 60 |
| +0x1480 / +0x14c0 / +0x1510 | `static_sdw_width` / `static_sdw_depth_format_name` / `static_sdw_shadow_map_format_name` | 2048 / Depth_32 / R32_G32_float |
| +0x19c0 | `color_correction_3dbake_texwidth` | 8 (색 보정 3D LUT 한 변) |
| +0x1aa0..+0x1b60 | `cube_map_max_tex_num` 2, `cube_map_max_tex_width` 256, `cube_map_create_mip_level_num` 15, `cubemap_dynamic_range` 1024.0, `cubemap_hdr_compose_power` 4.0 | |

웹에 필요한 그림자 값: 캐스케이드 2, 1024², 깊이 바이어스(polygon offset 0.3, scale 5.0 — 원본 그래픽 API 의 polygon offset 의미 그대로), PCF 오프셋 0.5 텍셀. near_0_i·far_0 를 캐스케이드 경계 [1.5, 20], [20, 60] 으로 읽는 것과 PCF 커널 모양(샘플 수·가중)은 아직 [추정]/[미확정]이다(그림자 프리패스 셰이더 미판독).

패스 순서(재질 셰이더 입력에서 역산) [추정]: 깊이 그림자(캐스케이드 2) → Z 프리패스 → 그림자 프리패스(화면 공간, `cGSysShadowPrePass` .xy) → 불투명 포워드(Hoian_UBER, 베이크·SH·동적광·안개 포함) → 반투명(`gsys_render_state_mode translucent`, `gsys_pass seal` 등) → 후처리(블룸 → DOF → `HDRCompose`). 후처리 셰이더는 `Hoian_ProcHDRCompose.sharcb` 프로그램 `HDRCompose`(매크로 HDR_BLOOM_COMPOSE 0..2, HDR_COLOR_CORRECTION 0..1, HDR_TONEMAPPING 0..5, HDR_GAMMA 0..2, VIGNETTE_SHAPE 0..2)이고 324조합 역번역은 `analysis/gfx4/sharc/hdrcompose/` 에 있다. 블룸·DOF 와 HDRCompose 사이의 패스 순서는 여전히 [추정]이고, **HDRCompose 안의 순서와 식은 5차에서 판독했다(§3.1)**.

정정(2026-10-03): 이전 판의 "어느 변형을 쓰는지·식 판독은 [미확정]"은 §3.1~§3.3 으로 대부분 해소되었다. 남은 것은 감마 변형과 블룸 합성 방식의 런타임 값(§3.2)이다.

### 3.1 HDRCompose 픽셀 식 [판독: 역번역]

정점 셰이더(모든 변형 공통): `uv = (u·C0.x + v·C0.z + C1.x, u·C0.y + v·C0.w + C1.y)`, `exposure = texture(cExposureTexture, (0,0)).w · cParam.x`. CPU 는 `cTexCoordCoeff0 = (1, −0, 0, 1)`, `cTexCoordCoeff1 = (0,0,0,0)` 을 넣는다(0x7101120eac, 즉시값 0x800000003f800000 / 0x3f80000000000000) [판독].

픽셀 순서(변형 BLOOM 1·CC 1·TONE 4·GAMMA 1·VIG 1 = variation #202 에서 확인):

```glsl
c  = HDR.rgb · exposure                       // BLOOM 0
c  = HDR.rgb · exposure + Bloom.rgb           // BLOOM 1 (fma)
c  = x + Bloom.rgb·(1 − clamp(dot(x, Y)))     // BLOOM 2, x = HDR·exposure, Y = (0.2989, 0.5866, 0.1144)
c  = tonemap(c)                               // 아래 6종
c  = texture3D(cColorCorrectionTable, c·CC.x + CC.y).rgb     // CC 1, CC = cColorCorrectionCoeff.xy
c  = mix(c, cVignetteColor.rgb, v·cVignetteColor.w)          // VIG 1/2
c  = pow(|c|, 1/2.2) (GAMMA 1) | pow(|c|, 2.2) (GAMMA 2) | 그대로 (GAMMA 0)
out.a = HDR.a
```

| HDR_TONEMAPPING | 채널별 식 (x = 위 c) |
|---|---|
| 0 | `x` (노출만) |
| 1 | `1 − exp(−x)` (`exp2(x·−1.44269502)`) |
| 2 | `x / (x + 1)` |
| 3 | `pow(abs(x·(6.2x + 0.5) / (x·(6.2x + 1.7) + 0.06)), 2.2)` |
| **4** | `L = dot(x, (0.2989, 0.5866, 0.1144))`, `t = 1 − exp(−L)`, `y = x·t/L`, `out = clamp(y + ((1 − exp(−x)) − y)·t², 0, 1)` — 휘도 기준 지수 곡선과 채널별 지수 곡선을 t² 로 섞음 |
| 5 | S 곡선: `x < cSCurveCrossOver.x` 이면 Toe, 아니면 Shoulder 계수로 `(x·a + b) / (x·c + d)` (R: a=.x b=.z c=.y d=.w, G·B 도 같은 배치). 계수는 HDR 객체 +0x28~+0x38 에서 CPU 가 계산(0x7101120eac, `tone == 5` 분기) |

비네트: VIG 1 = 타원 `sqrt(((2u − P.z − 1)/P.x·0.8716)² + ((2v − P.w − 1)·0.5625/P.y·0.8716)²)`, VIG 2 = 사각 `max(|…|, |…|)`, 둘 다 `v = clamp((r + cParam.z)·k − k)`, k = `1/max(cParam.w·0.25, 0.001)`(VIG 1) 또는 `1/max(cParam.w, 0.001)`(VIG 2), P = `cVignetteParam`. CPU 값: `cVignetteParam` = 게임 HDR 문맥 객체(+0x300) +0x1c/+0x14, `cVignetteColor` = +0x24/+0x2c, `cParam.zw` = +0xc/+0x10 [판독: 0x7101120eac]. 로비에서 비네트가 켜지는지(+8)·값은 [미확정].

### 3.2 변형 선택과 플래그 [판독 + 실행]

0x710112215c(비네트 객체, 뷰, 인자)가 매크로 값을 고르고 sharc 매크로 표의 자리값(+0x30 배열 0x28 B 간격, +0x20 u16)으로 변형 번호를 만든다. HDR 객체 = 활성 env `+0x2ae0`.

```
BLOOM = (블룸 텍스처 있음 && HDR+0x48 bit0) ? 1 + HDR+0x1c : 0
CC    = (색 보정 LUT 있음 && bit1) ? 1 : 0
TONE  = HDR+0x18
GAMMA = bit7 ? 2 : (bit2 ? 1 : 0)
VIG   = 비네트+8 ? (비네트+0x34 == 1 ? 2 : 비네트+0x34 == 0 ? 1 : 0) : 0
번호  = Σ 값×자리값   (sharc 순서 BLOOM 3, CC 2, TONE 6, GAMMA 3, VIG 3)
```

플래그 기록 0x7103744058(gsys 장면+0x2828 의 env 하위, 호출 0x71036c99b8 단계 5):

| 비트 | 조건 |
|---|---|
| bit0 블룸 | 설정(+8)+0x8b0 켜짐 · +0x288 bit0 꺼짐 · 설정+0x850 켜짐 · 블룸 객체(+0x290 = 장면+0x2ab8) +0x7d8(Enable) · +8 ≠ 0 · +0x438 ∈ {1, 2} · +0x280 bit0 |
| +0x1c | bit0 이 설 때만 `블룸+0x438 == 2` 로 기록 → BLOOM 1(가산) 또는 2(휘도 가중) |
| bit1 색 보정 | 색 보정 객체(+0x2b0 = 장면+0x2ad8) 있음 · 설정+0x8d0 · 객체+0x218(ColorGrading.Enable) · 그 뒤 `(+0x2410 >> 3) & 2` |
| bit2 감마 1 | 인자 bit0 = `(장면+0x1c0)+0xf00 && !(장면+0x523c bit4)` 이면 1, 아니면 `장면+0x5239 bit4`. bit3 은 항상 0. bit7(감마 2)을 쓰는 코드는 찾지 못함 |
| bit4 노출 텍스처 | 0x71037441e4: 자동 노출 객체(+0x2a8 = 장면+0x2ad0) 있음 · 설정+0x890 · 객체+0x48(AutoExpEnable) 이면 켜고 뷰별 자동 노출 결과 텍스처를 연결, 아니면 끔 |
| bit5 수동 노출 | 0x71011554a4: `HDRExposure.ExposureType == ManualExposure(0)` 이면 켬 + AutoExpEnable = 0, AutoExposure 면 끔 + AutoExpEnable = 1 |

**톤매핑 4**: HDR+0x18 에 쓰는 명령은 0x710121c240 의 `str w10, [x9, #0x18]`(w10 = 4) 하나뿐이다(env+0x2ae0 경유 전수 검색 `web/tools/r5_gfx_stage_ptrfield.py`, gsys 쪽 +0x2b8 경유 0건). 이 함수는 장면 gfx 클래스 6종(vtable 0x710556ea00 계열, 슬롯 30)이 공유하고, 같은 자리에서 게임 HDRCompose 그리기 콜백 0x710112c604 를 env+0x2af8 에 설치한다. 0x710112c604 를 가리키는 GOT 0x7105794448 을 쓰는 다른 코드는 없다(xref 의 다른 두 곳은 같은 하위 12비트 오탐). 따라서 게임 HDRCompose 경로에서 톤매핑은 4번이다 [판독].

로비 런타임 값: BLOOM 은 블룸 객체 +0x438(데이터 RenderingDay 에 없음, agl bloom 쪽 값)에 따라 1 또는 2, GAMMA 는 출력 버퍼 설정 비트(+0x1c0+0xf00, +0x523c, +0x5239)에 따라 0 또는 1 이다 — 둘 다 [미확정]. CC 는 ColorGrading.Enable = true 이고 LUT 생성 비트(+0x2410 bit4) 출처가 [미확정].

**6차 갱신 (2026-10-03)**

- **블룸 합성 = 가산(BLOOM 1)** [판독+데이터]. 블룸 객체(장면+0x2ab8)의 파라미터 묶음은 객체+0x30 에서 시작한다(0x71036ecd4c 가 `x19+0x30` 을 0x71036eb47c 에 넘김). 0x71036eb47c 는 이름 CRC 를 인라인으로 계산해 파라미터를 만든다. 묶음+0x3f0 이 `finalblend`(값 +0x408, 생성자 기본 1)이고, 묶음+0x0 이 `threshhold`(값 +0x18) 등이다. 따라서 블룸+0x438 = 묶음+0x408 = **`finalblend`**, 블룸+0x48 = `threshhold`, +0x68 = `threshold_range`, +0x88 = `intensity` 로 0x7102b699c0 의 기록 위치와 맞다. 로비 genv(VSLobby_Day)에는 블룸 객체가 없고 기본 env `defaultday.baglblm` 의 `finalblend`(해시 0x359a9772) = **1** 이다. RenderingDay 적용 0x7102b699c0 과 env 접근자(Bloom 0x08~0x1b)는 이 칸을 쓰지 않는다(0x7101050000~0x7101053000 범위 +0x438/+0x408 접근 0건). 0x7103744058 은 `+0x1c = (finalblend == 2)` 를 쓰므로 BLOOM = 1 + 0 = **1(`HDR·노출 + Bloom`)** 이다. 비트 0 의 나머지 조건(장면+0x280 bit0, 블룸+8 뷰 마스크)은 런타임 값이라 확인하지 못했다.
- **CC = 1** [판독]. ColorCorrection 객체 생성자 0x71035d9450 이 +0x2410 = 0 을 쓴 뒤 0x71035db354(곡선 초기화)를 불러 `+0x2410 |= 0x12`(bit1·bit4)를 켠다. +0x2410 을 쓰는 다른 곳(0x71035dc218 LUT 갱신 `&= ~2`, 0x71035de4a8·0x71035df17c·0x710104bf04·0x710115567c `|= 2`, 0x71035df17c `|= 0xa`)은 bit4 를 끄지 않는다(`r5_gfx_stage_bitscan.py` 전수). 따라서 색 보정 객체가 있고 `color_correction` 설정(+0x8d0)·ColorGrading.Enable(+0x218, 로비 true)이 켜져 있으면 CC = 1 이다.
- **7차 곡선 reader 해소** [실행]+[판독]: `Hermit2D` 번호7 = 0x710358CFE0, Data6의 `(X,Y,정규 접선)`과 8점 표본값은 §2.2.1입니다. 다른 연산 종류·GPU 셰이더·최종 LUT 내용은 계속 미확정입니다.
- **색 보정 LUT 는 GPU 에서 만든다** [판독]. 0x71035dc218 은 `+0x218 && (+0x2410 & 6)` 일 때 bit1 을 지우고, 12칸의 연산 목록(+0x258 색인, 종류 0~9)을 UBO 로 만든다. 종류 6 은 곡선 4개(+0xfc8/+0xfe0/+0xff8/+0x1010)를 `t = i/7`(i = 0..7) 8점으로 표본화하고, 다른 종류는 +0x960 의 0x28 B 칸(vec4 2개)을 그대로 넣는다. 그 뒤 렌더 타깃(한 변 `color_correction_3dbake_texwidth` = 8)에 그린다. LUT 값 자체는 agl 색 보정 셰이더 역번역과 연산 목록 대응이 필요해 [미확정]이다.
- **GAMMA** [판독, 일부 미확정]. 0x71036c99b8 의 인자 = `linear_lighting_enable(장면+0x1c0 +0xf00) ? (장면+0x523c bit4 ? 장면+0x5239 bit4 : 1) : 장면+0x5239 bit4`. 장면+0x1c0 이 gsys 장면 설정 객체이고 +0xf00 이 `linear_lighting_enable`(Common true)임은 생성자 실행으로 확인했다(§3.0). 장면+0x523c bit4 와 +0x5239 bit4(= 장면+0x4918 하위 객체 +0x924/+0x921)를 쓰는 명령은 gsys 범위 직접 오프셋·비트 쓰기 스캔에서 찾지 못했다. bit4 가 꺼져 있으면 GAMMA 1(`pow(c, 1/2.2)`)이다.

원본 실행 [실행]: `web/tools/r5_gfx_stage_emu.py` D·E — 0x710112215c 2000건(플래그 8비트·톤 0..5·블룸 종류·텍스처 유무·비네트 무작위)과 0x7103744058 2000건(설정·객체 유무·+0x438 0..4 무작위)이 판독식 재구현과 전부 일치. 스텁 없음(0x7103744058 의 자동 노출 배열 +0x2a8 은 0 으로 두어 뒤쪽 버퍼 교대 루프는 실행 안 함).

### 3.3 노출 [판독]

0x7101120eac(HDRCompose 그리기):

```
exposure_uniform = (HDR+0x48 bit5) ? exp2f(*(HDR+0x10)[view·0x128] + 0x110) : 1.0     // cParam.x, exp2f = PLT 0x7103e9c270(GOT exp2f)
exposure_tex     = (bit4) ? 자동 노출 결과(뷰별 +0x1e8 + 현재 버퍼×0x3e0) : 기본 텍스처 *(0x7105999230)+0x40
최종 배율        = exposure_tex(0,0).w × exposure_uniform
```

- `+0x110` 에는 0x71011554a4 가 `HDRExposure.ManualExposure.Value` 를 그대로 쓴다(env 접근자 ID 0x1d `HDRComposeExposure` 도 같은 칸) → **값은 EV(2의 지수)** 다.
- 기본 텍스처 표(0x7105723f20, 29개)는 싱글턴 +8 부터 8 B 간격으로 저장되므로(0x7103610a80 `str x21, [this + i·8 + 8]`) +0x40 = 7번 `White2D`, 채움 값 0xFFFFFFFF(분기표 0x7104ac036e) → w = 1 [판독].
- 로비(ManualExposure, Value 1.0): 배율 = 1 × 2^1 = **2.0**. 정정(2026-10-03): §9 의 "`toneMappingExposure 1`" 은 틀림 — 2.0 이다.
- 0x71013751d0(0x350 B 구조를 만들어 memcpy, 용도 [미확정])도 같은 식(수동이면 exp2f(+0x110), 아니면 1.0)을 0x350 B 구조 +0x270 에 넣는다 [판독].

### 3.4 블룸 파라미터 [판독]

RenderingDay `PostEffect.Bloom`(game::gfx::parameter::Bloom, 방문 0x710118e90c, 생성자 0x710118dbc4 기본값 — `param_reflect.py`): Enable +0x9c (true), Threshold +0x94 (4.0), ThresholdRange +0x98 (1.0), Intensity +0x60 (1.0), EnableClampedLuminance +0x9d (true), ClampedLuminance +0x30 (5.0), ComposeColor +0x34 (1.0…), Layer8x8Color +0x84 (0.953…), Layer16x16Color +0x64 (0.816…), Layer32x32Color +0x74 (0.094…), EnableDepthScaling +0x9f (false), DepthOffset 계열 false.

적용 0x7102b699c0 → env+0x2ab8 객체: +0x7d8 = Enable, +0x48 = Threshold, +0x68 = ThresholdRange, +0x88 = Intensity, +0x500 = EnableClampedLuminance, +0x5a0 = ClampedLuminance 칸, +0xa8..+0xb4 = ComposeColor, +0x378.., +0x3a0.., +0x3c8.. = 층 색 [판독]. 특이점: +0x5a0 은 디컴파일상 `B.ClampedLuminance + (A.Intensity − B.ClampedLuminance)·t` 로 다른 필드를 섞는다 — 정적 장면(t 출처 [미확정])에서의 영향은 [미확정]이며 원본 그대로 둔다.

로비 RenderingDay 에 Bloom 블록이 없으므로 기본값을 쓴다 [데이터+판독]. 블룸 셰이더(agl `bloom_mask`/`bloom_gaussian`/`bloom_reduce`/`bloom_compose`)의 식은 [미확정].

## 4. 렌더링 파라미터 적용 — 0x7102b5fe88 [판독]

```
apply(t, A, env, B):            // 값 = lerp(B값, A값, t)  (일부는 t 를 [0,∞) 로 자름)
  0x7102b5ff94  주 광원: env 첫 DirectionalLight(타입 ID *0x7105999180, RTTI 확인) 가 있으면
                  0x7102b607c4  DL+0x128 DiffuseColor = MainLight.Color ; DL+0x1a0 Intensity = MainLight.Intens
                  0x7102b60ea0  DL+0x1c0 Direction = (−sin(Lon)·cos(Lat), −sin(Lat), −cos(Lon)·cos(Lat))   // 도 → ×0.017453292
                  0x7102b6157c  MainLight 색·세기를 이벤트(vt 0x71055648b0)로 수신자들에게 전달
  0x7102b61c20  DepthFog·OverlookDepthFog 보간(env 의 agl Fog 객체가 있을 때만) → 0x71010be03c(안개 관리자 *0x7105812ac0 의 env별 레코드)   ← 5차 정정
  0x7102b63334  HeightFog → env 의 두 번째 agl Fog 객체: Start(+0x128), End(+0x148), Color(+0x188, t≥0 보간)   ← 5차 판독
  0x7102b63ce4  안개: DepthFog·HeightFog·RadialFog → 구조체(아래)를 이벤트(vt 0x710555da58, 키 0x7105812ac8)로 전달
  0x7102b66c54  env+0x2800 객체(+0x5ac/+0x5b0/+0x440/+0x360/+0x364/+0x400/+0x404/+0x380/+0x384/+0x420)  (미판독)
  0x7102b67bc4  BakeShadow → BlitzUBO0 [36]/[37] (§6.3)
  (vt+0x88 == 1) 0x7102b68ef4  env+0x2ac8 객체(미판독)
  0x7102b699c0  Bloom → env+0x2ab8 블룸 객체(§3.4)   ← 5차 판독
  0x71011554a4  HDRExposure: 노출 종류 → HDR 객체 bit5·+0x10→+0x110, 자동 노출 Enable(§3.2·§3.3)   ← 5차 판독
  0x710115567c  ColorGrading → env+0x2ad8 객체(+0x218 = Enable, 곡선 R/G/B 점 복사, +0x2410 |= 2)   ← 5차 판독(일부)
  0x7102b60200  (미판독)
```

6차 판독(2026-10-03) — 남은 적용 함수 세 개 [판독, 구조체 이름은 일부 추정]:

- **0x7102b66c54**: RenderingDay A/B 의 vt+0x80 하위 구조체를 읽어 env+0x2800 객체에 쓴다 — +0x5ac/+0x5b0(같은 값 두 칸), +0x440(구조체 +0x34 보간), +0x360/+0x364, +0x400/+0x404, +0x380, +0x420(구조체 +0x38 보간). env+0x2800 객체와 하위 구조체 이름은 [미확정] (필드 수·형태로는 그림자 계열로 보임 [추정]).
- **0x7102b68ef4**(vt+0x88 == 1 일 때만): vt+0x90 하위 구조체의 bool(+0x40, 플래그 +0x44), f32 +0x38(+0x41), +0x3c(+0x42), +0x30(+0x43)을 env+0x2ac8 객체 +0x1a8(bool, t ≈ 0 일 때만), +0x268(= max(0, 보간)), +0x1e8(보간) 등에 쓰고, 값이 바뀌면 0x71035e553c(갱신 표시)를 부른다. t ≈ 0 이면 +2000(0x7d0)을 0 으로 지운다. 하위 구조체는 방문 함수 0x71011dcd8c(`ShadowPPBlur` +0x50, `DynamicShadowMap` +0x48 을 담는 묶음) 쪽으로 보이나 어느 것인지는 [미확정].
- **0x7102b60200**: vt+0xc8 하위 구조체의 vec3 +0x30(플래그 +0x40)과 f32 +0x3c(플래그 +0x41)를 A/B 보간해 이벤트(키 0x7105810450, vtable 0x7105559ec0)로 `{vec3, vec3, f32}` 를 보낸다. RenderingDay 에서 vec3+f32 묶음은 `GlobalWind`(RenderingDay +0x58, 플래그 +0x89)이고 env 접근자에 `GlobalWindDir`·`GlobalWindIntens` 가 있어 GlobalWind {Dir, Intens} 로 본다 [추정: 형태·이름 대응]. 로비 RenderingDay 에는 GlobalWind 블록이 없다 [데이터].

정정(2026-10-03): 이전 판은 0x7102b61c20 을 "DynamicLight(Grid) → GridOffset/GridSize 기록"으로 적었으나 틀렸다. 이 함수가 읽는 vt+0x78 은 Fog 파라미터(0x7102b63ce4 에 넘기는 것과 같은 객체)이고, +0x30 포인터(플래그 +0x50) = DepthFog, +0x40(플래그 +0x51) = OverlookDepthFog 이다(Fog 리플렉션 0x71011a41fc: DepthFog/OverlookDepthFog/HeightFog +0x38/RadialFog +0x48). 레코드 = {ScatteringCoeff, Start, End, Color.rgba} ×2. env 의 첫 agl Fog 객체를 확인하는 타입 ID 전역 0x7105999168 은 `"Fog"` 등록(0x71035d5814)이다. 안개 관리자 0x71010bd494 가 이 레코드를 `t = *(0x7105812ac0+0x318)`(Overlook 비율)로 섞어 env 첫 agl Fog 객체에 Start(+0x128)·End(+0x148)·Color(+0x188)를 쓰고 같은 형식의 안개 이벤트를 다시 보낸다 [판독]. DynamicLight.GridSize 를 쓰는 코드는 다시 [미확정]이다.

agl::env 타입 ID 전역(0x71035d9320, 0x71035d57d0 등록) [판독]: 0x7105999168 Fog, 0x7105999170 AmbientLight, 0x7105999178 HemisphereLight, 0x7105999180 DirectionalLight, 0x7105999188 PointLight. agl Fog 파라미터 값 위치는 DirectionalLight 와 같은 규칙(값 = 파라미터 객체 +0x18, 첫 값 +0x128)으로 Start +0x128, End +0x148, Damp +0x168, Color +0x188, Direction +0x1b0 이다(Start/End/Color 는 위 두 기록자로 확인 [판독], Damp/Direction 위치는 [추정]). 로비에서 Damp·Direction 은 genv 값(FogTPS 1.0·(0,0,−1), Fog_Y0 1.0·(0,−1,0))이 남는다 [데이터].

- 호출자 0x7102b5c250(→0x7102b5c4a8). t 의 출처(시간대 전환 진행도)는 [미확정]. 로비는 낮 세트 하나라 A=B 로 두면 됩니다.
- 안개 구조체(0x7102b63ce4, 판독 일부): `DepthColor.rgba`, `−Start/(End−Start)`, `1/(End−Start)`(|End−Start| ≥ 0.01 로 보정), `ScatteringCoeff`, RadialFog 값들(+0x50 은 `1/exp2(2x)`), `HeightColor.rgba`, `normalize(HeightFog.Dir)`, `1/(End−Start)`, `−Start/(End−Start)`. 이것이 Env UBO 의 어느 칸으로 가는지(수신자)는 [미확정] — §5.5 의 셰이더 식과 형태가 맞습니다.
- 5차: 이벤트 객체 오프셋(0x7102b63ce4 지역 변수 배치 + 수신자 읽기로 대조) [판독]: +0x18 DepthFog.Color(rgba), +0x28 −Start/(End−Start), +0x2c 1/(End−Start), +0x30 ScatteringCoeff, +0x34 RadialFog(+0x30 필드), +0x38..+0x47 vec4(0x71010bb2b0 계열 값), +0x48 RadialFog(+0x48), +0x4c RadialFog(+0x50), +0x50 1/exp2(2·RadialFog(+0x50)), +0x54 RadialFog(+0x4c), +0x58 HeightFog.Color, +0x68..+0x70 normalize(HeightFog.Dir), +0x74 −Start/(End−Start), +0x78 1/(End−Start)(높이), +0x7c/+0x7d/+0x7e 블록 유효 플래그. RadialFog 필드 이름은 [미확정] (로비 RenderingDay `RadialFog: {}` → 기본값).
- **6차: RadialFog 필드 이름·기본값 [판독]**. 방문 함수 0x71011d4ddc(문자열 `game__gfx__parameter__RadialFog` 참조 0x71011d5cd8 의 클래스, vtable 0x710556a1f0), 생성자 0x71011d4d04:

| 오프셋 | 이름 | 기본값 | 안개 이벤트 칸 |
|---|---|---|---|
| +0x30 | BlendFactor | 0.0 | +0x34 → BlitzUBO0 [53].w |
| +0x34 | Color (vec4) | (1.0, 0.95, 0.7, 1.0) | (+0x38 vec4 계산에 쓰이는지는 [미확정] — 0x71010bb2b0 은 MainLight 쪽 값) |
| +0x44 | Intens | 1.0 | |
| +0x48 | LobeCtrl | 1.0 | +0x48 → [54].x |
| +0x4c | ShadowInfluence | 0.0 | +0x54 → [54].w |
| +0x50 | SizeCtrl | 5.0 | +0x4c → [54].y, +0x50 = 1/exp2(2·SizeCtrl) → [54].z |

설정됨 플래그는 +0x54 LobeCtrl, +0x55 SizeCtrl, +0x56 ShadowInfluence, +0x57 Color, +0x58 Intens, +0x59 BlendFactor 다. 로비는 빈 블록이라 BlendFactor = 0 → §5.5 의 `fogC = mix(Env[10].rgb, scat, [53].w)` 에서 산란 항이 꺼진다 [판독+데이터].
- 수신자(키 0x7105812ac8 등록 전수: GOT 0x71057932a0) [판독]: ① SceneCommonUBOHolder 0x7101185af4 → BlitzUBO0 [53]~[55] (§5.5), ② 조명 UBO 객체 0x710113492c 의 콜백 0x7101134e3c → 448 B UBO(§5.5 표), ③ 0x7101376404 → 0x71013751d0 이 만드는 0x350 B 구조(용도 [미확정]) +0x200~+0x268, ④ 0x7101162548(+0x2c4..+0x2d0 ← 이벤트 +0x28/+0x2c/+0x30/+0x24), ⑤ 0x7101152d40 등록(콜백 미확인). 보내는 쪽은 0x7102b63ce4 와 안개 관리자 0x71010bd6cc 둘이다.
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

**r8 정정(2026-10-03)**: 원본344af54 모듈31→3cf9ba0→3ccfcd4→3ccadd0/3ccaf2c로 DataType3/4가 bake0/bake1을 선택해 실제 텍스처 핸들2개와 gsys_bake_st0/1 vec4를 기록함을 확인했다 [실행]+[판독]. [bake_material_binding.md §3~§11](bake_material_binding.md). 합성32/32 핸들·uniform비트일치, 실제 로비 GPU는 미실행.

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

Env[10] = DepthFog 색(a = 최대 농도 A), Env[11].w/[12].x = −Start/(End−Start), 1/(End−Start), Env[13] = HeightFog 색, Env[14].xyz = HeightFog 방향 [추정: §4 안개 구조체의 값 형태와 일치, 실제 복사 코드 미판독]. BlitzUBO0 [53]~[55]의 기록자는 [미확정] (후보 0x7102c5a3c8 이 holder+0x13e8 기록 — 다른 에이전트가 디컴파일 `analysis/decomp/phys4/p4_world_ctrl.c` 에 둠).

정정(2026-10-03): BlitzUBO0 [53]~[55] 기록자는 0x7102c5a3c8(접지 판정, 무관)이 아니라 SceneCommonUBOHolder 의 안개 이벤트 콜백 **0x7101185af4**(등록 0x7101183ab8 안 0x71011857a4)다 [판독]. 멤버 값 주소 → UBO 칸은 BlitzUBO0 레이아웃(원본 실행, `analysis/render/blitzubo0_layout.tsv`, 멤버 기준 = holder+0x2b0, 값 = 멤버+0x38)으로 대응시켰다:

| BlitzUBO0 | holder 값 주소 | 값 (이벤트 오프셋, §4) | 조건 |
|---|---|---|---|
| [53] | +0x13e8 | (+0x30 ScatteringCoeff, +0x2c 1/(End−Start), +0x30 ScatteringCoeff, +0x34 RadialFog 값) | 이벤트 +0x7c |
| [54] | +0x1430 | 이벤트 +0x48..+0x57 = (RadialFog(+0x48), RadialFog(+0x50), 1/exp2(2·RadialFog(+0x50)), RadialFog(+0x4c)) | +0x7d |
| [55] | +0x1478 | 이벤트 +0x38..+0x47 (산란 색, vec3 칸) | +0x7d |

셰이더 판독과 맞춰 보면 `[53].x` = 산란 계수로 `exp(−s·ScatteringCoeff)` 형태가 되고(로비 0.3125), `[53].w`·`[54]`·`[55]` 는 RadialFog 쪽 값이다. RadialFog 필드 이름·기본값(로비는 빈 블록)은 [미확정] → 웹은 `[53].w = 0` 이면 산란 색 항이 꺼지므로 기본값 확인 전까지 산란 항을 끄는 것이 안전하다 [추정].

Env UBO 쪽(5차): Env[10..15] 의 원천은 env 의 agl `Fog` 두 객체다 — 첫 객체(FogTPS)에 안개 관리자 0x71010bd494 가 DepthFog Start/End/Color 를, 두 번째(Fog_Y0)에 0x7102b63334 가 HeightFog Start/End/Color 를 쓴다(§4) [판독]. agl Fog → gsys `gsys_environment`(512 B) 칸으로 옮기는 코드는 찾지 못했다 [미확정]. 같은 이벤트를 받는 조명 UBO(0x710113492c, 448 B, 레이아웃 원본 실행 `analysis/r5_gfx_stage/lightubo_layout.tsv`)는 Env 와 다른 블록이다:

| 조명 UBO(448 B) 칸 | 값 | 출처 |
|---|---|---|
| [10..16] (vec4[7]) | SH cAr..cC | SH 이벤트 콜백 0x7101135000 |
| [21] | DepthFog.Color (이벤트 +0x18) | 안개 콜백 0x7101134e3c |
| [22] | (−S/(E−S), 1/(E−S), ScatteringCoeff, RadialFog 값) (이벤트 +0x28) | 〃 |
| [23] | 이벤트 +0x38 vec4 | 〃 |
| [24] | 이벤트 +0x48 vec4 | 〃 |

이 448 B 블록을 어느 셰이더가 쓰는지(맵 재질의 Env 는 아님 — SH 가 [25..31] 이 아니라 [10..16])는 [미확정]이다.

#### 5.5.1 Env UBO(`gsys_environment`, 512 B) 칸 대응 (6차) [실행 + 판독]

정정(2026-10-03): 위의 "Env[10..15] = DepthFog/HeightFog [추정: 복사 코드 미판독]"과 "agl Fog → gsys_environment 로 옮기는 코드는 찾지 못했다"는 해소되었다. 뷰 레코드 배열 `*(gsys+0x578)`(0xd0 간격, 0x71036ae130 이 만든다)이 곧 Env UBO 객체이고, 0x71036b35c0(gsys, param = 뷰 번호)이 매 프레임 env 의 agl 광원·안개 객체에서 값을 읽어 멤버에 쓴다.

- **레이아웃 [실행]**: 0x71036ae130 안 레코드 0 선언 구간(0x71036ae468 → 0x71036ae374)을 원본 그대로 실행했다(`web/tools/r6_gfx_stage_envubo_layout.py`, 스텁은 startDeclare 0x71035b78ec 하나 — 표 헤더만 만들어 줌). 멤버 35개, 각 멤버는 16 B 경계에 놓이고 끝 커서 0x200(512 B). 마지막 멤버(종류 0x12 원시 블록)의 바이트 수는 gsys+0x5b4 이고 0x70 으로 두었다(환경광 관리자가 뷰 레코드 +0xa0 에 쓰는 SH 크기와 같음). 결과 `analysis/r6_gfx_stage/envubo_layout.tsv`.
- **기록자 [판독]**: 0x71036b35c0(`analysis/decomp/r6_gfx_stage/c2_envubo.c`). 멤버 i 의 오프셋은 표+12i+4, 종류는 +8 이다. 안개 4개는 0x71036b1300(기준 멤버 11/16/21/26)이 쓴다. 광원·안개 객체는 env 의 agl 타입 ID 색인표(env+0x18/+0x20/+0x30)로 찾고, 객체가 없거나 꺼져 있으면(`+0x58` 바이트 0) 0 또는 (0,0,0,1)을 쓴다.

| Env[] | 멤버 | 값 | 출처 |
|---|---|---|---|
| [0] | 0 | AmbientLight: Intensity(+0x150) × Color(+0x128) | 첫 AmbientLight(타입 ID *0x7105999170) |
| [1], [2] | 1, 2 | HemisphereLight: I(+0x178) × 색(+0x128), I × 색(+0x150) | 첫 HemisphereLight(*0x7105999178) |
| [3].xyz | 3 | Hemisphere 방향(뷰별 배열 +0x1b0) | 〃 |
| [4].xyz / [4].w | 4 / 5 | 첫 DirectionalLight 뷰별 방향(+0x1f8 배열) / Intensity(+0x1a0) | 첫 DirectionalLight(*0x7105999180) = 로비 MainLight |
| **[5]** | 6 | **Intensity × DiffuseColor(+0x128)** — 로비 rgb (6.706, 8.510, 10.0) [재구현 계산], w = 10 × Color.a | 〃 (0x7102b607c4 가 쓴 값) |
| [6] | 7 | Intensity × 둘째 색(+0x150) | 〃 |
| [7].xyz, [8], [9] | 8, 9, 10 | 둘째 DirectionalLight 의 방향(+0x1f8)·I×색(+0x128)·I×색(+0x150) | 둘째 DirectionalLight |
| **[10]** | 11 | 첫 Fog 색(+0x188) — 로비 DepthFog (0.749, 0.765, 0.698, 0.25) | 첫 agl Fog(FogTPS, 0x71010bd494 가 기록) |
| [11].xyz / **[11].w** | 12 / 13 | normalize(Direction +0x1b0) / **−Start/(End−Start)** | 〃 |
| **[12].x** / [12].y | 14 / 15 | **1/(End−Start)**(End = Start 이면 1) / Damp(+0x168) | 〃 |
| **[13]**, [14].xyz, [14].w, [15].x, [15].y | 16~20 | 둘째 Fog 같은 형식 — 로비 HeightFog 색 (0.098, 0.129, 0.141, 0.6875), 방향 genv (0,−1,0), Start 15 / End 90 | 둘째 agl Fog(Fog_Y0, 0x7102b63334 가 기록) |
| [16]~[18], [19]~[21] | 21~30 | 셋째·넷째 Fog(로비 genv 에 없음 → 색 0) | |
| [22].xyz | 31 | Hemisphere +0x198 vec3 | |
| **[23].xyz** | 32 | 첫 DirectionalLight 뷰별 방향(+0x208 배열) — 셰이더가 `L = −Env[23].xyz` 로 씀 | |
| [24].xyz | 33 | 둘째 DirectionalLight +0x208 | |
| **[25]~[31]** | 34 | 뷰 레코드 +0x98 이 가리키는 0x70 B(+0xa0) 복사 = **환경광 관리자 SH cAr..cC**(§5.6). 복사 전에 콜백(+0xa8)을 부른다 | 0x710102a3e8 등록 |

- 안개 값은 두 env 집합 사이에서 뷰 +0x94 비율로 섞는다(`(1−t)·A + t·B`, B 쪽 Fog 가 꺼져 있으면 t = 0). 방향은 섞은 뒤 정규화한다 [판독].
- 따라서 §5.5 셰이더 식의 Env[10..15] 해석(깊이 안개 = 첫 Fog, 높이 안개 = 둘째 Fog, `hf = clamp((−dot(P, dir) − S)/(E − S))·A`)이 원본 코드로 확정된다. 로비 높이 안개 방향 (0,−1,0) 이면 `hf = clamp((P.y − 15)/75)·0.6875`.
- +0x1f8 과 +0x208 두 방향 배열 중 어느 쪽이 월드 좌표인지는 agl DirectionalLight 갱신 코드를 보지 않아 [미확정]이다. 셰이더가 [23] 을 월드 좌표 식(V = camPos − P)에 쓰므로 +0x208 쪽이 월드 방향으로 보인다 [추정].

### 5.6 환경광 SH 의 출처 [판독 + 실행]

```
환경 큐브(캡처) ─ GPU Hoian_Proc IrradianceClearSH(7 MRT 지움)
                └ IrradianceCubeMapAllToSH(CUBE_MAP_WIDTH_INT 8..256, 인스턴스 점 = 면×W×W 텍셀, 가산 혼합)
                   텍셀 방향 d, 색 c(cMipLevel 밉) → 7 타깃에 SH9 원시 계수 ×가중(W = 8 변형 상수: 0.00923·c, 0.01599·d·c, 0.03575·(xy,yz,xz)·c, (0.03096z² − 0.01032)·c, 0.01788·(x²−y²)·c)
리드백(형식 0x2e RGBA32F 또는 0x2b RGBA16F, 프레임 지연 카운터 +0x71c)
  → 0x71010325d4: 7 텍셀 → cAr/cAg/cAb/cBr/cBg/cBb/cC (상수 0.32534343, 0.28175688, 0.07875311, 0.27280876, 0.23625931, 0.13640438, cC.w = 1), 유효 플래그
  → 0x710102c694: 환경광 관리자 객체(+0x3f0) +0x4b8..+0x527 에 저장
  → 0x710102a3e8: env 의 gsys 뷰 레코드(*(env+0x190)+0x578, 0xd0 간격) +0x98 = 그 주소, +0xa0 = 0x70 / NaN 검사(0x7101029e0c) 통과 시 SH 이벤트(키 0x710580e818, 이벤트 +0x18 = 계수 포인터) 송신
  → 수신: 팀색 관리자 0x71011767f8(skyUp = SH(0,1,0), team_color.md §5.3), 조명 UBO 0x7101135000
```

- 대체 경로 0x7101029f6c: 환경광 관리자 +0x5c8 이 켜져 있거나 조건이 맞으면 **SH = 주 광원을 위(0,1,0)에서 비춘 것**으로 만든다 — `0x7101033b78(sh, (0,1,0), 0.1·Intensity·DiffuseColor.rgb, 1)`(방향광 → SH 투영) [판독]. 로비에서 어느 경로가 쓰이는지는 [미확정] (IlluminateEnvMap 캡처가 끝나면 리드백 경로).
- 가중 식: 0x7101033b78 = `k = 4π/n`, Y1 = 0.488603, Y2 = 1.092548, Y20 = 0.315392(3z²−1), Y22 = 0.546274(x²−y²), Y00 = 0.282095 에 위 변환 상수를 곱해 cAr..cC 를 만든다(디스어셈블 결합 순서는 `web/tools/r5_gfx_stage_emu.py` re_dirlight_sh).
- SH 평가 0x7101033dc0 = 채널마다 `max(0, (A3 + ((x·A0 + y·A1) + z·A2)) + (((xy·B0 + yz·B1) + zz·B2) + xz·B3) + (x² − y²)·C)`, 4번째 반환 1.0.
- SH→큐브 역변환 `IrradianceSHToCubeMap`(조사도 큐브)의 상수는 0.429043, 0.743125, **0.866227**(통상 0.886227 와 다름 — 원본 그대로), 0.247708, 1.023328, 0.858086, × `cEnvCubeMapIntensity`·(1/π) [판독: `analysis/r5_gfx_stage/proc/`].
- 원본 실행 [실행]: 0x7101033b78·0x7101033dc0·0x71010325d4(+0x7101034608 텍셀 읽기, half/float 비정규 0 처리 포함)를 각 2000건 무작위 입력으로 실행, 재구현과 비트 일치. 판독 정정 2건: ① 0x7101033b78 의 cB*.w 항은 디컴파일 표기 `((d0·k)·1.092548)·d2` 가 아니라 `d0·((k·1.092548)·d2)`, ② 0x71010325d4 의 [23] 은 디컴파일상 텍스처 6.w 로 보이지만 실제는 텍스처 5.w(0x710103281c). NaN 은 비트 대신 NaN 여부로 비교.
- Env[25..31] 이 위 0x70 B 블록이라는 것은 크기(7×vec4)·형식(cAr..cC)이 맞는 [추정]이다. gsys 가 뷰 레코드 +0x98 을 Env 로 복사하는 코드는 찾지 못했다(memcpy·`str q, #0x190` 패턴 스캔 0건).
- 정정(2026-10-03, 6차): 복사 코드는 0x71036b35c0 끝부분이다. 뷰 레코드 +0x98(포인터)·+0xa0(크기 0x70)을 멤버 34(바이트 0x190 = Env[25])로 4 B씩 복사한다. 따라서 **Env[25..31] = 환경광 관리자 SH** 는 [판독]이다(§5.5.1).

#### 5.6.1 로비가 타는 경로와 SH 값 (6차) [판독]

- 환경광 객체(0x880 B, 0x71010290d0 생성, 0x71010297f0 초기화 `(obj, 크기, 6, 장면 번호, +0x5c8 플래그)`)를 만드는 곳은 여섯 군데다. 이름 "Main" 이 두 곳이다. 하나는 0x71010bf36c(`0x100, 6, 장면 0, 플래그 0`)이고 다른 하나는 0x7102b97874(`0x100, 6, 0, 플래그 1`)다. "Customize"(0x710110d7c4)는 `0x80, 6, 장면 3, 플래그 1`, 0x7102b93a70 의 다섯 개는 플래그 0 이다.
- 장면 gfx 관리자 팩토리 0x7101220208 은 장면 속성 `Scene_DevEnvViewer` 일 때만 0x7102b97f90(vtable 0x7105675998)을 만들고, 그 밖에는 기본 클래스 0x710121b210(vtable 0x710556ea00)을 만든다. 기본 클래스 슬롯 39(0x710121dbc0)가 env 객체(vtable 0x710555dd80)를 만들고, 그 슬롯 20 이 **0x71010bf36c(플래그 0)** 다. 플래그 1 인 "Main"(0x7102b97874, vtable 0x7105675848)은 DevEnvViewer 쪽 코드 묶음(0x7102b97xxx)에 있다. 그러므로 로비의 "Main" 은 **+0x5c8 = 0, 캡처 경로**다 [판독].
- 캡처 경로의 순서(0x710102c694 / 0x7101029f6c / 0x710102ce04):
  1. 0x7101029f6c 는 gsys 의 +0x5c8 객체 준비 조건이 맞으면 먼저 대체 SH(주광 `0.1·Intensity·DiffuseColor` 를 위에서 비춘 방향광 SH)를 만들어 SH 이벤트를 한 번 보낸다.
  2. 이어서 0x71035c1a8c 로 큐브 캡처를 요청한다.
  3. 0x710102ce04 가 `BaseCubeMap`(형식 0x2b RGBA16F, 256×256×6)에 장면을 그린다(0x710103dd08, 인자 4.0·1024.0, 캡처 카메라 = 장면 +0x578.. 복사). env 맵 종류가 Illuminate(+0x2e8 == 1, `game::gfx::EnvMapType` = Normal 0 / Illuminate 1)이면 `BaseCubeMap(ForIlluminate)` 에 0x7101037098(EnvMapIlluminator, IlluminateEnvMap.LightArray)을 그려 BaseCubeMap 으로 되복사한다.
  4. 그 큐브로 프리필터(0x710103921c)와 SH 투영(0x710103289c)을 하고, 리드백 카운터 +0x71c = 1 을 둔다.
  5. 리드백(0x71010325d4)이 끝날 때마다 +1000 카운터를 올린다. `(+0x5c8 ^ 1) < 카운터`, 곧 플래그 0 이면 **두 번째 캡처의 SH 가 최종값**이다. 첫 캡처 뒤에는 +0x608 대리자를 부르고 다시 캡처한다.
- 결론: 로비 하늘 SH 는 **실행 중 장면(맵·하늘 구 `EmissionIntensInEnvMap` 80·Illuminate 광원)을 CapturePos 에서 큐브로 그린 결과**를 투영한 값이다. romfs 에 이 큐브 데이터는 없다(`Model/IlluminateEnvMap.bfres`·`Fld_Emission4EnvMap.bfres` 는 그릴 모델일 뿐이다). CPU 로 다시 계산하려면 큐브 캡처 렌더(맵 재질의 큐브 패스 변형, 베이크 빛, 하늘, Illuminate 광원)를 재현해야 한다. 투영 셰이더·변환 함수는 확보했지만 입력 큐브가 없어 SH 값은 [미확정]이다.
- 팀색에는 영향이 없다: 로비에서는 skyUp 값과 관계없이 Ink/InkBright 가 같다(§1, [team_color.md §5.3](team_color.md) 6차, 원본 실행). SH 값이 남는 곳은 맵 재질 간접광 `SH(N)·diff'`(§5.4)뿐이다.

### 5.7 하늘 구 (SkySphere) [판독 + 데이터]

- `Model/Sky_Daytime00.bfres.zs` 재질 2개 → `gfx4_stage_programs.py` 로 프로그램 확정(불일치 0): `mSky` = 25(불투명, `_e0` 방출 텍스처, 그림자·셰이딩 꺼짐), `mSun` = 5359(반투명, 가산 `src_alpha + one`). 역번역 `analysis/r5_gfx_stage/sky/programs/`.
- mSky: `out.rgb = Emm.rgb·emission_color.rgb·(emission_intensity·emission_intens_not_in_envmap) + albedo_color.rgb`, `out.a = 1`, 안개 없음. 재질 값: emission_intensity 1, emission_color 1, albedo_color (0,0,0).
- mSun: `out.rgb = Alb.rgb·(emission_intensity + 1)`(= ×11), `out.a = clamp(정점 속성 .w)`.
- 0x71010b9088(재질 방문, vtable 0x710555d910)이 Hoian 재질 파라미터를 쓴다: `emission_intens_not_in_envmap = exp2f(SkySphere.ExposureNotInEnvMap)`(호출 쪽 0x71010b81f4 `ldr s0, [x26, #0x4c]` → exp2f), `emission_intens_in_envmap = SkySphere.EmissionIntensInEnvMap`(+0x48), `saturation_in_envmap = SkySphere.SaturationInEnvMap`(+0x60) [판독]. 로비: 2^2.0 = **4.0**, 80, 0.4.
- SkySphere Offset (−15,0,0)·Scale 1.1 이 하늘 액터 변환에 들어가는 코드는 [미확정].

## 6. 베이크 (bkres)

### 6.1 형식 [데이터]

`Bake/Scene/LobbyVersus_Day.bkres.zs` = zstd → SARC(9.7 MB):

| 파일 | 내용 |
|---|---|
| `bkdat.byaml` | `{Version 7, ExternalTexture false, DataElements[]}` |
| `textures.bntx` | `0_bktex0` BC5_UNORM 2299×1777 mip 12 (comp RG01) / `1_bktex0` BC6H_UFLOAT 1532×1184 mip 11 (comp RGB1) |

`DataElements[k] = {BindingSpace 0, DataType, TextureNames[], ModelElements[]}`: DataType **3 = AO/그림자(→ `_b0` cTexBakeAOShadow)**, **4 = 빛(→ `_b1` cTexBakeLight)** [추정: 형식(BC5 2채널 / BC6H HDR)과 셰이더 사용(.xy / .rgb·a·32) 일치]. `ModelElements[] = {Guid, ModelName, OriginalMaterialCount, MaterialElements[]}`, `MaterialElements[] = {MaterialName, OriginalMaterialIndex, TexcoordScale{X,Y}, TexcoordOffset{X,Y}, TextureIndex}`.

**r8 정정(2026-10-03)**: DataType3/4→bake0/bake1, 즉 기존 BFRES 슬롯_b0/_b1의 연결을 원본 등록·소비 식 및32건 원본 실행으로 확정한다 [판독]+[실행]. TexcoordScale/Offset은 vec4(Sx,Sy,Ox,Oy)로 실제 모델 vt158에 전달된다. [bake_material_binding.md §3~§10](bake_material_binding.md).

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
  Ink, InkBright = 선택 팀의 BlitzUBO0 [3]/[4] (팀0), [10]/[11] (팀1), [62]/[63] (팀2)
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
- 6차 [판독]: [22] 값 주소는 holder(`*0x7105818e38`, SceneCommonUBOHolder)+0xcb8..+0xcc4 다. **[22].z(+0xcc0) = 1 / (8 · ⌈S⌉)** 이고 기록자는 0x7102be8aec(ColPaint 쪽, 0x7102be90a4·0x7102be90f0)다. S 는 관리자 `*0x71058a8da0` +0xe0 문자열이 0x7101323040 이 돌려준 객체 +0x2d8 문자열과 같으면 200.0, 다르거나 관리자가 없으면 400.0 이다. 값은 1/1600 또는 1/3200 이 되고, 셰이더는 u 방향 이웃 텍셀 오프셋 `[20].z·[22].z` 로 쓴다(1 단위 = 8 텍셀이라는 도색 해상도와 맞음). holder 생성 0x7101183ab8 은 +0xcc0 = 0 으로 시작한다. **[22].w(+0xcc4)** 를 쓰는 명령은 holder GOT(0x7105791ec8)를 읽는 함수 33개 안에서 0건이다. 멤버 포인터(+0xc80)+0x44 형태 쓰기도 0x7102be8aec·0x7102c1b5a4 에는 없다 → [미확정]. 셰이더는 v 방향에 [22].w 를 쓴다. 비교 문자열의 정체도 [미확정].
- InkUBOParamDay 값: Roughness 0.05, Fresnel 0.015, InkIrradianceAnisotoropy 0.5, InkNormalIntensity 1.8, Thickness {Base 0.95, BaseWall 0.75, Anim {Amplitude 0.015625, WavePeriod 0.03125}}, Mottari {Base 1.75, Anim {0.0625, 0.08}}, SSS {InkRimIntensity 0.625, InkRimBlendCoef 0.875} [데이터]. Surface 구조 오프셋: Mottari +0x30, Thickness +0x38, InkNormalIntensity +0x40; Thickness {Anim +0x30, Base +0x38, BaseWall +0x3c}, Anim {Amplitude +0x30, WavePeriod +0x34} [판독: 0x71011b2b84 플래그 + 0x7102c2036c 읽기 순서].
- [20] = (clamp01(0.95 + 0.015625·sin(0.03125·f)), clamp01(0.75 + 0.015625·sin(0.03125·f)), max(0, 1.75 + 0.0625·sin(0.08·f)), f/60), f = GameFrame 정수 프레임(+0x148) [판독: 0x7102c2036c, 주기 단위는 라디안/프레임].

## 8. 동적 광원 (BlitzUBO2) [판독: 셰이더]

```glsl
cx = clamp(int((P.x − U2[0x226].x)·U2[0x227].x), 0, 19) ; cz = clamp(int((P.z − U2[0x226].z)·U2[0x227].z), 0, 19)
word = U2 의 (cz·20 + cx)번째 u32 ; if (word == 0xFFFFFFFF) 없음
for k in 0..3: i = (word >> 8k) & 0xFF ; if (i >= 30) break
   pos = U2[0x1CC0 + 16i], col = U2[0x1900 + 16i] (rgb), att = U2[0x1AE0 + 16i](x = 1/반경로 보임, y = 지수)
   Ld = pos − P ; d = |Ld| ; L = Ld/d
   a  = pow(clamp(1 − att.x·d), att.y) · clamp(dot(N, L))
   if (U2[0x2080 + 16i] != 0) {  // 스포트
      sp = U2[0x1AE8 + 16i](x = cos 경계 c, y = 지수) ; D = U2[0x1EA0 + 16i]
      a *= pow(clamp((−dot(L, D) − sp.x)/(1 − sp.x)), sp.y) }
   indirect += col·a·(diff/π + spec_GGX(…)/4π)
```

- 격자 원점·역셀 크기 = BlitzUBO2 data[0x226]/[0x227]. RenderingDay `DynamicLight.GridSize (10,1,10)` 와 셀 20개 → 200×200 범위로 보임 [추정]. 셀당 최대 4개, 전체 최대 30개.
- CPU 기록자(BlitzUBO2 = `*0x7105810020 + 0x1398` 블록, [shaders.md §3.9](shaders.md))는 [미확정]. 후보: holder+0x35f8/0x3608(=0x1398+0x2260/0x2270)을 함께 쓰는 0x71029b6698, 0x71034da0c8, 0x71034dc9dc, 0x710369bf40(`render_storescan.py`).
- 5차 후보 정리(`analysis/decomp/r5_gfx_stage/b1.c`) [판독]: 0x71029b6698 = 상태머신 객체 생성자(무관), 0x710369bf40 = agl 라이트맵(`"agllmap"`) 생성자(무관), 0x71034dc9dc = 버퍼 교대 토글(무관). 0x71034da0c8(vtable 0x710571c350, 0x2430 B 버퍼 할당)만 남았다 — 9024 B 블록과 크기가 가까운 후보이며 쓰기 함수는 미확인.
- 감쇠 지수 ↔ 데이터(`DampParam`/`DistDamp`/`AngleDamp`), 반경 ↔ 배치 `Scale`/`Radius` 대응은 [추정] (이름이 맞을 뿐 복사 코드 미판독).
- 6차 [판독, 기록자는 여전히 미확정]: 0x71034da0c8 은 vtable 0x710571c350 객체의 생성자다. 0x2430 B 버퍼 두 개를 힙에 잡아 0 으로 채우고 0x71034e1674 로 초기화해 배열(+0x10)에 넣고, 자기 안(+0x30)에도 같은 구조를 하나 더 둔다(이중 버퍼 + 현재). 버퍼 크기 0x2430(9264 B)은 BlitzUBO2 데이터 영역과 크기가 가깝지만, 이 객체가 holder+0x1398 블록에 쓰는 함수는 아직 찾지 못했다. 다음 볼 곳: vtable 0x710571c350 의 갱신 슬롯, 그리고 holder 전역(`*0x7105810020`, GOT 0x7105792048)을 읽는 함수 32개 가운데 0x710104668c(+0x1398 에 포인터를 저장함). GfxSpotLightDynamic/GfxPointLightDynamic 액터 등록(0x7101d259c0 → 0x7101044848·0x7101044f90)도 같은 관리자 쪽이다.

### r8 동적 광원 CPU 기록자·격자 정정 (2026-10-03)

원본manager1045f18/1046f20→accumulator104560c/10457dc→memberwriter1045218→GPUupload10471e4등을연결했다 [판독]. 원본15멤버선언,384upload·2048격자설정·8192점광원삽입 전수비트일치 [실행]. 이전inline UBO가정의 후보4개는잘못된구조였고+1398은UBO객체다. RenderingDayGridSize(10,1,10)·GridOffset0→extent(200,1,200)/origin(-100,-.5,-100)은1151a74/1044f90식으로확정한다. 셀당first4/전체30·packed400u32→GPU400vec4를 [dynamic_lighting.md](dynamic_lighting.md) §3~§10에정리했다. 감쇠·Radius 명명및rig전체는계속미확정이다.

## 9. 웹 포팅 (three.js) — 근사안

| 원본 | 웹 | 수준 |
|---|---|---|
| 포워드 Hoian_UBER 프로그램(1689/917/1714/946) | `MeshStandardMaterial` + `onBeforeCompile` 로 §5 식 이식(베이크 두 장, 잉크 분기). 최소안: map/normalMap/roughnessMap/metalnessMap + `aoMap`(BC5.R 를 occAO 식으로 변환) + `lightMap`(bakeLight·32) | 식은 원본, 합성은 근사 |
| 주 광원 | `DirectionalLight` 방향 = −(0.0431, −0.5664, −0.8230) 쪽에서 비춤(§4 식), 색 (0.6706,0.8510,1.0), 세기 10(선형). three 물리 조명 단위와 다르므로 노출로 맞춤 | 값 [판독] |
| SH 환경광(Env[25..31]) | 원본 송신원 [미확정]. 근사: CapturePos(−5.00, 1.13, −5.62)에서 `CubeCamera` 로 하늘(Sky_Daytime00)+맵을 찍고 `LightProbeGenerator.fromCubeRenderTarget` → `LightProbe` | 근사 |
| SH 환경광 (5차 갱신) | 송신원은 환경광 관리자(§5.6). 큐브 → SH 변환은 원본 GPU 식(§5.6)과 CPU 변환 0x71010325d4 를 그대로 옮길 수 있다(웹: CubeCamera 결과를 같은 가중으로 SH9 투영 → 같은 상수로 cAr..cC 포장 → 같은 평가식). 큐브 캡처 내용·밉·노출은 [미확정]이라 값 자체는 근사 | 식 [판독]+[실행], 값 근사 |
| 하늘 구 (5차) | `Sky_Daytime00` 모델을 맵과 함께 그리고 mSky 색 = 방출 텍스처 × **4.0**(= 2^ExposureNotInEnvMap), 안개·조명 없음. 해(mSun)는 알베도 ×11 가산 | 식 [판독] |
| 반사 `cPrefilEnvMapArray`(12 거칠기 층) | 같은 큐브 → `PMREMGenerator`(거칠기→밉). 층 = roundEven(5.5−5.5cos(πr)) 대신 three 기본 매핑 | 근사 |
| 베이크 | §6.4 | 원본 데이터 |
| 동적 그림자 | `DirectionalLight.shadow`(2048, 캐스케이드 대신 카메라 추종 박스 ~60) — 원본은 정적 메시가 대부분 `gsys_dynamic_depth_shadow 0` 이고 베이크 그림자를 씀 → 플레이어·움직이는 물체만 그림자 캐스터로 | 근사 |
| 동적 광원 | 켜진 SpotLightRig(뼈 위치) + GfxPointLightDynamic 을 `PointLight/SpotLight` 로. 감쇠는 셰이더 청크로 `pow(clamp(1−d/R), e)` | [추정] 대응 |
| 안개 | `scene.fog` 대신 셰이더 청크로 §5.5 식(깊이: Start 10/End 1000/A 0.25, 높이: 15/90/A 0.6875) | 식 [판독], 칸 대응 [추정] |
| 노출·색 보정 | ManualExposure 1.0 → `toneMappingExposure 1`. 톤매핑 변형 [미확정] → 우선 `NoToneMapping` + 색 보정 Hermite 곡선(§2.2)을 LUT 로, 결과 확인 후 조정 | 근사 |
| 노출·톤매핑 (5차 정정) | 정정(2026-10-03): 위 행의 `toneMappingExposure 1`·`NoToneMapping` 은 원본과 다르다. 원본은 선형 HDR 에 **×2.0**(exp2(ManualExposure 1.0)) → 블룸 합성 → **톤매핑 4번 식**(§3.1, three 내장에 없음 → `ShaderPass` 로 직접) → 색 보정 LUT → 비네트 → 감마(0 또는 1/2.2, [미확정]). three 에서는 `NoToneMapping` + 사용자 후처리 패스로 §3.1 식을 그대로 넣는다 | 식 [판독], 감마·블룸 방식 [미확정] |
| 잉크 | paint 영역의 도색 텍스처를 `cBlitzWallPaintGrid` 로, `_pu*` 는 paint4 결과로 생성 | §7 원본 식 |
| Env UBO (6차) | §5.5.1 표대로 한 블록을 채운다: [5] = 10·(0.6706, 0.8510, 1.0), [23] = 주광 방향, [10..12] = 깊이 안개(색 a 0.25, −S/(E−S) = −10/990, 1/(E−S) = 1/990), [13..15] = 높이 안개(방향 (0,−1,0), −15/75, 1/75), [25..31] = SH(값 [미확정] → 근사 유지) | 칸 [실행]+[판독], SH 값 근사 |
| 후처리 변형 (6차) | 블룸 **가산** 합성(`HDR·2.0 + Bloom`), 색 보정 LUT **켬**(LUT 내용은 근사), 감마 1/2.2 [미확정: 장면+0x523c bit4] | 블룸·CC [판독]+[데이터] |
| 동적 그림자 (6차) | `DirectionalLight.shadow` 를 캐스케이드 2(경계 1.5–20, 20–60 [추정]), 각 1024², 깊이 바이어스 polygon offset 0.3·scale 5.0(WebGL `polygonOffset(5.0, 0.3)` 에 해당 — 원본 인자 순서 factor/units 대응은 [추정]), PCF 오프셋 0.5 텍셀로. 정적 메시는 베이크 그림자(§6) | 설정 값 [실행]+[데이터], 필터 식 [미확정] |
| 하늘 SH·팀색 (6차) | 팀색 Ink/InkBright 는 skyUp 을 0 으로 둬도 원본과 같다(로비 조명에서 포화). 맵 간접광 SH 는 계속 근사 | 팀색 [실행] |
| RadialFog (6차) | 로비는 기본값 BlendFactor 0 → 산란 항 생략이 원본과 같다 | [판독]+[데이터] |
| 색 보정 곡선 (7차) | `(X,Y,M)` Hermit2D, 정규 접선에 X 구간 폭을 곱하지 않음. §2.2.1의 8점 f32 표본과 원본 결합 순서 반영; 최종 LUT 연산은 별도 | [실행]+[판독] |

구현 순서 권장: (1) 맵 glb + 베이크 두 장 + 주 광원 + 고정 환경광 → (2) 잉크 분기 → (3) 안개·색 보정 → (4) 동적광·그림자.

### 2026-10-03 정정: 환경 보간 t의 생산 [판독]+[실행]

§4의 기존 t 출처 [미확정] 기록을 보존하고 정정한다. 요청2b5af20은 N=int(duration),c=0과old/new포인터를 설정한다. 준비 완료 tick2b5c250은 N==1이면1, 그외f32(c)/f32(f32(N)-1)을apply에 넘긴뒤c++하고 c>=N에서old를지운다. 정상3072+조기반환6건 원본실행 모두 일치. 상세·실행경계는 [environment_transition.md](environment_transition.md) §3~§11. 2b5c4a8은 tick 내부주소며시간대시각 자체가 아니다.

### 2026-10-03 정정: 광원 Rig의 실제 뼈·필드 공급 [판독]+[실행]+[데이터]

§2.3의C32F024E는실제BonePrefix다. 네float는CycleA/B/AR/BR로이름·offset·소비를확인했다.37A1AA8이뼈worldmatrix의Offset/Direction을계산하고37A038C이Radius/Intensity/DampParam/Angle*.5/AngleDamp*(radius/Radius)를기록,1048D98이enable이중gate후104560C에공급한다.2,048건原本bitmatch. PointRig와배치Point/Spot Scale·감쇠공급도새writer/기존typedreflection/실제provider를연결해§8복사추정과§9Rig대응을해소했다.로비enabled는1,2,5,6,7이다. 상세 [light_rig_runtime.md](light_rig_runtime.md) §3~§11. 비Dynamic배치사용여부·실제GPUframe전체는별도미확정이다.

### 9.8 r8 DOF 접근자 정정 (2026-10-03) [판독]+[실행]

§4의 env+2AC8 “자동 노출 계열”은 이전 추정이다. 실제 vt90=`10C4C20`은 PostEffect.DOFGaussian을 반환하며, `2B68EF4`는 Level(clamp0..15)/Start/End/FarCancel/Enable을 DOF 객체에 쓴다. 원본1024건·typed getter4096건 비트 일치. 새 클래스 등록 DepthOfFieldObj/agldof와 범위·실패·남은 Shadow target은 [renderparam_runtime.md §3~§11](renderparam_runtime.md)에 기록했다. 적용 함수 전체 묶음은 아직 부분이다.

## 10. 검증

| 항목 | 방법 | 결과 |
|---|---|---|
| 재질 → 프로그램 | 키 표 정적 옵션 전수 대조(`gfx4_stage_programs.py`) | 64/64 불일치 0 [데이터] |
| 주 광원 방향 | 0x7102b60ea0 식에 로비 값 대입 | (0.04313, −0.56641, −0.82300) [재구현 계산] |
| BakeShadow 칸 | 0x7102b67bc4 식에 로비 값 대입 | §6.3 표 [재구현 계산] |
| env AAMP 이름 | CRC32 사전 공격 | 320 해시 중 다수 복원, 오탐 제거 목록은 `gfx4_aamp_names2.py` 실행 결과 기준 수동 [실행: 자체 도구] |

| (5차) 방향광 → SH 0x7101033b78 | 원본 unicorn 실행 vs 재구현, 무작위 2000건(`r5_gfx_stage_emu.py` A) | 2000/2000 비트 일치 [실행] (디컴파일 결합 순서 정정 1건) |
| (5차) SH 평가 0x7101033dc0 | 〃 B, s0..s3 비교 | 2000/2000 [실행] |
| (5차) 리드백 → SH 0x71010325d4 (+0x7101034608) | 〃 C, RGBA32F·RGBA16F·기타 형식 섞어 | 2000/2000 [실행] (디컴파일 [23] 출처 정정 1건) |
| (5차) HDRCompose 변형 선택 0x710112215c | 〃 D | 2000/2000 [실행] |
| (5차) HDRCompose 플래그 0x7103744058 | 〃 E | 2000/2000 [실행] |
| (5차) 조명 UBO 448 B 레이아웃 | `render_ubo_layout.py 0x7101133d40 0x2b0` 로 원본 생성자·선언 함수 실행 | 멤버 21개, 끝 0x1c0 [실행] |
| (6차) Env UBO 512 B 레이아웃 | `r6_gfx_stage_envubo_layout.py`: 0x71036ae468→0x71036ae374 원본 실행(스텁 startDeclare 1개) | 멤버 35개, 끝 0x200, SH 멤버 0x190 [실행] |
| (6차) 팀색 Ink/InkBright 의 skyUp 의존 | `r6_gfx_stage_inkcorr_emu.py 500`: 0x7101174afc 전체 원본 실행(powf/fmodf = SDK 원본), 로비 주광 + skyUp 5종 | 500/500 색에서 출력 비트 동일, 대조군(I 4, Diffuse 1) 485/500 달라짐 [실행] |
| (6차) gsys 장면 설정 이름 | `r6_gfx_stage_cfgparams.py`: 생성자 0x7103705fec 원본 실행(bl 10종·형식화 1개 스텁), crc32b 사슬 추적 + zlib 재계산 | 이름 약 175개 복원, 0x710370c15c 에서 중단 [실행] |

| (7차) Hermit2D 0x710358CFE0 | `r7_graphics_hermit2d_emu.py`: 로비 RGB36 + 증가 X 합성2091, 경계·비단위 X폭 | **2127/2127 비트 일치**, 함수 스텁 없음. reader 단독; GPU LUT 미실행 |

원본 실행 대조·화면 비교는 하지 않았습니다. 셰이더 식은 역번역 판독이고, CPU 쪽 UBO 칸 대응 중 [추정] 표시는 복사 코드를 보지 않은 것입니다.

정정(2026-10-03): 위 문장 이후 5차에서 CPU 쪽 다섯 함수를 원본 실행으로 대조했다(위 표 (5차) 행, 결과 `analysis/completion/r5/gfx_stage_emu.json`). 스텁은 없고, 실행 범위는 각 함수 단독(호출자·GPU 결과는 합성 입력)이다. 화면 비교는 여전히 하지 않았다.

## 11. 미확정 — 다음에 볼 곳

| 항목 | 다음에 볼 곳 |
|---|---|
| ~~Env UBO(gsys_environment 512 B) 칸 대응(주 광원 [5]/[23], 안개 [10..15], SH [25..31])~~ | **해소(6차)**: 기록자 0x71036b35c0·0x71036b1300, 레이아웃 원본 실행(§5.5.1). 남은 것: +0x1f8/+0x208 방향 배열의 좌표계, Hemisphere +0x198 의 의미. 5차 기록: 원천은 확인 — 안개 = env agl Fog 두 객체(§4), SH = 환경광 관리자 0x70 B 블록(gsys 뷰 레코드 +0x98/+0xa0, §5.6). gsys 가 이를 512 B 블록으로 옮기는 함수 미발견. 다음: 뷰 레코드 배열(*(env+0x190)+0x578, 0xd0 간격)을 읽는 gsys 함수(0x71036c9bf4 등 레코드 순회), agl Fog/DirectionalLight 필드(+0x128/+0x148/+0x188/+0x1a0/+0x1c0)를 함께 읽는 gsys 함수 |
| ~~하늘 SH 송신원~~ | 해소(5차): 환경광 관리자 0x710102a3e8/0x7101029f6c → 이벤트 키 0x710580e818(§5.6). 6차: 로비 = 캡처 경로(§5.6.1) [판독]. 남은 것: 하늘 SH **값** — 입력 큐브가 실행 중 장면 렌더(BaseCubeMap 256² RGBA16F, 0x710102ce04 → 0x710103dd08)라 큐브 캡처 렌더 재현이 필요(맵 큐브 패스 셰이더 변형, Illuminate 광원 0x7101037098). 팀색에는 영향 없음(로비) |
| BlitzUBO2 광원 격자 기록자 | §8 — 0x71034da0c8 은 2×0x2430 B 이중 버퍼 객체 생성자(6차 판독), 쓰기 함수 미발견. 다음: vtable 0x710571c350 갱신 슬롯, holder(*0x7105810020) 사용 함수 중 0x710104668c(+0x1398 저장) — 6차 추가: 0x710104668c 는 관리자(vtable 0x7105556ad8) 소멸자이고 +0x1398 은 gsys UBO 클래스(vtable 0x7105722198) 객체다. 0x71013776d0 은 이 UBO 를 CPU 버퍼 `*(관리자+0x1410)` 기준으로 셰이더 슬롯 2 에 바인딩하는 읽는 쪽이다 [판독]. 다음: `+0x1410` 버퍼에 쓰는 함수(ldr +0x1410 함수 9개: 0x71028de63c, 0x71028de7f0, 0x7102b39ab4, 0x7102cac4e0, 0x7102cad468, 0x710339ef8c, 0x71033a30a8, 0x71033a39d4), 관리자 vtable 0x7105556ad8 슬롯 |
| BlitzUBO0 [22].w | 6차: [22].z = 1/(8·S)(S 200/400, 0x7102be8aec) 해소(§7). [22].w(holder+0xcc4) 기록자 미발견 — 멤버 포인터 경유·memcpy 쓰기 후보를 동적 추적(UC_HOOK_MEM_WRITE)으로 찾을 것. S 를 고르는 문자열 비교 대상(*0x71058a8da0 +0xe0 vs 0x7101323040 +0x2d8)  **2026-10-03 r2 정정:** S 문자열은 기존 [panel_groups §9](../paint/panel_groups.md#9-200400-장면-문자열-판독데이터) BigWorld 비교로 이미 해소, Lby S400/Z1⁄3200. 새 [floor_ink_inputs_r2 §3~10](floor_ink_inputs_r2.md) 원본 init→texel→staging28건은 W초기0 보존/두store모두Z를 확인. W 후속 writer·whole GPU는 여전히 미확정. |
| ~~RadialFog 필드 이름·기본값~~ | 해소(6차, §4): BlendFactor/Color/Intens/LobeCtrl/ShadowInfluence/SizeCtrl. 남은 것: 이벤트 +0x38 vec4(0x71010bb2b0 MainLight 쪽 계산)의 식 |
| ~~톤매핑 변형·노출 계산~~ | 해소(5차): 톤매핑 4, 노출 = White2D.w × exp2(Value)(§3.2·§3.3) |
| 감마 변형의 로비 값 | 6차: 블룸 = finalblend 1(가산) 해소, 장면+0x1c0 +0xf00 = `linear_lighting_enable` true 해소(§3.2·§3.0). 남은 것: 장면+0x523c bit4 / +0x5239 bit4(장면+0x4918 하위 객체 +0x924/+0x921) 기록자 — 정적 스캔 0건, 장면 객체 갱신 함수 동적 추적 필요 |
| 색 보정 LUT 내용 | **7차: Hermit2D Data6·reader·로비 8점 표본은 해소(§2.2.1), 원본2127/2127 [실행]. 전체 LUT는 조사중 유지.** 6차: bit4 해소(생성 시 0x71035db354, CC = 1). LUT 는 0x71035dc218 이 12칸 연산 UBO 를 만들어 GPU 로 8³ 를 그린다 — agl 색 보정 셰이더 역번역 + 0x710115567c 가 채우는 연산 칸(종류 0~9) 대응이 필요  **r2 2026-10-03 추가/정정:** 기본 CPU연쇄128/128은 kind0→6→1, GLSL BRX표의 선택지는 kind1..10으로 복원했다. LUT좌표블록128/128; [ink_lighting_r2](ink_lighting_r2.md)§6/10. GPU bake/texel/filter/최종variant는 미확정 유지 |
| 블룸 셰이더 식 | agl `bloom_mask/gaussian/reduce/compose` 역번역(`agl_technique_pfx.sharcb`) |
| 적용 함수의 구조체 이름 | 6차: 세 함수 동작 판독(§4). 남은 것: 0x7102b66c54 의 vt+0x80 구조체·env+0x2800 객체 이름, 0x7102b68ef4 의 vt+0x90 구조체(ShadowPPBlur/DynamicShadowMap 후보), 0x7102b60200 = GlobalWind 대응 확인(RenderingDay 접근자 vt+0xc8 구현) |
| DynamicLight.GridSize 기록 위치 | 0x7102b61c20 이 아니었음(§4 정정). 적용 목록 미판독분 또는 0x71010bxxxx 안개 관리자 쪽 |
| 하늘 Offset/Scale 적용, 하늘 SH 대체 경로 조건 | Actor_SkySphere 참조 0x7102b584cc, 0x7101029f6c 의 +0x5c8 / *(env+0x190)+0x5c8 +0x88 bit1 |
| 베이크 텍스처 교체 코드, GfxPointLight/SpotLight(비 Dynamic)의 런타임 사용 여부 | `bkdat` 로더(문자열 `TexcoordScale`·`DataElements` xref), 0x7101d259c0 |
| `_pu*` 정점 속성 생성 | paint4(ColPaint UV) |
| 그림자 필터 식·캐스케이드 경계 해석 (6차 신규) | 설정 값은 해소(§3.0). PCF 커널(샘플 수·가중)·near_0_i/far_0 를 경계로 쓰는 코드: 그림자 프리패스 셰이더(agl/gsys sharc) 역번역, 0x710374c50c·0x710379b200(+0x1940 읽기) |
| 대전·로비가 gsys 설정 `Common` 을 쓰는지 | 장면+0x1c0 에 설정 배열(0x710370def4 가 32개 생성) 중 하나를 넣는 코드 |

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
| `web/tools/r5_gfx_stage_emu.py` | 5차 원본 실행 대조(SH 3종·HDRCompose 변형/플래그) → `analysis/completion/r5/gfx_stage_emu.json` |
| `web/tools/r5_gfx_stage_ptrfield.py`, `r5_gfx_stage_bitscan.py` | 포인터 필드 쓰기·비트 필드 쓰기 근접 스캔 |
| `analysis/decomp/r5_gfx_stage/` | 5차 디컴파일(b1~b17) |
| `analysis/r5_gfx_stage/` | Hoian_Proc 조도·프리필터 프로그램 역번역(`proc/`), 하늘 모델 덤프·프로그램(`sky/`), 조명 UBO 레이아웃(`lightubo_layout.tsv`) |
| `web/tools/r6_gfx_stage_envubo_layout.py` | 6차: Env UBO 512 B 멤버 선언 원본 실행 → `analysis/r6_gfx_stage/envubo_layout.tsv` |
| `web/tools/r6_gfx_stage_inkcorr_emu.py` | 6차: 팀색 보정 0x7101174afc 원본 실행(SDK powf/fmodf 연결), skyUp 의존 검사 → `analysis/r6_gfx_stage/inkcorr_emu.json` |
| `web/tools/r6_gfx_stage_cfgparams.py` | 6차: gsys 장면 설정 생성자 실행 + crc32b 이름 복원 → `analysis/r6_gfx_stage/gsys_cfg_params.tsv` |
| `web/tools/r6_gfx_stage_offscan.py`, `r6_gfx_stage_addimm.py`, `r6_gfx_stage_adrpscan.py`, `r6_gfx_stage_vtof.py` | 6차: 오프셋 접근 전수 스캔(바이트·하프·q·쌍 포함), add 즉시값 공통 함수, 넓은 창 ADRP 참조, vtable 칸 → vtable·슬롯 |
| `analysis/decomp/r6_gfx_stage/` | 6차 디컴파일: c1_envmap(큐브 캡처 0x710102ce04 등), c2_envubo(Env UBO 기록 0x71036b35c0·0x71036b1300), c3_bloom(agl 블룸 파라미터 0x71036eb47c), c4_cclut(색 보정 LUT 0x71035dc218), c5_radialfog, c6_shadowpp |
| `web/tools/r7_graphics_hermit2d_emu.py` | 7차: Hermit2D 원본 reader vs 독립 f32 대조 → `analysis/completion/r7/graphics_hermit2d_emu.json` |
| `analysis/decomp/r7_graphics/hermit2d.c`, `analysis/completion/r7/graphics_evidence.json`, `graphics_commands.md` | 새 함수 디컴파일·원본 명령/enum 연결·실제 명령과 실패 기록 |


### 11.1 r8 시각 도색 속성 생성 경로 (2026-10-03)

`_pu0/_pu1/_pu2`의생성은2bcb6b0→2bd00a4→2be2b8c(삼각형panel배정)→2be50fc→2be2de4다 [판독]+[실행]. 실제BFRES_p0조회/xyz읽기/삼각형u16+basevertex→panel후보0..11→세정점후처리를판독했고, 새후처리384입력/3456정점 UV/접선일치·비교4096nostub를확인했다. 기존 ColPaint작업으로보임 추정을 [../paint/model_panel_mapping.md §3~§11](../paint/model_panel_mapping.md)으로해소한다. 기존writer검증은재사용하며 GPU화면전체를실행한것은아니다.


### 11.2 r8 ProjShadow 자원·필드·렌더 소비 (2026-10-03)

[판독]+[실행] vt80은Shadow→ProjShadow이며 Density/Rotate/Scale/Trans/ScrollAnim/RotateAnim 전체writer와 native 렌더의matrix48B·Density clamp두개·texture slot14 gate를 확인했다. [projected_shadow_runtime.md §3~§11](projected_shadow_runtime.md)의 apply/direct/consumer3,072건 mismatch0이다. 기존 적용 구조체 질문중 DOF와GlobalWind getter는renderparam_runtime.md에서 정정했으나 env2800 targetaglprojsdw/VT572CC18·배정은추가생성구간64건/126레코드에서해소했다. live로비config·frame matrix/factor생산과ColorGrading전체연산칸 등큰묶음남은부분은별도여서조사중을유지한다.

### 2026-10-03 common_render_r5 정정·현재 웹 구현

이전 §6의Three LightProbe/단일그림자와미연결LUT는당시구현이다. [환경광](common_lighting_web_port.md)·[그림자](common_shadow_web_port.md)·[최종색](common_post_web_port.md)의새기록을우선한다.

**투영식 정정 [판독]:** §5.6/§6의“같은가중SH9”는선형면텍셀+입체각가중으로대체할수없다. 확보된shader128은sin 각도좌표·균일가중7MRT 가산이다. 새`103289c` 판독은texture+30 width>>1이256입력에서128변형을선택함을확인했다. UBO cMipLevel은texture-view+AA byte;live값은미확정이므로웹mip1을명시적정책으로분리했다. `10325d4+1034608` 원본128회 추가재생,3584bit불일치0. 이실행은기존2000건과별도포팅fixture이며원본GPU실행아니다.

웹은capture256²/near4/far1024/2회·sin7MRT·nativeCPU포장·2×1024shadow·Tone4뒤8³LUT를연결했다. 원본cube변형/Illuminate/saturation·12layer/BRDF·SPP/fade/PCF/nativebias·liveLUTsampler/rounding/gamma·Bloom/DOF는남는다. 기존결론을지우지않고날짜별정정으로보존했다. 고정inventorywhole승격0.


### 2026-10-03 common_render_r6 정정·현재 웹 구현

[조명 r6](common_lighting_r6.md)의 cube27 판독에 따라 mSky 환경광 캡처 saturation.4를 연결했다. IlluminateEnvMap.bfres는 성공 BFRES dump상 **모델0·embedded64² BC1_SRGB highlight texture1/mip7**이다. 앞선 그릴모델 설명은 정정하며 Fld_Emission4EnvMap의 cube모델24indices와 구분한다. native Illuminate/12layer/BRDF는 판독된 호출·식과 실제미연결을 함께 기록한다.

[그림자 r6](common_shadow_r6.md)는 rawPCF1/4/9/16비교·strict20경계·receiver near1.5 cutoff없음·SPP/fadeCPU식을확인했다. Default의fade40~60을웹에연결했으며 ctorfalse100~1000과구분한다. §11.2와r5의PCF/SPP/fade미확정은이좁은계산범위에서정정한다. projection/compare sampler·static/fullSPP·live선택은남는다.

[Bloom r6](common_post_r6.md)는 mask/reduce/HV/compose생산·DefaultDayold_calc=false를연결했다. HDR×2+Bloom뒤Tone4/LUT를소비하며 DOF방문자+40은masterEnable이아닌IsEnableFarCancel이었다. 기존typedpacket실행은바이트결과로유지하고DOF활성을그값으로확정하지않는다. [현재 웹 검증](../port/common_render_r6.md), fixedinventory whole승격0.


### 2026-10-03 잉크 surface r7 포팅 후속·정정

[현재 실제 구현·검증·잔여](../port/ink_surface_r7.md), [좌표/geometry](ink_visual_geometry_r7.md), [원본 판독식 소비](ink_surface_web_r7.md). 이전 별도 collision overlay/.35/단일색 미반영은 당시 상태다. 현재는 actual visual triangle에 원본 packed writer 값과 밝은 경계·법선·두께·F0.015/.05·공통 조명을 연결했다. 베이크 UV1은 paint UV로 바꾸지 않았고 clone의 shader hook/USE_UV1 defines를 유지한다.

원본 panel/atlas 전체는 customchart adapter, 환경반사는 PMREM/Three BRDF이다. native Z1/3200과 웹 페이지 폭 역수를 구별하고 초기 W0/emission0을 live 원본값으로 확정하지 않는다. 실제게임/GPU 검증은 포트 링크의 명령/실패를 따른다. fixed986/556 및 web13/62 유지, PNT06만 차이→일부.
