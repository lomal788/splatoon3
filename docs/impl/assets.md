# assets — 웹 에셋 변환

시험 사격장(대전 로비 `Lby_Lobby00`, 맵 모델 `Fld_VSLobby`) 1인 연습용 에셋. 출력 `web/games/splatoon3/assets/`, 입구 `catalog.json`.
**좌표·단위·축은 원본 그대로**(Y 위, 게임 단위). 스케일·축 변환 없음. 재생성은 §7 한 명령.

## 1. 구현한 것

| 번들 | 폴더 | 내용 | deps |
|---|---|---|---|
| `common` | `common/` | `data/*.json` 공용 표(§2.1). `lib/basis`(트랜스코더, 기존)는 files 에서 뺌(KTX2Loader 가 직접 받음) | `sfx/common` |
| `map/Lby_Lobby00` | `maps/Lby_Lobby00/` | `visual.glb`, `collision.json+bin`, `placement.json`, `env.json`, `params/SighterTarget*.json·WoodenFigure.json`, `parts/Obj_SighterTarget.glb·Obj_SighterTargetMove.glb·Obj_LobbyCopyrobot.glb`, `data/parts_anim_material.json` | — |
| `character/Player00` | `characters/Player00/` | `body.glb`(Player00) `body_hlf.glb`(Player00_Hlf) `squid.glb`(Player_Squid/Squid), `parts/*.glb` 7개, `anim/human.glb` `anim/squid.glb`, `tex/**.ktx2`, `params/SplPlayer.json`, `data/*.json` | `sfx/player` |
| `weapon/Shooter_Normal_00` | `weapons/Shooter_Normal_00/` | `model.glb`(Wmn_Shooter_NormalT), `params/*.json` 4표, `data/{weapon_info,weapon_spec,bullet_setting}.json` | `effect/shooter`, `sfx/shooter` |
| `effect/shooter` | `effects/shooter/` | `emitters.json`, `tex/*.ktx2`(28) + VAT `tex/*.bin`(2), `prim/*.glb`(10) | — |
| `sfx/shooter` `sfx/player` `sfx/common` | `sfx/<g>/` | `*.ogg`(Opus) + `sfx.json` | — |

