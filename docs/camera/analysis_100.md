# 사격장 카메라 100% 목표 — 고정 목록·원본 근거·잔여 (r10)

갱신: 2026-10-03. 대상: Splatoon 3 v0, Lby_Lobby00 1인 연습. **100% 목표는 아직 달성하지 않았다.** 사용자 요청 “여기까지하고 md파일 업데이트해줘”에 따라 추가 분석을 중단하고 현재 원본 근거를 정리했다.

## 1. 기능 개요와 체감 우선순위

제자리 시점 입력, 이동 중 추종, 벽 접근, 사람/오징어 리그, 발사·명중 피드백과 화면 출력 연결을 먼저 조사한다. 이번 요청은 원본 분석과 MD 반영이다. 웹 코드·에셋·impl은 수정하지 않았다. 마우스의 px 입력 정책은 원본 패드 입력과 구분한다.

## 2. 원본·범위·고정 기준

원본 v0 명령은 `extracted/exefs/main.reloc.img`, SDK 명령은 `extracted/exefs/sdk.img`, 지형은 원본에서 추출한 Fld_VSLobby bphsh를 읽었다. 모든 작업 파일은 `C:/dev/splatoon3` 안에 저장했다. `original/`은 읽기 전용이며 키 값은 복사하지 않았다.

기준은 r10 시작 직전 [전체 감사 목록](../analysis_completion.md)에서 동결한 카메라 **106개**, 전체 **986개**다. `analysis/camera_100_r10/baseline_inventory.json`에 원문·카메라 순번·SHA256를 보존했다. 질문의 문구·분모를 바꾸거나 질문을 잘라 확정수를 늘리지 않는다. 이 문서의 순번은 그 JSON의 카메라 내부 ordinal이다.

## 3. 호출 흐름과 조사 분담

```text
Save/Controller → PlayerInput → body stick/gyro flags
→ PlayerCamera input: snap/bias/yaw/pitch
→ body state/rig/follow/normal → boom sphere query → output pose
→ Spectator/active poser → CameraModule → LookAt/Perspective/device transform
→ gsys View → Context UBO View0..2/Projection7..10 → shader gl_Position
ELink name/condition → shake instance → world-position addition
model Fade helper → fade manager/variant → named material or model alpha
```

입력·투영/시작 연결, 상태 생산자, 쉐이크/ELink, 실제 지형 붐/Fade를 병렬로 조사했다. 새 판독 전 SHARED/FUNCS/decomp_index를 조회하고 기존 C·실행 결과를 재사용했다. 공유 목록·notes·목차는 부모가 검토한 뒤 반영했다.

## 4. 확정률·구조체 계약·집계

| 기준 | 확정 | 잔여 | 원본 근거 확정률 |
|---|---:|---:|---:|
| r10 시작 동결 | 78/106 | 28 | 73.58% |
| 현재 검토 반영 | 93/106 | 13 | 87.74% |

증가 **+15개 / +14.15%p**. 그중 신규 원본 근거로 해소한 행은 **13개**, 이미 해소된 근거의 문서 판정 정정은 **2개**다. 후자는 신규 분석 성과에 합치지 않는다. 전체 고정 목록은 **571/986=57.91%**다. 비율은 문서 질문의 처리율이며 원본 화면 유사도·웹 완성도 비율이 아니다.

주요 새 필드 계약: C188은 저장 하한−1과 pow 지수 하한0을 구분한다. M140은 viewport 공급 때만1로 쓰는 래치다. S=B92f8의 active/position/forward는 요청·ActorRef와 분리한다. Bdf0/Bdf4는 WaterFall 타이머/높이 래치다. user+B8은 SubjectiveType의 값이 아니라 property index metadata다. 각 타입·연산 순서는 아래 근거 문서 §4~6에 기록했다.

## 5. 상태 전이와 해소한 고정 질문

