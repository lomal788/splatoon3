# 카메라 수신·수명 추가 분석 (r9, 2026-10-03)

## 1. 기능 개요

사망 시 저장한 카메라 위치·주시점·조준 방향을 다른 플레이어의 PlayerCamera에 넘깁니다. 메시지를 받은 카메라는 기존 일반 리그 계산 결과를 목표로 삼고 저장한 위치에서 점차 이동합니다. 이 수신·보간·다른 플레이어 스냅샷 공급·대체 포즈 선택은 [판독]+[실행]입니다. §7의 원본 생산자를 새로 연결했습니다. 실제 솔로 사망 사건과 device posture에 따른 최종 픽셀은 실행 범위 밖입니다.

## 2. 분석 대상

Splatoon 3(v0), `main.reloc.img`의 원본 명령. 기존 디컴파일 `analysis/decomp/player/player_components_vt.c`(234f518), `camera/batch1.c`(24e5f6c), `camrest/cam_main_full.c`(24d9ae8), `r8_camweapon/death_camera.c`(2676548)를 재사용했습니다. SHARED/FUNCS/decomp_index를 확인했고 수신 메시지의 두 case와 이 보간 블록은 기존 확정 기록에 없었습니다.

## 3. 진입점과 호출 흐름

[판독] 2460808의 param6 → 24e5f6c(C, playerNo) → C1698 핸들. 조건은 `playerNo<8`, 본체 B1058==0, `playerNo!=자기 Actor+798`, 선택 플레이어 관리 객체+ a74==0입니다. 전역 G=*5791bd0의 G+b0 플레이어 포인터 배열에서 항목+8의 액터 핸들을 복사합니다. 유효 범위는 G+a8, 그 밖은 58bfb80 빈 핸들입니다. 이는 다른 플레이어의 액터를 연결하는 경로로, 전용 DeadCamera 액터 이름을 찾아야 한다는 이전 추정은 정정합니다.

기존 송신 조건(24d9ae8, T+8 대기 시작 프레임)은 재사용: 살아 있는 핸들, C16ee==0, 1<=B d60<B d68일 때 0x68 바이트 메시지를 한 번 보내고 C16ee=1. 새 원본 수신 234f518의 case 6c2b6a0e는 해당 SplPlayer의 `B+a878` PlayerCamera를 갱신합니다. case 6c2b6a0f는 수신 상태를 해제합니다.

## 4. 구조체·필드

기준 C=수신 PlayerCamera, M=메시지입니다.

| 필드 | writer / reader | 의미 |
|---|---|---|
| C1698 / 16a0 / 16a8 | 24e5f6c → 24d9ae8·24e50c0 | 다른 플레이어 액터 핸들 / 슬롯 / 세대 번호 |
| M40..48 / M4c..54 | 기존 송신 → 2350530..57c | Pos / At |
| M58..60 / M64 | 기존 송신 → 2350518..52c | ShotDirXZ / pitch 누적값 |
| C16ed | 2350514 → 24df2d8 | 수신 첫 프레임 대기 |
| C16ec | 메인 24d9ae8의 `ed!=0` 경로 → 다음 틱 | 수신 보간 활성 |
| C16b0..16c4 | 수신 복사, 24df318..3b8 | 현재 보간 Pos / At |
| C16c8..16dc | 수신 복사, 24df2ec..314 | 목표 Pos / At |
| C16e0 / 16e4 / 16e8 | 수신에서 0 → 24df3bc..3f0 | 진행 값 / 추종 비율 / 프레임 수 |
| C16ef | reset24d6598의 arg1&1 → 24dd3b0 | 목표 고정 여부 |

[판독] 원문에서 리플렉션으로 부른 23a749c는 메시지 기본 필드 초기화(0x14바이트)입니다. 실제 필드 방문은23a74b0, 복사는23a7460입니다. 2026-10-03 정정: 주소가 기능을 잘못 가리켰습니다.

## 5. 상태 전이·수명

[판독]+[실행] 수신에서는 reset(C,1,0,B34) 뒤 ed=1, 현재/목표 Pos·At을 모두 M에서 복사, 조준 방향과 pitch를 복사하고 e0/e4/e8을0으로 둡니다. 카메라 목표 기초점 C150..158은 Actor translation + Actor up축×0.6입니다. 그 틱 ed 경로는 목표를 일반 리그 출력으로 갱신하고 rate0이므로 보낸 위치를 그대로 출력합니다. 메인 후단은 ed를 ec로 옮겨 다음 틱부터 보간합니다.

