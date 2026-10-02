# [paint] 잉크 도색 구현 기록

담당 폴더: `games/splatoon3/core/paint/`, `games/splatoon3/client/paint/`. 근거 문서: [paint/paint_and_score.md](../paint/paint_and_score.md), [paint/paint_shape.md](../paint/paint_shape.md), [graphics/shaders.md §4](../graphics/shaders.md), [gimmick/collision_mesh.md](../gimmick/collision_mesh.md), [graphics/team_color.md](../graphics/team_color.md).

상태(2026-10-02): 시험 사격장(Lby_Lobby00) 충돌 메시로 도색 표면을 만들고, 슈터·스플래시·벽 낙하 요청을 원본 패스 규칙으로 CPU 격자에 칠해 화면에 표시한다. **스탬프 마스크는 아직 해석적 근사**(에셋 대기, 아래 조정 요청 1). 무기 쪽 호출(`world.paint.request`)은 아직 연결되지 않았다(조정 요청 4).

## 1. 구현한 것

### 1.1 파일

| 파일 | 내용 | 원본 근거 |
|---|---|---|
| `core/paint/shape.ts` | 슈터 반폭(거리 보간)·깊이 비율(각도·BreakFree)·스플래시·벽 낙하 반경 양자화·`rectSize`(W = 2w·ds^-1/4, L = 2w·ds^3/4)·`shooterPattern`(L/W 경계 1.3/1.6/2.2/2.85)·`centerShift`(X×n, 대체 축 n×Z, (L−W)/2)·수평 방향 | 0x7101751c08, 0x7101811b44, 0x7101646b10/0x71018ae054, 0x7101765fd8, 0x7101765ad8, 0x7101765b50 (paint_shape.md §4~§7). f32 연산 순서 그대로 |
| `core/paint/inktex.ts` | InkTexType 열거(50), InkTexInfo 행(에셋 `ink_tex_info.json` 또는 Shot00~04 대체 행 — 값은 데이터 그대로), 높이 범위(MinEdge/MaxEdge/Static/None), 시드 `|fcvtzs((z+(x+y))·100)| + 요청번호`, 변형 번호 `sead::Random(시드).u32 % PatternNum`, 스탬프 마스크(에셋 또는 근사)·쌍선형 샘플 | 0x7102c11f80 (§3.5.3, 원본 실행 600/600 재구현과 대조) |
| `core/paint/overpaint.ts` | PaintOverpaint 한 텍셀: 1% 자기 채널 감쇠 → `mix(d2, cColor, ink)` → 약한 덧칠 유지(모든 채널 < 0.315 이면 0.3 넘던 채널 보존) → 알파 테스트(내 채널 ≥ 0.3 이고 최대), ERASE | shaders.md §4.4, 상수 0x7102c188b4 (0.3, 0.99) |
| `core/paint/surface.ts` | 충돌 삼각형 → 칠 가능 판정 → 같은 평면 연결 차트(한 변 ≤ 1024 텍셀) → 선반 배치 페이지(폭 ≤ 2048) → 텍셀 중심 안/밖 마스크 → 구 질의용 격자 → 표시용 메시 | 밀도 8 텍셀/단위(§3.1). 차트 알고리즘은 웹 독자(원본 ColPaintBuilder 미판독) |
| `core/paint/paintworld.ts` | `PaintWorld` 구현: 요청 → 레코드(D) → 프레임 패스 → 팀 면적·플레이어 카운터·발밑 샘플 | §3.5 전체, §4, §7 |
| `core/paint/score.ts` | 팀 p = fcvtzu(count·0.015625·0.3030303), 플레이어 p = (int)(texels/211.2) | §4.2 |
| `core/paint/index.ts` | 시스템: init 에서 표면·`world.paint`·`shared.paintSurfaces`, step 에서 패스 실행, debug `paint.*` | — |
| `client/paint/index.ts` | 페이지별 `DataTexture`(RGBA8 = 원본 도색 텍스처 R/G/B 잉크량) + 칠 가능 충돌 삼각형 오버레이 메시, 팀 Ink(9) 색, 바뀐 사각형만 `addUpdateRange` 부분 업로드 | team_color.md §5.3 (render 의 `teamcolor.ts` 식·`parseEnv` 조명 재사용) |

