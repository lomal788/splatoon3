# 첨부 화면 대응 — 최종 HDR·색 보정과 LUT 저장 계약 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

사진의 잉크·캐릭터·총 색은 재질과 광원 계산 뒤에 **같은 최종색 처리**를 거친다. 현재 웹은 노출×2→Tone4→웹 선택 gamma1만 연결하고, 원본 LUT/Bloom/비네트 입력이 없다 [웹 판독]+[웹 실행]. 화면 채도를 재질별 임의 배율로 조정하면 같은 원본 경로를 재현할 수 없다. 사진은 정성 참고이며 동일 Lby 카메라/팀색/원본 프레임 비교는 아니다.

이번 새 원본 근거는 LUT texture initializer와 NVN builder 경계, 포맷 정보표의 해당 행이다. **8³ LUT는 RGB11/11/10 unsigned floating·4B/texel**이고 RGBA8을 임의 선택할 근거가 없다 [데이터]. 실제 저장 반올림·샘플러·GPU 픽셀은 미확정이다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, Lby_Lobby00. 원본은 extracted/exefs/main.reloc.img, shader는 analysis/gfx4/sharc/hdrcompose와 analysis/visual_gap_r2/light/cclut_final. 신규 함수 판독: analysis/decomp/reference_graphics_r3/post_texture.c, post_builder.c, post_sampler.c, post_sampler_builder.c. 실행 도구/결과: analysis/reference_graphics_r3/parent/post_texture_emu.py, texture_execution.json, post_sampler_emu.py, sampler_execution.json, post_evidence.json. 사진 비교 총괄은 [reference_graphics_gap](reference_graphics_gap.md).

SHARED/FUNCS/decomp_index.py --no-build로 35B1C84/3591474/35B1DC4가 미색인임을 확인하고 func_lookup→full_decomp로 새6함수를 판독했다. sampler 추가는 1034078/35B7160/3591834이며 각각 index/경계를 확인한 뒤 판독했다. 기존 35DAE6C/35DD5F4/1120EAC와 r2 packet/기존 shader는 재사용하며 새 실행 건수로 세지 않는다. 35B519C의 기존 paint 도구를 재사용하되 새 dimension2의 LUT3D 입력16건을 실행했다.

## 3. 진입점과 전체 호출 흐름

```text
RenderingDay.ColorGrading → native CPU packet [r2 재사용]
 → 35DAE6C allocator → 35B1C84 initializer
    → ROM swizzle/format table → 35B1DC4 max mip → 3591474 builder
    → NVN SetTarget/Width/Height/Depth/Levels/Format/Swizzle/Samples
 → color_correction_map bake → LUT [GPU 실행 미확정]
 → game HDRCompose: HDR·노출(+Bloom) → Tone4 → LUT → Vignette → Gamma
```

actual 웹 client/render/post.ts: configure→exposure2, render→HalfFloat HDR target→tone4→gammaMode1. 새 actual browser probe의 post.uniforms는 hdr/exposure/gammaMode 3개뿐이다. 원본 GPU pass 연결 검증이 아니다.

## 4. 구조체·필드·상수·열거형 표

기준 객체는 agl texture metadata T=35B1C84 인자0. ColorCorrection(CC) 본체와 같은 오프셋으로 해석하지 않는다.

| 위치/값 | writer→reader | 수준 |
|---|---|---|
| T+30/+32/+34 u16 | init/dimension helper→builder width/height/depth | [판독]+[실행], 로비8/8/8 |
| T+36 u16 | ROM4ABFC54[aglFmt]→builder SetFormat | [데이터]+[실행], agl1A→NVN numeric63(3F) |
| T+38 u8 | param9→SetSamples | [실행],0 |
| T+39 u8 | clamp requestedLevels/maxMip→SetLevels | [실행], 요청1이면1 |
| T+3A u16 | param2→SetTarget | [실행], 로비numeric2 |
| T+50..53 u8 | ROM4ABEF40+aglFmt×16→SetSwizzle | [데이터]+[실행],2/3/4/1 |
| T+A8 u16 / +AA u8 | aglFmt / 35B1DC4 maxMip | [실행],1A/4(N8) |
| ROM4ABF510+1A×14 | bit11/11/10/0,4B,3channel,float1,unsigned1,normalized0 | [데이터], 기존 표 스키마 재사용·이번 행 연결 |
| CC+1A14/+1A18 | allocator→HDR LUT coord | 기존 [판독]+[실행] 재사용,.875/.0625 |

