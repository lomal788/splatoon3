# 사운드 제한기·우선순위·정지 시간 (r9, 2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[데이터]+[실행] 슈터 발사음의 Weapon_AttackFocused/Weapon_InsLimit_00..03은 AGST 제한기 종류0이다. 그룹의0.016은 동시발음개수가 아니라 핸들에 복사하는 정지 시간(초)이다. 제한기가 있는 다른 그룹은 종류1..4의 정렬과 앞쪽 limitCount 생존 규칙을 쓴다. Priority만으로 모든 종류의 순서를 설명하면 틀린다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon3 v0 Lby_Lobby00. `extracted/exefs/main.reloc.img` SHA256 `39a8c94826d84b6106f112f2db16f7b2e2743bc6afd72054534a7708a9848a41`. AGST 원본 데이터와 이전 시작 순번 writer는 [sound_resources.md](sound_resources.md) §4.3/4.3.2를 재사용한다. 이번 새 근거는 `analysis/decomp/r9_sound/limiter_wrapper.c`, `envelope_update.c`, `aal_thread_clock.c`, `envelope_spatial_eval.c`, `slink_runtime_params.c` 및 r9 native 결과다. r5 종류1/600건·r6 순번2,445건을 신규로 다시 세지 않는다.

## 3. 진입점과 전체 호출 흐름

[판독] 기존 그룹 로더3837384가 GRP[0x21]→group+1B8, 재생383d14c가 값≥0일 때 group+1B8→wrapper+1C로 복사한다. 새37dfd10/37e019c가 wrapper+1C를37f9790에 넘긴다. 새37f9790→37f8fec는 원본 풀에서 stop/volume/envelope 명령을 생성하고 실제37e3fec 큐에 넣는다. positive duration은1/duration 진행률을 쓴다. 새 원본 오디오 스레드37e1834는 SDK 렌더러 카운터의 차이를f32×0.005하여 aal+30/+40에 쓴다. 새37ee58c는 명령 종류에 따라30/40을S0로 읽고 실제37fdd18→37e9be8로 전달한다.37fdd18은 Ghidra 실패했으므로 해당 연결은 원본 명령 판독이다.

제한기 전체38473e8은 각 실제 vtable sort 종류1=3847950,2=3847c6c,3=3847f84,4=38481f4를 호출하고 그 순서로 해제/억제를 적용한다. r9에서는 이 네 sort와 실제383cffc/383d940/383da0c→37dfde4/37dfd10/37e019c까지 실행했다.

## 4. 구조체·필드·상수·열거형 표

| 기준 | 필드 | 원본 의미 | 근거 |
|---|---|---|---|
| group | +1B8 | 정지 duration 기본 override. 슈터 해당 그룹 f32(0.016) | [데이터]+[판독] |
| wrapper | +1C | group 기본 정지 duration, 초 단위 | [판독]+[실행] |
| limiter | +8 / +C / +D / +E | limitCount / hard / 비교 guard / timer사용 | [판독]+[실행] |
| limiter | +10 / +14 / +18 / +28 | timer기간 / 억제비트 / 활성 bool / 경과시간 | [판독]+[실행] |
| voice | +8 | 풀의 시작 순번(id), 0은 빈칸 | 기존 r6 [실행] 재사용 |
| voice | +C4 / +CC | SLink Priority×runtime P+D4 / 별도 제한 스케줄 우선순위 배율 | [판독]+[실행] |
| voice | +210→+18 또는 +180 vt38 | normal listener 집계 AUDC 배율 / 외부공간 override 반환값 | [판독]+[실행] |
| runtime P | +D4 / +D8 / +BA | reset시1.0 / 0 / 0 | 새3885564 [실행] |
| envelope | +10/+14/+18/+20/+24 | 곡선종류/진행률/1.duration/시작값/목표−시작 | 새37f8fec [실행] |
| aal | +30/+40 | 렌더러 tick 차이×f32(0.005), 명령 갱신 dt | 새37e1834 [판독]+block[실행] |

