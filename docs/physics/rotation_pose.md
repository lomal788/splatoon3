# 회전 TOI의 자세 보간·행렬 변환 (9차, 2026-10-03)

## 1. 개요

원본 회전 질의 `0948360→094e6e4`가 사용하는 quaternion 보간 `08a8764`와 matrix writer `08a5ed0`, SIMD asin/sin `08a69e0/08a6770`의 원본 식·순서를 **[판독]+[실행]**으로 기록한다. 일반 회전 TOI 전체가 해소되었다는 뜻은 아니다.

## 2. 원본 파일·함수

- `analysis/decomp/r9_physics/generic_penetration_rotation.c`: `ae9b14/08a8764`.
- `rotation_matrix.c`: `08a5ed0`; `rotation_trig_penetration.c`: `08a69e0/08a6770/ae7fd0`.
- 기존 `rotation_toi_core.c`: 호출자 `094e6e4`; 기존 `b1.c`: 게임 처리기 `3c54140/3c54de4`.

SHARED/FUNCS·decomp_index·func_lookup 선행 확인 후 새 함수만 디컴파일했다. 이전 처리기/advance 분석은 재사용이다.

## 3. 데이터·입력

quat는 f32 4개 `(x,y,z,w)`, 시간은 낮은 두 lane에 같은 t를 넣는 실제 callback 입력이다. actual trace는 게임 처리기 전체 8회에서 quat callback16회·matrix24회를 저장했다. fixture는 수직 capsule, 이전 I/현재 Y회전, θ=0/.1/1/π/2, NULL query filter/codec이다. 정적 nativebody에 게임의 상대 운동·회전 입력을 명시적으로 주었으며 실제 Lby 동적 actor 상태라고 주장하지 않는다.

원본 `08a5ed0`은 q4 3개=48 B를 쓴다. 각 열의 W도 원본 값이며 임의로 모두0으로 채우면 다르다.

## 4. 실행 순서

`3c54140/3c54de4→09af088→0948360→094e6e4`의 실제 callback 진입에서 qa/qb/t와 output ptr·LR를 캡처하고 원본 return 직후 출력을 독립 계산과 비교했다. quat16×4 + matrix24×12 = **352필드 비트 불일치0**, 전체8회 정상 반환/null·auto·fault0. OS mutex/TLS/clock/free 환경만 fixture이며 pose/TOI 계산 스텁은 없다.

## 5. 상태·분기

`d=F(F(ax*bx+ay*by)+F(az*bz+aw*bw))`. d<0이면 qb 가중치의 부호를 XOR하여 짧은 경로를 고른다. `abs(d) >= bits(0x3f7fbe77)`이면 선형 `(1-t,t)` 가중치, 아니면 삼각함수 분기다. 끝에서 결과 quat 길이²를 원본 dot4 순서로 합하고 sqrt로 나눈다. 길이²=0은 quat0을 반환한다.

## 6. 식·상수·정확한 순서

`F`는 각 연산의 f32 반올림이며 FMA로 합치지 않는다. trig 경로는 `theta=π/2-asin(abs(d))`, `wa=sin(theta-t*theta)/sqrt(1-d²)`, `wb=sin(t*theta)/sqrt(1-d²)`. 원본은 angle 범위 축소에 **FRINTM(floor)**을 쓴다. decompiler의 정수 cast로 바꾸지 않는다. 이번 t∈[0,1]/단위 quat 범위에서는 angle floor가0이다.

asin은 `a=min(abs(v),1)`; a>.5면 z=.5*(1-a),base=sqrt(z), 그 외 z=a²,base=a. 다항식 계수 비트는 순서대로 `3d2cb352,3cc617e3,3d3a3ec7,3d9980f6,3e2aaae4`; Horner 뒤 `base+base*(z*P)`. a>.5는 π/2−2*결과, a<`38d1b717`은 a, v<0 부호 XOR이다. **−0 입력의 asin 출력은 +0**이다.

