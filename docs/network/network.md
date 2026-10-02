# 네트워크 동기화 (대전) — 목차와 요약

Splatoon 3 v0 main NSO의 대전 네트워크 동기화 구조를 정리한 문서 묶음입니다. 웹 포팅에서 브라우저와 서버가 무엇을 주고받아야 하는지 판단하는 근거로 씁니다. 작업 지침은 [../../분석.txt](../../분석.txt), 공용 자료는 [../README.md](../README.md)를 참고하세요.

상태: **분석 진행**(핵심 구조·직렬화·비트 패킹·헤더·GameFrame 동기(시계 = pia ClockProtocol)·시드 배포 경로·Rule 값 확정, PlayerNetState 필드 출처 전부 판독, 필드 의미 대부분 확정(3차), pia 신뢰 전송 창·재전송·다음 호스트 규칙 판독). 웹 구현 없음.

## 문서

| 문서 | 내용 |
|---|---|
| [01_layers_and_session.md](01_layers_and_session.md) | 라이브러리 계층(pia 6.20.1·NPLN·pead·Enl), 세션·메시·호스트 이전·LAN, 매치메이킹 gRPC |
| [02_replica_model.md](02_replica_model.md) | 레플리카(넷 액터) 데이터 설정, SenderPolicy·Protocol, 이벤트 큐, 송신 주기(4프레임), 송신 권한 검사, 수신 처리 방식 |
| [03_serialization.md](03_serialization.md) | 넷 타입 등록 표(348종), vtable 슬롯, 비트 writer API, 양자화 공식(위치·방향·속도), 디코드 |
| [04_player_state.md](04_player_state.md) | `spl::PlayerNetState` 546비트 필드 표, 하위 상태 variant, 송신 조건, `spl::PlayerNetControl` 지연 추정·재생 버퍼 |
| [05_events_combat.md](05_events_combat.md) | `spl::PlayerNetEvent::*` 82종 비트 배치, 탄 복제, 피격·데미지 권한(AttackEvent/DamageReason/TroubleDie), 도색·게임 흐름 이벤트 |
| [06_web_port.md](06_web_port.md) | 웹 포팅 구조(서버 권한 범위, 메시지 목록·주기, 의사코드, 이름 대응표), 검증 기대값 |

## 산출물·도구

| 경로 | 내용 |
|---|---|
| `analysis/network/nettypes.tsv` | 넷 타입 348종: 종류(event/state), 이름, 객체 크기, 비트 min/max, hash32, 등록 엔트리, 생성자, vtable, 슬롯 함수 주소 |
| `analysis/network/bitlayout.txt` / `.json` | write 함수 직선 판독으로 뽑은 필드별 (this 오프셋, 비트 수, 헬퍼) — 260종은 합계 = 등록 비트 |
| `analysis/network/netparams.json`, `netparams_summary.txt` | 액터 팩의 `game__NetParam` 72개 + ActorParam `Net` 참조 |
| `analysis/network/bootup_net.json` | Bootup 팩 `Net/*.game__NetEnlReplicaParam`·`NetEnlValueParam` 41개 |
| `analysis/network/hashuse.tsv`, `hashuse_byfunc.txt` | 타입 hash32 상수를 만드는 코드 위치(송수신 함수 찾기용) |
| `analysis/network/vtable_got_users.tsv` | 타입 vtable GOT 항목과 그걸 읽는 코드(스택에 이벤트를 만드는 송신·수신 함수) |
| `analysis/network/verify_result.json` | `network_verify.py` 결과 |
| `analysis/decomp/network/net_core.c`, `net_player.c`, `net_send.c` | 즉석 디컴파일 |
| `analysis/decomp/network/net_player_send.c` | 플레이어 넷 송신 0x7102483134 전체(28 KB, `player_bigdecomp.sh`) |
| `analysis/decomp/network/net_sync.c`, `net_sync2.c`, `net_sync3.c`, `net_valueelem.c`, `net_pia_host.c` | GameFrame·시작 시각·시드·OnlineVersusSetting·PlayerNetControl 생성자·도색 송신·pia 신뢰 전송/호스트 이전·값 요소 |
| `analysis/network/bitpack_result.json`, `clock_result.json` | `network_bitpack.py`, `network_clock.py` 결과 |
| `analysis/network/netrest_result.json` | `network_rest_verify.py` 결과(3차: Rule 열거, SuperHook +0x188, 시계 getter, pia GetClock, 로비→대전 설정 복사, 1회성 동작 종류 표) |
| `analysis/decomp/network/netrest_a.c`, `netrest_b.c` | 3차 디컴파일: 슈퍼후크 서브액션, 클론·ClockProtocol 연결, pia 신뢰 창 갱신·재전송, NetFacade 다음 호스트, 로비 설정 복사, Rule 변환 |
| `web/tools/network_*.py` | 아래 표 |

