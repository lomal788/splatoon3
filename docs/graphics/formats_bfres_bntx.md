# FRES v10 / BNTX 4.1 — 구조, 변환 도구, glTF 규칙, Hoian_UBER 재질

[목차](model_character.md)

## 1. 개요

`romfs/Model/*.bfres.zs`는 zstd(사전 없음)로 압축된 FRES v10 한 파일에 모델·스켈레톤·셰이프·재질·애니(스켈레탈/재질/가시성)·텍스처(BNTX)를 모두 담습니다. Jamboree(mpj)는 FRES 9를 여러 파일(.fmdb/.fskb/...)로 나눠 썼지만 Splatoon 3는 한 파일입니다 [데이터].

## 2. 자료와 버전 [데이터]

| 항목 | 값 | 근거 |
|---|---|---|
| FRES 헤더 | `46 52 45 53 20 20 20 20` "FRES    ", +8 u32 `0x000a0000`(v10.0), +0xC BOM `FF FE` | 샘플 14개 hex (압축 해제본은 확인 후 삭제, `graphics_convert.py --keep-raw`로 재생성) |
| 내장 텍스처 | `ExternalFiles["textures.bntx"]` = BNTX, 헤더 +8 u32 `0x00040100`(4.1), +0x1C u32 파일 크기 | `Wmn_Shooter_NormalT.bfres` +0x29000, 크기 549,064 |
| 셰이더 | 모든 샘플 재질이 아카이브 `Hoian_UBER`, 모델 `hoian_uber`. romfs의 셰이더 파일은 `Shader/Hoian_UBER.Product.100.product.Nin_NX_NVN.bfsha.zs`(6.6MB)와 `Shader/Sample...sarc.zs` 둘뿐. 구조·슬롯·옵션·역번역은 [shaders.md](shaders.md) | romfs_list, 덤프 |
| 회전 | 스켈레톤 `EulerXYZ`, 스케일 모드 `Maya`(세그먼트 스케일 보정) | 덤프 |

샘플(모델별): 뼈 / 셰이프 / 재질 / 정점 / 스켈·가시성·재질 애니 수 [데이터, `analysis/graphics/dump/samples.json.gz`(gzip)]

| 파일 | 뼈 | 셰이프 | 재질 | 정점 | 애니 S/V/M |
|---|---|---|---|---|---|
| Wmn_Shooter_NormalT | 2 (Root, Muzzle) | 2 | 2 | 4,116 | 0/0/0 |
| Player00 | 87 (스무스 74, 리지드 1) | 16 | 6 | 12,322 | 1044/506/644 |
| Player01 | 87 | 16 | 6 | 12,199 | 37/32/39 |
| Player02 | 87 | 16 | 6 | 12,127 | 31/31/37 |
| Player_Squid | 23 | 2 | 2 | 3,402 | 34/1/15 |
| Player_Octopus | 33 | 2 | 2 | 3,931 | 33/1/28 |
| Har_SQD000_F | 13 | 1 | 1 | 1,896 | 35/0/1 |
| Eyb_SQD000_F | 4 | 1 | 1 | 98 | 0/0/1 |
| Btm_000_F | 6 | 1 | 1 | 1,134 | 0 |
| Clt_SHT000 | 19 | 1 | 1 | 2,133 | 0 |
| Shs_BOT000 | 4 | 1 | 1 | 2,427 | 0 |
| Hed_CAP000 | 1 (Root) | 2 | 2 | 930 | 0 |
| Tnk_Simple | 21 | 24 | 5 | 7,535 | 1/0/5 |
| Gear_anim | — | — | — | — | 10/0/1 (애니 전용) |

## 3. FRES v10 판독 [실행]

