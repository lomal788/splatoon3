# 9차 카메라 붐: 실제 구 캐스트와 위치 쓰기 조건

## 1. 결론

2026-10-03 [실행]+[판독]: 원본 카메라 factory가 만든 반경0.3 구를 실제 nativeWorld broadphase에서 캡슐로 캐스트하여 적중 비율과 거리를 확인했습니다. 필터 없는 기하 fixture의 실행 성공을 실제 사격장 필터 완료로 확대하지 않습니다. 필터를 붙인 실행에서는 생성 직후 카메라 질의 마스크가0인 이유로 후보가 제외되며 활성 마스크 공급은 아직 미확정입니다.

본체B+de0>=1의 위치 출처 질문은 해소합니다. 이 조건은 새 위치를 고르는 분기가 아니라 **붐 위치 쓰기를 생략하여 현재 `*(C+60)` 세 좌표를 보존하는 분기**입니다. 그 뒤 C1760 보간 및 최종 보정은 계속 수행합니다.

## 2. 분석 대상

기분석 SHARED/FUNCS/index를 확인하고 r5의 형상·반경, r7의 거리 비율, r8의 월드 코덱·필터 배치를 재사용했습니다. 신규 추적은 nativeWorld vt+3f8의 실제 함수0a492e8, BroadPhase vt+d0의0adb134 및 원본 factory부터 실제 질의까지의 연결입니다. 24dee54..24def74와24df060..24df0fc는 아직 실행 검증되지 않았던 위치 쓰기/후속 혼합 구간을 새로 실행했습니다.

## 3. 진입점과 호출 흐름

[판독]+[실행] `24d5c6c → 3a62e78(query meta) → 3a72e1c → 3c27ae4 → 092efbc(sphere)`로 C1978와 내장Q=C1d0를 실제 생성합니다. Q VT559ad88+28=3c37768. 메인24d9ae8은 Q 시작/끝을 쓰고 Qf8|=c 뒤3a5f36c를 호출합니다. 새 실행 연결은 `3a5f36c → 3c37768 → W vt545e460+3f8=0a492e8 → BroadPhase vt+d0=0adb134 → 09af088 → 0947aec → 0948f30`입니다. 0a492e8는 profiler/TLS 준비 뒤 BroadPhase에 질의를 넘깁니다. 단일 closest 결과는3c37768 안의 변환 경로를 타므로 별도3c37498을 실제 호출했다고 기록하지 않습니다.

## 4. 구조체와 필드

| 필드 | 의미·확정 범위 |
|---|---|
| Q8 | 실제 hknpSphereShape 래퍼, 생성값 반경0.3 |
| Q60=C230 | C2d8의 질의 필터 데이터 |
| WBc0 | actual nativeWorld |
| WBd0 | WorldShapeTagCodec VT5755ee8, +40=RET3c49f00(기존 r8 판독 재사용) |
| WB110 | Entity CollisionFilterBackEnd VT5756560, provider+20 |
| CF8 | 엔진 결과 staging source. E20가 아닙니다 |
| Q50/Q54 | 적중 비율/이 비율에 cast 길이를 곱한 거리 |
| C60 | 생성 때 C30를 가리키는 위치 출력 포인터 |
| C1770..78 | 이번 프레임의 제한 전 native camera position |
| C1760 | 붐 결과 이후 native position/at 쪽으로 섞는 가중치 |

## 5. 상태 전이

원본 factory만 실행한 Q 필터의 +8=1, +c=0, +10=FFFFFFFF, +18=FFFFFFFFFFFFFFFF, +28=1입니다. 실제 Entity 필터와 원본 provider3b1ab5c를 붙인 fixture는 broad 후보에서3c56f80(kind2)→3b19dd4→3b1a114로 갑니다. 마지막3b1a264..26c의 queryMask(+c) bit 검사에서0을 읽어 거절합니다. 마스크를 근거 없는 정상값으로 채워 성공 처리하지 않았습니다. provider ctor 자체는 원본0x310 객체/테이블과 내부 backend를 생성했습니다.

## 6. 계산식과 순서

[실행] 필터NULL인 기하 fixture: 구 반경0.3, 캡슐 반경0.6·끝점(0,-1,0)/(0,1,0), 시작(2,0,0), 끝(-2,0,0), identity 회전입니다. native 비율의 비트=3e8ccccc, Q54=3f8ccccc(1.0999999046325684). 독립 축 정렬 기하 계산 `f32(f32(2-f32(.3+.6))/4)` 및 그 값에4를 곱한 결과와 비트가 같습니다.

