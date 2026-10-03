# 셰이더 해독 — Hoian_UBER 재질 · 도색 스탬프(Hoian_Proc) · UI MeterAction

Splatoon 3 v0의 셰이더 바이너리를 컨테이너 구조부터 풀고, Maxwell SASS를 GLSL로 역번역해 웹 포팅에 필요한 식·상수·슬롯 의미를 확정한 문서입니다. 확정 수준 표기는 [README](../README.md)를 따릅니다. 이 문서에서 **[판독]**은 "원본 셰이더 기계어를 Ryujinx 번역기로 GLSL로 옮긴 것을 판독"했거나 main 코드를 디컴파일해 판독한 경우입니다. 번역기가 만든 GLSL은 원본 소스가 아니라 SASS와 같은 동작을 하는 식입니다(변수명 `temp_N`, `precise`, `fma`는 번역기 산물).

관련 문서: [formats_bfres_bntx.md §5](formats_bfres_bntx.md)(재질 → glTF 근사), [team_color.md](team_color.md)(팀색 14색 계산), [../paint/paint_and_score.md](../paint/paint_and_score.md)(도색 요청·점수), [../ui/ui_hud.md §6.5](../ui/ui_hud.md)(특수 게이지).

## 1. 결론 요약

| 항목 | 결론 | 수준 |
|---|---|---|
| Hoian_UBER 샘플러 슬롯 의미 | 재질 샘플러 이름 ↔ 셰이더 심볼 31개 전부 확인(`_su0`=cTexSubstitution, `_cp0`=cTexCompPaint, `_re0..2`=cTexResource0..2 등, §3.2) | [데이터] |
| Hoian_UBER 옵션 기본값 | 정적 옵션 252개·동적 6개의 선택지와 기본값 전부(§3.4, 전체는 JSON) | [데이터] |
| 재질 → 실제 프로그램 | 샘플 36재질 모두 정적 옵션 불일치 0으로 프로그램 번호 확정(§3.5) | [데이터] |
| 팀색 혼합식 | `team_color_map_type`=2: `albedo = mix(Alb, my_team_color, clamp(Tcl.r + team_color_blend_alpha))`, =3: `mix(albedo_color, my_team_color, clamp(team_color_blend))`(§3.6) | [판독] |
| UV 세트 선택 | `texcoord_select_X = N` → 정점 속성 `_uN`(aTexCoordN), 행렬 `tex_mtx1`(2이면). 0이면 `_u0`+`tex_mtx0`(§3.7) | [판독] |
| GPU 스탬프 | 프로그램 `PaintOverpaint`, 텍셀 RGB = 팀 0/1/2 잉크량. 스탬프 값 × cAlpha 로 보간하고, **채널 ≥ 0.3 이면서 최대**인 팀만 통과(§4). 이 알파 테스트 모드들은 색이 아니라 소유 스텐실·카운트를 정하고, 색은 알파 테스트 없는 모드 9 가 씀(정정, [paint] 판독) | [판독] |
| 임계값 | `cTeamAlphaTestThreshold = 0.3`(0x3e99999a), `cConvex = 0.99`(0x3f7d70a4) — 0x7102c188b4 상수 | [판독] |
| MeterAction | 레이아웃 아카이브에 **원본 GLSL 소스**가 있음. 12시에서 시계 방향 채움, `__CUS_Float_1`=링 두께 비율, `__CUS_Float_2`=바깥 반지름(UV)(§5) | [판독: 원본 소스] |
| BlitzUBO0(gsys_user0) | 1104 B 레이아웃 확정(원본 생성자 에뮬 실행), 팀 세트 0/1/2 의 Ink/InkBright 등 7색 + 중립 3색, InkUBOParam 재질값, 2cl 잉크 색 = mix(InkBright×InkRimIntensity, Ink, clamp(m×InkRimBlendCoef))(§3.9) | [판독]+[실행: 레이아웃] |
| Ink(9)/InkBright(10) 값 | 셰이더에는 BlitzUBO0 data[3/4]·[10/11]·[62/63] 으로 들어감(§3.9). 값은 CPU 계산. 입력 = 활성 env `agl::env::DirectionalLight` 의 DiffuseColor(+0x128)·Intensity(+0x1a0) + 하늘 SH 위쪽 조도, InkBright 보정 0.1/0.5 — 계산식·입력 경로는 [team_color.md §5.3](team_color.md). 값은 스테이지 조명에 따라 달라짐 | [판독] (MainLight→DirectionalLight 경로도 [판독]: 0x7102b607c4/0x7102b60ea0 가 RenderingDay MainLight 를 직접 기록 — [stage_rendering.md §4](stage_rendering.md)) |
| 맵(스테이지) 재질 | Fld_VSLobby 64재질 프로그램 확정, 베이크·도색·동적광·안개 식 — [stage_rendering.md §5~§8](stage_rendering.md) | [데이터]+[판독] |
| 후처리 HDRCompose (5차) | `Hoian_ProcHDRCompose` 톤매핑 6종·감마·블룸 합성·색 보정 LUT·비네트 식과 픽셀 순서, 변형 선택(0x710112215c)·플래그(0x7103744058) 원본 실행 일치, 게임 경로 톤매핑 = 4 — [stage_rendering.md §3.1~§3.3](stage_rendering.md) | [판독]+[실행] |
| 조도 SH 프로그램 (5차) | `Hoian_Proc` `IrradianceClearSH`·`IrradianceCubeMapAllToSH`·`IrradianceSHToCubeMap` 역번역, CPU 리드백 변환 0x71010325d4 원본 실행 일치 — [stage_rendering.md §5.6](stage_rendering.md) | [판독]+[실행] |

## 2. 자료와 도구

### 2.1 원본 자료 [데이터]

| 파일 | 형식 | 내용 |
|---|---|---|
| `romfs/Shader/Hoian_UBER.Product.100.product.Nin_NX_NVN.bfsha.zs` | zstd → BFSHA v9.0.0 (36.9 MB) | 게임이 쓰는 재질 셰이더. 셰이더 모델 5개: `hoian_uber`(프로그램 5611), `hoian_uber_fur`(24), `hoian_uber_parallax_fur`(204), `..._fur_fin`(300), `..._fur_override`(3) |
| `romfs/Shader/Sample.Nin_NX_NVN.release.sarc.zs` | SARC | `Hoian_UBER.Nin_NX_NVN.bfsha`(130프로그램, 개발용 견본으로 보임 [추정]), `Hoian_Proc.sharcb`(도색·후처리), `Hoian_Replace.bfsha`, `Hoian_ProcOcean/HDRCompose.sharcb`, `GameAglShader.sharcb` |
| `Lib/agl/agl_resource...sarc.zs`, `Lib/gsys/gsys_resource...sarc.zs` | SARC | agl/gsys 공용 `.sharcb` |
| `Lib/NintendoSDK/TextureShader.bnsh` | BNSH | SDK 텍스처 셰이더(이번에 미사용) |
| `Layout/<이름>.blarc.zs` 안 `bgsh/` | BNSH + `.bushvt` + **GLSL 소스** | 레이아웃 셰이더. 예: `SuperGaugeTV_00`의 `bgsh/MeterAction.glsl`(21,878 B), `CombinerUserShaderVariation.glsl`, `__ArchiveShader.bnsh`(12변형), `__ArchiveShader.bushvt`(`DTCB` 3개 + `CBUS` "MeterAction") |

`Shader/` 폴더의 Product 파일과 Sample SARC 안의 같은 이름 bfsha는 프로그램 수가 다릅니다(5611 vs 130). 샘플 36재질은 모두 Product에서 정확히 일치하는 프로그램이 있었으므로 이 문서는 Product만 씁니다.

