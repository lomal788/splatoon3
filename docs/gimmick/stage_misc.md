# 스테이지 기타 요소: 이동 발판·장외/사망 판정·충돌 재질·스폰·히어로 모드 기믹

목차는 [stage_gimmicks.md](stage_gimmicks.md). 표기 규칙은 [inkrail.md](inkrail.md) 머리말과 같습니다.

## 1. 이동 발판 (Lft_*, spl::Lift)

### 1.1 v0 대전에서의 사용 [데이터]

움직이는 발판은 Vss_Carousel(スメーシーワールド)에만 있습니다. 모드 레이어마다 같은 4개가 반복됩니다.

| 액터 | 팀 | RailMovableSequentialParam | 레일(LiftRail, 부모 기준 좌표) | 점 BreakTime |
|---|---|---|---|---|
| Lft_CarouselBridgeMoveA | Alpha | MoveTime 4.0, WaitTime 4.0, PatrolType cContinue | (0,0.05,0) → (5.5,0.05,3) | 30, 22 |
| Lft_CarouselBridgeMoveB | Alpha | MoveTime 8.0, PatrolType cContinue | (0,0,0) → (11,0,6) | 22, 22 |
| Lft_CarouselBridgeMoveA | Bravo | 동일, Rotate (π,0,π) | (0,0.05,0) → (-5.5,0.05,-3) | 30, 22 |
| Lft_CarouselBridgeMoveB | Bravo | 동일, Rotate (π,0,π) | (0,0,0) → (-11,0,-6) | 22, 22 |

- 발판 → 레일 연결은 `spl__ailift__AILiftBancParam.ToRailPoint`(첫 점 Hash). 레일은 `game__GraphRailWithParentParam`입니다. 점 좌표는 **월드 좌표**이고(부모 변환은 생성 시 단위, §1.5), Bravo 쪽 레일은 레일 단위 `Rotation`이 (π, ~0, π)입니다 **[판독+데이터]**.
- `spl__LiftBancParam.ToNotPaintableArea` → `ChangePaintableArea` 링크(발판 이동 영역 칠 금지 [추정]).
- 같은 스테이지의 `Lft_CarouselCircleFloorMove`(Pnt), `Lft_CarouselCircleFloor_Hoko`(Vgl·Vcl)는 레일·이동 파라미터가 없습니다. 회전 방식은 **[미확정]**. `DObj_Carousel*`(관람차 등)는 `spl__DesignerObjBancParam.AnimName` 애니로 움직이는 배경 오브젝트 [데이터].

### 1.2 코드 구성 [판독]

2026-10-02 정정: 이전 판에서는 이동 주체를 `spl::Lift`의 엔진 컴포넌트로 추정했습니다. 실제로는 액터 컴포넌트 `AILift`(`Work/Component/AILift/BlitzCompatibles.spl__AILiftParam`, Bootup 팩, `ClassName "spl::AILiftBlitzCompatible"`)가 `game::RailMovableSequential` 객체를 품고 움직입니다. 이전에 "임시 가정"으로 둔 "도착 후 max(WaitTime, BreakTime)" 규칙은 틀렸습니다(WaitTime은 처음 1회만, 점마다는 BreakTime).

| 대상 | 주소 | 내용 |
|---|---|---|
| `spl::Lift` | vt `0x7105611398`(46), getName `0x71021a70c8` | 액터 본체. 이동 계산 없음 |
| `spl::AILiftBlitzCompatible` | vt `0x7105587128`(29), getName `0x7101479b1c`, 생성 `0x710147999c` | 이동 AI. 객체 +0x20 = RailMovableSequential, +0x88 = 레일 어댑터(vt `0x7105587318`), +0x1920 = SequentialRotate |
| 시작 | `0x7101479b30`(vt7) | 레일이 있으면 RailMovableSequential 초기화 후 일정 생성 `0x7101305238` |
| 시간 원점 | `0x7101479e80`(vt12) | +0x1a08(시간 진행 여부), +0x1a0c(현재 시간 초)를 액터 [+0x348]+0x20 객체(액터별 상태 보관 객체)의 +0x14/+0x18에서 복사. 그 뒤 [+0x348]+0x90 객체에 이름 "Start" 질의(`0x710397840c`)가 참이면 그대로 두고, 아니면 진행=1. 되쓰기 `0x710147a6d0`(+0x1a08/+0x1a0c → 보관 객체), 직렬화 `0x710147a9a0`/읽기 `0x710147a9fc`(모드 2일 때 bool+f32) |
| 매 프레임 | `0x7101479f7c`(vt15) | 진행이면 `t += 프레임수 * 0.016666668`(초), `0x71013043d8(t)` → 행렬(+0xa4), SequentialRotate(`0x71012eeb98`) 회전을 곱해 액터 목표 행렬로 출력 |
| 일정 생성 | `0x7101305238` | 아래 §1.3 |
| 시간 평가 | `0x71013043d8` | 아래 §1.3 |
| 이동 시간 | `0x7101305b40` | SpeedCalcType |
| 구간 처리 표 | `0x7105577e48` | 종류 0 정지 `0x71013046f4`, 1 점 대기 `0x7101304984`, 2 이동 `0x7101304cec`, 3 끝 `0x71013046f4` |

열거형(enum 정보 함수의 값 문자열) [판독]:

| 열거형 | 정보 함수 | 값 |
|---|---|---|
| `game::RailPatrolType` | `0x71012fcd1c` | cStop=0, cContinue=1 |
| `game::RailSpeedCalcType` | `0x71012fe3dc` | cTime=0, cSpeed=1 |
| `game::RailAttCalcType` | `0x71012fd528` | cInMove=0, cInBreak=1, cTangent=2 |
| `game::RailInterpolationType` | `0x71012fdc88` | cLinear=0, cSin=1 |

`game__RailMovableSequentialParam`(기준 = 파라미터 객체, 리플렉션 방문 `0x71012fb6f0`): 플래그는 바이트 +0x4c~+0x52. 이전 리플렉션 표의 타입 표기(SpeedCalcType f32, MoveSpeed s32)는 코드로 다시 확인했습니다.

| 오프셋 | 필드 | 타입 | 기본값 | 플래그 바이트 | reader |
|---|---|---|---|---|---|
| +0x30 | AttCalcType | enum | cInMove | +0x4d | `0x71013046f4`, `0x7101304984`, `0x7101304cec` |
| +0x34 | InterpolationType | enum | cLinear | +0x4e | `0x7101304cec` |
| +0x38 | MoveSpeed | **s32** | 1 | +0x52 | `0x7101305b40` (`(float)(int)`로 나눔) |
| +0x3c | MoveTime | f32 | 1.0 | +0x51 | `0x7101305b40` |
| +0x40 | PatrolType | enum | cStop | +0x4c | `0x7101305238`, `0x71013043d8` |
| +0x44 | SpeedCalcType | **enum** | cTime | +0x50 | `0x7101305b40` |
| +0x48 | WaitTime | f32 | 0.0 | +0x4f | `0x7101305238` |

