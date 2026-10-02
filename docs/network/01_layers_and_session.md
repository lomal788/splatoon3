# 01. 라이브러리 계층·세션·매치메이킹

[목차](network.md)

## 1. 개요

대전 통신은 닌텐도 미들웨어 **pia 6.20.1**(P2P 세션·전송)과 **NPLN 1.2.0**(gRPC 온라인 서비스) 위에 게임 측 **Enl/GameNet 계층**(레플리카·이벤트·상태)이 올라간 구조입니다. 게임 서버가 시뮬레이션하지 않습니다. 웹 포팅에서 이 문서의 내용은 "무엇을 대체해야 하는가"의 근거이고, 원본 라이브러리 동작을 재현할 대상은 아닙니다.

## 2. 근거 자료

| 자료 | 위치 |
|---|---|
| 미들웨어 버전 문자열 | `extracted/main_strings.txt` 54809~54830행 |
| 라이브러리 RTTI | `extracted/typeinfo_names.txt` (`N2nn3pia...` 216개, `N2nn4npln...` 487개, `N4pead...` 33개) |
| gRPC 메서드 경로 | `main_strings.txt`의 `/nn.npln.*` (94개) |
| 잡 상태 이름 | `NetHostMigrationJob::WaitRecreateNetwork` 등 |

## 3. 계층 [데이터]

`SDK MW+...` 문자열(main 끝부분):

| 모듈 | 버전 | 역할(이름 기준) |
|---|---|---|
| `Pia`, `PiaCommon`, `PiaTransport` | 6_20_1 | 스테이션·패킷·신뢰/비신뢰 프로토콜 |
| `PiaSession` | 6_20_1 | 세션·메시 참가·호스트 이전 |
| `PiaClone` | 6_20_1 | `ClockProtocol`(공유 시계), `EventProtocol`/`BroadcastEventProtocol` |
| `PiaSync` | 6_20_1 | 동기 메시지(`sync::StartMessage`, `DataMessageHeader`) |
| `PiaLocal` | 6_20_1 | 로컬 무선(LDN) |
| `PiaLan` | 6_20_1 | LAN(`LanBackgroundProcessJob`, `LanBrowseProcessJob`) |
| `PiaNpln` | 6_20_1 | NPLN 연동(`NplnRelayClient`, `IceServerConfigGetter`, `NplnHostMigrationJob`, `AttachMeshJob`) |
| `NintendoSDK_NPLN` / `_gRPC_For_NPLN` / `_Google_APIs_For_NPLN` | 1_2_0 / 0_0_0 | gRPC·protobuf 온라인 서비스 |

`pead` 네임스페이스는 pia가 쓰는 기반 유틸리티입니다(`pead::Heap`, `ExpHeap`, `Thread`, `Mutex`, `CriticalSection`, `SafeString`, `Delegate`, `RuntimeTypeInfo`). sead와 같은 모양의 pia 전용 사본으로 보입니다 **[추정 — 클래스 구성]**. 게임 네트워크 동작에는 직접 관여하지 않습니다.

pia 힙 이름 문자열(`pia common heap`, `pia transport heap`, `pia session heap`, `pia clone heap`, `pia sync heap`, `pia npln heap`, `pia lan heap`, `pia local heap`, `pia wan heap`)로 모듈별 힙이 따로 있습니다 **[데이터]**.

### 3.1 pia transport [데이터]

