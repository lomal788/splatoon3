# 이펙트·효과음 (ELink2 / SLink2 / Effect / Sound)

게임 이벤트에서 이펙트·효과음이 재생되기까지의 경로를 정리합니다. 이벤트 이름 → XLink 사용자 데이터 → 에셋 이름 → 리소스 파일 → 웹 재생 순서입니다. 대표 예시는 **스플래시 슈터(`WeaponShooterNormal`, `Shooter_Normal_00`)의 발사·탄·착탄·피격**입니다.

작업 지침은 [../../분석.txt](../../분석.txt), 확정 수준 표기는 [../README.md](../README.md)를 따릅니다. 이 영역에 원본 실행 확인은 없습니다. [실행]은 자체 파서·디코더를 원본 파일에 돌린 결과만 가리킵니다. **[참고]**는 공개 xlink2 디컴파일(Splatoon 2 기반)을 읽은 것입니다.

상태: 분석 진행(2차: xlink2 컨테이너·비교·커브·난수 규칙, 발사 키 대상, 머즐 플래시 액션 경로, 착탄 θ·벽 판정, Alto 롤오프 판독). 웹 구현은 없습니다. 검증은 합성 테스트와 데이터 전수 검사만 했습니다.

**2026-10-03 5차 갱신:**
- 원본 실행(unicorn)으로 확인한 것: 리스너 위치(TargetOffset) 512건, 리스너 지향성 거리 배율 2,048건, 그룹 제한기 적용(정렬 뒤 생존) 600경우.
- 판독으로 정리한 것: S1/S2 기준 플레이어(쏜 사람), 컬링 n(그 팀의 살아 있는 탄 수), 분열 탄 파티클 슬롯, 이미터 형상 0·1번 식, 벽 스플래시 색·알파 식.
- 위 문장의 "이 영역에 원본 실행 확인은 없습니다"는 3차까지의 상태입니다. 실행 기록은 [solo_fx_audit.md](solo_fx_audit.md)에 모았습니다.

## 하위 문서

| 문서 | 내용 |
|---|---|
| [xlink_format.md](xlink_format.md) | XLNK(ELink2/SLink2) 바이너리 형식, 컨테이너·트리거·조건 규칙, 웹 디스패처 |
| [sound_resources.md](sound_resources.md) | BARS/AMTA/BWAV/Stream, Alto 설정(감쇠·그룹·리스너), WAV 변환, WebAudio 파라미터 |
| [effect_resources.md](effect_resources.md) | esetb.byml + VFXB v46, 탄 파티클 OneEmitter 관리자, 착탄 스플래시 분류, HitEffectConfig, 텍스처 변환 |
| [solo_fx_audit.md](solo_fx_audit.md) | 원본 실행·데이터 대조 검증 기록(제한기, 리스너, 지향성, VAT) |

관련 문서(다른 담당): 탄 생성·이동은 [../weapon/shooter_bullet.md](../weapon/shooter_bullet.md), 피격 판정은 [../combat/damage_hit.md](../combat/damage_hit.md), 도색은 [../paint/paint_and_score.md](../paint/paint_and_score.md)입니다. ELink 에셋 파라미터 `CameraRumbleName`/`CtrlRumbleName`(진동·화면 흔들림) 매핑은 camera 담당 문서([../camera/camera_feel.md](../camera/camera_feel.md), 도구 `web/tools/camera_rumble_map.py`)에 있어 여기서는 다루지 않습니다.

---

## 1. 사용자에게 보이는 동작 (스플래시 슈터)

| 상황 | 소리 | 이펙트 |
|---|---|---|
| 무기를 듦 | `Wp_Shooter_Attach_00` (자기 플레이어만) | — |
| 한 발 쏨 | 자기: `Wp_ShooterNormal_Shot_00`, 아군: `Wp_NormalShot_Blurred_02`, 적: `Wp_NormalShot_02` | 총구 `WpShtrMzfNml`(머즐 플래시, 뼈 `Muzzle`) |
| 탄이 날아감 | — | 탄마다 `WpShtrBullet1Emit` 파티클 1개(팀별 OneEmitter 관리자) |
| 탄이 지형에 맞음 | HitEffectConfig `Shooter___Constant_Default`의 S2 = SLink HitEffect `インクヒット`(Focused는 칠 가능 여부·속도로 분기, 그 밖은 Random) [판독+데이터, "Constant = 지형"은 추정] | 법선 y ≤ 0.6414이면 벽 `Cmn(Np)WallSplash1Emit`, 아니면 탄 속도와 법선 사이 각도로 `CmnFloorSplash*`/`CmnNPFloorSplash*` [판독] |
| 탄이 상대에게 맞음(데미지) | `ヒット` → `HitEf_Damage_00`(연타 묶음), 맞은 쪽이 자기면 `インク被弾`(NotFocused는 랜덤 4종) | ELink `HitEffective` → `WpCmnHitEffective`, OneEmitter `Hit` → `WpCmnHit` |
| 탄이 물에 빠짐 | `水没` 8종 랜덤 | OneEmitter `SplashWater` → `WpCmnWaterSplash` |

## 2. 자료 위치

| 항목 | 위치 |
|---|---|
| 원본 데이터 | `extracted/romfs/ELink2/`, `SLink2/`, `Effect/`, `Sound/` (읽기 전용 추출물) |
| 액터 연결 | `Pack/Actor/WeaponShooterNormal.pack.zs` 안 `Component/ELink|SLink/WeaponShooterNormal.engine__component__*LinkParam.bgyml` = `{UserName: "WeaponShooterNormal"}` |
| 히트 조합표 | `Pack/Bootup.Nin_NX_NVN.pack.zs` → `System/CombinationDataTableData/Default_spl__HitEffectConfig.pp__CombinationDataTableData.bgyml` (JSON 사본 `analysis/effect_sound/HitEffectConfig.json`) |
| 전역 XLink 속성 | `RSDB/XLinkPropertyTable.Product.100.rstbl.byml.zs` (JSON `analysis/effect_sound/XLinkPropertyTable.json`) |
| 도구 | `web/tools/effect_xlink.py`, `effect_xlink_summary.py`, `effect_xlink_eval.py`, `effect_usernames.py`, `effect_esetb.py`, `effect_vfxb.py`(mpj 복사), `effect_vfxb46.py`, `effect_bntx_float.py`, `effect_blcallers.py`, `effect_ptrscan.py`, `sound_bars.py`, `sound_alto.py`(aroc·audc·selftest), 3차: `vfx_emitter46.py`(raw/stat/fields/sim/selftest), `vfx_resfield_scan.py`(ResEmitter 오프셋 사용처), `sound_constscan.py`(32비트 상수·매직 위치) |
| 디컴파일 | `analysis/decomp/effect_sound/batch1.c`, `batch2.c`, `xlink_core.c`(xlink2 컨테이너·값 해석 33개), `fx_batch3.c`(슈터 갱신 0x7102578c34, InkAction 0x7102864104, 히트 로더·집계, Alto 롤오프 모델), `fx_full.c`(전체 분석판: Alto 감쇠 계산 0x7103863fe8, AROC 파서 0x7103852e2c, 히트 컬링 0x71027e24a8) + 다른 담당 `analysis/decomp/camera/batch1.c`(0x71025817c8·0x7102581ccc·0x7102584fc8·0x7102864594·0x7102865628·0x710289a8b4), `analysis/decomp/network/net_player.c`(히트 분배 **0x71027b877c**), 3차: `analysis/decomp/vfx/`(nn::vfx 전 범위 `vfx_lib_00..02.c`, xlink 액션 트리거·Alto·AGST·진동 `snd_xlink_b1.c`, `snd_agst.c`, `snd_b2.c`, `xlink_pending.c`, `rumble_b1.c`) |
| 산출물 | `analysis/effect_sound/` — 사용자 덤프, `wav/`(3개), `tex/`(7개), `tex_float/`(FLOAT 3장), `esets_shooter.json`, `sound_index.json`, `hiteffect_slink_tree.txt`, `alto_attenuation_sets.txt`, `alto_aroc_models.txt`, `BusSetting.json`, `GroupSetting_byml.json`, 디스어셈블 `*.dis.txt`, 3차 `analysis/vfx/`(이미터 필드 `emitters_v46_fields.json`, 원시 덤프 `raw_*.txt`, 셰이더 역번역 `shader/p*.vert`, GRP 표 `agst_grp_dump.txt`, 재구현 표 `sim_*.txt`) |

