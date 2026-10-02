# 사운드 리소스 — BARS / AMTA / BWAV / Stream / Alto 설정

SLink가 고른 사운드 이름(`RuntimeAssetName`)이 실제 파형까지 이어지는 경로와 파일 형식, 웹 재생 방법을 다룹니다. 상위 문서는 [effect_sound.md](effect_sound.md)입니다.

이 게임은 nn::atk(FSAR) 대신 **Alto(aal)** 사운드 계층을 씁니다. main 문자열에 `alto__AltoConfig`, `AalConfig`, `alto__SLinkConfig`가 있습니다 [데이터].

---

## 1. 파일 구성 [데이터]

| 경로 | 개수 | 내용 |
|---|---|---|
| `Sound/Resource/*.bars.zs` | 533 | 사운드 묶음. 액터·무기·장면 단위(예: `WeaponShooterNormal.bars.zs`, `Shooter.bars.zs`, `HitEffect.bars.zs`) |
| `Sound/Resource/Stream/*.bwav` | 316 | 스트림 본편(BGM·긴 환경음). 압축 없음 |
| `Sound/Product.100.alto__AltoConfig.bgyml` | 1 | `$parent` = `Work/Sound/altoConfig.alto__AltoConfig.gyml` (Bootup 팩) |
| `Sound/Attenuation/Attenuation.Product.100.baatarc.zs` | 1 | SARC: 거리 감쇠 세트 `.baatn`과 하위 커브 `.baroc/.baudc/.baadr/.baacl` |
| `Sound/Group/GroupSetting.Product.100.bagst.zs` | 1 | `AGST` v9: TREE·GRP·MAND·PASE·GCCD·STRG 섹션(§4.3) |
| `Sound/Bus/BusSetting.byml.zs` | 1 | BYML 빅엔디언 v4 (`BY\0\4`). `spl_data.py cat`으로 그대로 풀림 → `analysis/effect_sound/BusSetting.json` (§4.4) |
| `Sound/Bgm/bgm.Product.100.byml.zs` | 1 | BGM 목록 |
| `Sound/ResourceListPack/` | 1 | 리소스 목록 팩 |

main 문자열: `Sound/Resource/%s.bars`(참조 0x7103027330 외 5곳), `content://Sound/Resource/Stream/`, `.prefetch.bwav`, `Sound/Attenuation/Attenuation.%s.baatarc`, `Sound/Bgm/bgm.%s.byml`, `.baatn/.baroc/.baudc/.baadr/.baacl`(로더 0x710384e9d0 안에서 확장자별로 나눔) [데이터].

## 2. BARS v1.2 [데이터 — 533개 전부 파싱]

| 오프셋 | 타입 | 내용 |
|---|---|---|
| 0x00 | char[4] | `BARS` |
| 0x04 | u32 | 파일 크기 |
| 0x08 | u16 | BOM `FFFE` |
| 0x0A | u8, u8 | 버전 2, 1 (= 1.2) |
| 0x0C | u32 | 항목 수 n |
| 0x10 | u32[n] | CRC32(사운드 이름), 오름차순 |
| 0x10+4n | {u32 amtaOff, u32 bwavOff}[n] | 파일 시작 기준 |

- 사운드 이름 = AMTA 안의 이름 = SLink `RuntimeAssetName`입니다. CRC32는 4,641개 항목 전부 이름과 일치합니다 [실행: `sound_bars.py`].
- 전체 색인은 `analysis/effect_sound/sound_index.json`입니다(이름 4,064종). 그중 382종은 여러 bars에 중복으로 들어 있습니다(예: 공용 SE가 장면별 묶음에 복제).
- SLink가 참조하는 RuntimeAssetName 4,052종 중 4,051종이 bars에 있습니다. 없는 하나는 `@Blank`(무음 자리표시로 추정)입니다 [데이터].

### 2.1 AMTA v5.0 (메타데이터)

| 오프셋(AMTA 기준) | 타입 | 내용 |
|---|---|---|
| 0x00 | char[4] | `AMTA` |
| 0x04 | u16 | BOM |
| 0x06 | u8,u8 | 0, 5 (= 5.0) |
| 0x08 | u32 | 크기 |
| 0x10 | u32 | data 오프셋(AMTA 기준, 보통 0x34) |
| 0x14–0x20 | u32×4 | marker/ext/tag 등 오프셋, 슈터 SE는 0 |
| 0x24 | u32 | 이름 오프셋(이 필드 위치 기준) |
| 0x28 | u32 | CRC32(이름) |
| 0x2C | u32 | 종류 — SE 2, 스트림 BGM 7 등 [데이터], 의미 [미확정] |
| 0x30 | u8,u8,u16 | 채널 수로 보이는 값 두 개, 플래그 |
| data+0x00 | u32 | 47 (공통) |
| data+0x04 | f32 | **샘플 피크(절대값 최대)** — 디코드 PCM과 6자리 일치 [실행] |
| data+0x08 | f32 | RMS 계열 값(디코드 RMS와 다름, 가중치 방식 [미확정]) |
| data+0x0C | f32 | 라우드니스(dB)로 보임 [추정] |
| data+0x10 | f32 | -100 또는 다른 dB 값 [미확정] |
| data+0x14 | u16 n, u16 | 점 개수, ? |
| data+0x1C | {f32, u32 sample}[ ] | 4,800샘플(0.1초) 간격 에너지 곡선으로 보임 [추정] |

