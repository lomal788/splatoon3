# mode1 커브 이름·기본값 (2026-10-03 r9)

## 1. 기능 개요

[판독]+[실행]+[데이터] PlayerCamera의 mode1은 잠망경 컴포넌트가 주는 전환 포즈를 따라가는 경로입니다. 위치 추종에는 PlayerFollowRate, 방향 보간에는 CameraAttInterpolateCurve를 씁니다. 기존 CameraModuleParam.Interpolation 추정은 실제 타입·반사 등록과 맞지 않습니다.

## 2. 분석 대상

원본 2355fc4 생성자, 235610c 반사 visitor, 23567c0 복사/방문 보조. 새 디컴파일은 analysis/decomp/r9_camera/periscope_ctor.c 및 periscope_param.c입니다. SHARED/FUNCS/decomp_index에서 미등록을 확인한 뒤 func_lookup으로 시작점을 찾았습니다. 24d9ae8 메인과 23555f0 파라미터 연결, r8 periscope_states.c는 기존 판독을 재사용했습니다. 잠망경 기믹 실제 동작을 추가 구현하는 분석이 아닙니다.

## 3. 진입점·호출 흐름

[판독] 23555f0이 이름 spl__PlayerCameraPeriscopeParam으로 0f5e51c의 타입 파라미터를 찾아 C1970에 연결합니다. 실제 타입 getName=2357354. 기존 266f780/266f918/266fd4c/266feb4 상태에서 24e58fc(C, Periscope+c8)를 호출해 C1878 모드와 C1894 진행 인자, 위치·방향 목표를 복사합니다. C1878==1이면 메인 24d9ae8의 두 커브 reader가 실행됩니다.

## 4. 구조체·필드

P=C1970 파라미터. 각 커브 구조의 +8 Type(u32), +c MaxX(f32), +10 count(u32), +18 data(u64)를 원본으로 확인했습니다.

| 이름 | P 오프셋 | override flag | 생성자 기본값 |
|---|---|---|---|
| YawAngleVelRateStick | d0 | f0 | Hermit [1,0,0.1,-2.9760000705718994], MaxX1 |
| YawAngleVelRateGyro | b0 | f1 | Hermit [1,0,0.1,-2.9757509231567383], MaxX1 |
| PitchAngleVelRateStick | 70 | f2 | Hermit [1,0,0,-3.4091989994049072], MaxX1 |
| PitchAngleVelRateGyro | 50 | f3 | Hermit [1,0,0,-3.4091989994049072], MaxX1 |
| PlayerFollowRate | 90 | f4 | Linear [0.949999988079071,1], MaxX1 |
| CameraAttInterpolateCurve | 30 | f5 | Linear [0,1], MaxX1 |

[실행] 원본 생성자와 반사 visitor가 낸 6개 descriptor 이름·오프셋·default가 모두 일치했습니다. 실제 SplPlayer GPT는 FollowRate 및 Yaw2개를 override합니다. FollowRate=Hermit [0,0,0.10000000149011612,0.1081760972738266], GyroYaw=[1,0,0.009999999776482582,-2.4174070358276367], StickYaw=[1,0,0.009999999776482582,-2.428913116455078]. 나머지는 원본 기본값입니다.

## 5. 상태 전이

진행 인자는 C1894입니다. 기존 문장의 단순 frame라는 이름은 호출자가 넣는 전환 진행 값으로 정정합니다. 구체적인 Off/Extend/View/Shrink 상태 전이는 r8 player_state의 잠망경 분석을 재사용합니다. 여기서는 타입과 커브 연결 질문만 확정합니다.

## 6. 계산식·순서

[판독] 위치: P90 커브의 Type이3보다 작으면 t=C1894/MaxX, 아니면 C1894; 5738610[Type]으로 값을 계산합니다. C1770..78의 현재값 각각에 curve*(target C1898..a0-current)를 더합니다. 방향: P30 CameraAttInterpolateCurve를 같은 정규화 방식으로 평가하고, yaw는1252ff0 각도 보간, 수직 성분은 C18c8+(C18d4-C18c8)*curve입니다. 두 커브를 같은 이름으로 치환하지 않습니다. 커브 수학 함수 자체는 기존 SHARED83의 판독을 재사용했습니다.

## 7. 화면 연결

이 경로는 일반 리그에서 만든 위치·방향을 전환 상태가 덮는 부분입니다. 최종 화면 포저 연결은 r8 player_camera §6.7.3을 재사용하며 이번 실행은 화면 renderer 전체를 실행한 것이 아닙니다.

## 8. 상호작용

각 필드 override flag가0이면 부모 파라미터에서 동일 타입을 따라가다가 실제 override를 찾거나 현재 기본값을 씁니다. 실제 원본 타입을 찾았으므로 메뉴·결과 화면용 CameraModuleParam.Interpolation 커브를 여기에 적용할 근거가 없습니다.

## 9. 웹 반영 필요

impl/camera.md의 mode1 미확정 목록에 두 커브 이름과 실제값을 기록할 수 있습니다. 사격장 스플래시슈터에서 잠망경 동작 자체는 범위 밖이며 웹 구현 코드는 수정하지 않았습니다.

## 10. 검증·명령

web/tools/r9_camera_periscope_param.py → analysis/completion/r9/camera_periscope_param.json. 원본2355fc4 전체 생성자와235610c 전체 visitor를 실행, 6 descriptor 및 6 기본 커브/전체 data 값 일치, mismatches0/fault0/null0/auto-page0. malloc1과 C++ guard7은 경계 스텁, actual typed resource loader는 실행하지 않았습니다. 데이터 값은 추출된 원본 SplPlayer GameParameters에서 읽었습니다. full_decomp.sh로 신규235610c/23567c0 2개 및2355fc4 1개 생성 성공, index6018.

## 11. 미확정·정정 이력

2026-10-03: player_camera 기존 mode1 CameraModuleParam.Interpolation 추정과 frame 이름을 정정. 실제 P=C1970의 타입명과 visitor이름, 원본 소비 오프셋이 확정 근거입니다. 해당 고정 질문 L387은 해소됐습니다. 큰 대체 리그 복합 질문 impl/camera:L95는 다른 리그 상태·필드·공급자를 포함하므로 이 결과로 전체 승격하지 않습니다. 실제 typed BYML loader 실행은 미실시이며 타입 메타데이터/추출값을 가짜 loader 실행으로 표기하지 않았습니다.