- 도구: BfresLibrary(Switch/ResFileParser 등에 `VersionMajor >= 10` 분기 있음)를 `web/tools/graphics_bfres2gltf/oss/BfresLibrary`로 **복사**해 함께 빌드했습니다(mpj 쪽은 수정·빌드하지 않음).
- `graphics_bfres2gltf.exe dump <out.json> <bfres...>`: 14개 파일 모두 예외 없이 읽힘(결과 `analysis/graphics/dump/samples.json.gz`, SuperHook 2개 `superhook.json.gz`, GearAlphaMask·Gear_anim `gear_misc.json.gz`).
- 회전 규약 확인: 각 뼈 로컬 TRS(EulerXYZ → R = Rz·Ry·Rx)를 곱한 바인드 월드와 파일의 `InverseModelMatrices`를 곱해 단위행렬과의 최대 오차를 봤습니다. Player00 4.9e-7, 파츠 ≤1.1e-7, 무기 0. 다른 가설(Rx·Ry·Rz)은 변환기가 함께 계산해 기록합니다(`meta.bindCheck`).

### 3.1 정점 속성 [데이터, 샘플 85 버퍼]

| 속성 | 형식(개수) | 의미 |
|---|---|---|
| `_p0` | Float32x3 (56), Half16x4 (29) | 위치 |
| `_n0` | 10_10_10_2 SNorm (85) | 노멀 |
| `_t0` | 8_8_8_8 SNorm (85) | 탄젠트(w=부호) |
| `_u0` | 16_16 UNorm (52) / Half (31) / SNorm (2) | UV0 |
| `_u1`, `_u2` | 16_16 UNorm/SNorm/Half, 8_8 UNorm | UV1, UV2 |
| `_i0` / `_w0` | 8x4 UInt / 8x4 UNorm (63), 8x2 (8), 8 (12) | 스킨 인덱스(행렬 팔레트 → `matrixToBone`) / 가중치 |

인덱스는 전부 UInt16 삼각형. 셰이프 LOD는 3단(61개) 또는 1단(24개). 스킨 수 4(43), 3(20), 1(12, 리지드), 2(8), 0(2, 뼈 자식). 형식 변환은 BfresLibrary `VertexBufferHelper`가 합니다.

## 4. BNTX 4.1 [실행]

- 도구: `web/tools/graphics_bntx.py`(mpj `graphics_bntx.py` 복사 + `read_bntx`: `.zs` 해제, FRES 안의 첫 `BNTX\0\0\0\0`를 찾아 +0x1C 크기만큼 자름). Tegra X1 블록 리니어 디스위즐(GOB 64B×8, 블록 높이 `1<<(layout&7)`), BC1~7은 Pillow `bcn`, ASTC는 `texture2ddecoder`(둘 다 이번에 `.venv`에 설치).
- 노멀(BC5 SNORM, 이름 `_Nrm`)은 Z를 재구성해 RGB로 저장합니다(원래 도구는 `_nml`만 처리 → `_Nrm` 추가).
- 샘플 11개 모델 212장 변환, 실패 0 (그때의 출력 `analysis/graphics/tex/`는 용량 때문에 지웠고, 같은 PNG가 `analysis/graphics/web/<모델>/tex/`에 남아 있음 — Player02 제외). 형식: BC4_UNORM 98, BC1_SRGB 83, BC5_SNORM 31. 채널 선택자(BRTI comp) RRRR 86, RGBA 83, RG01 31, RRR1 12.

형식 번호(BRTI +0x1C u32 의 상위 바이트)는 nn::gfx ChannelFormat 순서다. 이번에 `graphics_bntx.py` 의 표를 고쳤다(정정: 이전 `0x12: ("R16F?", bpp 2)` 는 틀림) — **0x0A = R16(2 B), 0x12 = R16_G16(4 B), 0x15 = R16_G16_B16_A16(8 B)**. 근거: `web/tools/graphics_bntx_fmtscan.py <형식>` 이 imageSize 를 블록 선형 정렬 크기와 맞춰 텍셀당 바이트를 역산한다 — `Tex/BossSPlashPreCL_Vfi` 등 0x0A_UINT 60×6144 → 2 B, 이펙트 `splash05_vsp` 등 0x15_FLOAT → 8 B [데이터]. 0x12 는 Model 1,283개·Effect·Tex·Layout·UI·Env·Lib 폴더 스캔(Pack·Bake 등은 안 봄)에서 **사용처 0개**라 데이터로 직접 확인하지는 못했고, 앞뒤 번호(0x0A=R16, 0x15=RGBA16)가 같은 열거 순서와 맞는 것으로 4 B 로 둔다 [데이터 + 추정]. 0x0A/0x12 의 PNG 디코드는 구현하지 않았다(필요 시 `effect_bntx_float.py` 방식).