| 순번 | 항목 | 확정 수준 | 근거 | 새 근거/기존 정정 |
|---:|---|---|---|---|
| 2 | BNVIB 해석·활성 포저·쉐이크 연결 | [실행]+[판독]+[데이터] | [camera/r10_shake_shooter.md](r10_shake_shooter.md) §3~11 | 기존 해소 정정(새 수명 검증 별도) |
| 6 | 대체 리그 조건의 두 타입 이름 | [판독]+[데이터] | [camera/r10_state_producers.md](r10_state_producers.md) §6.5/11 | 새 근거 |
| 10 | B65c 보편 번호식과 전체 생산자 | [판독]+[데이터]+[실행:분류구간] | [camera/r10_state_producers.md](r10_state_producers.md) §6.8/10/11 | 새 근거 |
| 11 | Pipeline·C1918 실제 상황 | [판독]+[데이터]+[실행:receiver/queue/FSM 구간] | [camera/r10_state_producers.md](r10_state_producers.md) §6.11/10/11 | 새 근거 |
| 14 | 물체 Fade helper·파라미터 관계 | [판독]+[데이터]+[실행:temporal/type1/type2/cache] | [camera/r10_boom_stage_fade.md](r10_boom_stage_fade.md) §3.2/6/7/10/11 | 새 근거 |
| 16 | 시작 리셋 상위 호출·모듈 포즈 생산자 | [판독]+[실행] | [camera/r10_module_projection.md](r10_module_projection.md) §3~11 | 새 근거 |
| 19 | 수몰 높이·타이머의 카메라 소비 | [판독]+[실행]+[데이터:기존이름] | [camera/r10_state_producers.md](r10_state_producers.md) §3~11 | 새 근거 |
| 20 | Dokan t≤.4 자동 yaw 분기 | [판독]+[실행:기존r8] | [camera/player_camera.md](player_camera.md) §7.2 및 [camera/r10_state_producers.md](r10_state_producers.md) §8/11 | 기존 해소 정정 |
| 21 | 9210/12 등 본체 상태 필드 의미 | [판독]+[데이터]+[실행:기존 수직·spring·stick 재사용] | [camera/r10_state_producers.md](r10_state_producers.md) §6.7/10/11 | 새 근거 |
| 22 | Pipeline·Dokan·C1918 상황 조합 | [판독]+[데이터]+[실행:receiver/queue/FSM 구간] | [camera/r10_state_producers.md](r10_state_producers.md) §6.11/10/11 | 새 근거 |
| 25 | 슈터 직접·가상 진동 시작 경로 | [판독]+[데이터]+[실행:actual voice/handle] | [camera/r10_shake_shooter.md](r10_shake_shooter.md) §8.3/8.4/10/11 | 새 근거 |
| 26 | Focused의 실제 선택 시점 조건 | [실행]+[판독]+[데이터] | [camera/r10_shake_shooter.md](r10_shake_shooter.md) §4.2/7/10/11 | 새 근거 |
| 27 | 자기 슈터 탄 명중의 진동·쉐이크 | [판독]+[데이터] | [camera/r10_shake_shooter.md](r10_shake_shooter.md) §3/7/11 | 새 근거 |
| 28 | 발사·표적 명중 피드백 | [실행]+[판독]+[데이터] | [camera/r10_shake_shooter.md](r10_shake_shooter.md) §3~11 | 새 근거 |
| 30 | 스틱 Y 속도·누적 피치각 | [판독]+[실행] | [camera/r10_input_response.md](r10_input_response.md) §3~11 | 새 근거 |

쉐이크는 현재 프레임 계산→루프 owner 검사→카운터 증가→루프 reset→종료 필터→월드 위치 합산 순서다. 마지막 계산 샘플이 곧 최종 합산 샘플이라는 해석은 틀렸다. Focused는 접미사 대신 원본 선택 시점/팀 분류와 ancestor Switch를 소비한다. WaterFall은 followpoint 높이차를 표면 법선 목표에 더하며 camera Y를 즉시 올리는 식이 아니다.

## 6. 계산식·상수·순서의 새 근거

