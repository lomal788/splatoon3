# 첨부 화면과 현재 웹의 그래픽 차이·원본 동등성 경로 — 2026-10-03

## 1. 기능 개요와 사용자에게 보이는 동작

목표는 사용자가 제공한 원본 화면과 같은 **잉크 표면·튀김·캐릭터·광원·최종색의 동작**이다. 사진의 색감을 임의 보정하여 비슷하게 보이는 것으로 완료하지 않는다. 현재 소스에는 원본 표시 경로가 여러 곳에서 끊겨 있으며, 기존 “그래픽 반영”은 일부 기반 연결을 뜻한다. 화면 동등성이 검증된 상태가 아니다.

| 첨부 화면에서 볼 비교 대상 | 현재 웹에서 확인한 차이 | 확인 수준·근거 |
|---|---|---|
| 바닥/벽의 젖은 잉크·도색 경계·반사 | paint.page0 일반 PBR overlay, roughness .35, envMap없음. 원본 map ink 분기/normal/환경층·BRDF 입력이 연결 안 됨 | [웹 실행] actual browser + [원본 표면](reference_ink_surface.md) |
| 입체적인 탄/튀김·시간에 따라 커짐/사라짐 | 원본 emitters 애니메이션 키의 번들→실행기 전달 결손; unlit 동일 material·VAT/normal 누락 | [웹 실행]+[데이터]+[판독], [발사 효과](../effect_sound/reference_shooter_visuals.md) |
| 피부·머리/오징어의 투과·산란·필름 | native enable_taransmission 철자를 잘못 찾고, 로드된 _Thc/_re2·cheapSSS/edge/film 최종 소비가 빠짐 | [웹 실행]+[판독], [캐릭터](reference_character_lighting.md) |
| 발밑/잠영 표면 파문·모델 숨김 | ownInk1/swimmingtrue에도 squid2mesh 표시, SplPlayer effect/상태 공급 부족 | actual 웹 fixture와 [기존 B7a0 분석](squid_ink_visibility_r2.md), 새로운 player FX 계약은 발사 효과 문서 |
| 화면 전체 채도·밝기·광원 반사 | post uniform에 LUT/Bloom/Vignette 없음. 원본 HSV→RGB8점→Gamma CC 경로와 분리됨 | [웹 실행]+[판독]+신규 [LUT 저장](reference_hdr_output.md) |
| 조명/반사 계산의 부호·괄호 | 일부 역번역 GLSL의 Negate 괄호 결함. 그 텍스트를 그대로 옮기면 원본과 다른 식 | 원시 Maxwell+보완출력 [판독], 원본 이상 동작으로 해석하지 않음 |

## 2. 분석 대상 원본·버전·자료 위치

분석 대상은 Splatoon 3 v0 Lby_Lobby00 1인 스플래시슈터다. 사용자 사진6501/6499는 **정성적 외관 참고**다. 사진만으로 v0·Lby·장비/감도/팀색/광원·프레임을 검증한 것은 아니다. 6501은 두 패널이며 상단 HUD/효과를 그대로 Lby 슈터로 대입하지 않는다. 다른 무기/특수 동작은 이번 분석 범위 밖이다.

![사용자 제공 비교 화면6501](../../../analysis/reference_graphics_r3/references/6501.jpg)

![사용자 제공 비교 화면6499](../../../analysis/reference_graphics_r3/references/6499.jpg)

