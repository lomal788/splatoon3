# 효과음 전역 거리 단위와 시간스텝 — r8 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행: 초기화 블록·getter] Alto 거리 정규화의 전역 단위는 **1.0f(0x3F800000)**로 초기화한다. 프레임수 60과 시간스텝 1/60을 거리 단위로 사용하지 않는다. SLink DistCoef 역수·리스너 지향성 배율과 결합하면 실제 거리 감쇠 식의 분모를 확정할 수 있다. 1.0을 미터나 센티미터로 명명하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`. 신규 `analysis/decomp/r8_fx/audio_initialize.c`, `audio_entry.c`, `audio_tick.c`, `audio_unit_getter.c`, `audio_parameters.c`; 기존 `vfx/snd_xlink_b1.c`의 `383f9d4`, `r5_fx/alto_listener.c`의 `383f418`은 재사용. 실제 `extracted/romfs/Sound/Product.100.alto__AltoConfig.bgyml`도 확인했다.

## 3. 진입점과 전체 호출 흐름

[판독] `3e06d8c`는 AltoConfig를 선택·읽고 **3915e44 → 37e0de8(System 생성) → 383f9d4**를 잇는다. System 전역은 `599a3f8`, GOT 주소는 `57914B8`이다. `383f9d4`가 0x1A0바이트 parameter 객체 P를 만들어 System+10에 넣는다. 그 내부 **38402E4..3840368**이 P+20=1.0f를 직접 쓴다. 이어 `383f418`은 P+8의 출력 장치/패닝 객체를 만들고 P+3C/+40/+44 장치 볼륨 등을 설정하며 P+20을 변경하지 않는다.

`37e11d8`은 System+10을 반환하고 **38551f4**는 그 객체+20을 float로 읽는다. 기존 거리 감쇠 `3863fe8` 및 게임 재정의 `3129c98`은 같은 P+20으로 나눈다.

## 4. 구조체·필드·상수·열거형 표

| 기준 | 필드 | 초기값·소비 |
|---|---|---|
| System | +10 | P 포인터, 3840368에서 설정 |
| P | +14 | 초기 60.0f, 3e071d4에서 60.0f로 명시 재설정 |
| P | +18 | 초기 1.0f; 프레임 갱신 시 양수 전역 입력으로 변경 |
| P | +1C | 초기 0x3C888889=f32(1/60); 프레임 갱신 시 입력/P+14 |
| P | **+20** | **거리 단위 1.0f**, 38402F4의 STP 두 번째 64비트 값 하위32비트 |
| P | +24 | 초기 1.0f, 이 문서에서 의미 미확정 |
| P | +28/+2C | 초기 340.0f/0x40B55555; 게임 초기화에서 +2C=(+28×+20)/60 |

## 5. 상태 전이와 전체 수명

[판독] 37e0de8은 System+10=0으로 생성한다. 383f9d4가 P를 설치하며 P+20을 1로 쓴다. 제품 AltoConfig BYML에는 `$parent=Work/Sound/altoConfig.alto__AltoConfig.gyml`만 있다 [데이터]. 이 설정의 게임 적용 3915e44 및 3e06d8c는 초기화 후 장치 볼륨·시간 관련 필드를 갱신하고 거리 단위+20을 덮어쓰지 않는다.

## 6. 계산식·조건·상세 의사코드

```text
// 3e06d8c 초기화 뒤
P14 = 60.0f
P2C = f32(f32(P28 * P20) / 60.0f)
P1C = f32(P18 / 60.0f)
// 3e07450 → 3e0746c, phase 0
s = *( *59a7430 + 8 )
if System && P && s > 0:
    P18 = s
    P1C = f32(s / P14)
// P20은 위 두 블록에서 변경하지 않는다.
```

[판독] 거리 결합은 기존 r6 §4.2.7의 식을 잇는다.

```text
d = f32(distance / 1.0f) * directivityRate * reciprocalDistCoef
if extensionFlag1: d *= FriendDistCoef(1.5f)
```

곱셈 순서는 원본 3129c98의 기존 판독을 따른다. `extensionFlag1`의 수치 조건은 UseFriendCoef && 로컬속성값==1로 기존 실행 확정됐지만 그 캐시 속성 이름은 여전히 미확정이다. 이름을 Friend라고 새로 확정하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[판독] 단위+20은 거리 감쇠뿐 아니라 리스너 지향성 반경과 SoundSourceSize에도 쓰인다(기존 sound_resources §4.1.3/4.2.7). 값1이면 이 반경·크기는 같은 원본 월드 좌표 크기를 유지한다. 카메라→실제 리스너 위치 공급자는 별도 미확정이다.

## 8. 다른 기능과의 상호작용

전역 입력+8의 양수 조건은 시간스텝만 바꾼다. 0·음수·NaN일 때 P18/P1C을 그대로 둔다 [실행]. 이를 거리 단위 변경이나 음높이 도플러 전체 규칙으로 확대하지 않는다. 장치 출력·SDK 파형은 실행하지 않았다.

## 9. 웹 포팅 구조와 구현 순서

`impl/fx.md`: 감쇠에 distance/1.0 × 리스너 지향성 × 1/DistCoef를 해당 순서로 연결할 근거다. 원본 시간스텝을 거리 분모에 넣으면 안 된다. +B8 속성 의미·실제 리스너 위치·음향 필터 선택은 확정 전 보류. 웹 소스·impl은 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

```powershell
.venv/Scripts/python.exe web/tools/r8_sound_unit_emu.py
.venv/Scripts/python.exe analysis/completion/r8/scan_sound_unit.py
```

[실행] **초기화 블록→System getter→unit getter→60Hz 설정 256건**, **프레임 쓰기 블록 40건**, 비트 불일치0·스텁 없음. 이미 할당된 합성 P/System을 공급하고 원본 블록은 초기화38402E4..3840370, 초기설정3E071B4..3E071F8, 갱신3E0749C..3E074DC에서 멈춘다. 두 getter는 전체 함수 실행이다. 실제 전체 부팅·네이티브 오디오 출력 실행과 구별한다. 결과 `analysis/completion/r8/sound_unit_emu.json`.

GOT 참조 국소 레지스터 추적은 +20 쓰기를 더 찾기 위한 후보 검색이며 포인터 탈출·모든 제어흐름의 부재 증명으로 쓰지 않는다. 반환 getter의 BL 주소3854434/38559EC는 functions 목록 공백에 있어 최근접 시작38542FC/3855548의 본문에 포함되지 않는다. 실제 raw명령에서 getter→38551F4 연결을 확인했다. 3E07450도 함수 목록 공백이라 새 함수로 디컴파일했다.

초기 실패 기록: byml 모듈 import 없음 → 기존 spl_data 사용; `spl_data.decompress` 없음 → `unzs/byml` 사용. `disasm.py <주소> 28` 실패 → `-n 28` 사용. 첫 스캔 편집 PowerShell 인용 파싱 실패 → here-string 사용. 파일 검색 PowerShell glob 경로 실패는 `rg <디렉터리> -g`로 정정했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·다음에 볼 곳 |
|---|---|
| User+B8 속성 이름 | 원본313d4ec는 유효비트·인덱스로 값0/1만 분기; 캐시 바인더/사용자 초기화 추적 필요 |
| 리스너 target 실제 공급자 | 390cfc4 vt+38 호출자→카메라 pose/target 포인터 연결 필요 |
| 네이티브 전체 초기화·출력 | allocator/device/hardware 제외, 원본블록 판독·실행 범위를 명시 |
| P24 및 P28 물리 단위 이름 | 실제 필드 수치·식만 확정, meters/s 명명 근거 미확정 |
