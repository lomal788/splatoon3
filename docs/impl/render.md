# render — 화면(맵·캐릭터·무기·애니메이션·팀 컬러·조명)

담당 폴더 `games/splatoon3/client/render/`. 근거 문서: `docs/graphics/{team_color,shaders,player_assembly,anim_state_machine}.md`, `docs/player/player_state.md`.
확정 수준 표기는 docs/README.md 를 따른다([데이터]/[판독]/[추정]/[미확정]/[근사] = 웹 표시용 근사).

## 1. 구현한 것

### 1.1 파일

| 파일 | 내용 |
|---|---|
| `index.ts` | 뷰 진입점. 번들(캐시) → 맵 → 팀 세트 → 플레이어 조립. 게임 프레임(60Hz)마다 애니 1스텝, 렌더 프레임마다 보간·포즈·표시 |
| `teamcolor.ts` | 팀 컬러 14색·재질 파라미터. `web/tools/graphics_verify/teamcolor.mjs` 의 TS 이식 |
| `hoian.ts` | Hoian_UBER 재질 근사(팀색 혼합식·방출 색·calc_color 일부를 `onBeforeCompile` 로 덧씌움) |
| `model.ts` | 텍스처 찾기, 바인드 행렬, 파츠 결합(`attach`), 재질 extras 정규화(`fresOf`) |
| `map.ts` | 맵 visual.glb 배치·정적 병합·env 조명·그림자, 에셋 없으면 격자 바닥 |
| `player.ts` | 몸·파츠·_Hlf·오징어·무기 조립, 하네스·입 모양 선택, 표시 모델 전환, 포즈 적용 |
| `shared.ts` | `world.shared.player`(physics `PlayerState`) 읽기 |
| `anim/asb.ts` | ASB 데이터·블랙보드·실수 파라미터 표·트리 평가·FloatBlend |
| `anim/slot.ts` | 래퍼·슬롯 0 엔트리 전진·FrameController·전환 블렌드·잎 가중치 |
| `anim/animator.ts` | 상태 번호 → 커맨드 요청, 블랙보드 공급, SM+0xf0, 표시 플래그, 몸 스프링 |
| `anim/asb_data.json` | 원본 `SplPlayer.pack.zs` `AS/SplPlayer.root.asb`·`AS/SplPlayerSquid.root.asb` 를 `gen/asb_gen.mjs` 로 변환 |
| `anim/state_table.json` | 상태 표 0x7105630270 (player_state.md 부록 → `gen/state_table_gen.mjs`) |
| `gen/shot.mjs` | 헤드리스 스크린샷(개발 서버 + playwright-core + 설치 Chrome) |

재생성:
```sh
cd web
node games/splatoon3/client/render/gen/asb_gen.mjs C:/dev/splatoon3/extracted/actor/SplPlayer/AS/SplPlayer.root.asb C:/dev/splatoon3/extracted/actor/SplPlayer/AS/SplPlayerSquid.root.asb games/splatoon3/client/render/anim/asb_data.json
node games/splatoon3/client/render/gen/state_table_gen.mjs docs/player/player_state.md games/splatoon3/client/render/anim/state_table.json
```

### 1.2 팀 컬러 (team_color.md 전부)

- `buildTeamSets(row, swap, envLight)` = 0x7101176830 → 0x71011743a0 → 0x7101174534. pow 2.2 선형화, hsvOffset(0x7101188334, 특이점 3개 포함), inkCorrection(0x7101174afc, Model/Ink/InkBright), HueDirPeak 반전, Tag 4/5 이면 세트2 = Charlie. env 가 없으면 Ink/InkBright 를 비워 둠(원본 조기 return).
- `materialTeamParams(set, renderInfo)` = 0x7101103490 (my_team_color = Model, type 7/10/8 덮어쓰기, hue_complement).
- 행: `common/data/team_color.json` 의 `dataSets` 에서 `OrangeBlue`(없으면 같은 값 내장). 내 팀 = `players[0].team` 의 세트(0/1/2). 경기 시작 때 한 번 계산(§7.2).
- Ink/InkBright 입력: 맵 env 의 주 방향광 색·세기(§1.4). skyUp(하늘 SH 위쪽 조도)는 런타임 값이라 null.

