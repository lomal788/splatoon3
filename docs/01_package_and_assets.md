# 01. 패키지와 에셋 구조

RomFS 구성, 데이터 포맷, 그리고 액터·파라미터가 어떻게 이어지는지를 정리합니다. 추출 방법은 [00](00_extraction_pipeline.md)을 참고하세요.

## 1. RomFS 최상위 [데이터]

| 폴더 | 파일 수 | 바이트 | 내용 |
|---|---|---|---|
| `Model/` | 1283 | 2,728,439,581 | `*.bfres.zs` 모델·애니 (FRES 버전 `00 0a 00 00`) |
| `Sound/` | 855 | 1,236,217,303 | `Resource/*.bars.zs`(533), `Resource/Stream/*.bwav`(316), `Bgm`, Alto 설정(`*.alto__AltoConfig.bgyml`, BusSetting은 빅엔디언 BYML) |
| `Bake/` | 139 | 468,307,045 | `Scene/*.bkres.zs` 스테이지 베이크(라이트맵 등) **[추정 — 이름]** |
| `Layout/` | 348 | 57,784,337 | `*.Nin_NX_NVN.blarc.zs` UI 레이아웃 |
| `Effect/` | 3 | 56,123,539 | 이펙트 세트 `*.esetb.byml.zs`, `EffectFileInfo` |
| `Pack/` | 3682 | 33,409,632 | `Actor/*.pack.zs` 3,572, `Scene/*.pack.zs` 107, `Params.pack.zs`, `SingletonParam.pack.zs`, `Bootup.Nin_NX_NVN.pack.zs` |
| `Font/`, `Tex/`, `Shader/`, `UI/`, `Lib/` | | | 폰트, 공용 텍스처, `*.bfsha.zs` 셰이더, UI 아이콘(`*.bntx.zs`), agl/gsys/sead 리소스 |
| `Mals/` | 14 | | 언어별 메시지 아카이브 `<언어>.Product.100.sarc.zs` |
| `RSDB/` | 64 | | `*.rstbl.byml.zs` 데이터베이스 표 (무기·기어·스테이지·씬 등) |
| `System/` | 5 | | `RomConfig`(부트 씬 `Work/Scene/Boot...`), `HeapSize`, `AddressTable`, `ResourceSizeTable` |
| `Phive/`, `AI/`, `Logic/`, `Event/`, `UniqueSequenceSPL/` | | | 물리(Phive=Havok 래퍼) 설정·내비메시, AI 노드 정의, 이벤트 플로우, 시퀀스(`*.ainb`) |

확장자별 합계는 `extracted/romfs_list.txt`에서 다시 낼 수 있습니다.

## 2. 데이터 포맷 [데이터]

| 포맷 | 판독 | 비고 |
|---|---|---|
| `.zs` | zstd, **사전 없음**(frame dict_id 0) | `spl_data.unzs` |
| `.pack` | SARC, 리틀엔디언, 파일명 테이블 있음 | `spl_data.sarc`. 안쪽 파일은 대부분 비압축 BYML |
| `.bgyml`, `.byml`, `.rstbl.byml` | BYML v7, `YB` 리틀엔디언 | 노드 0xA0 문자열, 0xC0 배열, 0xC1 사전, 0xD0 bool, 0xD1 s32, 0xD2 f32, 0xD3 u32 등. 0x20/0x21 해시 사전도 처리 |
| `.bfres` | FRES v10, 텍스처는 내장 `textures.bntx`(BNTX 4.1) | BfresLibrary(소스 복사본)로 샘플 14개 판독 성공 **[실행]**. `web/tools/graphics_convert.py`, `graphics_bntx.py` — [graphics/formats_bfres_bntx.md](graphics/formats_bfres_bntx.md) |
| `.blarc` | zstd SARC 안 BFLYT/BFLAN v9 | [ui/ui_layout_format.md](ui/ui_layout_format.md). 파츠는 같은 아카이브가 아니라 별도 blarc를 가리킴 |
| `.bntx` | BNTX 4.1 | `web/tools/graphics_bntx.py`, 형식 0x15(R16G16B16A16 FLOAT, VAT로 추정)는 `effect_bntx_float.py` — [graphics/formats_bfres_bntx.md](graphics/formats_bfres_bntx.md) |
| `.bars`, `.bwav` | BARS v1.2 / AMTA v5 / BWAV v1, 거의 전부 DSP-ADPCM | `web/tools/sound_bars.py`, 디코드는 `c:/dev/mpj/tools/vgmstream/vgmstream-cli.exe` — [effect_sound/sound_resources.md](effect_sound/sound_resources.md) |
| `.belnk`, `.bslnk` | XLNK v0x22 / v0x1F (Splatoon 2 xlink2에서 위치 필드 64비트) | `web/tools/effect_xlink.py` — [effect_sound/xlink_format.md](effect_sound/xlink_format.md) |
| `.bphsh` | Havok TAG0, 본문 hknpMeshShape(정점 1/512 고정소수점, shapeTag → 재질표) | `web/tools/collision_mesh.py` — [gimmick/collision_mesh.md](gimmick/collision_mesh.md) |
| `.esetb.byml` | BYML{Esets, PtclBin = VFXB v46} | `web/tools/effect_esetb.py`, `effect_vfxb46.py` — [effect_sound/effect_resources.md](effect_sound/effect_resources.md) |

