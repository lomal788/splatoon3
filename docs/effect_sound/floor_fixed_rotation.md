# 속도0 착탄 고정 회전 — Splatoon 3 v0, 2026-10-03 r8

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 바닥 착탄의 속도0 경로에서 사용하는 `0x71058237b0`은 **원본 정적 초기화가 만드는 3×3 단위행렬**이다. 해당 경로는 회전9성분을 이 값에서 읽고, 요청 위치를 붙여 코드 emitter에 전달한다. 고정 r7 `impl/fx.md:L123`의 '단위 회전은 웹 근사이며 원본 BSS 초기화 미확정' 질문을 신규 원본 init→소비 실행으로 해소한다.

## 2. 분석 대상 원본·버전·자료 위치

원본 `extracted/exefs/main.reloc.img`/raw MOD0 dynamic metadata와 `sdk.img`. 신규 `analysis/decomp/r8_combat/fx_identity_init.c`의 `124F5F0`/`12541C0`, 기존 `network/net_player.c`의 `27B877C`를 연결한다. `analysis/completion/r8/fx_identity_emu.json`, `web/tools/r8_fx_identity_emu.py`가 재현 근거다. 원본/웹 코드/impl 변경0.

## 3. 진입점과 전체 호출 흐름

[데이터]+[판독]+[실행] 실제 dynamic DT_INIT_ARRAY는 `0x71057AB0D8`, 크기64456B(8057개). index2692의 포인터 슬롯 **0x71057B04F8 =0x710124F5F0**다. 이 함수의 `124F6C0..6D4`가 회전을 초기화한다. 같은 init 배열 index2700의 `12541C0`은 이 회전을 읽어 다른 기본 객체에 복사한다. 전체 부팅 실행 대신 실제 원본 등록/순서 데이터와 해당 함수 전체를 확인했다.

실제 소비: `27B877C`의 E2=Splash, 방향Y>58CC928, 속도 길이<=0 경로 →58237B0..37D0 읽기→3×4 회전+위치→`137F558` 코드 emitter. 일반 명중 연결은 [hit_effect_pipeline.md](../combat/hit_effect_pipeline.md).

## 4. 구조체·필드·상수·열거형 표

| 원본 주소 | f32 값 | writer → reader |
|---|---|---|
| 58237B0/B4/B8 | 1 / 0 / 0 |124F6CC→27B877C |
| 58237BC/C0/C4 | 0 / 1 / 0 |124F6CC/6D4→27B877C |
| 58237C8/CC/D0 | 0 / 0 / 1 |124F6D4/6D0→27B877C |

위 표의 주소에는 공통 접두사 `0x710`을 붙인다. 인덱스0/4/8은u32=3F800000, 나머지는u32=00000000. 9f32/36B이며 quaternion/3×4 translation 자료가 아니다. 3×4 출력의 위치는 request+00/04/08에서 별도로 복사한다.

## 5. 상태 전이와 전체 수명

[판독] `.init_array` 호출에서 기본값을 만들며, 이번 원본 xref에서 그 초기 저장과 읽기 복사를 확인했다. `27B877C`는 중간 sqrt 실패 분기에서 읽은 값을 같은 globals에 다시 쓰는 명령이 있으므로 '쓰기 참조가 있다는 이유로 동적인 회전'이라고 해석하지 않는다. 모든 프로그램 writer 부재나 전체 세션의 불변성까지 증명했다고 확대하지 않는다. 고정 질문은 초기값이며 그 값이 소비되는 경로를 확인했다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행]

```text
init124F5F0:
  M[0..8] = [1,0,0, 0,1,0, 0,0,1]
velocity_zero_floor:
  out = [M0,M3,M6,px, M1,M4,M7,py, M2,M5,M8,pz]
  emit(out)
```