| 접미사 | 형식 | 슬롯 | 의미 |
|---|---|---|---|
| `_Alb` | BC1 sRGB | `_a0` | 알베도 [데이터] |
| `_Nrm` | BC5 SNORM | `_n0` | 노멀(XY) [데이터] |
| `_Rgh` / `_Mtl` / `_Ao` | BC4 | `_r0` / `_m0` / `_ao0` | 거칠기 / 금속 / AO [데이터: 옵션 이름 `enable_roughness_map` 등] |
| `_Opa` | BC4 | `_op0` | 불투명(알파 테스트, renderInfo `gsys_render_state_mode=mask`) [데이터] |
| `_Emm`/`_Emi` | BC4 / BC1 | `_e0` | 발광 [데이터: `enable_emission_map`] |
| `_Tcl` | BC4 | `_su0` (오징어 몸은 `_e0`에도) | 팀 색 치환 마스크 — 셰이더 심볼 `cTexSubstitution`, R 채널 + `team_color_blend_alpha`를 [0,1]로 잘라 `my_team_color`와 섞음 [판독 — [shaders.md §3.6](shaders.md)] (정정: 기존 [추정]을 셰이더 역번역으로 확정) |
| `_2cl` | BC4 | `_cp0` | `cTexCompPaint` — 몸에 묻은 잉크 표시 마스크(R + `two_color_complement_paint_intensity` − 1 이 BlitzUBO0 기준을 넘으면 잉크 재질로 셰이딩, 차분으로 범프) [판독 — [shaders.md §3.6.3](shaders.md)] |
| `_Trm` | BC1 sRGB | `_t0` | 투과 색 [데이터: `enable_taransmission`(원문 철자), `enable_transmission_map`] |
| `_Thc` | BC4 | `_re2` 등 | 두께(SSS) [추정: 옵션 `enable_thickness_map`, `restex_id_thickness_map`] |
| `_MAi`, `_MBi`, `_Fxm`, `_MltA` | | `_fm0`/`_re0`/`_re1` | 슬롯 의미는 확정: `_fm0`=cTexSfxMask, `_re0..2`=cTexResource0..2(범용, `restex_id_*` 옵션이 용도 결정) [데이터 — [shaders.md §3.2](shaders.md)]. 각 텍스처 채널의 쓰임은 재질별 프로그램 역번역에서 확인해야 함 [미확정] |
| `.0`, `.00` 번호 | | | 텍스처 패턴 애니 프레임(예 `M_Eye_Alb.00~.21` = 눈 색, `M_Eyelids_Opa.0~3` = 깜빡임) [데이터] |

GearAlphaMask: `Model/GearAlphaMask.bfres`에 `Btm_00_Opa`, `Clt_20_Opa`, `Shs_03_Opa` 등 128×128 BC4 마스크 55장. 기어 표의 `AlphaMaskF/M` 이름 + `_Opa`로 찾습니다(코드 0x7102b8ca48: 형식 `"%s%s"`, `"_Opa"`, `"GearAlphaMask"`) [판독]. 몸 재질의 `_op0`(`M_Body_Opa`)를 대신하는지는 [미확정].

## 5. Hoian_UBER 재질 → glTF 근사

### 5.1 재질 구성 [데이터]

재질마다 `shader.options`(정적 옵션, `<Default Value>`는 셰이더 기본값 — BFSHA 해독으로 252개 전부 확인 [데이터], [shaders.md §3.4](shaders.md)), `renderInfo`(문자열/실수 배열), `params`(셰이더 파라미터 248개 내외), `samplerAssign`(슬롯→재질 샘플러), `userData`(`Paintable`, `SealPolygon`, `VertexAlpha` 등).

