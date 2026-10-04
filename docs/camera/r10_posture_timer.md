# r10 사격 자세 타이머와 붐 이동량 항

작성일: 2026-10-03. Splatoon 3 v0, Lby_Lobby00 1인 슈터. 분석 전용이며 웹 source/assets/impl은 수정하지 않았다.

## 1. 기능 개요와 사용자에게 보이는 동작

**종료 시점 최신값(2026-10-03):** 새GrindRail 선행조건4096건을 더한 **14848건 불일치0**. 앞10752는이후속전검토값이다. §6.2의가상대상명칭정정과실행경계를우선하며고정33전체는조사중이다.


카메라 붐의 거리 복귀 속도에는 `B+ad0>0 && C+15d9==0`일 때 이동량 항이 추가된다. 원본은 발사 후 이 타이머를 올리고 공중 프레임 수에 따라 감소를 다르게 처리한다. 마우스 입력으로 발생한 갑작스러운 뒤돌기를 이 항의 정상 효과라고 단정하지 않는다.

**[실행] 신규:** 발사 후 writer 2,048건, 입력 단계의 감소 3,072건, 메인 단계의 −4 포화감소 512건, 합계 **5,632건 불일치0**. 실제 발사 함수 전체·모든 상태 writer·Lby 프레임 실행은 남아 고정 질문33을 전체 확정으로 올리지 않는다.

**2026-10-03 후속 [실행]:** 입력 활성 술어부터 감소까지 `24a0100..0444`를 추가 **4,096건 불일치0**으로 대조했다. 새 누계는 **9,728건**이다. 앞선 함수/가상 호출의 반환값을 입력으로 공급한 경계는 남지만, 앞 시험의 supplied active bool은 이번 시험에서는 원본 술어로 계산한다. 같은 정지·발사 후 값이라도 공격 카운터/입력, 스틱 차이/스틱 Y, 경사·속도·공중 조건에 따라 하한90 유지 여부가 달라진다.

그 뒤 별도 main 구간의 감소 후 하한 writer까지 **1,024건 불일치0**으로 이어 검증했다. 최종 신규 누계는 **10,752건**이다. 메인 ad0가 항상−4라는 확대 해석은 뒤의 원본 하한 재적용 때문에 성립하지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

원본 `extracted/exefs/main.reloc.img`, BASE `7100000000`을 Unicorn으로 실행했다. 기존 SHARED/FUNCS와 decomp_index를 먼저 확인해 `analysis/decomp/weapon/ink_consume.c`의24b28b0, `analysis/decomp/move/move_input.c`의249f494, `move_full_main.c`의2475a54, r7 붐 원본 실행640건을 재사용했다.

새 결과는 `analysis/camera_100_r10/timer/timer_native.json`, `active_native.json`과 `writer_candidates.json`이다. 새 후보24bd850은 별도 판독 후 타이머 writer에서 제외했다.

## 3. 진입점과 전체 호출 흐름

**[판독] 재사용과 신규 실행 구간:**

```text
Shooter2583008 →24b28b0
 →24b29ac: secondary-interface VT+118 getter
 →24b29b0..24b2a40: B ad0/ad4/ad8/adc/abc/ab8/ac4 writer [실행]
Input249f494 →24a03f8..24a0444: B ad0 조건부 감소/하한 [실행]
Main2475a54 →2481aac..2481b08: B ad0..adc −4 포화감소 [실행]
PlayerCamera24d9ae8 →24dde2c..24de70c: 붐 이동량 항 [기존 실행640]
```

후속 실행은 기존 C의 `24a0100..0444`를 판독한 뒤 원본 명령을 그대로 실행했다. `245aa00(...,mode0/1)`, Jetpack predicate `24c8ee8`, 무기 인터페이스 가상 predicate의 반환은 실행 전 입력이다. 이들 getter 전체를 스텁으로 실행한 것처럼 세지 않는다. 본체 포인터 `x19=B`, `x28=B4d0`, `x23=B4e0`, `x21=B518`, 스틱 입력 포인터 `Baa4`는 기존 원본 로컬 계산에 대응한다.