## 3. 진입점과 호출 흐름

### 3.1 공통: xlink 방출 [판독]

```
게임 코드 ── emitXLink(XC, key, mode) = 0x7103e1e37c
              mode 0: XC+0x78 (ELink UserInstance)
              mode 1: XC+0x80 (SLink UserInstance)
              mode 2: 둘 다
           └ 0x710389e6e8(instance, key, outHandle, 0)  searchAndEmit: 키 이진 탐색 → emit [판독]
           └ 인스턴스를 calc 큐에 등록(처음 활성일 때만)
속성 쓰기 ── 사용자 로컬 속성 인덱스(0x710280919c 가 이름으로 조회해 저장) → 값 갱신
액션 ── 액션 슬롯 이름 State[0], 액션 이름 = InkActionID 열거형 값 이름(0x7102864594 가 "::" 뒤 문자열로 표 생성)
```

### 3.2 발사 [판독]

탄 생성 함수 `0x7102581ccc`, `0x71025817c8`, `0x7102584fc8`가 발사 xlink 키를 정합니다. 탄 생성(`0x7102897640`)이 성공한 직후입니다. network 담당 보고에 따르면 원격 플레이어의 복제 탄도 같은 함수를 지나므로 아군·적 발사음도 이 경로입니다.

```
if (!farCull(muzzlePos, team))                // 0x71027e22bc, true = 너무 멀다
    w = this+0x38(무기)
    key = (WeaponShooterParam.VariableShotRepeatStartFrame > 0)      // 0x710289a8b4
            ? (this+0x98 > 0 ? "FireOn" : "FireImpact")
            : "Fire"
    (*(w+0x5f0))->vtable[3](out, &key)        // = SLink 만 searchAndEmit
```

- **무기 +0x5f0** = 무기 액터 +0x520의 16 B 래퍼 `{vtable 0x71055408b0, XC}`입니다(설정 0x710280eaf8 근처, 래퍼 생성 0x7100f765bc). 이 vtable의 슬롯 3(+0x18) = `0x7100f797f0` → `0x7103e1e61c`로 **XC+0x80(SLink)에만** searchAndEmit합니다. 슬롯 2는 ELink만(0x7103e1e5d0), 슬롯 0은 mode 지정 방출(0x7103e1e37c)입니다. 따라서 **발사 키는 이펙트(ELink)로 가지 않습니다** [판독]. 1차 문서의 "대상 객체 mode 미확정" → 해소.
- `farCull(pos, team)`: 기준점은 전역 객체의 행렬 이동 성분(+0x14c/+0x15c/+0x16c)이고, 카메라로 추정합니다. R = 600입니다. 기준 플레이어의 팀이 `team`이면 R = 600 − 500·min(n/30, 1)이고, n은 팀별 구조체 +0x10의 정수입니다(의미 미확정). `|pos − 기준점|² > R²`이면 방출하지 않습니다 [판독].
- **5차(2026-10-03) n의 의미 [판독]:** 팀별 구조체는 탄 관리자 싱글턴(`*0x7105850620`) +8 + team·0x58이고, +0/+8은 탄 연결 목록, **+0x10은 그 목록의 탄 수**입니다. 탄 공통 등록 `0x7101645590`(여러 탄 종류의 생성 경로가 BL로 부름)이 `탄+0x108→+0x2C` 팀의 목록에 탄을 넣고 +0x10을 1 올립니다. `BulletSimple` vt16 `0x7101645f84`가 빼고 1 내립니다(팀 −1·3은 건너뜀). 따라서 **n = 그 팀이 지금 가진 살아 있는 탄 수**이고, 자기 팀 탄이 30발 이상이면 발사음·히트 컬링 반경이 100으로 줄어듭니다. 히트 컬링(R = 400 − 300·min(n/30, 1))도 같은 n입니다. 기준점 객체(카메라 추정)의 정체는 여전히 [추정]입니다.
- 스플래시 슈터는 `VariableShotRepeatStartFrame`을 설정하지 않아 기본값 0을 씁니다([../../../analysis/param_reflect/spl__WeaponShooterParam.json](../../../analysis/param_reflect/spl__WeaponShooterParam.json)). 그래서 키는 **`"Fire"`**입니다. `WeaponShooterFlash`(값 10)는 `FireImpact`/`FireOn` 키를 쓰고, SLink 데이터의 키 이름도 그렇게 되어 있습니다 [데이터].

**머즐 플래시 = InkAction 액션 경로** [판독]. 슈터 갱신 함수 `0x7102578c34`(무기 behavior, +0x88 = 무기, +0x3aa8 = 플레이어)가 무기 InkAction을 바꾸고, `0x7102864104`가 그 이름으로 ELink·SLink 양쪽의 액션 슬롯 0(= `State[0]`)을 바꿉니다.

```
// 0x7102578c34 (매 갱신)
if (보는 쪽 조건 통과)                                 // +0xa8e0 객체 모드 0..4 분기
    setInkAction(weapon, behavior+0x40 == 0 ? FireOff(2) : FireOn(1))   // 0x7102578d74
...
if (이번 갱신에 탄을 쐈음)                              // 0x7102492120 성공 → 0x71025785f4(발사)
    0x71024b2f7c(...)                                   // 컨트롤러 진동으로 추정
    setInkAction(weapon, FireImpact(0))                 // 0x7102579af4

// setInkAction 0x7102864104(weapon, id, flag)
now = max(GameFrame(+0x148), 0)
if (id != 0) {
    if (now <= weapon+0x374) return              // 같은 프레임에 FireImpact 가 있었으면 무시
    if (id not in 7..10) { weapon+0x384 = id; return }   // 보류(적용은 다른 경로, 미추적)
}
if (weapon+0x320 != id) {
    상태 전환(weapon+0x318); idx = vt+0x1f8()
    name = 이름표[idx]                           // "FireImpact", "FireOn", ... (0x7102864594)
    0x710389b61c(XC.elink+0x98, name, (int)weapon+0x324, 0)   // 액션 슬롯 0
    0x710389b61c(XC.slink+0x98, name, (int)weapon+0x324, 0)
    weapon+0x374 = max(weapon+0x374, now)
}
```