포맷 표의 channel order는2/1/0/255, builder swizzle은2/3/4/1이며 서로 다른 표다. 두 값을 같은 enum이나 packed byte 순서로 합치지 않는다. NVN enum의 **기호 이름**을 확보했다는 주장도 하지 않는다.

## 5. 상태 전이와 전체 수명

metadata init의 param10 bit0이0이면 driver 호출 없이 생성하고,1이면 native builder를 거쳐 storage size/alignment를 요청한다. 이번 실행은 이 둘을 분리했다. 요청 mip1은 maxMip4가 가능하더라도1로 유지한다. 따라서 LUT를 mip4로 자동 생성해 샘플하는 변경은 원본 입력과 다르다.

native CC enable/dirty/thread와 CPU packet은 [ink_lighting_r2 §5](ink_lighting_r2.md) 재사용이다. LUT 전체 할당·업로드·재생성·프레임 교대·submit은 이번 실행에 포함하지 않았다.

## 6. 계산식·조건·상세 의사코드

### 6.1 로비 LUT 저장 입력 [데이터]+[실행]

```text
fmtNVN = u32(ROM4ABFC54 + aglFmt*4)
T.dimensions = u16(N,N,N)
T.format = u16(fmtNVN)           // agl1A→63
T.swizzle = low8(each ROM4ABEF40[aglFmt*16 + 0/4/8/12])
maxMip = dimension2 helper(N,N,N)
T.levels = max(1,min(requestedLevels,maxMip))  // 요청1→1
SetFormat(builder,T.format); SetLevels(builder,T.levels)
linearSize(type2,agl1A,N,N,N,1,mode0) = N^3*4
```

N8의 **선형 데이터 크기2048B**를 원본35B519C로 확인했다. 이것은 NVN tiled storage allocation size가 아니다. 해당 driver getter는 fixture 결과를 주입했으므로 실제 GPU memory size를2048B라고 단정하지 않는다.

### 6.2 TextureSampler 기본값과 driver 전달 [판독]+[실행-경계]

35B7160 constructor의 default manager5999230=null 조건에서 TSampler+D4..DB bytes는 `(1,1,2,7,7,7,1,1)`, LOD 범위는0..15, bias0, compareEnable0이다. native builder3591834의 인자0은 sampler config(TSampler+B8)다.

```text
SetMinMagFilter(builder, config.byte1D + 2*config.byte1E, config.byte1C)
SetWrapMode(builder, config.byte1F, config.byte20, config.byte21)
SetLodClamp(builder, config.float10, config.float14)
SetCompare(builder, config.u16_26 & 1, config.byte23)
```

기본 numeric min/mag=(5,1), wrap=(7,7,7)을 NVN sink에서 확인했다. 이름을 미확인한 numeric enum을 임의의 WebGL LINEAR/CLAMP 값으로 치환하지 않는다. constructor1건은 스텁0, builder12건은11API sink대체다. 실제CC draw의 bound sampler/lifetime와 다른 writer override는 실행하지 않았다. 추가로1034078은 texture metadata 복사·mip/layer 값과 dirty bit 소비·vt10 호출이며 **filter를 고르는 함수가 아니다**. 기존 §11의 이 주소에서 시작하자는 계획을 sampler filter 의미로 읽지 않는다.

### 6.3 최종색 순서 [기존 판독 재사용]

노출/Bloom→Tone4→3D LUT(.875*c+.0625)→비네트→감마. 로비 CPU 기본 CC 목록은 HSV Value1.0625→RGB8점 선형 보간→Gamma1이다. [ink_lighting_r2 §6](ink_lighting_r2.md)와 [stage_rendering §3](stage_rendering.md)를 따른다. gamma1 출력은 live flag 미확정인 웹 선택이다. 사진의 보라/노랑색을 Lby 팀색 상수로 대입하지 않는다.

### 6.4 역번역 검토 경계

새 surface 분석에서 bundled Ryujinx의 Negate 괄호 결함을 원시 Maxwell로 확인했다([reference_ink_surface](reference_ink_surface.md)). shader 파일이 생성됐다는 이유만으로 모든 식을 정확하다고 간주하지 않는다. 최종색의 기존 FMA/LUT 처리 순서는 재사용하되, GPU 포팅 전 raw/괄호 보완 출력으로 식 전체를 재검사해야 한다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

LUT는 화면 전체 upstream HDR의 소비자다. 바닥의 normal/반사, 캐릭터 cheapSSS/film, FX color0/1·alpha/VAT는 각각 다른 shader에서 HDR를 만든다. LUT 하나를 추가하는 것으로 누락된 표면/효과를 완성할 수 없다. 사람·오징어·탄·스플래시가 같은 후처리 계약을 사용해야 한다.