실행 시작의 live register와 body 메모리는 하네스 입력이다. getter 반환 n=4는 기존 실제 슈터 데이터이며 이번 writer 시험은 getter 이후부터 실행했다. 이를 getter 전체 실행이라고 쓰지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 필드/상수 | 원본 값·역할 | 근거·수준 |
|---|---|---|
| B ad0 | 발사 후 writer가 하한82로 올리는 정수 타이머; 붐 이동량 항 guard |24b29d4/24a0440/24dde2c 이후 [실행]+기존 [판독] |
| B ad4/ad8/adc | 같은 writer의 하한4/4/8 |24b29e4/29f8/2a08 [실행] |
| B abc/ab8/ac4 | 같은 writer의 하한4/4/4 |24b2a18/2a2c/2a3c [실행] |
| B c0 | 공중 프레임 수;4부터 ad0 감소를 건너뜀 |기존 이동 문서 의미+24a041c..043c [실행] |
| G58bbc20 |4, 공중 감소 분기 경계 |실제 초기화 스냅샷·기존writer2455db0 [데이터] |
| G58bbf2c/f30/f3c |90/12/4, 자세 유지·차감·추가값 |같은 기존 초기화 [데이터] |
| n |PostDelayFrame4 |기존 WeaponShooterParam [데이터]/writer [실행] |
| G58bbd80/d84 |각각 f32 0.2, Bad0 활성 술어가 읽는 입력 문턱 |post-init snapshot 및24a018c/01ac [데이터]+[실행] |
| G58bbb60 |f32 0.6414496898651123, B184 비교 문턱 |24a01d4 [데이터]+[실행] |
| literal3716feb5 |f32 9.000000318337698e−6, B114/118/11c 제곱합 문턱 |24a01fc..0210 [판독]+[실행] |
| Demo=[B+a650], Demo+bf4 |timed-direction 명령의 seconds; 양수timer 감소 후 여전히양수면 Bad0 하한2 |원본23613ec→250b8f0 [판독]+[실행:empty-queue tick] |

ad0/ad4/ad8/adc를 모두 회복 정지 시간으로 명명하지 않는다. 각 애니 소비자·전체 상태 의미는 기존 player 문서의 별도 범위이다.

## 5. 상태 전이와 전체 수명

새 시험은 발사 후 상승, 입력 단계 감소/유지, 메인 단계 포화감소를 각각 실행했다. 전체 액터 프레임 안에서 두 단계의 활성 bool와 여러 writer가 실제로 선택되는 조합까지 연속 실행하지 않았다. 그래서 “발사 후 정확히82프레임 유지”라는 결론은 내리지 않는다.

입력 단계는 공중 프레임이4 이상이면 기존 ad0를 줄이지 않고 하한만 적용한다. 메인 단계에는 별도의 −4 소비가 있다. 한 단계의 감소량을 전체 프레임 감소량으로 바꾸면 잘못된다.

## 6. 계산식·조건·상세 의사코드

**[실행]** 평상 슈터 n=4의24b29b0..2a40:

```text
ad0=max(s32(ad0),82)
ad4=max(s32(ad4),4); ad8=max(s32(ad8),4); adc=max(s32(adc),8)
abc=max(s32(abc),4); ab8=max(s32(ab8),4); ac4=max(s32(ac4),4)
```

**[실행] 최초 감소 시험:** 입력 단계24a03f8..0444의 ad0 부분. 이 최초 시험의 `active`는 앞선 술어가 만든 W11 입력이었다. 후속 §6.1에서는 술어부터 직접 실행했고, 그보다 앞선 함수 반환 공급은 별도 경계로 남는다.

```text
floor=active ? 90 : 0
if s32(Bc0)<4:
    ad0=max(s32(ad0-1),floor) # subtraction wraps32 before signed comparison
else:
    ad0=max(s32(ad0),floor)
```

INT_MIN에서 뺄셈이 INT_MAX로 돌아가는 원본 동작도 그대로 비교했다. 일반 수학의 무한 정수 뺄셈으로 정리하지 않는다.

### 6.1 후속: active를 만드는 원본 술어 [실행:구간]

아래 `g`는 공급된 `245aa00(mode0)`/`24c8ee8`/무기 predicate 반환의 bit0 중 하나가 참이거나, SM+c8가95/e2이고 B80c<1인 조건이다. `245aa00(mode1)`은 뒤의 다른 출력에 쓰며 이 active 결정에 직접 넣지 않는다.

