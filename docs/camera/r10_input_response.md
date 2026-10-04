# 스틱 주축 스냅·yaw·피치 누적 원본 실행 (r10, 2026-10-03)

## 1. 기능 개요와 체감 동작

[판독]+[실행] 스틱의 작은 축을 누르는 주축 스냅, 길이 응답 곡선, yaw 속도 평활, 피치 속도와 누적각의 실제 f32 계산을 검증했습니다. 스냅은 작은 축을 줄인 뒤 **원래 벡터 길이로 다시 정규화**합니다. 내부 누산값 C188과 pow 지수는 서로 다릅니다. 마우스 픽셀을 스틱 속도로 바꾸는 규칙은 원본에 없으며 이 검증에 포함하지 않습니다.

## 2. 분석 원본·버전·자료 위치

Splatoon 3 v0, `extracted/exefs/main.reloc.img`, base `0x7100000000`. 아래 주소는 base를 생략했습니다. SDK `powf/logf/expf`는 `extracted/exefs/sdk.img`의 실제 동적 심볼 명령을 실행했습니다. SHARED/FUNCS와 `decomp_index.py 0x71024e0178 --no-build`로 중복 확인 후 기존 `analysis/decomp/camera/batch1.c`, `analysis/decomp/camrest/cam_main_full.c`, `analysis/r5_camweapon/input_24e0178.asm`를 재사용했습니다. 재디컴파일하지 않았습니다.

## 3. 진입점·호출 흐름

```text
기존 PlayerInput249f494 → 24a73b8 → B[a9c,aa0,aa4,aa8]
PlayerCamera24e0178
  0b5c..0bbc: gyro/수직 deadzone/입력 전환 조건 [판독]
  0bbc..0d78: 주축 스냅 + 길이 복구 [실행4096]
  0f38..1008: 길이 bias [실행2048]
  10bc..12a8: yaw 최대 속도·목표·평활 [실행4096]
  1674..1c30: pitch 최대 속도·평활·기울기·누적·clamp [실행2048]
  1c50..1cd0: gyro 꺼짐의 pitchAngleToP 및 out 보정 [판독:기존]
```

0bbc의 입력은 deadzone/gyro 각도 재매핑을 지난 값입니다. 1674의 입력은 그 틱의 선택 조건을 지난 값입니다. 네 구간을 각각 실행했으며 **전체24e0178·실제 사격장 프레임을 이어 실행한 것이 아닙니다**. 기존 반전·생산자 판독과 새 구간 실행을 구분합니다.

추가 `0874..1cd0` 연결 probe16건에서는 스틱 읽기→gyro 각도 재매핑→deadzone→실제24c99f0→bias→yaw 방향 회전→pitch 누적→gyro 꺼짐24e64f0까지 원본을 이어 실행했습니다. 기존 B4cc=IsEnableGyro writer(Save4000→249fac0)은 재사용합니다. 일치하는 gyro flag8건과 일부러 불일치시킨8건을 구분했고, 이 probe는 관측과 연결 확인이며 별도 독립식12,288건의 수에 더하지 않습니다. 최종 gyro 절대각/p 후단은 종료 PC뒤여서 검증 범위 밖입니다.

## 4. 구조체·필드·상수·타입

| 필드 | 확정 의미 | 원본 생산·소비 |
|---|---|---|
| Baa4/Baa8 | 원시 오른쪽 스틱 − 지난 반전 후 기록의 차이 | 기존24a73b8 / 0bcc..0c24 |
| C180/C184 | 위 차이를 .2로 필터한 두 상태 | 0be0..0c3c / 스냅 누산 |
| C188 | 스냅 누산 상태, 두 차감 후 각각 하한−1 | 0c28..0cd4 / pow 지수 선택 |
| C14f8/C14fc | yaw 속도 / 최대 속도 rad/f | 1278..12a4 |
| C1504/C1508 | pitch 속도 / 최대 속도 rad/f | 17e0..1830 |
| C150c | 누적 피치각 degree | 1bfc..1c2c / 24e64f0 |
| C1cc/C1c8 | 스틱 감도 k / 자이로 감도 kG | 기존 reset / 입력 |
| C15f0 | 2미만이면 선택 슬롯, 그 밖이면 슬롯0 | 원본 ldrsw+cmp / 경계 보정 |
| Controller17d | **정확히1**일 때 기준·양 경계에+10 | 17c8..18c8 |

문서의 짧은 소수 표기와 실제 비트를 구분합니다.

| 식에 쓰는 상수 | 원본 bits | 정확한 f32 값 |
|---|---|---|
| yaw 음수 k 계수(약1.6) | 3fcccccc | 1.5999999046325684 |
| slow yaw 양수 k 계수(약1.8) | 3fe66664 | 1.799999713897705 |
| slow yaw 음수 k 계수(약.96) | 3f75c290 | .9600000381469727 |
| pitch 음수 k 계수(약.8) | 3f4ccccc | .7999999523162842 |
| degree→rad | 3c8efa35 | .01745329238474369 |
| rad→degree | 42652ee0 | 57.2957763671875 |