레일 점 파라미터 `game__LiftGraphRailNodeParam.BreakTime`(점 노드 파라미터 +0x30, 어댑터 vt+0x48 `0x710147b558`이 그대로 반환) = 그 점에서 쉬는 **초** [판독+데이터].

레일 어댑터(vt `0x7105587318`, 레일 = 점 배열 +0x18, 개수 +0x10, 닫힘 +0x40, 누적거리 배열 +0x40) [판독]:

| 슬롯 | 주소 | 의미 |
|---|---|---|
| +0x38 / +0x40 | `0x710147b500` / `0x710147b52c` | 점 위치(점+0x18) / 점 행렬(점+0x58) |
| +0x48 | `0x710147b558` | 점 BreakTime |
| +0x50 | `0x710147b57c` | 다음 점: `i + (rev ? -1 : +1)`, 닫힌 레일은 순환, 아니면 [0, n-1] 클램프 |
| +0x58 | `0x710147b5e4` | 이전 점: `i + (rev ? +1 : -1)` (같은 규칙) |
| +0x60 / +0x68 | `0x710147b64c` / `0x710147b694` | 시작 점 여부 / 끝 점 여부(`rev ? i==0 : i==n-1`, 닫힌 레일은 항상 거짓) |
| +0x70 | `0x710147b6dc` | `dist[b] - dist[a]`(부호 있음, 닫힌 레일은 전체 길이로 나머지) |
| +0x78 | `0x710147b764` | 점 i의 누적 거리 |
| +0x90 | `0x710147b7a8` | 거리 s의 자세 {위치, 회전}: 위치 = `0x71012ffeac`(레일 위치, §1.5 식), 회전 = `0x71013001f4`가 준 구간 (i, j=i+1, u)로 점 i·점 j의 회전(점 +0x64)을 `0x7101250f0c`(쿼터니언 slerp)로 보간 [판독] |
| +0x98 | `0x710147b870` | 위와 같은 회전부만 [판독] |
| +0xa0 / +0xa8 | `0x710147b91c` / `0x710147b928` | `0x71012ffeac`로 꼬리 분기: 위치 / 단위 접선(둘 다 레일 부모 변환 적용) [판독] |
| (+0x40 점 행렬) | 점 +0x58 | 점 자세 {위치 +0x58, 회전 +0x64}. 점 생성 `0x71013028d4` → `0x71012febec` → 점 vt+0x28 `0x7101301d58`이 회전을 채움 [판독] |

### 1.3 이동 법칙 [판독]

```
// 0x7101305238 일정 생성. 항목 = {start(초), kind, pos(점 번호), rev}
t=0, kind=0(시작), pos=시작 점(ToRailPoint), rev=false
loop:
  kind 0: d = WaitTime; (+0x18e8 = WaitTime); npos = next(pos,rev); nkind = 2
  kind 2: seg = prev(pos,rev); d = moveDur(seg,pos)
          nkind = (PatrolType==cStop && isEnd(pos,rev)) ? 3 : 1
  kind 1: d = BreakTime[pos]
          if PatrolType==cContinue: rev ^= isEnd(pos,rev)        // 끝 점이면 방향 반전(왕복)
          npos = next(pos,rev); nkind = 2
  if d > 0: 항목 {t, kind, pos, rev(갱신 전)} 기록                 // 0초 구간은 기록 안 함
  t += d; (kind,pos,rev) = (nkind,npos,nrev)
  (kind,pos,rev)가 이미 기록된 항목과 같으면 → 순환: 주기 +0x18ec = t - WaitTime, 끝
  kind==3 → {t,3,pos} 기록, 주기 = t - WaitTime, 끝
moveDur(seg,pos) = SpeedCalcType==cSpeed ? (dist[pos]-dist[seg]) / (float)(int)MoveSpeed
                 : SpeedCalcType==cTime  ? MoveTime : 1.0                  // 0x7101305b40

// 0x71013043d8 시간 평가 (t = 리프트 시간, 초)
t = max(t,0)
cStop:     te = min(t, WaitTime + 주기)
cContinue: u = t - WaitTime; if u > 0: u = u - 주기*(int)(u/주기); if u<0: u += 주기
           te = WaitTime + u          (주기 == 0 이면 te = 0)
항목 = start <= te 인 마지막 항목 → 처리 함수(te - start, pos, rev)

// 이동 0x7101304cec
seg = prev(pos,rev); D = moveDur(seg,pos); x = (D==0) ? 1 : τ/D
if InterpolationType==cSin: x = (sin(x*3.1415927 - 1.5707964) + 1) * 0.5
s = x * (dist[pos]-dist[seg]) + dist[seg]
AttCalcType: cInMove → 자세 = rail.poseAt(s)(+0x90)                       (v0 Carousel 은 기본값 cInMove)
             cInBreak → 위치 = rail.posAt(s)(+0xa0), 회전 = 출발 점(seg) 자세(+0x40)의 회전
             cTangent → poseAt(s) 후 Z열 = normalize(tangent(s))(+0xa8), X열 = normalize(Y열 × Z), Y열 = Z × X
                        (반환값 = |tangent|>0 && |Y×Z|>0)
// 점 대기 0x7101304984: cInMove → 점 행렬, cInBreak → 위치 = 점, 회전은 BreakTime 동안 seg→pos 회전 보간, cTangent → 점의 접선 기저
// 시작/끝 0x71013046f4: 점 행렬(cTangent면 접선 기저)
```

- WaitTime은 **처음 한 번만** 쓰는 지연입니다. 이후에는 점마다 BreakTime만 쉽니다. 시작 점의 BreakTime은 첫 바퀴에 쓰이지 않습니다.
- 시간은 초 단위 f32 누적(`프레임수 * 0.016666668`)입니다. 시간 원점(+0x1a0c 초기값)은 액터별 상태 보관 객체([액터+0x348]+0x20 의 +0x18)에서 받고, 같은 객체로 되쓰며(`0x710147a6d0`), 모드 2 직렬화(`0x710147a9a0`/`0x710147a9fc`)로 저장·복원됩니다 [판독]. 보관 객체의 생성 시 초기값은 판독하지 않았습니다 **[미확정 — 0으로 둠, 추정]**. 발판은 넷 복제 대상이 아니고(RSDB `MapObjReplicaInfo`에 `Lft_*` 행 없음, 액터 팩에 `spl__ReplayParam`만 있음 [데이터]) 각 기기가 같은 일정을 로컬로 돌립니다 [데이터+추정]. 모드 2 직렬화가 리플레이용인지는 **[추정]**.
- 2026-10-02 3차: 레일 위치 함수(+0xa0 → `0x71012ffeac`)를 판독했습니다. 점 사이에 제어점이 없으면(점 +0x1c NaN) 구간은 직선 세그먼트(vt `0x7105577ac0`, 길이 = 두 점 거리, 구간 비율 `clamp(sLocal/len, 0, 1)` `0x71013016a0`)이고 위치는 두 점 선형 보간 `0x7103db69e4` → `0x7103db6c20`입니다. 이전 판의 "직선 선형 보간 [추정]"은 **[판독]**으로 올립니다. 제어점이 있는 구간(Bezier, vt `0x7105577a60`, 31분할 호 길이표)은 v0 대전 레일에 없습니다 [데이터].