## 5. 상태 전이와 전체 수명

[판독]+[실행] limit<0은 정렬하지 않고 해당 억제비트 해제, 모든 억제비트가0이 되면 wrapper state3→4이며 종류2의 cursor24=0이다. limit0은 보호 voice+1F8 bit1과 wrapper kind0을 제외하고 억제한다. limit>0은 정렬 후 보호보이스를 제외한 앞 limitCount개를 생존시킨다. voice state6/7은 순위 slot을 소비할 수 있지만 억제/해제의 상태 변경은 건너뛴다.

hard는383d940(0,0), soft wrapperkind1은 정지, 다른 유효 kind는 억제비트를 세우고 처음 억제될 때 pause이다. kind2,wrapper+8=null fixture에서 state1→3만 하고 cursor/18은 유지했다. timer가 꺼져 있으면 elapsed28=−1/active18=false. 기간0 timer는 elapsed−1/active=true. positive timer는 elapsed≥0일 때 SystemParam+1C dt를 더하고 기간에 도달하면−1; 새 soft pause가 해당비트를 세우면 elapsed=0으로 재시작한다. timer와 음원 정지 duration은 다른 필드다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행] priority key는 `trunc(f32(f32(f32(C4*CC)*factor)*255))`. normal factor는 새38655dc의 listener별 `max(f32(weight*AUDCout18))`. class가−1이면 weight1, 그 밖에는 listener+58의 class별 값이다. 시작SLink38868e4는Param14 Priority(default0.5)→handle94; 기존3887e3c는 pending82 또는 인자 bit6일 때 `p=f32(handle94*P_D4)`가0..1이면voiceC4에 쓴다. 새3885564 reset은P_D4=1. 범위 밖/NaN은 이전C4 유지하며0..1 강제 clamp가 아니다.

새38485ac는 별도 대기목록 스케줄러다. 지연 대상 state2에 `CC=f32(CC*limiter18)`과 `C8=f32(C8*limiter14)`를 쓰고 다음 대상의 배율도 다시 곱한다. 원래 생성CC=1만 보고 전수 재생 내내1이라고 놓으면 안 된다. 이 함수는 판독이며 r9 수치 실행 대상으로 확대하지 않았다.

종류1은 priority 내림차순/동률순번 오름차순, 종류2는 priority 내림차순/동률순번 내림차순이다. 종류3/4는 순번이 우선이고 역/정 order와 priority 동률 비교를 사용한다(기존§4.3.1 guard식 재사용). state6/7·다른 억제비트·현재 timer의 guard값에 따른 key 조정도 보존한다. 종류1/2의 순번 차이는32bit 원본 뺄셈이라 wrap 직후 이상 순서도 그대로 둔다.

정지 duration≤0은 즉시 stop command이다. duration>0이면 원본 `rate=f32(1/duration)`, `t=min(f32(t+f32(rate*dt)),1)`, output=`f32(start+f32((target-start)*curve(t)))`. curve0/default=t,1=f32(t*t),2=sqrtf(t),3=sinf(f32(t*0x3FC90FDB)). 0..2는 새 원본 실행,3은 원본 명령 판독만 했다. t가1이 되는 호출은 return0, 다음 갱신에서 return1이다. renderer 한 tick dt=f32(0.005)이면 duration0.016은4번째에t=1,5번째에완료return1; SDK 실제 오디오 버퍼의 청각상 종료시간을5×0.005로 단정하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

슈터의 관련 그룹 값0.016과 type0은 기존 원본AGST 데이터다. 새 CPU 정지 duration consumer가 이름 InsLimit을 실제 동시발음제한으로 해석할 근거가 없음을 확정한다. SLink 사용자 LimitType/PlayableLimitNum은 별도 consumer 질문이며 이 그룹값과 섞지 않는다. 모든XLink 상태나PCM 파형 선택을 이 제한기 성공으로 확정하지 않는다.