typeinfo: `ReliableProtocol`, `UnreliableProtocol`, `BroadcastReliableProtocol`, `StreamBroadcastReliableProtocol`, `ReliableSlidingWindow`(+`AckMessage`, `SendBuffer`, `ReceiveBuffer`), `RttProtocol`, `SequenceIdController`, `NetworkEmulationProtocol`, `MonitoringDataProtocol`, 송수신 스레드(`Pia SendThreadStream`, `Pia ReceiveThreadStream`). 신뢰 전송은 슬라이딩 윈도 ACK 방식입니다. 클래스 위치(**정정**, 3차): 이전 판은 `ReliableSlidingWindow` vtable을 0x710540c9b0(GOT 0x7105778af8)·0x710540d058, `ReliableProtocol` vtable을 0x710540c918·0x710540cf90으로 적었습니다. RTTI 이름을 다시 읽으니 0x710540c998/0x710540c900 근처는 파생 클래스 `BroadcastReliableSlidingWindow`(이름 0x7104a5d031, 기반 typeinfo 0x710540d0c8)·`BroadcastReliableProtocol`(0x7104a5d002, 기반 0x710540d030)의 typeinfo/vtable 영역이라 틀렸습니다. 바른 값: **`ReliableSlidingWindow` vtable 0x710540d058**(= `[GOT 0x7105778b60]+0x10`, 생성자 0x71007e1c08, 소멸자 0x71007e1cec/0x71007e1e60, 초기화 0x71007e21ec/0x71007e20dc), **`ReliableProtocol` vtable 0x710540cf90**(= `[GOT 0x7105778b58]+0x10`, 생성자 0x71007e0c6c, 슬롯 +0x98 0x71007e1acc가 창 갱신 0x71007e3398 호출) (`analysis/decomp/network/net_sync2.c`, `netrest_a.c`, `netrest_b.c`) **[판독]**.

#### 3.1.1 신뢰 전송 창·재전송 (3차 해소) [판독]

생성자는 `+0x80 = 틱주파수 × 33 / 1000`(= **33 ms**)과 `+0xa4 = 1`(압축 사용 플래그로 보임)만 정하고, 초기화 0x71007e21ec/0x71007e20dc는 `+0x2c = 0, +0x30 = 1`(다음 시퀀스), 스테이션별 버퍼 리셋, 대기 비트맵(+0x74/+0x78/+0xa0) 0, 마지막 송신 시각(+0x50/+0x90/+0x98) 0으로 둡니다. 창 크기·재전송 간격은 상수가 아니라 갱신 함수 **0x71007e3398**이 계산합니다:

```
매 송신 틱 (ReliableProtocol 슬롯 +0x98 → 0x71007e3398(window, ..., 남은 바이트)):
  deadline = 0x71007e3a74(window):
      maxRtt = max over 연결 스테이션 s ( 0x71007e74d0(rtt(s), 0x71007e7540(rtt(s))) )   // 스테이션별 RTT 값(단위 ms로 보임)
      maxRtt ≥ 0 이면  now + 33ms틱 + 틱주파수 × (s32)(maxRtt × 1.4) / 1000
      스테이션 없으면  u16 window+0x5c(“미설정” 표식)
  now ≥ window+0x90 + 33ms 이면 0x71007e3b88: ACK 대기 스테이션(비트맵 +0x78)에게 종류 0x20 패킷 송신, +0x90 = now
  now ≥ window+0x98 + 33ms 이면 0x71007e3e04: 비트맵 +0xa0 스테이션에게 종류 0x40 패킷 송신, +0x98 = now
  now ≥ window+0x50 + 33ms 이면 vt+0x58로 대기 데이터 송신
  송신 버퍼(항목 0x5d0 B, 기준 +0x2c, 용량 u16 +0x28)를 앞에서부터:
      (항목 시퀀스 − 기준 시퀀스(+0x30)) > 0x7f 이면 멈춤                      // ★ 창 = 128 패킷
      재전송 시각(항목+8) == 표식 이면 = deadline
      재전송 시각 ≤ now 이면: 남은 바이트 안이면 vt+0x50으로 다시 보냄(재전송 횟수 +0x14 가 0이면 모드 0, 아니면 1),
                              재전송 시각 = deadline, +0x14 += 1
```

수신측 ACK 비트맵은 최대 0x80(128)개 항목, 16바이트(0x71007e5480)이고, 패킷 버퍼는 0x5a0(1,440) 바이트입니다(초과면 결과 0x4c0d). 즉 **신뢰 전송 = 창 128 패킷, 재전송 간격 = 33 ms + 1.4 × (연결 스테이션 중 최대 RTT), ACK·제어 패킷은 33 ms마다 최대 1번** **[판독]**. RTT 값의 단위(ms)와 0x71007e74d0/0x71007e7540의 정확한 의미(평균/최대 등)는 **[추정]**, 재전송 횟수 상한·연결 끊김 판정은 **[미판독]**입니다.

