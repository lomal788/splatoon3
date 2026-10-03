# 캐릭터·무기 Maya TexSrt 회전 0 변환 — r9 원본 실행

2026-10-03 · Splatoon 3 v0 Lby_Lobby00. 실제 텍스처 좌표에 영향을 주는 원본 CPU converter를 확인했다. 이번 실행 범위는 Maya·회전0의 여섯 출력 float이며, 원본 Mat UBO 전체 upload·다른 회전/모드·최종 GPU 픽셀과 구분한다.

## 1. 기능 개요와 사용자에게 보이는 동작

**[실행]+[데이터]** 탱크 M_Body `tex_mtx1`의 translationY−.6, 병 M_Bottle `tex_mtx0`의 scaleY2, 오징어 눈의 실제 회전0 SRT 곡선을 원본 Maya converter로 변환하면 기존 identity UV와 달라진다. 병은 단순히 V를2배로 만드는 대신 `V'=2*V−1`이 되고, 탱크는 `V'=V−.6000000238…`가 된다.

**[실행]** 원본 callback 설치→TexSrt dispatcher→Maya 함수 전체를 실제 SDK 상수·삼각함수 표에 연결해313건 실행했다. 웹 helper의 여섯 f32 출력 비트가 모든 원본 출력과 일치했다. 수학·삼각함수 함수 스텁과 PLT 스텁은 없다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치·근거 |
|---|---|
| main ARM | `extracted/exefs/main.reloc.img`, 원본 SHA256은 [fixture](../../games/splatoon3/tests/fixtures/material_texsrt_r9_native.json) |
| 실제 SDK data | `extracted/exefs/sdk.img`, 동적 symbol로 정확히 연결, SHA256도 fixture에 저장 |
| 신규 converter C | [texsrt_writer.c](../../../analysis/decomp/port_graphics_r9/material_anim/texsrt_writer.c) |
| 실제 raw 채널·static 값 | [character_material_animation_r9](character_material_animation_r9.md), [actual_variants.json](../../../analysis/port_graphics_r9/variants/actual_variants.json) |
| 원본 실행 도구 | [material_texsrt_r9_emu.py](../../tools/material_texsrt_r9_emu.py), [texsrt_native_summary.json](../../../analysis/port_graphics_r9/material_anim/texsrt_native_summary.json) |
| 웹 식·검증 | [material_texsrt.ts](../../games/splatoon3/client/render/anim/material_texsrt.ts), [material_texsrt.test.mjs](../../games/splatoon3/tests/material_texsrt.test.mjs) |
| 명령·실패 | [commands.md](../../../analysis/port_graphics_r9/material_anim/commands.md) |

SHARED/FUNCS/decomp_index의 TexSrt·ModeMaya·표 주소를 먼저 확인했다. 기존 FX r7 하네스의 SDK numeric import 바인딩을 재사용했고, FX transform 실행 건수를 이번 결과에 더하지 않았다. 폰트 ShaderParam 후보084c78c는 이미 범위 밖으로 제외되어 있었으므로 재디컴파일하지 않았다.

## 3. 진입점과 전체 호출 흐름

**[판독]+[실행]**

```text
088f308(resShaderAssign)
  param_count=+4a, parameter_table=+20, stride24
  type=entry+12 ≥28 && callback(entry+0)==0
  callback = table5440748[type−28]
  TexSrt type30 → 088efb0
088efb0(out,rawTexSrt)
  mode=raw+0 → table5440738[mode]
  Maya0 → 088f3d0
  Max1 → 088f4c0
  Softimage2 → 088ecb8
088f3d0
  rotation→SDK angle-index/table
  scale/translation→원본 f32 연산→out[0..5]
  return24
웹: nativeTexSrtRowsZeroRotation(raw)→6float
  → caller가 Hoian의 shader 소비 6lane에 연결
```

