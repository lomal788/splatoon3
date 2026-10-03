# ProjShadow 원본 적용과 렌더 소비 — r8

## 1. 결론

[판독]+[실행] RenderingDay의 Shadow.ProjShadow 값은 env+2800의 첫 객체에 기록된다. Density는 적용 시 제한하지 않으며, 렌더 uniform에는 `clamp(target+4E8,0,1) * clamp(Density,0,1)`이 들어간다. 자원 타입·필드·적용·소비와 대상의원본VT/태그·배정 연결을 확인했다. 공식C++ 클래스 심벌은 원본에 없어서 임의의 이름으로 채우지 않는다. stage L342의 전체 적용 묶음을 이 부분만으로 확정하지 않는다.

## 2. 원본 자료

원본 main.reloc.img, 기존 gfx4/g2_apply.c의2B66C54와g3_visitors.c의11DB834를 재사용했다. 새 projected_shadow.c는1152ED8/37AB8E0, projected_shadow_fields.c는11D3BA8이다. 새 projected_shadow_creation.c는3756CC8/374C50C이며 Scene의원문36C4A44(c2_envubo.c)는기존decomp를재사용한다. 도구 r8_gfx_projected_shadow_emu.py, 결과 analysis/completion/r8/projected_shadow_emu.json을 사용했다. 기존 DOF/GlobalWind 접근자 결과를 신규 완료로 다시 세지 않는다.

## 3. 자원 필드 [판독]

RenderingDay VT80=10C4AD4가 Shadow를 반환하고 Shadow+38이 ProjShadow다. Shadow+40은 해당 포인터 set flag다. 실제 방문자11D3BA8은 다음 이름/주소를 제공한다.

| 이름 | 자원 오프셋 | set flag | 대상 오프셋 |
|---|---|---|---|
| Density | 30 f32 | 54 | 5AC,5B0 |
| Rotate | 34 f32 | 55 | 440 |
| Scale | 3C/40 vec2 | 56 | 360/364 |
| Trans | 4C/50 vec2 | 57 | 400/404 |
| ScrollAnim | 44/48 vec2 | 58 | 380/384 |
| RotateAnim | 38 f32 | 59 | 420 |

## 4. 적용 순서 [판독]+[실행]

`2B66C54(S0=t,X0=A,X1=env,X2=B)`는 target=`*(env+2800)`가 없으면 반환한다. 원본은 Density→Rotate→Scale→Trans→ScrollAnim→RotateAnim 순서로 `B+(A−B)*t`를 f32 FSUB/FMUL/FADD로 적용한다. 입력 t나 결과에 clamp는 없다. 두 wrapper의 실제 typed getter10C4AD4를 실행했다. set flag=1 fixture라 상속 walk 실행 증명으로 확대하지 않는다.

새 `1152ED8(X0=wrapper,X1=env)`는 같은 필드를 보간 없이 직접 복사한다. 이 함수에도 target null 반환이 있다. 두 방식 각각1,024건에서 dirty target600B 전체를 독립 기대값과 byte 비교했고 모두 일치했다.

## 5. 렌더 consumer [판독]+[실행]

새 `37AB8E0`은 ctx=`*(arg1+D8)`, scene=`*ctx`, viewResource=`*(ctx+8)`을 받는다. scene+27F8의 count가0이 아니고 target+5B8이 true이면 texture slot14(0xE)에 viewResource+58을 전달한다. 그 외에는5999230의 기본 texture+40을 전달한다. 이것은 텍스처 바인딩 선택이며 실제 sampling/pixel 증명은 아니다.

scene count가0이 아니면 target530/540/550의 3개 vec4를 1B0B uniform110/120/130으로 복사한다. count0이면 원본 상수4997C90/4998180/4997170으로 만든 행렬을 사용한다. count가 없을 때의 matrix는 본문에서 임의의 일반적 투영행렬로 바꾸지 않는다.

uniform+1A0에는 `clamp(target+4E8,0,1)*clamp(target+5AC,0,1)`을 f32 곱셈으로 기록한다. 원본37ABA90의 첫FMIN1,37ABA9C의 Density FMIN1,음수 선택FCSEL을 판독했다. uniform은 실제 pool+CA0의 core×60 레코드+10에 포인터,+40에size1B0이 전달된다.

## 6. 원본 실행 대조 [실행]

apply1,024 +direct1,024 +render consumer1,024 =3,072건, mismatch0. apply는 전체600B를 비교하고 consumer는 행렬48B·밀도f32·scene matrix64B·texture slot14·실제 pool pointer/size를 대조했다. count0/1,enable0/1,Density−.1/0/.25/1/2/100 및 factor−2~3을 포함했다. NaN/inf와 상속 walk는 실행하지 않았다.

산술·필드 writer·typed getter는 스텁이 없다. 렌더 consumer 실행에서0837AC0 allocator는 지정한1B0B buffer를 공급하고, nn::os::GetTlsValue는 core0 fixture를 공급했다.37AF558은 texture binding 출력 sink로 기록했다. GUC의 TLS 서비스 기록2,048개가 남으며 미지의 PLT는0이다. GPU는 실행하지 않았다.


### 6.1 실제 대상 클래스·배정 [판독]+[실행:구간]

