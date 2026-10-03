# 원본 사운드 필터 표·그룹 정지 경로 (r9, 2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[데이터]+[실행] 원본 기본 필터는 임의 컷오프 보간이 아니라 정수 Q14 계수표 선택이다. 게임의 오클루전·감도 필터는 이 기본 종류를 덮어쓴다. 아래는 새 원본 등록/콜백·소비 판독의 명세이며 최종 모든 음원 선택을 확정했다고 확대하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon3 v0 `extracted/exefs/main.reloc.img`, SHA256 `39a8c94826d84b6106f112f2db16f7b2e2743bc6afd72054534a7708a9848a41`. 이전 피치·거리·계수식은 [sound_resources.md](sound_resources.md) §4.2/4.6 및 [sound_parameter_composition.md](sound_parameter_composition.md)를 재사용한다. 새 판독파일은 `analysis/decomp/r9_sound/filter_table_stop.c`, `filter_tables_coeff.c`, `new_voice_spatial.c`, `limiter_wrapper.c`이다.

## 3. 진입점과 전체 호출 흐름

[판독] aal 초기화 `37e1de0` 안 `37e2280..22b4`가 0x208B 필터 표(64객체 포인터)를 할당·초기화하고 aal+0x180에 두며 `37e4424(table,sampleRate,heap)`를 호출한다. 이는 다른 명령 큐 클래스 `37eab08`의 +0x180과 다른 객체이다. `37e4424`는 48000/32000에서 슬롯1..15를 등록하고 다른 샘플레이트에서는 반환한다. 슬롯0은 초기0 그대로다. Alto 필터 관리자의 기존 `37d7aa0` 종류0..5→슬롯0..5, 종류6→슬롯63 매핑과 결합된다.

[판독] 게임 갱신 `3144a98`는 새 보이스에 `3128bf4`(오클루전)를 먼저, `3129718`(감도)을 다음에 호출한다. 둘 다 voice+1CC, voice+1E0과 그 +A0 이름의 유효성을 검사한다. 오클루전 ext+28이 참이면 kind0 voice+84=6, amount voice+8C=ext+24를 쓴다. ext+24=0일 때에만 공간질의 `1339e78`를 호출한다. 감도 ext+18과 현재 listener가 유효하면 kind0=64, amount=원본 커브값을 쓰므로 앞의6을 덮어쓴다. 실제 커브 writer·기존 kind 합성은 추가 연결 필요다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 | 필드 | writer | reader | 확정 |
|---|---|---|---|---|
| aal 관리자 | +180 필터표 포인터 | 37e22a4 | 37fa104 | [판독] |
| 필터표 | +8+slot×8 객체 | 37e4424 | 37fa118 | [실행] |
| 표 필터 객체 | +0 vtable / +8 데이터 / +10 u32 count | 37e4424 | 37e4278/42bc | [실행] |
| 보이스 | +84 kind0, +8C amount | 3128bf4/3129718 | 기존383df38 | [판독] |
| 보이스 | +E0 핸들 래퍼 / +D0 그룹 | 기존383d14c | 383d14c/37dfd10 | [판독] |
| 그룹 | +1B8 f32 | 기존3837384(AGST[0x21]) | 383d238 | [판독] |
| 핸들 래퍼 | +1C f32 정지 인자 | 383d23c | 37dfd20,37e0204/02e4/03d4 | [판독] |

48000의 기본1(슬롯1)은 `4af09bc`, count121, 직접 a 선택이다. 기본3(슬롯3)은 `4af12d6`, count122, a(2−a) 선택이다. 32000에서는 슬롯1=`4aef58a`,112; 슬롯3=`4aefdb4`,122이다. 전체30개 객체·계수표는 `analysis/completion/r9/sound_filter_table_emu.json` records에 저장했다.

## 5. 상태 전이와 전체 수명

[판독] 초기 등록 뒤 보이스마다 amount로 표를 조회한다. 기존 `37fa0b8`은 amount를0..1로 제한하고 NaN은0으로 처리한다. 필터 객체가 null이면 enable0이며 직전 enable/계수와 같으면 명령을 생략한다. 필터표 소멸 `37e430c`는 슬롯0..15 객체의 가상소멸자를 실행하고 모든64칸을0으로 만든다. 사용자 객체 슬롯16이상은 별도 소유 관리다(기존37d8598).

