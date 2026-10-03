# 잉크·캐릭터 최종색 — ColorCorrection 공급·LUT bake 추가 분석

기준: Splatoon 3 v0, Lby_Lobby00 1인 연습. 날짜 2026-10-03. 이번 문서는 **새 CPU 연쇄 실행·원본 셰이더 분기 복원**만 추가한다. 주광10·베이크·기존 HDR/Tone4·Hermit2D reader 결과는 재사용한다. GPU 최종 픽셀/실기 캡처를 확인한 문서가 아니다.

## 1. 기능과 체감 동작

바닥 잉크·인간/오징어·총/탄의 HDR 색은 기존 후처리 순서를 거친다. 이번에 남은 색 보정의 공급을 좁혔다. 생성자 기본 순서(mode0)의 실제 로비 입력은 **HSV(밝기 Value1.0625) → 표본 RGB 곡선 → Gamma 연산**이다 [판독]+[실행-CPU]. 밝기1.0625를 곡선 뒤에 곱하거나, 원본 Hermit2D를 최종 픽셀마다 직접 계산하면 이 경로와 다르다.

원본 `color_correction_map`의 기존 분석 CLI 출력은 switch 분기표를 0으로 읽어 종류1~9와 HSV 일부 sector를 빠뜨렸다. **315행→1694행**으로 복원했다 [판독-도구]. 기존 문서의 곡선 reader 결론을 뒤집은 것은 아니며, 전체 GPU LUT 미확정에 필요한 다음 근거를 확보한 것이다.

## 2. 원본 버전과 자료 위치

- 원본 CPU: `extracted/exefs/main.reloc.img`의 `35DB354`, `115567C`, `35DC218`, `35DAE6C`, `35DD5F4` 등. original/는 읽기 전용으로 유지했다.
- 원본 shader 추출본: `analysis/r6_gfx_char/agl_resource/agl_technique_pfx.sharcb`, SHA256 `8e79a6adbdcdeb71109e28291a28fdd5c3d25f0a4f0f2f95cd48c00ec317d9e6`.
- `color_correction_map`: binary40(vertex)/41(pixel); `color_correction`:42/43. 두 프로그램 모두 macro 없는 단일 변형 [데이터].
- 원본 RenderingDay: `analysis/gfx4/scene_LobbyVersus/Gyml/LobbyVersusLockerTest.game__gfx__parameter__RenderingDay.bgyml.json`.
- 새 근거: `analysis/visual_gap_r2/light/{cpu_packet.json,shader_evidence.json,cclut_*.c,cclut_map_cb1/,cclut_final/,dumpfix/}`.

SHARED/FUNCS 및 `decomp_index.py --no-build`로 중복 확인했다. 기존 `35DC218`/`115567C`/Hermit2D는 다시 디컴파일하지 않았다. 새 setup/update/allocator/submit/caller 함수만 `func_lookup.py`→`full_decomp.sh`로 판독했다.

## 3. 진입점과 호출 흐름

| 단계 | 원본 경로 | 이번 근거 |
|---|---|---|
| 기본 연산 목록 | `35D9450` 생성자→`35DB354(mode0)`→`35DB574` 파라미터 칸 배정 | 새 디컴파일·native init 실행 |
| 게임 로비 공급 | `2B5FE88` 기존 흐름→`115567C`, env+2AD8의 ColorCorrection에 Hue/Saturate/Value 및 RGB Data 기록 | 기존 writer 재사용·native apply 실행 |
| CPU bake UBO | `35DC218`: enable/dirty/thread gate→12개 순서칸→header/param/count 패킹 | 진입부터 패킹 끝까지 원본 실행 |
| 3D LUT 할당 | `3743610`→`35DAE6C`, 또는 별도 `3669908`→동일 allocator | N³/형식 enum/좌표 계수 새 판독 |
| GPU bake | `color_correction_map`41: 픽셀 XY와 slice Z 생성→연산 순서 적용→MRT8 출력 | 분기 복원 shader 판독, GPU 미실행 |
| LUT 소비 | `35DD5F4`의 `RenderParam`·`color_correction`43; 게임 HDRCompose의 sampler3D 소비는 기존 근거 | 좌표 공급 새 판독·game route 전체 미확정 유지 |

`35DE4A8`의 mode0/1/2 변경 요청은 UI/파라미터 갱신 경로에 있다. 이번 실행은 생성자 기본 mode0이다. 실제 런타임 외부 변경/전체 reload를 실행한 것은 아니다.

