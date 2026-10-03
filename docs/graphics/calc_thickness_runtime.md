# 캐릭터 calc_color와 두께 맵 소비 — r8

## 1. 결론

[판독]+[데이터] calc source1은 **계산된 거칠기 scalar**, source4는 **투과 backlight RGB**이다. replace7은 **필름 아래 색**이다. `_Thc`는 원본 몸/얼굴에서 R을 읽어 `1−R`로 투과/산란·필름 투과 항에 곱하는 마스크다. 텍스처 이름만으로 물리적 길이를 뜻한다고 해석하지 않는다.

## 2. 원본과 도구

Hoian_UBER.Product.bfsha 원본과 keys5611행, BFRES 원본 덤프 samples.json.gz, 프로그램1279/227/295/1115/5549를 새로 역번역한 `analysis/completion/r8/graphics_calc_pN.{frag,vert,options.txt}`. 도구는 기존 shader_dump.dll(Maxwell 원본 코드→Ryujinx GLSL)이다. CPU 함수를 unicorn으로 실행한 결과가 아니며 GPU 실행 수준으로 표시하지 않는다. 기존 source2/9/10/50 등은 재사용했다.

## 3. source1 = 현재 거칠기 [판독]

program1279: enable_calc_color0=1, type6, replace0, A0/B100/C1_channel41/D110, clamp1. 실제 291행 r=`max(texture(cTexRoughness,uv).x,.0001)`;341행 q=`fma(r,-const_value0,const_value0)`;343~345행 out.rgb=`clamp(fma(albedo.rgb,const_color0.rgb,q),0,1)`. C1을 다른 target인 알베도에 넣어도 같은 계산된 scalar r를 사용한다. Channel41의 w역수도 raw Rgh alpha가 아니라 `1−r`다. 즉 “거칠기 텍스처”라고만 쓰면 R채널 최소값 처리·scalar 확장과 최종 거칠기를 혼동한다.

몸5549/얼굴1115의 calc2=A1×B102,replace4는 `max(Rgh.R,.0001)*const_color2.x`를 실제 roughness 변수에 쓴다. 이 자기 target 관찰만으로 남겨둔 이전 추정에, 이번1279 다른 target의 dataflow를 추가하여 source 의미를 확정했다.

## 4. source4 = 현재 투과 backlight 색 [판독]

program227: calc0 type5 `(Albedo+const_color0)*const_color0.w`를 임시200에 만들고 calc1 type16 A4/B101/C101_channel40/D200,replace0을 쓴다. 실제334행 TransRGB=texture(cTexTransmission,parallaxUV).xyz,388행 Tx=TransR×Mat.transmission_color_backlight.x,391행 outR=`fma(Tx+const_color1.x,const_color1.w,temporaryR)`;G/B도394/396행 동일하다. source4가 다른 target인 알베도에 소비되어도 **Mat transmission color를 곱한 현재 투과색**임을 확인했다. source4를 raw texture RGB로만 모델링하지 않는다.

1115/5549의 calc1=A4×const_color1,replace1은 기존현재투과색에 const_color1을 더 곱한다. 이번 다른 target의 원본dataflow를 근거로 이전 추정의 의미를 확정했다. type16 전체 ID 의미를 이 한 사용 예로 승격하지 않는다.

## 5. replace7 = 필름 아래 색 [판독]

새program295에서 replace7(type5 A9/B58/C5와후속calc2)의 최종 RGB는 507~510행 `Resource0+my_team_color_hue_complement`, `my_team_color`, `under_film_color` 곱으로 temp76/77/79에 들어간다. 586행 필름비율 `a=clamp(pow(clamp(NdotV,0,1),film_transmission_power)*film_transmission_rate.x*SfxMaskR,0,1)*(1−ThcR)`. 592~594행은 환경반사RGB와 위 tempRGB 사이를 이 a로 보간한 뒤 albedo기여를 더한다. 기존3623 단순 A9×B100 target과도 비교했다. 따라서 replace7이 일반 알베도나 emissive가 아니라 필름 아래 색의 입력임을 명령 dataflow로 확정한다. type5/16/source58/65 전체열거를 이것만으로 완료처리하지 않는다.

## 6. `_Thc` 실제 바인딩·채널 [데이터]+[판독]

Player00 M_Body 데이터에는 M_Body_Thc가 있고 restex_id_thickness_map=4, enable_thickness_map=true다. shader resource slot4는 cTexResource2/_re2로 매핑된다. 몸실제프로그램5549(index.tsv 선택 mismatch0)486행 `k=1−texture(cTexResource2,uv).x`, 얼굴1115 447행 동일이다. 두께맵의 G/B/A를 사용하지 않는다. k를 투과/산란 광량 항에 곱하므로 R=1이면 그항0, R=0이면그항그대로다. 잉크대체분기에서는 k=1로 덮는다.

## 7. 셰이더 연산 범위

새프로그램은 옵션을 수정해 가짜 variant를 만든 것이 아니라 원본키번호로 선택했다. 원본 GPU FMA는 GLSL `fma`로 남기며 CPU f32의 곱/합으로 비트 동일하다고 주장하지 않는다. sampler·texture압축·GPU보간·fullPBR은 실행하지 않았다. 식의 의미와 소비채널은 [판독], 텍스처/옵션 바인딩은 [데이터]다.

## 8. 남은 질문

모든 calc source/calc_type ID 전체, _MAi/_MBi/_Fxm/_MltA 모든재질의채널, fullPBR/UBO live입력은 별도미확정. 227·295 일부 새로운 ID dataflow는 기록했으나 전체열거 질문(shadersL230/L418)은 조사중으로 유지한다. 임의소스값을 채워 전체완료로 표시하지 않는다.

## 9. 웹 반영 필요

impl/render.md/assets.md: calc source1을 현재roughness scalar로, source4를 Mat backlight색이 곱해진 투과색으로 공급한다. replace7은 필름 아래 색 소비로 연결한다. 몸/얼굴Thc R을 물리적거리로 사용하지 않고원본1−R 감쇠마스크로 적용한다. 코드/impl 변경없음.

## 10. 검증·실제 명령

`dotnet shader_dump.dll prog-bfsha Hoian_UBER.Product.bfsha hoian_uber - analysis/completion/r8/graphics_calc_pN --index N`, N=1279/1115/295/227/5549 모두 exit0,vert/frag/options 생성. Programkeys/재질반사샘플러/consumerdataflow를 교차확인했다. GPU원본 실행/픽셀 비트 비교는 하지 않았다. 출력파일SHA256은 r8/calc_thickness_evidence.json에 기록한다.

## 11. 정정 — 2026-10-03

shaders§3.6.4 source1/4와replace7 추정 및formats§4 `_Thc`의SSS 추정을 이번원본다른target 프로그램과실제몸/얼굴소비로 해소. 기존글은삭제하지않는다. source1/4는 raw texture만을 뜻한다는 이전표현을 현재계산값으로정정했으며 전체calc ID 묶음은 남긴다.