| 도구 | 용도 |
|---|---|
| `network_typereg.py` | 등록 함수(0x71012f8808/0x71012f8db8) 호출 인자 추출 (`--target`, `--json`) |
| `network_typetable.py` | 위 결과 + 생성자→vtable→슬롯 표 → `nettypes.tsv` |
| `network_bitlayout.py [정규식]` | write 함수 필드 비트 배치 |
| `network_netparam_scan.py` | 전 액터 팩 NetParam 수집 |
| `network_constscan.py <hash>` / `network_hashuse.py` | 32비트 상수 생성 위치 |
| `network_fstart.py <주소>` | BL 대상·포인터 집합으로 함수 시작 추정(`disasm.py --func`보다 큰 함수에 강함) |
| `network_emu.py` | 직선 레지스터 추적 소형 에뮬레이터(정적 등록 인자 판독용) |
| `network_uc.py` | **unicorn으로 원본 함수 실행**(write/read 훅) |
| `network_verify.py` | 전 타입 비트 합계·양자화 재구현 대조·왕복·variant 매핑·지연 추정기 시뮬레이션 |
| `network_bitpack.py` | **원본 비트 writer**(0x7103582678 등) 실행: LSB 우선 패킹 대조, PlayerNetState 바이트열, 이벤트 헤더 값 요소(23/4비트) |
| `network_clock.py` | GameFrame 델리게이트(공유 시계→프레임 0x710126d1fc, 대기 0x710126d2ac, 로컬 0x710126d040) 실행 대조 |
| `network_rest_verify.py` | 3차 잔여 항목 원본 실행 6건(PLT 즉시 반환 훅 추가한 `network_uc` 하네스) |

unicorn은 이번 작업에서 `.venv`에 설치했습니다(`pip install unicorn`).

## 확정한 핵심 동작 (요약)