### 1.4 Carousel 재구현 결과 [재구현 — `PY web/tools/gimmick_lift.py Vss_Carousel`]

| 발판 | 일정(시작초 종류 점) | 주기 |
|---|---|---|
| MoveA (WaitTime 4, MoveTime 4, BreakTime 30/22, cContinue) | 0 시작@0 → 4 이동→1 → 8 대기@1(22초) → 30 이동→0 → 34 대기@0(30초) → 64 = 4와 같은 상태 | 60초 |
| MoveB (WaitTime 없음=0, MoveTime 8, BreakTime 22/22) | 0 이동→1 → 8 대기@1 → 30 이동→0 → 38 대기@0 → 60 = 0과 같은 상태 | 60초 |

표본: MoveA Alpha t=6 → 위치 (2.75, 0.05, 1.5), t=8~30 → (5.5, 0.05, 3), t=66 → (2.75, 0.05, 1.5)(= t=6). Bravo는 부호 반대. 두 발판 모두 60초 주기라 같은 박자로 움직입니다.

### 1.5 좌표계·회전 [판독 — 2026-10-02 3차 해소]

이전 판의 "[추정/미확정]"을 아래 판독으로 해소합니다. 디컴파일 `analysis/decomp/stage/lift_rail_matrix.c`, `lift_rail_class.c`.

**레일 객체**(`LiftRail`, 팩토리 이름 `0x710130279c` "LiftRail", 해시 `0xcf150159`, 크기 0x110, vtable `0x7105577bc8`; 생성자 `0x7101301c24`, 초기화 `0x71012fecec`). 기준 객체 = 레일 객체(어댑터 +8). 행렬은 **열 우선 9 float**(열 i = +0x0c·i)이고 곱 `0x7101250a80(A,out,B)` = A·B입니다.

| 오프셋 | 의미 | 초기값(생성자) | writer |
|---|---|---|---|
| +0x08 | 레일 데이터(Banc 점 배열 +0x18 stride 0x50, 점 수 +0x10, 닫힘 +0x40) | | 초기화 |
| +0x30 / +0x38 / +0x40 | 세그먼트 배열 / 누적 거리 개수 / 누적 거리 배열 | | 초기화 |
| +0x88 (T0), +0x94 (R0) | 부모 **초기** 자세 | (0,0,0), 단위 | 생성자만 |
| +0xb8 (T1), +0xc4 (R1) | 부모 **현재** 자세 | (0,0,0), 단위 | 생성자만 |
| +0xe8 | 레일 회전 R_rail | 단위 → Banc `Rails[].Rotation`으로 덮어씀 | `0x71012fecec` |

- 단위 상수: `0x7105823b50` = {위치 0, 회전 = `0x71058237b0`}(정적 초기화 `0x71012542a0`), `0x71058237b0` = 단위 3×3(`0x710124f6c4`가 1.0을 [0],[4],[8]에 기록) [판독].
- `LiftRail` vt+0x48(초기화 끝에서 호출)은 빈 함수 `0x7101300ac4`이고, 대전 범위에서 +0x88/+0xb8 계열을 다시 쓰는 코드는 찾지 못했습니다 → **LiftRail의 부모 변환은 단위 = 점 좌표가 곧 월드 좌표** [판독, 다른 부모 연결 경로 부재는 범위 검색 결과].
- `Rails[].Rotation`은 **라디안** 그대로, 순서 **R = Rz·Ry·Rx**(x = Rotation[0])입니다(`0x71012fecec`의 sin/cos 조합: +0xe8 열0 = (cy·cz, cy·sz, −sy) …) [판독].

**점 자세**(`0x7101301d58`, 점 vt+0x28): 회전(+0x34, 복사본 +0x64) = R_rail · Rz·Ry·Rx(노드 `game__LiftGraphRailNodeParam.Rotation` × 0.017453292 — **도 단위**, 필드 +0x34 vec3, 플래그 +0x41), 위치(+0x28, 복사본 +0x58) = Banc 점 Translate [판독]. 노드 Rotation은 v0 대전 데이터에 없습니다 [데이터].

**거리 s의 위치**(`0x71012ffeac`):
```
s' = closed ? s mod total : clamp(s, 0, total)          // total = 누적 거리 끝
i  = s'가 속한 구간(끝이면 n-2), u = seg[i].param(s' - dist[i])   // 직선: clamp(sLocal/len,0,1)
p  = lerp(point[i].pos, point[i+1].pos, u)               // 0x7103db69e4 → 0x7103db6c20
out = R1 · R0ᵀ · (p − T0) + T1                           // LiftRail 은 단위 → out = p
tangent(s) = R1 · R0ᵀ · normalize(dp/du)                 // +0xa8
```
**거리 s의 회전**(`0x710147b7a8`): `slerp(point[i].rot, point[i+1].rot, u)`. slerp `0x7101250f0c` = 행렬→쿼터니언(`0x71010176bc`), d = clamp(q0·q1, −1, 1), θ = acos|d|, |sin θ| < 1.1920929e-07이면 선형 가중, d < 0이면 q1 쪽 가중 부호 반전(최단 경로) → 행렬. 부모 회전 R1·R0ᵀ는 **회전에는 곱하지 않습니다**(위치에만) [판독].

**최종 출력**(`0x7101479f7c`): 위치 = 위 자세 위치, 회전 = 자세 회전 · SequentialRotate 회전(`0x71012eeb98` 결과 +0x1998). `game__SequentialRotateParam {}`(Carousel 전부 빈 값)은 생성자 `0x71012c9714` 기본값이 회전 벡터 (+0x30, +0x44) 모두 0이라 회전 각속도 0 → **단위 회전** [판독].

**Bravo 발판 회전 출처**: Bravo 레일 `Rotation` = (π, −8.74e-8, π) → R_rail = Rz(π)·Ry(≈0)·Rx(π) = diag(−1, 1, −1) = **Y축 180°**. 노드 회전이 없으므로 모든 점 회전이 R_rail이고 slerp 결과도 상수입니다. 즉 Bravo 발판의 출력 회전은 **레일 Rotation에서 오며**, 액터 배치 `Rotate`(같은 (π,0,π), Vlf·Vcl MoveB는 (−π,0,π−ε)로 같은 회전)와 일치합니다 [판독+데이터]. 액터 `Rotate`가 이 출력과 별도로 곱해지는지(출력이 액터 행렬을 대체하는지)는 소비 쪽을 판독하지 않았습니다 — 레일 회전 = 배치 회전이 16개 전부 성립하므로 **대체로 구현** [추정 — 데이터 일치].

