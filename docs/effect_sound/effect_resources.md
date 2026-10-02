# 이펙트 리소스 — esetb / VFXB v46 / 탄 파티클 OneEmitter / HitEffectConfig

ELink가 고른 이펙트 이름(`RuntimeAssetName`)과 코드가 직접 쓰는 이펙트 이름이 이미터셋·텍스처까지 이어지는 경로를 다룹니다. 탄 파티클 관리자와 착탄 스플래시 분류도 여기에 있습니다. 상위 문서는 [effect_sound.md](effect_sound.md)입니다.

---

## 1. 파일 구성 [데이터]

| 파일 | 해제 크기 | 내용 |
|---|---|---|
| `Effect/static.Nin_NX_NVN.esetb.byml.zs` | 120,421,176 | BYML `{Esets: [이름 1,120], PtclBin: 바이너리 120,386,880 B @0x7000}` |
| `Effect/Mission.Nin_NX_NVN.esetb.byml.zs` | — | 같은 구조, 이미터셋 431(미션 전용) |
| `Effect/EffectFileInfo.Product.100.Nin_NX_NVN.byml.zs` | 2,024 | `{StaticEsetb: ["static"], EsetbList: ["Mission"], BinaryDict: {액터/장면 이름: "Mission"}}` — 어떤 액터가 Mission 묶음을 불러오는지 |

PtclBin은 VFXB입니다. 헤더는 `VFXB    `, gfxApi 0x0400, **version 46**(0x2E), BOM FFFE, 이름 "static"입니다. 최상위 섹션은 ESTA(이미터셋 1,120), GRTF(텍스처, 0x2473940 B), PRMA, TRMA, G3PR(BFRES 프리미티브), GRSN(셰이더, 0x3dae458 B)입니다 [실행: `effect_vfxb.py tree`].

- Jamboree(mpj)의 VFXB는 버전 53이고 EmitterData가 0x1100 B입니다. 이 게임은 46이고 **0xEF0 B**입니다. mpj 파서(`web/tools/effect_vfxb.py`로 복사)의 섹션 순회는 그대로 맞지만 이미터 필드표는 맞지 않습니다. v46 필드표는 §2.2에서 nn::vfx 런타임 코드와 파티클 셰이더를 판독해 정했습니다(3차 작업에서 [미확정] → 주요 필드 [판독]).
- 셰이더(GRSN)는 파일 안에 있습니다(mpj와 다름). GRSN 본문은 **BFSHA 9.0 `GeneralShader`, 모델 `VfxGeneralShader`, 프로그램 6,285개, 정적 옵션 1,135개**이고 `shader_dump`로 역번역됩니다(§2.2.1) [실행].

## 2. 이미터셋 판독 [실행]

```sh
PY web/tools/effect_esetb.py tree  extracted/romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs
PY web/tools/effect_esetb.py ptcl  extracted/romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs analysis/effect_sound/static.vfxb
PY web/tools/effect_vfxb46.py eset analysis/effect_sound/static.vfxb WpShtrMzfNml WpShtrBullet1Emit ... --json analysis/effect_sound/esets_shooter.json
PY web/tools/effect_vfxb46.py bntx analysis/effect_sound/static.vfxb analysis/effect_sound/static_tex.bntx
```

중간 파일 `static.vfxb`(120 MB)와 `static_tex.bntx`(38 MB)는 디스크 절약을 위해 지웠습니다. 위 명령으로 다시 만들 수 있습니다.

`effect_vfxb46.py`는 이미터 바이너리 안에서 GTNT 텍스처 ID(u64 해시)와 같은 값을 찾아 샘플러 참조 후보로 냅니다. 8바이트 해시가 우연히 일치할 가능성은 매우 낮다고 봅니다.

| 이미터셋 | 쓰임 | 이미터 → 텍스처 |
|---|---|---|
| WpShtrMzfNml | 스플래시 슈터 머즐 플래시 | SplashCorn → splash09_fia, splash09_nrm / Flash → gradation02_fi, splash04_nrm, splash04_fi |
| WpShtrBullet1Emit | 슈터 탄(OneEmitter) | ball(속성 CSDP, CADP) → bulletshtr_vsp (형식 0x1505 = R16G16B16A16 FLOAT 6×83, §2.1에서 디코드) |
| CmnFloorSplash1Emit / Near / Dist | 칠할 수 있는 바닥 착탄 | Splash → splash06_fia, splash06_nrm / Crown → pattern01_fi, pattern01_nrm (세 종류 텍스처 같음, 파라미터 차이 미판독) |
| CmnNPFloorSplash1Emit | 칠할 수 없는 바닥 착탄 | Drip → splash00_fia/nrm / Splash → splash06_fia/nrm |
| CmnWallSplash1Emit | 벽 착탄 | Splash → splash06 / Ripple → pattern01 |
| WpCmnHit | 피격 공용(OneEmitter `Hit`) | Splash → splashpattern00_fi/nrm / SplashCorn → gradation02_fi, splash04 |
| WpCmnHitEffective | ELink `HitEffective` | HitMark → hitmark00_fi/fia / SplashCorn |
| GearInkDive | 독립 무기가 잉크에 빠짐 | crown, Splash, figure |

텍스처 표본 7장은 `analysis/effect_sound/tex/*.png`입니다(`graphics_bntx.py`의 parse/to_png를 이름 지정으로 호출). splash04_fi, splash06_fia, splash06_nrm, splash09_fia, pattern01_fi, gradation02_fi, splashpattern00_fi입니다. BC4/BC5 형식이고, splash06_fia는 잉크 방울 모양으로 정상 디코드되었습니다 [실행]. `_fia`/`_nrm`이 BC5 2채널이라 PNG에는 R/G만 의미가 있습니다. 팀 컬러는 런타임에 곱하는 것으로 봅니다 [추정].

### 2.1 부동소수 텍스처 0x15 (R16G16B16A16 FLOAT) [실행]

- 형식 값 0x1505의 상위 바이트 0x15는 nn::gfx 채널 형식 `R16_G16_B16_A16`, 하위 0x05는 FLOAT입니다. `graphics_bntx.py`가 쓰는 표와 같은 체계(BC1 = 0x1A)이고, 텍셀당 8 B는 imageSize로 확인됩니다(예 `splash05_vsp` 10×1126 → 147,456 B, 16 B/텍셀이면 180,160 B 이상 필요) [데이터].
- static 묶음의 이런 텍스처는 28장이고 이름이 전부 `_vsp`/`_vfp`로 끝납니다(`bulletshtr_vsp` 6×83, `bulletcmn_vsp` 8×64, `splash00..06_vsp`, `tohumanstandby_*_vfp` 등).
- 도구: `web/tools/effect_bntx_float.py` (graphics 소유 `graphics_bntx.py`는 고치지 않고 parse/deswizzle만 가져다 씀). `selftest` = 합성 블록선형 왕복 4/4 일치. `dump`가 float32 `.npy`, 채널별 정규화 미리보기 PNG, 범위 JSON을 냅니다.
- 표본 3장(`analysis/effect_sound/tex_float/`): `bulletshtr_vsp` RGB ∈ [−0.57, 0.59], A ∈ [−65504, 63104]; `splash06_vsp` RGB ∈ [−1.82, 1.70]; `bulletcmn_vsp` RGB ∈ [−1.40, 0.94]. NaN/Inf 없음.
- RGB가 모델 크기 정도의 작은 부호 있는 값이고 A가 half 범위 전체를 쓰는 것으로 보아 **정점 애니메이션 텍스처(VAT)**: RGB = 정점 위치(또는 변위), A = 압축된 법선 등으로 추정합니다. 가로/세로 축은 아래 3차 판독으로 확정(가로 = 시간, 세로 = 정점), A의 인코딩·용도는 [미확정]입니다.
- 웹: `.npy`를 `Float32Array`로 읽어 `THREE.DataTexture(…, RGBAFormat, FloatType)` 또는 HalfFloat로 올리면 됩니다. 원본 half 값을 그대로 쓰려면 디코드 전 u16을 `HalfFloatType`으로 넘깁니다.
- (3차 추가) 슈터 탄 `ball`의 정점 셰이더(프로그램 1383, `analysis/vfx/shader/p1383.vert`)는 `sysTextureSampler2`(= bulletshtr_vsp)를 `texelFetch(x = floor(너비 × frac(t × 사용자 유니폼 sysCustomShaderUniformBlock1.data[12].x / 너비)), y = sysTexCoordAttr.z(정점 번호))`로 이웃한 두 열을 읽어 선형 보간하고, A는 부호·지수를 직접 풀어 half 비트로 다시 짜는 코드입니다. 즉 **가로축 = 시간(프레임 열), 세로축 = 정점**입니다 [판독]. A의 최종 용도(법선 압축으로 추정)는 프래그먼트 쪽 판독이 남았습니다 [미확정].

