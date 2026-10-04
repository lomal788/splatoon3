# 카메라 모듈·시작 리셋·화면 방향 보정 (r10, 2026-10-03)

## 1. 기능 개요와 화면에서 느끼는 동작

[판독]+[실행] 활성 Spectator 포저의 포즈가 CameraModule의 현재 포즈로 복사되고, 최종 포즈로 뷰·논리 투영·장치 투영을 만듭니다. 모듈의 저장 포즈를 이용하는 리셋에서 읽던 `M140`, `M150..15c`의 실제 생산자를 연결했습니다. **원본 사격장의 live device posture와 최종 픽셀은 아직 미확정**입니다. 값 0을 임의로 넣어 최종 화면 질문을 닫지 않습니다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0, `extracted/exefs/main.reloc.img`, base `0x7100000000`. 아래 축약 주소에는 이 base를 더합니다. SDK 삼각함수는 `extracted/exefs/sdk.img`의 동적 심볼에 있는 원본 명령을 실행했습니다.

SHARED/FUNCS/decomp_index 확인 뒤 `camera/camui_batch3.c`의 `1010150`, `r7_camweapon/projection.c`의 `1017434/3589d74`, `r5_paint/r5_a.c`의 `3589b48`, `r8_camweapon/poser_consumer.c`의 `27600c8`, `r6_camweapon/actor_state.c`의 초기화 경로를 재사용했습니다. 신규 디컴파일은 `analysis/decomp/r10_camera/module_lifecycle.c`의 `0ffd64c/0f57018` 두 함수입니다. 함수 경계는 lookup 뒤 실제 prologue로 확인했습니다.

## 3. 진입점과 전체 호출 흐름

```text
Spectator S의 이미 계산된 포즈 S2fc
→ P=S288, 실제 VT56467f8
→ Module1010150: P.vt28=27602e4(ret), P.vt30=27600c8
→ M+d4 일반 포즈
→ M144 포즈 복사·월드 위치 쉐이크 합산
→ 1017434: M190 LookAt / M220 Perspective 필드
→ vt58=3589d74: M22c 논리 투영
→ vt60=3589b48(M2ac): M26c 장치 투영
→ M10 viewport가 있으면 M2d0 aspect와 M140 래치 갱신
```

[판독] 포즈 전환 시간이 남으면 임시 포즈→`1017d5c` 보간 경로를 사용합니다. 이번 전체 모듈 실행은 `M80=M84=0` 직접 포즈 경로이며 그 보간 분기를 새 실행 성과로 포함하지 않습니다. Spectator 선택·PlayerCamera getter의 기존 r8/r9 근거 역시 재사용입니다.

시작 리셋의 상위 연결 [판독]+[실행: bridge/dispatch]:

```text
Actor0f73ecc: state4d0=1의 준비 조건 → 0f7400c(mode0 또는1)
Actor0f746b4: 준비 완료 → 0f7400c(mode2) → state4d0=2
0f7400c: component mask·인덱스 매핑·RTTI 통과 → component.vt+d0
component 실제 VT553e788+d0=0f57018, component20=Behavior
→ 0ffd64c: 앞 component 초기화 → Behavior.vt78 → 뒤 component 초기화
→ 실제 PlayerBehavior VT5632b08+78=2353a18
→ 2472c4c → 기존 reset(C,0,1,B34)
```

모드별 마스크는 0이면 전 비트, 1이면 Actor.vt340 반환값, 2이면 그 보수, 그 밖이면 0입니다. 컴포넌트의 실제 배열 인덱스가 Actor+218의 매핑 값과 같고 RTTI가 맞아야 호출합니다. 이 초기화 경로는 매 프레임의 일반 카메라 reset이 아닙니다. 상위 ActorSystem 전체와 실제 Scene spawn은 새 실행 범위 밖이며, 위 상위 연결은 원본 판독입니다.

## 4. 구조체·필드·상수·타입