재구현 `PY web/tools/gimmick_lift.py Vss_Carousel --t 0,6,8,30,66`(결과 `analysis/stage/lift_sim_carousel_rot.json`) [재구현]: Alpha MoveA t=6 → 위치 (2.75, 0.05, 1.5), 회전 단위; Bravo MoveA t=6 → (−2.75, 0.05, −1.5), 회전 [[−1,0,0],[0,1,0],[0,0,−1]](yaw −180°). 원본 실행 대조는 없습니다.

웹 구현: `RailMover`(웹 이름) = §1.3 일정 + 위 자세 식. 레일 로더는 `Rails[].Rotation`(라디안, Rz·Ry·Rx)과 노드 `Rotation`(도)을 점 회전에 반영하고, 회전 보간은 쿼터니언 slerp(최단 경로). 서버·클라이언트가 같은 시간 원점을 쓰면 결정적입니다(원점 초기값은 0으로 둠 [추정]).

## 2. 고정 맵 파츠 (Mpt_*) [데이터]

모드마다 지형을 막거나 여는 고정 충돌 파츠입니다. 배치 이름이 `Lft_...`인 것이 많고 `spl__LiftBancParam`, `game__RailMovableSequentialParam {}`(빈 값)을 가지지만 이동 파라미터가 비어 있어 움직이지 않습니다. 레이어(모드)별로 다른 세트가 생성되는 것이 핵심입니다(예: Yagara Vgl 23개, Vlf 10개). 목록은 `analysis/gimmick/<스테이지>_summary.json`의 `static_lift_parts`.

웹: 모드 레이어 선택 시 해당 파츠의 충돌 형상(bphsh)과 모델(fmdb)을 함께 생성. 파츠 bphsh도 전부 hknpMeshShape이며 `web/tools/collision_mesh.py`로 변환됩니다([collision_mesh.md](collision_mesh.md)) [데이터].

## 3. 장외·사망 판정

### 3.1 박스 액터 [데이터]

| 액터 | 형상 | 재질 프리셋 → UserShapeTag | 레이어 히트마스크 |
|---|---|---|---|
| `Mpt_KeepOutPlayer` | 단위 박스(±0.5) × 배치 Scale | `SplKeepOutPlayer`(KeepOut), `PlayerUnsafe` | `SplKeepOutPlayer` = 98 = 비트 1,5,6 (CustomReceiver, SplPlayer, SplPlayerChariotShield) |
| `Mpt_PlayerDead` | 단위 박스 × Scale | 위 + `PlayerDead` | 같음 |

- 플레이어만 막는 투명 벽입니다(탄·카메라 레이어 비트 없음) [데이터 — PhiveConfig `LayerHitMaskEntityCollection`].
- 사용처: Yagara Vlf 12개(야구라 경로 주변, 예: (-11.9,2.5,11.25) 크기 3×6×4.5), Yunohana Vlf 20, Temple00 Vlf 16 + **Cmn PlayerDead 10개**(Y=51, 크기 12×3×18 — 맵 위 높은 곳), Scrap00 Vlf 16, Kaisou03 Vlf 10, District00 Vlf 8, Carousel Vlf 2 [데이터].
- `PlayerUnsafe`/`PlayerDead` 태그를 플레이어가 어떻게 해석하는지(즉사, 안전 위치 기록 제외 등)는 [player]/[combat] 소관 **[미확정]**.

**`Obj_LobbyKeepOutPlayerInSpecial`(로비, 2026-10-03 6차 [r6 assets])** — 형상은 위와 같은 단위 박스(ShapeParam `Box` 1개, HalfExtents 없음 → AutoCalc Min/Max = ±0.5 [데이터]), 프리셋 `SplKeepOutPlayer`·`PlayerUnsafe`, 몸 레이어 Ground·`EnableLayerHitMask SplKeepOutPlayer` [데이터]. 동작 클래스 `spl::ObjLobbyKeepOutPlayerInSpecial`(vt `0x71055fa488`, 생성 `0x7101f6a71c`) [판독]:

| 슬롯 | 주소 | 내용 |
|---|---|---|
| 8 | `0x7101f6a868` | 강체 핸들 +0x108 = `0x7103a102f0(+0x110, 0)` |
| 18 | `0x7101f6a898` | 매 프레임: 플레이어 관리자(`*0x7105791bd0` +0xd470 인덱스)에서 메인 플레이어를 찾아, 그 상태 +0x24 가 7~11 이 아니면 `0x7101701040`이 준 플레이어 객체의 [+0x108]+0xbf0 을 읽어 `v = (그 값 < 1)`, 그 밖(플레이어 없음·상태 7~11)은 `v = 1`. 끝에서 `0x7103ae4c48(강체, v)` |

- `+0xbf0`은 본체 기준이면 `specialFramesLeft`(스페셜 남은 프레임, [../paint/special_gauge.md](../paint/special_gauge.md) §표 +0xbf0)입니다. 여기서 읽는 객체가 본체(D)인지는 `0x7101701040` 반환값의 +0x108 이 본체라는 가정입니다 **[추정]**.
- `0x7103ae4c48(바디, bool)`은 바디 +0x88 비트11(0x800)을 켜고 끕니다([../combat/hitbox.md](../combat/hitbox.md) — 비트 의미 [미확정]). 같은 함수를 리스폰 무적이 끝나는 프레임에 (…, 0)으로, 슈퍼훅 cAttack 진입에 (ColBullet, 0)으로 부르므로 **1 = 판정 끔**으로 읽는 것이 일관됩니다 **[추정]**.
- 따라서 이 벽은 **스페셜을 쓰는 동안(남은 프레임 ≥ 1)만 켜지고 평소에는 꺼져 있다**는 것이 이름과 일치하는 해석입니다 — 조건식은 [판독], 비트11 의미와 객체 정체는 [추정]. 웹 에셋은 이 박스를 정적 충돌에서 뺐습니다(평소 상태와 같음).

### 3.2 지형 충돌 재질 [데이터]

지형(`Fld_<스테이지>`)의 충돌은 액터 팩 안 `Phive/Shape/Dcc/Fld_*.Nin_NX_NVN.bphsh` 하나입니다. 파일 끝의 재질표를 `web/tools/gimmick_phive.py`로 읽었습니다(결과 `analysis/gimmick/fld_phive_materials.txt`).