- InkActionID 값: 0 FireImpact, 1 FireOn, 2 FireOff, 3 FireFailed, 4 PaintOn, 5 PaintOff, 6 PaintNoInk, 7 FireCanopy, 8 RecoverCanopy, 9 SideStep, 10 StepSaber, 11 ChargeSpinner, 12 ChargeSaber, 13 BlowerInhaleOff, 14 BlowerInhaleOn, 15 Unknown [데이터: 열거 문자열].
- ELink `WeaponShooterNormal`의 `State[0]` 액션 `FireImpact`/`FireOn` 트리거가 `マズルフラッシュ`입니다. 그래서 **탄을 쏜 갱신에 FireImpact로 바뀌며 머즐 플래시가 나옵니다**. FireOn/FireOff는 같은 프레임의 FireImpact 뒤에는 무시되고, 그 밖에는 **FireOn/FireOff(id 1·2)가 언제나 보류(+0x384)로만 들어갑니다**(7..10만 즉시).
- **보류 적용** [판독, 3차]: `WeaponShooter` vtable(0x7105652468) 슬롯 19(+0x98) = `0x710286540c`가 보류 값(+0x384, 없음 = 0xF)을 적용합니다. 보류가 FireOff이고 현재가 FireOn이며 FireOn 연속 프레임(+0x380)이 `(*(무기+0x368))->vt+0x148()`보다 작으면 FireOn을 유지합니다(최소 유지). 현재와 다르면 상태 전환 후 ELink(XC+0x78)·SLink(XC+0x80) 액션 슬롯 0을 같은 함수 `0x710389b61c`로 바꿉니다. FireOn으로 들어갈 때 무기+0x370 바이트가 켜져 있으면 +0x37c = (+0x37c + 1) mod 8. 마지막에 보류 = 0xF, +0x380 = (현재 FireOn ? +1 : 0), +0x398 카운트다운이 1이 되는 프레임에 ELink 인스턴스 +0xf8 |= 0x1000. 이 슬롯을 부르는 쪽(프레임 내 순서)은 [미확정]입니다.
- **FireImpact → FireOn 전환 때 플래시를 다시 내지 않습니다** [판독, 3차]. 두 트리거 모두 같은 콜 테이블 2(`マズルフラッシュ`)를 가리키고 flag = 1(bit0 넘겨받기)이라, 새 액션 트리거는 직전 액션의 같은 에셋 이벤트를 넘겨받고 방출하지 않습니다([xlink_format.md](xlink_format.md) §4.4). FireOn → FireImpact도 같은 규칙이므로, **계속 쏘는 동안 플래시 이벤트 하나가 FireImpact/FireOn 사이로 넘겨지며 유지**되고, FireOff로 바뀔 때(그 액션에는 이 에셋 트리거가 없음) 꺼집니다.
- 이 이벤트의 이미터셋 `WpShtrMzfNml`은 **무한 방출 이미터**(hasEmitEnd 0)입니다: SplashCorn은 시작 2프레임부터 5프레임마다, Flash는 7프레임마다 파티클 1개(수명 6/5)([effect_resources.md](effect_resources.md) §2.2.6) [데이터]. 따라서 화면의 플래시 빈도는 탄 연사 간격이 아니라 이미터 간격으로 정해집니다 [판독+데이터 — 원본 실행 확인 아님].

**`MuzzleShotDirXZDot` 계산** (`0x7102578c34` 끝, `0x7102579244`~) [판독]:

**r9 정정(2026-10-03):** 아래 식의 reader는 확정했으나 `+3c4/+3c6`의 선택 뼈를 Muzzle이라고 부를 근거는 없다. 정상 슈터의 명시적 Muzzle 검색은 `+3bc`를 쓰며 `0f54d68`은 이름 복사 함수다. 기존 해석을 당시 기록으로 보존하고, 정확한 모델/뼈 인덱스와 타입 경계는 [muzzle_attachment_r9.md §3~6·11](muzzle_attachment_r9.md)을 따른다. 격리 원본 2,048입력 비트 일치는 실제 뼈 producer 검증이 아니다.

```
M  = 무기 모델(+0x5e8)의 뼈 행렬(뼈 번호 무기+0x3c4/+0x3c6, vt+0x78)     // 3x4, 행 우선
v  = normalize(-M[0][0], 0, -M[2][0])        // 뼈 X축의 XZ 성분을 뒤집어 정규화(길이 0 이면 (−M00, 0, −M20) 그대로)
D  = 플레이어 본체(+0x108) +0x538 의 vec3     // = PlayerCamera+0x1a4(리그 수평 시선) 사본 [판독, ../player/player_state.md §6.1.2]
dot = v.x*D.x + 0*D.y + v.z*D.z
holder(무기+0x100)+0x60 = dot
holder+0x18 객체 vt+0x58(dot, holder+0x5c)    // 다른 대상에도 같은 값
holder+0x28(ELink 인스턴스) vt+0x70(dot)  — 인덱스 holder+0x5e (= MuzzleShotDirXZDot)
```

머즐 플래시 Delay = Curve(dot): dot ≤ 0.75 → 2.0, dot ≥ 1 → 0, 사이 선형([xlink_format.md](xlink_format.md) §4.3). 뼈 방향과 D가 같으면 지연 없이, 많이 어긋나면 2(프레임으로 추정) 늦게 나옵니다.

### 3.3 장착 [판독]

`0x7102865628`가 장착 시 `OnAttach`를 mode 2로 방출합니다. SLink `OnAttach` 스위치(SubjectiveType)는 `Focused`일 때만 `Wp_Shooter_Attach_00`(그룹 Weapon_Default, LowSensi, DistCoef 5.0)을 냅니다. 분리음은 `OnDetatch`(오타 그대로) → `Wp_Detach_00`입니다(Volume 0.9–1.0, Pitch 0.9–1.1).

### 3.4 탄 비행 파티클 [판독]

`spl::BulletShooterBase` vtable 슬롯 106(`0x7101753bb4`)이 매 갱신마다 처리합니다.

```
team = 생성정보(+0x108)+0x2c; if team == -1 || team == 3: return
mgr = singleton(0x7105850618) + 8 + team*0x15e8      // 팀별 관리자 3개
0x71018b22a4(mgr + 0x000 /* WpShtrBullet1Emit 슬롯 */, bullet+0x140 /* 파티클 핸들 */)
```

