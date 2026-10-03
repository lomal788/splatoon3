# 볼록 질의의 겹침·퇴화 복구 (9차, 2026-10-03)

## 1. 개요

일반 cast `aec920`와 회전 closest `af7b70`의 `ae7b34→ae9b14` 복구 경로를 기록한다. 전체 원본 실행 trace와 독립 plane/barycentric 비트 검증을 구분한다. 사용자 최신 지시에 따라 새 TOI 확대를 여기서 멈추며, 미해소 whole은 승격하지 않는다.

## 2. 원본 파일·함수

`generic_recovery.c`:ae7b34(1180 B), `generic_penetration_rotation.c`:ae9b14(2844 B), `rotation_trig_penetration.c`:ae7fd0(2396 B). 새 `penetration_helpers.c`:ae892c(460),ae926c(556),ae9840(724),ae9498(248),ae8e80(1004),ae8af8(904 B). `penetration_barycentric.c`:ae9590(688 B). notes/index/lookup 확인 후 디컴파일했고 전 본문을 읽었다. 핵심 doubleplane/barycentric는 전체 ARM 명령도 대조했다.

## 3. 입력·자료 배치

원본 0x4e40 TLS 임시 arena: descriptor+0 callback/+8 shapeA/+10 shapeB; +20..5f 변환/원점; +60 margin/+68 margin²; +70/+78 A/B feature; +80 seed count/type. +c0 실제 vertexcount; A+B support arrays +d0/+4d0, 차 벡터 +8d0; face halfedge +d60, basepoint +1560, normal +1d60, inverse norm +2560, plane bound +2760, uncertainty +2960, double high/low +2be0/+3be0, final status +4de8/+4dec/+4df0, normal +4e00, distance +4e10, weights +4e20, segment parameter +4e30.

full trace는 cube/cube 겹침, cube/point 겹침, 같은 point, triangle 위 point, cube 경계 접촉의 5 geometry×initial output 유무2 =10질의다. 원본 allocator/native TLS 초기화; OS mutex/clock/free만 환경 fixture. 실제 Lby mesh 전체 접촉 입력이라고 주장하지 않는다.

## 4. 실행 순서 **[판독]**

`ae7b34`는 A/B feature count를 바탕으로1/3/4 seed를 만들고 arena를 할당한다. `ae9b14`는 양쪽 bbox를 callback으로 얻고 중심/extent에서 숫자 허용오차를 만든다. `ae7fd0`는 실제 paired feature를 먼저 모으며, 짧은 중복 변위와 공선성을 거부한다. 3vertex seed는 앞뒤 triangle 두 면을 만들고 남은 점을 삽입한다. 부족하면 `ae892c` 지원점으로 길이·면을 추가한다.

반복은 가장 큰 plane-bound(+2760) face를 고른다. 지원점 개선이 margin보다 작으면 최종 face/접점을 고른다. 개선이 있으면 보이는 면을 제거하여 `ae9498` horizon과 `ae8e80` 새면을 연결한다. 원본 halfedge adjacency를 그대로 갱신한다. vertex64 한도는 반환 상태3이며 임의 miss와 동치라고 명명하지 않는다. source의 `*(int)(D+4dec)`은 출력 접점 종류1/2/3(점/선분/면) 선택에 실제 소비된다.

## 5. 분기·상수 **[판독]**

`ae892c`: vertexcount<64일 때 supportcallback; A−Rᵀ(B−origin)과 기존 점의 차를 direction에 투영한다. normalized 개선량≥margin이면 새 support를 각 배열과 Minkowski 차 배열에 저장한다. 초기 state8에서는 음의 projected distance가 margin보다 큰 경우 state0·normal/distance를 먼저 저장한다.

bbox 기반 수치 오차는 approximate length의 float bit 연산·1.03, `max(margin*1024², bbox값)`의 exponent mask,4*2^-23 항 등을 사용한다. 기존 simplex의 네 번째 lane은 vertex tag이며 이것을 추가 공간축으로 계산하지 않는다. face visibility의 |dot|≤uncertainty는 **f64 high+low plane**으로 다시 확인하므로 모든 연산을 f32로 통일하면 원본이 아니다.

## 6. plane·barycentric 식 **[판독]+[실행]**

### 6.1 전체 ae926c

삼각형 edge는 f32로 뺀 뒤 cross는 f64로 계산한다. cross를 f32로 반올림한 N에 대해 H=`double(F(F(bias+N)-bias))`, L=`cross64-H`로 나눈다. N²의 합은 `F(F(Nx²+Ny²)+Nz²)`, inv=`F(1/sqrt(N²))`. uncertainty=`max(error,F(error*F(error*F(error*inv))))`; ARM 순서는 error*inv→error→error 곱이다. P=F(origin−triangle0)를 double로 바꾸고 H/L 각각 dot를 `(x+y)+z` 순서로 합한 뒤 두 합을 더한다. bound=`F(uncertainty+F(F(dot64)*inv))`. N=F(H+L) 및 preparedflag1을 저장한다.

