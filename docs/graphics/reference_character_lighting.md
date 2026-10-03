# 캐릭터 재질·빛·그림자의 원본 화면 차이 — 2026-10-03

이번 요청은 그래픽 분석과 MD 반영이다. 웹 코드·impl·원본·에셋은 수정하지 않았다. 첨부 사진은 캐릭터, 잉크의 광택, 주변광과 그림자를 비교하는 **정성 참고**다. 사진만으로 Splatoon 3 v0, Lby_Lobby00, 색 보정·조명 설정·정확한 재질 값을 확정하지 않는다. 상단·하단 화면의 게임/버전/HUD가 같은 것으로 묶지 않는다.

## 1. 기능 개요와 사용자에게 보이는 동작

캐릭터 외형의 동일성에는 모델 파일 외에 피부의 간이 산란(`enable_cheap_sss`), 가장자리 투과, 머리카락/오징어의 필름, 몸에 묻은 잉크 분기, 화면 공간 그림자와 환경 반사가 필요하다. 현재 웹은 원본 모델·팀색·일부 색 계산을 사용하지만, 네 핵심 재질(body/face/squid/hair)의 원본 투과·필름 최종 소비가 빠져 있다.

**[신규 판독]** 몸5549의 `_MAi.R`는 알베도에 곱하는 RGB 리소스의 일부인 동시에 cheap SSS와 투과량의 마스크다. `_Thc.R`를 읽어 만든 `1−R`를 투과 광량에 곱한다. 원본 주광은 단순 `max(N·L,0)`만 쓰지 않고 마스크 영역에 wrapped lighting을 섞으며, 별도 backlight 항을 마지막 RGB에 더한다. **[웹 실행]** 현재 생성된 shader에서 `_Thc`는 uniform/texture 준비까지 되고 실제 sampling은 없으며, 7개 SSS/필름 필드의 조명 소비가 없다.

이 확인은 캐릭터 재질의 주요 결손을 뜻한다. 실제 원본/웹 한 프레임의 픽셀 동등성이나 전체 그래픽100%를 뜻하지 않는다. 다른 화면 차이는 바닥 도색·발사 FX·환경·후처리 문서와 함께 봐야 한다.

## 2. 분석 대상 원본·버전·자료 위치

| 자료 | 위치 | 수준/재사용 범위 |
|---|---|---|
| 원본 FRES 덤프 | `analysis/graphics/dump/samples.json.gz` | [데이터], 기존 Player00/Player_Squid/Har_SQD000_F 원본 값 재사용 |
| 실제 원본 재질 프로그램 | Product Hoian_UBER: body5549, face1115, squid3358, hair2855 | [데이터]+[판독], 원본 키 선택을 유지 |
| 이번 표준 CLI CB1 재검사 | `analysis/reference_graphics_r3/character/{body5549,squid3358,hair2855}.{vert,frag}` | c1 분기표 보완 CLI 사용. 6stage가 기존 산출물과 SHA256 동일. 아래 음수식 출력 결함이 남은 legacy 파일 |
| 음수식 괄호 보완 덤프 | `analysis/reference_graphics_r3/character/{body5549,squid3358,hair2855}_grouped.{vert,frag}` | [판독 보조], 분석 전용 patched emitter로 6stage 출력. 본문의 식/행 번호는 이 파일을 사용 |
| 현재 출하 GLB | `web/games/splatoon3/assets/characters/Player00/{body,squid}.glb`, `parts/Har_SQD000_F.glb` | 실제 웹 에셋 JSON을 읽음. fixture 모델/임의 재질을 쓰지 않음 |
| 현재 렌더 소비 | `client/render/{player,model,hoian,forward,lighting}.ts` | [웹 판독]+[웹 실행: material hook CPU] |
| 이번 근거 | [web_material_consumers.json](../../../analysis/reference_graphics_r3/character/web_material_consumers.json), [native_material_data.json](../../../analysis/reference_graphics_r3/character/native_material_data.json), [grouped_shader_audit.json](../../../analysis/reference_graphics_r3/character/grouped_shader_audit.json), [commands.md](../../../analysis/reference_graphics_r3/character/commands.md) | 실행 경계·SHA·합성 입력을 보존 |