핸들은 생성 때 관리자 풀(+0x41c8, 0x1800개 × 0x10 B)에서 받습니다(`0x7101644650`). 정리 때 돌려줍니다(`0x710164546c` = BulletSimple vt 10). 자세한 내용은 [effect_resources.md](effect_resources.md) §3입니다.

### 3.5 착탄·피격 [판독 + 데이터]

**2026-10-03 r8 정정 [판독]+[데이터]+[실행]**: 아래 원문의 순서/Constant 추정을 보존하고 정정한다. 실제27B877C는 **로컬 S1/E1을 처리한 뒤27E24A8 컬링**, 이후S2/코드emitter/E2문자열을 처리한다. 신규5880소비+5FIFO+16컬링 원본실행 모두일치0. 코드emitter는E2문자열의대체가아니며둘다시도한다. 원본27B4704의result×70+row×560+material×2|local이반응열을확정한다. 지형의막는접촉/noReceiver가1(Constant)을생성하는기존판독과연결해Constant_Default→インクヒット가그경로착탄음임을확정;Constant전체가지형전용이라는역명제는근거없다. 자세한원본필드/게이트/정정/검증경계는[hit_effect_pipeline.md](../combat/hit_effect_pipeline.md) §3–11. 고정r7 L186 질문해소이며최종오디오/GPU실행은주장하지않는다.


※ 정정: 1차 문서는 히트 이펙트 분배를 `0x71027b84e0`이라 했지만, 이 주소는 668 B짜리 별도 함수(두 객체의 +0x40 종류·참조 비교)입니다. 실제 분배는 **`0x71027b877c`**(7,588 B, vtable 0x7105649130 슬롯, network 담당이 `analysis/decomp/network/net_player.c`에 디컴파일)입니다. 착탄 스플래시 호출 `0x71027b9978`도 이 함수 안입니다. 근거: 전체 분석 함수 경계(`func_lookup.py`), BL 호출자.

**히트 요청 구조**(분배 함수 param_2, 웹 권장 이름 `HitFxRequest`) [판독]:

| 오프셋 | 형 | 내용 |
|---|---|---|
| +0x00 | vec3 | 위치 |
| +0x0C | vec3 | 면 법선(n) [추정: 벽 판정·회전에 쓰는 방식] |
| +0x18 | vec3 | 탄 속도(v). 길이가 SLink `Velocity` 속성 |
| +0x28 | s32 | 5이면 보는 사람 조건 검사(+0x34/+0x38 플레이어 번호가 로컬 플레이어와 같을 때만) |
| +0x30 | f32 | > 0이면 요청을 지연 목록(+0x69140)에 복사 |
| +0x34 / +0x38 | s32 | 플레이어 번호(공격자/대상으로 추정). +0x34 < 0이면 팀 1, 아니면 그 플레이어의 팀 |
| +0x3C | u8 | 칠할 수 있음(paintable). SLink `IsPaintable` |
| +0x3D / +0x3E | u8 | 집계 경로 선택 플래그 |
| +0x58 | s32 | HitEffectConfig 셀 번호(관리자 +0xB8 + 번호·0x10 = {셀, E1 종류, E2 종류}) |

**분배 순서** `0x71027b877c(mgr, req, aggregateNum)`:

1. 팀을 정하고 `0x71027e24a8(req, team)`로 **거리 컬링**: R = 400, 보는 플레이어의 팀이 이 팀이면 R = 400 − 300·min(n/30, 1) (n = 팀별 구조체 +0x10, 발사 컬링과 같은 값). 멀면 이펙트·소리 전부 생략 [판독].
2. **S1·E1**은 집계 경로 `0x71027b4aa4`로 갑니다. 이 함수가 S1을 SLink 인스턴스(mgr+0x690b8)에, E1을 ELink 인스턴스(mgr+0x690c0)에 searchAndEmit합니다. 같은 프레임의 여러 명중이 묶여 `AggregateNum`(0..15로 자름)이 됩니다(`ヒット` Switch가 이 값을 봄) [판독, 묶는 기준은 0x71027b7938 미판독].
3. **S2**: SLink 인스턴스(mgr+0x690b8)의 로컬 속성 AggregateNum(+0x80+8) = aggregateNum, Velocity(+0xC) = |v|, IsPaintable(+4) = req+0x3C, SubjectiveType = `0x71027b5430(inst, req+0x34)`를 쓰고, 위치 행렬 `0x71027b5640` 뒤 S2 키로 searchAndEmit. 핸들이 유효하면 위치(+0xE4)를 req 위치로 씀.
4. **E2 종류**(로더가 문자열을 Splash 0 / Hit 1 / SplashWater 2, 그 밖 -1로 바꿔 둔 값)로 코드 파티클(OneEmitter):
   - **Splash(0)**: `n.y ≤ 0.64144969`(bss 0x71058cc928, 정적 초기화 0x71027b42a0)이면 **벽**: 슬롯 `mgr+0x1340 + p·0x60`(p = paintable, 0 → `CmnNpWallSplash1Emit`, 1 → `CmnWallSplash1Emit`), 행렬은 pitch = asin(n.y), yaw = n의 XZ 방향(acos(−n.z/|n_xz|), n.x 부호로 뒤집기)으로 만든 회전 + 위치.
     아니면 **바닥**: |v| = 0이면 θ = 0으로 보고 kind를 고른 뒤 고정 행렬(bss 0x71058237b0)로 슬롯 `mgr+0x1100 + kind·0xC0 + p·0x60`에 추가. |v| > 0이면 **θ = atan2(|v̂ × n|, v̂ · n)** (탄 진행 방향과 면 법선 사이 각, 0..π)과 v·n으로 만든 회전 행렬로 `0x71018b4f74(team, θ, mtx, paintable)`.
   - **Hit(1)**: 슬롯 mgr+0x14C0(`WpCmnHit`), Y축을 n으로 돌리는 회전 + 위치.
   - **SplashWater(2)**: 슬롯 mgr+0x1520(`WpCmnWaterSplash`), 같은 방식.
5. **E2 문자열**이 비어 있지 않으면 ELink 인스턴스(mgr+0x690c0)에 E2를 키로 searchAndEmit하고, 핸들 행렬을 n 방향 회전 + 위치, 스케일 1로 씁니다. E2 값 중 `BombSplashWater`, `BigSplashWater`, `SplashSame`, `BigSplash`, `HitBlowerInhole`은 ELink HitEffect 키이고, `Splash`/`Hit`/`SplashWater`는 ELink 키가 아니라 코드 파티클만 나옵니다 [판독+데이터].
6. req+0x30 > 0이면 요청을 지연 목록에 넣습니다(용도 미추적).