- 재질표 항목 = (MaterialCollection 인덱스, UserShapeTag 비트마스크). 이름은 `romfs/Phive/Config/PhiveConfig.byml.zs`(`analysis/gimmick/PhiveConfig.json`).
- 대전 판정에 중요한 태그: `Water`(물, 재질 Water), `PlayerDead`, `KeepOut`, `BombDead`/`TripleTornadoDeviceDead`(투척물 소멸), `Fence`(철망: 재질 Fence/RopeNet, 프리셋 `SplFence`는 잉크 통과 `SplInkThrough`·오징어 통과 `SquidThrough`), `FillUp`, `Slide`, `ForceColPaintNotPaintable`/`ForceColPaintPaintable`/`ForceColPaintYPlus`(칠 가능 여부 강제), `IgnoredByMiniMap`/`MiniMapOnly`.
- Yagara 예: 14번 Water+BombDead+TTDDead(수로), 16번 KeepOut+PlayerDead+BombDead(장외 바닥), 17~20번 NotPaintable(Vinyl/Plastic/Stone/Wood), 8번 RopeNet+Fence.
- 삼각형별 재질(shapeTag) 매핑, 재질별 삼각형 수·면적·높이 범위, 필터표 이름은 [collision_mesh.md](collision_mesh.md) §4. `FillUp`·`KeepOut` 면은 필터가 `SplKeepOutPlayer`(플레이어만 막음)인 수직 벽입니다 [데이터].
- 수면: `Vss_YagaraWater.game__gfx__parameter__Ocean` `OceanHeight 0.0`은 그래픽 수면 높이 [데이터]. 충돌 쪽 Water(14번) 면은 맵 전체를 덮는 **y=-0.05 평면**입니다 [데이터]. 물에 빠짐 판정이 이 면과의 접촉인지는 [player] 소관 **[추정]**.

### 3.3 사망 이유 열거형 [판독]

열거형 등록 코드는 이름 문자열을 기록한 직후 그 열거형의 정보 함수를 부르고, 정보 함수가 값 목록 문자열을 파싱합니다(RailPatrolType과 같은 패턴, §1.2).

| 열거형 | 이름 참조 → 정보 함수 | 값 (0부터) |
|---|---|---|
| `spl::PlayerDeadReason` | `0x710346ba10` → `0x710349f98c` | Unknown, Die, AirFall, WaterFall, KebaInkFall, Vanish |
| `spl::DamageReasonOtherId` | `0x71034605f4` → `0x710349a028` | Unknown, Blood, StepPaint, AirFall, WaterFall, GachihokoTimeUpBurst, GachihokoBarrierBurst, GachihokoBarrierBump, SalmonBuddy, InkBar, DamageConveyor |

이전 판의 "세 후보 중 미확정"을 위와 같이 정정합니다. 9748행 목록은 사망 이유가 아니라 **무기 외 피해 원인 ID**입니다. 18291행("Other , Timer , ... GotByPlayer")은 호코 관련 다른 열거형입니다(이름 미확인). 각 값을 어떤 조건에서 쓰는지(낙하 판정 높이, 물 접촉 등)는 [player]/[combat] 소관 **[미확정]**.

## 4. 칠 가능 영역

- `ChangePaintableArea`(Locator, 팀·Scale 박스): Yagara 78개(레이어별). 소비는 `spl::paint::ColPaintBuilder::setupChangePaintableArea_`(문자열 확인) → [paint] 소관 [데이터].
- 지형 재질 태그 `ForceColPaint*`(§3.2)도 칠 가능 여부를 정합니다.
  - 2026-10-03 6차 정리(원본 판독은 도색 문서 근거): 지형 아틀라스 생성 단계 `0x7102c0725c`는 MaterialCollection 21(Fence)·22(RopeNet) 삼각형과 UserShapeTag bit50(`ForceColPaintNotPaintable`) 삼각형을 버리고, bit48(`YPlus`)은 위 방향으로 강제하며, **bit49(`ForceColPaintPaintable`)는 보지 않습니다** [판독]+[실행] ([../paint/colpaint_atlas.md](../paint/colpaint_atlas.md) §4.1). 이 단계는 레이어(Ground/KeepOut 등)로 거르지 않습니다. 어떤 충돌(강체)이 대상 목록에 들어가는지(강체 +0x230 도색 대상 정보)는 [r6 paint] 진행 중이며 **[미확정]**입니다.
  - 요청 단계: 접촉 재질 UserShapeTag bit29 `KebaInkCore`·bit30 `KebaInk`가 있으면 그 탄은 칠하지 않습니다 [판독] ([../paint/paint_and_score.md](../paint/paint_and_score.md) §3.3).
  - 로비 `Lby_Lobby00` 충돌(웹 collision.json 52재질, 삼각형 6329)에는 `ForceColPaint*`·`KebaInk*` 태그가 하나도 없습니다 [데이터]. 로비에서 원본 규칙과 웹 `paintable`(layer == Ground)이 갈리는 곳은 Fence(재질 Fence, 460삼각형 — 둘 다 칠 불가)가 아니라 **KeepOut·PlayerThrough·CameraThrough·KeepOutBullet·Other 레이어 삼각형(합 902)** 쪽입니다. 원본 아틀라스 단계는 레이어로 거르지 않으므로 이 삼각형의 칠 여부는 대상 강체 목록에 달려 있습니다 [미확정].
- `PaintTargetArea_Cube`(Var 레이어, 예 Yagara (0,4,0) 크기 22×5×17)는 가치에리어 영역 [데이터, 소관: 모드 규칙].

### 4.3 충돌 메시 [판독+데이터 — 해소]

2026-10-02 해소·정정: bphsh 본문은 압축 메시(hknpCompressedMeshShape)가 아니라 **`hknpMeshShape`**입니다. TAG0 파서와 메시 디코더를 만들어 Yagara 지형을 삼각형 5103개 + 삼각형별 재질로 변환했고 glb로 출력했습니다. 형식·디코드 규칙·검증·웹 구조는 [collision_mesh.md](collision_mesh.md).

## 5. 스폰·시작 위치 [데이터]

| 액터 | 의미 | 연결 |
|---|---|---|
| `LocatorVersusStart` | 경기 시작 위치(팀별) | `LocalLocator` StartPos0~3 |
| `LocatorSpawner` | 리스폰 지점(팀별) | `spl__LocatorSpawnerBancParam.ToTarget_Cube` → `LocatorSpawnerTargetCube`(Scale 박스, 슈퍼점프 착지·방향 영역 [추정]) |

`StartPos0..3` 국소 오프셋: (2.4,0,0.3), (0.8,0,-0.3), (-0.8,0,-0.3), (-2.4,0,0.3) — 4인 배치 [데이터]. 월드 위치 = Translate + R(Rotate)·오프셋. 레일 `Rotation`은 R = Rz·Ry·Rx(라디안)로 판독했고(§1.5), 액터 `Rotate`도 같은 규약으로 둡니다 ~~[추정 — 같은 Banc 형식, 액터 행렬 생성 함수는 미판독]~~. (π,0,π)·(0,0,0) 배치에서는 순서와 무관합니다.

정정(2026-10-03, 6차 [r6 assets]): 액터 행렬 생성 함수를 찾아 원본 실행으로 확인했습니다. 액터 `Rotate`도 **R = Rz·Ry·Rx(라디안, x = Rotate[0])**이고 3×3은 **행 우선**으로 저장됩니다 **[실행]+[판독]** — §5.1.

