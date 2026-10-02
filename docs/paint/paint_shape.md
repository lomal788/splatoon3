# 탄 도색 모양 계산 (슈터·스플래시·벽 낙하 방울)

상위 문서: [paint_and_score.md](paint_and_score.md). 이 문서는 "탄이 어디에, 어떤 크기·방향·패턴으로 칠하는가"만 다룹니다. 탄 이동 자체는 [weapon/shooter_bullet.md](../weapon/shooter_bullet.md) 담당입니다.

주소는 main NSO를 0x7100000000에 올린 가상 주소입니다. 디컴파일 원문은 `analysis/decomp/paint/paint_batch1.c`(공용·스플래시·벽 낙하), `analysis/decomp/bullet/BulletShooterBase_vt.c`(슈터 슬롯), `analysis/decomp/paint/paint_batch3.c`(지연 도색)에 있습니다.

## 1. 사용자에게 보이는 동작

- 슈터 탄이 바닥·벽에 닿으면 진행 방향으로 길쭉한 잉크 자국이 남는다. 멀리 날아간 탄일수록 폭이 좁아지고(무기마다 다름), 얕은 각도로 닿을수록 길어진다.
- 탄이 날아가며 떨어뜨리는 스플래시(BulletSplashShooter)도 같은 공용 함수로 작은 자국을 남긴다. 높은 곳에서 떨어질수록 덜 길쭉하다.
- 벽에 칠해진 잉크에서 흘러내리는 방울(BulletWallDrop)은 바닥에 닿으면 원형 자국을 무작위 회전으로 남긴다.

## 2. 전체 호출 흐름

```
[접촉 처리로 추정] BulletShooterBase 슬롯58 0x7101764de4
   └ (this->vt+0x2a0)()  = 슬롯84 "접촉 도색"                                   [판독]
        ├ 슈터       0x7101751c08  (BulletShooterPaintParam)                    [판독]
        └ 스플래시   0x7101811b44  (BulletSplashShooterPaintParam)              [판독]
             └ 0x7101765e50(w, ds, bullet, hit, dir)  공용, 호출자 26곳          [판독]
                  ├ 접촉 선택 + 접촉점/법선(0x71012d4f8c)
                  └ 0x7101765fd8  크기(W,L)·패턴·중심 이동·요청 구성             [판독]
                       ├ 슬롯102 패턴 선택(슈터 0x7101765ad8 / 스플래시 0 고정)
                       ├ 0x7101765b50 중심 이동량
                       ├ 슬롯98 지연값 <= 0 → 즉시 0x7102c44e18(접촉 목록, 요청)  [판독]
                       └ 슬롯98 지연값  > 0 → 탄+0x1150.. 에 보관               [판독]
[다음 갱신] 슬롯55 0x71017510c0 → 보관분이 있으면 0x71017646a4(겹침 질의 후 접촉마다 0x7102c45488)  [판독]
```