## 8. 다른 기능과의 상호작용

팀색의 Ink/InkBright 생산과 최종 ColorGrading.Value1.0625는 다른 계산 단계다. 재질색을 바꿔 LUT를 흉내내면 팀색 마스크·잠영·발사 효과가 서로 어긋난다. HDR 중간 결과는 톤매핑 전 clamp하지 않고, 원본 저장 포맷·노출·패스 순서를 유지해야 한다. 연산별 샘플러/정밀도는 남은 원본 계약이다.

## 9. 웹 포팅 구조와 구현 순서

1. post.ts에 native CPU CC packet→8³ LUT 생산과 bind 소비 계약을 연결한다. 게임 core 원본식과 렌더 정책을 구분한다.
2. RGB11/11/10 unsigned floating의 저장/양자화 계약을 확보한다. 현재 웹 HalfFloat HDR RT와 LUT 포맷을 같은 것으로 처리하지 않는다.
3. SetLevels1과 샘플러 filter/addressing을 확인한 후 texel-center 좌표 및 Tone4 뒤 소비 순서를 구현한다.
4. native Bloom/비네트 활성·gamma live flag는 미확정 상태로 추적한다. 스크린샷 색상을 맞추기 위한 임의 조명 배율로 대신하지 않는다.
5. 같은 Lby 원본/웹 camera·팀색·도색 mask·frame 상태의 캡처로 차이를 검증한다.

이번은 분석만이며 source/impl/포트 상태는 변경하지 않는다. 구현 지시 요약은 [port/reference_graphics](../port/reference_graphics.md).

## 10. 검증 코드·실행 결과·기대값

| 실제 명령 | 결과·경계 |
|---|---|
| decomp_index.py --no-build→func_lookup.py→full_decomp.sh post_texture/post_builder | 신규3함수 판독. readOnly Ghidra |
| post_texture_emu.py | 56/56 metadata exact PASS. 28driver-off 스텁0 + 28driver-on 원본builder/14개API sink대체. dimension2·fmt1A/2B·N1..65535 입력, 생략 경로는 문서대로 |
| 같은 도구 type2 linear size | 신규16/16 exact PASS. 원본35B519C·N1/2/3/4/7/8/9/16×2format, driver 스텁0 |
| post_sampler_emu.py | constructor1 기본값 exact·builder12/12 sink계약 PASS, default manager nullfixture/11NVNAPI 대체. liveCC sampler/GPU 미실행 |
| xref/disasm nvnTextureBuilderSetFormat | loader83FC6C..80→global57D5830→native builder 확인 |
| node analysis/reference_graphics_r3/parent/browser_probe.mjs | actual 웹 Lby 3phase 캡처·page/console/HTTP 오류0. Edge headless SwiftShader, world.step 제어·ownInk stamp fixture. 원본 GPU 아님 |

56건을 도구 확장 뒤 재실행한 것을112건 신규 성과로 세지 않는다. 최종 고유 입력은 metadata56 + linear16이다. size/alignment API 반환은 합성값이며 float 저장/샘플러/원본 shader/GPU 비트 일치를 실행한 것은 아니다. 명령·실패는 analysis/reference_graphics_r3/parent/commands.md에 기록했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 질문 | 이번 시도·남은 이유 | 다음에 볼 곳 |
|---|---|---|
| NVN format63 symbolic 이름/float packing·rounding | table bit폭/float/unsigned·native SetFormat값·3D선형 크기 확정, driver 저장은 실행하지 않음 | native NVN format 정의·readback texel의11/11/10 layout 및 반올림 |
| filtering/addressing | color_correction sampler3D와 center coefficient 확인, numeric min/mag5/1·wrap7/7/7·LOD0..15 기본값과 builder reader 확보, live override/bind 및 enum 의미 미확정 | 3591834의 runtime 인자producer·CC draw sampler bind/수명·NVN enum 의미 |
| native GPU LUT 실제 RGB | CPU packet과 shader가 있어도 texel write/readback 미실행 | color_correction_map + actual N8³ target original GPU readback |
| 실제 로비 최종 픽셀 동일성 | 사진은 다른 stage/색/카메라, 현재 웹3phase는 fixture | 동일 Lby·시점·팀색·mask·frame의 원본/웹 HDR와 최종 framebuffer 비교 |
| gamma·bloom·비네트 live 값 | 기존 flags 판독 재사용, live runtime 미수집 | stage_rendering §11의 flags writer 및 pass state |

넓은 LUT/전체 그래픽 inventory 항목을 이 부분 실행으로 확정 승격하지 않는다.
