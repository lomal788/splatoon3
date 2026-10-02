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

**정정(2026-10-03, 5차):** 위 [추정]·[미확정]은 아래 §4.1.1~§4.1.3의 판독과 원본 실행으로 대체합니다. 리스너는 "카메라와 조준 대상 사이"가 아니라 **주시 대상 지점에서 카메라 쪽으로 1.5만큼 물러난 곳**에 놓입니다.

#### 4.1.1 Type 변환과 컨트롤러 [판독]

`ListenerParam`(리플렉션 방문 `0x71039535c0`, 생성자 `0x71039534ac`, 객체 0xD0 B)의 필드 오프셋은 `param_reflect.py`로 확인했습니다. `Type`(+0x9C)은 열거형 `None, CameraView, CameraOffset, TargetOffset, CameraTargetRate, ListenerAngleKeep, CameraTargetRateRange, CameraTargetRelative`(0~7)입니다 [데이터: main 문자열].

- 변환 `0x7103904470`(함수 시작은 `network_fstart.py` 기준, 전체 분석 경계 밖): 런타임 모드 = `Type == 7 ? 2 : Type`. 모드 3(TargetOffset)이면 변환 구조 +0x44..+0x4C에 `TargetOffset_Offset`(+0x84..+0x8C)을 복사합니다. 모드 2는 `Offset_Offset`(+0x64), 모드 4·5는 각각 +0x90·+0x30 한 값, 모드 6은 +0x98과 +0x94입니다.
- 적용 `0x710390b08c`: 모드가 바뀌면 `0x710390c5a0`이 리스너(+0xF8)의 컨트롤러를 새로 만듭니다(모드 1 vtable 0x7105734a28, 2 → `0x710390ca2c`, 3 → `0x710390ce6c` = vtable **0x710573c1e0**, 4·6 → `0x710384a010`, 5 → `0x710390d378`). 모드 3이면 컨트롤러 +0x98..+0xA0 = 오프셋 vec3입니다.
- 같은 함수가 `IsUseDirectivity`(변환 +0x3C bit1)일 때 리스너 지향성 값을 씁니다: 리스너 +0xBC = min(inner, outer) 각(라디안), +0xC0 = outer 각(0..π로 자름), +0xC4 = 차, +0xC8/+0xCC = inner/outer 반경 × 전역 단위(`*(*0x710599a3f8+0x10)+0x20`), +0xD0 = 차, +0xD4/+0xD8 = inner/outer `DistRate`, +0xDC = 차, +0x70 = 사용 플래그.

#### 4.1.2 리스너 위치 = 주시점 + Rᵀ·offset [판독 + 실행]

컨트롤러(모드 3) 슬롯:

| vtable 0x710573c1e0 슬롯 | 주소 | 동작 |
|---|---|---|
| 7 (+0x38) | `0x710390cfc4` | 입력 `{camera, target*}`: 컨트롤러 +0x48..+0x74 = camera+8..+0x37(3×4 뷰 행렬). camera가 타입 `0x71055f8840` 계열이면 +0x78..+0x80 = camera+0x44..+0x4C(sead `LookAtCamera`의 `at` 자리와 같은 배치 [추정: 이름]). +0xA8 = target 포인터 |
| 8 (+0x40) | `0x710390d0cc` | 출력 뷰 행렬 V = [R \| t′], R = 카메라 뷰 행렬 회전, T = (+0xA8 ? *+0xA8 : +0x78), `t′ᵢ = −(((T.x·Rᵢ₀ + T.y·Rᵢ₁) + T.z·Rᵢ₂) + offᵢ)`. FMA 없음(명령 판독) |

리스너 갱신 `0x710383b534`가 슬롯 8을 불러 리스너 +0x100 = V, +0x160 = 카메라 뷰 행렬을 받고, +0x130 = V⁻¹(`0x7100fa6fd4`, 일반 3×4 역행렬)을 만듭니다. 리스너 월드 위치는 +0x13C/+0x14C/+0x15C, 카메라 위치는 +0x190..+0x198, 위치 변화량은 +0x19C..+0x1A4입니다. 따라서

```
listenerPos = T + Rᵀ·offset        // R 행 = 카메라 X, Y, Z 축(월드), Z = normalize(카메라 위치 − 주시점)
대전(Versus): offset = (0, 0, 1.5) → listenerPos = T + 1.5·Z = 주시점에서 카메라 쪽으로 1.5
```

카메라 Z 축 정의(`Z = normalize(pos − at)`)는 [../camera/solo_completion.md](../camera/solo_completion.md) §3~6의 원본 실행 결과를 따릅니다. `Offset_Offset`(0,0,1.0)은 모드 2 전용이라 대전 리스너에는 쓰이지 않습니다. `TargetRateRange_*`·`TargetRate_Rate`도 모드 4·6 전용입니다 [판독].

원본 실행 `web/tools/r5_fx_listener_emu.py`: 슬롯 8 출력 512/512 비트 일치(외부 타깃 포인터 경로 포함), 리스너 갱신 전체(슬롯 8 + 역행렬)의 리스너·카메라 위치 512/512가 재구현과 최대 4.1e−5 안에서 일치. 스텁 없음. 결과 `analysis/completion/r5/fx_listener_emu.json`.

**남은 것 [미확정]:** 슬롯 7을 부르는 쪽(카메라 객체와 타깃 포인터를 넘기는 게임 코드)은 찾지 못했습니다. `+0x108`/`+0xF8` 컨트롤러의 vt+0x38 호출을 전수 스캔(BL·간접 호출 패턴)했지만 이 컨트롤러로 이어지는 것은 없었습니다. 그래서 T가 플레이어 카메라의 주시점인지, 외부 포인터(예: 플레이어 위치)인지는 확정하지 않았습니다. 다음에 볼 곳: 게임 사운드 갱신 `0x7103147020` 주변, 리스너 홀더 +0x2A0/+0x2E0 행렬을 쓰는 `0x7103909570`의 호출자.

**6차(2026-10-03) 추가 탐색 — 여전히 [미확정]:**
- `0x7103147020`은 리스너 지향 행렬과 `0x7103144a98`(새 보이스의 게임 처리), Alto 시스템 갱신 `0x71037e10a0`만 부르고 컨트롤러에 카메라를 넘기지 않습니다 [판독].
- `0x7103909570`의 호출자는 `0x71039042d0`(vtable `0x710573c038` 칸, 4회)와 `0x710390a72c`(=`0x7103909570` 자신이 부름)뿐이고, 둘 다 컨트롤러 vt+0x38을 부르지 않습니다.
- 슬롯 7 함수 `0x710390cfc4`는 vtable `0x710573c218` 한 칸에만 있습니다. Alto 영역(0x71037C0000~0x71039A0000)과 게임 사운드 영역(0x7103100000~0x7103160000)에서 `ldr xN,[xM,#0x38]; blr xN` 전수(x1 = 스택 구조체인 것 19건 + 전체 목록)와 꼬리 호출 `br`(vt+0x38) 전수를 확인했지만, 모두 힙 해제(`0x7103515cfc` 뒤 vt+0x38 = free)나 다른 객체였습니다.
- 리스너 갱신 `0x710383b534`는 컨트롤러가 없으면 리스너 +0x100 행렬을 그대로 씁니다. 따라서 게임이 컨트롤러 대신 리스너 +0x100에 직접 쓰거나, 슬롯 7을 이 영역 밖(예: 카메라·플레이어 코드)에서 부를 가능성이 남습니다. 다음에 볼 곳: Alto 영역 밖에서 vt+0x38을 `{카메라, 타깃}` 쌍으로 부르는 곳 전수, 리스너 +0x100..+0x12C에 쓰는 곳.