## 8. 다른 기능과의 상호작용

[판독] 새38655dc는 listener output의 FarFx와 filter도 별도로 집계한다. output18→aggregate18의 AUDC 우선순위가 이번 질문이고, output10→모든기본/override 필터 선택은 [sound_runtime_filters.md](sound_runtime_filters.md) §11의 별도 미확정이다. native timer의 dt는 Alto SystemParam+1C, 최종 stop command dt는 aal renderer clock이다. 둘을 모두60Hz로 대입하면 틀린다.

**정정(2026-10-03):** 과거 group+1B8 reader3121ca4는 PingPongDelay interface(PU+B0)+1B8=fullPU268 MaxDelayTime의 내부주소3121c8c다. 실제 group reader383d238로 정정했다. 과거0.016의미·2..4 sorter/timer 미실행은 이번 새전체실행/판독으로 해소한다. 과거 'Priority낮은것부터정지'는 종류3/4의 순번 우선과 guard를 빼먹었으므로 위 종류별 규칙으로 정정한다. 이전 기록을 삭제하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

impl/fx 기록에 필요한 변경: 모든 그룹 type/count·guard·timer를 원본 순서대로 적용하고,Priority×P_D4×CC×listener AUDC 배율을 보존한다. 순번은 기존 풀 writer 기준이다. 슈터 그룹 정지 기본값은0.016초이며 명시 duration≤0 즉시정지 및별도StopTime 인자를 우선한다. 전역 임의10ms 램프로 통일하지 말 것. renderer5ms clock과 게임 timer60Hz 입력을 분리한다. 웹 코드와impl은 수정하지 않았다.

## 10. 검증 코드·실행 결과·기대값

| 새 실행 명령 | 결과 | 원본 경계 |
|---|---|---|
| `.venv/Scripts/python.exe web/tools/r9_sound_limiter_apply_emu.py` | 4종 각1024=4096경우,168710필드/2906정렬/4096timer,0bad | mutex만no-op; 원본stop/pause/fade함수실행. wrapper8=null,ownerD8=null이라DSP/owner콜백없음 |
| `.venv/Scripts/python.exe web/tools/r9_sound_stop_envelope_emu.py` | 생성768/시계block6/진행10284/22824필드,0bad | 원본풀/큐/curve0..2. 렌더러counter명시fixture, 마지막SDKaudio-stop미실행 |
| `.venv/Scripts/python.exe web/tools/r9_sound_priority_chain_emu.py` | 2048SLink→8192집계→2048비교/94208필드,0bad | stub없음. listener출력/weightfixture,curve평가·외부voice180은이전근거/별도경계 |

모두null0/fault0/auto_map0이다. 첫 limiter 대조297bad는 `sound_limiter_apply_first_failure.json`으로 보존했다. 원인은 kind2+h8null pause의state1→3/cursor유지를 독립 참조가 정지로 잘못 처리한 것이다. 원본을 바꾸지 않고 참조를 정정했다. priority script 첫실행은seed십진문법SyntaxError였고0x938655dc로 수정했다.37fdd18 Ghidra실패는보존하고raw명령으로reader를확인했다. 실제 명령·실패 목록은 `analysis/completion/r9/sound_commands.md`이다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

[미확정] SLink User LimitType/PlayableLimitNum 전체consumer, 모든런타임P_D4 변경API의상위요청, voice180 custom spatial객체의공급, 필터종류P_D8의reset밖writer/전체필터선택, 모든FarFx버스연결, SDK실제PCM buffer/DSP response. 수식의 인자 P_D4/factor를확정된default1로전재생내내고정하지않는다. 이 문서가닫은 고정질문은4종제한기동작·정지0.016의초단위·AUDC/Priority제한기연결이며 '모든사운드완료'로확대하지않는다. 다음3864fe0/3863788의공간provider,3885590/3884de0 runtime setter,37fb028/SDKstop최종DSP이다.