- **2026-10-03 정정:** 위 반복 frac 식은 앞 clamp를 생략했다. 원본 시간은 끝 열에서 멈춘다. A는 compact normal이며 실제 fragment 법선 입력으로 이어진다. 아래 §2.1.1의 clamp·half 복원·방향식이 최신 결론 [판독]이다(solo_fx_audit §6.2에서 옮김). GPU 비트 실행 대조는 하지 않았다.

### 2.1.1 탄 ball VAT 적용식 (프로그램 1383) [판독]

원본 `analysis/vfx/shader/p1383.vert` 310–326행: `W = textureSize(sysTextureSampler2).x`, `k = sysCustomShaderUniformBlock1.data[12].x`, t = 파티클 나이(프레임).

```text
qtime = clamp(min(fma(t*k, 1/(W+0.00001), 0.00001), 0.99999), 0, 1)
f = W * fract(qtime)
x0 = trunc(f); x1 = (x0 < trunc(W-1)) ? x0+1 : x0
row = trunc(sysTexCoordAttr.z); blend = fract(f)
RGB = fma(RGB1-RGB0, blend, RGB0)           // 로컬 기하 위치
```

A는 알파가 아닙니다. half로 저장된 A를 float로 샘플한 값에서 half 비트 `h`를 다시 만듭니다(실제 샘플은 정상 범위 finite half). `e = trunc(log2(abs(A)))`, log2가 음수면 e를 한 번 더 줄입니다. `h = ((e+15)<<10) + trunc(fma(exp2(-e)*abs(A), 1024, -1024)) + (A<0 ? 0x8000 : 0)`.

```text
j = (h < 0x8000 ? h-0x400 : 0x8400-h) + 0x77ff
phi = j * 3.88322115
z = fma(j*2, -1.6276572e-5, 0.999983728)
x = abs(z)
a = fma(fma(fma(x,-0.0187293,0.0742610022),x,-0.2121144),x,1.5707288)*sqrt(1-abs(z))
theta = z<0 ? pi-2*a+a : a
normal = (sin(theta)*cos(phi), sin(theta)*sin(phi), z)
```

- 두 열의 normal을 각각 복호화한 뒤 선형 보간합니다.
- VAT RGB가 (0,0,0)이 아니면 ResEmitter+0xE4 × 원래 정점 normal을 더합니다(1383.vert의 temp120/129/135/136).
- 회전·동적 이미터 행렬을 거쳐 out_attr4로 보내고, fragment의 in_attr4가 실제 법선·조명 계산에 쓰입니다.
- **acos 근사 다항식이므로 재구현에서 임의로 acos나 normalize로 바꾸지 않습니다.**
- ResEmitter+0xE4의 모든 이미터 공통 의미는 [미확정]입니다.
- 검증: 실제 bulletshtr_vsp 83×6의 A half 498/498 비트 복원 [데이터 대조/재구현, `web/tools/completion_vat_normal_check.py`]. 원본 GPU 실행이 아니며 sin/cos/log2/exp2/FMA 비트 일치를 주장하지 않습니다.

## 2.2 VFXB v46 EmitterData 필드표 [판독 + 셰이더 판독 + 데이터]

### 2.2.1 근거와 도구

| 근거 | 내용 |
|---|---|
| nn::vfx 런타임 디컴파일 | `analysis/decomp/vfx/vfx_lib_00..02.c`(0x71007f0000–0x7100845000 함수 902개, 전체 분석판), `vfx_b1..3.c` |
| 런타임 객체 | 이미터 인스턴스 +0x250 = EmitterResource(0x470 B, 설정 0x710081aee4), EmitterResource +0x10 = **ResEmitter(파일 이미터 바이너리)**, +0x18 = ResEmitter+0x70(정적 블록). 이미터 인스턴스 +0xb0 = ResEmitter 사본(초기화 0x710080ca78) |
| 필드 사용처 스캔 | `web/tools/vfx_resfield_scan.py` → `analysis/vfx/resfield_uses.txt`(오프셋별 형·함수) |
| GPU 정적 UBO | 셰이더 블록 `sysEmitterStaticUniformBlock` 크기 **2704 B = 0xA90** = ResEmitter[0:0xA90] 통째. 역번역 GLSL의 `data[k]` = ResEmitter **+16·k** [판독: UBO 크기 + 셰이더 사용 위치가 데이터 값과 일치(아래)] |
| 셰이더 역번역 | GRSN의 BFSHA를 `analysis/vfx/static_grsn.bfsha`로 떼어 `shader_dump prog-bfsha … VfxGeneralShader - <출력> --index N`. 이미터 +0xC4C의 값이 프로그램 번호이고, 그 프로그램의 옵션(`_CALC_TYPE_*`, `_SCALE_ANIM_n_KEY` 등)이 이미터 데이터와 전부 맞습니다(아래 표의 "셰이더옵션") [실행] |
| 판독 도구 | `web/tools/vfx_emitter46.py raw/stat/fields/sim/selftest` |

재생성(중간 파일 120 MB·64 MB는 지웠음):

```sh
PY web/tools/effect_esetb.py ptcl extracted/romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs analysis/vfx/static.vfxb
PY web/tools/vfx_emitter46.py fields analysis/vfx/static.vfxb WpShtrBullet1Emit CmnFloorSplash1Emit CmnFloorSplashNear1Emit CmnFloorSplashDist1Emit CmnWallSplash1Emit WpShtrMzfNml --json analysis/vfx/emitters_v46_fields.json
# GRSN: Vfxb('static.vfxb').by_magic['GRSN'] 의 bin 부터 끝까지를 static_grsn.bfsha 로 저장
dotnet analysis/shader/build/bin/Release/net7.0/shader_dump.dll prog-bfsha C:/dev/splatoon3/analysis/vfx/static_grsn.bfsha VfxGeneralShader - analysis/vfx/shader/p1940 --index 1940
```

### 2.2.2 구역 배치 (ResEmitter 기준 오프셋)

v53(0x1100 B) 표와 순서는 같고, 정적 블록에서 키 개수 u32 8개(0x20 B)와 애니 키 표 4개(0x200 B)가 빠지며, 입자(Particle) 구역이 0x24 B 짧고 샘플러가 0x20 B 간격입니다.

| 구역 | v46 범위 | 확정 수준 · 앵커 |
|---|---|---|
| 머리 + 이름 | 0x000–0x070 | 이름 char[0x60] @0x10 [데이터] |
| 정적 블록(GPU UBO) | 0x070–0xA90 | UBO 크기·셰이더 위치 [판독] |
| EmitterInfo | 0xA90–0xB20 | calcType/seed/drawPath/페이드 [판독] |
| Inherit | 0xB20–0xB38 | 자식 생성에서 0xB2C·0xB30·0xB34 읽음 [판독-부분] |
| Emission | 0xB38–0xB80 | 0x710081b784·0x710081c0b8 [판독] |
| Shape | 0xB80–0xBD8 | 형상 함수 점프표 0x710540fea8(인덱스 = +0xB80) [판독] |
| Render | 0xBD8–0xBE8 | [추정: v53 순서] |
| Particle | 0xBE8–0xC30 | life/lifeRandom/momentum [판독] |
| Combiner | 0xC30–0xC40 | [추정] |
| ShaderRef | 0xC40–0xCF4 | +0xC4C 프로그램 번호 [실행: 옵션 일치] |
| Velocity | 0xCF4–0xD24 (+0xD24 상한) | 0x710081e3e4 [판독] |
| PColor | 0xD34–0xD60 | 색 종류 바이트 0xD3C–0xD3F [셰이더옵션] |
| PScale | 0xD60–0xD84 | 무작위 % 0xD6C–0xD74 [판독] |
| Samplers ×6 | 0xD90–0xE50 (0x20 간격, +0 u64 텍스처 ID) | [데이터: GTNT ID 일치] |
| TexAnim ×6, reserved | 0xE50–0xEF0 | [추정] |

### 2.2.3 필드표

이름은 **웹 권장 이름**(원본 이름 없음)입니다. 전체 목록과 근거 문자열은 `vfx_emitter46.py`의 `FIELDS`에 있습니다.

정적 블록(셰이더가 읽음, `data[k]`):