## 3. 경로 규칙 [데이터]

BYML 안의 참조는 `Work/<경로>.<타입>.gyml` 형식입니다. 실제 파일은 `Work/`를 떼고 확장자 `.gyml`을 `.bgyml`로 바꾼 이름으로, 해당 액터 팩이나 `Params.pack.zs` 안에 있습니다.

예: `Work/Component/GameParameterTable/WeaponShooterNormal.game__GameParameterTable.gyml` → `Params.pack.zs`의 `Component/GameParameterTable/WeaponShooterNormal.game__GameParameterTable.bgyml`.

`$parent` 키는 상속입니다. 자식 파일은 부모와 다른 값만 담습니다. 예: `BulletShooterBase` ActorParam의 `$parent`는 `Work/Actor/BulletParent.engine__actor__ActorParam.gyml`이고, `Params.pack.zs`의 파일 78개가 `$parent`를 씁니다.

파라미터 값의 병합은 **필드 단위**입니다. 코드가 필드를 읽을 때 그 객체의 "설정됨" 플래그가 꺼져 있으면 부모 파라미터 객체로 올라가고, 끝까지 없으면 생성자 기본값을 씁니다 **[판독]** ([02 §2](02_code_and_params.md), [weapon/shooter_bullet.md §4.1](weapon/shooter_bullet.md)). 배열 필드의 병합 방식은 확인하지 않았습니다 **[미확정]**.

## 4. 액터 → 컴포넌트 → 파라미터 [데이터]

무기 하나(스플래시 슈터, `Shooter_Normal_00`)를 예로 듭니다.

```
RSDB/WeaponInfoMain  행 Shooter_Normal_00
  Id 40, Label "スプラシューター", Range 12.5, SpecialPoint 200
  SubWeapon   Work/Gyml/Bomb_Suction.spl__WeaponInfoSub.gyml
  SpecialWeapon Work/Gyml/SpUltraShot.spl__WeaponInfoSpecial.gyml
  SpecActor   Work/Actor/WeaponShooterNormal.engine__actor__ActorParam.gyml
  GameActor   Work/Actor/WmnG_Shooter_Normal_00...   (표시용 모델 액터)

Pack/Actor/WeaponShooterNormal.pack.zs
  ActorParam  $parent MainWeaponParent
    Behavior           → SplWeaponShooter.game__BehaviorParam
    GameParameterTable → WeaponShooterNormal (Params.pack)
    ActorReservation   → BulletShooterBase ×32, BulletSplashShooter ×32, BulletWallDrop ×16 미리 생성
    ModelInfo          → Work/Model/Weapon/Wmn_Shooter_NormalT/output/Wmn_Shooter_NormalT.fmdb

Pack/Actor/BulletShooterBase.pack.zs
  ActorParam  $parent BulletParent
    Behavior  ClassName "spl::BulletShooterBase"   ← 코드 클래스 이름 (02 문서 참고)
    BulletBodyRef → BulletBodyControllerEntity → UnitArray[ BulletSimple.game__BulletBodyEntityParam ]
                    LayerEntity "SplInkBullet_FriendThrough", BlockableLayerHitMask "HitAll"
    PhysicsRef → ControllerSet CharacterControllerName "BulletSimple"
    GameParameterTable → BulletShooterBase (spl__DamageParam만 있음)
```