일부 오래된 `func_lookup` 범위 메타데이터는088efb0/088f3d0를 이전 함수088ec74/088f364에 붙였다. 원본 callback table과 직접 branch entry가 각각088efb0/088f3d0인 것을 확인한 뒤 `full_decomp.sh`로 그 entry에 C를 생성했다. 잘못된 앞 함수 시작 주소를 converter로 기록하지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체·필드 | 타입·의미 | writer → reader |
|---|---|---|
| raw TexSrt+0 | u32 mode, Maya0/Max1/Softimage2 | FRES static/FMAA raw patch → dispatcher088efb0 |
| +4/+8 | f32 scaleX/Y | 원본 static/FMAA → Maya088f3d0 |
| +c | f32 rotation | 같은 writer → SDK angle index |
| +10/+14 | f32 translationX/Y | 같은 writer → 원본 translate 계산 |
| shader parameter entry+0 | callback ptr | 088f308 null인 경우 설치 → material converter caller |
| entry+12 | u8 typed enum | FRES type30 TexSrt → 설치 table index2 |
| 5440748/50/58/60 | callback table | Srt2D/3D/TexSrt/Ex 자리; TexSrt→088efb0, Ex자리는 이번 이미지0 |
| 5440738/40/48 | mode table | Maya→088f3d0, Max→088f4c0, Softimage→088ecb8 |
| out0..14 | f32[6], 24B | Maya writes → shader의 선형4·이동2 값 |
| out18..1f | 이번 하네스 sentinel8B | 원본 writer는 쓰지 않음. 원본 upload padding 값은 미확정 |

**[데이터]** 실제 SDK dynamic symbols: `FloatPi` GOT5778fd0, `AngleIndexHalfRound` GOT5779150, `SinCosSampleTable` GOT5779158. table 첫 항목은 `(cos=1,sin=0,deltaCos=−.00026354214060120285,deltaSin=.024542152881622314)`다. 표를 `Math.sin/cos`로 다시 만들지 않았다.

## 5. 상태 전이와 전체 수명

static SRT는 해당 모델의 FRES 재질을 생성할 때 제공한다. live SRT는 raw FMAA curve 평가 이후 원래 typed field byte offset에 적용하고, 그 결과를 converter에 넣는다. 원본 모드가 Maya이고 원본 f32 rotation이0일 때만 이번 helper가 값6개를 돌려준다. 그 외는 null이다.

**[미확정]** 원본 전체 dirty buffer 갱신→Mat upload 수명은 이번 하네스에 포함하지 않았다. 신규 helper가 raw field를 읽고 여섯 값만 반환하는 이유다. type11 material multi-leaf blend·몸 CP·실제 피부 index는 이 converter 발견으로 해결되지 않는다. native typed callback 설치만으로 모든 재질 동작을 완료라고 바꾸지 않는다.

## 6. 계산식·조건·상세 의사코드

**[실행]+[판독]** `F=f32`, 회전0의 원본 표 값 `c=1,s=0`이다. 실제 명령 순서를 유지한다.

```text
sx=F(scaleX), sy=F(scaleY), tx=F(translateX), ty=F(translateY)
r0=F(sx*c)
r1=F(F(−sy)*s)
r2=F(sx*s)
r3=F(c*sy)
q=F(F(s*.5)−.5)
d=F(c*(−.5))
r4=F(sx*F(F(d−q)−tx))
r5=F(F(sy*F(F(d+q)+ty))+1)
return [r0,r1,r2,r3,r4,r5]
```

식을 단순화하지 않고 부호를 가진0을 보존한다. 양의 sy에서 r1은−0이며, 음의 sx에서 r2도−0이다. FMA로 합치지 않고 FMUL/FADD/FSUB의 각 결과를 f32로 반올림한다. shader에서 읽는 UV 식은 기존 [shader_uv_selection](shader_uv_selection.md)의 `U'=U*r0+V*r2+r4`, `V'=U*r1+V*r3+r5`이다. 여섯 값 뒤에 웹 carrier용0 두 개를 붙이는 것은 미사용 lane을 위한 웹 저장 방식이며, 원본 padding write를 확정한 것이 아니다.