```text
A = ab4<1 && (4d0>0 || 530!=0 || 531!=0)
B = ab8<1 && (4e0>0 || 532!=0 || 533!=0 || 4f2!=0)
C = ab8<1 && (518>0 || 534!=0 || 535!=0 || 52a!=0)
if g: active=1
elif A || B || C: active=0
elif abs(aa4)>=0.2 || abs(aa0)>=0.2: active=1
elif c0>=4 || ARM_LT(184,0.6414496898651123): active=0
elif ARM_PL(f32(f32(114²+118²)+11c²)-9e-6): active=0
elif ARM_HI(47c,0): active=0
else: active=1
```

필드는 모두 B 상대 주소다. 세 공격 묶음의 무기별 의미를 새로 이름으로 단정하지 않는다. `aa4`는 기존 입력 차이 X이며 `aa0`는 반전 적용 스틱 Y다. 두 축을 모두 같은 스틱 값으로 바꾸면 다른 동작이다. 합성 ordinary 입력에서 공격 묶음0·스틱0·공중0·B184=1·속도0·B47c=0이면 active1이고 ad0=82를90으로 올린다. A의4d0만1로 바꾸면 active0, ad0는81이 됐다. 따라서 발사 타이머만으로 이 필드 수명을 설명할 수 없다.

**NaN 순서 [실행]+[판독]:** 원본 FCMP에서 unordered의 `GE`는 거짓, `LT`/`PL`/`HI`는 참이다. `B184`, 속도 제곱합, `B47c`의 NaN은 inactive 쪽으로 간다. 스틱 NaN의 첫 GE는 거짓이라 다음 조건을 이어간다. 위 의사코드의 ARM 표기는 NaN까지 포함한 분기 조건이며 보통의 JS `<`/`>=`와 동일하다고 쓰지 않는다.

**[실행]** 메인 단계2481aac..1b08에서는 ad0/ad4/ad8/adc 각각 `max(s32(v),4)-4`를 쓴다. 진입 상황은 이 부분 실행만으로 오징어 전용이라고 명명하지 않는다.

**2026-10-03 후속 [실행]:** `2481aac..1b8c`는 그 감소 후 다음 하한을 적용한다. bytes는 공급된 stack 값이며 앞선 생산자 의미는 남는다.

```text
ad0=max(max(s32(old_ad0),4)-4,4*u8(stack3cd))
ad4=max(max(s32(old_ad4),4)-4,4*u8(stack3ce))
ad8=max(max(s32(old_ad8),4)-4,4*u8(stack3cf))
adc=max(max(s32(old_adc),4)-4,4*u8(stack3cf))
```

ad8과adc는 같은3cf를 쓰지만 ad0의3cd와 합치지 않는다. 전체byte 입력0..255와 signed극값을 대조한 결과이며 실제 producer가255를 만드는 상태라고 주장하지 않는다.

**기존 판독 재사용:** SHARED의 r6 camweapon 기록에 이8개byte의 source가 이미 있다. `2476698`은SP3c8..3cf를64bit zero로 초기화한다. 객체는SP3a8, VT562f3b8계열, flags는객체+20..27이다. `SP4c0==1`일 때 `2476778`이SP2a8 원천의type을검사한뒤 vt+38로 복사한다. 기존2423844는8bool×1bit/u32 2bit 직렬화reader다. 새 검색으로 재발견한 이 연결을 신규 분석 성과로 세지 않는다. 실제SP4c0 선택과원천 동일성은기존 기록에서도 미확정이므로0으로 공급해 닫지 않는다.

**기존 [실행]+[판독] 재사용:** 붐은 follow 변화량 Δp에서 `Bc0>=4`이면 Y−B73c를 적용하고, `Bad0>0 && !C15d9`이면 `length(Δp)*(0.5-0.4q)`로 speed 하한을 올린다. 원본 f32 순서/max/평활은 [player_camera §6.8.1](player_camera.md)에 있다. B7a0는 이 guard가 아니라 앞쪽 별도 wall 항의 guard이다.

### 6.2 2026-10-03 선행 가상 조건의 대상 정정

**정정 [판독]+[실행:구간]:** 앞 §6.1과 첫 하네스의 “무기 predicate” 설명은 잘못됐다. 실제 `249fdc0..fdcc`는 `x22=B+ad0`에서 `9ba0`를 더한 `[B+a670]`를 stack98에 저장한다. `24a0038`이 다시 같은 `[B+a670]`를 읽고 `24a0050`이 stack98을 x20으로 복원한다. 네 가상 호출의 대상은 모두 **PlayerGrindRail**, actual VT5635660이다. 기존 하네스/결과의 key `weapon`은 이 합성 반환값의 옛 이름이다. 기존4096건 산술 대조는 유효하지만 그 이름을 Weapon 인터페이스 근거로 쓰면 안 된다. 옛 문장을 보존하고 이 정정을 우선한다.

