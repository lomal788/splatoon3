# splatoon3 웹 구현 설계 규칙

원본(Splatoon 3 v0)의 관측 가능한 동작을 그대로 재현하는 것이 목표입니다. "더 자연스럽게" 바꾸지 않습니다.
근거 문서는 `web/docs/`(분석 명세)이고, 구현 상태·원본과의 차이·미확정은 `web/docs/impl/<영역>.md`에 남깁니다.

## 1. 폴더와 이식 규칙

```
web/
├ games/splatoon3/            ← 이식 시 ddalkkakrider_work/web/games/splatoon3/ 로 그대로
│  ├ core/      결정 로직. DOM·three·fetch 금지. Node 24 로 직접 실행 가능해야 함
│  ├ client/    three 화면·소리·입력. core 를 읽기만 함
│  ├ assets/    빌드된 웹 에셋(GLB·KTX2·Opus·JSON). catalog.json 이 입구
│  ├ tests/     *.test.mjs (node --test). core 를 직접 import
│  ├ bundle.mjs esbuild(포털 mgh5 와 같은 형태)  tsconfig.json  env.d.ts  DESIGN.md
├ scripts/app/games/splatoon3/  ← 이식 시 그대로: index.html, main.ts, style.css
├ tools/      개발 서버·빌드(serve.mjs, build.mjs, vendor.mjs) + 에셋 변환기(asset_*) + 분석 도구
└ docs/       분석 명세(기존) + impl/(구현 기록)
```

- URL 은 포털과 같습니다: `/game/splatoon3/`(페이지), `/game/splatoon3/app.js|app.css`, `/game/splatoon3/assets/*`. 코드에서는 `client/env.ts` 의 `ASSETS` 만 씁니다.
- import 방향: `scripts/app/.../main.ts → games/splatoon3/client → core`. core 는 client·scripts 를 import 하지 않습니다.
- core 문법 제한: import 는 `.ts` 확장자까지 명시, enum·namespace·생성자 parameter property 금지(`erasableSyntaxOnly`). Node 가 타입만 지우고 실행하기 때문입니다.
- 저장소 키·전역 이름은 `splatoon3.` 접두어를 붙입니다.
- three 는 npm `three@0.180` 을 bare import 합니다(`three`, `three/examples/jsm/...`). 포털 vendor 와 같은 r180 입니다.

## 2. 영역과 담당 폴더

