# 논리 카메라 행렬 → 렌더 UBO·뷰포트·출력 경로 (r10, 2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행] 일반 카메라의 논리 View/Projection이 실제 gsys 뷰 레코드와 `Context` UBO를 거쳐 로비 정점 셰이더로 전달되는 경로를 연결했다. 원본 UBO 선언은 **34멤버·2,336바이트**이며, View는 `Context[0..2]`, Projection은 `Context[7..10]`이다. 이 Projection은 CameraModule의 **논리 행렬**이고 `M26c` 장치 행렬을 이 경로의 GPU 입력으로 대체하면 원본과 달라진다.

2026-10-03 정정: [player_camera.md §6.7·11](player_camera.md)의 과거 기록은 `vt60` 장치 행렬을 뒤에 계산한다는 이유로 최종 그림의 행렬도 그 값일 수 있다고 남겼다. 계산 자체는 맞다. 이번 렌더러 소비자·실제 UBO 선언/작성자 연결로 **여기서 확인한 일반 gsys/로비 셰이더 경로는 논리 Projection을 사용**함을 확정한다. 과거 기록을 삭제하지 않으며 live `5997898`을0으로 확정하지 않는다.

신규 원본 실행은 **1,042건, 불일치0**이다. 실제 파생 framework의 present vtable 함수까지 포함한다. 다만 원본 GPU의 초기 swizzle 상태, 실제 Lby의 최종 출력 텍스처 provenance 및 physical display는 실행하지 않았다. 따라서 고정 질문12·31과29에 묶인 최종 화면 부호의 **전체 해소로 승격하지 않는다**. 확정 구간과 남은 경계는 §11에 적었다.

2026-10-03 후속: 위1,042건과 별도로 생성자·렌더 타깃 어댑터 **64건, 불일치0**을 확인했다(누적1,106건). [판독]+[데이터] 정상 진입점 `nnMain3445900`의 framework 생성·실제 vtable·초기220/223·window 생성·worker 제출, Device window-origin=1 공급자, HDR fullscreen triangle의 실제 정점/인덱스 공급을 연결했다. **같은 프레임 HDR 출력 텍스처→window image28**과 초기 GPU swizzle은 아직 연결되지 않았다. 사용자 요청에 따라 여기서 추가 탐색을 중단하고 현재 근거만 반영한다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon3 v0, Lby_Lobby00 1인 연습의 일반 카메라/로비 렌더 경로. 원본은 `extracted/exefs/main.reloc.img`, `extracted/exefs/sdk.img`이다. Main 축약 주소에는 `0x7100000000`을 더한다. **SDK 주소는 모듈 내 offset**이다. 에뮬러의 SDK base `0x7400000000`은 검사용 배치이며 원본 런타임 ASLR 주소를 확정한 값이 아니다.

새 분석 전에 SHARED/FUNCS 및 `decomp_index.py`로 중복을 확인했다. 기존 `1010de0`, CameraModule 전체, `36b2574`의 cached C, HDR1120eac와 로비/HDR 셰이더 추출은 재사용했다. 장치 자세 BSS/raw0·r9 writer scan은 이미 분석된 근거이므로 다시 신규 성과로 계상하지 않는다.

새 C: `analysis/camera_100_r10/posture/{context_projection,render_view,context_submit,context_declare,context_descriptor,context_layout,viewport,present,present_crop,frame_submit}.c`. SDK는 raw 명령·동적 심볼·동적 RELA·API 이름 표를 판독했다. 새 실행/감사 JSON은 같은 `posture/` 디렉터리에 있다. 원본/키·웹 소스·impl은 수정하지 않았다.

후속 C10묶음은 같은 위치의 `next_{frame_init_target,framework_factory,framework_window,fullscreen_init,graphics_task,render_system_init,fullscreen_geometry,fullscreen_buffers,native_window,fullscreen_bind_helpers}.c`다. 새 실행은 `next_frame_native.json`, 인계 기록은 `next_notes.md`·`next_commands.md`·`next_functions.tsv`·`next_recommendations.json`이다. 기존 분석과 후속 성과를 별도로 기록하고, 중앙 SHARED/FUNCS/inventory 수정은 상위 작업에서 수행한다.

## 3. 진입점과 전체 호출 흐름

### 3.1 일반 카메라 → gsys → 로비 셰이더 [판독]+[실행: 구간]

```text
활성 Spectator/poser → CameraModule1010150 → 1017434
  M190 = LookAt 객체, M220 = Perspective 객체
  M22c = 논리 행렬, M26c = 장치 행렬
1010de0 (기존 원본): viewport/view index로
  viewport entry+18=M190, +20=M220
  env object+78=M190, +80=M220
36c9198: 활성view+620 bit0 검사 → env+5c8 → 주/대체 View·Projection 선택
  → 36b2350(view, slot0/1/2, viewMatrix, projectionObject, previousView)
36b2350: row stride430에 View(+0), prev(+60)를 저장
  → 3624cd0(row+60의 frustum base, projectionObject)
3624cd0: 실제 Perspective VT57213b8의 dirty update
  → 36242b0(near/far/FOV/aspect, frustum, projectionObject+0C 논리 행렬, offset)
36242b0: frustum+60, 즉 row+C0에 논리 행렬 저장
36ceec4: active와recordcount 검사, row마다
  → 36b2574(view, i, row+0, row+C0, row+60, 0, rendererFlag)
36b2574: Context 선언에 따라 View@0, Projection@70 복사
로비 정점 셰이더: Context[0..2]·world → view
                   Context[7..10]·view → clip.xyzw
```