| 오프셋 | 형 | 웹 이름 | 근거 |
|---|---|---|---|
| 0x070 | u32 | staticFlags1 | data[7].x bit28/29/30 = 회전 X/Y/Z 무작위 반전(난수 > 0.5면 부호 반전) [판독] |
| 0x080 / 0x084 / 0x088 / 0x08C / 0x090 | u32 | numColor0Keys / numAlpha0Keys / numColor1Keys / numAlpha1Keys / numScaleKeys | 옵션 `COLOR_0_ANIM_n_KEY` 등과 9개 이미터 전부 일치 [셰이더옵션] |
| 0x0A0–0x0B0 | f32×5 | loopRate (color0, alpha0, color1, alpha1, scale) | > 0이면 애니 시간이 `frac((rand.x·loopRandom·loopRate + age)/loopRate)`로 반복, 0이면 `age/life` [판독: data[10].y, data[11].x] |
| 0x0B4–0x0C4 | f32×5 | loopRandom (같은 순서) | 반복 시작 위상 난수 배율 [판독: data[11].z, data[12].y] |
| 0x0D0 | f32×3 | gravityDir | data[13].xyz [판독] |
| 0x0DC | f32 | gravityScale | data[13].w [판독] |
| 0x0E0 | f32 | airRegist | data[14].x, CPU 0x7100826cb0도 같은 식 [판독] |
| 0x0E4 | f32 | (미상) | data[14].y, 정점 위치 보정에 곱함. 용도 [미확정] |
| 0x0F0 | f32×3 | pivotOffset | 정점 = (pos + 0.5·값)·scale [판독: data[15]] |
| 0x100–0x12C | | 흔들림(fluctuation) 진폭·주기·위상 | [추정: v53 순서] |
| 0x130 + 0x90·i | | 텍스처 패턴 애니 ×6 {num, freq, numRandom, pad, table[32]} | 표 0..31 [데이터] |
| 0x490 + 0x50·i | | 텍스처 스크롤 ×6 | data[73..82] 사용 [판독-부분], 필드 순서 [추정] |
| 0x670 | f32 | colorScale | data[103].x, CPU 정적+0x600 [판독] |
| 0x680 / 0x700 / 0x780 / 0x800 | {f32×4}×8 | color0 / alpha0 / color1 / alpha1 키 `{x,y,z,time}` | 알파는 `.x`가 값, `.w`가 시간(0..1) [판독: data[112..114]]. color1 [판독: data[120]], alpha1 [추정] |
| 0x880–0x8BC | | 소프트/프레넬/근·원거리 알파/데칼 파라미터 | [추정] |
| 0x8C0 | {f32×4}×8 | scale 키 `{sx,sy,sz,time}` | data[140..144] [판독] |
| 0x940 | | param 키 | [추정] |
| 0xA00 | f32×3 | rotateInit | [추정] |
| 0xA10 | f32×3 | rotateInitRand | `(rand−0.5)·값`을 GPU에서 더함 [판독: data[161]] |
| 0xA20 | f32×3 | rotateAdd (라디안/프레임) | data[162].xyz [판독] |
| 0xA2C | f32 | rotateRegist | data[162].w [판독] |
| 0xA30 | f32×3 | rotateAddRand | data[163] [판독] |

CPU 구역:

| 오프셋 | 형 | 웹 이름 | 근거 · 의미 |
|---|---|---|---|
| 0xA92 | u8 | calcType | 0 CPU, 1 GPU_TIME, 2 GPU_SO. 0이면 매 프레임 CPU 파티클 갱신 0x710081cb0c [판독 0x710081c0b8 + 셰이더옵션] |
| 0xA93 | u8 | followType | 0 → `FOLLOW_TYPE_ALL`, 1 → `NONE` [셰이더옵션]. 2 = POS [추정] |
| 0xA94 | u8 | randomSeedType | 0 전역 난수, 1 이미터셋 시드(set+0x5c), 2 고정: seed = randomSeed × 0xDFDC1C35 [판독 0x710080ca78] |
| 0xA95 | u8 | updateMatrixByEmit | 방출 간격마다 이미터 행렬 재계산 0x710080e4cc [판독] |
| 0xA99 / 0xA9B | u8 | fadeInCurve / fadeOutCurve | 0 끔, 1 선형, 2 제곱, 3 네제곱을 진행값에 적용 [판독 0x710080ec48/0x710080ecac] |
| 0xAA0 | i32 | randomSeed | [판독] |
| 0xAA4 | i32 | drawPath | 0x710080eb7c, 옵션 `DRAW_PATH_13` ↔ 13 [판독+옵션] |
| 0xAA8 / 0xAAC | i32 | fadeOutFrames / fadeInFrames | 진행값 += dt/fadeIn (0→1), 종료 요청 뒤 −= dt/fadeOut [판독 0x710081c0b8] |
| 0xAB0–0xAE8 | f32×15 | 이미터 trans, transRand, rotate, rotateRand, scale | 0x710080e4cc가 15개를 읽음 [판독], 순서 [추정] |
| 0xB18 / 0xB1C | f32 | fadeInMin / fadeOutMin | `min + p·(1−min)` (켜짐 바이트 0xA9A/0xA9C) [판독 0x710080ed10] |
| 0xB38 | u8 | hasEmitEnd | 0이면 무한 방출, 1이면 start+duration까지만 [판독] |
| 0xB39 | u8 | isWorldGravity | 옵션 `_WORLD_GRAVITY` 유무와 일치 [셰이더옵션] |
| 0xB3A | u8 | isEmitDistEnabled | 거리 기반 방출 분기 [판독 0x710081b784] |
| 0xB3B | u8 | isWorldOrientedVelocity | 지정 방향을 월드 기준으로 [판독 0x710081e3e4] |
| 0xB3C / 0xB40 / 0xB44 | u32 | emitStart(프레임) / emitTiming(자식: 부모 수명 %) / emitDuration(프레임) | [판독] |
| 0xB48 / 0xB4C | f32 / i32 | emitRate / emitRateRandom(%) | [판독] |
| 0xB50 / 0xB54 | i32 | emitInterval / emitIntervalRandom | 다음 간격 = interval + 1 + floor(u·intervalRandom) [판독 0x710080e9a4] |
| 0xB58 | f32 | positionRandom | 난수표(0x200개) 벡터 × 값을 위치에 더함 [판독] |
| 0xB5C | f32 | (방출 쪽 중력 배율) | 정적 0x0DC와 같은 값 [데이터], CPU 소비 미확인 |
| 0xB6C–0xB78 | f32 | emitDist unit / min / max / margin | [판독] |
| 0xB80 | u8 | volumeType | 형상 함수 점프표 인덱스 [판독], 번호별 형상 [미확정]. **5차:** 점프표 16칸 주소와 0·1번 식 [판독], 나머지 번호 이름 [추정] — §2.2.4.1 |
| 0xB88–0xBAC | f32 | sweepLongitude/Latitude/Start, caliberRatio, volumeRadius xyz | 형상 함수가 읽음 [판독-부분] |
| 0xBB0 | f32×3 | volumeFormScale | × 이미터셋 스케일 → 이미터+0x7f0 [판독] |
| 0xBE8 | u8 | infiniteLife | [판독] |
| 0xBEA / 0xBEB | u8 | billboardType / rotType | 3 POLYGON_XY, 4 POLYGON_XZ / 4 YZX, 6 ZXY [셰이더옵션]. **5차 조사:** POLYGON_XZ 변형(1886, 옵션 `_PARTICLE_TYPE_POLYGON_XZ_CONVERTER = 1`)의 정점 셰이더는 `sysPosAttr.x/.y/.z`를 축 교환 없이 `(sx·(x+0.5·pivot.x), sy·(y+…), sz·(z+…))`로 쓰고(vert 621–639), 회전(rotType 6)과 이미터 행렬만 곱합니다(vert 876–899). 따라서 XZ 배치는 셰이더가 아니라 **입력 쿼드 정점 버퍼**에서 결정됩니다. 그 버퍼를 만드는 nn::vfx 코드는 읽지 않아 축은 [미확정]입니다 |
| 0xBF8 / 0xBFC | i32 | life(프레임) / lifeRandom(%) | [판독] |
| 0xC00 | f32 | momentumRandom | m = 1 + r − 2·r·u [판독] |
| 0xC4C | i32 | shaderIndex | VfxGeneralShader 프로그램 번호 [실행] |
| 0xCF4 | f32 | allDirectionVel | × set+0x218 → 이미터+0x7cc [판독] |
| 0xCF8 | f32 | designatedDirScale | [추정] |
| 0xCFC | f32×3 | designatedDir | [판독] |
| 0xD08 | f32 | diffusionDirAngle(도) | 원뿔 안 cos을 [1 − a/90, 1]에서 균일 추출, φ = 2π·u [판독] |
| 0xD0C | f32 | xzDiffusion | 방출 위치의 XZ 방향(0이면 난수 방향) × 값을 속도에 더함 [판독] |
| 0xD10 | f32×3 | diffusionVel | 난수표 벡터 ⊙ 값을 더함 [판독] |
| 0xD1C | f32 | velRandom(%) | 속도 × (1 − u·값/100) [판독] |
| 0xD20 / 0xD24 | f32 | emitterVelInherit / 상한 | 이미터 이동량/dt × 값, 길이 > 상한이면 상한으로 [판독] |
| 0xD3C–0xD3F | u8 | color0Type, color1Type, alpha0Type, alpha1Type | 0 FIXED, 1 RANDOM, 2 ANIM [셰이더옵션] |
| 0xD40–0xD5C | f32×8 | color0 RGB, alpha0, color1 RGB, alpha1 | [추정: v53 순서. alpha1 값이 alpha1 키0과 같음(Splash 3.0)]. **2026-10-03 해소 [판독]:** D40 RGB = color0, D4C = alpha0, D50 RGB = color1, D5C = alpha1. 종류가 FIXED(0)이면 로딩 중 키0(0x680/0x700/0x780/0x800)에 복사(§2.2.7) |
| 0xD60 | f32×3 | particleScale | [추정] |
| 0xD6C | f32×3 | particleScaleRandom(%) | s·(1 − u·값/100). 세 값이 같으면 한 번 뽑은 u를 공유 [판독] |