| 필드 | 원본 계약 | 생산자 / 소비자 |
|---|---|---|
| M120 | 활성 포저 포인터 | 기존 포저 선택 / 1010150 |
| Md4..11f | 원래 포즈, padding 제외 길이4c | P.vt30 / 1010150 |
| M144..18f | 쉐이크 적용 포즈 | 1010150 / 1017434·24e4bc8 |
| M150..15c | 쿼터니언 x/y/z/w | 1010150의 Pose+0c 복사 / reset24e4bc8 |
| M140 byte | viewport 공급으로 1이 되는 유효 래치 | ctor100f980에서0, 10104c4에서1 / reset24e4bc8 |
| M190 / M220 | LookAt / Perspective 객체 | 기존 ctor / 1017434 |
| M2ac | 장치 posture 정수 | ctor가5997898을 읽음 / 3589b48 |
| M2b0 / M2b4 | Projection의 ZScale / ZOffset | ctor의 원본 값 / 3589b48 |
| M2d0 | aspect | viewport 또는 draw context / 다음 투영 갱신 |
| M228 / M229 | 논리 / 장치 투영 dirty byte | 포즈·viewport writer / 1010150 |
| component28 bit0 | 시작 대기 래치 | 0f57018 끝에서 clear | 
| Actor5cc | `<2`를 시작 인자로 전달 | 0f57018 / 2353a18→2472c4c |

Pose 복사는 `[0,2d)`, `[30,45)`, `[48,4c)`만 건드립니다. padding을 포함한 전체 memcpy로 확대하지 않습니다. `M140`은 viewport가 사라졌다고 그 틱에 0으로 바뀌는 값이 아닙니다. 생성 시 0이며 이 분기는 1만 씁니다.

## 5. 상태 전이·생성·종료

[판독] 모듈 생성자100f980은 M140=0, 기본 포즈·LookAt/Perspective·dirty 상태를 설정합니다. 일반 갱신은 포즈 복사 후 쉐이크를 월드 위치에만 더합니다. viewport M10이 있으면 M140=1입니다. 그 뒤 M10==0이면 이 함수는 M140을 보존합니다. 리셋24e4bc8이 읽는 quaternion은 이 모듈 갱신에서 복사한 값이므로 임의 Y키 저장 포즈라는 이름을 붙이지 않습니다.

시작 bridge는 Behavior.vt100의 삭제 요청 결과와 component28 bit1을 먼저 확인합니다. 삭제 경로가 아니면 Actor5cc<2를 `w1`로 넘기고 끝에 component28 bit0만 지웁니다. 실제 PlayerBehavior의 vt100은 원본0ffde28 경로이며 이번 입력에서 삭제 요청을 만들지 않습니다. 다른 클래스의 삭제 경로·동적 수명 전체를 이 검증으로 일반화하지 않습니다.

## 6. 계산식·조건·연산 순서

[판독]+[실행] viewport 화면비는 **행렬 생성 후** 다음 순서로 저장됩니다.

```text
logical = Perspective(pose.FOV, pose.near, pose.far, oldAspect, offsetXY)
device = DeviceTransform(logical, M2ac, ZScale, ZOffset)
if M10 != null:
    M228 = 1
    M140 = 1
    M2d0 = f32(f32(right-left) / f32(bottom-top))
```

M18 draw context 경로가 뒤에 있으면 그 화면비가 M10의 값을 다시 덮습니다. 1,024건 기본 검사에서는 M18=0이며 추가256건에서 이 원본 후행 경로도 실행했습니다. numerator는 max(u16(context40),1), denominator는 context4a==3이면 u16(context42), 그 밖이면 max(u16(context42),1)입니다. type3·height0이면 원본 그대로 +Inf가 저장되며 임의로1 클램프를 추가하지 않습니다. 이 경로는 M140을1로 만들지 않습니다. 따라서 M10/M18 변경의 새 화면비는 그 틱에 이미 생성한 투영에 소급 적용되지 않습니다. 앞의 dirty가0이면 이전 투영을 보존하는 경로도 있으므로 모든 렌더러 갱신 상황으로 확대하지 않습니다.

장치 투영의 x/y행 변환 [판독]+[실행], A=논리 행렬, D=장치 행렬:

| posture | D의 x행 | D의 y행 |
|---|---|---|
| 0 및 switch에 없는 값 | A.x | A.y |
| 1 | A.y | −A.x |
| 2 | −A.y | A.x |
| 3 | −A.x | −A.y |
| 4 | −A.x | A.y |
| 5 | A.x | −A.y |