### 1.3 셰이더 근사 (shaders.md §3.6~3.7)

원본 식 그대로 넣은 것 [판독 식]:
- `team_color_map_type 2`: `k = clamp(Tcl(_su0).r + team_color_blend_alpha, 0, 1)`, `albedo = mix(base, my_team_color, k)`, base = `enable_albedo_tex` 이면 알베도 텍스처, 아니면 `albedo_color`.
- `team_color_map_type 3`: `albedo = mix(albedo_color, my_team_color, clamp(team_color_blend))`.
- `emission_color_type 2`: 방출 = `my_team_color`, `1`: 혼합 알베도 × `_e0`. 세기는 `emission_intensity × emission_color`(곱 순서는 근사).
- `blitz_calc_color0..3` 중 `replace_color 0`(알베도)·`100`(임시) 대상만, calc_type 1/2/6/8/9/11, 소스 0(혼합 전 알베도)·50(my_team_color)·100~102(const_color)·110/111(const_value)·200+k, 채널 0/1/10/20/30/11, clamp01. 예: Player00 M_Body 피부 = 알베도 × const_color0, 무기 잉크병 = albedo + my_team_color.
- 팀색 uniform 은 `my_team_color`, `my_team_color_hue_complement` 둘(원본 샘플 프로그램이 읽는 것도 이 둘뿐, team_color.md §7.3).

PBR 근사(three `MeshStandardMaterial`)로 대신한 것 — **원본과 다름** [근사]:
- 최종 셰이딩 전체(Env/Context/BlitzUBO1·2 블록 미해독): 확산·반사·프레넬, 환경 BRDF·프리필터 큐브맵(`cPrefilEnvMapArray`), irradiance/edge irradiance, 동적 라이트 그리드.
- 투과·SSS(`enable_taransmission`, cheap_sss, thickness, edge_transmission), 투과 필름(`enable_transfilm`, 머리카락·오징어 몸의 `(_re0 + hue_complement) × under_film_color`).
- 2cl(CompPaint) 잉크 묻음 분기(§3.6.3, BlitzUBO0 Ink/InkBright) — 평소엔 `two_color_complement_paint_intensity = 0` 이라 꺼지는 경로.
- calc_color: 투과(1)·방출(2)·거칠기(4)·금속도(5)·불투명도(6)·필름(7) 대상, 텍스처 소스(9/10 cTexResource, 2 metalness 등)와 calc_type 5·22 등. 건너뛴 목록은 `player.info.skipped`(DEV 콘솔 `[render]`).
- 베이크 그림자·라이트(`_b0/_b1`, 로비 재질은 `BakeDummy` 텍스처), 안개(DepthFog/HeightFog), 컬러 그레이딩·HDR 노출, DOF, 하늘 구(Sky_Daytime00) — 미구현.
- 재질 애니(`Color_Eye`, `Color_Skin`, `Blink`, `Eye_Scroll`), `tex_mtx0` 스크롤 — 미구현(첫 프레임 값).
- `texcoord_select_*` ≠ 0(§3.7)은 팀색 마스크에만 확인하고 미지원 시 skipped 에 남김.

### 1.4 맵 (map.ts)