**정정(2026-10-03): 번역기 음수식의 괄호 결함.** 표준 CLI의 `InstGen.Negate`는 전체 식을 감싸지 않아 `a * 0.0 - b`를 출력하는 경우가 있다. 원본 FMUL의 negate는 `a*(0−b)`에 해당한다. 몸5549 원시 FMULR에 NegA=1이7곳이고, 0x9a0/0x9a8/0x9b8의 V.xyz 정규화가 이 사례다. 기존 SHA 동일6stage는 **같은 legacy 출력을 받았다는 확인**이며 식의 의미가 맞다는 증명이 아니다. 분석 전용 emitter에서 괄호 한 곳을 보완해 body/squid/hair를 다시 덤프했다. 표준 tool/source는 바꾸지 않았다. 아래 식의 시선·빛 부호는 원시명령/보완 출력과 대조했다. 보완 GLSL도 GPU 전체 실행과 동일하다고 승격하지 않는다.

SHARED/FUNCS와 `decomp_index.py 1134c40/36b35c0`를 먼저 확인했다. MainLight→Env·팀색·모델 조립·표시·기존 `_Thc.R` 결론은 재분석 성과로 세지 않는다. 신규 deep reading은 기존 프로그램의 **mask→직접광/역광→최종 RGB**와 **필름→환경광 법선/투과량** 소비 연결이다.

## 3. 진입점과 전체 호출 흐름

원본 경로 [기존 판독 재사용 + 신규 셰이더 소비 판독]:

```text
RenderingDay.MainLight
  2b607c4 Color/Intensity → agl DirectionalLight
  36b35c0 뷰별 Env[5]=Intensity*DiffuseRGBA, Env[23]=방향,
             Env[25..31]=SH7 vec4
실제 BFRES 재질·옵션·각 texture slot
  body5549 / face1115 / squid3358 / hair2855
  normal·CompPaint → 잉크 분기 또는 보통 재질 분기
  MAi/Thc/Trm + Mat 상수 → cheap SSS·edge transmission·film
  Env 주광 + BlitzUBO2 동적광 + SH + env cube/BRDF + shadow
  최종 RGB → 높이/깊이 안개 → HDR/CCLUT/감마
```

현재 웹 경로 [웹 판독/실행]: `PlayerView.load`가 실제 GLB와 파츠를 고름→`player.ts:237`의 `teamMaterials`→`fresOf`→`applyHoian`→`applyForward(..., bake=null)` (`player.ts:247–248`). `hoian.ts:115`는 Trm×backlight를 읽고 calc_color에 넘기지만, `forward.ts`의 최종 광량 식은 hCalcTransmission/hCalcUnderFilm을 소비하지 않는다.

원본 pass들의 전체 frame 실행 순서를 새로 확정하지 않았다. 위 식의 원본 uniform writer와 shader reader를 연결한 것이며, 현재 CPU fixture는 실제 게임 Actor/Scene/NVN/GPU를 실행하지 않았다.

## 4. 구조체·필드·상수·열거형 표

다음은 실제 FRES 기본값 [데이터]. **런타임 피부색·재질 애니 적용 뒤 값으로 확정하지 않는다.** 웹 GLB의 같은12필드×4재질=48개가 f32 비트 변환 기준 모두 같은 값이었다.

| 값 | Player00 몸/얼굴 | Player_Squid 몸 | Har_SQD000_F 머리카락 |
|---|---:|---:|---:|
| 원본 옵션 이름 | `enable_taransmission=True` | 동일 | 동일 |
| `transmission_rate` | .3 | .5 | .4 |
| `scattering_rate` | .2 | 1 | 1 |
| `scatter_distance` | .2 | 0 | 0 |
| `scattering_color.rgb` | (.78,.46,.44) | (1,1,1) | (1,1,1) |
| `edge_transmission_power` | 1.2 | 1 | 1 |
| `transmission_color_backlight.rgb` | (1,.16,.12) | (.6,.26,.09) | (.60382736,.26327342,.1004815) |
| `film_transmission_rate` | 0 | .9 | 1 |
| `film_transmission_power` | 3.2 | .7 | 2.5 |

`enable_taransmission`은 오타처럼 보이지만 **원본 실제 철자**다. 별개 옵션 `enable_transmission`도 Product에 있으며 몸5549에서는0이다. 둘을 같은 키로 간주하면 안 된다. 현재 `hoian.ts:128`은 별개 키만 검사해 SSS 미반영 진단을 내지 않는다. 이번4재질 모두 원본 taransmission은 켜져 있고 이 경고는0이었다. 이 결과는 경고 결손이지, 경고가 없으므로 원본 투과를 구현했다는 뜻이 아니다.