원본 자료·도구·SHA는 각 상세 문서와 analysis/reference_graphics_r3/*/commands.md 및 closeout.json에 있다. 기존 SHARED/FUNCS/decomp_index와 r2 문서를 먼저 확인해 알려진 근거를 재사용했다. 웹/impl/original은 읽기 전용이며 새 문서는 docs/graphics·effect_sound·port에만 저장한다.

## 3. 진입점과 전체 호출 흐름

```text
원본지형/ColPaint속성 → map ink surface shader ─┐
원본캐릭터/팀색/SSS/cloth/AS → character shader ┼→ native light/SH/reflection/shadow → HDR
원본ELink→VFXB→emit/VAT/color/alpha → FXshader ─┘
 → 노출/Bloom → Tone4 → ColorCorrection LUT → Vignette → Gamma
```

현재 웹은 원본 데이터를 로드하는 부분과 **최종 소비자를 실제로 연결한 부분**이 다르다. GLB에 재질 옵션/texture가 있거나 JSON에 emitter가 있다는 것만으로 원본 경로가 구현됐다고 판정하지 않는다. producer→asset→runtime→vertex/fragment→최종 HDR까지 확인한다.

## 4. 구조체·필드·상수·열거형 표

| 원본/현재 계약 | 확정된 값 또는 결손 | 구현 책임 |
|---|---|---|
| map ink sampler/normal/환경층 | 원본 shader1714/946 상세는 표면 문서 | stage visual mesh/ColPaint 속성·지형 ink shader |
| 현재paint material | roughness .35/metalness0/envMapfalse,MeshStandardMaterial | actual client/paint와 native forward 연결 |
| emitter animation | fields/키 전달과 actualconstructor 상태는 FX 문서 | 자원 추출→런타임 데이터 계약 |
| enable_taransmission | native 철자 그대로,body transmission_rate .3/scattering_rate .2 | hoian option/forward material 소비 |
| HDR post | actual exposure2/gamma1, uniform3개 | native output 선택/CC/Bloom/Vignette |
| LUT 저장 | N8³,level1, RGB11/11/10 UFLOAT·4B/texel,agl1A→NVN63 | 원본 포맷/quantization/sampler3D |
| B7a0 | 기존 native 지연/표시holder 입력,현재 snap/뷰 미연결 | core 상태 공급→인간/_Hlf/오징어 표시 |

위 확인을 함수 전체 shader/GPU/frame의 확정으로 확대하지 않는다. 원본 변수/웹 권장 이름의 상세 대응은 각 문서 §4와 §9를 따른다.

## 5. 상태 전이와 전체 수명

동일 외관은 시작·발사·착탄·칠·변신·잠영·복귀 전 구간에서 이어져야 한다. emitters의 시간 키·수명·색·alpha를 놓치면 첫 프레임 모양만 같아도 유지/소멸이 달라진다. ownInk 모델 숨김과 표면 파문도 서로 다른 소비자다. 원본 AS 상태와 같은 모델 파일을 갖췄다고 전체 포즈가 같아지는 것은 아니다.

현재 브라우저 probe는 world.step을 제어하고 같은 player 발밑에 ownInk stamp를 공급했다. fixture의 잠영 상태는 실제 웹의 sample/상태·재질을 확인한 것이며 원본 wholeframe 실행이 아니다.

## 6. 계산식·조건·상세 의사코드

상세 식을 여러 문서에 복사하지 않는다. **원본 근거 → 실제 웹 차이 → 필요한 소비 연결**을 다음 문서로 추적한다.

1. [reference_ink_surface §6](reference_ink_surface.md): mask/normal/BRDF·환경과 raw NegA로 보완된 표면식.
2. [reference_shooter_visuals §6](../effect_sound/reference_shooter_visuals.md): animation key/color·alpha/VAT·depth/blend.
3. [reference_character_lighting §6](reference_character_lighting.md): 주광/역광 cheapSSS·film normal·tau 소비.
4. [reference_hdr_output §6](reference_hdr_output.md): texture format·1mip·선형 크기·Tone4 뒤LUT.
5. [squid_ink_visibility_r2](squid_ink_visibility_r2.md): 숨김producer/holder의 원본 실행 경계.

부호 반전식의 잘못된 역번역과 원본 명령의 계산을 구별한다. 사진의 하이라이트로 roughness/조명 세기를 역으로 발명하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

사진에서 캐릭터 주변 효과는 무기/상태/장면에 따라 다르다. 참고 화면의 특수/다른 무기를 사격장 기본 효과로 추가하지 않는다. 사격장 스플래시슈터는 ELink의 실제 선택 emitter와 상태를 따라야 한다. 해당 material이 native 팀색·light 입력을 받는지도 함께 연결한다.

사진과의 차이에서 HUD는 이번 분석 우선순위가 아니다. 인게임 표시가 맞은 다음 UI를 진행한다는 사용자 범위를 유지한다. 원본·웹 카메라/팀색/프레임/도색mask가 같은 캡처가 있어야 정량 픽셀 비교를 할 수 있다.

## 8. 다른 기능과의 상호작용

web paint collision overlay는 칠 판정에 쓰는 차트와 시각 지형을 같은 것으로 처리한다. 원본 시각 모델 ColPaint 속성·베이크/normal/재질 번호와 함께 소비되어야 지형의 경계/빛 반응이 유지된다. 탄/도색 로직이 원본 표본과 일치해도 FX 표시계약이 달라질 수 있다. 원본 조명10은 확인된 값이므로 화면이 어둡거나 과광택이라는 이유만으로 임의 세기를 바꾸지 않는다.

## 9. 웹 포팅 구조와 구현 순서

구현 지시 요약은 [port/reference_graphics](../port/reference_graphics.md). 순서는 **표면·FX 공급 계약→캐릭터·잠영→공통 광원/최종색→동일조건 화면 검증**이다.

- 먼저 native surface 입력과 animation key 전달처럼 실제 끊어진 소비자를 연결한다. 광택 숫자1개 수정으로 완료하지 않는다.
- 원본 byte/GLB/VFXB에서 이미 있는 정보와 추출 때 버린 normal/색/시간 키를 구분하고, 정확히 필요한 필드를 보존한다.
- raw/괄호 보완 shader로 식을 검증한다. 기존 잘못된 GLSL을 코드의 기대값으로 복사하지 않는다.
- native capture/샘플러/양자화/AS 전체 포즈는 남은 근거를 추적하고 미확정 유지한다.

이번 작업은 구현 변경이 아닌 원본 분석/MD다. 고정 포트 반영률을 올리지 않는다.

## 10. 검증 코드·실행 결과·기대값

현재 실제 브라우저 화면:

![현재 웹 발사 fixture](../../../analysis/reference_graphics_r3/parent/firing.png)

![현재 웹 자기 잉크 잠영 fixture](../../../analysis/reference_graphics_r3/parent/own_ink_squid.png)

node browser_probe.mjs: actual5190 Lby3phase·Edge SwiftShader·page/console/HTTP 오류0. post.exposure2/gamma1,paint.page0의PBR/roughness.35/envMapfalse,ownInk1·swimmingtrue·squid2메시 확인 [웹 실행]. 원본GPU실기·동일프레임 픽셀 대조가 아니다. fixture의첫Fire 화면만으로 AS연결누락을 확정하지 않으며 장기hold 확인은 별도 기록한다.

원본 CPU 신규 metadata 56/56 + linear3D 16/16 + sampler constructor 1건·builder 12/12은 HDR 문서에 실행 경계를 기록했다. 각 담당의 실제source/shader/asset 검증 결과는 상세문서 §10과 종합 final_verification.json을 따른다. 이미 실행한 r2 28/128/10800건 등을 새로 합산하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 전체 동등성에 남은 것 | 이번 시도와 한계 | 다음 확인 |
|---|---|---|
| 원본 Lby 동일조건 화면 | 사용자사진은 다른scene·팀색·카메라/압축, 현재fresh웹3phase 확보 | 동일 Lby·팀색·시점·상태·frame의 원본 HDR/최종 캡처 |
| 원본 GPU 픽셀/driver sampler·format quantization | byte·판독·CPU 실행은 확보, native GPU 미실행 | NVN sampler/texel readback와 각pass fixture |
| 전체 ColPaint/frame 연결 | native panel/vertex 근거 재사용, 현재collision overlay 경로 | visual geometry attributes/atlas→surface 동일프레임 |
| 전체 AS/cloth/SSS·film 포즈 | material 소비누락은 확인,전체pose/frame/GPU는별도 | 원본state/AS/cloth→draw packet 연쇄 |
| player 잠영/발밑 FX 전체 | SplPlayer/emitter/state 계약 추가 추적,새사진으로runtime bound를알수없음 | B7a0/holder·ELink/state·teamcolor/uniform 공급 |

현재 상태는 **확인된 결손과 구현 명세가 추가된 상태**다. 사진과 동일한 결과를 달성했거나 그래픽100%가 됐다고 표시하지 않는다.
