# 머리카락 천의 프레임 전달과 hcl 스텝 경계 (r9)

## 1. 기능 개요

2026-10-03. 머리카락 천은 캐릭터 모델 갱신 경로 안에서 hclWorld를 진행한다. 원본 소비자는 일반 dt에 인스턴스별 배율을 곱한다. 별도 초기화는 약1/30초 30스텝이다 [판독]+[실행: 호출 경계]. **CullFrame의 실제 솔버 호출 gate는 신규 0F73368 원본 실행으로 연결했다. 게임 frameInfo 원본 writer와 인스턴스 배율 writer는 아직 추적 중이며, 전체 천 물리 확정으로 계수하지 않는다.**

## 2. 원본과 자료

Splatoon3 v0 main.reloc.img. 신규 decomp `analysis/decomp/r9_graphics/cloth_world_setup.c`, `cloth_step_candidates.c`, `cloth_update_entry.c`, `cloth_frame_bridge.c`, `cloth_actor_after.c`, `cloth_cull_record.c`, `cloth_cull_record_update.c`, `actor_frame_info.c`. 기존 actor 작업은 `analysis/decomp/r5_physics/actorjob.c`, 모델 단계는 `analysis/decomp/r5_range/xlink_action.c`를 재사용했다. 신규 실행 `web/tools/r9_gfx_cloth_dt_emu.py`, 결과 `analysis/completion/r9/graphics_cloth_dt_emu.json`. CullFrame 실행은 `web/tools/r9_gfx_cloth_cull_emu.py`, 결과 `analysis/completion/r9/graphics_cloth_cull_emu.json`이다.

## 3. 전체 호출 경로

`3CC95E0`(액터 단계1 작업, 기존 판독) → 액터vt190 → `0F7493C` → `134AA3C`(기존 모델 처리) → `13452F0` → `3A0FF14` → `3A1BAE4` → `3C0AAE0`(pre) → `3C0C0BC`(step) → `3C0D72C`(post).

`3C08D3C`는 hclWorld를0x128바이트로 생성해 천 상태객체C+28에 둔다. 생성자`CD3454`는worldVT54FDA90, stiffness dispatcher`D0401C`를world+48에 둔다. instance row는C+18, 개수C+10, stride58이고`CD4578`로world에연결한다 [판독].

`3C09F64` 종료는 외부collidable 제거→world instance제거`CD4D00`→각인스턴스해제→world해제 순서다 [판독]. 같은+28이라도3C07FBC~3C089DC는 **별도 bone-binding 객체**여서 world dt로 혼동하지 않는다.

## 4. 객체와 writer/reader

| 기준 객체 | 필드 | writer | reader/의미 |
|---|---|---|---|
| 액터 단계1 job J | +18 frameInfo pointer | producer 미확정 | 3CC95E0 |
| frameInfo F | +0 f32, +4 f32 | producer 미확정 | 3CC95E0가 actorTimescale을 두 값에 각각 곱함 |
| 액터 A | +258 f32 | 3CC95E0 | 선택한 actorTimescale(0이면getterkey0→1) |
| 모델 관리부M | +148 하위관리부P | 로딩측 | 3A0FF14→3A1BAE4 |
| P | +B0 count/+B8 pointer array | 로딩측 | 첫wrapper의+0=C 천객체 |
| P | +150 bit0, +156 bit4 | setter추적중 | 하나라도켜지면3A1BAE4는천갱신하지않음 |
| C | +10 u32/+18 array | 3C08D3C | instance rows stride58 |
| C | +28 worldptr | 3C08D3C | 3C0C0BC→CD3EAC |
| C | +48 flags bit14 | 3A1BAE4 초기화 및기타writer | 켜지면30회warmup, 종료시끄기 |
| instance row | +48 f32 dt배율 | writer미확정 | 정상 dt=f32(Fdt*배율) |
| 물리 component | +70 culling record K | 12E8EC8→12CEFE8 | 0F73368/12CF69C |
| K | +28 period, +2C phase | 기존12E9B28 | 실제 solver gate 0F73368 |
| K | +34.bit2 | 초기화/기타 setter | 켜지면 주기 gate 우회, dt 배율 없음 |
| global5827E20 manager | +F0 frame counter | writer 추적 중 | frame % period == phase 검사 |

## 5. 수명과 분기

`3A1BAE4`는 P150.bit0, global599DFA8+B8.bit4, P156.bit4, count0, Cnull을 검사하여 조기반환한다. wrapper+18이 있으면 별도`3A3D5AC` 목록을 갱신하고 현재 hcl direct 경로로 들어가지 않는다. P154가음수면 C48.bit26이0일때 C48.bit14(4000)를켜고`3C0A924`로초기화한다. 이후pre→step→post를같은incomingdt로호출한다 [판독].

## 6. dt 계산과 순서

`3CC95E0`는 frameInfo+0/+4를 각각 actorTimescale과 FMUL해서 local pair로 만들고 액터vt190에 전달한다. frameInfo+0의 **실제writer를찾지못했으므로1/60으로고정하지않는다**. PhiveWorld+24의1/60 writer와는 다른객체다.

`13452F0→3A0FF14→3A1BAE4`는 pair첫값을pre/step/post에 전달한다. 정상`3C0C0BC`는각instance에대해 `dt=f32(row48*inputdt)`를S0으로놓고 CD3EAC(world, threadContext, oneInstanceArray)를호출한다. decompiler가정수인자로표시한부분은 ASM3C0C884FMUL/3C0C890v0복사로정정한다.

