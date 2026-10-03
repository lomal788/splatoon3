# 탄·총 반영 요약 — 2026-10-03

스플래시슈터 원본 분석을 실제 사격장 경로에 반영했다. 원본 분석률과 구현 반영률은 별도다.

고정 BUL01~06 **3/6=50.00%**(이전2/6=33.33%), HIT01~04 **1/4=25.00%**, TGT01~04 **2/4=50.00%**. 전체 고정62개 **13/62=20.97%**. BUL03/04/06의 일부 결과를 전체 반영으로 승격하지 않았다.

| ID | 반영 | 남은 것 |
|---|---|---|
| BUL01 반영 확인 | 프레임 시작 활성 목록·player 사격과 기존 탄 post 경계·생성 age-1→다음0 | 전체 actor scheduler SYS02 별도 |
| BUL02/05 유지 | damage/radius·잉크 소비 수치 | 실제 query·회복 전체는 별도 |
| BUL03 일부 | input priority/native gate·abc/ab4·fresh Lobby seed13·기존 공유 조준 | a90/4d4/원점·일부 reset·GameFrame |
| BUL04 일부 | 초기 sphere overlap·wall requery·WallDrop .2 sphere·칠 불가 거름·분열 표 연결 | 두 형상 native query/filter/candidate·천장/paint flag |
| BUL06 일부 | 세 stop counters·음수 감소·previous max·stealth fields·회복 기본률 | 실제 지연 B7a0·상위 상태/기어 consumer |
| HIT01 반영 확인 | raw sender→receiver 한 번 rate→HP | 기타 이력/표시 계약 HIT02~04 별도 |
| TGT03 반영 확인 | damage와 분리된 physical bend callback·body center·stepVelSec·y=0·scaler | 표적 전체 모델/재질은 별도 |

검증: 원본 함수 대조 **1,926건**, 테스트 **153/153**, typecheck/build 통과. 브라우저 실제 Lby30발·모두6프레임 간격·바닥 칠4140texels·NoInk30/회복 경계·우선 입력·finite 값 확인, console/page/HTTP 오류0. 실제 표적 receiver와 휨은 통합 fixture(raw360→123→HP877)로 검증했다. 브라우저에서 17표적에 모두 명중했다는 뜻은 아니다.

변경 파일/함수·기존 결론 정정·실패 명령·미확정 상세: [impl/weapon](../impl/weapon.md) §1~11. 원본/키/commit/push는 건드리지 않았다. gun port 단계에서 원본 analysis inventory/SHARED/FUNCS는 유지했다.

다음 지시: **“BUL03/06의 실제 player producer와 BUL04 native query를 연결”**. 시각적으로 다른 탄/잉크/오징어/광원은 별도 [잉크 그래픽 분석](ink_visuals.md)을 따른다.
