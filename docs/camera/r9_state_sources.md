# 카메라 상태 공급자 (2026-10-03 r9)

## 1. 기능 개요

[판독]+[실행]+[데이터] 오징어 리그의 전역 모드와 수직 추종의 속도 비율 정의를 확정합니다. 카메라가 읽는 B9210/9212 등의 콜백 writer도 찾았으나 실제 이벤트 상황 연결은 §11에서 계속 조사합니다.

## 2. 분석 대상

신규 원본 판독 2643cd4, 24cb3ec, 24cbca8은 analysis/decomp/r9_camera/player_camera_flags.c에 저장했습니다. 기존 gsetting.c의 2b5662c..566e4, 메인24d9ae8의24dd9ec..dda08은 기존 디컴파일을 재사용하고 해당 미확정 구간을 새 실행했습니다. SHARED/FUNCS/index를 확인했으며 기존 이동 속도/벽 점프 정의는 새 성과로 세지 않습니다.

## 3. 진입점·호출 흐름

[판독] 2b582d0의2b58dc0..ddc 정적 등록은 태그 캐시58e9270의 이름=Scene_Coop입니다. gsetting2b5662c..566e4는 해당 태그와 sceneName==LobbyCoop를 OR하여58e87cc에 씁니다. 플레이어 전역 관리 객체의 슬롯2643cd4는 G143d0에58e87cc를 복사하며 sceneName==LobbyLocal && (*58e42f8).c8.6538.34==2이면1로 올립니다. 따라서 G143d0은 코옵 태그/코옵 로비 및 Local 종류2의 모드 판정입니다. 본문에서 원본 필드 번호를 보존하고 Local 종류2의 UI 이름을 임의로 붙이지 않습니다.

## 4. 구조체·필드

| 필드 | 원본 공급자·정의 |
|---|---|
| 58e87cc | Scene_Coop 태그 또는 LobbyCoop 이름 |
| G143d0 | 위 byte 복사, LobbyLocal 설정+34==2면1 |
| B73c | 기존 player/movement_physics §6.3/6.7의 일반 점프·중력 수직 속도 |
| B754 | 기존 movement §6.8.3의 벽 점프 차지 수직 임펄스 |
| 58bbc60 | 기존 원본 상수 Jump初速 f32 0.11499999463558197 |
| C1518 | 수직 주시점 추종 비율 캐시 |

G=*5791bd0(주소 값은580e340). 실제 ctor264b8d8의264b924가 VT563d530을 쓰며 +28 슬롯(pointer563d558)=2643cd4입니다. singleton264bb38이580e340에 자신을 저장합니다. 별도 설정 객체 *58e42f8(기존 SplSceneSetting)에서 Local 값을 읽습니다. 2026-10-03 추가 정정: 두 전역을 같은 객체로 부른 기록을 철회하며 G의 고수준 class명은 이 근거에서 단정하지 않습니다.

## 5. 상태 전이

G143d0은 설정 갱신 시 쓰이는 byte입니다. 프레임마다 입력 크기에서 결정하는 값이 아닙니다. 실제 Tag.Product.100 자료의 LobbyVersus 행4272에는 Scene_Coop가 없고 sceneFlag0이므로 사격장 로비의 해당 오징어 리그 분기는0입니다. LobbyCoop 행4270은 태그가 없어도 이름 검사로1입니다. Local 행4271은 설정 종류2일 때만1입니다.

## 6. 계산식·순서

[판독]+[실행] 수직 비율은 `r=min(f32(f32(B73c+B754)/Jump初速),1)`입니다. 이전 C(+e8) 표기는 C=카메라처럼 보이지만 실제 X28은 원본 상수 블록58bbb78이며+e8=58bbc60입니다. 하한은 이 나눗셈에 없고 이후 r<=-1 분기에서 목표rate0.7을 고릅니다. r=0은0.25, -1<r<0은 f32(r*f32(-.45)+.25). 양의 r은 원문 §6.6의 표면법선/기본·Jetpack 점프·벽 점프 플래그에 따라 보정됩니다. x/z는 리그값을 즉시 쓰고 y 주시점을 캐시rate로 따라간 뒤 동일 높이 차를 camera y에서도 뺍니다.

기존 movement 정의와 새 카메라 reader를 연결했으므로 73c/754의 의미를 미정의 수직 속도 추정으로 남기던 camera_feel L29 질문은 해소합니다. 큰 플래그 묶음 L439는9210/9212 등의 상황이 남아 일괄 확정하지 않습니다.

## 7. 화면 연결

비율은 일반 리그의 atY 추종에 사용합니다. 사망 수신·잠망경·특수 상태는 각 분기에서 비율 또는 pose를 바꿉니다. 이번 실행은 새 ratio writer/consumer와 scene 판정이며 전체 프레임 화면을 실행하지 않았습니다.

## 8. 상호작용

[판독] B744는 Jetpack 공중 점프 조건, B782는 벽 차지 점프 후 유지 가산 차단입니다(기존 movement 문서 재사용). 웹 impl/camera의 DashPanel로 붙인 B744 이름은 원본 점프 writer와 맞지 않습니다. 이 발견만으로 모든 특수 비율 복합 질문을 확정하지는 않습니다.

## 9. 웹 반영 필요

impl/camera.md: 수직 ratio의 분모를 원본 Jump初速0.115로 기록하고 일반/벽 차지 수직 성분 합계를 입력합니다. G143d0는 코옵/Local 종류2 조건으로 오징어 곡선 상수를 선택합니다. B744를 DashPanel로 부른 부분은 Jetpack 공중 점프 플래그와 대조해야 합니다. 코드와 impl은 수정하지 않았습니다.

## 10. 실제 검증·명령

web/tools/r9_camera_scene_ratio_emu.py → analysis/completion/r9/camera_scene_ratio_emu.json. 원본 scene 태그 predicate113행, G143d0 writer452조합, ratio4096사례 비트 일치. mismatches0/fault0/null0/auto-page0. Scene 객체 공급1323040만452회 경계 스텁, actual RSDB tag bit table를 사용했습니다. tag 이름 검색기/이전 이동 정의는 기존 실행 근거를 재사용했습니다. 새 full_decomp3함수 성공, 최초 add 즉치 기반 field scan은0건이며 MOV 레지스터 오프셋 검색으로 writer를 찾았습니다.

## 11. 미확정·다음 근거

- B9210/9214: 원본24cb3ec가1을 씁니다. B9212:24cbca8 leaf가1을 씁니다. Player 생성 콜백 등록PC245800c/2458184에서 callback 주소·typed token58bc348을 확인했으나 이벤트 발행 측의 상황 정의는 아직 미확정. 다음1e9f5e4/1ea4bd8 token58bc348 참조와 실제 콜백 dispatch.
- B9314 생산자는 MOV offset9314만 검색해서 찾지 못했습니다. 큰 필드의 분리된 주소 생성/구조체 복사 경로가 필요합니다. 다음 B9300 주변 구조를 설정하는24cb.. 또는23547bc/reset.
- 수직 특수 비율 전체 상태 질문은 다른 분기 predicates의 정체를 포함하므로 이 비율 실행4096으로 전체를 승격하지 않습니다.
- 2026-10-03 정정: 기존 수직 변수 의미 추정, 분모를 카메라 C+e8로 읽는 혼동 및 오징어 G143d0 의미를 위 새 writer/reader에 따라 정정하며 이전 문장은 보존했습니다.