- 번들 `map/Lby_Lobby00` 의 `visual.glb`(없으면 첫 glb), 없으면 200×200 격자 바닥.
- 정적 병합: (재질, 속성 구성, 40 유닛 공간 칸) 같은 메시를 `mergeGeometries` 로 합침. 칸으로 나눠 three 프러스텀 컬링이 칸 단위로 남는다. 스킨·모프·다중 재질은 그대로. 로비: 메시 125 → 93, 삼각형 146k.
- 루트 이름 `splatoon3.map`(다른 영역이 `scene.getObjectByName` 으로 찾을 수 있음). 병합 메시 `userData.sources` = 원래 메시 이름.
- env.json(assets 형식) → 조명:
  - 주 방향광 색·세기 = `teamColorLight.lobbyMainLight`(RenderingDay MainLight Color (0.671,0.851,1.0), Intens 10) — MainLight→DirectionalLight 대응 [추정, team_color.md §5.3]. 없으면 `defaultDay`(1,1,1)/4.0.
  - 방향 = **MainLight Latitude/Longitude → `lonLatToDir`**: env 접근자 `MainLightDirLongitudeLatitude` set 0x710104dea8 [판독] `Direction = (−sin(lon)·cos(lat), −sin(lat), −cos(lon)·cos(lat))`, 도→라디안 0.017453292, `sinf`/`cosf` 임포트(PLT 0x7103e9be40/0x7103e9be30), 결과는 DirectionalLight+0x1c0. 입력 vec2 순서 (lon, lat) 와 RenderingDay 경유는 [추정]. 로비 → (0.0431, −0.5664, −0.8230). 기본 env Day Direction (−0.3,−0.7,−0.6) 도 같은 꼴(lat 46.2°, lon 26.6°).
  - 배경색 = `rendering.Fog.DepthFog.Color`(sRGB 로 보고 선형화) [근사: 하늘 구 대신].
  - three 세기 = 원본 Intensity × 0.25, 헤미스피어 1.0(하늘 = 안개색, 땅 = 상수) [근사: HDR 합성 미해독, 화면 밝기 맞춤 값].
- 동적 그림자 [근사]: 주 방향광 1024² 그림자맵, 플레이어 주변 ±6 유닛만(원본 동적 깊이 그림자 캐스케이드 설정 미해독). 맵 메시 receive, 플레이어 cast.

### 1.5 캐릭터 조립 (player_assembly.md §5.4·§6)

- 번들 `character/<id>` 의 glb 를 이름으로 분류: 몸 `body|Player0N`, `_Hlf` `*_Hlf|hlf`, 오징어 `*squid*|*octopus*`, 파츠 접두 `Har/Eyb/Clt/Btm/Shs/Tnk/Hed`(종류마다 첫 번째), 나머지는 애니 클립 묶음.
- 결합(§6.3, `model.ts attach`): Har/Eyb `Head_Root→Head`, Clt/Btm `Skl_Root`, Shs `Leg_2_L` + 오른발 미러(`*_L→*_R`, Scale(−1,1,1), BackSide), Tnk `Spine_3`, Hed `Root→Head` translate, 무기 `Root→Weapon_R` full(번들 `weapon/<id>` 의 `model.glb`). `_Hlf` 는 같은 뼈 이름으로 몸 스켈레톤에 묶음(0x7101459154 뼈 복사).
- 하네스(§6.1, 0x71026f8f38): 메시 `visBone` 이 `Harness_{S,M,L}[F]`/`Harness_Hide` 중 옷의 값과 다른 것은 숨김. 옷 Clt_SHT000 = S/thin false/hide false [데이터: GearInfoClothes] — 번들에 옷 데이터가 오면 거기서 읽도록 바꿀 것.
- 입 모양: `Mouth01~04_Model` 숨김, Mouth00 만(가시성 애니 미구현).
- 재질 extras 두 형식 지원: `extras.fres`(graphics_bfres2gltf) / `extras.hoian`(에셋 번들). 팀색 마스크 등 PBR 슬롯 밖 텍스처는 glb 이미지 이름 → 번들 `*.ktx2` → glb 옆 `tex/<이름>.png` 순서로 찾음.
- 위치·방향: `PlayerState.pos`(발 위치)·`facing` 을 게임 프레임 사이 alpha 로 보간(방향은 최단각).

### 1.6 애니메이션 (anim_state_machine.md, player_state.md)

