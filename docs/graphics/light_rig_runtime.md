# SpotLightRig의 데이터·뼈·런타임 광원 대응

## 1. 기능 개요

로비 낮 환경의 SpotLightRig8개는 Fld_VSLobby 모델의 Dynamic_SpotLightA..H 뼈에 연결된다. 켜진 1,2,5,6,7만 동적 광원 입력에 들어간다 [데이터]+[판독]. 원본 뼈행렬 소비→SpotLight 필드 기록→동적격자 입력을2,048건 실행해 바이트 대조했다 [실행].

## 2. 원본·근거

SHARED/FUNCS/index/func_lookup 대조 후 새 analysis/decomp/r8_graphics/spotrig_factories.c,spotrig_base.c,spotrig_consumers.c,spotrig_model_bind.c,lightrig_generic_binding.c,lightrig_bone_binding.c,point_rig_runtime.c를 판독했다. 기존 r8 dynamic_fill.c/provider·격자 proof를 연결했다. 데이터 analysis/gfx4/env/VSLobby/vslobby_day.txt. 도구 web/tools/r8_gfx_spotrig_emu.py, 결과 analysis/completion/r8/spotrig_emu.json.

## 3. 생성과 실제 이름 [판독]

37a21d0은 SpotLightRig→factory37a0a38(size5F0),SpotLightRig::Obj→37a1488(size378)을 등록한다. Param 기반36d47b8은 문자열 ModelName/BonePrefix/MaterialPrefix를 실제CRC 연산으로 등록한다. 기존0xC32F024E는 BoneName가 아니라 **BonePrefix**다. ModelName hash6448209E,BonePrefix C32F024E,MaterialPrefix85A6BBB2.

37a0a38의 이름 미상 네 float는 **CycleA/ CycleB/ CycleAR/ CycleBR**다. CRC는BDC3DF92/24CA8E28/49DBEEE2/62F6BD21이며, Indv 접두사는 이 네 이름에 없다. 나머지 해시는 AnmType21E45B6E,IndvSpecColD7FFDD43,IsOffsetWorld86FE9C49,IsFollowDirDCB2146C다.

## 4. Param 필드 [판독]+[데이터]

| value offset | 실제 이름 | 생성 기본값 |
|---|---|---|
| 130(string ptr),13C(buffer) | ModelName | untitled |
| 1A0(ptr),1AC(buffer) | BonePrefix | untitled |
| 210(ptr),21C(buffer) | MaterialPrefix | untitled |
| 290 | AnmType i32 | 0 |
| 2B0 | Intensity f32 | 1 |
| 2D0/2F0 | Specular/IndvSpecCol bool | true/false |
| 310/338/360 | Color/ColorOffset/SpecularColor rgba | (1,1,1,1)/(0,0,0,0)/(0,0,0,1) |
| 388/3A8 | Radius/RadiusOffset | 10/1 |
| 3C8/3E8/408/428 | CycleA/B/AR/BR | .2/.05/.09/.003 |
| 448 | DampParam | 1.2 |
| 468 | Offset xyz | (0,0,0) |
| 490 | IsOffsetWorld | false |
| 4C0 | Direction xyz | (0,1,0) |
| 4E8 | IsFollowDir | true |
| 508/528 | Angle/AngleDamp | .8/1 |

원본AAMP record header는value의18B 앞(vt+0,hash+8,next+10)이다. 위는 value offset이다. +530 이후 일부 파라미터의factory hash는"default"로 등록되며 추측한 새로운 이름을 붙이지 않는다.

로비 모든8개 AnmType=0,Specular=true,IndvSpecCol=false,Cycle값은표와같다. ModelName=Fld_VSLobby,BonePrefix=Dynamic_SpotLightA..H,MaterialPrefix=untitled,IsOffsetWorld=false,IsFollowDir=true.

| Rig | enable | Intensity | Radius | DampParam | Angle | AngleDamp |
|---|---|---|---|---|---|---|
|0|false|50.400002|10|1.2|1.671327|1|
|1|true|10|13|.31|2.949955|1.72|
|2|true|15|12|.69|2.880841|1.42|
|3|false|1|10|1.2|.8|1|
|4|false|32|12|.92|2.010619|1|
|5|true|28|6|1.2|1.775|2.88|
|6|true|12.7|7|1.23|1.240929|1.71|
|7|true|13.3|10|1.2|1.407434|1.02|

Color/Offset/Direction의원본8행은데이터덤프에보존한다. 사용된색도 (1,1,1,1) 또는덤프그대로이며화이트광으로강제하지않는다.

## 5. 뼈 배정·수명 [판독]

Param vtB8=36d4e78은 모델 목록을 순회한다. 실제 모델 리소스 이름과 ModelName을 비교(빈값은all,끝*은prefix허용)하고, 뼈 vt30 count/vt48 name을 읽어 BonePrefix 길이만큼 앞 문자열을 비교한다. 맞은 뼈마다 Param vtC0=37a07b4가obj를 얻어 boneIndex360=s16인덱스를 기록하고 모델·Param 두 intrusive list에 붙인다. 문자열을 단일 뼈 exact equality로 바꾸지 않는다.