## 4. 구조체·필드·상수·열거형

| 위치 | 의미/값 | 수준 |
|---|---|---|
| CC+258+i×20 (12개) | 연산 객체 번호 또는 −1 | [판독]+[실행] |
| CC+3C0+j×78+48/+68 | kind / 데이터 칸 번호 | [판독]+[실행] |
| CC+960+slot×28+18 | 단순 연산 vec4 | [판독]+[실행] |
| CC+FA0+curveSlot×280 | RGB/A 곡선 래퍼 | 기존 판독+새 연쇄 실행 |
| CC+218 / +2410 | enable / dirty 등 bit; pack 후 bit1 제거 | [판독]+[실행-부분] |
| UBO Context byte0..BF | 12×16B header `(kind,paramBase,0,0)` | [판독]+[실행] |
| byteC0..33F /340 | 최대40vec4 param / active step count | [판독]+[실행] |
| 실제 기본 로비 header | `(0,0,0,0)`, `(6,1,0,0)`, `(1,10,0,0)`; count3 | [실행-CPU] |
| param0 | `(Hue0,Saturate1,Value1.0625,0)` | [데이터]+[실행] |
| param1..8 /9 | RGB 8점 표본 / 마지막 표본 복사 | [실행] |
| param10 | Gamma `(1,1,1,1)` | [실행-기본모드] |
| Hue/Saturate 기본값 | visitor1192868→ROM4A98B88/8C:0/1 | [판독]+[데이터] |
| allocator 입력 | +8=buffer count,+C=format enum,+10=N | [판독] |
| LUT 형식 | caller3743610·3669908 공급 enum`0x1A`; 실제 NVN 포맷명/저장 반올림은 아래 미확정 | [판독-숫자] |
| CC+1A14/+1A18 | `1−1/N`, `.5/N`; N8→`.875,.0625` | [판독]+[실행-명령블록] |

형식 enum`0x1A`를 근거 없이 RGBA8/float라고 바꾸지 않는다. shader reflection의 Context848B와 CPU 실제 upload`0x344`(836B)는 다르다. header192B+param640B+count4B가 836B이고, 반올림된 declared block 크기와 구별한다.

## 5. 상태 전이와 수명

생성자는 mode0을 설치한다. mode0의 12순서칸 가운데 처음3칸만 객체0/1/2이고 나머지는−1; 객체 kind는0/6/1이다. `35DB574`는 단순 param 슬롯과 곡선 슬롯을 배정하고 기본 Gamma를1로 채운다. `115567C`가 Hue/Saturate/Value와 RGB 곡선을 쓰고 dirty bit1을 켠다. 패킹은 CC enable이고 dirty bit1/2가 있을 때 진행하며, 패킹 시작 시 bit1을 지운다.

`35DC0C4`는 기본값과의 차이를 객체 flag+71에 기록한다. 그러나 실제 `35DC218` 패킹은 기본 Gamma1도 헤더에 포함했다. **Gamma1을 identity라고 보고 목록에서 제거하는 것은 원본 packet과 다르다.** 완전한 GPU 리소스 교대/전체 장면 lifecycle은 실행하지 않았다.

## 6. 계산식과 상세 조건

### 6.1 shader 분기표 복원

기존 `web/tools/shader_dump/Program.cs`의 `Acc`는 번역 중 `IGpuAccessor.ConstantBuffer1Read`를 구현하지 않았다. 기본 반환0으로 Ryujinx `Decoder.FindBrxTargets`가 간접분기 target을 읽는다. GLSL 출력 이후 정적 상수를 치환하는 코드는 이 decoder 단계의 누락을 복원하지 못한다.

보완은 **번역 전에 원본 ControlShader.GetConstants(byteCode)를 Acc에 전달**하고 `ConstantBuffer1Read(offset)`가 실제 uint32를 읽도록 했다. 분석 전용 복사본 dumpfix와 이후 보완된 표준 CLI의 map pixel 출력은 SHA256 동일이다. target table byte24의 kind1..10 포인터는 `[550,640,6B8,740,7D0,840,A00,12C0,1AB0,1C90]`다. 이는 shader 내 상대 분기 값이며 CPU 주소가 아니다.

### 6.2 기본 로비 활성 3연산