[판독]+[실행] 24dee54..24def74는 signed Bde0>0이면24def5c로 건너뜁니다. 이때 C60 출력 xyz를 전혀 쓰지 않으며 C177c의 at 세 좌표만 C70..78로 복사합니다. <=0이면 `len=f32(C14c4*C14cc)` 후 각각 `pos_i=f32(pivot_i+f32(dir_i*len))`을 쓰고 원문의 수직 보정을 적용합니다. 이후24df060..24df0fc는 두 경우 모두 `pos_i=f32(pos_i+f32(C1760*f32(native_i-pos_i)))`와 at의 같은 보간을 수행합니다. 따라서 de0 분기에서 native position으로 자동 교체한다는 해석은 틀립니다.

## 7. 화면 연결

기본 붐 경로에서 이 블록에 진입한 출력은 현재 C60가 가리키는 기존 출력입니다. 제약 전 위치 C1770는 별도의 이번 프레임 계산값이며 생략 분기 자체는 이를 복사하지 않습니다. C1760=0이면 보존, 1이면 후속 혼합이 native position으로 옮깁니다. 메인의 다른 분기24dd370..398은 native position/at를 바로 출력에 복사하고, 사망 수신·special 등의 경로는 각 원본 분기에서 선택합니다. 생략 조건만 보고 모든 상태의 위치를 이전 프레임이라고 단정하지 않습니다. 이후0.16 근접 보정·포저는 기존 본문 §6.7을 따릅니다.

## 8. 다른 시스템과 상호작용

native 캡슐 body와 broadphase 등록은 실제09e64f8→09c78f0→09c6a70으로 생성합니다. userdata의 Phive typed CharacterMatterRigidBody/래퍼 및 staging은 합성 입력입니다. native query 수학을 스텁하지 않았습니다. 원본 Lby_Lobby00 지형TAG0의 broadphase 질의, 액터 순서 전체 및 실제 게임 프레임은 이 fixture로 실행하지 않았습니다. 필터 표·지형 shapeTag 규칙은 gimmick/collision_mesh §3.4.3의 기존 원본 근거를 재사용합니다.

## 9. 웹 반영 필요

impl/camera의 붐 반경0.2는 기존 원본0.3과 다릅니다. Ground 단일 마스크로 원본 필터를 완전히 재현했다고 표기할 근거는 아직 없습니다. 위치 생략은 출력 xyz 보존→C1760 후속 혼합 순서를 유지해야 합니다. 코드와 impl은 수정하지 않았습니다.

## 10. 실제 검증과 명령

- r9_camera_boom_probe.py: 원본 factory·구/캡슐 backend·native broad cast 1기하 사례 성공, 비율/거리의 독립 비트 일치. null/auto/fault0. OS TLS·mutex·clock·allocation 경계는 하네스 처리입니다.
- r9_camera_boom_filter_probe.py: 원본 filter/provider/codec를 붙인 broad 후보 제외를 확인, null/auto/fault0. geometry 진입 전에 거절됨을 성공 적중으로 처리하지 않습니다.
- r9_camera_boom_gate_emu.py: 2048사례(생략1024·위치 적용1024), gate xyz/at 및 후속 blend 총24576f32 독립 비트 불일치0, null/auto/fault/PLT0.
- full_decomp native_boom_cast.c 2함수 및 native_broad_filter.c 2함수 성공; provider3b1ab5c/3b19ca0 신규2함수 성공,3c56f80은 기존 파일을 재사용.

최초 no-staging fixture는 native collector에 적중했으나 Q50=-1/Q54=0으로 남았습니다. CF8 staging을 명시하여 원본 결과 변환이 실행되게 했습니다. 이는 기하 miss와 구분됩니다. 회전 배열12float를9float로 정정했고, 최초 patch의 IndentationError를 수정했습니다. GetContent의 미존재 후보 파일 및 Windows rg wildcard 오류, disasm.py의 -n 누락, 재고 출력 Python unmatched ')'와 cp949 출력 실패도 commands.md에 보존합니다.

## 11. 미확정과 다음 근거

- 실제 camera Q 필터+c 마스크 생산자 및 활성 게임 상황은 미확정. 원본 생성자는0을 쓰고 main24d9ae8에는 직접C2e4 쓰기가 보이지 않습니다. 다음: PlayerCamera 초기화/등록 호출자와 Q 필터 데이터 alias writer·query init callback. 값FFFFFFFF 주입으로 덮어 확정하지 않습니다.
- Lby_Lobby00 실제 지형 broadphase/filter/shapeTag까지 연결한 whole query는 아직 미실행. 다음: 기존 실제 TAG0 material-leaf fixture의 mesh를 native body로 등록하고 World entity backend와 query layer mask writer를 연결.
- L352/L443/camera_feelL30/implL91/L105/L114는 질문에 실제 필터 또는 전체 질의를 포함하므로 조사중 유지합니다. 현재 신규 geometry 증거만으로 전체 질문을 승격하지 않습니다.
- 2026-10-03 정정: World d0를 충돌 필터,110을 codec로 부른 기존 혼동은 위 실제 클래스 배치로 정정합니다. 기존 결론을 삭제하지 않고 이 정정에 연결합니다.