### 2.2 도구 [실행: 자체 도구]

| 도구 | 용도 |
|---|---|
| `web/tools/shader_ryujinx/ShaderLibrary/` | KillzXGaming/ShaderLibrary(GitHub, commit 790dd2e, 2026-05-24) — BFSHA/BNSH/SHARCB 파서. `ShaderLibrary.CompileTool/Libs/`에 Ryujinx.Graphics.Shader.dll(net7 빌드, Ryujinx 라이선스 동봉) |
| `web/tools/shader_ryujinx/src/` | Ryujinx 소스 참고용(openpak/ryujinx sparse clone, commit c5052b1, `src/Ryujinx.Graphics.Shader`·`ShaderTools`). 빌드에는 쓰지 않음 |
| `web/tools/shader_dump/` | C# 덤프·역번역 도구. 빌드: `cd web/tools/shader_dump && dotnet build -c Release`(시스템 .NET SDK 7) → `analysis/shader/build/bin/Release/net7.0/shader_dump.dll` |
| `web/tools/shader_material_programs.py` | 샘플 재질마다 옵션을 조립해 프로그램을 고르고 GLSL로 뽑음 |
| `web/tools/shader_strip.sh` | 역번역 GLSL에서 temp 선언·공용 블록을 빼고 본문만 출력 |
| `web/tools/shader_ubo_writer_scan.py` | 같은 기준 레지스터에 지정 오프셋들을 함께 쓰는 함수 스캔(UBO 작성자 찾기) |
| `web/tools/shader_paint_overpaint.py` | 도색 스탬프 픽셀 식 재구현 + 합성 테스트 |
| `web/tools/shader_meteraction.py` | MeterAction 재구현 + 각도·반지름 표 + 렌더 |

```sh
SD="dotnet analysis/shader/build/bin/Release/net7.0/shader_dump.dll"
$SD info-bfsha C:/dev/splatoon3/extracted/shader/Hoian_UBER.Product.bfsha analysis/shader/Hoian_UBER.Product.info.json
$SD keys-bfsha <bfsha> hoian_uber analysis/shader/Hoian_UBER.Product.keys.tsv      # 5611 프로그램 × 옵션 선택값
$SD prog-bfsha <bfsha> hoian_uber <options.json> <출력접두> [--index N]           # .vert/.frag/.options.txt
$SD info-sharc <x.sharcb> <out.json>
$SD prog-sharc <x.sharcb> <프로그램|*> <출력폴더>                                 # 매크로 조합 전부
$SD bnsh <x.bnsh> <출력폴더>
.venv/Scripts/python web/tools/shader_material_programs.py [bfres 이름 필터]
```

입력 준비: bfsha는 `extracted/shader/Hoian_UBER.Product.bfsha`(zstd 해제본), Sample/agl/gsys SARC는 `spl_data.py unpack`으로 `extracted/shader/<팩 이름>/`에 풀었습니다. 레이아웃은 `ui_sarc.py extract`로 `extracted/shader/layout/<이름>/`.

역번역 후처리(`shader_dump`): ① Ryujinx 이름 `fp_t_tcb_<2*loc+8 16진>` → 반사(reflection) 샘플러 이름, `fp_c<loc+3>` → 블록 이름, `in_attrN`/`out_attrN` → 속성 이름. ② `c1` 블록(컨트롤 섹션이 가리키는 임베디드 상수)을 실수 리터럴로 치환. ③ bfsha 블록은 uniform 오프셋 표로 `Mat.data[i].c` → `Mat.<이름>.<성분>`으로 바꿈. sharc는 uniform 위치가 RegisterUBO 안 바이트 오프셋이라 같은 방식으로 붙임(크기는 다음 uniform까지로 잡으므로, 한 변형에서 쓰지 않는 uniform이 사이에 있으면 `cAlpha[0].x`처럼 배열 표기가 붙음 — 이름 자체는 맞음).

산출물: `analysis/shader/` — `Hoian_UBER.Product.info.json`(옵션·샘플러·블록·기본값 전부), `Hoian_UBER.Product.keys.tsv`(3.1 MB), `hoian_uber/<bfres>__<재질>.{vert,frag,options.txt,opts.json}` + `index.tsv`, `hoian_proc/*.glsl`, `layout_SuperGaugeTV_00/*.glsl`, `meteraction_gauge.png`. main 디컴파일은 `analysis/decomp/shader/`.

### 2.3 한계

- 역번역 GLSL은 동작 등가 식입니다. 변수 의미(어느 temp가 무엇인지)는 사람이 판독한 것입니다.
- bfsha의 사용자 블록 `gsys_user0..2`(셰이더 심볼 `BlitzUBO0..2`, 1104/1536/9024 B)와 `Context`·`Env`는 uniform 목록이 비어 있어 `BlitzUBO0.data[i]`처럼 번호로만 나옵니다. 3차 작업에서 `BlitzUBO0`(gsys_user0)의 CPU 작성자와 레이아웃을 확정했습니다(§3.9). `BlitzUBO1/2`·`Context`·`Env` 는 여전히 번호로만 읽습니다.
- `hoian_uber` 외 fur 계열 4개 모델은 ShaderLibrary가 읽은 심볼 표가 한 칸씩 어긋나 있어(같은 이름 반복) 이름 대응을 쓰지 않았습니다. 플레이어 샘플은 모두 `hoian_uber`입니다.

## 3. Hoian_UBER 재질 셰이더

### 3.1 키 구조 [데이터]

`hoian_uber`: 정적 키 길이 19 워드 + 동적 1 워드. 프로그램마다 키 표(`KeyTable`)가 있고, 옵션마다 `Bit32Index`(워드)·`Bit32Shift`·`Bit32Mask`로 선택지 번호를 꺼냅니다. 동적 옵션 6개: `gsys_weight`(−1,0..8 = 스킨 가중치 수), `gsys_index_stream_format`, `is_graffiti_bake`, `gsys_assign_type`(material/zonly/visualize/cubemap/depth_silhouette/dilate/xlu_zprep), `blitz_ink_type`, `system_id`.

### 3.2 샘플러 슬롯 [데이터]

재질 `samplerAssign`의 키(bfsha 샘플러 이름)와 셰이더 안 심볼(`SymbolData`), 샘플 재질에서 실제로 꽂힌 텍스처 접미사입니다.

| bfsha 샘플러 | 셰이더 심볼 | 샘플 텍스처 | 비고 |
|---|---|---|---|
| `_op0` | cTexOpacity | `*_Opa` | |
| `_a0` | cTexAlbedo | `*_Alb` | 없으면 `Mat.albedo_color` 사용(눈썹 등) [판독] |
| `_su0` | cTexSubstitution | `*_Tcl` | 팀색 치환 마스크(.r) — §3.6 |
| `_n0` | cTexNormal | `*_Nrm` | BC5 .xy, z = sqrt(1−x²−y²) [판독] |
| `_r0` | cTexRoughness | `*_Rgh` | .r, max(…, 0.0001) [판독] |
| `_m0` | cTexMetalness | `*_Mtl` | |
| `_e0` | cTexEmission | `*_Emm`/`*_Emi` (오징어 몸은 `*_Tcl`) | |
| `_t0` | cTexTransmission | `*_Trm` | |
| `_ao0` | cTexAO | `*_Ao` | |
| `_fm0` | cTexSfxMask | `*_MAi`/`*_Fxm` | |
| `_b0`, `_b1` | cTexBakeAOShadow, cTexBakeLight | | 지형 베이크 |
| `_cp0` | cTexCompPaint | `*_2cl` | "two color complement paint" 마스크 — §3.6.3 |
| `_re0`..`_re2` | cTexResource0..2 | `*_Thc`, `*_MAi`, `*_MltA`, `*_Nrm` 등 | 옵션(`restex_id_*`)이 용도를 정하는 범용 슬롯 |
| `gsys_*` 15개 | cGSysProjection0, cGSysShadowPrePass, cGSysStaticDepthShadow, cGSysDepthShadowCascade, cGSysRenderTargetColor/Depth 등 | | 엔진 공급 |
| `gsys_user0`, `gsys_user3` | cBlitzPaint, cBlitzWallPaintGrid | | 지형 도색 텍스처(게임 공급) |