근거 문서: graphics/*, effect_sound/*, gimmick/collision_mesh.md, paint/paint_and_score.md, 01_package_and_assets.md, range/shooting_range.md.

## 2. 형식 명세 (최종)

### 2.1 common/data/
| 파일 | 형식 |
|---|---|
| `param_defaults.json` | `{ "<$type>": { 필드: 기본값 } }`. 출처 ① `analysis/param_reflect/<$type>.json` `classes[0].defaults`(154종) — 읽기 실패 값(`{"partial":true}` 76·`{"unwritten":true}` 13, 목록 `analysis/assets_work/param_defaults_dropped.json`)은 뺌. 빠진 것 중 실린 표가 쓰는 것: `spl__DamageParam`(HitPointHolderArray/DamageReceiverArray — 배열, 표에 값 있음), 특수·코옵 계열. ② 리플렉션 직접 실행 `spl__SighterTargetParam`(asset_data.REFLECT_EXTRA). ③ 문서 판독값: `spl__PlayerGearSkillParam_{HumanMoveUp,SquidMoveUp,OpInkEffectReduction}`(player/gear_skills.md §4.3, 필드 `<이름>_{Low,Mid,High}`), `spl__BendCalculatorParam`(Kp 0, Kd 0), `game__RailMovableSequentialParam`(enum 은 데이터 표기 문자열 `cInMove/cLinear/cStop/cTime`, MoveSpeed 1, MoveTime 1.0, WaitTime 0), `game__LiftGraphRailNodeParam`(BreakTime 0). f32 값은 f32 반올림된 double |
| `damage_rate_info.json` | `{ default:1.0, rowKeys[98], colKeys[42], rows:{ <행>:{ <열>: rate } } }` — `DamageRate` 가 있는 셀만(1713). 없는 셀 = 1.0 |
| `hit_effect.json` | `{ rowKeys[48], colKeys[17], rows:{ <HitEffectorType>:{ <Result_수신종류>:{E1?,E2?,S1?,S2?} } } }` — 빈 문자열 필드 생략(원본은 "명시적 없음"과 "필드 없음"을 구분하지만 웹 조회에는 같음 [추정]) |
| `team_color.json` | `dataSets[36]`(RSDB TeamColorDataSet 행 + `name`), `offsets{이름:{Brightness,Hue,Saturation}}`, `colorNames[14]`, `tagEnum`, `hueDirPeak`, `inkColorCorrection`(싱글턴 원본), `inkColorCorrectionDefaults`(생성자 기본값 — graphics/team_color.md §5.2) |
| `singletons.json` | VersusConstant, LobbyConstant, GearSkillTraitsParam, CameraModuleParam, RumbleModuleParam, SoundSpatialConfig, KebaInkMgrConstant, KebaInkPlayerReaction 원본 |
| `phive_config.json` | PhiveConfig 발췌(Layer/SubLayer/HitMask/UserShapeTag/MaterialPreset/Material 컬렉션) 원본 |
| `ink_tex_info.json` | RSDB InkTexInfo 50행(`name` = 행 이름) |
| `ink_stamps.json` | `{ "<텍스처 이름>": { w, h, format, data: base64 R8(행 우선, 행 0 = 텍스처 위쪽 v=0) } }` — `romfs/Model/InkTexture.bfres.zs` BC4 → R. Shot00_0..11, Shot01..04_0..5, WallDrip00/01(+_0..4), Disk, DiskConcave, DiskDonut, Rectangle (52장) |
| `layer_filter_bullet.json` | `analysis/combat/layer_filter_bullet.json` 그대로 |

### 2.2 weapons/Shooter_Normal_00/
- `params/{WeaponShooterNormal,BulletShooterBase,BulletSplashShooter,BulletWallDrop}.json` — GameParameterTable 원본(이 4표는 `$parent` 없음, 있으면 체인 전부 같은 폴더에 둠).
- `data/weapon_info.json` `{ main: WeaponInfoMain 행, sub, special }`.
- `data/weapon_spec.json` — ActorParam(`$parent` 병합) components, `behavior.ClassName`, `actorReservation`(32/32/16), `bullets[이름]{actorChain, behavior, bulletBody(참조 펼침: Layer SplInkBullet_FriendThrough, 구 반지름 0.15 GroundOnly/ExceptGround), bulletSetting(컴포넌트 파일 — romfs 에 없어 `$missing`), bulletSettingInfo(RSDB 행), phive}`.
- `data/bullet_setting.json` `{ rows: { BulletShooterBase|BulletSplashShooter|BulletWallDrop: RSDB BulletSettingInfo 행 } }` (BulletWallDrop 은 행 없음 → null).
- `model.glb` — §2.5 규칙.

### 2.3 characters/Player00/
- `params/SplPlayer.json` GameParameterTable 원본.
- `data/player_actor.json` — SplPlayer 액터 components, phive(`SplPlayer_cct` 캡슐 2, ColBullet 캡슐, CharacterController 원본), componentParams(BulletShotDirAllInkActionParam 등).
- `data/character.json` — 파츠별 bfres·모델·정점·뼈 수, 기본 장비 근거, 클립 목록(`clips.human/squid`, `humanFrames`/`squidFrames` = FSKA FrameCount, `humanMissing`), `teamTextures{파츠:{텍스처이름:"tex/<파츠>/<이름>.ktx2"}}`, `missingPatternTextures`.
- `data/gear.json` — 슬롯별 RSDB 행 원본(head/clothes/shoes/hair/eyebrow/bottom/tank; **HarnessType·IsThinHarness·IsHideHarness·AlphaMaskF/M**), `headParamSet`(Hed 의 GearHeadParamSet), `alphaMasks{이름:"tex/alphamask/<이름>_Opa.ktx2"}`.
- `data/asb_SplPlayer.json`, `data/asb_SplPlayerSquid.json` — `state_asb.py --json` 결과(commands·nodes·header), graphics/anim_state_machine.md 해석.
- `data/player_states.json` `{ states:[{id, human, squid, blend(w2 값), flags}] }` (상태 표 287행).
- `data/anim_material.json` `{ human|squid: { materialAnims:[{name,frames,loop,materials:{<재질>:{params:{<param>:{"<offset>":[프레임별]}|const}, patterns:{<샘플러>:[[프레임,텍스처]]}}}}], boneVisibility? } }` — 정수 프레임 베이크. 몸: Color_Eye, Color_Skin, Blink, Eye_Scroll / 오징어: Sqd_Blink, Sqd_Injection*, Sqd_Surprise, Sqd_Wait.
- `tex/body/*.ktx2`, `tex/squid/*.ktx2` — 재질 애니 텍스처 패턴(눈 색 M_Eye_Alb.00~20, M_Eyelids_Opa.0~3, 오징어 눈 .0~3). `tex/<파츠>/<이름>.ktx2` — 팀색 Tcl(`_su0`)·2cl(`_cp0`) 마스크(선형). `tex/alphamask/*.ktx2` — GearAlphaMask.
- `anim/human.glb`, `anim/squid.glb` — **뼈 노드 + 클립만**(메시 없음). 노드 이름 = 몸 뼈 이름이라 three `AnimationMixer` 를 몸 SkinnedMesh 루트에 붙이면 이름으로 묶임. `animation.extras = {source, frames, loop, fps:60, scaleMode, missingBones}` 보존(gltfpack 이 지운 것을 되넣음). 키 = 정수 프레임(시간 = 프레임/60, LINEAR, `-af 0` 재샘플 없음). gltfpack 이 바인드 값과 같은 상수 트랙을 지워 **duration 이 0 인 클립(예 `Dead`)이 있으니 길이는 extras.frames 를 쓸 것**.
  - 사람 68클립: ASB 커맨드(WaitHold, WalkHold, WalkBackHold, Jump_St/Jump/Jump_Ed, JumpShoot_*, Shoot, WaitShoot, WaitShootNG, Walk*Shoot, ToSquid, ToHuman, ToHuman_WallJump, WallJump_Ar/Ed, ToHumanRespawn, Damage, WaitDamage, WalkDamage, Repelled, Dead, WaterDrown, Slip, SlipSlope, ToHumanStandby*, ToSquidStandby) 트리의 잎을 `Nrml→Shtr`, `@→Win01` 치환해 bfres 에 있는 것. 없는 것: `WalkBackHold_Shtr`(대체 규칙 [미확정]).
  - 오징어 22클립: SplPlayerSquid ASB 전체 커맨드의 잎.

### 2.4 maps/Lby_Lobby00/
**placement.json**
```
{ version:1, map, source, units,
  actors: [{ hash:"<u64 10진 문자열>", instanceId, name, gyml, className|null, pos:[x,y,z], rot:[rx,ry,rz] (rad), scale:[..],
             team, layers:[..], bakeable, params:{원본(spl__*, game__*)}, links:[{dst:"<해시>", name}] }],
  actorTypes: { <gyml>: { className, actorChain[], models[](fmdb 이름), gameParameterTable, phive?:{ shapes{이름:{file,...ShapeParam 원본}}, rigidBodies{이름:{file,...RigidBodyEntityParam 원본}} } } },
  rails: [ Banc Rails 원본(Hash→hash 문자열, Points[].hash) ], aiGroups: [ 원본 ] }
```
- 257 액터 전부. 사격장: SighterTarget 12, _Large 2, _Move 3, _TipsTrial 18, _TipsTrialMove 2, LobbyShootingArea 3 + _Cylinder 1, StartPos 10, StartPosTipsTrial 17, WoodenFigure 1, PaintedArea_Cube 8, PaintedArea_Cylinder 19, SpawnerForBeaconGimmick_TipsTrial 1, SpawnerForShieldGimmick_TipsTrial 2. 레일 3(LiftRail).
- 2^53 이상 정수(해시·링크)는 params 안에서도 10진 문자열.
- 회전 규약 R = Rz·Ry·Rx, 배치 행렬 = T·R·S [추정 — 레일 Rotation 판독 규약을 액터에도 적용(gimmick/stage_misc.md §1.5). 이 맵의 표적은 (π,0,π)·(0,±π/2,0) 같은 값이라 순서 영향 작음].

**collision.json + collision.bin**
```
bin = [positions f32 x,y,z … | indices u32 … | triMaterial u16 … | triSource u16 …]   (구간마다 4바이트 정렬)
json = { version:1, vertexCount, triangleCount,
  layout:{ positions:{offset,count,type:"f32x3"}, indices:{offset,count(=삼각형×3),type:"u32"}, triMaterial:{offset,count,type:"u16"}, triSource:{offset,count,type:"u16"} },
  materials:[{ name(Phive 재질), layer:"Ground|Water|KeepOut|KeepOutBullet|InkThrough|PlayerThrough|CameraThrough|Other", paintable,
               flags:{ userShapeTags[], layerHitMask, subLayerHitMask, filterRaw, bodyLayer, bodySubLayer, bodyMotionType } }],
  sources:[{ hash, gyml, body, shape }],
  primitives:[{ type:"capsule|sphere|cylinder", source, actorMatrix(열 우선 4x4 = T·Rz·Ry·Rx·S), material, shape:{원본 필드: CenterA/B|Center, Radius, OffsetTranslation, OffsetRotation(도)} }],
  bounds:{min,max}, source, notes[] }
```
- **월드 좌표로 구움**(배치 행렬 적용). 지형 Fld_VSLobby 는 원점·단위 배치라 원본 정점(1/512 격자) 그대로.
- 포함(정점 5489, 삼각형 6329, 재질 52): Fld_VSLobby 5480(bphsh), Obj_LobbyPod 441(bphsh), DObj_LobbyPlayerDevice 84(bphsh), Box 프리미티브 → 12삼각형(Obj_LobbyProjector ×19, DObj_Minigame ×5, 캡슐머신·음악선택기·로비 문). Box 꼭짓점 = OffsetTranslation + R(OffsetRotation°)·(Center ± HalfExtents(기본 0.5)) 후 배치 행렬 [추정 — 이 맵 데이터에서는 Center 가 y 만 있어 순서 영향 없음].
- `primitives`(삼각형 안 만듦): 캡슐머신의 Capsule·Sphere, 미니게임 의자 Capsule ×11.
- 제외: SighterTarget*·WoodenFigure(움직이는 표적 — `placement.actorTypes[gyml].phive` 의 캡슐 사용), NPC, `Obj_LobbyKeepOutPlayerInSpecial`(스페셜 중에만 막는 것으로 봄 [추정], placement 에 Box·Scale 있음), x=−1000 의 `Mpt_Fld_LockerEditBG`, 센서(CustomReceiver) 몸.
- `layer` = 삼각형 필터 LayerHitMaskEntity 분류(SplSolidGround/HitAll → Ground, SplKeepOutPlayer(AndCamera) → KeepOut, 미지 마스크 0x1fffff1e → Other). 몸 레이어는 모두 Ground(flags.bodyLayer).
- `paintable` [추정]: layer == Ground 이고 `ForceColPaintNotPaintable` 없음(`ForceColPaintPaintable` 이면 참). 재질별 칠 불가(paint_shape §7.2 의 재질 플래그 0x60)는 미확정. 참고: 표시 모델 재질 extras `userData.Paintable` 도 있음(§2.5).

**visual.glb** — Fld_VSLobby(+FldBG_LobbyDV) + 정적 배치 파츠(로비 문, 스크린, 포드, 플레이어 디바이스, 캡슐머신, 음악선택기, 미니게임 ×5, 의자 ×11, 프로젝터 ×19, 로커 문)를 배치 행렬 노드로 합침. gltfpack 이 한 번만 쓰인 정적 메시는 월드 좌표로 구워 합치고, 여러 번 쓰인 메시(프로젝터 등)는 `<모델>__model` 노드 + 행렬로 남김 — 어느 쪽이든 렌더 월드 위치 = 원본 배치(헤드리스 렌더로 충돌과 겹침 확인). 노드 155·메시 125·삼각형 146,127·KTX2 216장(같은 bfres 텍스처는 한 장으로 합침). NPC·표적·조명 액터 없음.

**parts/** (배치 안 함, range 가 placement 좌표에 놓음): `Obj_SighterTarget.glb`(모델 Obj_SighterTarget + 파편 Fragment00·Fragment01, 클립 Brust 1·DamageShot 30·DamageShotBend 360(loop)·Expand 45·Flick 24), `Obj_SighterTargetMove.glb`(같은 클립), `Obj_LobbyCopyrobot.glb`(WoodenFigure, 클립 PowerOn·PowerOff). 씬 루트 아래 모델 이름 노드. SighterTarget_Large 는 같은 모델 + 표의 `Scale`(1.3). `data/parts_anim_material.json` = 재질 애니(표적 `Damage` 100f, 로봇 `PowerOn/Off`, `Light_ON/OFF`).

**env.json**: `teamColorLight{defaultDay(DiffuseColor (1,1,1), Intensity 4, Direction), lobbyMainLight(RenderingDay MainLight 원본)}`, `rendering`(LobbyVersusLockerTest RenderingDay 원본: 안개·MainLight·EnvMap·SkySphere·PostEffect·Shadow), `fieldEnv`, `sceneEnv`(vslobby_day.baglenv AAMP → dict, 이름 모르는 키는 CRC 16진), `defaultEnv`(Env/Default day/defaultday.baglenv).

### 2.5 GLB 공통 규칙
- 변환: bfres → `asset_bfres2gltf.exe`(graphics_bfres2gltf 복사 + `--model`, `anim --only`) → 재질 extras 정리 → gltfpack.
- 노드·뼈: graphics/formats_bfres_bntx.md §6 규칙 그대로(노드 0 `<모델>__model`, 뼈 = 노드 이름·부모·바인드 TRS, EulerXYZ → 사원수, 스킨 1개, 리지드 메시는 뼈 자식, 메시 노드 `extras{shape, visBone, skinCount, material, lods, uv}`). 캐릭터·무기·파츠는 `-kn` 로 노드 유지.
- 정점: 위치·UV **실수 그대로**(`-vpf -vtf`, KHR_mesh_quantization 의 노드 역양자화 스케일 없음), 노멀·탄젠트 8비트 정규화, meshopt 압축(EXT_meshopt_compression).
- `texcoord_select_<슬롯> = N` 이면 그 glTF 텍스처의 `texCoord = N`(오징어 몸 노멀 = TEXCOORD_2) — shaders.md §3.7. `tex_mtx*` 는 params 에만.
- 재질 `extras.hoian` = `{ shader, options(기본값 아닌 것), samplers{슬롯:텍스처 이름}, attribAssign, renderInfo(gsys_render_state_*/alpha/blend/depth/my_team_color_*/paint_*/spl_model_type 등), params(albedo_color, emission_*, roughness, metalness, opacity, team_color_*, two_color_*, tex_mtx*, const_color*, …), userData(Paintable 등), teamColor{maskTcl, map2cl, team_color_map_type, my_team_color_type, …}, gltfUsed }`. 원래 extras.fres(재질당 ~20KB, 파라미터 248개)는 뺐다.
- 텍스처: glb 안 KTX2(KHR_texture_basisu). 색 = ETC1S(sRGB), 노멀 = UASTC(선형), 거칠기·금속·AO 합성 = ETC1S(선형). glTF 슬롯에 없는 텍스처(Tcl·2cl·패턴·알파마스크)는 번들 `tex/**.ktx2` 단독 파일.

### 2.6 effects/shooter/emitters.json
```
{ version, group, source, units, enums, notes[],
  splashKind:{T0:0.5235988, T1:1.0471976, wallNormalY:0.64144969, rule},
  oneEmitterSlots:{이미터셋:{n,count}}, weaponTriggers:[{actions:["FireImpact","FireOn"], eset:"WpShtrMzfNml", bone:"Muzzle", delay:{curve…}, matrix}],
  emitterSets:{ <이미터셋>:[{ name, depth, parent, attrs,
      calc:"CPU|GPU_TIME|GPU_SO", follow:"ALL|NONE|POS", life, lifeRandom, infiniteLife,
      emission{…}, velocity{…}, gravity{dir,scale,world}, airRegist, momentumRandom,
      scale{base, randomPct, keys:[[x,y,z,t]…], numKeys}, rotate{…}, billboard, rotType,
      color{scale, color0/alpha0/color1/alpha1:{type:"FIXED|RANDOM|ANIM", keys}, loopRate, loopRandom},
      fade{…}, emitterTransform{…}, volume{…}, pivotOffset, drawPath, shaderIndex, randomSeedType, randomSeed,
      textures:[{slot, offset, name}], primitive:{id,index,model,file}|null, fields:{판독 필드 전체(키 배열 제외)} }] },
  textures:{ <이름>:{file, kind:"mask|normal|vat", width, height, …} }, missingEmitterSets:[] }
```
- 이미터셋 17: WpShtrBullet1Emit, WpShtrMzfNml, WpCmnBulletSplash1Emit, CmnFloorSplash/Near/Dist1Emit, CmnNPFloorSplash/Near/Dist1Emit, CmnWallSplash1Emit, CmnNpWallSplash1Emit, WpCmnHit, WpCmnHitEffective, WpCmnHitCritical, WpCmnHitInvalid, WpCmnWaterSplash, WpShtrHitMarker. 행 = effect_resources.md §2.2.6 웹 재현값 표의 열 + 키.
- `tex/*.ktx2` 28장(마스크 ETC1S 선형, `_nrm` UASTC 선형; BC4 → R, BC5 → RG). `tex/bulletshtr_vsp.bin`, `bulletcmn_vsp.bin` = VAT R16G16B16A16 FLOAT 원값(half LE, 행 = 정점, 열 = 시간).
- `prim/*.glb` 10개 = VFXB G3PR 프리미티브(BulletShtr, BulletCmn, Circle00, Crown01pro, Crown03Pro, HitMark, RingPlane00, Ripple01, Ripple03, YbillboardPlane00). 정점색 `_c0` → COLOR_0, 재질 없음.

### 2.7 sfx/<group>/sfx.json
```
{ version, group, notes[], lobbyMaterials[],
  users:{ <SLink 사용자>:{ localProperties, userParams, roots:{키:호출표 번호}, callTables:[원래 번호 그대로, 안 쓰는 칸 null, 가지치기 칸 {i,key,parent,condition,pruned:true}],
                           actionSlots, actions, actionTriggers(쓰는 것만, _i=원 번호), properties, propertyTriggers, prunedBranches } },
  assets:{ <RuntimeAssetName>:{ file, bars, sampleRate, channels, samples, duration, loop:{start,end,startSample,endSample}|null, prefetch, opusPreSkip, opusDuration, decodedPeak, amtaPeak, bytes } },
  attenuation:{ <DistanceParamSetName>:{ refs(AATN), curves{이름:{kind:"ROC|UDC|ADR|ACL", …}} } },
  events:{ <DESIGN 이벤트>:[{user,key}] } }
```
- callTables 의 `container.children = [첫, 끝]`(포함 범위), `condition`, `params`(RuntimeAssetName, Volume/Pitch `{Random:[a,b]}`·`{Random2Pow:[a,b]}`·`{curve:{prop,points}}`, Delay(프레임 [추정]), DistanceParamSetName, DistCoef, GroupName …) 는 effect_xlink.py 출력 원본. 평가 규칙 effect_sound/xlink_format.md.
- shooter: WeaponShooterNormal 전체(Fire 3종, OnAttach, OnDetatch). player: Player_Focused 32키(특수·코옵·데모·미션 제외), PlayerFoot 11키(발소리·점프·착지·SlipSlope), PlayerTank. common: HitEffect 11키(ヒット, ヒット_短減衰, 3連ヒット, クリティカルヒット, ノーダメージ, 飛沫, インクヒット(_多量), インク被弾, 水没(_大)), SighterTarget 전체, WoodenFigure.
- PlayerFoot 의 `GndMaterial == X` 분기 중 로비 충돌에 없는 재질 66개를 pruned(소리 생략).
- events(이름 기반 [추정]): Fire→WeaponShooterNormal/Fire, BulletHit→HitEffect/インクヒット, Damage→HitEffect/ヒット·SighterTarget/ダメージ, Jump→PlayerFoot/ジャンプ·Player_Focused/インクからジャンプする, Land→PlayerFoot/着地·InkLand, ToSquid→イカに変身·ヒト状態からインクに潜る, ToHuman→ヒトに変身, Swim→インクの中を泳ぐ·イカで泳ぐ単発音.

## 3. 변환 규칙·도구

| 단계 | 도구 | 비고 |
|---|---|---|
| 데이터 | `tools/asset_data.py` | 파라미터 표·RSDB·싱글턴·조합표·스탬프 |
| 맵 | `tools/asset_map.py` | Banc → placement, bphsh/ShapeParam → collision, env, visual(합치기), parts |
| 캐릭터·무기 | `tools/asset_char.py` | ASB → 클립 선택, 패턴·팀색 텍스처, gear |
| 이펙트 | `tools/asset_fx.py` | esetb → VFXB(effect_esetb.py), 필드(vfx_emitter46.FIELDS), BNTX, G3PR |
| 효과음 | `tools/asset_sfx.py` | SLink(effect_xlink.py), BARS/BWAV(sound_bars.py) → **자체 DSP-ADPCM 디코드** → ffmpeg libopus(모노 64 kbps, 스테레오 96 kbps VBR) |
| 공용 | `tools/asset_common.py`, `asset_model.py`(glb 입출력·합치기·gltfpack), `asset_ktx2.py`(PNG→KTX2 단독: 운반용 glTF 를 gltfpack -tc 로 인코딩해 이미지 바이트를 꺼냄) |
| 변환기 | `tools/asset_bfres2gltf/`(C#, graphics_bfres2gltf 복사 + `gltf --model <이름>`, `anim <bfres> <out> --only a,b`) → 빌드 산출 `analysis/assets_work/build/` | BfresLibrary 는 `graphics_bfres2gltf/oss` 참조(수정 없음) |
| 카탈로그 | `tools/asset_catalog.py` | |
| 검증 | `tools/asset_verify.mjs`, `tools/asset_view/{view.html,shot.mjs}` | §6 |

외부 도구(출처·버전):
- **gltfpack 1.3** — meshoptimizer v1.3 공식 배포 `gltfpack-windows.zip`(https://github.com/zeux/meshoptimizer/releases/tag/v1.3), `web/tools/bin/gltfpack.exe`(gitignore). BasisU 인코더 내장(KTX2 ETC1S/UASTC). `asset_build.py` 가 없으면 받음.
- **ffmpeg 6.1.1**(gyan.dev essentials, libopus) — npm devDependency `ffmpeg-static@^5.3.0`(`web/package.json` devDependencies 에만 추가).
- KTX2 트랜스코더 = 기존 `assets/common/lib/basis`(three vendor).
- vgmstream 은 쓰지 않음(자체 디코더).

## 4. 원본과 다른 점
- **텍스처 손실 압축**: BC1/4/5 → PNG → BasisU(ETC1S q8 / UASTC). 해상도는 원본 그대로(축소 없음). 0x15 FLOAT VAT 는 무손실(half 그대로).
- **셰이더 근사 정보만**: Hoian_UBER 를 glTF PBR 로 근사(formats_bfres_bntx.md §5.2). 베이크 라이트맵(`_b0/_b1` = Bake/Scene/LobbyVersus_Day.bkres)·환경맵·SkySphere(`Sky_Daytime00`)는 넣지 않음 — 로비가 원본보다 평평하게 보임.
- **정점 속성**: 사용자 속성 `_c0`(정점색)·`_pu*` 를 gltfpack 이 버림(맵·캐릭터. 이펙트 프리미티브는 `_c0` → COLOR_0 로 살림). 노멀 8비트 양자화.
- 셰이프 LOD 0 만, 세그먼트 스케일 보정(Maya) 미표현(formats §7).
- 클립: 정수 프레임 베이크(원본 커브 아님), 회전 12비트 양자화, 바인드와 같은 상수 트랙 제거.
- 맵 visual 은 gltfpack 이 메시를 합쳐 파츠별 노드 이름이 대부분 없어짐. 움직이는 표적·로봇은 parts 로 분리.
- 효과음: Opus 재인코딩(손실), 44.1/32 kHz 원본도 48 kHz 로 재샘플. 앞 패딩은 `opusPreSkip`(312)로 기록.
- 사격장 밖 재질의 발소리 분기 제거(pruned).

## 5. 미확정
| 항목 | 상태·필요한 것 |
|---|---|
| 기본 장비 | v0 데이터에 초기 장비 표시가 없다. `FST`(first) 접두는 머리 `Hed_FST000` 만 모델·RSDB 행이 있고 옷 `Clt_FST001` 은 UI 아이콘만, 신발 FST 없음 → 슬롯별 최소 Id 행(Hed_FST000 Id1, Clt_TES001 Id1001, Shs_SLO000 Id1000), 커스텀 Id 0(Har_SQD000, Eyb_SQD000, Btm_000), 탱크 Tnk_000 [추정]. 세이브 초기값 코드(0x… 미탐색)를 보면 풀림 |
| 액터 Rotate 순서 | Rz·Ry·Rx [추정](레일 판독 규약). 액터 행렬 생성 함수 판독 필요 |
| Box OffsetRotation/Center 합성 순서 | [추정], 이 맵에는 영향 없음 |
| paintable | 재질 기준 [추정]. ColPaintBuilder·재질 플래그 0x60 대응 |
| 조명 | MainLight→DirectionalLight 대응 [추정](team_color.md §5.3) |
| VFX 프리미티브 매핑 | G3NT i ↔ BFRES 모델 i [추정: 개수 185 일치, ball→BulletShtr 등 이름도 맞음] |
| 클립 대체 | `WalkBackHold_Shtr` 없음 — ASB 치환 결과가 없을 때 규칙 [미확정] |
| 패턴 텍스처 | `Color_Eye` 21프레임 째 `M_Eye_Alb.21` 이 Player00 에 없음(Player01 등 다른 파일 [추정]) |
| 44.1 kHz 효과음의 AMTA 피크 | 디코드 피크와 ≤ 수 % 차(48 kHz 는 전부 일치) — AMTA 가 48 kHz 재샘플 뒤 측정 [추정] |
| 매치 시드(weapon 요청 `data/match_seed.json`) | 정적 데이터 없음(로비→설정 런타임 값, network 문서) — 만들지 않음 |
| 머리카락 천 물리·hair 클립 | Har 의 클립 35개·bphcl 은 넣지 않음 |

## 6. 검증 (`node web/tools/asset_verify.mjs` → `analysis/assets_work/verify.json`)
- GLB 27개 전부 three r180 GLTFLoader(node, MeshoptDecoder, KTX2 자리표시)로 파싱 성공. 몸 메시 16·뼈 87·삼각형 7,642(formats §6.1 기록과 같음), _Hlf 3·79, 오징어 2·23·3,010, 무기 2·2,230, 탱크 24·9,010, 클립 사람 68·오징어 22·표적 5·로봇 2, `animation.extras.frames` 보존.
- 내장 KTX2(맵 216 등)·단독 KTX2 84개 전부 basis 트랜스코더(assets/common/lib/basis, node)로 RGBA 디코드 성공. 전부 검은 텍스처는 원래 검정/알베도 끔 합성(`none__*_Opa.ba`, RampRubber_Alb).
- Opus 301개: Ogg granule − pre-skip 길이와 원본 샘플 길이 차 최대 0.000021 s, ffmpeg 디코드 길이 차 최대 0.000021 s. DSP-ADPCM 디코드 피크가 AMTA 피크와 48 kHz 항목 전부 일치(슈터 발사음 3종 = sound_resources.md §3 표 값).
- collision: 지형 Fld_VSLobby 5,480 삼각형(collision_scan 기록 `scan_all.json` 과 같음), Pod 441·PlayerDevice 84(같음). 지형 삼각형의 재질별 분포가 `collision_mesh.py` 통계(38 shapeTag)와 키 전부 일치(diffKeys 0). 인덱스 범위·유한값 확인.
- 헤드리스 렌더(`node web/tools/asset_view/shot.mjs`, Chromium swiftshader): visual.glb 실제 KTX2Loader 디코드, 충돌 와이어가 표시 모델과 겹침, 표적 14개가 배치 좌표에 섬 → `analysis/assets_work/shots/view_range.png`.

## 7. 재생성
```sh
cd c:/dev/splatoon3
.venv/Scripts/python web/tools/asset_build.py            # 전부(data map char fx sfx catalog verify) + 중간 산출물 정리, 약 2분
.venv/Scripts/python web/tools/asset_build.py map catalog # 일부 단계만 (data map char fx sfx catalog verify)
.venv/Scripts/python web/tools/asset_build.py --keep      # analysis/assets_work 중간 산출물(png, raw bfres, static.vfxb 120MB, wav) 유지
node web/tools/asset_view/shot.mjs view=range view=top    # 눈으로 확인
```
순서 의존: sfx 는 map 의 collision.json(재질 목록)을 읽음. 필요: `.venv`, dotnet 7 SDK, node 24 + `npm install`(three, ffmpeg-static), 인터넷(최초 gltfpack 받기).

## 8. 번들별 크기 (catalog bytes, 2026-10-02)
| 번들 | 파일 | 바이트 | 큰 것 |
|---|---|---|---|
| common | 9 | 346,383 | ink_stamps 105K, damage_rate_info 52K, param_defaults 48K, hit_effect 45K, phive_config 45K (+ lib/basis 576K 별도) |
| map/Lby_Lobby00 | 13 | 9,590,174 | **visual.glb 8.23M**, Obj_SighterTarget 469K, Obj_SighterTargetMove 452K, collision.bin 167K, placement 147K |
| character/Player00 | 76 | 5,315,833 | anim/human 2.22M, Tnk_Simple 564K, body 368K, Clt 257K, Shs 251K, body_hlf 250K, anim/squid 248K |
| weapon/Shooter_Normal_00 | 8 | 313,493 | model.glb 299K |
| effect/shooter | 41 | 438,498 | emitters.json 174K |
| sfx/shooter | 6 | 22,112 | |
| sfx/player | 202 | 1,191,741 | 발소리 다수 |
| sfx/common | 96 | 485,329 | |
| 합계 | | 17,703,563 | 연습장 판 시작 시 전부 받음 |

## 9. 조정 요청
- 없음(형식은 기존 `client/assets.ts`·`app.ts matchData` 규칙에 맞춤). 참고: `sfx/player` 202개·`sfx/common` 96개 .ogg 를 판 시작 때 전부 fetch·decode 한다(요청 수가 많음). 나중에 지연 로딩이 필요하면 assets.ts 에 확장자별 지연 규칙을 두는 것을 제안.
