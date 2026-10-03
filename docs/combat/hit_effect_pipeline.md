# 슈터 명중 큐·피드백 소비 — Splatoon 3 v0, 2026-10-03 r8

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 실제 명중의 HitEffect 요청과 조준 예측 마커는 별개다. 실제 명중은 결과0(Through)이면 요청을 만들지 않으며, 그 밖에는 무기 행·결과·재질·로컬 여부로 셀을 고른다. S1/E1은 피격 피드백, S2/E2는 해당 충돌의 소리·이펙트 경로다. 원본은 **로컬 S1/E1 처리 뒤 거리 컬링**을 한다. 컬링을 전체 피드백의 첫 조건으로 옮기면 원본과 다르다.

고정 r7 `combat/hitbox.md:L98`은 [shooter_bullet.md §3.3.9–3.3.10](../weapon/shooter_bullet.md)의 실제 Shooter 표시 호출/단계 수 및 명중 요청 생성과 이 문서의 원본 큐·소비를 연결해 해소한다. `effect_sound/effect_sound.md:L186`의 미추적 반응 열은 원본 셀 번호 생산·소비로 해소한다. 전체 renderer·오디오 믹서·실제 게임 캡처 검증으로 넓히지 않는다.

## 2. 분석 대상 원본·버전·자료 위치

- 원본: v0 `extracted/exefs/main.reloc.img`, 원본 SDK `extracted/exefs/sdk.img`; 수정·패치 없음.
- 기존 디컴파일 재사용: `analysis/decomp/r5_combat/b1.c`(27b4704), `network/net_player.c`(27b877c), `network/net_core.c`(27b7938), `effect_sound/fx_batch3.c`(27b5430/5640/4aa4/5980), `effect_sound/fx_full.c`(27e24a8).
- 원본 설정 추출: `analysis/combat/HitEffectConfig.json`, 실제 `Shooter___결과_재질` 키. 문자열이 없으면 Default 재질 행을 찾는 loader 판독은 기존 근거를 재사용한다.
- 신규 검증: `web/tools/r8_hiteffect_consume_emu.py`, `analysis/completion/r8/hiteffect_consume_emu.json`. 기존 SHARED/FUNCS/decomp_index 대조 뒤 재디컴파일 없이 실제 함수 연결을 실행했다.

## 3. 진입점과 전체 호출 흐름

[판독]+[실행]

```text
접촉/receiver 결과 →16d99f4→12d4f8c/12d68cc→16d9c60
 →실제 WeaponInfo/HitEffectorType 행→27b4704(G,request)
 →27b7938(G,context) FIFO 소비
 →27b877c(wrapper{VT5649130,G},node,aggregate)
   1. 로컬/Armored·3D/3E·활성 게이트→27b4aa4: S1/E1
   2. ActorID→146cb20→146d164, 팀 선택
   3. 27e24a8 거리 컬링
   4. S2: AggregateNum/Velocity/IsPaintable→27b5430/27b5640→XLink
   5. E2 코드 emitter 분기
   6. E2 문자열 XLink 발생(코드 emitter와 별도)
   7. delay>0이면 억제용 목록에 복사
```

요청 생성은 새 `shooter_bullet§3.3.10` 원본1024건/paintability2688건 근거를 사용한다. **코드 emitter를 고른 뒤에도 E2 문자열 XLink를 시도한다.** Splash/Hit/Water 문자열을 코드 emitter로 대체해서 XLink 발생을 생략하지 않는다.

## 4. 구조체·필드·상수·열거형 표

G=HitEffect 관리자, node=0x70B 큐 항목. 아래 오프셋을 PlayerDamage/Weapon 객체와 혼동하지 않는다.