#### 4.1.3 리스너 지향성 → 거리 배율 [판독 + 실행]

게임 파라미터 `spl__SoundSpatialConfig`(`analysis/camera/SingletonParam/Gyml/Singleton/spl__SoundSpatialConfig.spl__SoundSpatialConfig.bgyml.json`): `IsListenerDirectivityUseCamera` **true**, `FriendDistCoef` **1.5**, `OcclusionInterpTime` 0.5, `OcclusionHfReference` 10000, `OcclusionMinGain` −60, `MinDirectVolume` 데이터 없음(생성자 기본 0.01) [데이터].

- 게임 사운드 갱신 `0x7103147020`: `IsListenerDirectivityUseCamera`이면 리스너마다 지향 행렬(리스너 +0x80..+0xB8) = (카메라 뷰 행렬 +0x160)⁻¹ × Y축 180° 회전을 씁니다. 아니면 리스너 +0xE0 = 1이고, `0x710383b534`가 리스너 월드 행렬에서 지향 행렬을 만듭니다 [판독].
- 음원·리스너 쌍 갱신 `0x7103863ab4`(Alto 감쇠 vtable 0x71057352a0 슬롯 5): 리스너마다 0x98 B 기록을 만들고, 기록 +0x8C = 리스너 거리(`0x710383b88c`), 기록 **+0x90 = 거리 배율**입니다. 배율은 감쇠 세트(음원 +0x30)가 있고 (음원 플래그 bit5 또는 세트 +0x90 바이트)일 때 `0x710384922c(listener+0x68, pos)`, 아니면 1.0입니다. 세트 +0x90 바이트가 AATN 파일의 어느 칸인지는 [미확정]입니다.

```
distRate(pos):                                  // 0x710384922c, P = listener+0x68
  if !useDirectivity: return 1
  rel = pos − 지향 행렬 위치;  if rel == 0: return innerRate
  r = |rel|;  if r <= innerR: return innerRate
  s = r <= outerR ? (r − innerR)/(outerR − innerR) : 1;  if s == 0: return innerRate
  a = cone(axis = 지향 행렬 +Z, rel)               // 0x71038612b0: θ = atan2(|axis×rel|, axis·rel), θ<=inner→0, <=outer→(θ−inner)/(outer−inner), 그 밖 1
  if a == 0: return innerRate
  s = min(s, a);  return s == 1 ? outerRate : innerRate + s·(outerRate − innerRate)
```

대전 값(inner/outer 반경 3/6 × 전역 단위, 원뿔 40°/90°, DistRate 1.0/2.5)이면 리스너 근처 3 안이나 시선 원뿔 40° 안의 소리는 배율 1, 6 밖이면서 원뿔 90° 밖이면 2.5배 먼 것으로 계산됩니다. 이 배율이 감쇠 계산의 `+0x90`(§4.2.2 "정규화 거리")입니다.

원본 실행 `web/tools/r5_fx_listener_dir_emu.py`: `0x710384922c`+`0x71038612b0` 2,048건 비트 일치(대전 값과 무작위 값, 안쪽 988·바깥 197·중간 863). 스텁은 `atan2f` PLT(`0x7103e9c1e0`) 하나를 파이썬 f32 atan2로 바꾼 것뿐입니다. 결과 `analysis/completion/r5/fx_listener_dir_emu.json`.

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

- 1차 문서는 이 값들의 수식을 [미확정]으로 두었습니다. 아래 §4.2.1–4.2.3에서 AROC 평가식과 컬링을 판독했습니다. DistCoef 결합만 남았습니다. **6차:** DistCoef 결합은 §4.2.7에서 [실행]으로 확정했습니다(확장+4 = 1/DistCoef). 남은 것은 전역 단위 값입니다.
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

- 필터 커브는 D = 0, mixMode 1이라 `out = 1 − g`입니다. 가까우면 0(필터 없음), 멀수록 커지는 값입니다. 이 값(음원 계산 객체 +0x10, 0 이상)을 로패스 컷오프로 바꾸는 곳은 [미확정]입니다(§4.2.5). **6차:** 보이스 biquad 쪽 경로와 필터 3종 계수식은 §4.6에서 판독했고, 감쇠 +0x10이 어느 필터 채널·종류로 들어가는지가 남았습니다.
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
- **2026-10-03 5차 보완:** 여기서 "객체"는 음원 자체가 아니라 음원·리스너 쌍 기록(0x98 B, `0x7103863ab4`가 리스너마다 만듦)입니다. **+0x8C writer = `0x710383b88c`(리스너 거리), +0x90 writer = 리스너 지향성 거리 배율 `0x710384922c`**(§4.1.3, [판독 + 실행 2,048건]). 전역 단위의 writer와 값은 여전히 [미확정]입니다(다음에 볼 곳: `*0x710599a3f8 +0x10` 객체를 만드는 Alto 시스템 초기화).
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

**정정 후보(2026-10-03, 5차):** 위 첫 문단의 "감쇠 세트 +0x60 커브 → 출력 +0x08(우선순위)"는 근거가 약합니다. 두 근거가 다른 배치를 가리킵니다.
- AATN 데이터의 이름 칸 순서는 volume, farFx, filter, (빈 칸), priority, directivity, culling입니다(`sound_alto.py aatn`) [데이터]. 세트 객체가 이 순서로 +0x58부터 8 B씩 둔다면 farFx = +0x60, priority(AUDC) = +0x78입니다. 이 저장 순서 자체는 로더를 판독하지 않아 [추정]입니다.
- 게임 재정의 `0x7103129c98`은 출력 +0x08을 게임 쪽 FarFx 곡선(확장 +8의 sead 곡선, `SoundSpatialConfig.FarFxCurve`와 같은 `Type`/`MaxX`/`Data` 형태)으로 덮어씁니다. 출력 +0x18(세트 +0x78)은 결과가 0이면 음원을 사유 0x10002로 멈춥니다. AUDC에는 "cut 거리 너머 0"이 있으므로 이 동작과 맞습니다 [판독].
- 따라서 **출력 +0x08 = FarFx 전송량, 출력 +0x18 = AUDC 우선순위 × AACL 페이드**로 보는 쪽이 판독과 맞습니다. 로더(`0x7103851b4c` 부근 AATN 매직 비교 뒤 저장)를 읽어 확정해야 합니다. 이전 기록은 지우지 않습니다.