일반 nonzero rotation에서는 SDK table 보간이 수행되는 것을 판독했지만 이번 웹 API는 그 결과를 만들지 않는다. 입력이 유한한 f32인지 확인하고, 다른 mode나 회전이 있으면 null을 돌려준다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

**[데이터]** 실제 Tank/Bottle 입력은 variants 에이전트가 기록한 현재 원본 대응 FRES metadata를 그대로 읽고 파일 SHA256을 fixture에 저장했다. Tank는 `tex_mtx1`→선택UV2/attrib `_u2=_u0`를, Bottle은 `tex_mtx0`→UV0를 쓴다. sampler·선택 프로그램 근거는 [character_variants_r9](character_variants_r9.md)에 있다.

오징어 `Sqd_Surprise`는 실제 FMAA Cubic의 scale/translation 값을 사용한다. 회전0은 원본 상수다. 이전의 원본 curve fixture 출력에서 분수 시간의 실제 네 채널 값을 읽어 이번 native converter에 입력했다. 정수 frame bake·잠영 상태가 이 값을 대신하지 않는다.

이번 개선은 재질의 UV와 그에 따른 패턴·광택/자원 텍스처 위치에 영향을 준다. 새 이펙트·효과음·카메라 공급을 만들거나, 최종 색/빛 계산까지 전부 완료한 것으로 표현하지 않는다.

## 8. 다른 기능과의 상호작용

새 converter는 raw SRT와 curve 평가를 분리한다. 부모 runtime은 actual model target에서 `patchTexSrt(base,offsets)`를 먼저 적용한 뒤 converter를 호출할 수 있다. 기존 Hoian shader가 읽는 `row0.xyzw/row1.xy`를 갱신하며, PBR normal/roughness/기타 텍스처의 UV 소비는 variants 담당의 별도 검증 범위다.

몸 잉크 `B+cb8`와 피부색 index의 생성자는 바뀌지 않는다. native Mat UV 공급이 확보되어도 이 두 입력을 즉시 swimming 값이나 skin0으로 채우지 않는다. multi-leaf material mixing이 unsupported인 구간은 UV converter를 찾았다는 이유로 지원 처리하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

API는 `nativeTexSrtRowsZeroRotation(raw:NativeTexSrt):number[]|null`이다. 타입은 [material_channels.ts](../../games/splatoon3/client/render/anim/material_channels.ts)의 `{Mode,Scaling:{X,Y},Rotation,Translation:{X,Y}}`를 사용한다.

1. static FRES raw SRT 또는 actual type11 curve patch의 raw SRT를 확보한다.
2. helper가 null이면 기존 경계 진단을 유지한다.
3. 값6개면 선택 UV의 Hoian Mat carrier 선형4·이동2에 전달한다.
4. 미사용2lane은 웹 carrier0으로 기록하고 원본 upload padding과 구분한다.
5. 실제 sampler가 같은 선택 UV를 읽는지 별도로 검증한다.

이번 담당은 helper·fixture·MD만 소유한다. Hoian static matrix 적용은 variants 에이전트, actual model/type11 live 적용·전체 테스트·브라우저는 부모 통합 소유다.

**2026-10-03 웹 통합 확인:** 실제 `hoian.ts`가 static raw SRT에 이 helper를 사용하고, `setHoianMaterialTexSrt(material,name,raw)`가 live 여섯 lane을 공급한다. 실제 `player.ts`는 `patchTexSrt` 이후 이 setter를 호출한다. 선택 Tank/Bottle static UV와 실제 loaded squid frame3 live UV가 연결되었다. type11 단일 full-weight 경계는 유지한다.

## 10. 검증 코드·실행 결과·기대값

