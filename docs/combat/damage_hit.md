# 피격·데미지·타격 판정 (combat)

Splatoon 3 v0 원본에서 **탄이 무언가에 맞았을 때 데미지 값이 정해지고, 대상에게 전달되어 배율이 곱해지고, 넉백·히트 이펙트가 만들어지기까지**를 정리합니다. 주로 슈터 탄(`spl::BulletShooterBase`)을 따라갔고, 같은 수신 경로를 쓰는 다른 무기에도 적용되는 부분은 그렇다고 적었습니다.

- 작업 지침: [../../분석.txt](../../분석.txt). 확정 수준 표기: **[실행] [판독] [데이터] [추정] [미확정]** ([README](../README.md)).
- 탄 이동(GoStraight/Brake/Free)과 탄 나이(age) 증가 순서: [weapon/shooter_bullet.md](../weapon/shooter_bullet.md) ([bullet] 담당). 여기서는 그 결과(age, 속도)를 입력으로만 씁니다.
- 공용 사실 게시판: `analysis/notes/SHARED.md`, 함수 의미 표: `analysis/notes/FUNCS.tsv`(이 문서의 함수는 area=`combat`).

상태: **분석 진행 중**. 탄 쪽 계산(데미지 감쇠, 충돌 반경, 넉백, 크리티컬 누적)과 수신 쪽 배율 적용은 판독을 마쳤습니다. 2026-10-03 [r5 combat]: 데미지 감쇠·반경·넉백·크리티컬 링·수신 결과 판정(이력 모드 1~6·시간 창 포함)·이력 나이·히트마커 플래그를 **원본 함수 실행(unicorn)으로 재구현과 비트 대조**했습니다(불일치 0, §10). 조준 히트마커 조건을 새로 판독했습니다(§6.7). 수신 이후의 **플레이어 HP 감소·자연 회복·적 잉크 지속 데미지·아머·사망 판정과 피해 적용 기기**는 [player_life.md](player_life.md)로 분리했습니다(HP 홀더는 원본 실행 일치). 남은 것은 §11. 웹 구현은 없습니다.

---

## 1. 기능 개요와 사용자에게 보이는 동작

1. 슈터 탄의 데미지는 **날아간 프레임 수(탄 나이)**에 따라 `ValueMax`에서 `ValueMin`까지 선형으로 줄어듭니다. 스플래시슈터는 36.0에서 18.0까지 줄어듭니다.
2. 탄의 충돌 구는 두 개입니다. 지형용(GroundOnly)과 플레이어·오브젝트용(ExceptGround)이고, 반경은 나이에 따라 `Init*`에서 `End*`로 바뀝니다.
3. 맞은 대상이 받는 데미지는 `DamageRateInfo` 표의 배율을 곱한 값입니다. 행은 무기 계열(`Shooter`, `ChargerFull` 등), 열은 대상 종류(`Default`=플레이어, `BulletUmbrellaCanopyNormal`=우산 등)입니다.
4. 같은 팀 탄은 같은 팀 플레이어를 통과합니다(충돌 레이어 `SplInkBullet_FriendThrough`). 같은 팀 탄이 리시버에 닿더라도 결과는 `Through`이고 데미지는 0이 됩니다.
5. 한 발(같은 샷 ID)의 탄 여러 개가 한 대상에게 합계 1000(100.0) 이상 맞으면 그 히트는 `CriticalHit`로 표시됩니다.
6. 맞은 대상에게는 탄 진행 방향의 수평 넉백 벡터가 전달됩니다. 크기는 데미지에 따라 95에서 280까지 변합니다.
7. 히트 결과(`Damaged`, `Armored`, `Invincible`, `Through` 등)와 무기 종류에 따라 `HitEffectConfig` 표에서 이펙트(E1/E2)와 사운드(S1/S2)를 고릅니다. 결과가 `Through`(0)이면 히트 이펙트 자체가 생기지 않습니다(§3.2).
8. 조준 표시의 히트마커는 "지금 쏘면 맞을 대상"을 미리 보여 주는 표시입니다. 탄 궤적을 예측해 상대 팀 리시버에 닿으면 `WpShtrHitMarker`, 지형 등 리시버 없는 곳이면 `WpShtrFieldHitMarker`, 아무것도 없으면 히트마커 없이 가운데 점만 보입니다(§6.7).

## 2. 분석 대상 원본·버전·자료 위치

| 항목 | 값 |
|---|---|
| 원본 | Splatoon 3 v0 XCI, main NSO(심볼 없음), 0x7100000000 기준 ([00](../00_extraction_pipeline.md), [02](../02_code_and_params.md)) |
| 데미지 배율 표 | `romfs/Pack/Bootup.Nin_NX_NVN.pack.zs` → `System/CombinationDataTableData/spl__DamageRateInfoConfig.pp__CombinationDataTableData.bgyml` → JSON `analysis/combat/DamageRateInfoConfig.json` |
| 히트 이펙트 표 | 같은 팩 `System/CombinationDataTableData/Default_spl__HitEffectConfig...bgyml` → `analysis/combat/HitEffectConfig.json` |
| 무기 → 배율 행 | `romfs/RSDB/WeaponInfoMain.Product.100.rstbl.byml.zs` → `analysis/combat/rsdb/WeaponInfoMain.json` (`DefaultDamageRateInfoRow`, `ExtraDamageRateInfoRowSet`, `DefaultHitEffectorType`) |
| 탄 데미지·충돌 파라미터 | `extracted/params/Component/GameParameterTable/Weapon*.json` (`DamageParam`=`spl__BulletShooterDamageParam`, `CollisionParam`=`spl__BulletSimpleCollisionParam`) |
| 수신 측 파라미터 | 같은 폴더 `SplPlayer`, `Bullet*`의 `spl__DamageParam`(DamageReceiverArray / HitPointHolderArray / DamageSenderArray) |
| 탄 형상 | Bootup 팩 `Phive/ShapeParam/BulletShooterBase.phive__ShapeParam.bgyml` → `analysis/combat/BulletShooterBase.phive__ShapeParam.json` |
| 충돌 레이어 표 | [gimmick] 산출물 `analysis/gimmick/PhiveConfig.json` → 탄 행만 `analysis/combat/layer_filter_bullet.json` |
| 디컴파일 | `analysis/decomp/combat/batch1~4.c`, 탄 vtable 전체 `analysis/decomp/bullet/BulletShooterBase_vt.c`, 조준 예측·PlayerCollision `analysis/decomp/r5_combat/b1~b3.c` |
| 도구 | `web/tools/r5_combat_emu.py`(원본 함수 unicorn 실행 대조 A~F, 2026-10-03), `web/tools/combat_damage.py`(재구현·검증), `combat_param_reader_scan.py`(파라미터 리더 위치 스캔), `combat_callers.py`(BL 호출자), `combat_vtname.py`(vtable 이름 반환 함수), `combat_layers.py`(레이어 표 추출) |

## 3. 진입점과 전체 호출 흐름

### 3.1 매 프레임 (탄 쪽)

`spl::BulletShooterBase` vtable `0x71055a5030` 기준 슬롯 번호입니다 **[판독]**.

```
슬롯18 0x71016460fc  탄 갱신 ([bullet] 문서)
  ├─ prevPos(+0x110) 저장
  ├─ age(+0x134) += 1          (슬롯73이 거짓일 때)
  ├─ 슬롯54 0x7101750d6c 이동  → 첫 줄에서 데미지 캐시 +0x11f0 = -1 로 무효화
  └─ 슬롯57 0x7101764ef8      → 충돌 반경 갱신
        r_field  = 0x71018a6b68(CollisionParam, age) → 바디(+0x138) vt+0xd0
        r_player = 0x71018a6fe4(CollisionParam, age) → 바디(+0x138) vt+0xd8
```

### 3.2 접촉 시 (탄 쪽 → 수신 쪽)

물리 접촉 콜백이 슬롯22를 부릅니다. 접촉 콜백을 부르는 시점(탄 갱신 전인지 후인지)은 확인하지 못했습니다 **[미확정]**. → 정정(2026-10-03 [r5 combat]): **[판독]**. 슬롯22는 물리 스텝 안이 아니라 `PhysicsContactReactionSequencer(Entity)`가 단계1 그룹0에서 큐를 비울 때 불리며, 이는 같은 프레임의 모든 액터 슬롯18과 Phive 월드 갱신 뒤, 슬롯19·20·21 앞입니다([physics/phive_controller.md §6.7](../physics/phive_controller.md), [r5 physics]). 그래서 이동 접촉의 첫 명중 age는 0입니다([hitbox.md §1](hitbox.md)).

```
슬롯22 0x71017504f4  OnHit(this, contact)
  1. dmg = 0x71017506d0(this)            → this+0x11f0 에 캐시          [판독]
  2. if 0x7101649a18(this, contact)      (대상이 판정 대상인지)
       && 공격자(생성정보+0x1c)가 플레이어 ID 이고 접촉 플래그 조건 만족
       → crit = 0x71016e6260(전역 *0x7105797f18, contact, 플레이어인덱스(0x71026437d0, 실패 시 0),
                              샷ID=생성정보+0x94, dmg, 1000, 생성정보+0x92)
         this+0x11ef = crit                                            [판독]
  3. → 0x7101763310 (같은 함수의 뒷부분)
       extra = 슬롯95 0x7101753b90()     (+0x11ef 이면 17=CriticalHit, 아니면 생성정보+0x91<<3)
       0x71016498bc(&info, this, extra)  DamageInfo 초기화, 배율 행 이름 결정
       슬롯83 0x7101753a54(this,&info)   info.damage = 캐시(+0x11f0)
       kbParam = {95.0, 300, 280.0, 2000, 0.0}; 슬롯96(no-op) 덮어쓰기 기회
       vel = 슬롯49 0x7101762d00()       (+0x1118 속도)
       info.knockback = 0x7101e66c4c(up=(0,1,0), info.damage, vel, kbParam)
       res = 0x71012d4adc(contact, &info) → 대상 액터의 리시버마다 전달 (§3.3)
       슬롯100(no-op)(this, res)
       if BulletHitEffect(+0x158) && 슬롯72(=슬롯71 위임) 통과:
           슬롯97, 히트 방향 = normalize((1-k)*접촉법선 - k*속도방향), k=슬롯103=0.5
           (*(this+0x1190))[0] (…)        콜백 객체, 기본 vtable 0x710559c250 슬롯0 = ret
           0x71016d99f4(BulletHitEffect, contact, 방향, &info) → 0x71016d9c60 히트이펙트 넷이벤트
  4. 0x7101646910(this, contact)         대상 종류에 따라 슬롯58/59/60 (바닥/벽/기타 착탄 처리, [bullet]/[paint])
```

**히트 이펙트 발생 조건 [판독]** (2026-10-03 [r5 combat], `0x7101763310` 뒷부분·`0x71016d99f4`·`0x71016d9c60`): OnHit은 3단계의 `res`(리시버 결과의 최댓값)로 info 첫 칸을 덮어쓰고(`info[0] = res`, `info[1] = −1`) 히트 방향을 info+0x10..+0x18에 넣은 뒤 `0x71016d99f4`를 부릅니다. `0x71016d99f4`와 `0x71016d9c60`은 둘 다 **첫 칸(결과)이 0(Through)이면 바로 돌아갑니다**. 따라서 같은 팀 탄(결과 Through)이나 리시버가 없는 대상(막는 접촉이 없으면 결과 0)에는 히트 이펙트 이벤트가 생기지 않고, 지형처럼 리시버 없이 막는 접촉이면 결과 1(Constant)로 이벤트가 생깁니다. 이벤트는 `0x71027b4704(*0x7105798618, &event)`로 넘어갑니다(소비 쪽 [미확정], [effect_sound]). 이벤트 위치는 접촉 목록에서 첫 막는 접촉(+0x68 비트1, 없으면 첫 접촉)의 점이고, 쌍 방향 바이트 조건에 따라 그 접촉의 +0x30 값 × +0x10 벡터만큼 옮깁니다. 방향은 info+0x10이 NaN이 아니면 그 값, NaN이면 `0x71012d4f8c`가 접촉에서 구한 벡터입니다. 그 밖에 접촉 재질 값(+0x38/+0x48 중 쌍 방향으로 고른 u32)과 `0x71012d68cc` 결과 1비트를 넘깁니다 **[판독]**.