| 입력 | writer/자료→reader | 확정 경계 |
|---|---|---|
| `cTexSfxMask/_fm0`의 MAi.R | body M_Body_MAi / face M_Face_MAi→body510/643–647행 | [판독]+[데이터], cheap SSS mask와 tau |
| `cTexResource0/_re0`의 MAi.RGB | 같은 MAi texture→body505–509행 | [기존 판독] calc0의 알베도 곱. R에 추가 의미가 있음 |
| `cTexResource2/_re2`의 Thc.R | `restex_id_thickness_map=4`→body511/edge799행 | [기존+신규 판독] k=1−R→최종 역광 |
| `cTexTransmission/_t0`의 Trm.RGB | body499/512–514행 | Mat backlight×const_color1 뒤 역광 입력 |
| `Env[5].rgb/.w` | 원본36b35c0→body587/644–647/804–806행 | RGB=I×DiffuseRGB, **w=I×DiffuseAlpha**. 주광 역광항은w 사용 |
| `BlitzUBO2` light RGBA/거리/방향 | [dynamic_lighting.md](dynamic_lighting.md)→body717–779행 | packed cell 첫4개·동적 역광도RGBA.w 소비 |

원본 번역 파일 행 번호는 `_grouped` 분석 전용 보완 산출물 기준이다. 실제 sampler의 원본 loc와 보완 GLSL `layout(binding)` 번호는 서로 다른 번호 공간이므로 바꾸어 쓰지 않는다. f32/FMA를 조합한 새 CPU 구현이 GPU와 bit 일치한다고 주장하지 않는다.

## 5. 상태 전이와 전체 수명

- 재질의 위 분기는 매 fragment 현재 CompPaint/법선/시선/빛을 소비한다. `_Thc`, `_MAi`, Trm 텍스처를 불러오기만 하고 캐릭터 기본색을 바꾸는 것으로 동등하지 않다.
- 몸5549 잉크 분기에서는 MAi 마스크=0, k=1, tau=0으로 바꾸며 피부 산란 대신 잉크 재질을 쓴다(480–495,618–619행). 피부용 SSS를 잉크로 덮인 몸에도 그대로 더하면 원본과 다르다.
- 인간↔오징어 모델 교체와 아군 잉크 잠영 숨김은 별개다. B7a0 지연→SM 표시→holder→off 재질 캐시 reset의 기존 [실행] 근거는 [squid_ink_visibility_r2.md](squid_ink_visibility_r2.md)를 따른다. 이번에 재실행하지 않았다.
- 현재 `PlayerView.draw`는 body/hlf/squid 표시만 소비하고, `applyLeaves`는 type3 skeletal만 적용한다(`player.ts:67`). type11 재질·type18 가시성 leaf, 눈/피부 패턴·몸 잉크 런타임 변화의 실제 적용은 여전히 빠져 있다. bundle의 `data/anim_material.json` 존재는 소비 구현의 증명이 아니다.
- 원본 머리카락의 cloth frame/pre/step/post와 HairArrange는 기존 문서를 재사용한다. 현재 `PART_RULES.Hed`의 translate 부착(`player.ts:22`)은 기존 확정 `Head·P·ManualBindSRT`와 차이가 있으며, 독자 hair bone의 정적 부착만으로 천 변형을 구현했다고 볼 수 없다.


**발사 포즈 공급의 현재 관찰과 경계 [웹 판독/실행 참고].** 부모의 [visual_smoke.json](../../../analysis/reference_graphics_r3/parent/visual_smoke.json)의 제어fixture는 frame151에 Fire/BulletSpawn이 있고 state0x56(WaitHold)을 기록했다. 원본 게임의 프레임이 아니며, world.step을 정지시키고 입력/플레이어 step을 호출한 웹fixture다. 이것만으로 Fire→AS 전체 경로가 끊겼다고 확정하지 않는다. 실제 `core/weapon/runtime.ts:447–451`은 weapon.shooting/frame을 쓰고 `core/player/index.ts:197–198`은 그 값을 읽으며 `core/player/sm.ts:274–276`은 shoot이면0x59(WaitShoot)를 선택한다. `core/systems.ts:16–17`의 player→weapon 순서는 첫 발사tick에 이전 weapon 값을 읽는 지연 원인이 될 수 있다. **추가 웹 실행(2026-10-03):** [fire_pose_smoke.json](../../../analysis/reference_graphics_r3/parent/fire_pose_smoke.json)의40프레임 hold 뒤 frame180은 state0x59, weaponShooting=true, weaponFrame179이고 errors0/badResponses0이다(시작 frame140은0x56/false). 따라서 이 fixture의 지속발사에서 WaitShoot 상태까지 연결됨을 확인했다. 원본 GPU/최종 Shoot leaf·clip·포즈 동등성은 확인하지 않았다. 최초 발사tick의 공급 지연과 최종 leaf/clip 연속 기록은 여전히 별도 검증 대상이다.