6c2b6a0f는 ec/ed 두 바이트와 ef를 0으로 만들며 ee나 저장 위치를 지우지 않습니다. 자기 B1058==0인 ec 경로 역시 상태를 지우고 자기 B538 방향/B544 피치로 리셋합니다. 사격장 1인에서는 다른 플레이어 핸들을 실제로 받는 사건을 이 실행으로 검증한 것은 아닙니다.

## 6. 계산식·순서

[판독]+[실행] native Pos/At=일반 리그가 그 틱에 먼저 출력한 값입니다. ef==0이면 목표를 native Pos/At으로 갱신합니다. ef!=0이면 수신 이후 저장한 목표를 유지합니다. 위치 3축·주시점 3축을 각각 다음 f32 순서로 계산합니다.

```text
frame += 1
if !ef: target = nativePosAt
for i in 0..5:
    delta = f32(target[i] - current[i])
    current[i] = f32(current[i] + f32(rate*delta))
progress = f32(progress + f32(rate*f32(1-progress)))
rate = f32(rate + f32(f32(1-rate)*0.01))
output Pos/At = current
```

0.01의 명령 비트는 0x3c23d70a. 위치 보간에 FMA가 없으며, 그 틱의 이전 rate로 위치를 계산한 뒤 rate를 올립니다. 초기 rate0에서 첫 출력이 수신 위치인 순서를 보존합니다.

## 7. 화면 연결

일반 C88 포즈는 기존 1016d0c→Spectator→CameraModule 사슬(r8 player_camera§6.7.3)을 재사용합니다. **2026-10-03 추가 정정**: interface58bc540 공급자가 미확정이던 이유는 PlayerCamera 부 vtable5633a70의 뒤에 붙은 **별도 객체 vtable5633a90**을 같은 카메라의 부 인터페이스로 읽었기 때문입니다. 실제 생산자는 아래와 같습니다. 이전 미확정 기록은 이 추가 근거로 해소합니다.

[판독]+[실행] `C primary VT5633960+38=24e6184`가 **S(size0xc8, VT5633a90)**를 할당하고 `C1968=Behavior`의 e8/f0 원형 리스트에 S+8을 등록합니다. 원본 RTTI24e6e48은 토큰58bc540 및 base5802438을 인정합니다. 토큰의 문자열 이름을 새로 붙이지 않고 원본 객체/주소로 식별합니다.

```text
수신 PlayerCamera 일반 리그→수신 Pos/At 보간→C88 최종 논리 포즈
24d9ae8 후단24df9f0→24dffd8
    S상태.active = C16ec
    S상태.modeNonzero = (C1878 != 0)
    S상태.progress = C16e0
    S상태.Pose = C88의 실제 필드 청크
Actor Behavior 슬롯18 앞 리스트 slot28→24e7018: back→front
Actor Behavior 슬롯19 앞 리스트 slot30→24e7070: front→back
연결 Actor의 component24→Behavior 목록→2676548 상태
    active!=0 → 메인24df8bc..91c가 Pose를 자기 C+d4에 복사
getter24e50c0: 유효 연결+active이면 C+d4, 나머지 C88
→ 기존 Spectator/포저(CameraModule) 입력
```

`F=*59a37c8+4c8`의 바이트를 a,b,c로 두면 `a==2 && b!=254 && c!=254 && (b==0 || (b==1 && c==0))`일 때 **writer는 front(S18), reader는 back(S6c)**를 사용합니다. 나머지는 writer back, reader front입니다. 원본은 읽는 쪽과 쓰는 쪽을 반대로 선택합니다. Player 슬롯19의 일반 프레임 경로는 back에 쓰고 다음 슬롯18 앞의 리스트 교환에서 front로 옮기는 순서를 보존합니다. 같은 그룹 액터의 병렬 실행을 임의 순서로 치환하지 않습니다.

Pose는 S상태+8, 길이0x4c입니다. 복사 구간은 Pose+[0,2d),+[30,45),+[48,4c)이고 패딩3바이트씩을 memcpy로 확대하지 않습니다. S+c1/c0은 각각 back→front/front→back 요청이며 교환 후0입니다. reset24e7004는 front/back의 활성·mode 두 바이트와 progress를0으로 만들지만 Pose 저장값은 보존합니다.

## 8. 다른 기능과 상호작용