`3624cd0`은 장치 dirty가 있으면 장치 행렬도 갱신하지만, 마지막 소비 호출의 포인터는 항상 `Projection+0c`다. dirty==0이면 이전 행렬을 보존한다. 함수 전체 실행32건에서 논리/장치 dirty4조합×posture8값을 검사했다. CameraModule 전체의 이미 확정한 계산식은 [r10_module_projection.md](r10_module_projection.md)를 재사용한다.

### 3.2 Context 선언의 실제 생산자 [판독]+[실행]

```text
367a110: singleton59994b8 생성/반환
367a43c: singleton+8 UBO에36b563c 호출
36b563c → 35b78ec: descriptor34개 할당/초기화 → 실제 원본 필드 선언
36ae130: *(singleton+18) descriptor를 각row+3a0에 배정
          *(singleton+40) size를row+3c8에 배정
36b2574: row+3a0 descriptor의 offset/type로row+3a8 CPU buffer 작성
```

`36ae130`의 env 개체 초기화는 r6의 기존 근거다. 이번 신규 해석은 Context descriptor 배정 부분이며 기존 env 분석의 재실행 성과로 세지 않는다.

### 3.3 부가 draw-context 및 native 출력 [판독]+[실행: 구간]

`117230c`는 manager+2f0의 context 리스트를 순서대로 방문한다. `param2==0`이고 현재 scene==param3일 때만 local Perspective를 만들고 **slot24+i**로 `36b2350`에 넘긴다. Main slot0의 일반 포저 생산자로 오인하지 않는다. caller `110dbf8`의 tail B가 이 함수를 호출한다.

HDR1120eac는 viewport/scissor/depth를 직접 설정하고 원본 HDR 합성을 수행한다(기존 근거). 공통 `358b9d0` 역시 `358baf4`의 사각형 변환 후 Scissor→Viewport→DepthRange를 호출한다. 마지막 `3503410`은 output 상태50==2·window140+10!=0일 때 선택 callback→`nvnQueuePresentTexture`→조건부 `nvnWindowAcquireTexture` 순서다. 아직 일반 Lby의 동일 프레임 HDR 출력 텍스처와 이 window index를 전체 task lifecycle로 연결하지 않았다.

[판독]+[데이터] framework의 draw·queue submit·present는 다음 실제 vtable로 연결된다. 기존 `3502e18`의 C는 재사용했고 `35032d8`과 파생 present `3d98c6c`를 새로 판독했다.

| vtable | draw +e8 | submit +f8 | present +100 | wait/crop +110 |
|---|---|---|---|---|
| 571eed8 | 3502e18 | 35032d8 | 3503410 | 35036b4 |
| 55552c8 / 56734a0 / 5762010 | 3d98c5c→3502e18 | 3d98c64→35032d8 | 3d98c6c | 3d98c68→35036b4 |

```text
3502e18: BeginRecording → method tree/render callbacks → EndRecording
  command handle을framework+1e8에저장
  framework+220==0이면vt+f8 (35032d8 / tailB3d98c64)
35032d8: framework+223!=0검사 → mutex lock →+221=1
  embedded+228의vt+10이false이면
    nvnQueueSubmitCommands(queue+1b0,1,&handle+1e8)
  true이면embedded+228의vt+0에위임
  QueueFenceSync → QueueFlush → command/control사용량최대값갱신
  self vt+100 → base3503410또는derived3d98c6c → mutex unlock
```

위 흐름은 원본의 호출·데이터 계약이다. `3d98c6c`의 전체 gate40건을 추가 실행했고 base40건과 일치한다. vtable 주소의 코드 xref는 destructor에서도 발생하므로 이 데이터 표만으로 실제 로비 frame object의 생성·선택까지 확정하지 않는다. `+220`이0이 아닌 경우의 worker submit과 HDR 출력 텍스처 생산자는 별도로 남는다.

### 3.4 정상 부트의 framework·window 생산자 — 2026-10-03 후속 [판독]+[데이터]

위§3.3의 생산자 미연결 기록을 정정한다. `nnMain3445900`의 직접 호출 `3445b90→3501dbc`와 생성자 이후 store를 추적했다. 원본 정상 부트 코드는 다음 순서다. 이는 전체 nnMain 부트를 실제 실행했다는 뜻은 아니다.

```text
nnMain3445900: framework 0x368바이트 할당
  초기 params: interval1, clear(.5,.5,.5,1), window1920×1080
  →3501dbc(self,params): 기본VT571eed8, flags220=0x01000001
  →첫파생VT5762010 →global580e5e8에self공개 →최종VT56734a0
  →350205c(self,heap,0,logicalSize1280×720)
350205c: NV graphics/VI 초기화·default display/layer/native window 생성
  →350df08: graphicscontext 생성 →59978a0
  queue→framework1b0 및context38
  windowwrapper(size0x68,VT571f8d0)→framework140 및context50
  →windowVT+10=350d42c: NVN window·texture 배열 초기화/첫Acquire
  commandbuffer→framework170 및context40
  worker1d0(size0xe0,VT5720f88), callbackwrapper(VT571f060)
     callback=3502c08(self): selfVT+f8로BR
     실제56734a0+f8=3d98c64→35032d8→present
```

`350205c`는 API/장치 초기화 실패·SDK 버전 불일치 등의 조기 반환을 포함한다. 정상 부트의 window 기본1920×1080과 전달한 논리1280×720은 서로 다른 필드이며, 실제 Lby의 매 프레임 내부 렌더 해상도나 동작 모드 변경 후 크기를 이 초기값으로 확정하지 않는다. `+220==1`의 worker callback 자체는 원본 간접 분기3명령으로 연결했으나 스레드 전체 스케줄링을 실행하지 않았다.

