# 나와바리 결과: 최종 p·‰·승패

상위 문서 [paint_and_score.md](paint_and_score.md) §4, 계산 세부 [special_gauge.md](special_gauge.md) §6.8~6.9. 표기 [../README.md](../README.md#확정-수준-표기). 상태: **분석 진행(4차, [paint4])** — 결과 확정 함수 순서·승패 규칙 판독, 호출 시점(경기 종료 상태머신)은 미확정.

## 1. 결과 확정 흐름 `0x71030a85ec` [판독]

```
referee = *0x71058367f8 (VersusReferee),  result = referee+0x128
if 전역 0x71058e8770 != 0:  다른 객체에서 결과를 복사(관전/재생 경로로 보임 [추정]) → 아래 계산 생략
else:
   D = 블랙보드 "PaintPtMax" (팀 p 기록 0x7103092a4c 가 먼저 써 둔 값)
   0x710303bd80(referee, &D)          // PaintPermille: 팀 링 +0x70 p, +0x74 ‰ 기록. 상위 두 팀 동률이면 정렬상 앞 팀 +1‰ 하고 그 팀 p 재계산
   referee->vt[0xc8](referee, &D)    // 나와바리 = 0x71030424ac (VersusRefereePaint 슬롯 25): 승리 팀 결정
   … 이어서 결과 송신/기록(0x7102aed930, "PlayGameFrame") 등
```

디컴파일: `analysis/decomp/paint/referee_paint.c`(슬롯 25), `gauge/gauge_batch4.c`(0x710303bd80), `paint4/p4_misc1.c`(0x71030a85ec).

## 2. 승패 규칙 `0x71030424ac` [판독]

```
ring = result+0x10d0 (항목 0x80 B), 시작 +0x10dc, 크기 +0x10d8, 개수 +0x10e0
A = ring[시작], B = ring[시작+1]          // 개수 0이면 둘 다 ring[0], 1이면 B = A
result+0x70 = (A.p(+0x70) < B.p) ? 1 : 0  // 1 = Bravo 승, 0 = Alpha 승
```

- **동률 처리**: 승패는 PaintPermille 보정 **뒤의** p로 정합니다. p·‰가 완전히 같으면 PaintPermille이 정렬상 앞 팀(원본 실행에서 Alpha)에 +1‰을 주고 p를 다시 계산하므로 그 팀 p가 커져 승리합니다. 보정 뒤에도 같으면(예: D가 작아 +1‰이 p를 바꾸지 못함) `A.p < B.p`가 거짓이라 **Alpha 승**입니다 **[판독]**. 즉 원본에 무승부 결과값은 없습니다.
- 전부 0(아무도 안 칠함)이면 PaintPermille이 Alpha에 1‰을 주므로 Alpha 승 **[실행(에뮬) — special_gauge.md §6.8 결과에서 연결]**.
- 트라이컬러(규칙 5)는 별도 심판 클래스이며 이 문서 범위 밖입니다.

## 3. 결과 화면 수치

결과 미터·문자열은 [special_gauge.md](special_gauge.md) §6.9: 내 팀이 앞에 오도록 교환, p가 같으면 한쪽 +1(표시용, 승패와 별개), `"[‰/10].[‰%10]%"`, `"[p]p"`.

경기 중 우세 표시(만분율 차 5단계, 0x7103042394 슬롯 19)는 집계 카운터 a/b 를 직접 쓰고, 결과는 p(÷211.2) 정수로 정하므로 **둘은 반올림 단위가 다릅니다** — 우세 표시가 동률(2단계)이어도 결과는 위 규칙으로 갈립니다 **[판독]**.

## 4. 랭크(가치) 모드 구조만

- 결과 저장 키 `Result{PaintPoint, PaintPermille, GachiLeftCount}`(0x710306a718) **[판독]**. 결과 미터는 규칙 1..4면 `(100 − GachiLeftCount)` 쌍을 씁니다(0x71030a3bfc) **[판독]**. 카운트 규칙은 범위 밖.

## 5. 웹 포팅

```ts
function decideTurfWinner(ptA: number, ptB: number /* PaintPermille 보정 뒤 */): 0 | 1 {
  return ptA < ptB ? 1 : 0;   // 0 = Alpha. 원본은 무승부 없음
}
// 순서: teamP 기록(0x7103092a4c) → PaintPermille(special_gauge.md §6.8) → decideTurfWinner
```

## 6. 미확정 — 다음에 볼 곳

| 항목 | 다음에 볼 곳 |
|---|---|
| 0x71030a85ec 의 호출 시점(종료 연출 몇 프레임째) | 호출자 추적(심판 상태머신) |
| 0x71058e8770 플래그 의미, 복사 원본 객체(*0x71058e0460+0x66d8) | 해당 전역 writer |
| 링 항목 순서가 항상 Alpha, Bravo 인지 | 0x7103092a4c 기록 순서와 링 시작(+0x10dc) writer |