| 문서 | 새로 확인한 원본 계약 |
|---|---|
| [스틱 입력](r10_input_response.md) §4~6 | .2 delta 필터·대각 계수·C188 하한/지수·스냅 뒤 길이 복구, yaw/pitch f32 묶음과 상수 비트 |
| [모듈·투영](r10_module_projection.md) §3~6 | 시작 VT 연결·Pose 복사 범위·M140/150 생산자·행렬 뒤 aspect 저장·device posture 0..5 식 |
| [상태 생산자](r10_state_producers.md) §4~6 | 실제 affine 입력·whole blocked predicate·Water contact→normal·Gate/Mission 요청·typed flag·19타입 분류·Demo producer·VehicleSpectacle cockpit→typed ActorRef/queue/FSM→C1918; 입력 차단과 자동복귀 조건 구분 |
| [렌더·UBO·출력](r10_render_projection.md) §3~6 | logical Projection 소비·Context34멤버2336B·current/previous View·viewport integer conversion·compiled submit/present·original SDK packet. 최종GPU는 미확정 |
| [쉐이크·슈터](r10_shake_shooter.md) §4~8 | isLooped/isFinished 식·curve*(gain*Scale)·serial/slot 재사용·ELink 원본 이름 조건·Focused 값 writer |
| [실제 지형·Fade](r10_boom_stage_fade.md) §3~7 | actual Default helper/config→비마스크·LP·RSDB·Banc→mesh TOI/최근접·법선, 등록queue의 sameworld·Actor dispatcher 조건 연결. 최초Actor pose→native 적용 잔여. Fade actual named material sink |
| [사격 자세 타이머](r10_posture_timer.md) §3~6 | Bad0 발사 후 하한82·입력 활성 술어·공중4부터 감소 우회·메인 stackbyte×4 하한·actualGrindRail 선행 가상조건 정정; 전체 상태/프레임 미확정 |

원본 소수 약칭과 실제 f32 비트를 구분한다. 수학적으로 같은 식도 묶음/원본 SDK 구현이 다르면 마지막 비트가 달라질 수 있다. 이 차이는 가독성을 이유로 다른 계산식으로 대체하지 않았다.

## 7. 화면·이펙트·에셋 연결

스플래시슈터 ID40의 원본 extraSet은 비었고 일반/critical17 모두 Shooter 행을 선택한다. 일반 발사·표적·선택된 HitEffect 키의 Camera/Ctrl 이름 공백을 원본 admission과 함께 확인했다. 이것을 총구 이펙트·사운드·탄 spread 자체가 없다는 결론으로 확대하지 않는다.

helper가 쓰는 실제 material 이름은 `fade_dither_alpha`다. 옛 문장의 “잉크레일” 값1/.1/.5/30은 실제 `spl__GrindRailParam` 소유이며 common Fade helper의 직접 입력이 아니다. helper의 actual supplier는 별도 `game__gfx__FadeOutCameraXluParam`이다. 모든 variant/실제 shader dither/GPU 출력은 아직 검증 경계 밖이다.

## 8. 다른 기능·전체 프레임 경계

입력/상태/포저/Module의 각각 확인된 연결과 실제 사격장 전체 tick는 다르다. fixture 액터·컴포넌트·contact·posture·profile virtual 입력을 원본의 실시간 관측값으로 부르지 않는다. SDK math는 원본 명령을 실행했지만 allocator/lock·capture 경계가 남는 도구는 각 문서 §10에 구별했다. 타입 이름 판독 때문에 다른 무기/스페셜 실제 동작을 새로 분석하지 않았다. Demo CanControlCamera는 메시지 기본값0과 component 초기값1을 구분한다. 피치 자동복귀는 whole blocked predicate와 별도 조건이며 Demo Time을 자동복귀 guard에 임의로 더하지 않는다.

## 9. 웹 반영 필요 우선순위