## 5. 상태 전이와 누산값 수명

[판독]+[실행] gyro 모드에서는 C188=0이며 이 구간에서 C180/184를 갱신하지 않습니다. 일반 모드에서는 차이값 평활→C188의3 추종→차이값 곱에 따른 차감→대각 입력에 따른 차감 순서입니다. 각 차감 뒤 하한−1을 저장하고, 그 뒤 pow에 넘길 때만 max(C188,0)을 계산합니다. 저장값을 매 틱0이상으로 제한하면 원본과 달라집니다.

수직 입력0은 C15d8 하나를 보고 모든 구간에서 강제로 쓰는 규칙이 아닙니다. 원본0b8c..0bb8은 `abs(y)<(C15d8?0:.15)` 또는 `(B4cc!=0 && global58bbb80==0)`일 때 y와|y|를0으로 만듭니다 [판독]. B4cc는 전환 펄스가 아니라 현재 IsEnableGyro입니다. 4ce/4cf가 각각 방금 꺼짐/켜짐입니다(기존 근거 재사용). probe의 불일치 flag는 실제 일반 프레임 상태라는 주장이 아닙니다.

reset·gyro 변경으로 피치 누산을 비우는 경로는 기존 `player_camera.md` §5/§6.9와 r9 reset 근거를 재사용했습니다. 이번 원본 실행은 임의 유한 pre-block 상태를 공급했으며 각 상태가 실제 Lby에서 발생하는 빈도를 입증하지 않습니다.

## 6. 계산식·조건·원본 연산 순서

모든 add/sub/mul/div는 각 단계 f32입니다. x,y는 스냅 이전 signed 입력, X=|x|,Y=|y|, a,b는 C180/184입니다.

```text
a += .2*(Baa4-a); b += .2*(Baa8-b)
c = X*Y
if c > .001: c *= 1-abs(X-Y)/(X+Y)
E += .1*(3-E)
E = max(E + sqrt(abs(b*(-a)))*(-3), -1)
E = max(E + sqrt(c)*bitsBF333333, -1)   # 약 -.7
exponent=max(E,0)
before=sqrt(X*X+Y*Y)
if X>Y: y*=powf(1-(X-Y)/X, exponent)
else if Y>0: (-x)*=powf(1-(Y-X)/Y, exponent)
after=sqrt(y*y+(-x)*(-x))
if after>0: (-x,y)*=before/after
m'=bias(sqrt(x*x+y*y), gyro?.4:.8)
```

원본은 `1-(major-minor)/major`를 사용합니다. 수학적으로 같은 `minor/major`로 바꾸면 비트가 달라질 수 있습니다. 또한 스냅 이전 길이를 복구하므로 작은 축 억제를 입력 벡터 전체 감속으로 해석하지 않습니다.

yaw는 `player_camera.md` §6.4의 구조를 따르되 아래 순서와 §4 비트를 사용합니다.

```text
base=4+k*(k<0?bits3FCCCCCC:3)
slow=bits4019999A+k*(k<0?bits3F75C290:bits3FE66664)
if !C15d9: base+=w*(slow-base)
if base>C156c: base+=(C156c-base)*(C1550*C1764)
degrees=Bf34 in {2,3,4}?slow:base
term=(-x)*fovRatio
if term*C14d4<0: term*=1-abs(C14d4)
rad=degrees*bits3C8EFA35
alpha=a0+m'*(a1-a0)
target=rad*(m'*term)
yawVel+=alpha*(target-yawVel)
```

`a0/a1`은 gyro 꺼짐 .8/.3, gyro 켜짐 `.1+k*(k<0?bits3CA3D70C:bits3CA3D708)`/.2입니다. k·±0 명령도 원본에 있지만 이번 유한 k에서는 결과를 바꾸지 않습니다. 기존 구조식의 약.02는 위 비트 두 개로 나뉩니다.

pitch는 `pitchMax=(1.8+(k<0?k*bits3F4CCCCC:k))*bits3C8EFA35`, `target=(m'*(y*fovRatio))*pitchMax` 순서입니다. 속도를 alpha로 갱신한 뒤 다음 누적을 계산합니다.

```text
adjust=Controller17d==1?10:0
base=-75+adjust
lo=-103+kG*(kG<0?11:3)+adjust
hi=-31+kG*(kG<0?-18:-6)+adjust
# gyro 선택 슬롯의 두 offset이 있으면 lo/hi에 원본 순서로 적용
t=clamp((s+base-lo)/(hi-lo),0,1)
slope=(bias(t+bits3A83126F,bits3EE66666)-bias(t,bits3EE66666))/bits3A83126F
s+= (pitchVel*bits42652EE0)*slope
limit=C1680*(-75)+90
s=clamp(s,-limit,limit)
```