| 기준 | 필드 | writer → reader |
|---|---|---|
| request/node+24 | u32 재질 | 접촉 생성→27b4704 셀번호 |
| +28/+2C | s32 결과/행 | receiver·실제 WeaponInfo→27b4704 |
| +30 | f32 delay 초 | 정보 생성→27b877c 지연목록 |
| +34/+38 | s32 owner/target | 요청 생성→로컬·Subjective 조건 |
| +3C | u8 paintable | 12d68cc→속성/코드 emitter |
| +3D/+3E | callback/발생 gate | 실제 bullet VT/발생flag→집계 조건 |
| +40/+48/+50 | kind/참조/ID | 생성→단순·그룹 큐/참조 증가/그룹 비교 |
| node+58 | u32 cellIndex | **27b4704 생산**→27b877c/27b4aa4 |
| node+60/+68 | list next/previous | enqueue→FIFO walk/recycle |
| G50/58/60/68/78 | 단순 head/tail/count/free/capacity | loader/queue→frame consumer |
| G80/88/90/98/A8 | 그룹 queue, 같은 구성 | kind!=0→group consumer |
| G+B8+16×index | {Cell*,E1kind,E2kind} | loader→controller |
| Cell+48/+50/+58/+60 | E1/E2/S1/S2 문자열 | 원본 config 필드→원본 소비 |
| Cell+68..6B | S1/S2/E1/E2 설정 flag | typed loader→parent field 선택 |
| G690B8/G690C0 | SLink/ELink instance | loader→XLink 요청 |
| instance80+0/4/8/C/10 | IsLocal/IsPaintable/AggregateNum/Velocity/SubjectiveType | 원본 소비→XLink 조건 |

원본 getter `14188b8`/`27b8258`/`26bc9ac`가 반환하는 것은 **이름 배열 포인터**다. 실제 실행으로 행48·결과8·재질35개의 순서를 읽었다. Shooter 행=1. 결과는 Through0, Constant1, Aggregated2, NetPriorityFailure3, Invincible4, Armored5, Damaged6, Cure7. 재질 Undefined0, Character1, Water2, … KebaInk24, Ink26, Barrier27, Shield28, … CoopFloat34. 전체 배열은 결과 JSON에 보존한다. 배열 getter를 인자별 문자열 getter로 처리한 첫 검증은 UnicodeDecodeError로 실패했고 교정했다.

## 5. 상태 전이와 전체 수명

[판독]+[실행] 두 큐의 실제 용량은 각64, node는0x70B. count>=capacity이면 새 요청을 버린다. node 내용을 복사하고 자유 목록에서 제거하여 head에 삽입한다. 리스트의 빈 sentinel은 **head=tail=자기 head 주소**다. 원본 consumer는 tail부터 previous를 따라 발생 순서대로 처리하고 모든 node를 free 목록으로 되돌린다.

요청+48 참조는 enqueue 때 atomic 증가, 소비/제거 때 감소한다. 이번 실행은 null 참조로 실제 코드의 null 분기를 사용했으며, **유효 참조 pool 해제 전체는 미검증**이다. request+30>0이면 G69140 지연 목록에 복사하며 원본은 f32(1/60)씩 줄여<=0에서 해제한다. 이 지연은 즉시 발생을 늦추는 예약이라고 바꾸지 않는다. 그룹 재발생 억제에서 소비된다. 지연 목록·비어 있지 않은 그룹 비교 전체는 이번 독립 실행 밖이며 기존 판독 범위로 남긴다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행]

```text
if result==0: return
index = u32(result*0x46 + row*0x230 + material*2) | u32(owner==localD470)
cell = (index>>8 <0x69) ? G+B8+index*16 : G+B8
```

원본 index 산술에 재질 범위를 자동 clamp하는 코드를 추가하지 않는다. 범위 초과 셀을 whole게임의 정상 재질로 단정하지도 않는다. 실행 fixture는 실제 enum 범위0..34를 사용했다.

S1/E1 대상은 owner>=0이며 localD470와 일치하는 owner, 또는 결과5 Armored이고 target이 localD470와 일치하는 경우다. 해당 셀의 S1/E1가 둘 다 비어 있고 E1kind<0이면 집계를 생략한다. req3D=0이면 직접 집계, req3D!=0이면 scene650C=0·유효 peer상태(-1/3 제외)·req3E!=0일 때 집계한다. 이번 실행은 정상 solo peer1 및 네 가지 gate 조합을 공급했다. 네트워크 serializer는 실행 범위 밖이다.

S1/E1: paintable=1, velocity=0, aggregate는 signed 0..15 clamp. S2/E2: paintable=req3C, velocity=sqrt(f32(vx²+vy²+vz²)), aggregate 원값. `27b5430`은 owner==PM+D474면 IsLocal1/Focused0, owner<0이면 IsLocal0/Enemy2, 나머지는 팀으로 Friend1/Enemy2를 고른다. **localD470(셀/피드백 gate)와 D474(Subjective)를 합치지 않는다.**

