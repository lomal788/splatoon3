# ColPaint 묶음 생성·연결 좌표·크기 분할

## 1. 기능 개요

U/V 띠를 공유 패널로 이어 묶음을 만든 다음, 실제 좌표로 펼쳐 크기를 측정한다. 한도를 넘으면 먼저 띠 단위, 다시 개별 패널 단위로 분할한다. 이 문서는 buildGroupWithDir와 묶음 분할의 전체 분기를 [판독]으로 확정한다. 연결 자체를 생성하는 기하 조건은 panel_connections의 별도 질문이다.

## 2. 원본·자료

main.reloc.img v0. SHARED/FUNCS/decomp_index를 먼저 대조하고 기존 미판독 `analysis/decomp/paint4/colpaint_r2.c`의 2c01420/2c01e58/2c02124/2c02750/2c00878/2c00d6c/2c03338/2c03cdc/2c04f48와 2bfa500/2bfa760를 끝까지 읽었다. 장면 writer의 새 디컴파일은 `analysis/decomp/r8_graphics/scene200_writer.c`와 `mission_table_fields.c`, `panel_connector_core.c`이다. 2026-10-03 정정이다.

## 3. 호출 흐름 [판독]

2c01420 → U/V 패널 ID별 map 구성(2c02124) → 연결 전체 순회(2bfa500/2bfa760) → 각 방문의 2c02750 → 공유 띠 추가(2c01e58). 이후 2c03338는 group index마다 2c00878로 좌표를 펼치고 크기를 검사하며, 최종 보존 목록을 2c04f48로 정렬한다.

## 4. 구조·상수 [판독]

| 구조 | 실제 필드 |
|---|---|
| holder | +20 group index RBtree, +50 최종 index 수, +38/+40 보존 목록, +48 목록 수, +60 분할 띠 목록 |
| group node 60B | +20 index, +28/+30 두 띠 포인터, +38 공유 panel ID, +48/+50 같은 index의 chain |
| 띠 | +8 32B ring entry 배열, +10 capacity/+14 start/+18 count, +20/+24 크기 |
| 띠 entry | +0 panel, +8..1C 2×3 패널 좌표 행렬 |
| U/V map row 40B | panel ID의 하위16bit 키, +28 띠, +30 할당 group index(초기 −1) |
| 펼친 group | +20 32B 띠 entry 배열, +28/+2C/+30 capacity/start/count, +8/+C 최종 크기 |

한도는 각각 `8*max(ceil(sceneSize),1)`이다. sceneSize는 §9의 실제 문자열 비교에서 200 또는 400이다. +3의 양쪽 여백으로 최종 크기는 펼친 bbox+6이다.

## 5. 순회·group 할당 [판독]

2c01420의 bool=false는 U 목록, true는 V 목록을 순회한다. 어느 쪽이든 root의 V-map group index로 이미 배정되었는지를 검사한다. 2bfa500은 root(direction=−1), 방향2 사슬, 3 사슬, 0 사슬, 1 사슬 순서로 들어간다. 재귀 callback 2bfa760은 0→1→2→3이다. panel+A8 방문 byte로 순환을 막고 전체 배열 방문 flag를 지운다. global58F07B8+2C0+2BC bit0 취소가 순회와 정리를 중단할 수 있다.

방문 callback은 U/V-map의 group index를 현재 index로 쓴다. U 띠는 패널에 2/3 연결이 있을 때, V 띠는 0/1 연결이 있을 때 공유 node를 만든다. 같은 group chain에 동일한 전체 panel ID가 이미 있으면 추가하지 않는다. callback이 node를 하나도 만들지 않으면 root의 연결 방향에 맞는 U/V 띠를 택하거나 현재 순회 띠 자체로 single node를 만든다. index는 node마다가 아니라 root 순회마다 한 번 증가한다.

## 6. 띠 배치와 변환식 [판독]

2c03cdc는 chain의 +28 뒤 +30을 읽어 null을 제외한 서로 다른 띠 포인터를 모은다. count는 패널 수가 아닌 띠 수다. 첫 띠는 identity, 둘째는 공유 panel ID로 정렬한다. 나머지는 chain을 반복해서 훑어 한쪽이 이미 배치되고 다른 쪽이 아직 없을 때만 추가한다. 둘 다 있거나 둘 다 없으면 건너뛴다. 연결되지 않은 입력에 임의 좌표를 주는 fallback이나 반복 횟수 상한은 이 경로에 없다.

2c00d6c는 공유 ID의 하위16bit를 각 띠 ring에서 찾는다. 못 찾으면 원본4AA2B1C 행렬을 사용한다. source 패널의 V 열을 부모 행렬로 옮긴 벡터 w와 새 띠 패널의 V 열 v를 각각 길이가 양수일 때 정규화한다. `c=dot(w,v)`; `c+1 >= 1.1920929e-6`이면 v.y==0일 때 s=w.y/v.x, 아니면 s=(v.x*c−w.x)/v.y다. 그 밖은 c=−1,s=0이다. 회전은 `(c,−s;s,c)`, 이동은 부모가 옮긴 source 이동−회전한 target 이동이다. 원본의 0 곱셈과 각 float 연산을 보존한다. NaN/부호0에서 이를 이상적인 회전식으로 단순화하지 않는다.

