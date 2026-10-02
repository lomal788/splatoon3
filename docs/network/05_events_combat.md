# 05. 이벤트: 탄 복제·피격 권한·도색·게임 흐름

[목차](network.md)

## 1. 개요

순간 동작은 이벤트로 보냅니다. 핵심은 세 가지입니다.

1. **탄**: 넷 객체가 아닙니다. 발사자 기기만 `spl::PlayerNetEvent::Bullet*`를 보내고, 받는 기기는 같은 발사 함수로 **복제 탄을 자기 쪽에서 시뮬레이션**합니다.
2. **피격**: 맞았는지는 공격자 기기의 탄 시뮬레이션이 판정합니다. **플레이어**가 맞으면 공격자 기기가 `PlayerNetEvent::Attack`을 보내고 **피해자를 조작하는 기기만** HP를 줄입니다. 쓰러지면 그 기기가 `PlayerNetEvent::TroubleDie`로 알립니다. **오브젝트**(비컨·스프링클러 등 `spl:DamageHelper`를 가진 액터)는 맞힌 기기가 `spl::AttackEvent`를 보내고 **모든 기기가 각자** HP 홀더에 적용합니다 ([../combat/player_life.md](../combat/player_life.md)).
3. **게임 흐름·모드**: 세션 마스터 쪽 Referee 이벤트(`SessionMasterOrEvent`), 시작 시각 이벤트.

## 2. 자료

- 비트 배치: `analysis/network/bitlayout.txt` (이벤트별 `오프셋:비트(헬퍼)`)
- hash 사용 위치: `analysis/network/hashuse_byfunc.txt`, vtable GOT 사용처: `vtable_got_users.tsv`
- 디컴파일: `net_core.c`(DamageHelper 수신 0x7101e421a4, HitEffect 0x71027b7938, StageBullet 0x71018b78f0), `net_player.c`(AttackEvent 송신 0x7101e4476c, 디코드 0x7101e441b8, PlayerNetEvent::Attack 송신 0x7102496b24, 플레이어 이벤트 처리 0x71024c17d8), `net_send.c`(송신 0x71018b7f30, StageBullet 처리 0x71018b8420), 슈터 발사·수신은 [camera] 의 `analysis/decomp/camera/batch1.c`(0x7102583008, 0x71025817c8, 0x7102581ccc, 0x7102586af0)

## 3. 탄 복제 흐름 [판독]

```
[발사자 기기]  슈터 발사 0x7102583008
   로컬 탄 생성: 0x71025817c8 / 0x7102581ccc (x1 = 발사 문맥, w5 = 1)        // 0x7102583ca8, 0x7102583cd8
   이벤트 구성: 스택에 PlayerNetEvent::BulletShooter (GOT 0x7105798fe0)
       +0x20..+0x28 발사 위치(Q17), +0x2c 속도(VEL41), +0x38 값(11비트, q/256),
       +0x3c u4, +0x40 bool                                                   // 0x71025841c0~0x7102584200
   송신: 0x71018b7f30(sender = 탄 관리자 this+0x178+0x20?, &evt, lifeNumber = owner+0x28 & 0xF)
       sender 모드 0 → 소유 플레이어 기기에서만 큐잉
[받는 기기]  무기 갱신 0x7102586af0
   소유자 replica 의 수신 큐에서 hash 0xbc4e7627 항목 → 0x71018b84d4 로 (evt, frame, life) 디코드
   life != 소유자 현재 LifeNumber 이면 버림
   복제 탄 생성: 같은 함수(0x71025817c8/0x7102581ccc) 를 x1 = NULL, w5 = 0, w6 = 송신 프레임 으로 호출
```