**정정(2026-10-03, 6차): 위 정정 후보를 [판독]으로 확정합니다.** 이유: AATN 로더를 읽었습니다.
- `0x710384eaac` 안 `0x7103851b4c`에서 매직 `AATN`(0x4E544141)·버전 1을 확인한 뒤 `0x7103860218(세트, &파일)`을 부릅니다.
- `0x7103860218`은 이름 칸 k(파일 +0xC + 8k의 u32, 문자열 영역 = 파일 + *(파일+8))의 이름으로 하위 커브를 찾아 `0x7103860088(세트, k, 커브)`에 넘깁니다. `0x7103860088`은 k < 5이면 **세트 +0x58 + 8k**에 저장합니다. 칸 5(파일 +0x34)는 AADR 목록에서 찾아 세트 +0x80, 칸 6(+0x38)은 AACL 목록에서 찾아 +0x88에 둡니다(`0x71038608e4`, `0x7103860b1c`).
- `sound_alto.py aatn`이 읽는 칸 순서(파일 +0xC부터 volume, farFx, filter, 칸 3, priority, directivity, culling)와 그대로 겹칩니다 [데이터]. 따라서 **세트 +0x58 = volume, +0x60 = farFx, +0x68 = filter, +0x70 = 칸 3(데이터는 빈 이름), +0x78 = priority(AUDC), +0x80 = directivity(AADR), +0x88 = culling(AACL)**입니다 [판독 + 데이터].
- 음원 계산 `0x7103863fe8`의 출력 대응(§4.2.2 표)과 합치면 **출력 +0x04 = 볼륨, +0x08 = farFx 커브(FarFx 전송량), +0x10 = 필터, +0x14 = 칸 3, +0x18 = AUDC 우선순위**입니다. 위 첫 문단 "세트 +0x60 커브 → 출력 +0x08(우선순위)"은 틀렸고, +0x60은 farFx입니다.

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

슈터 발사음 `WeaponMuzzle`(80°, 140°, 0.8, 0): 총구 앞 ±80° 안이면 그대로, 뒤쪽(140° 이상)은 0.8배입니다 [판독+데이터]. 필터 값 +0x10(AROC 필터 커브 + 지향성)을 실제 로패스 컷오프로 바꾸는 코드는 찾지 못했습니다 [미확정]. (6차 진행 상황: §4.6)

#### 4.2.6 DistCoef 결합 — 3차에서 좁힌 것 [판독-부분]

- 이 게임은 Alto 감쇠 계산(슬롯 7 `0x7103863fe8`)과 같은 서명의 **게임 쪽 재정의 `0x7103129c98`**을 가집니다. 여기서 거리 배율은 `+0x90 × 확장(+0x50)+4`이고, 확장 +1이 켜져 있으면 그룹 객체 +0x158의 게임 파라미터 `FriendDistCoef`(+0xd8)를 한 번 더 곱합니다. 확장이 없으면 정적 기본값(+0 = 1, +4 = 1.0)을 씁니다. 이어서 `d = 거리(+0x8C) / 전역 단위 × 배율`로 같은 AACL·AROC 계산을 합니다.
- 게임 파라미터 클래스(방문 함수 `0x7103127cf0`) 필드: `MinDirectVolume`(+0xdc), `FriendDistCoef`(+0xd8), `IsListenerDirectivityUseCamera`(+0xec), `OcclusionInterpTime`(+0xe4), `OcclusionHfReference`(+0xe0), `OcclusionMinGain`(+0xe8) 등. 같은 계열 `0x7103127304`: `CurveScaleToFarFxSendScale`, `FarFxCurve`, `SensitivityFilterCurve`.
- SLink ParamDefine 21 `DistCoef`, 24 `UseFriendCoef`가 확장 +4/+1에 들어간다고 보는 것이 자연스럽지만, 확장을 채우는 코드는 찾지 못했습니다 [추정]. 1.0 근처 값이 기본인 배율 자리라서, `DistCoef`(데이터 5–30)를 쓰려면 역수(`1/DistCoef`)여야 거리 감쇠가 상식적인 범위가 됩니다. 이 역수 관계도 코드로 확인하지 않았습니다 [추정].
- 웹 임시 구현은 `d = 거리 / DistCoef`를 유지하고 `UseFriendCoef && 아군`이면 `FriendDistCoef`를 곱합니다(값 미확인 — 게임 파라미터 데이터에서 찾아야 함).
- **2026-10-03 5차 보완:**
  - `FriendDistCoef` 값은 **1.5**입니다 [데이터: `spl__SoundSpatialConfig`, §4.1.3].
  - 게임 재정의 `0x7103129c98`의 거리 식을 다시 정리하면 `d = 기록+0x8C / 전역 단위 × (기록+0x90 × 확장+4 × (확장+1 ? FriendDistCoef : 1))`입니다. 기록+0x90은 리스너 지향성 거리 배율(§4.1.3)입니다 [판독].
  - 확장(+8)이 있으면 볼륨 출력 +0x04를 `MinDirectVolume`(게임 파라미터 +0xDC) 이상으로 올립니다. 출력 +0x08은 `확장+0x30 × 확장+0x10 × 곡선(d) / 볼륨`(곡선 = 확장+8의 sead 곡선, 표 `0x7105738610`)으로 바꿉니다 [판독]. 확장 필드에 어느 `SoundSpatialConfig` 곡선이 들어가는지는 [미확정]입니다.
  - (5차 기록, 6차에 해소 — 아래 "6차" 절) **DistCoef → 확장+4 연결은 이번에도 확정하지 못했습니다 [미확정].** 시도한 것은 세 가지입니다. ① ELink 식 인라인 getter 패턴(비트 21 검사 + ParamDefine 기본값 `+0x208`)을 0x7102000000~0x7103E00000 전수 스캔했지만 ELink `getColorRed`만 나왔습니다. ② 팝카운트 마스크 `0x3fffff` 사용처 전수 목록에서 SLink 경로를 찾지 못했습니다. ③ 문자열 `DistCoef`/`UseFriendCoef`의 xref도 없습니다. SLink 에셋 파라미터는 일반 인덱스 접근 함수로 읽히는 것으로 보입니다. 다음에 볼 곳: SLink 에셋 실행 `0x7103887e3c` 영역(`getVolume`/`getPitch`/`getLpf`/`getPriority`를 한 함수에서 읽는 0x7103888030~0x71038888f4)의 나머지 파라미터 처리, 그리고 확장 객체(기본값 표 `0x7105911d18`, 정적 초기화 안)를 할당해 음원 +0x50에 넣는 코드.

#### 4.2.7 DistCoef → 확장+4 = 1/DistCoef (6차, 2026-10-03) [실행 + 판독]

5차 "다음에 볼 곳"인 `0x7103888030~0x71038888f4`는 함수 경계 밖의 SLink 핸들 파라미터 갱신부였고(인덱스 3 Volume → 핸들 +0x84, 6 Pitch → +0x8C, 7 Lpf → +0x90, 14 Priority → +0x94), DistCoef는 거기서 읽지 않습니다. 확장 객체를 따라가 쓰는 곳을 찾았습니다.