`350df08`은 NVN `DeviceSetWindowOriginMode(Device,1)`의 실제 cell `57d53d8`을 호출한다. 기존 SDK `4a72f0→Device+0`와 viewport `4c8210`의 분기에 연결되어 **정상 초기화 코드가 origin1을 공급함**을 확정한다. 합성 입력이나 BSS0으로 만든 결론이 아니다. 이후 모든 런타임 writer의 부재·GPU swizzle 기본값·CameraModule `5997898`의 값까지 이 근거로 확정하지 않는다.

### 3.5 출력 window 이미지의 생산자와 남은 HDR 경계 [판독]+[데이터]

실제 window `VT571f8d0+10=350d42c`는 wrapper+30/+38/+40에 NVN texture2개 또는3개를 생성한다(개수는+51). NVN window builder에 native VI handle+48과 이 texture 배열을 전달하고, 만든 native window(size0x180)를 wrapper+18에 저장한다. 첫 `AcquireTexture(window18,sync20,&image28)`가 표시 image index를 생산한다. 따라서 window140/image28의 **표시 측 생산자→기존 present 소비자**는 연결됐다.

HDR1120eac의 render target 인수 `param3[5]`는 `35a83f4`가 실제 NVN color/depth handle로 풀어 `SetRenderTargets`에 전달한다(§6.5). 그러나 이 render target의 color slot이 **해당 wrapper+30 배열의 image28 texture와 같은 것인지**는 아직 생산자/소비자 연결을 얻지 못했다. 동일 API·색상 포맷·전역 graphicscontext 공유만으로 동일 texture라고 승격하지 않는다.

## 4. 구조체·필드·상수·열거형 표

| 기준 객체 / 필드 | 의미·형식 | writer → reader |
|---|---|---|
| CameraModule M190/M220 | LookAt/Perspective 객체 | ctor·1017434 → 기존1010de0 |
| Env+78/+80 | View/Projection 객체 포인터 | 기존1010de0 →36c9198 |
| Env+1f8 | 대체 카메라 포인터 | 이번 writer 미추적 →36c9198 |
| Env+8a | 主/대체 선택 u16 | 기존 경로 재사용 →36c9198 |
| Renderer+5245 bit3 | 대체 카메라 사용 중 이전view를主view로 유지 | 이번 writer 미추적 →36c9198 |
| View+620 bit0 | 활성 여부 | 이번 writer 미추적 →36c9198/36ceec4 |
| View+10/+18 | record count / array | 36ae130 →36ceec4/36b2574 |
| Row+0/+60/+c0 | 현재view/이전view(frustum base)/논리projection raw matrices |36b2350/3624cd0/36242b0 →36ceec4/36b2574 |
| Row+390 | UBO 객체, 실제 VT57221a8 |36ae130 →36b2574; VT+18=35b810c(return256) |
| Row+3a0/+3a8/+3c8 | declaration descriptor / CPU buffer / size |36ae130·35b7a30 →36b2574 |
| Row+421 bit0 | UBO 갱신 gate | 기존 생성/dirty 경로 →36b2574; param6 bit0가 force |
| Projection+8/+9 | 논리/장치 dirty byte | 기존 모듈 →3624cd0 |
| Projection+0c/+4c | 논리/장치4×4행렬 | 실제 VT58/60 →3624cd0 소비자는+0c |
| Projection+8c/+90/+94 | posture/ZScale/ZOffset | 생성·복사 →device 계산; live posture 공급 미확정 |
| Context+40/+42/+4a | width/height/type u16 | 기존 draw context →117230c |
| Context+4c4/+4c8/+4cc | near/far/FOV f32 | 이번 writer 미추적 →117230c local Perspective |
| Rect+8/+c/+10/+14 | left/top/right/bottom f32 | caller →358baf4/358b9d0 |
| Rect+18/+1c/+20 | posture u32 / depth near/far f32 | caller →358baf4/358b9d0 |
| Target+8/+c | 논리 너비/높이 f32 | caller →사각형 normalize |
| Target+10/+14/+18/+1c | 출력영역 left/top/right/bottom f32 | caller →사각형 scale/translation |
| NativeCmd+0/+8/+60 | command write pointer / end / SDK Device | SDK init/recording →NVN packet writer |
| SDK Device+0 | window origin mode integer | SDK DeviceSetWindowOriginMode+4a72f0 →4c8210의Yscale 분기 |
| Output+50/+140/+158/+a6 | state/window/callback/acquire policy byte | frame framework →3503410 |
| Window+18/+20/+28 | native window/sync/image index | acquire/frame →3503410 |
| Window+52/+54..60 | crop dirty byte /4개crop값 | 이번 writer 미추적 →35036b4→WindowSetCrop, dirty=0 |

2026-10-03 후속으로 확인한 필드:

| 기준 객체 / 필드 | 확정된 생산자와 의미 | 한계 |
|---|---|---|
| Framework VT / global580e5e8 | nnMain: 기본571eed8→5762010→실제56734a0, size368 | 전체 부트·후속 파생 교체 미실행 |
| Framework+220..223 |3501dbc의u32=01000001: async220=1,221=0,222=0,enableSubmit223=1 | 후속 live flags는§5의별도계약 |
| Framework+224/+225 | 생성자u16=ff00: pending224=0,225=ff | pending producer 전수 미연결 |
| Framework+50 | 생성자0; 기존3502d10에서1이면2로전이 | state1 writer 미연결 |
| Framework+140/+1b0/+170/+1d0 |350205c window/queue/commandbuffer/worker | 정상 코드의 생성 연결, 실제 driver 객체 미실행 |
| GraphicsContext+38/+40/+50 |350205c가동일queue/commandbuffer/window alias 저장 | HDR 출력color의동일성증명아님 |
| Window+10/+50/+51 |350205c 초기enable1/interval1/texture개수2또는3 | 이후enable/크기 writer 미확정 |
| Window+18/+20/+28/+30..40/+48 |350d42c nativewindow/sync/acquiredindex/texturearray/nativeVIhandle | 현재 HDR target→array 연결 미확정 |
| Global5999220 |3602bb0에서size31f8 singleton 생성,3602c8c ctor | fullscreen 공급자는§6.5 |
| Fullscreen+338/+370/+37c/+388 |3605e58 vertexbuffer,position/normal/UV format29/29/11,byteoffset0/6/12 | HDR 실제정점buffer, stride16 |
| Fullscreen+458/+460/+464/+480/+488 |index descriptor /indexformat0/primitive값/count3/nativebuffer |1120eac 실제사용,quad count6과구분 |
| RenderTarget+20..58/+60 | color8slot/depth texture포인터 |35a83f4→NVN handle/view 변환 |