### 2.2.4 방출·수명·초기 속도 (CPU) [판독]

```
// 방출 (0x710081c0b8 → 0x710081b784). 시간 단위 = 프레임, 난수 u = LCG(x*0x41c64e6d+0x3039) / 2^32, 이미터 +0xbc
active = start <= time && (hasEmitEnd == 0 || time < start + duration)
매 간격: count += rate * (1 - rateRandom/100 * u) * 이미터 배율 * 이미터셋 배율
          interval_next = (interval + 1 + floor(u * intervalRandom)) * 이미터 간격 배율 * 이미터셋 간격 배율
hasEmitEnd==1 이면 time > start + duration + maxLife(+ fadeOutFrames) 에서 이미터 종료
// 파티클 하나 (0x710081e3e4)
pos = shape(volumeType)(...) + randUnit[i&0x1ff] * positionRandom
vel = (shape 법선 * allDirectionVel) + designatedDirScale * coneSample(designatedDir, diffusionDirAngle)
      + (xzDiffusion ? normalizeXZ(pos) * xzDiffusion : 0)
vel = vel * (1 - u*velRandom/100) + randTable[j&0x1ff] ⊙ diffusionVel + emitterVelocity/dt * inherit (|.| <= 상한)
life  = int( L * (1 - floor(u*lifeRandom)/100) * 이미터셋 수명 배율 )    // infiniteLife 면 2.68e8
scale = 이미터셋 스케일 * 이미터 스케일 * particleScale * (1 - u*particleScaleRandom/100)
momentum = 1 + momentumRandom - 2*momentumRandom*u
```

형상 함수(점·구·원 등)의 세부 식과 셰이프 법선 정의는 판독하지 않았습니다(아래 대상 이미터는 전부 volumeType 0) [미확정].

#### 2.2.4.1 형상 함수 (5차, 2026-10-03)

호출 `0x710081e3e4` 안(vfx_lib_01.c 23553행): `ok = shape[ResEmitter+0xB80](&pos, &dir, emitter, i, n, emitter+0x760)`. 반환이 0이면 그 파티클을 만들지 않습니다. `dir`이 위 의사코드의 "shape 법선 × allDirectionVel"이고, 함수가 이미 이미터+0x7CC(= allDirectionVel × 이미터셋 배율)를 곱해 돌려줍니다 [판독].

점프표 `0x710540fea8` [판독, 디컴파일 `analysis/decomp/r5_fx/vfx_shapes.c`, 기존 `vfx/vfx_lib_01.c`]:

| 번호 | 함수 | 읽는 ResEmitter 필드 | 형상(이름) |
|---|---|---|---|
| 0 | `0x710081fa94` | — | 점 [판독] |
| 1 | `0x710081facc` | 0xB81, 0xB88, 0xB90, 0xBA4, 0xBAC | 원(XZ 평면) [판독] |
| 2 | `0x710081fcac` | + 0xB94, 0xBBC, 0xBC8, 0xBCC | 원 등분 [추정: 이름] |
| 3 | `0x710081ffb0` | + 0xB98 | 채운 원 [추정] |
| 4 | `0x71008202a4` | 0xB81/82/85/8C/90, 0xBA4/A8/AC | 구 [추정] |
| 5 | `0x71008207ec` | 0xB83(등분 표 `0x71054100f8`), 0xB85, 0xB8C, 0xBBC | 구 등분 [추정] |
| 6 | `0x7100820cbc` | 0xB84(표), 0xB85, 0xB8C, 0xBBC | 구 등분 64 [추정] |
| 7 | `0x7100821184` | 구 필드 + 0xB98 | 채운 구 [추정] |
| 8, 9 | `0x7100821730`, `0x71008217b8` | 0xBA8 | (원기둥 계열로 보이나 필드가 맞지 않음) [미확정] |
| 10, 11 | `0x7100821840`, `0x71008219f0` | 0xBA4/A8/AC (+0xB98) | 상자 / 채운 상자 [추정] |
| 12, 13 | `0x7100821c28`, `0x7100821cb0` | 0xB9C, 0xBA0 (+0xBD0/BD4/BBC) | 선 / 선 등분 [추정] |
| 14 | `0x7100821dec` | 0xBA4, 0xBAC | 사각형 [추정] |
| 15 | `0x7100821f34` | 0xBBC | 프리미티브 [추정] |

이름 [추정]은 nn::vfx(eft2) 형상 열거 순서와 필드 패턴이 맞는다는 것만 근거입니다. 사격장 표본 11이미터는 전부 0번입니다 [데이터]. 0번과 1번 식은 다음과 같습니다(이미터 = E, R = E+0xB0의 ResEmitter, S = E+0x760).

```
// 0 점 (0x710081fa94)
pos = (0,0,0,0)
k = E+0xBA (u16) ; E+0xBA = k+1
dir = T[k & 0x1ff] (vec4) × S+0x6C (= E+0x7CC)          // T = *0x71057d52f8 의 512개 vec4 표(런타임 생성, 내용 [미확정])

// 1 원 (0x710081facc), s0 인자 r(호출자 공급, 출처 [미확정])
θ = (R+0xB81 ? 2π·r : R+0xB90) + R+0xB88·u − R+0xB88·0.5       // u = E+0xBC LCG 현재값/2³², 그 뒤 E+0xBC = E+0xBC·0x41c64e6d+0x3039
s, c = sead sin/cos 다항식(θ를 [−π, π]로 접은 뒤)
pos = (s · R+0xBA4 · S+0x90, 0, c · R+0xBAC · S+0x98, 0)   // S+0x90/+0x98 = E+0x7F0/+0x7F8(volumeFormScale × 이미터셋 스케일)
dir = (s · S+0x6C, 0, c · S+0x6C, 0)
```

- 0번 점 형상은 위치가 항상 원점이고, 방향만 512개 표에서 순서대로 꺼냅니다. 표 내용은 런타임에 만들어지므로 웹은 같은 순서를 재현할 수 없습니다(연출값).
- sin/cos는 libm이 아니라 sead 다항식입니다(`_SinCoefficients`/`_CosCoefficients`).
- 2~15번의 세부 식은 [미확정]입니다. 다음에 볼 곳은 위 표의 함수들이고, 사격장 이펙트에서 0 이외 형상이 쓰이는지 전수 확인하는 것이 먼저입니다(표적 ELink 이미터셋 포함).

**6차(2026-10-03) 추가 [판독, 디컴파일 `analysis/decomp/r5_fx/vfx_shapes.c`]:** 12·13·14번 식을 읽었습니다. u = E+0xBC LCG 현재값/2³²(읽을 때마다 E+0xBC = E+0xBC·0x41c64e6d + 0x3039).

```
// 12 선 (0x7100821c28)     L = R+0xBA0 · S+0x98,  c = R+0xB9C
pos = (0, 0, L·u − (L + L·c)·0.5, 0)
dir = (0, 0, S+0x6C, 0)

// 13 선 등분 (0x7100821cb0)   n = R+0xBD0,  m = *(*(E+0x250)+0x10)+0xBBC (u32)
m == 2 : i = E+0x40 mod n;  E+0x40 = (E+0x40 + 1 < n) ? E+0x40 + 1 : 0     // 순차
m == 1 : i = trunc(u · n)                                                  // 무작위
그 밖  : i = (호출 인자 파티클 번호) mod n;  m == 0 이면 n = n − trunc(f32(R+0xBD4) · s0 · 0.01 · n)  // s0 = 호출자 인자
t = (n − 1 ≠ 0) ? i / (n − 1) : 0.5
pos = (0, 0, L·t − (L + L·c)·0.5, 0);  dir = (0, 0, S+0x6C, 0)

// 14 사각형 둘레(XZ) (0x7100821dec)   X = R+0xBA4 · S+0x90, Z = R+0xBAC · S+0x98
s0..s3 = LCG 연속 4개(E+0xBC는 4번 진행)
s0 < 0x7FFFFFFF : x = X·(2·s2/2³² − 1),  z = (s1 > 0x7FFFFFFE) ? −Z : Z      // 앞뒤 변
그 밖          : x = (s1 > 0x7FFFFFFE) ? −X : X,  z = Z·(2·s3/2³² − 1)      // 좌우 변
pos = (x, 0, z, 0);  dir = 정규화(pos) × S+0x6C (0 성분은 0으로 둠, SIMD 판독)
```

