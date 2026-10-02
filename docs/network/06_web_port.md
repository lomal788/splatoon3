# 06. 웹 포팅 구조와 검증 기대값

[목차](network.md)

원본의 **관측 가능한 동작**(원격 캐릭터 갱신 주기, 탄은 발사자 기준으로 판정, 이벤트 스탬프·생명 번호로 낡은 이벤트 폐기, 양자화 오차)을 유지하면서 웹 환경에 맞춘 구조입니다. 원본은 P2P(전용 서버 없음)이고, 아래 "서버"는 웹에서 pia 세션 + 세션 마스터 역할을 대신하는 중계 서버입니다.

## 1. 권장 구성

| 모듈(웹 권장 이름) | 원본 대응 | 책임 |
|---|---|---|
| `NetClock` | GameFrame 싱글턴 `+0x148` + NetUtilFrameStarter | 온라인: `frame = trunc(f32(f32(s32(sharedMs − startMs)/1000)·60))` 를 갱신마다 다시 계산(시작 전 INT_MIN). 오프라인: 매 스텝 +delta. sharedMs = 원본에서는 pia ClockProtocol 공유 시계(µs)÷1000 [02 §5.5·§5.6](02_replica_model.md#56-공유-시계--pia-cloneclockprotocol-판독--실행); 웹은 서버 시계 동기 값 |
| `StartClockNegotiator` | NetUtilFrameStarter 0x710126c02c | 각 클라이언트 desired = now + offsetMs, 마스터(=서버)가 최댓값을 startMs로 확정·배포 |
| `NetTypeRegistry` | 0x71012f8808/0x71012f8db8 | 타입 이름·hash·비트 수·encode/decode |
| `BitWriter/BitReader` | writer vt+0xa8 등 | n비트 정수, 양자화 헬퍼 |
| `Replica` | NetEnl 레플리카 | 상태 요소(Unreliable/Reliable), 이벤트 송·수신 큐, SenderPolicy |
| `EventSender` | 0x71018b7f30 | 권한 검사, (payload, frame, life) 큐잉, 참가자 1명이면 실제 송신 생략 |
| `StateSender` | 0x71024890d8, GameNet 0x710129193c | `frame % 4 == 0` 일 때 상태 작성 |
| `RemotePlayerSync` | `spl::PlayerNetControl` 0x7102658bb4 | 지연 추정·샘플 링버퍼·오차 스프링 |
| `RelayServer` | pia 세션 + 세션 마스터 | 방, 브로드캐스트, `SessionMaster*` 레플리카 소유, 시작 시각 |

### 1.1 서버 권한 범위 (판단 근거)

| 대상 | 원본 권한 | 웹 권장 | 근거 |
|---|---|---|---|
| 자기 플레이어 이동·상태 | 소유 기기 | 클라이언트(서버는 중계) | PlayerNetState 송신은 소유 기기만 [판독] |
| 탄 생성 | 발사자 기기, 이벤트로 복제 | 클라이언트 → 서버 → 다른 클라이언트 | 송신 모드 0 = 소유자 확인 [판독] |
| 명중 판정 | 공격자 기기의 탄(DamageHelper) | 클라이언트 판정 유지(원본 체감 재현). 부정행위 방지가 필요하면 서버 검증을 **추가**하되 결과는 같게 | [판독] |
| HP·사망 | 피해자 조작 기기(`PlayerNetEvent::Attack` 적용, HP는 PlayerNetState +0x6c로 다른 기기에 전달) | 피해자 클라이언트 또는 서버 | [판독] ([05 §4.2](05_events_combat.md), [04 §4.7](04_player_state.md)) |
| 모드 오브젝트(호코·야구라·에리어·아사리), 승패 판정 | 세션 마스터(`SessionMasterOrEvent`) | **서버** | [데이터] |
| 시작 시각·설정(`VersusSetting`, `StationInfo`) | 세션 마스터, Reliable | 서버 | [데이터] |
| 탄 난수 시드·룰·시간 | 매치 공용 시드 a..d = `OnlineVersusSetting` +0x238..+0x244(Rule +0x84, Time +0x88), 송신 권한 기기가 xorshift128로 생성해 배포, 로비 0x7102d60098이 대전 설정 +0xa4..에 복사 | 서버가 매치 시작 때 u32×4·Rule·Time 생성·배포 | [판독/실행] ([05 §3.1](05_events_combat.md)) |

## 2. 메시지 목록

| 메시지 | 주기/시점 | 신뢰성 | 크기(원본 비트) | 내용 |
|---|---|---|---|---|
| `PlayerState` | 4스텝마다 | 비신뢰(최신 값만 의미) | 546 | [04 §4](04_player_state.md#4-playernetstate-필드-표-실행--판독) |
| `Event{type, frame, life, payload}` | 발생 스텝 | 신뢰·순서 보장(원본 이벤트 요소) | payload + 헤더(GameFrame ≤ 8,388,607, LifeNumber 0~15) | [05](05_events_combat.md) 표 |
| 모드 상태(`GachihokoNetState` 70, `GachiyaguraNetState` 88~234, `PaintTargetAreaNetState` 21, `VersusRefereeVAreaNetState` 2~146 …) | 4스텝마다 | 원본 Protocol 값 따름 | `nettypes.tsv` | 서버 → 클라이언트 |
| 설정·시작(`VersusSetting`, `StationInfo`, `VersusStartClockEvent`) | 변경 시 | 신뢰 | | 서버 → 클라이언트 |

이벤트 헤더는 payload 뒤 GameFrame 23비트 + LifeNumber 4비트입니다([03 §3.5](03_serialization.md)). 원본 이벤트 요소가 신뢰 전송인지는 pia 계층을 판독하지 않아 **[미확정]**이지만, 탄·사망 이벤트를 잃으면 원본에서도 복구 수단이 보이지 않으므로 웹은 신뢰 채널을 씁니다.

## 3. 의사코드

```ts
// 고정 스텝 (1/60 s). 표시 프레임과 분리
function step() {
  // 원본 온라인: GameFrame 은 공유 시계에서 매 갱신 다시 계산 (02 §5.5)
  clock.frame = started ? Math.trunc(f32(f32(s32(sharedNowMs() - startMs) / 1000) * 60)) : INT_MIN;
  game.update();                              // 이 안에서 sendEvent(...) 호출
  if (clock.frame % 4 === 0) sendState(buildPlayerState(Math.max(clock.frame, 0)));
}
// 주의: 시계 기반이라 갱신 사이에 frame 이 2 이상 뛰거나 그대로일 수 있고, 그 경우 4프레임 송신이 빠지거나 반복될 수 있음(원본과 같음).
// 오프라인/연습: clock.frame = paused ? frame : frame + 1 (기본 델리게이트 0x7101028850)

function sendEvent(owner: Replica, type: NetType, ev: object) {
  if (!owner.canSend(localPlayer)) return false;          // 모드 0: owner.playerId === local
  if (session.memberCount < 2) return true;               // 원본: 혼자면 성공 처리만
  outQueue.push({ type: type.hash, frame: Math.max(clock.frame, 0),
                  life: owner.lifeNumber & 0xF, payload: type.encode(ev) });
  return true;
}

function onEvent(msg) {                                   // 소비자별 폴링과 같은 결과
  const owner = replicas.get(msg.replicaId);
  if (msg.life !== owner.lifeNumber) return;             // 이전 생명의 이벤트 폐기
  dispatch(msg.type, decode(msg), msg.frame);
}

// 원격 플레이어 (PlayerNetControl)
function remoteStep(r: RemoteSync, received?: PlayerState) {
  if (!received) r.w *= 0.992;
  else { r.D += (1 - r.w) * ((r.localFrame - received.frame) - r.D); r.w = 1; r.samples.push(received); }
  const T = r.D > 5 ? r.D - 5 : r.D < 2 ? r.D - 2 : 0;
  r.S += (T - r.S) * 0.03;
  // 샘플 선택·오차 스프링: 04 §5
}
```

정밀도: 양자화·보정 계산은 `Math.fround`로 f32 순서를 지키고 정수 변환은 `Math.trunc`. 각도는 `Math.atan2/asin`으로 99.3% 동일·최대 1 LSB 차이([03 §6](03_serialization.md#6-검증-실행)); 완전 동일이 필요하면 원본 표를 추출해 씁니다.

## 4. 원본 이름 ↔ 웹 권장 이름

| 원본(확인된 이름·주소) | 웹 권장 |
|---|---|
| `spl::PlayerNetState` | `PlayerState` |
| `spl::PlayerNetControl` | `RemotePlayerSync` |
| `spl::PlayerNetEvent::*` | `PlayerEvent.*` (같은 이름 유지) |
| `game::NetSenderPolicy` 값 | `SenderPolicy` 같은 이름 |
| `game::NetEnlProtocol` Unreliable/Reliable | `channel: 'unreliable' / 'reliable'` |
| GameFrame `+0x148` | `clock.frame` |
| LifeNumber (`U32_LifeNumber`) | `lifeNumber` |
| GameNet `+0x1c0`(=4) | `STATE_SEND_INTERVAL = 4` |
| PlayerNetControl `+0x2000/+0x2004/+0x2008` | `D / w / S` |

## 5. 원본과 같게 유지할 것 / 바꿔야 할 것

- 유지: 4스텝 상태 주기, 이벤트 프레임 스탬프와 LifeNumber 필터, 위치 ±256 범위·1/256 단위 양자화(맵 좌표가 ±256 안이라는 전제 — 스테이지 크기 확인 필요 **[미확정]**), 지연 추정 상수(0.992, 0.03, 2, 5), 오차 스프링 상수.
- 바꿈: pia P2P·호스트 이전 → 서버 중계·서버 마스터(원본에서 마스터 이전 때 생기는 공백이 없어짐: 관측 차이로 기록할 것). 비트 패킹은 원본이 LSB 우선·바이트 정렬 없음([03 §3.4](03_serialization.md))이므로 원본과 같은 형식을 쓰면 원본 바이트열과 대조 시험이 가능합니다(호환 자체는 불필요).

## 6. 에셋·데이터 추출

- 넷 타입 표: `PY web/tools/network_typetable.py > analysis/network/nettypes.tsv` (hash·비트 수를 웹 레지스트리 생성에 그대로 사용 가능)
- 레플리카 설정: `PY web/tools/network_netparam_scan.py` + Bootup `Net/` (`analysis/network/bootup_net.json`)
- 각도 표(정확 재현 시): 이미지 `[0x7105794808]`(atan, 129×8 B), `[0x7105794810]`(sin/cos, 256×16 B)

## 10. 검증 기대값 (웹 구현 테스트용)

| 입력 | 기대 출력 | 출처 |
|---|---|---|
| Q17 enc(10.5) | 2687, dec → 10.49625 | [실행] |
| Q17 enc(-3.25) | 66367 (=0x1033F), dec → -3.24614 | [실행] |
| Q17 enc(100.0) | 25599, dec → 99.99762 | [실행] |
| VEL41 v=(0.3,0,-0.4)/프레임 | P=0, Y=3256, S=959 → dec (0.29976, 0, -0.39954) | [실행] |
| 탄 이벤트 +0x38 = 1.5 | 384 → 1.5 | [실행] |
| 기본 PlayerNetState | 546비트 | [실행] |
| 지연 8프레임, 4스텝 주기, 시작 D=0,w=1,S=0 | 60스텝: D 2.4267 S -0.4114, 300: D 6.6871 S 1.365, 599: D 7.7793 S 2.7281 | [재구현] |
| 매 스텝 수신 | D 0 유지, S → -2.0 | [재구현] |
| LifeNumber 다른 탄 이벤트 | 복제 탄 생성 안 함 | [판독] |
| 참가자 1명 | 이벤트 송신 함수 true, 실제 송신 없음 | [판독] |
| GameFrame: sharedMs − startMs = 42 ms / 409,002 ms, base 0 | 2 / 24,540 | [실행] (`network_clock.py`) |
| 이벤트 헤더 GameFrame = 8,388,608 | 23비트 포화 8,388,607 | [실행] (`network_bitpack.py`) |
| 비트 열 (558,10비트),(6,3),(1721824,21),(2918,14) | 바이트 `2e 1a bc 48 9b 2d` | [실행] (원본 writer) |
| 복제 탄 시드 | `mgr+0x120 + 송신 GameFrame` — 발사자 로컬 탄과 같은 값 | [판독] |

"분석 완료"(구조·직렬화)와 "웹 구현 완료"(없음), "동작 검증 완료"(직렬화 함수 단위만 원본 실행, 전체 통신 흐름은 미검증)는 구분합니다.