Context에서 처음4개 멤버의 원본 선언/실행 결과:

| index | UBO byte offset | 모양 | shader 대응 |
|---|---:|---|---|
| 0 | 0x000 | 3×4 f32, type6 | View `data[0..2]` |
| 1 | 0x030 | 4×4 f32, type6 | ViewProjection `data[3..6]` |
| 2 | 0x070 | 4×4 f32, type6 | Projection `data[7..10]` |
| 3 | 0x0b0 | 3×4 f32, type6 | 역view `data[11..13]` |

나머지30멤버의 원본 count/offset/columns/type는 `ubo_native.json`에 있다. 이 문서는 그 의미를 임의로 모두 명명하지 않는다.

## 5. 상태 전이와 전체 수명

[판독] 카메라 객체 자체의 시작·리셋·종료는 기존 [r10_module_projection.md](r10_module_projection.md) 및 [r9_lifecycle.md](r9_lifecycle.md)에 연결한다. 여기서는 렌더용 상태 수명만 추가한다.

- Context descriptor singleton은 없을 때만 `367a110`에서 생성된다. 새 renderer row는 그 descriptor를 공유하고 별도 CPU buffer를 가진다. 단순 매 프레임34개 멤버 재생성이 아니다.
- Perspective의 dirty8/9를 소비하면 해당 갱신 후 clear한다. `3624cd0`의 최종 copy는 dirty와 무관하게 논리+0c를 전달한다.
- 비활성view는 선택 및 submit을 건너뛴다. UBO writer는 Row421 bit0 또는 force6 bit0가 없으면 출력버퍼를 보존한다. native96건에서 active/force와param7 양쪽을 검사했다.
- Native present는 state50==2와window enable 조건을 충족해야 호출한다. callback 뒤 window140을 다시 읽는다. a6이0일 때만 같은 wrapper가 acquire한다. base3503410 및 actual derived3d98c6c 각각40건, 전체80건의 gate/호출순서를 검증했다.
- `35036b4`의 하단은 window52 crop dirty가 있으면 WindowSetCrop를 호출하고0으로 지운다. scheduler·sync wait·crop writer·실제 window수명은 이 단독 present 실행으로 검증하지 않았다.

2026-10-03 후속 [판독]: 기존 `analysis/decomp/r5_ui/frameflag.c`의 `3502d10`은 재사용했다. `222&3!=1`인 경로에서 pending224=1이면223=1, pending224=2이면223=0으로 쓰고 처리한 pending을0으로 지운다. `state50==1`이면2로 바꾼 뒤 실제VT의 draw/calc/wait/crop 등을 호출한다. 따라서 생성자 초기220/223과 **그 이후223 전이 소비자**를 구분한다. pending224의 모든 live 생산자와 최초state1 생산자는 미연결이며, 단독 생성자의flags를 매 프레임 불변으로 일반화하지 않는다.

## 6. 계산식·조건·상세 의사코드

### 6.1 실제 Projection 선택과 UBO 복사 [판독]+[실행]

```text
if !(view620 & 1): return
env = view5c8
mainView = env78 ? env78 : object5999258
mainProjection = env80 ? env80 : object59992c0
useAlt = (env8a & 0x21)!=0 && (env8a & 2)!=0 && env1f8!=null
if useAlt:
    currentView = alt+10                 # alt+8 View 객체의matrix+8
    projection = *(alt+160)
    previousView = (renderer5245 & 8) ? mainView+8 : alt+10
else:
    currentView = mainView+8
    projection = mainProjection
    previousView = mainView+8
for slot in [0,1,2]: 36b2350(view,slot,currentView,projection,previousView)

# 3624cd0: whole original actual vtable updates then
36242b0(near,far,FOV,aspect,frustum,projection+0c,offset)
frustum+60 = logicalProjection4x4       # row+60+60 = row+c0

# whole36b2574, actual descriptor/VT:
if row421.bit0 || force6.bit0:
    Context[0..2]  = currentView3x4     # 원본 raw f32 비트 그대로
    Context[7..10] = logicalProjection4x4
    # VP/inverse/나머지값도 원본 작성; 새 독립비트대조 범위는 위copy/gate
```

`117230c` local aspect는 width=max(u16(ctx40),1), height는 type3이면 원시u16(ctx42), 그 밖에는 max(height,1)이다. **type3·height0의+Inf를 보존**한다. FOV는 전체각이며 sin/cos/tan(FOV×0.5)의 원본 SDK를 사용한다. Projection8c에는 원본 global5997898을 복사하지만 이 local 값을 main live posture로 일반화하지 않는다.

### 6.2 로비 정점·HDR의 좌표식 [판독, 기존 shader 재사용]