**5차(2026-10-03) 묶음 기준과 지연 목록 [판독]** (프레임 처리 `0x71027b7938`, 비교 `0x71027b84e0`):
- 같은 요청 판정 `same(a, b)`: `a+0x40 == b+0x40`(종류 k ∈ {1, 2, 3}, 그 밖은 거짓)이고, 참조 대상 `a+0x48 == b+0x48`(참조 객체 +0x28 ≠ −1)이어야 합니다. 그 위에 k = 2면 `a+0x28 == b+0x28`, k = 3이면 `a+0x50 == b+0x50`이 더 필요합니다. +0x40·+0x48·+0x50은 요청 생성 때 info[7]·info+10 참조·info[0xC]입니다(§3.5 요청 필드).
- 처리 순서:
  1. mgr+0x50 목록의 요청은 AggregateNum 1로 하나씩 분배합니다.
  2. 묶음 목록(mgr+0x20, 개수 +0x90)은 맨 앞 요청 A를 잡고, 목록 전체에서 `same(A, ·)`인 요청 수를 세며 빼냅니다(A 자신 포함).
  3. A+0x30 > 0이고 지연 목록에 `same`인 항목이 있으면 분배하지 않습니다.
  4. 아니면 `0x71027b877c(A, 센 수)`로 분배합니다. **AggregateNum = 같은 프레임에 같은 대상(·종류)으로 들어온 요청 수**입니다.
- 지연 목록(mgr+0x69140): 항목의 남은 시간(+0x58)을 매 프레임 1/60씩 줄이고 0 이하면 지웁니다. 즉 **req+0x30 = 같은 대상·종류의 히트 이펙트를 다시 내지 않는 억제 시간(초)**입니다.
- 네트워크로 받은 `HitEffect` 이벤트는 받는 쪽이 조작 플레이어일 때(`+0xD470` 비교) `0x71027b4aa4`로 바로 집계 방출됩니다.

**θ와 바닥 3종**: a = π/2 − |π/2 − θ|. 탄이 바닥에 수직으로 꽂히면 v̂·n = −1 → θ = π → a = 0 → kind 0 `FloorSplash`. 비스듬히 스칠수록 θ → π/2 → a → π/2 → kind 2 `FloorSplashDist`. 30°/60° 경계 [판독]. 1차 문서의 "θ 정의·벽 슬롯 사용처 [미확정]" → 해소. 벽 판정 상수 0.64144969는 각도로 약 50.1°(acos)입니다.

**피격 표**: HitEffectConfig에서 행(탄 종류, 슈터는 `Shooter`/`Shooter_CriticalHit`)과 열(`<반응>_<대상>`, 예 `Damaged_Default`)로 셀을 찾습니다. 셀이 없으면 `<행>___<반응>_Default`를 씁니다. 셀 필드 오프셋은 리플렉션으로 E1 +0x48, E2 +0x50, S1 +0x58, S2 +0x60이고, 방문 순서 S1, S2, E1, E2에 맞춰 "설정됨" 플래그가 +0x68..+0x6B에 있습니다(`param_reflect.py E1 E2 S1 S2`, 방문 0x710279ecdc) [판독].

`Shooter` 행 (전체는 `HitEffectConfig.json`):

| 열 | E1 (ELink, 집계) | E2 (코드 파티클 / ELink) | S1 (SLink, 집계) | S2 (SLink, 즉시) |
|---|---|---|---|---|
| Damaged_Default | HitEffective | Hit | ヒット | インク被弾 |
| Damaged_Shield | HitEffective | Hit | シールド | インク被弾 |
| Armored_Default | HitInvalid | Hit | アーマード | インク被弾 |
| Invincible_Default | HitInvalid | Splash | ノーダメージ | インク被弾 |
| Constant_Default | — | Splash | — | インクヒット |
| Constant_Water | — | SplashWater | — | 水没 |
| Constant_KebaInk | HitInvalidKebaInk | — | ケバインクヒット | — |
| Cure_Default | HitEffective | Hit | ヒット | — |

- **지형 착탄음**: `Constant_Default`(E2 Splash = 바닥/벽 스플래시)의 S2 `インクヒット`가 지형 착탄음입니다. SLink HitEffect의 `インクヒット`는 SubjectiveType이 Focused면 IsPaintable·Velocity(> 0.9 강/약)로 갈리고, 그 밖(NotEqual Focused)은 Random 컨테이너입니다([effect_resources.md](effect_resources.md) §4). "Constant 반응 = 지형 명중"은 E2 Splash와 묶인 데이터 형태로 본 [추정]입니다(반응 열을 고르는 코드 미추적).
- S1/S2가 "공격자/피격자" 중 누구 기준인지: 둘 다 같은 HitEffect 사용자 인스턴스(관리자 소유)에서 나가고, SubjectiveType은 req+0x34 플레이어로 정합니다(`0x71027b5430`). +0x34가 공격자인지 대상인지는 [미확정]입니다.
- **5차(2026-10-03) 해소 [판독]:** 탄 명중 요청은 `0x71016d99f4`(BulletHitEffect, 접촉, 방향, info) → `0x71016d9c60`이 스택에 만들어 `0x71027b4704(*0x7105798618, req)`로 넣습니다. 여기서 **req+0x34 = 탄 소유 플레이어 번호**입니다. 헬퍼 +0x30(탄) → vt+0x78 객체 +0x208 → 액터 id, 없으면 탄 생성 정보(+0x108)+0x1C를 플레이어 번호로 바꿉니다(`0x71026437d0`). req+0x38은 이 경로에서 −1로 남습니다. 따라서 S1/S2의 SubjectiveType은 **쏜 사람 기준**입니다.
- SubjectiveType 결정 `0x71027b5430(inst, p)` [판독]:
  - p == 조작 플레이어 번호(`*0x7105791bd0`+0xD474)이면 0 Focused.
  - p < 0이면 2 Enemy.
  - 그 밖은 p 플레이어의 팀(+0x160)이 조작 플레이어 팀과 같으면 1 Friend, 다르면 2 Enemy.
  - 값이 바뀔 때만 속성 갱신 비트(+0x70 |= 0x10)를 켭니다.
  - 사격장 1인 연습에서 자기 탄의 명중은 Focused입니다.
- req 나머지 필드 [판독]: +0x00 위치, +0x0C 법선(info+0x10, NaN이면 접촉에서 다시 구함), +0x18 속도, +0x24 접촉 재질 값, +0x28 info[0], +0x2C `0x71028fed18(info[1..3])`, +0x30 info[8] (지연), +0x3C paintable(`0x71012d68cc`), +0x3D 탄 vt+0x208 결과, +0x3E 소유자+0x108+0x6D, +0x40 info[7], +0x50 info[0xC].

## 4. 데이터: 스플래시 슈터 사용자 [데이터]

### 4.1 ELink `WeaponShooterNormal` (`analysis/effect_sound/elink_WeaponShooterNormal.json`)

로컬 속성: `MuzzleShotDirXZDot`(F32, −1..1), `StandAloneType`(Enum; 값 문자열 `None, Die, DieInWater, DieInKebaInk, Throw` [추정: 문자열 위치]).

| 키 | 구조 | 에셋(RuntimeAssetName) | 파라미터 |
|---|---|---|---|
| マズルフラッシュ | 에셋 | `WpShtrMzfNml` | Bone `Muzzle`, Matrix 2, BitFlag 14, **Delay = Curve(MuzzleShotDirXZDot): (0.75→2.0), (1.0→0.0)** |
| InkDive | Switch StandAloneType | `== DieInWater` → `GearWaterSplash` / `!= None` → `GearInkDive` | Clip 4, Matrix 0 |
| WaterRipple | Switch SpecMode(전역) | `!= Coop` → `GearWaterRipple` / 기본 → `GearWaterRippleCoop` | Clip 4 |