`Behavior.ClassName` 문자열은 main 안의 클래스 이름 문자열과 정확히 같고, 그 문자열을 반환하는 함수가 해당 클래스 vtable의 슬롯 2에 있습니다 **[판독]**. 그래서 데이터의 클래스 이름에서 코드 vtable로 바로 갈 수 있습니다([02](02_code_and_params.md) §3).

## 5. GameParameterTable [데이터]

`GameParameters` 사전의 각 항목은 `$type`(코드의 파라미터 구조체 이름, `::`를 `__`로 바꾼 것)과 **기본값과 다른 필드만** 담습니다. 비어 있는 필드는 코드 생성자의 기본값을 씁니다. 예를 들어 `WeaponShooterNormal`에는 `RepeatFrame`이 없는데, `spl::WeaponShooterParam` 생성자 기본값이 6입니다 **[판독]**.

`Params.pack.zs`에 있는 모든 `$type`과 데이터에 나온 필드 목록은 `analysis/param_types_in_data.json`(176종)에 있습니다.

## 6. Banc 배치 → 액터 행렬 [실행]+[판독 — 2026-10-03 6차]

Banc 액터의 `Translate`·`Rotate`(라디안)·`Scale`은 파서 `0x7103d03768`이 엔트리로 옮기고, `0x7103d03f4c`가 생성 정보 +0x40 위치 · +0x4c 회전 3×3(**행 우선, R = Rz·Ry·Rx**) · +0x70 스케일(행렬에 곱하지 않음)로 만듭니다. 씬 섹션 부모 행렬은 로비·대전 맵에서 단위입니다. 원본 실행 4257/4257 비트 일치(`PY web/tools/r6_assets_actor_mtx_emu.py`). 상세·주소·검증은 [gimmick/stage_misc.md](gimmick/stage_misc.md) §5.1. 스케일이 모델·형상 행렬에 들어가는 위치(T·R·S)는 [미확정]입니다.

## 7. 공용 표·리소스 로더 판독 [판독+데이터 — 2026-10-03 6차]

### 7.1 CombinationDataTable 셀의 "필드 없음"과 빈 문자열

`HitEffectConfig`(Bootup 팩 `System/CombinationDataTableData/Default_spl__HitEffectConfig…bgyml`, 셀 `$type spl__HitEffectCell` 816개, 행 48 × 열 17)의 셀에는 `E1/E2/S1/S2` 필드가 아예 없는 경우와 `""`인 경우가 섞여 있습니다 [데이터]. 원본에서는 **둘이 같은 값**입니다 [판독]+[데이터]:

- 셀 생성자 `0x710279ec14`가 `RowKey/ColumnKey`(+0x30/+0x38)와 `E1/E2/S1/S2`(+0x48/+0x50/+0x58/+0x60, 방문 `0x710279ecdc`) 전부를 같은 빈 문자열 포인터 `0x710496315d`("")로 채우고, 설정 플래그 4바이트(+0x68..+0x6b)를 0으로 둡니다 [판독].
- 로더 `0x71027b5980`은 필드를 읽을 때 그 필드의 설정 플래그(예 +0x48 필드는 +0x6a, `0x71027b68e4`)가 꺼져 있으면 부모 파라미터(+0x10/+0x18 사슬)로 올라가고, 부모가 없으면 자기 값(생성자 기본값)을 씁니다(`0x71027b68f4~0x71027b69c8`) [판독]. 이 표의 셀 816개에는 `$parent`가 없습니다 [데이터].
- 따라서 필드가 없으면 `""`과 같은 문자열을 읽습니다. 웹 `common/data/hit_effect.json`이 빈 필드를 생략한 것은 원본 조회 결과와 같습니다. +0x48 필드는 `"Splash"`/`"Hit"`/`"SplashWater"`와 문자열 비교로 종류를 정하며(`0x71027b69c8~`), 빈 문자열은 셋 모두와 다르므로 "그 밖" 분기로 갑니다 [판독]. 데이터에서 이 세 값을 갖는 열은 E2 이므로(리플렉션 표기 +0x48 = E1 과 다름) 리플렉션 이름 대응은 다시 확인이 필요합니다 **[미확정]** — 결론(없음 = "")에는 영향 없음.