z행은 대수적으로 묶지 않고 원본 f32 순서를 보존합니다.

```text
D20 = f32(zs*A20)
D21 = f32(zs*A21)
D22 = f32(zs*f32(A22+f32(zo*A32)))
D23 = f32(f32(zs*A23)+f32(zo*A33))
```

P23는 원본3589e28..e30의 `f32(invDepth * f32(f32(far*-2)*near))`입니다. 곱 순서를 바꾸면 1ulp가 달라질 수 있습니다. 이 순서는 기존 r7이 이미 정확히 검증한 것을 재사용했으며, 아래 첫 재현 실패는 새 harness의 참조식 오류였습니다.

## 7. 카메라·음향·에셋 연결

Spectator 포저→Module→View/Projection의 원본 연결을 재사용했고 전체 모듈 갱신에 이 callback을 실제로 포함했습니다. 이번 Module 실행에서 shake 개수는0입니다. 쉐이크 수명·발사/명중 ELink는 [r10_shake_shooter.md](r10_shake_shooter.md)의 별도 근거를 사용합니다. 음향 리스너와 렌더러 UBO/GPU 업로드를 함께 실행한 것은 아닙니다.

## 8. 다른 기능과 상호작용

24e4bc8의 유효 포즈·쿼터니언 공급 질문은 §§3~5와 [r9_reset_contexts.md](r9_reset_contexts.md)의 실제 적용식으로 연결됩니다. 시작 lifecycle은 앞 component 초기화가 Behavior slot15보다 먼저라는 순서를 보존합니다. Actor 상태1→2와 같은 프레임의 물리/슬롯19 순서는 기존 physics 프레임 그래프 판독을 재사용합니다. 같은 그룹의 병렬 Actor를 임의 직렬 순서로 해석하지 않습니다.

## 9. 웹 반영 필요와 구현 순서

이번 요청은 분석·MD만이므로 웹/impl을 수정하지 않았습니다. 향후 반영할 항목은 모듈 포즈와 원본 viewport 갱신 시점의 구분, reset 입력의 원본 생산자, Pose padding 제외 복사, 장치 행렬의 XY 변환과 z행 곱 순서입니다. **실제 posture가 아직 미확정이므로 웹에 특정 값·반전 정책을 임의 추가하지 않습니다.**

## 10. 실제 실행 명령·결과·실패

`python -X utf8 web/tools/r10_camera_module_emu.py`:

- 전체3589b48: 임의 유한 4×4 행렬·posture0..6/FFFFFFFF·ZScale/ZOffset 4,096건, 65,536 f32 필드 비트 불일치0.
- 전체1010150: 실제 포저 callbacks→원본1017434/LookAt/Perspective/device transform 1,024건, 논리16+장치16+view12+aspect1의 46,080 f32 필드 비트 불일치0. 별도로 Pose의 실제 복사 범위·valid·dirty 검사.
- 추가 draw-context256건: 후행 aspect 덮어쓰기·projection이 oldAspect 사용·valid140은 viewport 공급에만 반응·type3/height0의+Inf 모두 원본과 일치. valid latch128개의2틱 시퀀스에서는 viewport존재→소실 후140이1을 유지했습니다. 불일치0.
- SDK sinf/cosf/tanf 각1,536회 원본 실행. quaternion identity, synthetic source Pose/viewport/context/posture를 사용했습니다. null/자동페이지/fault/미지원 PLT0. **원본 장치의 실제 posture·전체 Lby Scene·GPU·음향 실행은 아닙니다.**
- 첫 실행: 1,024불일치. PUC의 Python trig hook 뒤 SDK hook이 다시 적용되는 harness 오류. `initial_double_trig_failure.json` 보존. SDK 호출을 PUC subclass의 단일 PLT 처리로 고쳤습니다.
- 둘째: P23 곱 순서 참조식 오류로421불일치. `initial_projection_order_failure.json` 보존. 실제 asm·기존 r7 참조식을 재사용해 수정 후0.