1. **P2P 메시 + 세션 마스터** — 대전은 pia(6.20.1) 세션 위 P2P입니다. 전용 게임 서버는 없고, NPLN(gRPC) 서버는 매치메이킹·ICE/TURN 서버 할당·인증만 맡습니다. 세션 마스터(호스트)는 pia가 정하고 이전(migration)됩니다. **[판독/데이터]** → [01](01_layers_and_session.md)
2. **레플리카 설정은 데이터** — 넷 액터는 `game__NetParam`(액터 팩)·`game__NetEnlReplicaParam`(Bootup `Net/`)으로 정의합니다. 요소(상태 Unreliable/Reliable), 이벤트 큐(기본 32), SenderPolicy(Invalid/PlayerIdBased/SessionMasterOnly/Atomic/Anyone/SessionMasterOrEvent). 일반 탄은 넷 액터가 아닙니다. **[데이터/판독]** → [02](02_replica_model.md)
3. **상태는 4프레임마다(15 Hz), 이벤트는 발생 프레임에 큐잉** — GameNet 송신 작업(0x710129193c)이 `프레임 % 4 == 0` 플래그를 세우고, 플레이어는 이 플래그가 켜진 프레임에만 `PlayerNetState`를 씁니다. 이벤트는 송신 시점 GameFrame(`*0x710580e758`+0x148, 23비트)과 소유자의 LifeNumber(0~15, 4비트)를 payload 뒤에 붙이고, 수신측은 LifeNumber가 현재와 다르면 버립니다. **[판독/실행]** → [02](02_replica_model.md)
3-1. **GameFrame은 기기 간 동기** — 대전 시작 시 각 스테이션이 원하는 시작 시각을 내고 세션 마스터가 최댓값을 `VersusSetting` 값으로 확정, 모든 기기가 `frame = (sharedMs − startMs)/1000·60`을 매 갱신 다시 계산합니다(NetUtilFrameStarter 0x710126c02c, 델리게이트 0x710126d0ec). **[판독 + 실행(델리게이트)]**. 시계는 넷 관리자+0x60 객체가 매 프레임 pia `clone::ClockProtocol::GetClock()`(µs)에서 받아 ÷1000 한 ms 값 **[판독 + 실행]** → [02 §5.5·§5.6](02_replica_model.md#56-공유-시계--pia-cloneclockprotocol-판독--실행)
4. **자체 비트 직렬화** — 넷 타입 348종(이벤트 289, 상태 59)이 이름·hash·비트 수와 함께 등록되고 write/read가 필드를 비트 단위로 씁니다. 위치는 부호+16비트(±256, 1/256 단위 근방), 방향은 pitch/yaw 각도 양자화. 원본 함수를 직접 실행해 확인했습니다. 비트는 **LSB 우선, 바이트 정렬 없음**(원본 writer 실행 대조). **[실행]** → [03](03_serialization.md)
5. **PlayerNetState = 546비트 고정** — 위치·속도 2종·방향 2종·조준 방향·카메라 피치·HP·아머·스페셜 %·잉크·공중 프레임·발밑 잉크·1회성 동작 카운터(mod 8)·룰 오브젝트 값 + 3개 variant(Squid/Human, Jump/DokanWarp/RespawnLand, InkAction 13종) + 내장 SuperHook 하위 객체를 고정 길이로 패딩합니다. 44개 필드 전부의 송신측 출처(플레이어 본체·컴포넌트 오프셋)를 송신 함수 0x7102483134에서 판독했고, 3차에서 대부분의 게임 의미와 수신 적용 일부를 확정했습니다(남은 필드 7개 내외). **[실행/판독]** → [04](04_player_state.md)
6. **수신측 지연 보정** — `spl::PlayerNetControl`(0x7102658bb4)이 송신 프레임 스탬프로 지연 D를 추정(무수신 프레임마다 가중치 ×0.992, 수신 시 갱신), 2~5프레임 창 밖 초과분을 0.03 계수로 평활해 재생 지점을 고릅니다. **[판독]**, 의미 해석은 **[추정]** → [04](04_player_state.md)
7. **탄은 이벤트로 복제** — 발사자 기기만 `PlayerNetEvent::Bullet*`(위치·속도·부가값)를 보내고, 수신측은 같은 발사 함수를 "비소유" 플래그로 호출해 복제 탄을 시뮬레이션합니다. 송신 GameFrame은 탄 난수 시드(`mgr+0x120 + frame`)로만 쓰이고 경과 프레임만큼 앞당기는 보정은 없습니다. **[판독]** → [05](05_events_combat.md)
8. **피격 판정은 공격자 쪽** — 탄의 `spl:DamageHelper`가 `spl::AttackEvent`(+`DamageReason`)를 만들고, 각 기기의 같은 DamageHelper 복제가 소유자 번호가 맞는 AttackEvent만 처리합니다. 사망은 피해자 쪽 `PlayerNetEvent::TroubleDie`로 알립니다. 흐름은 **[판독]**, "HP 감소를 피해자 기기가 확정한다"는 **[추정]** → [05](05_events_combat.md)

9. **매치 공용 시드** — 탄 관리자(`*0x7105850620`) +0x124..+0x130 = 대전 설정 `RandomSeed0..3`, +0x120 = 13a+59b+71c+97d(초기화 0x71016e2fd4). 시드는 송신 권한 기기가 전역 xorshift128로 생성해 `spl::OnlineVersusSetting` 이벤트(+0x238..+0x244)로 배포하고(0x7102d5e478), 받은 로비 객체가 0x7102d60098에서 대전 설정(`G+0xd0` 묶음)의 +0xa4..+0xb0·Rule·Time으로 복사합니다 **[판독 + 실행]**. `G+0xd0 → G+0xc8`(게임이 읽는 쪽) 한 단계만 [추정] → [05 §3.1](05_events_combat.md)
10. **도색 이벤트** — 도색을 실행한 기기가 먼저 로컬 적용 후 `PaintRequest` 레플리카로 송신(0x7102c42330). **[판독]** → [05 §6](05_events_combat.md)

## 확정 수준 표기

[../README.md](../README.md#확정-수준-표기)와 같습니다: **[실행]** 원본 실행(여기서는 unicorn으로 main NSO 함수를 직접 실행), **[판독]** 코드 판독, **[데이터]**, **[추정]**, **[미확정]**. "재구현"은 파이썬으로 다시 짠 계산을 뜻하고 원본 실행과 구분합니다.

## 남은 미확정 (요약, 상세는 각 문서 11절)

3차([netrest])에서 해소: Rule 2/3/5 = 야구라/호코/트리컬러 [실행], +0x188 = 슈퍼후크 벽 부착 [실행], +0xa4 = 송신 writer 없음(항상 0)·수신은 LifeNumber 비교로 쓰러짐 중 상태 무시 [판독], 넷 관리자 시계 = pia ClockProtocol [판독+실행], OnlineVersusSetting → 대전 설정 복사(0x7102d60098) [판독+실행], 신뢰 전송 창 128·재전송 33 ms + 1.4×RTT [판독], 다음 호스트 = 항목 +9 최소 [판독], 원격 HP = 상태 +0x6c → PlayerDamage+0xee0 [판독], PlayerNetState 필드 의미 다수([04 §4](04_player_state.md)).

- `PlayerNetState` 남은 필드 의미: 속도 B(본체+0xfc), 방향 B(본체+0x198), 본체+0xcfc/+0xd08, 본체+0xb60/+0xb61, 그래플 대상 값, 야구라 플래그 뜻. 카운터 #21·#23·#25의 수신 재생 코드.
- 게임 설정 묶음 `G+0xd0 → G+0xc8` 복사 지점, `OnlineVersusSetting` 송신 기기 = 세션 마스터인지.
- ClockProtocol 내부 동기 알고리즘, `VersusStartClockEvent` 사용처.
- pia: RTT 함수 단위·재전송 횟수 상한·끊김 판정, 다음 호스트 항목 +9의 뜻, 패킷 헤더, 중계 경로 조건.
- 복제 탄이 도색 요청을 하는지, 자식 탄 시드(생성 시점 GameFrame)의 기기 간 차이 영향([bullet]/[paint]).
- LifeNumber(소유 넷 객체 +0x28) 증가 시점 — [respawn] 담당(SHARED.md 조율).