| renderInfo | 샘플 분포 | glTF |
|---|---|---|
| `gsys_render_state_mode` | opaque 25, mask 10, translucent 1 | OPAQUE / MASK / BLEND |
| `gsys_alpha_test_enable`/`_value` | true 10 (0.5) | alphaCutoff |
| `gsys_render_state_display_face` | front 35, both 1 | doubleSided |
| `my_team_color_hue_offset`, `my_team_color_bright_offset`, `my_team_color_type`, `enable_overlay_paint_on_emission` | 무기 M_Body hue_offset 0.5 | 팀색 계산에 씀 ([team_color.md §6](team_color.md)) |
| `spl_model_type`, `paint_prior_face`, `gsys_bake_*`, `gsys_dynamic_depth_shadow` 등 | | 기록만 |

팀색 관련 셰이더 파라미터(파일 값은 전부 1,1,1,1 → 런타임이 씀): `my_team_color`, `my_team_color_bright`, `my_team_color_dark`, `my_team_color_hue_bright(_half)`, `my_team_color_hue_dark(_half)`, `my_team_color_hue_complement`, `my_alpha/bravo/charlie_team_color`, `team_flag`(vec3), `player_skin_color` [데이터].

### 5.2 변환 규칙 (`BuildMaterialHoian`, 웹 근사) [추정 — 조명은 근사, 팀색·UV 원본 식은 [shaders.md §3](shaders.md)]

```
baseColorTexture = _a0  (enable_albedo_tex != "False")
   + _op0 가 있고 mode ∈ {mask, translucent} 이면 알파로 합친 "<alb>__<opa>.ba.png"
   albedo 끔이면 baseColorFactor = params.albedo_color
metallicRoughnessTexture = "<rgh>__<mtl>.mr.png" (G=_r0, B=_m0; _m0 는 enable_metalness_map=="True"일 때만)
   없으면 roughnessFactor = params.roughness, metallicFactor = params.metalness
normalTexture = _n0 (enable_normal_map != "False"), occlusionTexture = _ao0 (enable_ao != "False")
emissiveTexture = _e0 (enable_emission_map=="True"), emissiveFactor = emission_color * emission_intensity (≤1)
alphaMode = mask→MASK(cutoff=gsys_alpha_test_value), translucent→BLEND; doubleSided = display_face=="both"
extras.fres = 재질 원자료 전부 + teamColor{maskTcl(_su0 png), map2cl(_cp0 png), team_color_map_type, my_team_color_type, ...}
```

UV는 모두 texCoord 0으로 둡니다(현재 변환기). 셰이더 해독 결과 `texcoord_select_X = "2"`는 그 슬롯을 정점 속성 `_u2`(aTexCoord2)와 `Mat.tex_mtx1`로 샘플합니다(오징어 몸 노멀) [판독 — [shaders.md §3.7](shaders.md)]. 변환기에서 해당 슬롯의 glTF `texCoord`를 2번 세트로 바꾸는 것은 아직 반영하지 않았습니다(원값은 extras에 보존).

## 6. glTF 변환 파이프라인 [실행]

```sh
cd c:/dev/splatoon3
.venv/Scripts/python web/tools/graphics_convert.py Wmn_Shooter_NormalT
.venv/Scripts/python web/tools/graphics_convert.py Player00 --clip Wait --clip Run --clip Shoot_Shtr --clip WaitHold_Shtr
.venv/Scripts/python web/tools/graphics_convert.py Player_Squid --clip Sqd_Wait --clip Sqd_ToHuman
# 다른 파츠: Har_SQD000_F Eyb_SQD000_F Clt_SHT000 Btm_000_F Shs_BOT000 Tnk_Simple Hed_CAP000
node web/tools/graphics_verify/check.mjs Player00 ...      # three GLTFLoader 구조 검증
node web/tools/graphics_verify/shot.mjs "scene=assembled&clip=Wait&frame=0"   # 헤드리스 조립 렌더
```

1. `romfs/Model/<이름>.bfres.zs` → zstd 해제 → `analysis/graphics/raw/<이름>.bfres` (변환 후 삭제, `--keep-raw`면 유지)
2. 내장 BNTX → `analysis/graphics/web/<이름>/tex/<텍스처>.png` + `.json`(형식·크기·mip·comp)
3. `graphics_bfres2gltf.exe gltf raw.bfres out.glb --texdir tex --texuri tex/ --meta meta.json [--anim <bfres> --clip <이름>...]`
   - `--anim`에 같은 bfres(또는 다른 bfres, 예: Player01 모델 + Player00 애니)를 주고 `--clip`으로 고릅니다(이번에 추가한 옵션). Player00은 클립 1,044개라 전부 넣지 않습니다.