| 검증 | 결과·정확한 범위 |
|---|---|
| `full_decomp.sh … texsrt_writer.c 088f308 088efb0 088f3d0` | 신규3entry C 생성. decomp completion/INDEX 갱신 확인 |
| `material_texsrt_r9_emu.py` | 원본313case, return24B, 뒤8B 쓰기 없음, 함수/수학/삼각함수/PLT 스텁0 |
| `material_texsrt.test.mjs` | **2/2 PASS**, 출력6float313건 모두 비트 일치, nonzero/Max/nonfinite 입력은 null |
| 채널·binding·converter 세 테스트 파일 | **10/10 PASS**. whole game/GPU 픽셀 검증 아님 |
| variants 실제 Hoian UV shader 검증 | 선택UV96입력 **maxAbs0**, GL0. [gpu_verification.json](../../../analysis/port_graphics_r9/variants/gpu_verification.json). native NVN 실행이 아닌 원본 판독 GLSL/웹GLSL 대조이며, 전체448 중 UV96을 구분 |
| 부모 actual Lby 연결 | 12phase/87display trace, 단일full-weight `Sqd_Wait` 실제 적용. loaded squid에 제어된 `Sqd_Surprise` frame3을 적용해 matrix verified=true/rawSrtUnbound=false, 세 패턴 공급/GL0 확인. 자연스러운 Surprise trigger·가중혼합은 제외 |

313건은 실제 static/원본 분수 Sqd_Surprise 채널 입력56건과 합성 유한·signed-zero257건이다. generic curve1,212·initialized skin67은 다른 시험이며, 겹치는 기존 FX r7 실행을 합산하지 않았다.

하네스는 실제 `sdk.img`를 별도주소에 mapping하고, main의 undefined numeric imports를 정확한 SDK symbol 값에 연결한다. SDK symbol binding 자체는 original data 공급이며, 삼각함수 호출을 상수로 반환하는 스텁이 아니다. 모델·dirty-buffer 업로드·GPU는 실행하지 않았다.

**부모 추가 연결 검증(2026-10-03):** 앞313건에 없는 controlled frame3을 원본 curve7개→별도 공급한 raw SRT→원본 callback1회로 실행해 실제 웹 UV6lane과 일치를 확인했다. [controlled_surprise_native.json](../../../analysis/port_graphics_r9/controlled_surprise_native.json). SDK 원자료와 PLT/수학 스텁0을 유지했으며 정상 상태 trigger·전체 typed material apply/upload·GPU는 제외했다. JSON에 기록한 signed zero는 정규화되므로 CPU 비트 검사는 앞313 fixture와 구분한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 남은 이유·다음 근거 |
|---|---|
| nonzero rotation/Max/Softimage | native mode table과 함수 entry를 판독했지만 이번 API/fixture는 Maya0만. 다음088f4c0/088ecb8 및 원본 angle-table 보간/경계 실행 |
| Mat 전체 upload·미사용2lane | 원본 converter의24B 출력과 shader6lane 소비만 확인. 다음 material dirty upload caller 및 실제 Mat UBO capture |
| ShaderParam type31 TexSrtEx | 실제 callback table 자리가0이며 이번 선택 재질은TexSrt30. 다른 path callback 설치와 extended field writer 추가 필요 |
| full type11 material mixing | raw curve→동일SRT 변환은 실행되나 multi-leaf 가중typed 혼합식은 미확정 |
| 몸 CP/현재 skin index | 원본별도 producer를 이번 UV 변환에 섞지 않음. [material animation §11](character_material_animation_r9.md#11-미확정-사항과-추가-분석에-필요한-근거) 추적 필요 |

2026-10-03 정정: 앞선 r9 기록의 “Maya SRT producer 미확정” 중 **Maya·회전0·출력6lane** 범위를 이번 원본 실행으로 확정했다. 나머지 회전/모드/전체 GPU upload는 미확정으로 남는다.