kind0은 RGB→HSV 변환 후 `Hue+=param.x/360`, `S*=param.y`, `V*=param.z`를 적용하고 RGB로 돌린다. 원본은 min/max 기반 조건과 `delta<1e−5` gate를 쓰며, hue에는 `fract(fma(HueOffset,1/360,h)+1000)`이 있다. +1000의 f32 반올림과 원본 tie/sector 선택을 생략하지 않는다. 로비 Hue0/S1/V1.0625라도 HSV 왕복을 단순 RGB곱과 GPU 비트 동일이라고 주장할 수 없다.

kind6은 **8개 Hermit2D 출력 표본을 선형 보간**한다. 채널별:

```text
q=clamp(c,0,1)*7
j=floor(q); w=q-floor(q)
out=fma(sample[j+1]-sample[j],w,sample[j])
```

paramBase=1, RGB는 각각 독립 표본 채널이다. CPU가 sample8=sample7을 복사하므로 q=7일 때 j+1을 읽어도 마지막값을 유지한다. GPU가 매 픽셀에서 Hermit2D 원식을 재평가하는 경로가 아니다. CPU sample 표는 기존 stage_rendering§2.2.1을 재사용한다.

kind1은 `exp2(log2(abs(c))/(gammaChannel*gammaCommon))`를 사용한다. 기본 param10은 전부1이다. `pow(c,1)`이나 대입으로 교체한 결과를 원본 GPU 비트일치라고 부르지 않는다. 이 연산과 HDRCompose의 이후 출력 감마 variant는 별개다.

### 6.3 3D LUT 격자와 texel-center 좌표

allocator는 texture initializer35B1C84에 dimension2 및 N/N/N, format enum0x1A를 공급한다. slice8개를 MRT8개로 그리고, N이8일 때 LUT 입력은 `(pixelX−.5)/7,(pixelY−.5)/7,(baseSlice+i)/7`이다. `RenderParam`은 `(N,1/(N−1))`; fragment slice loop는8번이다 [판독].

소비 좌표는 각 RGB에 `fma(c,scale,bias)`, scale=`1−1/N`, bias=`.5/N`. N8은 **`.875*c+.0625`**다. `35DAE6C`+1A14/+1A18의 실제 writer와 `35DD5F4`의 RenderParam 복사를 확인했다. 삼선형 filtering/addressing/실제 NVN 포맷 변환의 최종 숫자는 GPU 제출·sampler 생성이 남아 있다.

## 7. 이펙트·캐릭터·광원 연결

이 후처리는 광원 계산 뒤의 최종색 경로다. 발사 emitter의 vertex C0/C1·alpha, 바닥 잉크 normal/층12 reflection, 몸/오징어 _Thc·SSS·숨김은 각각 upstream이며 이 문서로 확정하지 않는다. 주광·SH·베이크·FX 조명을 빠뜨린 채 후처리만 맞추면 최종 장면이 같아지지 않는다.

원본 큐브/SH는 실행 중 캡처가 입력이다. 이번에는 캡처 큐브나 fixed SH를 새로 만들지 않았고, 최종 native cubemap 내용은 여전히 미확정이다.

## 8. 다른 기능과 상호작용

Value1.0625는 InkColorCorrection의 팀별 Ink/InkBright 생산과 다른 위치다. 팀색을 바꿔서 최종색 보정을 흉내내면 인간·무기·바닥·발사효과가 같은 후처리 계약을 공유하지 못한다. HDRCompose의 노출×2/Tone4→LUT→비네트→감마 기존 순서를 유지한다. 정확한 runtime gamma 선택 bit의 미확정도 유지한다.

## 9. 웹 반영 필요와 구현 순서

1. GR07의 색 보정 LUT 입력을 native UBO 계약과 맞춘다: HSV Value1.0625 **먼저**, RGB8점 보간 **다음**, native Gamma step **그다음**. 기존 Hermit2D 원본 sample값을 재사용한다.
2. 실제 N8³ 격자와 sampler3D texel-center `.875*c+.0625`를 맞춘다. 픽셀마다 매끄러운 Hermite를 계산하는 것은 근사다.
3. GPU 포맷/삼선형·경계 clamp/driver sampler 설정을 닫은 뒤 quantization을 반영한다. enum0x1A 이름을 추측하여 코드에 넣지 않는다.
4. 이 작업은 조명 전반 GR05·FX 색조합·paint재질의 전체 반영을 대체하지 않는다.

웹 코드/impl/포트 상태표를 이 담당 작업에서는 변경하지 않았다. 넓은 `LUT 최종색` 질문은 **조사중 유지**한다.

## 10. 실제 명령과 검증 결과