역번역 프래그먼트에서 별도로 보이는 엔진 샘플러: `cEnvBRDFMap`, `cPrefilEnvMapArray`(큐브 **배열**: 4번째 좌표 = 배열 층 `roundEven(5.5 − 5.5·cos(π·r))` ∈ 0..11, 잉크 분기는 층 12·lod 0) [판독]. 정정: 이전 판의 "거칠기→밉"은 틀림 — samplerCubeArray 의 4번째 좌표는 밉이 아니라 층이다(맵 재질 1714 역번역에서 잉크 분기가 `float(12)` 와 명시 lod 0.0 을 함께 쓰는 것으로 확인, [stage_rendering.md §5.4](stage_rendering.md)).

### 3.3 정점 속성·유니폼 블록 [데이터]

속성(이름 → location): `_p0`→0(aPosition), `_n0`→1(aNormal), `_t0`→2(aTangent), `_c1`→3, `_w0`→4(aBlendWeight0), `_i0`→6(aBlendIndex0), `_u0..3`→8..11(aTexCoord0..3), `_c0`→12, `_pu2`→13, `_pu0`→14, `_pu1`→15.

| 블록 | 심볼 | 크기 | uniform 목록 |
|---|---|---|---|
| gsys_context | Context | 2336 | 없음 |
| gsys_shape | ShpMtx | 256 | 없음 |
| gsys_environment | Env | 512 | 없음 |
| gsys_shader_option | ShaderOption | (옵션 254개) | 옵션 이름과 같은 uniform |
| gsys_material | **Mat** | 1904 | **248개**, 오프셋·기본값 전부 JSON |
| gsys_scene_material | SceneMat | 0 | 4 |
| gsys_user0/1/2 | BlitzUBO0/1/2 | 1104/1536/9024 | 없음(셰이더 쪽). BlitzUBO0 은 CPU 레이아웃 확정 — §3.9 |
| gsys_skeleton | Mtx | 48 | |

Mat의 팀색 관련 uniform(바이트 오프셋, 기본값): `albedo_color` 112 (1,1,1,1), `team_color_blend` 128 (0), `team_color_blend_alpha` 132 (0), `emission_intensity` 176, `emission_color` 192, `two_color_complement_paint_intensity` 408 (0), `two_comp_paint_team` 412 (0, **정수 비트로 읽음** — `floatBitsToInt`), `thr_comp_paint_intens_alpha/bravo/charlie` 416/420/424, `comp_paint_texcoord_offset` 428 (0.005), `comp_paint_norm_intens` 432 (1.0), `display_team_type` 460, `my_team_color` 1344, `_bright` 1360, `_dark` 1376, `_hue_bright` 1392, `_hue_bright_half` 1408, `_hue_dark` 1424, `_hue_dark_half` 1440, `_hue_complement` 1456, `my_alpha/bravo/charlie_team_color` 1472/1488/1504, `team_flag` 1536, `tex_mtx0/1/2` 1552/1584/1616(각 32 B, 기본 단위행렬).

### 3.4 옵션 기본값 [데이터]

전체 252개는 `analysis/shader/Hoian_UBER.Product.info.json`의 `staticOptions[].default/choices`. 재질 파일의 `<Default Value>`는 이 값입니다. 자주 쓰는 것:

| 옵션 | 기본 | 선택지 |
|---|---|---|
| `enable_albedo_tex` / `enable_normal_map` / `enable_shading` | 1 / 1 / 1 | 0,1 |
| `team_color_map_type` | 0 | 0..4 |
| `texcoord_select_teamcolormap`, `_normal`, `_rghmap`, `_mtlmap`, `_emmmap`, `_trsmap`, `_sfxmask`, `_comppaint`, `_res0..2` | 0 | 0,2,3 (`_ao`만 0..3) |
| `my_team_color_type` | 0 | 0..7,10,8 |
| `emission_color_type` | 0 | 0,1,2 |
| `comp_paint_type` | **2** | 0,1,4,2,3 |
| `transmission_mask` | **3** | 0,1,4,2,3 |
| `blitz_paint_type` | 0 | 0..5 |
| `enable_overlay_paint_on_emission` | 0 | 0,1,2 |
| `enable_roughness_map`, `enable_metalness_map`, `enable_emission(_map)`, `enable_ao` | 0 | 0,1 |
| `enable_shadow_shadow_pre_pass`, `enable_static/dynamic_depth_shadow`, `enable_projection_shadow`, `enable_fog_z/y`, `enable_diffuse/specular(_direct)`, `enable_irradiance_map`, `enable_light_pre_pass`, `enable_ink_gi`, `enable_dynamic_light`, `enable_polygonal_light`, `enable_edge_irradiance_map` | 1 | 0,1 |
| `gsys_alpha_test_func` | 6 | 0..7 |
| `bake_shadow_type`, `bake_light_type` | −1 | |
| `restex_id_parallax_height_map` / `parallax_target` / `blitz_parallax_occlusion_target` | 2 / 1 / 2 | |
| `blitz_calc_color0..3_*` (replace_color, calc_type, A..D, *_channel, clamp01) | 0 | 색 계산 네트워크(§3.6.4) |

### 3.5 재질 → 프로그램 선택 [데이터]

게임의 정확한 선택 코드는 보지 않았고, 아래 절차로 **키 표와 완전히 일치하는** 프로그램을 찾았습니다(`shader_material_programs.py`).

1. 재질 `shader.options`(`<Default Value>` 제외, `True/False` → `1/0`).
2. renderInfo: `gsys_render_state_mode` → `gsys_renderstate`(opaque 0, mask 1, translucent 2, custom 3 — ShaderLibrary TestSP3와 같은 대응), `gsys_alpha_test_enable`, `gsys_render_state_display_face` → `gsys_display_face_type`(both 0, front 1, back 2, none 3).
3. 나머지 정적 옵션은 bfsha 기본값, 동적 `gsys_assign_type = gsys_assign_material`.
4. 키 표에서 정적 옵션 + assign_type이 모두 같은 프로그램. 남는 후보는 `gsys_weight`(스킨 가중치 수)만 다름.

결과(36재질 모두 불일치 0): 무기 몸 2102·병 320, Player00 몸 5549·눈 685·눈꺼풀 4187·얼굴 1115·속 605·팀색 2790, Player01 속 195, Player02 눈꺼풀 4088, Squid/Octopus 몸 3358, Squid 눈 1059, Octopus 눈 776, 머리카락(Har) 2855, 눈썹(Eyb) 275, 하의 2711, 모자 2731·스티커 1880, 상의 834, 신발 4453, 탱크 몸 2419·BombLine 4004·Glass 5114·Harness 4526·Ink 4042(`analysis/shader/hoian_uber/index.tsv`). `gsys_renderstate`를 넣지 않으면 mask/translucent 재질 11개(몸·눈꺼풀·신발·탱크 BombLine/Harness/Ink/Glass)가 이 옵션 하나만 어긋나는 것으로 2번 규칙을 확인했습니다.

### 3.6 팀색·색 계산 [판독]

#### 3.6.1 `team_color_map_type = 2` (머리카락·눈썹·하의·모자·플레이어 팀색·오징어 몸)