진단 로그 문자열 `[Analysis] StationIndex, RTT[ms], RTTMin[ms], RTTMax[ms], UnicastPacketLoss[%%], BroadcastPacketLoss[%%]`로 스테이션별 RTT·손실률을 집계합니다 **[데이터]**.

### 3.2 pia session / 호스트 이전 [데이터]

- 세션 잡: `CreateSessionJob`, `JoinSessionJob`, `JoinRandomSessionJob`, `BrowseSessionJob`, `LeaveSessionJob`, `CreateMeshJob`, `JoinMeshJob`, `LeaveMeshJob`, `KickoutManageJob`, `OpenCloseParticipationJob`, `SessionStatusCheckJob`.
- 호스트 이전: `ProcessHostMigrationJob`(상태 `UpdateHost`, `WaitNetworkHostMigration`, `WaitUpdateSessionMessageFromNewHost`, `CompleteProcess/CompleteFailure`), `LeaveMeshWithHostMigrationJob`(`CalcNextHost`, `SendStartHostMigrationMessage`, `WaitStartHostMigrationAck`, `WaitNextHost`), `net::NetHostMigrationJob`(`InquireNetworkState`, `EmulateDisconnection`, `WaitRecreateNetwork`, `ReconnectNetwork`, `WaitAllClientsAck`, `HostSuccessProcess/ClientSuccessProcess`), `npln::NplnHostMigrationJob`.
- 메시지: `NetStartHostMigrationMessage`, `NetUpdateNetworkHostMessage`, `NetKeepAliveNetworkMessage`(+Ack), `NetUpdateNetworkConnectionStatusMessage`(+Ack).
- 결과 코드: `ResultSessionConnectionIsLostByHost`, `ResultSessionMigrationFailed`, `ResultSessionConnectionIsLostByHostMigrationFailure`, `ResultJoinSessionFailedByHostMigration`.

즉 **호스트(세션 마스터)가 나가면 남은 스테이션 중 다음 호스트를 계산해 이전**합니다.

#### 3.2.1 `LeaveMeshWithHostMigrationJob` 상태 흐름 [판독]

상태 문자열은 코드 참조가 있습니다(`xref.py str "LeaveMeshWithHostMigrationJob::CalcNextHost"` → 0x71007cc894 등). 잡 객체 +0x30 = 다음 상태 함수, +0x40 = 상태 이름, 반환 5 = 다음 틱에 다시, 0 = 상태 전환(`analysis/decomp/network/net_pia_host.c`).

```
진입 0x71007cc808: 세션(+0x58)+0x784 != 0 이면 CompleteProcess
                   이미 조건(0x710077a4a4) 충족이면 대기(5)
                   마감 +0xd8 = now + tick/ms × 설정표[0x10](float, *0x71057d4fd0 +0x10*0xc+4) → CalcNextHost
CalcNextHost 0x71007cca4c: 메시->vt[+0x118](&결과, 메시, &후보ID(+0x68))
                   결과 0 이고 후보 스테이션(0x71007d18a8) 있으면:
                       스테이션+0x28 == −3 이면 WaitNextHost
                       아니면 0x71007c7710(세션) 후 마감 +200 = now + 5000ms → SendStartHostMigrationMessage
                   결과가 0x4c11 오류이거나 후보 없음: 마감(+0xd8) 전이면 대기, 지나면 CompleteProcess
WaitNextHost 0x71007cccac: 마감 전이고 후보가 그대로면(−3이면 대기) SendStartHostMigrationMessage,
                   후보가 바뀌었으면 CalcNextHost 로 돌아감; 마감 지나면 CompleteProcess
```