| 순서 | 구현 기록 | 원본 근거로 바꿔야 할 계약 |
|---:|---|---|
| 1 | ../impl/camera.md·입력 소비 | C188 저장−1/지수0·스냅 길이 복구·상수 비트·FOV 곱·pitch 누적. 마우스 매핑은 별도 정책 유지 |
| 2 | ../impl/camera.md·리셋/포즈/렌더 | 시작 slot15·M140/150·Pose 복사·aspect 후행 저장. 일반UBO는 logical Projection/Context7..10, View0..2;device 행렬과 viewport 반전을 혼용하지 않음 |
| 3 | ../impl/camera.md·발사/피드백 | 일반 발사/명중의 nonempty rumble 이름 조건; 흔들림 gain 묶음·owner 수명·serial/끝 샘플 필터 |
| 4 | ../impl/camera.md·상태/추종 | whole blocked predicate, S request/active 수명, Water contact 래치→surface-normal 보정. 실제 supplier 미연결 값은 임의 활성화하지 않음 |
| 5 | ../impl/camera.md·충돌 | 원본반경.3/query7/mask8·Default1fffffff/07ffffff·Ground/Ground·RSDBbit28→LayerPair/query wrapper. entrybit1은normal유지/0만FNEG;등록dispatcher는연결,최초pose 끝writer 잔여 |
| 6 | ../impl/camera.md·모델 렌더 | 별도 FadeType 모델 metadata→count/alpha/cache→fade_dither_alpha; GrindRail owner 분리. GPU dither 검증 필요 |

위 표는 r10 분석 종료 당시 이식 필요 계약이다. **2026-10-04 후속:** 사용자 웹 반영 지시로 입력/피치·logical투영·상태 소비·쉐이크를 적용했다. [적용·실행경계·실제공급자 잔여](../port/camera_r10.md). 원본분석93/106과잔여13질문은변경하지 않았다.

## 10. 실제 명령·원본 실행 결과·실패

| 명령 (`C:/dev/splatoon3`에서 실행) | 검사 수/결과 | 실행 경계 |
|---|---|---|
| python -X utf8 web/tools/r10_camera_input_emu.py | 12,288 / 비트 불일치0 | native 네 입력 구간, SDK libm 원본; 합성 pre-block |
| python -X utf8 web/tools/r10_camera_input_chain_probe.py | 16 연결 관측 / null·fault0 | 독립 참조식 검사 수에 더하지 않음; gyro 후단/whole frame 제외 |
| python -X utf8 web/tools/r10_camera_module_emu.py | device4096/65,536float·Module1024/46,080float, context256/latch128시퀀스 모두0불일치 | 합성 pose/posture·identity quaternion·noShake; 전체 장치 화면 제외 |
| python -X utf8 web/tools/r10_camera_start_dispatch_emu.py | 1,024 / 전달·래치·순서 일치 | 실제 bridge/slot15; signal/setup capture, 빈 component list |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_state_emu.py·r10_camera_state_water_emu.py·r10_camera_state_request_emu.py·r10_camera_state_classifier_emu.py·r10_camera_state_demo_emu.py·r10_camera_state_next_vehicle_emu.py | 6,071+288=6,359 / 비트·반환 불일치0 | 새Vehicle whole receiver192/queue→FSM callback 직전96·actualSDK memset;유효ref thread/물리callback·전체script/scene 미실행 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_posture_emu.py·r10_camera_shake_ubo_emu.py·r10_camera_shake_viewport_emu.py·r10_camera_shake_sdk_nvn_emu.py·r10_camera_shake_next_frame_emu.py | 1,042+64=1,106 / 불일치0 | logical renderer/Context/compiled present/SDK packet와actual ctor32/target bind32;clock·texture transition·NVN capture/할당경계,GPU최종화면 미검증 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_shake_emu.py·r10_camera_shake_focused_emu.py·r10_camera_shake_voice_emu.py | 4,424+996+666=6,086 / 불일치0 | 원본 lifetime·admission·Focused/actual voice VT; getters/SDK 입력·호출capture/queue 경계 분리 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_boom_mesh_query.py --authored·r10_camera_boom_mesh_verify.py --authored | 초기실제 mask 면8 / 40float 비트 불일치0 | actual raw Default→Entity/TAG0 mesh; 초기비마스크/world/frame fixture |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_boom_mesh_query.py --actor-source·r10_camera_boom_mesh_verify.py --actor-source | 최종16 / 128f32 비트 불일치0 | 실제helper/config/비마스크/Banc/태그→원본TAG0 최근접,create-info→body와holderadapter;slot68dispatcher/초기pose writer 미연결 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_boom_entity_mask_verify.py·r10_camera_boom_actor_source.py·r10_camera_boom_banc_source.py·r10_camera_boom_source_contract.py | mask353/2118u32·tag889·Banc15f32·normal128/384f32 각각불일치0 | 원본reader/typed membership/parser/SDK matrix/Defaultfactory/camera entrynormal 구간; 서로다른검증을전체scene검증으로합산하지않음 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_timer_emu.py·r10_camera_posture_active_emu.py·r10_camera_posture_main_floor_emu.py·r10_camera_posture_grind_gate_emu.py | 10,752+4,096=14,848 / 술어·정수 불일치0 | 새actualPlayerGrindRailVT pre-gate4096;옛keyweapon 명칭정정. getter이후·나머지선행반환/stackbyte 공급·부분 실행 |
| .venv/Scripts/python.exe -X utf8 web/tools/r10_camera_boom_fade_emu.py | 22,288 / 불일치0 | temporal/type1/type2/cache; model-null cache는 upload 실행 아님 |