- 13번의 `m`과 `R+0xBD4`의 이름은 [미확정]입니다(eft2의 "분할 방출 방식"·"호 열림 %"와 배치가 비슷하나 이름 근거 없음).
- 2~11·15번 식은 여전히 [미확정]입니다. 사격장 표본 이미터는 전부 0번이라 슬라이스 웹에는 영향이 없습니다 [데이터].

### 2.2.5 파티클 운동·애니 (GPU_TIME 정점 셰이더, 프로그램 1940 판독)

```
t   = (현재 시각 - 탄생 시각) + dyn[2].w                  // 프레임
f(t)= airRegist==1 ? t : (1 - a^t)/(1 - a)
g(t)= airRegist==1 ? t^2/2 : (t - (a^t - 1)/ln a)/(1 - a)
G   = gravityScale * gravityDir  (WORLD_GRAVITY 면 월드 중력을 이미터 행렬 축으로 되돌려 로컬화)
P   = P0 + momentum * (V0 * f(t) + G * g(t))            // 이미터 로컬 → 탄생 시 이미터 행렬(sysEmtMat*)로 월드
tn  = loopRate>0 ? frac((rand.x*loopRandom*loopRate + t)/loopRate) : t / life
scale = keyLerp(scaleKeys, tn) * 탄생 스케일 * 이미터셋 동적 스케일(dyn[3].yzw)
alpha0 = (ANIM ? keyLerp(alpha0Keys, tn).x : alpha0Keys[0].x) * dyn[0].w
rot    = initRot(± 무작위 반전) + (rand-0.5)*rotateInitRand
       + (rotateAdd + (r1+r2-1)*rotateAddRand)(± 반전) * R(t),  R(t) = regist==1 ? t : (1 - r^t)/(1 - r)
keyLerp: tn < k0.time → k0, 키 사이 선형, 마지막 키 시간 이후 → 마지막 값
```

CPU 쪽 같은 식 `0x7100826cb0`(airRegist 보정 `a' = a + (1−f)(1−a)`, `(1 − a'^t)/(1 − a')`)도 판독했습니다. 이 함수의 f(이미터+0x50)가 무엇인지는 [미확정]입니다.

### 2.2.5.1 색·알파 입력과 프로그램별 조합 (solo_fx_audit §6.1·§6.3에서 옮김, 5차 보완) [판독]

**FIXED 패치.** 리소스 설정 `0x710082a29c` → `0x71008190fc`가 EmitterResource+0x10의 ResEmitter를 고칩니다. 종류 분기는 0x7100819214–0x7100819230, load/store는 0x7100819d5c–0x7100819db4입니다.

```text
if R[D3C] == 0: R[680:68C] = R[D40:D4C]  // color0 RGB
if R[D3E] == 0: R[700:704] = R[D4C:D50]  // alpha0
if R[D3D] == 0: R[780:78C] = R[D50:D5C]  // color1 RGB
if R[D3F] == 0: R[800:804] = R[D5C:D60]  // alpha1
```

따라서 파일의 color0 키0이 0이어도 PColor FIXED 값이 1이면 셰이더 입력은 1입니다. 파일을 처음 파싱한 JSON과 패치 뒤 원본 메모리 값은 다릅니다. `0x710081aee4`는 부가 섹션 포인터를 찾는 함수이고 FIXED 패치 본체가 아닙니다.

**정점 출력(공통 꼴).** 아래 C0/C1/A0/A1은 정점 셰이더가 만드는 값입니다. 1886·1747 정점 셰이더로 확인했습니다.
- C0 = color0(FIXED면 data[104] = +0x680, ANIM이면 키 보간) × `NnVfx2EmitterDynamicParam[0].rgb` × colorScale(data[103].x = +0x670)
- A0 = alpha0(키 보간 또는 FIXED) × dyn[0].w
- C1 = color1 × dyn[1].rgb × colorScale
- A1 = alpha1(data[128].x = +0x800) × dyn[1].w
- 알파 페이드 `fade` = 카메라 거리 근접 페이드(data[137].x/y = +0x890/+0x894 사이 0→1) × dyn[3].x
- 팀색을 dyn[0]/[1]에 쓰는 게임 호출자는 [미확정]입니다.

| 프로그램(이미터) | 조명 전 색 / 알파 | 근거 |
|---|---|---|
| 1940 바닥 Splash | `(T0.rgb·C0 + C1)·vRGB`; `a = clamp(T0.a·vA·A0, 0, 1)·dyn[3].x` | vert 882–921, frag 284–298·440–442 |
| 1897 바닥 Crown | `C0·vRGB`; `a = soft·clamp((T0.a·vA − A0)·A1, 0, 1)·dyn[3].x` | frag 288·295–297, alpha1 vert 991 |
| 1383 탄 ball | C0를 조명 입력으로 사용, `a = clamp(A0·in_attr2.w, 0, 1)·dyn[3].x`, 최종 Custom1[11].x/y로 fma 후 clamp | vert 499·529–531, frag 517 |
| **1886 벽 Splash (5차)** | `(T0.rgb·C0 + C1)·vRGB`·(Custom1[2]/[3] 보간 계수); `a = clamp((T0.a·vA − A0)·A1, 0, 1)·fade`, `a ≤ data[138].z(+0x8A8)`이면 discard, 출력 `clamp(fma(a, Custom1[11].x, Custom1[11].y), 0, 1)` | frag 283–293·476–479·616, vert 607–610·904–945 |
| **1747 머즐 SplashCorn (5차)** | `(T0.rgb·C0 + C1)`·(같은 보간 계수), 정점색 곱 없음; `a = clamp(T0.a·in_attr4.w·A0, 0, 1)·fade`, discard 같음, 출력 `clamp(fma(a, Custom1[11].x, Custom1[11].y), 0, 1)` | frag 282–293·474–476·509·623, vert 707–735 |

- 1940은 alpha1 고정 데이터가 있어도 이 알파식에 alpha1을 읽지 않습니다.
- 1897·1886은 alpha0을 **빼고** alpha1을 곱합니다. 벽 Splash(1886)는 alpha1 FIXED 3, alpha0 ANIM 0→1이라, 수명이 갈수록 마스크가 깎이는 모양입니다 [판독 + 데이터].
- texture0 **A**를 쓰는 경로를 단순 texture R 마스크로 바꾸면 원본과 다릅니다.
- 최종색은 이 입력 뒤 법선 텍스처·SH·주광·동적광·안개를 거칩니다.
- 1747의 정점 셰이더는 location 4를 쓰지 않습니다. 그래서 프래그먼트의 `in_attr4.w` 값은 [미확정]입니다(하드웨어 기본값에 의존).
- 1885(벽 Ripple)과 1202(머즐 Flash)는 역번역하지 않았습니다 [미확정].
- 이 표는 6,285개 프로그램 전체의 일반식이 아닙니다.

### 2.2.6 웹 재현값 (슈터 탄 + 착탄 스플래시)

`analysis/vfx/emitters_v46_fields.json`(전체 필드), 아래는 웹 파티클에 필요한 값만 뽑은 것입니다 [데이터].

| 이미터셋/이미터 | calc | follow | 수명(±%) | 방출 | V0(로컬) | 중력 | 크기(±%) | 회전 | 빌보드 |
|---|---|---|---|---|---|---|---|---|---|
| WpShtrBullet1Emit/ball | CPU | ALL | 120 | 1개 | 0 | 0 | (0.5,0.1,0.5) ±30 xz | Y 무작위 2π, 추가 −0.349 rad/f ±0.087, regist 0.99 | POLYGON_XY, YZX, 프리미티브 + VAT |
| WpCmnBulletSplash1Emit/ball_Copy1 (분열 탄, 6차) | CPU | ALL | 120 | 1개 | 0 | 0 | (1,1,1) ±30 xz, 피벗 (0,0,0) | X·Z 무작위 2π, 추가 (0.0175,0,0) rad/f, 추가 무작위 (0,0.157,0), regist 0.99 | 빌보드 3·rotType 4(탄과 같음), VAT `bulletcmn_vsp`, 프로그램 1385 |
| CmnFloorSplash1Emit/Splash | GPU_TIME | NONE | 14 (−0..24%) | 1개 | 0.02·(0,1,0) | 0.005 월드 −Y | (1.5,0.8,1.5) ±25 y | Y 무작위 2π | POLYGON_XY, YZX |
| CmnFloorSplash1Emit/Crown | GPU_TIME | NONE | 12 | 1개 | 0 | 0 | (2.4,0.5,2.4) ±20 xz | Y 무작위 2π | POLYGON_XY |
| …Near1Emit/Splash · Dist1Emit/Splash | 같음 | | 14 ±25 | 1개 | 같음 | 같음 | 같음 | Y 무작위 π / 2.618 | |
| CmnWallSplash1Emit/Splash | GPU_TIME | NONE | 14 ±20 | 1개, 위치 ±0.1 | 0.03·(0,1,0) | 0.02 월드 −Y | (2.1,0.4,2.1) ±39 y | Z 무작위 2π | POLYGON_XZ, ZXY |
| CmnWallSplash1Emit/Ripple | GPU_TIME | NONE | 8 | 1개 | 0 | 0.02 | (1.95,0.2,1.95) ±20 xz | Z 무작위 2π | POLYGON_XZ |
| WpShtrMzfNml/SplashCorn | GPU_TIME | ALL | 6 | **무한**, 시작 2, 5프레임마다 1개 | 0 | 0 | (0.7,3.0,0.7) ±30 y | Y·Z 무작위 2π | POLYGON_XY |
| WpShtrMzfNml/Flash | GPU_TIME | NONE | 5 | **무한**, 시작 2, 7프레임마다 1개 | 0 | 0.0029 | (0.6,0.6,0.6) ±40 | Y·Z 무작위 2π | POLYGON_XY |