- 상태 번호 → 상태 표 행(커맨드, 모델, 블렌드 프레임, 플래그). 0x11e 이상은 표[0].
- 래퍼 2개(사람/오징어) + 슬롯 0. 다른 모델로 넘어갈 때 새 상태 플래그 bit3 이면 이전 래퍼를 정지하지 않고 표시만 남김(래퍼+0x38), 아니면 정지(cmd = −1).
- 커맨드 요청 프레임 cur = 0 → 같은 프레임 틱에서 1(§4.2). 전진 0x71039ab2c4 그대로(round4, 비반복은 end = FSKA FrameCount 에서 정지, 반복 감싸기식). end/loop 는 glTF `animation.extras.frames/loop`.
- 트리 평가: StringSelector(case, 없으면 その他), IntSelector, BoolSelector, FloatBlend(§4.4: 첫 [lo,hi) 구간, 겹치면 선형 가중, 0.01/0.99 스냅, 범위 밖은 마지막 자식), Simultaneous, Sequence, 잎(스켈레탈/재질/가시성) + 부착 FrameController(rate/start/end/mode).
- 실수 파라미터 표(§2.7): bb 값 → 변화율 제한 → `clamp(offset + scale·x, min, max)`.
- 블랙보드(§4.6): MoveSpeedRt = `e0 += 0.2·(clamp((v−0.027)/0.023,0,1) − e0)`(사람 이동 상태 0x5e~0x81 밖이면 0), StainFrm 0, EquipWeaponMain 참, WeaponCategory "Shtr", JumpVarID 0.
- 클립 이름 치환 `Nrml → Shtr`, `@ → Win01`(§3).
- 전환 블렌드(§4.5): B = 노드 레코드 타입 0 값 또는 상태 표 블렌드, `t += dt/B`, ease-in-out 2차, 이전 층은 계속 재생하며 최대 4층, 층 가중 `w_i·Π(1−w_j)`.
- 표시 모델(§5.4): (a) SM+0xf0 갱신(physics 의 `transform` 이 있으면 그 값), (b) `hlf = humanOn && f0 ≥ 61`, `body = humanOn && !hlf`, `squid = squidOn`, 둘 다 꺼지면 f0 = 90/140, (c) 사람·오징어 동시면 상태 {0x91..0x98, 0xad, 0xae, 0xf1, 0xf2} 이고 (cur==0 && 직전 0x82..0x84) 가 아니면 오징어 끔, 아니면 사람 끔 → 한 프레임에 한 모델.
- 몸 스프링 0x71014586a0: 몸이 0→1 로 켜질 때 x = −0.03, v += 0.02, 매 프레임 `v = (v − 0.2x)·0.8; x += v`, 스케일 (1+1.5x, 1+x, 1+1.5x).
- 파츠·무기·탱크는 `body || hlf` 일 때 보임.
- 포즈 적용: three `AnimationMixer` 에 잎마다 액션(LoopOnce + clamp), `time = frame/60`, 가중치 = 잎 가중치, `mixer.update(0)`. 렌더 보간으로 다음 틱까지 alpha 만큼 앞 프레임을 샘플(원본에 없는 표시 보간).
- physics 가 상태를 안 줄 때(`state` 없음)의 임시 대응: 0x56/0x5f/0x85/0x87, 전환은 0x82→0x84, 0x91→0x92 를 원본 판정식 `end < cur + 3` 으로 [표시 확인용, 원본 전이 규칙 아님].

## 2. 원본과 다른 점

| 항목 | 이유 |
|---|---|
| 최종 셰이딩·조명 전부 PBR 근사(§1.3 목록) | 조명 UBO 미해독 (근사) |
| 조명 세기 배율 0.25, 헤미스피어, 배경 = 안개색 | HDR 합성·하늘 구 미구현 (근사, 웹 값) |
| 그림자: 플레이어 주변 1024² 하나 | 원본 캐스케이드 설정 미해독 (근사) |
| 슬롯 1(보조 상체 레이어) 미사용 | 뼈 그룹 이름 [미확정] (player_state.md §4 bit5~10) |
| 재질·가시성 애니(Sqd_Wait 재질 등) 미적용, 입 모양 Mouth00 고정 | 미구현 |
| 머리카락 천 물리 없음(고유 뼈 정지) | TAG0 상수 미해독 (player_assembly §6.1) |
| 모자 ManualBindSRT·HairArrange 미적용 | 결합 순서 [미확정] |
| GearAlphaMask(몸 가림) 미적용 | 재질 슬롯 바인딩 [미확정] |
| `_Hlf` 모델이 번들에 없으면 그 구간은 몸으로 대신 그림 | 웹 대체 |
| 스프링 트리거: 몸 표시 0→1 | 트리거 조건 해석 [추정] |
| 클립이 없으면 그 잎은 가중 0(바인드 포즈 쪽으로 섞임) | 원본 대체 규칙 [미확정] |
| 렌더 보간(포즈 alpha 앞당김·위치 보간) | 웹 표시용 |
| 한 렌더 프레임에 게임 스텝이 여러 개면 마지막 상태로 그만큼 진행 | 뷰는 스텝마다 불리지 않음 |

