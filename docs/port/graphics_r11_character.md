# 사격장 캐릭터·무기 그래픽 r11 — 2026-10-04

사격장 Player00(잉클링 F)과 탱크·무기가 원본 사진보다 탁한 갈색이고 평평하게 보이는 원인 중 **캐릭터 재질 쪽 원인**을 찾아 고쳤다. 공통 경로(하늘 색 공간·SH·노출·감마)는 광원 담당 문서 [graphics_r11_light.md](graphics_r11_light.md)가 다룬다. 이 문서의 수정은 모두 원본 데이터 값과 원본 함수 식이다. 임의 밝기·채도 배율, 그림자·외곽선·틴트는 넣지 않았다.

## 1. 찾은 원인과 고친 것

| # | 증상 | 원인(웹) | 원본 근거 | 수정 |
|---|---|---|---|---|
| 1 | 머리카락이 팀색이 아니라 갈색 | `model.ts textureResolver`가 소유 폴더 `tex/<모델>/`를 보지 않고 번들의 첫 같은 이름을 썼다. 그래서 `Har_SQD000_F`·몸 `M_TeamColor`의 `_su0 M_TeamColor_Tcl`(512×256)·`_cp0 M_TeamColor_2cl`이 **눈썹 Eyb의 16×16/8×8**으로 풀렸다. 오징어·`_Hlf`의 `M_Body_2cl`은 몸 것으로 풀렸다. 머리 Alb는 어두운 갈색(sRGB 평균 74,62,59)이라 팀색 마스크가 틀리면 갈색이 된다 | 재질 FRES sampler 이름은 모델마다 지역 이름이다 [데이터: 각 GLB extras.fres] | 순서 `tex/resources/<owner>/` → `tex/<owner>/` → glb → 번들. 몸·오징어·_Hlf에도 owner(`body`/`squid`/`body_hlf`)를 넘긴다 |
| 2 | 피부가 갈색 | `M_Body`/`M_Face`의 `const_color0`(피부색)·`scattering_color`·`transmission_rate`·`edge_transmission_power`·`const_color1/2`를 FRES 정적값 그대로 썼다. 정적 피부색 (.734,.491,.387), 산란색 (.78,.46,.44) | 피부 홀더 `0x71014522b0`은 `Color_Skin`을 항상 붙이고 frame = 피부 번호(범위 밖이면 이전, 처음 0)로 둔다 [판독+실행 r5/r9]. 화면 값은 커브 값이다. 번호 기본 = 새 세이브 초기값 SkinColor 0 ([player_assembly §5.2](../graphics/player_assembly.md)) | 로드 때 `Color_Skin` frame0을 typed FRES 값에 쓴다: 피부 (1,.996,.997), 산란 (1.000785,.974349,.98073), edge power .429. 눈은 `Color_Eye` frame = 눈 번호(0..20)로 `_a0` 패턴 공급(몸·_Hlf) |
| 3 | 눈 발광·오징어 팀색 마스크 값이 낮게 샘플 | glb 내장 `M_Eye_Emm`·`M_TeamColor_Emm`·`M_Glass_Emm`·오징어 `M_Body_Tcl`이 KTX2 tf=2(sRGB)라 GPU가 sRGB 디코드했다 | 원본 BNTX 154장 집계: `_Emm` 3/3, `_Tcl` 6/6 = **BC4_UNORM** [데이터: analysis/graphics/web/*/tex/*.json]. gltfpack은 값 바이트를 바꾸지 않고 태그만 붙인다 | 캐릭터 resolver와 glTF `map/emissiveMap` 슬롯에서 `_Emm/_Tcl`만 `NoColorSpace`(저장값 그대로). 맵은 광원 담당이 같은 helper를 쓴다 |
| 4 | 오징어 두께·투과 | 오징어 `M_Body_Thc`(256²)·`M_Body_Trm`(256²)이 번들에 없어 Player00 몸 것(64²)으로 풀렸다 | Player_Squid BNTX: Thc BC4_UNORM, Trm BC1_SRGB [데이터] | 원본 디코드 PNG를 `asset_ktx2.py`(UASTC, Thc linear/Trm sRGB)로 `tex/resources/squid/`에 추가, catalog 갱신 |
| 5 | 팀색 행 | render·paint가 OrangeBlue 고정 | 로비 선택기 0: 부팅 때 VersusRegular 10행 중 sead::Random `(r·n)>>32` 균등, swap 0 [판독+실행 r6] | `lobbyTeamRow()`: 표 순서 VersusRegular 10행, xorshift128 한 번. render·paint·fx(`teamColors`, 기존 Original 색 소비) 같은 행. 시드는 [미확정] → 웹 crypto 난수, `?teamSeed=N` 재현 |
| 6 | 탱크 잉크가 거의 빈 것처럼, 잉크색이 어둡게 | 탱크 `Gauge` 슬롯 애니가 없어 `Scale` 뼈가 바인드 (1,1,1), `M_Ink team_color_blend`가 FRES 0.5 | 탱크 초기화가 Gauge를 rate0으로 요청, 매 프레임 `0x71026fb6d0`이 Gauge 프레임 = (1−r)·100. 가득 찬 탱크 frame0 = Scale S(1.4254897, 1, **2.1952798**), M_Ink team blend **1** [판독+실행+데이터] | `anim/tank_gauge.ts`(원본 비트 일치) + `data/tank_anim_native.json`(Tnk_Simple FSKA/FMAA 원시 키). Gauge 뼈·재질과 잉크 부족 60프레임 `InkShortage`(45f 반복 M_Glass 발광) 공급 |
| 7 | 모자 결합 | translate 모드 근사 | 모자 슬롯49 `0x71026e613c`: O = Head·P·ManualBindSRT [실행 259/259] | `mode:"head"`, 역행렬 = P·S, S = `V<변형>_<머리>` 키(없으면 단위). 현재 Hed_FST000×SQD000은 키가 없어 화면 결과가 같다 |
| 8 | 애니 이름·점프 변형 | Nrml/@ 단순 치환, 없는 클립도 엔트리 생성, JumpVarID 0 고정 | 해석기 `0x710244d0b0` 후보 순서, 실패 시 엔트리 없음 [실행]; JumpVarID `0x710244128c` 이전%2+1 교대 [판독] | `anim/clip_name.ts`(전부 치환·63자), 스켈레탈 잎 미바인드 시 엔트리 없음, `anim/jump_var.ts` |
| 9 | 머리카락 HairArrange | 미적용 | 키 = 머리카락 id×10000 + 모자 변형, `0x71026df700` 적용식 [실행 r6] | `data/hair_arrange.json`(Hed_FST000 팩의 Blitz_SQD000_2) + `hairArrangeLocal`. 이번 조합은 Front_1 단위 변환·AnimReduceRt 0이라 화면 변화 없음 |

`hoian.ts`(공용)에는 한 가지만 바꿨다. `albedo_color`·`team_color_blend(_alpha)`·`emission_intensity`를 GLSL 리터럴 대신 같은 FRES 초기값의 uniform으로 두고 `setHoianMaterialParam()`을 추가했다. 정적 화면은 리터럴과 같고, 탱크 FMAA가 매 프레임 값을 바꿀 수 있게 했다.

재질 식 자체(body5549/face1115/hair2855/squid3358 cheapSSS·edge/림·film·투과, `enable_taransmission` 철자)는 원본 역번역 GLSL과 다시 대조해 웹과 같음을 확인했다. 피부 albedo = Alb·const_color0·MAi(각 채널), 머리 albedo = mix(Alb, my_team_color, Tcl.r+blend_alpha), film = sat(N·V^2.5·1)·(1−Thc), 바탕색 = mix(albedo, (Thc+보색)·under_film_color, film)이다. 그래서 남은 차이는 재질 식이 아니라 입력(위 1~6)과 공통 경로였다.

## 2. 원본 실행 대조

새 하네스 `web/tools/r11_gfx_char_emu.py`가 원본 v0 함수를 unicorn으로 실행하고 입력·출력 전체를 `tests/fixtures/r11_gfx_char_native.json`에 저장한다. `tests/r11_gfx_char.test.mjs`가 웹 함수와 f32 비트로 비교한다.

| 원본 | 사례 | 결과 | 스텁·경계 |
|---|---:|---|---|
| 탱크 `0x71026fb6d0` 전체 + 정적 초기화 `0x71026f5020` | 48시퀀스×90프레임 | Gauge/InkLock/SubMarker/InkShortageGauge 프레임, 요청·정지·TankEmpty, r/+0x524/+0x528/래치 **전부 일치** | AS update/request/stop·xlink·슬롯 setter는 기록 후 반환. 프레임 사이 +0x4c0/+0x4c4 감소(slot18)와 +0x534 기록은 하네스가 판독식대로 함 |
| 모자 `0x71026e613c` | 161 | 12 f32 **일치**(FMLA 융합을 정확 반올림으로 재현) | owner vt+0x1f8 ret, bone get 공급 |
| 팀색 `0x7101179d6c..da0` | 400 | 인덱스·다음 상태 **일치** | 전역 Random 포인터 공급 |
| HairArrange `0x71026df700` | 80케이스 | 행렬·스케일 **일치** | 뼈 vt 훅, sinf/cosf = 파이썬 f32(웹 JS Math와 같은 값) |
| 클립 이름 `0x710244d0b0` | 520 | 조회 순서·반환 **일치** | 바인더 조회 훅 |
| LOD `0x7103788760` | 600 | 단계 **일치** | 없음 |
| FRES 커브 `0x710088e380` | 697 | 탱크 FSKA Scale·FMAA 커브 **일치** | FSKA 바인더가 이 리더를 쓰는지는 [미확정] |
| hcl `8A63E0`/`DC42A0`+`EE41F0`/`D47BD0`/`D1C354` | 512/160/400 | pow·effectiveDt·계수·적분·Standard/Bend **일치** | r9 합성 객체 |

**원본과 달랐던 기존 기록 2건을 정정했다.**
- InkLock 프레임은 `(1.05−L<0) ? 0 : min(1.05−L, 1)·100`이다. 디컴파일(`tank2.c`)과 player_assembly §6.1이 `FMIN`을 빠뜨렸다(0x71026fb7dc..818).
- 클립 이름 치환 `0x710351c964`는 **모든 일치**를 바꾸고, 전부 실패하면 원래 이름을 63자로 잘라 돌려준다. r5 판독식 `.replace(…,1)`은 중복 문자열이 없는 2210건에서만 맞았다.

## 3. 테스트·실행 결과

- `npm run typecheck` 통과. `npm test` **422/422**(광원 담당 테스트 포함 시점)(신규 `r11_gfx_char.test.mjs` 8건, `r11_gfx_char_web.test.mjs` 9건 포함).
- 화면(단일 캡처 실행, swiftshader): 기본 시점은 수정 전과 같은 입력·시점(OrangeBlue, `?teamSeed=1`), 근접은 플레이어 기준 카메라 덮어쓰기. 브라우저 page/console 오류 **0**(두 로드 모두), 캐릭터 재질 7개 texture ready, 탱크 Gauge frame0 Scale (1.4254897,1,2.1952798) 확인. 상세는 [char_shot_report.json](../../../analysis/gfx_r11/char_shot_report.json).

| 수정 전 | 수정 후 |
|---|---|
| [now_front.png](../../../analysis/gfx_r11/now_front.png) | [char_after_front.png](../../../analysis/gfx_r11/char_after_front.png) |
| [now_back.png](../../../analysis/gfx_r11/now_back.png) | [char_after_back.png](../../../analysis/gfx_r11/char_after_back.png) |
| — | 근접 OrangeBlue [앞](../../../analysis/gfx_r11/char_after_close_front_OrangeBlue.png)·[뒤](../../../analysis/gfx_r11/char_after_close_back_OrangeBlue.png) |
| — | 근접 PinkGreen(`?teamSeed=15`) [앞](../../../analysis/gfx_r11/char_after_close_front_PinkGreen.png)·[옆](../../../analysis/gfx_r11/char_after_close_side_PinkGreen.png) |

원본 사진(analysis/reference_graphics_r3/references/6501.jpg)과 같은 프레임의 픽셀 대조는 하지 않았다. 원본 동일 장면 캡처가 없다.

## 4. 남은 미확정

| 항목 | 이유 | 다음 근거 |
|---|---|---|
| 피부·눈 번호의 실제 Lby 값 | 플레이어 정보 +0x844/+0x848 복사 경로 미추적. 웹은 세이브 초기값 0 | custom save → PlayerInfo 복사 caller |
| 팀색 시드 | 전역 sead::Random(*0x7105997950) 초기화·시드 공급원 미추적 | 생성자/시드 writer |
| M_Body `_o0` 기어 알파 마스크 | 합성 셰이더 FILTER_TYPE 4 식 미확정(r6). 웹은 원래 `M_Body_Opa` 유지 | 0x71058161a0 아카이브 프로그램 역번역 |
| 탱크 InkLock·SubMarker·InkShortageGauge | 본체+0x69c와 서브 무기 잉크 비용 생산자가 웹에 없다. 값 대입 안 함 | 서브 무기 vt+0x68, +0x69c writer |
| 탱크 shortage enable(w2), M_Glass `multi_normal_weight` | 호출자 상태 조합 미해석(웹 1), Hoian multi-normal 소비자 없음 | 0x710248b1c0.. 상태 조건, multi normal 분기 |
| HairArrange +0x338/+0x348 교환, AnimReduceRt 가중 | 필드 writer 미확정, 머리 뼈에 스켈레탈 트랙이 없음 | 0x71026e2450 이후 writer |
| 머리카락 천 | LocalRange/Transition/Stretch·캡슐 충돌·입자→뼈 write-back·frameInfo dt 미확정. 확정 부품(감쇠·적분·Standard/Bend·CullFrame gate)은 `anim/hair_cloth.ts`에 비트 일치로 두고 뼈에 연결하지 않음 | hcl operator vt38 나머지, BoneSpaceSkinP |
| LOD | 선택기는 비트 일치(`anim/lod.ts`). 번들 GLB에 LOD1/2 메시가 없고 `viewRecord+8` 생산자가 미확정이라 연결하지 않음. 사격장 카메라 거리(약 2~4)는 Default 20/50 기준 단계0 | 변환기 `--lod 1/2` 메시, ModelScene 뷰 레코드 writer |
| 애니 type18 가시성·잎 키 목록 | 가시성 클립 미포함, ASB 노드→해석기 키 목록 경로 미추적(웹은 Weapon/Emote 둘 다 있다고 둠) | 0x71039d3608 진입 경로 |
| FSKA 커브 리더 | 같은 데이터에서 88e380과 일치. 스켈레탈 바인더가 이 리더를 호출하는지 미확인 | FSKA 바인더 판독 |

## 5. 공통 경로에서 발견한 것(광원 담당 전달)

- 캐릭터 재질 식은 원본과 같다. 수정 후에도 피부가 주황 쪽으로 진하게 보이는 것은 albedo(Alb 자체가 주황 기미)×광원·SH·노출·톤맵의 결과다. 광원 담당이 하늘 BC6H를 sRGB로 디코드하던 결손(SH 어둡고 파랑 편향)을 이미 찾았다.
- `textureResolver`의 `_Emm/_Tcl` 선형 처리는 인자로 켜는 방식이다. 맵(`map.ts`)도 같은 helper를 쓴다(이중 처리 없음).
- `hoian.ts`의 `emission_color_type` 0·replace2 없음 경로는 three `emissive×emissiveMap`에 의존한다. 변환기가 `emissiveFactor`에 intensity를 넣는 관례와 맞물려 있다. 이 관례는 원본 식(Emm·emission_color·intensity)과 같은 결과지만 변환기 쪽 규칙이라 공통 경로에서 기억해 둘 것.
- 탱크 `M_Body`(Tnk_Simple)의 붉은 발광은 r9 calc22 경로(Emi·0.33+MBi−MAi, ×intensity .5) 그대로이며 이번에 바꾸지 않았다. 팀색과 무관하게 붉게 보여 원본과 다를 가능성이 있다 [확인 필요: 원본 탱크 근접 화면·MAi UV2 대응].
- replace-color 2 경로(오징어 M_Body 등)는 `hCalcEmission = emissive(=intensity)×map`에 다시 `emission_intensity`를 곱한다. intensity가 두 번 들어간다(오징어 .01→.0001). 공용 hoian 식이라 이번에 고치지 않았다.

## 6. 변경 파일

웹: `client/render/{model,player,teamcolor,index,shared}.ts`, 공용 `client/render/hoian.ts`(라이브 파라미터 1건), `client/paint/index.ts`(같은 팀색 행 사용), `client/render/anim/{animator,asb,slot,material_channels}.ts`와 신규 `anim/{clip_name,jump_var,tank_gauge,hair_cloth,lod,native_f32}.ts`. `character_material(_math).ts`·`forward.ts`는 바꾸지 않았다. 에셋: `characters/Player00/tex/resources/squid/{M_Body_Thc,M_Body_Trm}.ktx2`, `data/{tank_anim_native,hair_arrange}.json`, catalog는 `character/Player00`만. 도구·테스트: `web/tools/r11_gfx_char_emu.py`, `tests/r11_gfx_char.test.mjs`·`r11_gfx_char_web.test.mjs`, `tests/fixtures/r11_gfx_char_native.json`. 캡처 스크립트 `analysis/gfx_r11/char_shot.mjs`. 원본 폴더·commit·push 변경 없음.

## 조정자 후속 수정 (2026-10-04): 발광 세기 이중 곱

- `client/render/hoian.ts` replace_color 2 발광 경로에서 emission_intensity가 두 번 곱해지던 것을 고쳤다. 원본 식은 방출 색 × emission_intensity 한 번이다(shaders.md, 2162).
- 원인: native 발광 텍스처가 없을 때 `hCalcEmission` 초깃값을 three의 `totalEmissiveRadiance`로 잡는데, 이 값에는 이미 세기가 곱해져 있다(`setHoianMaterialParam`가 emissive = Emm 색 × 세기). 그 뒤 replace2 경로가 다시 세기를 곱했다(오징어 M_Body .01 → .0001).
- 수정: 대체 경로 초깃값에서 세기를 나눠 뺐다. emission_color_type 1 경로는 결과가 이전과 같도록 대체 경로에서만 세기를 다시 곱한다. native 텍스처 경로는 변경 없음.
- 검증: typecheck, `npm test` 422/422, build 통과.
