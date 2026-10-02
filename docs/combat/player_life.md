# 플레이어 생명 흐름 (HP·피해 적용·적 잉크·회복·아머·사망) [life]

Splatoon 3 v0 원본에서 **플레이어가 맞은 데미지가 실제 HP에서 빠지고, 적 잉크에서 조금씩 깎이고, 쉬면 회복되고, 0이 되면 쓰러지기까지**를 정리합니다. 탄이 데미지 값을 정하고 리시버가 배율을 곱하는 단계는 [damage_hit.md](damage_hit.md)에 있고, 이 문서는 그 다음 단계부터 다룹니다.

- 작업 지침: [../../분석.txt](../../분석.txt). 확정 수준 표기: **[실행] [판독] [데이터] [추정] [미확정]** ([README](../README.md)). 이 문서에서 [실행]은 "원본 함수를 unicorn으로 실행"한 것입니다.
- 주소는 main NSO를 0x7100000000에 올린 가상 주소입니다.
- 이름 규칙: 원본에서 확인된 이름은 `spl::PlayerDamage`처럼 원래 철자로, 이 문서가 붙인 이름은 *기울임*(예: *HP 홀더*)으로 씁니다.

상태: **분석 진행 중**. HP 홀더(누적·감소율·회복·클램프)는 원본 실행과 재구현이 일치합니다. 피해 적용 기기, 적 잉크 데미지식, 회복 속도, 사망 판정 조건, 사망 시간 계산은 판독했습니다. 2026-10-02 [respawn] 3차: 사망 대기 → 리스폰 실행(`Revival`) → 리셋(HP 1000·리스폰 무적·ToHumanRespawn 타이머) → `WaitRespawn` → `ToSpawner` 흐름, 리스폰 지점 선택, 모드 보정, 아머 HP 설정자(StartArmor), 무적 판정 각 조건의 출처, 원격 HP 필드를 판독했고, 타이머·리셋·무적 판정은 원본 함수 실행(unicorn)으로 확인했습니다(§6.8~§6.10, §10). 남은 것은 §11. 웹 구현은 없습니다.

---

## 1. 기능 개요와 사용자에게 보이는 동작