```glsl
// 머리카락 프로그램 2855, Player00 M_TeamColor 2790, Squid M_Body 3358 에서 같은 형태
float k  = clamp(texture(cTexSubstitution, uv0).r + Mat.team_color_blend_alpha, 0.0, 1.0);
vec3 base = enable_albedo_tex ? texture(cTexAlbedo, uv0).rgb : Mat.albedo_color.rgb;
vec3 albedo = mix(base, Mat.my_team_color.rgb, k);          // fma(my - base, k, base)
// emission_color_type 1 (머리카락): emission = albedo * texture(cTexEmission, uv0).rgb
// emission_color_type 2 (눈썹): emission 색 = Mat.my_team_color.rgb
```

- 치환 마스크는 `_su0`(`*_Tcl`)의 **R 채널**이고, `team_color_blend_alpha`(재질 값, 샘플 모두 0)를 더한 뒤 [0,1]로 자릅니다.
- `Mat.my_team_color`는 CPU가 넣는 팀색 [8 Model](또는 renderInfo `my_team_color_type`에 따라 다른 색, [team_color.md §6](team_color.md)).
- 머리카락(투과 필름 옵션)은 `(texture(cTexResource0).rgb + my_team_color_hue_complement) * under_film_color`를 필름 아래 색으로 씁니다.

#### 3.6.2 `team_color_map_type = 3` (탱크 잉크, 무기 잉크병)

```glsl
float k = clamp(Mat.team_color_blend, 0.0, 1.0);                 // 텍스처 없음
vec3 albedo = mix(Mat.albedo_color.rgb, Mat.my_team_color.rgb, k);
// Tnk M_Ink (team_color_blend 0.5, albedo_color 0, emission_intensity 1.5):
//   방출 = Mat.emission_intensity.x * Mat.my_team_color.rgb 를 최종 색에 더함
// Wmn M_Bottle (calc_color0 사용): albedo 식 결과에 my_team_color 를 한 번 더 더함
```

#### 3.6.3 2cl(CompPaint) 경로 — 몸에 묻은 잉크 표시

`blitz_paint_type 4` 재질(머리카락·옷·몸 등)에는 분기가 하나 더 있습니다.

```glsl
int   t   = 1 - floatBitsToInt(Mat.two_comp_paint_team);            // 정수 uniform
float c   = min(texture(cTexCompPaint, uv).r + Mat.two_color_complement_paint_intensity - 1.0, 0.3)
            + BlitzUBO0.data[21].w;
float wA  = c * (1 - abs(t)), wB = c * max(0, t), wC = c * max(0, -t);
float m   = max(wA, wB, wC) - BlitzUBO0.data[21].w;
bool ink  = min(clamp(m, 0, 1) * 1000.0, 1.0) > 0.5;                 // m > 0.0005
if (ink) {   // 잉크 재질로 셰이딩: 색 = 선택된 팀의 BlitzUBO0 색쌍
  col0 = sel(wA,wB,wC) · (data[10], data[3], data[62]).rgb ; col1 = 같은 순서 (data[11], data[4], data[63]).rgb
  albedo = mix(col1 * data[45].y, col0, clamp(m * data[45].z, 0, 1))
  normal: 2cl 텍스처 차분(±comp_paint_texcoord_offset)으로 범프, comp_paint_norm_intens 배율
}
```

샘플 재질은 `two_color_complement_paint_intensity = 0`이므로 `c ≤ data[21].w`, 즉 `m ≤ 0`이 되어 평소에는 잉크 분기를 타지 않습니다. 이 세기를 런타임에 올리는 쪽(피격·잉크 묻음 연출로 추정)은 [미확정].

색쌍의 정체 [판독 — §3.9]: `col0` = 팀색 **Ink(9)**, `col1` = **InkBright(10)**. `wB`(team 0) → data[3]/[4] = 세트0, `wA`(team 1) → data[10]/[11] = 세트1, `wC`(team 2) → data[62]/[63] = 세트2 이므로 `two_comp_paint_team` = 팀 번호 0/1/2 그대로입니다. `data[45].y` = InkUBOParam `Material.SSS.InkRimIntensity`, `.z` = `Material.SSS.InkRimBlendCoef`(낮 0.625 / 0.875), `data[21].w` = 기준 0.3(전역 바람 "GlobalWind" 켜지면 10.0). 정리하면

```
잉크 albedo = mix(InkBright × InkRimIntensity, Ink, clamp(m × InkRimBlendCoef, 0, 1))
```

(정정: 이전 판의 "Ink/InkBright 계열로 추정"을 CPU 작성자 판독으로 확정.)

#### 3.6.4 `blitz_calc_color*` 네트워크 (플레이어 몸·얼굴)

Player00 M_Body(프로그램 5549)에서 관찰한 대응 [판독, 일반화는 미확정]:

| 옵션 | 값 | 결과 식 |
|---|---|---|
| calc_color0 | replace 0, type 9, B 100, C 9 | `albedo.xy *= Mat.const_color0.xy`, `albedo.z *= tex.z * const_color0.z` |
| calc_color1 | replace 1, type 2, A 4, B 101 | `transmission *= Mat.const_color1` |
| calc_color2 | replace 4, type 2, A 1, B 102 | `roughness *= Mat.const_color2.x` |

즉 replace_color 0=알베도, 1=투과(backlight), 4=거칠기, B 100/101/102 = `Mat.const_color0/1/2`, calc_type 2 = 곱.

3차 작업에서 키 표의 옵션 하나(또는 몇 개)만 다른 프로그램 쌍 20개를 역번역해 ID 의미를 넓혔습니다(`analysis/render/calc_color/calc_color_ids.tsv`, 역번역 `p<N>.frag`) [판독, 괄호 = 근거 프로그램]:

| 옵션 | 값 → 의미 |
|---|---|
| calc_type | 0 = (enable_calc_colorN 꺼짐이면 무시, 4306/4311), 1 = A+B (1702/1704), 2 = A·B, 6 = A·B + C·D (1860; B_channel 1·D=B 이면 mix(A, C, B), 1862), 8 = A·B + C (5197), 9 = A·B·C (5197, 2162), 11 = A·B·C·D (5203) |
| *_channel | 0 = rgb, 1 = 1−x (1862), 10/20/30/40 = .x/.y/.z/.w 스칼라 브로드캐스트 (5197), 11 = 1 − x.x (5197) |
| clamp01 | 1 = 결과 clamp(0,1) (5197) |
| source(A..D) | 0 = cTexAlbedo, 2 = cTexMetalness .x (1727), 9/10 = cTexResource0/1, 50 = my_team_color (2162), 54/55 = BlitzUBO0.data[15]/[16] = 중립 세트 Original/Bright (2164, 5199, 5201), 59/60/62 = my_alpha/bravo/charlie_team_color (5138/5140/5142), 100~102 = const_color0~2, 110/111 = const_value0/1, 200+k = calc_color k 결과. 1 = 거칠기, 4 = 투과는 [추정] (위 관찰) |
| replace_color | 0 = 알베도, 1 = 투과, 2 = 방출 색(× emission_intensity, 2162), 4 = 거칠기, 5 = 금속도 (1727), 6 = 불투명도 output.w (5197), 100 = 대상 없음(임시, 200+k 로 참조), 7 = 필름 아래 색 [추정] (3623) |

**정정(2026-10-03 r8) [판독]+[데이터]:** 위 source1/4 및replace7 추정은 해소했다. 새원본program1279/227은 거칠기·투과값을 다른target인알베도에 소비한다. source1은 max(Rgh.R,.0001)의현재scalar(브로드캐스트),source4는 TransRGB×Mat.transmission_color_backlight의현재투과RGB다. rawtexture만공급하면원본과다르다. replace7은 필름아래색으로, 새295의반사↔underfilm 혼합consumer까지확인했다. 몸/얼굴ThcR은1−R의투과·산란마스크다. 실제식/프로그램행/남은ID전체/검증경계는 [calc_thickness_runtime.md §3~§11](calc_thickness_runtime.md)에 기록한다.