각 띠의 네 모서리를 bbox에 합친 뒤 min을 −min+3만큼 옮긴다. height<width일 때 90도 회전해 폭/높이를 바꾼다. 원본 cos90은 −4.371139e−8이며 0으로 치환하지 않는다.

## 7. 크기 분할 [판독]

폭 또는 높이가 한도보다 **엄격히 클 때** 분할한다. 같은 크기는 보존한다. 두 축은 현재 scene query를 별도로 다시 읽어 검사한다.

- 띠 count>1: constituent 띠 각각에 새 index를 부여하고 +30=null인 single group node를 추가한다.
- 띠 count==1이고 그 띠의 panel count>1: 패널마다 identity entry 하나인 48B 띠를 만들고 2bfe07c로 크기/좌표를 계산한다. 새 띠를 holder+60에 보관하고 새 group index를 추가한다.
- oversize인 1띠1패널이나 0띠: 펼친 group 객체를 해제하고 보존 목록에 추가하지 않는다.

새 index가 holder+50을 늘리므로 같은 루프가 새 group도 처리한다. 이에 따라 띠 분할 뒤에도 한도를 넘으면 패널 분할까지 진행한다. 옛 RBtree의 group node가 즉시 제거되는 것은 아니다. 삭제되는 것은 이번 펼친 객체이며 보존 목록에는 들어가지 않는다. 적합한 group만 보존 목록에 들어간다.

## 8. 최종 순서 [판독]

2c04f48는 보존 목록을 max(width,height)가 큰 순서로 안정 정렬한다. 같은 크기는 원래 순서를 유지한다. 이 함수를 분할 group의 제거 함수로 해석하면 안 된다. 최종 패킹 및 전체 로비 GPU 실행은 별도다.

## 9. 200/400 장면 문자열 [판독]+[데이터]

2026-10-03 정정: 초기 빈 FixedSafeString64만 확인하여 +E0의 writer를 미확정으로 남긴 과거 기록을 보존한다. 2f686c4 생성자의 **indexed store**까지 읽어 writer를 찾았다. 2997c34의 자원 키는 `spl__MissionStageTable`이고, 2f25190이 **BigWorldSceneName → resource+78, flag+DA**를 명시한다. 생성자 i=1은 상속 플래그를 따라 +78 경로를 가져와 38a41d8로 경로의 basename을 추출하고 manager의 `+88+i*58 = +E0`에 쓴다. 경로 입력은 127자, destination은 63자로 잘린다.

2f24704 기본 생성자의 +78은 **Work/Scene/BigWorld.engine__scene__SceneParam.gyml**다. 원본 Singleton MissionStageTable의 추출 JSON에는 BigWorldSceneName override가 없다. 따라서 v0 기본 비교 문자열은 **BigWorld**다. SmallWorldSceneName는 resource+C8로 첫 번째 destination+88이며 +E0가 아니다. 200을 SmallWorld나 사격장 고유 최적화로 붙이지 않는다.

2c03338/기존 atlas 생성자들은 scene getter1323040의 +2D8 문자열과 manager+E0를 같다고 비교할 때 200, manager/scene가 없거나 다르면 400을 쓴다. **Lby_Lobby00는 BigWorld와 다르므로 이 조건에서는 400, 분할 길이 한도 3200**이다. mode나 스토리의 실제 동작까지 조사한 결론으로 확대하지 않는다.

## 10. 웹 반영과 미확정

impl/paint.md/assets.md의 단순 group 연결 및 고정 크기 근사는 공유 패널 변환·bbox+6·안정 정렬·엄격한 두 축 한도·띠→패널 재분할·BigWorld 비교로 바꿀 필요가 있다. 이번 작업은 분석만 하며 impl/코드는 고치지 않았다. 연결을 처음 생성하는 세 functor와 strip 기하식, 최종 atlas packing 및 GPU scene 전체 실행은 별도 미확정이다. group 전체를 Unicorn으로 실행한 것으로 표기하지 않는다.

## 11. 검증·명령·실패

SHARED/FUNCS 검색, decomp_index --no-build, func_lookup 및 disasm으로 위 시작 주소를 확인했다. cached r2의 group 9함수와 네 방향 순회 전체를 판독했다. full_decomp scene200_writer.c(2997c34/38a41d8), mission_table_fields.c(2f248bc/2f25190), panel_connector_core.c(2f24704 포함) 신규 성공. func_lookup2bf3f10은 앞 함수 끝으로 잘못 묶어 disasm의 sub sp prologue로 교정했다. 2f67d7c는 Scene manager 아닌 Missionstate라 제외했다. xref.py의 숫자 단독 호출은 invalidcmd였고 `xref.py str BigWorldSceneName` 및 실제 경로 문자열로 정정했다. 실패와 명령 전문 분류는 analysis/completion/r8/paint_commands.md 및 graphics_commands.md 참조. [판독]/[데이터]이며 원본 group 실행·전체 로비 실행은 미시행이다.