수신 보간 중에는 일반 붐·리그 출력 뒤에 위치/주시점을 덮어씁니다. reset의 첫 인자는 ef 고정과 연결 액터 해제에도 관여합니다. 메시지6c2b6a0f 해제는 위치 저장값 초기화와 다릅니다. 네트워크 serializer 전체는 이번 1인 범위 밖이므로 추적하지 않았습니다.

## 9. 웹 반영 필요

`impl/camera.md`의 사망 포즈 전환 상태는 별도 기록해야 합니다. 추천 변수명(원본 이름 아님): `linkedPlayerHandle`, `receivedPose`, `blendTargetPose`, `receivedPoseRate`, `freezeReceivedTarget`. 원본 순서·f32 계산·clear가 저장값을 지우지 않는 성질을 유지합니다. 다른 플레이어 스냅샷의 front/back 선택·교환과 논리 포즈 getter를 구현 근거로 사용할 수 있습니다. device posture/최종 픽셀 질문은 별도 미확정입니다. 웹 코드와 impl 문서는 수정하지 않았습니다.

## 10. 실제 검증·명령

`web/tools/r9_camera_death_emu.py` → `analysis/completion/r9/camera_death_emu.json`:

- 원본 234f518 dispatcher+RTTI+수신 복사1024사례, 22528필드 비트 일치.
- 해제 원본 dispatcher3사례: ec/ed/ef만0, ee=77 보존.
- 원본24dd3a4→24df40c 블록2048사례(ef0/1), 28672필드 비트 일치.
- 불일치0, fault/null/auto-page0. reset24d6598과 rig setup24d6e84만 경계 스텁. 전체 프레임·렌더러·실제 솔로 사망 사건 실행으로 확대하지 않습니다.

`decomp_index.py 234f518/24e5f6c/2676548 --no-build`, `func_lookup.py 234f518`, `disasm.py 2350470 -n104`, `disasm.py 24dd3a4 -n105`, `disasm.py 24df2d8 -n105` 실행. 이미 디컴파일된 주소를 새 full_decomp로 다시 만들지 않았습니다.

원본 새 `r9_camera_snapshot_emu.py` → `camera_snapshot_emu.json`: factory1, publication1024, 실제 Behavior 리스트 디스패치 교환1024, actor reader2048, 메인 대체 복사1024, getter 선택1024, reset3 모두 비트/포인터 일치. 48개 frame-context 조합, 무작위 Pose 바이트와 활성0/1·mode값·progress 비트 공급. malloc1·threadValid1024·handleLookup1024만 경계이며 snapshot RTTI/필드/버퍼 선택/대체 복사/유효 세대·actor phase 검사는 원본 실행. fault/null/auto-page0. 전체24d9ae8·프레임 스케줄·렌더러·하드웨어 posture·실제 솔로 사망 사건을 실행했다고 주장하지 않습니다.

`func_lookup.py 24e7004/7018/7070`은 직전 deallocator24e6fa0를 가리켰습니다. disasm으로 실제 leaf 시작을 확인하고 `full_decomp.sh analysis/decomp/r9_camera/snapshot_exchange.c 0x71024e7004 0x71024e7018 0x71024e7070`으로 새3함수 디컴파일 성공. 기존 index의24dffd8/24e6184/2676548/24e50c0 및0ffdaa4/0ffdb6c는 재디컴파일하지 않았습니다.

## 11. 미확정·다음 근거

- 원래 사망 카메라 질문의 **받는 Actor·핸들 writer·수신/해제·사망 논리 포즈 식·공급자·getter**는 §§3~7의 새 근거로 해소했습니다. 원본에서 1인 연습 중 다른 플레이어 대상 연결 이벤트가 실제로 발생한다는 뜻은 아닙니다. 송신/프레임 그래프·포저의 기존 확정은 재사용했고 신규 실행 수로 세지 않았습니다.
- device posture5997898: strict GOT reference280개와 direct page ADRP6605개 검사에서 대상 저장을 찾지 못했습니다. window8 xref의317e480은5916898을 가리키는 오검출이라 제외. 결과 `camera_posture_refs.json`·`camera_posture_direct_refs.json`; 이 제한된 static scan만으로 전역이 런타임0이라고 확정하지 않습니다. 다음: Projection 기본 posture의 초기화·다른 모듈 공급자·M2ac writer. 고정 player_camera:L226의 최종 화면 질문은 조사중 유지합니다.
