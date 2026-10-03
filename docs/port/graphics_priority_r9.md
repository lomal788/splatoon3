# 재질·눈 패턴·총구 그래픽 r9 반영 — 2026-10-03

화면에 직접 나타나는 **탱크·하네스·총의 잉크병 재질**, **원본 UV 변환과 오징어 눈 재질 채널**, **손과 총을 따라가는 총구 이펙트**를 우선 분석해 웹에 연결했다. 바닥·벽 잉크는 [r7](ink_surface_r7.md), 캐릭터 피부·머리·잠영 표시와 공통 광원은 [r8](character_graphics_r8.md)을 유지한다.

| 기존 항목 | 이번 반영·원본 근거 | 남은 범위 |
|---|---|---|
| **GR03: 탱크·하네스·병** | [추가 재질 §3~9](../graphics/character_variants_r9.md). Tnk2419/2423·Harness4526/4530·Bottle320 실제 옵션 일치0. FxM.R 필름/투과와 edge/scattering 분기, 병의 constant film·team backlight [판독]+[데이터]. 해당 세 재질에 없는 CP/Thc를 필수 조건으로 요구하던 경로 수정 | native cube12/BRDF/SPP·전체 조명·원본 GPU 픽셀 |
| **GR03: 탱크 텍스처 소유권** | 같은 `M_Body_MAi/Trm` 이름이 Player00의 다른 텍스처로 해석되던 차이 확인. `tex/resources/Tnk_Simple/`의 실제 MAi/Fxm/Trm 3개 우선. 마스크 linear/Trm sRGB [데이터], 총7640B | 다른 모델 전부의 텍스처 소유권 감사를 완료한 것은 아님 |
| **GR03/GR02: 원본 UV** | [SRT 상세 §3~10](../graphics/character_texsrt_r9.md). native callback 설치 `088f308`→TexSrt30 `088efb0`→Maya `088f3d0`의 6float writer [판독]+[실행]. Tnk translateY−.6, Bottle scaleY2, 실제 오징어 눈 곡선에 연결 | Maya 회전≠0·다른 모드, native UBO padding/dirty upload 전체 |
| **GR02: 재질 애니·눈** | [재질 채널 §3~10](../graphics/character_material_animation_r9.md). FMAA 원시 frame/key/scale/offset을 보존한 f32 reader와 type11 전용 metadata. full-weight 단일 leaf의 눈 albedo/normal/거칠기 R·SRT 공급 [데이터]+[실행] | weighted type11 blend, 몸 잉크 B+cb8 공급, 실제 피부 선택 idx·type18·binder reset |
| **FX01/FX02: 총구 부착** | [총구 상세 §3~10](../effect_sound/muzzle_attachment_r9.md). actual Weapon_R→Root→Muzzle 월드 행렬을 owner별로 공급. 현재 hand pose의 위치·방향·롤·스케일을 복사해 FX에 전달 [판독]+[데이터] | `MuzzleShotDirXZDot`의 실제 선택 뼈 writer·native Delay 평가 순서, 전체 emitter 운동 |

원본 내적 식은 2,048입력 [실행: 부분]으로 확인했지만, reader의 +3c4/+3c6을 Muzzle이라고 부른 기존 해석은 **2026-10-03 정정**했다. 정상 슈터의 명시적 Muzzle 검색은 +3bc에 기록된다. 시각 부착과 내적 producer를 구분했고 실제 웹 내적을 미확정 입력으로 교체하지 않았다. 탄의 물리 생성 위치도 그대로다.

| 고정 기준 | 현재 | 이번 상태 변경 |
|---|---:|---|
| 원본 전체 | **556/986 = 56.39%** | 전체 질문 승격0 |
| 원본 그래픽 | **102/204 = 50.00%** | 분모·분자 유지 |
| 웹 전체 반영 확인 | **13/62 = 20.97%** | 일부37/차이9/원본 미확정3 유지 |
| 웹 그래픽 GR01~10 | **0/10 = 0.00%**, 일부7/10 | 복합 질문 전체 완료 아님 |

비율은 기존 질문 전체의 충족률이며 재질 개수·검사 표본 수·화면 유사도 점수가 아니다. 부분 셰이더/CPU 공급을 전체 프레임 확정으로 올리지 않았다.

## 실제 검증

