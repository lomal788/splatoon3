# 사격장 동적 광원 격자의 CPU→GPU 경로

## 1. 기능 개요

원본은 XZ 20×20 격자와 최대30개 광원 레코드를 만들고,각셀에 먼저 들어온 최대4개의 8비트 광원번호를 쓴다. 실제 manager→accumulator→UBO member→GPU upload를 연결해 기존 CPU기록자 미확정을 해소했다 [판독]. 점광원 삽입8192건,격자설정2048건,CPU/8멤버upload384건이 비트 일치했다 [실행].

## 2. 원본·근거

Splatoon3 v0 main.reloc.img. SHARED/FUNCS/decomp_index/func_lookup 대조 후 새 `analysis/decomp/r8_graphics/dynamic_light_main.c`,dynamic_light_manager.c,dynamic_light_providers.c,dynamic_fill.c,dynamic_grid_upload.c,dynamic_grid_insert.c,dynamic_grid_cells.c,dynamic_cone_hairinfo.c를 읽었다. 생성15멤버 결과 `analysis/completion/r8/dynamic_ubo_layout.tsv`; 도구 `web/tools/r8_gfx_dynamic_ear_emu.py`,r8_gfx_grid_insert_emu.py; 결과dynamic_ear_emu.json/grid_insert_emu.json.

## 3. 호출 흐름 [판독]

1045f18이 DAT5810020에 manager를 설치한다(GOT5792048). manager+58=accumulator,manager+1078=member holder. 1046928이 holder초기화·reset·writer와6provider를 만든다. 갱신1046f20은10450e8 reset→enabled2570이면provider목록+28..50의순서대로byte8 검사/vt50호출→1045218이원본값을member에복사한다. member vt18이GPU mappedbuffer에쓴다.

정정(2026-10-03): 예전5810020+1398을rawshaderdata배열로가정하고+35F8/+3608 동시store를찾은방법은 틀렸다. +1398은manager+1078+320의UBO하위객체다. CPU값은member별+38과별도배열stride에있고upload가변환한다. 후보29b6698/34da0c8/34dc9dc/369bf40과이번+1410스캔후보들은 다른상태머신·디버그·agl lightmap객체였다.

## 4. 필드·GPU 대응 [실행]+[판독]

accumulator와holder 기준을구분한다. 원본104601c 생성·각member vt10 선언을실행해아래오프셋을얻었으며 기존shader읽기위치와일치한다. GPU data[i]는16B vec4다.

| acc offset·원본형 | holder member/value | GPU byte/data[i] | upload |
|---|---|---|---|
| +2B0,u32[400] | +3A0/+3D8 | 0/[0..399].x |10471E4 |
| +8F0,rgba[30] | +A18/+A50 |1900/[400..429] |1047434 |
| +AD0,att4[30] | +C30/+C68 |1AE0/[430..459] |1047684 |
| +CB0,xyz[30] | +E48/+E80 |1CC0/[460..489].xyz |10478D4 |
| +E18,dir3[30] | +FE8/+1020 |1EA0/[490..519].xyz |10478D4 |
| +F80,i32[30] | +1188/+11C0 |2080/[520..549].x |1047B3C |
| +1010,origin3 | +1238/+1270 |2260/[550].xyz |1047D8C |
| inverse(+FF8 cell3) | +1280/+12B8 |2270/[551].xyz |1047D8C |

u32[400]/i32[30]은GPU에서 각16B stride다. xyz는CPU12B→GPU16B. 미사용padding은upload가쓰지않는다(합성초기A5 유지 실행확인). 나머지7member도생성했다:552vec4×4,556.x/y scalar,557vec3,558vec2,559vec4×4,563vec3. 전체15member의최종cursor2340=9024B. 이뒤7개칸의화면의미는별도미확정이며임의값을넣지않는다.

## 5. reset·우선순위 [실행]+[판독]

10450e8은count101C=0,grid400u32=FFFFFFFF,rgba30=(1,1,1,1),AD0부터528B=0으로쓴다. 1010/FF8의grid설정은reset에서지우지않는다. provider는등록순서다. 104560C는count<30이고 최소1cell에새번호를넣었을때만색·감쇠·위치·방향·종류를기록하고count++한다. 전체관련cell이차있으면새광원은count를소모하지않는다. 거리순정렬이나가까운4개로교체하지않는다.

## 6. 격자·점광원 식 [실행]+[판독]

1044F90:cell성분이[-2^-23,+2^-23] 안이면1,다른음수/NaN을임의양수로고치지않는다. extent=(20*cellX,cellY,20*cellZ),origin=GridOffset−extent*.5. 1151A74는RenderingParam vt70→DynamicLight(+30ptr,flag5B)→GridSize3C(flag48)/GridOffset30(flag49)를상속해결하고manager+1050/+1068(=accFF8/1010)에같은식을쓴다. 초기cell=(10,1,10),extent=(200,1,200),origin=(-100,-.5,-100). 로비GridOffset0/GridSize(10,1,10)의200×200은원본식과데이터로확정한다.

