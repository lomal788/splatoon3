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