### 1.2 한 프레임 처리 (paint 시스템 step, 무기 뒤)

원본 0x7102c13750(수명) → 대기→실행 → 렌더 패스 0x7102c14168 순서를 그대로 둔다.

1. 수명: 실행 중 레코드 `age++`(원본 D+0x6f → D+0x48++, 대상이 유효하면 그리지 않은 프레임도 증가 — 0x7102c1461c 판독), 큐2(지우기)는 바로, 그 밖은 `age > (AF−1)·AS` 이면 제거.
2. 대기 → 실행: 기한이 된 요청을 차트·텍셀·스탬프 값으로 풀어 둔다(아래 1.3).
3. `age % AS == 0` 인 레코드만 그림:
   - 큐0(플레이어 0~7) 모드 4/5/6: 알파 테스트(프레임 앞 색) && `(stencil & 팀비트) != 팀비트` → `stencil = 팀비트`, 그 플레이어 카운터 +1 (칠 가능 텍셀만)
   - 큐1(비플레이어, owner < 0) 모드 0/1/2: 알파 테스트 통과 → `stencil = 팀비트`
   - 큐2 모드 11: 지우기 알파 테스트(세 채널 모두 < 0.3) → `stencil = 0`
   - 모드 9: 큐0 → 큐1 순서로 알파 테스트 없이 색(R,G / 3팀이면 B) 순차 기록(그리기마다 배리어), 8비트 UNORM 저장
   - 모드 10: 지우기 색
   - 모드 7(깊이만)·12(저해상도 사본)·8(InkRut)은 판정·표시에 영향이 없어 생략
4. 처음 그린 레코드마다 이벤트 `Paint {team, pos, owner}`.

팀 면적(원본 a,b,c = 모드 14/15/16 스텐실 EQUAL)은 스텐실이 바뀔 때 증감으로 유지하고, 전체 d(모드 17)는 칠 가능 텍셀 수다. Shot00~04 는 AF 3·AS 3 이라 한 요청이 0·3·6 프레임에 세 번 그려지고 매번 센다(잉크량이 0.2 → 0.36 → 0.49 로 늘어 소유가 퍼짐 — 테스트로 확인).

### 1.3 요청 → 레코드

| `PaintRequest.kind` | 처리 | 근거 |
|---|---|---|
| `"Shooter"` | 접촉 순간 요청. 패턴 = L/W 경계, 중심 += (L−W)/2 진행 방향, **1 프레임 뒤** 적용, 반경 `clamp(0.5·hypot(W,L), 0.05, 2000)` 구에 닿는 모든 면 | 슬롯98 = 1.0 → 탄+0x1150 보관 → 다음 갱신 슬롯55 0x71017646a4 구 질의(접촉마다 0x7102c45488 flags 0 = 위치·법선 교체 없음) |
| `"ShooterDeferred"` | 위와 같고 지연 없음(무기 쪽이 이미 늦춘 경우) | — |
| `"Splash"` | 패턴 0(Shot00), 이동 없음, 즉시, 접촉 근방(반경 0.1) | 슬롯102 = 0, 슬롯98 = 0 (vtable 0x71055af4c8) |
| `"WallDrop"` | ds 무시, W = L = 2·widthHalf, 패턴 0, 즉시 | 0x71018ae054. `widthHalf = wallDropSize(PaintRadiusGround)/2` 로 넘길 것 |
| `"Erase"` | 큐2 | 모드 11 → 10 |
| InkTexType 이름(`"Disk"` 등) | 그 행·스탬프로 즉시, 반경 0.5·hypot(W,L) | 슈터 외 호출자(15곳 미분류)의 웹 입구 |

- `widthHalf <= 0` 이면 칠하지 않음(§7.2, 블래스터 탄).
- `seed` = 요청 번호(원본 N+4 = 탄 슬롯105 값). 실제 시드는 위치(중심 이동 후)와 합쳐 paint 가 계산한다.
- `owner >= 0` 은 플레이어(등장 순서로 0~7 번호), `< 0` 은 비플레이어(큐1, 카운트 없음 — N+0x44 = 2).
- 법선·방향이 0 이면 (0,1,0)·(1,0,0) (N+0x1c/+0x28 규칙).
- cAlpha = 1(슈터 요청 0xff).