실패도 보존했다. Module 첫 harness의 SDK trig 중복 적용1,024건, 잘못된 P23 참조 묶음421건을 고친 뒤 모두 일치했다. mesh 첫 시도는 backend/query wrapper 혼동으로8nohit였고 실제 wrapper로 수정했다. curve gain의 참조 묶음 오류1ULP, Focused의 잘못된 raw Team fixture PC0/null118, Water contact의 불일치 side fixture도 각 commands에 기록했다. 파일 없음·cp949·PowerShell glob·xref 미지원·함수 경계 오인 등 도구 실패를 원본 근거 부재로 사용하지 않았다.

명령·실패 상세는 `analysis/camera_100_r10/commands.md`, `state/commands.md`, `shake/commands.md`, `boom/commands.md`와 결과 JSON에 보존한다. 기존 r5/r7/r8/r9 재사용/재실행은 위 신규 검사 수에 합치지 않았다. 보호 경로 SHA 검사는 `validation.json`으로 기록한다.

## 11. 미확정·시도한 방법·다음 근거

현재 고정 질문 **13개**가 남아 있다. 아래는 새로운 작은 질문을 만든 표가 아니라 동결 순번의 잔여를 요약한 표다. 부분 결과가 많아도 행 전체 미확정을 해소하기 전에는 확정으로 승격하지 않는다.