액션 슬롯 `State[0]`: `FireImpact` → 트리거 0, `FireOn` → 트리거 1. 둘 다 `マズルフラッシュ`, startFrame 0, endFrame 0x7FFFFFFF, flag 1.

Delay 커브는 점 사이 선형 보간입니다 [판독, xlink_format.md §4.3]. 속성 값은 `0x7102578c34`가 매 갱신 뼈 X축(XZ, 반전)과 플레이어 +0x538 벡터의 내적으로 씁니다(§3.2) [판독]. 내적이 1이면 지연 0, 0.75 이하이면 2(프레임으로 추정)입니다.

### 4.2 SLink `WeaponShooterNormal` (`slink_WeaponShooterNormal.json`)

로컬 속성 `SubjectiveType`(값 문자열 `Focused , Friend , Enemy` [추정]: 기준 플레이어 자신 / 아군 / 적). 사용자 파라미터: Priority 0.5, ArrangeGroupParams 192, 나머지는 기본값.

| 키 → 조건 | RuntimeAssetName | GroupName | Volume | Pitch | DistanceParamSetName | DistCoef | 기타 |
|---|---|---|---|---|---|---|---|
| Fire → Focused | Wp_ShooterNormal_Shot_00 | Weapon_AttackFocused | Random 0.9–1.1 | **Random2Pow** 0.7–1.25 | WpMuzzle_HighSensi | 12.22 | BitFlag 9, UseOcclusion false |
| Fire → Enemy | Wp_NormalShot_02 | Weapon_InsLimit_00 | Random 0.9–1.1 | Random 1.1–1.2 | WpMuzzle_HighSensi | 12.22 | BitFlag 9 |
| Fire → Friend | Wp_NormalShot_Blurred_02 | Weapon_InsLimit_00 | Random 0.9–1.1 | Random 1.1–1.2 | WpMuzzle_HighSensi | 12.22 | BitFlag 9 |
| OnAttach → Focused | Wp_Shooter_Attach_00 | Weapon_Default | — | — | LowSensi | 5.0 | BitFlag 11 |
| OnDetatch → Focused | Wp_Detach_00 | Weapon_Default | 0.9–1.0 | 0.9–1.1 | LowSensi | 5.0 | BitFlag 8 |

에셋 파일: 발사음 3종은 `Sound/Resource/WeaponShooterNormal.bars.zs`, 장착·분리음은 `Shooter.bars.zs`에 있습니다.

### 4.3 전역 속성 (RSDB XLinkPropertyTable)

`SpecMode`(Versus 0, Mission 1, Coop 2, Other 3), `IsWalk`, `FestivalState`, `GlobalWind`, `CoopWeather`, `SeqMainState_*`, `MissionProgressLevel`, `MiniMapScale` 등 14개입니다. 전역 속성은 게임 시스템이 값을 넣고, 모든 사용자의 Switch가 이 값을 봅니다.

## 5. 상태와 수명

| 대상 | 시작 | 유지 | 끝 |
|---|---|---|---|
| 발사음 | 탄 생성 성공 직후 키 방출(원샷) | 에셋 길이(0.5–0.6 s) | 자연 종료. 루프 아님(loopEnd 없음) [데이터] |
| 장착음 | `OnAttach` | 0.25 s | 자연 종료 |
| 탄 파티클 | 탄 생성 시 풀 핸들 획득 | 매 갱신 위치 기록 | 탄 소멸 시 핸들 반환 |
| 착탄 스플래시 | 충돌 처리 시 | Splash 수명 10–14프레임, Crown 12프레임(§2.2.6) | 자동 |
| xlink 인스턴스 | 첫 방출 시 calc 큐 등록 | 이벤트가 살아 있는 동안 calc | 참조 0 [추정] |

같은 프레임에 여러 발이 나가면 키 방출도 발마다 일어납니다. 발사음 그룹 `Weapon_AttackFocused`·`Weapon_InsLimit_00`의 GRP 레코드에는 **동시 발음 제한기가 없습니다**(제한기 종류 0) [판독+데이터]. 두 그룹에는 대신 0.016(+0x84 = 레코드 [0x21])이 게임 그룹 객체 +0x1b8에 들어가며, 그 의미는 [미확정]입니다([sound_resources.md](sound_resources.md) §4.3).

제한기가 있는 그룹은 정렬 뒤 **앞쪽 limitCount 개가 남고**, 나머지는 즉시 정지(핸들 종류 1 또는 hard 플래그)하거나 일시정지됩니다 [판독 + 실행, sound_resources.md §4.3.2]. 사격장에서 들리는 그룹 중 제한기가 있는 것은 [데이터, `analysis/vfx/agst_grp_dump.txt`]:

| 그룹 | 쓰는 소리 | 제한기 종류, 개수 |
|---|---|---|
| `BulletHit_ToObject` | S1 `ヒット`(`HitEf_Damage_00`) | 4, 1 |
| `InkSpray_NotFocused` | S2 `インク被弾`(NotFocused) | 1, 5 |
| `BulletHit_Marking` | 표적 `MarkingStart` | 1, 1 |
| `Obj_InsLimit_00`, `Obj_Default`, `Weapon_*` | 표적 `ダメージ`/`Break`, 발사음 | 0(없음) |

종류 4는 순서 키 +8이 큰 보이스를 앞에 두므로 `ヒット`는 +8이 가장 큰 하나만 남습니다. +8의 게임 의미(시작 순번 여부)는 [미확정]이라, "가장 최근 소리가 남는다"고 확정하지 않습니다.

| 대상 | 시작 | 유지 | 끝 |
|---|---|---|---|
| InkAction(무기 +0x320) | 매 갱신 FireOn/FireOff(보류), 쏜 갱신 FireImpact(즉시) | 무기 +0x374 = 마지막 즉시 변경 프레임 | 다른 액션으로 바뀔 때 |
| 머즐 플래시 | FireImpact 액션 변경 → `State[0]` 트리거(이미 FireOn에서 넘겨받은 이벤트가 있으면 새로 안 냄) | FireImpact↔FireOn 동안 이벤트 유지, 이미터가 5/7프레임마다 방출 | FireOff 등 이 에셋이 없는 액션으로 바뀔 때 페이드 [판독] |
| 히트 집계(S1·E1) | 명중마다 `0x71027b4aa4`에 쌓임 | 프레임 처리 `0x71027b7938` | AggregateNum과 함께 방출 |

## 6. 웹 포팅 구조