재생에 필요한 값(샘플레이트, 루프)은 BWAV에 있습니다. AMTA는 웹 재생에 쓰지 않아도 됩니다.

### 2.2 BWAV v1

| 오프셋 | 타입 | 내용 |
|---|---|---|
| 0x00 | char[4] | `BWAV` |
| 0x04 | u16 | BOM |
| 0x06 | u16 | 버전 1 |
| 0x08 | u32 | CRC32(데이터로 추정) |
| 0x0C | u16 | prefetch (1 = 앞부분만 있는 프리페치) |
| 0x0E | u16 | 채널 수 |
| 0x10 + 0x4C·c | 채널 정보 | `u16 codec(0 PCM16, 1 DSP-ADPCM)`, `u16 pan(0 L, 1 R, 2 중앙)`, `u32 sampleRate`, `u32 samplesNonPrefetch`, `u32 samples`, `s16 dspCoef[16]`, `u32 startOffsetNonPrefetch`, `u32 startOffset`, `u32 isLoop?`, `u32 loopEnd(0xFFFFFFFF 없음)`, `u32 loopStart`, `u16 predScale`, `u16 hist1`, `u16 hist2`, pad |

통계 [데이터]: 코덱은 DSP-ADPCM 4,640, PCM16 1입니다. 채널은 1ch 4,085, 2ch 483, 4ch 50, 6ch 20 등입니다. 샘플레이트는 48 kHz 3,305, 44.1 kHz 965, 32 kHz 183, 24 kHz 134 외입니다. loopEnd가 있는 항목(루프)은 610, 프리페치는 338입니다.

- `isLoop`로 둔 +0x38 필드는 원샷 SE에서도 1입니다. 루프 여부는 **loopEnd ≠ 0xFFFFFFFF**로 판정합니다. vgmstream도 슈터 SE를 루프 없이 0.6초로 디코드합니다 [실행].
- 프리페치(prefetch=1) 항목은 bars 안에 앞부분만 있고, 본편은 `Sound/Resource/Stream/<이름>.bwav`에 있습니다. 예: `BGM_Coop_Event`가 `BgmCoop.bars`와 `Stream/BGM_Coop_Event.bwav`에 있습니다 [데이터]. 웹에서는 Stream 파일을 디코드해 쓰면 됩니다.

## 3. 디코드와 웹 변환 [실행]

```sh
PY web/tools/sound_bars.py ls  extracted/romfs/Sound/Resource/WeaponShooterNormal.bars.zs --amta
PY web/tools/sound_bars.py wav extracted/romfs/Sound/Resource/WeaponShooterNormal.bars.zs Wp_ShooterNormal_Shot_00 analysis/effect_sound/wav/Wp_ShooterNormal_Shot_00.wav
PY web/tools/sound_bars.py find Wp_NormalShot_02          # 이름 → 들어 있는 bars
PY web/tools/sound_bars.py index analysis/effect_sound/sound_index.json
```

- `wav` 명령은 BWAV 바이트를 잘라 `.bwav`로 저장한 뒤 `c:/dev/mpj/tools/vgmstream/vgmstream-cli.exe`(경로 그대로 실행, r2117)로 16비트 PCM WAV를 만듭니다.
- 변환한 표본은 3개입니다(`analysis/effect_sound/wav/`).

| 이름 | 길이 | 형식 | AMTA 피크 | 디코드 피크 |
|---|---|---|---|---|
| Wp_ShooterNormal_Shot_00 | 28,800 샘플 (0.600 s) | 48 kHz 1ch DSP | 0.105988 | 0.105988 |
| Wp_NormalShot_02 | 24,000 (0.500 s) | 48 kHz 1ch DSP | 0.107361 | 0.107361 |
| Wp_NormalShot_Blurred_02 | 24,000 (0.500 s) | 48 kHz 1ch DSP | 0.119873 | 0.119873 |

피크가 일치하므로 DSP-ADPCM 디코드(계수·히스토리 처리)는 원본 툴체인과 같은 PCM을 낸다고 봅니다. RMS 계열 값은 다릅니다.

