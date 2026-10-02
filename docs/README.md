# Splatoon 3 (v0) 분석 문서 목차

원본을 분석해 웹으로 포팅하기 위한 명세입니다. 작업 지침은 [../분석.txt](../분석.txt).

## 프로젝트 정보

| 항목 | 값 |
|---|---|
| 게임 | Splatoon 3, TitleID `0100C2500FC20000`, v0 (XCI) |
| 원본 | `c:/dev/splatoon3/original/` — **읽기 전용** |
| 추출물 | `c:/dev/splatoon3/extracted/` (재생성 가능) |
| 분석 산출물 | `c:/dev/splatoon3/analysis/` |
| 분석 도구 | `c:/dev/splatoon3/web/tools/` (+ Ghidra는 `c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC` 그대로 사용) |
| 웹 프로젝트 | 아직 없음 |

## 공용 문서

- [00_extraction_pipeline.md](00_extraction_pipeline.md) — XCI→NCA→ExeFS/RomFS 추출, 해시 검증, 재현 명령
- [01_package_and_assets.md](01_package_and_assets.md) — RomFS 구성, zstd/SARC/BYML, 액터→컴포넌트→파라미터 연결
- [02_code_and_params.md](02_code_and_params.md) — main NSO(심볼 없음), 파라미터 리플렉션으로 필드·기본값 판독, 클래스명→vtable
- [tools.md](tools.md) — 분석 도구 사용법 (즉석 디컴파일 포함)

## 기능 문서

