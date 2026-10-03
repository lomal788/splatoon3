# RenderingDay 접근자와 DOF 런타임 연결 — r8

## 1. 결론

[판독]+[실행] `vt+0x90`은 `PostEffect.DOFGaussian`이다. 적용 `2B68EF4`는 env+2AC8의 DOF 객체를 갱신한다. 이전 “자동 노출 계열”은 접근자를 식별하지 못한 추정이었다. Level은 원본 명령에서 **[0,15]**로 clamp한다.

## 2. 원본 자료

원본 `main.reloc.img`, 기존 `gfx4/g2_apply.c`·`g3_visitors.c`, 새 `r8_graphics/renderparam_accessors.c`·`dof_runtime.c`·`dof_ctor_mask_render.c`. 도구 `r8_gfx_renderparam_dof_emu.py`, 결과 `analysis/completion/r8/renderparam_dof_emu.json`. 기존 판독을 재실행한 것 중 새 근거는 실제 타입 접근자와 DOF 식의 명령 대조이다.

## 3. 실제 접근자 [판독]+[실행]

RenderingDay 래퍼 primary VT=0x7105564930, 리소스 root=`*(wrapper+8)+158`이 가리키는 객체다. `10C4AD4`(vt80)는 root78=`Shadow`를 읽는다. `10C4C20`(vt90)은 root70=`PostEffect`의 +40=`DOFGaussian`을 읽는다. `1158508`(vtC8)은 root58=`GlobalWind`를 읽는다. 원본 방문자 `11D5FF0`/`11CEFAC`의 필드 이름과 포인터 오프셋을 대조했다. ShadowPPBlur/DynamicShadowMap 파생 필드가 있다는 이유로 vt90을 그 타입으로 해석한 것은 옳지 않다.

root 설정 플래그82/83/89와 PostEffect50가 없으면 기존 parent/세대/RTTI 검사로 상속 객체를 찾는다. 이번 실행은 지역값 flag1만 사용했고 상속 walk의 실행 증명으로 확대하지 않는다.

## 4. DOFGaussian 적용 [판독]+[실행]

`2B68EF4(S0=t,X0=A,X1=env,X2=B)`에서 D=`*(env+2AC8)`, 없으면 반환. DOFGaussian 필드는 End30, FarCancel34, Level38, Start3C, Enable40이며 set flag41..45다. `mix=B+(A−B)*t`는 FSUB→FMUL→FADD로 모두 f32, FMA가 아니다.

| 입력 | 실제 기록 |
|---|---|
| Level38 | D268=clamp(mix,0,15); 바뀌면 rebuild |
| Start3C | D1E8=mix |
| End30 | D208=mix |
| FarCancel34 | D2A8=mix |
| Enable40 | abs(t)≤2^-23인 경우만 A의 bool을 D1A8에 기록; 바뀌면 rebuild |

abs(t)≤2^-23이면 D7D0을0으로 지운다. 마지막에 D68=true로 만들며, D1A8=true이고 D2A8<D1E8이면 다시 false로 만든다. 각 변경에 `35E553C(D+30)`을 부른다. 이 함수는 단순 dirty 기록이 아니라 DOF shader 선택 레코드를 재구성한다. 로비 값 Start484/End900/Level.5/FarCancel20은 원본 데이터다.

## 5. 원본 클래스 식별 [판독]

등록 `36F4310`은 문자열 `DepthOfFieldObj`, factory `36F4214`, size898을 `35CF870`에 넘긴다. factory는 `agldof` 이름과 VT57295C8/secondary5729690을 설정한다. generic EnvObj base `35CF1E4`만 읽어서 전체 DOF 기본값을 얻었다고 주장하지 않는다. Live env+2AC8 생성 전체·GPU DOF 픽셀 계산은 이 질문 밖의 미확정이다.

## 6. Shadow·GlobalWind 연결 [판독]

새 접근자는 `2B66C54`의 자원 입력이 Shadow→ProjShadow임을 확정하고 `2B60200`의 vec3/Intensity 입력이 GlobalWind임을 확정한다. [r8 추가] Shadow.ProjShadow의 이름/필드/전체 apply와 native texture·uniform 소비는 [projected_shadow_runtime.md §3~§6](projected_shadow_runtime.md)에서 원본3,072건으로 대조했다. Shadow의 env+2800 대상은aglprojsdw/VT572CC18이며 config19E0→374C50C allocation→Scene27F8/2800 연결을추가64건/126레코드원본실행으로확인했다. live로비config·frame matrix/factor producer는남는다. 적용 함수 전체 묶음 질문(stage L342)은 이 일부 성과만으로 확정하지 않는다.

## 7. 신규 분석에서 제외한 후보

GearAlphaMask `_op0` 결합은 SHARED r6의 `103F434`→work_tex0/1→M_Body sampler 근거가 이미 있었다. 이번 `1041F98`의 `_o0` 우선/`_op0` fallback, TargetOpacity 생성 확인을 새 완료 항목으로 다시 세지 않는다. `2B8DE6C`는 RenderingParam 적용으로 마스크 합성 후보에서 제외한다. Cloth/Havok 이름 xref는 reflection이고 실제 step dt 근거가 아니다.

## 8. 남은 한계

DOF render/픽셀 식, target 생성 전체, Shadow2800 live로비config·frame matrix/factor producer·GPU 실행, live scene 자원 로드는 미확정이다. 각 다음 대상은 DOF secondary VT5729690 init/reader, native projection shadow update, `35E553C` 이후 shader 소비다. 작업 시간이 부족한 항목을 원본 확정 불가로 바꾸지 않는다.

## 9. 웹 반영 필요

impl/render.md: DOFGaussian typed 연결, Level clamp0..15, start/end/farcancel f32 보간·t≈0 enable 갱신·D68 gate를 보존한다. `toneMappingExposure`나 자동 노출 값으로 쓰면 원본과 다르다. 웹 코드와 impl 문서는 변경하지 않았다.

## 10. 검증과 명령

`python web/tools/r8_gfx_renderparam_dof_emu.py`: 원본 apply1,024건·getter4,096건 byte 일치, null DOF 반환 확인. `35E553C`은 출력 sink로 변경 호출을 기록했고 실제 shader 재구성은 실행하지 않았다. 계산·필드 writer 스텁은 없다. 부모 상속 walk는 제외. 외부 PLT 서비스도 호출되지 않았다.

최초 실행은 Level상한을 잃은 디컴파일식으로 계산하여 case0에서 15 vs88.85213 불일치했다. raw ASM692C0의 FMOV15/692C4 FMIN을 확인하여 원본 상한을 적용한 뒤 전체통과했다. 디컴파일에는 unreachable block692C4 제거 경고가 있으므로 그 C만 신뢰하면 상한을 놓친다. `disasm.py addr 24`는 인자 오류이고 `-n24`로 교정했다. PowerShell Python stdout cp949 오류는 PYTHONIOENCODING=utf8로 교정했다.

## 11. 정정 이력

2026-10-03: stage§4 env2AC8 자동 노출 추정을 DOF 원본 접근자·클래스 등록·writer 실행으로 정정. 이전 문장은 삭제하지 않는다. 묶음 stageL342·GearAlphaMask stale row의 기존 근거를 신규 성과로 재계상하지 않았다. 실제 명령/실패는 r8/graphics_commands.md에 남겼다.
