# ColPaint 패널의 독립·연결·메시 패턴

## 1. 기능 개요

원본은 충돌에서 얻은 패널을 그대로 사각형으로 칠하지 않는다. 세 recognizer가 panel+9C의 숫자 패턴을 결정하고, 얇거나 무효인 패널은 시각 메시를 다시 배정한다. 여기서는 세 recognizer의 전체 분기와 모델 콜백·11/12 보정까지 [판독]으로 확정한다. 연결 조건과 겹침 패턴의 새 원본 실행 9,216건이 일치했다 [실행]. 전체 로비 아틀라스·GPU 실행 검증은 별도다.

## 2. 원본·자료

Splatoon3 v0 main.reloc.img. SHARED/FUNCS/decomp_index와 비교 후 기존 미판독 C `analysis/decomp/paint4/colpaint_r2.c`(2bfb8b8/2bfbbcc/2bfbe40), r1(2be68e8/2bde9ac/2bf4a6c), 새 `analysis/decomp/r8_graphics/paint_pattern_callbacks.c`를 읽었다. 도구 `web/tools/r8_paint_pattern_emu.py`, 결과 `analysis/completion/r8/paint_pattern_emu.json`. 기존 실행·근거는 새 건수로 재계상하지 않는다.

## 3. 호출 흐름 [판독]

패널 추출·병합과 mapBox 확보 → recognizeIndependentPattern(2bfb8b8) → recognizeConnectPattern(2bfbbcc) → recognizeMeshConnectPattern(2bfbe40) → fixInvolvedPanel(2be68e8). 메시 recognizer는 setupper 작업모델 vt28의 실제 삼각형을 2bfc714로 순회한다. 정확한 연결 생성·group 배치·최종 shader는 다른 질문으로 유지한다.

## 4. 구조·상수 [판독]

| 기준 panel 필드 | writer/reader와 의미 |
|---|---|
| +20..34 | 충돌투영 box min/max, Independent 크기 입력 |
| +3C..50 | 시각 삼각형 배정으로 넓힌 mapBox, 패턴·면적 입력 |
| +38 | 42방향. 40=바닥,41=천장,일반 E=(d>>3)+1/az=d&7 |
| +88 | 연결쌍을 읽는 트리;P15/P4에서 pair의 root/other 사용 |
| +90 | 다른 panel을 키로 하는 양방향 이웃 트리;메시 가중합 |
| +98 | shrunken box 안의 공유 정점 방문 횟수;삼각형별 누적 |
| +9C | 숫자 패턴. 아래 세 recognizer가 쓰는 값·조건은 §6 |
| +A0/+B0/+B8 | 연결 root/방문flag/인접수/방향별 이웃 배열 |
| +C8 | 겹침 support panel별 면적 트리;P5 판정 |
| +1C8/+1D8 | P5 support panel / 시각 배정 overlap 누적 |

P6의 이웃 패턴6..16 가중치는 원본4AA2AF0의 `(1,1,1,1,0,1,1,1,1,1,1)` [데이터]. 3/9/10/16은 이 세 recognizer가 새로 쓰지 않으며, 전역 enum 이름이나 다른 writer가 없다고 확대 해석하지 않는다.

## 5. 수명·순회 [판독]

Independent는 입력 순서로 모든 패널을 재분류한다. Connect는 기존1/2를 건너뛰며 순서대로 P1→P2→P15→P4를 시험한다. 성공하지 않으면 기존 패턴을 보존한다. P1/2는 U 연결 전체, P4는 U 뒤 V로 전파하며 P15는 자기 패널만 쓴다. global58F07B8+2C0 객체의 +2BC bit0 취소가 각 패널 사이에서 작업을 멈춘다.

2bfa208 연결 순회는 root를 directionArg=-1로 먼저 방문한다. mode0은 방향0 사슬 뒤1 사슬,mode1은2 뒤3이다. 방문flag로 재방문을 막고 종료 시 되돌린다. root 인접수2/3/4 미달 때 해당 슬롯은 인접0으로 대체된다. 이 순서와 마지막 overwrite를 보존해야 한다.

## 6. 패턴 분기 [판독]+[실행]

Independent의 충돌 크기 `(u,v)`,map 크기 `(mu,mv)`: 어느 하나 <=.3이면 thin 경로. mapBox 세 축 min<=max면 P11,무효면 P12. 무효이고 d40 또는 d<32(41제외),충돌면적>1,overlap1D8/충돌면적>.5이면 mapBox=collisionBox로 고치고 P13. 그 밖은 다음과 같다.

- d<24이고 `(u<=1 || v<=1 || u*v<4 || mu<=1 || mv<=1)`이면 P14.
- `u>2 && abs(u-mu)/u>.2` 또는 `v>2 && abs(v-mv)/v>.2`이면 P17,그 밖 P0.
- 위 축약식은 유효 유한 좌표에 대한 표현이다. NaN에서는 원본 fcmp 조건을 보존하며 C의 복잡한 NAN 분기를 단순히 정상값으로 채우지 않는다.

Connect 조건은 다음과 같다.