### 7.2 VFX 프리미티브: G3NT i번째 ↔ BFRES 모델 i번째

VFXB 로더 `0x710082863c`가 최상위 섹션 사슬을 돌며 `G3PR`(0x52503347)을 만나면 첫 자식 `G3NT`의 본문 시작(자식 +0x14)을 리소스 +0xc8 에 두고 `0x7100829e58`(리소스, G3PR)을 부릅니다. `0x7100829e58`은 G3PR 본문을 ResFile 로 캐스트(`0x710088caec`)해 리소스 +0xa8 에 두고 `0x710082a764`를 부릅니다 [판독].

```
// 0x710082a764 (analysis/decomp/vfx/vfx_lib_02.c 1행)
n = u16 ResFile+0xdc                    // 모델 수
prim = 할당(n × 0x90)
desc = 리소스+0xc8                       // G3NT 첫 항목
for i in 0..n-1:
    0x710082c0a0(prim[i], ResFile+0x28 모델 배열 + i×0x78, desc)
    desc = desc+8 의 next 가 0 이 아니면 desc + next, 아니면 0
```

즉 **i번째 프리미티브 = BFRES 모델 i번째 + G3NT i번째 항목**입니다 [판독]. G3NT 항목의 8바이트(`effect_vfxb.py`가 "의미 미확정"으로 둔 값, 예 `00 01 02 ff 04 ff 00 00`)는 `0x710082c0a0`이 +0x14·+0x15(8바이트 중 4·5번째)를 정점 속성 인덱스로 써서 `_p0`·`_u1` 등이 없을 때 대체 속성을 고르는 데 씁니다 [판독-부분]. `static` VFXB 의 G3NT 185개 = 모델 185개 [데이터]. 웹 `asset_fx.py`의 대응 규칙은 원본과 같습니다.

### 7.3 효과음 AMTA 피크 [데이터]

AMTA `data`+0x04 피크는 48 kHz 원본에서는 자체 DSP-ADPCM 디코드 피크와 6자리 일치합니다([effect_sound/sound_resources.md](effect_sound/sound_resources.md)). 44.1 kHz 원본(웹 번들 195개, 48 kHz 는 106개)에서는 비 `amtaPeak/decodedPeak`가 **0.853~1.428**로 흩어집니다(예 Spray07 1.348, HitEf_Slime_02 1.428, Pl_FootUpLStone00_03 0.853) [데이터, `web/games/splatoon3/assets/sfx/*/sfx.json`]. 대역 제한 재샘플만으로는 피크가 15% 줄거나 43% 커지기 어려우므로 "48 kHz 재샘플 뒤 측정"이라는 이전 [추정]은 데이터와 잘 맞지 않습니다. 이 값은 제작 툴이 기록한 것이고, 게임 코드가 이 피크를 읽는지(AMTA 로더 후보 `0x710386c63c`, `0x710386ed4c`)는 확인하지 않았습니다 **[미확정]**.

## 8. 미확정 (2026-10-03 6차 갱신)

| 항목 | 상태 | 다음에 볼 곳 |
|---|---|---|
| 배열 필드의 `$parent` 병합 방식 | [미확정] (§3) | |
| 배치 행렬의 S 합성 위치 | [미확정] — [gimmick/stage_misc.md](gimmick/stage_misc.md) §8 | 컴포넌트 vt+0x50 |
| Box `OffsetRotation`/`Center` 합성 순서 | [미확정] — 같은 곳 | Phive Box 빌더 |
| AMTA 피크(44.1 kHz) 기록 방식·소비 여부 | [미확정] §7.3 | AMTA 로더 `0x710386c63c`/`0x710386ed4c`의 data+4 읽기 |
| ~~CombinationDataTable 빈 필드 = ""~~ | 해소 §7.1 [판독]+[데이터] | |
| ~~VFX 프리미티브 매핑~~ | 해소 §7.2 [판독] | |