Param vtD8=37a028c는context+4958의SpotObjpool에서pop하고obj358에owner Param을쓴다. Obj58을켜고dirtybit를기록한다. Param vtD0=37a0348→373FD8C는 해당모델의obj를두list에서분리,enable해제,boneindexFFFF/phase0/resetflags후pool에돌린다. vtC8=37a0988은MaterialPrefix로선택된재질의gsys_point_light_color를 찾아Param498에값포인터를저장한다.

## 6. 갱신과 공간 식 [실행]+[판독]

Obj vtC0=37a1AA8은모델vt98(boneIndex)의bit0=false 또는owner58=false면반환한다. 모델vt88은뼈world3×4행렬 M을준다. obj36C=model+8의mask&호출mask. IsOffsetWorld=false: position=M.rotation*Offset+M.translation;true: position=Offset+M.translation. 각곱과덧셈은별도f32이며FMA로합치지않는다.

AnmType0은Color/Radius 그대로. AnmType2는498재질colorptr가있으면RGB=color.rgb*material.rgb,alpha=Color.a;없으면(0,0,0,1)이다. Specularfalse→specular(0,0,0,1);true/IndvSpecColfalse→현재Color;true/true→SpecularColor.

AnmType1은두phase364/368을dt,π,CycleA/B 및 RNG*CycleAR/BR로증가시키고,phase합의상위8bit·하위24bit로4AA5B5C원본sin표를선형보간한다. u=sin*.5+.5,color=Color+ColorOffset*u,radius=Radius+RadiusOffset*u다. RNG는5997950의4u32xorshift이며정수 비트를 float로 재해석해 [1,2) 값을 만들고 1을 뺀다. 이 분기는 전체 명령을 판독했으나 이번 2,048건 실행에는 포함하지 않았다. 로비 데이터는 모두 AnmType0이다.

## 7. 최종 필드와 동적광 입력 [실행]+[판독]

Param vtE0=37A038C이Obj에쓴다. Direction은IsFollowDir이면M.rotation*Direction,아니면그대로이며여기서는정규화하지않는다. Obj128=color,150=specular,1E0=position,1B8=direction,198=radius,208=**Angle*.5**,178=Intensity,228=DampParam,248=AngleDamp*(radius/Radius). Radius==0일때역수대신1을쓴다. 후속104560C에서direction을정규화하고cos(halfAngle)을att.z로쓴다는기존원본소비와연결된다. Angle는degree가아니라cosf에공급하는radian전체각이다.

1048D98은actorview+460의pool목록을읽고obj58/owner58가둘다켜진것만colorRGBA*Intensity,radius198,halfAngle208,damp228,angleDamp248,position1E0,direction1B8,type1로104560C에넘긴다. SpecularColor는이provider의input색에는별도로합치지않는다.

PointRig도새3791CD8→3790020 writer를읽었다. Obj178=position,1A0=radius,1C0=Intensity,1E0=DampParam,210=SpecularSize*(radius/Radius).1048C3C은owner328/enable을확인하고color*Intensity,radius,position,damp,type0으로격자에넘긴다.

## 8. 배치 Actor Scale 경로 [판독]

기존typed LocatorPoint/SpotLightBancParam와이번실제1049B08/104A0C4를연결했다. Point반경=component배율24*actortransform70;DampParam30/color34..40/Intensity44. Spot반경=2*(배율24*actortransform74),halfAngle=min(atan((배율24*actortransform70)/max(2*radiusRaw,2^-23)),π),DistDamp44/AngleDamp30/color34..40/Intensity48. 즉배치Scale을단일Radius로읽는규칙은Point와Spot에서다르다. 이름GfxPointLight/SpotLight(비Dynamic)의등록·베이크여부전체는아직별도미확정이다.

## 9. 웹 반영 필요

impl/render.md/assets.md:BonePrefix matching·worldmatrix Offset/Direction·Angle반각·원본DampParam과AngleDamp·Radius보정·enable이중gate를연결한다.기본three.js SpotLight감쇠나angle=dataAngle전체값으로대체하면동일하지않다. 원본격자/UBO와shader감쇠는dynamic_lighting/stage_rendering의식을쓴다.코드/impl은변경하지않았다.

## 10. 검증

python web/tools/r8_gfx_spotrig_emu.py →2,048건byte완전일치. 실제37A1AA8→37A038C→1048D98를실행하여임의matrix/offset/direction/AnmType0·2/specularflags/Intensity/radius/AngleDamp를대조했다. 외부getter는합성bone행렬과visiblebit,104560C는기록sink다. math/fieldcopy 알고리즘스텁은없고libc mutex만서비스stub. 해당sink다음의격자/GPUupload는이전r8독립실행proof를재사용한다.

첫실행은else0구문오류(exit1),공백수정후exit0. lookup37A038C/3790020은앞짧은함수범위로잘못묶었으므로실제leaf시작명령과RET로확인했다.379260C는noop이어서runtimewriter근거에서제외한다.

## 11. 정정·한계

2026-10-03:stage§2.3의뼈이름/4float/Angle추정,§8의DampParam/DistDamp/AngleDamp/Radius/Scale복사미확정,§9의켜진SpotLightRig+GfxPointLightDynamic 대응을원본생산·소비·실행으로정정했다. 이전기록은삭제하지않았다. 전체라이브자원로드/GPUframe·비Dynamic배치사용여부는별도질문이며이번확정을그범위로확대하지않는다.