**경로** [판독]
1. SLink 에셋 시작 `0x7103885e44`가 보이스를 만들 때 `0x710383b028(이미터=에셋+0x68, 시작 정보, …)`를 부릅니다. 이미터 +0xDC가 켜져 있으면 이미터 +0xE0..+0x110 블록을 **보이스 +0x1D0..+0x200**에 복사하고 보이스 +0x1CC = 이미터 +0xDC입니다. 이미터 +0xDC = !(SLink 사용자 리소스 +0xE4)입니다(`0x7103889d54`).
2. 같은 함수 끝에서 전역 xlink 시스템(`*0x710599ada8`) +0x1278의 **게임 훅 객체**(vtable `0x71056b45a8`, 생성 `0x71031432bc` 부근) 슬롯 5(+0x28) = **`0x710313d4ec`**를 부릅니다(인자 {사용자, 보이스 핸들 칸, 에셋 리소스, 에셋 인스턴스, 핸들 파라미터}).
3. `0x710313d4ec`는 SLink **사용자 정의(custom) 에셋 파라미터**를 일반 접근 함수로 읽습니다. custom 인덱스 i의 실제 번호 = ParamDefine 표 +0x34 + i이고, +0x34 = numAsset − numCustom = 29 − 9 = **20**입니다(표 setup `0x71038922f0`: +0x30 = numCustom, +0x34 = numAsset − numCustom) [판독 + 실행]. 접근 함수: float `0x710389331c`, bool `0x7103893040`, int `0x71038931b8`, string `0x7103892e08`(모두 마스크 비트가 없으면 ParamDefine 기본값, 있으면 값 해석 `0x7103893490`).

| custom i | 파라미터(번호) | `0x710313d4ec`의 처리 |
|---|---|---|
| 0 | Shape(20) | 문자열이 비어 있지 않으면 형상 블록(사용자 +0x40 객체, `0x7103911c40`/`0x71039109e8`) |
| 2, 3 | Volume2(22), Pitch2(23) | 핸들 파라미터 +0xBC = max(Volume2, 0), +0xC4 = max(Pitch2, 0), 플래그 +0xB8/+0xBA bit0·bit2. `0x7103887e3c`가 보이스 볼륨 = 핸들 볼륨 × Volume × **+0xBC**, 피치 = Pitch × **+0xC4**로 씀 |
| — | (보이스 +0x1CC == 0이면) SpeakerBalanceType(27) | 값 1 → custom 8 Pan을 읽고 `0x710312c1cc`, 0 → `0x710312c2dc`. 이 경로는 확장을 만들지 않음 |
| 1 | **DistCoef(21)** | 보이스 +0x1CC ≠ 0일 때 확장 = `0x710312b534(관리자+0x20, &보이스)`(보이스별 노드, 기본값 +0 = 1, +1 = 0, **+4 = 1.0**, +8 = 0, +0x10 = 1.0, +0x18 = 0, +0x20 = −1, +0x28 = 1, +0x2C = 0, +0x30 = 1.0). **DistCoef > 0이면 확장 +4 = 1.0 / DistCoef** (`0x710313d6e0`), 확장 +0x10 = 1.0 |
| 4 | UseFriendCoef(24) | 사용자 +0xB8의 로컬 속성 값 v(아래)가 1이면 확장 +1 = UseFriendCoef. v가 0이면 확장 +0 = 0 |
| 5 | UseOcclusion(25) | 확장 +0x28 = UseOcclusion. 단 v == 0이고 사용자 이름이 `Player`/`Weapon`으로 시작하면 0 |
| 6 | SoundSourceSize(26) | > 0이면 보이스 +0x1EC = 크기 × 전역 단위(`*(*0x710599a3f8+0x10)+0x20`) |
| — | — | 보이스 +0x1F8 bit2..4 = 전역 바이트 `0x7105912ac8`[0..2], **보이스 +0x200 = 확장**(`0x710313df24`), 훅 객체 +0x28/+0x30 목록에 보이스 추가 |

4. 프레임 처리에서 이미터 vt+0x50의 게임 재정의 `0x710312d398`이 보이스 +0x200(없으면 정적 기본값 `0x7105911d18`)을 감쇠 요소 파라미터 +0x30에 넣고, 감쇠 vtable 슬롯 4 `0x7103863788`이 요소 파라미터 0x38 B를 감쇠 객체 +0x20..+0x57로 복사합니다(파라미터 +0x30 → 감쇠 객체 **+0x50**) [판독]. 게임 감쇠 계산 `0x7103129c98`이 이 +0x50의 +4를 거리 배율에 곱합니다(§4.2.6).

사용자 +0xB8 값 v: 사용자 인스턴스 +0xB8의 u64(bit0 유효, bit1..16 = 인덱스)로 +0x80 정수 배열에서 꺼낸 로컬 속성 값입니다. 0과 1만 특별 취급합니다. 이 캐시 인덱스가 `SubjectiveType`(값 문자열 `Focused , Friend , Enemy`, main 문자열에 있음)이라면 0 = Focused(자기 소리), 1 = Friend입니다. 인덱스를 쓰는 곳을 찾지 못해 이 대응은 [추정]입니다.

**결론**

```
d = 거리(+0x8C) / 전역 단위 × 지향성 배율(+0x90) × (1 / DistCoef) × (확장+1 ? FriendDistCoef(1.5) : 1)
확장+1 = UseFriendCoef && v == 1(Friend로 추정)
보이스 +0x1CC == 0(이미터 +0xDC 꺼짐)이면 확장이 없어 1/DistCoef 가 곱해지지 않음(정적 기본 +4 = 1.0)
```

5차의 "역수일 것" [추정]은 [실행]으로 확정합니다. 웹의 `d = 거리 / DistCoef`는 단위·지향성 배율을 빼면 같은 꼴입니다.

**원본 실행** `web/tools/r6_fx_distcoef_emu.py`: 실제 `slink2.Product.100.bslnk`의 ParamDefine 표·에셋 파라미터 블록·direct 값 표를 에뮬 메모리에 올리고, ParamDefine 표 객체를 원본 setup `0x71038922f0`으로 만든 뒤 `0x710313d4ec`를 원본 그대로 실행했습니다. 사용자 정의 접근 함수와 값 해석, 확장 노드 할당 `0x710312b534`(트리 삽입 `0x710312b8b0` 포함)도 원본입니다. `UC_HOOK_MEM_WRITE`로 쓴 PC를 기록했습니다.
- 에셋 파라미터 블록 13,730개 × 사용자 이름 4종 × v(없음/0/1/2) = **219,680건**에서 확장 +4·+0·+1·+0x28, 보이스 +0x1EC·+0x200, 핸들 +0xBC·+0xC4가 파일 값으로 계산한 독립 재구현과 **전부 비트 일치**(불일치 0).
- 확장 +4를 쓰는 PC는 `0x710312b584`(노드 초기화 1.0)와 **`0x710313d6e0`(1/DistCoef)** 두 곳뿐입니다. 확장 +1 = `0x710313d95c`, +0x28 = `0x710313de08`/`0x710313deac`, 보이스 +0x200 = `0x710313df24`.
- 스텁: `nn::os::Lock/UnlockMutex` PLT만 ret. 실행하지 않은 범위: Shape 문자열이 있는 에셋의 형상 블록(사용자+0x40 = 0으로 건너뜀), 보이스 +0x1CC == 0 경로, 보이스 +0x1E0 ≠ 0 경로(그룹 곡선 탐색 `0x7103129400`), DistCoef 등이 Curve/Random 값인 블록 861개(제외). 결과 `analysis/completion/r6/fx_distcoef_emu.json`.