**원본값과 현재 공급이 다른 별도 확정 지점.** [animation_weapon_blackboard.md §1/3–5](animation_weapon_blackboard.md)의 원본 일반슈터는 선택 중 Category/Detail 둘 다 `Shtr`, holder null전환에는 둘 다empty다. 현재 `client/render/anim/animator.ts:46–47`은 Category=weaponAbbr, Detail=empty를 고정한다. 이 차이는 기존 원본 근거의 웹 consumer 비교다. 네이밍·클립 치환에 영향을 주지만 전체 발사포즈 오류의 원인 하나로 단정하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 몸5549: cheap SSS의 주광과 역광 [신규 판독]

기호는 설명용 이름이다. N=현재 재질 법선, V=픽셀→카메라 단위벡터, D=Env[23].xyz, L=−D, C=Env[5].rgb, W=Env[5].w, m=MAi.R, k=1−Thc.R. clamp와 FMA의 정확한 연산 순서는 원시명령과 `_grouped` GLSL을 함께 기준으로 구현한다. 보통 나눗셈/pow로 적은 아래 식은 구조 설명이고 원본은 reciprocal 및 log2→곱→exp2를 쓴다.

```text
u = dot(N,L)
n = clamp(u,0,1)
wrapped = clamp(u+scatter_distance,0,1)/(1+scatter_distance)
Cdirect = mix(n*C,
              clamp(n+scattering_color.rgb,0,1)*wrapped*C, m)
tau = m*transmission_rate
T = Trm.rgb*transmission_color_backlight.rgb*const_color1.rgb
q = (scattering_rate-1)^2
edge = pow(clamp(1-dot(N,V)*clamp(-u,0,1),0,1), edge_transmission_power)
       * (q*(pow(clamp(max(dot(V,D),.001),0,1),1/scattering_rate)-.2)
          +.200000003) * k
AoLight = clamp(1-shadowOcclusion*BlitzUBO0[36].w,0,1)
BacklightRGB = AoLight*edge*T*W*tau
```

body634–647행은 Cdirect를 만들고, body799–806행은 edge/BacklightRGB를 **마지막 RGB에 실제 더한다**. body804–806행의 RGB는 `AO*IndirectRGB + shadowMask*BRDF*Cdirect*(1−tau)*normalCorrection + BacklightRGB + inkEmission`의 구조다. BRDF/normalCorrection/shadow 입력을 생략한 위 식을 전체 재질 구현으로 삼으면 안 된다.

같은 분기는 body763–779행의 동적광에도 있다. 기존 packed cell에서 최대4개의 light를 읽고 거리/spot 감쇠를 계산한 뒤, cheap SSS의 RGB 직접광과 `LightColor.w*edge*T*tau` 역광을 각각 합한다. 웹 `hDynamic`의 diffuse+specular만으로는 이 경로를 재현하지 못한다. `hLightColor`가 vec3라는 현재 계약에는 원본 W의 전달도 필요하다.

**[재구현 계산: 합성 sanity]** 실제 몸 기본값을 사용하되 N=(0,1,0), V=L=(0,0,1), MAi.R=1, Thc.R=0, Trm=(1,1,1), 주광RGBA=(1,1,1,1), shadow=1인 입력을 넣었다. 원본식 직접광RGB≈(.13,.0766667,.0733333), 추가 역광RGB≈(.0162648,.000957312,.000689472)다. 보통 Lambert의 N·L 직접광은0이다. 이는 사진 픽셀/실제 Lby 입력이 아니라 **빛의 방향에 따라 원본에서 남는 항을 웹이 통째로 누락하는 반례**다. 계산은f64이며 GPU FMA 비트 검증은 아니다.