원본 distance gate: 같은 팀 R=400−300×min(n/30,1), 그 밖R=400; disabled면 false. 비교는 distance²>R²이므로 경계와 같은 거리는 유지한다. **거리보다 먼저 S1/E1을 실행**하여, 멀 때 S2/E2가 생략되어도 이미 요청한 로컬 피격 피드백은 남는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[데이터]+[판독]+[실행] 실제 슈터 ID40의 기본행 Shooter와 critical ExtraInfo17의 동일행 선택은 기존 r6 근거를 재사용한다. 이번 신규 원본 queue/controller 실행이 실제 소비 셀과 키를 연결했다.

| 결과·재질 fallback | S1 / E1 | S2 / E2 |
|---|---|---|
| Constant_Default | 비어 있음 | インクヒット / Splash |
| Constant_Water | 비어 있음 | 水没 / SplashWater |
| Armored_Default | アーマード / HitInvalid | インク被弾 / Hit |
| Invincible_Default | ノーダメージ / HitInvalid | インク被弾 / Splash |
| Damaged_Default | ヒット / HitEffective | インク被弾 / Hit |
| Cure_Default | ヒット / HitEffective | S2 없음 / Hit |

`Constant`는 **응답 결과1**이다. 기존 `damage_hit§3.2`가 판독한 막는 접촉·리시버 없음의 지형 경로는1을 생성한다. 신규 index식은1을 Constant열로 보내고 실제 Undefined 재질은 Constant_Default를 사용한다. 따라서 이 경로의 착탄음은インクヒット이다. **Constant이면 지형뿐이라는 역명제는 근거가 없다.** Barrier 등의 별도 Constant 셀도 원본 설정에 존재한다. 기존 effect_sound§3.5의 'Constant=지형' 추정을 이 방향으로 정정한다.

ELink/SLink resource의インクヒット 조건(Focused, IsPaintable, Velocity>0.9)은 기존 `effect_resources§4` 근거를 재사용한다. 이 문서는 nativeconsumer가 해당 속성과 키를 보내는 연결을 새로 실행한 것이다. 실제 샘플 렌더·믹서 소리를 들었다고 주장하지 않는다.

조준 히트마커는 실제 Shooter 보조VT5637898+60=2586AA0, P64 ShotGuideFrame/flag96을 사용한다. show/predict 전체 gate와 표시 갱신은 `shooter_bullet§3.3.9` 876+512 PASS, 기존 예측/receiver flag 실행12000건과 연결한다. 실제 명중 이벤트로 예측 마커를 토글하지 않는다.

## 8. 다른 기능과의 상호작용

피격 결과0은 queue 이전과 enqueue 양쪽에서 차단된다. 같은 프레임에 복수 요청이 오면 단순 큐는 FIFO이며 그룹 큐는 kind·참조·result/ID에 따라 집계한다. 피격 피드백 조건·거리 조건·표적 HP 소비·조준 예측은 각각 별도다. 한 조건을 다른 경로의 HP 판정으로 바꾸지 않는다.

요청0C 방향은 실제 info 방향 또는 NaN fallback contact 방향이며 **항상 면 법선으로 확정할 수 없다**. renderer의 벽/바닥 산술에 들어간다는 사실과 물리적인 면 법선이라는 이름을 구분한다. 전체 Ray/Capsule/Havok·실제 표적 ActorRef는 다른 미확정 inventory 항목이다.

## 9. 웹 포팅 구조와 구현 순서

코드는 수정하지 않았다. `impl/weapon.md`, `impl/range.md`, `impl/fx.md` 반영 필요:

1. 실제 Shooter show/predict gate와 ShooterParam 단계 수를 연결하고 예측 표시와 실제 명중 이벤트를 분리한다.
2. 원본 셀번호·재질 fallback·S1/E1/S2/E2를 데이터로 보존하고 각64 큐/FIFO를 유지한다.
3. 로컬 피격 피드백을 먼저 요청한 뒤 S2/E2 거리 컬링을 적용한다.
4. S1/E1의 paint1/vel0/aggregate clamp와 S2/E2의 실제 paint/velocity를 구분한다.
5. E2 코드 emitter 뒤 문자열 XLink 발생을 보존한다. 팀/도색 가능 슬롯을 원본대로 선택한다.
6. 정상적인 지형 충돌→Constant_Default→インクヒット 경로를 쓰고 Constant를 지형 전용 enum으로 치환하지 않는다.