| 영역 | 담당 폴더 (이 폴더 밖은 고치지 않음) | 근거 문서 |
|---|---|---|
| assets | `tools/asset_*`, `games/splatoon3/assets/**` | graphics/*, effect_sound/*, gimmick/collision_mesh.md, 01 |
| physics | `core/collision/`, `core/player/` | player/*, physics/phive_controller.md, gimmick/collision_mesh.md |
| camera | `core/camera/`, `client/camera/`, `client/input.ts` | camera/player_camera.md, aim_swerve.md |
| weapon | `core/weapon/` | weapon/shooter_bullet.md, camera/aim_swerve.md, combat/damage_hit.md |
| paint | `core/paint/`, `client/paint/` | paint/*, graphics/shaders.md(도색) |
| render | `client/render/` | graphics/*, player/player_state.md(애니 상태) |
| fx | `client/fx/`, `client/audio/` | effect_sound/*, camera/shake_rumble.md |
| range | `core/range/`, `client/range/` | (사격장 표적은 새로 분석) gimmick/*, combat/* |
| 조정 | `core/world.ts types.ts systems.ts input.ts events.ts params.ts fmath.ts rng.ts`, `client/app.ts views.ts context.ts assets.ts env.ts`, `scripts/**`, `tools/serve·build·vendor.mjs` | — |

조정 파일을 바꿔야 하면 직접 고치지 말고 `docs/impl/<영역>.md` 의 "조정 요청" 절에 적습니다. 공용 계약(`core/types.ts`)에 필드가 필요하면 같은 방식으로 요청합니다.

영역 간 공유 상태는 `world.shared` 에 키로 둡니다. 키는 아래 표에 등록합니다(쓰는 영역만 쓰기).

| 키 | 쓰는 영역 | 내용 |
|---|---|---|
| `player` | physics | 로컬 플레이어 상태 객체(위치·속도·상태 번호·오징어 여부·팀·잉크량 등) — 타입은 `core/player/` 에서 export |
| `camera` | camera | 조준 yaw/pitch, 카메라 위치·주시점·FOV, 조준 방향 벡터 |
| `bullets` | weapon | 살아 있는 탄 목록(표시용 읽기 전용) |
| `paintSurfaces` | paint | 도색 표면 정의(클라이언트 표시용) |
| `range` | range | 표적 목록·상태 |
| `debug` | 누구나 | 개발 표시용 숫자(키 접두어로 영역 이름) |

## 3. 프레임 순서 (고정 60Hz)

`core/systems.ts` 순서대로 step 합니다. collision → range → camera → player → weapon → paint.

- 원본 근거: 탄 갱신 순서(이전 위치 저장 → age++ → 이동 → 물리 적분 → 이동 후 처리)는 weapon/shooter_bullet.md §3.2, 플레이어 프레임 순서는 player/movement_physics.md. **액터 종류 간 순서(카메라·플레이어·탄·표적 중 무엇이 먼저인지)는 원본에서 확정하지 못했습니다 [미확정].** 지금 순서는 추정이고, 바꿀 근거를 찾으면 조정 요청으로 올립니다.
- 표시는 렌더 프레임마다 `View.update(world, alpha)` 를 부릅니다. 보간이 필요하면 각 뷰가 이전 스텝 값을 보관합니다.

## 4. 이벤트 (core → client)

`world.events.emit({ type, ... })`. 화면·소리만 소비하고, 결정 로직은 이벤트에 의존하지 않습니다. 이름은 원본 xlink 키를 우선합니다.

| type | 보내는 영역 | 필드 | 원본 대응 |
|---|---|---|---|
| `Fire` | weapon | owner, pos, dir, weapon | xlink "Fire" (SLink만) |
| `FireImpact` / `FireOn` / `FireOff` | weapon | owner | 무기 액션 슬롯 0 (머즐 플래시) |
| `BulletSpawn` / `BulletDie` | weapon | id, kind, pos | 탄 파티클 WpShtrBullet1Emit |
| `BulletHit` | weapon | id, pos, normal, surface("Floor"/"Wall"/"Object"), paintable | 착탄 이펙트·사운드 |
| `Paint` | paint | team, pos | (표시 갱신 힌트) |
| `Damage` | range/combat | target, value, critical, pos | 히트마커·히트 사운드 |
| `Jump` / `Land` / `ToSquid` / `ToHuman` / `Swim` | physics | owner, pos | 플레이어 xlink |

새 이벤트는 이 표에 추가하고 `docs/impl/<영역>.md` 에도 적습니다.

## 5. 에셋

형식: 모델 **GLB**(meshopt 압축 가능, 텍스처는 KTX2/Basis), 텍스처 **KTX2**, 소리 **Opus(.ogg)**, 데이터 **JSON**(+ 큰 배열은 .bin).

```
assets/
├ catalog.json                 번들 목록: { version, bundles: { "<종류>/<id>": { dir, files[], deps[], bytes } } }
├ common/                      항상 받음: lib/basis(트랜스코더), data/(param_defaults, 상수, 공용 표)
├ maps/<mapId>/                맵: visual.glb, collision.json + collision.bin, placement.json, env.json, params/*.json
├ characters/<charId>/         캐릭터: body.glb, squid.glb, parts/*.glb, anim/*.glb, data/*.json
├ weapons/<weaponId>/          무기: model.glb, params/<표>.json(무기·탄 GameParameterTable)
├ effects/<group>/             이펙트: emitters.json, tex/*.ktx2
├ sfx/<group>/                 효과음: *.ogg, sfx.json(이벤트 → 파일·볼륨·피치 규칙)
└ ui/                          (나중)
```

- 번들 id: `common`, `map/<mapId>`, `character/<charId>`, `weapon/<weaponId>`, `effect/<group>`, `sfx/<group>`. 무기·캐릭터 번들은 필요한 effect/sfx 번들을 `deps` 로 겁니다.
- 판 시작 때 `bundlesFor(spec)` → `AssetLoader.load()` 가 의존까지 펼쳐 필요한 것만 받습니다.
- 코어에 넘어가는 데이터 규칙(`client/app.ts matchData`): 어느 번들이든 `params/<표>.json` 은 파라미터 표, `data/<이름>.json` 은 `world.data.tables[이름]`.
- 원본 추출물(`extracted/`)은 웹 에셋 폴더에 두지 않습니다.

## 6. 입력 (원본 조이콘 → 웹)

| 웹 | 원본 | 비고 |
|---|---|---|
| WASD | 왼쪽 스틱 | 대각선 길이 1로 정규화. 원본 스틱 응답 곡선(|v|^4 등)은 physics 가 그대로 적용 |
| 마우스 이동 | 오른쪽 스틱 + 자이로 | **이식 차이**. 원본 yaw/pitch 회전 규칙 위에 마우스 델타를 각도로 직접 더함. 대응식은 camera 담당이 docs/impl/camera.md 에 기록 |
| 좌클릭 | ZR(사격) | |
| Shift | ZL(오징어) | |
| Space | B(점프) | |
| 우클릭 / E | R(서브) | 연습장 1차 범위 밖 |
| Q | 스페셜 | 범위 밖 |
| R | — | 웹 전용: 시작 위치로 |

## 7. 정밀도

원본 f32 연산은 `core/fmath.ts` 의 `f32`(Math.fround)로 연산마다 맞춥니다. 탄·이동·점프 코드는 FMA 가 없다는 판독이 있으므로 연산 순서를 문서 식 그대로 둡니다. `sead::Random` 은 `core/rng.ts`.

## 8. 기록 규칙 (docs/impl/<영역>.md)

각 영역은 자기 문서를 만들고 다음을 유지합니다.

1. 구현한 것 — 원본 근거 문서·주소와 함께
2. 원본과 다른 점 — 웹 이식 때문(입력 등)인지, 미구현 때문인지
3. 미확정·추가 분석 필요 — 무엇을 보면 풀리는지
4. 검증 — 테스트 이름, 재구현 계산과의 대조, 원본 실행 대조
5. 조정 요청 — 조정 파일·공용 계약 변경 요청
