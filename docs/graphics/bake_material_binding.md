# 베이크 텍스처의 원본 재질 연결

## 1. 기능 개요

원본은 bkdat의 DataType 3/4를 각각 `bake0`/`bake1` 샘플러와 `gsys_bake_st0`/`gsys_bake_st1` 재질 파라미터에 연결한다. 자리표시자 텍스처의 이름을 비교해 교체하지 않는다. 모델 Guid·모델명 해시·재질명과 원본 인덱스 검증을 거쳐 실제 텍스처 핸들 두 개와 UV scale/offset 네 성분을 기록한다 [판독]+[실행].

## 2. 원본 자료

원본 main.reloc.img; 기존 r5_camweapon/phive_cfg.c의 미판독 모듈31; 새 r8_graphics/bake_module_setup.c, bake_slot_register.c, bake_apply_model.c, bake_material_lookup.c, bake_event.c. 앞서 SHARED/FUNCS/decomp_index를 대조했다. 기존 모듈15(Phive) 결론은 새 성과로 세지 않았다.

## 3. 초기화 흐름 [판독]+[실행]

설정 팩토리 344af54 **case31** → 0x12D8B 설정 객체, 항목수+12C8=2. 항목은 설정+8부터 0x78B 간격이다. 모듈 초기화3cf9ba0는 init+28에서 설정을 받아 {설정+8,항목수}를3cce7b8로 넘긴다. 3cce7b8→3ccfa2c가 전역59A3DF8의 40슬롯 표를 초기화하고 3ccfcd4가 등록한다.

| DataType | BindingSpace | 표 인덱스 | 샘플러 | vec4 파라미터 |
|---:|---:|---:|---|---|
| 3 | 0 | 2 | bake0 | gsys_bake_st0 |
| 4 | 0 | 3 | bake1 | gsys_bake_st1 |

등록과 소비의 인덱스 식은 `((space<<2)&0x1c)|((type-1)&3)`로 같다. type0은 등록·소비하지 않는다. 설정 두 항목의 실제 문자열·타입·space와 원본 표 등록을 실행했다.

## 4. 주요 구조 [판독]

표 항목+8/+10 = sampler SafeString 포인터/용량32, +40/+48 = parameter SafeString 포인터/용량32, +70/+74 = DataType/BindingSpace. 모델 등록 레코드0x18B = {모델 포인터, Guid 해시u64, 모델명 해시u32}. DataElement+8/+10/+18/+1C는 Guid 해시표/인덱스표/수/용량, +20/+28는 ModelElements 수/64B 배열, +40/+48는 해석된 텍스처 수/포인터 배열, +90/+94는 타입/space다.

ModelElement+0/+8/+C는 재질명 해시표/수/용량, +10/+18은 MaterialElements 수/0x28B 배열, +20은 모델명 해시, +28은 OriginalMaterialCount. MaterialElement+0/+4=TexcoordScale X/Y, +8/+C=Offset X/Y, +10=TextureIndex, +14/+18=OriginalMaterialIndex, +20=MaterialName 포인터. 3ccbda0는 명명된 BYML 키를 읽어 이 배치에 쓴다. 디컴파일의 `(float)local_78`는 u32 저장의 잘못된 C 타입 표기이며 숫자를 f32로 변환하는 의미가 아니다.

## 5. 모델·재질 선택 [판독]

3ccadd0는 리소스 vt28/30으로 각 DataElement를 얻고 타입/space로 표를 선택한다. 등록 모델마다3ccaf2c를 호출한다. Guid 해시를 선형 탐사해 ModelElement를 찾고 모델명 해시가 일치해야 한다. 모델 RTTI 확인 뒤 OriginalMaterialCount>=0이면 실제 BFRES 재질수(model+132)와 같아야 한다.

각 재질의 이름을 vtD8로 얻고3ccbc7c가 원본0f7694c 해시 및 선형 탐사로 MaterialElement를 찾는다. TextureIndex가 음수/범위밖이면 반환 텍스처 포인터는0이며, 정상 입력과 같은 유효 텍스처로 임의 보정하지 않는다. OriginalMaterialIndex>=0이면 실제 재질 인덱스(*material+A0)와 비교한다. 불일치시3ccb4f0 복구 경로로 빠져 실패한다.

