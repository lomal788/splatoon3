# 공통 조명 r6 — 하늘 큐브 변형과 남은 환경맵 경로

2026-10-03. Lby_Lobby00 v0. 원본 신규 판독과 실제 웹 반영을 구분한다. 고정 inventory의 질문을 쪼개거나 GR05/GR10 전체를 확정으로 올리지 않는다.

## 1. 목적·범위·확정 수준

화면용 하늘과 환경광 캡처용 하늘의 색 차이를 원본으로 확인하고 `SkyView`에 반영했다. **mSky의 큐브 색 계산 [판독], 파라미터 [데이터]**, 웹 GPU 21건 검증이다. 원본 NVN GPU 실행·최종 환경맵 픽셀 동등성은 주장하지 않는다. 캐릭터 SSS·ColPaint·잠영 표시는 별도 범위다.

## 2. 원본 근거와 기존 분석 재사용

먼저 SHARED/FUNCS와 `decomp_index.py --no-build`로 확인했다. 기존 `r5_gfx_stage/b16_sky.c`의 `0x71010B9088` 재질 방문자, `r6_gfx_stage/c1_envmap.c`의 `0x710102CE04` 캡처 흐름, `r5_gfx_stage/b1.c`의 `0x710102E6C8` 생성자는 재디컴파일하지 않았다.

`Hoian_UBER.Product.bfsha`의 실제 재질 옵션 전체와 keys.tsv를 대조했다. `Sky_Daytime00.mSky` 화면용은 **program25**, `gsys_assign_cubemap`은 **program27**, 둘 다 옵션 불일치0·후보1이다. `analysis/port_common_r6/sky/selection.json`에 대조를 보존했다. Negate 괄호·CB1 분기표를 보완한 기존 분석 전용 CLI로 program27을 역번역했다. 원본 파일/표준 도구는 수정하지 않았다.

## 3. 진입점과 전체 호출 흐름

```text
기존10B9088 → SkySphere의 visible/capture/saturation 재질 필드
MapView.captureEnvironment → LightingState.capture 두 번
  setCapture(true) → mSky cube27 색 계산 → 웹 256² cube
  SH7MRT 투영 → 기존 원본 CPU packing → hSH
  웹 PMREM → scene.environment
  setCapture(false) → mSky program25 화면 색 계산
```

원본 `102CE04`는 별도로 Illuminate 합성과 native prefilter를 요청한다. 아래 원본 후속 함수들을 새로 판독했지만, 그 경로를 웹 PMREM와 동등하다고 하지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 원본 | 값/의미 | 수준·웹 연결 |
|---|---|---|
| SkySphere ExposureNotInEnvMap | 2 → exp2f → 화면 노출4 | 기존 [판독]/[데이터], 유지 |
| EmissionIntensInEnvMap | 80, exp2를 적용하지 않음 | 기존 [판독]/[데이터], 유지 |
| SaturationInEnvMap | 0.4000000059604645 | [데이터], 이번 cube27 연결 |
| cube27 휘도 계수 | (.298911989,.586611,.114478) | 신규 [판독]; 일반 tone 계수와 혼용하지 않음 |
| mSky emission_intensity / emission_color / albedo_color | BFRES/배포 GLB 기존 원본 파라미터 | [데이터], 같은 슬롯 소비 |
| 102FF04 holder+0xC34 | f32 .11 | [판독]; Illuminate cLightParam의 writer이며 하늘 saturation과 별개 |
| 102FF04 holder+0xC78..C84 | MainLight 입력+0x128..0x137의 RGBA 복사 | [판독]; Intensity10을 임의 곱하지 않음 |
| 102FF04 holder+0xCC0 + 16*i | LightArray의 방향3float·Intensity×holder+EC4 | [판독]; 웹 Illuminate 공급은 아직 없음 |

## 5. 상태 전이와 전체 수명

`setCapture(true)`에서 노출80·saturation 데이터값·cube 분기를 함께 선택한다. 화면으로 복귀할 때 노출4·saturation1·화면 분기를 복구한다. 화면 분기는 휘도 보정을 우회하여 기존 program25의 식을 유지한다. `LightingState.capture`의 finally에서도 복구한다. 첫 SH를 두 번째 캡처가 소비하는 기존 수명은 그대로다.

## 6. 계산식·조건·상세 의사코드

```text
C = texture(_e0, materialUV).rgb * emission_color.rgb
Y = fma(C.b,.114478,fma(C.g,.586611,C.r*.298911989))
cubeRGB[k] = fma(fma(C[k]-Y,SaturationInEnvMap,Y),
                 emission_intensity*EmissionIntensInEnvMap,albedo_color[k])
alpha = 1
visibleRGB = C*(emission_intensity*exp2(ExposureNotInEnvMap))+albedo_color
```

웹 GLSL은 같은 항·순서로 공급한다. NVN FMA와 WebGL 연산/드라이버의 반올림은 비트 동등성이 검증되지 않았다.

Illuminate 후속 신규 판독:

