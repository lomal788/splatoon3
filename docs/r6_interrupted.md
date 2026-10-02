# 6차 중단 담당 기록 (2026-10-03)

사용량 한도로 7개 담당을 작업 중에 멈췄다. 결과 json(`analysis/completion/r6/<키>.json`)이 없어 추적표 확정률에는 들어가지 않았다. 아래는 각 담당이 공유판(`analysis/notes/SHARED.md`)에 남긴 `[r6 <키>]` 줄 전부와, 6차 동안 바뀐 문서·도구 목록이다. 담당들은 결과를 본문에 바로 쓰던 중이었으므로 **아래 문서의 끝 절(§8~§11 검증·미확정 표)은 덜 갱신됐을 수 있다**. 재개할 때 먼저 확인한다.

재개: `analysis/completion/r6/BRIEF.md`로 같은 키의 담당을 다시 시작하고(이미 쓴 본문·SHARED 줄을 이어받게 함), 끝나면 `analysis/completion/r5_merge.py` → `web/tools/analysis_completion.py render`.

## 피격·판정 (`combat`)

- 새 도구: `web/tools/r6_combat_filter_emu.py`, `web/tools/r6_combat_hiteffect_emu.py`, `web/tools/r6_combat_sender_modes.py`, `web/tools/r6_combat_vcallscan.py`
- 공유판 기록:
  - [r6 combat] 진행: 탄 바디 F+0x30·아군 충돌(0x7103b09ee4/0x7103a62e78/0x71010036a8, 내부바디+0x138 vs 강체+0x180), 조준 표시 슬롯33 호출 조건·예측 단계 수, 송신자 이력 모드(0x7101e3d69c), 크리티컬 HitEffectConfig 행(0x71028fed18), 형태별 피격 형상(PlayerCollision 슬롯13/48/73·비트11), 시간 창 카운터·R+0x208 writer, 생성 겹침 첫 명중 age — web/docs/combat/*.md, web/tools/r6_combat_*.py — 2026-10-03
  - [r6 range] 조율: 송신자 이력 모드 0x7101e3d69c 는 [r6 combat] 결과를 받아 표적 행만 갱신(직접 분석 안 함). 로케이터 Banc Rotate→생성 정보 3×3 은 [r6 assets] 결과를 우선 사용(range 는 0x7100f827c4 복사·판정 쪽만). PaintedArea 칠 요청 형식은 [r6 paint], range 는 AINB 활성화(Logic_Activate) 경로만 봄 — 2026-10-03

## 도색 (`paint`)

- 새 도구: `web/tools/r6_paint_footmon_emu.py`, `web/tools/r6_paint_img.py`, `web/tools/r6_paint_pattern_emu.py`, `web/tools/r6_paint_texfmt_emu.py`, `web/tools/r6_paint_uc.py`
- 공유판 기록:
  - [r6 paint] 진행: 발밑 잉크 샘플 사슬(0x7102c3d954, vt 0x7105680730, S+0xe8 writer), ColPaint 패턴 인식·연결(0x7102bfb8b8/0x7102bf03d0/0x7102bf22a8/0x7102c01420), 텍스처 비트 폭(메모리 크기 역산), 0x7102c50d18 프레임 위치, 관리자+0x30a 높이 하한, 모드 3 COPY 스텐실 조건, PaintedArea·아틀라스 씬·강체 +0x230 — web/docs/paint/, analysis/decomp/r6_paint/, web/tools/r6_paint_*.py — 2026-10-03
  - [r6 range] 조율: 송신자 이력 모드 0x7101e3d69c 는 [r6 combat] 결과를 받아 표적 행만 갱신(직접 분석 안 함). 로케이터 Banc Rotate→생성 정보 3×3 은 [r6 assets] 결과를 우선 사용(range 는 0x7100f827c4 복사·판정 쪽만). PaintedArea 칠 요청 형식은 [r6 paint], range 는 AINB 활성화(Logic_Activate) 경로만 봄 — 2026-10-03
  - [r6 assets] 완료: 18행(확정 3·미확정 10·범위 밖 5) → analysis/completion/r6/assets.json. 미확정 남김: S 합성 위치(컴포넌트 vt+0x50), Box 합성 순서(Box 빌더 미발견, AutoCalc 판별 불가 web/tools/r6_assets_box_autocalc.py), paintable 대상 목록([r6 paint]), Delay 단위·AMTA 소비(fx), 이벤트 키 일부, 매치 시드(camweapon)

## 물리·충돌 (`physics`)

- 새 도구: `web/tools/r6_physics_contactsort_emu.py`, `web/tools/r6_physics_functorscan.py`, `web/tools/r6_physics_gravity_emu.py`, `web/tools/r6_physics_shapefilter_emu.py`, `web/tools/r6_physics_sublayer_emu.py`, `web/tools/r6_physics_vcallscan.py`, `web/tools/r6_physics_writeback_emu.py`
- 공유판 기록:
  - [r6 physics] 진행: 평상시 Phive→본체+0x10 write-back(0x7100f76f78/슬롯19 동적 추적), TOI 처리기 4종(0x7103c52d30 등)·접촉 정렬 0x7103a6144c, shapeTag 필터 배열 writer(0x7103a221cc 이후)·형상 행 결합(0x7103c34b7c→0x7103b02470), hknp 솔버 사용 여부(0x7103c48298), 중력 [월드+0xb8]+0x2a4·dt 변경 경로, 관통력 +0x18c·오징어 하위 레이어·Free vt+0x30·Result+0x1358 (2026-10-03)

## 그래픽(스테이지) (`gfx_stage`)

- 새 도구: `web/tools/r6_gfx_stage_addimm.py`, `web/tools/r6_gfx_stage_adrpscan.py`, `web/tools/r6_gfx_stage_cfgparams.py`, `web/tools/r6_gfx_stage_envubo_layout.py`, `web/tools/r6_gfx_stage_inkcorr_emu.py`, `web/tools/r6_gfx_stage_offscan.py`, `web/tools/r6_gfx_stage_vtof.py`
- 공유판 기록:
  - [r6 gfx_stage] 진행: 하늘 SH 값(skyUp) CPU 재계산·대체 경로 판정, Env UBO 512 B 칸 대응(뷰 레코드 순회), 감마·블룸 합성·LUT 변형 로비 값, 사격장 그림자 방식, BlitzUBO2 writer·[22].zw·RadialFog, 적용 함수 0x7102b66c54/0x7102b68ef4/0x7102b60200 — web/docs/graphics/{stage_rendering,shaders,team_color,formats_bfres_bntx}.md, web/tools/r6_gfx_stage_*.py, analysis/r6_gfx_stage/ — 2026-10-03
  - [r6 gfx_stage] Env UBO(gsys_environment 512 B) 칸 대응 해소: 기록자 0x71036b35c0(뷰마다)+안개 0x71036b1300, 레이아웃 0x71036ae130 선언 구간 원본 실행 35멤버/0x200 B. [0]Ambient [1][2]Hemi 색 [3]Hemi 방향 [4].xyz 주광 방향(+0x1f8) [4].w Intensity [5]=I·Diffuse [6]=I·(+0x150) [7..9] 둘째 방향광 [10..21] agl Fog 4개(색, normalize(dir), −S/(E−S), 1/(E−S), Damp) [22] Hemi +0x198 [23] 주광 방향(+0x208) [24] 둘째 [25..31] 뷰 레코드 +0x98 SH 0x70 B — stage_rendering.md §5.5.1, web/tools/r6_gfx_stage_envubo_layout.py — [실행]+[판독]
  - [r6 gfx_stage] 로비 환경광 "Main" = 기본 장면 gfx(0x710121b210, 슬롯39 0x710121dbc0 → env 객체 슬롯20 0x71010bf36c) → +0x5c8=0 캡처 경로. 플래그1 "Main"(0x7102b97874)은 Scene_DevEnvViewer(0x7102b97f90) 전용. SH = 실행 중 BaseCubeMap(256² RGBA16F, 0x710102ce04) 두 번째 캡처 투영값 → romfs 큐브 없음, 값 [미확정](큐브 캡처 렌더 재현 필요) — stage_rendering.md §5.6.1 — [판독]
  - [r6 gfx_stage] 팀색 Ink/InkBright 는 로비 조명(I 10, L*(Diffuse) 92.73 → t≥9.27)에서 r=Rate6 포화로 skyUp 무관: 0x7101174afc 원본 실행(SDK powf/fmodf 연결) 500색×skyUp5종 비트 동일, 대조군 485/500 변화 — team_color.md §5.3, web/tools/r6_gfx_stage_inkcorr_emu.py — [실행]
  - [r6 gfx_stage] gsys 장면 설정(장면+0x1c0) 생성자 0x7103705fec 실행+crc32b 사슬 추적으로 이름 ~175개 복원(analysis/r6_gfx_stage/gsys_cfg_params.tsv): +0xf00 linear_lighting_enable, +0x850/+0x890/+0x8b0/+0x8d0 bloom/auto_exposure/hdr/color_correction, 동적 그림자 depth_shadow_tex_width/height 1024, polygon_offset 0.3/scale 5.0(0x71036c971c 가 렌더 상태로 복사), pcf_offset 0.5(0x7103751a78: 0.5/폭), 정정: 2048/Depth_32/R32_G32_float = static_sdw_* — stage_rendering.md §3.0 — [실행]+[데이터]
  - [r6 gfx_stage] HDRCompose 로비: 블룸+0x438 = agl bloom 파라미터 finalblend(묶음 = 블룸+0x30, 0x71036eb47c), Default env 값 1 → BLOOM 1(가산). CC: +0x2410 bit4 는 생성 시 0x71035db354 가 켜고 끄는 곳 없음 → CC 1. GAMMA: linear_lighting_enable true → 장면+0x523c bit4 꺼짐이면 1(1/2.2), bit4 기록자 미발견 — stage_rendering.md §3.2 — [판독]+[데이터]
  - [r6 gfx_stage] RadialFog(방문 0x71011d4ddc, 생성자 0x71011d4d04): BlendFactor +0x30 0, Color +0x34 (1,0.95,0.7,1), Intens +0x44 1, LobeCtrl +0x48 1, ShadowInfluence +0x4c 0, SizeCtrl +0x50 5. BlitzUBO0 [53].w=BlendFactor, [54]=(LobeCtrl,SizeCtrl,1/exp2(2·SizeCtrl),ShadowInfluence). [22].z = 1/(8·S) (0x7102be8aec, S 200/400) — stage_rendering.md §4·§7 — [판독]
  - [r6 gfx_stage→impl/render] 웹 반영 필요: ① Env UBO 블록을 stage_rendering §5.5.1 표대로(주광 [5]/[23], 안개 [10..15] 원본 식), ② 블룸 가산 + 색 보정 켬, ③ 동적 그림자 캐스케이드 2·1024²·polygon offset 0.3/scale 5.0·PCF 0.5 텍셀(현재 1024² 하나 ±6 유닛 근사), ④ 팀색 skyUp=0 이어도 로비 Ink/InkBright 원본과 같음, ⑤ RadialFog 산란 항 생략 = 원본(로비)

## 그래픽(캐릭터) (`gfx_char`)

- 새 도구: `web/tools/r6_gfx_char_cfgpath.py`, `web/tools/r6_gfx_char_hairarrange_emu.py`, `web/tools/r6_gfx_char_lodscan.py`, `web/tools/r6_gfx_char_opscan.py`, `web/tools/r6_gfx_char_teamcolor_emu.py`
- 공유판 기록:
  - [r6 gfx_char] 진행: 몸 잉크 색(0x7101178030 로비 호출자)·오징어 몸 변형(모델 바인드·애니 경로)·HairArrange 소비자(동적 추적)·GearAlphaMask 재질 슬롯(0x710103f434)·LOD +0x38 reader(vtable 스캔)·_Hlf 시작 프레임·JumpVarID·천 dt·기본 장비·PlayerTank 표시식/점멸 — web/docs/graphics/{model_character,player_assembly,anim_state_machine,hair_cloth,solo_graphics_audit}.md, web/tools/r6_gfx_char_*.py — 2026-10-03 시작

## 이펙트·효과음 (`fx`)

- 새 도구: `web/tools/r6_fx_distcoef_emu.py`, `web/tools/r6_fx_memscan.py`, `web/tools/r6_fx_storescan.py`, `web/tools/r6_fx_voiceserial_emu.py`
- 공유판 기록:
  - [r6 fx] 진행: DistCoef→확장+4(SLink 실행부 unicorn 메모리 훅)·리스너 주시점 공급자(vt+0x38 호출자)·필터 컷오프/패닝/FarFx·보이스 +8 writer·AATN 로더·이미터 형상 2~15·Splash1Emit 필드 — web/docs/effect_sound/, web/tools/r6_fx_*.py — 2026-10-03
  - [r6 fx] DistCoef 확정: SLink 에셋 시작 0x7103885e44 → 전역 xlink+0x1278 게임 훅(vt 0x71056b45a8) 슬롯5 0x710313d4ec 가 custom 파라미터(시작=PDT+0x34=20) 읽음: 확장+4 = 1/DistCoef(0x710313d6e0), +1 = UseFriendCoef(사용자+0xb8 값 v==1), +0x28 UseOcclusion, 보이스+0x200 = 확장 → 0x710312d398 → 감쇠 +0x50. 원본 실행 web/tools/r6_fx_distcoef_emu.py 실제 slink2 파일 219,680건 비트 일치(뮤텍스만 스텁) — sound_resources.md §4.2.7 — [실행]+[판독]
  - [r6 fx] AATN 세트 칸 확정: 로더 0x7103860218 이름칸 k → 세트+0x58+8k: +0x58 volume, +0x60 farFx(출력 +0x08), +0x68 filter(+0x10), +0x70 칸3, +0x78 AUDC(+0x18), +0x80 AADR, +0x88 AACL — sound_resources §4.2.4 정정 — [판독]+[데이터]
  - [r6 fx] Alto 보이스 +8 = 시작 순번: 풀 할당 0x71037d790c(보이스+8 = 풀+0x20, 다음은 +1, 0xFFFFFFFF→1). 제한기 종류1 동률 = 먼저 시작한 쪽 생존. 원본 실행 r6_fx_voiceserial_emu.py 2,445회 일치 — sound_resources §4.3.2 — [실행]
  - [r6 fx] 보이스 필터: SetVoiceBiquadFilterParameter ← 0x71037fa0b8(amount 0..1) ← 0x710383e3e8/e64c/e8c0(ch0 = 보이스+0x14c(=SLink Lpf 가산)+감쇠, 종류 +0x144 기본1; ch1 +0x150, 종류 +0x148 기본3). 필터 객체: 내장(종류6→슬롯0x3F) 1차 저역 −40·a dB@8kHz, 게임 PeakingFilter(User0 3150Hz −21·a dB Q5)·HiShelvingFilter(User1 19500Hz −80·a dB Q0.5). SLink 보이스 필터 종류 writer 미확정 — sound_resources §4.6 — [판독]+[데이터]
  - [r6 fx] 정정: effect_resources §2.2.6 슈터 탄 ball 알파는 FIXED 패치 적용 시 alpha0 1.0, alpha1 5.0(파일 키0 1.5/8 아님). 분열 탄 WpCmnBulletSplash1Emit/ball_Copy1 필드 추가(크기 (1,1,1)±30, alpha0 1.0, alpha1 3.0, VAT bulletcmn_vsp, 프로그램 1385) — [데이터]+[판독]
  - [r6 fx→impl/fx] 웹 반영 필요: 거리 d = dist/단위 × 지향성배율 × (1/DistCoef) × (Friend && UseFriendCoef ? 1.5 : 1)(현재 /DistCoef 유지 가능), Volume2·Pitch2 곱, SoundSourceSize, Lpf는 Hz 아님(필터 amount 가산 — BiquadFilter lowpass 매핑은 근사 표기), 탄 ball 알파 1.0/5.0 정정, 분열 탄 이펙트 값(effect_resources §2.2.6)

## 이동 (`player`)

- 새 도구: `web/tools/r6_player_dynq.py`, `web/tools/r6_player_dyntrace.py`, `web/tools/r6_player_pltaddr.py`, `web/tools/r6_player_regoffscan.py`, `web/tools/r6_player_uc.py`, `web/tools/r6_player_walljump_emu.py`, `web/tools/r6_player_world.py`
- 공유판 기록:
  - [r6 player] 진행: 메인 플레이어 갱신 동적 추적 하네스(상태 big·입력 함수 unicorn 실행, 본체 필드 쓰기 PC 기록) — +0x78c/+0x790/+0x745/+0x780 writer, 덮어쓰기 스틱 +0x80c..814, +0x4d8/+0xfa5/+0xa5c/+0x18c, 측면 접촉 공중 적용, 걷기 재생 속도식·0x710244a260, 패드 비트 이름(nn::hid 변환), 사격 구역 입력 종류 1~3·전역 0x71058e87ac, 잉크액션 vt40 호출자 — web/docs/player/*.md, web/tools/r6_player_*.py, analysis/decomp/r6_player/ — 2026-10-03

## 6차 동안 바뀐 문서 (최근 6시간 수정)

- [01_package_and_assets.md](01_package_and_assets.md)
- [README.md](README.md)
- [analysis_completion.md](analysis_completion.md)
- [camera/aim_swerve.md](camera/aim_swerve.md)
- [camera/camera_feel.md](camera/camera_feel.md)
- [camera/player_camera.md](camera/player_camera.md)
- [camera/shake_rumble.md](camera/shake_rumble.md)
- [camera/solo_completion.md](camera/solo_completion.md)
- [combat/damage_hit.md](combat/damage_hit.md)
- [combat/hitbox.md](combat/hitbox.md)
- [combat/player_life.md](combat/player_life.md)
- [completion_run.md](completion_run.md)
- [completion_summary.md](completion_summary.md)
- [effect_sound/effect_resources.md](effect_sound/effect_resources.md)
- [effect_sound/effect_sound.md](effect_sound/effect_sound.md)
- [effect_sound/solo_fx_audit.md](effect_sound/solo_fx_audit.md)
- [effect_sound/sound_resources.md](effect_sound/sound_resources.md)
- [effect_sound/xlink_format.md](effect_sound/xlink_format.md)
- [gimmick/collision_mesh.md](gimmick/collision_mesh.md)
- [gimmick/inkrail.md](gimmick/inkrail.md)
- [gimmick/sponge.md](gimmick/sponge.md)
- [gimmick/stage_gimmicks.md](gimmick/stage_gimmicks.md)
- [gimmick/stage_misc.md](gimmick/stage_misc.md)
- [graphics/anim_state_machine.md](graphics/anim_state_machine.md)
- [graphics/formats_bfres_bntx.md](graphics/formats_bfres_bntx.md)
- [graphics/hair_cloth.md](graphics/hair_cloth.md)
- [graphics/model_character.md](graphics/model_character.md)
- [graphics/player_assembly.md](graphics/player_assembly.md)
- [graphics/shaders.md](graphics/shaders.md)
- [graphics/solo_graphics_audit.md](graphics/solo_graphics_audit.md)
- [graphics/stage_rendering.md](graphics/stage_rendering.md)
- [graphics/team_color.md](graphics/team_color.md)
- [impl/assets.md](impl/assets.md)
- [impl/camera.md](impl/camera.md)
- [impl/fx.md](impl/fx.md)
- [impl/paint.md](impl/paint.md)
- [impl/physics.md](impl/physics.md)
- [impl/range.md](impl/range.md)
- [impl/render.md](impl/render.md)
- [impl/weapon.md](impl/weapon.md)
- [network/01_layers_and_session.md](network/01_layers_and_session.md)
- [network/02_replica_model.md](network/02_replica_model.md)
- [network/04_player_state.md](network/04_player_state.md)
- [network/05_events_combat.md](network/05_events_combat.md)
- [network/06_web_port.md](network/06_web_port.md)
- [network/network.md](network/network.md)
- [paint/colpaint_atlas.md](paint/colpaint_atlas.md)
- [paint/paint_and_score.md](paint/paint_and_score.md)
- [paint/paint_shape.md](paint/paint_shape.md)
- [paint/special_gauge.md](paint/special_gauge.md)
- [paint/turf_result.md](paint/turf_result.md)
- [physics/character_controller.md](physics/character_controller.md)
- [physics/collision_runtime_completion.md](physics/collision_runtime_completion.md)
- [physics/phive_controller.md](physics/phive_controller.md)
- [player/gear_skills.md](player/gear_skills.md)
- [player/movement_physics.md](player/movement_physics.md)
- [player/player_state.md](player/player_state.md)
- [player/solo_completion.md](player/solo_completion.md)
- [range/shooting_range.md](range/shooting_range.md)
- [tools.md](tools.md)
- [ui/ui_hud.md](ui/ui_hud.md)
- [ui/ui_layout_format.md](ui/ui_layout_format.md)
- [ui/ui_minimap.md](ui/ui_minimap.md)
- [ui/ui_vs_maintv_elements.md](ui/ui_vs_maintv_elements.md)
- [weapon/shooter_bullet.md](weapon/shooter_bullet.md)
- [weapon/solo_shooter.md](weapon/solo_shooter.md)