새 도구 `r10_camera_posture_grind_gate_emu.py`는 원본 `24a0038..24a00f4`와 실제 가상 함수들을 **4096건 불일치0**으로 실행했다. null/자동페이지/PLT/수학 스텁/명령 patch는 모두0이다. 실제 global58bd688의 post-init 값은60이다. G=[B+a670]일 때 다음 순서다.

```text
excluded = SM.c8∈[82..90] 또는 [aa..ac] 또는 {ed,ee,10c}
if G.vt100(0)!=0 && !excluded: result=1
elif G.vt148()!=0: result=1
elif (G.vt108()&1)!=0: result=u32(G.vt1c8())>>31
else: result=0
```

actual slot100=2530fe0은 인수0일 때 G173의 nonzero를 반환한다. slot148=2529960은 slot120=2531038의 G1c8 bit0와 signed `0<=G1f0<=60`을 검사한다. slot108=2531020은 G1c0 byte, slot1c8=25310d0은 G1d0 u32를 반환한다. 단순히 첫 G173만 쓰거나 네 호출을 무기 상태로 합치면 다른 조건이다. 결과 분포는 첫 rail 경로2575/slot148 경로341/slot108+sign 경로236/거짓944였다. 이 분포는 합성 검사 입력이며 실제 사격장의 발생 빈도가 아니다.

원본 세 함수의 새 C는 `analysis/decomp/camera_100_r10/timer/next_grind_predicates.c`다. slot100은 이미 저장된 C를 재사용했고 slot120은 실제 leaf 명령을 판독했다. 새4096건은 앞 active4096과 다른 원본 구간이다. 타이머 검증 누계는 **10752+4096=14848건**이며 전체 액터 프레임 검증 수라는 뜻이 아니다. 선행245aa00/24c8ee8, 메인 variant selector/stackbyte 실제 공급, 상태별 writer와 전체 프레임은 여전히 남는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

**2026-10-03 새 Demo writer 연결 [판독]+[실행]:** [상태 생산자](r10_state_producers.md)의 원본 `23613ec` 메시지6e9f8228/payload+50가 Demo+bf4 seconds를 공급한다. 이 Demo offset을 본체B+bf4로 쓰지 않는다. 음수seconds는FLT_MAX로 바꾸고 NaN은 보존한다. whole `250b8f0`의빈queue tick은 `bf4>0`일때 f32−1/60 후남은시간이양수면 signed `Bad0<=1`을2로올린다. 만료면be4..bf8을clear하고그writer를실행하지않는다. 이는사격writer의하한82와다른실제생산자다. 원본 전체selected receiver/parser/tick 922건 중emptytick384건이며, **상태문서의922를이문서신규10752에중복합산하지않는다**. 실제script sender/queue/scene 도달은별도미확정이다.

기존 Shooter 발사 writer와 붐 consumer의 같은 B ad0 필드를 연결했다. 파라미터 n=4를 새 임의 값으로 공급하지 않았으며 원본 WeaponShooterParam 근거를 재사용했다. 다른 무기·서브·스페셜의 실제 동작은 이번 조사에서 제외했다.

## 8. 다른 기능과의 상호작용

B7a0 ordinary producer는 기존 [player_state §6.1.4](../player/player_state.md), [squid_ink_visibility_r2](../graphics/squid_ink_visibility_r2.md) 원본 실행을 재사용한다. 평지 아군 잉크 오징어에도 참이 될 수 있으므로 벽 전용 bool로 바꾸면 안 된다. 이 지연 표시 상태를 ad0 타이머와 합치지 않는다.

주소 후보의 오프셋도 타입 근거가 아니다. 24bd850의 ADD ad0는 타이머 후보로 찾았지만 새 C를 읽으니 PlayerTank 모델 선택의 다른 구조체 접근이었다. 후보 목록의80개 direct store·325개 alias를 모두 본체 writer로 세지 않았다.

## 9. 웹 포팅 구조와 구현 순서

웹 반영 필요: `impl/camera.md`의 생략된 ad0 이동량 항은 기존 원본 guard·Δp·q·max/평활을 따라야 한다. 타이머를 임의 초 단위로 유지하거나 발사 후 단순82프레임 카운터로 대체하지 않는다. 공중 감소 우회와 메인 단계 별도 writer를 결합하려면 actual frame 공급이 추가로 필요하다. 웹은 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