### 3.3 수신 쪽

```
0x71012d4adc(contact, info)
  대상 = contact 의 상대 바디 사용자 액터(+0x70/+0x78), 그 액터+0x238 = 송신자/데미지 컴포넌트(sender)
  for 리시버 in 대상 리시버 목록 (+0x248, 개수 +0x240 / 다른 종류는 +0x160, +0x158):
      copy = 0x71017db2d4(info)
      result = 리시버.vt+0x38(copy, sender)   = 0x7101a86ec0 computeResult
      리시버.vt+0x40({copy.damage, result, flag}, copy, sender) = 0x7101a87e24 apply → 리스너 통지
  반환 {max(데미지), max(result), flag}
```

`0x71012d4adc`는 탄 클래스 80여 곳에서 호출됩니다(`combat_callers.py`). 수신 처리는 무기 종류와 무관하게 공통입니다 **[판독]**.

## 4. 구조체·필드·상수·열거형

### 4.1 `spl::BulletShooterDamageParam` (GameParameterTable `DamageParam`)

팩토리 `0x7101521104`, 방문 함수 `0x71015211c8`, vtable `0x710558e2a0` **[판독]**.

| 오프셋 | 플래그 | 이름 | 타입 | 기본값 | 단위 | reader |
|---|---|---|---|---|---|---|
| +0x38 | +0x40 | ValueMax | s32 | 180 | 0.1 HP | 0x71017506d0 |
| +0x3c | +0x41 | ValueMin | s32 | 120 | 0.1 HP | 0x71017506d0 |
| +0x34 | +0x42 | ReduceStartFrame | s32 | 8 | 탄 나이(프레임) | 0x71017506d0 |
| +0x30 | +0x43 | ReduceEndFrame | s32 | 24 | 탄 나이(프레임) | 0x71017506d0 |

필드를 읽을 때는 '설정됨' 플래그가 0이면 `$parent` 체인을 따라 부모 파라미터 객체로 올라갑니다 **[판독]**([bullet] 확정 사실). 예: `WeaponShooterNormal_Coop`은 `ValueMin`만 300으로 덮어씁니다.

**단위 [데이터]+[판독]**: 데이터의 데미지·HP 정수는 0.1 HP 단위입니다. `ValueMax 360` = 36.0. 근거는 다음과 같습니다.
- 비컨·스프링클러 `MaxHitPoint 1200`, 퀵 어뢰 200 등 HP 값이 같은 정수 체계입니다 [데이터].
- 크리티컬 누적 판정이 상수 `1000`(=100.0, 플레이어 한 명 분량)과 비교합니다 [판독, 0x71017504f4 `mov w5,#1000` 인자].
- 넷 이벤트 `spl::AttackEvent` 0x30 필드가 17비트입니다([network] `analysis/network/bitlayout.txt`). 수신 상한 99998(§6.4)을 담을 수 있는 폭입니다 [추정].

