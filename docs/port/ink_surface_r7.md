# 바닥·벽 잉크 표면 실제 웹 반영 r7 — 2026-10-03

체감 우선 작업 **PNT06: 보이는 잉크·모델 좌표**를 반영했다. 충돌 면을 .02 띄우던 별도 overlay를 제거하고, 실제 시각 지형의 같은 draw에서 원본 잉크 분기가 색·법선·광원 반응을 바꾸도록 연결했다. **원본 전체 아틀라스와 동일한 화면으로 완료된 것은 아니다.**

| 고정 기준 | 현재 값 | 처리 |
|---|---:|---|
| 웹 전체 | **13/62 = 20.97%** | 반영 확인13 유지, 일부36→37, 차이10→9, 원본 미확정3 |
| 도색 PNT01~06 | **1/6 = 16.67%** | PNT06 차이/미반영→일부 반영, PNT02 원본 atlas는 차이 유지 |
| 그래픽 GR01~10 | **0/10 = 0.00%**, 일부7/10 | 복합 질문의 나머지 캐릭터/환경/GPU 조건이 남음 |
| 원본 inventory | **556/986 = 56.39%** | 기존 실행 근거 재검증·웹 포팅, 전체 질문 승격0 |

점수는 고정 항목의 전체 범위 완료율이다. 변경량이나 화면 유사도 점수로 해석하지 않는다.

| 실제로 달라진 것 | 원본 근거·반영 | 남은 경계 |
|---|---|---|
| 바닥·벽·경사에 붙는 도색 | 실제 visual triangle을 현재 chart에 분할·배정. 베이크 UV1, 재질 UV·법선·색·접선과 변환 보존. 별도 LIFT/polygonOffset 없음 | chart 탐색/클리핑·coplanar/shelf atlas는 웹 adapter. 원본 panel·42방향·3200² whole atlas와 두 panel seam은 미연결 |
| 밝은 잉크 경계·색 | 원본 near-max 가중합, 동률 색을 나누지 않음, .3005 주변 f32 표시 gate, InkBright×.625→Ink와 양×.875 혼합 | actual Lby 팀색 행 선택 미확정. 기존 OrangeBlue 정책 유지 |
| 표면 굴곡·두께 | UV 선택/반전, 이웃 채널 차×1.8, floor.95/wall.75·프레임 진동, 최종 N 및 world-up SH 혼합의 normalize 부재 보존 | native Z=1/3200 대신 현재 페이지 폭 역수. W는 확인된 초기0 유지, 후속 writer 미확정. JS sin/WebGL FMA는 native 전수비트 일치 아님 |
| 빛·반사·최종색 | F0.015·roughness.05, 공통 direct/bake/SH/dynamic/AO/shadow/fog→HDR/Bloom/LUT 연결. dry fragment는 기존 지형 재질 | PMREM/Three BRDF adapter, native cube12/Illuminate/live sampler·최종 NVN 픽셀 남음 |
| 재질·자원 수명 | 원본 Hoian/forward hook와 USE_UV1 defines를 clone에 명시 복사. 캡처 완료 뒤 바인딩, 해제 시 원본 geometry 복원 후 clone/texture 해제 | emission은 원본 member18 초기0 사용; 현재 환경 Ink reader→member18.z 경로는 미확정 |

**실제 사격장:** 후보 12mesh 중 11mesh에 바인딩, 대상 visual triangle 5,914개 중 1,891개 배정, 1page·10개 잉크 재질. 부분적으로 배정한 triangle도 분할 조각만 칠하므로 이 수치를 원본 atlas coverage나 완료율로 세지 않는다. 미배정 조각은 마른 원본 재질로 남긴다. skipped=0. 이전 paint.page overlay는 0개다. LobbyFloorConcrete·Wall02를 포함했고, 베이크 AO75/light75/missing0·환경 캡처2회가 유지됐다. 생성된 visible19mesh 중 UV1을 쓰던18개에서 그대로 보존했다. 게임 최초 발사/도색 장면을 확인했으며 모든 벽·경사·맵 모서리에 실제 발사를 전수 시험한 것은 아니다.

| 실제 수행 명령 | 결과·검증 범위 |
|---|---|
| `decomp_index.py`·SHARED/FUNCS 확인 | 모두 기존 leaf/판독 재사용, 새 디컴파일0 |
| `.venv/Scripts/python analysis/port_ink_r7/uv/export_fixture.py` | 원본 UV/switch/tangent writer277입력, panel UV/접선256입력, world 변환 명령블록128입력 일치. whole BFRES/accessor/shape lookup·GPU는 제외 |
| `.venv/Scripts/python analysis/port_ink_r7/shader/native_fixture.py` | corrected native GLSL 대입문 독립 해석88입력, [재구현], 원본 함수 실행 아님 |
| `node analysis/port_ink_r7/shader/gpu_compare.mjs` | **431/431 PASS**, 최대차5.960464477539063e-8. 같은 WebGL에서 판독 GLSL slice와 실제 포트 소비자 비교; NVN 실행 아님 |
| `npm test` | **285/285 PASS**, 실패0. UV/geometry11·잉크8 추가 |
| `npm run typecheck`, `npm run build` | 각각 exit0 |
| `node analysis/port_ink_r7/browser_verify.mjs` | 실제 게임 콜백으로 대기·발사·착탄·잔상4단계. 지형 속성/재질·Bloom16draw·GL0, 콘솔/페이지/HTTP/셰이더 오류0 |
| adapter polygon fuzz | 4,096개 입력·5개 겹침 chart, 면적 손실 검사 실패0. 원본 실행과 구별 |

실패를 숨기지 않았다. 첫 실제 실행은 clone의 USE_UV1 누락으로 7개 shader compile 오류와 RAF 대기 timeout이 났다. defines를 복사한 두 번째는 shader 오류0이지만 callback 대기 timeout으로 실패했다. 로딩 이전 실제 app callback을 잡고 수동 호출하는 검사로 수정한 뒤 재실행했다. shader 단독 검사의 reserved word `active`, 잘못된 fixture branch, 없는 경로와 도구 호출 실패도 [전체 명령](../../../analysis/port_ink_r7/commands.md)과 UV/shader 하위 명령에 보존한다.

원본 상세·11절 검증 경계: [시각 모델 좌표](../graphics/ink_visual_geometry_r7.md), [잉크 셰이더](../graphics/ink_surface_web_r7.md). 실제 결과는 `analysis/port_ink_r7/browser_verification.json`, `lobby_dry.png`, `lobby_after.png`, 보호 검사는 `final_verification.json`에 있다. impl/scripts/package/에셋은 SHA256 불변, original은 키 제외 목록·크기·mtime 불변을 확인한다. 원본 내용 SHA나 최종 픽셀 일치 검사가 아니다. commit/push·큰 파일 삭제/이동0.

다음 체감 우선 지시:

- **“GR03의 피부·머리·오징어 cheapSSS·투과·film을 원본 식대로 실제 재질에 연결해줘.”**
- **“GR01/02·MOV04의 B7a0 잠영 숨김·ASB 가시성/재질과 발밑 파문을 연결해줘.”**
- **“PNT02의 원본 panel/basis/atlas·두 panel seam을 실제 시각 geometry에 연결해줘. 현재 web adapter를 원본 완료로 세지 마.”**
- **“잉크의 native BRDF/cube12·Illuminate·W/환경 emission 실제 공급자를 분석해 연결해줘.”**