미확인: source 1·3·4·5·8·51~53·56~58·61·65·70·112·201~207·300, calc_type 4·5·7·12 이상(단일 옵션만 다른 쌍이 키 표에 없음).

### 3.7 UV 세트 선택 [판독]

정점 셰이더(Squid M_Body, `texcoord_select_normal = 2`):

```glsl
uv0 = vec2(dot2(aTexCoord0, tex_mtx0))   // out_attr0.xy: u' = u*m[0].x + v*m[0].z + m[1].x ; v' = u*m[0].y + v*m[0].w + m[1].y
uv2 = vec2(dot2(aTexCoord2, tex_mtx1))   // out_attr0.zw
normal = texture(cTexNormal, uv2)        // 프래그먼트: in_attr0.zw
```

- 선택지 `0` → `_u0`(aTexCoord0, location 8) + `tex_mtx0`, `2` → `_u2`(aTexCoord2, location 10) + `tex_mtx1`. `3` → `_u3` + `tex_mtx2`로 추정 [추정 — 샘플에 없음].


**r8 정정(2026-10-03)**: 선택3은 활성 발광맵 프로그램2485에서 `_u3(aTexCoord3,location11)→tex_mtx2→out_attr1.xy→cTexEmission` 양단을 판독해 [판독]으로 해소했다. 첫 후보121/155/310/2659는 해당 텍스처가 제거되어 증거에서 제외했다. [shader_uv_selection.md §3~§11](shader_uv_selection.md).
- `tex_mtx`는 vec4 2개: `[0] = (m00, m01, m10, m11)`, `[1].xy = 평행이동`. 기본은 단위행렬.

### 3.9 BlitzUBO0 (gsys_user0, 1104 B) — CPU 레이아웃 [판독 + 실행]

- 바인딩: 0x710110f8cc 가 모델마다 vt+0x248(사용자 블록 설정)을 세 번 부른다 — user0 = `SceneCommonUBOHolder`+0x5d0, user1 = holder+0x1b50, user2 = holder+0x1b50(전역 `*0x7105810020` 이 있으면 그 +0x1398). holder 는 전역 `*0x7105818e38`(0x5c28 B, 생성 0x7101182114, GfxModule 초기화 0x7101117d18 의 "SceneCommonUBOHolder" 단계).
- 레이아웃: 생성자 0x71011823d0 이 멤버 62개(stride 0x48, 값 = 멤버+0x38)를 만들고 각 멤버 vt+0x10 이 선언 커서를 정렬한다(vec3/vec4/vec2/vec4[4]/vec4[7]). **unicorn 으로 생성자·선언 함수를 원본 그대로 실행**해 마지막 멤버 끝 = 0x450(1104) 으로 bfsha 블록 크기와 일치 [실행: 원본 코드 에뮬, `web/tools/render_ubo_layout.py`]. 전 멤버 표 `analysis/render/blitzubo0_layout.tsv`, 필드 출처 `analysis/render/blitzubo0_fields.tsv`.

| vec4 | 내용 | 작성 / 시점 |
|---|---|---|
| 0..6 | 팀 세트0 색 [0 Original, 4 HueBright, 6 HueDark, **9 Ink, 10 InkBright**, 11 InkLame, 12 InkLameRare] | 0x7101185c7c — 팀색 신호(타입 키 0x7105818928, 등록 0x7101185848) 수신 때. 세트 계산(0x7101178030 → 0x7101176830) 직후 디스패치(0x7101177e98), 매 프레임 아님. 초기 (1,0,0)(0x7101183ab8) |
| 7..13 | 세트1 같은 순서 | 〃 |
| 14 | 세트1 색 12 다시(원본이 같은 주소 +0x458 을 두 번 읽음) | 〃 |
| 15..17 | 세트3(Neutral) 색 [0, 2 Bright, 3 Dark] | 〃 |
| 18 | (Material.Roughness, Surface.InkNormalIntensity, env 접근자 ID 0x5e "Ink"(0x710104e6dc), Material.RoughnessCompPaint) | InkUBOParam 적용 0x7102c1d6ec |
| 19 | x = Material.Fresnel, z = Material.InkIrradianceAnisotoropy | 〃 |
| 21 | (0.000625, 0.70710677, −0.70710677, **w = 0.3**) — w 는 env 접근자 ID 0x5f "GlobalWind"(bool) set 0x710104e76c 가 참이면 10.0, 거짓이면 0.3 | 0x7102c1b270 / 0x7102c4ff64 초기화 |
| 36 | z = `*(*(env+0x1338)+0x7c8)` | 0x7101110750 |
| 45 | y = Material.SSS.InkRimIntensity, z = Material.SSS.InkRimBlendCoef | 0x7102c1d6ec |
| 59..65 | 세트2(Charlie 또는 Neutral) 색 [0, 4, 6, 9, 10, 11, 12] | 0x7101185c7c |
| 66 | env 접근자 ID 0x60 "GlobalWind" get 0x710104e808 (12 B) | |

- 팀 세트 색 i 는 `mgr + 0x2a8 + 세트×0xF0 + i×0x10`([team_color.md §3](team_color.md) 의 전역+0x560 표와 같은 메모리)에서 복사. 세트0 은 swap 이면 Bravo.
- InkUBOParam 선택 0x7102c1d59c: 시간대 0 Day / 1 Sunset / 2 Night, 모드 플래그에 따라 Oil 또는 Marble 변형. 데이터는 Bootup 팩 `Gyml/InkUBOParam*.bgyml` [판독+데이터].
- 미확정: data[20], [36].w, [52]~[55] (안개 계열로 보임)의 작성자(holder+0xc28, +0x13a8, +0x13e8, +0x1430, +0x1478), GlobalWind ID 0x5f 를 켜는 데이터.
- 6차: [22].z(holder+0xcc0) 작성자 = 0x7102be8aec, 값 1/(8·S)(S = 200 또는 400, 문자열 비교로 선택) [판독]. [22].w(+0xcc4) 작성자는 미발견. [53]~[55] 의 RadialFog 칸 이름: [53].w = BlendFactor(로비 기본 0 → 산란 항 꺼짐), [54] = (LobeCtrl 1, SizeCtrl 5, 1/exp2(10), ShadowInfluence 0) [판독] — [stage_rendering.md §4](stage_rendering.md).
- 5차: [53]~[55] 작성자 = SceneCommonUBOHolder 안개 이벤트 콜백 0x7101185af4 — [53] = (ScatteringCoeff, 1/(End−Start), ScatteringCoeff, RadialFog 값), [54]/[55] = 안개 이벤트 +0x48/+0x38 vec4 [판독]. 표와 이벤트 배치는 [stage_rendering.md §4·§5.5](stage_rendering.md). 정정(2026-10-03): stage_rendering 의 이전 후보 0x7102c5a3c8 은 접지 판정 함수라 무관. 남은 것: [36].w, [52], GlobalWind 데이터.

### 3.8 웹 포팅