**웹 에셋 형식**: WAV(PCM16)를 그대로 `AudioContext.decodeAudioData`에 넣을 수 있습니다. 용량을 줄이려면 Ogg Opus나 AAC로 다시 인코딩합니다. 다시 인코딩한 파일은 앞쪽에 패딩(Opus 기본 312샘플 등)이 생기므로, 발사음처럼 시작 시점이 중요한 소리는 WAV를 쓰거나 `AudioBufferSourceNode.start(when, offset)`로 패딩만큼 건너뜁니다. 루프 사운드는 BWAV loopStart/loopEnd를 `loopStart/loopEnd`(초 = 샘플/샘플레이트)로 넘깁니다.

## 4. Alto 설정 [데이터]

### 4.1 AltoConfig (Bootup 팩 `Sound/altoConfig.alto__AltoConfig.bgyml`)

`AalConfig { MaxEmitterCount 512, ResourceHeapSize 60, OutputVolumStereoJack 1.0, OutputVolumeBuildInSpeaker 1.0, IsCreateSpatialCalcuratorOnInit false }`, 리스너 `Main`(ListenerParam Versus/Mission/Normal/Demo/Periscope), Scenery `Spl`.

대전 리스너(`Sound/Listener/Versus.alto__ListenerParam.bgyml`):

| 필드 | 값 |
|---|---|
| Type | TargetOffset |
| Offset_Offset / TargetOffset_Offset | (0,0,1.0) / (0,0,1.5) |
| TargetRateRange_Start / _End, TargetRate_Rate | 0.2 / 1.0, 1.0 |
| IsUseDirectivity, IsUseCameraMtxForAngle | true, true |
| Dir_InnerConeAngle / OuterConeAngle | 40 / 90 |
| Dir_InnerSphereRadius / OuterSphereRadius | 3.0 / 6.0 |
| Dir_InnerDistRate / OuterDistRate | 1.0 / 2.5 |

이름으로 보아 리스너는 카메라와 조준 대상 사이에 놓이고, 카메라 방향으로 지향성을 줍니다 [추정]. 실제 계산 코드는 판독하지 않았습니다 [미확정].

### 4.2 거리 감쇠 세트 (`DistanceParamSetName` → `.baatn`)

SLink 에셋의 `DistanceParamSetName`이 `Attenuation/<이름>.baatn`을 고릅니다. AATN은 이름으로 하위 커브 파일을 묶습니다. 도구 `web/tools/sound_alto.py set <이름>`, 출력 `analysis/effect_sound/alto_attenuation_sets.txt`.

| 세트 | volume | farFx | filter | priority | directivity | culling |
|---|---|---|---|---|---|---|
| WpMuzzle_HighSensi (슈터 발사음) | WpMuzzleVol | $FarFx_WpMuzzle | CmnFlt_High | CmnPrio_High | WeaponMuzzle | WpMuzzleCulling |
| LowSensi (무기 장착음, 잉크 비말) | CmnVol | $FarFx_Cmn | CmnFlt_Low | CmnPrio_Low | (없음) | CmnCulling |
| HitEffect | CmnVol | — | — | — | — | CmnCulling |

하위 파일 원시값(헤더 8 B 뒤, u32/f32):

| 파일 | 형 | 값 |
|---|---|---|
| WpMuzzleVol | AROC v2 | 3, 1.0, 0.0, 0.70794(= −3 dB), 1.0, 0, 0 |
| CmnVol | AROC | 1, 1.0, 0.0, 1.0, 1.0, 0, 0 |
| $FarFx_WpMuzzle / $FarFx_Cmn | AROC | 0, 1.0, 0.0, 1.0, 1.0, 0, 0 |
| CmnFlt_High / CmnFlt_Low | AROC | 1, 10.0, 0.0, 0.2, 0.0, 1, 0 |
| CmnPrio_High | AUDC v1 | 0, 0.9, 0.41, 0, 3.0, 0.1, 0 |
| CmnPrio_Low | AUDC | 0, 0.4, 0, 0, 3.0, 0.1, 0 |
| WeaponMuzzle | AADR v1 | 80.0, 140.0, 0.8, 0 (각도 두 개 + 바깥 이득으로 보임) |
| WpMuzzleCulling / CmnCulling | AACL v2 | 8.0, 4.0, 0 |

- 1차 문서는 이 값들의 수식을 [미확정]으로 두었습니다. 아래 §4.2.1–4.2.3에서 AROC 평가식과 컬링을 판독했습니다. DistCoef 결합만 남았습니다.
- 거리 컬링은 SLink 이전 단계에서 게임 코드가 한 번 더 합니다. 발사 xlink 방출 생략 반경 600, 히트 이펙트 생략 반경 400([effect_sound.md](effect_sound.md) §3.2, §3.5) [판독].

