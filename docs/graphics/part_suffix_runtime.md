# 캐릭터 부품 `_F`/`_M` 선택 — 원본 이름 생성

## 1. 개요

사람 커스터마이즈·기어의 actor/model 이름은 부품 종류, RSDB 행, PlayerModelType으로 만든다 [판독]+[실행]. 접미사는 이름의 외형에 대한 추정이 아니라 원본 조건이다.

## 2. 원본·자료

v0 main, 새 `analysis/decomp/r8_graphics/char_suffix_binder.c` 26fd010/26fd810, `char_names.c` 1450cc4, `char_type_params.c` 144f9a0. 기존 `analysis/decomp/r6_gfx_char/squid_bones.c` 24397bc와 `analysis/decomp/camera/camui_batch3.c` 24719d4를 재사용했다.

## 3. 호출 흐름 [판독]

PlayerModel 컴포넌트 초기화 24397bc의 243a1fc/243a204는 컴포넌트+7A0 타입을 초기화 descriptor+ C에 둔다. 144f9a0은 descriptor+C→부품 홀더+34로 복사한다. 24719d4의 2471e0c→1450cc4 및 같은 초기화의 직접 경로는 홀더+34를 26fd010의 w3로 넘긴다. 여기의 컴포넌트+7A0은 본체 B+7A0 byte 숨김 플래그와 다른 객체·필드다.

## 4. 입력·필드 [판독]

26fd010(x0=출력 BufferedSafeString,w1=부품종류,w2=행 ID,w3=모델타입,w4=variation,w5=별도이름플래그). 출력 객체+8은 char buffer,+10은 용량이다. 부품 종류 0=머리,17=눈썹,8=하의,4/5/6=머리기어/옷/신발이다. RSDB 행+0 이름, 기어 행+7A IsUnisex다. 이름 등록 파서13b7ab4의 IsUnisex 문자열주소4931f59→행+7A를 확인했다.

## 5. 수명·실패

조회가 실패하면 출력 이름을 비우고 false를 반환한다 [판독]. 성공 시 이름을 복사·접미사를 붙여 true다. 복사/추가는 출력 용량−1까지만 쓰고 NUL을 유지한다. 기어 variation은 0 이상이며 행+74 최대 이하인 값만 받는다. 이 문서의 실행은 variation0 성공 경로다.

## 6. 원본 조건 [실행]+[판독]

```text
maleSuffix = (modelType | 2) == 3
suffix = maleSuffix ? "_M" : "_F"
Hair/Eyebrow/Bottom = rowName + suffix
Head/Clothes/Shoes = rowName + (IsUnisex ? "" : suffix)
```

따라서 모델 타입 0(SquidF)/2(OctopusF)/4(Rival)는 F, 1(SquidM)/3(OctopusM)는 M이다. Rival을 별도 성별 분기로 해석하지 않는다. 기어 variation>0이고 결과가 `Hed_`로 시작하지 않으면 `.%d`를 뒤에 더한다 [판독].

## 7. 에셋 연결

1450cc4는 커스텀 정보+290/+498/+6A0에서 기어 ID, +838/+84C/+83C에서 머리/눈썹/하의 ID를 읽어 같은 함수로 이름을 만든 뒤1450578로 부품 요청을 붙인다. 원본 RSDB 실제 행·파일 목록은 [player_assembly.md](player_assembly.md) §2·§4의 기존 데이터다.

## 8. 상호작용

홀더 모델 타입은 몸·오징어 모델 타입과 동일 입력을 공유한다. IsUnisex는 성별 접미사를 붙이는 단계만 생략한다. 캐릭터 뼈 바인딩과 헤어 물리는 이 이름 선택 뒤 단계다.

## 9. 웹 포팅

권장 `PartNameResolver`에서 타입값 1/3에만 M을 붙이고, 기어에서 IsUnisex를 적용한다. 이름 규칙만 보고 Rival/예외를 별도 추측하지 않는다. ID→행 조회, 용량 절단, variation 접미사 순서를 원본대로 둔다. 구현 코드는 변경하지 않았다.

## 10. 실행 검증

`web/tools/r8_gfx_frame_suffix_emu.py`: 26fd010 전체 **240/240** 출력문자열·true 반환 일치. 타입5×부품6×IsUnisex2×출력용량4(2/9/32/64)다. 스텁은 RSDB 조회 13c380c/13b6b40/139c940/13bb5a8의 합성 행 반환과 memcpy PLT3e99f20이다. 이름 선택·절단은 원본 실행이다. 원본 RSDB 파싱, 실패, variation>0, actor 리소스 로딩까지 실행한 것은 아니다.

## 11. 정정·미확정

2026-10-03 r8: '_F/_M 코드 미발견' 추정을 26fd010 실제 조건과 caller/writer 연결로 정정했다. 실행 최초 문법 오타, 이후 합성 관리자 포인터를 +1C로 놓은 오프셋 오류로 UC_ERR_READ_UNMAPPED 실패; +18로 수정 후 240/240이다. 전체 부품 스켈레탈 합성·Cloth·LOD 최종 화면은 [미확정]이고 이 이름 규칙만으로 완료로 올리지 않는다.