애니 키(시간 = 수명 비율):

| 이미터 | scale 키 {sx,sy,sz @t} | alpha0 키 {a @t} | 기타 |
|---|---|---|---|
| ball | (0.439,1,0.439)@0 → (0.99,1,0.99)@0.17 → (0.3,1,0.3)@1 | FIXED 1.5 | alpha1 FIXED 8, colorScale 2 |
|  | **정정(2026-10-03, 6차):** 위 ball 행의 FIXED 값은 파일 키0(1.5 / 8)을 그대로 적은 것입니다. ball도 색 종류 0xD3C~0xD3F가 전부 0(FIXED)이라 §2.2.5.1 FIXED 패치로 키0이 PColor로 바뀝니다 → **alpha0 = 0xD4C = 1.0, alpha1 = 0xD5C = 5.0** [판독(패치 규칙) + 데이터(`vfx_emitter46.py raw`)]. 이전 값은 기록으로 남깁니다 | | |
| ball_Copy1 (분열 탄, 6차) | (0.67)@0 → (1.955)@0.33 → (1.955)@1 (세 축 같음) | **FIXED 1.0**(색 종류 0xD3C~0xD3F 전부 0 → FIXED 패치로 키0 = PColor 0xD4C = 1.0. 파일 키 0.6@0 → 2.5@0.05 → 0.5406@1은 쓰이지 않음) | alpha1 **FIXED 3.0**(0xD5C), color0·color1 FIXED (1,1,1), colorScale 2, fadeIn 10·fadeOut 3(curve 1) 프레임 |
| Floor Splash | (0.75,1,0.75)@0 → (0.9185,1.28,0.9185)@0.11 → (1.05,1.45,1.05)@0.33 → (1.1,0.9185,1.1)@0.66 → (1.1,0,1.1)@1 | 5@0 → 1@0.45 → 0.7857@1 | alpha1 FIXED 3 |
| Near Splash | …@0.33 (1.05,1.45,1.12) → (1.17,0.9185,1.37)@0.66 → (1.23,0,1.59)@1 | 같음 | z쪽으로 늘어남 |
| Dist Splash | …@0.33 (1.09,1.45,1.15) → (1.28,0.9185,1.39)@0.65 → (1.45,0,1.65)@1 | 같음 | 더 넓게 퍼짐 |
| Floor Crown | (0.3,1.7,0.3)@0 → (0.8,1,0.8)@0.25 → (1,0.2,1)@1 | 0@0 → 0.3@0.21 → 1@1 | color0 2@0.1 → 1@0.5, alpha1 3@0.2 → 0@1 |
| Wall Splash | (0.5,0.5,0.5)@0 → (1,1,1)@0.55 → (1.4,1.3,1.4)@1 | 0@0 → 1@1 | alpha1 FIXED 3, color1 ANIM(키 2개) |

Floor/Near/Dist(§3.1의 kind 0/1/2) 차이는 **Splash의 Y 회전 무작위 폭(2π/π/2.618)과 scale 키의 z 늘어남, Crown의 scale 키**뿐이고 수명·속도·중력은 같습니다 [데이터]. 이미터셋 행렬(§3.1의 info 행렬)의 축 배치에 따라 z 늘어남이 탄 진행 방향이 됩니다 [추정]. **5차 정정:** 행렬의 로컬 Z = 면에 투영한 진행 방향은 [판독]이지만, Y 초기 회전 난수 때문에 늘어남 방향은 진행 방향 주위로 흔들립니다(§3.1 끝).

재구현 표: `PY web/tools/vfx_emitter46.py sim analysis/vfx/emitters_v46_fields.json CmnFloorSplash1Emit/Splash` → `analysis/vfx/sim_CmnFloorSplash_Splash.txt`(로컬 y 최고 0.04 @ t=4, t=14에 −0.21, scale y 0) [재구현 계산].

## 3. 탄 파티클 OneEmitter 관리자 [판독]

탄은 액터별 이펙트 대신 **이미터셋 하나를 여러 인스턴스가 공유하는 관리자**로 그립니다.

| 항목 | 값 |
|---|---|
| 싱글턴 포인터 | `[0x7105850618]` (GOT 0x7105797f10), vtable 0x71055b7bd8 (슬롯 4 init 0x71018b4bac, 5·6 갱신 → 0x71018b3348, 7 0x71018b4d9c) |
| 팀별 관리자 | `inst + 8 + team·0x15e8` (team 0,1,2. -1과 3은 무시. 3 이상은 team 0 주소) — 3개를 init이 `0x71018b2cc0(mgr, heap, team)`으로 만듦 |
| 핸들 풀 | `inst + 0x41c0`: 0x1800개, 원소 0x10 B `{u64 owner, u32 nextFree, u32 generation}`, 잠금 +0x4200 |
| 슬롯 | 0x100 B(탄) / 0x60 B(착탄) 간격. `0x710137f020(slot, n, heap)`이 인스턴스 버퍼 n×0x60 B를 할당. `0x710137f144(slot, name, count, 0)`이 이름으로 이미터셋을 찾아 생성(최초 갱신 때 지연 생성, 0x71018b3348) |

슬롯 표(관리자 기준 오프셋, 버퍼 n, 생성 count = slot+0xB8):

| 오프셋 | 이미터셋 | n | count | 사용 탄(갱신 함수) |
|---|---|---|---|---|
| 0x000 | WpShtrBullet1Emit | 40 | 100 | BulletShooterBase vt106 0x7101753bb4 |
| 0x100 | WpSlshBullet1Emit | 80 | 120 | 0x710177262c 계열 |
| 0x200 | WpSlshBathtubBullet1Emit | 16 | 96 | 0x7101775a24 계열 |
| 0x300 | WpRllrBullet1Emit | 80 | 120 | 0x7101702ea4 |
| 0x400 | WpShltBullet1Emit | 80 | 240 | 0x710173c5fc, 0x710175657c 계열 |
| 0x500 / 0x600 | WpBulletStrn1st1emit / 2nd1emit | 12 / 12 | 144 / 144 | 0x7101890eec (스트링어) |
| 0x700 | WpBulletStrnTail1emit | 120 | 400 | |
| 0x800 | WpCmnBulletSplash1Emit | 40 | 160 | 0x71017ffc30, 0x710180c210 |
| 0x900 | WpChrgBulletSplash1Emit | 28 | 96 | 0x710180489c |
| 0xA00 | WpShtrBullet1Emit (두 번째) | 12 | 120 | 0x7101850364 (탄 종류 미확인) |
| 0xB00 | WpSlshLunchSplash1Emit | 36 | 288 | 0x71018170a8 |
| 0xC00 | SpRainBullet | 40 | 600 | 0x71017f3760, 0x71017f6898 |
| 0xD00 | WpsTakoBullet1Emit | 12 | 96 | 0x7101807b34 |
| 0xE00 | StaffrollBullet1Emit | 1 | 256 | 0x710188f208 |
| 0x1100 + k·0xC0 + p·0x60 | 착탄 바닥 스플래시(§3.1) | 40 | 80 | 0x71018b4f74, 속도 0이면 분배 함수가 직접 |
| 0x1340 / 0x13A0 | CmnNpWallSplash1Emit / CmnWallSplash1Emit | 40 | 80 | 히트 분배 0x71027b877c가 법선 y ≤ 0.64144969일 때 직접 추가(잠금 mgr+0x10A0 + p·0x40) [판독] |
| 0x14C0 | WpCmnHit (E2 `Hit`) | 40 | 80 | 히트 분배(잠금 +0x1420) |
| 0x1520 | WpCmnWaterSplash (E2 `SplashWater`) | 40 | 80 | 히트 분배(잠금 +0x1460) |
| 0x1580 | StaffrollBulletSplash1Emit | (별도) | 4 또는 80 | 0x710188ea88 |

n과 count의 정확한 의미(인스턴스 최대 수 / 파티클 수)는 이름이 없어 [추정]입니다. 각 탄의 갱신 함수는 `0x71018b22a4(slot, bullet+0x140 handle)`로 인스턴스 데이터(위치 등)를 씁니다.

