# Splatoon 3 (v0) 원본 분석 → 웹 포팅 — 인계 문서

이 저장소는 Nintendo Switch 게임 Splatoon 3(v0, XCI)을 바이너리 리버스 엔지니어링으로 분석하고, 그 명세대로 **원본과 같은 동작**을 웹(three.js + TypeScript)으로 다시 만드는 작업입니다. 이 문서는 작업을 이어받는 사람이나 AI가 가장 먼저 읽는 입구입니다.

- 분석 명세 목차: [docs/README.md](docs/README.md)
- 웹 구현 설계 규칙: [games/splatoon3/DESIGN.md](games/splatoon3/DESIGN.md)
- 작업 지침 원문: [분석.txt](분석.txt)

## 1. 절대 규칙

1. **원본과 같은 동작이 목표입니다.** "더 자연스럽게" 바꾸지 않습니다. 원본의 특이한 계산·예외도 확인 없이 정리하지 않습니다.
2. **근거 없는 값을 채우지 않습니다.** 모르는 것은 `[미확정]`으로 두고 "다음에 볼 곳"을 적습니다.
3. **확정 수준을 항상 표기합니다.** `[실행]` 원본 실행(에뮬) 확인 / `[판독]` 원본 명령 판독 / `[데이터]` 데이터 확인 / `[재구현]` 판독식 재구현 계산 / `[추정]` / `[미확정]`. "분석 완료", "웹 구현 완료", "동작 검증 완료"는 다른 상태입니다.
4. **새 근거가 기존 결론을 뒤집으면** 본문을 정정하고 이유와 날짜를 남깁니다. 지우지 않습니다.
5. **원본 파일은 읽기 전용입니다.** `C:/dev/splatoon3/original/`(XCI, prod.keys, title.keys). 키 값은 어떤 문서·출력에도 옮기지 않습니다.
6. **모든 작업 파일은 `C:/dev/splatoon3` 안에 둡니다.** 사용자 요청 없이 git commit 하지 않습니다.

## 2. 폴더 지도

```
C:/dev/splatoon3/
├ original/              원본 (읽기 전용)
├ extracted/             원본에서 뽑은 것 (재생성 가능): exefs/main.reloc.img, romfs/, params/
├ analysis/              분석 산출물
│  ├ notes/SHARED.md     ★ 공유 게시판 — 확정 사실·정정·진행 중 선점 (추가만, `>>`)
│  ├ notes/FUNCS.tsv     ★ 의미가 밝혀진 함수 표 (~650개)
│  ├ decomp/INDEX.tsv    ★ 디컴파일된 함수 색인 (~3,500개)
│  ├ functions/main.nso.tsv  Ghidra 전체 분석 함수 목록 (144,170개)
│  ├ param_reflect/      파라미터 구조체 154종의 필드·오프셋·기본값
│  └ <영역>/             영역별 결과
├ ghidra_proj/           Ghidra 프로젝트 (spl3_main = 전체 분석, f1/f2 사본, q0~q3 raw)
├ .venv/                 파이썬 환경 (capstone, unicorn, zstandard 등)
└ web/                   ← 이 폴더
   ├ docs/               분석 명세 (영역별) + docs/impl/ (웹 구현 기록)
   ├ tools/              분석·변환 도구 (사용법: docs/tools.md)
   ├ games/splatoon3/    웹 게임 본체 (core / client / assets / tests)
   └ scripts/app/games/splatoon3/  페이지 (index.html, main.ts)
```

## 3. 지금 상태 (2026-10-02 기준)

| 기준 | 파악도(판단치) |
|---|---|
| 대전 핵심 한 줄기 (스플래시슈터 · 나와바리 · 한 스테이지) | 약 93% |
| 게임 전체 콘텐츠 | 약 25% |

영역별 상태와 남은 미확정은 [docs/README.md](docs/README.md)의 "기능 문서" 표에 정리돼 있습니다. 각 문서 끝의 미확정 표에는 "다음에 볼 곳"(주소·함수)이 적혀 있습니다.

**분석이 거의 안 된 영역**:
- 슈터 외 무기 10종류, 서브 14종, 스페셜 22종
- 랭크 모드 4종, 연어런, 히어로 모드(스토리)
- 메뉴·로비·상점 UI, BGM

**웹 구현**: 시험 사격장(대전 로비 `Lby_Lobby00`) 1인 연습을 구현 중입니다.
- 영역별 1차 구현 8개(assets·physics·camera·weapon·paint·render·range·fx)가 끝났습니다. 타입 검사 통과, 테스트 119개와 소리 자체 검사 51개가 통과하고, 헤드리스에서 콘솔 오류 없이 루프가 돕니다. 영역 간 통합은 아직입니다.
- 영역별 구현 기록: [docs/impl/](docs/impl/)
- 통합에서 남은 일: 각 `docs/impl/*.md`의 "조정 요청" 절

## 4. 분석하는 방법

main NSO에는 **게임 함수 이름이 없습니다**. 데이터 이름에서 코드로 가는 길은 세 가지입니다.
1. 파라미터 리플렉션: 필드 이름 → 방문 함수 → vtable → 생성자 기본값. 도구는 `tools/param_reflect.py`, 설명은 `docs/02_code_and_params.md`.
2. 클래스 이름 → vtable: Behavior의 `ClassName` 문자열 → vtable 슬롯 2. 도구는 `tools/class_info.py`.
3. 넷 타입 등록: 이벤트·상태 이름 → write/read 함수.