### 6.2 오징어3358: 필름은 반사색만의 옵션이 아니다 [신규 판독]

squid480–500행에서 underFilm=`(Resource0.rgb+my_team_color_hue_complement.rgb)*under_film_color.rgb`, T=`Trm.rgb*backlight.rgb*my_team_color.rgb`, k=1−Thc.R이다. squid575행의 film은 다음과 같다.

```text
film = clamp(pow(clamp(max(dot(N,V),.001),0,1),film_transmission_power)
             *film_transmission_rate,0,1)*k  // squid의 mask는1
SHNormal = mix(currentNormal, originalVertexNormal, film)
DiffuseInput = mix(albedo*(1-metalness), underFilm, film)
tau = transmission_rate*(1-film)
```

squid576–588행은 이 값으로 **SH평가 법선, 직접 diffuse 입력, 투과량**을 바꾼다. 환경반사층은 roughness의 원본 cube-array 층을 읽고, manual Fresnel도 별도 적용한다. 필름을 단순한 화면 투명도 또는 emissive 색으로 옮기면 원본과 다르다. 머리카락2855도 같은 underFilm·tau 연결을 한다(577–590행). 선택된 squid3358와 hair2855의 보통 재질 분기는 film mask를1로 놓고 그 뒤 k=1−Thc.R을 곱한다. 다른 재질/프로그램의 별도 mask를 이 변형에 임의로 넣지 않는다. hair의 T는 Trm×backlight이고, squid의 T에는 team RGB가 추가된다. 원본 UV 선택, normal과 originalVertexNormal의 구별을 보존한다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

원본 재질은 인간/`_Hlf`/오징어의 실제 표시 결정과 동일 프레임의 재질·가시성 애니를 함께 소비해야 한다. 머리카락·오징어의 팀색은 Model 색, under-film의 보색, Trm의 팀색 곱이 서로 다르다. 바닥/이펙트의 Original/Ink/InkBright를 아무 재질에나 공통색으로 대입하지 않는다.

몸5549는 screen shadow `cGSysShadowPrePass.xy`와 projection `cGSysProjection0.R`를 읽어 각각 occlusion·최종 직접광 gate를 만든다(571,590–593행). 원본 그림자 설정·객체 생성/등록·slot14·두 clamp는 [projected_shadow_runtime.md](projected_shadow_runtime.md)와 [stage_rendering.md §3/5](stage_rendering.md)를 따른다. live projection 행렬/factor와 화면 shadow texture 전체는 미확정이다.

현재 웹은 `map.ts:130–137`의1024² 단일 Directional shadow와 ±6 유닛·bias−.0005, `PCFSoftShadowMap`을 쓰고 `forward.ts`에서 getShadowMask를 합한다. 원본의 별도 화면 공간 shadow .xy와 projection sampler를 공급하지 않는다. 이 차이를 입증했지만 원본 PCF kernel/전체 pass를 새로 확정하지 않았다. 캐릭터는 castShadow 설정만 두고 receiveShadow를 별도로 켜지 않는다(`player.ts:211`); 실제 web renderer의 그 결과는 GPU 캡처로 따로 확인해야 한다.

## 8. 다른 기능과의 상호작용

캐릭터의 빛은 같은 Scene의 MainLight/SH/dynamic grid/environment cube를 사용한다. `LightingState.capture`의 웹 cube projection·두 번 캡처·PMREM은 현재 문서에서도 근사이며, 원본12층 roughness prefilter+잉크층12+BRDF map과 자동으로 동등하지 않다. 위 native film/transmission을 추가할 때 PMREM 차이와 shader 결손을 함께 검증해야 한다.

최종 HDR/색보정/감마를 먼저 과도하게 조절해 SSS나 film의 결손을 가리면 빛의 방향·몸 회전·잠영 전환에서 다시 차이가 생긴다. 원본식 입력→재질 RGB→환경/그림자→후처리 순으로 각각의 출력을 비교해야 한다. 카메라가 바뀌면 N·V·V·D가 바뀌므로 머리카락/오징어의 느낌도 바뀐다. 이는 카메라 버그와 별개인 정상 재질 시선 의존성이다.

## 9. 웹 포팅 구조와 구현 순서

이번에 구현하지 않았다. 아래는 현재 코드에 대한 구체적 구현 지시 단위다.