`analysis/gfx4/programs/FldBG_LobbyDV__CeillingEmi.vert`는 worldXYZ를 Context0..2에 FMA로 곱하고, 그 viewXYZ를 Context7..10에 FMA로 곱해 gl_Position.xyzw를 만든다. UBO 선언/작성자의 새 offset70 근거가 이 번호와 정확히 연결된다. 이 한 재질 검증을 모든 skin/VAT 셰이더의 CPU/GPU 전면 검증으로 확대하지 않는다.

HDR의 모든 변형 공통 vertex식과 CPU coefficient는 [stage_rendering.md §3.2](../graphics/stage_rendering.md)를 재사용한다.

```text
clip.x = aPosition.x * 2
clip.y = aPosition.y * 2
uv.x = fma(u,C0.x,v*C0.z) + C1.x
uv.y = fma(u,C0.y,v*C0.w) + C1.y
C0 = (1,-0,0,1); C1=(0,0,0,0)       #1120eac의 원본 즉시값
```

이 coefficient 자체는 X반전/XY교환을 만들지 않는다. 그러나 fullscreen primitive의 실제 attribute 공급 및 마지막 texture/window 연결 전체를 이번 native 검사로 실행하지 않았다.

2026-10-03 후속 정정: 실제 fullscreen attribute 공급은 §6.5에서 **[판독]+[데이터]로 연결**했다. 전체 GPU/HDR draw를 native 실행한 것은 아니며 마지막 texture/window 경계는 계속 남는다.

### 6.3 Rect posture 변환과 NVN viewport [판독]+[실행]

Rect=(l,t,r,b), w=f32(r−l),h=f32(b−t), Target 논리크기=(W,H)일 때 `358baf4`의 원점:

| posture | x | y |
|---|---|---|
| 0 및 switch밖 | l | t |
| 1 | t | f32(f32(H−w)−l) |
| 2 | f32(f32(W−h)−t) | l |
| 3 | f32(f32(W−w)−l) | f32(f32(H−h)−t) |
| 4 | f32(f32(W−w)−l) | t |
| 5 | l | f32(f32(H−h)−t) |

원점은 x/W·outputWidth+outputLeft, y/H·outputHeight+outputTop 순서다. posture1/2는 viewport의 w/h도 교환한다. `358b9d0`은 normalize→scale한 높이와원점으로 bottom origin Y를 만들고, x/y를 **FCVTZS signed**, width/height를 **FCVTZU unsigned**로 절삭한다. C decompiler의 int형만 보고 마지막 두 값을signed로 일반화하지 않는다. 상세 f32 참조식은 `r10_camera_shake_viewport_emu.py`이다. 음수영역에 임의 clamp나 자연스럽게 보이는 보정을 추가하지 않는다.

### 6.4 실제 SDK NVN 명령 패킷 [판독]+[실행]

Main의 NVN loader083eb80(기존 판독)는 이름으로 받은 함수포인터를 cell에 저장한다. SDK bootstrap 원본은 다음 경로다.

```text
SDK4e9820(nvnBootstrapLoader)
 →4ace50 staticcbaa78의resolver4a71f0
 →cd3c70의resolver4acc20
 →'nvn' prefix검사·532개 sorted name binary search
 →profile/current table 또는 fallback tablecd2bc0의index포인터
```

새 실행은 SDK debugger init guardD99F94=1, profileD99FB0=0, current tableD99F60=0을 **합성 입력으로 공급**하여 fallback9개의실제 이름을 검증했다. 실제 플랫폼 부트의 이 값들을 확정한 것은 아니다. SDK RELATIVE10,777개와 defined-symbol23,349개 재배치는 검사용 RAM에서만 적용했다.

| API | SDK 함수 offset | 원본 명령 계약 |
|---|---:|---|
| CommandBufferInitialize | 49bc80 | buffer80B를 포함0으로초기화, device+1a18 bit0를cmd15에복사 |
| CommandBufferBeginRecording | 49c060 | suppliedcontrol memory에16B header; swizzle packet 직접작성없음 |
| CommandBufferSetViewport | 4c8380→4c8210 | xScale=f32(width×0.5),xTranslate=f32(x+xScale) |
| CommandBufferSetDepthRange | 4c84d0→4c83c0 | 원본 depth 범위 패킷 |
| CommandBufferSetScissor | 4c8770→4c8640 | 원본 scissor 범위 패킷 |
| CommandBufferSetViewportSwizzles | 4c8500 | 아래4×3bit packed GPU method |
| QueuePresentTexture | 4b98b0 | 이름/주소만 연결; native API 전체실행아님 |
| WindowSetCrop | 4b9510 | 이름/주소만 연결; native API 전체실행아님 |

`4c8210`의 yScale은 Device+0==1이면 `height×−0.5`, 그밖에는 `height×+0.5`다. **X배율에는 그분기가 없다.** 1280×720 fullrect에서 device origin0/1/2에 따른Xscale 비트는 모두 `0x44200000`(640), Yscale은 각각`0x43b40000/0xc3b40000/0x43b40000`(±360)이다. 같은 SDK 구현을 실행하는 지원 범위의 packet검증이지 Maxwell 출력의 검증은 아니다.

`4c8500`의 입력4개 enum a/b/c/d는 각각3bit만 남기며 `packed=(a&7)|((b&7)<<4)|((c&7)<<8)|((d&7)<<12)`이다. GPU method header는 `0x20010000 | ((0xa18+0x20*viewportIndex)/4)`다. 예시`(0,2,4,6)→0x6420`, `(1,3,5,7)→0x7531`. 이검사에서 그패턴을 **실제 Lby의초기 swizzle**이라고명명하지않는다. viewport setter 자체가 이method를작성하지않는다는 원본경계도 보존한다.

### 6.5 HDR fullscreen 실제 정점과 render-target 어댑터 — 2026-10-03 후속