순서:
1. **먼저 확인합니다.** `analysis/notes/SHARED.md`, `FUNCS.tsv`, `PY tools/decomp_index.py <주소|이름>`로 이미 된 것인지 봅니다. 이미 된 분석을 다시 하지 마세요.
2. **디컴파일합니다.** `sh tools/full_decomp.sh <출력.c> <주소...>`(전체 분석 프로젝트, 약 30초, 3개 동시). 함수 시작은 `PY tools/func_lookup.py <주소>`로 찾습니다.
3. **가능하면 원본을 실행해 확인합니다.** unicorn 하네스로 원본 함수를 직접 실행해 재구현과 비트 단위로 대조합니다. 예시는 `tools/network_uc.py`, `life_emu.py`, `move_jump_emu.py`, `paint4_emu.py`.
4. **기록합니다.** 해당 영역 문서를 `분석.txt` 11절 형식으로 쓰고, `SHARED.md`·`FUNCS.tsv`에 한 줄씩 추가(`>>`)합니다.

도구 전체 목록과 알려진 함정은 [docs/tools.md](docs/tools.md)에 있습니다. 함정 예: capstone 범위 디스어셈블이 데이터를 만나면 멈춤, 리플렉션의 커브 필드 오프셋이 꼬임, 사전 인덱스 주소 접근을 스캔이 놓침.

```sh
cd C:/dev/splatoon3
PY=.venv/Scripts/python
$PY web/tools/decomp_index.py 0x7101763a10          # 이미 디컴파일·의미 등록됐는지
$PY web/tools/func_lookup.py 0x7101768bd4           # 주소가 속한 함수
sh web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/<영역>/x.c 0x71...
$PY web/tools/xref.py str SpawnSpeed                # 문자열 참조
$PY web/tools/spl_data.py cat <x.bgyml|x.pack.zs> [팩 안 경로]   # 데이터 → JSON
```

Ghidra는 `C:/dev/mpj/tools/ghidra_12.1.2_PUBLIC`(JDK 21, `JAVA_HOME="C:/Program Files/Java/jdk-21"`)을 씁니다. `ghidra_proj/spl3_main`은 스크립트로만 엽니다.

## 5. 웹 구현하는 방법

```sh
cd C:/dev/splatoon3/web
npm install
npm run dev        # http://127.0.0.1:5190/game/splatoon3/
npm run typecheck
npm test           # node --test games/splatoon3/tests/*.test.mjs
npm run build      # dist/game/splatoon3/
```

- **구조**: `core/`는 결정 로직입니다(DOM·three 금지, `.ts` 확장자까지 import, enum·namespace·parameter property 금지 — Node가 타입만 지우고 실행). `client/`는 three.js 화면·소리·입력입니다. 고정 60Hz 스텝입니다.
- **소유권**: 영역별 폴더가 나뉘어 있고, 공용 계약(`core/types.ts`, `world.ts`, `systems.ts` 등)은 조정자만 고칩니다. 자세한 것은 DESIGN.md §2입니다.
- **정밀도**: 원본 f32 연산은 연산마다 `Math.fround`를 씁니다(`core/fmath.ts`). 탄·이동 코드에는 FMA가 없다는 판독이 있습니다. 난수는 `sead::Random`(`core/rng.ts`)입니다.
- **에셋**: GLB·KTX2·Opus·JSON. `assets/catalog.json` 번들 단위로 판마다 필요한 것만 받습니다(현재 8개 번들, 17.7MB). 변환기는 `tools/asset_*`이고, 형식·원본과 다른 점·추정한 것은 `docs/impl/assets.md`에 있습니다. 다시 만들 때는 `cd C:/dev/splatoon3 && .venv/Scripts/python web/tools/asset_build.py`(전체 약 3분, 검증 포함)를 씁니다.
- **입력**: 원본 조이콘 대신 마우스·WASD를 씁니다. 대응표와 근거는 DESIGN.md §6과 `docs/impl/camera.md`입니다.
- **검증**: 핵심 계산은 원본 실행 결과나 판독식 재구현과 비트 일치하는 테스트를 둡니다. 기존 테스트 기대값은 근거 없이 바꾸지 않습니다.
- **최종 이식 대상**: `E:/programming/python/ddalkkakrider_work/web`의 `games/` 아래입니다. 폴더 구조가 1:1이라 `games/splatoon3/`와 `scripts/app/games/splatoon3/`만 옮기면 됩니다. 단 포털 서버의 에셋 허용 확장자(json|png|ogg|flac)에 glb·ktx2·bin·wasm을 추가해야 합니다.

## 6. 다음에 할 일 (우선순위)

1. **사격장 통합 마무리**
   - 각 `docs/impl/*.md`의 조정 요청을 처리합니다(계약 필드 추가, 이벤트 표, 시스템 순서).
   - 4차 분석 결과로 근사를 교체합니다:
     - 캐릭터 컨트롤러 규칙(`docs/physics/character_controller.md`)
     - 지형 도색 아틀라스(`docs/paint/colpaint_atlas.md`)
     - 스테이지 렌더링(`docs/graphics/stage_rendering.md`)
   - 브라우저에서 전체 동작을 확인합니다.
2. **슬라이스 남은 미확정**: 액터↔물리 엔진의 프레임 내 순서, 톤매핑, 히트마커 조건 등입니다. 각 문서의 미확정 표를 보면 됩니다.
3. **폭 넓히기**: 다른 무기 종류 → 서브·스페셜 → 랭크 모드 → 연어런 → 스토리. 슈터에서 쓴 방법(리플렉션 → vtable → 디컴파일 → 에뮬 대조)을 그대로 반복합니다.
4. **UI·대전·네트워크**: 분석 명세는 `docs/ui`, `docs/network`에 있습니다.