`0x7102c44e18` 이후(접촉 → 도색 대상 → 텍스처)는 [paint_and_score.md §3](paint_and_score.md#3-도색-요청이-텍스처까지-가는-길)에 있습니다.

## 3. 파라미터 구조체

`$parent` 상속은 필드 단위입니다. 코드가 필드를 읽을 때 그 객체의 "설정됨" 플래그 바이트(`flag`)가 0이면 부모 파라미터 객체로 올라가고, 끝까지 없으면 마지막 객체(생성자 기본값)를 씁니다 **[판독 — 0x7101751c08의 while 루프, SHARED [bullet] 항목과 같은 결론]**.

### 3.1 `spl::BulletShooterPaintParam` (팩토리 0x71015240b4, 방문 0x71015241c4, 객체 0x78 B)

데이터 키: 무기 표의 `PaintParam`. 기준 객체 = 파라미터 객체 자신.

| 오프셋 | flag | 필드 | 기본값 | 읽는 곳 | 의미 |
|---|---|---|---|---|---|
| +0x50 | 0x68 | DistanceNear | 2.0 | 0x7101751c08 | 폭 보간 거리 점 1 |
| +0x4c | 0x69 | DistanceMiddle | 20.0 | 〃 | 거리 점 2, near/far 구간 경계 |
| +0x48 | 0x6a | DistanceFar | 20.0 | 〃 | 거리 점 3 |
| +0x64 | 0x6b | WidthHalfNear | 1.4 | 〃 | 점 1의 반폭 |
| +0x60 | 0x6c | WidthHalfMiddle | 1.4 | 〃 | 점 2의 반폭 |
| +0x5c | 0x6d | WidthHalfFar | 1.4 | 〃 | 점 3의 반폭 |
| +0x34 | 0x6e | DegreeUseDepthScaleMin | 35.0 | 〃 | 이 각도 이상이면 DepthScaleMin |
| +0x30 | 0x6f | DegreeUseDepthScaleMax | 10.0 | 〃 | 이 각도 이하이면 DepthScaleMax |
| +0x40 | 0x70 | DepthScaleMin | 1.4 | 〃 | |
| +0x38 | 0x71 | DepthScaleMax | 2.4 | 〃 | |
| +0x58 | 0x72 | HeightUseDepthScaleMinBreakFree | 10.0 | 〃 | 낙하 높이 이상이면 DepthScaleMinBreakFree |
| +0x54 | 0x73 | HeightUseDepthScaleMaxBreakFree | 1.5 | 〃 | 낙하 높이 이하이면 DepthScaleMaxBreakFree |
| +0x44 | 0x74 | DepthScaleMinBreakFree | 1.2 | 〃 | |
| +0x3c | 0x75 | DepthScaleMaxBreakFree | 2.4 | 〃 | |

### 3.2 `spl::BulletSplashShooterPaintParam` (팩토리 0x71015a4bb4, 방문 0x71015a4c94)

데이터 키: `SplashPaintParam`.

| 오프셋 | flag | 필드 | 기본값 | 의미 |
|---|---|---|---|---|
| +0x40 | 0x48 | WidthHalf | 1.28 | 일반 스플래시 반폭 |
| +0x44 | 0x49 | WidthHalfNearest | 1.792 | 최근접(총구 앞) 스플래시 반폭 |
| +0x3c | 0x4a | DepthScaleMin | 1.0 | |
| +0x38 | 0x4b | DepthScaleMax | 1.2 | |
| +0x34 | 0x4c | DepthMinDropHeight | 10.0 | 이 낙하 높이 이상이면 DepthScaleMin |
| +0x30 | 0x4d | DepthMaxDropHeight | 3.0 | 이 낙하 높이 이하이면 DepthScaleMax |

### 3.3 `spl::BulletWallDropCollisionPaintParam` (팩토리 0x710163c924, 방문 0x710163c9f4)

데이터 키: `WallDropCollisionPaintParam`. 필드 PaintRadiusShock +0x3c(1.3), PaintRadiusFall +0x34(0.65), PaintRadiusGround +0x38(0.6), FallPeriodFirstSecondTargetAlp +0x30(1.0). 이 세 반지름은 탄 공용 vtable 슬롯 61 `0x7101646b10`이 읽어 벽 낙하 방울의 생성정보에 정수로 넣습니다: `+0x94 = (int)(PaintRadiusShock / 0.05f + 0.001f)`, `+0x98 = Fall`, `+0x9c = Ground` **[판독, gauge 담당]**. 소비는 §6.

### 3.4 탄 쪽 필드 (기준 객체 = 탄 `spl::BulletShooterBase`, 0x1230 B)

| 오프셋 | 타입 | 이름(웹 권장) | writer | reader | 근거 |
|---|---|---|---|---|---|
| +0x108 | ptr | spawnInfo | 생성 | 전역 | SHARED [bullet] |
| spawnInfo+0x1c | u32 | ownerId | 생성 | 0x7101765fd8 | 요청 B+0 → 0x7102c3ea50이 플레이어 번호(0~7)로 바꿔 레코드 N+0에 씀 **[판독]** (정정 2026-10-02 [paintgpu]: 이전 "team [추정]") |
| spawnInfo+0x2c | u32 | team | 생성 | 0x7101765fd8 | 요청 C+4 → N+0x34 → 그리기 팀(cColor·cTeam·모드) **[판독]** (이전 [미확정]) |
| spawnInfo+0x30 | vec3 | spawnPos | 생성 | 0x7101751c08 (각도) | **[판독]** |
| spawnInfo+0x6d | u8 | paintEnabled(= 로컬 발사) | 생성 0x71025823b0(`+0x6d = local`, 0x7102582864), 자식 탄 0x7101648a4c 복사 | 슬롯84 진입 | 0이면 칠하지 않음 **[판독]**. 복제 탄(local 0)은 칠 요청을 하지 않음 **[판독]** |
| spawnInfo+0xe0 | weak ref | shooterPaintParam | 생성 | 0x7101751c08 | +0xe8 세대 번호와 비교 **[판독]** |
| +0x198 | s32 | moveState | 0x7101762f68 | 0x7101751c08 | 0이 아니면 BreakFree 깊이 사용 **[판독]** (상태 의미는 SHARED [bullet]) |
| +0x1200 | f32 | travelDist | 0x71017512bc(누적), 생성 시 0 | 0x7101751c08 | 이동한 3D 거리 누적 **[판독]** |
| +0x1204 | f32 | maxYInState | 0x71017512bc(state≠0 동안 max), 생성 시 -1e6 | 0x7101751c08 | **[판독]** |
| +0x1150 | u8 | pendingPaint | 0x7101765fd8 | 0x71017510c0 | 지연 도색 보관 플래그 **[판독]** |
| +0x1154..+0x1188 | | pendingReq | 0x7101765fd8 | 0x71017510c0 | pos, normal, dir, size, slot105 값, pattern, 원래 접촉 y **[판독]** |

## 4. 슈터: 반폭 w와 깊이 비율 ds (0x7101751c08)

### 4.1 반폭 — 이동거리 구간 보간 **[판독]**

```
dist = bullet.travelDist                      // +0x1200
if dist < DistanceMiddle:
    w = clampLerp(dist, DistanceNear, WidthHalfNear, DistanceMiddle, WidthHalfMiddle)
else:
    w = clampLerp(dist, DistanceMiddle, WidthHalfMiddle, DistanceFar, WidthHalfFar)

clampLerp(x, x0, y0, x1, y1):                 // 인라인. x0 > x1 이면 두 점을 바꿔서 같은 식
    if x1 < x0: swap((x0,y0),(x1,y1))
    if x <= x0: return y0
    if x >= x1: return y1
    t = (x1 - x0 == 0) ? 0 : (x - x0)/(x1 - x0)
    return y0 + (y1 - y0) * t
```

데이터에는 DistanceMiddle(1.1)이 DistanceNear(기본 2.0)보다 작은 무기가 많습니다(예: `WeaponShooterNormal`). 원본 코드는 두 점 순서가 뒤집혀도 정렬해서 보간하므로 결과적으로 `dist < 1.1`이면 WidthHalfMiddle과 WidthHalfNear 사이를 1.1~2.0 구간으로 보간하는 셈입니다. 이 동작을 "정리"하지 말고 그대로 재현해야 합니다.

### 4.2 깊이 비율 — 입사 각도 **[판독]**

```
p   = bulletPosition()                         // 0x710164434c: 물리 바디 위치 (s0,s1,s2)
dxz = hypot(p.x - spawnPos.x, p.z - spawnPos.z)
if dxz > 0:                                    // NaN이면 sqrtf로 다시 계산
    deg = atanf(|p.y - spawnPos.y| / dxz) * 57.295776
    t   = (deg - DegreeUseDepthScaleMax) / (DegreeUseDepthScaleMin - DegreeUseDepthScaleMax)
else:
    t = 1.0
ds = (t <= 0) ? DepthScaleMax : (t >= 1) ? DepthScaleMin : DepthScaleMax + t*(DepthScaleMin - DepthScaleMax)
```

각도는 실제 탄 진행 방향이 아니라 "생성 위치에서 현재 위치까지의 직선"의 수평 대비 기울기입니다. 낮게 쏴서 멀리 간 탄은 각도가 작아 `DepthScaleMax`(더 길쭉), 아래를 향해 쏜 탄은 `DepthScaleMin`.

### 4.3 깊이 비율 — Brake/Free 상태의 낙하 높이 **[판독]**

```
if bullet.moveState != 0:                      // +0x198
    h  = bullet.maxYInState - p.y              // +0x1204 - 현재 y
    t2 = (h - HeightUseDepthScaleMaxBreakFree) / (HeightUseDepthScaleMinBreakFree - HeightUseDepthScaleMaxBreakFree)
    dsBF = lerp(DepthScaleMaxBreakFree, DepthScaleMinBreakFree, clamp01(t2))
    ds = (ds < dsBF) ? ds : dsBF               // 작은 쪽
ds = (ds < 1.0) ? 1.0 : min(ds, 5.0)
```

### 4.4 방향 **[판독]**

```
v = bullet.vt[0x188]()                          // 슬롯49 getVelocity (+0x1118)
d = (v.x, 0, v.z) 정규화; 길이 < 1e-5 이면 (1, 0, 0)
0x7101765e50(w, ds, bullet, hit, &d)
```

## 5. 스플래시 (0x7101811b44) **[판독]**

```
if !spawnInfo.paintEnabled: return
param = spawnInfo+0xa0 (BulletSplashShooterPaintParam)
w  = spawnInfo.isNearest(+0x90) ? WidthHalfNearest : WidthHalf
drop = spawnInfo.spawnY(+0x34) - p.y
t  = (drop - DepthMaxDropHeight) / (DepthMinDropHeight - DepthMaxDropHeight)
ds = max(1.0, lerp(DepthScaleMax, DepthScaleMin, clamp01(t)))      // 상한 5 클램프 없음
d  = normalize(spawnInfo+0x94, 0, spawnInfo+0x98)                   // 길이 0이면 정규화 생략
0x7101765e50(w, ds, bullet, hit, &d)
```

스플래시 클래스는 슬롯102(패턴)가 0, 슬롯98(지연)이 0.0이라 항상 `Shot00` 패턴으로 즉시 칠합니다 **[판독 — vtable 0x71055af4c8 슬롯 102 = 0x71018125b4 `mov x0,xzr`, 슬롯 98 = 0x71017f40bc `fmov s0,wzr`]**.

## 6. 벽 낙하 방울의 바닥 도색 (BulletWallDrop, 0x71018ae054) **[판독]**

```
접촉점 pos, 법선 n (0x71012d4f8c)
seed = (*0x7105797f18)+0x120 + spawnInfo+0x64          // sead::Random 초기화 (SHARED [bullet] 난수식)
r    = 난수 1회 → 상위 8비트로 각도표(0x7105794810, 16 B 항목) 선택 + 하위 24비트 보간
dir  = (표.a + 표.b*f, 0?, 표.c + 표.d*f)              // 무작위 회전용 방향 [추정: 단위원 표]
size = (spawnInfo+0x9c 정수) * 0.05 * 2   → W = L = size  (원형)
pattern = 0, 높이범위 ±20000, ownerId = spawnInfo+0x1c   // 요청 B+0 자리(소유자). 팀은 C+4 쪽 — §7.6 정정
요청 id = spawnInfo+0x74 + bullet.age(+0x134) + 1 (0x1745d1 이상이면 0x1745d1 고정)
0x7102c44e18(hit 접촉 목록, 요청...)
```

반지름이 정수×0.05로 양자화되어 생성정보에 들어온다는 점(네트워크 동기화용으로 추정)이 특징입니다. +0x9c는 `PaintRadiusGround`이고(writer `0x7101646b10`), 낙하 중 도색 `0x71018ae5e8`은 +0x98(`PaintRadiusFall`) × 0.05 × 2를 씁니다 **[판독]**. (2026-10-02 갱신: 이전 판에서는 writer 미발견으로 미확정이었습니다.)

## 7. 공용: 크기·패턴·중심 이동 (0x7101765e50 → 0x7101765fd8)

### 7.1 접촉 선택 (0x7101765e50) **[판독]**

hit+0x10 의 접촉 목록에서 강체 플래그(+0x68 bit1)가 켜진 첫 접촉을 고르고, 없으면 목록의 첫 접촉을 씁니다. 위치는 접촉점, 접촉 방향이 뒤집힌 경우 `pos + normal*depth(+0x30)`. 법선은 `0x71012d4f8c(contact, out, flipped)`.

### 7.2 조기 종료 **[판독]**

- `w <= 0`이면 칠하지 않음. 블래스터 계열 표는 WidthHalf* = 0이라 탄 접촉 도색이 없습니다(폭발로 칠함) **[데이터]**.
- 접촉 목록 중 하나라도 재질 플래그 `(+0xb) & 0x60`이 켜져 있으면 칠하지 않음 **[판독]** (칠 불가 재질로 추정 **[추정]**).
- 슬롯98 지연값 > 0 이고 이미 보관 중(+0x1150 ≠ 0)이면 무시.

### 7.3 크기 **[판독]**

```
s = sqrt(ds);  q = sqrt(|s|)                 // q = ds^(1/4)
L = (2w) * s * q    = 2w · ds^(3/4)          // 진행 방향 길이   → 요청 size.y
W = (2w / s) * q    = 2w · ds^(-1/4)         // 진행 직교 폭     → 요청 size.x
```

성질: `L/W = ds`, `W·L = 4w²·√ds`. 즉 깊이 비율이 커지면 면적이 √ds 배 늘어납니다.

### 7.4 패턴 (슬롯102) **[판독]**

슈터(0x7101765ad8)는 `L/W = ds`로 InkTexType을 고릅니다.

| ds | 반환 | InkTexType | 텍스처 크기(가로×세로) [데이터] | 세로/가로 |
|---|---|---|---|---|
| < 1.3 | 0 | Shot00 | 32×32 (12종) | 1.00 |
| < 1.6 | 1 | Shot01 | 32×42 (6종) | 1.31 |
| < 2.2 | 2 | Shot02 | 32×54 (6종) | 1.69 |
| < 2.85 | 3 | Shot03 | 32×70 (6종) | 2.19 |
| 그 외 | 4 | Shot04 | 32×91 (6종) | 2.84 |

열거형 값 = `spl::paint::InkTexType` 문자열 순서(Shot00=0 …)입니다. 각 텍스처의 세로/가로 비가 경계값과 맞고, 런타임 InkTexInfo 표가 이 값으로 50칸(< 0x32) 색인되며, 큐 선택 0x7102c14dec가 0x12/0x13(= 문자열 순서의 InkRutStart/InkRutMove)을 따로 다루는 것과도 맞습니다 **[판독 근거 보강, 2026-10-02 [paintgpu]]**.

**같은 패턴 안의 변형(`Shot00_0`~`_11`) 선택 규칙(해소) [판독]+[실행(에뮬) 600/600]**: 그리기 레코드 변환 `0x7102c11f80`이 `시드 = |fcvtzs((p.z + (p.x + p.y)) × 100)| + 요청번호(N+4)`(p = 대상 공간 접촉 중심, 요청이 시드를 직접 주면 그 값)로 sead::Random을 만들어 첫 u32 % PatternNum 번째 텍스처를 고릅니다. 슈터 요청은 시드를 직접 주지 않습니다(C+0x18 = 0). 상세·예시는 [paint_and_score.md](paint_and_score.md) §3.5.3.

### 7.5 중심 이동 (0x7101765b50) **[판독]**

```
if pattern in 1..7:
    a = normalize(X × n);  |X × n| < 0.1 이면 다른 축으로 다시 만든 접선
    v = a*d.z + (n × a)*d.x                    // 진행 방향을 표면 평면으로 옮긴 벡터
    shift = v / |v| * ( L * ((L/W - 1) / (2·L/W)) )   = v̂ · (L - W)/2
else: shift = 0
pos += shift
```

길쭉한 패턴(Shot01~04)은 접촉점에서 시작해 진행 방향으로 뻗고, 원형에 가까운 Shot00은 접촉점이 중심입니다.

### 7.6 도색 요청 (스택 지역 구조, 웹 권장 이름) **[판독]**

| 오프셋 | 값 | 웹 이름 |
|---|---|---|
| A+0x00 | pos + shift (vec3) | center |
| A+0x0c | 접촉 법선 (vec3) | normal |
| A+0x18 | 진행 방향 d (vec3, ≈0이면 전역 기본 벡터 *0x71057919a0) | forward |
| A+0x24 | W, L | size |
| A+0x2c | -1.0f | heightLimit: > 0이면 \|접촉.y − 중심.y\| ≥ 값인 접촉은 칠하지 않음(0x7102c4126c). 슈터 −1 → 검사 안 함 **[판독]** |
| B+0x00 | spawnInfo+0x1c | ownerId (→ N+0 플레이어 번호) **[판독]** |
| B+0x04 | 슬롯105 반환(전역 프레임 카운터 기반) | stamp |
| C+0x00 | !슬롯77 (bool) | noGauge: 1이면 N+0x44 = 1 → 칠 p만 세고 스페셜 게이지 제외. 슬롯77은 제트팩 탄만 0 **[판독]** (정정: 이전 "isRemote? [추정]") |
| C+0x04 | spawnInfo+0x2c | team **[판독]** |
| C+0x08 | pattern | inkTexType |
| C+0x0c | 0xff (u16) | |
| C+0x10 | +20000.0f, -20000.0f | heightRange |

### 7.7 지연 도색 (슈터만) **[판독]**

슈터 슬롯98은 1.0을 반환하므로 접촉 순간에는 요청을 탄+0x1150~에 보관만 합니다. 다음 갱신의 슬롯55(0x71017510c0)가 보관분이 있으면 `0x71017646a4`를 부르고, 이 함수는

```
r = 0.5 * hypot(W, L) * slot98()              // 슈터 1.0
r = max(r, 전역 최소(기본 0.05, 설정 +0x21c)); r = min(r, 2000); 비정상이면 1.0
반지름 r 구로 겹침 질의 → 걸린 접촉 전부에 0x7102c45488(요청)
```

를 합니다. 즉 슈터 자국은 "맞은 면 하나"가 아니라 사각형의 반대각선 반경 안에 있는 모든 면(바닥과 붙은 벽 등)에 찍힙니다. 보관 플래그를 언제 지우는지와 탄 소멸 시점은 **[미확정]** (탄 수명은 bullet 담당).

## 8. 실행 검증 (재구현 계산, 원본 실행 아님)

`web/tools/paint_shape.py`

- `check`: 기본값 경계(거리 0 → WidthHalfNear, 거리 ∞ → WidthHalfFar), `rect_size` 성질(L/W=ds, W·L=4w²√ds), 중심 이동 (L-W)/2, 평지 각도 0° → DepthScaleMax, 가파른 각도 → DepthScaleMin, `WeaponShooterNormal` 0~30 거리 연속성 → 통과.
- `table`: 모든 GameParameterTable의 슈터·스플래시·벽 낙하 도색 파라미터를 `$parent`+기본값으로 풀어 `analysis/paint/shooter_paint_table.json`(58개 표)에 저장.

기대값 예 (`WeaponShooterNormal`, 재구현):

| 입력 | w | ds | W × L |
|---|---|---|---|
| dist 0 | 1.93 | | |
| dist 20, 수평 10 떨어진 같은 높이(0°) | 1.71 | 2.24 | 2.7955 × 6.2620 |
| dist 20, 수평 1·아래 5 (78.7°) | 1.71 | 1.31 | |

이 계산은 원본 실행 결과와 대조하지 않았습니다. 원본 함수 판독과 재구현을 같은 수식으로 맞춘 단계입니다.

## 9. 웹 구현

```ts
// paint/shape.ts — 서버·클라이언트 공용 (결정적이어야 함, f32는 Math.fround)
interface PaintRequest { center: Vec3; normal: Vec3; forward: Vec3; size: [number, number];
                         team: number; inkTexType: number; heightRange: [number, number] }

function shooterPaintRequest(p: ShooterPaintParam, b: BulletState, hit: Hit): PaintRequest | null {
  const w = widthHalf(p, b.travelDist);
  let ds = depthByAngle(p, b.spawnPos, b.pos);
  if (b.moveState !== 0) ds = Math.min(ds, depthBreakFree(p, b.maxYInState - b.pos.y));
  ds = ds < 1 ? 1 : Math.min(ds, 5);
  return rectRequest(w, ds, hit, horizontalDir(b.vel), patternByDs(ds), b.team);
}
```

- 모든 중간값을 `Math.fround`로 감싸 f32 순서를 지킵니다(특히 `ds^(1/4)`는 `sqrt(sqrt)` 두 번).
- 슈터는 "접촉 프레임에 보관 → 다음 갱신에 구 질의로 칠함" 순서를 지켜야 합니다. 웹에서 한 프레임에 바로 칠하면 칠해지는 시점이 1갱신 빨라집니다.
- 스플래시는 즉시, 패턴 Shot00 고정, 중심 이동 없음.

## 10. 미확정

| 항목 | 이유 / 필요한 근거 |
|---|---|
| ~~패턴 변형 번호(Shot00_0~11) 선택~~ | 해소 [판독]+[실행(에뮬)] (2026-10-02 [paintgpu]): §7.4. 회전은 진행 방향의 면 투영 각(대상 vt+0x70 = 0x7102c1233c) + 경사 보정(0x7102c124bc) — [paint_and_score.md](paint_and_score.md) §3.5.5 |
| ~~스탬프 텍스처 값 → 칠함 여부 임계~~ | 해소 [판독]: 마스크 × cAlpha 로 팀 채널에 보간하고, 결과 채널 ≥ 0.3(`cTeamAlphaTestThreshold`, 0x7102c188b4 상수)이면서 최대일 때만 기록(ALPHA_TEST 변형 = 모드 0·1·2·4~7·11. 슈터 요청은 큐0 → 모드 4/5/6(카운트)·7·9·12를 모두 거침 — paint_and_score.md §3.5.4). 빈 텍셀 기준 마스크×cAlpha ≥ 0.3 → cAlpha=1이면 스탬프 텍스처 텍셀 중 Shot00_0 26.6%, Shot01_0 28.3%, Bomb00 50.7%가 첫 스탬프로 칠해지는 영역(PNG 8비트 값 기준, 실제는 쌍선형 샘플·회전·크기 변환을 거침) [데이터 계산] — [../graphics/shaders.md §4.4](../graphics/shaders.md) |
| ~~요청 A+0x2c(-1.0), C+0x04 의미~~ | 해소 [판독]: A+0x2c = 높이 제한(≤0 끔), C+0x04 = 팀 (§7.6) |
| 지연 도색 플래그 해제 시점 | 슬롯55 이후 경로 미판독 |