#### 4.2.1 AROC(롤오프 커브) [판독]

로더 `0x710384eaac`가 확장자별로 나눠 `.baroc`를 `0x7103852e2c`(AROC 파서), `.baudc`를 `0x710385b234`, `ACTC`(점 커브)를 `0x71038571d4`에 넘깁니다. AROC 객체의 평가(vtable 0x7105734f70 슬롯 6)는 `0x7103852da4`입니다.

| 파일 오프셋 | 형 | 객체 | 의미(웹 권장 이름) |
|---|---|---|---|
| +0x08 | u32 | 모델 | 1 Rational(역거리, vtable 0x7105735030), 2 Linear(0x7105735078), 3 Power(0x71057350c0), 그 밖 = 모델 없음 |
| +0x0C | f32 | +0x60 | `refDist` A. > 0일 때만 반영(기본 1.0) |
| +0x10 | f32 | +0x64 | `maxDist` B. ≥ 0일 때 반영. 0이면 평가 때 FLT_MAX |
| +0x14 | f32 | +0x68 | `factor` C. ≥ 0일 때 반영(기본 1.0) |
| +0x18 | f32 | +0x6C | `mix` D. 0..1일 때만 반영 |
| +0x1C | u32 | +0x70 | `mixMode` (0이면 g·D, 아니면 1 − (1 − g)·D) |
| +0x20 | f32 | +0x74 | v2 파일만(v1은 0). 이 평가에서는 쓰지 않음 |

A·B·C를 쓸 때마다 모델의 계수 함수(vt 슬롯 3)로 `coef`(+0x78)를 다시 계산합니다.

```
evalAROC(d):                                   // 0x7103852da4
  if (!model) return D
  max = (B == 0) ? FLT_MAX : B
  g = d <= A ? 1 : model(min(d, max))          // |g| < 3.05e-5 이면 0
  out = mixMode == 0 ? g*D : 1 - g*(1-D)
  return clamp(out, 0, 1)                      // 1 이상 자르고 음수면 0

Rational (0x710385681c, coef 0x7103856868): g = A / (C*x + (1-C)*A)
Linear   (0x7103856964, coef 0x71038569b4): g = 1 - (x - A) * C / (max - A)
Power    (0x7103856aa4, coef 0x7103856b08): g = x^(-C) * A^C = (A/x)^C
```

전수 표(`sound_alto.py aroc` → `analysis/effect_sound/alto_aroc_models.txt`, d는 아래 정규화 거리):

| 커브 | 모델 | A, B, C, D, mixMode | d = 2 / 4 / 8 / 16 |
|---|---|---|---|
| WpMuzzleVol (슈터 발사음 볼륨) | Power | 1, ∞, 0.70794, 1, 0 | 0.612 / 0.375 / 0.229 / 0.141 |
| CmnVol (장착음·피탄 등) | Rational | 1, ∞, 1, 1, 0 | 0.5 / 0.25 / 0.125 / 0.0625 (= 1/d) |
| CmnFlt_High/Low (필터) | Rational | 10, ∞, 0.2, 0, 1 | 0 / 0 / 0 / 0.107 (d > 10부터 오름) |
| $FarFx_* | 모델 없음 | D = 1 | 항상 1 |

- 필터 커브는 D = 0, mixMode 1이라 `out = 1 − g`입니다. 가까우면 0(필터 없음), 멀수록 커지는 값입니다. 이 값(음원 계산 객체 +0x10, 0 이상)을 로패스 컷오프로 바꾸는 곳은 [미확정]입니다(§4.2.5).
- AUDC(priority)·AADR(directivity) 평가식은 3차에서 판독했습니다(§4.2.4, §4.2.5).

#### 4.2.2 음원 감쇠 계산 `0x7103863fe8` [판독]

| 출력(음원 계산 객체) | 입력 커브(감쇠 세트 +오프셋) | 거리 |
|---|---|---|
| +0x04 볼륨 | +0x58 (volume AROC) | d₀ |
| +0x18 컬링/추가 계수 | +0x78 | 인자5 구조 +0x14 거리 기준 |
| +0x10 (누적, 0..1) | +0x68 | 인자5 +0x08 거리 기준 |
| +0x08 | +0x60 | 인자5 +0x0C 거리 기준 |
| +0x14 | +0x70 | 인자5 +0x10 거리 기준 |
| (지향성) | +0x80 (AADR) | 리스너 행렬 |