플레이어 최대 HP는 **1000** 입니다 **[판독]**: `spl::PlayerDamage` 리셋(슬롯13 0x7102506960)이 HP 홀더 최대값(PlayerDamage+0x78)에 `0x3e8`을 씁니다. HP 필드는 PlayerDamage+0x7c입니다([player_life.md §4](player_life.md#4-구조체필드상수)). (이전 판의 '[추정]'을 정정)

### 4.2 `spl::BulletSimpleCollisionParam` (`CollisionParam`)

방문 함수 `0x710153abfc`, 팩토리 `0x710153ab24` **[판독]**. 기본값과 슈터 데이터:

| 오프셋 | 플래그 | 이름 | 타입 | 기본 | 스플래시슈터 | reader |
|---|---|---|---|---|---|---|
| +0x48 | +0x4c | InitRadiusForPlayer | f32 | 0.2 | 0.2 | 0x71018a6fe4 |
| +0x3c | +0x4d | EndRadiusForPlayer | f32 | 0.2 | 0.2 | 0x71018a6fe4 |
| +0x34 | +0x4e | ChangeFrameForPlayer | s32 | 0 | (없음=0) | 0x71018a6fe4 |
| +0x40 | +0x4f | FriendThroughFrameForPlayer | s32 | 0 | 0 | 0x7101762f68(시작), 0x7101763a10(이동) — §4.8 |
| +0x44 | +0x50 | InitRadiusForField | f32 | 0.2 | 0.2 | 0x71018a6b68 |
| +0x38 | +0x51 | EndRadiusForField | f32 | 0.2 | 0.2 | 0x71018a6b68 |
| +0x30 | +0x52 | ChangeFrameForField | s32 | 0 | 0 | 0x71018a6b68 |

생성정보(탄 +0x108)의 +0x80 핸들(+0x88 세대 번호)로 이 파라미터를 찾습니다 **[판독]**(0x7101764ef8).

### 4.3 `spl::BulletShooterBase` 객체 필드 (combat 관련)

객체 크기 0x1230, 생성 `0x710174e644` **[판독]**.

| 오프셋 | 타입 | 의미 | writer | reader |
|---|---|---|---|---|
| +0x108 | ptr | 생성정보(무기→탄 공유). +0x1c 공격자 ID, +0x2c 팀, +8 무기 카테고리, +0xc 무기 ID, +0x80 CollisionParam 핸들, +0x91 byte VariableRepeat, +0x92 byte 크리티컬 필요 히트 수, +0x94 샷 ID, +0x110 DamageParam 핸들 | 무기 | 여러 곳. 필드 의미 중 +0x91/+0x92/+0x94는 **[추정]** (쓰이는 방식에서 역추론) |
| +0x134 | s32 | 탄 나이(age). 시작 `0x7101645590`이 −1(정정, 이전 "생성 시 0"), 갱신마다 +1 → 첫 갱신 0 | 0x7101645610, 0x71016460fc | 0x71017506d0, 0x7101764ef8 |
| +0x138 | ptr | 탄 바디(충돌). vt+0xd0/+0xd8 반경 설정 | | 0x7101764ef8 |
| +0x158 | ptr | `spl::BulletHitEffect` 헬퍼 | 슬롯36 0x71015315d0 | 0x71017504f4 |
| +0x160 | ptr | `spl:DamageHelper` 헬퍼 | 슬롯36 | `spl:DamageHelper`는 HitPointHolderArray의 HP 홀더를 가진 **피해 수신 액터 쪽 컴포넌트**입니다(0x220 B, 생성 0x7101e3d53c, [player_life.md §3.6](player_life.md#36-오브젝트비컨스프링클러-등와-spldamagehelper-판독)). 탄 객체에서의 이 포인터 용도는 **[미확정]** |
| +0x11b0 | ptr | `spl::KnockBackHelper` 헬퍼 | 슬롯36 | `spl::KnockBackHelper`(0x38 B, vtable 0x71055ebff8, 생성 0x7101e65a7c)는 슬롯25 0x7101e046b0이 액터의 메인 컴포넌트(타입 GOT 0x7105793118)를 +0x30에 바인딩하는 것 외에 상태가 없습니다 **[판독]**. 넉백 벡터 계산은 같은 모듈의 자유 함수 0x7101e66c4c입니다. 탄 쪽 사용처는 **[미확정]** |
| +0x1118 | vec3 | 속도 | 슬롯50 | 슬롯49 0x7101762d00 |
| +0x1190 | obj | 히트 콜백 객체(vtable 0x710559c250, 슬롯0 = 빈 함수) | 생성자 | 0x71017504f4 |
| +0x11ef | u8 | 크리티컬 히트 래치 | 시작 0x710174efc0에서 0, OnHit에서 0x71016e6260 결과 | 슬롯95 |
| +0x11f0 | s32 | 데미지 캐시. -1이면 미계산 | 생성자 -1, 매 이동 0x7101750d6c에서 -1, OnHit에서 계산값 | 슬롯83 |

### 4.4 DamageInfo (스택 구조체, 0x71016498bc가 초기화)

`0x71016498bc`, `0x71017db2d4`(복사), `0x7101a86ec0`(소비)에서 읽은 필드입니다. 기준 객체는 OnHit 스택의 `sp+0x38` 구조체입니다 **[판독]**.

| 오프셋 | 타입 | 의미 | 초기값 / 출처 |
|---|---|---|---|
| +0x00 | s32 | damage | 0 → 슬롯83이 탄 데미지로, 리시버가 배율 적용값으로 덮어씀 |
| +0x04 | s32 | 공격자 팀 | 생성정보+0x2c (리시버 팀 비교에 사용) |
| +0x08 | u32 | 공격자 ID | 생성정보+0x1c (상위 니블 0xc = 플레이어 계열 판정에 사용) |
| +0x0c..+0x14 | f32×3 | 넉백 벡터 | 0x7101e66c4c 결과. 리시버가 +0x1e0 배율을 곱함 |
| +0x20.. | obj | 무기 식별(카테고리, 0, ID) | 0x7101a81a68 |
| +0x58 | char* | DamageRateInfoRow 이름(버퍼 +0x64, 용량 0x40) | 0x7101a88920(카테고리, ID, ExtraInfo) |
| +0xa8 | u8 | 리시버 **시간 창(R+0x1fc) 판정을 건너뜀**(0이 아니면 §6.4의 시간 창 블록을 실행하지 않음) **[판독 + 실행]**. 정정(2026-10-03 [r5 combat]): 이전 판의 "'반복 히트 제한' 무시 플래그, 의미 [미확정]"을 바로잡음(근거 `0x7101a876a4` `ldrb w8,[x20,#0xa8]; cbz → 시간 창`) | 기본 1 |
| +0xa9 | u8 | 대상 상태·높이 검사 사용(§6.4 첫 줄) **[판독]** (2026-10-03 [r5 combat]) | |
| +0xac / +0xb0 / +0xb4 / +0xb8 | f32 / f32 / f32 / u32 | 기준 높이 / 하한 / 상한 / 0이 아니면 높이 검사 생략. `h = 기준점.y − (+0xac)`, 기준점 = R+0x1f0(NaN이 아니면) 또는 리시버 액터(R+0x180)+0x28c 위치, `h < +0xb0` 또는 `h > +0xb4`면 결과 0 **[판독]** (`0x7101a87018`~`0x7101a87048`, 2026-10-03 [r5 combat]; 이전 "리시버 +0x1ed 조건에서 사용 [미확정]"). 이 값을 채우는 송신 쪽은 [미확정] | |

### 4.5 DamageReceiver (vtable `0x71055c96f8`, 생성 `0x7101a860f0`)

생성자 호출자는 `0x7101e3f5e0` 하나입니다. 데이터는 `spl__DamageParam.DamageReceiverArray` 항목(`spl__DamageReceiverParam`)입니다 **[판독]**.

| 오프셋 | 의미 | 초기값 / 데이터 |
|---|---|---|
| +0x08/+0x10 | 리스너 개수 / 배열(용량 4) | apply가 순회 |
| +0x128 | DamageRateInfoCol 이름(버퍼 +0x134, 용량 0x40) | 데이터 `DamageRateInfoCol`. 플레이어 Main=`Default`, Chariot=`Chariot` |
| +0x178 | Flag 비트 마스크 | 데이터 `Flag`(`spl::DamageReceiverFlagType`: TargetedByBombRobot, TargetedByMultiMissile, CantParasiteSalmonBuddy) |
| +0x170..+0x1a0 | 히트 이력 리스트(항목 0x18+) | |
| +0x1b0 | 이력 최대 개수 | 데이터 `DamageHistMaxSize`(전부 64) |
| +0x1b8 | 팀 판정 모드 | 1 (1=같은 팀 무시, 2=같은 팀이면 Cure) |
| +0x1bc | 소속 팀 | 3(=없음) |
| +0x1c0..+0x1c3 | u8×4 **팀별 히트마커 플래그**(팀 0~3). 조준 예측이 이 리시버에 닿을 때 `HitEffective`(1)인지 `HitConstant`(0)인지 결정 — §6.7 | 매 프레임 `0x7101a86be8`이 다시 계산 **[판독 + 실행]** |
| +0x1c4 / +0x1cc | 추가 배율 / 사용 여부 | 0 / 0 |
| +0x1c8 | 추가 배율 사용 시 결과 덮어쓰기(8=안 함) | 8 |
| +0x1d0 | 판정 대상 아님일 때 결과 | 0 (Through) |
| +0x1d4 | 같은 팀일 때 결과 | 0 (Through) |
| +0x1d8 | 배율 후 데미지 0일 때 결과 | 0 |
| +0x1dc | 중복 히트로 거부될 때 결과(결과>4일 때만 적용) | 0 |
| +0x1e0 | 넉백 배율(NaN=안 곱함) | NaN |
| +0x1e8 | 송신자 필터 모드 | 2 |
| +0x1fc/+0x200/+0x204 | 시간 창: 켜짐(u8) / 간격 겸 배수(s32) / 마지막 허용 카운터(부호로 상태 표시) — §6.4 시간 창 의사코드 **[판독 + 실행]** (2026-10-03 [r5 combat], 이전 "의미 [미확정]") | 1 / 8 / 0 (생성자 `0x7101a86344`~`0x7101a86360` [판독]) |
| +0x208 | 히트마커 플래그 모드: 0 = 팀·추가 결과로 계산, 1 = 네 팀 모두 켬, 2 = 모두 끔, 그 밖 = 바꾸지 않음 | 0 (생성자가 +0x204와 함께 8바이트 0을 씀 `0x7101a86360` [판독]). 다른 writer는 못 찾음 [미확정] |
| +0x20c | 무시할 팀 비트 마스크 | 0 |

이 초기값 일부(+0x1b8, +0x1bc, +0x1d4 등)는 액터 쪽에서 나중에 덮어쓸 수 있습니다. 플레이어 리시버의 실제 팀 설정 값은 확인하지 못했습니다 **[미확정]**.

**플레이어 리시버 설정 [판독]** (2026-10-03 [r5 combat], 이전 [미확정] 해소): 생성자 `0x7101a86314`~`0x7101a86320`이 +0x1b8 = 1(팀 모드 1), +0x1bc = 3(없음)을 쓰고, 플레이어 초기화 `0x71024719d4`(PlayerBehavior 함수 `0x71023538f0`이 꼬리 호출, 인자 본체+0xa5fc/+0xaf0/+0xa8d0/+0x9218/+0xa658)가 DamageHelper 리시버 목록(+0x50/+0x58)의 0번·1번 항목 리시버(데이터 순서로 보아 `Main`·`Chariot` [추정])에 **+0x1bc = 액터+0x668(팀), +0x1e8 = 0(송신자 필터 없음), +0x1fc = 0(시간 창 끔)** 을 씁니다(`0x7102471ad0`~`0x7102471ae4`, `0x7102471b94`~`0x7102471ba8`). 따라서 같은 팀 탄은 팀 모드 1 판정으로 결과 R+0x1d4(기본 0 = Through), 데미지 0입니다. 코옵 좀비가 되면 리스폰 리셋 `0x710249cb60`(`0x710249d2d8`~)이 +0x1bc = 1로, 좀비 해제 `0x71024b270c`(`0x71024b2804`~)가 다시 액터 팀으로 씁니다. `SighterTarget` 리시버는 `0x71021ef704`가 +0x1bc = (로컬 플레이어 팀 == 1 ? 0 : 1)을 씁니다.

### 4.6 DamageRateInfo 표 [데이터]+[판독]

- 98행 × 42열 = 4,116셀이 모두 있습니다. 셀 키는 `"<Row>___<Column>"`입니다.
- 셀 `spl::DamageRateInfoCell`(0x50 B, 팩토리 `0x7101a803f4`, vtable `0x71055c9158`): `DamageRate` f32 +0x44, 플래그 +0x48, **기본값 1.0** [판독]. 데이터에 `DamageRate`가 없는 셀은 1.0입니다.
- 조회 `0x7101a856e8(mgr, rowName*, colName*)` [판독]:
  - 빈 문자열은 `"Default"`로 바꿉니다.
  - `sprintf("%s___%s")` → 해시(0x71038a0d98) → 트리 검색 → 셀의 DamageRate를 읽습니다(부모 체인 적용).
  - 표가 없거나 셀이 없으면 **1.0**을 반환합니다.
- 표 로드: `0x7101a859f0`(경로 문자열 `0x7104956eb5`).
- 행 이름 결정 `0x7101a88920(카테고리, 무기ID, ExtraInfo)` [판독]:
  - 무기 정보 항목 +0x90 + ExtraInfo×0x58에 미리 만든 이름을 씁니다. ExtraInfo > 0x19이면 +0x90(=Normal)입니다.
  - 카테고리 0/1/2가 각각 다른 표를 봅니다. Main/Sub/Special 순서로 보입니다 **[추정]**.
  - 무기 ID 50004/50005/50010(카테고리 무관), 40008(카테고리2·ExtraInfo 11), 40065(카테고리1)는 하드코딩된 이름을 씁니다(주소 0x71055c9760~0x71055c9780의 문자열 포인터).
  - 찾지 못하면 기본 문자열 `*(0x7105790020)`을 씁니다.
  - 무기 정보 항목의 내용은 `WeaponInfoMain`의 `DefaultDamageRateInfoRow`(ExtraInfo=Normal)와 `ExtraDamageRateInfoRowSet{ExtraInfo, DamageRateInfoRow}`로 채워진다고 봅니다 **[추정]**(채우는 코드는 미판독. 이름 필드 visitor 0x7101a80f70/0x7101a811a8만 확인).
- 열 이름: 리시버 +0x128 = 데이터 `DamageRateInfoCol`.

예 [데이터]: `Shooter___Default` = 1.0(키 없음), `Shooter___BulletUmbrellaCanopyNormal` = 0.7, `ChargerFull___BulletUmbrellaCanopyNormal` = 3.0, `Blaster_KillOneShot___MsnBoxL` = 10.0.

### 4.7 열거형 (main 문자열) [데이터]

| 열거형 | 값 (순서 = 정수값, 아래 근거로 확인한 것만 표시) |
|---|---|
| `game::DamageResultType` | Through=0, Constant, Aggregated, NetPriorityFailure, Invincible=4, Armored=5, Damaged=6, Cure=7. 6/7은 0x7101a86ec0 상수로 확인 [판독]. 나머지는 문자열 순서 [추정] |
| DamageEffectorExtraInfo (ExtraInfo) | Normal=0, FullCharge, RollerCore, ExtraBombCore, BlasterWeakBlast, ExtraPaintSplash, ExtraPaintSplashExplosion, SlosherLauncherFollower, ShooterVariableRepeat=8, ShelterCanopy, UltraStampSwing, BlowerInhale=11, ShockSonarWave, SaberShot, SaberChargeShot, SaberSlash, SaberChargeSlash, CriticalHit=17, CurlingDirectHit, MultiMissileDirectHit, JetpackJet, RollerInkNoDamage, SlosherBig, SprinklerInk, ChariotBody, GoldenIkuraAttack. 8과 17은 슬롯95 상수로 확인 [판독] |
| `spl::HitEffectorType` | Default, Shooter, Shooter_CriticalHit, Roller, … (48개, `HitEffectConfig` 행 이름과 같음) |
| HitEffectType(E1) | NoHit, HitConstant, HitEffective, HitBombDead, HitKebaInkCore, ChargeKeep |
| 플레이어 생존 상태 | `Dying, AirFall, WaterFall, RespawnWait, Normal` (등록 0x71026bd6e0), 표시 상태 `Dying, WaterFall, AirFall, RespawnWait, Half, HalfToHuman, Human_RecoverDamage, Human_Normal, Squid_RecoverDamage, Squid_Normal, NoAction`. 소비 코드는 미판독 [미확정] |

### 4.8 충돌 형상과 레이어 [데이터]

- `BulletSimple.game__BulletBodyEntityParam`: `LayerEntity "SplInkBullet_FriendThrough"`, `BlockableLayerHitMask "HitAll"`(0xFFFFFFFF).
- 형상 `BulletShooterBase.phive__ShapeParam`: 구 2개, 둘 다 반경 0.15입니다.
  - `GroundOnly`(마스크 26 = CustomReceiver|Ground|Water)
  - `ExceptGround`(마스크 0x1FFFFFE6 = NoHit·Ground·Water 제외 전부)
  - 런타임에 vt+0xd0/+0xd8로 반경을 덮어씁니다. 0xd0이 GroundOnly, 0xd8이 ExceptGround라는 대응은 **[추정]**(필드 반경 → 지형 구, 플레이어 반경 → 나머지).
- Phive 레이어 필터 표(`LayerEntityParamTableSet` / `…Other` / `…Same`, 값 0=충돌 없음, 1=접촉만으로 보임, 2=충돌). 이름으로 보아 Other=다른 팀 쌍, Same=같은 팀 쌍으로 추정합니다:

| 탄 레이어 × 상대 | Default | Other | Same |
|---|---|---|---|
| SplInkBullet_FriendThrough × SplPlayer | 2 | 2 | **0** |
| SplInkBullet × SplPlayer | 2 | 2 | 2 |
| SplInkBullet_FriendThrough × SplInkShield / SplGreatBarrier / SplBluntWeapon | 2 | 2 | 0 |
| SplInkBullet_FriendThrough × Ground / Water / SplObject | 2 | 2 | 2 |

Same/Other 선택 규칙은 Havok 래퍼 쪽이라 코드로 확인하지 않았습니다 **[추정]**. 전체 행은 `analysis/combat/layer_filter_bullet.json`에 있습니다. → 정정(2026-10-02 [combat4], 2026-10-03 확인): 쌍 판정 `0x7103af44e8`이 두 강체의 필터 객체(강체+0x180) +0x30(u16)을 비교해 하나라도 0이면 Default, 같으면 Same, 다르면 Other 표를 고릅니다 **[판독]** — [hitbox.md §3](hitbox.md). 단 탄 바디 래퍼의 필터 객체는 내부 바디+0x138에 있고(위 레이어 setter), 이 경로가 강체+0x180을 읽는 `0x7103af44e8`을 타는지, 탄 바디의 +0x30 값은 [미확정]입니다(hitbox §3 표).

**`FriendThroughFrameForPlayer`(FTF)가 레이어를 바꿉니다 [판독]** (Phive `LayerEntityCollection` 순번 8 = `SplInkBullet`, 9 = `SplInkBullet_FriendThrough` [데이터]):

```
탄 시작 0x710174efc0 → 0x7101762f68:
    if 바디 레이어(vt+0xc0) ∈ {8, 9}: 바디.vt+0xb0( FTF > 0 ? 9 : 8 )      // 0x7101763234~0x7101763268
탄 이동 0x7101750d6c → 0x7101763a10 (age 증가 뒤):
    if 바디 레이어 == 9 && FTF >= 1 && FTF == age(+0x134): 바디.vt+0xb0(8)  // 0x7101763f4c~0x7101763f6c
```

즉 데이터(`BulletBodyEntityParam`)가 `SplInkBullet_FriendThrough`여도 **FTF가 0이면 시작하자마자 `SplInkBullet`(8)로 바뀌고**, FTF>0이면 그 나이가 될 때까지만 FriendThrough입니다. vt+0xc0/+0xb0을 "레이어 읽기/설정"으로 본 것은 값 8/9가 레이어 순번과 맞는 데서 나온 **[추정]**입니다. → 정정(2026-10-03 [r5 combat]): **[판독]**. 탄 바디 래퍼(vtable `0x710559f3f8`/`0x710559f698`, 슬롯4 `0x71016caf20`·슬롯5 `0x71016cafc0`과 같은 표)의 vt+0xb0 = `0x71016cb4c0`이 내부 바디(vt+0x90)의 필터 객체(+0x138)+8 **비트0~5에 값을 넣고**(`bfxil w9, w19, #0, #6`), vt+0xc0 = `0x71016cb538`이 같은 비트를 읽습니다(`and x0, x8, #0x3f`). 바로 다음 슬롯 `0x71016cb4fc`는 비트6~11(하위 층)을 씁니다. 데이터 분포: FTF 0이 60개, 2가 28개, 3이 39개, 4가 5개, 1000이 13개, 1200이 1개(GameParameterTable 전수, 슈터 `WeaponShooter*`는 0). 같은 팀 탄이 `SplInkBullet`(8) 상태로 같은 팀 플레이어에 닿아도 리시버 결과는 Through·데미지 0입니다(§6.4). 물리적으로 막히는지는 Same 표 해석(위 [추정])에 달려 있습니다. 위 표의 '탄 레이어 = FriendThrough'는 데이터 기준이며 실행 중 레이어는 이 규칙을 따릅니다(정정).

### 4.9 기어 파라미터(피격 관련) [판독 — 생성자 기본값, 데이터 파일에는 값 없음]

| 구조체(방문 함수) | 필드 (Low / Mid / High) |
|---|---|
| OpInkEffectReduction 추정 (0x7102378bb0, 문자열 참조 0x710237b610 인접) | OpInk_DamagePerFrame 0.003 / 0.00225 / 0.0015, OpInk_DamageLmt 0.4 / 0.3 / 0.2, OpInk_ArmorHP 0 / 26 / 39 (그 밖에 이동 감속 필드는 [player] 담당) |
| SubEffectReduction 추정 (0x710237fe5c) | DamageRt_BombH 1/0.75/0.5, DamageRt_BombL 1/0.8/0.6, DamageRt_Sprinkler 1/0.75/0.5, DamageRt_Shield 1/0.75/0.5, DamageRt_LineMarker 1/0.75/0.5, MarkingTimeRt 1/0.43/0.1, MarkingTimeRt_Trap 1/0.55/0.1, MoveDownRt_PoisonMist 1/0.75/0.5 |
| RespawnTimeSave 추정 (0x710237c648) | Dying_AroundFrm 90/60/30, Dying_ChaseFrm 270/180/90 |

구조체 이름은 `spl__PlayerGearSkillParam_*` 문자열이 팩토리 근처에서 참조되는 것으로 추정했습니다 **[추정]**. 보간식은 [player] gear_skills.md(원본 에뮬 일치)이고, 결과는 PlayerParam+0x110/+0x114/+0x118(OpInk), +0xf0/+0xf4(RespawnTimeSave)에 저장됩니다. **소비 코드는 [player_life.md](player_life.md) §6.2(적 잉크), §6.5(사망 대기)에서 판독했습니다.**

단위 **[판독]**: 적 잉크 데미지 = `int(DamagePerFrame × 적잉크비율 × 1000)`(0.1HP 단위, 기본 3 = 0.3HP/프레임), 적 잉크만으로는 HP가 `1000 − DamageLmt×1000`(기본 600) 아래로 내려가지 않습니다. `OpInk_ArmorHP`(0/26/39)는 HP가 아니라 **적 잉크에서 데미지가 0인 프레임 수**입니다([player_life.md §6.2](player_life.md#62-적-잉크-1프레임-데미지--0x710268bc7c0x710268bd44-판독-원본-명령-직접-확인)). (이전 판의 '비율로 보임 [추정]'·'단위 미확정'을 정정)

### 4.10 HitPointHolder (오브젝트 HP) [데이터]

| GPT | MaxHitPoint | 리시버 열 |
|---|---|---|
| BulletBeacon | 1200 | Wsb_Flag |
| BulletSprinkler | 1200 | Wsb_Sprinkler |
| BulletBombTorpedo | 200 | Bomb_TorpedoBullet |
| BulletSpGreatBarrier | 1200 | GreatBarrier_WeakPoint / GreatBarrier_Barrier |
| BulletSpBlowerInhale | 8000 | BlowerInhale |
| BulletShelterCanopy*, BulletShield, BulletSpShockSonarGenerator | 0 (다른 곳에서 설정되는 것으로 보임) | BulletUmbrellaCanopy*, Wsb_Shield, ShockSonar |
| SplPlayer | HitPointHolder 없음. 리시버 Main(Default), Chariot(Chariot) | |

HitPointHolder가 데미지를 HP에서 빼는 코드: `spl:DamageHelper`가 대상마다 *HP 홀더*를 갖고, 맞힌 기기의 리스너 0x7101e4476c와 다른 기기의 AttackEvent 처리 0x7101e45f9c가 0x7101a89524로 누적, 매 프레임 0x7101e43218 → 0x7101a8905c가 HP에 반영합니다 **[판독, 홀더 함수는 원본 실행 확인]** ([player_life.md §3.6, §6.1](player_life.md)). 데이터 MaxHitPoint를 홀더 최대값에 넣는 경로는 확인하지 않았습니다.

## 5. 상태 전이와 전체 수명

| 상태 | 시작 | 갱신 | 끝 / 초기화 |
|---|---|---|---|
| 탄 age +0x134 | 생성자 0 → 시작에서 −1(정정) | 갱신마다 +1(이동 전), 첫 갱신 0 | 탄 소멸 |
| 데미지 캐시 +0x11f0 | 생성자 -1 | 매 이동 -1, OnHit 첫 줄에서 항상 다시 계산해 저장 | 슬롯83(getDamage)은 캐시가 0 이상이면 그 값을 쓰고, 아니면 계산 [판독] |
| 크리티컬 래치 +0x11ef | 시작(슬롯15)에서 0 | OnHit에서 덮어씀 | 다음 OnHit |
| 크리티컬 누적 링(전역) | 게임 단위 | 플레이어(0~9)별 8칸 링. 빈 칸(키 -1)에 넣고, 없으면 키가 가장 작은 칸을 교체 | 링 초기화 시점 [미확정] |
| 리시버 히트 이력 | 생성 | 히트마다 추가, 최대 +0x1b0(64)개를 넘으면 가장 오래된 것 제거 | |
| 충돌 반경 | 매 프레임(슬롯57) | age로 다시 계산 | |

## 6. 계산식·조건·상세 의사코드

### 6.1 슈터 데미지 감쇠 — `0x71017506d0` [판독 + 실행]

`ldr w20,[x25,#0x38]` / `ldr w28,[#0x3c]` / `ldr w27,[#0x34]` / `ldr w8,[#0x30]` 다음 꼬리 명령(0x7101750c14~0x7101750c64)을 그대로 옮겼습니다.

```
function shooterDamage(age, Max, Min, Start, End):   // 모두 s32
    denom = End - Start
    if denom == 0: denom = 1                 // subs + cinc eq
    t = f32(age - Start + 1) / f32(denom)    // scvtf, fdiv
    t1 = fmin(t, 1.0)
    if t < 0: t1 = 0                         // fcmp #0 + fcsel mi
    d = (f32(Min) - f32(Max)) * t1 + f32(Max)
    return trunc_toward_zero(d)              // fcvtzs
```

- **원본 실행 [실행]** (2026-10-03 [r5 combat]): `0x71017506d0`을 unicorn으로 그대로 실행해 위 재구현과 3,216건 비트 일치(실제 표본 7종 + 무작위 60종 × age −1~44·100·1000, DamageParam `$parent` 체인 1~3단·필드별 '설정됨' 플래그 무작위). 따라서 **필드별 `$parent` 해석 규칙**도 실행으로 확인됨: 자식부터 그 필드의 설정 플래그가 선 첫 노드의 값을 쓰고, 부모가 없거나 부모 핸들 세대가 맞지 않으면 그 노드의 값(생성자 기본값)을 씁니다. 명령 `web/tools/r5_combat_emu.py`, 결과 `analysis/combat/r5_emu_combat.txt`.
- `+1` 때문에 age == Start에서 이미 1/denom만큼 줄어듭니다. 최솟값에는 age == End-1에서 도달합니다.
- Max == Min이면 상수입니다. 블래스터 데이터가 이 경우입니다(Start -1, End 99).
- 결과는 OnHit 시점의 age를 씁니다. **정정(2026-10-02 [combat4])**: age는 생성 시 0이 아니라 시작(`0x7101645590`, 명령 `0x7101645610`)이 **−1**을 써서 **첫 갱신이 age 0**입니다(이전 판의 "첫 갱신 뒤 age=1"은 틀림). 이동으로 생긴 첫 접촉은 age 0, 생성 위치 겹침은 age −1일 수 있으나 감쇠 시작 최솟값이 4라 첫 명중 데미지는 같습니다. 같은 비행 프레임에서 age가 이전 가정보다 1 작으므로 감쇠 곡선은 한 프레임 늦게 적용됩니다. 근거·프레임 순서 가정은 [hitbox.md §1](hitbox.md#1-탄-age는-1에서-시작한다-판독-명령-직접--정정).

### 6.2 충돌 반경 — `0x71018a6b68`(Field), `0x71018a6fe4`(Player) [판독 + 실행]

```
function bulletRadius(age, Init, End, ChangeFrame):
    if ChangeFrame == 0: return End
    t = clamp01(f32(age) / f32(ChangeFrame))   // fmin 1, fcsel mi→0
    return max(Init + t*(End - Init), 0.02)    // fmax, 0x3ca3d70a
```

**원본 실행 [실행]** (2026-10-03 [r5 combat]): 두 함수를 CollisionParam 체인 1~3단(필드별 플래그 무작위), ChangeFrame 0·음수·양수, age −2~29·100으로 5,280건 실행해 재구현과 비트 일치. ChangeFrame이 음수면 `t = age/Change`가 음수 → 0이 되어 Init 쪽 값(0.02 하한)이 됩니다.

### 6.3 크리티컬 누적 — `0x71016e6260` [판독 + 실행]

```
function critAccumulate(mgr, contact, pIdx, shotKey, dmg, need=1000, needCount):
    if pIdx > 9 or shotKey == -1: return false
    target = contact 상대 바디의 액터(+0x70/+0x78)
    ring = mgr + 0x3c0 + pIdx*0x80          // 8칸 × {target ptr, key s32, dmg s32}
    slot = 첫 key==-1 칸, 없으면 key(u32) 최소 칸
    ring[slot] = {target, shotKey, dmg}
    sum = Σ ring[i].dmg  (ring[i].key==shotKey && ring[i].target==target)
    cnt = 그런 칸 수
    return sum >= need && cnt >= needCount
```

호출 조건(0x71017504f4)은 다음과 같습니다.
- `0x7101649a18`이 참이어야 합니다. 대상 쪽 객체를 형 검사합니다.
- 공격자 ID가 플레이어 계열이고, 접촉 목록에 플래그 +0x8 bit4가 없어야 합니다.

**원본 실행 [실행]** (2026-10-03 [r5 combat]): 같은 관리자 메모리에 3,000번 연속 호출(대상 3개 + 널, 쌍 방향 바이트 4조합, 플레이어 번호 0/1/2/9/10, key −1·증가, 필요 개수 1~3)해 반환값과 링 8칸 내용 모두 재구현과 일치. 실행으로 확인한 세부:
- 빈 칸이 없을 때 교체 칸 = key를 **u32로 비교한 최솟값, 같으면 앞 칸**.
- 대상 = 접촉 쌍 `C+0x38 → [0] → [0]` 객체의 +0x70(쌍 바이트 +8 == +9이고 비트0 = 1, 또는 다르고 비트0 = 0일 때; 단 +0x69 비트4면 0) 또는 +0x78. 대상이 널이면 칸에는 기록하되 결과는 거짓(need 1000 > 0).

인자는 dmg=탄 원 데미지(+0x11f0, 배율 적용 전), needCount=생성정보+0x92 byte, shotKey=생성정보+0x94입니다. 어떤 무기가 needCount를 1보다 크게 주는지는 무기 쪽 코드를 봐야 합니다 **[미확정]**.

### 6.4 수신 배율 — `0x7101a86ec0` (DamageReceiver 슬롯7) [판독 + 실행]

```
function computeResult(R, info, sender):
    if info.flagA9:                                      // [판독] 0x7101a86ef0~0x7101a87048, 실행 안 함(+0xa9 = 0으로만 실행)
        if R+0x1ed: 통과 조건 = R+0x1ec ≠ 0
        else: comp = (R+0x180 액터)+0x510; comp 없으면 통과, comp+0x69 ≠ 0이면 comp+0x68 ≠ 0일 때 통과,
              comp+0x69 == 0이면 [[[comp+0x18]+0x10]+8]+0x40 상태 표의 현재 항목 +8 == 0일 때 통과
        통과 못 하면 return reset(info, 0)
        if info+0xb8 == 0 && 높이 h가 [info+0xb0, info+0xb4] 밖: return reset(info, 0)   // §4.4
    // 송신자 필터 (R+0x1e8, 기본 2)
    if R.mode1e8 == 2: ok = sender.vt30()
    elif R.mode1e8 == 1: ok = sender.vt38() ? sender.vt30() : R.flag1e4
    else: ok = true
    if !ok: return reset(info, R.res1d0)
    team = info.attackerTeam
    if (R.teamMode == 1 && R.team != -1 && R.team != 3 && R.team == team) || (R.ignoreTeamMask >> team & 1):
        return reset(info, R.res1d4)                     // 같은 팀 → 기본 Through(0)
    result = (R.teamMode == 2 && R.team 유효 && R.team == team) ? Cure(7) : Damaged(6)
    if R.extraRateOn:                                    // +0x1cc
        info.damage = fcvtzs((R.extraRate + 1e-5) * f32(info.damage))
        if R.extraResult != 8: result = R.extraResult
    rate = DamageRateInfo(info.rowName, R.colName)       // 0x7101a856e8
    info.damage = fcvtzs((rate + 1e-5) * f32(info.damage))
    if info.damage == 0: return reset(info, (R.extraRateOn && R.extraResult != 6) ? R.extraResult : R.res1d8)
    ObjectEffectUp(R, info)                              // 0x7101a87aa0: 공격자 플레이어가 기어 보유 시
                                                         //   info.damage = (int)(rate("ObjectEffect_Up", col) * f32(dmg))  (엡실론 없음)
    if !isnan(R.kbRate): info.knockback *= R.kbRate
    switch sender.vt20():                                // 이력 모드 1~6, §6.4.1
       거부되면 result = (result > 4) ? R.res1dc : result 이고 데미지·넉백 0
    if R.tw(+0x1fc) && !info.flagA8:                     // 시간 창 [판독 + 실행], 아래 설명
        cur = max(*(*0x7105790610)+0x148, 0)             // 전역 카운터(정체 [미확정])
        if |R.tw204| == cur: R.tw204 = −cur; mult = R.tw200
        else:
            if R.tw204 < 0: R.tw204 = R.tw200 − R.tw204  // = 마지막 허용 + 간격
            if R.tw204 <= cur: R.tw204 = −cur; mult = R.tw200 else mult = 0
        info.damage = fcvtzs(f32(mult) * f32(info.damage))
        if mult == 0: info.knockback = 0                 // 결과는 그대로, 이력에도 데미지 0으로 들어감
    if info.damage > 99999: info.damage = 99998
    handle = sender.vt18(); if handle 없음 || handle.id == −1: return result   // 이력 기록 없음
    if mode == 5: 같은 key(≥0) 항목 하나 삭제
    if 개수 >= R.histMax: 가장 오래된 항목 삭제
    이력 맨 앞에 {age 0, handle, info.damage, key(모드 5면 vt48, 아니면 −1)} 추가
    return result

reset(info, r): info.damage = 0; info.knockback = 0; return r
```

#### 6.4.1 수신 이력과 이력 모드 case 1~6 [판독 + 실행] (2026-10-02 [respawn], 이전 [미확정]; 실행 2026-10-03 [r5 combat])

기준: DamageReceiver R. 이력은 R+0x170을 보초로 하는 이중 연결 목록입니다(+0x188 끝, +0x190 처음, +0x198 개수, +0x1a0 빈 항목 목록, +0x1b0 최대 개수). 항목(노드−0x18 기준) = `+0 f32 age(초)`, `+8 송신자 핸들(참조 카운트, 핸들+0x28 = id, −1이면 무효)`, `+0x10 데미지`, `+0x14 key`(모드 5일 때 vt48, 그 밖 −1).

- **나이 증가**: `0x7101a86dc8(R, dt)`가 모든 항목에 `age = min(age + dt, 15.0)`을 하고 15.0이 되면 지웁니다. 유일한 호출자는 `spl:DamageHelper` 슬롯23 0x7101e43218(목록 +0x50/+0x58의 대상마다 R = 대상+0x58, dt = DamageHelper+0xd8 = 1/60)입니다. 즉 age 단위는 **초**이고 최대 15초 보관합니다. (DamageHelper의 +0x50/+0x58 "두 번째 목록"은 항목+0x58이 리시버인 목록입니다 — [player_life.md](player_life.md) §3.6 정정.)
- **추가**: 통과한 히트는 송신자 핸들이 유효하면 `{age 0, 핸들, 최종 데미지, key}`로 추가하고, 개수가 R+0x1b0 이상이면 가장 오래된 항목을 지웁니다. 모드 5면 추가 전에 같은 key(≥0)의 기존 항목 하나를 지웁니다.

| 모드(송신자 vt+0x20) | 판정 | 송신자 슬롯 |
|---|---|---|
| 1 | 같은 송신자(핸들 같고 id ≠ −1) 항목 중 `age < vt28()`(초)가 있으면 **거부** | vt18 핸들, vt28 f32 간격 |
| 2 | `dmg = max(dmg − Σ(같은 송신자 항목의 데미지), 0)`, 0이면 거부(0x7101a87edc) — 이전 합계를 넘는 만큼만 들어감 | vt18 |
| 3 | `cap = fcvtzs((DamageRate(info 행, R 열) + 1e-5) × vt40())`(ObjectEffect_Up·R 추가 배율도 적용), `Σ = 같은 송신자 합계`, `dmg + Σ ≥ cap`이면 `dmg = max(cap − Σ, 0)`, 0 이하면 거부 — 송신자별 누적 상한 | vt18, vt40 int 상한 |
| 4 | age ≤ FLT_EPSILON(이번 프레임에 추가된) 항목 중 key ≥ 0이면 key == vt48()인 것, key < 0이면 같은 송신자인 것이 있으면 거부 — 같은 프레임 중복 차단 | vt18, vt48 key |
| 5 | 4와 같은 판정 + 통과 시 같은 key 항목을 교체 | vt18, vt48 |
| 6 | 1과 같은 판정, 거부되면 대신 모드 2 판정(간격 안이면 초과분만, 밖이면 전부) | vt18, vt28 |
| 그 밖 | 이력 판정 없음 | |

**원본 실행 [실행]** (2026-10-03 [r5 combat], `web/tools/r5_combat_emu.py` E): `0x7101a86ec0`(모드 2는 `0x7101a87edc`, 모드 3 사본은 `0x71017db2d4`까지 원본 실행)과 이력 나이 `0x7101a86dc8`을 무작위 리시버 60개 × 최대 40히트로 연속 실행해 결과·최종 데미지·넉백·시간 창 상태(+0x204)·이력 목록 전체(순서·나이·핸들·데미지·key)를 재구현과 비교, 3,823건 **불일치 0**. 모드별 거부 경로(1: 6, 2: 25, 3: 29, 4: 1, 5: 4, 6: 6회)와 시간 창 배수 0/1/8 경로를 모두 지났습니다. 실행으로 확인한 세부:
- 이력은 R+0x188을 보초로 하는 이중 연결 목록이고 **새 항목은 맨 앞**(R+0x190), 가득 차면 **맨 뒤(가장 오래된 것)** 를 지웁니다.
- 거부된 히트는 이력에 들어가지 않습니다(결과 = 결과 > 4면 R+0x1dc, 아니면 그대로; 데미지·넉백 0).
- 모드 4·5의 "이번 프레임" = 항목 나이 `−FLT_EPSILON ≤ age ≤ FLT_EPSILON`. key 비교는 정수.
- 모드 3 상한 계산은 info 사본으로 배율(같은 표 조회)·ObjectEffect_Up·R 추가 배율을 다시 곱합니다.
- 송신자 필터 모드 1: `vt38()`이 참이면 `vt30()`, 거짓이면 R+0x1e4 바이트로 통과 여부를 정합니다.
- **시간 창**: R+0x200 하나가 **간격**과 **배수**로 함께 쓰입니다(같은 레지스터 값으로 `sub`와 `scvtf` — `0x7101a87844`, `0x7101a87868`). 같은 카운터 값에서 다시 맞으면 계속 허용되고, 다른 카운터 값이면 마지막 허용 + 간격에 도달해야 허용, 그 전에는 배수 0(데미지 0, 넉백 0, 결과는 Damaged 그대로, 이력에는 0으로 기록). 탄 DamageInfo는 +0xa8이 기본 1이라 이 블록을 건너뜁니다. 어떤 info가 +0xa8 = 0을 쓰는지, 카운터 `*0x7105790610`(= 변수 `0x710580e758`)+0x148의 정체는 [미확정].

스텁 범위(E): DamageRateInfo 조회 `0x7101a856e8`은 시나리오가 정한 배율을 돌려주는 스텁(표 조회 자체는 §4.6 판독), ObjectEffect_Up `0x7101a87aa0`은 아무것도 안 하는 스텁(기어 없음과 같음), 송신자 객체는 가짜 vtable, info+0xa9(높이 필터) = 0 고정이라 그 분기는 실행하지 않았습니다.

**해소(2026-10-03 [r6 combat]) [판독]**: 송신자 클래스(vtable `0x71055bdfd0`)와 기본값(모드 0)·클래스별 functor 52개 표는 [hitbox.md §4](hitbox.md). **슈터 탄 = 모드 0(이력 판정 없음)**, 시간 창도 info+0xa8 = 1이라 건너뜀. 시간 창 카운터 `*0x7105790610` = 변수 `0x710580e758`(GOT 판독) = GameFrame 싱글턴, +0x148 = 게임 프레임 [판독, network 문서의 원본 실행 근거]. 리시버 +0x208 writer(DamageHelper 목록+0x58 경로 스캔): ShelterCanopyBase `0x710172f380`·BulletShield `0x71017458f4`와 연어런·미션 적(SakeBigMouth, Sakediver, Sakedozer, SakelienBomber/CupTwins/Shield, Sakerocket, EnemyRock 등)이 모두 2(히트마커 끔), EnemyCleaner는 1 또는 2. 플레이어·SighterTarget은 쓰지 않음 → 0 [판독].

이전 기록: 송신자(접촉 상대 액터+0x238) 쪽 구현 — 어느 클래스가 어떤 모드·간격·상한·key를 돌려주는지 — 는 찾지 못했습니다 **[미확정]**. 데이터 `DamageSenderArray`는 이름·강체뿐이라 값은 코드에 있습니다. 후보 vtable 자동 스캔(`web/tools/respawn_sender_vt.py`)은 조건을 만족하는 표가 6천 개를 넘어 결론에 쓰지 않았습니다.

`fcvtzs((rate+1e-5)*dmg)`에서 엡실론이 결과를 바꾸는 예가 있습니다. rate 0.344, dmg 843 → **290**(엡실론이 없으면 289) [재구현 계산].

### 6.5 넉백 — `0x7101e66c4c` [판독 + 실행]

인자는 `s0..s2`=up=(0,1,0), `w1`=info.damage, `x2`=속도, `x3`=`{f32 95.0, s32 300, f32 280.0, s32 2000, f32 0.0}`입니다(0x7101763368, 슬롯96은 빈 함수).

```
dir = normalize(vel)
t = (p.b == p.a) ? 1 : clamp01(f32(dmg - p.a) / f32(p.b - p.a))
mag = p.lo + (p.hi - p.lo) * t
v = dir * mag
if up != 0 and dot(up, v) != 0:
    v -= up * dot(up, v)                 // 수직 성분 제거
    if p.blend > 0: 크기 보정(blend==1이면 mag로 복원, 아니면 |v| + blend*(mag-|v|))   // 슈터는 0이라 안 함
return v
```

**원본 실행 [실행]** (2026-10-03 [r5 combat]): `0x7101e66c4c`를 슈터 파라미터 9건 + 무작위 400건(up 0·수평·임의, 속도 0 포함, blend 0/1/0.5/임의)으로 실행해 재구현과 409건 비트 일치. 슈터 값(up (0,1,0), 진행 방향 +Z) 크기: dmg 360 → 101.5294, 1150 → 187.5, 2500 → 280.0. 호출부 `0x71017633a8`~`0x71017633c8`에서 up = (0,1,0)(s0..s2 = 0, 1, 0), 속도 = 슬롯49(vt+0x188), dmg = info.damage, 파라미터 = 스택 {95.0, 300, 280.0, 2000, 0.0}(슬롯96 vt+0x300이 바꿀 기회)임을 명령으로 확인 [판독]. 속도가 0이면 넉백도 0입니다.

플레이어가 받으면 리스너 0x71024632ec가 `v = 넉백 × (1/3600)`, `|v| ≤ 0.48`로 바꾼 뒤(×8.0 조건 = Chariot 사용 중·야구라 탑승 등, [hitbox.md §5.2](hitbox.md)) 0x71024c8318이 `v × 60 × 60`을 플레이어 물리 쪽 메시지로 보냅니다 **[판독]**(즉 95~280은 크기를 3600배로 표현한 값). 물리 쪽에서 이 메시지를 속도에 어떻게 더하는지는 **[미확정]**입니다.

### 6.6 히트 이펙트 선택 [데이터 — 선택 코드는 미판독]

`HitEffectConfig` 셀 키는 `<HitEffectorType>___<ResultType>_<수신 종류>`입니다(17열: Aggregated_/Armored_/Constant_/Cure_/Damaged_/Invincible_/NetPriorityFailure_ × Default/BlowerInhale/Barrier/KebaInk/Water/CoopFloat/Shield). 셀 필드 E1/E2는 이펙트 종류, S1/S2는 사운드 이름(일본어 라벨)입니다. 예: `Shooter___Damaged_Default` = E1 HitEffective, E2 Hit, S1 ヒット, S2 インク被弾.

행은 `WeaponInfoMain.DefaultHitEffectorType`(`Shooter`)과 ExtraInfo에서 정해지는 것으로 봅니다(CriticalHit → `Shooter_CriticalHit`) **[추정]**. 실제 재생은 `0x71016d9c60`이 만드는 `spl::HitEffectNetEvent`를 거칩니다([effect_sound], [network]).

**행 선택 정정(2026-10-03 [r6 combat]): [추정] → [실행]**. OnHit이 sp+0x38 이벤트 정보를 {+0 결과, +4/+8/+0xc}로 만들고 슬롯97 `0x7101765a94`가 +4 = 생성정보+8(카테고리), +8 = 생성정보+0xc(무기 ID), +0xc = 슬롯95(ExtraInfo, 크리티컬이면 17)를 씁니다. `0x71016d9c60`이 `0x71028fed18(카테고리, 무기 ID, ExtraInfo)`로 HitEffectorType 번호(`spl::HitEffectorType` 순서)를 얻어 이벤트+0x34에 넣습니다. 규칙: 무기 ID < 0 → ExtraInfo 3이면 Bomb(26) 아니면 0, 5xxxx → MultiMissile(ExtraInfo 19면 40, 아니면 41; 카테고리 1·ID 50010은 26), 4xxxx → 카테고리 1·ID 40000이면 26, 카테고리 0·ID 42000이면 Charger 계열(ExtraInfo 5→7, 1→6, 그 밖 5), 그 밖 ExtraInfo 5면 33; 카테고리 0/1/2는 무기 정보 표(*`0x710599b420`+0x18 목록 10/11/12, 트리 +0x118/+0xd8)의 ID 노드+0x28[ExtraInfo](ExtraInfo ≥ 26이면 [0]), 노드 없으면 0; 그 밖 카테고리는 ExtraInfo 25면 47. 노드 배열은 행 빌더 `0x7101413a60`이 26칸 모두 행+0x50(DefaultHitEffectorType, `0x7101416108`)으로 채운 뒤 ExtraHitEffectorInfoSet 칸만 덮어씁니다(`0x7101414154`) [판독]. 원본 실행 `PY web/tools/r6_combat_hiteffect_emu.py` 36,900건 불일치 0(WeaponInfoMain 실제 데이터, 카테고리 1/2는 합성 트리, 스텁 없음). 결과: **스플래시슈터 등 대부분 슈터는 크리티컬이어도 `Shooter` 행**, `Shooter_CriticalHit`는 ExtraHitEffectorInfoSet에 CriticalHit가 있는 7행(TripleMiddle 계열)만 [실행 + 데이터].

참고 [데이터]: `Shooter_CriticalHit___Damaged_Default` = E1 `HitMiddleCritical`, E2 `Hit`, S1 `3連ヒット`, S2 `インク被弾`(일반 `Shooter___Damaged_Default`는 E1 `HitEffective`, S1 `ヒット`). 즉 E1은 아래 §6.7의 `HitEffectType` 열거형이 아니라 이펙트 이름입니다. 크리티컬(ExtraInfo 17)이 이 행으로 가는 코드는 [미확정]이고(이벤트 구성 `0x71016d9c60` 안 `0x71028fed18(info[1], info[2], info[3])`가 후보), 스플래시슈터의 `ExtraDamageRateInfoRowSet`은 비어 있어 DamageRateInfo 행은 크리티컬이어도 `Shooter`입니다 [데이터].

### 6.7 조준 히트마커(ShotGuide) — 발생·종료 조건 [판독, 플래그·예측 함수는 실행] (2026-10-03 [r5 combat] 신규)

사격장에서 보이는 슈터 조준 표시(가운데 점·좌우 바이어스·히트마커)는 UI 레이아웃이 아니라 **xlink 이펙트**입니다. ELink 사용자 `PlayerShotGuide`(`analysis/effect_sound/elink2_users.json`)의 콜 테이블 키를 `"<기본 이름>_<HitEffectType 이름>"`으로 찾아 내보냅니다. **히트마커는 "맞힌 뒤" 표시가 아니라 "지금 쏘면 맞을 대상"의 예측 표시**입니다. 실제로 맞힌 뒤의 이펙트·소리는 §6.6 HitEffect 이벤트입니다.

```
spl::PlayerInkActionFree(vtable 0x71056362d8) 슬롯33 0x7102548bec(this, show, predict):   // 슬롯59 0x7102549b38은 this−0x30 썽크
    if !show: +0x88(가운데·히트마커) 이펙트 정지 0x710267739c, +0xb8(바이어스) 정지 0x710267ceb4; return
    if predict: 0x7102548c3c   // 궤적 예측 → this+0x68 = 종류, this+0x50 = 예측 착탄점
    else:       0x71025495e4   // this+0x68 = 0(NoHit), 위치 = 기준점 − 0x710287b104 값 × 방향 × (무기+0x3c8 핸들 파라미터 +0x50 int)
    0x71025498d4               // 이펙트 이름 갱신·위치 설정

0x7102548c3c:
    q.team = 액터+0x668 ([[this+0x120]+0x108]+8]+0x668), q.out = this+0x50, q.steps = (this+0x40 핸들 파라미터)+0x30 int
    q.collision = CollisionParam(무기 +0x3d8 핸들), q.spawn = [this+0x128]+0x18
    this+0x68 = 0x710175779c(*0x71057988b0, &q)
    종류 ≠ 0 && this+0xf0 == 같은 대상 id → this+0xf8 += 1, 아니면 0     // 연속 조준 프레임 [판독, 소비처 미확정]

0x710175779c (예측):                                   // 탄 한 발을 실제 탄과 같은 규칙으로 흉내
    필터: 레이어 = FriendThroughFrameForPlayer > 0 ? 9 : 8, 그룹(+0x30) = (team ∈ {−1,3}) ? 0 : team+1,
          +0x14 = q.spawn+0xc8, 비트12 = (q.spawn+0xcc ≠ 0)
    매 단계: 탄 이동 0x71017697f8로 다음 위치, 반경 = 0x71018a6b68/0x71018a6fe4(param, 단계) → 쓸어 넘기기 질의 0x7101758c94
    첫 접촉 대상 강체 B: B+0x240(리시버 수) == 0 → 1(HitConstant)
                         아니면 B+0x248[0].vt+0x48(&team) = 0x7101a87e8c
    접촉 없이 단계 끝 → 0(NoHit)

0x7101a87e8c(R, &team):  team == −1 → 1;  f = R+0x1c0[team < 4 ? team : 0];  f ? 2(HitEffective) : 1(HitConstant)

0x7101a86be8(R)  — spl:DamageHelper 슬롯20(0x7101e421a4) 끝에서 매 프레임 리시버마다 호출:
    R+0x208 == 2 → 네 칸 0;  == 1 → 네 칸 1;  0이 아니면 그대로
    e = R+0x1cc(추가 배율 사용) ? (R+0x1c8 > 4) : 1
    t = 0..3: R+0x1c0[t] = e && !(R+0x20c >> t & 1) && !(R+0x1b8 == 1 && R+0x1bc ∉ {−1,3} && R+0x1bc == t)
```

이펙트 이름 [데이터 + 판독]: 형식 문자열 `0x710495eb81` = `"%s_%s"`, 뒷부분 = `0x710267e51c`가 열거형 문자열 `"NoHit , HitConstant , HitEffective , HitBombDead , HitKebaInkCore , ChargeKeep"`에서 고른 이름(종류 < 6). 키가 없으면 핸들이 0이 되어 아무것도 나오지 않습니다(`0x7102677578`의 `searchAndEmit`).

| 종류 | `Shooter_Center_*` | `Shooter_HitMarker_*` | `Shooter_BiasLeft_*` / `Shooter_BiasRight_*` |
|---|---|---|---|
| 0 NoHit | `WpShtrSite` | (키 없음 → 표시 없음) | `WpShtrSiteSide` |
| 1 HitConstant | `WpShtrSiteHit` | `WpShtrFieldHitMarker` | `WpShtrSiteSide`(RGBA 0.5) |
| 2 HitEffective | `WpShtrSiteHit` | `WpShtrHitMarker` | `WpShtrHitMarkerSide` |

**사격장에서 보이는 것**: 표적 `SighterTarget`은 리시버 팀을 "로컬 플레이어 팀 == 1 ? 0 : 1"로 두므로([range/shooting_range.md](../range/shooting_range.md)), 기본 팀 모드 1에서 로컬 팀 칸이 1 → 예측이 표적 몸에 닿으면 **HitEffective(`WpShtrHitMarker`)**. Burst 중 리시버 무적 모드(+0x1cc = 1, +0x1c8 = 4)면 e = 거짓 → 0 → 몸에 닿아도 **HitConstant(`WpShtrFieldHitMarker`)**. 지형·리시버 없는 강체에 닿으면 HitConstant, 아무것도 닿지 않으면 NoHit(가운데 점만). Burst 중 표적 몸 강체가 꺼져 질의에 닿지 않는지는 [range] 쪽 판독(몸 끔)에 따릅니다.

**원본 실행 [실행]**: `0x7101a86be8`(모드 0/1/2/3, 팀 모드 0/1/2, 팀 −1~3, 무시 마스크 0~15, 추가 결과 on/off)과 `0x7101a87e8c`(팀 −1/0~3/4/7) 12,000건 재구현과 일치(`web/tools/r5_combat_emu.py` F). 예측 함수 `0x710175779c`·`0x7102548c3c` 자체는 판독만 했습니다.

**호출 조건 (2026-10-03 [r6 combat]) [판독, 의미 일부 미확정]**: 인터페이스(PlayerInkActionFree+0x30, 보조 vtable `0x7105636450`)의 vt+0x60이 슬롯59 `0x7102549b38`(this−0x30 후 슬롯33과 같은 본문)입니다. 0x7102400000~0x7102700000의 vt+0x60 호출 17곳 중 16곳은 (0, 0)(무기 교체 `0x71024901c4` 등 끄기)이고, 값을 계산하는 곳은 `0x71024c0fbc`(호출 `0x710243ade0`, 인자 x0 = 본체+0xa5f9, x1 = 본체+0x588, x2 = 본체+0x678, 스택 = T(본체+0xd58), [본체+0xa650], [본체+0xa898], [본체+0xa6c0], [본체+0xa778]) 하나입니다. 여기서 **show = predict = 같은 값**이라 이 경로에서 예측 없는 표시(`0x71025495e4`만)는 생기지 않습니다. 값 = (A(0x1a) Chariot 사용 중 ∨ ¬h) ∧ ¬b ∧ [본체+0xa898]+0x30. b(가림)는 T+8 > 0, [본체+0xa650]+0x34 == 0, [본체+0xa818]+0x38 ≠ 0 또는 +0xb0 ≠ 0, 스폰 관리자 *`0x7105863d00` 리스폰 단계 조건, [본체+0xa6d8] 연결 대상 상태, [본체+0xa6d0]+0x38 ≠ 0(PlayerPipeline) 중 하나. h는 공격 입력 B(본체+0x4e0 묶음: +0, +0x12, +0x52, +0x53, 본체+0xab8)·C(본체+0x518 묶음)·특수 0x12/0x13 상태로 정해지고 [*(본체+0x588)].vt+0x158이 참이면 뒤집힙니다(명령 `analysis/decomp/r6_combat/c0fbc_part.asm`, 디컴파일 `c1.c`). h·b 각 항의 게임상 의미는 [미확정]. 예측 단계 수 = (this+0x40 핸들, 형 `0x710555cdc0`) 파라미터 +0x30 int(설정 플래그 +0x34) — 파라미터 이름 [미확정], 다음: `0x710555cdc0`을 참조하는 팩토리 `0x71010aa70c`.

**미확정**: 슬롯33을 부르는 쪽의 show/predict 조건(오징어 상태·발사 중 등), 예측 단계 수 파라미터(this+0x40 핸들의 +0x30 int — 이름 [미확정]), 무기 +0x3c8 핸들 파라미터, `0x7101758c94` 질의의 형상, this+0xf8 소비처.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

- 히트 이펙트·사운드: §6.6. 이펙트 이름(E2 `Hit`, `Splash`, `SplashWater`, `HitBlowerInhole`)이 실제 ELink 이벤트로 어떻게 이어지는지는 [effect_sound] 문서를 참고하세요.
- 히트 방향 = `normalize(0.5*접촉법선 − 0.5*진행방향)`(슬롯103 = 0.5, 0x71017504f4 뒷부분) **[판독]**.
- 조준 표시(가운데 점·바이어스·히트마커) 이펙트 이름과 선택 조건: §6.7(ELink 사용자 `PlayerShotGuide`).
- 플레이어 피격 연출 문자열 `PlayerDamage`, `PlayerDamageSmall`, `PlayerDamageSmallKnockBack`(참조 0x71019389fc, 0x710193a230 등)과 `PlayerKnockBack`(0x7101927104)은 위치만 확인했습니다 **[미확정]**.

## 8. 다른 기능과의 상호작용

| 상대 | 내용 |
|---|---|
| 탄 이동 [bullet] | age 증가 → 이동 → 반경 갱신 순서. 데미지 캐시는 이동마다 무효화 |
| 도색 [paint] | OnHit 끝의 0x7101646910이 바닥/벽/기타 착탄 슬롯(58/59/60)으로 나눔. 바닥/벽 구분 임계는 법선 Y > `*(f32*)0x7105858358` |
| 네트워크 [network] | `spl::AttackEvent`(0x30 필드 17비트), `spl::ReceiveDamage`, `spl::DamageReason`, `HitEffectNetEvent`. 데미지 권한(누가 판정하는지)은 [network] 담당 |
| 플레이어 [life] | 리시버 이후의 HP·사망·회복·적 잉크·아머·피해 적용 기기는 [player_life.md](player_life.md). 0x71024319f0은 `spl::PlayerStepPaint`(vtable 0x710563eb68)의 슬롯25이고, PlayerStepPaint+0xb8에 PlayerDamage를 저장합니다(이전 판의 'player+0xb8'을 정정: 기준 객체는 플레이어 본체가 아니라 PlayerStepPaint) |
| 기어 | ObjectEffect_Up(0x7101a87aa0 [판독]), SubEffectReduction / OpInkEffectReduction / RespawnTimeSave(§4.9 값만) |

## 9. 웹 포팅 구조와 구현 순서

### 9.1 모듈 (웹 권장 이름은 원본에서 확인된 이름이 아님)

| 웹 모듈(권장) | 책임 | 원본 대응 |
|---|---|---|
| `damageTable.ts` | DamageRateInfo / HitEffect 표 로드, `rate(row,col)` | 0x7101a859f0, 0x7101a856e8 |
| `bulletDamage.ts` | `shooterDamage(age, p)`, 반경, 넉백, 크리티컬 링 | 0x71017506d0, 0x71018a6b68/6fe4, 0x7101e66c4c, 0x71016e6260 |
| `damageReceiver.ts` | 결과 판정·배율·이력·리스너 | 0x7101a86ec0, 0x7101a87e24 |
| `hitDispatch.ts` | 접촉 → 리시버 순회 → 최대값 반환 | 0x71012d4adc |
| (공용) `paramResolve.ts` | `$parent` 필드 단위 상속 | 모든 파라미터 reader |

브라우저와 서버(권위 판정 쪽)가 같은 코드를 써야 하는 것은 `bulletDamage`와 `damageReceiver` 전부입니다(정수 결과가 1 차이 나면 확정킬이 갈림).

### 9.2 상태 객체 (웹 권장)

```ts
interface ShooterDamageParam { ValueMax: number; ValueMin: number; ReduceStartFrame: number; ReduceEndFrame: number } // s32, 0.1HP
interface BulletCombatState { age: number /* +0x134 */; dmgCache: number /* +0x11f0, -1 */; critLatch: boolean /* +0x11ef */ }
interface DamageInfo { damage: number; attackerTeam: number; attackerId: number; knockback: [number,number,number]; rowName: string; extraInfo: number }
interface Receiver { colName: string; teamMode: 1|2; team: number; ignoreTeamMask: number; resSameTeam: number /*0*/; resZero: number; kbRate: number /*NaN*/; histMax: number /*64*/; history: Hist[]; listeners: Listener[] }
```

### 9.3 구현 순서

1. 표 로드(이미 JSON으로 뽑아 둠) + `rate()` + `$parent` 해석.
2. `shooterDamage`, `bulletRadius`.
3. 수신 `computeResult`. 팀 판정, 배율, 상한, 이력 모드 1~6, 시간 창까지 §6.4/§6.4.1 그대로(원본 실행 E와 일치, 2026-10-03 정정: 이전 판은 "이력은 [미확정] 부분을 뺀 형태로"). 슈터 탄의 송신자 모드 값만 [미확정]이라 모드 0(이력 판정 없음)으로 두고 표시합니다. 테스트 기대값은 `web/tools/r5_combat_emu.py`의 `ref_result`와 같은 입력으로 만듭니다.
4. 넉백 벡터 계산(적용은 player 문서 확정 후).
5. 크리티컬 링(이펙트 행 선택에만 영향).
6. 히트 이펙트 표 조회.

### 9.4 원본과 똑같이 지켜야 할 것

- 모든 곱셈·나눗셈은 **f32**로 하고(`Math.fround`), 정수 변환은 **0 방향 절삭**으로 합니다(`Math.trunc`).
- 배율 곱에는 `+1e-5`(f32 `0x3727c5ac`)를 넣습니다. ObjectEffect_Up 보정에는 넣지 않습니다.
- 감쇠식의 `+1`과 분모 0 → 1 처리를 그대로 둡니다.
- 셀이 없거나 DamageRate가 없으면 1.0을 씁니다.
- 99999를 넘으면 99998로 바꿉니다.
- 반경 하한은 0.02입니다.

### 9.5 웹에서 바꿔야 하는 부분

- Havok 레이어 필터 → 자체 충돌 마스크. `SplInkBullet_FriendThrough`는 같은 팀 `SplPlayer`, `SplInkShield`, `SplGreatBarrier`, `SplBluntWeapon`과 충돌하지 않습니다(§4.8).
- 해시 트리 조회 → `Map<string, number>`(키 `${row}___${col}`). 원본 해시 충돌 가능성은 무시합니다.

## 10. 검증 코드·실행 결과·기대값

아래 표의 위 네 줄은 **재구현 계산**입니다(원본 명령을 판독해 같은 순서로 옮긴 것을 실제 데이터로 돌림). 2026-10-03 [r5 combat]에 추가한 아래 여섯 줄은 **원본 함수 실행**(unicorn, 원본 명령 무수정)과 독립 재구현(`r5_combat_emu.py`의 `ref_*` 함수, 이 문서 의사코드를 f32로 옮긴 것)의 비트 대조입니다. 정정(2026-10-03): 이전 판의 "모두 재구현 계산이며 원본 실행이 아닙니다"는 r5 실행 추가로 더 이상 맞지 않아 바꿨습니다.

| 검사 | 명령 | 결과 |
|---|---|---|
| 감쇠 경계(합성) | `PY web/tools/combat_damage.py selftest` | OK. 9건: age 0/6/7 → 360, age 8 → 354(360−5.625=354.375 절삭), age 39 → 180, age 100 → 180, 분모 0, Min>Max |
| 스플래시슈터 실제 데이터 | `PY web/tools/combat_damage.py weapon Shooter_Normal_00` | 360(age 0~7) → 354, 348, 343, … → 180(age 39~) |
| 전 무기 감쇠 표 | `… falloff` → `analysis/combat/shooter_damage_falloff.txt` | 59종. 예: Heavy 620→350(9~25), Precision 280→140(4~20), 블래스터 상수 |
| 수신 배율·상한·넉백 | `analysis/combat/verify_receive_knockback.txt` | Shooter→Default 360, 우산 0.7 → 252, 0.344×843 → 290(엡실론 없으면 289), 200000 → 99998, 넉백 dmg 360 → 크기 101.529, 1150 → 187.5, 2500 → 280(클램프) |
| **원본 실행 A** 데미지 감쇠 `0x71017506d0` | `PYTHONIOENCODING=utf-8 PY web/tools/r5_combat_emu.py` | 3,216건 불일치 0 (표본 67종 × age −1~44·100·1000, `$parent` 1~3단) |
| **원본 실행 B** 반경 `0x71018a6b68`/`0x71018a6fe4` | 같음 | 5,280건 불일치 0 |
| **원본 실행 C** 넉백 `0x7101e66c4c` | 같음 | 409건 불일치 0, 크기 360 → 101.5294, 1150 → 187.5, 2500 → 280.0 |
| **원본 실행 D** 크리티컬 링 `0x71016e6260` | 같음 | 연속 3,000회, 반환값·링 메모리 불일치 0 |
| **원본 실행 E** 수신 결과 `0x7101a86ec0`(+`0x7101a87edc`, `0x71017db2d4`)·이력 나이 `0x7101a86dc8` | 같음 | 3,823건 불일치 0, 이력 모드 1~6 거부 경로·시간 창 배수 0/1/8 경로 모두 통과 |
| **원본 실행 F** 히트마커 플래그 `0x7101a86be8`·예측 `0x7101a87e8c` | 같음 | 12,000건 불일치 0 |

스텁(원본 실행 A~F): 허용 목록 밖 게임 함수는 x0 = 0 반환, PLT memcpy/memset/strlen은 파이썬, `__cxa_guard_acquire`는 0(정적 형식 객체 초기화 생략 — IsA 검사는 가짜 vtable이 항상 참). E에서 DamageRateInfo 조회(`0x7101a856e8`)는 배율을 돌려주는 스텁, ObjectEffect_Up(`0x7101a87aa0`)은 빈 스텁, 송신자는 가짜 vtable, info+0xa9 = 0 고정. 파라미터 객체·리시버·이력 노드·접촉 구조체는 원본 오프셋대로 만든 가짜 메모리입니다. 결과 파일 `analysis/combat/r5_emu_combat.txt`. 단일 함수 실행이며 OnHit 전체 흐름(접촉 → 리시버 → 이펙트)의 연결 실행은 아닙니다.

외부 관찰값과의 대조(공략 위키의 스플래시슈터 36/18 등)는 원본 실행이 아니라 참고용이라 결론 근거로 쓰지 않았습니다.

**검증되지 않은 범위**:
- 접촉 콜백 시점(age가 0인지 1인지).
- ~~수신 이력 case 1~6의 정확한 의미.~~ → 2026-10-03 원본 실행 E로 확인. 남은 것은 어떤 송신자 클래스가 어떤 모드를 돌려주는지.
- 플레이어 HP 반영 전체(→ [player_life.md §10](player_life.md#10-검증): HP 홀더 함수만 원본 실행 확인).
- `$parent` 병합을 필드 단위로 한 것. 스칼라 필드는 원본 실행 A·B로 확인했고, 배열 필드 병합은 확인하지 않았습니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

2026-10-02 [life] 작업으로 플레이어 생명 관련 항목을 [player_life.md](player_life.md)에서 해소하거나 범위를 좁혔습니다. 줄 앞의 ✔는 확정 수준이 오른 항목입니다. 2026-10-03 [r5 combat]에 바뀐 칸은 "r5:"로 표시했습니다.

| 항목 | 상태(전 → 후) | 근거 / 다음 단서 |
|---|---|---|
| ✔ 플레이어 HP 저장·감소, 최대값 1000 | [미확정]/[추정] → **[판독] + 홀더 [실행]** | PlayerDamage+0x30 HP 홀더, 누적 0x7101a89524 → 프레임 갱신 0x7101a8905c, 최대 1000(0x7102506960). 원본 unicorn 실행과 재구현 9,600프레임 일치 |
| ✔ 사망 판정 | [미확정] → **[판독]** | `hp < 1` 이고 쓰러짐 타이머 4개가 모두 0(0x7102483134 안), 사망 시작 0x710245ff9c. 리스폰 흐름은 player_life §6.8에서 해소(T+0x103은 미션 전용 경로로 정정). 남은 것: 조작 기기의 리스폰 착지 단계 2~5 writer |
| ✔ 자연 회복 | [미확정] → **[판독]**(조건 의미는 [추정]) | 대기 60프레임(상수 0x71058bbd38), 초당 125.0 또는 1000.0(0x71024a41a4, 조건 0x71024591c8) |
| ✔ 적 잉크 지속 데미지 적용 | 값만 [판독] → **식 [판독]** | 0x710268b3b8 안 0x710268bc7c~0x710268bd44(fmax 0 포함), 적용 0x71024b9d34 → 0x71024b0c70 |
| ✔ 리스폰 시간 | 기어 값만 → **사망 대기식 [판독]** → **리스폰 시점까지 [판독 + 원본 실행]** | T+8 = Around + Chase(+모드 보정) + 30. 모드 보정 = `VersusReferee` vt+0x50(트리컬러만 팀 2 → 120). 조작 기기가 T+8 1→0 프레임에 리스폰(390번째 호출), 리셋 T+0 60/T+4 15/T+0xf4 59 — player_life §6.5, §6.8 |
| ✔ 무적·아머 설정자 | [미확정] → 부분 [판독] → **[판독] + 무적 조건 원본 실행** (2026-10-02 [respawn]) | 무적 판정 0x71024c7624 조건별 출처 컴포넌트·리스폰 무적 T+0xf4(리셋이 59/119) — [player_life.md](player_life.md) §6.11. 아머 HP 설정자 = startArmor 0x710243c1c4(원인 작은 번호 우선, 홀더 max/hp, 시작·끝 GameFrame, `StartArmor` 이벤트) — §6.9. 남은 것: 원인 번호 ↔ 무기 이름 |
| ✔ FriendThroughFrameForPlayer | [미확정] → **[판독]**; r5: vt+0xb0/+0xc0 = 필터 +8 비트0~5 설정/읽기 **[판독]** (`0x71016cb4c0`/`0x71016cb538`) | §4.8: 0x7101762f68/0x7101763a10이 탄 레이어 8/9 전환 |
| ✔ DamageHelper(+0x160), KnockBackHelper(+0x11b0) 역할 | [미확정] → 클래스 역할 [판독] | DamageHelper = 피해 수신 액터의 HP 홀더 목록 컴포넌트, KnockBackHelper = 바인딩만 하는 0x38 B 컴포넌트. 탄 객체에서 두 포인터를 쓰는 곳은 여전히 [미확정] |
| ✔ 넉백 적용 | [미확정] → 변환 [판독]; r5: 넉백 벡터 계산 `0x7101e66c4c` **[실행]**(§6.5) | 플레이어: ×1/3600, 최대 0.48, 0x71024c8318이 ×3600으로 물리 메시지. 물리 쪽 처리 [미확정] — [hitbox.md §5.2](hitbox.md) |
| ✔ 수신 이력 case 1~6 | [미확정] → **모드별 판정 [판독]** (2026-10-02 [respawn]) → r5: **[실행]** 3,823건 일치(§6.4.1) | §6.4.1: 1 = 간격(초) 안 같은 송신자 거부, 2 = 이전 합계 초과분만, 3 = 송신자별 누적 상한, 4 = 같은 프레임 같은 송신자/key 거부, 5 = 4 + key 교체, 6 = 1이 거부하면 2로. 이력 나이는 DamageHelper가 1/60초씩 더하고 15초에 지움. 남은 것: 송신자(액터+0x238) 클래스별 모드·값 [미확정] |
| ✔ 시간 창(+0x1fc~0x204) | [미확정] → r5: **동작 [판독 + 실행]**(§6.4, §4.5) | +0x200이 간격과 배수를 겸함, info+0xa8 ≠ 0이면 건너뜀(탄은 기본 1). 남은 것: 카운터 `0x710580e758`+0x148의 정체, info+0xa8 = 0을 쓰는 송신 쪽, R+0x1fc/+0x200을 바꾸는 쪽 [미확정] |
| ✔ 접촉 콜백 시점(첫 명중 age) | [미확정] → **age 시작값 정정 [판독], 첫 명중 age 0 [추정]** (2026-10-02 [combat4]) → r5: **이동 접촉 첫 명중 age 0 [판독]**([r5 physics] 프레임 순서) | age −1 시작([hitbox.md §1](hitbox.md)). 남은 것: 생성 위치 겹침 접촉의 age(데미지는 같음) |
| 플레이어 피격 형상·리시버 분배·Same/Other 표 선택 | 신규 → [hitbox.md](hitbox.md) §2~§4: ColBullet 캡슐 r 0.35 y 0.35~1.30 [데이터], 리시버는 바디별 목록 [판독], 표 선택 = 필터 객체 F+0x30 비교 [판독], F+0x30 값 출처 [미확정] | `0x7103ae53f0` 호출자 |
| Blast 데미지 | 신규 → [hitbox.md §5.1](hitbox.md) 거리·평면 표 조회·넉백 [판독], 차폐 [미확정] | |
| 무기 → DamageRateInfoRow 표 채우기, 카테고리 0/1/2 의미 | [추정] | 0x7101a88920이 읽는 무기 정보 트리 생성 코드 |
| 크리티컬 needCount(생성정보+0x92), VariableRepeat(+0x91), 샷ID(+0x94) | [추정] | 무기 발사 쪽 생성정보 기록 함수 |
| Same/Other 레이어 표 선택 규칙 | [추정] → [판독] (2026-10-02 [combat4], [hitbox.md §3](hitbox.md)) | 표 선택 = 두 바디 F+0x30 비교. r5: F+0x30 writer 정리(hitbox §3) — 탄 바디 writer [미확정] |
| r5 신규: 조준 히트마커 조건 | **[판독]**, 플래그·예측 함수 **[실행]**(§6.7) | 남은 것: 슬롯33 show/predict 호출 조건, 예측 단계 수 파라미터 이름, 질의 형상 `0x7101758c94` |
| r5 신규: 데미지 감쇠·반경·크리티컬 링 | [판독] → **[실행]**(§6.1~§6.3) | 크리티컬 → HitEffectConfig `Shooter_CriticalHit` 행 선택 코드 [미확정] (`0x71028fed18` 후보) |
| r5 신규: 리시버 +0x208(히트마커 모드) writer | [미확정] | 생성자는 0. 다른 writer는 `str w,[x,#0x208]` + `0x1c4/0x1c8` 동반 스캔으로 못 찾음(`combat4_iscan.py`) |
| r6: 탄 바디 F+0x30·아군 충돌 | [미확정] → **[실행]** | [hitbox.md §3](hitbox.md): 슬롯9 `0x71013405e0` 팀+1, 쌍 판정 `0x7103c55ed8`. 슈터 탄은 아군에 막힘(데미지 0) |
| r6: 송신자 이력 모드·탄 +0x160 용도 | [미확정] → **[판독]** | 슈터 모드 0, 클래스별 표 hitbox §4. +0x160 = 탄 쪽 DamageHelper(송신자 보유) |
| r6: 크리티컬 HitEffectConfig 행 | [추정] → **[실행]** | §6.6: `0x71028fed18` 36,900건. 스플래시슈터 크리티컬 = `Shooter` 행 |
| r6: 조준 표시 호출 조건 | [미확정] → 식 **[판독]**, 항 의미 [미확정] | §6.7: `0x71024c0fbc`. 단계 수 파라미터 이름 미확정(형 `0x710555cdc0`) |
| r6: 시간 창 카운터·R+0x208 writer | [미확정] → **[판독]** | GameFrame+0x148, R+0x208 = 2 쓰는 클래스 목록(§6.4.1) |