## 10. 검증 코드·실행 결과·기대값

실행 명령: `.venv/Scripts/python.exe web/tools/r8_hiteffect_consume_emu.py`. 실제 명령은 이 절과 combat_commands.md에, 원본 v0 범위는 §2에 기록했다. 최종 JSON에는 enum배열·주요 사례·키/속성·호출경계를 저장한다.

- queue140건: 단순·그룹 각각70요청,64수용/6drop, 복사0..43·ID·index 전체 일치.
- controller5880건: 결과1..7×재질35×paint2×방향/속도3×gate4, native S1/E1/S2/E2 키·5속성 기대식과 모두 일치.
- native frame consumer5건: Damaged→Armored→Invincible→Constant→Cure FIFO 및 모든 node 회수 일치.
- native 거리16건: count0/10/30/60, 각 R−1/R/R+1/2R. S1/E1 유지와 S2/E2 생략 순서 일치.
- 원본 SDK asinf/acosf/sinf/cosf/atan2f를 실제 모듈로 실행했다. 합성 sin/cos 근사로 코드 emitter 행렬을 만들지 않았다. 단, **행렬 전체의 독립 bit대조를 한 것이 아니라 키/속성/선택/큐 경로가 검증 대상**이다.

SDK allocation·mutex·guard 및 ctor3585094/0000250/083D2F0 경계는 JSON에 기록한다. ActorManager의 외부 두 virtual getter는 current0/ActorID C0000001을 공급했고 이후 `146cb20/146d164`는 원본 실행했다. typed config 필드는 원본 JSON으로 공급하며 일반 loader 전체는 실행하지 않았다. ActorRef는 실제 invalid ID−1을 써 원본 invalid 경로를 실행했다. null page를 허용하지 않는 read hook에서 **null read0**.

XLink resource lookup `389e830/38a0a08`, 최종 emit `389e90c`, 코드 emitter backend `137f558`, scope밖 replica update129E630는 요청 캡처/경계다. 가짜 활성 핸들로 native 후속 속성 write 조건을 진행했으며 실제 GPU/오디오 실행은 아니다. 원본 코드 패치0.

실패 보존: enum배열을 문자열로 처리해 UnicodeDecodeError; 가짜 ActorID0 때문에146D454의null118→정상ActorID/PM 공급; ActorRef ID를+8에 쓴 오프셋 오류로3C8829C null68→실제+10의−1 적용; 코드 emitter를 E2 문자열 발생의 대체로 본 기대식 실패→실제 원본 두 경로를 모두 보존. 첫 directqueue fixture의 빈 head0도 native loader sentinel self로 교정한 뒤 전체 재실행했다. 실패를 원본 게임의 결함으로 해석하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

whole L98/L186의 질문은 위 원본 연결로 답했으나 아래를 전체 확정으로 승격하지 않는다.

- 실제 full manager/typed config loader·부팅·리소스 startup 및 유효 ActorRef 위치 행렬: 27B5980,279EC14 visitor,27B5640,0F555C4 전체 생성 연결 필요.
- 비어 있지 않은 그룹/지연 억제·유효 참조 pool lifecycle:27B7938/27B84E0/12D7C64 새 연결 실행 필요. 다른 고정 질문에 합치거나 새 분모로 만들지 않는다.
- 정적 코드 emitter 바닥 회전행렬58237B0의 startup: 기존 impl/fxL123 미확정 유지. 이번 실행에서0이었던 BSS를 원본 기본회전으로 단정하지 않는다.
- 최종 XLink emission·VAT·GPU·오디오 믹서와 거리감쇠 전체는 다른 inventory 질문이다. native요청이 맞는 사실을 실제 화면/소리의100% 재현으로 승격하지 않는다.

**2026-10-03 r8 후속 정정 [판독]+[실행]**: 이 문서의58237B0 정적초기화 미확정은 [floor_fixed_rotation.md](../effect_sound/floor_fixed_rotation.md) §3–10으로 해소했다. 원본124F5F0가init_array2692에등록되어단위3×3을만들고,속도0 착탄행렬1024건/초기화128건13440f32 모두일치. 기존초기화전 fixture0은원본default근거가아니며전체GPU/부팅검증주장없음.