- **정규화 거리** `d₀ = 음원 거리(객체 +0x8C) / 전역 단위(*0x710599a3f8 → +0x10 → +0x20) × 객체 +0x90`. 다른 출력도 같은 꼴로 `거리 / 단위 × +0x90`입니다 [판독]. 전역 단위 값과 +0x90을 쓰는 코드는 찾지 못했습니다. **SLink `DistCoef`(ParamDefine 21번, 기본 10.0)가 어디에 들어가는지는 여전히 [미확정]**입니다. 3차에서 좁힌 것은 §4.2.6.
- **컬링(AACL, 세트 +0x88)**: 컬링 거리 = 볼륨 AROC 객체의 vt 슬롯 7(0x71038540d4) 값이 0이 아니면 그 값 + AACL+0x4C, 0이면 AACL+0x48(데이터 8.0). 페이드 폭 = AACL+0x4C(데이터 4.0). `d₀ ≥ 컬링 거리`면 0, `컬링 거리 − 폭 < d₀`이면 `(1 − (d₀ − (컬링 − 폭))/폭)²`, 아니면 1. 결과가 0이고 음원 플래그(+0x48 bit6)가 켜져 있으면 음원을 끄고 사유 코드 0x10000/0x10002를 돌려줍니다. AACL+0x50이 켜져 있으면 이 페이드 값을 +0x78 커브 결과에 곱합니다.
- 볼륨 결과에 지향성(AADR)·리스너 거리 보정이 곱해지고, 마지막에 |볼륨| ≤ 3.05e-5면 정지 처리합니다.

웹 구현은 아래 순서로 하면 됩니다. 단위와 DistCoef가 확정되기 전에는 `d = 거리 / DistCoef`로 두고, 이것이 가정임을 표시합니다.

```ts
function altoVolume(set: AttnSet, dist: number, distScale: number /* +0x90, 미확정 */, unit = 1 /* 미확정 */) {
  const d = dist / unit * distScale;
  let cull = 1;
  if (set.culling) { const edge = set.culling.dist, w = set.culling.fade;     // 8.0, 4.0
    if (edge > 0) cull = d >= edge ? 0 : (w > 0 && edge - w < d ? (1 - (d - (edge - w)) / w) ** 2 : 1); }
  return set.volume ? evalAROC(set.volume, d) : 1;                          // + 지향성, cull 은 +0x78 결과에 적용
}
```

#### 4.2.3 점 커브 ACTC (`0x71038571d4`, 평가 `0x7103857460`) [판독]

`{f32 x, f32 y, u32 shape, f32 power}` 0x10 B 항목 배열을 x로 정렬해 둡니다. 평가는 `x`가 음수면 0, 해당 구간 [xᵢ, xᵢ₊₁)에서 t = (x − xᵢ)/(xᵢ₊₁ − xᵢ)를 shape로 바꿔 `yᵢ + (yᵢ₊₁ − yᵢ)·f(t)`입니다. shape: 0 선형, 1 t^p, 2 t^(1/p), 3 sin(t·π/2)(^p), 4 1 − cos(t·π/2)^p, 5 계단(yᵢ). power < 0이면 0. 이 커브를 쓰는 데이터 파일은 이번에 확인하지 않았습니다.

#### 4.2.4 AUDC(거리 우선순위 커브) [판독]

파서 `0x710385b234`, 평가 = 객체 vtable 0x7105735168 슬롯 6 `0x710385b148`. 음원 계산 `0x7103863fe8`에서 감쇠 세트 +0x60 커브로 출력 +0x08(우선순위)을 만듭니다(거리 기준 = 인자5 +0x0C).

| 파일 오프셋 | 형 | 객체 | 의미(웹 권장 이름) | 반영 조건 |
|---|---|---|---|---|
| +0x08 | u32 | +0x58 | `type` 0 지수, 1 선형 | 항상 |
| +0x0C | f32 | +0x5C | `near` A — 가까울 때 값 | 0..1 |
| +0x10 | f32 | +0x60 | `far` B — 수렴 값 | 0..1 |
| +0x14 | f32 | +0x64 | `start` C — 감쇠 시작 거리 | ≥ 0 |
| +0x18 | f32 | +0x68 | `step` D — 감쇠 단위 거리 | > 0 |
| +0x1C | f32 | +0x6C | `ratio` E — D마다 곱해지는 비율 | 0..1 |
| +0x20 | f32 | +0x70 | (평가에 안 씀) | ≥ 0 |

```
v(x) = x <= C ? A
     : x > cut ? 0
     : E == 1 ? A : E == 0 ? B
     : B + (A - B) * (type == 0 ? E^((x-C)/D) : max(1 - (1-E)(x-C)/D, 0))     // |v| < 2^-15 이면 0
cut  = (A < B || B > 0) ? FLT_MAX : A <= 0 ? 0 : E == 0 ? C
     : C + D * (type == 0 ? ln(t0)/ln(E) : (1 - t0)/(1 - E)),  t0 = max(-B/(A-B), 3.0517578e-5)
```

