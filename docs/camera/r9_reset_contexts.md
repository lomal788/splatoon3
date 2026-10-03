# 카메라 리셋 호출과 모듈 포즈 적용(r9, 2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 원본 24e4bc8은 CameraModule 저장 포즈가 유효할 때 수평 방향으로 카메라를 리셋한 뒤 장치 방향별 피치 오프셋을 적용합니다. **Y 버튼 전용 함수로 단정하지 않습니다.** 설정 반영 메시지와 Lobby 메뉴 전환 메시지가 같은 함수를 부르는 실제 경로를 찾았습니다. 전체 고정 질문의 모든 상황 의미는 남아 조사중입니다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3(v0), main을 0x7100000000에 로드한 주소입니다. 아래 축약 주소에 이 base를 더합니다. 원본은 읽기 전용입니다.

- 기존 재사용: analysis/decomp/camera/batch1.c(24e4bc8/24d6598), camui_batch3.c(2470bc0), analysis/decomp/player/player_phase.c(2472c4c), player_components_vt.c(234f518/2353a18).
- 신규: analysis/decomp/r9_camera/reset_contexts.c(2f3cebc/1254324), reset_message_sources.c(2dc14fc/2dcf9b8/2e041e8).
- 실행: web/tools/r9_camera_reset_module_emu.py와 analysis/completion/r9/camera_reset_module_emu.json.

## 3. 진입점과 전체 호출 흐름

[판독] 직접 BL 전수 조회에서 reset24d6598의 caller PC는235050c,24715e0,2472ccc,249d960,24b1e9c,24d9c80,24e4d0c입니다.

| 진입 | 원본 조건·구체적 상황 | reset 인자와 이후 동작 |
|---|---|---|
| 234f518, message6c2b6a0e | 다른 SplPlayer의 사망 포즈 수신; r9_lifecycle 근거 재사용 | (C,1,0,B34), 수신 포즈 보간 시작 |
| 2470bc0 | Bf60에 등록된 state 동기화 callback, 읽기 mode3과 type2 하위 분기; 전체 네트워크는 범위 밖 | mode3은(C,1,0,B538) 뒤C16c=B544; type2 재시작 하위 경로는 B34 |
| **2472c4c** | PlayerBehavior slot15의2353a18→실제player setup 함수 | **(C,0,1,B34)**; slot15의 상위 lifecycle 공급 시점은 추가 연결 필요 |
| 249cb60 | 재시작 PlayerRestartType | cWarp_CameraNoReset3/cPlayGamePadRecorder6에서는 생략, 그외 기존 조건; 방향B34 또는cFirst의 시작방향−180° |
| 24b1ae0 | DeathFall 및 cVanish4 재시작 | 기존B34 방향 reset |
| 24d9ae8 | 수신 카메라 ec 종료, 일반 메인 복구 | (C,1,0,B538) 뒤C16c=B544 |
| 24e4bc8 | module M140 유효; 아래 두 실제 메시지 진입 | (C,0,0,moduleQuat의XZ방향) 뒤 피치·gyro오프셋 설정 |

정정(2026-10-03): 기존 §7은2472ccc를24719d4에 귀속했으나 **2472c4c에 별도 prologue**가 있습니다. 이미 정확한 player_phase 디컴파일이 있어 이를 재사용했습니다. 잘못된 함수 경계 때문에 상황 이름을 추측하지 않습니다.

[판독] 234f518의 **6c2b6a28** case가B+a878의24e4bc8을 부릅니다. 새로운2f3cebc는 현재 플레이어 배열G+a8/G+b0를 순회해 유효 액터에 이 메시지를 큐3e0db84로 보냅니다. 앞에서는 구성값을 전역58e2dc0의 객체에 복사합니다. 이 함수의 pointer는569e0a8에 있으며 상위 클래스·UI 동작 전체는 미분석입니다.

[판독] camera receiver2355d74의 **41cc9200** case도24e4bc8을 부릅니다. 새로운2dc14fc/2dcf9b8/2e041e8이 조작 플레이어의 ActorID로 이 메시지를 보내고 `Lobby_MenuMode_00`/`Lobby_ListFriend_00`를 다룹니다. 메뉴 UI 자체는 이번 범위 밖이므로 송신→카메라 경계만 확인했습니다. 이 메시지를 Y 버튼과 동일시하지 않습니다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 | 필드 | writer/reader |
|---|---|---|
| M=(*(*5790ef8)+e8), CameraModule | 140byte 유효,144..14c translation,150..15c quaternion(x,y,z,w) | M의 live 저장 producer 추가 필요/24e4bc8 |
| C=PlayerCamera | 1968 Behavior→108 B | 기존 factory/24e4bc8 |
| B=Player 본체 | 544 정규 피치 | 기존 플레이어/24e4bc8→C16c |
| I=*(*5790f50) | 164bit2: d0상태 또는20상태 선택, 선택된 상태17dbyte | 기존r8입력/24e4bc8 |
| C | 15f0 슬롯:unsigned<2면0/1, 그외0 | 기존선택/24e4bc8 |
| C | 15f4[2] yaw오프셋,15fc[2] pitch오프셋,1604[2] 이전pitch | 24e4bc8 선택슬롯만 갱신 |
| C | 15e8 피치 bias,1c8 gyro gain | 기존reset설정/24e4bc8 |
| C | 168=.2;14f8/1504/150c=0 | 24e4bc8 |