sin은 j=`(trunc(F(abs(v)*bits(3fa2f983)))+1)&~1`; r에 j와 `bf490000,b97da000,b3222169`를 차례로 곱해 더한다. z=r², cosine 계수 `37ccf5ce,bab6061a,3d2aaaa5`, sine 계수 `b94ca1f9,3c08839e,be2aaaa3`. j&2로 sin/cos를 고르고 최대1 제한 후 입력 부호와 `(j&4)<<29`를 XOR한다. 각 곱·합·범위 축소·부호 적용의 완전한 식은 독립 참고 코드 `r9_physics_rotation_pose_emu.py`의 `asin_ref/sin_ref`에 그대로 보존했다.

matrix는 dx=2x,dy=2y,dz=2z,xx=dx*x,yy=dy*y,zz=dz*z,xy=dy*x,xz=dz*x,yz=dz*y,wx=dx*w,wy=dy*w,wz=dz*w,h=1−zz일 때 다음48 B이다.

```text
[h−yy, xy+wz, xz−wy, yz−wx,
 xy−wz, h−xx, yz+wx, xz+wy,
 xz+wy, yz−wx, (1−xx)−yy, 0]
```

## 7. 화면·애니메이션·효과 연결

TOI 형상의 실제 순간 자세를 만드는 계산이다. 캐릭터 skeletal pose나 camera quaternion에 같은 의미를 자동 적용하지 않는다.

## 8. 다른 기능과의 상호작용

[rotation_toi_advance.md](rotation_toi_advance.md)의 원본 advance/refinement와 연결된다. support/closest `af7b70`, overlap recovery `ae7b34→ae9b14`의 전체 기능은 별도이며 quat 성공으로 전체 collision을 확정하지 않는다.

## 9. 웹 반영 필요

`impl/physics.md/weapon.md`: 회전 자세를 근사 .2 fraction으로 맞추지 않고 원본 f32·shortest quaternion·정규화·48 B 대응을 사용한다. 원본 sin/asin을 host double math로 바꾸면 비트 일치가 깨질 수 있다. 이번에는 웹 코드를 수정하지 않았다.

## 10. 명령·검증 결과

`python -X utf8 web/tools/r9_physics_rotation_pose_emu.py`:4097회, asin16,388/sin16,388/quat16,388/matrix49,164 = **98,328필드 불일치0**, linear1,025/trig3,072. null/auto/fault/PLT0. finite asin[-1,1],sin[-100,100],단위 quat/같은·반대 quat,시간중복t[0,1].

`python -X utf8 web/tools/r9_physics_rotation_pose_actual_trace.py`: game whole8회·callback40회·352필드 불일치0, 정상 반환/nullauto0. 두 JSON은 `analysis/completion/r9/physics_rotation_pose_emu.json` 및 `physics_rotation_pose_actual_trace.json`.

실패도 보존한다: standalone 첫 실행은 UC_ARM64_REG_Q0 import 누락 NameError(exit1), import 수정 후 성공. actualtrace 첫 실행은 `else12` 구문 오류(exit1), 공백 정정 후 성공. 로그 `analysis/completion/r9/physics_commands.md`.

## 11. 미확정·다음 근거·정정

2026-10-03 정정: Ghidra의 `08a69e0/08a6770` return void 표기는 Q0 다항식 결과를 소실한 디컴파일 함정이다. 전체 ARM 명령을 읽어 위 식과 독립 실행으로 확정했다. NaN/inf, 비단위 quat 및 중복되지 않은 시간 lane 전체는 이 실행으로 검증하지 않았다.

**[미확정]** `af7b70` 전체 closest/support와 `ae7b34→ae9b14` EPA/overlap, sphere→quad `094ae10`의 전체 TOI 연결. 고정 L359/L495/L508은 조사중 유지. 다음 주소는 `ae7fd0/ae892c/ae926c/ae9840/ae9498/ae8e80`, `af7b70`이다.