원본 전체4097회, f32/f64/int **65552필드 비트 불일치0**. synthetic finite/nondegenerate facet와4lane bias/origin. NaN/0면은 이 독립 실행의 범위 밖이다.

### 6.2 전체 ae9590

edge E0=C−B,E1=A−C,E2=B−A. E0/E1 길이²는 **z²+(y²+x²)**, E2는 (x²+y²)+z² 순서다. 최소 edge mask→원본 table `[0,0,1,0,2,0,1,0]`로 j를 고르고 i=`((0x36>>(2*j))&3)^j`, k=`((0x2d>>(2*j))&3)^j`. E_i의 norm/projection은 f64; perpendicular는 다시 f32. delta=P−V_k의 perpendicular 투영으로 λ_i, 잔여의 E_i dot로 λ_j를 구하고 λ_k=(1−λ_j)−λ_i. 네 번째 λ=0.

signed-weight는 원본 approximate inverse length이다. I의 bits=`0x5f2fed52-(bits(edgeLen²)>>1)`, 보정=`(((len²*bits(bf0e425b))*I)*I+bits(3fc6fa83))*I`; η=λ*보정. host sqrt로 바꾸지 않는다. 상세 float order는 독립 참고 `r9_physics_penetration_barycentric_emu.py`에 보존했다.

원본 전체4097회/**32776필드 불일치0**, shortest mask1/2/4와 동률7 257회. 첫898참조 불일치는 E0/E1 길이 합 순서를 `(z²+x²)+y²`로 읽은 오류였다. 원본 `ae9620/ae962c` 순서로 정정했고 첫failure JSON을 보존했다.

## 7. 실제 호출 입력 연결

원본 generic10whole에서 plane32+barycentric14 callback의 입력을 받아 같은 독립식과 원본 return 출력을 비교했다. **46callback/624필드 비트 불일치0**, 전체10 정상 반환/null·auto·fault0. 원본 allocator/TLS가 arena를 공급하며 면/접점 생산자를 스텁으로 대체하지 않았다. 정상 반환 관찰을 EPA 전체 재구현 비트 일치로 바꾸어 표현하지 않는다.

## 8. 다른 기능과의 상호작용

최종 normal은 음수로 output에 저장되고 distance는 낮은2lane에 복제한다. 접점은 종류1: 한 vertex,2:선분 보간,3:선택face의 세 Avertex 가중합이다. A/B feature 슬롯을 원본 선택 순서로 복사한 후 `ae7b34`가 낮은16bit feature tag 중복을 줄인다. A+Bcount>4이면 큰 쪽3/작은 쪽1로 만들고context+d4=1을 쓴다. 게임 collector/staging은 phive_controller§6.12.1 기존 신규 결과와 연결된다.

## 9. 웹 반영 필요

`impl/physics.md/weapon.md`: nearzero/overlap을 임의 fraction0/normal0으로 치환하지 않는다. doubleplane 재검사·원본 bound·64vertex 한도 상태·tag 중복제거·근사 inverse length·동률 순서를 구분한다. 이번에는 MD/analysis/new tools만 수정했다.

## 10. 명령·결과·실패

- 새 full_decomp helpers6 exit0/INDEX6150,barycentric1 exit0/INDEX6151. 선행 notes/index/lookup·전체본문 판독 완료.
- `r9_physics_generic_recovery_probe.py`:10whole 정상 반환. 최초 `u.init_native()`는 method가 아닌 modulefunction이라 AttributeError(exit1); 실제 `init_native()` import로 정정하고 성공했다.
- `r9_physics_penetration_plane_emu.py`:4097/65552 bit0bad.
- `r9_physics_penetration_barycentric_emu.py`:최초898bad, ARM 합 순서 정정 후4097/32776 bit0bad. firstfailure 별도JSON.
- `r9_physics_penetration_actual_trace.py`:whole10/callback46/624fields bit0bad. 새수식 독립 검증이며 앞선10whole 관찰 표본을 신규10+10으로 합산하지 않는다.

각 JSON은 `analysis/completion/r9/physics_*` 동일 이름, 명령 로그는 physics_commands.md이다.

## 11. 미확정·다음 근거

**[미확정]** 원본 전체 EPA/GJK를 독립 포팅하여 모든 helper의 모든 분기까지 비트 검증한 것은 아니다. seed/multi-face topology/face-choice는 전체 source 판독, plane/barycentric는 원본명령+독립실행, 나머지는 원본 whole trace로 수준을 구분한다. 특히 `ae9840`의 후보face 선택 및 `ae8e80` 전체 horizon topology synthetic 전수 대조, 회전 `af7b70` arbitrary feature 대응, native mesh leaf/queryfilter live게임 입력은 별도이다.

사용자 최신 지시로 TOI 신규 확대를 중단했다. 고정 phive L359/L495/L508은 현재 조사중이며 이 문서의 부분식으로 전체 승격하지 않았다. 필요한 다음 주소를 삭제하지 않는다:ae7fd0/ae892c/ae8af8/ae8e80/ae9498/ae9840,af7b70. FillUp runtime은 [fillup_contact_runtime.md](fillup_contact_runtime.md)로 별도 진행한다.