4. meta의 `combine` 목록대로 `.mr.png`(G=거칠기, B=금속), `.ba.png`(RGB=알베도, A=불투명) 생성.

glb 규칙은 mpj 변환기와 같습니다: 노드 0 `<모델>__model`, 뼈 = 노드(이름·부모·바인드 TRS), 스킨 1개(관절=모든 뼈, 역바인드=계산 바인드 월드의 역), 리지드(스킨 1) 정점은 뼈 월드로 미리 변환, 스킨 0 셰이프는 뼈 노드 자식, 메시 노드 `extras.visBone`(가시성 애니 대상 뼈), 클립 = 정수 프레임 베이크(시간 = 프레임/60, LINEAR), `animation.extras{frames, loop, scaleMode}`.

### 6.1 샘플 결과 [실행]

| 모델 | glb B | 텍스처 B (png 수) | 메시 | 정점 | 삼각형 | 클립(프레임) |
|---|---|---|---|---|---|---|
| Wmn_Shooter_NormalT | 332,136 | 392,991 (10) | 2 | 4,116 | 2,230 | — |
| Player00 | 2,320,848 | 551,945 (65) | 16 | 12,322 | 7,642 | Run 32, Shoot_Shtr 10, Wait 135, WaitHold_Shtr 120 |
| Player_Squid | 495,960 | 317,035 (22) | 2 | 3,402 | 3,010 | Sqd_ToHuman 3, Sqd_Wait 120 |
| Har_SQD000_F | 161,324 | 458,270 (9) | 1 | 1,896 | 1,470 | — |
| Eyb_SQD000_F | 26,804 | 4,514 (3) | 1 | 98 | 62 | — |
| Clt_SHT000 | 177,108 | 349,751 (5) | 1 | 2,133 | 1,534 | — |
| Btm_000_F | 101,236 | 290,097 (7) | 1 | 1,134 | 574 | — |
| Shs_BOT000 | 210,100 | 693,341 (8) | 1 | 2,427 | 846 | — |
| Tnk_Simple | 739,612 | 718,139 (35) | 24 | 7,535 | 9,010 | — |
| Hed_CAP000 | 93,864 | 683,182 (12) | 2 | 930 | 650 | — |

텍스처 해상도 예: 무기 `M_Body_Alb` 256×256 BC1, `M_Body_Nrm` 512×512 BC5; Player00 `M_Body_Alb` 256², `M_Body_Nrm` 384², `M_Eye_Alb.00~.20` 128²(.15 이후 256²); 머리카락 `M_TeamColor_*` 512×256.

`node check.mjs` 결과(10개 모델): 메시·정점·삼각형 수가 meta와 같고, 바인드 포즈 스킨 오차 ≤2.2e-7, 클립 길이 = 프레임/60, 오류 0 (`analysis/graphics/verify/*.json`).

## 7. 원본과 같게 / 웹 때문에 바꾸는 것

- 같게: 뼈 이름·계층·바인드 TRS(EulerXYZ=Rz·Ry·Rx), 정점 데이터, 클립의 정수 프레임 값(60fps), 텍스처 내용·크기, 재질 원자료(extras).
- 바꿈: 셰이더(BFSHA) 대신 PBR 근사 + 팀색 혼합 청크. 세그먼트 스케일 보정(`scaleMode: Maya`)은 glTF로 표현 못 함 — 비등방 스케일 애니가 있는 클립은 자식 뼈 형태가 원본과 다를 수 있음 [미확정: 샘플 클립에서 영향 미측정]. BC 압축은 PNG로 풀었으므로 웹 배포 시 KTX2(BasisU) 재압축을 권장(크기 목적, 원본 동작과 무관).
- C: 여유 공간이 적어 전체 1,283개 일괄 변환은 하지 않았습니다. 전체 변환 시 raw bfres(압축 해제 ~2.7GB 이상 [추정])는 디스크에 남기지 말고 스트리밍 처리하는 것이 좋습니다.

