# 사격장 그래픽(캐릭터) 원본 실행 검증 기록

작성: 2026-10-03, 갱신: 2026-10-03(r5 gfx_char, r6 gfx_char). Lby_Lobby00 1인 연습 범위의 캐릭터·무기·애니 그래픽 검증 기록이다. 웹 구현 파일은 수정하지 않았다.

**이 문서는 검증 기록만 둔다.** 확정한 동작·식은 본문 문서의 해당 절로 옮겼다(2026-10-03 r5). 아래 표의 "본문"이 근거 위치다.

## 1. 기능 개요와 사용자에게 보이는 동작

사격장에서 보이는 내 캐릭터는 몸·파츠·무기·모자와 애니메이션으로 그려진다. 이 문서는 그중 원본 함수를 unicorn 으로 실행해 판독식과 비트 비교한 항목을 모은다. 동작 설명은 본문 문서를 본다.

## 2. 원본·버전·자료 위치

- v0 `extracted/exefs/main.reloc.img`, 기준 주소 0x7100000000.
- 하네스: `web/tools/completion_head_matrix_emu.py`(이전 회차), `web/tools/r5_gfx_char_*.py`(r5). 공용 실행 틀은 `web/tools/network_uc.py` 와 `web/tools/r5_gfx_char_uc.py`(PLT 처리 추가)다.
- 결과: `analysis/completion/graphics_head_matrix_emu.json`, `analysis/completion/r5/gfx_char_*.json`.
- 디컴파일: `analysis/decomp/gfx4/p_batch1.c`(이전 회차 재사용), `analysis/decomp/r5_gfx_char/*.c`(r5 신규).

## 3. 진입점과 호출 흐름 — 본문으로 옮김

| 내용 | 본문 |
|---|---|
| 모자 슬롯 15/49, ManualBindSRT 결합식 | [player_assembly.md §6.1](player_assembly.md) "모자 행렬식" |
| 무기 슬롯 15/49/70, 모델 루트 행렬 설정 0x7100f735b0 | [player_assembly.md §6.1](player_assembly.md) "무기" |
| 클립 이름 해석기 0x710244d0b0 | [anim_state_machine.md §3.1](anim_state_machine.md) |
| 선택 노드 BoolSelector/IntSelector | [anim_state_machine.md §2.5](anim_state_machine.md) |
| 눈 색·피부 색 0x710145249c/0x71014522b0 | [player_assembly.md §5.2](player_assembly.md) |
| 몸 표시 스프링 0x71014586a0 | [player_assembly.md §5.4](player_assembly.md) |

## 4. 구조체·필드·상수 — 본문으로 옮김

모자 +0x350/+0x352/+0x380/+0x3f0, 무기 +0x3b8, 홀더 +0xa0~+0xac, 모델 +0x268~+0x270·+0x28c~+0x2b8, 해석기 +0x10/+0x18/+0x20 은 위 본문 절에 writer·reader 와 함께 있다.

## 5. 상태 전이와 수명 — 본문으로 옮김

스프링 상태 전이(트리거·죽음 리셋·평형 분기)는 [player_assembly.md §5.4](player_assembly.md)에 있다.

## 6. 계산식과 상세 의사코드 — 본문으로 옮김

모자 행렬식(FMLA 융합 포함)은 [player_assembly.md §6.1](player_assembly.md)로 옮겼다. 이전 판의 이 절 내용은 그곳에 그대로 있고, Head 바인드 × P = I 데이터 확인을 덧붙였다.

## 7. 애니메이션·에셋 연결 — 본문으로 옮김

클립 이름 대체 규칙과 `WalkBackHold_Shtr` 사례는 [anim_state_machine.md §3.1](anim_state_machine.md), `M_Eye_Alb.21` 이 닿지 않는 이유는 [player_assembly.md §5.2](player_assembly.md)에 있다.

## 8. 다른 기능과의 상호작용·정정 기록