| 커브 | type, A, B, C, D, E | 값 d = 0 / 1 / 2 / 4 / 8 | cut |
|---|---|---|---|
| CmnPrio_High (슈터 발사음) | 0, 0.9, 0.41, 0, 3, 0.1 | 0.9 / 0.637 / 0.516 / 0.433 / 0.411 | ∞ |
| CmnPrio_Low | 0, 0.4, 0, 0, 3, 0.1 | 0.4 / 0.186 / 0.086 / 0.019 / 0.0009 | 13.55 |
| CmnPrio_Const / BGM | 0, 1, 0.91, 0, 3, 0.1 / 0.3 | 1 / 0.952 / … → 0.91 | ∞ |

`sound_alto.py audc`가 전수 표를 냅니다. 우선순위 값을 소리 고르기에 쓰는 코드는 판독하지 않았습니다 [미확정].

#### 4.2.5 AADR(음원 지향성) [판독]

로더 `0x710384eaac` 안(0x71038515ec~)에서 파일 값을 객체에 넣고, 음원 설정 `0x7103863788`이 라디안으로 바꿔 음원별 지향 객체(+0x58)에 둡니다. 평가는 음원 계산 `0x7103863fe8` 안입니다.

| 파일 오프셋 | 객체 | 의미 | 범위 |
|---|---|---|---|
| +0x08 | +0x48 | `innerAngle`(도) | 0..180 |
| +0x0C | +0x4C | `outerAngle`(도) | 0..180 |
| +0x10 | +0x50 | `outerGain` | 0..1 |
| +0x14 | +0x54 | `outerFilter` | 0..1 |

```
o = clamp(outer * π/180, 0, π);  i = min(max(inner * π/180, 0), o)        // 0x7103863788
θ = atan2(|z × v|, z · v)        // z = 음원 행렬 3열(로컬 +Z), v = 청자 위치 − 음원 위치 (0x710386119c)
                                 // 청자 위치 = 청자 행렬 이동 성분(+0x13c/+0x14c/+0x15c), +0x1b0 켜짐이면 +0x1b4 값
θ <= i      : t = 0, gain = 1
i < θ <= o  : t = (θ - i)/(o - i), gain = 1 - t(1 - outerGain)
θ > o       : t = 1, gain = outerGain
volume *= gain;  filter(+0x10) += t * outerFilter;  t 는 출력 +0x94 에도 저장
```

슈터 발사음 `WeaponMuzzle`(80°, 140°, 0.8, 0): 총구 앞 ±80° 안이면 그대로, 뒤쪽(140° 이상)은 0.8배입니다 [판독+데이터]. 필터 값 +0x10(AROC 필터 커브 + 지향성)을 실제 로패스 컷오프로 바꾸는 코드는 찾지 못했습니다 [미확정].

#### 4.2.6 DistCoef 결합 — 3차에서 좁힌 것 [판독-부분]

- 이 게임은 Alto 감쇠 계산(슬롯 7 `0x7103863fe8`)과 같은 서명의 **게임 쪽 재정의 `0x7103129c98`**을 가집니다. 여기서 거리 배율은 `+0x90 × 확장(+0x50)+4`이고, 확장 +1이 켜져 있으면 그룹 객체 +0x158의 게임 파라미터 `FriendDistCoef`(+0xd8)를 한 번 더 곱합니다. 확장이 없으면 정적 기본값(+0 = 1, +4 = 1.0)을 씁니다. 이어서 `d = 거리(+0x8C) / 전역 단위 × 배율`로 같은 AACL·AROC 계산을 합니다.
- 게임 파라미터 클래스(방문 함수 `0x7103127cf0`) 필드: `MinDirectVolume`(+0xdc), `FriendDistCoef`(+0xd8), `IsListenerDirectivityUseCamera`(+0xec), `OcclusionInterpTime`(+0xe4), `OcclusionHfReference`(+0xe0), `OcclusionMinGain`(+0xe8) 등. 같은 계열 `0x7103127304`: `CurveScaleToFarFxSendScale`, `FarFxCurve`, `SensitivityFilterCurve`.
- SLink ParamDefine 21 `DistCoef`, 24 `UseFriendCoef`가 확장 +4/+1에 들어간다고 보는 것이 자연스럽지만, 확장을 채우는 코드는 찾지 못했습니다 [추정]. 1.0 근처 값이 기본인 배율 자리라서, `DistCoef`(데이터 5–30)를 쓰려면 역수(`1/DistCoef`)여야 거리 감쇠가 상식적인 범위가 됩니다. 이 역수 관계도 코드로 확인하지 않았습니다 [추정].
- 웹 임시 구현은 `d = 거리 / DistCoef`를 유지하고 `UseFriendCoef && 아군`이면 `FriendDistCoef`를 곱합니다(값 미확인 — 게임 파라미터 데이터에서 찾아야 함).