| 명령/행동 | 결과 | 실행 경계 |
|---|---|---|
| `decomp_index.py --no-build`/`func_lookup.py` | 기존 함수 재사용·새 함수 경계 확인 | 분석 중복 방지 |
| `sh web/tools/full_decomp.sh …` 최초 | PowerShell sh 미인식 exit1 | 저장 실패; 분석 근거 없음 |
| `C:/Program Files/Git/bin/sh.exe web/tools/full_decomp.sh …` | 새3+2+1+1+2 함수 판독 exit0 | 원본Ghidra readOnly |
| 기존 shader_dump `prog-sharc … color_correction_map …` | exit0지만315행·분기누락 | whole shader 근거에서 제외 |
| 분석 복사CLI CB1 공급 보완 build | warning0/error0; 재덤프1694행 | native shader 판독, GPU 미실행 |
| 보완 표준CLI map 재덤프(parent 검증) | pixel byte/hash 동일; build warningMSB3539 1/error0 | web/tools 보완 한정 |
| `.venv/Scripts/python.exe -B analysis/visual_gap_r2/light/cclut_packet.py` | 로비 native packet1건·RGB24값 일치; 합성128/128 **192B 계약 비트일치** | init+apply+pack; ABI getter/ThreadID2개 공급; viewport/GPU 전 `35DCA00` 중단 |
| 같은 도구 allocator math block | 128/128 bitmatch; N8=`3f600000/3d800000` | `35DB0F0..35DB110`, 스텁0; 전체allocator 실행 아님 |
| 초기 CPU 대조 출력 | `curve_bits_match=false` | RGB 외 A의 type0 reader와 단순i/7까지 잘못 비교한 보고 범위 오류; RGB만 분리해 true, A는 후속128대조에서 제외 |
| 자료 검색 | nonexistent analysis/extracted/Shader 등 경로/광범위rg ACL 오류 | 실패 보존, 확인된 existing extract 사용 |

CPU 128건은 Hue/Sat/Value 범위, RGB Hermit2D tangent 합성 입력으로 헤더·HSV·24 RGB표본+끝값복사·Gamma·count를 대조한다. A 표본은 native pack에 존재하지만 독립 원식 대조에서 제외했다. unused header/stack padding도 비트 일치 범위에 넣지 않았다. 표본 reader만 재실행한 기존2127건을 신규건수로 세지 않는다. 테스트나 build를 웹 동등성 검증으로 재사용하지 않는다.

## 11. 미확정과 다음에 볼 곳

| 항목 | 시도/남은 한계 | 다음 근거 |
|---|---|---|
| actual LUT GPU texel RGB | CPU 공급 및 완전 분기 shader 확보; GPU execution/readback 없음 | shader41을 실제 input UBO와 NVN render/MRT에 실행·readback |
| format enum0x1A의 실제 저장 포맷/반올림 | 3743610·3669908 supply→35DAE6C→35B1C84까지 숫자 확정 | 35B1C84 내부 agl→NVN enum mapping 및 texture init |
| 실제 sampler filtering/addressing | shader43/HDRCompose의 sampler3D와 center coefficient 소비 확인 | CC sampler object·NVN sampler writer/submit slots |
| live 전체 order/reload | constructor mode0 및 supplied parameter chain 실행; mode 변경UI 존재 | 35DE4A8/35DF17C의 serialize/reload·실제 scene input |
| game HDRCompose 전체 CC coeff producer | standalone35DD5F4는 reader 확인; game callback112C604는 기존 흐름 | 1120EAC/112215C의 실제 CC texture/coeff 전송 전체 |
| runtime 출력gamma·native environment capture | 이번 shader·CPU 분석으로 입력 장면을 얻지 못함 | 기존 stage_rendering§11의 output bit writer/capture renderer |

[추정] 값으로 미확정을 채우지 않았다. 분모/질문 개수는 바꾸지 않으며, 이 부분 실행·판독으로 렌더링 전체 확정률을 승격하지 않는다.

### 2026-10-03 LUT 저장·샘플러 후속 근거

[reference_hdr_output](reference_hdr_output.md)에서 agl1A의RGB11/11/10 unsigned floating·4B/texel와NVNnumeric63,level1,metadata56/linear3D16/samplerconstructor1+builder12를 추가했다. 이전§11의포맷비트폭미확정은해당범위에서정정하며실제GPU저장반올림·샘플러live binding은유지한다. 1034078은filter선택자가아닌texture metadata/mip/layer복사다.