- `1037098`은 MainLight 포인터가 nonnull일 때만 임시 `illuminate` texture를 만들고 `102FF04` → `10351E8` → `1035C4C(layer0)` → `1035FA0` → mip별 되복사를 한다.
- `10351E8`은 원본 CSTR를 직접 읽어 **MRT=1**, 입력 view+3A가1이면 FILTER_TYPE=3, 아니면2, Illuminate 인자+38 포인터가 있으면 ILLUMINATE=1을 선택한다. shader의 변형이 달라질 수 있으므로 legacy 파일 하나를 전체 경로로 승격하지 않는다.
- `1036A18`은 native layer **0..11을 실제로 각각 draw**한 뒤 `1036D84`를 호출한다. `1035C4C`의 roughness는 `t=layer/(layerCount-1)`, `r=t+(sin((t-.92)*2π)-.4817533)*.13`; 별도 포인터가 있으면 그 float로 덮어쓴다. cParam0=(r,4,1024,sampleCount)이다 [판독]. sampleCount는 상위 객체/요청 분기에 따라 달라진다.
- `1036D84`는 flag0일 때 layer12를 공용 texture에 복사한다. flag1이면 별도 producer 자원/Illuminate 처리 분기를 탄다. 어느 분기가 최종 Lby frame에 활성인지는 미확정이다.
- `1037474` → `1030288`은 gyml 상속을 따라 설정3float와 최대20개 LightArray 항목을 holder에 복사한다. 입력의 필드 이름·런타임 선택 전체는 별도 typed visitor 대조가 필요하다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

캡처된 hSH는 기존 stage/player/knownFX가 공유한다. 이번은 그 입력 하늘색을 고친 것이다. MainLight/베이크/spot rig 값이나 팀색 행을 임의로 바꾸지 않았다. `mSun`은 정확한 cubemap 옵션 후보를 못 찾았다(최소 불일치1, ordinary 5359/5360). 선택 실패를 mSky처럼 확정하지 않는다.

## 8. 다른 기능과의 상호작용

공통 조명 후 HDR/Bloom/색 보정은 [common_post_r6](common_post_r6.md), 그림자는 [common_shadow_r6](common_shadow_r6.md)을 따른다. 하늘 saturation은 tone/CC saturation과 별개의 단계다. 카메라 캡처 near4/far1024와 플레이 카메라 값을 혼용하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

`sky.ts`에서 cube27/visible25 분기를 추가했고 `lighting.ts` 진단에 그 연결과 남은 Illuminate 경계를 표시했다. 원본 재질·텍스처/GLB/에셋은 변경하지 않았다. native cube12layer/BRDF를 원한다면 입력 cubemap 재질 변형, Illuminate highlight texture·sampler·typed 설정, layer12 생산/최종 소비를 함께 연결해야 한다.

## 10. 검증 코드·실행 결과·기대값

| 실제 실행 | 결과/경계 |
|---|---|
| `python analysis/port_common_r6/sky_select.py` | mSky25/27 각1후보·불일치0. mSun cube는 불일치1 → 미확정 |
| 보완 CLI `prog-bfsha … --index 27` | exit0, cube GLSL 확보. 원본 GPU 실행 아님 |
| `node analysis/port_common_r6/sky_gpu.mjs` | 실제 Lby 캡처2회·화면 복구 확인; 입력7×visible/cube/restored=21건 RGB32F GPU readback, 최대 절대차0.0000159153, page/console/HTTP/GL오류0 |
| 기존 Ghidra readOnly QuickDecomp 4배치 | 4+6+6+3함수, exit0. 재사용 함수는 배치에서 제외 |
| BFRES `dump` 및 `graphics_bntx.py info` | IlluminateEnvMap: 모델0, embedded64² BC1_SRGB highlight texture1·mip7. Fld_Emission4EnvMap은 cube shape24indices·재질1 |

첫 압축 해제는 시스템 Python에 zstandard가 없어 실패했다. `.venv/Scripts/python.exe`로 동일 입력을 해제해 성공했다. 실패한 중간 dump의 모델0을 데이터 결론으로 쓰지 않았고, 성공 dump의 externalFiles/texture header를 다시 대조했다. 이 위치에는 키를 읽거나 기록하지 않았다. 기타 경로/검색 실패와 실제 명령은 `analysis/port_common_r6/commands.md`에 기록한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 남은 것 | 시도·막힌 이유·다음 위치 |
|---|---|
| native 최종 cube 픽셀·SH | cube27 산술은 확보, 그 외 재질 cubemap/Illuminate/pass 자원·원본 frame readback 없음. `1037098/10351E8/1035C4C`의 live 입력·원본 GPU capture 필요 |
| Illuminate typed/default/live 설정 | writer/상속 복사 확보, C34 .11·색/각도/Intensity 소비 확인. `1030288`의 +58/+5C/+60 필드명을 typed visitor와 대조하고 global5818E38+B98 roughness override의 실제 값을 확인해야 함 |
| native12layer/BRDF/layer12 | draw/warp/후속 copy는 확보, 모든 변형의 sampler·압축/인코딩·계층/요청 선택 전체와 최종 투영 input 불명. `1036A18/1036D84/103921C`의 실제 RT와 downstream consumer 필요. 웹 PMREM 유지 |
| mSun cubemap 변형 | 완전일치 후보 없음. 원본 material assignment fallback/상위 pass 선택 확인 필요 |
| sky 배치·GPU 산술·동일 화면 | Offset/Scale의 원본 writer, mip/sampler/compression·NVN FMA/live frame 전체 검증 필요 |

**2026-10-03 정정:** r5 §11의 “SaturationInEnvMap .4 미연결”은 이번 cube27 원본 판독과 웹 연결로 좁은 항목만 해소했다. 최종 cube 내용 전체 미확정은 유지한다. `stage_rendering`의 IlluminateEnvMap.bfres “그릴 모델” 설명은 성공 BFRES dump상 모델0·texture-only이므로 정정한다. Fld_Emission4EnvMap은 실제 모델이며 서로 혼동하지 않는다.
