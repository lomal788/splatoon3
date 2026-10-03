# 플레이어 넉백 메시지 → 물리 속도 (v0)

## 1. 기능 개요와 사용자에게 보이는 동작

탄의 넉백을 받은 플레이어는 입력 속도에 충격 가속을 더하고 일정 시간 감쇠한다. 게임 리스너의 프레임 단위 벡터를 메시지로 바꾼 뒤, 액터 큐가 캐릭터 컨트롤러의 `CharacterUpdateImpactAndReject`에 전달한다 [판독]+[실행]. 고정 inventory `damage_hit.md:L406/L509`의 “물리 쪽에서 속도에 어떻게 더하는지”를 이 경로로 해소한다. 최종 지형 접촉 솔버와 별도 외력 K는 다른 질문이다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`. 기존 `life/batch2.c`, `bulletbody/bb_queue.c`, `r5_physics/actor2.c`는 재사용. 새 자료 `analysis/decomp/r8_combat/impact_defaults.c`, `impact_component_bind.c`, `impact_queue_init.c`, `web/tools/r8_combat_knockback_chain_emu.py`, `analysis/completion/r8/combat_knockback_chain_emu.json`. 원본 파일에는 쓰지 않는다.

## 3. 진입점과 전체 호출 흐름

```text
피해 리스너24632ec → 24c8318(B+a5f9,vec,kind,reject;s0=time,s1=hold)
  → [[B+8]+510]+20 = Q, Q.vt+10 = 12eb378
  → 원본메시지 RTTI 확인 → 12d53f8 필드복사 → Q에 저장
액터0f76a78: 행동슬롯18 다음 → 12eb680(Q,entity)
  → 각M의vec/time/kind/reject → 12ad75c(D,...)
Phive 캐릭터 UpdateComponents의 ImpactAndReject → 12adb58
  → 감쇠전 가속도를 velocity에 더함 → 감쇠/시간/보정 소모
```

Q 생성 `12e8ec8`은 컨트롤러의 UpdateComponents를 `12eb0a0`으로 이름·RTTI 탐색하고 Q+990에 Impact 컴포넌트를 바인딩한다. 실제 이름은 `CharacterUpdateImpactAndReject` [판독]+[실행]. SplPlayer 프리셋의 `ImpactAndReject` 포함·배열 순서 및 실행기 `3a80560`은 기존 [phive_controller.md](../physics/phive_controller.md) §3/5 근거를 재사용한다. 새 실행은 실제 생성자 `12a95f0`과 원본 component search까지 연결했다.

원본 `0f76a78`에서는 큐 소비가 **행동 슬롯18 이후**다. 접촉 큐는 단계1 그룹0에 비워지는 기존 프레임 그래프이므로, 그때 발생해 저장된 메시지는 다음 액터 단계0의 슬롯18 뒤에 소비된다 [판독: 기존 프레임 그래프와 호출자 연결]. 이미 행동 슬롯18에서 들어온 메시지는 같은 액터 호출에서 소비될 수 있다. 원본 프레임 전체를 emulation으로 실행한 결과는 아니다.

## 4. 구조체·필드·상수·열거형 표

B=플레이어 본체, Q=넉백 메시지 큐, M=메시지, I=Impact 컴포넌트, D=[I+28]. 각 기준 객체를 구분한다.

| 객체/필드 | 의미 | writer → reader |
|---|---|---|
| Q+00 VT5576e60 | queue 실제VT(표 시작5576e50+10) | 12e8ec8 → 24c8318 vt10 |
| Q+08/+0C s32 | 저장 수/최대16 | ctor·12eb378 → 12eb680 |
| Q+10 pointer | M 포인터배열 | ctor → enqueue/consume |
| Q+18 pointer | 재사용 free list, M크기88 | ctor·consume → enqueue |
| Q+928 VT5576ea8 | 기본 callback(slot0=12ebbfc RET) | ctor → enqueue; 합성callback 아님 |
| Q+990 pointer | Impact 컴포넌트 | 12eb0a0 이름+RTTI 검색 → consume |
| M+40 vec3 f32 | 충격/밀어냄 가속 | 24c8318→12d53f8→12ad75c |
| M+58 u32 / +5C/+60 f32 / +6D byte | kind/시간/hold/rejectbit0 | 같은 경로 |
| D+08/+24 vec3 | impact/reject | 수신 → update |
| D+14 f32 | 생성기본 NaN(7FC00000); 유한값은별도배율 | 12a95f0 → 12adb58 |
| D+18/+1C/+20 f32 | 감쇠 시간/hold 시간/역입력 제거강도 | 수신·update |
| static5826CD8/CDC/CE0 f32 | 생성기본60/30/30 | 신규12ad660 → enqueue/default, update/strength |

`12ad708..12ad754`에서 packed store **60.0,30.0**과 별도 **30.0**을 원본 실행했다. 5826CE0이 1.0이라는 근거는 없다. 기본 메시지는 CD8×f32(1/60)=1.0초, CDC×f32(1/60)=0.5초를 갖지만 `24c8318`의 인자가 이를 덮어쓴다. 일반 피격 리스너는 두 시간 1.0을 공급한다 [판독].

## 5. 상태 전이와 전체 수명

Q의 16개 메시지 풀→빈 노드를 꺼내 원본 타입 확인/필드 복사→배열 저장→큐 소비에서 D에 합성→M 원본 소멸자 호출 후 free list 복귀→Q 저장 수0. 최대 수 이상이면 enqueue는 그대로 반환한다 [판독]. D는 새 벡터가 영벡터일 때 시간을 늘리지 않는다. 양의 hold가 있으면 strength1. 시간이 줄어도 가속 적용이 먼저다. NaN 기본 감쇠의 f32 잔량은 정수60프레임으로 강제 자르지 않는다.

## 6. 계산식·조건·상세 의사코드

송신 벡터는 `f32(f32(v*60.0)*60.0)`이다. 단일 f32(v*3600)로 반올림 순서를 바꾸지 않는다. 송신 gate는 B+a6c0→+2658, 일치 actorref와special1C, static58bbb9a, B+a5f4/a5f8 조건을 기존 원문대로 유지한다 [판독]. gate가 참이면 메시지를 보내지 않는다.

수신 및 모드별 갱신의 전체 식은 [hitbox.md §5.3](hitbox.md#53-넉백-메시지의-수신합성감쇠-판독--실행-2026-10-03-r8-combat)에 있다. 핵심 순서는 다음과 같다 [판독]+[실행: 보통 모드3].

```text
A = reject ? D.reject : D.impact
A = normalize(A+new) * sqrt(max(dot(A,A),dot(new,new)))
# 합벡터0이면 normalize하지않고0 유지
T=max(T,time); hold=max(hold,holdTime)
velocity += dt*impact       # 감쇠 전, 모드1 예외는 hitbox§5.3
velocity += dt*reject
velocity += (negativeCorrection+positiveCorrection)/dt
if isnan(decay): acceleration *= max(1-dt/T,0) if T>0 else 0
else: acceleration *= decay; lengthSquared<1e-4이면0
각 시간 = max(시간-dt,0)
if hold-dt <=0:
    strength=max(strength + dt/(f32(default30)*f32(-1/60)),0)