- 원본 FMAA reader **1,212건 비트 일치**, 초기화된 피부 홀더 범위/호출 **67건**. 피부 홀더의 모델 갱신은 capture callback 경계이며 현재 플레이어의 피부 idx 공급을 확정한 결과는 아니다.
- 원본 Maya SRT callback/writer **313건 비트 일치**. 실제 SDK 수치·삼각함수 표를 바인딩했고 PLT/수학 스텁0. 24B/6float와 미기록 padding을 구분했다.
- 추가 [controlled frame3 연결 대조](../../../analysis/port_graphics_r9/controlled_surprise_native.json): 원본 눈 curve7개→별도 제공한 SRT 구조체→원본 Maya callback1회→실제 웹6 UV uniform 일치. 정상 상태 trigger·전체 material upload·GPU 픽셀 제외. 앞313개 fixture에 없는 frame3을 별도로 실행했으며 동일 표본을 중복 계수하지 않았다.
- 원본 내적 reader 명령 블록 **2,048건 비트 일치**, 외부 호출0. 실제 행렬 선택 producer·caller·ELink callback 제외.
- 선택 원본 GLSL 항↔웹 GPU **448/448**, 최대 오차 `5.960464477539063e-8`. 실제 세 재질 shader controlled draw 통과. r8 **512/512** 회귀도 통과. 원본 NVN GPU 실행이 아니다.
- 전체 **326/326 테스트**, `npm run typecheck`·`npm run build` exit0. 실제 Lby 사격→자기 도색→변신→숨김→복귀·재진입·reset **12단계/87표시 프레임**, 추가 마른 바닥 오징어/복귀2단계. 재질7개 모두 texture/compile/consumer/지원UV 확인, 실제 Wait 재질35회 적용, controlled Surprise 눈3패턴+원본 UV 공급. 페이지·HTTP·GL·shader 오류0. [최종 보호·검증](../../../analysis/port_graphics_r9/final_verification.json).

처음 actual 브라우저 검사는 잠영 숨김 전에 squid draw를 하지 못해 7재질 compile 확인이 실패했다. 마른 바닥 오징어 draw를 추가해 원본 상태 전이를 유지한 채 coverage를 확보했다. dry20의 type11 weight.92는 근거 없는 강제 합산 대신 unsupported로 남겼으며 dry60 full-weight settle을 별도로 확인했다. `Sqd_Surprise`의 3패턴·SRT draw는 실제 모델에 대한 controlled full-weight 입력이며 정상 상태 trigger를 확인한 장면은 아니다.

에셋은 원본에서 나온 탱크 texture3개와 raw FMAA bank1개만 추가하고 `character/Player00` catalog를 갱신했다. 기존 GLB·다른 에셋·원본·키·impl·scripts·package.json·commit/push 변경 없음. [실제 명령/실패](../../../analysis/port_graphics_r9/commands.md), [웹 실행](../../../analysis/port_graphics_r9/browser_verification.json), [현재 웹 화면](../../../analysis/port_graphics_r9/lobby_after.png).

## 다음 지시 우선순위

| 순서 | 지시 가능한 작업 | 완료 기준 |
|---|---|---|
| **1 P0: 몸에 묻은 잉크·피부** | body B+cb8 writer와 현재 Color_Skin idx 공급을 추적해 CP intensity/team·skin raw 채널을 실제 shader에 연결 | writer→SM→binder→재질 갱신 연속 실행. 잠영 비율로 몸 잉크를 만들어 넣지 않음 |
| **2 P0: 잠영 파문·탄/착탄** | SplPlayer의 상태/행렬/Custom1 및 Ripple dynamic color·linked alpha·VAT 시간률 공급, 형상·CPU 운동 후속 | 실제 발사/착탄/자기 잉크 잠영·복귀·재진입의 자원/색/alpha/수명과 원본 식 대조 |
| **3 P0: 반사·그림자** | native cube12·BRDF·Illuminate·SPP.xy/fade를 현재 공통 조명과 캐릭터/잉크 shader에 공급 | 원본 sampler/계층/producer/소비 순서 확보. PMREM 근사를 전체 원본 반사로 승격하지 않음 |
| **4 P1: 재질 전이·시각 시간** | weighted type11·reset·type18, 내적 실제 뼈 writer와 ELink frame 순서 추적 | 시작→유지→전환→중단→복구의 전체 수명 대조 |

각 항목의 미확정 이유·시도한 방법·다음 함수는 상세 MD §11에 남겼다. 이 문서를 근거로 다음 작업을 지시할 수 있으며 완료율 수치만으로 원본 화면과 동일하다고 판단하지 않는다.