| 영역 | 문서 | 상태 |
|---|---|---|
| 슈터 탄 계산 | [weapon/shooter_bullet.md](weapon/shooter_bullet.md) | 이동 상태머신·스텝식·프레임 순서·난수·발사 속력·초기 속도·스플래시 생성·바디 적분·충돌 콜백(바닥 58/벽 59/대상 60) 판독, 재구현 계산. 첫 명중 age(1로 추정) 미확정 |
| 플레이어 물리·이동 | [player/movement_physics.md](player/movement_physics.md) ([gear_skills](player/gear_skills.md), [player_state](player/player_state.md)) | 기어→속도(원본 실행 731건), 목표 속도·상한·입력 곡선, 점프 곡선 확정(탭 최고 0.841/14f, 원본 함수 연결 실행 비트 일치), 최종 속도 합성식, 가속 식 전체, 벽 타기·벽 점프·오징어 롤, 상태 286개·전이 우선순위 판독. 세계 중력 런타임 값·일부 플래그 의미 미확정 |
| Phive 물리 계층 | [physics/phive_controller.md](physics/phive_controller.md) | 플레이어 중력 0.008 유닛/프레임²·v=0.98v−g·종단 −0.4(게임 코드가 적용, Phive 중력·감쇠는 0), 컨트롤러 단계 순서, 탄 바디 적분(서브스텝 없음, p += dt·(v×60), dt 1/60)·충돌 응답(최소 f 접촉점에서 정지)·충돌 콜백 분배(바닥/벽/플레이어) 판독. 접촉 처리의 프레임 내 시점·shapeTag 필터 콜백 미확정 |
| 피격·데미지·타격 판정 | [combat/damage_hit.md](combat/damage_hit.md), [combat/player_life.md](combat/player_life.md) | 탄 데미지 감쇠·반경·크리티컬·넉백·배율표·수신 이력 6모드 판독. HP·회복·적 잉크 데미지·사망·리스폰 흐름(타이머·Revival·리스폰 무적·지점 선택)·StartArmor·무적 판정 판독, HP 홀더·리스폰 타이머 원본 실행 일치. 리스폰 착지 단계 입력 쪽·아머 원인↔무기 이름 미확정 |
| 잉크 도색·점수 | [paint/paint_and_score.md](paint/paint_and_score.md), [paint/paint_shape.md](paint/paint_shape.md), [paint/special_gauge.md](paint/special_gauge.md) | 도색 모양·지연 도색·요청 큐→송신→렌더 패스 전체 경로·모드 0~17(패스 역할+팀)·스탬프 회전·패턴 변형(원본 실행 600건)·텍스처 size(1단위당 8텍셀)·집계 규칙·p 환산·PaintPermille·스페셜 게이지(원본 실행) 판독. 게이지 일부 writer·지형 아틀라스 밀도 미확정 |
| 카메라·손맛(조작감) | [camera/camera_feel.md](camera/camera_feel.md) ([aim_swerve](camera/aim_swerve.md), [player_camera](camera/player_camera.md), [shake_rumble](camera/shake_rumble.md)) | 조준 흔들림·연사 타이머·카메라 리그·감도·스틱·추종·쉐이크 판독, 대체 리그 7종 발동 조건·자이로 경로·리셋·쉐이크 적용 위치·블래스터·Diffusion 판독. 반전 설정(원본 실행 4건 일치)·벽 회피 거리 반영·슈퍼점프 카메라 판독, Diffusion의 두 필드는 결과에 영향 없음. 질의 형상·사망 메시지 수신 측 미확정 |
| 그래픽·모델·캐릭터 | [graphics/model_character.md](graphics/model_character.md) ([formats](graphics/formats_bfres_bntx.md), [team_color](graphics/team_color.md), [player_assembly](graphics/player_assembly.md), [anim_state_machine](graphics/anim_state_machine.md), [shaders](graphics/shaders.md)) | FRES v10·BNTX 변환, 팀 컬러(Ink/InkBright = 주 방향광+하늘 SH 기반) 판독, BlitzUBO0 레이아웃(원본 실행)·몸 잉크 색식, 셰이더 슬롯·옵션·혼합식, 인간/오징어/_Hlf(변신 과도기) 표시 선택, ASB 노드·끝 프레임·전환 블렌드·블랙보드, 신발 미러·모자 바인드 판독. 스테이지 조명 호출 경로·LOD 거리 계산·머리카락 천 물리 미확정 |
| 이펙트·효과음 | [effect_sound/effect_sound.md](effect_sound/effect_sound.md) ([xlink](effect_sound/xlink_format.md), [sound](effect_sound/sound_resources.md), [effect](effect_sound/effect_resources.md)) | xlink 실행 규칙·트리거 비트·보류 액션 판독, VFXB v46 이미터 주요 필드·GPU 위치식(셰이더 역번역)·슈터 이펙트 웹 재현값 표, Alto 롤오프·AUDC·AADR 판독, 무기 그룹 동시 발음 제한 없음 확인. 이미터 형상별 식·DistCoef 확장값·필터 컷오프 미확정 |
| 스테이지 기믹 | [gimmick/stage_gimmicks.md](gimmick/stage_gimmicks.md) ([inkrail](gimmick/inkrail.md), [sponge](gimmick/sponge.md), [misc](gimmick/stage_misc.md), [collision_mesh](gimmick/collision_mesh.md)) | 배치 레이어=모드, 잉크레일·탑승·스펀지 판독+재구현, 충돌 메시(hknpMeshShape) 디코드 1485개 전수·Yagara glb 출력, 이동 발판 일정·회전(Bravo=레일 Y축 180°)·좌표계 판독, 잉크레일 이탈 경로 5종(끝 자동 이탈 없음), 스펀지 중심·SafePos, 사망 이유 열거형, 간헐천 법칙. 점프대 속도·파이프라인·그라인드 레일 미확정 |
| 네트워크 | [network/network.md](network/network.md) (01~06 하위 문서) | P2P 메시·15Hz 상태·비트 직렬화(LSB 우선)·PlayerNetState 필드 출처·의미 다수(HP·아머·공중 프레임 등)·GameFrame 동기·시계=pia GetClock(ms)·시드 로비→설정 복사·Rule 값 표·pia 신뢰 전송(창 128, 재전송 33ms+1.4×RTT)·다음 호스트 선택, 원본 실행 다수. 일부 필드·로비→게임 객체 복사 지점 미확정 |
| UI | [ui/ui_hud.md](ui/ui_hud.md) ([layout format](ui/ui_layout_format.md), [VS_MainTV 요소](ui/ui_vs_maintv_elements.md), [minimap](ui/ui_minimap.md)) | 대전 HUD 특수 게이지 추적, 레이아웃 v9·폰트·MSBT 파서 전수 실행, 칠 포인트·타이머·Pinch·결과 % 판독, 갱신 루프 순서·dt·애니 명령(원본 실행 13건 일치), 미니맵 정사영·축 규약·맵 열기 입력·맵 셰이더(역번역) 판독, 게이지 표시 = min(value, trace) 확정(원본 실행 56건). 뷰포트 실제 크기 미확정 |

## 확정 수준 표기

- **[실행]** 원본 실행 확인
- **[판독]** 원본 코드/명령 판독 확인
- **[데이터]** 데이터 확인
- **[추정]** 추정
- **[미확정]** 미확정

"분석 완료", "웹 구현 완료", "동작 검증 완료"는 서로 다른 상태입니다. 현재 웹 구현은 없습니다.
