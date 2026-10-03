# 정지 상태 마우스 시점 문제 — 반영 지시 요약 (2026-10-03)

사용자 증상: **가만히 서서 마우스로 시점만 바꿀 때 갑자기 뒤돌거나 뜻과 다르게 시점이 보정됨**. 이번 작업은 분석·MD만 수행했다. [상세 원인·실행 경계](../camera/mouse_view_jumps.md), [입력 수명](../camera/mouse_input_lifecycle.md), [원본 제어 경계](../camera/mouse_original_controls.md).

현재 확인된 것은 **재현 조건이 있는 웹 동작**이며, 실제 사건의 raw delta·감도·프레임 기록이 없어 어느 경로가 사용자의 사건에 해당했는지는 미확정이다. 이동/변신/벽/Alt+Tab을 주원인으로 가정하지 않았다.

| 우선순위·기존 계약 | 재현된 차이 | 다음에 반영할 명세·검증 | 상태 |
|---|---|---|---|
| **P0 마우스 입력→CAM02 렌더 회전 경로** | 큰 누적dx를 첫 fixed step에 전량 적용. −210° 입력에 actual quaternion은 +150° 최단 경로로 보간. 5step catch-up이면 pre-turn 이력도 소실 | 입력 시간·전체량·부호를 보존하는 소비/보간 계약. 큰 회전을 endpoint 두 개로만 표현하지 않음. 임의 delta 잘라내기 값은 원본값으로 넣지 말 것 | 웹 정책 반영·회귀 검증 완료 (2026-10-03) |
| **P0 마우스 pitch→CAM01/02 리그/기저** | 손을 멈춰도 pFollow로 목표p를 추종. 기본dy−200 뒤60무입력step에 시선이 추가15.983365° 이동 | 원본 s/p 곡선·리그와 mouse adapter 정책을 구분. 입력 중단과 화면 중단을 원하는 경우 별도 정책으로 명시하고 pFollow/경계 테스트 | 웹 정책 반영·회귀 검증 완료 (2026-10-03) |
| P1 CAM06 입력·reset 수명 | pending dx/dy가 blur/잠금 상실 뒤에도 남아 unlock loop에서 소비. KeyR도 unlock 입력 허용 | pointer-lock/blur/visibility 소유 기간·pending/hold 정리와 reset reason 기록. 이번 사용자 사건의 원인이라고 단정하지 않음 | 입력 소유 수명 반영·30건 웹 실행 (2026-10-03) |
| 조사: 원본 자동 yaw | C1940 타입은 MissionTicketGateAction. ordinary 평지정지 auto-yaw는 조건부rate0이며 해당 특수 경로가 현 웹에 없음 | B9314 writer/실제 native flags는 미확정 유지. 일반 마우스 해결책으로 특수 auto-yaw를 추가하지 않음 | 원본 신규 판독·데이터, 사건 원인으로 제외 |

기본 yaw .15°/px에서180° 임계는 누적1200px. 배율20이면60px, sens5/배율20이면약34.286px다. **사용자의 실제 감도·입력값을 읽었다는 뜻이 아니다.** 작은dx10×240step은 ±π 숫자 경계를 넘어도 매step 실제시선≤1.500004°로 연속이었다.

기존 고정 반영표 **13/62=20.97%**, 카메라 **2/7=28.57%** 유지. CAM01/02의 원본 리그/기저 계산 확인은 유지하지만, 그 점수는 마우스 체감 전체 완료를 뜻하지 않는다. 이번에는 코드 수정0·새 반영 완료0이다. 원본 카메라 **78/106=73.58%**, 전체 **556/986=56.39%**도 웹 재현으로 올리지 않았다.

바로 내릴 지시:

- **“정지 마우스의 큰 delta·한 스텝 일괄 소비·최단 quaternion 역방향 보간을 입력량 보존 조건으로 수정해줘.”**
- **“마우스를 멈춘 뒤 수직 시점이 계속 움직이는 pFollow 연결을 분석 명세대로 조정하고 원본 피치 곡선은 유지해줘.”**

첫 지시의 완전한 사건 진단을 위해 실제 delta·settings·sample 각·frame step 수·pre/current basis·렌더각·reset reason을 한 trace에 남겨야 한다. 확인되지 않은 브라우저/기기 버그나 원본 자동 시점 기능을 실제 원인으로 채우지 않는다.


## 우선순위1 실제 반영 — 2026-10-03

사용자의 후속 웹 반영 지시로 mouse adapter를 구현했다. [mouse_web_port](../camera/mouse_web_port.md)에 변경과 검사 경계를 기록했다. `sample(남은step수)`로 pending 전량 분배, signed yaw/residual/orbit 보간, mouse-only 목표pitch즉시소비, lock/blur/hidden 잔여입력 정리를 연결했다. 원본 미지정 pad의 pFollow와 native 피치곡선·리그는 유지했다.

camera42/42·view268checks·input/appcallback30/30 PASS. 실제 브라우저에서도5step입력량보존·피치입력중단후travel0·오류0을 확인했다. 사용자의 실제 사건 기록을 확보했다는 뜻은 아니다. 고정camera2/7·전체13/62는복합질문전체완료로승격하지않아유지한다.