### 4.3 그룹 (`GroupName`) — AGST v9 [데이터]

| 섹션 | 위치(해제 파일 기준) | 내용 |
|---|---|---|
| 헤더 | 0x00 | `AGST`, BOM, 버전 9, 섹션 오프셋 6개(0x24, 0x540, 0x5AFC, 0x8AAC, 0x8F64, 0x8F80) |
| TREE | 0x24 (0x514 B) | 그룹 트리(Default → Root → `*_folder` → 그룹). 노드 형식 미해석 |
| GRP | 0x540 (0x55B4 B) | 그룹 레코드 108개(대부분 0xC4 B, 이름 문자열이 끼면 더 김). 칸 배치는 아래 표 [판독] |
| MAND | 0x5AFC | 내장 BYML: 덕커 세트(예 `Cmn_Boot`: World_folder를 0으로, `Cmn_Customize`: 각 폴더 0.3, Sqrt 페이드 0.1/0.2 s) |
| PASE | 0x8AAC | 내장 BYML: 일시정지 그룹(`Custom_SoundGamePause` 등) |
| GCCD | 0x8F64 | 내장 BYML(비어 있음) |
| STRG | 0x8F80 | 이름 문자열 109개 |

- 내장 BYML 3개는 `analysis/effect_sound/GroupSetting_byml.json`으로 풀었습니다.
- (3차) GRP 레코드 판독 [판독: 헤더 확인 0x710386b5b8, 트리 생성 0x7103837080, 레코드 적용 0x7103837384]. 섹션 = `GRP `, 크기, 개수 108, **u32 오프셋[108]은 파일 시작 기준**(1차의 "GRP 기준"은 틀림). 레코드는 u32/f32 단위이고 [i]는 레코드 안 i번째 4 B입니다.

| 칸 | 그룹 객체에 쓰는 곳 | 의미(웹 권장 이름) |
|---|---|---|
| [0] | — | 이름(STRG+8 기준 오프셋) |
| [1] | 0이면 잎 그룹(팩토리 vt+0x10), 1이면 폴더(vt+0x18, 자식 순회) | `isFolder` |
| [3] | +0x174 | (미상, 전부 0) |
| [4]–[0xB], [0xE], [0xF] | +0x98, +0x9C, +0xA0, +0xAC, +0xA8, +0xB0, +0xB4, +0xB8, +0xBC, +0xA4 | 볼륨류(데이터 1.0/1.0/0/0/-1…), 이름 [미확정] |
| [0x16] | 제한기 생성 `0x71038477b0(type)` | `limiterType` 0 없음, 1–4 클래스 4종(vtable 0x7105734878/8b8/8f8/938) |
| [0x17] | 제한기 +8 | `limitCount` |
| [0x18] 바이트 2개(+0x62/+0x63) | 제한기 +0xC/+0xD | 플래그 |
| [0x19]–[0x1E] | 두 번째 객체(+0x5C 켜짐) {[0x1a], [0x1b], [0x1c..0x1e]} | (미상, 감쇠 계열로 보임) |
| [0x1F]–[0x20] | +0x5D 켜짐, 값 | (미상) |
| [0x21] | 게임 그룹 클래스(0x71056a7a30)일 때 +0x1B8 | (미상) |
| [0x22]–[0x24] | +0x158 객체 +0xC/+0x10/+0x14 | (미상) |
| [0x25] | +0x168 (0..1) | (미상) |
| [0x26] | +0x16C | (미상) |
| [0x27] + 5칸×n | `0x710383acfc`로 다른 그룹에 연결 | 덕킹/연결 목록으로 보임 [추정] |

  전체 표: `analysis/vfx/agst_grp_dump.txt`. 무기 관련 [데이터]:

| 그룹 | limiterType, limitCount | [0x21] |
|---|---|---|
| Weapon_Default | 0, −1 | 0 |
| Weapon_AttackFocused (슈터 자기 발사음) | 0, −1 | 0.016 |
| Weapon_InsLimit_00..03 (아군·적 발사음) | 0, −1 | 0.016 |
| Player_Voice | 2, 4 | 0.016 |
| Enemy_Attack | 2, 6 | 0 |
| Obj_Break | 2, 5 | 0 |

- 즉 **슈터 발사음 그룹은 AGST 수준의 동시 발음 제한기가 없습니다** [판독+데이터]. "InsLimit"라는 이름의 제한은 다른 곳(게임 그룹 +0x1B8 = 0.016, SLink 사용자 파라미터 `LimitType`/`PlayableLimitNum` — WeaponShooterNormal은 기본값 0/−1)에서 올 수 있으나 확인하지 않았습니다 [미확정]. +0x1B8을 읽는 곳 `0x7103121ca4`는 "입력 ≥ 0.01이고 +0x1B8 ≥ 입력이면 +0x1BC = 입력"입니다(의미 미정리).

