# ColPaint 패널 연결 생성·절단·띠 좌표

## 1. 기능 개요

connectPanel은 방향별 충돌 검색으로 후보를 얻고, 실제 삼각형의 공유 모서리를 판정해 연결 pair와 네 방향 인접 슬롯을 만든다. fixConnection은 특정 연결을 양쪽에서 끊는다. 띠 배치는 양쪽 모서리의 투영 차이로 이동을 맞춘다. 드라이버·후속 callback·띠 식은 [판독], 공유 모서리와 2D 투영 4,096건은 [실행]이다.

## 2. 원본·자료

v0 main.reloc.img. SHARED/FUNCS/decomp_index를 대조한 뒤 cached paint4 colpaint_r0/r1/r2의 2bf03d0/2bf2120/2bf22a8/2bf4750/2bf4a6c/2bf6cbc/2bf7784/2c057e4/2bff4c0/2bfa208/2bfd864/2bd7ec8/2bfe07c를 끝까지 읽었다. 신규 `analysis/decomp/r8_graphics/panel_connector_core.c`(2bf3f10/2bf71f4/2bf7310), `panel_connect_occupied.c`(2bf48b0), 실제 instruction disasm과 `web/tools/r8_paint_connect_geometry_emu.py`가 추가 근거다.

## 3. 순서와 검색 [판독]

2bf03d0은 panel+70 충돌 shape를 방향 목록에 넣는다. 바닥40의 elevation bucket은1, 천장41은6, 그 밖은 (d>>3)+1이다. azimuth bucket은 d&7이며 40/41은 이 목록에서 제외된다. 같은 shape는 목록 안에서 중복 추가하지 않는다. 7 elevation 목록과 8 azimuth 목록 각각의 occupied AABB를 합쳐 98B depth3 octree를 만들고 shape를 2be0868로 삽입한다. 모든 목록을 위한 master AABB/octree도 만든다. AABB에 임의 .1 여유를 더하지 않는다.

실제 functor 순서는 비40/41의 azimuth 검색(567CFE0→2bf6a9c→2bf3f10 mode0), 바닥40만의 elevation2/3/4 검색(567D088→2bf6cbc), 마지막 모든 패널의 elevation 검색(567D0F8→2bf6f84→2bf3f10 mode1)이다. 중복 확인 bitset은 pass/종류마다 다시 초기화한다. 이후 임시 octree/목록을 해제한다. 클래스 이름으로 7/8을 뒤집지 않고 이 실제 index식을 따른다.

2bf2120은 mutex 안에서 octree가 있으면111e8c4, 없으면 목록을 순회하여 shape vt20 충돌 callback을 호출한다. 2bf7784는 자기 shape를 제외하고 ColPaintPanel RTTI/user pointer를 검사하며 ID=FFFFFFFF나 이미 방문한 ID를 거른다. panel ID bitset은160 u32=5120bit이고 후보를 호출한 뒤 양쪽 bitset에 기록한다.

## 4. 공유 삼각형 모서리 [판독]+[실행]

2c057e4는 source 삼각형 정점0→1→2마다 상대 정점0→1→2를 순서대로 비교한다. float32 차이 제곱합의 sqrt가 **.001보다 작을 때** 일치한다. 첫 일치 상대 정점을 선택하고 두 source 정점이 일치하면 공유 모서리의 두 끝을 source 좌표 그대로 기록한다. 남은 bitmask의 첫 비트를 택해 양쪽 반대 정점을 내보낸다. 인자를 null로 주면 해당 출력만 생략한다. 퇴화 삼각형을 교정하거나 고유 정점으로 다시 매칭하지 않는다.

실행은 유한 비퇴화 삼각형, 공유 정점0..3개·순열·.0009/.001/.0011 주변 입력2,048건에서 반환값과 공유 모서리·반대 정점 바이트가 일치했다. 퇴화·NaN 전체 실행으로 확대하지 않는다.

## 5. 연결 방향과 점유 슬롯 [판독]