- **2026-10-03 정정(이전 회차):** 26e613c 를 HairArrange 적용 함수 후보로 두었던 기록은 틀렸다. 이 함수는 ManualBindSRT 결합이다. 26e5ccc 는 HairArrange 맵 해제다. 실제 HairArrange 소비자는 아직 찾지 못했다.
- **2026-10-03 정정(이전 회차):** GearAlphaMask 후보 2b8c668/2b8c800 은 소멸·해제 함수다. 재질 샘플러 연결 증거가 아니다.
- **2026-10-03 r5:** 무기 초기화로 기록된 0x71028754d0/0x710288030c 는 각각 `spl::WeaponBrush`/`spl::WeaponManeuver` 의 슬롯 15 다. 슈터는 `spl::WeaponShooter` 슬롯 15 0x710289bd80 이다(본문 §6.1).
- **2026-10-03 r5:** 웹 모자 결합 `translate` 는 원본과 다르다(본문 §6.3 정정).
- **2026-10-03 r6 정정:** HairArrange 맵 키는 `머리카락 id × 10000 + 변형`(r5 의 "id + 변형×10000" 정정). 소비자는 모델 홀더 영역 0x7101454544 였다(player_assembly §6.1). anim §4.4/§4.5 의 다음 주소 0x71039bcb9c·0x71039cd350 은 각각 부착 수집·가중 전파 함수였다(동기화·포즈 합성 아님).
- MainLight Color/Intens/Lat/Lon 경로는 기존 stage_rendering §4 의 직접 기록으로 이미 [판독]이다. 로비 값은 Color (0.6706, 0.851, 1), Intens 10, Lat 34.5, Lon −3 이다. 하늘 SH 수신값은 별도 [미확정]이다(그래픽 스테이지 담당 문서).

## 9. 웹 포팅 구조와 구현 순서

웹 반영 목록은 본문 각 절과 `analysis/completion/r5/gfx_char.json` 의 `web` 칸에 있다. 요약하면 다음과 같다.
- 모자: `Head 월드 · P · ManualBindSRT`. FMLA 비트 동등이 목표면 Math.fround 곱·덧셈 분리로는 부족하다.
- 무기: 지금 `full` 방식 유지(원본과 같음).
- 스프링: 트리거를 "몸만 보임 0→1 && 직전 프레임에 무엇이든 보임"으로 고친다.
- 클립 대체: 후보 순서를 원본대로 하고, 모두 없으면 그 잎은 엔트리를 만들지 않는다.
- 눈 색: 번호 0..20 만 반영한다.

## 10. 검증 코드·명령·결과

| 대상 | 명령 | 결과 | 스텁·실행하지 않은 범위 |
|---|---|---|---|
| 모자 슬롯 49 0x71026e613c | `PY web/tools/completion_head_matrix_emu.py` | 259/259 비트 일치, 몸 포인터 없음 1/1. 곱·덧셈 분리 f32 는 254/259 건 다름 | 소유 모델 vt+0x1f8 ret, Head 뼈 get vt+0x78 합성 공급, pack/rope 인덱스 −1, 모델 콜백 null·객체 수 0, 인덱스 쌍 0. 실제 뼈 producer·프레임 스케줄·HairArrange·천 솔버 미실행 |
| 클립 이름 해석 0x710244d0b0 (+0x710351c964, 0x710244dfc4 원본) | `PY web/tools/r5_gfx_char_clipname_emu.py` | 2210/2210(조회 순서·종류 인자·반환 이름) | 바인더 조회 vt+0x18 만 스텁(이름 기록 + 집합 판정). PLT memcpy/memmove/memcmp/strlen 파이썬. 실제 바인더 사전 조회·잎 진입·키 목록 출처 미실행 |
| 무기 부착 0x710289beb8 + 0x7100f735b0 | `PY web/tools/r5_gfx_char_attach_emu.py` | 403/403 비트 일치(회전 9·평행이동 3·스케일 3, 뼈 get 인자), 몸 없음 1/1 | 뼈 get vt+0x78 합성 공급, 무기 모델 vt+0x1f8 ret, 0x7100f72b7c 즉시 복귀, 컴포넌트 vt+0xc8 → 유닛. 실제 뼈 producer·호출 시점 미실행 |
| 몸 표시 스프링 0x71014586a0 | 같은 명령 "spring" | 14400/14400(60열 × 240프레임, 발동 93회) | 외부 호출 없음. 표시 플래그 producer 0x71014595b0·프레임 순서 미실행 |
| 눈 색 0x710145249c + 0x71036751a4 | `PY web/tools/r5_gfx_char_eye_emu.py` | 88/88 | 0x7101262c18·0x7103673874·0x7103674288·0x7103673fd0 즉시 복귀(호출 여부만 기록). 첫 진입 초기화(이름 조회) 미실행 |
| BoolSelector 0x71039c46c8 / IntSelector 0x71039cda20 (+0x71039982bc 원본) | `PY web/tools/r5_gfx_char_boolsel_emu.py` | 10/10 + 120/120 | 블랙보드 경로 문맥 vt+0x130/+0x148 스텁. 실수 파라미터 경로·IntSelector 블랙보드 경로·재평가 캐시 미실행 |
| 머리카락 천 상수 46팩 | `PY web/tools/r5_gfx_char_bphcl_batch.py` | 23개 bphcl 요약 [데이터] | 실행이 아니라 데이터 해독(gfx4p_bphcl.py) |
| 팀색 선택기 번호 0x7101179a24 + 해시 0x7101179f90 + 선택기 0 0x7101179fd0 (r6) | `PY web/tools/r6_gfx_char_teamcolor_emu.py` | 1152/1152, 5/5, 132/132 | 게임 객체·0x71058e87dc 합성 값, 선택기 0 의 0x710140946c·0x7101179c80 스텁. 0x71011795b0 플래그 조회·무작위 행 순회 미실행 |
| HairArrange 적용 0x71026df700 (+0x71026e12e4·0x71026e3a28·0x71038b6944·0x71026e0f9c 원본) (r6) | `PY web/tools/r6_gfx_char_hairarrange_emu.py` | 60/60 f32 비트 일치 | 뼈 vt+0x40/+0x68/+0x50/+0xa0 파이썬, PLT sinf/cosf 파이썬 math(f32 반올림). 애니 가중·부모 상속 사슬 미실행 |

