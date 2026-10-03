# Hoian_UBER — UV 선택값 3

## 1. 기능 개요

`texcoord_select_* = 3`은 활성 텍스처가 해당 선택을 쓸 때 `_u3`(aTexCoord3, location11)와 `tex_mtx2`를 선택한다 [판독]. 키 표에 3이 있다는 사실만으로 활성 샘플을 확정하지 않는다.

## 2. 원본 자료

원본 Product Hoian_UBER BFSHA와 5611행 키 표. 새 역번역 근거 `analysis/completion/r8/graphics_shader_p2485.{vert,frag,options.txt}`. 기존 SHARED/FUNCS/decomp_index에 선택3 판독 근거가 없는 것을 먼저 확인했다.

## 3. 연결 흐름 [판독]

프로그램2485: enable_emission_map=1, texcoord_select_emmmap=3 → vertex aTexCoord3.xy → Mat.tex_mtx2 → out_attr1.xy → fragment in_attr1.xy → cTexEmission(_e0) 샘플. 정점/픽셀 양쪽의 연결을 판독했다.

## 4. 입력 구조 [데이터]

aTexCoord3는 location11 vec4이고 원본 사용 성분은 xy다. tex_mtx2는 두 vec4로 반사 이름이 붙는다. 이 프로그램의 다른 UV0/UV2는 tex_mtx0/tex_mtx1을 쓰므로 세 번째 변환과 구별할 수 있다.

## 5. 수명

선택은 프로그램 정적 옵션이다. 프레임별 tex_mtx2 값 writer·애니메이션 적용은 이번 질문의 범위 밖이며 다른 미확정에 남긴다.

## 6. 식 [판독]

```text
u = fma(aTexCoord3.x, tex_mtx2[0].x,
        aTexCoord3.y*tex_mtx2[0].z) + tex_mtx2[1].x
v = fma(aTexCoord3.x, tex_mtx2[0].y,
        aTexCoord3.y*tex_mtx2[0].w) + tex_mtx2[1].y
Emission = texture(cTexEmission, (u,v)).rgb
```

FMA는 역번역 식에 실제 나타나며 CPU 비FMA 규칙으로 바꾸지 않는다. sampler 필터/정밀도/GPU 실행 결과는 별도 질문이다.

## 7. 에셋 연결

선택3의 의미는 위 활성 프로그램으로 확정했다. Fld_VSLobby의 UV1 베이크 경로와 혼동하지 않는다. 파츠별 어느 재질이 이 변형을 고르는지는 각 재질의 정적 옵션 대조가 필요하다.

## 8. 상호작용

resource0/1/2 선택값이 3이어도 해당 리소스가 비활성/제거되면 정점 입력에 UV3가 없다. 프로그램121/155/310/2659는 첫 조사 후보였지만 해당 선택3 텍스처 샘플이 제거되어 전체 연결 증거로 쓰지 않았다.

## 9. 웹 반영 필요

impl/render.md/impl/assets.md에서 UV 선택3을 지원할 때 _u3→tex_mtx2로 연결한다. 원본 fma 항과 변환행의 성분 배치를 유지한다. 코드·impl 문서 변경 없음.

## 10. 검증

shader_dump prog-bfsha --index2485 성공, 새 vert/frag에서 입력→변환→varying→샘플을 판독했다. GPU 픽셀 실행·에뮬레이터 대조는 하지 않았다. 따라서 [실행]으로 표기하지 않는다.

## 11. 정정·미확정

2026-10-03 r8: shaders §3.7의 '_u3+tex_mtx2 추정' 및 formats §8의 선택3 질문을 원본 프로그램2485 양단 판독으로 확정한다. 종전 추정 문구는 삭제하지 않고 날짜·이유와 이 문서를 연결했다. 최종 조명·샘플러·재질별 채널 전체는 미확정 유지.
