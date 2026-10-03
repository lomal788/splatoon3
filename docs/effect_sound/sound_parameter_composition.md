# 효과음 피치·파라미터 합성 — r8 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] SLink Pitch/Pitch2로 정한 음높이는 그룹과 동적·공간 파라미터의 **곱**으로 합성된다. 중간 Pitch를 더하거나 semitone 값으로 변환하지 않는다. 최종 비양수는 0이다. 파형·SDK 출력 재생은 이 분석에서 실행하지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`. 신규 `analysis/decomp/r8_fx/pitch.c`, `param_multiply.c`, `group_param.c`; 기존 `analysis/decomp/r5_fx/alto_listener.c`의 `383df38`을 재사용했다. 도구 `web/tools/r8_sound_pitch_emu.py`; 결과 `analysis/completion/r8/sound_pitch_emu.json`.

## 3. 진입점과 전체 호출 흐름

[판독] 기존 SLink `3887e3c`는 voice+0x3C=Pitch×Pitch2를 쓴다. 그룹 갱신 `383836c`는 `37ded4c(out=group+118, group+98, group+D8)` 후 상위 그룹이 있으면 `37debc0(out,parent+118)`을 호출한다. 보이스 `383df38`는 `37ded4c(out=voice+138, voice+38, voice+78)` → dynamic(voice+D8이 가리키는 객체)+10 → group(voice+D0)+118 순서로 `37debc0`을 적용한다. 최종 `SetVoicePitch` 명령 `37fe730`(+8 float 그대로 SDK에 전달)은 기존 r6 판독 근거를 잇는다.

## 4. 구조체·필드·상수·열거형 표

| 기준 | 오프셋 | 의미·생산/소비 |
|---|---|---|
| 합성 parameter block A | +0 | volume, 곱 |
| A | +4 | Pitch, 곱; voice+3C/7C→13C |
| A | +8 | 의미 미확정 f32 가산(voice+0x140); filter kind +0xC/+0x10와 구분 |
| A | +C/+10 | s32 선택값: 뒤 입력이 음수면 앞 값 유지 |
| A | +14/+18/+20 | f32 가산 |
| A | +1C | s32 가산 |
| A | +24 | f32 곱 |
| A | +28 | 선택적인 채널 파라미터 포인터(이 실행에서는 null) |
| voice V | +144/+148 | 합성한 filter kind0/1. 음수면 `383df38`가 1/3으로 대체 |

위 이름 가운데 일반 block의 피치(+4) 외 미정 의미는 더 구체적인 이름으로 승격하지 않는다. +8의 용도는 caller에서 voice+140인 구조 배치와 구분하며, 실제 Lpf amount는 voice+14C이다.

## 5. 상태 전이와 전체 수명

[판독] group+79/+7A dirty 또는 상위 그룹+7B dirty가 있을 때 그룹 합성을 수행하고 +7B=1을 쓴다. +79/+7A는 뒤에 0으로 지운다. voice 합성은 현재 입력 블록에서 출력+138을 새로 계산하고 외부 요소를 차례로 적용한다. 이전 최종 Pitch에 계속 누적하는 식이 아니다.

## 6. 계산식·조건·상세 의사코드

```text
groupPitch = f32(f32(localPitch * automatedPitch) * parentPitch) // parent 없으면 마지막 곱 없음
voicePitch = f32(localPitch * spatialPitch)
if dynamic: voicePitch = f32(dynamicPitch * voicePitch)
if group: voicePitch = f32(groupPitch * voicePitch)
if voicePitch <= 0: voicePitch = +0.0f
```

[판독]+[실행] MUL마다 f32이며 이 피치 경로에 FMA는 없다. 음수·0·음수 0과 0.25/0.7/1/1.25/2 조합을 대조했다. NaN은 `<=0` 비교에 실패하므로 값이 그대로 남는 분기다 [판독; NaN bit payload 실행 비교는 하지 않음]. 필터 선택값은 `37ded4c`에서 **뒤 입력이 nonnegative이면 뒤 입력**, 아니면 앞 입력이다. in-place `37debc0`는 **현재 값이 negative일 때만 추가 입력으로 채운다**. 즉 dynamic/group이 이미 설정된 필터 종류를 무조건 덮어쓰지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

스플래시슈터 발사음 Pitch random(0.7..1.25) 평가 값과 Pitch2의 기존 경로는 `sound_resources.md` §4.2.7/§5를 따른다. 이 문서는 그 뒤 중간 합성이 곱인 점을 새로 확정했다. SDK `SetVoicePitch`에 넘길 재생 비율의 근거로 연결하며, 난수 호출 전체 프레임 순서는 별도 미확정이다.

## 8. 다른 기능과의 상호작용

[판독]+[실행] 합성 중 filter kind 값이 끝까지 음수면 ch0=1/ch1=3을 적용한다. 숫자 기본값을 실제 필터 객체의 종류·주파수 응답과 같다고 확대하지 않는다. 슬롯1/3 등록 객체, SLink override writer, voice+180 공간 객체는 남은 질문이다. 채널 배열 합성의 negative sentinel 규칙은 두 신규 함수에 있으나 이 피치 실행에서는 배열을 사용하지 않았다.

## 9. 웹 포팅 구조와 구현 순서

`impl/fx.md`의 playbackRate에 SLink Pitch×Pitch2뿐 아니라 위 그룹·동적 합성을 필요한 순서로 연결할 근거다. 권장 이름 localPitch/spatialPitch/automatedPitch는 웹 설명용이다. 원본과 같은 f32 MUL 순서와 비양수 0 처리가 필요하다. 웹 소스·impl은 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

```powershell
& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/r8_fx/pitch.c 0x71037ded4c
& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/r8_fx/group_param.c 0x710383836c
& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/r8_fx/param_multiply.c 0x71037debc0
.venv/Scripts/python.exe web/tools/r8_sound_pitch_emu.py
```

[실행] **32,768건 원본 group→voice 연결 실행, 스텁 없음, f32 비트 불일치0**. 합성 구조체·채널 배열 null, 유한 피치 값 8종의 5개 인자 조합. 실제SDK음성재생·도플러·시간스텝은 실행하지 않았다. 28,368건이 최종비양수라0이 됐고, 필터종류fallback1/3도 매 입력에서확인했다. 첫 하네스 `UC.read_u32` API 없음으로 실패→기존메모리읽기+struct.unpack으로수정한뒤통과.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·다음에 볼 곳 |
|---|---|
| 음파·도플러 포함 최종 피치 | `3864908` 및 보이스 명령 enqueue의 추가 변경; 합성 중간 질문과 별도 |
| 슬롯1/3 실제 필터 응답 | `37d7aa0` 관리자 초기화·필터 등록·SLink parameter override writers |
| Delay 단위 | 원본 leaf countdown의 dt 및 parameter accessor 연결 필요 |
| 배열형 부가 파라미터 | `37ded4c/37debc0` +28 배열 전체를 추가 실행할 수 있으나 피치 scalar 질문을 분할하지 않음 |