### 5.1 Banc 액터 배치 → 생성 정보 → 액터 [실행]+[판독 — 2026-10-03 6차]

| 단계 | 주소 | 내용 |
|---|---|---|
| Banc 엔트리 파서 | `0x7103d03768`(호출 `0x7103cfdcd4`, 함수 `0x7103cfd608` 안) | BYML 키를 엔트리(스택 sp+0xa0)에 그대로 옮김: +0x00 `Translate` f32×3, +0x0c `Rotate` f32×3(라디안 원값), +0x18 `Scale` f32×3, +0x28 `Gyaml` 문자열, +0x38 `Hash`, +0x74 `Gyaml`이 "Work/"로 시작하지 않음, +0x75 유효(시작 시 0). 각 성분은 BYML 형식 0xd2(f32)일 때만 씀 [판독] |
| 생성 정보 채우기 | `0x7103d03f4c(엔트리, 생성 정보, 부모 3×4)` — 람다 vt `0x710575cdf0` 슬롯0 `0x7103d01298`이 부름 | 엔트리 +0x75 == 0 이면 0 반환. 아니면 생성 정보 +0x40 위치 = P·T + P.t, +0x4c 3×3 = P.R · R(Rotate), +0x70 Scale = 엔트리 +0x18 그대로(곱하지 않음), +0x98/+0xa0/+0xb0~+0xcf 등 나머지 복사 [판독] |
| 부모 3×4 P | 씬 섹션 객체(배열 관리자 +0x150, 0x2f0 B 간격) +0x260, 행 우선 3×4(평행이동 = [3],[7],[11]) | 섹션 생성 `0x7103cfa6bc~0x7103cfa6d0`이 단위 행렬(`0x7104a98200`)로 초기화. `0x7103cfc140(…, x6=행렬)`이 x6 이 있으면 그 값, 없으면 단위로 다시 씀. 호출자 `0x7100fcdda8`은 x6 = 0(단위), `0x71030e1290`(SplVersusResult / NewsStudio / SplCoopStartDemo 데모 씬)만 스택 행렬을 넘김 [판독]. 0x7103cc0000~0x7103d10000 범위에서 섹션 +0x260 의 다른 writer 는 없음 [판독, 범위 검색] → **로비·대전 맵의 P = 단위** |
| 액터 초기화 | `0x7103cc30c4`(액터 [+0x348] = 생성 정보) | 액터 +0x28c 위치, +0x298..+0x2b8 회전 3×3(행 우선), +0x2bc 스케일, 초기값 사본 +0x25c 위치·+0x268..+0x288 회전 [판독] |

```
// 0x7103d03f4c — 행렬은 행 우선. sx = sinf(Rotate.x) … (SDK sinf/cosf, PLT 0x7103e9be40/0x7103e9be30)
R = | cy·cz   (sx·sy)·cz − sz·cx   sx·sz + sy·(cx·cz) |       = Rz(z)·Ry(y)·Rx(x)
    | sz·cy   (sx·sy)·sz + cx·cz   sy·(sz·cx) − sx·cz |
    | −sy     sx·cy                 cx·cy             |
pos  = P[:, :3]·T + P[:, 3]           // ((p0·Tx + Ty·p1) + Tz·p2) + p3 순서, FMA 없음
rot  = P[:, :3]·R                     // 원소별 곱·덧셈 순서는 r6_assets_actor_mtx_emu.py reimpl() 그대로
scale = Scale                          // 행렬에 곱하지 않고 따로 보관
```

- **검증** `PY web/tools/r6_assets_actor_mtx_emu.py` → `analysis/completion/r6/assets_actor_mtx_emu.json`: 원본 `0x7103d03f4c`를 unicorn으로 실행했습니다. 표본 4257건(로비 placement 257액터 실제 값 + 무작위 3000 + 단위가 아닌 부모 1000). 6가지 오일러 순서 × 행/열 우선 후보 중 **Rz·Ry·Rx · 행 우선이 4257/4257 최적**(최대 오차 1.3e-7), 명령 순서를 그대로 옮긴 f32 독립 재구현과 **위치 3·회전 9 원소 4257/4257 비트 일치**, 스케일 복사 4257/4257, 위치 불일치 0 [실행]. 순진한 f32 식(곱 순서 다름)은 2199/3257만 비트 일치합니다. 스텁: sinf/cosf 는 SDK(`extracted/exefs/sdk.img`) 원본 함수를 unicorn 으로 실행해 돌려줌(이름 기준 연결), 그 밖 PLT 호출 없음, 생성 정보를 0 으로 채워 `0x7103515cfc` 경로(+0xa8 bit7·+0xf8)는 타지 않음.
- 레일 `Rotation`(§1.5 `0x71012fecec`)과 같은 규약입니다. 로케이터 판정이 읽는 생성 정보 +0xc..+0x2c([../range/shooting_range.md](../range/shooting_range.md) §6.6의 "생성 정보")는 이 표의 +0x4c..+0x6c(위치 +0x40 기준 +0xc)와 같은 칸이고, 행 우선 R 입니다.
- **배치 행렬 T·R·S의 S 위치는 [미확정]**: 생성 정보·액터는 T, R(3×3), S 를 따로 보관하고 이 단계에서 S 를 곱하지 않습니다 [판독]. 액터 스케일이 바뀌면 `0x7100f76f78`(액터 갱신, `0x7100f78038~0x7100f780e8`)이 +0x2bc 를 쓰고 컴포넌트 목록(+0x208, 개수 +0x200)의 vt+0x50(이전, 새 스케일)을 부릅니다 [판독]. 모델 쪽 루트 행렬 설정 `0x7100f735b0`은 3×4의 열 길이를 축 스케일로 분해하므로 모델 행렬 = [R·diag(S) | T] 형태입니다([../graphics/player_assembly.md](../graphics/player_assembly.md) §6.1, [실행]). 액터 S 가 모델 유닛 스케일·Phive 형상에 어떻게 들어가는지(vt+0x50 수신자)는 추적하지 않았습니다 — 다음: 컴포넌트 vt+0x50 구현 중 모델 유닛 +0x268..+0x270 을 쓰는 것.

리스폰 지점 **선택 규칙**(여러 Spawner 중 무엇을 쓰는지, 슈퍼점프 착지 박스 처리)은 [respawn] 담당 소관입니다. 이 문서는 배치 데이터만 제공하며, 조율 내용은 `analysis/notes/SHARED.md`([stage] 2026-10-02 3차 항목)에 올렸습니다.

Yagara: VersusStart Alpha (7.5,13.5,76.5) Rotate (π,0,π) → 4명 (5.1,13.5,76.2)…, Bravo (-7.5,13.5,-76.5); Spawner Alpha (7.5,33.5,106.5), Bravo (-7.5,33.5,-106.5) (Vgl은 z=±110, ±79). 트리컬러(Tcl)에는 Charlie (7.5,33.5,74)가 추가됩니다 [데이터]. 리스폰 동작(낙하 연출, 무적) 코드는 [combat]/[player] 소관.