그룹+1B8이0이상일 때 재생시작383d14c가 wrapper+1C에 복사한다. 37dfd10 및37e019c의 핸들종류1/2/기타 정지·일시정지 경로가 이 값을37f9790의 f32 인자로 전달한다. 37dfde4의 즉시정지는 항상0을 전달한다. 수치의 초 단위·CPU aal envelope는 r9 추가 [sound_limiter_runtime.md](sound_limiter_runtime.md) §3–10으로 해소했다. SDK 실제PCM소리는별도이다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행] n=count, 계수 한 행은 signed i16 다섯 개(10B), 저장순서는 b0,b1,b2,a1,a2이다. `37e4278`: i=clamp(trunc(f32(f32(n−1)×a)),0,n−1). `37e42bc`: q=f32(f32(2−a)×a), i=clamp(trunc(f32(f32(n−1)×q)),0,n−1). f32 사이의 FMA 결합은 없고, 표 보간도 없다. 원본10B를 그대로 SDK BiquadFilterParameter 계수로 복사한다. Hz 단위의 단일 컷오프를 억지로 붙이지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[데이터] 슈터 focused 발사음은 WpMuzzle_HighSensi/DistCoef12.22/UseOcclusion=false이다. friend/enemy도 같은 거리세트이며 오클루전 기본값은 별도 에셋 기본 정의에 따른다. 표 계수는 original read-only 이미지에서 읽었고 다른게임의 음향값은 사용하지 않았다. 감도커브·FarFx·TargetOffset 최종 공급 경로는 §11 경계다.

## 8. 다른 기능과의 상호작용

오클루전 kind6 뒤 감도kind64의 덮어쓰기를 반영해야 한다. 종류64는 원본 enum 검색→사용자필터 관리자+8 객체의 +10 슬롯으로 해석한다. 이는 종류값64를 SDK 슬롯64로 직접 쓰는 규칙과 다르다(기존37d86e8/383e3e8).

**정정(2026-10-03):** 기존 sound_resources§4.3의 “그룹+1B8을3121ca4가 읽는다”는 객체 기준이 잘못됐다. 3121ca4는 실제 시작3121c8c의 내부명령이며 PingPongDelay 인터페이스(PU+B0)를 기준으로 한다. 공장3120ff8은 PU+268에 MaxDelayTime을 넣으므로 인터페이스+1B8은 이 값이다. 실제 그룹+1B8은383d238에서 wrapper+1C로 전달된다. 같은 오프셋만으로 연결했던 기존 설명은 보존하고 이 근거로 정정한다. InsLimit의 전체 의미가 해소됐다는 뜻은 아니다.

## 9. 웹 포팅 구조와 구현 순서

impl/fx 대응에 필요한 변경은 기본필터1·3을 원본Q14표와 양자화 인덱스로 구현하고, kind6→64 우선순위를 따르는 것이다. stop의 그룹+1B8을 동시발음개수로 해석하면 안 된다. 실제 웹 코드/impl은 변경하지 않았다. WebAudio 응답으로 옮길 때 SDK a1/a2 부호 관례·Q14를 정확히 검증할 필요가 있다.

[판독]+[실행] r9 추가: 새3885564/3884de0의정확한runtime P 기준으로reset/defaultP_D4=1,P_D8=0,BAflags0을확인했다. 원본reset256/4864u32필드비트0bad. 실제kindoverride는3887e3c 인자bit7이켜질때만voice48에써서resetP_D8=0을모든보이스kind로강제하지않는다. 기본필터등록→37fa0b8 nativepool+37e3fec→37ef290 SDK packet2048/12288필드,cache2048,0bad. SDK12B전달은실행했으나audioDSP파형은실행하지않았다. 그룹정지시간의원본단위는 [sound_limiter_runtime.md](sound_limiter_runtime.md) §3–10으로해소했고모든필터최종선택질문은남긴다.

## 10. 검증 코드·실행 결과·기대값

`PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe web/tools/r9_sound_filter_table_emu.py`: 원본초기화3회(48000,32000,44100), 실제30객체/90등록필드, 원본표선택18,682건/93,410계수필드, mismatch0/null0/fault0/auto_map0. 44100은 제공한 빈표를 그대로 둔다. heap malloc만 메모리공급경계로 대체했고 실제등록·콜백·Q14복사를 모두원본실행했다. amount=0,.25,.5,.75,1,각 행 경계와 seed9022026 난수를 검증했다. Q14표 자체는 원본 데이터이며 수학적 설계 의도를 추정하지 않는다.

`full_decomp.sh` 실행은 `analysis/completion/r9/sound_commands.md`에 남긴다. 함수경계 내부주소를 처음 지정한388d190/388d230 및3889d54 조각은 whole 함수근거로 쓰지 않았으며, 실제시작388d170/388d2c4/3889af8을 재판독했다. func_lookup가 metadata gap에서 이전함수를 반환한38485ac/37e4278/37e42bc는 raw RET/진입명령으로 시작을 확인했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

[미확정] SLink runtime P+D8 reset밖 동적writer, voice+180 외부공간 객체 공급·동적갱신, 거리커브→모든보이스 최종선택 전체, SDK 실제 주파수응답부호, SDK 실제 PCM정지시점. 신규 계수표만으로 복합질문 whole확정으로 올리지 않았다. 다음: 3885590의 P+18 공급, 37f9790 및 명령소비자, 게임3129718의 감도커브 공급,383d14c param3[1].