[판독]+[데이터] `37a6440`의 render-system 초기화가 `3602bb0`의 singleton 생성/반환 후 `3605924`를 호출한다. `3605924`는 square `3605a14`, fullscreen triangle `3605e58` 등을 초기화한다. HDR1120eac가 읽는 vertex+338 및 index descriptor+458의 공급자는 **3605e58**다.

| 정점 | position XYZ | normal XYZ | UV |
|---|---|---|---|
|0|(-0.5,+0.5,0)|(0,0,1)|(0,0)|
|1|(+1.5,+0.5,0)|(0,0,1)|(2,0)|
|2|(-0.5,-1.5,0)|(0,0,1)|(0,2)|

인덱스는 **[0,2,1]**, 원본 draw count는 **3**이다. `360e800`은 position half3→bytes0..5, normal half3→6..11, UV half2→12..15의stride16을 공급한다. half 변환 함수는 `360fe20`, vertex/index buffer initialize는 `35b8c9c`/`35a7eb8`다. 이 경로는 원본 명령과 상수 판독이며 변환기의 모든 부동소수점 입력이나 GPU vertex fetch를 실행 대조한 주장은 아니다.

기존 HDR shader의 clip.xy=position.xy×2에 결합하면 정점은 `(-1,+1),(3,+1),(-1,-3)`이고 UV.x는 clip.x와 함께 증가한다. **실제 fullscreen attribute 공급과 CPU coefficient에서 추가 X반전은 없다.** 일반 square의4정점·6인덱스를 HDR의 실제3정점 대신 사용했다고 해석하지 않는다. 마지막 sampling 대상과 GPU state의 미확정은 유지한다.

[실행32]+[판독] `35a83f4(ctx,target)`는 ctx+f0에target을 저장하고 color8슬롯과 depth를 원본 texture-manager59979f8의 descriptor table에서 NVN handle로 변환한다. 각 texture+60 index가−1이면 건너뛰고 texture+B8를 view로 전달한다. color count는 **마지막 유효 slot+1**이며 중간 구멍은0으로 보존한다. depth도 같은handle/view 규칙이다.

```text
35a83f4 →cell57d61d8 nvnCommandBufferSetRenderTargets
         →각 유효color3594120 및depth3594350 transition
         →조건을충족하면barrier
```

새32건은8개 color-mask×invalid-last2×depth유무2 조합이다. SetRenderTargets·transition·clock은 검사용 경계에서 capture/공급했고 실제 driver/texture contents는 실행하지 않았다. 순서와 handle/view/count 변환을 확인한 결과이며 **target 자체가 window image라는 증거는 아니다**.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

플레이어 입력·활성포저·모듈의근거는 [r10_input_response.md](r10_input_response.md), [r10_module_projection.md](r10_module_projection.md), 쉐이크는 [r10_shake_shooter.md](r10_shake_shooter.md)를사용한다. 이번현재View는 이미쉐이크를월드위치에합산한M190이므로GPU에서쉐이크를새로더하지않는다.

LOBBY재질·HDR shader파일은기존추출을읽었다. 새shader변환·VFX·음향리스너를실행하지않았다. 도색/캐릭터의각재질프로그램모두를새97건UBOcopy로검증했다는주장은하지않는다.

## 8. 다른 기능과의 상호작용

Env대체카메라·previousView설정은 현재표시와전프레임행렬의용도가다름을보인다. framebuffer postprocess/temporal기능에서둘을혼용하면같은pose라도화면이어긋날수있다. 그러나그대체조건의모든live writer나로비에서의활성빈도는새fixture의합성flags로확정하지않는다.

draw-context slot24+i는모델/추가context의투영이며일반주카메라slot0..2와구분한다. 큐브맵localProjection5997a78·parent의36d174ccopy는별도경로다. offsets가같다고모든projection객체를M220로명명하지않는다.

Output35036b4의sync/frame wait·crop는3503410의present gate와분리했다. 원본async 대기정책을웹requestAnimationFrame과같다고해석하지않는다.

## 9. 웹 포팅 구조와 구현 순서

이번요청은분석·MD만이다. 웹/impl코드는수정하지않았다. 향후반영할내용:

1. CameraModule의View객체와논리Projection객체를원본index에결합하고, 일반렌더 경로의GPU입력은논리행렬로유지한다.
2. 주/대체View와previousView의조건을분리한다. `env8a&0x21`·bit1·alt포인터와keepPreviousbit3를각각보존한다.
3. Context레이아웃은View0..2/Projection7..10의row 배열순서를그대로검증한다. 웹/Three 이름은권장명일뿐원본클래스명이아니다.
4. viewport와canvas framebuffer의픽셀영역 변환을분리하고, resize/aspect갱신시점은parent모듈문서의후행dirty계약을따른다.
5. HDR는기존원본coefficient식·actualshadervariant에맞춘다. liveposture가미확정이라는이유로마우스X반전이나임의행렬교환을추가하지않는다.

| 웹권장상태명 | 원본대응 | 검증인터페이스 |
|---|---|---|
| renderViewCurrent | row+0/Context0..2 | 12f32 rawbytes |
| renderProjectionLogical | row+c0/Context7..10 | 16f32 rawbytes |
| renderViewPrevious | row+60 | 별도current/previous선택 |
| projectionLogicalDirty / projectionDeviceDirty | Projection8/9 | 각각clear/보존 |
| renderViewportRect | Rect/Target | pixelrectangle와행렬반전구분 |

실제GPU최종화면과의대조가남아있으므로이표를웹반영완료나물리화면동일성완료로표시하지않는다.

## 10. 검증 코드·실행 결과·기대값