| 패턴 | 원본 조건 |
|---:|---|
| 1 | d<16,V연결은root뿐,U사슬의 elevation이 실제 순서에서 비감소·변화있음·각 du차<=.2. Σarea>10,Σsin(angle)*dv>3 |
| 2 | 16<=d<32,나머지 같고 elevation은 비증가 |
| 15 | d<16,자기면적<=20. +88의 다른panel 중 바닥40제외·d<16 발견하면즉시참;그외유효이웃(천장41포함)>1 |
| 4 | root d26. root 충돌면적=V순회의 마지막 az6 면적(±.01),az0/4 면적도±.01이며 각각 곱이 음수아님;연결+88에 다른바닥40 정확히1개,그면적-du6*du0가±.1 안 |

P4의 실제 비교쌍은 root 충돌면적/state0 및state4/state8이다. az6→state0/duC,az0→state4/du10,az4→state8/du14. 처음 값 -1을 임의0으로 바꾸지 않는다.

E는 d40→0,d41→6,그밖(d>>3)+1. sin angle은40→0,E2→raw3F16CBE4,E3→3F7B53D2,그밖(E−2)*3F490FDB. callback2bfb3a4가 변화/비증가/비감소/폭동일 flag를 실제 순서로 갱신하며2bfb56c가 원본sinf 높이합을 만든다.

Mesh는 d8..15에서 +98>=3이면 P7. 그 밖 +90의 이웃 가중합>2면 P6;1..3은가중0,다른panel의 +80 parent가 d40 또는d<8이면1,나머지는 위 원본표. 이 외에는2bef220를 호출한다. 두 번째 순회에서 d40 또는d<24이고 네 직접이웃 중 P7이 있으면 P8.

2bef220는 현재P1/2만 검사한다. mapArea 절댓값<=2^-23이면 보존한다. +C8 키 순회에서 면적이 엄격히 더 큰 첫 support를 선택(동률은 첫번째). 최대면적/mapArea>.1이면 P5와+1C8=support를 쓰고 support가P1/2면 support를0으로 만든다. 이 식 2,048건 원본 실행 일치.

## 7. 시각 메시 연결 [판독]

2bfc714는 시각 삼각형을 순회한다. prior-face가바닥이며panel은비바닥이면2c0e594 overlap을 임시트리에 누적하나 이 임시트리는 끝에 해제만 한다. 실제 P5가 소비하는 +C8과 구별한다.

panel d40 또는d<16에서 box 중심과 halfExtent*.7을 만든다. 각 삼각형 정점의 서로 다른 인접panel(max6)이 둘 이상이고 정점을panel 기저에투영한 값이 축소box안(경계포함)이면 +98을 증가시킨다. 삼각형마다 같은 정점이 재등장하면 또 센다. 전역 고유 정점 수로 바꾸지 않는다.

바닥panel은 다른바닥/d<16 panel을2bf4a6c로 양방향+90 트리에 연결하고, 이 삼각형과 다른panel box의 겹침면적을 다른panel+C8에 자기panel 키로 누적한다. 비바닥d8..15는 연결을 만들지만 +C8면적을 추가하지 않는다. 임시노드는0x70B,풀0x46000/최대0x1400.

## 8. 11/12 보정 [판독]

2be68e8은 P11/12의 +70 충돌prism을2bde9ac로 방향별검색목록·옥트리 링크에서 제거한다. BuildMeshModel vt28의 시각 삼각형을 resetup콜백(vt567C668)으로 다시 돌린 뒤 기존11/12를 전체목록·방향목록에서 memmove로 빼고 연결·패널풀을 해제한다. 원본 지형/원본 파일을 삭제한다는 의미가 아니다. P13은 이 삭제조건에 들어가지 않는다. 이후 패널 mapBox·UV 소비는 [model_panel_mapping.md](model_panel_mapping.md) §3~§8을 따른다.

## 9. 웹 반영 필요

impl/paint.md/impl/assets.md: panel+9C에 위 원본 조건·실제 연결 순서를 적용하고 11/12 resetup, P5 support 해제, 공유정점 반복계수, 취소flag를 보존해야 한다. 웹 독자 차트의 결과를 원본 패턴으로 간주하지 않는다. 이번에는 구현 코드를 변경하지 않았다.

## 10. 실행 검증

`python web/tools/r8_paint_pattern_emu.py` → Connect1 2048,Connect2 2048,Connect15 2048,P4 1024,Meshfallback5 2048,총9216 mismatch0. 원본 함수·연결순회·callback을 실제 실행한다. SDK sinf도 별도 Unicorn에서 원본 실행하며, 참조쪽에는 각도 sin 결과만 공유한다. 패턴 자체와 판정은 재구현 대조한다. 합성panel/연결트리가 입력이며 원본 로비 전체추출/GPU 실행은 아니다.

첫 실행은 case44에서 sinf 반환u32를 숫자float로 잘못 읽어 참조값이 틀려 실패했다. 반환비트를f32로 다시 해석한 뒤8192건통과,P4를추가해9216건통과했다. 명령·실패는 `analysis/completion/r8/paint_commands.md`에 기록한다.

## 11. 미확정·정정

2026-10-03 정정: colpaint_atlas §2/§10의 세 recognizer 미판독을 위 새근거로 해소한다. +9C는 조건별숫자태그이며 외부 명칭을 상상해 붙이지 않는다. 세 recognizer가 쓰지 않는3/9/10/16의 전역의미는 미확정이다. 연결 생성/fixConnection 및 group 알고리즘,200단위씬,원본로비 전체 최종아틀라스·GPU는 계속 조사한다. 다음:2bf03d0/2bf22a8/2c01420/2c03338/2c03cdc.