남은 것 [미확정]: 전역 단위(`*(*0x710599a3f8+0x10)+0x20`) 값과 writer, 사용자 +0xB8 인덱스의 속성 이름, 사용자 리소스 +0xE4(이미터 +0xDC를 끄는 값)의 의미.

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

- **2026-10-03 보완:** 제한기 4종의 비교·guard는 아래 §4.3.1(이전 위치 [solo_fx_audit.md §6.4](solo_fx_audit.md)), 비교 3함수 원본 실행 2,304건은 [solo_fx_audit.md](solo_fx_audit.md) §10.1에 기록했다. 정렬 뒤 생존·+8 시작 순번·그룹 +0x1B8 의미는 여전히 [미확정]이었다.
- **2026-10-03 5차:** 정렬 뒤 생존 규칙은 §4.3.2에서 [판독 + 실행]으로 확정했다. +8 writer와 그룹 +0x1B8 의미는 [미확정]으로 남는다.

#### 4.3.1 제한기 비교 키와 guard [판독 + 실행] (solo_fx_audit §6.4에서 옮김)

`g80/g84/g88` = 전역 0x710599aa80/84/88, `m = 1 << (0x71057349d0 & 31)`, `other = voice.byte[0xE] & ~m`. 이 전역들은 적용 함수 `0x71038473e8`이 정렬 직전에 씁니다: 0x71057349d0 = 제한기 +0x14(레벨 비트 번호), g80 = g84 = 제한기 +0xD, g88 = 제한기 +0xE가 켜져 있고 (+0x10 == 0이거나 타이머 +0x28이 0 이상 +0x10(0.2) 미만)일 때 참. 타이머는 매 적용마다 시스템 +0x1C(프레임 시간)만큼 늘고, +0x10에 닿으면 −1(꺼짐)이 됩니다. 정렬 뒤 새로 억제된 보이스가 생기고 +0x10 > 0이면 타이머를 0으로 다시 시작합니다. 제한 없음(count < 0)·0개 분기에서는 g88을 이전 값으로 되돌립니다 [판독].

- g80이고 `(voice.u32[4] & 0xfffffffe) == 6`이거나, g84이고 other ≠ 0이면 priority 키 = −1, 순서 키 = INT64_MIN.
- 그 밖 priority = `f32(f32(C4·CC)·factor)`. g88이고 byte[0xE] ≠ 0이고 other == 0이면 priority에서 1을 뺀 뒤 `trunc(f32(priority·255))`.
- 종류 1/2 비교 `0x7103848c88`은 `key(B) − key(A)`. 동률이면 정렬 함수가 종류 1은 A.+8 − B.+8, 종류 2는 B.+8 − A.+8을 씁니다.
- 종류 3/4의 64비트 순서 키는 각각 `~u32[8]`/`u32[8]`이고, g88의 위 조건이면 0xffffffff를 뺍니다. 큰 키를 먼저 정렬하고, 같으면 guard 보정 전 순수 priority 곱×255를 비교합니다.
- factor = 보이스 +0x210 → +0x18(또는 +0x180 vt+0x38 분기, 실행 안 함).

#### 4.3.2 정렬 뒤 생존과 억제 [판독 + 실행]

그룹 레코드 적용 `0x7103837384`가 제한기를 그룹 +0x178 객체(X) +0x18에 두고, 보이스 목록(노드 = 보이스 +0x230)을 X+0x30에 둡니다. 제한기 +8 = `limitCount`([0x17]), +0xC = 레코드 바이트 +0x63, +0xD = 레코드 바이트 +0x62, +0x10 = 0.2 [판독]. 보이스가 그룹 대기 목록(그룹 +0x1C0)에서 X+0x30(없으면 상위 그룹 목록 X+0x40)으로 옮겨진 뒤(`0x710383a330`) `0x71038388c4`가 적용 `0x71038473e8(제한기, 목록)`을 부릅니다.

```
apply(lim, list):                                     // 0x71038473e8
  if lim.count < 0:                                   // 제한 없음
     모든 보이스(상태 6/7 제외): byte[0xE] &= ~(1<<lim.bit); 비트가 모두 꺼지면 핸들 상태 3→4(재개)
  elif lim.count == 0:                                // 전부 억제
     모든 보이스(+0x1F8 bit1 꺼짐, 핸들 +0x14 ≠ 0): suppress(v)
  else:
     sort(list)                                       // vt slot3(연결 목록), 종류별 비교 §4.3.1
     i = 0
     for v in list (정렬 순서):
        if v.flags1F8 & 2: continue                   // 세지도 건드리지도 않음
        if i < lim.count: 레벨 비트 해제(위와 같음)    // 앞쪽 limitCount 개가 남는다
        else: suppress(v)
        i += 1
suppress(v):
  if lim.hard(+0xC): 즉시 정지 0x710383d940(0,0)      // 재생 중(상태 ≥3)이면 페이드 0 정지, 아니면 핸들 정지·상태 7
  elif 핸들 종류(+0xE0→+0x14) == 1: 정지(위와 같은 분기, 0x710383cffc)
  else: byte[0xE] |= 레벨 비트, 비트가 처음 켜질 때 핸들 일시정지(0x71037e019c)
```

종류 1에서 "우선순위 높은 것 먼저, 같으면 +8 작은 것 먼저"로 정렬한 뒤 **앞쪽 limitCount 개가 남습니다**. impl/fx §1.5의 "앞쪽이 남음 [추정]"은 이것으로 확정됩니다. 핸들 종류 1 이외(일시정지 대상)의 의미는 [미확정]입니다(루프·스트림으로 추정하지 않음).

원본 실행 `web/tools/r5_fx_limiter_core_emu.py`: 종류 1 제한기로 600경우(보이스 1~12개, limitCount −1/0/1~n+1, hard 켜짐/꺼짐, 상태 1/2/3/4/6/7, 핸들 종류 1/2, +0x1F8 bit1) 정렬 순서·비트·핸들 상태·호출 순서가 독립 재구현과 전부 일치했습니다. 생존 1,593·정지 795·일시정지 247·플래그 건너뜀 279건입니다. 스텁: `nn::os::Lock/UnlockMutex` PLT(no-op), `0x71037dfde4`·`0x71037e019c`·`0x710383da0c`·`0x71037dca78`·`0x7103862298`(호출 기록만). 종류 2~4 정렬 함수와 타이머 분기(+0xE 켜짐)는 실행하지 않았습니다. 결과 `analysis/completion/r5/fx_limiter_core_emu.json`.