2bf3f10 mode0은 두 반대 정점의 Y 비교로 양쪽 slot0/1을 정한다. mode1은 panel+A0 root의 42방향에서 azimuth/elevation을 읽어 원본 벡터 `(cos(az)*sin(el),0,−sin(az)*sin(el))`의 반대 정점 차이 내적이 <=0이면slot2,그 밖slot3을 택한다. floor/ceiling의 az는−π/4, el은0/π; E2=.5890486,E3=.98174775,그 밖(E−2)*π/4다. 원본의 0 곱셈과 float 연산 순서를 유지한다.

두 `(slot+1)`의 곱이2 또는12일 때만 실제 직결 인접을 시험한다. 2bf48b0는 슬롯+8 byte가0이고 기존 이웃이 있으면 기존 pair를 2bf4750에 보존하고 양쪽 flag=1로 한 뒤 인접 포인터·모서리를 초기화한다. 기존 이웃이 없으면0,flag가 이미1이면1이다. 두 슬롯 상태와 이번 pair 성공 여부에 따라 pair RBtree의 해당 동일 방향 기록을 지운 뒤 새 직접 인접을 쓴다. 이 과정은 근접한 패널을 무조건 이어 붙이는 규칙이 아니다.

2bf4750는 같은 상대 panel과 같은 양쪽 slot pair가 있으면0,없으면2bf4a6c로 새64B pair를 만든다. pair+0/+8=두panel,+10/+14=양쪽slot,+18..2F=공유모서리,+30/+38=목록링크. 양쪽 panel+88 RBtree는 상대panel 포인터를 키로 같은 pair를 참조한다. 새 pair pool/두 tree node의 capacity guard를 그대로 둔다. 공유 모서리 성공이 없으면 slot−1/−1과 기본 모서리 `(0,0,0)→(1,0,0)`를 가진 pair를 시도하며 직접 네 방향 인접으로 바꾸지 않는다.

2bf6cbc는 동일 component를 제외하고 삼각형 공유 모서리들을 순회하여 반대 정점Y로0/1 방향을 택한다. 성공 pair가 하나라도 있으면 기본−1 pair는 추가하지 않는다. pair 기록과 방향 인접 기록을 구분해야 한다.

## 6. 연결 절단 [판독]+[데이터]

2bf22a8 첫 pass는 floor40 또는 d<8부터 +78 연결 component를 순회한다. 2bf71f4는 같은 panel을 중복 수집하지 않으며 전체 visited 목록과 이번 component 목록에 추가한다. 2bf7310은 이번 component 안의 패널에 대해 네 방향 인접의 상대가 component 밖이면 절단 목록에 넣는다. 순회 방문 표시는2beee9c로 초기화한다.

두 번째 pass는 P17의 네 방향 인접을 모두 끊는다. 그 밖 d24..31(40/41제외)은 slot2/3 인접이 있을 때 slot0/1도 끊는다. slot2/3 각각의 모서리 끝들을 panel U축으로 투영해 collisionBox U중심과의 절대거리 중 작은 값이 **du*.5*.75보다 작을 때** 그 인접을 끊는다. 경계 같음은 유지된다.

각 절단은 상대 슬롯도 지우며 모서리를 `(0,0,0)→(1,0,0)`로 초기화한다. opposite table499CAD8은 원본 `(1,0,3,2)` [데이터]이다. 연결 pair RBtree 전부를 삭제하는 것으로 확대하지 않는다. global58F07B8+2C0+2BC bit0 취소를 각 루프에서 따른다.

## 7. 띠 생성과 순회 [판독]

2bff4c0은 floor40 또는 d<8에서 component를 시작하여 이미 수집된 root는 건너뛴다. 첫2beebac 순회는 panel 수를 세고, 둘째는 정확한 count의32B ring entry를 채운다. 2beee9c는 두 순회 뒤 방문 byte를 되돌린다. 생성된 띠의 vt20을 불러 최종 크기/행렬을 계산한다.

방향별 이어 붙이기2bfa208은 root 먼저, mode0은0 사슬→1 사슬,mode1은2→3 사슬이다. 작은 인접 수에서 슬롯이 없으면 slot0을 사용하는 원본 fallback도 유지한다. group용 네 방향 순회와 공유 panel-ID 배치는 [panel_groups.md](panel_groups.md) §5~§7이다.