### 7.1 LOD 임계 선택 [데이터 + 판독]

- RSDB `LODThreshold` 36행(플레이어 전용 행 없음). 대표 Start/End: Default 20/50, SuffixFar 500/2000, PrefixFld 30/60, PrefixFldBG 100/100, PrefixKbi 50/80, 나머지는 Fld/Obj 개별 행 [데이터].
- 선택 0x71010fe270(모델 생성 콜백 0x710110f8cc 가 호출): ① 모델 이름별 표(+0x30 트리) → ② 없으면 이름 끝 `_Far` = SuffixFar, 앞 `Fld_` = PrefixFld, `FldBG_` = PrefixFldBG, `Kbi_` = PrefixKbi, 그 밖 Default. 행 +8 = **End**, +0xc = **Start** 를 읽어 유닛마다(vt+0x228 개수, +0x38 배열 0x50 B 간격) **[Start, 2·Start − End, 1/(End − Start)]** 를 기록(Start == End 면 세 번째 값 1) [판독]. 정정(gfx4): 이전 판은 +8 = Start 로 보아 [End, 2End−Start, 1/(Start−End)] 라 적었으나, RSDB 행 적재 0x71013de244~0x71013de28c 가 `EndDistFromBounding` → 행+8, `StartDistFromBounding` → 행+0xc 에 쓰고(16 B 행 = 이름 8 B + End + Start), 리플렉션 0x71011bb6a0 도 End +0x30 / Start +0x34 로 같은 순서다 [판독]. 조회 0x71013df5e4 가 돌려주는 포인터가 이 행(또는 객체+0x28)이라는 것은 [추정: 두 배치 모두 +8=End 로 일치]. 예: Default(Start 20, End 50) → [20, −10, 1/30], SuffixFar(500/2000) → [500, −1000, 1/1500]. 필드 이름 `…DistFromBounding` 으로 보아 거리는 바운딩(구) 표면 기준으로 본다 [추정].
- 플레이어 모델은 Default(20/50)를 받는 것으로 본다 [추정]. 이 세 값을 읽는 거리 계산과 셰이프 LOD 3단의 연결은 [미확정] (gfx4 조사: 유닛 클래스 vtable 미식별 — 0x710110f8cc 는 모델 생성 리스너 보조 vtable 0x7105560e38 슬롯 0x58 이고, 같은 슬롯 호출이 *0x7105812710 의 리스너에도 있음. main 문자열에 `SLOD_TYPE`·`FROM_SLOD_TYPE`·`TO_SLOD_TYPE`·`SLOD_TRANSITION_TYPE`·`PERFORM_LOD_CHECK`, Hoian_UBER 옵션에 `fade_dither_alpha`·`enable_model_dither_*` 가 있어 디더 페이드 경로 후보 [데이터]) — 웹은 당분간 LOD0 고정 또는 three.js `LOD` 에 위 임계를 그대로 넣는 근사.

## 8. 미확정과 필요한 근거

| 항목 | 이유 | 필요한 것 |
|---|---|---|
| ~~셰이더 옵션 기본값·슬롯 의미~~ | 해소: 옵션 기본값·샘플러 심볼·Mat 오프셋 [데이터], 팀색·2cl 사용 [판독] — [shaders.md](shaders.md) | `_MAi`/`_Fxm`/`_MltA` 채널별 쓰임은 해당 재질 프로그램(`analysis/shader/hoian_uber/*.frag`)에서 읽으면 됨 |
| ~~`texcoord_select_*` 값 의미~~ | 해소: 0→`_u0`+tex_mtx0, 2→`_u2`+tex_mtx1 [판독], 3은 [추정] | 값 3 재질 역번역 |
| Maya 스케일 보정 영향 | 클립별 스케일 커브 미조사 | 덤프 `--keys`로 스케일 키 ≠1 클립 집계 |
| LOD 전환식 | 부분 판독: 표 선택·기록까지(§7.1, 필드 순서 정정됨). 거리 계산 소비처 [미확정] | 유닛 레코드(+0x38 배열, 0x50 B)의 [0]/[8] 을 읽는 gsys 셰이프 그리기 코드(vt+0x228 클래스 vtable 부터) |