## 6. 기타 오브젝트 [데이터, 동작 미확정]

| 액터 | 스테이지 | 비고 |
|---|---|---|
| `Obj_YagaraBox00~05` | Yagara 48개 | `spl::WallaObjGroupProc`, 넷 복제(RSDB MapObjReplicaInfo), SenderPolicy Anyone — 밀리는 소품 [추정] |
| `Obj_RollingCone` | District00 4개 | MapObjReplicaInfo 행 있음 |
| `DObj_Guillotine`, `DObj_GantryCrane` | Scrap00 | DesignerObj 애니 |
| `LocatorSuperJump*Area/SafePos*` | Carousel | 슈퍼점프 착지 보정 |
| `GeneralLocator` | 전 스테이지 | 스펀지 `SafePosLinks` 대상 등 |

## 7. 히어로 모드 기믹 (대전 v0 배치 없음) [판독 범위: 파라미터·클래스, 간헐천·점프대 동작 일부]

대전 Banc 8개에는 점프대·간헐천·파이프라인·그라인드 레일이 없습니다 [데이터]. 플레이어 쪽 파라미터는 `SplPlayer.game__GameParameterTable`에 있어 클래스·파라미터만 정리합니다.

| 기믹 | 오브젝트 클래스(vt) | 플레이어 클래스(vt) | 파라미터(SplPlayer 데이터 / 기본값) | 상태 |
|---|---|---|---|---|
| 그라인드 레일 | (미확인) | — | `spl__PlayerGrindRailParam`(방문 `0x7102389e58`): AerialVelYToBind -0.05, AutoFinish_CheckDist 0.001, AutoFinish_VelY 0.05, AutoJumpFinishNoBindFrame 60, BindDistY 0, FinishNoBindFrame 10, FinishPlayerVelRateY 0.5, GndCol_FallNoBindFrame 60, GndCol_Radius 0.3, PlayerJumpSpeed 0.145, PlayerSideJumpEndFix 0 / 기본 PlayerAcc 0.05, PlayerSpeedMax 0.2 등 | — |
| 점프대 | — | `spl::PlayerJumpGimmick`(`0x710563d230`) | `spl__PlayerJumpGimmickParam`: JumpDisableFrm 24(기본 12), JumpGndFrm 5, PreInputAcceptFrm 24 | — |
| 간헐천 | `spl::Geyser`(`0x710560deb8`) | — | `spl__PlayerGeyserParam`: BindToRoofMinSec 0.05, JumpVelAtRoof 0.12 / PlayerBindVel 0.25, PlayerBindLerpRate 0.05, BindEndStickLen 0 | Wait, Extend, KeepMaxHeight, Shrink (`0x71021550a0`) |
| 파이프라인 | `spl::Pipeline`(`0x7105613b50`) | `spl::PlayerPipeline`(`0x710563e1b0`) | `spl__PlayerPipelineParam`: DarkenDelaySec 0.79, FinishSec 0.5, FinishVel 0.28, MoveAcc 0.05, OpenEndDistance 8, StartSec 0.8, StartSplashStartOffsetZ 0.5, StartAttCurve Hermit [0,2.176,1,0,1,0], ModelOffsetY/Z 커브 / MoveVelMax 0.4, NoCameraControlSec 1.0 | 오브젝트 Closed, Open, CloseOmen, ExitOpen (`0x71021d4740`); 플레이어 Free, Start, RailMove, Finish (`0x710267168c`) |

- 플레이어 상태 열거형에 `Human_DokanWarp`, `Human_GrindRail`, `Squid_InkRail`, `Squid_Geyser`, `Squid_Pipeline` 등이 있습니다(main_strings 47712행) [데이터].

### 7.1 리플렉션 커브 필드 오프셋 정정 [판독 — 2026-10-02 3차]

원인: `param_reflect.py`는 방문 함수의 `add xN, this, #imm`을 나온 순서로 모아 이름을 만나면 [값, 플래그]로 씁니다. 커브 필드(타입 `0x7105553c68`)는 방문 코드가 **값 포인터 → 이름 → 플래그 포인터** 순서라서 커브의 플래그가 다음 필드의 값으로, 다음 필드의 값이 플래그로 밀립니다. 새 도구 `web/tools/gimmick_reflect_fix.py`는 블록(방문자 `blr` 사이)마다 `str xF,[sp,#0x18]` = 플래그, `stp xT,xV,[x29,#-0x10]`의 값, `str wK,[sp,#0x20]` = 순번으로 역할을 정합니다. 결과 `analysis/stage/hero_param_reflect_fix.txt`.

| 구조체(방문 함수) | 필드 | 정정 전(param_reflect) | 정정 후 (값 / 플래그 바이트) |
|---|---|---|---|
| `spl__PlayerGrindRailParam` (`0x7102389e58`) | SideJumpCurve | +0x30 / 없음 | +0x30 / +0x13c |
| | PlayerSideJumpGndColOffsetY | +0x13c / 0xd0 | **+0xd0 / +0x13d** |
| `spl__PlayerPipelineParam` (`0x7102429e2c`) | StartPosCurveXZ | +0x90 / 없음 | +0x90 / +0xf9 |
| | StartPosCurveY | +0xf9 / 0xb0 | **+0xb0 / +0xfa** |
| | StartAttCurve | +0xfa / 0x70 | **+0x70 / +0xfb** |
| | StartSplashStartOffsetZ | +0xfb / 0xf4 | **+0xf4 / +0xfc** |
| | ModelOffsetZ | +0x50 / 없음 | +0x50 / +0x105 |
| | ModelOffsetY | +0x105 / 0x30 | **+0x30 / +0x106** |

나머지 필드(GrindRail 56개, Pipeline 9개, `spl__PlayerGeyserParam` 5개, `spl__PlayerJumpGimmickParam` 3개)는 두 도구 결과가 같습니다. 표 §7의 GrindRail·Pipeline 값 자체는 SplPlayer **데이터** 값이라 영향이 없고, 코드가 읽는 오프셋을 볼 때만 위 정정표를 쓰세요. 같은 결함이 다른 영역의 커브 필드 구조체에도 있을 수 있습니다(공용 도구 수정은 담당 밖, SHARED.md에 알림).

### 7.2 간헐천 spl::Geyser 동작 [판독 — `analysis/gimmick/annot/gimmick_b2.c`]

파라미터(정정 도구로 판독, 방문 `0x7102052b50`, 기본값 = 생성자 `0x71020529f4` 즉시값, 기준 = GeyserParam 객체 = 액터 +0x1b8):