10457DC는position xyz의NaN을거부하나cell선택에는Y를쓰지않는다. local=(pos.x-origin.x,cellY*.5,pos.z-origin.z). cx/cz=floor(local.xz/cell.xz),rx/rz=ceil(radius/cell.xz). x가바깥,z가안쪽인inclusive범위를순회하고0..19만허용한다. cell중심=((x+.5)*cellX,cellY*.5,(z+.5)*cellZ). type0 점광원은중심거리 < radius+max(cellX,cellZ)*0.70710677이다. 엄격한부등호를보존한다.

셀index=z*20+x. 기존u32의최상위byte가FF이면 `new=(old<<8)|lightIndex`,아니면차있으므로유지한다. 순서0,1,2,3이면 FFFFFF00→FFFF0001→FF000102→00010203. shader의byte읽는순서는stage_rendering§8의기존원본식을유지한다.

104560C는att=(1/radius,DistDamp,cos(angle),AngleDamp),world위치xyz를쓴다. direction은sqrt제곱합>0이면정규화,종류는입력i32다. 방향0은0으로남는다. 반경/위치이외NaN을자연스럽게제거한다는조건을추가하지않는다.

## 7. provider·spot [판독]

첫2provider(vt5556F38/5556FD8)는1049A58→vt58=1049B08/104A0C4,frame+44F8의actor목록경로는104AD3C→1048C3C/1048D98이다. 첫point는actor transform40world위치,actor배율24*transform70을radius,component color34..40*intensity44,damp30을104560C에넘긴다.

첫spot는위치40/48,방향=-transform열50/5C/68,radius=2*(actor배율24*transform74),angle=min(atan((actor배율24*transform70)/max(2*radiusRaw,2^-23)),pi),color34..40*intensity48,거리지수44/각지수30을넘긴다. 이raw필드의명명및rig보정전체는별도질문이다.

type1/2의cellcone은1048FA8이다. normalize(center−pos),normalize(inputdir),dot[-1,1]clamp→cos(angle) 비교. 원뿔밖이면cross(direction,dir)*sin(angle/2)와2cos(angle/2)의원본3×3식을만들고radius를곱해방향으로투영한길이를0하한으로제한하여distance<projectedRadius+cellMargin을시험한다. cross를단위화하는원본명령은없다. 이분기는[판독]이며점광원실행8192건에포함하지않는다. 임의의구/원뿔교차알고리즘으로바꾸어동등하다고하지않는다.

## 8. shader 연결

kind표4ABFDC8과member vt18이CPU의packed격자를GPU data[i].x로확장한다. shader는origin550/inverseCell551로XZcell을찾고cell4index,color400/att430/pos460/dir490/type520을읽는다. 감쇠·spot·specular의기존shader식은stage_rendering§8참조. 이번함수일치를전체scene/NVN프레임검증으로확대하지않는다.

## 9. 웹 반영 필요

impl/render.md/assets.md:두자료구조를구분해원본cell/radius판정,선착4/전체30,packedbyte,원본UBO offset/stride,att/dir/type을반영한다. 임시가까운광원정렬이나PBR감쇠를동등하다고취급하지않는다. 웹/impl은변경하지않았다.

## 10. 검증

`python web/tools/render_ubo_layout.py 0x710104601c 0x2b0 analysis/completion/r8/dynamic_ubo_layout.tsv`→15members/final2340. mutex초기화만외부stub.

`python web/tools/r8_gfx_dynamic_ear_emu.py`→48inputs의reset→CPUwriter→8member upload384건원본byte완전일치. stub은mutexinit/lock/unlock,mappedbuffer준비getter,memcpy/memset서비스뿐이다. upload변환은원본명령이다.

`python web/tools/r8_gfx_grid_insert_emu.py`→setting2048,point insertion8192,packed400cells/광원필드bitmatch. algorithmstub없음,cosf는별도Unicorn의원본SDK. 최초실행은SDK PLT주소를3E99BE30으로써FETCH_UNMAPPED,원본BL의3E9BE30으로고쳐통과했다.

## 11. 미확정·정정

2026-10-03 CPUwriter/GPUlayout/격자원점범위의이전미확정을위새원본으로해소했다. DampParam/DistDamp/AngleDamp/Radius/Scale의rig/actor생성→provider전체명명대응,비Dynamic GfxPointLight/SpotLight 사용여부,member552이후칸의의미,전체scene/GPU화면일치는계속조사한다. 다음:rigreflection2B9D88C/2B9DEF0/2B9E934/2B9F124,actorcomponentreflection,1048C3C/1048D98 writer,shaderbind1187A88.