| 순번 | 원래 질문의 잔여 요약 | 다음 근거·막힌 경계 |
|---:|---|---|
| 1 | 전체 카메라 개요의 복합 미확정 | 전체개요복합질문 — poser/사망receiver/수명·Pipeline/Vehicle/Dokan 상황의미는기존r8/r9 및새r10 해소. 지형최초pose→native적용,최종texture/window·GPU부호,남은전체상태공급은4/9/12/23/29/31/32/33/35/36/37/38과함께유지 |
| 4 | 벽·지형 회피 전체 | Banc/create-info/context pose→Actor298..2b8/28c current pose 최초 writer와3ae14b0 Entity/native 초기pose 적용의 마지막 동일성·조건. identity 값 일치만으로 source 동일성 승격하지 않음. 다음3ae14b0/3cc3c1c/0f73930 및Actor최초posewriter. 전체SceneUC미실행만을추가완료조건으로삼지않음 |
| 9 | 조작 불가·자동 피치 복귀의 상태 의미 | Demo34/BF4·BeforeGame/GameEnd/Ready/Result 직접의미·실제피치조건표 해소. CoopSeq1348 message18의raw12→typed enum명,일부mode FSM 상태 자연어명 잔여;wholequeue/runtime를 이 의미 질문의 새 완료조건으로 추가하지 않음 |
| 12 | 스틱 오른쪽과 최종 화면의 좌우 | 정상framework/init flags/worker·origin1·window image·HDR triangle 공급 해소. 같은프레임1120eac target→동일window140 image28 texture identity,SDK4bb970/4d2050/backend의GPU초기A18swizzle,livepending/state1후속writer 잔여;CPU성공을최종화면부호전체확정으로승격하지않음 |
| 23 | 원본 붐 구간 질의의 전체 필터 | Banc/create-info/context pose→Actor298..2b8/28c current pose 최초 writer와3ae14b0 Entity/native 초기pose 적용의 마지막 동일성·조건. identity 값 일치만으로 source 동일성 승격하지 않음. 다음3ae14b0/3cc3c1c/0f73930 및Actor최초posewriter. 전체SceneUC미실행만을추가완료조건으로삼지않음 |
| 29 | 스틱 X 응답식과 잔여 최종 화면 부호 | 정상framework/init flags/worker·origin1·window image·HDR triangle 공급 해소. 같은프레임1120eac target→동일window140 image28 texture identity,SDK4bb970/4d2050/backend의GPU초기A18swizzle,livepending/state1후속writer 잔여;CPU성공을최종화면부호전체확정으로승격하지않음 |
| 31 | 원본과 웹 좌우 부호의 최종 대응 | 정상framework/init flags/worker·origin1·window image·HDR triangle 공급 해소. 같은프레임1120eac target→동일window140 image28 texture identity,SDK4bb970/4d2050/backend의GPU초기A18swizzle,livepending/state1후속writer 잔여;CPU성공을최종화면부호전체확정으로승격하지않음 |
| 32 | 레이·구 캐스트 대체와 원본 붐 전체 | Banc/create-info/context pose→Actor298..2b8/28c current pose 최초 writer와3ae14b0 Entity/native 초기pose 적용의 마지막 동일성·조건. identity 값 일치만으로 source 동일성 승격하지 않음. 다음3ae14b0/3cc3c1c/0f73930 및Actor최초posewriter. 전체SceneUC미실행만을추가완료조건으로삼지않음 |
| 33 | Bad0 이동량 항의 상태별 생산자·runtime | GrindRail actualVT 선행predicate 해소. 245aa00/24c8ee8 실제 공급과메인SP4c0 variant 선택/stack3cd..cf source 동일성,상태별writer/실제Lby프레임 잔여; Bad0를발사후82프레임 고정으로해석하지 않음 |
| 35 | 대체 리그·벽·경사·연출 전체 | Pipeline/Vehicle/Dokan 상황의미와사망receiver·기본경사식은기존/신규근거참조. 24d9ae8의7리그가중치·C1550/1570·다운/벽/경사/연출mode1의전체상태공급조합잔여;이부분은사용자종료요청뒤추가분석하지않음 |
| 36 | 특수 수직 목표의 실제 액터 공급 | 0x7102551fe0 — 1660~1720행 |
| 37 | 조작 불가의 모든 피치 복귀 상황 | Demo34/BF4·BeforeGame/GameEnd/Ready/Result 직접의미·실제피치조건표 해소. CoopSeq1348 message18의raw12→typed enum명,일부mode FSM 상태 자연어명 잔여;wholequeue/runtime를 이 의미 질문의 새 완료조건으로 추가하지 않음 |
| 38 | 벽 접근 판정·전체 카메라 붐 | Banc/create-info/context pose→Actor298..2b8/28c current pose 최초 writer와3ae14b0 Entity/native 초기pose 적용의 마지막 동일성·조건. identity 값 일치만으로 source 동일성 승격하지 않음. 다음3ae14b0/3cc3c1c/0f73930 및Actor최초posewriter. 전체SceneUC미실행만을추가완료조건으로삼지않음 |

다음 분석 후보는 실제 Lby HDR texture/window·GPU 초기swizzle, 지형 Banc→Actor 최초pose→native초기적용의마지막동일성, 자세타이머의상태별실제프레임 공급이다. Entity 비마스크·Defaulthelper·Banc·RSDB·최근접 경쟁과등록dispatcher는근거로보강했으며,미연결초기pose를identity값일치만으로닫지않았다. 이전 raw Default→numericQ→D 연결은 Ragdoll Q의 float 필드를 Entity mask로 오인한 것으로 정정했다. raw BSS0·주소 검색0·합성 입력 성공만으로 원본 live 값이나 경로의 전면 부재를 확정하지 않는다. 확정 불가 판정은 시도/원인/다음 위치까지 기록해야 하며 근거 확정률에는 포함하지 않는다. 이번 종료는 사용자의 중단 요청에 따른 것이며 100% 달성이나 웹 반영 완료를 뜻하지 않는다.