스탬프 배치(차트마다): 차트 법선 `np`·요청 법선 `nq` 가 `np·nq ≤ 0.001` 이면 거부(뒷면·수직면). 진행 방향을 차트 평면에 투영한 축(L, 스탬프 +y = v=0 쪽), 오른쪽 = fwd × np(W, u 증가). 요청 중심을 차트 평면에 내린 점을 중심으로 실제 크기로 놓는다(원본은 회전 0x7102c1233c + 경사 보정 0x7102c124bc 로 경사면에서도 실제 크기). 텍셀 위치의 요청 법선 방향 높이가 높이 범위(Shot = ±min(W,L)/2) 밖이면 버린다. 마스크는 텍셀 중심 uv 에서 쌍선형.

### 1.4 발밑 샘플 `sample(pos, radius)`

반경 구 안 칠 가능 텍셀 수 N 과 팀별 소유(스텐실) 텍셀 수로 `ratio[t] = cnt[t]/N · min(N/15, 1)`, `team` = 비율 최대 팀(없으면 −1). 반환에 `texels: N` 추가(원본은 N = 0 이면 직전 값을 한 번 재사용 — 호출하는 쪽 규칙). 근거 §7 PlayerStepPaint 0x710268b3b8 [판독], 스텐실 경유는 [추정].

### 1.5 표시

- 페이지 텍스처 = 코어 `Page.color`(같은 버퍼, 복사 없음), Linear 필터, 밉맵 없음.
- 오버레이 = 칠 가능 충돌 삼각형, 법선 방향 0.02 띄움 + polygonOffset(−1, −4). 셰이더(MeshStandardMaterial onBeforeCompile): `m = max(R,G,B)`, `m < 0.3` 이면 discard, 아니면 최대 채널 팀의 Ink 색.
- 팀 색: `team_color.json` `OrangeBlue` 행(render 와 같은 행) → `buildTeamSets(row, false, parseEnv(env.json).light)` 의 colors[9] (Ink). 로비 env 는 render 와 같은 해석(lobby MainLight 색·세기).

## 2. 원본과 다른 점

| 항목 | 원본 | 웹 | 동등성 근거 / 영향 |
|---|---|---|---|
| 도색 연산 | GPU 스탬프 사각형 래스터 + 셰이더 + 스텐실 + SAMPLES_PASSED 카운터 | CPU 텍셀 루프(같은 패스 순서·판정) | 텍셀 판정 9경우가 `paintgpu_frame_sim.py` 와 일치(테스트). 래스터 경계 규칙(top-left)은 반열린 구간 근사 |
| 카운터 지연 | GPU 결과 1~2 프레임 늦게 읽음 | 즉시 | 지연 프레임 수 [미확정] |
| 지형 아틀라스 | ColPaintBuilder(패널·프리즘·패턴 인식·UV 매퍼·수평/수직 옥트리, Col 셀) | 같은 평면 연결 차트 + 선반 배치 | 밀도 8 텍셀/단위만 맞춤. 로비 칠 가능 면적 30872 단위² × 64 = 1,975,804 대비 안 텍셀 1,868,437(−5.4%, 얇은 삼각형의 텍셀 중심 판정 손실) → 결과 % 분모가 원본과 다를 수 있음 |
| 대상 종류 | Floor(200×200 위에서 본 텍스처 + 높이 텍스처) / Col / Obj | 전부 차트 하나의 방식 | 회전·경사 보정·높이 마스크를 "차트 평면 위 실제 크기 + 요청 법선 높이 범위"로 일반화 [근사] |
| 뒷면 거부 | Col: 법선·축(*0x71058ed12c) < 0.001, Obj: 대상 vt+0xc0 | 차트 법선·요청 법선 ≤ 0.001 | 바닥 스탬프가 붙은 벽을 칠하지 않음(테스트) |
| 즉시 요청의 면 | 탄 접촉 목록 | 반경 0.1 구 | [근사] |
| 시드의 대상 공간 위치 | Floor 는 위치 그대로, Col/Obj 는 0x7102c4a6bc 변환 | 월드 위치 | Col/Obj 변환 미검증 → 변형 번호가 원본과 다를 수 있음 |
| 칠 가능 재질 | ColPaintBuilder + 요청 단계 재질 플래그 (+0xb)&0x60 | 에셋 `paintable`(Ground && !ForceColPaintNotPaintable) 이고 Water·Fence·KeepOut·FillUp·PlayerDead 태그·플레이어 전용/잉크 통과 필터 아님, ForceColPaintPaintable 은 칠함 | 태그 이름 기반 [추정]. 로비 장외 바닥(KeepOut+PlayerDead, SplSolidGround)은 에셋이 칠 가능으로 두었지만 여기서는 뺐다 |
| 충돌 프리미티브 | 캡슐·원기둥 등도 Phive 형상 | 삼각형 메시만 칠함 | 로비 프리미티브 13개는 도색 없음 |
| 감김 방향 | (b−a)×(c−a) 앞면으로 봄 | 위·아래 향 면적 중 아래가 70% 넘으면 전체 뒤집기 | 로비는 뒤집지 않음(flipped=false) |
| 표시 | 시각 메시가 도색 텍스처를 샘플(지면 셰이더·잉크 노멀·InkUBOParam 미판독) | 충돌 메시 오버레이, 0.3 문턱, Ink 색 + 표준 재질(거칠기 0.35) | 충돌↔시각 거리 99% 2.6cm 이내(collision_mesh.md §5) — 띄움 0.02 보다 시각 면이 높은 곳은 가려질 수 있음 |
| 저해상도 사본(모드 12)·InkRut(모드 8)·스페셜 게이지 분리(+0x6c) | 있음 | 없음 | 연습장 슈터에 영향 없음. 게이지 제외는 제트팩 탄만 |
| 레코드 풀 넘침 시 요청 버림 | 있음(크기 미확정) | 없음 | |