**+8(순서 키) writer [미확정]:** 보이스 영역(0x7103830000~0x7103870000)에서 "카운터 +1 → [x, #8] 저장"과 "시스템 프레임 수(+0x84) → +8" 패턴을 스캔했지만 찾지 못했습니다. 다음에 볼 곳: 보이스를 그룹 대기 목록(+0x1C0)에 넣는 재생 시작 경로.

**정정(2026-10-03, 6차): +8 writer 확정 [실행 + 판독].** 재생 시작 `0x710383b028`이 보이스를 얻는 풀 함수 **`0x71037d790c(풀 = *(*0x710599a3f8+8))`**가 씁니다(보이스 영역 밖이라 5차 스캔에 걸리지 않았음).

```
alloc(pool):                                   // 0x71037d790c
  lock(pool+0xC8)
  s = pool+0x38 (검색 시작), n = pool+0x28, arr = pool+0x30
  [s, n) 에서 +8 == 0 인 첫 보이스 → pool+0x38 = s + 1          // 찾은 칸이 아니라 시작 +1
  없고 s >= 1 이면 [0, s) 에서 찾음 → pool+0x38 = (s >= n) ? 0 : s + 1
  찾으면: voice+8 = pool+0x20;  pool+0x20 += 1 (0xFFFFFFFF 다음은 1, 0 은 건너뜀)
          pool+0x40 목록에 연결(노드 = voice + pool+0x54), pool+0x50 += 1
  unlock;  return voice (없으면 0)
```

- 즉 **+8 = 보이스 시작 순번**(단조 증가, 0 = 빈 칸)이고, `0x710383b028`이 이 값을 핸들 id로 돌려줍니다(SLink 핸들 +0x78). 실패 경로는 +8 = 0으로 되돌립니다(`0x710383b0b8`).
- 제한기 종류 1의 동률 비교 `A.+8 − B.+8`(§4.3.1)은 **먼저 시작한 보이스가 앞**(살아남음), 종류 2는 반대입니다. 32비트 정수 뺄셈이라 순번이 감긴 직후에는 순서가 뒤집힐 수 있습니다(원본 그대로).
- 원본 실행 `web/tools/r6_fx_voiceserial_emu.py`: 합성 풀(보이스 1~12개, 순번 시작값 1·2·0x7FFFFFFE·0xFFFFFFFE·0xFFFFFFFF·무작위, 검색 시작 무작위, 중간 해제 포함) 300경우 **2,445회 할당이 독립 재구현과 전부 일치**(반환 보이스·각 +8·pool+0x20/+0x38/+0x50). 스텁: 뮤텍스 PLT만. 결과 `analysis/completion/r6/fx_voiceserial_emu.json`.
- 남은 것: pool+0x20 초기값(풀 생성자)은 확인하지 않았습니다. 웹은 1부터 세면 되고, 제한기 순서에는 상대 순서만 쓰입니다.

### 4.4 BusSetting [데이터]

`analysis/effect_sound/BusSetting.json`: `BusGraphPreset` 18개(Default, VS_City/VS_Hall/VS_Outdoor, Mission_*, Scene_*)와 이펙트 정의 29개.

- 버스: `WorldFx`, `FarFx`, `FarFx_Loud`, `Effect` → `FinalMix`(전부 6ch 48 kHz, 볼륨 1.0). 그래프 = WorldFx→FinalMix, FarFx→Effect, Effect→FinalMix(Send 1.0).
- 대전 야외 `VS_Outdoor`: FarFx 버스에 `FarFx_Reverb_Outdoor`(DspI3DL2Reverb: RoomGain −800, RoomHfGain −800, LateReverbDecayTime 5000, ReflectionsGain −500, ReverbGain −300, HfReference 1000 등).
- 감쇠 세트의 `farFx` 커브(§4.2, 현재 전부 모델 없음 = 1)가 FarFx 버스로 보내는 양으로 보입니다 [추정].
- 웹: WorldFx = 드라이 GainNode, FarFx = ConvolverNode(리버브 근사) 또는 생략. I3DL2 파라미터를 그대로 재현하는 WebAudio 노드는 없으므로 근사입니다.
- **2026-10-03 5차 보완:** 게임 재정의 `0x7103129c98`은 감쇠 출력 +0x08을 게임 FarFx 곡선(`SoundSpatialConfig.FarFxCurve`/`CurveScaleToFarFxSendScale`와 같은 sead 곡선 형식)으로 계산합니다(§4.2.4 정정 후보, §4.2.6). 데이터 값 [데이터]: `FarFxCurve.FarFx_WpMuzzle` = Hermit2DSmooth Data (4.0, 1.0, −0.6, 8.0, 0.0, −0.022), MaxX 15. `CurveScaleToFarFxSendScale.FarFx_WpMuzzle` = Linear2D Data (0.0, 0.1, 200.0, 0.8), MaxX 220. 이름은 `FarFx_Cmn`/`FarFx_FesBgm`/`FarFx_Spectacle`/`FarFx_WpMuzzle` 4종이고, 감쇠 세트의 farFx 이름(`$FarFx_WpMuzzle` 등)과 `$`만 다릅니다. 이 곡선이 어느 음원에 어떤 이름으로 연결되는지, 출력 +0x08을 FarFx 버스 전송량으로 쓰는 보이스 코드는 [미확정]입니다. I3DL2 리버브의 웹 대응은 여전히 근사입니다.
- **6차(2026-10-03):** AATN 로더 판독(§4.2.4 정정)으로 세트 +0x60 = farFx 커브 → 출력 +0x08이 [판독]으로 확정됐습니다. 출력 +0x08을 FarFx 버스 전송(서브믹스 이득)으로 바꾸는 aal 코드는 여전히 [미확정]입니다(믹스 볼륨 명령 `0x71037fce9c`까지만 확인).

### 4.5 패닝 입력 [판독-부분]

Alto 감쇠 vtable 0x71057352a0 슬롯 8 `0x71038644fc`(음원·리스너 쌍 갱신 `0x7103863ab4`가 매 갱신 호출)가 리스너 좌표계의 음원 위치(기록 +0x68/+0x78/+0x88 = x, y, z)로 패닝 입력을 만듭니다.

```
size = 음원 +0x3C (SoundSourceSize로 보임 [추정: 이름])
size <= 0 (점 음원), 음원 플래그 +0x48 bit0 켜짐:
   기록+0x1C = |(x, z)| (리스너 +0xE8 켜짐이면 × 리스너 +0xEC)
   기록+0x20 = 같은 값
   기록+0x24 = 기록+0x28 = atan2Idx(−x, z) ^ 0x80000000      // 0x7101252998, 0이면 0
size > 0: bit3이면 |p| <= size일 때 p = 0, 아니면 p ·= (1 − size/|p|); 스테레오 폭(bit4)이면 좌우 두 점의 거리·각을 따로 계산
bit0 꺼짐: 기록+0x1C = +0x20 = size, 각 = 0 (또는 인자 bit0이면 (−2, 2))
```