재구현끼리 비교한 항목은 없다. 모든 [실행] 항목은 unicorn 에서 돈 원본 출력과 판독식을 비교했다.

## 11. 미확정과 다음 근거

| 항목 | 시도와 남은 이유 | 다음에 볼 곳 |
|---|---|---|
| ~~Head 뼈 API 의 표준 Mat34 대응~~ | 해소(2026-10-03 r5): 같은 뼈 get 결과를 무기 슬롯 49 가 그대로 모델 루트(행 우선 3×4, 평행이동 [3],[7],[11])로 쓴다 [판독], 무기 부착 403/403 [실행]. 바인드에서 Head·P = I [데이터]. 뼈 get producer 자체는 여전히 스텁 | 몸 스켈레톤 vt+0x78 구현 |
| HairArrange Rotation/Scale/Transform/AnimReduceRt 적용 | 맵 구조 판독, +0x360~+0x37c 읽기·10000 상수 전수 검색으로 소비자를 못 찾음(본문 §6.1 r5 항목) | sead 트리 find 호출자, HairArrangeParam 리소스 +0x158 reader, 머리카락 +0x390 writer |
| ~~HairArrange 적용~~ | 해소(r6): 0x7101454544 → 0x71026df354 → 0x71026df700, [실행] 60/60 | 남은 것: 애니 가중 경로 실행 검증 |
| GearAlphaMask 재질 슬롯 | 컨테이너 → 전역 관리자 대기 목록 → 프레임 콜백 0x71010413f8 → 0x710103f434 경로까지 판독 | 0x710103f434, 컨테이너 +0x2b8 이름 해시 조회 호출자, 0x71011805b4/0x71011807c8 의 플레이어 쪽 호출자 |
| ↳ r6 | 슬롯 = `M_Body` 재질 샘플러 `_o0`(셰이더 `_op0`) 해소 [판독]+[데이터]. 마스크 합성 연산 [미확정] | 아카이브 *0x71058161a0 의 `FILTER_TYPE 4` 프로그램 역번역 |
| ~~LOD 거리 소비~~ | 2026-10-03 r8 해소 [판독]+[실행]: nativeBfresModel5727180→3689a28/3777354→3777f28/377e3a8→3788760;8192+2048 전체바이트 일치 | [lod_runtime.md §3~§11](lod_runtime.md); 남은 live입력 생산/GPU는별도 |
| ↳ r6 | `r6_gfx_char_lodscan.py` 전 범위(×0x50 madd·lsl#4 첨자 + s 적재) 17후보 모두 다른 배열, `ldr #0x228`+`ldr #0x38` 동시 출현은 너무 많음 → [미확정] | 모델 클래스 vtable(슬롯 0x228 = 레코드 수)을 찾아 그 슬롯 함수들의 +0x38 접근, 사후 증가 ldp 패턴 |
| 기본 장비 결정 지점 | v0 데이터에 초기 장비 표시 없음, 세이브 기록 함수는 기본값을 정하지 않음 | 세이브 구조 생성자, `PlayerMake` 씬 |
| ↳ r6 | 세이브 커스텀 구획 초기값(vtable 0x7105665240 슬롯 2 0x7102a66e28, 키 = murmur3) 판독: 기어·무기 −1 | −1 해석 지점(플레이어 정보 +0x844 채우는 함수), `PlayerMake` |
| 엔트리 없는 애니 잎의 포즈 기여 | 잎은 엔트리를 만들지 않고 "끝남" 비트만 세움 | 포즈 합성 0x71039cd350, 0x71039be4a0 |
| ↳ r6 | 0x71039cd350 = 가중 전파·진행률 보고(포즈 합성 아님) [판독] | 포즈 샘플러 정규화(AS 슬롯 → 모델 애니 적용 경로) |
| 하늘 SH·톤매핑 | 범위 밖(스테이지 담당) | stage_rendering §11 |

이 항목들은 **[미확정]**이다. 원본에 없다고 확인한 항목이 아니며, 조사 시간을 근거로 확정 불가 처리하지 않는다.