## 3. 미확정·추가 분석 필요

| 항목 | 풀 방법 |
|---|---|
| **스탬프 마스크 원본 텍스처** | 에셋(조정 요청 1). 그때까지 근사: 원본 Shot00~04 의 "≥0.3 비율·무게중심 높이"를 맞춘 원뿔 원(꼬리 무늬·12/6 변형 차이 없음) |
| 스탬프 방향 부호: 진행 방향이 텍스처 v=0(위) 쪽인지, u 가 오른쪽인지 | 행렬 0x7102c17ae0 곱 순서 + 0x7102c1233c θ 부호 판독. 지금은 무거운 덩어리(텍스처 아래쪽, v≈0.7)가 접촉점 쪽, 꼬리가 앞쪽이 되게 둠 |
| 애니 프레임(AF)마다 바뀌는 값 | D+0x48 읽는 그리기 코드. 지금은 같은 스탬프를 다시 그림(잉크량만 누적) |
| 0x7102c50d18 이 게임 갱신 앞/뒤인지(요청이 그 프레임에 그려지는지) | 프레임 루프 판독. 지금은 같은 프레임(즉시 요청) |
| Col 대상 시드 위치 변환 0x7102c4a6bc, Col 대상 크기·아틀라스 밀도 | ColPaint 빌더 판독 |
| 지면 표시 셰이더(문턱·경계 부드러움·잉크 색 종류) | Hoian 지면 재질의 도색 텍스처 샘플 경로 판독. 지금 Ink(9) 색은 작업 지시·team_color.md 근거 |
| 로비 `spl::PaintedArea`(Cylinder 19, Cube 8, 팀 Alpha) | [range] 가 분석 중(analysis/decomp/range/painted_area*.c). 미리 칠한 영역이면 InkTexType 이름 요청(예 `"Disk"`, owner −1)으로 칠할 수 있음 |
| 텍스처 비트 폭(8비트 UNORM)·SAMPLES_PASSED | NVN 열거값 이름 확인 |

## 4. 검증