- 받는 기기의 복제 탄은 양자화된 시작 위치·속도로 원본과 같은 탄 물리를 돌립니다.
- **송신 프레임(`w6`)의 용도 = 탄 난수 시드, 지연 보정(앞당기기) 없음 [판독]**. 발사 함수 0x71025817c8은 `w6`을 생성정보 채우기 0x71025823b0의 `w7`로 넘기고(`mov w7, w8` @0x710258195c), 여기서 생성정보 `+0x64`에 저장합니다(`str w23, [x19,#0x64]` @0x7102582868). 로컬 발사도 같은 자리에 `max(GameFrame, 0)`(발사 시점)을 넣고, 이 값은 이벤트 헤더 GameFrame과 같은 프레임 값입니다(같은 갱신 안에서 큐잉). 생성정보 `+0x64`를 읽는 곳은 바이너리 전체에서 `[x,#0x108]` 다음 `[..,#0x64]` 패턴 79곳이며, 분류하면 (a) 탄 관리자 `+0x120`과 더해 sead::Random 시드를 만드는 곳 32곳(예: 슈터 시작 0x710173c5fc `seed = mgr+0x120 + 생성정보+0x64`), (b) 자식 탄 생성정보에 그대로(또는 오프셋을 더해) 복사하는 곳, (c) 두 번째 직렬화 경로(0x71016447d8, u32로 기록)입니다. `GameFrame − 생성정보+0x64`처럼 경과 프레임을 계산해 복제 탄을 미리 진행시키는 코드는 이 79곳과 GameFrame GOT 참조(탄 코드 범위)에서 찾지 못했습니다. 즉 **복제 탄은 수신한 프레임부터 처음 위치에서 시뮬레이션을 시작하고(전송 지연만큼 늦게 보임), 흩어짐 난수는 발사자와 같습니다** [판독 — 탐색 범위 내 부재]. 하위 탄 생성(0x7101648824)은 자식 생성정보 +0x64에 그때의 GameFrame을 넣으므로, 복제 쪽 자식 탄의 시드는 발사자와 다를 수 있습니다 — 영향 범위는 [bullet] 담당 **[미확정]**.
- 탄 이벤트 공통 헤드(`PlayerNetEvent::BulletBase` 103비트) = 위치 Q17×3 + VEL41 + 11비트 값. 무기별 추가 필드는 아래 표.
- 탄 액터가 넷 컴포넌트를 갖지 않는 것은 데이터로 확정입니다([02](02_replica_model.md#44-데이터-표본-데이터)).
- 별도 전역 레플리카 `StageBullet`(Anyone, 수신 큐 64)과 `spl::BulletNetEvent::SpawnWallDrop`(199비트, 벽 잉크 방울 생성)이 있습니다. 탄 관리자(싱글턴 `*0x7105850620`, 초기화 0x71016e2fd4)가 이 레플리카를 만들고, 매치 공용 시드 a..d와 `+0x120 = 13a+59b+71c+97d`를 탄 난수 시드로 둡니다 **[판독]**. 시드 원천은 아래 §3.1처럼 **세션 쪽에서 생성해 `spl::OnlineVersusSetting` 이벤트로 배포하는 매치 설정의 RandomSeed0~3**입니다(이벤트 내용·생성은 [판독], 로비 → 대전 설정 객체(`G+0xd0` 쪽) 복사는 [판독+실행], `G+0xd0 → G+0xc8` 한 단계만 [추정]).

### 3.1 매치 공용 시드 — 대전 설정과 `OnlineVersusSetting` [판독/실행]

**대전 설정 객체** = `[[0x71058e42f8]+0xc8]+0x6548` (0xc0 B, vtable 0x710566c478, 생성 0x71029e04fc, 소유 객체 생성자 0x7102ae7568의 0x7102ae85d8에서 할당). 필드는 BYML 키로 채웁니다(로더 vtable 슬롯 16 = 0x7102aeb310 이름 키, 슬롯 17 = 0x7102aeb890 해시 키, 슬롯 18 = 0x7102aebe10 BYML 쓰기, 슬롯 7 = 0x7102aeac8c 복사). 게임 설정 싱글턴 G = `*0x71058e42f8`은 같은 종류의 설정 묶음(0x6570 B)을 `+0xc8`(게임이 읽는 쪽)과 `+0xd0`(온라인 로비가 쓰는 쪽) 두 개 가집니다(아래 복사 경로):

| 오프셋 | BYML 키 | 기본값(생성자) |
|---|---|---|
| +0x3c | `Rule` | — |
| +0xa0 | `Time` | 180 |
| +0xa4/+0xa8/+0xac/+0xb0 | `RandomSeed0`~`RandomSeed3` | 1, 0, 0, 0 |
| 그 밖 | `Mode`, `MatchMode`, `BattleId`, `TeamColorHash`, `BgmId`, `IsBankaraPromotion`, `IsFastEnter`, `IsSubGearSkillDeactivated`, `FestSpecialMatchType` | |

탄 관리자 초기화 0x71016e2fd4가 `[[*0x71058e42f8]+0xc8]+0x6548`의 +0xa4..+0xb0을 a..d로 복사합니다(객체가 없으면 1,2,3,4) **[판독]**.

**`spl::OnlineVersusSetting`**(이벤트, 등록 721~751비트, 객체 592 B, 생성 0x7102d6394c, vtable 0x71056a1fa0, write 0x7102fa1aa4, read 0x7102fa1d18): write 순서 `+0x20` 7비트, `+0x30` 문자열 64 B(512비트), `+0x80` 3비트, `+0x84` 3비트, `+0x88` s32(32), `+0x90` 참가자 배열(개수 4비트 + 최대 10개 × 3비트, 빈 칸 0 패딩, 0x7102fa1c0c), **`+0x238/+0x23c/+0x240/+0x244` u32 ×4**, `+0x248`/`+0x24a` u16 ×2 **[판독]**. 생성자 기본값은 `+0x88` = 180, `+0x238` = 1, 나머지 0으로, 대전 설정 객체의 `Time`(180)·`RandomSeed0..3`(1,0,0,0) 기본값과 같고 필드 순서도 BYML 키 순서(Mode, BattleId, Rule, MatchMode, Time, RandomSeed0~3, TeamColorHash, BgmId)와 맞습니다.

**생성·송신** 0x7102d5e478(로비/매칭 쪽 객체 갱신): 송신자 모드 검사(0 소유 플레이어, 1/4 세션 마스터 판정 `넷관리자+0x58 vt+0x90`, 2, 3)를 통과한 기기가 스택에 OnlineVersusSetting을 만들고 **전역 xorshift128 난수기(`*0x71057906a0`, sead::Random 상태 4워드)를 4번 돌린 값을 `+0x238..+0x244`에 넣은 뒤** 이벤트로 큐잉합니다(0x7102d5e724 이후, `uStack_228..uStack_21c`). 같은 자리에서 `+0x88` = 3600(모드 값 & ~1 == 2) / 300 / 180 을 정합니다 **[판독]**. 받는 쪽 0x7102d61700은 해시 0x2970fcdb 항목을 디코드해 자기 객체 `+0x3e0`에 복사하고 `+0x630 = 1`로 표시합니다 **[판독]**.

결론: 탄 난수 시드 a..d는 **한 기기(송신 권한 기기, 세션 마스터로 추정)가 무작위로 만들어 이벤트로 모든 기기에 배포한 값**이고, 모든 기기가 같은 `13a+59b+71c+97d`로 탄 흩어짐을 계산합니다.

**이벤트 → 대전 설정 복사 경로 (3차 해소) [판독 + 실행]**: 이전 판은 "이벤트 → 대전 설정 객체(+0xa4..)로 옮기는 코드를 찾지 못함(기본값·순서 일치로 [추정])"이었습니다. 받은 이벤트는 로비 객체(이하 L) +0x3e0에 복사되므로(OVS +0x238 → **L+0x618**), `ldr #0x618..#0x624 → str #0xa4..#0xb0` 쌍을 검색해 찾았습니다. 함수 **0x7102d60098**(L 갱신, 함수 시작은 프롤로그로 확인 — 전체 분석 표에는 0x7102d5dc64에 묶여 있음):

```
if L+0xa44(f32) > 600.0: 0x710126a1b0(*0x71058e8604)        // 타임아웃 처리
if L+0x630 (OnlineVersusSetting 받음):
    G = [*0x71058e42f8] ; H = [G+0xd0]                        // 다음(대기) 게임 설정 묶음, 잠금 G+0xf8
    V = [H+0x6548]                                            // 대전 설정 객체
    V+0x40 = L+0x84                   V+0x38 = L+0x460 (OVS +0x80, 3비트)
    V+0x3c = L+0x464 (OVS +0x84 = Rule) V+0xa0 = L+0x468 (OVS +0x88 = Time)
    V+0xa4..+0xb0 = L+0x618..+0x624   (OVS +0x238..+0x244 = RandomSeed0..3)
    H+0x6508 = GameNet(*0x7105825fd0)+0x1c8
    V+0xb6 = L+0x628 (OVS +0x248, u16)  V+0xb4 = L+0x62a (OVS +0x24a, u16)  V+0xba = L+0xa0 (byte)
    0x7102d63a64(L, sp, 0) ...
elif L+0x8d0 (코옵 설정 받음): 같은 방식으로 [H+0x6550] 코옵 설정에 복사
```

원본 실행(`network_rest_verify.py` [5], 0x7102d601a8 직전까지, 잠금 등 외부 함수는 즉시 반환): 시드 4개·Rule 5·Time 300·u16 2개·GameNet+0x1c8이 위 위치로 그대로 복사됨을 확인했습니다. 따라서 OVS 필드 대응도 확정됩니다: **+0x80 → 설정+0x38, +0x84 → Rule(+0x3c), +0x88 → Time(+0xa0), +0x238..+0x244 → RandomSeed0..3, +0x248 → +0xb6, +0x24a → +0xb4**.

남은 한 단계 **[미확정]**: 로비는 게임 설정 묶음 `G+0xd0`에 쓰고, 탄 관리자 초기화(0x71016e2fd4)·PlayerNetState 송신(Rule)은 `G+0xc8`을 읽습니다. 두 칸은 같은 클래스(0x6570 B, 생성 0x7102af0f4c, vtable 0x710566c038, 둘 다 0x7102af0c14에서 할당)의 별개 객체이고, 포인터 교환 코드는 없습니다(`ldp/stp #0xc8` 교차 검색 0건). `+0xd0 → +0xc8` 내용 복사는 묶음 vtable 슬롯 7(0x7102ae5810, 하위 객체마다 vt+0x38 복사)로 이뤄질 것으로 보이나 호출 지점을 찾지 못했습니다 **[추정]**.

## 4. 피격·데미지 권한

### 4.1 AttackEvent (115비트) [실행 + 판독]

| 오프셋 | 비트 | 형식 | 비고 |
|---|---|---|---|
| +0x20 | 33 | ACC33 | 넉백 벡터로 추정 |
| +0x2c | 3 | u | |
| +0x30 | 17 | v+1 | |
| +0x34 | 3 | v+1 | |
| +0x38~ | 22 | 내장 `spl::DamageReason` (+0x58 u2+1, +0x5c u4, +0x60 u16+1) | DamageReason 타입 단독도 22비트 |
| +0x68, +0x69 | 1, 1 | bool | |
| +0x6c | 31 | u | |
| +0x70 | 4 | u | |

여러 대상용 `AttackEventMulti4/8/16`(119/123/131비트)이 있습니다.

### 4.2 흐름 [판독]

> **정정(2026-10-02, [life])**: 이전 판에는 "`spl:DamageHelper`는 탄 쪽 헬퍼이고 AttackEvent 콜백이 HP를 줄이는 대상은 미확정, 피해자 기기가 자기 플레이어에 적용하는 것으로 추정"이라고 적었습니다. 다시 추적한 결과 (1) `spl:DamageHelper`는 **피해를 받는 액터의 컴포넌트**(HitPointHolderArray의 HP 홀더 목록을 가짐, 플레이어 본체에도 +0xa6a0)이고, (2) AttackEvent는 그 오브젝트 HP를 **모든 기기가 적용**하는 경로이며, (3) **플레이어 HP는 AttackEvent가 아니라 `PlayerNetEvent::Attack`으로 전달되어 피해자 조작 기기만 적용**합니다. 근거는 아래 주소입니다.

**오브젝트 (`spl:DamageHelper`, vtable 0x71055ea2e8)**

```
[맞힌 기기]  탄 OnHit → 대상 액터 DamageReceiver → 리스너 0x7101e4476c (DamageHelper 쪽)
   리시버 이름 → 대상 비트마스크, 대상 HP 홀더마다 0x7101a89524(누적) / Cure면 0x7101a89790
   넉백 ≠ 0 또는 dmg ≥ 1 이면 대상 수(+0x30)에 따라 AttackEvent / Multi4/8/16 송신 (넷 객체 +0x208)
[모든 다른 기기]  DamageHelper 슬롯 20 = 0x7101e421a4
   대상 수 ≤1 → hash 0xf429516a(AttackEvent), ≤4 → Multi4, ≤8 → Multi8, ≤16 → Multi16
   (evt, frame, life) 디코드, life == 소유자 LifeNumber 인 것만
   넉백 ×3600 변환 후 functor(vtable 0x71055ea5e8) 슬롯0 = 0x7101e45f9c 호출
     → 마스크 비트의 대상 홀더(대상+0x58)에 0x7101a89524(홀더, ev, 1), 추가 리스너 통지, 넉백 메시지
[매 프레임]  DamageHelper 슬롯 23 = 0x7101e43218 → 대상 홀더마다 0x7101a8905c(dt=+0xd8, 1/60)
```

**플레이어**

```
[공격자 기기]  피해자 레플리카의 DamageReceiver → 플레이어 리스너 0x71024632ec
   (같은 팀이면 끝, 피해자 무적이면 dmg 0, 넉백 /3600·최대 0.48)
   메시지 0x6c2b6a04 를 공격자 플레이어에 게시 → 0x7102496b24 → 조작 기기이면 PlayerNetEvent::Attack 큐잉
   피해자가 이 기기 조작이 아니면 예측 HP(PlayerDamage+0xee4)만 감소 (처치 연출 예측)
[피해자 조작 기기]  원격 플레이어 이벤트 처리 0x71024c17d8 → 대상 플레이어에 메시지 0x6c2b6a05
   → 0x7102497264: 쓰러짐 중이면 무시, payload 생명 번호 != 자기 값이면 무시,
     조작 기기이면 0x71024b0c70 (아머·같은팀 검사 후 PlayerDamage+0x30 HP 홀더에 누적)
[매 프레임, 조작 기기]  0x7102483134 → 0x7101a8905c(1/60, PlayerDamage+0x30): 누적을 HP에 반영, 회복
   HP < 1 이면 사망 시작 0x710245ff9c, PlayerNetEvent::TroubleDie 송신
[다른 기기]  PlayerDamage.hp ← 원격 상태로 받은 값(PlayerDamage+0xee0, 0x7102475a54가 기록)
```

`PlayerNetEvent::Attack` payload(메시지 구조 기준, 송신 0x7102496b24가 그대로 복사): +0x40 u4 **피해자** 플레이어 번호(리스너가 피해자 액터+0x798로 채움), +0x44 u4 피해자 생명 번호, +0x48 u17 데미지, +0x4c u3 모드(0 일반, 1 별도 홀더), +0x50..+0x58 넉백(×1/3600 된 값), +0x5c u3 팀, +0x61 bool 크리티컬, +0x64..+0x6c DamageReason. 이벤트 비트 배치(+0x20 u4 … +0x3c bool)와 순서가 맞습니다 **[판독, 필드 대응은 순서 기반]**. 받는 쪽(0x71024c17d8)은 첫 u4로 대상 플레이어를 찾고, 메시지 0x6c2b6a05의 +0x40에는 보낸(공격자) 플레이어 번호(+0x798)를 넣습니다 **[판독]**.

### 4.3 관련 이벤트

| 이벤트 | 비트 | 필드 | 송신 쪽 |
|---|---|---|---|
| `PlayerNetEvent::TroubleDie` | 78 | 위치 Q17×3, +0x2c u4 마지막 공격자 번호, +0x30 bool, DamageReason(+0x58 u2, +0x5c u4, +0x60 u16) | 피해자 조작 기기(0x7102483134 안, HP<1 사망 판정 직후 조작 기기 확인, GOT 사용 0x71024894cc) **[판독]** |
| `PlayerNetEvent::Attack` | 141 | +0x20 u4 피해자 번호, +0x21 u4 피해자 생명 번호, +0x24 u17 데미지, +0x28 u3 모드, +0x2c/+0x30/+0x34 u29×3 넉백, +0x38 u3 팀, +0x3c bool 크리티컬, DamageReason | 공격자 기기(메시지 0x6c2b6a04 → 0x7102496b24, 조작 기기 확인 후 큐잉, 리플레이 기록 0x7102b1f190 에도 전달). **플레이어 피해 전달용** — 피해자 조작 기기가 0x7102497264로 적용 **[판독]** |
| `PlayerNetEvent::AssistKill` | 59 | 위치, u4, u4 | |
| `PlayerNetEvent::Revival` | 110 | 위치, u16, DIR25, u9, u9 | |
| `PlayerNetEvent::TroubleAirFall` / `WaterFall` | 62 / 71 | 위치, u11 (+u9) | |
| `spl::ReceiveDamage` | 39 | u32, u7 | 오브젝트 피해(잉크레일 등 사용처 0x7102212b64) |
| `spl::HitEffectNetEvent` | 99 | 위치, DIR21, u3, u4, u16, u4 | 전역 `HitEffect` 레플리카(Anyone). 피격 이펙트 표시 전용, 1/60초 감소 타이머로 수명 관리(0x71027b7938) |

## 5. `PlayerNetEvent` 전체 (82종)

`bitlayout.txt`에서 모두 합계 일치(`DokanWarp_Start`·`BulletSpMultiMissile` 제외: 각각 133비트·76~355 가변). 형식 약어는 [03](03_serialization.md). `P`=위치 Q17×3(51비트), `V`=VEL41, `D25`/`D21`=방향.

| 분류 | 이벤트(비트) | 추가 필드(BulletBase 103 이후 또는 전체) |
|---|---|---|
| 메인 탄 | BulletShooter 108, BulletSpChariotShooter 108 | u4, bool |
| | BulletSpinner 132 | u4, u25 |
| | BulletManeuver 109 | u4, bool, bool |
| | BulletCharger 118 | u12, u3 |
| | BulletSaber 107 / BulletSaberSlash 77 | bool+u3 / (P, D25, bool) |
| | BulletSlosher 257 | P, D25, V, D25, P', u17, bool, D25, u10, u11 |
| | BulletRoller 191 / BulletBrush 192 | P, D25, V, D25, D25, u10, bool×3, u11 / (Roller 형식 191 + bool) |
| | BulletStringer 181 | P, D25, u20, u12, D25, u10, D25, u10, u3 |
| | BulletShelterShot 103, BulletShelterCanopyPurge 103 | — |
| 서브 | BulletBomb 103, BulletBombCurling 112(+u9), BulletBombRobot/Torpedo/Sprinkler/Shield 107(+u4), BulletBombFizzy 106(+u3), BulletBeacon 113, BulletTrap 92, BombFizzyBurstNum 2 | Beacon/Trap: u4, u16, P, D21(, D21) |
| 스페셜 탄 | BulletSpSuperShot/UltraShot/NiceBall/JetpackLauncher/UltraStampThrow/ChariotCannon/BlowerInhaleFinish/BlowerExhaleWait 103, BulletSpInkStorm 105(+u2), BulletSpShockSonar 105(+u2), BulletSpEnergyStand 105(+u2), BulletSpTripleTornado 106(+u3), BulletSpGachihoko 115(+u12), BulletSpBlowerInhale 111(+u4,u4), BulletSpBlowerExhale 115(+u12), BulletSpGreatBarrier 128, BulletSpMultiMissile 76~355, BulletClam 154(+P') | |
| 스페셜 상태 | PerformSpecial 51(P), StartSpUltraStamp 0, StateSpUltraStamp 8, StartSpNiceBall 43, UpdateSpNiceBall 40, SpSuperHookStart 67, SpSuperHookShot 79, SpSuperHookAttack 95, StartSpMicroLaser 0, SpJetpackStart 86, SpJetpackBoost 0, StartMarking/StartMarkingDirect 22, FinishMarking 0, StartArmor 48, GetEnergyStand 22, ChariotStart 19, SkewerStart 95, SkewerOmen 18, SkewerPreBurst 38, SkewerAttackPlayer 7 | |
| 이동 | SideStepStart 124, ForwardRollStart 25, DokanWarp_Start 133 / _ReDefine 67 / _End 0 | |
| 생사 | TroubleDie 78, TroubleAirFall 62, TroubleWaterFall 71, Revival 110, AssistKill 59, Attack 141 | §4.3 |
| 모드·기타 | ReqGetGachihoko 0, ReqGetTricolNoroshi 0, DirectBankClam 0, TeamSignal 5, Emote 10, RequestAttachCustomPart 21, CoopRescued 4, CoopRoundSetup 2 | |

`Req*` 이벤트(0비트)는 세션 마스터가 상태를 가진 모드 오브젝트에 대한 **요청**입니다(SenderPolicy `SessionMasterOrEvent`) **[추정 — 이름·정책]**.

## 6. 도색·게임 흐름 이벤트

| 이벤트 | 비트 | 레플리카 |
|---|---|---|
| `spl::paint::FloorPaintEvent` | 133 | `PaintRequest`(Anyone, 큐 256) |
| `spl::paint::ObjPaintEvent` / `ColPaintEvent` | 154 / 153 | 〃 |
| `spl::paint::MultiTargetPaintEvent` | 50 | 〃 |
| `game::GameFlowNodeNetEvent` | 5 | 게임 흐름 노드 번호 |
| `game::GameFlowPulseDelayNetEvent` | 8~104 (write는 항상 5+3+4×24 = 104) | 노드 5비트, 지연 항목 수 3비트(≤4), 항목 `_Delay` 24비트(u5 + u19) |
| `spl::VersusStartClockEvent` | 32 | writer `+0x70`(u32) 1개 — 시작 시각 |
| `spl::VersusTransitionNetEvent` | 1024 | 128바이트 문자열 |
| `spl::VersusRefereeGachiGameFinishNetEvent` 등 Referee | 가변 | 세션 마스터 판정 |

도색 이벤트 송신 [판독]: 도색 요청 함수들(0x7102c449f0 접촉 도색, 0x7102c44ca4·0x7102c45d1c 바닥/대상 도색)은 요청 구조를 만든 뒤 **먼저 자기 기기에 적용**(0x7102c3f0c4)하고, 도색 관리자(`*0x7105790c60`)의 `PaintRequest` 레플리카(+0x2e8)가 있고 매치 상태(`[*0x7105798658]+0xc8`) ≠ 2이면 송신 함수 0x7102c42330을 부릅니다. 0x7102c42330은 `GameNet+0x195 == 0`이면 아무것도 안 하고 성공, 세 번째 인자(호출자 플래그의 반대)가 1이면 네트워크 대신 0x7101323ea8 경로로 넘기고, 아니면 이벤트 송신 0x71018b7f30과 같은 권한 검사(+0x78 비활성, +0x30 모드 switch) 뒤 요청 종류(+0x38: 1 → FloorPaintEvent, 2 → ColPaintEvent, 3 → ObjPaintEvent; MultiTargetPaintEvent는 같은 함수의 다른 분기)에 맞는 `spl::paint::*PaintEvent`를 GameFrame 스탬프와 함께 큐잉합니다. 송신에 성공하면 0x7102c3f4c8을 부릅니다. 즉 **도색 이벤트는 그 도색을 실행한 기기가 보냅니다**. 탄 도색이 발사자 기기에서만 실행되는지(복제 탄도 도색 요청을 하는지)는 탄 쪽 호출 조건이라 [paint]/[bullet] 담당 **[미확정]** — 도색 계산은 [../paint/paint_and_score.md](../paint/paint_and_score.md). 시작 시각 합의(각 스테이션 desired → 세션 마스터가 최댓값을 `VersusSetting` 값 요소에 기록 → 모든 기기가 같은 start로 GameFrame 계산)는 [02 §5.5](02_replica_model.md#55-gameframe-기기-간-동기--netutilframestarter-판독--실행)에서 판독했습니다. `VersusStartClockEvent`(32비트)의 사용처는 아직 보지 않았습니다 **[미확정]**.

## 8. 다른 기능과의 상호작용

- 탄 계산·난수: [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md). 탄 시드는 탄 관리자 `+0x120`, 발사 흔들림 시드는 같은 객체 `+0x124..+0x130`과 GameFrame `+0x148`([camera] 문서).
- 데미지 계산: [../combat/damage_hit.md](../combat/damage_hit.md).
- 이펙트: `HitEffectNetEvent`는 표시 전용.

## 11. 미확정

| 항목 | 다음 근거 |
|---|---|
| ~~AttackEvent 콜백이 HP를 줄이는 기기~~ | **해소**: functor 0x7101e45f9c = 오브젝트 HP 홀더 누적(모든 기기). 플레이어는 `PlayerNetEvent::Attack` → 피해자 조작 기기(§4.2, [player_life.md](../combat/player_life.md)) |
| ~~원격 HP가 담긴 PlayerNetState 필드~~ | **해소 [판독]**: PlayerNetState +0x6c(10비트, 송신 = PlayerDamage+0x7c) → 수신 0x7102475a54가 PlayerDamage+0xee0에 기록, 예측 HP +0xee4 상한도 갱신([04 §4.7](04_player_state.md)) |
| ~~복제 탄 지연 보정(송신 프레임 사용)~~ | **해소 [판독]**: 송신 프레임은 탄 시드(생성정보+0x64)로만 쓰이고 앞당기기 없음(§3). 남은 것: 자식 탄 시드의 기기 간 차이 영향([bullet]) |
| 탄 시드 원천 공유 | **해소 [판독+실행]**: OnlineVersusSetting 이벤트로 배포, 로비 0x7102d60098이 `[G+0xd0]+0x6548`+0xa4..에 복사(§3.1). 남은 것: `G+0xd0 → G+0xc8` 복사 지점, 송신 기기가 세션 마스터인지(송신자 모드 값) |
| ~~`PlayerNetEvent::Attack` 용도~~ | **해소**: 플레이어 피해 전달(§4.2) |
| 도색 이벤트 송신자 | **해소 [판독]**: 도색을 실행한 기기(§6). 남은 것: 복제 탄이 도색 요청을 하는지, 0x7101323ea8 경로의 정체 |