## 3. 미확정·추가 분석 필요

| 항목 | 풀리는 곳 |
|---|---|
| 로비 시험 사격장의 TeamColorDataSet 행(지금 OrangeBlue)과 내 팀 swap | 로비 씬 팀색 결정 호출자(0x7101178030 → 0x7101176830) |
| BoolSelector 자식 순서(0 = 참) | 노드 종류 21 진입 함수(점프표 0x7104af3260) |
| 선택 노드 재평가 시점(지금은 요청 때 한 번) | AS 노드 vt 갱신 함수 |
| IntSelector 기본 항목(지금 마지막 항목) | 노드 종류 8 진입 |
| 실수 파라미터 rate 0 의 의미(지금 제한 없음), 모드 1(각도) 감싸기 | 0x7103997de0 |
| WeaponCategory/WeaponDetail/JumpVarID 실제 값 | anim_state_machine §4.6 호출자 |
| 사람 걷기 재생 속도식(요청 rate) | state_big_full.c 2725~2985행 — physics `stateRate` 를 그대로 씀 |
| FloatBlend 자식 프레임 동기화 | 0x71039bcb9c |
| Sequence 진행 조건(앞 자식 끝) | 노드 종류 7 |
| 다층 포즈 합성 방식(지금 가중 합) | 0x71039cd350, 0x71039be4a0 |
| 스프링 스케일 축 대응(+0x268/+0x26c/+0x270 = x,y,z) | 모델 +0x268 사용처 |
| MainLight Latitude/Longitude 입력 순서·RenderingDay 경유 | 0x710104dea8 호출자 |
| 하늘 SH 위쪽 조도(Ink/InkBright 의 skyUp) | team_color.md §9 |
| 옷 하네스 값을 번들 데이터에서 읽기 | 에셋이 GearInfoClothes 행을 줄 때 |

## 4. 검증

- 팀 컬러 TS 이식 = 참조 구현 비트 일치: 36행 × swap 2 × 조명 3가지 × 세트 4 × 14색, 46,080 값 최대 차 0 (f32 비교). OrangeBlue set0 Model (0.6421, 0.1149, 0.0123), set1 HueDark (0.3860, 0.0652, 0.6168) = team_color.md §8 표. [재구현 대조]
- ASB 변환: 커맨드 → 클립 `WaitHold → WaitHold_Shtr`, `WalkHold → blend(blend(WalkHold_Shtr, RunHold_Shtr), InjectionLanding_Shtr)`, `Jump_St → Jump_Shtr00_St`, 오징어 `Wait → sim(Sqd_Wait 스켈, Sqd_Wait 재질)`, `Emote_@` 레코드 블렌드 10(§2.3 과 일치), 오징어 36 FrameController start/end = bb DirectAnimStartFrm/EndFrm(§4.3 과 일치).
- 전환 시뮬(클립 길이 = player_state.md §6.2 데이터 6/13/3/30, 전이 판정 `end < cur + 3` 을 시험 쪽에서 흉내):
  - ToSquid 요청 프레임 S 에 사람 cur 1 → S+4 에 0x84, 사람 클립 프레임 1~4 표시(§4.2 예와 같음). `_Hlf` 는 0x82 의 4번째 프레임(f0 70)부터(§5.4 와 같음).
  - 0x91 → 다음 프레임 0x92, `_Hlf` 29프레임(f0 89..61) 뒤 몸(ToHuman cur 30)과 동시에 스프링 시작.
  - 한 프레임에 두 모델 동시 표시 0회.