| 우선순위 | 반영할 일 | 현재 지점 | 완료 조건 |
|---|---|---|---|
| P0 | body/face MAi.R cheap SSS·Thc.R·Trm 역광의 원본 consumer | hoian.ts:73–83/111–128, forward.ts의 accum | mask/방향/역광 fixture의 원본 항과 순서 보존; 실제GPU 비교 별도 |
| P0 | squid/hair film→DiffuseInput/SHNormal/tau/보색 연결 | hoian.ts의 hCalcUnderFilm 생성, forward.ts | 원본 두 법선/film gate/팀색/12층 cube reader를 연결 |
| P0 | material option 이름을 원본 `enable_taransmission`와 별개 transmission 옵션으로 처리 | hoian.ts:128 | native true인데 warning가 없는 현재 상태 제거. 임의 spelling 정규화 금지 |
| P0 | CompPaint 잉크분기와 ordinary 피부/필름분기 분리 | 실제 body/face/squid/hair 재질 | 잉크덮임 때 피부m/tau0, 잉크색/거칠기/법선으로 전환 |
| P0 | 일반 슈터 Category/Detail `Shtr/Shtr`, null전환empty를 두 해석기/BB에 공급하고 지속Fire 상태·leaf를 연속 확인 | anim/animator.ts:46–47, core/player/index.ts:197–198, core/weapon/runtime.ts:447–451 | 첫발사와 다음tick을 구분; WaitShoot→Shoot clip까지 검증 |
| P1 | B7a0 delayed 표시와 type11/type18 재질·가시성 애니 | player.ts:67/301–365, anim/animator.ts | 첫 잠영/유지/나오기/재진입과 눈·피부·몸 칠 비교 |
| P1 | native shadow prepass/projection 입력과 최종 캐릭터 수신 | forward.ts shadow, map.ts:130–137 | projection live source 미확정은 별도 추적. 단일shadow 근사=원본이라 표시하지 않음 |
| P1 | 모자 Head·P·ManualBindSRT, HairArrange/cloth/LOD | player.ts:22, model.ts:108 | 기존 native 근거를 각 consumer에 적용; 전체포즈/cloth 미확정은 남김 |

재질별 native input을 하나의 상수 머티리얼로 합치지 않는다. 권장 모듈 이름은 `CharacterMaterialInputs`, `NativeCharacterLighting`, `CharacterDisplayInputs`이며 원본 클래스명은 아니다. 피부색/팀색/material animation provider→texture channels→native branch→linear HDR framebuffer→최종 후처리의 검증 경계를 각각 보존한다.

## 10. 검증 코드·실행 결과·기대값

| 실제 명령 | 결과 | 실행/증명 범위 |
|---|---|---|
| `decomp_index.py 1134c40`, `36b35c0` | 기존 캐시2함수 확인 | 중복 decompile 없음, 기존 UBO 근거 재사용 |
| 표준 `shader_dump.dll prog-bfsha ... --index 5549/3358/2855` | exit0,3program×2stage | c1 보완전후6stage SHA동일, 음수 괄호 결함이 남은 legacy 출력. GPU실행 아님 |
| 분석 전용 `surface/dump/.../dump.dll prog-bfsha ... --index 5549/3358/2855` | exit0,3program×2stage | Negate 괄호 보완 출력6stage와 SHA 저장. 원시5549 NegA FMULR7곳 대조, 원본GPU 실행 아님 |
| `shader_raw_audit.dll ... 5549 ...body5549_raw`; `... ops ... > ...raw.ops.txt` | exit0 | 원본 fragment opcode/분기 행 보존. GLSL 출력이 원본 명령을 잘못 묶는 사례를 교정 |
| `node analysis/reference_graphics_r3/character/web_material_consumers.mjs` | **30/30 PASS** | 실제 GLB metadata+actual fresOf/applyHoian/applyForward CPU hook. texture는 빈 handle/white team/UV0 fixture, WebGL 미실행 |
| 부모 actual browser Fire hold40 | frame140 state0x56/false→frame180 state0x59/true, errors0/badResponses0 | 웹 상태 연결까지. 원본/Shoot leaf·clip·포즈 비교 아님 |
| `.venv/Scripts/python -X utf8 analysis/reference_graphics_r3/character/native_material_data.py` | **48값 f32 대조+1sanity=49/49 PASS**, 합성12입력 보존 | 기존 FRES값 재사용. native 함수/원본 GPU를 실행한 사례가 아님 |