아래명령은`C:\dev\splatoon3`에서실제로실행했다. Python실행파일은`.venv/Scripts/python.exe -X utf8`, Bash는`C:/Program Files/Git/bin/bash.exe`다.

| 도구·결과JSON | 신규원본실행건수 | 결과/경계 |
|---|---:|---|
| `r10_camera_shake_posture_emu.py` →bridge_native.json |696| provider504,rendererselector144,submit16,logicalconsumer32;0불일치 |
| `r10_camera_shake_ubo_emu.py` →ubo_native.json |97| descriptor1+wholeUBOwriter96;0불일치;copied View/Projection비트·gate대조 |
| `r10_camera_shake_viewport_emu.py` →viewport_native.json |152| viewport72+basepresent40+actualderivedpresent40;0불일치;NVN API capture |
| `r10_camera_shake_sdk_nvn_emu.py` →sdk_nvn_native.json |97| bootstrap9+init/begin4+swizzle36+gamewrapper→SDKpacket48;0불일치;API stub0 |
| **합계** |**1,042**|별도합성입력의원본구간검증;전체Scene/GPU/실제device부트실행아님 |

2026-10-03 후속 실행은 위 합계에 중복 합산하지 않고 별도로 기록한다.

| 후속 도구·결과JSON | 이번신규건수 | 결과/경계 |
|---|---:|---|
|`r10_camera_shake_next_frame_emu.py`→next_frame_native.json:3501dbc|32|8fps×4tick,VT/flags/params50B/tick3slot/f32timing 비트 일치|
|같은도구:35a83f4|32|8mask×invalid-last2×depth2,handle/view/구멍/count/호출순서 일치|
|**이번후속합계**|**64**|**불일치0**;기존1,042는재실행·재계상하지않음|

생성자 tick-frequency5997960=19,200,000과 target-manager59979f8의 descriptor/handle은 **합성 입력**이다. clock 공급96회, SetRenderTargets capture32회, color/depth transition capture78/16회다. JSON의 SDK_stubs/non_SDK_stubs 사전이 비어있더라도 이 boundary capture와 공급이 없다는 뜻은 아니다. whole-original 함수의 제어·저장·변환을 실행했으며 실제 nnMain 전체 부트·driver 할당·HDR shader draw·표시 장치는 실행하지 않았다.

후속 실제 명령과 실패/정정은 `analysis/camera_100_r10/posture/next_commands.md`에 전부 정리했다. 새 C10묶음 모두exit0, 새native64건 첫 실행에서0불일치다. `bl_callers.py` 및 NVN map의 축약 주소 입력이 처음 빈 결과/None을 반환했으나 **전체0x710... 주소로 정정**해 정상 caller/API를 얻었다. 첫 빈 결과를 경로 부재 근거로 사용하지 않았다. func_lookup350da78은 이전350d42c를 반환했으므로 raw350da78 prologue로 함수 시작을 정정했다.

bridge696의경계capture:36b2350=384회,36b2574=12회,36242b0=32회,rendererhelpers367c688/371e014/36f5158/371121c=144회씩·367c814/374e580=72회씩.SDKsin/cos/tan각168회원본명령실행. guardacquire/release각3회경계대체. vtable/dirty갱신은원본이다.

UBO97는원본35b78ec까지실행하고allocation83d2f0두회만검사용heap으로대체,SDKmemcpy72회동등copy경계다. 역행렬fa6fd4·원본FMA계산도실행하지만새독립비트대조의주장은View/Projectioncopy와gate에한정한다. GPUflush는row3b8=0조건이며실제GPUupload를검증하지않는다.

viewport152는NVNScissor/Viewport/DepthRange각72회,present8회,acquire4회,선택callback4회capture다. SDK97는게임→actualSDKcommandwriter사슬에**스텁0**,원본코드패치0이다. supportedpositive rectangle의X/Yscale부호와fullrectpacketbit를대조했다. SDKdebugger/liveprofile원본초기화는별도합성입력경계다.

추가실제명령:

```text
web/tools/func_lookup.py <주소>
web/tools/decomp_index.py <주소>
web/tools/disasm.py <주소> -n <명령수>
web/tools/xref.py addr/str <주소/이름>
full_decomp.sh .../context_projection.c 117230c 36b2350 358baf4
full_decomp.sh .../render_view.c 3624cd0 36c9198
full_decomp.sh .../context_submit.c 36ceec4 36242b0
full_decomp.sh .../context_declare.c 36ae130
full_decomp.sh .../context_descriptor.c 367a43c 367a110
full_decomp.sh .../context_layout.c 36b563c
full_decomp.sh .../viewport.c 358b9d0
full_decomp.sh .../present.c 3503410 35034b4
full_decomp.sh .../present_crop.c 35036b4
full_decomp.sh .../frame_submit.c 35032d8 3d98c6c
web/tools/r10_camera_shake_posture_scan.py
web/tools/r10_camera_shake_nvn_audit.py
analysis/r5_camweapon/sdk_dis.py <SDKoffset> <hex byte수>
analysis/camera_100_r10/posture/sdk_backend_probe.py
```

위C10묶음은저장성공. 366096c(`gsys_context` bindinglookup)는cached`render/r3_batch1.c`가있어서`full_decomp`가skip했으며새context_ubo.c를생성하지않았다. bindingname검색을UBO작성자근거로혼동하지않았다.

실패와정정도남긴다.