`python -X utf8 web/tools/r10_camera_start_dispatch_emu.py`: 실제 bridge VT553e788→Behavior VT5632b08→2353a18까지1,024건, 전달13포인터·bool·component 래치·순서 일치. Actor5cc=0/1/2/FFFFFFFF, component28 모든 byte를 공급. signal 등록2352f88와2472c4c setup만 각각1,024회 경계 capture, 빈 Behavior list, null/자동페이지/fault/PLT0. 전체 setup/reset/실제 ActorSystem 실행으로 확대하지 않습니다.

결과는 `analysis/camera_100_r10/module/module_emu.json`, `start_dispatch_emu.json`, `posture_data_audit.json`. `func_lookup.py`, `decomp_index.py --no-build`, `disasm.py`, `bl_callers.py`, `r6_combat_vcallscan.py` 및 `full_decomp.sh ... module_lifecycle.c 0x7100ffd64c 0x7100f57018`를 실제 실행했습니다.0f7400c의 decomp는 도구가 기존 cached C를 확인하고 새 실행을 하지 않았습니다. `xref.py call` 두 번은 미지원 subcommand로 실패했으며 `bl_callers.py`로 수정했습니다. `git status`는 이 디렉터리가 Git 저장소가 아니어서 실패했고 Git 변경/commit/push는 없습니다. 명령 상세는 r10 commands.md에 기록합니다.

## 11. 미확정·다음 근거

고정 질문16의 다음 근거였던 **setup slot15 상위 lifecycle 및 module140/150 live 생산자**는 이번 원본 판독·실행으로 연결했습니다. 기존 재시작 enum·다른 메시지·사망 수신 경로의 근거는 r8/r9 재사용이며 신규 성과로 재계상하지 않습니다.

고정 질문12/31의 최종 화면 부호는 조사중입니다.5997898 raw BSS bytes는0이고 이 포인터의 aligned data 참조는57917d0 하나라는 새 데이터 감사만으로 live 값0을 확정하지 않습니다. r9의 static writer scan0과 합쳐도 모든 외부/간접 writer 부재 증명이 아닙니다. 다음은 device posture 초기화·플랫폼 출력 설정·M2ac setter/dirty 공급과 실제 Lby framebuffer의 투영 업로드 경로입니다. 이번 전체 Module 실행 성공으로 이 질문을 닫지 않습니다.

추가 판독(2026-10-03): 후보 `3589938`은 Projection 복사 함수입니다. dirty8/9를 복사하고 각 dirty가0일 때만 해당 논리/장치 행렬을 복사하며, posture8c/ZScale90/ZOffset94는 항상 복사합니다. 새 `projection_copy.c`와 실제 명령을 확인했습니다. 이 함수의 direct BL 두 곳36d1b90/36d1bc8은 `36d174c`의 큐브 렌더용 local Projection이고 source는5997a78입니다. 첫 BL caller 도구의 선행36d1138 표기를 그대로 쓰지 않고 prologue/func_lookup으로 정정했습니다.36d1138은 큐브 렌더 객체 초기화에서5997898을 읽는 후보로 확인했으며 PlayerCamera Module의 live setter와 연결하지 못했습니다. 새 C 세 함수·raw 판독은 실제 시도지만 최종 화면 질문을 닫을 근거는 아닙니다. 다음은 여전히 M2ac 공급과 플랫폼 출력 설정입니다.

**2026-10-03 렌더 소비자 후속 [판독]+[실행]:** [r10_render_projection §3~6](r10_render_projection.md)의 일반 renderer는 logical Projection+0c→row+c0→Context7..10을 사용한다. 이 문서의 device M26c 계산식은 유효하지만 해당행렬을 일반 UBO 입력이라고 확대하지 않는다. CPU/SDK 연결1042건은 성공했으며 실제 Lby 출력texture/window·GPU 초기상태는 미확정 유지다.

**r10 사용자 종료 시점 후속 안내** (2026-10-03): [렌더 후속](r10_render_projection.md)의실제normalfactory/flags/worker·origin1/display image·HDR triangle공급자는추가로연결했다. 이전최종출력경계중같은frameHDRtarget/window 및GPU초기swizzle은남는다. [최종집계](analysis_100.md)는93/106이며100%미달이다.