`0x7101252998`은 [r5 range]가 원본 실행으로 확인한 atan2 인덱스 함수입니다(SHARED.md). 이 각·거리를 실제 좌우 이득으로 바꾸는 스피커 배분 코드(`SpeakerBalanceUnifier`, 설정 `Sound/Interior/Stereo.alto__InteriorParam`: `InteriorSize` 3.0, `PresetType` cStereo [데이터])는 판독하지 않았습니다 [미확정]. 다음에 볼 곳: `InteriorSize` 리플렉션 방문 `0x710394fe24`(필드 +0x30)의 소비자. 슬롯 9 `0x7103864908`은 도플러(음원 +0x38 계수, 시스템 +0x2C × +0x18)입니다 [판독-부분].

- **6차(2026-10-03) 보완 [판독-부분]:** 좌우 이득이 최종으로 들어가는 SDK 호출은 `nn::audio::SetVoiceMixVolume`(GOT `0x7105770ce8`/`0x7105770cf0`)이고, 호출자는 aal 명령 실행 `0x71037fce9c` 하나입니다. 출력 대상 종류(vt+0x50 = 1 FinalMix, 2 SubMix)별로 명령의 채널 이득 6개 × 배율을 채널마다 넣고, −128 미만은 −128, NaN은 0으로 바꿉니다. 이 6채널 이득을 만드는 스피커 배분(위 패닝 입력 → 이득) 코드는 여전히 [미확정]입니다. 다음에 볼 곳: `0x71037fce9c`를 슬롯으로 가진 명령 vtable(포인터 직접 참조 없음 — GOT로 vtable−0x10을 읽는 생성 코드)과 그 명령을 채우는 함수.

### 4.6 보이스 필터(biquad) 경로 (6차, 2026-10-03) [판독 + 데이터]

필터 값(감쇠 출력 +0x10)이 컷오프로 바뀌는 곳을 찾기 위해 반대 방향(SDK 호출 → 계산)으로 거슬러 올라갔습니다. aal은 main 안에 있습니다.

1. `nn::audio::SetVoiceBiquadFilterParameter`(GOT `0x7105770c90`) 호출자는 aal 명령 실행 `0x71037ef290` 하나입니다. 명령 +0xE의 `BiquadFilterParameter`(enable, b0 b1 b2 a1 a2, Q14 정수)를 보이스에 그대로 넣습니다. `SetVoicePitch`는 `0x71037fe730`(명령 +8 float 그대로), `SetVoiceMixVolume`은 `0x71037fce9c`(채널별 이득 × 배율, −128 미만은 −128)입니다.
2. biquad 명령을 만드는 곳은 `0x71037fa0b8(amount, 보이스 aal 핸들, ch, 필터 슬롯)` 하나입니다. **amount를 [0, 1]로 자르고(NaN → 0)**, 필터 표(`*0x710599a408` +0x180, 64칸, +8 + 슬롯×8)의 필터 객체 vt+0x10(amount, 계수 출력)을 부릅니다. 객체가 없으면 enable = 0(필터 끔). 계수가 직전과 같으면 명령을 내지 않습니다.
3. 호출자 `0x710383e3e8`(ch 0), `0x710383e64c`(ch 1), `0x710383e8c0`(둘 다):
   - **ch 0 amount = max(보이스 +0x14C + a, 0)**, 필터 종류 = 보이스 +0x144(음수면 1). **ch 1 amount = 보이스 +0x150 + …**, 종류 = +0x148(음수면 3). 범위 고정은 보이스 파라미터 합성 `0x710383df38`(+0x14C/+0x150을 0..1로).
   - a: 보이스 +0x180(외부 공간 객체)이 있으면 그 vt+0x40(ch 0)/vt+0x30(ch 1). 없고 보이스 +0x208(감쇠 세트)이 있으면 리스너마다(세트 +0x4A 비트) `1 − w·(1 − r+0x4C)`(ch 1은 +0x50)의 최솟값, w는 리스너별 가중(+0x58[i], 실내 번호 일치 시). ch 1에는 보이스 +0x210 객체 +0x14를 더 더합니다.
   - SLink 보이스 +0x14C의 원천: SLink 핸들 갱신 `0x7103887e3c`가 보이스 +0x4C = **Lpf**(핸들 +0x90) + 핸들 파라미터 +0xC8을 씁니다(합성 뒤 +0x14C). 따라서 **SLink `Lpf`는 컷오프(Hz)가 아니라 필터 ch 0 amount(0..1)에 더해지는 값**입니다 [판독].
4. 필터 종류 → 필터 객체 [판독]: 종류 < 7이면 필터 관리자(`*0x710599a3f8`+0x30) +0x108[종류] 슬롯. 내장 초기화 `0x71037d7aa0`이 종류 0..5 → 슬롯 0..5, **종류 6 → 슬롯 0x3F**를 넣고 슬롯 0x3F에 내장 필터를 등록합니다. 종류 ≥ 0x40은 사용자 필터(관리자 +8 + (종류−0x40)×8 객체의 +0x10 슬롯).
5. 필터 객체별 계수식 [판독]:

| 필터 | 등록 | amount a → 계수 |
|---|---|---|
| 내장(슬롯 0x3F, vt 0x71057305d0, 계산 `0x71037d8b78`) | `0x71037d7aa0` | 표 128칸(i = trunc(a·127)) = `0x71038048f0(g = −40·i/127 dB, 0, f = 8000 Hz, fs = aal 출력 샘플레이트, 기본 48000)`. 1차 저역 통과: G = 10^(g/10), c = cos(2πf/fs), p = ((1 − G·c) − √(2G(1−c) − G²(1−c²)))/(1 − G), **b0 = 1 − p, a1 = p**, 나머지 0. g = 0이면 통과(b0 = 1) |
| `PeakingFilter`(사용자 슬롯 0x10) | 게임 `0x710314372c` | 게임 콜백 `0x7103141e30` → `0x71038046fc`(피킹 EQ, K = tan(πf/fs), V = 10^(G/20)): 값은 `spl__SoundBiquadFilterConfig.User0` = **CenterFreq 3150, Gain −21 × a dB, QValue 5**(SampleRate 기본 48000) |
| `HiShelvingFilter`(사용자 슬롯 0x11) | 게임 `0x71031437e0` | 게임 콜백 `0x71031423ac` → `0x7103804504`(하이 셸프, √V 사용): `User1` = **CenterFreq 19500, GainDb −80 × a dB, QValue 0.5** |

   - 두 게임 필터의 값 객체는 BiquadFilterConfig(`*0x7105912e00`+0x158) +0x30(User0 클래스, 필드 `Gain`, 방문 `0x710311f2f0`)과 +0x38(User1 클래스, 필드 `GainDb`, 방문 `0x710311e47c`)이고, 필드 +0x30 CenterFreq, +0x34 Gain(Db), +0x38 QValue, +0x3C SampleRate입니다 [판독 + 데이터: `analysis/camera/SingletonParam/Gyml/Singleton/spl__SoundBiquadFilterConfig…json`].
   - 계수 형식은 Q14 정수(×16384 후 정수 변환)입니다. 사용 불가 조건(f ≤ 0, fs ≤ 0, f ≥ fs/2, tan < 0)이면 통과 계수(b0 = 0x4000)입니다.