- 헤드리스 스크린샷(`node games/splatoon3/client/render/gen/shot.mjs --fake --map games/splatoon3/assets/maps/Lby_Lobby00/visual.glb ...`, swiftshader): `test/out/render_wait.png`(WaitHold_Shtr, 머리카락·잉크탱크 팀색 주황, 그림자), `render_shoot.png`(Shoot_Shtr, 무기 손), `render_squid.png`(Sqd_Wait, 오징어 팀색), `render_wide.png`(로비 전경, 드로우콜 ~100, 삼각형 ~150k), `render_real.png`(주입 없이 physics `PlayerState` 그대로: 시작 위치 (−0.149, 0, −11.959), 상태 0x56 WaitHold), 결과 요약 `test/out/render_shots.json`. `--fake` 는 캐릭터 GLB 를 `analysis/graphics/web`(graphics_bfres2gltf 출력, 클립 4+2개)으로 대신한다 — 에셋 번들의 캐릭터 GLB 가 나오면 `--fake` 없이 다시 찍을 것.
- 원본 화면과 픽셀 비교는 하지 않음.

## 5. 조정 요청

1. **[assets] 캐릭터 번들 `character/Player00`** 에 GLB 필요(지금 data/params 만): 몸 `Player00`(또는 `body`), `Player00_Hlf`, `Player_Squid`(오징어), 파츠 `Har_*`, `Eyb_*`, `Clt_*`, `Btm_*`, `Shs_*`, `Tnk_*`(이름 접두로 분류). 애니: Player00 스켈레탈 클립(적어도 상태 표 커맨드가 고르는 `WaitHold_Shtr, Wait, WalkHold_Shtr, RunHold_Shtr, Walk, Run, Shoot_Shtr, WaitShoot_Shtr, WalkShoot_Shtr, RunShoot_Shtr, Walk{Left,Right,Back}Shoot_Shtr, Run{Left,Right,Back}Shoot_Shtr, Jump_Shtr00{_St,,_Ed}, Jump00{_St,,_Ed}, JumpShoot_Shtr00{_St,,_Ed}, ToSquid, ToHuman, InjectionLanding_Shtr`)와 오징어 `Sqd_*`. glTF `animation.extras = {frames(FSKA FrameCount), loop}` 유지 필요(끝 프레임 규칙). 별도 glb 로 나눠도 됨(몸과 같은 뼈 이름이면 그대로 붙음).
2. **[assets] 무기 번들 `weapon/Shooter_Normal_00`** 에 `model.glb`(Wmn_Shooter_NormalT).
3. **[assets] 재질의 PBR 밖 텍스처**: 팀색 마스크 `_su0`(Tcl)는 셰이더가 직접 샘플한다. glb `images` 에 이름(텍스처 이름 그대로)으로 넣거나 번들에 `<이름>.ktx2` 로 넣어 줄 것(지금 render 는 둘 다 찾음). `_cp0`(2cl)은 아직 안 씀.
4. **[assets] 맵 카탈로그**: `maps/Lby_Lobby00/visual.glb` 가 폴더에는 있지만 catalog `map/Lby_Lobby00` files 에 빠져 있다(지금 render 는 격자 바닥으로 그림).
5. **[assets] 옷 하네스 값**: GearInfoClothes 행(HarnessType/IsThinHarness/IsHideHarness)을 캐릭터 data 로 주면 내장값 대신 읽겠다.
6. **[physics]** render 가 읽는 `PlayerState` 필드: `pos`, `facing`, `vel`, `state`, `transform`(SM+0xf0), `stateRate`, `team`. 추가로 있으면 쓰는 것: `sub`(보조 상태, 슬롯 1용), `animSpeed`(SM+0xd4, 없으면 수평 속력), `dead`. physics 의 전환 판정(`stateFrame/stateEnd`)은 `sm.ts` CLIP 표 길이를 쓰고 render 는 GLB `frames` 를 쓴다 — 두 값이 같아야 화면 클립 끝과 전환 프레임이 맞는다.
7. **[조정] `client/app.ts`**: 없음(번들은 `ctx.assets.load` 캐시로 다시 받음). 렌더러 그림자맵은 render 가 `createRenderView` 에서 켠다(`renderer.shadowMap.enabled`, PCFSoft).