**5차(2026-10-03) 슬롯 사용 탄 클래스 [판독]** (함수가 든 vtable을 `effect_ptrscan.py`로 찾고 `class_info.py`로 클래스 범위 확인):

| 슬롯 | 갱신 함수 | 탄 클래스 | 근거 |
|---|---|---|---|
| 0x000 WpShtrBullet1Emit | `0x7101753bb4` | `spl::BulletShooterBase` vt106 | 기존 판독 |
| **0x800 WpCmnBulletSplash1Emit** | **`0x71017ffc60`** | **`spl::BulletSplashShooter`(vt 0x71055af4c8) vt106**. vt15 `0x71017ffc30`가 vt106을 부르는 래퍼이고, 이 래퍼는 12개 BulletSplash* vtable에 있음 | 명령 `0x71017ffca0 add x0, x8, #0x800` |
| 0x800 (같은 슬롯) | `0x710180c210` | `spl::BulletSplashRollerBrushNearest` vt81 | vtable 0x71055ae648 범위 |
| **0xA00 WpShtrBullet1Emit(두 번째)** | `0x7101850364` | **`spl::BulletSprinklerInk`**(vtable 0x71055b2d30 슬롯 81) — 슈터 탄이 아님 | vtable 범위 |

- **슈터 분열 탄(BulletSplashShooter)은 `WpCmnBulletSplash1Emit` 슬롯(0x800)으로 그립니다.** impl/fx의 "분열 탄은 WpShtrBullet1Emit로 그림(0xA00 추정)"은 원본과 다릅니다. 팀 −1·3이면 건너뛰고, 팀 0~2만 팀별 관리자를 씁니다.
- `WpCmnBulletSplash1Emit`의 이미터 필드는 아직 뽑지 않았습니다(`vfx_emitter46.py fields`에 이름을 추가해 다시 실행해야 함) [미확정].
- **6차(2026-10-03) 해소 [데이터]:** `PY web/tools/vfx_emitter46.py fields analysis/assets_work/r6/static.vfxb WpCmnBulletSplash1Emit WpShtrBullet1Emit --json analysis/completion/r6/fx_splash1emit_fields.json`. 이미터는 `ball_Copy1` 하나이고 속성 CSDP·CADP, VAT 텍스처 `bulletcmn_vsp`(슈터 탄은 `bulletshtr_vsp`), 셰이더 프로그램 1385(슈터 탄 1383)입니다. 값은 §2.2.6 표에 넣었습니다.
- **벽 낙하 방울(`spl::BulletWallDrop`, vtable 0x71055b77d0, 81슬롯)에는 OneEmitter 갱신 슬롯(vt106)이 없습니다.** OneEmitter 관리자 GOT(0x7105797f10)를 참조하는 함수 24개를 전수로 봤는데, 그중 WallDrop 함수(0x71018ac000~0x71018b0000)는 없었습니다 [판독: 부재 확인]. 그래서 벽 낙하 방울은 이 탄 파티클 관리자로 그리지 않습니다. 다른 표시 경로(ELink, 모델 등)가 있는지는 [미확정]입니다.

### 3.1 착탄 스플래시 분류 `0x71018b4f74(inst, team, θ(s0), info(x2), paintable(w3))`

```
if team == -1 || team == 3: return
mgr  = inst + 8 + (team < 3 ? team*0x15e8 : 0)
a    = π/2 - |π/2 - θ|                       // 상수 0x3fc90fdb = 1.5707964
kind = a < T0 ? 0 : (a >= T1 ? 2 : 1)        // T0 = 0.5235988 (30°), T1 = 1.0471976 (60°), 정적 초기화 0x71018b2278
p    = paintable & 1
slot = mgr + 0x1100 + kind*0xC0 + p*0x60      // 이름: p=0 CmnNP*, p=1 Cmn*; kind 0 FloorSplash, 1 FloorSplashNear, 2 FloorSplashDist
잠금(slot 기준 +0x20) 후 슬롯 이미터셋이 살아 있으면:
  info 의 f32 12개(3×4 행렬로 보임)를 열/행 바꿔 인스턴스 하나 추가 (0x7100817b28)
```

- 호출자는 `0x71027b9978` 하나이고, 히트 분배 **`0x71027b877c`** 안입니다(※ 1차 문서의 `0x71027b84e0`은 다른 함수라 정정. [effect_sound.md](effect_sound.md) §3.5). paintable = 요청 +0x3C.
- **θ = atan2(|v̂ × n|, v̂ · n)**: 탄 속도 방향 v̂와 면 법선 n 사이 각(0..π) [판독]. 정면으로 꽂히면 θ ≈ π → a ≈ 0 → Floor, 스칠수록 a → π/2 → Dist. 속도가 0이면 이 함수를 부르지 않고 분배 함수가 θ = 0과 같은 슬롯(kind 0)·고정 행렬로 넣습니다.
- 법선 y ≤ 0.64144969이면 이 함수 대신 벽 슬롯(0x1340/0x13A0)으로 갑니다.
- 행렬 인자(info)는 v와 n으로 만든 회전(법선 기준 기울기 + 진행 방향 yaw)과 위치입니다. 정확한 축 배치는 `analysis/decomp/network/net_player.c`의 `0x71027b877c` 본문을 그대로 옮겨야 합니다 [판독, 식 미정리].
- **5차(2026-10-03) 식 정리 [판독]** (fx 구현 담당이 같은 본문에서 판독한 SHARED.md `[fx impl]` 줄을 이 문서로 연결):
  - 벽(n.y ≤ 0.64144969): A = asin(n.y), B = acos(−n.z/|n_xz|)(n.x ≥ 0이면 −B), R = Ry(B)·Rx(A). 로컬 −Z가 n이고, n = (0,0,−1)이면 단위 행렬입니다.
  - 바닥(|v| > 0): a1 = asin(−n.x), a2 = ±acos(n.y/|n_yz|), c = v×n(v는 정규화 전 속도, |v·n| > 0.99999면 (0,0,1)), a3 = d = n×c와 g = n×(Ẑ×n) 사이 각. 결과는 Y = n, Z = 면에 투영한 진행 방향(Ry(a3))입니다. rodata 0x7104997a00 = (−0, 0, 1).
  - |v| = 0이면 bss 0x71058237b0 고정 행렬을 씁니다. 그 값(정적 초기화)은 [미확정]입니다.
  - 재구현 대조는 `web/games/splatoon3/client/audio/selftest.mjs`의 합성 검증(벽 −Z = n 3건, 바닥 Y = n·Z = 투영 진행 방향)뿐이고, 원본 실행은 아닙니다.
- 그래서 §2.2.6의 Near/Dist scale 키 z 늘어남은 행렬상 **진행 방향 축(로컬 Z)**에 놓입니다. 다만 Splash 이미터의 Y 초기 회전 난수(rotateInitRand.y: Floor 2π, Near π, Dist 2.618)가 `(u − 0.5)·폭`으로 더해집니다. 그래서 실제 늘어남 방향은 진행 방향을 중심으로 Floor ±π(사실상 무작위), Near ±π/2, Dist ±1.309 rad 안에서 흔들립니다 [판독 + 데이터].
- "Near/Dist" 이름은 비스듬히 스친 탄(Dist)이 멀리 퍼지는 스플래시라는 뜻으로 보입니다 [추정].

## 4. HitEffectConfig [판독 + 데이터]

- 위치: Bootup 팩 `System/CombinationDataTableData/Default_spl__HitEffectConfig.pp__CombinationDataTableData.bgyml`, TableType `spl__HitEffectConfig.pp__CombinationDataTable`. 행 48개, 열 17개입니다.
- 셀 `$type spl__HitEffectCell`: `RowKey`, `ColumnKey`, `E1`, `E2`, `S1`, `S2`. 필드가 없는 것과 빈 문자열 `""`이 구분되어 저장돼 있습니다. 빈 문자열은 "명시적으로 없음"으로 봅니다 [추정].
- 로더 `0x71027b5980`: 셀 이름을 `"%s___%s_%s"`(행___반응_대상)으로 찾고, 없으면 `"%s___%s_Default"`로 다시 찾습니다. E2는 `"Hit"`, `"SplashWater"`(그 외 `"Splash"`)와 문자열 비교해 코드 쪽 종류로 바꿉니다. 사용자 이름 `"HitEffect"`, 속성 `"SubjectiveType"`을 참조합니다.
- 행: Blaster, Charger, Shooter, Shooter_CriticalHit, Roller, Slosher, Spinner, Bomb* 등 48개. 열(반응_대상): Aggregated / Armored / Constant / Cure / Damaged / Invincible / NetPriorityFailure × Default / BlowerInhale / Barrier / KebaInk / Water / CoopFloat / Shield.