1. **재질별 프로그램을 고정**: 위 절차(§3.5)로 프로그램 번호를 정하고, 그 프로그램의 역번역 GLSL을 참조 구현으로 둡니다. 우버 셰이더 전체를 옮길 필요 없이 플레이어에 쓰이는 프로그램 수십 개만 three.js `onBeforeCompile` 청크로 재현합니다.
2. 팀색 청크(§3.6.1/3.6.2)와 UV 선택(§3.7)은 원본 식 그대로 씁니다. 텍스처는 PNG로 풀었으므로 `_su0`의 R 채널을 그대로 샘플합니다.
3. `Mat` uniform 값은 bfres 재질 `params`(없으면 §3.3 기본값), 팀색은 [team_color.md](team_color.md) 계산 결과.
4. 조명(Env/Context/BlitzUBO1·2)은 CPU 쪽 칸 대응이 미해독이므로 PBR 근사를 유지합니다. 정정(2026-10-03, 6차): **Env(`gsys_environment`, 512 B)** 는 칸 대응이 해소되었다 — 멤버 35개 레이아웃 원본 실행, 기록자 0x71036b35c0·0x71036b1300 판독([stage_rendering.md §5.5.1](stage_rendering.md)). Env 는 원본 값으로 채울 수 있고(SH [25..31] 값만 근사), Context·BlitzUBO1·2 는 여전히 미해독이다. (5차: Env 의 안개·SH 원천과 후처리 HDRCompose 는 [stage_rendering.md §3·§4·§5.6](stage_rendering.md)에서 확인, 512 B 블록으로 옮기는 코드는 여전히 미확인)(셰이더 쪽 사용 칸과 식은 맵 재질 기준으로 [stage_rendering.md §5.4·§5.5·§8](stage_rendering.md)에 정리). BlitzUBO0 은 §3.9 대로 팀 세트 색(Ink/InkBright 포함)·InkUBOParam 으로 채우면 2cl 잉크 분기를 원본 식으로 돌릴 수 있습니다. 팀색·마스크·UV처럼 **색이 정해지는 부분만** 원본 식이고, 최종 셰이딩은 근사라는 점을 구분해 두세요.

## 4. 도색 GPU 스탬프 (Hoian_Proc.sharcb)

### 4.1 프로그램 [데이터]

`Hoian_Proc.sharcb`(SHARCB v9, 변형 388): `PaintAlpha`, `PaintOverpaint`(매크로 ENABLE_MASK, ENABLE_ALPHA_TEST, ENABLE_ERASE, ENABLE_WRITE_NORMAL), `PaintCopy`, `PaintMask`(TYPE 0..4), `PaintExpandMask`(TYPE 0,1), `PaintTargetArea(Line/Point)`, `PaintUVShrink`, `GraffitiMaskFold/Copy`, 그 외 조명·SMAA·안개 등. 변형 번호 = 매크로를 앞에서부터 상위 자리로 둔 혼합 기수(`idx = Σ value_i × Π_{j>i} count_j`), 바이너리 = `BaseIndex + idx × (기하 셰이더 있으면 3, 아니면 2)` — PaintOverpaint 16변형에서 MASK=1일 때만 cHeightRange·cHeightTex, ERASE=1일 때 cColor 미사용으로 순서를 확인했습니다 [데이터].

PaintOverpaint uniform(RegisterUBO 128 B, 바이트 오프셋): `cColor` 0 (vec4), `cAlpha` 16, `cHeightRange` 24 (vec2), `cWorldViewProj` 32 (mat4), `cFrameBufferSizeInv` 96 (vec2), `cTeamAlphaTestThreshold` 104, `cConvex` 108, `cTeam` 112 (int). 샘플러: `cInkTex`(스탬프), `cHeightTex`(MASK), `cDstPaintTex`(현재 도색 텍스처 사본). main 문자열 `"cColor, cAlpha, cHeightRange, cWorldViewProj[0], cFrameBufferSizeInv, cTeamAlphaTestThreshold, cConvex, cTeam"`(0x71048cd456)이 같은 순서의 열거형입니다 [데이터].

### 4.2 CPU 쪽: 프로그램 등록과 그리기 [판독]

| 주소 | 내용 |
|---|---|
| 0x7101141ea8 | Hoian_Proc 프로그램 이름 등록. `PaintOverpaint` 번호를 `*0x7105793d18`, `PaintAlpha`를 `*0x7105793d10`에 저장 |
| 0x7101146890 / 0x7101146c40 | PaintOverpaint uniform/샘플러 이름 열거형(0x7101146dd4 / 0x7101147044)을 변형별 위치 표에 연결 |
| 0x7102c16ed0 | 도색 렌더러 초기화. PaintOverpaint 16변형을 렌더러 `+0x828 + idx*8`에 저장, `idx = MASK | ALPHA_TEST<<1 | ERASE<<2 | WRITE_NORMAL<<3` |
| **0x7102c188b4** | 스탬프 1회 그리기. 변형 선택 + uniform을 NVN 인라인 상수 갱신(0x200408e0/0x6004..08e4 명령)으로 기록 + 사각형 그리기(0x7102c11c90) |
| 0x7102c564d0 | 도색 대상(면 투영 하나)마다 뷰포트·행렬·높이 범위를 만들고 0x7102c188b4 호출 |
| 0x7102c368dc | 요청 `+0x50` 바이트의 비트 0..5(면 6개로 추정)마다 0x7102c564d0 반복. 직접 호출자는 없고 데이터 8곳(0x710567f808 등)에 포인터가 있어 가상 함수로 봄 [추정] |
| 0x7102c17ae0 | 스탬프 월드-뷰-투영 행렬(크기 D+0x28, 회전 θ, 경사 보정 (φ, c)). 사인/코사인 보간 표 0x7104aa5b5c. **정정**: 이전 판의 "표 인덱스에 팀 번호가 더해짐"은 오독이었다 — 더해지는 값은 대상 vt+0x70 = 0x7102c1233c 가 돌려주는 회전 각 θ(진행 방향 D+0x3c 를 면에 투영한 각)이고, 0x7102c124bc 는 경사 보정 (φ, \|n·Z\|)이다([paint]가 판독, [../paint/paint_and_score.md §3.5.5](../paint/paint_and_score.md)). 곱 순서 식은 거기서도 [미확정] |

0x7102c188b4(param_3 = 모드, param_4 = 팀)가 넣는 값:

| uniform | 값 |
|---|---|
| cColor | 팀 0/1/2 → (1,0,0,0)/(0,1,0,0)/(0,0,1,0) (표 0x7104aa2b6c/60/54), 그 외 0 |
| cAlpha | 요청 `+0x58` 바이트 / 255 |
| cHeightRange | 대상 vt+0x80 (vec2). Floor `0x7102c1b820` / Col `0x7102c0d6e0` = (w+min, w+max). 정정(2026-10-03): 이전 기록 "vt+0x68"은 틀렸다. `0x7102c564d0`이 vt+0x68 결과(스탬프 이동, y = D+0x0c 깊이 키)를 지역 변수에 받은 뒤 vt+0x80 결과로 덮어써 넘긴다 [판독] (paint_and_score.md, [r5 paint]) |
| cWorldViewProj | 0x7102c17ae0 결과 |
| cFrameBufferSizeInv | (1/폭, 1/높이) — 도색 텍스처(`대상+0x2d8/+0x2da`) |
| **cTeamAlphaTestThreshold** | **0.3f** (0x3e99999a) |
| **cConvex** | **0.99f** (0x3f7d70a4) |
| cTeam | 팀 번호(정수) |
| 샘플러 | cInkTex = 요청 `+0x60` 텍스처, cDstPaintTex = 대상 `+0x358`, cHeightTex = 대상 `+0x748`(대상 vt+0x40이 참일 때만 → MASK 변형) |

변형 선택(모드 = param_3): `ALPHA_TEST`는 표 0x7104aa2b78 = `[2,2,2,0,2,2,2,2,0,0,0,2]`(모드 0..11, 12 이상은 0), `ERASE` = 모드 10·11, `WRITE_NORMAL` = 모드 8, `MASK` = 높이 텍스처 있음. 모드 12는 다른 대상 텍스처(`+0x900`, 나머지는 `+0x4f8`)에 그립니다.