시간 단위: `FUN_7100781ac8()`가 ms당 틱 수를 주고 `FUN_7100781a38`이 현재 틱입니다(마감 = 현재 + ms × 틱/ms) **[판독, 함수 의미는 추정]**. 다음 호스트 선택 규칙은 §3.2.2에서 판독했습니다. 게임 쪽에서 "세션 마스터만"이 보내는 레플리카(SenderPolicy `SessionMasterOnly`/`SessionMasterOrEvent`, [02](02_replica_model.md))의 송신 주체가 이 호스트입니다.

#### 3.2.2 다음 호스트 계산 (메시 vt+0x118) [판독]

`INetwork`(RTTI `N2nn3pia7session8INetworkE`)를 상속하는 클래스는 RTTI상 **`nn::pia::net::NetFacade` 하나뿐**입니다(typeinfo 0x71054076d0, 주 vtable 0x71054074a8). 그래서 `[*0x71057d48b0+0x18]->vt[+0x118]`은 NetFacade 슬롯 0x7100788434로 봅니다(메시 객체 타입은 상속 관계로 정한 것 — [판독: RTTI], 런타임 객체 확인은 안 함).

```
0x7100788434(result, facade, &candidate):
    cur = 구현(facade+0x10)+0x98 주소 값(유효하지 않으면 0x10408)
    0x710078e7a8(구현, &next):                        // 후보 계산
        [구현+0x120]->vt+0x98([구현+0x118]) 거짓이면 0x4c11; 구현 vt+0x178 참이면 +0x270 주소로 두 객체를 다시 검사, 거짓이면 0x4c11 (§3.2.1의 “0x4c11 오류”)
        best = −1, bestKey = 0xff
        for i in 0 .. u16 구현+0x114e − 1:              // 스테이션 항목 배열 구현+0x88
            e = 항목[i]
            if !valid(e+0x10) (0x7100780ac0): continue
            if e+0x10 == 구현+0xb8 (0x7100780b24 같음 비교): continue
            if u8 e+9 < bestKey: best = i, bestKey = e+9   // 같은 값이면 앞 항목 유지
        best == −1 이면 next 무효, 0x2c0a;  아니면 next = 항목[best]+0x10
    next == cur 이면 0x6c57
    스테이션 관리자에서 next 를 찾아(0x71007d1730) 없으면 next 를 그대로 candidate 에, 있으면 그 스테이션 정보로 candidate 를 채움
```

규칙: **구현+0xb8 주소와 다른 유효 스테이션 중 항목 +9(u8) 값이 가장 작은 스테이션**(동률이면 배열 앞쪽)을 고르고, 그것이 구현+0x98 주소와 같으면 실패(0x6c57)입니다 **[판독]**. +0xb8/+0x98이 각각 자기 주소/현재 호스트 주소인지, +9 값의 뜻(접속 순번 등)은 **[추정/미확정]**. 웹 포팅에서는 서버가 마스터라 이 계산이 필요 없습니다(§5).

### 3.3 LAN / 로컬 [데이터]

`lan::LanBackgroundProcessJob`, `LanBrowseProcessJob`, `LanCreateNetworkSetting`, `LanConnectionStatus` 와 `local::LdnBackgroundProcessJob`, `LocalEjectClientBackgroundJob`이 있습니다. 같은 세션/전송 계층을 LAN·로컬 무선으로 바꿔 끼우는 구조입니다 **[추정 — 클래스 이름과 공통 기반 `NetworkFactory`]**. 웹 포팅에는 필요 없습니다.

## 4. NPLN (온라인 서비스) [데이터]

gRPC 메서드(일부):