## 6. 실제 바인딩 [판독]+[실행]

기본 핸들러(mgr+8=0): 3ccb7e4가 BFRES sampler ResDict(*material+38)에서 표의 sampler명을 찾고, 원본 함수 안의 다른 ResDict 검색이 shader parameter명을 찾는다. 둘 중 하나가 없으면 이 재질은 건너뛴다. 성공하면 TextureIndex가 가리킨 텍스처 객체+88/+90의 두 핸들을 material+50/+58 배열의 해당 sampler index에 저장한다. 변경된 핸들과 material+78 callback이 있으면 callback을 호출한다.

이어서 모델 vt158에 `{ScaleX,ScaleY,OffsetX,OffsetY}`를 vec4로 넘긴다. S/T를 임의로 뒤집거나 offset을 앞에 두지 않는다. mgr+8 사용자 핸들러가 있으면 그 vt0에 모델·재질index·슬롯·설명자를 넘긴다. 이 별도 훅의 내부 구현은 이번 기본 경로 실행 밖이다.

## 7. 로비 자료 연결

기존 로비 bkdat/BFRES 데이터의 DataType3(BC5)/4(BC6H)와 `_b0=bake0`/`_b1=bake1` 매핑은 이 원본 설정·소비 식으로 연결된다. 셰이더의 AO/Shadow .xy와 Light RGB 사용은 stage_rendering §5.1/§6.1의 기존 판독을 재사용했다. 이번 새 근거는 파일 형식의 닮음 대신 실제 슬롯 선택과 핸들 쓰기다.

## 8. 상호작용·한계

지형 도색 `_pu*` 생성은 ColPaint 별도 경로다. 정적 GfxPointLight/SpotLight의 런타임 소비 여부, 전체 GPU 패스·실제 화면 대조, 사용자 bake handler 훅은 이 기본 바인딩 결과로 확정하지 않는다.

## 9. 웹 반영 필요

impl/render.md 및 impl/assets.md: bkdat Guid/모델명/재질명·원본 인덱스 검증→DataType3/4 샘플러 선택→TexcoordScale/Offset vec4 적용. BakeDummy 이름을 찾아 임의 치환하는 구현이 있다면 원본의 타입·space·재질 슬롯 규칙으로 바꿔야 한다. 코드와 impl은 수정하지 않았다.

## 10. 실행 검증

`web/tools/r8_gfx_bake_binding_emu.py` → `analysis/completion/r8/graphics_bake_binding_emu.json`: 원본 팩토리2항목·슬롯2항목 일치, 타입3/4 합성32건의 텍스처 핸들2개·uniform16B **32/32 비트 일치**. 원본3ccfa2c/3ccfcd4/3ccadd0/3ccaf2c/3ccbc7c/3ccb7e4/0f7694c를 실행했다. 해시나 ResDict 조회를 스텁으로 대체하지 않았다.

스텁은 malloc/memset/memcpy/strlen/memcmp의 메모리 동작과 합성 SDK 모델의 RTTI=true, 재질수1, 재질명 getter, uniform 기록 sink, DataElements 수/getter다. 합성 모델당 재질1개만 검증했다. 실제 로비 전체 리소스·GPU는 실행하지 않았다.

## 11. 정정·미확정

2026-10-03 r8: stage_rendering의 '자리표시자 교체 코드 미판독'과 'DataType3/4 샘플러 대응 추정'을 실제 설정→표→모델 바인딩 판독·실행으로 해소했다. 이전 문구는 원문에 날짜 정정을 추가해 보존했다. 첫 실행은 원본 정적 RTTI 가드가 초기화되지 않아 guard_acquire PLT에서 중단; 합성 SDK의 가드 byte를1로 초기화하고 재실행32/32 성공했다. 3730a48는 +12C8만 닮은 decalAoTmp 소비자여서 후보 제외. 혼합 항목 stage:L343의 정적 광원 부분은 조사중으로 유지한다.