### 4.4 BusSetting [데이터]

`analysis/effect_sound/BusSetting.json`: `BusGraphPreset` 18개(Default, VS_City/VS_Hall/VS_Outdoor, Mission_*, Scene_*)와 이펙트 정의 29개.

- 버스: `WorldFx`, `FarFx`, `FarFx_Loud`, `Effect` → `FinalMix`(전부 6ch 48 kHz, 볼륨 1.0). 그래프 = WorldFx→FinalMix, FarFx→Effect, Effect→FinalMix(Send 1.0).
- 대전 야외 `VS_Outdoor`: FarFx 버스에 `FarFx_Reverb_Outdoor`(DspI3DL2Reverb: RoomGain −800, RoomHfGain −800, LateReverbDecayTime 5000, ReflectionsGain −500, ReverbGain −300, HfReference 1000 등).
- 감쇠 세트의 `farFx` 커브(§4.2, 현재 전부 모델 없음 = 1)가 FarFx 버스로 보내는 양으로 보입니다 [추정].
- 웹: WorldFx = 드라이 GainNode, FarFx = ConvolverNode(리버브 근사) 또는 생략. I3DL2 파라미터를 그대로 재현하는 WebAudio 노드는 없으므로 근사입니다.

## 5. 웹 재생 파라미터 (SLink 에셋 → WebAudio)

| SLink 파라미터 | 원본 근거 | WebAudio 대응 | 확정 |
|---|---|---|---|
| RuntimeAssetName | BARS 이름 | 디코드된 AudioBuffer 키 | [데이터] |
| Volume (Random 등) | xlink 값 해석(§xlink_format 4.2) | `GainNode.gain` 곱 | 값 [데이터], 난수식 [참고] |
| Pitch | 같음 | `playbackRate`(음높이 비율, 1.0 = 원음) | 비율 해석 [추정] |
| Delay | ParamDefine Float | `start(ctx.currentTime + delay/60)`, 프레임 단위로 봄 | 단위 [추정] |
| Lpf | 기본 0.0 | BiquadFilter lowpass, 0이면 끔 | [미확정] |
| DistanceParamSetName + DistCoef | §4.2 | PannerNode 대신 매 프레임 `evalAROC` 직접 gain 계산 | AROC 수식·컬링 [판독], DistCoef 결합 [미확정] |
| GroupName | §4.3 | 그룹별 동시 발음 제한 큐, 덕킹(MAND) | 무기 그룹 제한기 없음 [판독+데이터], 덕킹 표 [데이터] |
| Priority | 기본 0.5 | 제한 초과 시 낮은 것부터 정지 | [추정] |
| BitFlag | 9(발사음)/11(장착)/8(분리) | 의미 미상 | [미확정] |

```ts
class SoundPlayer implements AssetSink {
  play(p: ResolvedParams, h?: Handle) {
    const buf = bank.get(p.RuntimeAssetName); if (!buf) return;
    const src = ctx.createBufferSource(); src.buffer = buf;
    src.playbackRate.value = p.Pitch ?? 1;
    const g = ctx.createGain(); g.gain.value = (p.Volume ?? 1) * attenuation(p.DistanceParamSetName, p.DistCoef, dist);
    src.connect(g).connect(groupBus(p.GroupName));
    src.start(ctx.currentTime + (p.Delay ?? 0) / 60);
  }
}
```

## 6. 미확정과 다음 근거

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| AROC 롤오프 수식 | **해소** [판독] §4.2.1 | — |
| 감쇠 계산 순서·컬링 | **해소** [판독] §4.2.2 | — |
| DistCoef 결합(거리 정규화의 +0x90/전역 단위) | [미확정], 게임 재정의 0x7103129c98까지 좁힘(§4.2.6) | 게임 감쇠 확장(음원 +0x50)의 +1/+4를 채우는 코드, FriendDistCoef 데이터 값 |
| AUDC/AADR 평가식 | **해소** [판독] §4.2.4, §4.2.5 | — |
| 필터 값 → 컷오프 변환 | [미확정] | 음원 계산 출력 +0x10을 읽는 보이스 코드 |
| AGST GRP 레코드(동시 발음 제한) | **레코드 배치 해소** [판독] §4.3, 무기 그룹은 제한기 없음 [데이터] | 제한기 4종의 동작, [0x21](+0x1B8) 의미 |
| BusSetting | **해소** [데이터] §4.4 | — |
| AMTA 데이터 블록 f[1]–f[3] | [미확정] | 웹 재생에 불필요 |
| Pitch 단위 | [추정] 비율 | aal 재생 코드 |