CPU generated shader4개와 source SHA를 결과에 저장했다. `_re2`를 준비하지만 sampling0인 사실, SSS7필드 미소비, 원본taransmission을 놓친 diagnostic은4재질 모두 재현했다. GLTFLoader/texture pixels/GPU/원본 whole frame은 실행하지 않았다. 원본 Unicorn 신규 사례는0이다. 기존 원본 실행 수를 새30/49건에 더하지 않는다.

실패도 commands.md에 보존했다. 오타 경로 `web/分析.txt`, 없는 `Har_SQD000__M_Hair.frag`/`asset_models.py`를 읽는 검색은 실패했다. 실제 분석.txt, `Har_SQD000_F__M_TeamColor`, 실제 material source를 확인해 교정했다. 분석 값이나 원본 파일을 실패 회피용으로 바꾸지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 미확정 | 이유·시도·다음에 볼 곳 |
|---|---|
| 첨부사진과 동일한 frame의픽셀 | 사진의 버전/스테이지/설정·원본 uncompressed frame·view/material frame 입력 없음. 정성비교만 사용. 실제Lby 원본 같은카메라/팀색/노출 기준frame 필요 |
| 원본 Env cube/12층필터/BRDF texture의 실제값 | shader reader/CPU SH계수는 기존확정, web PMREM은근사. stage_rendering§5.4/5.6 actual capture/pre-filter source 필요 |
| 화면 shadow prepass XY와 projection livefactor/matrix | 본문 shader channel/consumer는확정, 생성/밀도 근거 재사용. projected_shadow_runtime§8의530/4E8 writer와 실제pass texture 필요 |
| 지속 Fire의 실제 AS leaf/최종포즈 | 최초Fire fixture는WaitHold이나 추가40frame hold는0x59/weaponShooting=true까지 확인. writer→reader 존재와 상태연결은웹실행으로확인, 최종Shoot leaf/clip·원본포즈비교는미실행. WeaponDetail 원본과차이는별도확정 |
| live skin/materialanimation 값과 전체포즈 | 이번은 실제 BFRES 기본값 대조. player.ts type11/18 적용 없음. anim_state_machine/asb_event/as_request_first_tick의 연속tick·최종material producer 추적 |
| shader 완전등가와GPU FMA/압축/filter/raster | CB1보완6stage legacy SHA동일을 semantic 증명으로 쓰지 않는다. Negate 한 곳 보완6stage/원시FMULR7곳을 대조했으나 번역 전체 오류 없음과 원본GPU 실행은 미확정. CPUhook30PASS/f64 sanity를GPU확정으로 승격하지 않음 |
| 머리카락cloth 실제body/LOD/frame 연결 | 원본 상수·부분step 기존확정, live dt/cull/capsule/order/전체pose 미확정. cloth_frame_runtime§11와 native3A1BAE4/3C0AAE0/3C0C0BC/3C0D72C |

고정986 inventory·port62 분모/상태는 변경하지 않았다. 기존 넓은 캐릭터/UBO/GPU/포즈 질문을 이 부분 consumer 결과로 승격하지 않는다. 사진 느낌에 맞춘 임의 밝기·roughness·shader 상수를 넣지 않는다.


### 2026-10-03 웹 반영 r8 후속 — 기존 결론 보존

[현재 반영/검증](../port/character_graphics_r8.md), [재질 소비](character_material_r8.md), [표시 공급](character_display_r8.md)를 우선한다. 기존 '이번 작업은 분석만/구현하지 않음'은 해당 회차 기록이다. r8은 실제 네 캐릭터 재질, RGBA 강도, B7a0 지연 숨김/SM/holder, Shtr/Shtr를 웹에 연결했고 전체304/304·typecheck/build·Lby12단계를 검증했다. live 재질/전체 pose·원본 GPU/Phive 동등성을 완료로 승격하지 않는다.

정정: 현재 실제 face GLB에는 `_ao0=M_Face_Ao`가 존재하며 face1115가 읽는다. 예전 요약 sampler 목록의 누락을 실제 리소스 부재로 해석하지 않는다. 실제 texture ready 확인과 원본 face reader [데이터]/[판독] 근거는 character_material_r8 §4·10을 따른다.