**모드의 뜻(정정·해소, [paint] 판독 — [../paint/paint_and_score.md §3.5.4](../paint/paint_and_score.md))**: 모드는 도색 종류(슈터·롤러·폭탄)가 아니라 **패스 역할 + 팀**이다. 4/5/6 = 팀 0/1/2 칠 카운트용(스텐실 NOTEQUAL), 0/1/2 = 소유 스텐실 갱신, 9 = 실제 색 칠하기(알파 테스트 없음), 12 = 저해상도, 8 = InkRut, 11/10 = 지우기(스텐실/색), 14~17 = 모니터 카운트. 일반 칠 요청 하나가 같은 프레임에 "소유 스텐실(4~6 또는 0~2) → 색(9) → 저해상도(12)"를 모두 거친다. 모드 0~7·11·14~17 은 타깃0 색 쓰기가 꺼져 있어(채널 마스크) ALPHA_TEST 변형의 결과는 색이 아니라 **스텐실·카운트**에만 반영된다. 2팀 규칙 텍스처는 RG(스위즐 B = 0, A = 1).

### 4.3 정점 셰이더 [판독]

```glsl
// 입력 aPosition = 사각형 꼭짓점(±1)
uv = vec2(sign(x) * 0.5 + 0.5, -sign(y) * 0.5 + 0.5);   // y 뒤집힘
gl_Position = cWorldViewProj * vec4(aPosition.xyz, 1);
```

### 4.4 픽셀 셰이더 [판독]

텍셀 `D = texture(cDstPaintTex, gl_FragCoord.xy * cFrameBufferSizeInv)`. **R/G/B = 팀 0/1/2의 잉크량**, A는 cColor.w(=0)로만 덮이는 별도 채널(의미 [미확정]).

```text
ink = texture(cInkTex, uv).r * cAlpha            // 스탬프 마스크(0~1 그래디언트) × 세기
if ink <= 0: discard
[MASK]  h = texture(cHeightTex, 같은 좌표).r ; if h < cHeightRange.x or h > cHeightRange.y: discard

기본(ERASE=0, WRITE_NORMAL=0):
  for ch in R,G,B,A:
     s   = clamp(D.ch - TH, 0, 1)                 // TH = cTeamAlphaTestThreshold = 0.3
     d2  = D.ch * (1 - s*(1-cConvex)*cColor.ch)    // 이미 칠해진 자기 채널을 아주 조금(1%) 감쇠
     N.ch = mix(d2, cColor.ch, ink)                 // 스탬프 보간
  weak = N.r < TH*1.05 and N.g < TH*1.05 and N.b < TH*1.05
  for ch in R,G,B: if D.ch > TH and weak: N.ch = D.ch   // 약한 덧칠이 기존 소유를 지우지 못하게
  [ALPHA_TEST] if N[cTeam] < TH or N[cTeam] < max(N.rgb): discard   // 내 팀이 0.3 이상이고 최대일 때만 기록
  out = N

ERASE: N = clamp(D - ink, 0, 1) ; [ALPHA_TEST] N.r/g/b 중 하나라도 >= TH 이면 discard(완전히 지워질 때만 기록)
WRITE_NORMAL(모드 8): max(D.rgb) >= TH + 0.3 이고 D[cTeam] 가 최대일 때만,
                      out = max(ink_raw * ink * cColor + D * (1 - ink), TH * cColor * 1.05)
```

**칠함 여부 임계값의 답**: 스탬프 마스크 값 자체에는 임계가 없습니다(`ink > 0`이면 보간에 참여). 임계는 결과 텍셀의 **팀 채널 ≥ 0.3이면서 세 채널 중 최대**입니다(ALPHA_TEST 변형, 모드 0·1·2·4·5·6·7·11). 빈 텍셀에서는 `ink = mask × cAlpha ≥ 0.3`인 곳만 칠해지고, 상대 팀이 1.0으로 칠한 텍셀은 `ink ≥ 0.5`여야 넘어옵니다(합성 테스트 §4.6).

### 4.5 웹 포팅

[paint_and_score.md §6](../paint/paint_and_score.md)의 CPU 격자 구조에 그대로 넣을 수 있습니다. 텍셀을 `RGBA float`(또는 8비트 정규화 — 포맷은 [paint] 판독상 2팀 RG8·3팀 RGBA 로 보이나 비트 폭 이름은 추정, [../paint/paint_and_score.md §3.1](../paint/paint_and_score.md))로 두고. 아래 함수의 "written" 은 원본에서는 모드에 따라 **색이 아니라 소유 스텐실**에 반영된다는 점(위 모드 설명)에 맞춰 써야 한다:

```ts
// 모드별 변형: alphaTest = [1,1,1,0,1,1,1,1,0,0,0,1][mode] ?? 0, erase = mode==10||mode==11, writeNormal = mode==8
function overpaintTexel(D: Float32Array /*4*/, inkMask: number, cAlpha: number, team: 0|1|2, v: Variant): boolean /*written*/ {
  const TH = 0.3, CONVEX = 0.99, K = 1.04999995;
  const ink = inkMask * cAlpha; if (ink <= 0) return false;
  // ... §4.4 의사코드 그대로 (Math.fround 로 f32 재현)
}
```

- 스탬프 마스크는 `analysis/paint/inktex/*.png`의 R 채널, 텍셀 중심 좌표로 **쌍선형** 샘플(원본 샘플러는 linear [추정 — sharc 샘플러 상태 미확인]).
- 위치·회전은 0x7102c17ae0 행렬(크기 + 사인 표 회전). 회전 각 = 0x7102c1233c(진행 방향의 면 투영), 경사 보정 = 0x7102c124bc — [../paint/paint_and_score.md §3.5.5](../paint/paint_and_score.md).
- 소유 팀 판정(점수)은 같은 "≥ 0.3 이고 최대" 규칙을 소유 스텐실 경유로 쓴다([paint] 판독, paint_and_score.md §3.5.4·§3.5.6). 발밑 샘플이 같은 스텐실을 세는지는 거기서도 [추정].

### 4.6 검증 [재구현 계산]

`.venv/Scripts/python web/tools/shader_paint_overpaint.py` (합성 입력, 원본 실행 아님):

| 입력 | 결과 |
|---|---|
| 빈 텍셀, 팀0, ink 1.0 / 0.5 / 0.3 / 0.29 | (1,0,0) / (0.5,0,0) / (0.3,0,0) / discard |
| 팀0 1.0 위에 팀1 ink 1.0 / 0.6 / 0.4 | (0,1,0) / (0.4,0.6,0) 소유 팀1 / discard |
| 팀0 0.35 위에 팀1 ink 0.2, 알파 테스트 끔 | (0.35, 0.2, 0) — 약한 덧칠이 기존 0.35를 유지 |
| 팀0 0.8 위에 팀0 ink 0.05 | 0.8062 (1% 감쇠 후 보간) |
| 팀0 1.0 지우기 0.5: 모드 10 / 모드 11 | (0.5,0,0) / discard(아직 0.3 이상) |

스텁·미검증: 텍스처 포맷 양자화, 블렌드 상태(셰이더 출력이 그대로 기록된다고 가정 — 블렌드 설정 미확인), 행렬, GPU 래스터 규칙. 정정(2026-10-03): 이 가운데 행렬은 스탬프 행렬 `0x7102c17ae0` 원본 실행 6400/6400 원소 비트 일치로 해소됐다 [실행] (paint_and_score.md §3.5.5, `web/tools/r5_paint_stamp_emu.py`).

## 5. UI 사용자 셰이더 MeterAction

### 5.1 원본 소스 [판독: 원본 GLSL 소스]