실제 init은w9=3F800000, `stp x9,xzr,[M]`, `str w9,[M+20]`, `stp x9,xzr,[M+10]`의64/32bit 저장이다. x9의 상위32bit는0이므로 +4/+14도0이다. '같은 값일 것이다'가 아니라 임의 old36B를 실제 명령이 모두 덮는 것을 확인했다. 소비행렬은 row3×4에서 translation3/7/11에 요청 위치를 넣는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[판독] 바닥 Splash 코드 emitter가 사용하는 기본 회전이다. paintable이 슬롯 선택에 들어가도 속도0 회전은 동일하며 translation만 다르다. 양의 속도 벽/바닥 회전·방향 분기·VAT/GPU·소리 리소스는 이 단일 질문에 포함하지 않는다. 자이로 더미 등 다른58237B0 사용처도 이번 신규 확정수로 재계상하지 않는다.

## 8. 다른 기능과의 상호작용

원본 앞단 HitEffectConfig E2=Splash와 컬링/팀 게이트를 그대로 거친다. 요청방향을 무조건 물리 면법선이라고 부르지 않는다. 이번 fixture는 방향(0,1,0), 속도(0,0,0), 정상local0/team0이며 실제 원본 queue/controller를 실행했다. 사격장의 모든 입력이 이 분기를 탄다는 주장은 아니다.

## 9. 웹 포팅 구조와 구현 순서

`impl/fx.md` 반영 필요: 기존 속도0 단위 회전 값을 **원본 확정값**으로 사용할 수 있다. 3×3→3×4 행/열 대응과 요청 위치를 그대로 유지한다. 코드와 impl 문서는 수정하지 않았다. 양의 속도 회전을 이 단위행렬로 치환하지 않는다.

## 10. 검증 코드·실행 결과·기대값

명령 `.venv/Scripts/python.exe web/tools/r8_fx_identity_emu.py`:

- init128건: old9u32를 무작위/NaNpayload로 채운 뒤 **124F5F0 함수 전체** 실행, 9개 원본f32 bits가 단위행렬과 일치.
- 원본 init 뒤 실제27B4704→27B877C 속도0 소비1024건: paint0/1×위치512, 12f32 독립 기대식 모두비트일치.
- 총13440f32 fields, mismatch0/null read0/mainSDK patch0.
- init의 외부 호출 `_ZN2nn3err18ErrorResultVariantC1Ev`(sdk+183AD0,8B), `_ZN2nn3ldn15MakeIpv4AddressEhhhh`(sdk+2FADE0,32B)는 **실제 SDK 함수**로128/384회 실행했다. 이 주소는 심볼표에서 조회했고 CPU코드 그대로 실행,0반환 스텁으로 초기화를 흉내 내지 않았다.

SDK mutex/guard/allocator와 ActorManager virtual2개 등 consumer fixture는 [hit_effect_pipeline§10](../combat/hit_effect_pipeline.md)의 경계다. XLink lookup/emission 및137F558 backend는 캡처한다. 해당 검증에서 태그 범위 밖 renderer·live 세션·최종음원은 실행하지 않았다. floor 종류 selector의 임계 global은 소비fixture 상태이며 **출력slot값을 사격장 기본kind로 새확정하지 않는다**. 검증 대상은 고정 회전9개와 위치3개의 bit값이다.

실제 시도: SHARED/FUNCS/impl행 대조→decomp_index 주소 미기록→xref initial호출 `xref.py 58237b0` syntaxfail1→`xref.py addr 0x71058237b0` 정상→124F6C4의store찾기→func_lookup124F5F0 size240/12541C0 size272→full_decomp신규2함수→rawMOD0 DT_INIT_ARRAY 확인→원본 실행PASS. 12541C0을 같은global writer로 혼동하지 않고 copyreader로 판독했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

고정 r7 impl/fxL123 초기값 질문은 해소했다. 전체 bootstrap의 성공/8057개 init 전체실행, 나머지global rotation writer 유무전수, 실제GPU emitter 출력은 별도 미검증이다. 다음whole질문과 혼합하지 않는다. 다른 함수의 널/합성 입력을 원본 BSS값으로 쓰지 않으며, 기존5880 소비 검증의 초기화 전 회전0 fixture도 실제 default의 근거로 사용하지 않는다.