## 8. 띠 회전·모서리 투영 [판독]+[실행]

2bd7ec8은 같은 방향이면 정확한2×2 identity다. 다른 방향이면 두42방향 normal의 cross를 길이가 양수일 때 정규화하고 dot으로 acos 반각 quaternion을 만든다. dot<−1은반각π/2,dot>1은0,그 밖acos(dot)*.5다. 새 방향 U/V를 quaternion으로 옮겨 이전 방향 U/V에 투영한다. 첫2D 열을 정규화하고 첫 성분+1<1.1920929e−6이면(−1,0;0,−1),그 밖 `(c,−s;s,c)`다. source의 acos/cos/sin과 정규화 순서를 그대로 보존한다.

**2bfd864는 s0와s1의 2성분을 반환한다.** 디컴파일 C의 float 반환만 따르면 Y를 잃는다. 각 패널의 U/V basis에 모서리 endpoint p를 투영하고 mapBox 중심을 뺀 다음8배 한다. 부모/새띠 2×2 행렬을 각각 곱한 두2D좌표의 차이를 반환한다. 실제 `2bfd864..2bfda1c` disasm의 마지막 `fsub s0`/`fsub s1`이 근거다. 두 성분2,048건을 각각 바이트로 비교하여 일치했다. basis 및 SDK sinf/cosf도 원본 명령으로 실행했으며 알고리즘 stub은 없다.

## 9. 실제 띠 bbox [판독]

2bfe07c는 각 panel+54에 원래 방향+38을 쓴다. 첫 panel은 identity,폭/높이는 mapBox 크기*8을 양수에서 ceil하는 원본 float→int 규칙으로 얻으며 이동은그크기의절반이다. 다음 panel은 이전 회전에2bd7ec8 결과를 원본 순서로 합성한다. 기존 인접 slot1(인자bit0=0) 또는slot2(bit0=1)의 두 endpoint 각각을2bfd864로 투영하고, 길이가 더 짧은2D차이를 택한다. **동률은 둘째 endpoint**다. 선택차이를 이전 이동에 더한다.

폭/높이*8의 양수ceil 직사각형 네 모서리를 옮겨 bbox를 합치고, 모든 entry 이동에서 bbox min을 뺀다. 최종 bbox 크기도 양수ceil 규칙으로 쓴다. 이 단계에3픽셀 여유는 없으며, group 단계에서 별도로 bbox+6을 적용한다. 공유 panel로 다른 띠를 맞추는2c00d6c의 정확한 임계/변환식은 panel_groups §6에 기록했다.

## 10. 웹 반영과 남은 한계

impl/paint.md/assets.md의 단순 방향 유사성 연결과 회전 근사는 실제 shape→octree 후보·.001 공유모서리·slot/flag pair·component 절단·두성분투영·endpoint tie·8배ceil 순서를 반영해야 한다. 코드는 고치지 않았다. 이번 두 질문은 전체 함수 분기로 [판독] 해소하되 전체 로비 ColPaint 생성/최종packing/GPU raster 원본 실행으로 표기하지 않는다. 퇴화/NaN의 edge 실행 및 취소·allocation 실패 전체 실행은 미검증이다.

## 11. 실제 검증·실패

`decomp_index.py --no-build`,SHARED/FUNCS,func_lookup 확인 뒤 full_decomp panel_connector_core.c[2bf3f10,2bf71f4,2bf7310,2f24704],panel_connect_occupied.c[2bf48b0] 성공. cached octree driver·fix·sharededge·strip·rotation·projection 전체를 판독했다. func_lookup2bf3f10/2bf48b0는 앞 함수 끝에 잘못 묶어 실제 sub sp prologue/ret로 새 시작을 확인했다. 2bfd864의 C 단일 float는 disasm으로 2D반환을 교정했다. `python web/tools/r8_paint_connect_geometry_emu.py` exit0:shared_edge2048+strip_endpoint_2D2048 mismatch0,opposite=(1,0,3,2). 결과 analysis/completion/r8/paint_connect_geometry_emu.json. commands.md는 앞선 실패·잘못된중간fragment 제외도 보존한다.