- 첫bridge참조식은altView+8로예상해실패했다. 실제원본은alt객체+8View객체의matrix+8,즉**alt+10**이다. 참조식을고친뒤696일치;원본코드수정아님.
- SDKbootstrap첫실행은RELATIVE만적용해`strcmp`PLT가미결정되어UC_ERR_FETCH_UNMAPPED였다. definedsymbolRELA23,349개까지RAM에서올바르게적용해실제SDKstrcmp를실행한뒤97일치. PLT를Pythonstrcmp로우회하지않았다.
- func_lookup117230c/11723dc는이미끝난11720a0,size620을반환했고,3503af4/35036b4는끝난3503410,size164를반환했다. 실제prologue/ret를읽어117230c 및**crop35036b4**로정정했다.35034b4는posture를사용하는renderbufferclear다.
- PowerShell의일부`rg` glob경로·존재하지않는projection_copy_chain.c/render_pipeline.md/sdk_dis.py경로검색실패는실제존재파일로정정했다.일부SDKdisasm인자를잘못나눠0x4ac부터과다출력했으며분석근거로사용하지않았다.문자열NUL표현실수로과다출력한읽기명령도NUL바이트split으로정정했다.

사전후보scan은unsignedSTRW8c총498개·dirty8/9근접28개·draw-context4c4/C8/CC근접14개다. 이는동일객체증명아니다. 네이티브NVN audit의ADRP8-instruction직접참조후보는clobber검사로false3개를제외했다. 보완scan은**GOT페이지577a000을참조하는main ADRP17,185개**에서base변경/branch/128명령전까지+48 직접memref를읽어swizzleloader8419b0한곳만찾았다. aliases/arithmetic/inlineprivatepacket/GPU기본값부재로확대하지않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 고정질문 | 이번에확정한구간 | 전체상태 / 남은근거 |
|---|---|---|
|12 스틱오른쪽→최종화면좌우| 활성포저/모듈기존근거→logicalrenderer→actualContextUBO→로비clip식;viewportXscale양수원본SDKpacket | **[미확정] 부분추적**: GPU초기swizzle/default·sameframeHDR/출력texture/windowindex 연결·nativeactualframe |
|29 스틱X응답식+잔여화면부호| 응답식r10입력기존해소,위렌더경로신규 | **[미확정] 복합질문부분유지**:12/31잔여를분리계상하여전체확정하지않음 |
|31 원본↔웹좌우최종대응| 논리행렬을device행렬로대체하는가정은이번에정정;UBO/셰이더/viewport계약확정 | **[미확정] 부분추적**:물리화면·웹축최종대응에는남은nativeGPU/output경계필요 |

현재확정한CPU경로의live값을임의추측하지않는다. 특히`5997898`rawBSS0,SDKcurrenttable/profile0의합성fallback검사,SDKswizzle입력(0,2,4,6)의packet6420은**실제사격장초기값확정자료가아니다**.

다음독립근거:

1. 2026-10-03 후속 정정: 정상 `nnMain3445900`의 생성자3501dbc→최종VT56734a0/global580e5e8→350205c의window/worker 생성,220초기async1·223초기enable1·worker3502c08→VTF8,window350d42c의texture배열→Acquire image28은 해소했다. 남은 것은 **실제 같은 프레임 HDR1120eac의param3[5] target color→해당window texture[image28]** 연결이다. 다음은 기존112c604→1120eac 인수생산자 및 render-target 할당/교체 경로다. pending224·state1의 live 생산자도 아직전수연결되지않았다.
2. SDKQueueInitialize4b33c0→4b25f0의 초기 명령을 읽고 backend context 생성4bb970까지 연결했다. DeviceInitialize4a7270의 resolver 경로4ac150→4abf90→4d0210→4d2050도 읽었다. `4d2050`은 Device+1b20 객체+20의 vt+28을 호출해 얻은 버퍼에 SDK상수 블록들을 복사하지만, 그 버퍼를 viewport swizzle의 초기 GPU state라고 확정할 type/method 연결은 얻지 못했다. bounded 발췌는 `sdk_backend_probe.md/json`에 보존했다. 다음은4bb970·4d2050의 backend virtual 수신자와 GPU context 초기 상태다. SDKSetViewportSwizzles4c8500은 명시적인 패킷 형식만 확정했고 live 호출 부재/기본값 전면 부재는 증명하지 않았다.
3. Main`_nvnPrivate0`inlinepacket경로의관련method작성자를검사한다. directGOT조사는alias/연산포인터/inlinepacket을포괄하지않는다.SDKbootstrapfallback/profiletable의실제부트선택도필요하다.
4. 2026-10-03 후속 정정: 정상 graphicscontext350df08의DeviceSetWindowOriginMode(1) 공급자와37a6440→3605924→3605e58의HDR attribute 공급은 해소했다. 남은 backend GPU 초기swizzle는4bb970 및4d2050의virtual수신자·private method A18 writer에서 추적해야한다. field scan의 unsigned LDRX2af8=1/STRW480=137/STRB220=65/223=4/224=18개는 **타입 미증명 후보**다. 유일LDR2af8의24fb6e4는render-HDR객체동일성증명없이사용하지않으며, static부재·BSS0으로live상태를채우지않는다.
5. 최종좌우의 CPU 계약은 남은 원본 task/command/default state 사슬을 전부 연결하면 코드로 더 확정할 수 있다. 따라서 capture가 무조건 필수라고 단정하지 않는다. 다만 현재근거에는 texture 연결과GPU초기state가 빠져있고 **실제 rasterization·physical display 및 픽셀 동일성**을 검증하지않았다. 이부분을입력fixture 건수만으로동일하다고선언할수없으며 실제GPU capture는독립검증방법이다. 사용자종료요청에따라이번에는위주소를다음근거로남긴다.

본문의partial추천은분모축소·질문쪼개기·일부결과전체확정승격을피하기위한것이다. 전체확정률갱신은고정inventory를보유한상위작업에서수행하며이문서가그수치를임의작성하지않는다.