원본3756CC8은 태그`aglprojsdw`, primaryVT572CC18, 묶음이름`projection_shadow`를 설정한다.3756CC8 기본 객체의Scale360/364는1이며 Rotate440/Trans400/404/Scroll380/384/RotateAnim420은0이다. 공식C++심벌/typeinfo 이름은 stripped라 원본태그와VT로 객체를 식별한다.37AB8E0이읽는target을다른DOF/후처리객체로 부르지 않는다.

새374C50C는 config+19E0의개수만큼7F8B 레코드를 할당하고 각레코드에3756CC8을부른다.5AC/5B0/5B4는1,5B8/5B9는0/1,4E8은0,530..55F의행렬은원본상수초기값이다. manager+18F8/1900에 count/pointer를기록한다. 기존36C4A44는 manager=`Scene+F00`을374C50C에전달하므로 실제Scene+27F8/2800과정확히연결된다. 초기5B8=0은texture slot14에서기본텍스처를고르는 조건이고,4E8=0이면초기uniform밀도0이다. 실제frame의활성화/계수갱신전값을로비영구값이라고주장하지않는다.

`r8_gfx_projected_shadow_creation_emu.py`는 실제374D134..374D32C allocation/constructor/loop/배정구간64건(count0..4),실제레코드126개를실행했다.3756CC8과공통생성자360154C/35B7160/35EBEF8은원본전체를실행하며 allocator는native요청size에맞는buffer를공급한다. sinf/cosf만외부math서비스로연결한다. size7F8×count/포인터/count/VT/밀도pair/flags/Scale/Factor/행렬48B가모두일치하고unknownPLT0이다. Scene전체생성과로비실제config파일공급의실행증명은아니다.

## 7. 기존 근거 재사용과 제외

13751D0(render/blitzubo.c)의 같은 Shadow matrix/Density reader는 이미 decomp가 있으므로 새 함수로 세지 않는다.369BF40 agllmap Scene 생성자의2800 zero도r5 원문이므로 새 성과로 세지 않는다.378E4F8의5AC/5B0 저장은 다른 반복 파라미터 객체의count/set flag여서 target Density 생성자로 채택하지 않는다.35D9450은aglccr,3602C8C/36115F4/3617E34의 큰 구조체 저장 후보도 해당 target 연결이 입증되지 않아 제외했다.

## 8. 남은 미확정

env2800 객체의VT/태그와배정은§6.1에서해소했다. 남은 것은 target530의frame matrix producer/target4E8의frame factor producer, 로비 실제set flag/parent 상속, GPU 투영 그림자 픽셀은 [미확정]이다. 전체 적용묶음L342는 조사중이다. 다음은 native projection shadow update와 target360/380/400/420/440이530 frame matrix로 변환되는 실제호출자다. config19E0의live로비값 공급도별도남는다. 정적 offset 후보는 다른 객체와 중첩되므로 offset만 같다는 이유로 클래스 이름을 정하지 않는다.

## 9. 웹 반영 필요

impl/render.md: ProjShadow Density를 원본필드로 처리하고 apply 단계 무clamp와 최종 uniform 단계 두clamp의 차이를 보존한다. Rotate/Scale/Trans/ScrollAnim/RotateAnim 필드 오프셋 및f32 보간 순서, slot14의count+enabled gate를 반영해야 한다. 대상 factor나 투영행렬을 임의 값으로 채우면 안 된다. 웹 코드와 impl는 변경하지 않았다.

## 10. 실제 명령과 실패

full_decomp.sh projected_shadow.c 37AB8E0 1152ED8 성공2함수; projected_shadow_fields.c11D3BA8 성공1함수. projected_shadow_creation.c3756CC8/374C50C 성공2함수이며36C4A44는기존캐시로자동skip했다. func_lookup는37AB8E0을 직전37AB850의132B 범위로 잘못 보고하므로 raw37AB8E0 prologue와함수return구간을 확인하여 실제 주소로 decomp했다. 첫 실행은 대조3,072건이 통과한 뒤 TLS가unknown이라고 가정한 최종assert만 실패했다. 알려진TLS core service를 명시해 재실행했고 mismatch0·unknownPLT0으로 저장했다.

render_storescan --range를 `start/end` 한인자로 사용한 명령은ValueError였다. start와end 두인자로 교정했다. --shift 광범위 검색은 많은 다른 객체/음수shift 후보를 출력하여 유효한 타입 결론을 얻지 못했다. graphics_stringxref.py는 없는 파일이라 실패했고 실제xref.py str/addr를 사용했다. 상세 명령과 실패는graphics_commands.md에 기록했다.

## 11. 정정 이력

2026-10-03: Shadow→ProjShadow의 각필드 이름/전체apply/실제uniform consumer를 추가했다.37AB8E0 C의unreachable37ABA9C 제거 경고로 Density 상한1이 사라지는 것을 rawFMIN 판독+원본실행으로 정정했다. 추가원본3756CC8의aglprojsdw/VT572CC18와374C50C→Scene27F8/2800 생성구간64건으로기존target클래스/생성미확정을정정했다. 기존stage§11의 적용 구조체 질문은삭제하지않는다. 전체apply묶음에는ColorGrading연산칸/LUT 등별도남은부분을확인해야하므로stageL342의큰질문승격은보류한다.