| 오프셋 | 필드 | 기본값 | Geyser 데이터 |
|---|---|---|---|
| +0x68 | ExtendAcc | 360.0 (유닛/초²) | |
| +0x6c | ExtendKd | 0.98 | |
| +0x70 | ExtendVel | 18.0 (유닛/초, 상승 속도 상한) | |
| +0x74 | KeepMaxHeightSec | 5.0 | |
| +0x78 / +0x7c | OmenEffectIntervalSec / OmenEffectTotalSec | 1.0 / 3.0 | |
| +0x88 | ShrinkAcc | 32.4 | |
| +0x8c | ShrinkVel | 30.0 | |
| +0x54 | BodyRoofWaitOffsetY | −0.2 | −0.02 |
| +0x50 / +0x90 | BindDistanceFromPillarCenter / StartBindOffsetY | 1.2 / 0.1 | 1.5 / 0.3 |
| +0x5c / +0x60 / +0x64 | DamageToEnemy / ToMapObj / ToPlayer (s32) | 10000 / 15000 / 10000 | |
| +0x30 | TopPosOffset (커브) | | Sin [0.5, 0.2], MaxX 2.0 |

`spl__GeyserBancParam`(방문 `0x7102051be0`): +0x34 **MaxHeight**(플래그 +0x38), +0x30 InkTeam(+0x39).

상태(등록 `0x71021550a0`, 상태머신 this+0x198, 상태 프레임 = 머신 +0x3c): 0 Wait(enter `0x7102155e1c`, exec `0x7102156070`, exit `0x7102156274`), 1 Extend(`0x71021562a4`, `0x7102156674`), 2 KeepMaxHeight(`0x7102156d58`, `0x7102156ee8`), 3 Shrink(`0x7102157630` 빈 함수, `0x7102157634`).

```
h = this+0x13c (기둥 높이), v = this+0x140 (높이 속도), dt = 프레임 수(인자)
Extend exec:   v = v*ExtendKd;  v += ExtendAcc*dt/60;  v = min(v, ExtendVel)
               h = min(h + v*dt/60, MaxHeight)
               top(+0x14c) = 액터 위치 + h * 액터 Y축(회전 열 +0x29c/+0x2a8/+0x2b4)
               h - MaxHeight >= -1.1920929e-07 → 상태 2
KeepMaxHeight: 상태 프레임/60 >= KeepMaxHeightSec → 상태 3
               남은 초 int(KeepMaxHeightSec - 프레임/60) ∈ [0, OmenEffectTotalSec] 이면
               OmenEffectIntervalSec 간격으로 이펙트 "Omen"(위치 = top)
Shrink exec:   v += -ShrinkAcc*dt/60;  v = max(v, -ShrinkVel);  h = max(h + v*dt/60, 0)
               |h| <= 1.1920929e-07 → 상태 0
Wait exec:     지붕 형상(+0x130) 위치 = top(+0x14c) + (0, BodyRoofWaitOffsetY, 0), 나머지 형상(+0x118..+0x128) = top
```
- `ExtendKd`는 dt와 무관하게 호출마다 1회 곱합니다(원본 그대로) [판독].
- Wait → Extend 진입 조건(잉크 피격·InkTeam)은 이번에 추적하지 않았습니다 **[미확정]**.

### 7.3 점프대 spl::PlayerJumpGimmick 발사 조건 [판독-부분]

플레이어 쪽 컴포넌트(vt `0x710563d230`) 갱신 `0x71026418a0`, 파라미터 = `spl__PlayerJumpGimmickParam`(this+0x90; +0x34 JumpGndFrm 5, +0x38 PreInputAcceptFrm 24, +0x30 JumpDisableFrm 24 — SplPlayer 데이터).
```
n   = 본체+0x734 (수직 속도 갱신 카운터, physics 문서)   held = 본체+0x72c (점프 버튼 유지, network/04 Jump 필드)
pre = 본체+0x730
if 아직 발사 안 함(this+0x31==0) and n < JumpGndFrm:
    if !held and pre > PreInputAcceptFrm: return            // 선입력 허용 프레임 초과
    vel = (this+0x3c + this+0x48, this+0x40 + this+0x4c, this+0x44 + this+0x50)
    0x71024c8318(1.0, 1.0, 본체+0xa5f9, &vel, 0, 0)          // 플레이어 물리로 속도 메시지(combat 문서의 넉백 전달과 같은 함수)
    this+0x31 = 1; 점프대 액터에 메시지
```
`this+0x3c..+0x50`(점프대 속도 성분)의 출처와 `pre`(본체+0x730)의 정확한 의미, JumpDisableFrm 사용처는 **[미확정]**. v0 대전 배치가 없으므로 웹 대전 구현 대상이 아닙니다.

## 8. 미확정 (2026-10-03 6차 [r6 assets] 갱신)

| 항목 | 상태 | 다음에 볼 곳 |
|---|---|---|
| 액터 `Rotate` 순서·저장 | **해소** [실행]+[판독]: Rz·Ry·Rx(라디안), 행 우선, 부모 P = 단위(로비·대전) — §5.1 | — |
| 배치 행렬의 S 합성 위치(T·R·S) | [미확정]: 생성 정보·액터는 S 를 따로 보관 [판독], 모델은 [R·diag(S)\|T] [실행, r5 gfx_char] | 액터 갱신 `0x7100f780e8`이 부르는 컴포넌트 vt+0x50 구현(모델 유닛 +0x268..+0x270, Phive 형상 스케일) |
| Box `OffsetRotation`/`Center` 합성 순서 | [미확정]: 형상 파라미터 오프셋은 판독(기본 `OffsetRotation` +0x64·플래그 +0x7e, `OffsetTranslation` +0x70·+0x7f, Box `Center` +0x84·+0xa0, `ConvexRadius` +0x90·+0xa2, `HalfExtents` +0x94·+0xa1 — 방문 함수 `0x7103bcec10`·`0x7103bc8748` 뒤쪽). 설정 플래그+값 근접 패턴 전수 검색으로는 Box 형상 빌더를 못 찾음. 데이터 대조(`PY web/tools/r6_assets_box_autocalc.py [--compound]`, AutoCalc AABB 와 후보식)는 단일 Box 740개 중 OffsetRotation≠0 이 0개, 회전이 있는 복합 형상 42개는 후보 A/B 가 같은 7개만 맞아 판별 불가 | `phive__ShapeUnitBoxParam` 등록부(`0x7103bc2b68`, `0x7103bc93a0`)의 타입 객체를 쓰는 형상 생성 코드, 또는 hknpConvexPolytopeShape 생성 호출자 |
| `Obj_LobbyKeepOutPlayerInSpecial` 켜짐 조건 | [판독] 조건식(§3.1), 비트11 = 판정 끔·+0x108 = 본체는 [추정] | 바디 +0x88 비트11 소비자(`0x7103b08540`~), `0x7101701040` 반환 객체 |
| 칠 대상 강체 목록(레이어 KeepOut 등 포함 여부) | [미확정] — [r6 paint] 진행 중 | 강체 +0x230 writer, ColPaint TargetCollisionList |