실행의 lo<hi 유한 범위에서 invLerp를 독립 대조했습니다. gyro를 끈 후 `24e64f0`에 전달하는 상대각과 out 되돌림은 기존 판독입니다. 스틱→누적각을 마우스 픽셀로 치환하는 것은 별도 웹 설계이며 이 원본 확정식으로 임의 변환 규칙을 만들지 않습니다.

## 7. 카메라 포즈·에셋·진동 연결

입력의 yaw 속도는 기존 원본 사인표로 C18c 방향을 회전합니다. 최종 포즈·장치 행렬은 [r10_module_projection.md](r10_module_projection.md)의 별도 원본 실행입니다. 실제 device posture·최종 픽셀 부호는 그 문서 §11의 미확정을 유지합니다. 이 입력 구간은 진동·사운드·이펙트 에셋을 직접 생성하지 않습니다.

## 8. 다른 기능과 상호작용

속도 블렌드 w, FOV 비율, Bf34 분기, C1550/C1764 추가 제한은 기존 생산·소비 판독을 재사용했습니다. 이번 yaw 실행은 Bf34=0/1/2/3/4/5/FFFFFFFF를 공급해 선택 조건을 검증했으며 상태 이름의 의미까지 실행한 것은 아닙니다. 실제 상태 생산자는 [r10_state_producers.md](r10_state_producers.md)를 참조합니다.

## 9. 웹 반영 필요

일반 스틱 경로에서 C188 저장 하한−1과 pow 지수 하한0을 구분하고, 대각 계수 c와 길이 복구를 함께 반영해야 합니다. 상수 비트와 곱셈 묶음, pitch의 컨트롤러17d==1 조건도 보존해야 합니다. 마우스 정책·최종 화면 부호를 이번 구간 실행으로 확정하지 않습니다. 웹 코드·impl은 수정하지 않았습니다.

## 10. 실제 명령·결과·실패

`python -X utf8 web/tools/r10_camera_input_emu.py`: 주축 스냅4096, bias2048, yaw4096, pitch 속도·누적2048 **총12,288건**, 독립 f32 참조식 대비 모든 검사 필드의 비트 불일치0. SDK powf4095/logf10842/expf5421 원본 호출, null/자동페이지/fault/미지원 PLT0. 합성 pre-block 입력이며 전체 함수 실행으로 확대하지 않습니다. 결과 `analysis/camera_100_r10/input/input_emu.json`.

실제 중복 확인은 `decomp_index.py 0x71024e0178 --no-build`, SHARED/FUNCS 검색. `disasm.py`로 0b00/0c20/0fcc/10a0/1460/1740/1910/1a34 명령을 읽었습니다. 잘못 지정한 `analysis/decomp/cam_main_full.c` 읽기는 파일없음으로 실패 후 실제 `camrest/cam_main_full.c`를 찾아 재사용했습니다. PowerShell에서 `rg web/tools/*.py`·와일드카드 디렉터리 인자를 넘긴 두 검색은 경로 구문 오류였으며 `rg web/tools -g '*.py'`로 수정했습니다. 명령 결과 실패를 원본 결론의 부재 근거로 사용하지 않습니다.

`python -X utf8 web/tools/r10_camera_input_chain_probe.py`:16건 모두 종료1cd0까지 도달, 실제predicate/1252998/사인표/24e64f0·SDK libm 호출, null/자동페이지/fault/PLT0. 원본 관측값은 `analysis/camera_100_r10/input/chain_probe.json`에 보존합니다. gyro 일치 조건의 순수 수직(.8) 입력은 누적0, gyro 꺼짐 일치 조건은 첫 틱누적.4476691782474518입니다. gyrotrue/B4ccfalse의 의도적 불일치 입력은.18669305741786957이며 이 반례를 실제 사격장 gyro 활성 동작으로 일반화하지 않습니다.

## 11. 미확정·기존 결론 정정·다음 근거

**정정(2026-10-03 r10):** 기존 `player_camera.md` §6.4의 “a,b,c 의미 미확정”은 a,b의 delta 필터와 c의 정확한 생산식을 연결해 해소했습니다. 기존 요약의 “e=max(e,0)”은 저장값 제한이 아니라 pow에 쓰는 별도 지수 제한입니다. C188 저장 하한은−1이며 두 차감 모두 max(-1)입니다. 기존 소수1.6/1.8/.96은 구조를 나타내는 약칭으로 보존하되 실행 명세에는 §4 원본 비트를 사용합니다.

고정 질문30의 오른쪽 스틱 y→속도→누적각 계산은 이 원본 판독·실행 범위에서 확정합니다. 고정 질문29의 식에 새 근거를 보강했으나 해당 행에 함께 남겨둔 최종 화면 부호는 질문12/31과 함께 미확정입니다. gyro 각도 재매핑·활성 상태 공급·whole input/frame·GPU 전체를 이12,288건으로 완료 처리하지 않습니다. 다음은 실제 device posture writer, 대체 상태 생산자, 실제 지형 boom 질의입니다.