ELink `HitEffect` 사용자(E1 키 15개, 이름은 키 → 이미터셋): HitEffective → WpCmnHitEffective, HitEffectiveNoSplash, HitCritical(진동 PresetDoka.bnvib), HitCriticalShield, HitMiddleCritical(Scale 0.8, LifeScale 0.5), HitInvalid → WpCmnHitInvalid, HitInvalidKebaInk, SplashSame / HitEffectiveSame / HitInvalidSame(EmissionRate 커브), HitBlowerInhole, BombSplashWater, BigSplashWater, BigSplash.

SLink `HitEffect` 사용자(콜 테이블 302개, 로컬 속성 `AggregateNum, IsPaintable, SubjectiveType, Velocity`) 트리 전체는 `analysis/effect_sound/hiteffect_slink_tree.txt`에 있습니다. 슈터 관련 부분:
- `ヒット`: Switch AggregateNum. 1 → `HitEf_Damage_00`. 2 → Sequence 2회. 3 이상 → Sequence 3회. 그룹 BulletHit_ToObject/Aggregated, 감쇠 HitEffect, DistCoef 30.
- `インク被弾`: Switch SubjectiveType. NotEqual Focused → Random 4종 `HitEf_InkHit_Splash_00..03`(weight 0.5씩, InkSpray_NotFocused, LowSensi, DistCoef 8).
- `インクヒット`: Switch SubjectiveType → Focused: Switch IsPaintable → Blend → Switch Velocity(> 0.9 강 / 기본 약) → Random 10종 등.
- `水没`: Random2 8종 `HitEf_InkHit_WaterIn_00..07`, Volume = Curve(Velocity).

## 5. 웹 구현

```ts
class BulletParticleMgr {                 // 원본 싱글턴 0x7105850618
  teams = [0,1,2].map(t => new TeamSlots(t));     // 팀 잉크 색은 graphics 의 TeamColor 표
  acquire(): Handle; release(h: Handle);          // 0x1800 풀
  updateBullet(team: number, slotOfs: number, h: Handle, pos: Vec3) { if (team<0||team===3) return; ... }
  emitSplash(team: number, theta: number, mtx: Mat34, paintable: boolean) {
    if (team === -1 || team === 3) return;
    const a = Math.PI/2 - Math.abs(Math.PI/2 - theta);
    const kind = a < 0.5235988 ? 0 : (a >= 1.0471976 ? 2 : 1);
    this.teams[team < 3 ? team : 0].splash[kind][paintable ? 1 : 0].push(mtx);
  }
}
```

- 렌더러는 슬롯마다 인스턴스 메시 하나와 텍스처 한 벌로 시작합니다. 수명·크기·속도·애니는 §2.2.6 값과 §2.2.5 식을 그대로 씁니다(3차에서 임시값 → 판독값).

```ts
// GPU_TIME 파티클 하나 (정점 셰이더 1940 판독 식). e = emitters_v46_fields.json 의 한 항목
function particleState(e: Emitter, p: {p0: Vec3, v0: Vec3, birth: number, life: number, m: number, s0: Vec3, rnd: Vec4}, now: number) {
  const t = now - p.birth;                                  // 프레임
  if (t < 0 || t >= p.life) return null;                    // 셰이더도 이 조건에서 화면 밖으로 버림
  const a = e.airRegist;
  const f = a === 1 ? t : (1 - a ** t) / (1 - a);
  const g = a === 1 ? 0.5 * t * t : (t - (a ** t - 1) / Math.log(a)) / (1 - a);
  const pos = add(p.p0, scale(add(scale(p.v0, f), scale(e.gravityDir, e.gravityScale * g)), p.m)); // 이미터 로컬
  const tn = e.loopRate[4] > 0 ? frac((p.rnd.x * e.loopRandom[4] * e.loopRate[4] + t) / e.loopRate[4]) : t / p.life;
  const sc = mul(keyLerp(e.scaleKeys, e.numScaleKeys, tn), p.s0);
  const alpha = e.alpha0Type === 2 ? keyLerp(e.alpha0Keys, e.numAlpha0Keys, t / p.life)[0] : e.alpha0Keys[0][0];
  return { pos, sc, alpha };                                 // 월드 = 탄생 시 이미터 행렬 * pos (follow NONE)
}
```

- 수명은 정수 프레임입니다(`int` 절삭). 난수는 원본 이미터 LCG(`x*0x41c64e6d+0x3039`)를 쓰면 같은 시드에서 같은 값이 나오지만, 시드(randomSeedType 0 = 전역 xorshift 상태)는 기기마다 달라 웹은 아무 난수기나 써도 됩니다(연출).
- 각도 비교는 f32입니다. 경계(정확히 30°/60°)를 원본과 맞추려면 `Math.fround`로 계산합니다. 30°는 `<`, 60°는 `>=`입니다.

검증 기대값: θ = 0.1745(10°) → kind 0, 0.7854(45°) → 1, 1.3963(80°) → 2, 2.9671(170°) → 0. team 3 → 무시.

## 6. 미확정

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| VFXB v46 EmitterData 필드(0xEF0 B) | **주요 필드 해소** [판독+셰이더옵션] §2.2. 구역 배치·방출·수명·속도·중력·airRegist·크기/색/알파 키·회전·calcType·follow·빌보드 | 남은 것: 형상(volumeType)별 위치·법선 식, Render/Combiner/TexAnim 바이트, 0x0E4·0xB5C 용도, 색 FIXED 값의 출처(Splash는 color0 키0이 0인데 PColor 0xD40은 1 — 런타임 UBO 패치 여부), 흔들림·스크롤 필드 순서. 다음 근거: 0x710540fea8 형상 함수들, 0x710081aee4(기존 UBO 복사·패치 후보), 프래그먼트 셰이더. **2026-10-03 정정:** FIXED 출처는 `0x71008190fc`의 PColor → 키0 패치로 해소(§2.2.5.1, 이전 solo_fx_audit §6.1). **5차:** 형상 0·1번 식과 점프표(§2.2.4.1), 1886/1747 색·알파(§2.2.5.1) 추가. 나머지는 유지 |
| VAT 텍스처(bulletshtr_vsp) 축 | **해소** [판독] §2.1(가로 = 시간, 세로 = 정점) | 이전 A 채널 용도 미확정은 **2026-10-03 해소**: compact normal → fragment 법선, §2.1.1(이전 solo_fx_audit §6.2). GPU 비트 실행 미검증 |
| 텍스처 형식 0x15 | **해소** [데이터] §2.1 (기존 [실행]은 디코더 자체 실행) | 이전 VAT 판독 필요 중 ball1383 해석은 2026-10-03 [판독] 해소. 다른 VAT 프로그램은 별도 |
| θ 정의, 벽 스플래시 슬롯, E2 Splash 의 슬롯 | **해소** [판독] §3.1 | — |
| OneEmitter n/count 의미, 인스턴스 0x60 B 레이아웃 | [미확정] | 0x71018b22a4, 0x7100817b28, 0x710137f558 |
| 슬롯 사용 탄(0x800 분열 탄, 0xA00) | **5차 해소** [판독] §3: 0x800 = BulletSplashShooter vt106, 0xA00 = BulletSprinklerInk. **6차:** WpCmnBulletSplash1Emit 필드 추출 [데이터] §2.2.6 | — |
| 벽 낙하 방울 표시 | OneEmitter 경로 없음 [판독: 부재 확인] §3 | BulletWallDrop의 ELink·모델 표시 여부 |
| 형상 함수(volumeType) | 점프표 16칸·0번(점)·1번(원) 식 [판독], **6차: 12 선·13 선 등분·14 사각형 둘레 식 [판독]**, 2~11·15 식 [미확정] §2.2.4.1 | 0x710081fcac~0x7100821840, 0x7100821f34, 표 0x71057d52f8 생성 |
| 색·알파 조합 | 1940/1897/1383 [판독] (solo_fx_audit에서 옮김), 1886/1747 [판독] §2.2.5.1 | 1885·1202 역번역, dyn[0]/[1] 팀색 writer |
| POLYGON_XZ 축 | 셰이더는 축 교환 없음 [판독], 입력 쿼드 버퍼 축 [미확정] | nn::vfx 쿼드 정점 버퍼 생성 코드 |
| Mission 묶음 로드 시점 | [미확정] | EffectFileInfo BinaryDict 소비 코드. **5차:** BinaryDict 56항목은 전부 미션·이벤트·NPC·보스 액터이고, 사격장(Lby_Lobby00)·플레이어·무기·SighterTarget은 없음 [데이터] → 사격장 범위 밖 |

### 2026-10-03 잔여 필드 판독 보완

alpha1의 값 = .x, 시간 = .w는 1897.vert data[128]/[129] → out_attr1.w로 확정됐다. FIXED 네 채널은 `0x71008190fc`가 PColor 값으로 키0을 패치한다. §2.2.3의 고정 RGB/alpha 값 출처 [추정]은 load/store 판독으로 해소됐다(본문 §2.2.5.1로 옮김, 2026-10-03 5차).