1. 플레이어 최대 HP는 **1000(=100.0)** 입니다 [판독]. 데미지·HP는 0.1 단위 정수입니다([damage_hit.md §4.1](damage_hit.md#41-splbulletshooterdamageparam-gameparametertable-damageparam)).
2. 한 프레임에 맞은 데미지는 바로 HP에서 빼지 않고 *누적값*에 모았다가, 그 플레이어를 조작하는 기기의 프레임 갱신에서 한 번에 뺍니다 [판독+실행].
3. 맞으면 **60프레임** 동안 회복하지 않습니다. 그 뒤 초당 **125**(0.1 단위, 즉 12.5 HP/초), 잉크에 숨은 상태 등에서는 초당 **1000**(100 HP/초)씩 회복합니다 [판독]. 회복 상태 조건의 의미는 [추정].
4. 적 잉크를 밟고 있으면 매 프레임 `int(OpInk_DamagePerFrame × 적잉크비율 × 1000)`씩 깎입니다. 기본값이면 프레임당 3(=0.3 HP). 단, 적 잉크만으로는 HP가 `1000 − OpInk_DamageLmt×1000`(기본 600=60.0) 아래로 내려가지 않습니다 [판독, 재구현 계산].
5. 기어 OpInkEffectReduction의 `OpInk_ArmorHP`(0/26/39)는 HP가 아니라 **적 잉크에 들어간 뒤 데미지가 0인 프레임 수**입니다. 적 잉크를 벗어나 60프레임이 지나면 한 프레임에 1씩 다시 찹니다 [판독].
6. HP가 1 미만이 되고 다른 쓰러짐 타이머가 없으면 쓰러집니다. 사망 대기 시간 = `Dying_AroundFrm + Dying_ChaseFrm(+모드 보정) + 30` 프레임입니다(기어 미적용이면 90+270+30=390) [판독]. 쓰러짐은 그 플레이어를 조작하는 기기가 `PlayerNetEvent::TroubleDie`로 알립니다 [판독].
7. 다른 플레이어를 맞힌 기기는 상대 HP를 직접 줄이지 않습니다. 맞힌 사실을 `PlayerNetEvent::Attack`으로 보내고, **피해자를 조작하는 기기가 HP를 줄입니다**. 맞힌 기기는 화면 표시용으로 *예측 HP*만 따로 줄입니다 [판독].
8. 사망 대기가 끝나면 그 플레이어를 조작하는 기기가 리스폰을 실행해 `PlayerNetEvent::Revival`을 보내고, 리스폰 지점(팀·순번별 포즈)으로 옮기며 HP를 1000으로 되돌립니다. 대전 기본값(팀별 스폰 관리자)으로 리스폰 프레임 R의 14프레임 뒤에 `ToHumanRespawn`을 요청하고, R+58까지 리스폰 무적 카운터, R+59까지 리스폰 후 타이머가 남아 그동안 무적입니다. 그 뒤 `WaitRespawn`에서 리스폰 착지(발사) 단계가 시작되면 `ToSpawner` → `Injection_Pre`로 넘어갑니다 [판독 + 원본 실행, 발사 입력 쪽은 미확정](§6.8).
9. 아머는 원인 번호(1~5)별로 걸리고 작은 번호가 우선합니다. 리스폰 착지 처리는 원인 3으로 HP 300(=30.0) 아머를 겁니다 [판독](§6.9).

## 2. 분석 대상 원본·자료 위치

| 항목 | 값 |
|---|---|
| 원본 | Splatoon 3 v0, main NSO(심볼 없음) |
| 디컴파일 | `analysis/decomp/life/batch1.c`(58함수), `batch2.c`(9), `batch3.c`(2), `big1.c`(0x7102483134 플레이어 프레임/넷 갱신, 8000줄). 기존 것: `player/player_main_calc.c`(0x7102475a54), `player/player_misc1.c`(0x710245ff9c), `player/playerparam_gear.c`(0x710266c838), `network/net_player.c`(0x7101e4476c, 0x7102496b24, 0x71024c17d8), `network/net_core.c`(0x7101e421a4) |
| 상수 블록 | 플레이어 상수 구조체 `0x71058bbb78`(정적 초기화 0x7102455db0, 값은 `analysis/player/bss_consts_58bb000.json` — [player] `player_initemu.py`로 원본 정적 초기화를 실행해 얻은 값) |
| 도구 | `web/tools/life_hp.py`(재구현), `life_emu.py`(원본 unicorn 실행 비교), `life_scan.py`(즉시 오프셋 LDR/STR/MOVZ 스캔), `life_msgscan.py`(32비트 메시지 ID 구성 위치) |
| 도구([respawn]) | `web/tools/respawn_emu.py`(사망→리스폰 타이머·리셋·무적 판정 원본 실행), `respawn_addscan.py`(ADD Xd,Xn,#imm 스캔 — 하위 구조체 포인터 전달 위치), `respawn_sender_vt.py`(피해 송신자 인터페이스 후보 vtable 스캔, 후보가 너무 많아 결론에 쓰지 않음) |
| 디컴파일([respawn]) | `analysis/decomp/respawn/batch1.c`(스폰 관리자 0x71027ca08c/0x71027c8c98/0x71027c95f0, 0x710249e0fc, 0x71024cb4cc, `VersusReferee` vt+0x50 0x710303f4e4, 트리컬러 파라미터 0x710305ebcc/0x710305f300), `batch2.c`(0x7103042c40). 기존: `gauge/gauge_batch1.c`(0x71024a2c98, 0x710249cb60), `move/move_helpers.c`(0x710243c1c4) |
| 결과([respawn]) | `analysis/respawn/emu_respawn.txt` |
| 결과 | `analysis/life/emu_hp_holder.txt`(원본 실행 비교 9,600프레임) |

## 3. 진입점과 전체 호출 흐름

### 3.1 객체 관계 [판독]

기준 객체 *플레이어 본체* = `PlayerBehavior+0x108`(0xac80 B, vtable 0x7105632a60, [player] 문서). 여기서 쓰는 컴포넌트와 하위 구조체:

| 본체 오프셋 | 대상 | 비고 |
|---|---|---|
| +0xa8a0 | `spl::PlayerDamage`(0xf00 B, vtable 0x71056347b0, 생성 0x7102506884) | +0x30에 *HP 홀더* |
| +0xa8c0 | `spl::PlayerArmor`(0xf38 B, vtable 0x7105632640, 생성 0x710243b84c) | +0x38에 아머용 *HP 홀더* |
| +0xa7c0 | `spl::PlayerCoopZombie`(0xef8 B, vtable 0x7105634680, 생성 0x7102505d9c) | +0x30에 *HP 홀더*. 연어런 계열로 추정 |
| +0xa688 | `spl::PlayerStepPaint`(0xf0 B, vtable 0x710563eb68, 생성 0x710268b25c) | 발밑 잉크·적 잉크 데미지. +0xb8 = PlayerDamage(슬롯25 0x71024319f0이 바인딩), +0xc8 = PlayerParam |
| +0xa658 | `spl::PlayerParam` | 기어 계산 결과(+0x110 OpInk_DamagePerFrame 등, [player] gear_skills) |
| +0xa6a0 | `spl:DamageHelper` | 오브젝트용 HP 홀더 목록을 갖는 범용 컴포넌트(§3.6) |
| +0xaf0 | 플레이어 DamageReceiver 포인터 | 아머가 +0x128(열 이름)을 `"Default"`/`"NiceBall_Armor"`로 바꿈(0x710243ba44) |
| +0xd58 | *쓰러짐 상태* 구조체 T | T+8 사망 대기, T+0x88/+0x98/+0xb4 다른 쓰러짐 타이머(낙하·수몰 추정), T+0 리스폰 후 타이머, T+4 ToHumanRespawn 대기, T+0xf4 리스폰 무적, T+0x148 리스폰 지점 포즈, T+0x178(=본체+0xed0) *리스폰 착지(RespawnLand)* 구조체. 필드 표는 §6.8.1 |
| +0xf34 | *리스폰 착지 단계*(= T+0x178+0x64) | 1 = 스폰 지점 대기, 2~4 = 발사 진행, 5 = 착지 [판독, 단계 이름은 추정]. 무적·상태 전이·넷 `RespawnLand`가 읽음 |
| +0x10 | 위치(f32×3) | 리스폰 리셋이 리스폰 지점 위치로 덮어씀 |
| +0xe60 | *처치 예측 표시* 구조체 | [0] 타이머(10), [2] 공격자 번호 |
| +0xa4c8 | 플레이어 통계(맞은 데미지 합 등) | |

### 3.2 다른 플레이어에게 맞았을 때 (네트워크 경로) [판독]

```
[공격자 기기]
 탄 OnHit → 0x71012d4adc → 피해자 레플리카의 DamageReceiver
   computeResult 0x7101a86ec0 (배율·팀 판정)  → apply 0x7101a87e24 → 리스너
   플레이어 리스너: 0x7102462df0(모드0) / 0x7102462ea4(모드1) → 0x71024632ec
     1. 같은 팀(info+4 == 피해자 팀)이면 끝
     2. 넉백 v = info.knockback × (1/3600), |v| ≤ 0.48 (특정 상태면 크기 ×8.0 [0x71058bbf60])
     3. 피해자가 무적(0x71024c7624)이면 dmg = 0
     4. 메시지 0x6c2b6a04 를 공격자 플레이어 객체에 게시
          payload +0x40 피해자 번호(액터+0x798), +0x44 피해자 생명 번호(넷 레플리카 +0x28), +0x48 dmg,
                  +0x4c 모드, +0x50..+0x58 넉백, +0x5c 팀, +0x60 송신 여부, +0x61 크리티컬, +0x64.. DamageReason
     5. 피해자가 이 기기 조작이 아니면: 예측만 (§6.6)
        피해자가 이 기기 조작이면: 모드0 → 0x71024b0c70 (§6.3) + 넉백 0x71024c8318
                                   모드1 → 본체+0x93f0 HP 홀더에 직접 누적
 공격자 플레이어 메시지 처리 0x710234f518 case 0x6c2b6a04 → 0x7102496b24
   공격자가 이 기기 조작이고 payload+0x60 이면 PlayerNetEvent::Attack 큐잉(+ 리플레이 기록)

[피해자를 조작하는 기기]
 원격 플레이어 이벤트 처리 0x71024c17d8: Attack 디코드 → 첫 u4(피해자 번호)의 플레이어에 메시지 0x6c2b6a05
   (메시지 +0x40 = 보낸 공격자 번호로 바꿔 넣음)
 0x710234f518 case 0x6c2b6a05 → 0x7102497264
   쓰러짐 타이머(T+8, +0x88, +0x98, +0xb4) 중 하나라도 > 0 이면 무시
   payload+0x44 != 자기 생명 번호 이면 무시 (이전 생명에 대한 공격 폐기)
   이 기기가 피해자 조작 기기이면:
       모드0 → 0x71024b0c70(…, info, dmg > 99998, accumulate=1) + 넉백
       모드1 → HP 홀더(본체+0x93f0)에 직접 누적
   아니면(표시만): 피격 반응 0x71024b1510, 통계 0x7102462f5c
```

### 3.3 적 잉크 [판독]

```
PlayerStepPaint 갱신 0x710268b3b8 (매 프레임)
  발밑 잉크 비율로 상태 S+0x30 결정 (2/3 = 적 잉크 우세)
  상태 2/3 이고 무적 아님(0x71024c7624 거짓):
      dmg = ink_damage(...)   §6.2
      0x71024b9d34(본체+0xa5f9, PlayerDamage, 본체+0xaf0, 본체+0xa4c8, &info)
         조작 기기 확인(§6.7) → 통계 += dmg → 0x71024b0c70(…, info, 0, 1)
  적잉크 무데미지 프레임(S+0xac) 증감  §6.2
```

### 3.4 매 프레임 HP 갱신 [판독]

`0x7102483134`(플레이어 프레임/넷 갱신, 인자 48개, [network]·[gauge]도 디컴파일) 안:

```
if 이 기기가 조작 기기:
    PlayerCoopZombie 활성(+0xeec) → 0x7101a8905c(1/60, Zombie+0x30)
    PlayerArmor 갱신 0x710243b93c   (내부에서 아머 HP 홀더 0x7101a8905c(1/60, Armor+0x38))
    hp0 = PD.hp; 0x7101a8905c(1/60, PD+0x30); 회복량 = PD.hp - hp0
    회복량 > 0 이면 PD+0xef0 += 회복량 (회복 통계), 본체+0xa4c8 두 칸 조정
else:
    PlayerArmor 원격 갱신 0x710243c098
    예측 HP 회복(PD+0xee8 타이머가 끝난 뒤) §6.6
    PD.hp = clamp(PD+0xee0)        // 원격 상태로 받은 HP = PlayerNetState+0x6c (u10) — §6.10
그 뒤: 사망 판정 §6.5 (조작 기기)
```

회복률 설정(매 프레임, `0x71024a2c98` 안 0x71024a4178~0x71024a41a4):

```
PD+0xeec = PD.hp                       // 직전 HP 보관
PD+0x154 (= 홀더+0x124 회복률) = 0x71024591c8(본체+0x784) ? 1000.0 : 125.0     // [0x71058bcccc], [0x71058bccd0]
```

### 3.5 사망 [판독]

`0x7102483134` 4100줄대(big1.c):

```
if T+8 < 1 && T+0x88 < 1 && T+0x98 < 1 && T+0xb4 < 1 && PD.hp < 1 && !(본체+0xf88+0x1c):
    if 액터+0x7b9 == 0 && 전역 0x71058e8784 && 본체+0x92ec(단계) > 0:
        단계 -= 1, HP 재설정 0x71024bf79c (쓰러지지 않음 — 미션 모드 계열로 추정)
    elif 특정 플래그(액터+0x28 비트 11/9, +0x4d4 비트0, +0x4d0==3) 아님:
        사망 시작 0x710245ff9c (§6.5)
        통계 0x7102460808
        조작 기기이면 PlayerNetEvent::TroubleDie 구성·송신
            (위치 = 액터+0x28c..+0x294, u4 = 마지막 공격자 번호(본체+0xaf0+0x10),
             bool = T+7, DamageReason = 마지막 피격 정보)
```

### 3.6 오브젝트(비컨·스프링클러 등)와 `spl:DamageHelper` [판독]

`spl:DamageHelper`(0x220 B, vtable 0x71055ea2e8, 생성 0x7101e3d53c)는 HP 홀더 목록을 가진 범용 컴포넌트입니다(데이터 `HitPointHolderArray`).

| 오프셋 | 의미 |
|---|---|
| +0x30 / +0x38 | 대상 수 / 대상 배열. 대상+0x58 = *HP 홀더* 포인터 |
| +0x50 / +0x58 | 두 번째 목록: 항목+0x58 = DamageReceiver. 슬롯23이 매 프레임 0x7101a86dc8(리시버, dt)로 수신 이력 나이를 늘림(15초에 삭제) **[판독, 2026-10-02 정정]** — [damage_hit.md §6.4.1](damage_hit.md) |
| +0x98 | 리시버 이름 → 대상 비트마스크 트리 |
| +0xd8 | dt(기본 1/60 = 0x3c888889) |
| +0xdc | 활성 플래그(기본 1) |
| +0xe0 / +0xe8 | 추가 리스너 수 / 배열 |
| +0x200 | 액터(넉백 메시지 대상) |
| +0x208 | 넷 레플리카(AttackEvent 송수신) |

```
[맞힌 기기] 리시버 리스너 0x7101e4476c(listener, result, info, sender)
   리시버 이름 → 대상 마스크, 대상마다:
       result == Cure(7) → 0x7101a89790(홀더, info)  (회복)
       아니면 0x7101a89524(홀더, info, 1)   (누적)
   추가 리스너 통지, 넉백이 있으면 액터에 메시지
   넉백 ≠ 0 또는 dmg ≥ 1 이면 AttackEvent(대상 1개)/Multi4/8/16 송신 (+0x208)
[다른 모든 기기] DamageHelper 슬롯20 0x7101e421a4: 받은 AttackEvent → functor 0x7101e45f9c
   마스크 비트의 대상 홀더에 0x7101a89524(홀더, ev, 1), 추가 리스너 통지, 넉백
[매 프레임] 슬롯23 0x7101e43218: 대상마다 0x7101a8905c(+0xd8, 홀더)
```

즉 **오브젝트 HP는 모든 기기가 각자 같은 이벤트를 적용**하고, 플레이어 HP는 **조작 기기 한 곳만** 적용합니다. 플레이어의 `SplPlayer` GPT에는 `HitPointHolderArray`가 없으므로([damage_hit.md §4.10](damage_hit.md#410-hitpointholder-오브젝트-hp-데이터)) 플레이어의 DamageHelper(+0xa6a0)는 HP 대상이 없는 상태로 보입니다 **[추정]**. 이 경우에도 0x7101e4476c가 AttackEvent를 보내는지는 확인하지 않았습니다 **[미확정]**.

## 4. 구조체·필드·상수

### 4.1 *HP 홀더* (기준: 홀더 시작. PlayerDamage+0x30, PlayerArmor+0x38, PlayerCoopZombie+0x30, DamageHelper 대상+0x58→) [판독 + 실행]

초기화 0x7101a88ce0(H, &초기 최대값), 리셋 0x7101a88e1c, 누적 0x7101a89524, 회복 0x7101a89790, 프레임 갱신 0x7101a8905c.

| 오프셋 | 타입 | 이름(웹 권장) | 의미 | writer | reader |
|---|---|---|---|---|---|
| +0x00 | u32 | `flags` | 비트0 HP 음수 허용(하한 −max), 비트1(비트0=0일 때) 감소율로는 1 미만이 안 됨, 비트2 피격·감소 시 회복 대기 재설정. 초기 6 | 초기화 | 갱신, 회복 |
| +0x08 | functor | `onDamage` | 누적 끝에 호출(기본 vtable 0x71055c9798 = 빈 함수) | 초기화 | 0x7101a89524 |
| +0x28 | functor | `onCure` | 회복 끝에 호출 | 초기화 | 0x7101a89790 |
| +0x48 | s32 | `max` | 최대 HP | PlayerDamage 리셋 0x7102506960(1000), 0x71024bf79c(1000/300), 0x710249cb60(1000) | 클램프 |
| +0x4c | s32 | `hp` | 현재 HP | 리셋(=max), 갱신, 회복 | 사망 판정, 적잉크 상한 |
| +0x50 | DamageInfo(0xc8 B) | `pending` | 이번 프레임 누적. +0x50 데미지 합, +0x54 팀, +0x58 공격자 … (가장 큰 단일 히트의 정보) | 누적 | 갱신 |
| +0x118 | s32 | `pendingMax` | 이번 프레임 최대 단일 데미지 | 누적 | 누적 |
| +0x11c | u8 | `hitThisFrame` | 이번 프레임 피격 | 누적 | 갱신 |
| +0x120 | f32 | `drainPerSec` | 지속 감소율(초당) | 플레이어는 쓰는 곳 못 찾음 | 갱신 |
| +0x124 | f32 | `regenPerSec` | 회복률(초당) | 플레이어: 0x71024a41a4 | 갱신 |
| +0x128 / +0x12c | f32 | `drainFrac` / `regenFrac` | 소수 누적 | 갱신, 리셋(0) | 갱신 |
| +0x130 | s32 | `regenWait` | 회복 대기 프레임 | 갱신(=상수 60), 리셋(0) | 갱신 |
| +0x138 | DamageInfo | `lastHit` | 마지막으로 적용된 피격(+0x138 데미지, +0x13c 팀, +0x140 공격자) | 갱신 | 사망 처리 등 |
| +0x200 | 링(용량 8, 항목 200 B) | `damageLog` | 누적 호출 이력 | 누적 | |
| +0x858 | 링(용량 8) | `cureLog` | 회복 이력 | 회복 | |

### 4.2 `spl::PlayerDamage` (기준: PlayerDamage 시작, 0xf00 B) [판독]

| 오프셋 | 의미 | writer | reader |
|---|---|---|---|
| +0x30 | *HP 홀더*(위 표). 따라서 +0x78 = max, +0x7c = hp, +0x154 = 회복률 | | |
| +0xee0 | 원격 HP(다른 기기에서 받은 HP). 출처 = 받은 `PlayerNetState`+0x6c(u10, 송신 측 PD+0x7c) **[판독]** §6.10 | 리셋(1000), 0x7102475a54(원격 상태 반영) | 0x7102483134(원격일 때 hp ← 이것) |
| +0xee4 | *예측 HP*(맞힌 기기가 줄이는 값) | 리셋, 리스너 0x71024632ec, 0x7102475a54, 0x7102483134 | 리스너(≤0이면 처치 표시) |
| +0xee8 | 예측 HP 회복 대기 프레임 | 리스너(=60) | 0x7102483134 |
| +0xeec | 직전 프레임 HP | 0x71024a41a0 | 0x71024a412c(1000 회복 순간 판정) |
| +0xef0 | 누적 회복량 통계 | 0x7102483134 | |
| +0xef8 | 바인딩된 액터 메인 컴포넌트(타입 GOT 0x7105793118; +0x108 본체 → +8 → +0x668 팀) | 슬롯25 0x710235e0f0 | 팀 비교 |

PlayerDamage 슬롯13 `0x7102506960`(리셋): max=1000, hp=clamp(hp), 홀더 리셋, +0xee0=+0xee4=1000, +0xee8=0, +0xeec=1000 **[판독]**.

### 4.3 `spl::PlayerStepPaint` 중 적 잉크 관련 (기준: PlayerStepPaint 시작) [판독]

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x30 | s32 | 발밑 상태. 2/3 = 적 잉크(3은 다른 조건 동반), 0/1/4/5 그 밖 | 0x710268b3b8 | 같은 함수 |
| +0x38 | s32 | 적 잉크 팀(데미지 정보의 팀) | 0x710268b3b8 | 적잉크 데미지 |
| +0x48 | f32 | 적 잉크 비율(평활) | 0x710268b3b8 | 적잉크 데미지 |
| +0xac | f32 | *적잉크 무데미지 프레임* 남은 수 | 0x710268b3b8, 리셋 0x710268d22c(0) | 적잉크 데미지 |
| +0xb0 | s32 | 적 잉크를 벗어난 뒤 재충전 대기(상태 2일 때 60) | 0x710268b3b8 | 같은 함수 |
| +0xb4 | u8 | 적 잉크 지속 중 플래그 | 0x710268b3b8 | |
| +0xb5 | u8 | 상한 처리 사용. **생성자 0x710268b388만 1로 씀**(다른 writer 없음, 주변 함수 스캔) | 생성자 | 적잉크 데미지 |
| +0xb8 | ptr | PlayerDamage | 슬롯25 0x71024319f0 | |
| +0xc8 | ptr | PlayerParam | | |

### 4.4 플레이어 상수(구조체 0x71058bbb78 기준 오프셋) [판독 + 실행(정적 초기화 에뮬)]

| 오프셋 | 주소 | 값 | 쓰임 |
|---|---|---|---|
| +0x1c0 | 0x71058bbd38 | 60 | 회복 대기 프레임(홀더 갱신), 예측 HP 회복 대기 |
| +0x1c4 | 0x71058bbd3c | 10 | 처치 예측 표시 타이머 |
| +0x1c8 | 0x71058bbd40 | 60 | 본체+0xe60[1] 재설정값(무적일 때) |
| +0x1cc | 0x71058bbd44 | 99999 | 즉사급 데미지 기준(이상이면 아머 파괴) |
| +0x1b4 | 0x71058bbd2c | 30 | 사망 대기 추가 프레임 |
| +0x1fc | 0x71058bbd74 | 1000 | 아머 파괴 직후 감산값 |
| +0x200 | 0x71058bbd78 | 800 | 아머 관통 상한 |
| (별도) | 0x71058bc084 / 0x71058bc088 | 60 / 120 | `Scene_Coop`(전역 0x71058e87a4)일 때 사망 대기(Around/Chase) |
| +0x1a0 / +0x1a4 | 0x71058bbd18 / 0x71058bbd1c | 120 / 60 | 리스폰 리셋의 T+0 (스폰 관리자 팀별 아님 / 팀별) |
| +0x1a8 / +0x1ac | 0x71058bbd20 / 0x71058bbd24 | 45 / 45 | T+4 = max(T+0 − 이 값, 1) (팀별 / 팀별 아님) |
| +0x1b0 | 0x71058bbd28 | 35 | 매치 시작 배치(0x71024cb4cc)가 본체+0x920c에 씀 [판독, 의미 미확정] |
| +0x5e4 | 0x71058bc15c | 600 | 0x710245fd38이 리스폰 착지 구조체 +0x48 = T+0 + 600 |
| +0x6c0 | 0x71058bc238 | 300 | 코옵 좀비(cCoopZombie) HP |
| +0x6dc | 0x71058bc254 | −180.0 | cFirst 재시작 카메라 시작 방향(도) |
| +0x57c | 0x71058bc0f4 | 300 | 아머 원인 5의 HP(0x7102459630) |
| +0x65c / +0x660 | 0x71058bc1d4 / 0x71058bc1d8 | 300 / 180 | 아머 원인 3(리스폰 착지 0x710246292c)의 HP / 기본 지속 |
| (PlayerDamage TU) | 0x71058bcccc / 0x71058bccd0 | 1000.0 / 125.0 | 회복률(초당). 예측 HP 상한 계산에도 1000.0 사용 |
| | 0x71058bbf60 | 8.0 | 특정 상태 넉백 배수 |

### 4.5 플레이어 메시지 ID (0x710234f518 switch) [판독]

| ID | 처리 | 의미 |
|---|---|---|
| 0x6c2b6a04 | 0x7102496b24 | PlayerNetEvent::Attack 송신(공격자 쪽) |
| 0x6c2b6a05 | 0x7102497264 | 받은 Attack 적용(피해자 쪽) |
| 0x6c2b6a1e | 0x71024b18e4 | 99999 데미지 강제 적용(DamageReason 값 4). 송신 0x7101fee4f4 |
| 0x6c2b6a43 / 0x6c2b6a44 | 0x71024bf79c | 최대 HP 재설정(단계 0이면 300, 아니면 1000) |

## 5. 상태 전이와 전체 수명

| 대상 | 시작 | 갱신 | 끝/초기화 |
|---|---|---|---|
| HP(PD+0x7c) | 리셋 0x7102506960 / 리스폰 0x710249cb60 → 1000 | 조작 기기: 프레임마다 0x7101a8905c. 원격: PD+0xee0로 덮어씀 | 1 미만이면 사망 판정 |
| 누적 데미지(PD+0x80) | 0 | 피격마다 + | 그 프레임 갱신에서 HP에 반영 후 0 |
| 회복 대기(PD+0x160) | 0 | 피격(또는 감소율 작동) 프레임에 60 → 같은 갱신에서 59 → 매 프레임 −1 | 0이면 회복 |
| 적잉크 무데미지(S+0xac) | 0 | 적 잉크 중(상태 2이고 S+0xb4) −1, 벗어나 60프레임 뒤 +1(상한 ArmorHP) | 리셋 0 |
| 예측 HP(PD+0xee4) | 1000 | 맞힌 기기의 리스너가 −dmg, 60프레임 뒤 회복 | 리셋 |
| 사망 대기(T+8) | 0 | 사망 시작에서 설정, 0x71024a2c98에서 매 프레임 −1. 조작 기기는 0까지, 그 밖은 1에서 멈춤 | 조작 기기: 1→0 프레임에 리스폰 실행 0x710249e2bc. 원격: `Revival` 수신 리셋이 0으로 [판독+실행] (§6.8) |
| 리스폰 후 타이머(T+0) | 0 | 리스폰 리셋이 60(대전)/120 넣음, 매 프레임 −1 | 0이 되는 프레임에 충돌 객체 전환 [판독, 의미 미확정] |
| ToHumanRespawn 대기(T+4) | 0 | 리셋이 15(대전)/75 넣음, 매 프레임 −1 | 1→0 프레임에 0x710245fd38 → `ToHumanRespawn` 요청 |
| 리스폰 무적(T+0xf4) | 0 | 리셋이 59(대전)/119 넣음, 매 프레임 `max(v,1)−1` | ≥1이면 무적 판정 참 [판독+실행] |

## 6. 계산식·조건·의사코드

### 6.1 HP 홀더 [판독 + 원본 실행 일치]

```
add_damage(H, info, acc):                 // 0x7101a89524
  if acc:
    s = H.pending + info.dmg
    H.hitThisFrame = 1
    if H.pendingMax < info.dmg:           // 가장 큰 단일 히트의 정보만 보관
        H.pendingMax = info.dmg
        H.pendingInfo = info (팀, 공격자, 넉백, 무기, 이름 …)
    H.pending = s
  damageLog.push(info); H.onDamage(info)

cure(H, info):                            // 0x7101a89790 (결과 Cure일 때)
  H.hp = clamp(H.hp + info.dmg); cureLog.push(info); H.onCure(info)

update(H, dt):                            // 0x7101a8905c, 플레이어는 dt = 1/60 (f32 0x3c888889)
  if (H.flags & 1) || H.hp > 0:
    a = H.drainFrac + H.drainPerSec * dt;  n = floor(a);  H.drainFrac = a - n
    if n > 0:
        v = H.hp - n
        if (H.flags & 3) == 2: v = max(v, 1)
        H.hp = v
        if H.flags & 4: H.regenWait = 60           // [0x71058bbb78+0x1c0]
    if H.pending > 0:  H.hp -= H.pending;  H.lastHit = H.pendingInfo
    if H.hitThisFrame && (H.flags & 4): H.regenWait = 60
    if H.regenWait < 1:
        a = H.regenFrac + H.regenPerSec * dt;  n = floor(a);  H.hp += n;  H.regenFrac = a - n
    else:
        H.regenWait -= 1
    H.hp = clamp(H.hp)
  H.pending = 0; H.pendingInfo = 기본(팀 3, 공격자 −1, …); H.pendingMax = 0; H.hitThisFrame = 0

clamp(v) = v < lo ? lo : min(v, H.max),   lo = (H.flags & 1) ? −H.max : 0
```

- 모든 곱셈은 f32, `floor`는 원본의 `(int)a - (a<0 && a != (int)a)`입니다.
- `hp > 0`이 아니고 비트0도 없으면(=쓰러진 뒤) 감소·누적·회복을 **하지 않고** 누적값만 비웁니다.
- 피격 프레임에 대기 60이 들어가고 같은 호출에서 바로 1 줄어 59가 됩니다. 따라서 마지막 피격 다음 **60번째 갱신에서 처음 회복**합니다(재구현 계산).
- 회복량 예: 125.0/s × (1/60) = 2.0833 → 프레임당 2, 소수는 누적돼 12프레임에 25(=2.5 HP). 1000.0/s면 프레임당 16 또는 17.

### 6.2 적 잉크 1프레임 데미지 — 0x710268bc7c~0x710268bd44 [판독, 원본 명령 직접 확인]

```
ratio1000 = S.enemyRatio(+0x48) * 1000.0                         // f32
perFrame  = (전역 0x71058e8784 | 0x71058e8788) ? 0.003 : PlayerParam.OpInk_DamagePerFrame(+0x110)
dmg = fcvtzs(perFrame * ratio1000)
lmt = PlayerParam.OpInk_DamageLmt(+0x114)        // PlayerParam+0x180이 켜져 있으면 0x71024fe8bc 결과
if S.b5:                                         // 항상 1
    v = (S.armorFrames(+0xac) > 0) ? 0.0 : lmt * 1000.0
    w = fcvtzs(v)
    if w <= 999:
        cap = max(float(w + PD.hp - 1000), 0.0)  // fmax 0 — Ghidra 디컴파일에는 빠져 있음(명령 0x710268bd30)
        dmg = fcvtzs(min(cap, float(dmg)))
info = {dmg, team = S+0x38, …};  0x71024b9d34(…, &info)
```

무데미지 프레임(S+0xac, f32) 갱신. 같은 함수에서 위 데미지 계산 **다음에** 실행되므로 데미지는 이전 프레임 값으로 판단합니다:

```
// (1) 감소: 탈것·특수 상태가 아닐 때
inInk = (S.state == 2)
if uVar15 == 0: S.b4 = inInk  else: inInk = S.b4          // uVar15 = 본체+0xd0 >= 상수+0xa8(4) 등 [판독, 의미 미확정]
if inInk: S.armorFrames = max(S.armorFrames - 1, 0)
// (2) 재충전
if S.state == 2: S.b0 = 60
else:
    t = S.b0
    if t < 1: S.armorFrames = min(S.armorFrames + 1, PlayerParam.OpInk_ArmorHP(+0x118))
    S.b0 = (t > 1) ? t - 1 : 0
    if t == 1: S.b4 = 0
```

| 입력 | 결과(재구현 계산 `life_hp.py selftest`) |
|---|---|
| 기본(0.003), 비율 1.0, HP 1000 | 3 |
| 57AP(0.0015, Lmt 0.2) | 1 |
| HP 601, Lmt 0.4 | 1 (상한 601−600) |
| HP 600 이하 | 0 |
| 무데미지 프레임 남음 | 0 |
| 비율 0.5 | 1 (0.003×500=1.5 → 1) |

### 6.3 플레이어 피해 적용 — 0x71024b0c70 [판독]

인자: (본체+0xa5f9, …, param_6 = PlayerDamage, param_7 = PlayerArmor, param_8 = PlayerCoopZombie, …, info, `force`, `acc`).

```
if !force && 무적(0x71024c7624):
    (미션 모드 특수 조건 아니면) return
if 코옵 좀비 모드(전역 *0x7105791bd0+0x143d0 && Zombie+0xeec): 같은 팀이면 Zombie 홀더에 누적 후 return
if 무기 정보(0x7101a81a68)가 '종류1' 이고 팀 다르면: PD 홀더에 바로 누적(아머 무시) 후 return   // 종류1 의미 [미확정]
lethal = info.dmg >= 99999
if lethal && force: 아머 파괴 0x710243beb0(armor, 0)
c = copy(info)
if !(lethal && force):
    if armor.ef8(파괴 직후 유예 프레임) >= 1:
        c.dmg = (info.dmg > 1000) ? info.dmg - 1000 : 0
        if armor.flags31 & 0xC7: c.dmg = min(c.dmg, 800)
    if armor.active(+0xf18): 팀 다르면 아머 홀더(armor+0x38)에 누적
    else: 팀 다르면 PD 홀더(PD+0x30)에 누적
else: 팀 다르면 PD 홀더에 누적
if armor.active && armor.hp <= armor.pending && info.dmg - 1000 > 0:     // 이번에 아머가 깨짐
    over = info.dmg - 1000;  if armor.flags & 0xC7: over = min(over, 800)
    팀 다르면 PD 홀더에 over 누적
통계 0x7102462f5c; dmg > 0 이고 무적 아님 → 피격 반응 0x71024b1510 …
```

- 같은 팀 판정은 `info.team != 피해자 팀`(액터 +0x668)입니다. 리시버의 팀 판정(Through)과 별개로 한 번 더 막습니다.
- 아머 수치(1000/800, 유예 20프레임)는 상수 블록 값과 0x710243b93c의 `0x14`입니다. 아머 HP 자체(아머 홀더 max)는 startArmor 0x710243c1c4가 넣습니다(§6.9, 이전 [미확정] 해소).

### 6.4 회복률 선택 [판독, 조건 의미는 추정]

`0x71024591c8(본체+0x784)`가 참이면 1000.0/s, 아니면 125.0/s. 참 조건: (+0x784)+0x1c 바이트, 또는 본체+0xa5f4 바이트, 또는 전역 0x71058bbb9a, 또는 넷 레플리카 상태 7~11이 아님, PlayerGeyser(+0xa808) 상태 1·2, PlayerPipeline(+0xa6d0) 상태≠0, PlayerPeriscope(+0xa818) 상태 2, PlayerVehicleSpectacle(+0xa6d8) 조건 … . 첫 조건이 "자기 잉크에 잠수"일 것으로 봅니다 **[추정]**.

### 6.5 사망 시작 — 0x710245ff9c(T, PlayerParam, …, 공격자) [판독]

```
if T+8 > 0 || T+0x88 > 0 || T+0x98 > 0 || T+0xb4 > 0: return
T+0x105 = 0x71024c9824(…) & 1; T+0x106 = (param_3+0x10); T+0x18 += 1     // 쓰러진 횟수
if 공격자 == −1 && Scene_Versus(0x71058e877c) && info+0x38 == −1 && info+0x40 == 6:
    공격자 = {팀0: 10, 팀1: 11, 팀2: 12}[액터+0x668] (그 밖 팀이면 −1)      // 공격자 없는 사망의 대리 번호
T+0x1d = 0
if !Scene_Coop(0x71058e87a4):
    T+0x1d = 본체+0xd70 ≥ 2 && 공격자 ≥ 0 && PP+0x5c > 0              // 원문 조건 (공격자<0 && 공격자&~1 != 10)은 공격자<0 과 같음
    T+0xc  = int(0x710266c838(PP, 0x10, 공격자, 1))                    // Dying_AroundFrm
    c      = int(0x710266c838(PP, 0x11, 공격자, 1))                    // Dying_ChaseFrm
    보정   = VersusReferee(*0x71058367f8) ? vt+0x50(referee, 액터+0x668 팀) : 0
    T+0x10 = max(c + 보정, 0)
else: T+0xc = 60, T+0x10 = 120                                        // [0x71058bc084]/[0x71058bc088]
T+8 = T+0xc + T+0x10 + 30                                             // [0x71058bbd2c] = 30
if Scene_Mission(0x71058e8784): (미션 관리자 0x7102199b78 경로) T+8 = T+0xc = 미션값(+0x240, 액터+0x7b9면 +0xb4), T+0x10 = 0
… 이후: 0x7102491758(상태 정리), 상태 요청 Dead(0xe6), 리스폰 지점 포즈 선택(§6.8.5), 보조 객체 정리
```

`0x710266c838(PP, idx, 공격자, 기어적용)`: 기어 적용 조건이 참이면 PlayerParam+0xb0+idx×4(=기어 보간 결과, idx 0x10 → +0xf0, 0x11 → +0xf4), 거짓이면 RespawnTimeSave 파라미터의 Low 값(+0x34 / +0x40)을 그대로 씁니다. 기어 적용 조건(디컴파일 `analysis/decomp/player/playerparam_gear.c` 직접 확인): 인자로 받은 적용 플래그가 1이고 `본체+0xd70 < 2 또는 공격자 < 0`이면(원문은 `공격자<0 && (공격자&~1)≠10`인데 10/11은 음수가 아니므로 같은 뜻), [0x7105795dd8]+0x1f가 꺼져 있을 때 `GameFrame < 본체+0xa5a0`로 다시 정합니다. 즉 `본체+0xd70 ≥ 2`이고 공격자가 있으면 항상 기어를 적용하고, 그 밖에는 시간 창 안에서만 적용합니다 **[판독]**. 이 필드들의 의미(연속 사망 수, 시간 창)는 **[추정]**. 특수 능력(0x710266de0c가 켜는 두 플래그)이면 AP×[0x71058c03b0/b4] 보정 경로를 탑니다 **[판독, 능력 이름 미확정]**.

**모드 보정(이전 [미확정] → [판독])**. `*0x7105796510`(GOT) → 변수 `0x71058367f8`은 `VersusReferee` 싱글턴입니다(설정 0x710303c460, 해제 0x710303ba2c/0x710303ceb8). 슬롯 3이 클래스 이름 문자열을 쓰는 vtable 7개를 확인했고, vt+0x50은 다음과 같습니다.

| 클래스(슬롯 3 문자열) | vtable | vt+0x50 | 보정 |
|---|---|---|---|
| `VersusReferee` | 0x71056a90a8 | 0x710303f4e4 | `return 0` |
| `VersusRefereePaint`(영역 배틀) | 0x71056a9460 | 0x710303f4e4 | 0 |
| `VersusRefereeVArea` / `VClam` / `VLift` | 0x71056a9798 / 0x71056a98e0 / 0x71056a9b88 | 0x710303f4e4 | 0 |
| `VersusRefereeVGoal` | 0x71056a99f0 | 0x710303f4e4 | 0 |
| `VersusRefereeTricol` | 0x71056a9570 | 0x7103042c40 | 팀 == 2 → `RespawnTimeCorrectFrame_Defense`(+0x68), 그 밖 → `_Offense`(+0x6c) |

`spl__VersusConstant_RefereeTricol` 파라미터 기본값(생성자 0x710305eae4, `param_reflect.py`): `RespawnTimeCorrectFrame_Offense` 0, `RespawnTimeCorrectFrame_Defense` 120, `RoundNum` 2, `Noroshi*` 시간 값들 **[판독 — 생성자 기본값, 데이터 파일은 못 찾음]**. 따라서 **트리컬러 밖의 대전은 보정 0**, 트리컬러에서 팀 번호 2는 Chase에 120프레임이 더해집니다. 팀 2가 경기 규칙상 어느 쪽(방어/공격)인지는 **[추정 불가 — 미확정]**.

기본값(기어 0, RespawnTimeSave Low): Around 90, Chase 270 → **T+8 = 390프레임** [재구현 계산, 판독한 식 + [combat] §4.9 값]. 이 390을 시작값으로 리스폰까지의 프레임 흐름은 원본 실행으로 확인했습니다(§10).

### 6.6 맞힌 기기의 예측 HP(처치 표시) — 0x71024632ec, 0x7102483134 [판독]

```
피해자가 이 기기 조작이 아님:
    PD+0xee4 -= dmg   (아머가 켜져 있으면 아머 홀더 쪽 예측 armor+0xeec 를 먼저 깎고 넘친 양만)
    PD+0xee8 = 60
    PD+0xee4 <= 0 이고 본체+0xe60[0] < 1:  본체+0xe60 = {10, …, 공격자 번호, 무기정보, 크리티컬}  // 처치 연출용 [추정]
매 프레임(원격 플레이어):
    PD+0xee8 > 0 이면 −1, 아니면 PD+0xee4 = min(max, int(PD+0x154/60 + PD+0xee4))
원격 상태 수신(0x7102475a54):
    PD+0xee0 = 받은 HP                // PlayerNetState+0x6c (§6.10)
    PD+0xee4 = min(PD+0xee4, min(1000, int(1000.0 * 경과프레임/60 + 받은 HP)))
```

### 6.7 *조작 기기* 판정 [판독]

여러 함수에 같은 switch가 반복됩니다(넷 객체 = 본체+0xa8e0 등의 레플리카 정보):

```
if GameNet(*0x71057908b8)+0x180 != 0: 거짓          // 의미 [미확정]
local = *(*0x7105790d88 + 0xc70) + 0x18              // 로컬 스테이션 번호, <0 이면 오프라인 → 참
if !obj+0x2c: 거짓
switch obj+0x48: 0 → obj+0x44 == local; 1,4 → 세션 콜백 vt+0x90; 2 → obj+0x98 == local; 3 → 참
```

### 6.8 쓰러짐 타이머·리스폰 흐름 [판독 + 원본 실행]

[state] 담당의 상태 표([../player/player_state.md](../player/player_state.md) 부록, 표 0x7105630270)와 맞춰 본 결과입니다. 디컴파일은 `analysis/decomp/gauge/gauge_batch1.c`(0x71024a2c98, 0x710249cb60), `life/batch1.c`(0x710249e2bc, 0x710249eec4), `life/batch3.c`(0x710245fd38), `respawn/batch1.c`·`batch2.c`(스폰 관리자, 모드 보정), `state/state_big_full.c`(0x7102442354)입니다.

**정정(2026-10-02 [respawn])**: 이전 판은 "일반 경로 0x71024a3300~0x71024a3610에서 T+8을 1까지 줄이고 2→1이면 T+0x103=1"이라고 적었습니다. 분기 명령 0x71024a2dcc~0x71024a2df4를 직접 읽으니 이 경로는 `Scene_Mission`(0x71058e8784) && 액터+0x7b9 == 0 && 0x7102f7ae50() && T+0x104 == 0일 때만 탑니다. 즉 **미션(히어로 모드) 전용**이고, 대전은 §6.8.2의 "조작 기기" 경로입니다. 또 0x710245fd38의 상태 선택은 "미션 플래그면 0xea"가 아니라 **스폰 관리자 팀별 플래그 F가 참이면 0xe9, 거짓이면 0xea**입니다(§6.8.4).

#### 6.8.1 T(본체+0xd58) 필드 [판독]

| T+ | 타입 | 이름(웹 권장) | 의미 | writer | reader |
|---|---|---|---|---|---|
| +0x00 | s32 | `postRespawnTimer` | 리스폰 후 타이머. >0 동안 무적, F 참이면 매 프레임 SM+0x108 = 2 | 리셋 0x710249cb60(F ? 60 : 120, 그 밖 0), 0x71024a2c98(−1) | 무적 판정, 0x7102442354(상태 없음이면 결정 보류), 0x71024a2c98(0이 되는 프레임에 PlayerCollision(+0xa690)+0x48/+0x50 객체에 0x7103ae4c48(…,0); 리셋은 (…,1). 의미 [미확정]) |
| +0x04 | s32 | `toHumanDelay` | ToHumanRespawn 요청까지 | 리셋(max(T+0 − 45, 1)) | 0x71024a2c98(1→0이면 0x710245fd38) |
| +0x07 | u8 | | TroubleDie 송신 bool | 리셋(0) | 0x7102483134 |
| +0x08 | s32 | `deathWait` | 사망 대기 | 0x710245ff9c(§6.5), 리셋(0) | 0x71024a2c98, 사망 판정, 무적 판정, Attack 수신 무시 |
| +0x0c / +0x10 | s32 | `around` / `chase` | 사망 대기 구성값 | 0x710245ff9c | |
| +0x18 | s32 | `deathCount` | 쓰러진 횟수 | 0x710245ff9c(+1) | |
| +0x1d | u8 | | 기어 관련 조건 플래그(§6.5) | 0x710245ff9c, 리셋(0) | [미확정] |
| +0x88 / +0x98 / +0xb4 | s32 | `fallWait*` | 다른 쓰러짐 타이머(0이 되면 리스폰 kind 2/3/4) | 낙하·수몰 쪽 [미확정], 리셋(0) | 0x71024a2c98, 무적 판정 |
| +0xac / +0xc4 | s32 | | +0x98 / +0xb4와 짝으로 무적 판정에 쓰임 | [미확정] | 무적 판정 |
| +0xf4 | s32 | `respawnInvincible` | 리스폰 무적 | 리셋(T+0 − 1), 0x71024a2c98(`max(v,1)−1`) | 무적 판정(≥1이면 무적) |
| +0xf8 | s32 | | 0 이상이면 0x71024a2c98이 관리자 표(+0xa8/+0xb0) 항목을 읽어 처리 | [미확정] | 0x71024a2c98 |
| +0x101 | u8 | | 무적 / 원격 Revival 무시 | [미확정] | 무적 판정, 0x710249eec4 |
| +0x102~+0x106 | u8 | | +0x102 = (T+8, +0x88, +0x98 중 하나가 30이고 F) 때 1(0x71024a3008 뒤, 미션 경로 밖), +0x103 미션 경로 2→1, +0x104 미션 경로 차단, +0x105 0x71024c9824 결과, +0x106 사망 정보 | 0x71024a2c98, 0x710245ff9c, 리셋(0) | +0x102·+0x103 소비자 [미확정] |
| +0x148 | 0x30 B | `spawnPose` | 리스폰 지점 포즈(+0 위치 f32×3, 이후 방향 등) | 0x710245ff9c(§6.8.5) | 0x710249e2bc |
| +0x178 | 구조체 | `respawnLand` (= 본체+0xed0) | +0x48 = T+0 + 600, +0x4c = T+0, +0x50 = 0, +0x64(= 본체+0xf34) 단계 | 0x710245fd38(F일 때 단계 1), 원격 상태 반영 0x7102475a54 | 넷 `RespawnLand`([network/04](../network/04_player_state.md) §4.2), 무적 판정, 상태 전이 |
| +0x9b70 / +0x9b88 | ptr | | 상태기계(본체+0xa8c8) / 넷 레플리카(본체+0xa8e0) | | |

#### 6.8.2 매 프레임 타이머 — 0x71024a2c98 앞부분 + 0x71024a3f90~0x71024a4120 [판독 + 원본 실행]

호출: 플레이어 프레임 계산 0x7102475898 안 0x7102476fd0(`analysis/decomp/move/move_full_main.c` 2003줄, param_7 = T). 경로 선택은 함수 첫 분기입니다.

```
A = Scene_Mission && 액터+0x7b9 == 0 && 0x7102f7ae50() && !T.b104
if A:                                   // 미션 전용 0x71024a3300~
    T+8, +0x88, +0x98, +0xb4: v ≥ 3 → v−1, v ∈ {1,2} → 1 (2→1이면 T.b103 = 1)
elif 액터+0x7b9 != 0:                   // 0x71024a2e04~ 별도 액터 경로
    네 타이머 0까지 감소, 1→0 프레임에 액터 처리(0x7103db1ab4, 액터+0x438 비트 0x4000 해제, 0x7100f721b8)
elif GameNet+0x180 != 0 || !조작기기(§6.7):        // 0x71024a3028
    T+8, +0x88, +0x8c, +0x98, +0xb4: v > 1 → v−1   (1에서 멈춤; 원격은 Revival 수신으로 리셋)
else:                                    // 조작 기기 0x71024a62e8~
    if [0x71058bbb96] == 0:              // 정적 초기화 값 0
        old = T+8; T+8 = max(old−1, 0); old == 1 → revive(P, T, T+0x148, 본체+0x350, 넷, useAlt=0, kind=1)
    else: (네 타이머 중 1인 것을 2로 올린 뒤 감소 → 1 유지, 리스폰 없음)   // 디버그 정지 [추정]
    T+0x88: 1→0 → revive(…, 1, 2);  T+0x98: → (…, 1, 3);  T+0xb4: → (…, 1, 4)
    T+0x8c: >0 이면 −1
… (중간 처리 생략) …
if T+0 > 0:                              // 0x71024a3f90~
    T+0 −= 1
    if T+0 == 0:
        if !F: 상태 ∈ [0xe6, 0x11d]면 ASB 슬롯 2개에 0x710245064c/0x7102450348; T.b100 = 0
        PlayerCollision 객체 0x7103ae4c48(…, 0)
    if F: SM+0x108 = 2
if T+4 > 0: T+4 −= 1; 0이 되면 0x710245fd38(T, SM, …, T+0x178, 본체+0xa8d0)
T+0xf4 = max(T+0xf4, 1) − 1
```

`F` = 스폰 지점 관리자(`*0x7105863d00`, §6.8.5)가 있고 +0x3680 비트0과 +0x3681 비트0이 모두 켜짐. 대전은 팀별 스폰이라 F가 참일 것으로 봅니다 **[추정 — 넷 `RespawnLand` 변형이 같은 조건이고, 거짓일 때 고르는 상태 이름이 `_Msn`]**.

#### 6.8.3 리스폰 실행·리셋 — 0x710249e2bc, 0x710249eec4, 0x710249cb60 [판독 + 원본 실행]

```
revive(P=본체+0xa5f9, T, spawnPose, X=본체+0x350, net, useAlt, kind):        // 0x710249e2bc (조작 기기)
    if !Scene_Coop:
        if !Lobby(0x71058e87ac): pose = useAlt ? 0x710249e0fc(…) : copy(spawnPose)
        else: 0x7102daf228(&pose), 실패 시 X 기반
        type = 0 (cRespawn)
    else: 코옵 좀비 포즈, 0x7102643148(X, pose, …), X+0xfc = 1, type = 5 (cCoopZombie)
    if 조작 기기 && 세션 인원 > 1:
        PlayerNetEvent::Revival { +0x20 위치 f32×3, +0x2c 0, +0x30 방향 f32×3, +0x3c T+0, +0x40 T+0xf4 } 송신
        // T+0/T+0xf4는 리셋 전 값(보통 0). 수신 측 0x710249eec4는 이 두 값을 쓰지 않음 [판독]
    리플레이 기록 0x7102b1cc78
    reset(…, pose, dir, type, &kind)                                    // 0x710249cb60
    0x710249f298(P, …, T, type)

remoteRevive(P, …, ev):                                               // 0x710249eec4 (원격 기기; 0x71024c17d8이 해시 0x74400e72 수신 시)
    무시: T.b101 || 본체+0x9212 || 본체+0x9213 || CoopSeq(+0xa830)+0x1348 == 0xc || MissionTicketGate(+0xa6c8)+0x38 ∉ {0,5}
    pos = ev+0x20 (ev+0x2c ≠ 0이면 0x71012db7b4가 돌려준 행렬로 변환), dir = ev+0x30
    reset(…, pos, dir, Scene_Coop ? 5 : 0, &0)

reset(…, pose, dir, type, &kind):                                    // 0x710249cb60, type = spl::PlayerRestartType
    if type ∉ {2,3}: 본체+0x9218 = 1, +0x921c = 0 (미션이면 최대 HP 재설정 0x71024bf79c)
    본체+0x10 ← pose 위치(12 B), 방향 ← dir
    T+8, +0xc, +0x10, +0x1d, +0x88~+0xb4 계열, +0x102~+0x106 = 0
    PlayerDamage: max = 1000, hp = clamp(hp), 홀더 리셋 0x7101a88e1c(hp = max), +0xee0 = +0xee4 = 1000, +0xee8 = 0, +0xeec = 1000
    PlayerArmor: 원인 비트 +0x30 = 0, 홀더 리셋, 활성 +0xf18 = 0, +0xef0~+0xf14 = −1, +0xeec = 아머 max
    PlayerCoopZombie: +0xeec = 0, 홀더 리셋; type == 5면 +0xeec = 1, max = hp = 300([0x71058bc238])
    상태기계 리셋 0x710243dcf8(SM, type)   (type ∉ {2,3} 또는 X+0xb):
        type ≠ 1 → WaitHold(0x56) [본체+0x9210이면 오징어 WaitStandby(0x86), 코옵 좀비면 오징어 Wait(0x85)]
        type == 1(cFirst) → World면 WorldAppear(0xf1), 미션이면 MsnAppear(0xef), 코옵이면 0x104+…, 그 밖은 위와 같음
    카메라 리셋(type ∉ {3,6}), type == 1이면 시작 방향 −180°([0x71058bc254])
    T.b7 = 0
    if type ∈ {0,5}:                                                  // cRespawn, cCoopZombie
        if !Scene_Mission || (!World(0x71058e8788) && !0x7102f800a0(3) && !0x7102f800a0(6)):
            T+0    = F ? 60 : 120                                     // [0x71058bbd1c] / [0x71058bbd18]
            T+4    = max(T+0 − 45, 1)                                 // [0x71058bbd20] / [0x71058bbd24]
            T+0xf4 = T+0 − 1
        else: T+0 = T+4 = T+0xf4 = 0, 곧바로 0x710245fd38
    else: T+0 = T+4 = T+0xf4 = 0
    if kind != 6: 리스폰 알림 객체(vt 0x71056333a8, +0x20 액터+0x798 번호, +0x30 kind, 포즈) 큐잉
```

`spl::PlayerRestartType` = `cRespawn(0), cFirst(1), cWarp_CameraReset(2), cWarp_CameraNoReset(3), cVanish(4), cCoopZombie(5), cPlayGamePadRecorder(6)` **[판독]** — 열거형 정보 함수 0x710349fe34가 문자열 0x71048e2f2e를 분할하고, 이름 기록(0x7103486c48) 직후 이 함수를 부릅니다. 코드 분기와도 맞습니다: 3이면 카메라 리셋 생략, 6이면 리셋 생략·알림 없음, 1이면 시작 방향 −180°, 5면 코옵 좀비 HP 300. [camui]가 요청한 "param_40 ↔ PlayerRestartType 대응"도 이것입니다.

#### 6.8.4 ToHumanRespawn → WaitRespawn → ToSpawner [판독, 단계 의미는 추정]

```
0x710245fd38(T, SM, …, RL = T+0x178, …):                // T+4가 0이 되는 프레임
    if CoopZombie+0xeec == 0 && (!Scene_Mission || (!World && !f800a0(3) && !f800a0(6))):
        상태 요청 F ? 0xe9 ToHumanRespawn : 0xea ToHumanRespawn_Msn   (성공 시 SM+0xf0 = 0x6b; 전역 *0x7105790698+0x120이면 SM+0x1e4로 지연)
    if !F: ASB 슬롯(관리자 +0x40 = 1) 정리
    else:  RL+0x48 = max(T+0,0) + 600, RL+0x4c = max(T+0,0), RL+0x50 = 0, RL+0x64(본체+0xf34) = 1
상태 결정 0x7102442354 (0x71024437f0~0x7102443f90):
    상태 ∈ {0xb5 DokanWarp_ToSpawner_Ed, 0xe9, 0xea} && 애니 끝(0x710244fed8) → 0xe4 WaitRespawn
    상태 없음(−1)이고 T+0 > 0 → 결정 보류
    f34 = 본체+0xf34
    if f34 ∈ {2,3,4}:  0xe4 → 0xe5 ToSpawner;  0xe5 + 애니 끝 → 0xbb Injection_Pre (블렌드 f34 ∈ {3,4,5} ? 1.0 : 0)
                       0x97 ToHumanStandby → 0x98;  0x98 + 애니 끝 → 0xbb
    else:
        본체+0x9213 || CoopSeq+0x1348 == 0xc: 0xe5/0x98 + 애니 끝 → 0xbb
        본체+0x9211 == 0: 0xbb이고 (f34 == 1 || T+0 ≥ 1) → 0xe4로 되돌림, 그 밖은 위 줄과 같음
        본체+0x9211 != 0: 0x98/0xe5 + 애니 끝 → 0xbb, 0xbb → 0xe4
    (0xbb에서 f34 ∈ {3,4,5}면 ASB 재생 속도 0x7102450510 설정 후 다시 판정)
```

**WaitRespawn에서 나가는 조건(이전 [미확정] → [판독])**: F 참(대전 추정)에서 `WaitRespawn`(0xe4)은 *리스폰 착지 단계* 본체+0xf34가 2~4가 되면 `ToSpawner`(0xe5)로, 그 애니가 끝나면 `Injection_Pre`(0xbb, 스폰 지점에서 발사 준비)로 갑니다. 단계 1(0x710245fd38이 넣음)에서는 `WaitRespawn`에 머뭅니다. 조작 기기에서 단계 2~5를 넣는 writer(발사 입력 처리)는 찾지 못했습니다 **[미확정]**. 원격 기기는 받은 `RespawnLand` 상태로 본체+0xf34를 덮어쓰고(0x7102475a54: 단계 1/2/4는 타이머 설정, 5는 0x710246292c 착지 처리) §6.9의 아머 원인 3을 겁니다.

#### 6.8.5 리스폰 지점 선택 [판독, 관리자 정체는 추정]

`*0x71057999c8`(GOT) → 변수 `0x7105863d00`이 *스폰 지점 관리자*입니다(설정 0x71027cb104 / 해제 0x71027cb11c가 vtable 0x71056494b8 영역의 슬롯이고, 그 앞 슬롯에 문자열 `"player_point"`). 사망 시작 0x710245ff9c 끝에서:

```
M = *0x7105863d00
if M && M+0x3680 & 1:
    pose = (M+0x3681 & 1) ? 0x71027ca08c(M, 팀 = 액터+0x668, i = 액터+0x79c)
                          : 0x71027c8c98(M, …)
    T+0x148 .. +0x177 ← pose (0x30 B)
0x71027ca08c(M, 팀, i):           // mutex M+0x28
    팀 0: i < M+0x270 → (M+0x278)[i];  팀 1: i < M+0x850 → (M+0x858)[i]
    팀 2: g = i / ceil(인원수([0x710580e340]+0xd330) / M+0x19f0), i %= …, 표 = M+0xe30 + g×0x5e0 (g < 2)
    항목 있으면 항목+0x60, 없으면 M+0x3650
0x71027c8c98: 같은 색인, 항목 자체(+0) 반환
```

i = 액터+0x79c는 팀 안 순번으로 보이고 플레이어마다 다른 항목(포즈)을 받습니다 **[추정]**. 항목을 채우는 쪽은 데이터 `LocatorSpawner`(팀별, [gimmick] [stage_misc.md](../gimmick/stage_misc.md) §5)로 보이나 연결 코드는 보지 않았습니다 **[미확정]**. 낙하 리스폰(useAlt = 1)은 0x710249e0fc가 본체+0x90..의 포즈를 기본으로 하고, 관리자가 팀별이 아니면 `PlayerMake` 씬은 M+0x3684 포즈, 그 밖은 0x71027c8c98/0x71027c933c/0x71027c8ef4를 씁니다 **[판독, 일부]**.

#### 6.8.6 대전 기본 타임라인 [원본 실행]

사망 시작이 T+8 = 390을 넣은 뒤 0x71024a2c98의 n번째 호출 기준(F 참, 조작 기기, 기어 0):

| 호출 | 일 |
|---|---|
| 1~389 | T+8: 389 → 1 |
| **390 (R)** | T+8 1→0, `revive` → 리셋(HP 1000, 위치 = 리스폰 지점, T+0 = 60, T+4 = 15, T+0xf4 = 59). 같은 호출 뒤쪽에서 T+0/T+4/T+0xf4가 바로 1씩 줄어 59/14/58 |
| R+14 = 404 | T+4 1→0 → 0x710245fd38(`ToHumanRespawn` 요청, 리스폰 착지 단계 1) |
| R+58 = 448 | T+0xf4 = 0 (리스폰 무적 카운터 끝. T+0 > 0이라 무적 판정은 아직 참) |
| R+59 = 449 | T+0 = 0 (T 쪽 무적 조건 모두 해제) |

F 거짓이면 T+0 = 120, T+4 = 75, T+0xf4 = 119이고 각각 R+74 / R+118 / R+119입니다(원본 실행 결과 같음). 사망 판정·사망 시작(0x7102483134 안)과 0x71024a2c98의 프레임 안 호출 순서는 확인하지 않았습니다 **[미확정]** — 사망 프레임과 R 사이 간격은 이 순서에 따라 390 또는 391입니다.

### 6.9 아머 HP 설정(StartArmor) — 0x710243c1c4 [판독]

```
startArmor(A = PlayerArmor, hp, startFrame, duration, cause, send):
    if hp < 1: return
    if A.causeBits(+0x30) != 0 && (A.causeBits & ((1 << cause) − 1)) != 0: return   // 더 작은 번호 원인이 이미 있으면 무시
    A.causeBits |= 1 << cause
    A.holder.max(+0x80) = hp;  A.holder.hp(+0x84) = clamp(hp)       // 홀더 = A+0x38
    A+0xeec = A+0xee8 = hp                                          // 예측 아머 HP(맞힌 기기 표시용)
    A+0xef0 = startFrame;  A+0xef4 = startFrame + duration
    if send && 조작 기기 && 세션 인원 > 1:
        PlayerNetEvent::StartArmor { start(GameNet+0x194면 start − GameFrame, 0 이상), duration, hp, cause, 생명번호 } 송신
    if cause ∈ {2,3,4,5}: xlink "SuperArmor_Mount"(0x71048ea9a1)
```

이전 판의 "아머 HP 설정자 [미확정]"을 해소합니다. 활성·종료는 기존 판독과 이어집니다: 0x710243ba44가 GameFrame ≥ A+0xef0이면 활성(+0xf18 = 1, 리시버 열 `NiceBall_Armor`(원인 비트1 없을 때)/`Default`), A+0xf00+4×원인이 지나면 그 원인 해제(0x710243bc78). 0x710243b93c는 활성 중 원인 4·5 비트가 있고 오징어 이동 상태(0x82~0x90, 0xaa~0xac, 0xed/0xee/0x10c)가 아니면 원인 5·4를 해제하고, `hp > 0 && GameFrame < A+0xef4`가 아니면 끝냅니다(hp < 1이고 원인 4·5가 없으면 파괴 유예 20, 그 밖 0 → `SuperArmor_Break`(hp ≤ 0) / `SuperArmor_Vanish`(hp > 0)).

호출부(원인 번호는 w4 즉시값):

| 호출 위치 | 원인 | HP | 시작 | 지속 | 비고 |
|---|---|---|---|---|---|
| 0x71025e4ca4 안 0x71025e5140 | 1 | 인자 | 인자 | 인자 | 송신 0. 클래스 [미확정] |
| 0x710246292c 안 0x7102462b1c | 3 | 300 ([0x71058bc1d4]) | GameFrame | 180([0x71058bc1d8]) + [x24+0xac] | 송신 0. *리스폰 착지* 처리(원격 `RespawnLand` 단계 5 수신 0x7102482500에서도 호출) |
| 0x7102442354 안 0x7102446cd4 | 4 | 인자 | 인자 | 인자 | 상태 전이 안. 오징어 상태를 벗어나면 해제 |
| 0x7102459630 안 0x7102459e24 | 5 | 300 ([0x71058bc0f4]) | 인자 | 인자 | 오징어 상태를 벗어나면 해제 |
| 0x71024b3efc → b 0x710243c1c4 | 인자 | 인자 | 인자 | 600 | 송신 0 |
| 0x71024c17d8 안 0x71024c5cec / 0x71024c5e74 | 이벤트 값 | 이벤트 값 | 이벤트 값 | 이벤트 값 | 원격 `StartArmor` 수신 |

원인 번호 ↔ 무기·스페셜 이름은 **[미확정]**(데이터 `ArmorHP`, `SuperBallArmorHPRate` 문자열 위치만 확인). 원인별 종료 프레임 A+0xf00~+0xf14의 writer도 찾지 못했습니다 **[미확정]**.

### 6.10 원격 플레이어 HP의 넷 필드 [판독]

원격 상태 반영 0x7102475a54는 스택에 `PlayerNetState`(vtable 0x710562e018, 디컴파일 변수 `local_2b0`)를 만들고 0x7102658bb4로 받은 상태를 채운 뒤, `local_244`(= 상태+0x6c, 기본 1000)를 PD+0xee0에 씁니다(코옵 좀비 활성이면 다른 객체의 +0xee0). 같은 블록에서 예측 HP를 `min(PD+0xee4, min(1000, int(1000.0 × (GameFrame − 상태+0x88)/60 + 받은 HP)))`로 내립니다. 따라서 **원격 HP = `PlayerNetState`+0x6c (u10)**이고 송신 측 출처는 PD+0x7c입니다([network/04_player_state.md](../network/04_player_state.md) 필드 출처표의 후보를 확정). 이전 후보 "PlayerDamage+0x7c / u10 +0x6c"는 송신·수신 양쪽에서 같은 필드였습니다. 같은 수신 블록에서 상태+0x128 변형이 2(`RespawnLand`)가 아니면 본체+0xf34 = 0, 2이면 받은 단계로 바꿉니다.

### 6.11 무적 판정 — 0x71024c7624 조건별 출처 [판독 + 원본 실행]

인자(호출부 0x7102484224 기준): x0 = 본체+0xa5f9, x1 = T, x2 = PlayerDokanWarp(+0xa880), x3 = 본체+0x925c, x4 = PlayerDashPanel(+0xa698), x5 = 본체+0x9208, x6 = PlayerMissionTicketGateAction(+0xa6c8), x7 = 본체+0x588, 스택 = PlayerInkActionSpSkewer(+0xa7e8), PlayerInkActionSpSuperLanding(+0xa7f0), 상태기계(+0xa8c8), PlayerDemo(+0xa650), `force`(bool). 컴포넌트 이름은 `analysis/player/player_components.tsv`.

| 순서 | 참(무적) 조건 | 출처 | 의미 |
|---|---|---|---|
| 1 | T+0xf4 ≥ 1 | T | 리스폰 무적 |
| 2 | (본체+0x9213 == 0 && CoopSeq+0x1348 ≠ 0xc일 때) 본체+0x9211 ≠ 0, T+0 > 0, 본체+0xf34 ∈ {1,2,4} | 본체 | 리스폰 착지 단계 대기/발사 중 [추정] |
| 3 | T+8, T+0x88, T+0x98, T+0xb4, T+0 중 하나 > 0 | T | 쓰러짐·리스폰 직후 |
| 4 | T+0x101 ≠ 0, 본체+0x9314(T+0x85bc) ≠ 0 | T/본체 | [미확정] |
| 5 | MissionTicketGate+0x38 == 1 && +0x3c ≤ 124.0 | 컴포넌트 | 미션 게이트 연출 앞부분 [추정] |
| 6 | DokanWarp+0x30 == 3 | 컴포넌트 | 도칸 워프(배관) 이동 중 [추정] |
| 7 | 본체+0x925c+0x45 && (+0x4d \|\| GameFrame ≤ +0x48) | 본체 | 기한형 무적(마감 GameFrame) [의미 미확정] |
| 8 | DashPanel+0x68 > 0 | 컴포넌트 | 대시 패널 |
| 9 | 넷 레플리카 상태 7~11 아님(본체+0xa810 경유, mutex) | 넷 | [미확정] |
| 10 | MissionTicketGate+0x38 ∉ {0,5} | 컴포넌트 | 미션 게이트 동작 중 [추정] |
| 11 | 본체+0x9210 / +0x9212 / +0x9213 ≠ 0, CoopSeq+0x1348 == 0xc | 본체 | [미확정] |
| 12 | PlayerDemo+0x30 / +0x31 ≠ 0 | 컴포넌트 | 데모(연출) 중 |
| 13 | 상태 0xef/0xf0(MsnAppear*)이고 ASB 프레임 ≤ 95, 0xf1(WorldAppear 오징어), 0xf2(WorldAppear 사람)이고 프레임 ≤ 50 | 상태기계 | 등장 연출 |
| 14 | (본체+0x588 == +0x598 또는 +0x678 == +0x688)이고 본체+0x65c == 0x1b이고 SpSkewer+0x40 ∈ {3,4,5} | 컴포넌트 | 스페셜 0x1b 사용 중 [스페셜 이름 미확정] |
| 15 | `force`면 여기서 거짓. 본체+0x65c == 0x1c이고 SpSuperLanding(+0x40 ∉ 4~6 && (+0x40 ≠ 3 \|\| (int)(+0x80 − +0x44) > 5)) → +0x188 > 0, 그 밖 참 | 컴포넌트 | 스페셜 0x1c 착지 [이름 미확정] |

원본 실행(§10)으로 1, 3(5종), 2(f34 = 1, 본체+0x9211), 4(T+0x101), 5, 6, 8, 12, 13(0xf1)을 하나씩 켜면 참, 모두 0과 f34 = 3은 거짓임을 확인했습니다. 7·9·10·11·14·15는 실행하지 않았습니다.

## 7. 애니메이션·이펙트·소리 연결

- 아머 xlink 키 **[판독]**: 시작(원인 2~5) `SuperArmor_Mount`(0x71048ea9a1, 0x710243c1c4), 파괴 유예 끝 `SuperArmor_Break`(0x710243bb84), 해제 시 HP ≤ 0이면 `SuperArmor_Break`(0x71048a994f), HP > 0이면 `SuperArmor_Vanish`(0x71048c581f).
- 아머 활성 시 리시버 열 이름을 `NiceBall_Armor`로 바꿔 DamageRateInfo 열이 달라집니다(0x710243bbe8) **[판독]**. 데이터 열 `NiceBall_Armor`의 배율은 [damage_hit.md §4.6](damage_hit.md#46-damagerateinfo-표-데이터판독) 표에서 봅니다.
- 피격 반응(애니·이펙트)은 0x71024b1510, 0x71024be3b4 경로이며 내용은 미분석 **[미확정]**.

## 8. 다른 기능과의 상호작용

| 상대 | 내용 |
|---|---|
| 탄·리시버 [combat] | 리시버 결과·배율이 끝난 info가 입력. 플레이어는 리스너 0x71024632ec, 오브젝트는 0x7101e4476c |
| 네트워크 [network] | 플레이어: `PlayerNetEvent::Attack`(공격자 기기 → 피해자 조작 기기), `TroubleDie`·`Revival`·`StartArmor`(조작 기기 송신, §6.8.3/§6.9). 오브젝트: `spl::AttackEvent`(모든 기기 적용). 원격 HP = `PlayerNetState`+0x6c → PD+0xee0(§6.10), 리스폰 착지 단계 = `RespawnLand` 변형 → 본체+0xf34 |
| 상태기계 [state] | Dead(0xe6) 요청(사망 시작), 리셋 후 WaitHold(0x56), ToHumanRespawn(0xe9/0xea) → WaitRespawn(0xe4) → ToSpawner(0xe5) → Injection_Pre(0xbb) (§6.8.4) |
| 스테이지 [gimmick] | 리스폰 지점 = 스폰 관리자 `*0x7105863d00` 표(§6.8.5), 데이터 `LocatorSpawner` 연결은 미확정 |
| 대전 규칙 | `VersusReferee` vt+0x50이 Chase 보정(트리컬러만 0이 아님, §6.5) |
| 이동 [player] | 넉백은 0x71024c8318이 (넉백×3600)을 물리 메시지로 보냄. 적잉크 이동 감속은 [player] 문서 |
| 기어 [player] gear_skills | OpInk_DamagePerFrame/Lmt/ArmorHP(+0x110/114/118), RespawnTimeSave(+0xf0/f4), 서브 데미지 배율(PlayerParam+0x11c~+0x12c, 리스너에서 서브 종류별 적용, 전역 0x71058e87c8 조건) |
| UI [ui] | 본체+0xd60/+0xde0/+0xdf0/+0xe0c(>0이면 Down 아이콘) = T+8/T+0x88/T+0x98/T+0xb4 쓰러짐 타이머 |

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈 (웹 권장 이름)

| 모듈 | 책임 | 원본 |
|---|---|---|
| `hpHolder.ts` | §6.1 그대로 | 0x7101a88ce0 / 88e1c / 89524 / 89790 / 8905c |
| `playerDamage.ts` | 리셋, 적용 0x71024b0c70, 예측 HP | §6.3, §6.6 |
| `inkDamage.ts` | §6.2 | 0x710268b3b8 일부 |
| `playerLife.ts` | 프레임 순서(§3.4), 회복률(§6.4), 사망 판정·시작(§3.5, §6.5) | 0x7102483134, 0x710245ff9c |
| `netDamage.ts` | Attack/TroubleDie 송수신, 생명 번호 검사, 조작 기기 판정 | §3.2, §6.7 |
| `respawn.ts` | T 타이머(§6.8.2), revive/reset(§6.8.3), ToHumanRespawn 요청·리스폰 착지 단계(§6.8.4), 지점 선택(§6.8.5), `Revival` 송수신 | 0x71024a2c98 일부, 0x710249e2bc, 0x710249eec4, 0x710249cb60, 0x710245fd38 |
| `armor.ts` | startArmor(§6.9), 활성·해제·파괴 유예 | 0x710243c1c4, 0x710243ba44, 0x710243b93c, 0x710243bc78 |
| `invincible.ts` | §6.11 조건(구현된 기능만 연결, 나머지는 거짓 고정임을 표시) | 0x71024c7624 |

### 9.2 순서

1. `hpHolder` + `life_hp.py`와 같은 테스트(원본 실행 비교 데이터 재사용 가능).
2. 적 잉크(§6.2)와 무데미지 프레임.
3. 피해 적용(아머 없이) → 아머 분기.
4. 회복률 선택(조건은 우선 "잠수 중" 하나로 근사, 근사임을 표시).
5. 사망 판정·시작, 대기 시간.
5-1. 리스폰: T+8 감소 → revive → reset(T+0 60 / T+4 15 / T+0xf4 59) → ToHumanRespawn → WaitRespawn. `web/tools/respawn_emu.py`의 기대 프레임(§6.8.6)을 테스트로 씁니다. 리스폰 착지(발사) 단계 2~5는 writer 미확정이라 우선 입력 하나로 단계 2를 넣는 근사로 두고 근사임을 표시합니다.
5-2. 아머: startArmor → 활성(GameFrame ≥ 시작) → 피해 분기(§6.3).
6. 네트워크: 서버 권위로 바꿀 경우에도 "피해자 조작 쪽이 HP를 줄인다"를 서버 한 곳으로 옮기는 것과 같습니다. 예측 HP(§6.6)는 클라이언트 표시용으로 유지.

### 9.3 원본과 똑같이 지킬 것

- 데미지는 **누적 후 프레임 갱신에서 한 번에** 반영합니다. 같은 프레임 여러 히트는 합산되고 `lastHit`은 가장 큰 단일 히트입니다.
- 회복 대기 60은 피격 프레임에서 바로 59로 줄어듭니다.
- 감소/회복 누적은 f32 소수 누적(`floor`)입니다.
- 적 잉크 상한 `max(…, 0)`은 디컴파일에 없지만 명령에 있습니다.
- 사망 판정은 `hp < 1`이고 다른 쓰러짐 타이머가 모두 0일 때만입니다.
- 리스폰 리셋은 같은 프레임의 T+0/T+4/T+0xf4 감소보다 **먼저** 실행됩니다(0x71024a2c98 안 순서). 그래서 리셋 프레임에 이미 59/14/58이 됩니다.
- 원격 기기는 T+8을 1에서 멈추고 `Revival` 수신 때만 리셋합니다(조작 기기만 타이머로 부활).
- 아머 원인은 작은 번호 우선입니다. 더 작은 번호 원인이 걸려 있으면 새 startArmor는 무시됩니다.

## 10. 검증

| 종류 | 내용 | 결과 |
|---|---|---|
| **원본 실행**(unicorn) | `PY web/tools/life_emu.py`: 원본 0x7101a88ce0으로 홀더를 만들고 무작위 시나리오 40개 × 240프레임(flags 0/2/3/4/6/7, max 200~8000, 감소율·회복률 여러 값, 피격 0~99999·음수, 회복)을 원본 0x7101a89524/0x7101a89790/0x7101a8905c와 재구현 `life_hp.py`에 똑같이 넣고 hp·누적·대기·마지막 피격·공격자 비교 | 9,600프레임 **불일치 0** (`analysis/life/emu_hp_holder.txt`) |
| 스텁 | PLT memcpy/memset/strlen만 파이썬으로 처리, 그 밖 외부 호출은 0 반환. bss 상수 +0x1c0(60)은 정적 초기화 에뮬 값으로 써 넣음 | 홀더 함수는 다른 게임 함수를 부르지 않아 스텁 영향 없음(문자열 복사 가상 함수는 원본 코드 그대로 실행) |
| 재구현 계산 | `PY web/tools/life_hp.py selftest`: 적잉크 데미지 7건, 동시 2히트 1건 | 8/8 OK |
| 원본 명령 판독 | 적잉크 상한 `fmax`(0x710268bd30), 회복률 선택(0x71024a4178~0x71024a41a4), 미션/대전 경로 분기(0x71024a2dcc~0x71024a2df4) | 디스어셈블 직접 확인 |
| **원본 실행**(unicorn) A | `PY web/tools/respawn_emu.py` A: 원본 0x710249e2bc → 0x710249cb60(재시작 cRespawn, 홀더 리셋 0x7101a88e1c 포함)을 실행. 스폰 관리자 팀별 F = 1/0 | F=1: T+0 60, T+4 15, T+0xf4 59 / F=0: 120, 75, 119. 두 경우 HP 1000/1000, PD+0xee0 = +0xee4 = 1000, 위치 = 리스폰 지점 포즈(7.5, 33.5, 106.5). 기대와 **일치** |
| **원본 실행** B | 0x71024a2c98을 매 프레임 실행(조작 기기, T+8 = 390 시작). revive·reset도 원본 그대로 이어서 실행 | F=1: 390번째 호출에 리스폰, 404에 0x710245fd38 호출, 448에 T+0xf4 = 0, 449에 T+0 = 0 / F=0: 390, 464, 508, 509. §6.8.6 기대와 **일치** |
| **원본 실행** C | 조작 기기 아님(넷 +0x48 = 0, +0x44 ≠ 로컬), T+8 = 5 시작 | T+8: 4,3,2,1,1,1,1,1, 리스폰 없음 — **일치** |
| **원본 실행** D | 무적 판정 0x71024c7624를 조건 하나씩 켜 16회 실행(인자는 호출부 0x7102484224 배치) | 모두 0 → 거짓, f34 = 3 → 거짓, 나머지 14개 → 참 — **일치**(§6.11) |
| 스텁(B~D) | 허용 함수 = 0x71024a2c98, 0x710249e2bc, 0x710249cb60, 0x7101a88e1c, 0x7101a88ce0(준비), 0x71024c7624. 그 밖 게임 함수는 x0 = 0 반환 스텁(호출 기록), PLT memcpy/memset/strlen은 파이썬. 메모리: reloc 이미지 + 플레이어 정적 초기화 상수(`bss_consts_58bb000.json`) + 0 채운 널 페이지(0~0x400000) + 가짜 본체 0x10000 B와 컴포넌트 포인터 표(+0xa600~+0xa910)마다 0 버퍼 | 스텁 영향: 0x710245fd38(상태 요청), 상태기계 리셋 0x710243dcf8, 카메라 리셋, 넷 송신, 스폰 관리자 함수는 **실행 안 함**(호출 시점만 확인). 그래서 상태 전이·Revival 내용·지점 선택은 판독 수준. 결과 `analysis/respawn/emu_respawn.txt` |

**검증되지 않은 범위**: 0x71024b0c70(아머·코옵 분기 포함)는 실행하지 않았습니다. 적잉크 비율(S+0x48) 계산, 회복률 조건, 사망 판정·사망 시작 0x710245ff9c, startArmor 0x710243c1c4는 판독만 했습니다. 원격 HP 필드(§6.10)는 판독입니다. 타이머 원본 실행은 단일 함수 체인(0x71024a2c98 → revive → reset) 실행이며 프레임 전체(0x7102483134와의 순서)를 검증한 것이 아닙니다.

## 11. 미확정 사항

2026-10-02 [respawn] 3차에서 바뀐 항목은 상태 칸에 전 → 후를 적었습니다.

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| 리스폰 전이 | [미확정] 일부 → **[판독 + 원본 실행]**(§6.8): T+0/T+4/T+0xf4 writer = 리셋 0x710249cb60, 리스폰 실행 = 0x710249e2bc(조작 기기, T+8 1→0) / 0x710249eec4(원격, `Revival`), HP 리셋 연결, WaitRespawn → ToSpawner 조건(본체+0xf34 ∈ 2~4). **정정**: T+0x103 경로는 미션 전용 | 남은 것: 조작 기기에서 리스폰 착지 단계 2~5를 넣는 writer(발사 입력), T+0x103 소비자(미션 경로), 사망 시작과 0x71024a2c98의 프레임 안 순서 |
| 리스폰 지점 선택 | [미확정] → **[판독]**(§6.8.5): 스폰 관리자 `*0x7105863d00` 팀·순번 표 | 표를 채우는 코드(데이터 `LocatorSpawner` 연결), 관리자 클래스 이름 |
| 원격 HP가 담긴 PlayerNetState 필드 | [추정] → **[판독]** `PlayerNetState`+0x6c (u10) → PD+0xee0 (§6.10) | — |
| 아머 HP 설정(StartArmor) | [미확정] → **[판독]** 0x710243c1c4 (§6.9) | 원인 번호 1~5 ↔ 무기·스페셜 이름, 원인별 종료 프레임(+0xf00~) writer |
| 무적 판정 0x71024c7624의 각 조건 | 조건 목록 [판독] → **조건별 출처 컴포넌트 [판독] + 표 15줄 중 9줄 원본 실행(16회)** (§6.11). T+0xf4 = 리스폰 무적 확정 | 본체+0x9210~+0x9213, +0x925c 구조체, T+0x101, 넷 상태 7~11, 스페셜 0x1b/0x1c의 이름 |
| 모드별 사망 보정(관리자 vt+0x50) | [미확정] → **[판독]**: `VersusReferee` 싱글턴, 트리컬러만 팀 2 → Defense 120 / 그 밖 Offense 0, 다른 규칙 0 (§6.5) | 트리컬러 팀 번호 2의 경기상 역할, 파라미터 데이터 파일(기본값만 확인) |
| 기어 RespawnTimeSave 적용식 | [판독] 유지, 적용 조건 문장 정리(§6.5) | 본체+0xd70, +0xa5a0, PP+0x5c 의미 |
| 전역 플래그 이름 | [미확정] → **[판독]**: 0x71058e877c `Scene_Versus`, 0x71058e8784 `Scene_Mission`, 0x71058e87a4 `Scene_Coop`, 0x71058e8788 = 씬 이름이 `"World"`(0x7102b546e0 씬 분류 비트, 이름 정적 0x71058e90f0/0x71058e9150/0x71058e9270) | 0x71058e87c8, 0x71058e87ac(UI 문서: Lobby) |
| 플레이어 홀더 감소율(+0x120) | writer 못 찾음 | 플레이어에서 0이면 쓰지 않는 기능일 수 있음 |
| 피해 적용의 '무기 종류1' 즉시 경로 | [미확정] | 0x7101a81a68 종류 값 |
| 리스폰 후 T+0 = 0에서 바꾸는 PlayerCollision 객체(0x7103ae4c48) | [미확정] | 0x7103ae4c48 (Phive 쪽 추정) |