```text
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_timer_scan.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_timer_emu.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_active_emu.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_main_floor_emu.py
.venv/Scripts/python.exe -X utf8 web/tools/r10_camera_posture_grind_gate_emu.py
```

5,632건 모두 독립 정수식과 일치했다. signed 극값/−1/0/4/82/90 인접값, 공중3/4/5, active0/1, 난수 기존값을 포함했다. null/auto/fault/PLT/libm 모두0, 명령 patch0. timer block에는 SDK 함수를 대체한 수학 스텁이 없다.

후속4,096건에서는 original active와 최종 ad0를 독립 술어/정수식과 대조했다. active3,143/inactive953, NaN 입력1,410건이다. null/auto/fault/PLT/libm 모두0이고 original helper/math 실행을 대체한 patch도0이다. 앞 함수 반환을 제공한 pre-block 경계는 결과 JSON에 명시했다. 첫 실행은 PUC에 없는`w64` 메서드로 실패했고 기존 `wq`로 수정한 뒤 모두 일치했다. 이 실패는 원본 명령 실행 실패나 부재 증거가 아니다.

main-floor 후속1,024건은4필드 감소와3개의stackbyte×4 하한을 독립 정수식과 비트 일치시켰다. `main_floor_native.json`에 결과·범위를 보존했다. null/auto/fault/PLT/libm 모두0이고 명령patch0이다. 앞512건은 감소만의 기존검증이며 새1,024건과 중복 실행으로 누적한 것이 아니다.

`disasm.py 주소 끝주소` 첫 명령은 CLI 인자 오류로 실패했고 `--end`로 정정했다. 24bd850은 SHARED/FUNCS/index에 없음을 확인하고 func_lookup 시작을 검증한 뒤 full_decomp로 C를 저장했다. 이 후보는 타이머 생산자가 아니므로 확정 성과로 세지 않는다. 실제 명령과 실패는 `analysis/camera_100_r10/commands.md`에 기록한다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

고정 질문33은 **[실행:부분]+[판독], 조사중** 유지다. 후속으로active 술어와메인 감소 후하한을 직접 실행했지만 모든 상태 writer, 앞선245aa00/24c8ee8/무기 가상 predicate의 실제 공급, stack3cd/3ce/3cf 원천의선택과 본체/actor 동일성의 실제 프레임 연결이 남았다. 다음은249f494의249fdc0..24a0100 선행 반환 공급,2475a54의SP4c0선택(SHARED기존다음후보2423b28/24246b4·2476428),2483134의248590c 활성 조건이다. 앞512건은 하한 재적용 이전 구간까지의 실행으로, 최종 메인 ad0가 항상−4라고 확대하지 않는다. SP literal stores와alias 검색0건은전체writer 부재를증명하지 않으며64bit reset/virtual copy는기존근거를재사용했다. 출하 사격장 전체 프레임을 구성하지 못한 이유는 actor/component/world/bootstrap 입력이 아직 합성 경계이기 때문이며, 임의상태0으로 채워 확정하지 않는다.

**2026-10-03 selector 후보 제외 후속 [판독]:** SHARED525의 다음 후보2423b28/24246b4를 index 조회 후 새 C/명령으로 확인했다. 각각 payload+20 byte/+24 u32, 그리고+28/+2c/+34/+38/+3c를 복사할 뿐이다.2476434 호출 직후2476438이SP4c0을0으로 별도 초기화하므로 그 두 복사를SP4c0=1 직접 writer로 해석할 수 없다. 실제+1 선택 공급은 남는다. 기존2658bb4는 FUNCS177의 수신 갱신 함수임을 확인해 cached 근거만 재사용했고, 범위 밖 네트워크 동작을 새로 분석하지 않았다. 이 부분 drain/stack fixture의 성공을 1인 연습 actual frame 도달 증명으로 계상하지 않는다.

**2026-10-03 요청에 따른 분석 종료 기록:** 선행 가상 조건의 대상·반환은 §6.2로 해소했다. q33 전체는 조사중이며, 아직 확인하지 않은 상태/프레임을0으로 공급해 닫지 않는다. `245aa00`/`24c8ee8` cached C와 실제 호출 인자를 읽었지만 이번 종료 전 새 whole 검증은 수행하지 않았다. SP4c0의 literal store/copy 재조회만으로 실제 source 선택을 확정하지 않는다.