```

마지막 줄의 **생성기본 분모는 30프레임, 약0.5초**다. dt=f32(1/60), strength1, hold0에서 새 strength는 **0.9666666388511658**이다 [실행]. static parameter runtime override가 없다는 주장은 하지 않는다. T1/dt1/60은 60번째의 가속 잔량과 61번째의 소모가 기존 실행 그대로다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

이 경로는 속도와 충격 상태를 변경한다. HitEffect/히트마커·피격 ASB·카메라 shake는 별도 경로로, 이 큐와 이름이 비슷하다는 이유로 동일하게 연결하지 않는다. 생성 정보의 크기·피해 결과는 `damage_hit.md` §6.5와 연결한다.

## 8. 다른 기능과의 상호작용

게임 이동이 읽는 D의 가속합/3600과 물리 속도의 dt가속을 같은 단위로 해석한다. 게임 외력 B+16C와 D가 같은 저장소는 아니다. D+4C/+58은 보정 속도이며 매 스텝 소모한다. 지형 접촉·경사·벽 처리 이후의 최종 변위는 별도 솔버 질문으로 남긴다.

## 9. 웹 포팅 구조와 구현 순서

`impl/physics.md`, `impl/weapon.md`, `impl/range.md`의 원본 비교에는 메시지 큐/충격 상태와 적용 순서를 추가해야 한다. 송신→16노드 큐→액터 슬롯18 후소비→nativeImpact 가속전용→감쇠→시간소모를 유지한다. hold 종료 뒤 strength 감소의 기본30과 실제runtime설정을 구분한다. 이번에는 코드·impl에 쓰지 않았다.

## 10. 검증 코드·실행 결과·기대값

`.venv/Scripts/python.exe web/tools/r8_combat_knockback_chain_emu.py` → **1,024건·28,672 update f32 필드 비트 일치, 불일치0**. 추가로 실제원본 큐수신 상태를 독립f32수신대조와 동일하게 확인한다. 실제메시지VT/복사/소멸자·기본RETcallback은 원본을 실행한다. 주변 플레이어/월드 구조체만 합성. 업데이트는 mode3, 모든 rejectbit/kind/시간/영벡터 포함이다. 원본Impact 생성과 type/name바인딩, 수신·갱신은 전체함수, 큐 ctor는 `12e8f68..9074`, static numericwriter는 `12ad708..754` 블록 실행이다.

SDK `__cxa_guard_acquire/release` 각5회, allocator wrapper083d2f0 2회만 경계 처리. 수학·큐·피격 함수 스텁은0. 전역 heaptracking=0과 보통 송신 gate0을 공급했으며 전체 OS/부팅/최종솔버를 검증하지 않는다. 최초 도구에서 queue receiver를 대조 전에 초기화한 부분은 actualstate를 먼저 snapshot하고 독립검증값과 비교하도록 보강해 재실행 통과했다.

사전SHARED/FUNCS/INDEX/func_lookup 확인 후 기존Qctor/actor는 skip/reuse, bind2함수는 새full_decomp. `impact_queue_init.c`의 신규 함수는13450c0이고 나머지2는기존skip. 잘못된 `hitbox_knockback.md`·`regscan.py`·phys5 경로는 실제자료로 정정하고 근거로 사용하지 않았다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

K(B+16C)의 writer·D와의 관계, 피격 애니/카메라/이펙트, 최종 지형 접촉 솔버는 각각별도고정질문이다. static5826CD8/CDC/CE0의 생성기본은 확정했고 런타임설정 override 전체는 미확정으로 남긴다. 다음근거는 해당staticparameter loader/fielddescriptor, PlayerCollision비트11·형태조건, 실제 피격 상태 ASB와 카메라 소비자이다. composite hitbox:L88/L99는 승격하지 않는다.