`Layout/SuperGaugeTV_00.Nin_NX_NVN.blarc.zs` 안 `bgsh/MeterAction.glsl`은 노드 편집기(SGE)가 생성한 GLSL 소스입니다. `CombinerUserShaderVariation.glsl`이 `#if NW_COMBINERUSERSHADER_TYPE == 1 #include "MeterAction.glsl"`로 끼워 넣고, 컴파일본은 `__ArchiveShader.bnsh` 변형 9~11입니다(역번역에서 같은 상수 0.005·`uv*2-1`·atan 구조 확인 [판독]). main 함수를 정리하면:

```glsl
vec2  uv = nwTextureCoord0;                       // 페인 UV (P_pict_00/02: LT(0,0) RT(1,0) LB(0,1) RB(1,1), 텍스처 SRT 없음)
vec4  tex = texture(nwAlbedoTexture0, uv);        // GaugeSp_00^s
float F0 = nwExUserDataFloat_0, F1 = nwExUserDataFloat_1, F2 = nwExUserDataFloat_2;
vec2  p  = uv * 2.0 - 1.0;
float t  = 1.0 - (atan(p.x, p.y) + PI) / (2.0 * PI);    // GLSL atan(y=p.x, x=p.y)
float e0 = mix(-0.005, 1.0, F0);
float arc   = 1.0 - smoothstep(e0, e0 + 0.005, t);
float d     = distance(uv, vec2(0.5));
float outer = smoothstep(F2 + 0.005, F2, d);              // d < F2 이면 1
float rin   = F2 - mix(0.0, F2, F1);                      // = F2 * (1 - F1)
float inner = smoothstep(rin, rin + 0.005, d);            // d > rin 이면 1
vec4  c = mix(nwConstantColor0 /*black*/, nwConstantColor1 /*white*/, vec4(tex.rgb, arc * tex.a * outer * inner));
OUTPUT = c * vColor;   // 이후 CalcAlphaProcess(알파 처리), FinalAdjustmentFragmentColor()
```

### 5.2 해석

- **시작각·방향**: `t`는 `p = (0, −1)`(UV v가 작은 쪽 = 화면 위, 12시)에서 0이고, 화면 기준 시계 방향(12→3→6→9시)으로 0→1 증가합니다. `t < F0`인 부분이 보이므로 **12시에서 시계 방향으로 채워집니다**. 보이는 끝 각도 = `360° × (1.005·F0 − 0.0025)`(경계 폭 0.005 = 1.8°) [판독 + 재구현 계산].
- 게이지는 `F0 = 0.75 × 비율`([ui_hud.md §6.3](../ui/ui_hud.md))이라 가득 차면 270°, 텍스처 `GaugeSp_00`의 270° 호(12시→9시 시계 방향, 왼쪽 위 사분면 비어 있음)와 정확히 맞습니다. 이 정합은 "UV v=0이 화면 위"라는 가정(레이아웃 기본 UV)도 함께 뒷받침합니다.
- **`__CUS_Float_1`** = 링 두께 비율: 안쪽 반지름 `F2·(1−F1)`. 1이면 중심까지 채움(안쪽 마스크 없음).
- **`__CUS_Float_2`** = 바깥 반지름(UV 단위, 중심 0.5에서의 거리). 1이면 모서리(0.707)보다 커서 바깥 마스크 없음. HUD 데이터는 둘 다 1.0이라 반지름 마스크가 꺼져 있고 호 모양은 텍스처가 정합니다.
- `__CUS_Float_N` ↔ `nwExUserDataFloat_N`은 이름 번호 대응으로 본 것입니다 [추정 — ui2d가 usd1 항목을 상수 버퍼에 넣는 코드는 미확인].

### 5.3 검증 [재구현 계산]

`.venv/Scripts/python web/tools/shader_meteraction.py`: 반지름 0.4 원 위 36000점에서 alpha>0.5 구간 — F0=0.25 → 0..89.55°, 0.5 → 0..179.99°, 0.75 → 0..270.45°. F1/F2 반지름 마스크 — (0.5,0.5) → 0.253..0.500, (0.2,0.45) → 0.363..0.452(기대 0.36..0.45). 렌더 `analysis/shader/meteraction_gauge.png`(F0 = 0.1875/0.375/0.5625/0.75, 주황 #ff5d00)에서 12시 시작 시계 방향 채움과 텍스처 호 정합을 눈으로 확인.

## 6. 미확정과 다음 근거

| 항목 | 상태 | 필요한 근거 |
|---|---|---|
| ~~Ink(9)/InkBright(10) 팀색 값~~ | 해소 — 입력 P 는 "도색 관리자"가 아니라 env 관리자(전역 0x71059a7838)의 DirectionalLight(정정 이유: GOT 0x71057907e8 이 가리키는 객체의 +0x4bd0/+0x4be0 은 env 객체 타입별 색인표, RTTI 0x7105814c50 = DirectionalLight). `CorrectionInkSSS` 기본값 BrightnessOffset 0.1 / BrightnessOffsetLuminance 0.5 (생성자 0x71011af154) | [team_color.md §5.3](team_color.md), 남은 것은 거기 §9 |
| ~~BlitzUBO0 레이아웃~~ | 해소(§3.9): 작성자 0x7101185c7c(팀색)·0x7102c1d6ec(InkUBOParam), 레이아웃 원본 에뮬 실행 1104 B 일치. r3_batch1 후보 4개는 무관한 생성자·소멸자였음. 5차: [53]~[55] = 0x7101185af4(안개 이벤트), [20] = 0x7102c2036c([stage_rendering.md §7](stage_rendering.md)) | 남은 것: data[36].w/[52] 작성자, GlobalWind 데이터. 6차: [22].z = 1/(8·S)(0x7102be8aec, S 200/400), [53].w = RadialFog BlendFactor(기본 0), [54] = (LobeCtrl, SizeCtrl, 1/exp2(2·SizeCtrl), ShadowInfluence) — [stage_rendering.md §4·§7](stage_rendering.md). [22].w 작성자 미발견 |
| `blitz_calc_color` ID 전체 의미 | 대부분 해소(§3.6.4 표). 남은 source/calc_type 값은 단일 옵션 쌍이 없음 | 여러 옵션이 다른 쌍 역번역 |
| ~~도색 모드 0..17 ↔ 도색 종류~~ | 해소([paint]): 모드 = 패스 역할 + 팀(§4.2 모드 설명). 모드 3·7·13 용도는 [paint] 쪽 미확정 | paint_and_score.md §3.5.4 |
| ~~도색 텍셀 A 채널 의미~~, 텍스처 포맷 정밀도, ~~블렌드 상태~~ | A 는 모드 13 만 씀(판정 무관), 블렌드 끔·채널 마스크는 원본 에뮬로 확인([paint] §3.1·§3.5.4). 비트 폭 이름만 [추정] | paint_and_score.md |
| ~~소유 판정·점수 집계 임계~~ | 해소([paint]): 집계도 0.3·최대 규칙(스텐실 경유) | paint_and_score.md §3.5.6 |
| `texcoord_select = 3` | `_u3`+`tex_mtx2` [추정] | 값 3을 쓰는 재질 프로그램 역번역 |
| fur 계열 셰이더 모델 심볼 | 라이브러리 판독 어긋남 | SymbolData 판독 수정 |

### 11.8 calc source/replace와Thc 정정 — 2026-10-03 r8

새원본5프로그램역번역과cross-targetdataflow로 source1/4,replace7의기존추정을해소했다. GPU실행으로표시하지않고[판독]+[데이터]다. source/calc_type 전체묶음은남으며 rawtexture·currentvalue 구분을보존한다. 근거 [calc_thickness_runtime.md](calc_thickness_runtime.md).