**남은 것 [미확정]:** SLink 보이스의 필터 종류(보이스 +0x44/+0x48 → 합성 뒤 +0x144/+0x148)를 쓰는 곳(`0x7103887e3c`는 +0x48 = 핸들 파라미터 +0xD8을 씀, 이 +0xD8 writer 미확인), 슬롯 1·3(기본 종류 1·3)에 등록된 필터 객체, 보이스 +0x180 공간 객체의 정체. 그래서 "감쇠 필터 커브 값 → 실제 주파수 응답"은 위 세 필터 중 무엇이 쓰이는지에 달려 있고, 아직 하나로 고르지 못했습니다. 다음에 볼 곳: 필터 표 슬롯 1~5에 객체를 넣는 코드(`*0x710599a408`+0x180 +0x10..+0x30 저장), 핸들 파라미터 +0xD8 writer, `0x71037d8cfc`(종류 번호 목록).

## 5. 웹 재생 파라미터 (SLink 에셋 → WebAudio)

| SLink 파라미터 | 원본 근거 | WebAudio 대응 | 확정 |
|---|---|---|---|
| RuntimeAssetName | BARS 이름 | 디코드된 AudioBuffer 키 | [데이터] |
| Volume (Random 등) | xlink 값 해석(§xlink_format 4.2) | `GainNode.gain` 곱 | 값 [데이터], 난수식 [참고] |
| Pitch | 같음 | `playbackRate`(음높이 비율, 1.0 = 원음) | 비율 해석 [추정]. **6차:** 보이스 피치 = 핸들 Pitch × Pitch2(`0x7103887e3c`, §4.2.7)이고 최종값은 `nn::audio::SetVoicePitch`(`0x71037fe730`)에 그대로 들어감 [판독]. SDK 피치는 재생 속도 비율이라 playbackRate 대응은 맞음. 중간 합성(`0x71037ded4c`)의 곱/합 여부는 미판독 |
| Delay | ParamDefine Float | `start(ctx.currentTime + delay/60)`, 프레임 단위로 봄 | 단위 [추정] |
| Lpf | 기본 0.0 | BiquadFilter lowpass, 0이면 끔 | [미확정]. **6차:** 컷오프(Hz)가 아니라 보이스 필터 ch 0 amount(0..1)에 더해지는 값(§4.6) [판독]. amount → 응답은 필터 종류에 달림(내장 1차 저역 −40·a dB @8 kHz / 피킹 3150 Hz −21·a dB / 하이 셸프 19.5 kHz −80·a dB), 종류 선택 [미확정] |
| DistanceParamSetName + DistCoef | §4.2 | PannerNode 대신 매 프레임 `evalAROC` 직접 gain 계산 | AROC 수식·컬링 [판독], 거리 배율 +0x90 = 리스너 지향성 [실행], FriendDistCoef 1.5 [데이터], **DistCoef: 확장+4 = 1/DistCoef [실행 219,680건, §4.2.7]**, 전역 단위 [미확정] |
| (리스너 위치) | §4.1.2 | 청자 = 주시점 + Rᵀ·(0,0,1.5) | [실행] 공식, 주시점 공급원 [미확정] |
| GroupName | §4.3 | 그룹별 동시 발음 제한 큐, 덕킹(MAND) | 무기 그룹 제한기 없음 [판독+데이터], 덕킹 표 [데이터], 정렬 뒤 앞쪽 limitCount 생존 [실행] |
| Priority | 기본 0.5 | 제한 초과 시 낮은 것부터 정지 | 제한기 키 = int(C4·CC·factor·255) [실행], C4·CC와 SLink Priority의 연결 [미확정] |
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
| DistCoef 결합(거리 정규화의 +0x90/전역 단위) | [미확정], 게임 재정의 0x7103129c98까지 좁힘(§4.2.6). **5차:** +0x90 = 리스너 지향성 거리 배율 [실행 2,048건], FriendDistCoef 1.5 [데이터]. **6차 해소:** DistCoef → 확장+4 = 1/DistCoef, writer `0x710313d4ec`(게임 SLink 훅 슬롯 5) [실행 219,680건] §4.2.7. 전역 단위만 [미확정] | 전역 단위 writer(`*(*0x710599a3f8+0x10)+0x20`), 사용자 +0xB8 속성 이름 |
| 리스너 위치(TargetOffset) | **해소** [판독 + 실행 512건] §4.1.2. 주시점 공급자는 [미확정] (6차 추가 탐색 실패, §4.1.2) | Alto·게임 사운드 영역 밖의 vt+0x38 호출, 리스너 +0x100 writer |
| 리스너 지향성 | **해소** [판독 + 실행 2,048건] §4.1.3 | 감쇠 세트 +0x90 바이트의 AATN 칸 |
| AUDC/AADR 평가식 | **해소** [판독] §4.2.4, §4.2.5. **6차:** AATN 로더 판독으로 세트 +0x58 volume / +0x60 farFx / +0x68 filter / +0x70 칸3 / +0x78 AUDC / +0x80 AADR / +0x88 AACL 확정 [판독 + 데이터] | AUDC 우선순위(출력 +0x18)를 제한기 키로 쓰는 곳 |
| 필터 값 → 컷오프 변환 | [미확정], **6차에 크게 좁힘** §4.6: SDK biquad 호출 → 명령 `0x71037fa0b8`(amount 0..1) → 필터 객체 3종 계수식 [판독 + 데이터], SLink Lpf = ch 0 amount 가산 [판독] | SLink 보이스 필터 종류(+0x144/+0x148) writer, 필터 표 슬롯 1~5 등록, 보이스 +0x180 객체 |
| 패닝 | 입력(리스너 좌표 XZ 거리·atan2 인덱스) [판독] §4.5, 좌우 이득 법칙 [미확정]. 6차: 최종 SDK 호출 `SetVoiceMixVolume` 실행부 `0x71037fce9c` [판독] | 믹스 볼륨 명령을 채우는 함수, InteriorParam 소비자 |
| AGST GRP 레코드(동시 발음 제한) | **레코드 배치 해소** [판독] §4.3, 무기 그룹은 제한기 없음 [데이터]. **5차:** 정렬 뒤 앞쪽 limitCount 생존·억제 규칙 [실행 600경우] §4.3.2. **6차:** 보이스 +8 = 시작 순번, writer `0x71037d790c` [실행 2,445회] | [0x21] (+0x1B8) 의미, 종류 2~4 정렬 실행 |
| BusSetting | **해소** [데이터] §4.4 | — |
| FarFx 전송량 | 게임 곡선 데이터 [데이터], 출력 +0x08 계산 [판독] §4.2.6, 세트 +0x60 = farFx [판독, 6차] | 확장 곡선 선택, 버스 전송 코드 |
| AMTA 데이터 블록 f[1]–f[3] | [미확정] | 웹 재생에 불필요 |
| Pitch 단위 | 비율 [판독, 6차]: `SetVoicePitch`에 그대로(§5) | 중간 합성 `0x71037ded4c` |