### 3.1 활성 필터의 실제 reset 생산자 — 정정(2026-10-03)

[판독]+[실행] §1/§5/§11의 '활성 마스크 producer 미확정'은**24d6598 reset의24d6d94..24d6dc8**로해소합니다. 원본이 `C2e0=(C2e0&FFFFFFC0)|7`, `C2e4=8`을씁니다. C2d8=Q60 필터객체이므로 F8 layer7=SplCamera, Fc mask8=Ground(bit3)입니다. 앞선factory-only의F8=1/Fc=0은reset전상태였습니다. 기존문장을남기고실제호출단계차이로정정합니다.

world21c runtime=.01은**기존r5**344af54 caseF→3dad17c→3db346c→3ac71c8사슬12/12실행근거(SHARED390,phive_controller§6.4)를재사용합니다. 반경=max(.01,.3)=.3입니다. 새로운config값으로계상하지않습니다.

### 6.1 필터 계약·실제 native 적중·법선 선택

[판독]+[실행] 새로운r9_camera_boom_active_filter_probe.py는factory다음**원본reset필터store구간**을실행해7/8을만든뒤original3a5f36c→EntityfilterVT5756560→3c56f80(kind2)→3b19dd4→3b1a00c→기존3b19308→nativeBroadPhase/09af088/0947aec/0948f30까지실행합니다. 명시적Ground3·targetmaskFFFFFFFF의합성캡슐에서hit1,frac3e8ccccc,distance3f8ccccc로독립기하식과비트일치합니다. 초기동일Ground입력전label0(NoHit)fixture는정상거절됐습니다. 임의camera querymask로성공시킨것이아니며원본writer를실행했습니다.

[판독] query_body_filter.c 신규3b19dd4/3b1a00c/3b1a114는typed shape allow masks(b8/bc),targetLPgetter vt90,query f8bit5예외,skip목록 및양방향layer/subLayer표조건을보존합니다. 실제활성F는CustomReceiver1전용3b1a114대신일반3b1a00c→3b19308로갑니다. provider Default/Same/Other선택·양방향Fc·F10조건은기존r8body_pair_permission과character_controller§3.3.2를재사용합니다. 따라서**'Ground레이어하나로모든지형태그를무시'하는근사는원본과다릅니다.** Ground후보에서상대mask가SplCamera(bit7)를허용하고표/태그·typed shape필터도허용해야통과합니다.

[판독]+[실행:iterator] 적중후C318 listener에실제point목록이생기며원본12d8dcc를**x0=listener,x8=hidden-return** ABI로실행했습니다. 첫point+0c법선=(1,0,0),entry+8bit0=1입니다. 메인24dddd0..24dde04는이bit가1이면pointN그대로,0이면−pointN을사용합니다. 웹의항상법선반전은이조건을보존해야합니다. Q40의(0,0,1)기본벡터를적중법선으로오해하지않습니다.

### 10.1 추가 실제 명령·결과

- `.venv/Scripts/python.exe web/tools/r9_camera_boom_active_filter_probe.py`:원본filterwriter7/8→실제broadcast→iterator,hit1·거리비트일치, null/auto/fault0. allocator/TLS/mutex/clock은기존nativeharness경계;metadata/world-bodylabel/mask는명시입력.
- `full_decomp.sh .../query_body_filter.c 0x7103b19dd4 0x7103b1a00c 0x7103b1a114`:신규3함수성공. func_lookup앞두개는선행3b19ca0로잘못표시해실제prologue판독후디컴파일.
- 실패:camera/cam_main_full.c미존재(실제다른폴더파일재사용), JSON기본cp949UnicodeDecodeError→utf8로수정. 초기activeprobe의targetlabel0거절은입력대상NoHit이므로geometrymiss와구분;Ground3명시후성공.

### 11.1 현재 whole 질문 경계

L352/implL114의**형상·반경·질의filter계약**은원본Sphere/.3/생산7·8/consumer분기·태그및상대허용조건으로해소합니다. 실제stage전체를원본실행했다는뜻이아닙니다. 더큰L443/camera_feelL30/implL91/L105는기존원본산술·이번활성질의근거를모두연결하되**실제Lby_Lobby00 FieldRigidBody concreteVT/태그필터를붙인mesh broad-query 및전체프레임**까지연결하지못해조사중으로유지합니다. 다음:실제Fld_VSLobby body 생성·typed vt90 LayerProperty공급→nativeuserdata98,realTAG0/Hnative부착→query. 기본abstractVT5749048의nullFgetter를실제지형으로대체한척하지않습니다.
