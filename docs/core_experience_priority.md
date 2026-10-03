# 사격장 핵심 체감 경로 — 최우선 분석 기준

2026-10-03 사용자 지시 반영. **카메라·물리·사격·바닥 도색·그래픽(렌더링/캐릭터/광원)을 최우선**으로 한다. 주변 기능의 확정 수가 늘어도 핵심 경로가 남아 있으면 목표가 달성된 것이 아니다.

## 1. 완료 판단

출처별 처리율과 핵심 경로 완성 여부를 따로 보고한다. 아래 다섯 경로가 입력부터 플레이어가 보고 느끼는 최종 결과까지 원본 근거로 이어지는지가 우선이다. 단일 함수나 합성 객체 실행을 전체 게임 동작 검증으로 바꾸어 말하지 않는다. 미확정에 임의 값·더 자연스러운 동작을 넣지 않는다.

## 2. r7 시점의 우선 작업과 남은 연결

| 최우선 경로 | 원본 근거가 이어져야 할 끝점 | 현재 남은 핵심·다음 근거 |
|---|---|---|
| 카메라 | 입력/감도→리그·추종/붐→최종 포즈→뷰·투영→실제 화면 | 최종 device posture(5997898→모듈+2ac), 활성 포저 vt+30→C+88, 질의 필터 W+d0·world vt+3f8. 붐/FOV 부분 실행만으로 전체 화면 확정 아님 |
| 이동·물리 | 입력→속도/중력→실제 지형 접촉→접지·계단·경사·벽→최종 위치 | 원본 로비 지형→Havok09cec84/09cee34→SplResultPlayer2c5a3c8/분류2c5dd20→계단 추가질의2c5e6a8→슬롯19 위치. 실제 접촉으로 연결한 전체 실행이 남음 |
| 사격 | 버튼→게이트/연사·잉크→총구·탄→지형/표적 명중→피드백 | B+4d0 writer는7차 해소. 남은 B+4d4·a90 writer와 B+58 총구 기준점 writer, 실제 탄 TOI 5756468 경로. 입력과 시각 총구/충돌까지 원본 순서로 연결 필요 |
| 바닥 도색 | 탄/스플래시 명중→칠 모양→ColPaint 패널/아틀라스→지형 메시 색·발밑 판정 | 2bd00a4→2be50fc→2be2de4→2bed910/2bedb98→_pu writer 연결은7차 일부 실행. 실제 모델/패널 매칭·삼각형 경계와 GPU 표시/샘플 연결이 남음 |
| 그래픽 | 실제 스테이지/캐릭터→재질·셰이더/애니→광원·환경→톤매핑→화면 | Hermit2D 정규 접선은7차 해소. 남은 전체 ColorGrading LUT/GAMMA, 환경 UBO·광원 연결, 캐릭터 조립/_Hlf/애니·머리카락·LOD 잔여. 함수 하나 해소로 렌더링 전체 완료 처리하지 않음 |

주소 표기는 main의 0x710 접두부 생략. 상세 최신 근거와 한계는 [카메라](camera/player_camera.md), [컨트롤러](physics/character_controller.md), [사격](weapon/shooter_bullet.md), [ColPaint](paint/colpaint_atlas.md), [렌더링](graphics/stage_rendering.md) 및 [7차 보고](completion_r7.md)를 따른다. 이 표는 경로 단위 우선순위이며 별도의 확정률 분모에 더하지 않는다.

## 3. 이후 작업 규칙

1. 위 경로의 남은 연결과 근사 구현 차이를 먼저 선택한다. 기존 SHARED/FUNCS/decomp_index 및 최신 본문으로 중복 분석을 피한다.
2. 병렬 담당도 이 다섯 경로 또는 직접 의존하는 판정/표현을 배정한다. 범위 밖 다른 무기·모드·메뉴, 주변 효과·효과음 항목을 우선하지 않는다.
3. 문서에는 원본 주소·식·순서·입출력·실행 경계·실패·다음 근거를 남긴다. 해결한 기록 수보다 어떤 핵심 연결이 이어졌고 무엇이 아직 끊겨 있는지 먼저 보고한다.
4. 웹 코드/impl는 읽기 전용이다. 확정 후 필요한 코드 변경은 감사 표의 웹 반영 열에만 기록한다.

## 4. 현재 판정

다섯 핵심 경로 모두 아직 전체 연결 완료로 선언하지 않는다. [analysis_completion.md](analysis_completion.md)의 확정률은 출처 기록 처리율이다. [실행]/[판독]/[데이터] 근거가 있는 일부 결과를 축적하고 있으며 실제 게임 전체 동작과의 완전 일치는 별도 확인이 필요하다.

정정(2026-10-03): 도색의 초기 다음 후보2b71960/2b71fd8은 새 판독에서 미니맵 생성으로 밝혀졌다. 실제 지형 표시 setupMapModel_는2bd00a4이며 이 표와 ColPaint 본문에 정정했다.


## 5. r8 신규 연결과 남은 핵심 (2026-10-03)

위 §2는 r7 시점 기록으로 보존한다. 현재 고정 inventory의 r8 증가 목표는 모두 충족했고 세부 확정·조사중 상태는 [completion_r8.md](completion_r8.md)를 따른다. 전체 다섯 체감 경로를 모두 실행 완료했다고 해석하지 않는다.

| 경로 | r8에서 새로 이어진 연결 | 계속 남은 핵심 |
|---|---|---|
| 카메라 | 설정입력11B·sixaxis 행렬/각속도 생산, 활성Spectator→포저 LookAt/쉐이크 위치, 감도21단계, 특수 리그 요청 입력 | 실제 device posture/최종 화면의 전체 경로와 아직 남은 복합 질문은 player_camera/shake_rumble 본문·감사 목록 유지 |
| 물리·이동 | game/native 속도·pose 되쓰기, 최초속도→침투target/normal순차행→8normal/7carry→finalize→doubleCOM→native원점·잔차, 이동입력 edge/AP/착지spring 소비 | 실제 Lby 전체 메시·계단·경사 접촉 생성, runtime SplPlayer 모션속성/모든modifier, 탄 TOI(0aec920/0aefdc0) 전체 |
| 사격·피격 | 탄팀 producer·벽낙하 표/helper소유권·소멸 lifecycle, native피격sphere/capsule/owner 연결·bit11 filter·배율 행/명중반응 큐·표적 Main pose | 실제 탄 지형 TOI부터 전체 피드백·남은 상위 writer/전체연출 복합 질문 |
| 바닥 도색 | 실제 모델vertex→panel 매칭·recognizer·그룹/root writer·공유edge 연결과 seam, texture배열 runtime 로더 | 전체 지형 도색 GPU 픽셀·샘플/발밑판정의 남은 복합 연결 |
| 그래픽 | LOD Default→실제7FMDL/mesh/draw 인자, AS 이벤트/진행률/무기 이름, 팀색RSDB 공급, calc roughness/transmission/thickness, Shadow 생성/적용/렌더 소비 부분 | 전체 포즈합성/머리카락·GPU/LUT, Shadow liveconfig19E0/matrix530/factor4E8, L342 전체적용묶음 |

부분 결과는 기존 복합 질문을 전체 확정으로 올리는 데 쓰지 않았다. 새 pending 주소는 각 근거 문서와 완료 표에 연결했으며 신규 질문을 분모에 더하지 않았다.