[판독:기존 재사용] PlayerRestartType 정보349fe34는 Respawn0/First1/Warp_CameraReset2/Warp_CameraNoReset3/Vanish4/CoopZombie5/PlayGamePadRecorder6입니다. 원문 “추정” 표기는 이 근거로 정정하며 새 성과로 계상하지 않습니다.

## 5. 상태 전이와 전체 수명

M140==0이면 카메라 전체를 그대로 반환합니다. 유효하면 방향 reset 후B544를C16c로 복사하고 장치별 피치를 선택 슬롯에 저장합니다. module valid의 생성/갱신/종료 전체는 아직 연결되지 않았습니다. reset 자체의 감도 재적용과 rig 초기화는 기존 §6.3/§7 근거를 재사용합니다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행] f32 연산 순서를 유지합니다. quaternion을 이번 함수에서 재정규화하지 않습니다. original1254324는34행렬의 translation/열벡터를 출력으로 재배열합니다.

```text
rx = f32(f32(z*f32(x+x)) + f32(y*f32(w+w)))
rz = f32(f32(1-f32(x*f32(x+x))) - f32(y*f32(y+y)))
length = sqrtf(f32(f32(f32(rx*rx)+0) + f32(rz*rz)))
dir = (rx,0,rz); if length>0: dir *= f32(1/length)
reset(C,0,0,dir)
C16c = B544
s = selectedInputState(I164 bit2 ? I+d0 : I+20)
base = s17d==1 ? -65 : -75
v = f32(base-C15e8)
lo = s17d==1 ? -120 : -45
v = v<lo ? lo : min(v,45)
j = uint(C15f0)<2 ? C15f0 : 0
C15f4[j]=0; C15fc[j]=v; C1604[j]=v
C168=.2; C14f8=C1504=C150c=0
```

정정(2026-10-03): Ghidra가24e4de4를 unreachable로 제거했지만 원본은 **FMIN v,45**를 실행한 뒤 하한을 고릅니다. 일반 bias에서는 상한이 안 걸려도 원본의 상한을 생략하지 않습니다. 유한 C1c8에 ±0을 곱해base에 더하는 실제 명령은 그대로 판독했으며 실험은 유한값만 사용했습니다. NaN·Inf의 별도 전파 검증은 하지 않았습니다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

사망 메시지6c2b6a0e는 [r9_lifecycle.md](r9_lifecycle.md)의 포즈/버퍼 수명과 연결됩니다. 다른 두 메시지는 camera reset을 호출하며 reset 함수 자체가 화면·음향 자산을 직접 방출하는 근거는 없습니다. 메뉴 메시지의 UI 연출은 분석 범위 밖입니다.

## 8. 다른 기능과의 상호작용

6c2b6a28 handler는 reset 후 B1058==0이면 Phive 이동 상태를 복구하는 경로로 갑니다. 이 후반 전체를 이번 emu에서 실행하지 않았습니다. state 동기화 serializer는 call edge/branch만 판독하고 범위 밖 네트워크 payload 동작으로 확장하지 않았습니다. main 복구 경로는 기존 snapshot/수신 종료 결과를 재사용합니다.

## 9. 웹 포팅 구조와 구현 순서

카메라 reset은 재시작·수신 종료·입력 구성 적용처럼 진입 이유별로 isRestart와세번째 인자를 보존합니다. module pose reset에서는 원본 방향을 reset에 넘긴 후 정규 피치를B544로 복구하고, 선택된 gyro 슬롯의오프셋만 덮습니다. 피치 clamp의 상한45와 장치별 하한을 유지합니다. M의live 저장 시점은 근거가 확보되기 전 임의로 Y키 포즈와 묶지 않습니다. 웹 코드/impl은 수정하지 않았습니다.

## 10. 검증 코드·실행 결과·기대값

명령 `.venv/Scripts/python.exe web/tools/r9_camera_reset_module_emu.py`.

- 활성2048, module무효64,28672 f32 독립 비트 일치, reset경계2048. slot0/1/2/FFFFFFFF·입력 상태0/1/2·164bit2 양쪽.
- 상한45적용211·하한적용1020 사례 포함, quaternion XZ 방향·피치·선택 슬롯·세 reset accumulator 모두 일치.
- null/자동페이지/fault/PLT스텁0. **24d6598 reset 전체만 경계로 캡처**했으며 C15e8/C1c8은reset후 입력값으로 공급했습니다. matrix재배열1254324/제곱근/정규화/장치 선택/후반 store는 원본입니다. 전체 화면 실행은 아닙니다.
- 실패: 최초 `PUC.call(max_insn=...)`는TypeError; 실제인자 `count=`로 수정 후 성공. commands.md에 명령 실패도 기록했습니다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

고정 player_camera:L389 전체 질문은 **조사중** 유지합니다. 새로운 exact 함수경계·두 메시지 공급과 모듈 적용식은확정했지만 setup slot15의 상위 actor lifecycle 연결과 module140/150의 live 저장 시점이 남았습니다. 다음: Behavior slot15 실제dispatch→2353a18, module실제VT와140/150writer, 설정객체569e0a8의상위caller. 이미해소된reset재시작enum/사망snapshot은재분석하지 않습니다. 직접BL검색에caller가없다는것은virtual호출이없다는증명이아닙니다.