| 서비스 | 메서드 | 웹 포팅에서의 대응 |
|---|---|---|
| `nn.npln.matchmaking.v1.Matchmaker` | `CreateMatchmakingTicket`, `TrackMatchmakingTicket`, `CancelMatchmakingTicket`, `CreateAcceptance` | 매치메이킹 API (자체 구현) |
| `nn.npln.matchmaking.v1.GameSessionService` | `CreateGameSessionCreationTicket`, `JoinGameSession`, `QueryGameSessions`, `SyncGameSession`, `GetUserSession`, `ListLatencyMeasurementServers`, `AllocateIceServerSet`, `IssueMatchmakingIdToken`, `IssueUserDelegationToken`, `*ShortAlias` | 방 생성·참가, 지연 측정 서버 목록, **ICE(STUN/TURN) 서버 할당** |
| `nn.npln.gamesync.v1.Gamesync` | `KeepUserSession`, 트랜잭션·문서 읽기/쓰기 | 세션 유지·결과 보고 |
| `nn.npln.auth.v1.Auth` | 토큰 발급 | 인증 |
| `nn.npln.toyohr.v1beta1.*` | `Schedule/SelectVsSchedules`, `GameRecord`, `FestService`, `Replay`, `Locker` 등 | 스케줄·전적 등 게임 고유 서비스 |

`AllocateIceServerSet` + pia `turn::TurnJob`, `npln::NplnRelayClient`, `wan::NatTraversalJob`로 **P2P 연결은 NAT 통과(ICE)로 맺고, 실패하면 TURN 중계를 쓰는** 구조입니다 **[추정 — 이름 조합]**.

오류 보고 키(`erepo_network_error`, `GamesyncRefereeTimeoutVs1~3`, `GamesyncRefereeValidate`, `MatchFixTimeout0~2`, `MatchSyncTimeout`, `RTTAve_msec`, `P2PSessionClock_sec`)가 있습니다. "Gamesync Referee"가 대전 결과를 서버에서 대조하는 절차로 보이나 판독하지 않았습니다 **[추정]**.

네트워크 오류 종류 열거 문자열(`None, ReadyNetworkFailed, AccountUnavailable, ... SessionMergeFailed, DetectHashCollision, ... AutomatchTimeout, ...`)과 오류 영역 열거(`None, Nifm, Curl, Ldn, Friend, NexCommon, NexSystem, Pia, Account, Ens, Eagle, Npln, Application, Enl`)가 있습니다 **[데이터]**. `Enl`은 게임 레플리카 계층의 이름으로 쓰입니다([02](02_replica_model.md)).

## 5. 웹 포팅 관점

- pia 세션·전송·호스트 이전은 **재현 대상이 아닙니다.** 브라우저 P2P(WebRTC)로 같은 구조를 만들 수도 있지만, 원본에도 권한 서버가 없어 호스트 이전·신뢰성 문제가 생깁니다. 웹은 **WebSocket(또는 WebTransport) 중계 서버 + 서버가 세션 마스터 역할**을 맡는 구성을 권합니다([06](06_web_port.md)).
- NPLN 매치메이킹은 방 목록·티켓 수준의 단순 HTTP API로 대체합니다. 원본 프로토콜과의 호환은 목표가 아닙니다.
- 세션 마스터가 바뀌어도 게임 상태가 이어지려면 `SessionMasterOrEvent` 레플리카 상태를 새 호스트가 이어받아야 합니다. 서버가 마스터를 맡으면 이 문제가 없어집니다.

## 11. 미확정과 추가 근거

| 항목 | 이유 | 필요한 근거 |
|---|---|---|
| 다음 호스트 선택 규칙 | **해소 [판독]** — §3.2.2: 구현+0xb8 주소 제외, 항목 +9(u8) 최소 스테이션. 남은 것: +9 값의 뜻, 메시 객체가 NetFacade인지 런타임 확인 | 항목 +9 writer |
| 신뢰 전송 윈도·재전송 주기, 패킷 최대 크기 | **해소 [판독]** — §3.1.1: 창 128 패킷, 재전송 = 33 ms + 1.4 × 최대 RTT, ACK·제어 33 ms 간격, 버퍼 1,440 B. vtable 주소 정정. 남은 것: RTT 함수 단위, 재전송 횟수 상한·끊김 판정 | 0x71007e74d0/0x71007e7540, 재전송 횟수(+0x14) reader |
| 메시에서 중계 경로 사용 조건 | `SessionRelayRouteManager` 미판독 | 해당 클래스 |
| Gamesync Referee의 결과 검증 내용 | 미판독 | `GamesyncReferee*` 문자열 참조 함수 |