| 테스트 | 대조 대상 | 결과 |
|---|---|---|
| `tests/paint_shape.test.mjs` 반폭·깊이·스플래시·W×L·중심 이동 | `paint_shape.py` 재구현(무기 표 11종 × 거리 14점, 무작위 각도 13건, 스플래시 16건, (w,ds) 105쌍) → `tests/paint_fixture_shape.json` | 통과(허용 오차 f32 수준 2e-6~2e-5) |
| 같은 파일: `paint_shape.py check` 경계 성질, 패턴 경계, 벽 대체 축 이동, 벽 낙하 양자화 | 문서 식 | 통과 |
| 같은 파일: 시드·변형 번호·높이 범위 80건(Shot00~04 70 + 기타 10) | `paintgpu_record_emu.py re_convert`(원본 0x7102c11f80 실행 600/600 일치) | 통과. 시드 0 → Shot00_5 |
| `tests/paint_world.test.mjs` 텍셀 판정 9경우(자기 땅 덧칠 0, 0.4 로 못 뺏음, 0.29 색만, 같은 프레임 겹침, 약한 덧칠, 지우기 …) | `paintgpu_frame_sim.py` 출력(색 8비트·스텐실·카운터) | 9/9 일치 |
| 애니 프레임(AF3·AS3) | 0x7102c13750/0x7102c1461c 판독 | 0·3·6 프레임 그림, 색 51→92→125, 소유는 3 프레임째, 카운트 64 |
| 슈터 지연·모양 | §7.5·§7.7 | 접촉 프레임 0, 다음 프레임 칠함, 범위가 W×L·전진 이동 안 |
| 바닥/벽 | — | 바닥 스탬프가 수직 벽을 칠하지 않음, 벽 스탬프는 벽만 |
| 발밑 샘플 | §7 min(N/15,1) | 반경 0.25 → N 12 → 0.8 |
| 면적·p | `paint_score.py`(`score_check.json`) | 0/211/212/2112/42240/100000 → 0/0/1/10/200/473 |
| 실제 로비 충돌(노드) | — | init 195ms, 차트 2646, 페이지 1905×1994, 슈터 50발 27ms |
| 브라우저(개발 서버, 헤드리스 swiftshader) | — | 카메라 앞 55곳 주입 → 오렌지·파랑 잉크 표시 확인(스크린샷), 팀 p 45/8 |

## 5. 조정 요청

1. **[assets] 스탬프 마스크** `common/data/ink_stamps.json` = `{ "<텍스처 이름>": { "w": 32, "h": 32, "data": "<base64, R8 행 우선, 행 0 = PNG 위>" } }`. 원본 `romfs/Model/InkTexture.bfres.zs` → `analysis/paint/inktex/*.png`(R 채널, BC4). 최소 Shot00_0~11, Shot01~04_0~5(36장, 약 95KB base64). 표 이름 `ink_stamps` 로 `world.data.tables` 에 들어오면 자동으로 원본을 쓴다(debug `paint.surface` 의 "마스크 원본/근사").
2. **[조정] `core/types.ts`**: `InkSample` 에 `texels: number`(원 안 칠 가능 텍셀 수 — 원본 "전체 0 이면 직전 값 재사용" 규칙용), `PaintWorld` 에 `playerTexels(owner): number`(플레이어 +0xbd4 누적 — p·스페셜 게이지 입력). 지금은 구현 클래스(`PaintWorldImpl.sample` 반환 `InkSampleEx`, `playerPaintTexels`)에만 있다.
3. **[조정] `PaintRequest`**: 선택 필드 `noGauge?: boolean`(요청 C+0, 제트팩 탄), `alpha?: number`(cAlpha 바이트/255) 추가 제안. `kind` 값 목록은 위 1.3 을 DESIGN.md 에 등록 요청. 이벤트 `Paint` 에 `owner` 필드를 더했다(표 갱신 요청).
4. **[weapon] 호출**: 슈터 탄 접촉 순간 `world.paint.request({kind:"Shooter", widthHalf: w, depthScale: ds, pos: 접촉점, normal: 접촉 법선, dir: 수평 진행 방향(§4.4), team, owner: 플레이어 id, seed: 요청 번호})` — 1 프레임 지연·구 질의는 paint 가 한다(무기 쪽에서 또 늦추면 `"ShooterDeferred"`). 스플래시 `"Splash"`, 벽 낙하 `"WallDrop"`(`widthHalf = wallDropSize(PaintRadiusGround)/2`). `core/paint/shape.ts` 의 같은 식(`shooterWidthHalf` 등)을 써도 된다. 복제 탄(+0x6d = 0)은 부르지 않는다.
5. **[render]** 팀 세트(Ink 포함)를 `world.shared` 에 내어 주면(키 등록 필요) paint 는 다시 계산하지 않는다. 원본처럼 시각 메시가 도색 텍스처를 샘플하게 바꾸려면 render 재질 쪽 작업이 필요(지금은 오버레이).
