# 캐릭터 조명·자기 잉크 잠영 r8 실제 반영 — 2026-10-03

몸·얼굴의 피부 산란/역광, 머리카락·오징어의 필름 투과, 자기 잉크에서 숨는 지연을 실제 웹에 연결했다. 선택 슈터의 WeaponCategory/WeaponDetail도 Shtr/Shtr로 공급한다. 바닥·벽 잉크는 [r7 반영](ink_surface_r7.md)을 유지한다.

| 반영한 것 | 원본 근거와 실제 웹 결과 | 남은 범위 |
|---|---|---|
| 몸·얼굴 | [재질 상세 §3~6](../graphics/character_material_r8.md): MAi.R 피부 마스크, Thc.R 두께, Trm×backlight×constant, wrapped direct·edge transmission. body5549/face1115 [판독], 실제 FRES [데이터] | live type11/피부/몸 잉크 분기, 별도 재질 세 개의 필수 자원 미공급 |
| 머리카락·오징어 | hair2855/squid3358 [판독]: film량으로 바탕색·SH 법선·투과량 변경, 실제 2cl 차분 보정 법선 사용 | 원본 12층 cube/BRDF·SPP.xy/fade·전체 GPU 일치 |
| 조명 RGBA | Main A×Intensity=10, 동적 spot RGBA.w도 강도 적용. 원본 1048cb8..ce8 격리 명령 블록 [실행] 2,048입력/8,192float bits 불일치0 | whole provider/actor/capture/GPU 실행을 검증한 수치가 아님 |
| 자기 잉크 잠영 | [표시 상세 §3~6](../graphics/character_display_r8.md): 후보→B794/B798 지연→B7a0→SM→holder. 숨은 동안 wrapper tick 유지, 나올 때 _Hlf 경유와 몸 복귀 확인 | 정적 바닥의 웹 contact/sphere query adapter. 벽 edge·상승 공중 B1b4 미공급 시 unsupported, type11 binder reset은 기록만 함 |
| 변신 입력·기어 | actual ActionSpecUp triplet45/18/5와 기존 AP 보간을 +13c 캐시에 공급. 원본 구 probe 기하384/반경10블록 [실행] 대조 | native Phive 전체 질의/이동/플랫폼 결과 공급은 별도 |
| 지속 사격 애니 | 기존 [무기 이름 근거](../graphics/animation_weapon_blackboard.md)로 Shtr/Shtr 공급. 실제 ASB Shoot_Shtr skeletal leaf 테스트, 사격 hold 시 state59 확인 | holder-null/clear 수명, 재질·가시성 leaf 전체, 원본 최종 pose |

전체 소스 반영률 **13/62=20.97%**, 일부37/차이9/원본 미확정3. 그래픽은 **반영 확인0/10, 일부7/10** 유지. 원본 분석은 **556/986=56.39%**, 그래픽 **102/204=50.00%** 유지. 기존 고정 질문 전체가 닫히지 않아 분모·분자·상태를 바꾸지 않았다. 이 수치는 실제 개선량이나 화면 유사도 점수가 아니다.

## 실제 검증

- 전체 **304/304 테스트**, typecheck/build exit0.
- 원본 표시 producer2,048/SM384/holder384, corner zero512, geometry384/radius10, 연결288프레임 대조. query 결과·raw fields는 fixture 입력, SM material setter는 capture 경계. 전체 slot19/Phive/GPU 실행 아님.
- 선택 원본 GLSL 식↔WebGL 포트 **512/512**, maxAbs `1.1920928955078125e-7`. 동일 WebGL에서 비교했으며 원본 NVN GPU 실행이 아님.
- 실제 Lby **12단계/표시87프레임**: 사격→자기 잉크1→변신→지연 숨김→_Hlf→몸 복귀→재진입/숨김→재복귀→reset. 실제 총탄이 만든 칠을 사용했고 발밑 잉크를 fixture로 주입하지 않았다.
- 실제 body/face/hair/squid **네 재질 texture ready/compile/consumer 확인**, 별도 후보 세 개는 미공급 진단과 기존 렌더 유지. 조명 A10/spot5, 베이크75+75, 환경 capture2, 잉크 visual11mesh 유지. shader/page/HTTP/GL 오류0, 각 단계 Bloom16draw.
- [현재 웹 화면](../../../analysis/port_character_r8/lobby_after.png)은 웹 실행 기록이다. 사용자 사진과 같은 원본 frame의 픽셀 대조는 하지 않았다.

[명령·실패 기록](../../../analysis/port_character_r8/commands.md), [웹 실행 결과](../../../analysis/port_character_r8/browser_verification.json), [보호 검사](../../../analysis/port_character_r8/final_verification.json). 첫 screenshot30s timeout, 두 번째 잘못된 입력 유지/후보7개 전체 검사, 세 번째 _Hlf 복귀를 body만 기대한 검사·latch 참조 snapshot 오류는 보존했다. 입력을 실제 app callback에도 유지하고 snapshot 복사/원본 _Hlf 경유 기대를 수정한 최종 실행은 통과했다. 검사 실패를 원본 동작 수정으로 해결하지 않았다.

## 다음 그래픽 우선순위

1. **몸 잉크/피부 및 _Hlf·탱크 추가 재질**: type11 material ASB→CompPaint intensity/team/thickness 공급과 누락 texture 경로. 기준은 character_material_r8 §11, 실제 진단은 browser JSON의 character/playerInfo.
2. **잠영 파문·총구·착탄/탄 VAT**: hidden 상태를 파문 식으로 대체하지 않는다. [ink_visuals](ink_visuals.md)의 FX02/03/04 원본 emitter/색·alpha/VAT 경계를 이어서 반영한다.
3. **환경반사·캐릭터 SPP 그림자**: 원본 cube12/Illuminate/BRDF texture와 SPP.x/y/fade를 확보해 현재 PMREM/공통 shadow adapter를 교체한다.
4. **벽·모서리·상승 공중 잠영**: Ba74/Ba78/B1b4/PC contact 전체 생산자를 연결한다. unsupported를 상수0으로 채우지 않는다.

원본·assets·impl·scripts·package.json은 이번 작업에서 변경하지 않았고 commit/push도 하지 않았다.