C48.bit14가켜지면 `CD3EA4→CD3EAC` dtbits3D088889 한회, 이후29회 `(3C0AAE0(dt), CD3EA4(dt))`를진행한다. 총30스텝, pre29회이며 row48배율과 incomingdt를사용하지않는다. 마지막C48.bit14를끈다. 1/60을30회또는1/30을29회로바꾸지않는다 [판독]+[실행].

SDK`CD3EAC`는 world의지연작업목록`CD3DE8`→task준비→instance+18상태의operator목록→vt28각operator를 local step context로 실행한다. context+0에dtbits를기록한다 [판독]. 실제operator식은본실행에서제외했다.

## 7. 모델과 머리카락 연결

PlayerCustomHair49의Head/Head_Root모델행렬복사는천스텝함수자체가아니다.3C0AAE0/3C0C0BC/3C0D72C가각각입력/스텝/출력을연결한다. CullFrame 최종 step gate는 `0F73368→3DB1704→3A0FF14→3A1BAE4`로 연결된다. 기존 `0F76F78`의 0F77A68~0F77A78은 전달 frame pair 두 값에 S9 배율을 각각 곱해 이 함수에 넘긴다. Player 갱신 `243A4EC`의 243AED0~243AEDC 역시 관리 대상 액터마다 저장한 S9/S8 pair를 `0F73368`에 넘긴다 [판독]. S9의 상위 공급자는 별도로 남는다.

K가 있고 period≥2이며 K34.bit2=0이면 manager+F0를 읽어 `frame % period == phase`인 프레임에만 `3DB1704`를 부른다. 호출 S0은 `f32(period * incomingDt)`이고 S1은 원래 전달값이다. CullFrame4 정상 경로는 스텝 4프레임당 한 번에 dt 4배다. bit2=1 또는 period<2이면 매번 호출하며 dt 배율이 없다. **manager가 null이면 period≥2여도 매번 scaled dt로 호출한다**. 원본의 이 예외를 정상 주기와 합치지 않는다 [판독]+[실행].

이후 `12CF69C`에는 scaled dt가 아닌 원래 incomingDt와, 첫 천 객체의 instance row18 bits0/1 중 하나라도 켜져 있는지 여부를 전달한다. 이 함수는 생략 프레임의 뼈 버퍼 보간 소비자다. 전체 보간 행렬의 독립 실행은 미검증이다. 머리/척추 capsule의 정확한 갱신 순서는 Simulate operator 내부로 추적 중이다.

## 8. 다른 기능과의 상호작용

월드물리dt와모델프레임dt는별도객체다. 글로벌천중지비트599DFA8+B8.bit4는모델천진입을차단한다. actor time scale은프레임pair에곱해져 모델경로로전달된다. 스케일0/음수도 dt소비자가클램프하지않는다 [실행: 합성유효구조체].

## 9. 웹 반영 필요

`impl/render.md`, `impl/assets.md`: 천 dt를고정1/60가정에서frameInfo전달값×instance배율모델로분리한다. 원본writer확정전임의고정값을넣지않는다. 초기화warmup은30×f32(1/30), pre29순서를별도로둔다. CullFrame은 period/phase gate와 scaled dt, 초기화 bit2 우회를 반영해야 한다. 최종 solver 및 뼈 보간식은 미확정이다. 웹코드는수정하지않았다.

## 10. 실행 검증

`PY web/tools/r9_gfx_cloth_dt_emu.py` →768, f32bits/호출순서mismatch0,LR종료. 실제원본3C0C0BC/CD3EA4의 분기와FMUL을실행했다. 입력dt0/음수/1/60/1/30/가변값, row배율0/음수/양수, warmup/normal을대조했다.

**Fixture:** CD3EAC는S0캡처후return(솔버실행아님), warmuppre3C0AAE0는호출캡처,3C10648목록allocator와threadprovider/TLS/core0을합성한다. 결과는최종입자위치검증이아니다. 초기실행은record44=0으로SDKbuffer를참조하여invalidread3C0C4B0(0x0); 원본record필드요건인44=1로독립fixture를정정했다. 이후TLS맹글링6TlsSlot오타를실제7TlsSlot으로수정했으며허용PLT두개외호출은없다.

`PY web/tools/r9_gfx_cloth_cull_emu.py` → 원본 0F73368 전체 2048, f32bits/호출 mismatch0, LR종료. period1/2/4/6, phase, frame, dt0/양수/음수, flags와 manager null을 대조했다. Fixture는 하위 `3DB1704`의 step 호출 캡처, `12CF69C`의 후처리 호출 캡처, nn::os read lock/unlock no-op이다. 원본 gate와 FMUL을 실행했으며 하위 Havok 입자/최종 포즈는 실행하지 않았다.

## 11. 남은 근거와 다음

- frameInfo+0/+4 producer, instance row48 writer: 3C88E74가 job+18에 manager+2B0를 넣고, 3C85FBC가 외부 pair를 manager+2B0에 복사한다. 신규3CDB41C/3CDB8BC/3CDC2C0는 상위 pair 복사 소비자로서 최초 writer가 아니다. module 가상 호출과 C 생성후 배율 setter를 추적한다.
- CullFrame4 solver gate는 신규0F73368으로 연결했다. 남은 것은 global manager+F0 writer, K34.bit2/P156.bit4 setter 및 12CF69C 뼈 보간의 전체식이다. HairArrange와 solver는 같은 period/phase를 읽지만 별도 호출이다.
- hcl damping/Bend/LocalRange/지형충돌 정확식은operator별nativeconsumer가필요하다.
- cloth scalardt를실행한결과로위3개광범위질문전체를확정승격하지않았다.