| 모듈(웹 권장 이름) | 원본 대응 | 책임 |
|---|---|---|
| `XLinkDatabase` | XLNK 파일 + `effect_xlink.py dump` | 사용자 JSON 로드, CRC32 이름 → 사용자 |
| `XLinkComponent` | XC(+0x78 ELink, +0x80 SLink) | 액터별 ELink/SLink 인스턴스 두 개, `emit(key, mode)` |
| `XLinkUserInstance` | xlink2 UserInstance | 로컬 속성, Switch/Random/Blend/Sequence 평가, 액션 슬롯 |
| `GlobalXLinkProps` | 전역 PropertyDefinition | SpecMode 등 |
| `SoundPlayer` | Alto/aal | AudioBuffer 뱅크, Volume/Pitch/Delay, 그룹 제한, 거리 감쇠 |
| `EffectPlayer` | ELink 에셋 실행 | 이미터셋 재생(뼈 부착, Delay, Scale, 색) |
| `BulletParticleMgr` | OneEmitter 관리자(0x71018b2cc0 계열) | 팀×슬롯 인스턴스 풀, 탄 파티클, 착탄 스플래시 |
| `HitEffectTable` | HitEffectConfig + 로더 0x71027b5980 | (행, 반응, 대상) → E1/E2/S1/S2 |

갱신 순서(원본 순서가 확인된 것만): 슈터 갱신 `0x7102578c34` 앞부분에서 FireOn/FireOff 요청 → 같은 갱신 안에서 발사(탄 생성 → SLink 발사 키 방출) → FireImpact 액션 변경(ELink 머즐 플래시) → 끝에서 MuzzleShotDirXZDot 갱신 → (xlink calc 큐는 프레임 후반에 처리, 순서 [미확정]) → 탄 갱신에서 파티클 위치 기록. MuzzleShotDirXZDot이 FireImpact보다 늦게 쓰이므로 첫 프레임 Delay는 직전 갱신 값으로 계산될 수 있습니다(calc 시점 미확정).

```ts
// 발사 (0x7102581ccc 대응)
function onShotFired(weapon: Weapon, shooter: Player, muzzlePos: Vec3) {
  if (farCull(muzzlePos, shooter.team)) return;                    // R=600 (조건부 600-500*min(n/30,1))
  const key = weapon.param.VariableShotRepeatStartFrame > 0
      ? (weapon.state98 > 0 ? 'FireOn' : 'FireImpact') : 'Fire';
  weapon.xlink.slink.props.set('SubjectiveType', subjective(shooter, viewer)); // Focused/Friend/Enemy
  weapon.xlink.slink.searchAndEmit(key);                           // 무기+0x5f0 vt[3] = SLink 만 [판독]
  weapon.setInkAction(InkAction.FireImpact);                        // 0x7102864104 → ELink·SLink State[0] [판독]
}
function setInkAction(w: Weapon, id: number, now = gameFrame) {   // 0x7102864104
  if (id !== 0) { if (now <= w.lastImpactFrame) return; if (id < 7 || id > 10) { w.pendingAction = id; return; } }
  if (w.action === id) return;
  w.action = id; const name = INK_ACTION_NAMES[id];
  w.xlink.elink?.changeAction(0, name, w.actionFrame | 0); w.xlink.slink?.changeAction(0, name, w.actionFrame | 0);
  w.lastImpactFrame = Math.max(w.lastImpactFrame, now);
}
function muzzleShotDirXZDot(boneMtx: Mat34, d: Vec3) {             // 0x7102578c34 끝
  let x = -boneMtx[0][0], z = -boneMtx[2][0]; const l = Math.hypot(x, z);
  if (l > 0) { x /= l; z /= l; }
  return x * d.x + z * d.z;                                        // d = 플레이어 본체 +0x538 = 카메라 리그 수평 시선
}
function subjective(p: Player, viewer: Player) { return p === viewer ? 'Focused' : p.team === viewer.team ? 'Friend' : 'Enemy'; }
```

에셋 변환:
1. 사운드: `sound_bars.py wav`(BWAV → vgmstream → WAV). 필요한 이름만 `sound_index.json`으로 찾아 변환합니다. 스트림은 `Sound/Resource/Stream/*.bwav`를 바로 vgmstream에 넣습니다.
2. 이펙트: `effect_esetb.py ptcl`(VFXB 추출, static 120 MB) → `effect_vfxb46.py eset`(이미터·텍스처 목록) → `effect_vfxb46.py bntx` + `graphics_bntx` 디코드(필요한 텍스처만, 형식 0x15 FLOAT은 `effect_bntx_float.py`). 이미터 운동 파라미터는 `vfx_emitter46.py fields`로 뽑습니다(필드표·식 [effect_resources.md](effect_resources.md) §2.2). 형상(volumeType)별 위치 식과 일부 바이트는 남았습니다.

웹에서 바꿔야 하는 부분: 원본은 xlink 인스턴스를 calc 큐로 매 프레임 갱신합니다. 웹은 원샷 에셋을 즉시 재생하고, 루프·Sequence·액션 트리거만 프레임 콜백에서 처리합니다. 결과는 같다고 봅니다 [추정]. 난수(Volume/Pitch, Random 컨테이너)는 원본 xlink System 난수기 순서를 맞출 근거가 없습니다. 연출용 값이라 비결정 난수를 허용합니다.

## 7. 검증

| 검증 | 종류 | 결과 |
|---|---|---|
| XLNK 두 파일 전체 구조 | [실행: 자체 파서] `effect_xlink.py check` | 표 경계·사용자 경계 1,162개·키 CRC·트리거 참조 전부 일치 |
| 사용자 이름 CRC32 | [실행] | 액터 UserName 기반 ELink 390/429, SLink 465/733 복원 |
| 키 → 에셋 평가 | [합성] `effect_xlink_eval.py --selftest` | 26/26 PASS (`analysis/effect_sound/selftest_xlink_eval.txt`). Fire×3 SubjectiveType, OnAttach, 무음 조건, Volume 범위, Random2Pow 중앙 집중, 머즐 Delay 커브 4점, InkDive/WaterRipple 스위치, Grid 4, Random2 직전 회피, Curve 계단 |
| Alto 롤오프 | [합성] `sound_alto.py selftest` | 7/7 PASS. 전수 표 `analysis/effect_sound/alto_aroc_models.txt` |
| FLOAT 텍스처 | [실행] `effect_bntx_float.py selftest`/`dump` | 블록선형 왕복 4/4, 표본 3장 디코드 |
| BWAV 디코드 | [실행: vgmstream] | 3개 WAV, AMTA 피크와 6자리 일치 |
| BARS 전수 | [실행] | 533 파일 4,641 항목 파싱, SLink 참조 4,052종 중 4,051종 존재(없는 것 `@Blank`) |
| 이펙트 이미터셋 | [실행: 섹션 순회] | 대상 10종의 이미터·텍스처 목록, 텍스처 7장 PNG |
| 코드 경로 | [판독] | 키 선택·거리 컬링·방출 mode·OneEmitter 슬롯·스플래시 분류 |
| VFXB v46 필드 | [실행: 자체 파서 + 셰이더 역번역] `vfx_emitter46.py fields`, `shader_dump prog-bfsha` | 키 개수 u32 5개·calcType·followType·billboard/rot·WORLD_GRAVITY·색 종류가 대상 9개 이미터의 셰이더 옵션과 전부 일치 |
| 파티클 식 | [합성] `vfx_emitter46.py selftest` | 12/12 PASS(airRegist 극한 연속, 키 보간 경계, Splash 높이·수명 범위) |
| AUDC·AADR | [합성] `sound_alto.py selftest` | 16/16 PASS(AROC 7 + AUDC 6 + AADR 3) |

웹 구현이 맞춰야 할 기대값(합성 테스트와 같음):
- `evaluate(SLink WeaponShooterNormal, 'Fire', {SubjectiveType:'Focused'})` → `Wp_ShooterNormal_Shot_00` 하나, Volume ∈ [0.9, 1.1], Pitch ∈ [0.7, 1.25].
- Enemy → `Wp_NormalShot_02`, Friend → `Wp_NormalShot_Blurred_02`. SubjectiveType이 없으면 아무것도 재생하지 않습니다.
- 스플래시 분류: θ = 10°이면 Floor(kind 0), 45°이면 Near(1), 80°이면 Dist(2), 170°이면 a = 10°로 접혀 Floor(0) [판독식 재구현]. θ는 탄 속도 방향과 법선의 각이므로, 바닥(n = (0,1,0))에 v = (0,−1,0)으로 수직 낙하하면 θ = 180° → Floor, v = (1,−0.1,0)으로 스치면 θ ≈ 95.7° → Dist.
- 벽 판정: n.y = 0.64144969면 벽(≤), 0.6414498이면 바닥.
- 히트 컬링: 400.0 (조건부 400 − 300·min(n/30,1)).
- 거리 컬링: 기준점에서 600.0 초과면 생략, 정확히 600.0이면 방출(엄격 부등호 `R² < d²`) [판독].

스텁·미검증 범위: 원본 게임은 실행하지 않았습니다. Switch 선택 순서·Curve 보간·compare·Random2·Grid는 이제 [판독] 규칙의 재구현이고(합성 테스트 26/26), 원본 실행 비교는 아닙니다. Alto 롤오프 모델은 재구현 합성 테스트(`sound_alto.py selftest` 7/7)만 했습니다. 이미터 파티클 운동, 그룹 제한은 구현·검증하지 않았습니다.

### 7.4 r9 사운드 제한기·정지 시간 신규 확정 (2026-10-03)

[사운드 제한기 런타임](sound_limiter_runtime.md) §3–10: 그룹1B8의0.016은초단위정지duration이며4종전체적용/타이머/실제CPU정지경로4096원본대조0bad,originalenvelope768생성/10284진행0bad. type0인슈터그룹에는동시발음개수제한기로쓰지않는다. 이전§5/§8의0.016미확정및4종미실행은정정한다. 마지막SDKPCM/전체XLink수명은별도미확정이다.

## 8. 미확정과 다음 근거

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| 발사 키 방출 대상(무기+0x5f0)과 mode | **해소** [판독]: SLink 전용 래퍼 슬롯 3 | — |
| 머즐 플래시 액션 변경 시점 | **해소** [판독]: 쏜 갱신에 FireImpact(0x7102579af4) | — |
| 보류 액션(+0x384) 적용, FireImpact→FireOn 재발생 | **해소** [판독] §3.2: 슬롯 19 `0x710286540c`가 적용, 넘겨받기라 재발생 없음 | 슬롯 19 호출 시점 |
| `MuzzleShotDirXZDot` 값 계산 | **식 해소** [판독]. +0x538 = PlayerCamera+0x1a4(리그 수평 시선) 사본, 매 프레임 0x7102458630이 씀 [판독, player_state.md §6.1.2, 5차에 문서 연결] | 웹 무기 뼈 행렬(Muzzle·무기 X축) 공급 |
| 착탄 각도 θ의 정의, 벽 스플래시 슬롯 사용처 | **해소** [판독] (§3.5) | — |
| 지형 착탄 효과음 | **해소** [판독+데이터]: Constant_Default S2 `インクヒット` | 반응 열(Constant 등)을 고르는 호출자 코드 |
| S1/S2 기준 플레이어 | 부분: 둘 다 관리자 인스턴스, SubjectiveType은 req+0x34. **5차 해소** [판독] §3.5: req+0x34 = 탄 소유 플레이어(`0x71016d9c60`), 판정 규칙 `0x71027b5430` | DamageHelper 경로 등 다른 요청 생성자의 +0x34 |
| AggregateNum 묶는 기준, req+0x30 지연 목록 | **5차 해소** [판독] §3.5: 같은 대상(+0x48)·종류(+0x40, k=2면 +0x28, k=3이면 +0x50)끼리 개수, +0x30초 동안 같은 요청 억제 | 요청 +0x40 값을 정하는 info[7] 생성자 |
| 발사·히트 컬링 n | **5차 해소** [판독] §3.2: 그 팀의 살아 있는 탄 수(등록 `0x7101645590`, 해제 `0x7101645f84`) | 기준점 객체(카메라 추정)의 정체 |
| 리스너·지향성·제한기 생존 | **5차 해소** [실행] ([sound_resources.md](sound_resources.md) §4.1.2·§4.1.3·§4.3.2) | 리스너 주시점 공급원, 보이스 +8 writer |
| 필터 컷오프·패닝 이득·FarFx 버스 | [미확정] (패닝 입력만 [판독], sound_resources §4.5) | aal 보이스 적용, SpeakerBalanceUnifier |
| xlink compare 1–4, Switch 순서, Curve 형태 | **해소** [판독] ([xlink_format.md](xlink_format.md)) | — |
| Alto 거리 감쇠 | **모델·평가식·우선순위(AUDC)·지향성(AADR) 해소** [판독] ([sound_resources.md](sound_resources.md) §4.2). DistCoef 결합은 게임 쪽 재정의(0x7103129c98)까지 좁힘 [미확정]. **6차 해소:** 확장+4 = 1/DistCoef, writer = 게임 SLink 훅 `0x710313d4ec` [실행 219,680건] (sound_resources §4.2.7). AATN 세트 칸 배치 확정 [판독] (§4.2.4) | 전역 단위 값, 필터 종류 선택(sound_resources §4.6) |
| 그룹 동시 발음 제한 | GRP 레코드 → 그룹 객체 배치 **판독**, 무기 그룹 `Weapon_InsLimit_*`은 제한기 없음(type 0) [판독+데이터]. **5차:** 비교 키·guard [실행 2,304건], 정렬 뒤 앞쪽 limitCount 생존·억제 [실행 600경우] (§5, sound_resources §4.3.1~4.3.2) **6차:** 보이스 +8 = 시작 순번, writer `0x71037d790c` [실행 2,445회] (sound_resources §4.3.2) | 그룹 +0x1b8(0.016) 의미, 종류 2~4 정렬 실행 |
| VFXB v46 이미터 필드 | **주요 필드 해소** [판독] ([effect_resources.md](effect_resources.md) §2.2) | 형상별 식, Render/Combiner |
