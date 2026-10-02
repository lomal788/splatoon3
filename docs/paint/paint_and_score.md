# 잉크 도색 시스템과 점수 계산

Splatoon 3 v0 원본에서 "어디에 무엇이 칠해지는가", "칠한 결과가 어떻게 점수(p, %)·스페셜로 이어지는가"를 웹으로 옮기기 위한 명세입니다. 작업 지침은 [../../분석.txt](../../분석.txt), 표기 규칙은 [../README.md](../README.md#확정-수준-표기)를 따릅니다.

- 하위 문서: [paint_shape.md](paint_shape.md) — 슈터·스플래시·벽 낙하 방울의 도색 모양(폭, 깊이 비율, 패턴, 중심 이동, 지연 도색)
- 하위 문서: [colpaint_atlas.md](colpaint_atlas.md) — 지형 도색 아틀라스(ColPaint) 생성 규칙·텍셀 밀도·패킹 (4차)
- 하위 문서: [turf_result.md](turf_result.md) — 나와바리 결과 확정 순서·승패·동률 (4차)
- 하위 문서: [special_gauge.md](special_gauge.md) — 플레이어별 칠 텍셀 집계, 스페셜 게이지 가산·비율·사망 보존·넷 %, PaintPermille, 결과 미터
- 관련 문서: [weapon/shooter_bullet.md](../weapon/shooter_bullet.md)(탄 이동), [network/network.md](../network/network.md)(도색 이벤트 동기화), [ui/ui_hud.md](../ui/ui_hud.md)(HUD 표시)

상태: **분석 진행**. 웹 구현 없음. 원본 실행 검증: 게이지·PaintPermille 명령 구간을 unicorn으로 실행([special_gauge.md §10](special_gauge.md#10-검증)), 도색 레코드 변환 0x7102c11f80(600/600)·렌더 상태 18개 설정을 unicorn으로 실행(§8). 도색 모양은 재구현 계산만. 2026-10-02 [paintgpu]: GPU 파이프라인(요청 큐·패스·모드·스텐실 카운트) §3.5 추가. 2026-10-03 [r5 paint]: 스탬프 행렬·회전·경사 보정·카메라·투영(6400/6400 원소 비트 일치), 지형(Col) 대상 좌표 변환·되돌림(6000/6000) 원본 실행, D+0x0c = 깊이 키(요청 프레임), 모드 3·7·13 역할, 레코드 풀 2560개, 애니 프레임 재그리기 입력 동일, 칠 불가 태그(KebaInk) 추가 — §3.3, §3.5.3~§3.5.7, §8.

## 1. 기능 개요

| 사용자에게 보이는 동작 | 원본 쪽 구현 요지 | 확정 |
|---|---|---|
| 탄·폭발·롤러 등이 바닥·벽·오브젝트에 잉크 자국을 남김 | 탄 클래스가 "도색 요청"(중심, 법선, 진행 방향, W×L, 팀, 잉크 텍스처 종류)을 만들어 맞은 접촉 목록에 분배 | [판독] |
| 칠한 결과가 지형 표면에 보임 | 도색 대상별 GPU 텍스처(PaintTextureData)에 스탬프. 해상도는 대상 크기(월드 단위 올림) × 8. 소유 판정은 별도 스텐실(팀비트) | [판독] (§3.1, §3.5) |
| 나와바리 결과의 팀별 p, % | 도색 텍스처의 팀별 텍셀 수(a, b, c)와 전체 텍셀 수(d)를 집계. 팀 p = ⌊count/211.2⌋ | [판독] |
| 플레이어별 칠한 포인트(p) | 플레이어 본체 +0xbd4 의 u32 텍셀 누적 / 211.2. 칠 시스템의 플레이어별 카운터(+0x5a708+i×0xe18)의 +4를 매 프레임 더함 | [판독] (2026-10-02 [gauge] 해소, 이전 [미확정]) |
| 경기 중 우세 표시 | 만분율 차 ±1000/±1500 경계로 5단계 → VS_MainTV_00 레이아웃 상태 | [판독] 화면 의미 [추정] |
| 스페셜 게이지 | 게이지 텍셀 += 스페셜용 칠 텍셀 × 배율(+0xe8) + 역경 강화 + 규칙 가산, 비율 = 게이지 텍셀 / (int)(SpecialPoint×211.2) | [판독]+[실행(에뮬 구간)] — [special_gauge.md](special_gauge.md) |
| 결과 화면 칠 % | PaintPermille = round(팀 p / PaintPtMax × 1000), 상위 두 팀 동률이면 한쪽 +1‰ | [실행(에뮬)] — [special_gauge.md](special_gauge.md) §6.8 |

## 2. 분석 대상과 자료 위치

| 구분 | 위치 |
|---|---|
| 코드 | `extracted/exefs/main.reloc.img` (주소는 0x7100000000 기준) |
| 디컴파일 | `analysis/decomp/paint/paint_batch1.c`, `paint_batch2.c`, `paint_batch3.c`, `paint_count.c`, `paint_point.c`, `referee_paint.c`, GPU 경로 `analysis/decomp/paintgpu/pg1.c`~`pg7.c` |
| 도색 파라미터 | `analysis/param_reflect/spl__Bullet*PaintParam.json`, 무기 표 `extracted/params/Component/GameParameterTable/Weapon*.json` |
| 잉크 텍스처 표 | `RSDB/InkTexInfo.Product.100.rstbl.byml.zs` → `analysis/paint/InkTexInfo.json`(50행) |
| 스탬프 텍스처 | `romfs/Model/InkTexture.bfres.zs` (107장) → `analysis/paint/inktex/*.png` (`web/tools/graphics_bntx.py png`) |
| 스테이지 | `Pack/Scene/Vss_*.pack.zs`, `extracted/params/Banc/Vss_*.bcett.byml.json` |
| 상수 | `Pack/SingletonParam.pack.zs` `spl__VersusConstant`, `spl__GearSkillTraitsParam` |
| 도구 | `web/tools/paint_shape.py`, `paint_score.py`, `paint_imports.py`(PLT 임포트 이름), `paint_blrefs.py`(BL 호출자), `paint_funcstart.py`, `paint_findconst.py`(f32 상수 movz/movk 검색), `paint_fieldscan.py`(플래그+필드 동시 접근 검색), GPU 경로 `paintgpu_q.py`(메모리 읽기), `paintgpu_nvnmap.py`(NVN 함수 포인터 이름), `paintgpu_renderstate_emu.py`, `paintgpu_record_emu.py`, `paintgpu_frame_sim.py` |
| 산출물 | `analysis/paint/shooter_paint_table.json`, `score_check.json`, `InkTexInfo.json`, `inktex/`, `analysis/paintgpu/*_out.txt` |

## 3. 도색 요청이 텍스처까지 가는 길

```
탄 슬롯84 (paint_shape.md)            ─┐
벽 낙하 방울 0x71018ae054 / 0x71018ae5e8 ─┼→ 0x7102c44e18(hitContacts, req, team.., flags, ...)       [판독]
기타 호출자(전체 16곳, 폭발 등 미분류) ─┘      │ 접촉 목록(*(hit+0x10) 의 +0x40 리스트)마다
                                               ▼
                                      0x7102c45488(out, contact, req, cb, flags)               [판독]
                                         flags&0xff     : 위치를 접촉점(+법선*깊이)으로 교체
                                         flags&0xff00   : y만 접촉점 y로 교체
                                         flags&0xff0000 : 법선을 접촉 법선으로 교체(대상 형상 종류 8/7 검사)
                                               ▼
                                      0x7102c41160 → 접촉 강체의 도색 대상(+0x70 또는 +0x78)과
                                                      셰이프키(+0x58/+0x5c)로 0x7102c4126c          [판독]
                                               ▼  (대상·면 중복 제거, 높이 제한, 뒷면 거부 — §3.5.1)
                                      콜백 0x7102c46240 → 0x7102c45f9c → 0x7102c449f0                [판독]
                                         ├ 0x7101323ea8  같은 프레임 메시지 방송(구독자 예 0x71030c03a8)
                                         ├ 0x7102c3ea50  네트워크 레코드 N(0x60 B) 작성 (§3.5.2)
                                         └ 송신 0x7102c42330 이 성공을 돌려줄 때만 → 0x7102c3f4c8 로컬 적용
수신 기기: 이벤트 콜백 0x7102c43a78 / 0x7102c43e64 / 0x7102c4418c / 0x7102c444b0 → 0x7102c3f4c8   [판독]
                                               ▼
                                      0x7102c14dec  N+0x44 로 큐 4개 중 하나의 대기 목록에 넣고
                                                    0x7102c11f80 으로 그리기 레코드 D 작성 (§3.5.3)  [판독]+[실행(에뮬) 600/600]
                                               ▼  매 프레임 0x7102c13750: 대기 → 실행 목록, 그린 레코드 수명 처리
                                      렌더 패스 0x7102c50f20 → 0x7102c14168 (모드 순서, §3.5.4)
                                         → 0x7102c1461c (대상 선택·카운터·애니 프레임)
                                         → 대상 vt+0x28 (0x7102c564d0, 오브젝트는 0x7102c368dc 가 면마다) → 0x7102c188b4
                                      PaintOverpaint 셰이더 — ../graphics/shaders.md §4                     [판독]
지연 경로: 0x71017646a4 = 저장된 요청 위치에서 구 겹침 질의 → 접촉마다 0x7102c45488                    [판독]
```

(2026-10-02 [paintgpu] — 이전 판의 "요청 큐 → 렌더 패스 연결은 미추적 [미확정]"을 위 경로로 해소했습니다.)

- 같은 요청이 접촉한 **모든** 면에 각각 들어갑니다. 바닥과 벽 모서리에 맞은 탄은 양쪽에 찍힙니다 **[판독]**. 다만 한 번의 분배(0x7102c44e18 호출 하나) 안에서 같은 대상·같은 면은 한 번만 칠합니다(§3.5.1 중복 비트) **[판독]**.
- 도색 결과는 네트워크 이벤트로 동기화됩니다. 이벤트 클래스 이름 `spl::paint::FloorPaintEvent`, `ColPaintEvent`, `ObjPaintEvent`, `MultiTargetPaintEvent` **[데이터]**, 수신 핸들러 4종은 `0x7102c41980`이 "PaintRequest" 이름으로 등록(0x7102c438b8, 0x7102c43c98, 0x7102c43fc4, 0x7102c442e8; 페이로드 ≤0x58 B + u32 2개) **[판독]**. 직렬화 형식은 [network] 담당에 넘깁니다.
- ~~요청의 `flags[0] = !슬롯77` 값이 원격 재생 여부로 보입니다 [추정]~~ → **정정 [판독]** (2026-10-02 [paintgpu]): `flags[0]`(C+0)은 레코드 N+0x44로 들어가 "칠 p만 세고 스페셜 게이지에는 넣지 않음" 표시가 됩니다(§3.5.2, §4.4). 탄 vtable 슬롯 77은 101개 탄 vtable에서 `return 1`(0x7101649bd8)이고, 0을 돌려주는 것은 `spl::BulletSpJetpackLauncher`(제트팩, 0x71017fed74) 하나뿐입니다. 즉 제트팩 탄의 칠은 p에만 들어갑니다.
- **복제 탄은 칠하지 않습니다 [판독]**: 슈터 발사 함수의 생성정보 채우기 `0x71025823b0`이 `+0x6d = local 인자`(0x7102582864, 로컬 1 / 복제 0)를 쓰고, 슈터·스플래시 슬롯84는 `+0x6d == 0`이면 바로 돌아갑니다([paint_shape.md](paint_shape.md) §3.4). 자식 탄(벽 낙하 등)은 부모의 `+0x6d`를 복사합니다(0x7101648a4c). 다른 기기의 칠은 그 기기가 보낸 PaintRequest 이벤트로만 들어옵니다(수신 콜백 → 0x7102c3f4c8). 슈터 외 무기(롤러·차저·블래스터 폭발 등)의 발사 함수는 이번에 보지 않았습니다 **[미확정]**.
- 로컬 적용 조건 **[판독]**: 0x7102c449f0은 도색 관리자 `+0x2d8`(칠 시스템)·`+0x2e8`(PaintRequest 레플리카)가 있고 `[*0x7105798658]+200 != 2`이며 송신 0x7102c42330이 1을 돌려줄 때만 0x7102c3f4c8을 부릅니다. 0x7102c42330은 `GameNet+0x195 == 0`(오프라인)이면 1, 세 번째 인자가 1이면 메시지 경로로 1, 그 밖에는 권한 검사에 실패하면 0 → **송신이 거부되면 자기 기기에도 칠하지 않습니다**.

### 3.0 벽 낙하 방울 반경의 출처 **[판독]** (2026-10-02 [gauge])

[paint_shape.md](paint_shape.md) §6의 "생성정보 +0x9c 정수 × 0.05, writer 미발견"을 해소합니다. 모든 탄 클래스가 공유하는 vtable 슬롯 61 `0x7101646b10`(BulletShooterBase/BulletSimple/BulletSplashShooter 같은 함수)이 벽 낙하 탄의 생성정보를 채우면서 `WallDropCollisionPaintParam`을 상속 체인으로 읽어 정수로 바꿉니다.

```
spawn+0x94 = (int)(PaintRadiusShock  (+0x3c, 기본 1.3 ) / 0.05f + 0.001f)   // 26
spawn+0x98 = (int)(PaintRadiusFall   (+0x34, 기본 0.65) / 0.05f + 0.001f)   // 13
spawn+0x9c = (int)(PaintRadiusGround (+0x38, 기본 0.6 ) / 0.05f + 0.001f)   // 12
```

- 소비: `0x71018ae054`가 +0x9c(Ground) × 0.05, `0x71018ae5e8`가 +0x98(Fall) × 0.05 × 2를 도색 크기로 씁니다(후자는 생성정보 +0x6e > 0 또는 탄 +0x3c0 ≥ 0일 때) **[판독]**. +0x94(Shock)의 소비 함수는 이번에 보지 않았습니다 **[미확정]**. → **해소 (2026-10-03 [r5 paint]) [판독]**: 같은 벽 도색 경로가 `생성정보+0x6e > 0`이면 +0x98(Fall), 아니면 `탄+0x3c0 ≥ 0`일 때 +0x98, **`탄+0x3c0 < 0`이면 +0x94(Shock)**를 고르고(0x71018aecac~0x71018aecc0, 분기 0x71018af25c), 크기 = 정수 × 0.05 × 2 입니다. 탄+0x3c0 의 의미(첫 충돌 여부로 보임)는 [weapon] 담당 문서 기준을 따릅니다.
- 정수 양자화는 0.05 단위이고 +0.001은 f32 나눗셈 오차(0.6/0.05 = 11.99999…) 보정으로 보입니다 **[추정]**.
- paint_shape.md 본문 갱신은 [paint] 담당에게 넘겼습니다(SHARED.md [gauge→paint]).

### 3.1 도색 텍스처 (PaintTextureData)

`void spl::paint::PaintTextureData::create(const game::Len2f &, bool, sead::Heap *, sead::Heap *)` = `0x7102c4881c` **[판독 — 단언 문자열 0x71048a14c0]**.

```
nx = ceil(size.x) (최소 1),  ny = ceil(size.y) (최소 1)       // int 절삭 후 소수부 있으면 +1
tex0 (+0x2a8)  : (nx*8, ny*8), 포맷 = (플랫폼 설정값 == 5) ? 0x1d : 10
tex1 (+0x760)  : (nx,   ny  ), 포맷 같은 규칙
tex2           : (nx*8, ny*8), 포맷 0x5b
bool 인자가 참이면 추가 텍스처(포맷 9, 0x10000 플래그) 생성
```

- 객체 0xa60 B, 생성 경로 `0x7102c55da8 → 0x7102c56174(대상, size, heap…) → 0x7102c4881c` **[판독]**. size = 대상 vt+0x48(모든 대상 클래스가 `0x7102bc3e08` = `대상+0x390` 반환)의 Len2f입니다. (정정: 이전 판의 `0x7102c55be0`은 대상 소멸자이고, 생성 호출은 그 다음 함수 0x7102c55da8 안 0x7102c55f88입니다.)
- **size 출처와 단위 [판독]** (2026-10-02 [paintgpu], 이전 [미확정]):
  | 대상 | `대상+0x390` writer | 값 |
  |---|---|---|
  | Floor 대상(관리자 +0x2b0, 0x3d8 B, 생성자 0x7102c1b270) | 생성자 0x7102c1b3f0 | (200.0, 200.0) 기본값 |
  | 오브젝트 대상 vtable 0x71056803d0/0x7105680580 | vt+0xd8 = 0x7102c3c884(AABB) | (+0x1158 & ~1) == 2 일 때 (ceil(max.x−min.x), ceil(max.z−min.z)), 각각 최소 1, 아니면 (1,1) |
  | 오브젝트 대상 vtable 0x710567fae0/0x710567fc98/0x710567fe98/0x7105680050 | vt+0xd8 = 0x7102c3a194(AABB) | 세 변 길이 중 (ceil(최대), ceil(중간)), 최소 1 |
  | 오브젝트 대상 vtable 0x7105680208 | 0x7102c3c25c | (1.0, 1.0) |
  
  AABB 변 길이는 월드 단위이고 `ceil`(fcvtzs 후 소수부 있으면 +1, 최소 1) → `×8 ×0.125`로 다시 정수 단위가 됩니다. 따라서 **size = 월드 단위(올림), 텍스처 = 월드 1 단위당 8 텍셀**입니다. 점수식 `count/64/3.3`(§4.2)의 64 = 8×8과 맞습니다. ColPaint(지형, kind 2) 아틀라스도 **패널 평면 좌표 1 단위 = 8 텍셀, 아틀라스 400 단위 = 3200×3200**입니다 **[판독]** (2026-10-02 [paint4] 정정, 이전 [추정]) — [colpaint_atlas.md](colpaint_atlas.md) §6. 단 지형 텍셀 수는 실제 면적이 아니라 42개 대표 방향 평면에 투영한 면적 기준입니다.
- **포맷 [판독]+[추정]**: agl 포맷 번호 → 스위즐 표 `0x7104abef40`(16 B/항목, NVN 스위즐 0=ZERO 1=ONE 2=R 3=G 4=B 5=A)와 NVN 포맷 표 `0x7104abfc54`(u32):
  | 텍스처 | agl 포맷 | 스위즐(R,G,B,A) | NVN 포맷 값 | 해석 |
  |---|---|---|---|---|
  | tex0 색(+0x2a8), tex1 저해상도(+0x760), 규칙 ≠ 5 | 10 | R,G,0,1 | 13 | 2채널 RG8 UNORM [추정: 값→이름] |
  | 같은 텍스처, 규칙 == 5(Tcl 트리컬러) | 0x1d | R,G,B,A | 37 | RGBA8 UNORM [추정] |
  | tex2(+0x448) 깊이·스텐실 | 0x5b | R,R,R,1 | 53 | 깊이+스텐실(스텐실은 §3.5.4에서 사용) [추정: 이름] |
  | 높이 마스크(bool 인자, +0x740) | 9 | R,0,0,1 | 5 | 1채널 R16F [추정] |
  
  - **비트 폭 확정 (2026-10-03 [r6 paint]) [데이터]+[실행]**: 게임(agl) 쪽 포맷 정보표 `0x7104abf510`(0x14 B × 0x5d, agl 포맷 번호 색인)에 채널별 비트 수와 텍셀당 바이트가 있습니다. 이 표의 +8(텍셀당 바이트)을 쓰는 agl 이미지 크기 함수 `0x71035b519c(type, fmt, w, h, d, mips, mode)`를 선형 경로(mode 0)로 원본 실행하면 0x5d개 포맷 × 크기 5가지 **465/465건이 `표+8 × w × h`**와 같습니다(`web/tools/r6_paint_texfmt_emu.py`, 스텁 없음, 결과 `analysis/paint/r6_texfmt_emu_out.json`). 표 필드는 +0..+3 채널별 비트 수, +4..+7 채널 순서, +8 텍셀당 바이트, +9 채널 수, +0xa 압축, +0xb 정규화, +0xc 부동소수, +0xd 부호 없음, +0xf 깊이·스텐실 계열입니다. 필드 이름은 표 안 일관성(R8·R8SN·R8UI·R8I 네 행이 +0xb/+0xd 조합 네 가지를 가짐 등)으로 붙였습니다.

    | 텍스처 | agl 포맷 | 비트(채널 순) | 텍셀당 바이트 | 정규화/부동소수/부호 없음 | 결론 |
    |---|---|---|---|---|---|
    | tex0·tex1, 규칙 ≠ 5 | 10 | 8, 8 | 2 | 1 / 0 / 1 | 채널당 8비트 부호 없는 정규화(0~1, 1/255 단위) 2채널 |
    | tex0·tex1, 규칙 5(Tcl) | 0x1d | 8, 8, 8, 8 | 4 | 1 / 0 / 1 | 같은 형식 4채널 |
    | tex2 깊이·스텐실 | 0x5b | 24, 8 | 4 | 1 / 0 / 1, 깊이 계열 1 | 24비트 정규화 깊이 + 8비트 스텐실 |
    | 높이 마스크(+0x740) | 9 | 16 | 2 | 0 / 1 / 0 | 16비트 부동소수 1채널 |

    3200² tex0 = 20 480 000 B(2 B/텍셀). 깊이 24비트 정규화이므로 깊이 키(§3.5.3)의 1/16 단위가 범위 1048576/2^24 와 맞는다는 이전 정합성 관찰이 이제 근거를 갖습니다. 웹 격자는 색을 채널당 0..255 정수로 두면 원본과 같은 양자화입니다(셰이더 출력 → 8비트 정규화 저장의 반올림 방식은 GPU 하드웨어 동작이라 여기서 다루지 않음).
  - 정정(2026-10-03 [r6 paint]): 아래 5차 "확정 불가" 판정을 철회합니다. 이유: 비트 폭은 이름표가 아니라 게임 안 포맷 정보표로 정해지고, 그 표를 쓰는 크기 계산을 원본 실행했습니다. 포맷 **이름**(NVN 열거 이름)은 여전히 게임 바이너리에 없지만, 구현에는 필요 없습니다. 과거 기록은 그대로 둡니다.

  채널 수는 스위즐 표로 확정이고, 비트 폭(8비트 UNORM)은 NVN 열거값 이름 기억에 기댄 **[추정]**입니다. **확정 불가(2026-10-03 [r5 paint])**: main 문자열에서 agl 포맷 번호(10, 0x1d, 0x5b, 9) → 이름 표를 찾지 못했습니다. `R8_G8_*`, `D24_S8` 문자열은 Havok 이미지 형식(hkImageFormat) 이름이고 agl 표가 아닙니다. NVN 포맷 열거값의 이름은 드라이버 쪽에 있어 게임 바이너리만으로는 확인할 수 없습니다. 다음 근거: NVN SDK 헤더(원본 밖) 또는 포맷별 바이트 크기를 쓰는 코드(텍스처 메모리 크기 계산 0x7102c4881c 안의 크기 조회)를 따라가 비트 폭을 역산. 참고로 깊이 키(§3.5.3 D+0x0c)의 해상도 1/16 단위가 0x5b 를 24비트 깊이로 볼 때 범위 1048576 / 2^24 와 정확히 맞습니다(정합성 근거일 뿐 **[추정]**). 규칙 값 `*(*(*0x71058e42f8+200)+0x6548)+0x3c`가 5일 때만 3팀(B 채널·스텐실 비트 4)을 씁니다. 이 값은 대전 설정 `Rule`이고 5 = Tcl(트리컬러)입니다(SHARED [netrest]: 문자열→정수 0x71010c8e3c 원본 실행 Pnt0 Var1 Vlf2 Vgl3 Vcl4 Tcl5) **[판독 연결]**.
- **A 채널 [판독]**: 도색 모드 0~12·14~17의 채널 마스크(§3.5.4 표)는 A를 쓰지 않습니다. 2팀 규칙에서는 텍스처에 A가 없고 스위즐로 1을 읽습니다. A를 쓰는 것은 모드 13(깊이 ALWAYS·스텐실 REPLACE 0·RGBA 전부, 초기화로 추정)뿐입니다. 즉 A는 도색 판정·카운트와 무관합니다(셰이더의 A 계산은 결과가 버려짐). 이전 판의 "A 채널 의미 [미확정]"을 해소합니다.
- 렌더 패스 순서 문자열 `Paint , PlayerPaintMonitor , PaintMonitor , PreMain , Main , MiniMap , ...` **[데이터]**. Paint = 스탬프 패스 `0x7102c50f20`, 그 뒤의 두 모니터 패스는 카운트 모드 14~17을 그리는 `0x7102c3e570`(목록 칠시스템+0x5a5b8, 매 프레임 비움)과 `0x7102c51004`(목록 +0x5a668)로 봅니다 **[추정 — 이름 순서와 함수 역할 대응]**. 2026-10-03 [r5 paint] 보강: 등록 함수 `0x7102c3e2f0`이 `0x71010f6bf8(번호, …)`로 스탬프 패스(콜백 → 0x7102c50f20)를 **번호 0**, `0x7102c3e570`을 **번호 2**로 등록합니다. 0x71010f6bf8 은 이 번호로 렌더 관리자(*0x7105999378) +0x28 배열을 색인합니다 **[판독]**. 번호가 위 이름 열거 순서(Paint 0, PlayerPaintMonitor 1, PaintMonitor 2)라면 `0x7102c3e570`은 `PlayerPaintMonitor`가 아니라 `PaintMonitor`입니다. 이름 `PlayerPaintMonitor`를 단 객체는 따로 `0x7102c3d954`(vtable 0x7105680730)가 만듭니다. 번호 = 열거 순서라는 점은 **[추정]**입니다.
  - **해소 (2026-10-03 [r6 paint]) [실행]+[판독]**: 이름 배열 함수 `0x71010f7ba8`을 원본 실행하면(스텁: PLT 의 guard·mutex 만, `web/tools/r6_paint_uc.py`) `[0] Paint, [1] PlayerPaintMonitor, [2] PaintMonitor, [3] PreMain …` 순서의 이름 포인터 배열을 돌려줍니다. `0x7102c3e2f0`은 번호 0 을 `이름[0]`(+0x00)과, 번호 2 를 `이름[2]`(+0x10)와 함께 넘깁니다. 다른 등록 함수들도 같은 규칙입니다(예: `0x710110d1b0` 번호 7 ↔ `이름+0x38`, `0x7101118ee0` 번호 10 ↔ `+0x50`). 따라서 **`0x7102c50f20` = `Paint` 패스, `0x7102c3e570` = `PaintMonitor` 패스**입니다. 번호 1(`PlayerPaintMonitor`)을 등록하는 코드는 `0x71010f6bf8` 직접 호출자 2곳 중에 없습니다. 플레이어 발밑 모니터도 `PaintMonitor` 패스에서 셉니다(§7).
  - `0x7102c3d954`가 만드는 0x248 B 객체는 렌더 패스가 아니라 이름 문자열 "PlayerPaintMonitor"를 붙인 프로세스(태스크) 객체입니다. 기반 생성자 `0x7103c7e4d8`(시퀀서 공통 기반)를 쓰고, 칠 관리자 초기화 `0x7102c4ff64`가 `0x7102c3d6bc`("PaintBaseProc" 설정)로 만들어 관리자+0x2c8 에 둡니다 **[판독]**. 발밑 샘플 사슬과는 무관합니다.

### 3.2 지형 도색 UV (ColPaint)

지형 모델에는 도색용 UV가 데이터로 들어 있지 않고, 실행 중 충돌 메시에서 만듭니다. 근거는 단언 문자열에 남은 함수 이름입니다 **[데이터]**:

`ColPaintBuilder::build / buildOriginal_ / buildReplica_ / setupPanel_ / setupMapModel_ / setupPaintUV_ / setupGraffiti_ / setupChangePaintableArea_ / setupColMeshTable_`, `ColPaintPanelExtractor::extractPanel / mergeInsidePanel_ / aggregatePrismInFace_`, `ColPaintPrismExtractor::extractPrisms`, `ColPaintPanelConnector::connectPanel / fixConnection`, `ColPaintPanelPatternRecognizer::*`, `ColPaintUVMapper::map / mapUVWithGroup_`, `ColPaintPixelAreaBuilder::buildPixelAreaWithDir`, `ColPaintPixelAreaGroupHolder::calcAreaNumInGroup`, `SimpleColMgr<ColPaintHorizontal,8> / <ColPaintVertical,7>::buildOctree`, 스레드 이름 `ColPaintThread`.

즉 충돌 삼각형 → 패널(평면 묶음) 추출 → 연결·패턴 인식 → UV 아틀라스 배치 → 픽셀 영역 그룹 → 수평/수직 옥트리입니다. (2026-10-02 [paint4] 갱신, 이전 "알고리즘 미판독 [미확정]") 프리즘 42방향 분류·기저·깊이 슬랩·패널 추출(옥트리 이웃 + 정점 공유)·병합·텍셀 밀도(8/단위, 올림, 여백 3)·기요틴 패킹을 판독하고 원본 실행으로 확인했습니다 → **[colpaint_atlas.md](colpaint_atlas.md)**. 연결(띠)·패턴 인식·시각 메시 매핑은 아직 [미확정]입니다.

### 3.3 칠 가능 여부 데이터

- 스테이지 배치(`Vss_Yagara`)에 `ChangePaintableArea` 78개(Layer Cmn, `TeamCmp.Team`, Scale), `Mpt_GeneralCube…AP` / `…NP` 상자, 리프트에 `spl__PaintBancParam`, `spl__LiftBancParam.ToNotPaintableArea` **[데이터]**. AP/NP = 칠 가능/불가 로 보는 것은 이름 기반 **[추정]**.
- 재질 쪽: `ForceColPaintNotPaintable/Paintable/YPlus` 태그가 Phive 설정에 있음(SHARED [gimmick]) **[데이터]**.
- 도색 요청 단계의 재질 차단은 [paint_shape.md §7.2](paint_shape.md#72-조기-종료-판독) 참고.
- **칠 불가 규칙 정리 (2026-10-03 [r5 paint])** — 원본에서 확인한 것만 적습니다.

  | 단계 | 규칙 | 근거 | 확정 |
  |---|---|---|---|
  | 지형 아틀라스 생성 | MaterialCollection 21(Fence)·22(RopeNet) 삼각형, UserShapeTag bit 50(`ForceColPaintNotPaintable`) 삼각형은 패널(=텍셀)이 생기지 않음. bit 48(`YPlus`)은 위 방향(0x28)으로 강제. bit 49(`ForceColPaintPaintable`)는 이 단계에서 보지 않음. 물(MaterialCollection 2)은 이 단계에서 걸러지지 않음 | 0x7102c0725c, [colpaint_atlas.md](colpaint_atlas.md) §4.1 | [판독]+[실행] |
  | 슈터·스플래시 요청 구성 | 접촉 목록 중 하나라도 상대 쪽 재질 레코드 +0xb 바이트 & 0x60, 즉 UserShapeTag **bit 29 `KebaInkCore`·bit 30 `KebaInk`**가 켜져 있으면 그 탄은 아무 데도 칠하지 않음 | 0x7101765fd8 (paint_batch1.c 137행). 같은 16 B 레코드를 벽 낙하 함수가 `u64(+8) >> 25`와 `byte(+0xb) >> 1`로 둘 다 bit 25(`Fence`)로 읽으므로 +8 = u64 태그 마스크, +0xb = bit 24~31 바이트 | [판독]+[데이터] |
  | 벽 낙하 방울 | 접촉 상대 태그 bit 25(`Fence`)면 바닥 도색을 건너뜀 | 0x71018ae054(walldrop_redecomp.c 505행), 0x71018ae5e8(783행) | [판독]+[데이터] |
  | 대상 단계 | 강체 +0x230(도색 대상 정보)이 없으면 거부, 대상 정보 +7 바이트가 0이면 종류 0(거부) | 0x7102c4126c, 0x7102c71e50 | [판독] |
  | 대상 단계 | 지형(Col)은 요청 법선 · 패널 대표 축 < 0.001 이면 거부(뒷면·수직면) | 0x7102c40cd0 | [판독] |

  로비(`Lby_Lobby00`) 충돌에 KebaInk 태그가 있는지는 이번에 데이터로 세지 않았습니다. 어떤 충돌 강체가 +0x230 도색 대상 정보를 갖는지(장외 바닥·KeepOut 벽·물 포함 여부)는 **[미확정]** — 다음: 강체 +0x230 writer(대상 등록), ColPaint 빌드의 TargetCollisionList 구성.

### 3.4 잉크 텍스처 종류 (InkTexType, InkTexInfo)

`spl::paint::InkTexType` 열거 문자열 **[데이터]**:
`Shot00, Shot01, Shot02, Shot03, Shot04, RlrSplash00, RlrSplash01, RlrSplash02, ChgrSplash00, ChgrSplash01, Bomb00, WallDrip00, WallDrip01, Roller00, PaintLift00, PaintLift01, Disk, Rectangle, InkRutStart, InkRutMove, QuadDonut, Rain00_0, Rain00_1, Rain00_2, SprBall00, StampKingFace, Common, WallDrip00_0..4, WallDrip01_0..4, SpStamp00, Death00, SprLanding00, Manta, GachihokoCross00, BombLineMarker, Slosher00, Chgr00, Bomb00Height3pnt4, Bomb00ForBombFlower, TripleTornado, DiskHD, AllPaint`

`InkTexInfo` 50행 필드 (`analysis/paint/InkTexInfo.json`) **[데이터]**:

| 필드 | 예 (Shot00) | 의미 |
|---|---|---|
| TextureName | "" (빈 값이면 행 이름) / Chgr00 → "Shot00" | 사용할 스탬프 텍스처 |
| PatternNum | 12 | 변형 수 (`Shot00_0`~`_11`) |
| AnimationFrame / AnimationStep | 3 / 3 | 한 요청을 AF번, AS 프레임 간격으로 다시 그림(매번 카운트) [판독, §3.5.7]. 매 회 무엇이 바뀌는지 [미확정] |
| HeightRangeType | MinEdge | `MinEdge , MaxEdge , Static , None` = 0..3. 높이 범위 ±Rate·min(W,L)/2, ±Rate·max(W,L)/2, (Max,Min), ±20000 [판독, §3.5.3] |
| HeightRangeRate | 1.0 | |
| StaticHeightRangeMin/Max | -1 / 1 | Static 일 때 높이 범위 |
| DisableSlopeScale | false | 참이면 D 법선 0 → 경사 보정 없음 [판독, §3.5.5] |

스탬프 텍스처는 0~1 그래디언트(BC4)입니다. 값 → 칠함 판정은 셰이더 `PaintOverpaint`(Hoian_Proc.sharcb)에서 확인했습니다 **[판독]** — [../graphics/shaders.md §4](../graphics/shaders.md): 도색 텍스처 RGB = 팀 0/1/2 잉크량, `ink = 마스크 × cAlpha(요청 +0x58 바이트/255)`로 팀 원-핫 색에 보간, 결과 텍셀에서 **내 팀 채널 ≥ 0.3(`cTeamAlphaTestThreshold`)이면서 최대**일 때만 기록(ALPHA_TEST 변형 = 모드 0·1·2·4~7·11 — 이 모드들은 색을 쓰지 않고 소유 스텐실·카운트만 정합니다. 실제 색은 알파 테스트 없는 모드 9가 씁니다. 모드 표는 §3.5.4). 마스크 값 자체에는 임계가 없고(ink > 0이면 참여), 빈 텍셀은 `ink ≥ 0.3`, 상대가 1.0으로 칠한 텍셀은 `ink ≥ 0.5`부터 넘어옵니다.

### 3.5 GPU 도색 파이프라인: 요청 → 큐 → 렌더 패스 **[판독]** (2026-10-02 [paintgpu])

디컴파일: `analysis/decomp/paintgpu/pg1.c`~`pg7.c`(이번 작업), `paint/paint_batch3.c`(0x7102c4126c), `shader/paint_draw*.c`, `gauge/gauge_batch2.c`(0x7102c13750, 0x7102c1461c). 기준 객체: **관리자** = `*(*0x7105790c60)`(= `*0x71058f07b8`), **칠시스템** = 관리자+0x2d8, **N** = 네트워크 레코드(0x60 B), **D** = 그리기 레코드(vtable 0x710567e2e8, 칠시스템이 풀에서 할당).

#### 3.5.1 대상 단계 `0x7102c4126c(bits, 강체, 셰이프키, 접촉점, req, cb)`

```
if 강체+0x230 == 0: 거부
info = 0x7102c71e50(...)               // kind(1 Floor / 2 Col / 3 Obj), id(u16), 면 비트
if !0x7102c45844(kind, id, ...): 거부  // 대상 유효(오브젝트 목록·Col 셀 존재)
if 관리자+0x30a && req.y < 관리자+0x30c: 거부        // 전역 높이 하한 [판독], 용도 [미확정]
local = {pos 0, 기본 법선/방향(*0x71057995b0/b8), size = req+0x24, -1.0}
0x7102c3fef0(&local, 강체, 셰이프키, req)            // 강체 변환(+0xd8..+0x104)으로 대상 공간 요청 [판독-부분]
중복 비트(bits = 0x7102c44e18 스택 0x280 B):
   Obj: (id*6 + 면) 비트(0x600개)가 모두 켜져 있으면 거부, Col: id 비트(0x1400개), Floor: bits+0x340 바이트
0x7102c40cd0: Obj → 대상 vt+0xc0(법선, 면), Col → 법선·축(*0x71058ed12c) < 0.001 이면 거부(뒷면)
if req+0x2c > 0 && |접촉.y − req.y| >= req+0x2c: 거부    // 슈터는 −1.0 → 검사 안 함
cb(&local, info) → 0x7102c449f0 (위 §3 흐름)
성공하면 중복 비트 켬
```

**대상 공간 변환 `0x7102c3fef0` (2026-10-03 [r5 paint], 이전 [판독-부분]) [판독]+[실행 6000/6000]**: 대상 정보는 `0x7102c71e50`이 **간접 반환 레지스터 x8**로 돌려줍니다(+8 종류, +0xc id). 강체 변환 R|t = 강체 +0xd8..+0x104(3×4 행 우선, 마지막 열 = 이동)입니다.

```
Obj(3)  : 위치 q = Rᵀ(p − t), 법선·방향 = Rᵀ·v                          // 오브젝트 지역 좌표
Col(2)  : q = Rᵀ(p − t) → (메시 트리 관리자+0x2c0 → +0x3a8, 0x7102c0df24 가 준 형상 키로 찾은 3×4 가 있으면 곱함)
          → 패널 좌표 (u, v, w) = (B0·q, B1·q, B2·q),  B = 0x7102bd7b2c(패널 +0x54 매핑 방향)
          법선·방향도 같은 식(이동 없음)
Floor(1)·그 밖: 요청 그대로(월드)
f32 순서: 각 내적 ((a·b + c·d) + e·f), FMA 없음(명령 판독)
```

원본 실행 `web/tools/r5_paint_colxform_emu.py`: 강체 단위·임의 회전/이동 반반, 패널 매핑 방향 0..0x29 무작위 6000건에서 9성분(위치·법선·방향) 비트 일치. 스텁 범위는 §8.

`관리자+0x30a`/`+0x30c`(전역 높이 하한)는 관리자 생성자(0x7102c4fb30 근처)에서 0으로 초기화되는 것만 찾았습니다. 0x7102b00000~0x7102d00000 범위에서 `#0x30a`/`#0x30c` 직접 저장을 전수 검색했지만 이 관리자에 1·값을 쓰는 명령은 없었습니다 **[미확정]** — 다음: 관리자 포인터(*0x71058f07b8)를 받아 구조체 복사로 쓰는 경로, 또는 레지스터 간접 주소.

**해소 (2026-10-03 [r6 paint]) — 높이 하한 = 수면(Ocean) 높이 [판독]+[데이터]**: 검색 범위를 main 전체로 넓히니 `strb #0x30a` 12곳 중 칠 관리자(GOT `0x7105790c60`)를 읽는 함수가 2개 있었습니다. 둘 다 수면 객체(vtable `0x7105562c00`, 같은 코드 범위에서 `OceanType`·`DrawOceanSurfaceType`·`OuterMeshVertWidth` 문자열 사용) 메서드입니다.

| writer | 쓰는 값 | 부르는 곳 |
|---|---|---|
| `0x71011311a4` (`0x7101131404`: +0x30a = 1, `0x7101131408`: +0x30c) | 수면 파라미터(객체+0x1c0 → +0x158 를 `$parent` 사슬로 따라간 뒤 +0x60) **+0x3c = `OceanMesh.OceanHeight`** (f32 비트 그대로) | 수면 갱신 `0x710112fa64`(vtable 칸 0x7105562f00), 파라미터 방문 `0x7101131b2c` |
| `0x7101131424` (`0x7101131930`/`0x7101131934`) | `OceanHeight + 동적 오프셋`(조건부로 다른 객체 +0x290 값을 더함), 같은 값을 객체+0x1d0 → +0x1028 에도 씀 | vtable 칸 0x7105562f10 |

- `OceanHeight`는 `game__gfx__parameter__OceanMesh`(리플렉션 vtable 0x71055698c0, 생성자 0x71011c8bc4, 기본값 0.0, 필드 +0x3c; 타입 이름은 같은 vtable 슬롯3 `0x71011c98c4` 가 씀) **[판독]**.
- **용도**: §3.5.1 의 `if 관리자+0x30a && req.y < 관리자+0x30c: 거부` → **수면보다 낮은 위치의 칠 요청은 대상 단계에서 버려집니다** **[판독]**.
- 데이터: `Vss_Yagara` 씬 팩에 `Gyml/Vss_YagaraWater.game__gfx__parameter__Ocean.bgyml`이 있고 `Mesh.OceanHeight = 0.0` **[데이터]** → 야가라는 y < 0 요청 거부. 물 충돌 평면 y = −0.05([colpaint_atlas.md](colpaint_atlas.md) §4.1)에 닿은 요청은 이 규칙으로 칠해지지 않습니다(요청 y가 접촉점 근처일 때). 로비 씬 팩 `LobbyVersus`에는 Ocean 파라미터가 없습니다 **[데이터]** → 수면 객체가 없으면 +0x30a = 0(생성자 값) 그대로라 높이 하한이 없습니다. 로비에 다른 경로로 수면 객체가 생기는지는 씬 팩 밖을 보지 않았습니다.
- 웹: 스테이지에 Ocean 이 있으면 `paintFloorY = OceanHeight`(+동적 오프셋, 야가라는 0)를 두고 `req.y < paintFloorY` 요청을 버립니다.

#### 3.5.2 네트워크 레코드 N (`0x7102c3ea50(N, local, B, C, info)`, 0x60 B)

| N 오프셋 | 값 | 출처 | 비고 |
|---|---|---|---|
| +0x00 u8 | 플레이어 번호(0~7) 또는 8+팀 | B+0(소유자 식별값) → `*0x7105801cb8` vt+0x30 → `0x71026437d0` | 소유자가 플레이어가 아니면 8(+C+4 팀, 팀이 −1/3이면 8) |
| +0x04 | B+4 | 탄 슬롯105 등(요청 번호) | 0x1745d1 = 특수값 |
| +0x08 | 위치 | local | |
| +0x14 | (W, L) | local+0x24 | |
| +0x1c | 법선(정규화, 0이면 (0,1,0)) | local+0xc | |
| +0x28 | 진행 방향(정규화, 0이면 (1,0,0)) | local+0x18 | |
| +0x34 | **팀** | **C+4** | cColor·cTeam·모드 선택에 쓰임 |
| +0x38 | 대상 종류 1/2/3 | info | 1 → FloorPaintEvent, 2 → Col, 3 → Obj |
| +0x3c u8 | 면 비트 | info / Obj vt+0xf0 | |
| +0x3e u16 | 대상 id | info | |
| +0x40 | InkTexType | C+8 | |
| +0x44 | **칠 종류** | C+1 ≠ 0 → 3(지우기); InkTexType 0x12/0x13(InkRutStart/Move) 또는 소유자가 플레이어 0~7이 아님 → 2; 그 밖 → C+0(0 또는 1) | 큐와 게이지 여부를 정함 |
| +0x48 u8 | cAlpha 바이트 | C+0xc(슈터 0xff) | |
| +0x49/+0x4a | 0 | | 0x7102c3f0c4 등이 나중에 씀 |
| +0x4b, +0x4c | 높이 범위 직접 지정 여부, (max,min) | C+0xd, C+0x10 | 슈터 (+20000, −20000) |
| +0x54, +0x58 | 시드 직접 지정 여부, 시드 | C+0x18, C+0x1c | |

정정 **[판독]**: [paint_shape.md](paint_shape.md) §7.6의 `B+0x00 = 팀`, `C+0x04 = ownerKey? [미확정]`은 거꾸로였습니다. B+0은 플레이어 번호로 바뀌는 소유자 식별값이고, 팀은 C+4입니다.

#### 3.5.3 그리기 레코드 D (`0x7102c11f80(D, N)`, D 객체 vtable 0x710567e2e8 슬롯 2) — **[판독]+[실행(에뮬) 600/600]**

| D | 값 |
|---|---|
| +0x08 | N+0 (플레이어 번호, 8 이상이면 카운트 안 함) |
| +0x0c f32 | `u32(온라인 ? (N+4 == 0x1745d1 ? 0xfffffb : N+4×11 + N+0) : N+4×11) × 0.0625` — **깊이 키**(아래). (이전 "소비처 [미확정]" 해소, 2026-10-03 [r5 paint]) |
| +0x10 | 팀(N+0x34) |
| +0x14 | 위치, +0x28 (W,L), +0x3c 진행 방향 |
| +0x30 | 법선. InkTexInfo 행 +0xc8(DisableSlopeScale)이 참이면 0 → 경사 보정 없음(§3.5.5) |
| +0x20/+0x24 | 높이 범위 (max, min): N+0x4b면 N+0x4c; 아니면 HeightRangeType별 — MinEdge(0): ±Rate·min(W,L)/2, MaxEdge(1): ±Rate·max(W,L)/2, Static(2): (행+0xbc, 행+0xc0), None(3): ±20000 |
| +0x48 | 애니 프레임 0, +0x49 = 행+0x14(AnimationFrame), +0x4a = 행+0x18(AnimationStep) |
| +0x4c | 대상 종류, +0x50 면 비트(Obj만), +0x52 대상 id |
| +0x54 | 시드 = N+0x54 ? N+0x58 : `|fcvtzs((p.z + (p.x + p.y)) × 100)| + N+4` (p = 0x7102c4a6bc(kind, id, 위치) = 대상 공간 위치, Floor는 위치 그대로) |
| **+0x60** | **스탬프 텍스처 = 행.텍스처[ r % PatternNum ]** (r = sead::Random(시드)의 첫 u32; 행+0x00 개수보다 크거나 같으면 [0]) |
| +0x58 | cAlpha 바이트 = N+0x48. 지우기(N+0x44 == 3)면 `(int)(min(1, N48/255 × AnimationFrame) × 255)` |
| **+0x6c** | **N+0x44 != 1** → 게이지 포함 여부(§4.4) |
| +0x6d | 지우기이고 N+4 == 0x1745d1 |
| +0x6e | N+0x49 && (id >> 10) > 4 |

**D+0x0c = 스탬프 깊이 키 [판독]+[실행] (2026-10-03 [r5 paint])**:
- N+4(요청 번호)는 탄 슬롯105 `0x71016696f8` = `min(max(GameFrame, 0), 0x1745d1)`입니다. GameFrame = `*0x710580e758`+0x148, 기기 간 동기된 게임 프레임(SHARED [netsync]) **[판독]**.
- 대상 vt+0x68(Floor `0x7102c1b7c8`, 기본 클래스 `0x7102bc3c3c`)이 스탬프 이동량의 **y 성분에 D+0x0c를 그대로** 넣습니다. Col은 `0x7102c0d554 → 0x7102bed4f0(s0 = D+0x0c)`입니다.
- 도색 카메라는 렌더러 +0x8a8 LookAt(위치 (0, 1048575.875, 0), 주시 (0,0,0), 위 (0,0,−1))입니다. 투영은 직교 near 0 / far 1048575.875, 깊이 범위 (0, 1)이므로 **D+0x0c가 클수록 카메라에 가까워 깊이 값이 작습니다**. 원본 실행으로 D+0x0c를 1/16 늘릴 때 clip z가 항상 줄어드는 것을 확인했습니다(200/200, §8).
- 키 범위: 오프라인 `frame×11/16`, 온라인 `(frame×11 + 플레이어)/16`. 최대 `0x1745d0×11+7 = 16 777 207 < 2^24`이므로 f32에 정확히 들어가고, ×1/16 하면 1048575.4로 카메라(1048575.875) 아래입니다. 0x1745d1 특수값은 0xfffffb/16 = 1048575.6875로 가장 가깝습니다.
- 쓰임은 §3.5.4의 깊이 테스트입니다(모드 0~11 깊이 비교 값 4 = 게임 문자열 표의 `lequal`). 같은 텍셀에서 **더 늦은 프레임의 요청이 이기고, 이미 늦은 요청이 소유를 차지한(모드 7이 깊이를 쓴) 텍셀에는 더 이른 요청의 재그리기(애니 프레임)·색 칠이 들어가지 않습니다**. 온라인에서 같은 프레임이면 플레이어 번호가 큰 쪽이 가깝습니다.

InkTexInfo 런타임 표 = `*0x71058eeae8`+0x40, 행 0xd0 B × 50(InkTexType 순서). 행 필드: +0x00 텍스처 수, +0x08 텍스처 배열(0xf8 B), +0x10 나눗수(PatternNum), +0x14/+0x18 AnimationFrame/Step, +0xb8 HeightRangeType, +0xbc/+0xc0 높이(max,min), +0xc4 HeightRangeRate, +0xc8 DisableSlopeScale. +0x14/+0x18/+0xb8/+0xc8은 소비 코드와 이름이 맞고, +0x10·+0xbc·+0xc0·+0xc4 이름은 쓰임(나눗수·(max,min) 쌍·배율)으로 붙인 **[추정]**입니다. 파서(0x71013c3fd0)의 임시 구조체는 다른 배치(+0x10 AF, +0x14 AS, +0x18 Rate, +0x1c Type, +0x20 PatternNum, +0x24 Max, +0x28 Min, +0x2c Disable)입니다.

**패턴 변형 번호 선택 규칙(해소)**: `Shot00_<k>`의 k = `sead::Random(D+0x54).getU32() % PatternNum`. sead::Random 초기화는 `s0=(x^x>>30)·0x6c078965+1 …+4`, 첫 값 `t=s0^(s0<<11); t^(t>>8)^s3^(s3>>19)` (SHARED [bullet] 난수식과 같음). 예: 시드 0 → 0x4807714d → Shot00_5 [재구현]. 텍스처 배열 순서가 `_0, _1, …` 이름 순서인지는 로더를 보지 않아 **[추정]**.

#### 3.5.4 큐·패스·모드·렌더 상태

**큐 선택** `0x7102c14dec(칠시스템, N)`: N+0x44 ∈ {0,1} → 큐0, 2 → 큐1(InkTexType 0x12/0x13이면 큐3), 3 → 큐2. 레코드 풀(칠시스템 +0x2c8 자유 목록, +0x2c0 사용 수 < +0x2d8 최대)이 차면 **그 요청은 버려집니다** **[판독]**. **풀 크기 = 2560(0xa00)개 [판독]** (2026-10-03 [r5 paint], 이전 [미확정]): 칠시스템 초기화 `0x7102c130a0`(호출자 0x7102c4ff64)이 칠시스템+0x2dc부터 0x90 B 레코드 2560개를 자유 목록으로 잇고 `+0x2d8 = 0xa00`을 씁니다(0x7102c131b0~0x7102c131b8). 큐 4개가 함께 씁니다. 슈터 레코드는 7프레임(0·3·6 그리기 뒤 제거)만 살므로 사격장 1인 연습에서 넘칠 일은 거의 없습니다(계산상 판단). 큐 q의 대기 목록 = 칠시스템+0x5a2e0+q×0xb0, 실행 목록 = 같은 블록 +0x18.

**패스 순서** `0x7102c14168`(렌더 패스 Paint, `0x7102c50f20`가 호출) — 각 단계는 `0x7102c1461c(…, 모드, D, 카운트 여부)`:

| 순서 | 대상 | 모드 | 카운트 |
|---|---|---|---|
| 1 | 큐0, D+8 < 8 | 4/5/6 = 팀 0/1/2 | **예**(플레이어 D+8의 카운터 엔트리) |
| 2 | 큐0 전부 | 7 | |
| 3 | 큐1 | 0/1/2 = 팀 | |
| 4 | 큐0, 큐1 | 9 (그 레코드 행 AnimationFrame−1회 추가 반복, 칠시스템+0x5a701일 때) | |
| 5 | 큐0, 큐1 | 12 (저해상도 tex1, 마지막 애니 프레임에만) | |
| 6 | 큐3(InkRut) | 8 | |
| 7 | 큐2(지우기) | 11 → 10 | |
| 별도 | 모니터 목록(`0x7102c148c0`) | 14/15/16(규칙 5만)/17, 플래그 +0x88 비트 0/1/2 | **예**(목록 항목 +0x80의 카운터 4개) |

`0x7102c1461c`: 대상 = D+0x4c(1 → 관리자+0x2b0, 2 → (관리자+0x2c0)+0x308, 3 → 관리자+0x2b8 목록[D+0x52]), 대상 +0x3a8 & ~1 == 2일 때만. `D+0x48 % D+0x4a == 0`(모드 12는 추가로 `(D+0x49−1)×D+0x4a == D+0x48`)인 프레임에만 그리고, 그릴 때 D+0x6f = 1. 렌더 상태 = 렌더러(`*0x71058ee648`) + 모드×0x74.

**모드별 렌더 상태** — 원본 실행 **[실행(에뮬)]** `web/tools/paintgpu_renderstate_emu.py`(0x7102c16e2c 기본 생성 18개 → 0x7102c16ed0 설정, 필드 배치는 바인드 함수 0x7103588fcc 판독, 결과 `analysis/paintgpu/renderstate_emu_out.txt`). 스텐실 비교/연산 이름은 NVN 열거값(1=NEVER…8=ALWAYS, 1=KEEP 2=ZERO 3=REPLACE) **[추정: 값→이름]**:

| 모드 | 셰이더 변형 | 깊이 테스트/쓰기 | 스텐실 (함수, ref, 비교 마스크, zpass) | 색 쓰기(타깃0) | 쓰임 |
|---|---|---|---|---|---|
| 0/1/2 | ALPHA_TEST | LEQUAL / 씀 | ALWAYS, 팀비트 1/2/4, REPLACE | 없음 | 큐1 소유 표시 |
| 3 | 기본 | LEQUAL / 씀 | ALWAYS, 3(규칙5: 7), REPLACE | 없음 | ~~쓰는 곳 못 찾음~~ → 높이 텍스처 대상 초기화 `0x7102c49844`(아래, 2026-10-03) |
| 4/5/6 | ALPHA_TEST | LEQUAL / 안 씀 | **NOTEQUAL**, 팀비트, 마스크 팀비트, REPLACE | 없음 | **플레이어 칠 카운트** |
| 7 | ALPHA_TEST | LEQUAL / 씀 | 끔 | 없음 | 깊이만 ~~[용도 미확정]~~ → 소유 텍셀에 깊이 키 기록(아래, 2026-10-03) |
| 8 | WRITE_NORMAL | LEQUAL / 안 씀 | 끔 | RG(규칙5: RGB) | InkRut |
| 9 | 기본 | LEQUAL / 안 씀 | 끔 | RG(B) | **실제 색 칠** |
| 10 | ERASE | LEQUAL / 안 씀 | 끔 | RG(B) | 지우기 색 |
| 11 | ERASE+ALPHA_TEST | LEQUAL / 씀 | NOTEQUAL, 3(7), ZERO | 없음 | 완전히 지워진 곳 소유 해제 |
| 12 | 기본(+0x900 타깃) | 끔 | 끔 | RG(B) | 저해상도 사본 |
| 13 | 기본 | ALWAYS / 씀 | ALWAYS, 0, 마스크 0xff, 세 연산 모두 REPLACE | RGBA | 초기화 — 확정 [판독], 아래 참고(2026-10-03) |
| 14/15/16 | 기본 | 끔 | **EQUAL**, 1/2/4, 마스크 3(7) | 없음 | 팀 소유 텍셀 수 |
| 17 | 기본 | 끔 | NOTEQUAL, 3(7), 마스크 3(7) | 없음 | 전체 텍셀 수 |

(공통: 블렌드 마스크 0xfe = 타깃0 블렌드 끔, 컬링 값 2, 스텐실 쓰기 마스크 0xff(바인드에서 고정).)

**깊이 비교 이름 확정 (2026-10-03 [r5 paint]) [데이터]+[판독]**: 렌더 상태 +0x64 바이트는 바인드 0x7103588fcc가 변환 없이 `nvnDepthStencilStateSetDepthFunc`에 넘깁니다(0x71035892a4). 같은 필드를 gsys 재질 파서 0x71036bb5a4가 문자열 `gsys_depth_test_func`에서 채우는데, 이름 파서 0x71036bc6e0(`never, less, equal, lequal, greater, nequal, gequal, always` → 0..7)과 변환표 0x710499caf8 = [1,2,3,4,5,6,7,8]을 거칩니다. 따라서 **값 4 = `lequal`, 8 = `always`**는 게임 자체 이름표로 확정됩니다. 스텐실 비교(+0x6a → `nvnDepthStencilStateSetStencilFunc`)는 같은 1~8 체계로 보지만 게임 안 이름표를 찾지 못해 **[추정]**으로 남깁니다.

**모드 3·7·13 역할 (2026-10-03 [r5 paint], 이전 [미확정])**:
- **모드 7** = 큐0 전부를 알파 테스트하면서 **깊이만 씁니다**. 그 프레임에 소유를 얻을 수 있는(내 팀 ≥ 0.3 이고 최대) 텍셀에 요청의 깊이 키(D+0x0c)를 기록해서, 그 뒤 모드 9 색 칠과 다음 프레임 재그리기의 깊이 비교 기준이 됩니다 **[판독]**.
- **모드 13** = 대상 텍스처 초기화입니다. `0x7102c17e90`이 대상 전체 사각형을 이동 (0,0,0)(깊이 = far, 즉 1.0)·색 (0,0,0,0)·스텐실 0으로 그립니다. 대상 초기화 vt+0x98 `0x7102c56b58`과 vt+0xa0 `0x7102c56c80`이 주 텍스처(+0x4f8)와 저해상도(+0x900)에 한 번씩 부릅니다 **[판독]**.
- **모드 3** = 높이 텍스처가 있는 대상(vt+0x40 참: Col `0x7102c0d240` = 1, Floor·기본 `0x7102bc3e00` = 0)의 초기화 `0x7102c49844`에서 모드 13 뒤에 씁니다. `COPY_TYPE` 프로그램(Hoian_Proc)으로 높이 텍스처(+0x748)를 그리며 깊이를 쓰고 스텐실을 3(규칙 5는 7)으로 바꿉니다 **[판독]**. 스텐실 3은 모드 4/5/6(NOTEQUAL 팀비트, 마스크 팀비트)도, 모드 11(NOTEQUAL 3)도, 모드 17(NOTEQUAL 3 = 전체 수)도 통과하지 못하는 값입니다. 따라서 "칠 불가로 표시한 텍셀"로 보이지만, 셰이더가 어떤 텍셀을 버리는지(어느 텍셀이 3이 되는지)는 판독하지 않았습니다 **[추정]** — 다음: Hoian_Proc `PaintCopy`의 COPY_TYPE 변형 픽셀 셰이더([graphics] 역번역 도구 `shader_ryujinx/`).
  - **해소 (2026-10-03 [r6 paint]) [판독]+[데이터]**: `0x7102c49844`가 고르는 프로그램은 `PaintCopy`가 아니라 Hoian_Proc **`CopyBuffer`**(매크로 `COPY_TYPE` 0/1/2, baseIndex 68)의 `COPY_TYPE=1` 입니다. 근거: 프로그램 번호 전역 `0x7105564168` = 등록 객체 `0x7105564140`+0x28 이고, 등록 `0x7101142080`이 이 객체에 이름 `"CopyBuffer"`를 넣습니다. 매크로 값 문자열 `0x710492cadd` = `"1"`. (`PaintCopy`는 매크로가 없고 `discard`도 없는 단순 복사입니다.) 역번역(`dotnet …/shader_dump.dll prog-sharc … CopyBuffer`, 결과 `analysis/shader/hoian_proc_copybuffer/`):
    ```glsl
    // CopyBuffer COPY_TYPE=1 (binary 71)
    if (texture(cSrc, uv).x > CommonUBO.cParam0.x) discard;   // cSrc = 대상 높이 텍스처(+0x748)
    out = vec4(1)                                              // 모드 3 은 색 쓰기 없음 → 스텐실 3·깊이만 남음
    ```
    `cParam0` = `0x71035a7554`로 만든 16 B 블록의 첫 값 `0xc61c3c00` = **−9999.0**(`0x7102c49af4`~`0x7102c49af8`) **[판독]**. 그리고 높이 텍스처 지우기 `0x7102c18318`은 같은 `CopyBuffer`의 `COPY_TYPE=2`(픽셀 = `cParam0` 그대로 출력)를 `cParam0 = (−10000.0, −10000.0, −10000.0, −10000.0)`(0x7102c18584~0x7102c1858c 상수 `0xc61c4000`)으로 그립니다 **[판독]**. 따라서 **스텐실 3 = 높이 텍스처 값 ≤ −9999 인 텍셀 = 지우기 값 −10000 이 그대로 남은 텍셀 = 높이 마스크 그리기(`ColPaintMaskDrawer`, `0x7102bd919c`, Col 대상 vt `0x7102c0d7e8`에서 호출)가 한 번도 쓰지 않은 텍셀**입니다. 모드 17(전체 수, NOTEQUAL 3)·모드 4~6(소유 카운트)·모드 11 모두 이 텍셀을 건너뛰므로, 빈 아틀라스 칸과 패널이 덮지 않은 텍셀은 칠·점수 분모 d에서 빠집니다. 패스의 뷰포트·가위는 대상 텍스처 크기(+0x500/+0x504)와 대상 범위(+0x508..+0x514)로 계산합니다. `ColPaintMaskDrawer`의 패스 구성(`PaintMask` TYPE 0 → 2 → 1 → 4 와 깊이·임시 버퍼, 문자열 `ColPaintMaskDrawer::depth/temp`)은 [판독-부분]이고, 어떤 삼각형을 어떤 값으로 그리는지는 **[미확정]** — 다음: `0x7102bd919c`(14 KB) 본문. 셰이더 변형 선택은 [../graphics/shaders.md §4.2](../graphics/shaders.md) 그대로입니다(ALPHA_TEST 표 0~11, 12 이상 0). 모드 8·9는 그릴 때마다 `nvnCommandBufferBarrier`(0x7102c564d0 끝)를 넣어 다음 그리기가 앞 결과를 읽습니다 **[판독]**.

**모드 ↔ 도색 종류 대응(해소)**: 모드는 도색 종류(슈터·롤러·폭발)가 아니라 **패스의 역할 + 팀**입니다. 모든 일반 칠 요청은 같은 프레임에 "소유 스텐실 갱신(4~6 또는 0~2) → 색 칠(9) → 저해상도(12)"를 거칩니다. 종류 차이는 InkTexType(스탬프 텍스처·애니)과 N+0x44(큐)로만 납니다. 예외: InkRutStart/Move는 모드 8, 지우기 요청은 모드 11/10.

**결과로 정해지는 판정 규칙 [판독]**: 소유 스텐실은 "알파 테스트 통과(그 스탬프 뒤 내 팀 채널 ≥ 0.3 이고 최대)"인 조각에만 팀비트로 바뀌고, 팀 면적(§4.1)과 발밑 샘플(§7)은 그 스텐실을 EQUAL로 셉니다. **점수 집계도 셰이더와 같은 0.3·최댓값 규칙**(마지막으로 그 규칙을 통과한 팀)입니다. 색 텍스처는 모드 9가 알파 테스트 없이 쓰므로 소유를 바꾸지 못하는 약한 덧칠도 색에는 남습니다.

#### 3.5.5 스탬프 회전·경사 보정

- **회전 각 = 대상 vt+0x70 = `0x7102c1233c(D, 면)`** (모든 대상 클래스 공통 0x7102c56a24 → 0x7102c1233c) **[판독]**: 기저 B(Floor `0x71058ef334`, Col `0x71058ed114`, Obj 대상 vt+0xa8(면); 3×3)에서 `θ = sead_atan2Idx(d·(B2×B1), d·B1)`, d = D+0x3c(진행 방향). 즉 스탬프 L축을 진행 방향의 면 투영에 맞춥니다. (정정: [../graphics/shaders.md §4.2](../graphics/shaders.md)의 "표 인덱스에 팀 번호가 더해짐"은 이 반환값이었습니다 — SHARED로 [graphics]에 전달.)
- **경사 보정 = `0x7102c124bc(D, 면)`** → (φ, c): n = D+0x30, Z = B 셋째 행, t = normalize(n × Z); |t| ≥ 0.01이면 φ = −atan2Idx(t·B1, t·B0), c = |n·Z|, 아니면 (0, 1.0). n이 0(DisableSlopeScale)이면 (0, 1.0). 0x7102c564d0은 대상 vt+0x78이 참일 때만 이 값을 쓰고 아니면 (0, 1.0).
- 행렬 `0x7102c17ae0(크기 D+0x28, θ, (φ,c))`: c ≠ 1이면 θ+φ 방향으로 c배 축소 후 되돌린 뒤 θ 회전. 사인표 0x7104aa5b5c(256칸×16 B, 상위 8비트 칸 + 하위 24비트 보간). 각 단위 u32(2^32 = 360°)는 sead 관례로 **[추정]**. 정확한 곱 순서는 이번에 식으로 정리하지 않았습니다 **[미확정]**.
  - **정정·해소 (2026-10-03 [r5 paint]) [판독]+[실행]**: 표는 칸마다 `(sin, Δsin, cos, Δcos)`이고 칸 i = 2πi/256과 3.7e-8 안에서 같습니다 → **u32 2^32 = 360°** **[데이터]**. 곱 순서와 f32 순서는 아래와 같고, 원본 실행에서 출력 16원소가 6400/6400 비트 일치했습니다(`web/tools/r5_paint_stamp_emu.py`, §8).

```
(s,c)(a) = (T[a>>24].sin + T.Δsin·f, T.cos + f·T.Δcos),  f = (a & 0xffffff)·5.9604645e-08
M0 (3×4 행) = r0 (W,0,0 | 0),  r1 (0,0,1 | 0),  r2 (0,−L,0 | 0)        // 쿼드 (x,y,0) → (W·x, 0, −L·y)
Ry(a): r0' = fma(r2, sin a, r0·cos a) + 0,  r2' = fma(r2, cos a, r0·(−sin a)) + 0,  r1' = r1   // 원본은 fmla(융합)
c ≠ 1 (f32 비교) 이면: ψ = φ + θ (u32 덧셈) → Ry(ψ) → r0 ·= c → Ry(−ψ)
Ry(θ)
이동: r0[3] = p0 + r0[3],  r1[3] = p1 + r1[3],  r2[3] = −p2 + r2[3]     // p = 대상 vt+0x68 결과
VM  = (0,0,0,V_i3) + fma(r2, V_i2, fma(r1, V_i1, r0·V_i0))   (V = 렌더러 +0x8b0 3×4, 행 단위)
WVP = (0,0,0,P_i3) + fma(VM2, P_i2, fma(VM1, P_i1, VM0·P_i0)) (P = 대상 투영 +0x4c 4×4)
```

  - **원본 실행으로 확인한 의미 (Floor 대상, V = P = 단위로 월드 좌표를 직접 봄) [실행 200/200]**: 쿼드 +y(정점 셰이더 uv.y = 0, 즉 스탬프 텍스처 **첫 행 = PNG 위쪽**)는 **진행 방향 d를 면에 투영한 쪽, 길이 L**로 갑니다. 쿼드 +x(uv.x = 1, PNG 오른쪽)는 **d × 위(면 법선)** 쪽, 길이 W입니다. 경사 보정은 요청 법선 n의 수평 성분과 직교하는 방향, 즉 **등고선 방향 û = normalize(−n.z, n.x)(XZ)으로 c = |n·Z|배 압축**합니다. 가장 가파른 방향으로 압축하는 것이 아니라는 점에 주의합니다(원본 그대로). 예: n이 +X 쪽으로 30° 기울고 d = +Z면 L 축(+Z)이 0.866배, W 축(−X)은 그대로입니다. 표 보간 오차 때문에 의미 검사는 5e-4·크기 허용으로 봤고, 행렬 원소 자체는 비트 일치입니다.
  - 정점 셰이더 uv 식(`uv = (sign(x)·0.5+0.5, −sign(y)·0.5+0.5)`)은 [../graphics/shaders.md §4.3](../graphics/shaders.md) **[판독]**, PNG 추출(graphics_bntx.py)은 행을 뒤집지 않습니다(코드 확인).
  - **기저 전역 값 [실행]**: Floor 기저 0x71058ef334 = 행 (1,0,0)·(0,0,−1)·(0,1,0)(정적 초기화 0x7102c2e270), Col 기저 0x71058ed114 = 단위 행렬(0x7102bd77e0). 둘 다 원본 정적 초기화를 실행해 얻었습니다. Floor θ = atan2Idx(−d.x, −d.z), Col θ = atan2Idx(−d.u, d.v) + 패널 UV 행렬 회전 atan2Idx(m[3], m[0])(Col vt+0x70 `0x7102c0d5dc`)입니다.
  - **대상별 vt (2026-10-03 판독)**: Floor vtable 0x710567e540: +0x50 투영 객체(+0x2b8), +0x58 뷰포트 사각형(+0x368), +0x60 투영 갱신 `0x7102c1b5a4`(직교 ±size/2, near 0, far 1048575.875), +0x68 이동 `0x7102c1b7c8` = (B0·p, D+0x0c, B1·p), +0x80 높이 범위 `0x7102c1b820`. Col vtable 0x710567e058: +0x40 = 1(높이 텍스처 있음 → MASK 변형), +0x68 `0x7102c0d554 → 0x7102bed4f0`(패널 매핑 AABB 중심을 뺀 (u,v)에 패널 UV 행렬을 곱하고 S = 400/200 으로 아틀라스 위치를 만드는 것으로 보임 **[판독-부분]**, y 성분 = D+0x0c), +0x70 회전, +0x80 `0x7102c0d6e0` = (w + min, w + max) → 0x7102c564d0 이 이 값을 `cHeightRange`로 넘김(같은 지역 변수에 vt+0x68 결과를 먼저 받고 vt+0x80 으로 덮어씀)(패널 패턴 +0x9c ∈ {1,2,3}이면 매핑 깊이 중심을 뺌) → Col 스탬프는 **높이 텍스처의 패널 깊이 w가 요청 w ± 높이 범위 밖이면 버려집니다**(MASK 변형) **[판독]**.

#### 3.5.6 GPU 카운터

- 시작 `0x7101043e64`: 카운터 버퍼를 0으로 비우고 `nvnCommandBufferResetCounter(cmd, 1)`; 끝: `nvnCommandBufferReportCounter(cmd, 1, nvnBufferGetAddress(…+0x38))`; 읽기 `0x7101043cdc`가 결과 u32를 꺼냄 **[판독 — NVN 함수 이름은 로더 0x710083eb80 문자열로 확인, web/tools/paintgpu_nvnmap.py]**. 카운터 종류 1 = SAMPLES_PASSED(통과 조각 수)는 NVN 열거값 기억과 "색을 안 쓰는 스텐실 패스만 감쌈"에 근거한 **[추정]**.
- **플레이어 칠 카운터 C_i 엔트리 값의 의미(해소)**: 모드 4/5/6 그리기 하나가 통과시킨 조각 수 = 그 스탬프로 **새로 내 팀 소유가 된 텍셀 수**(이미 내 팀 스텐실인 텍셀은 NOTEQUAL에서 탈락 → 자기 땅 덧칠은 0, 상대 땅 뺏기는 포함, 같은 프레임 같은 팀 겹침은 먼저 그린 쪽만). 알파 테스트는 이 프레임 앞의 색을 읽습니다(색은 그 뒤 모드 9에서 바뀜). 집계·게이지 쪽은 [special_gauge.md](special_gauge.md) §4.2.
- **팀 면적 a,b,c,d**: 모니터 목록 항목마다 모드 14/15/16/17 → 카운터 4개(+0x80 → +0, +0x38, +0x70, +0xa8) → 카운터 객체(vtable 0x710567e9c8 계열) `0x7102c25654`가 2벌 교대로 읽어 +0x3c/+0x44/+0x4c/+0x54(+유효 바이트) 저장 → vt+0x70 `0x7102c25ed0`이 vt+0x78(i)로 out[0..3] + vt+0x60(유효) → `0x7102c54b84`가 합산 **[판독]**. 결과는 1~2프레임 늦은 GPU 결과입니다(이중 버퍼).

#### 3.5.7 프레임 순서와 레코드 수명 (`0x7102c13750`, `0x7102c50d18`에서 호출)

```
1. 플레이어 8명 카운터 C_i 갱신(0x7102c1aa74, GPU 결과 읽기)          ← special_gauge.md §3
2. 큐 0~3 실행 목록: D+0x6f(그려짐)이면 지우고 D+0x48++,
     큐2(지우기)는 바로 제거, 그 밖은 칠시스템+0x5a701 이거나 D+0x48 > (AF−1)×AS 이면 제거
3. 칠시스템+0x5a700 이면 모든 목록 비움(리셋)
4. 대기 → 실행 목록 이동(0x7102c14fb0), 모니터 대기 목록 처리(0x7102c14c7c)
렌더(Paint 패스 0x7102c50f20): 0x7102c14168 (§3.5.4 표 순서)
```

한 요청은 AnimationFrame(AF)번, AnimationStep(AS) 프레임 간격으로 다시 그려지고 매번 카운트됩니다(스텐실 덕분에 같은 텍셀을 두 번 세지 않음). 애니 프레임마다 무엇이 달라지는지(크기·마스크)는 **[미확정]** — D+0x60 텍스처는 고정이고, D+0x48을 읽는 그리기 쪽 코드는 찾지 못했습니다. 0x7102c50d18이 게임 갱신의 앞인지 뒤인지(같은 프레임 요청이 그 프레임에 그려지는지)도 **[미확정]**.

- **애니 프레임마다 바뀌는 입력 = 없음 (2026-10-03 [r5 paint], 해소) [판독]**: 그리기 경로 전체(0x7102c564d0, 0x7102c368dc, 0x7102c188b4, 0x7102c17ae0, 0x7102c1233c, 0x7102c124bc, 0x7102c195f0(모드 12), Floor vt 0x7102c1b7c8/0x7102c1b820, Col vt 0x7102c0d248~0x7102c0d7f0, 0x7102bed4f0)에서 D+0x48/+0x49/+0x4a 읽기를 전수 검색했고 없었습니다. 이 필드는 일정 판단(0x7102c1461c, 0x7102c13750)에서만 씁니다. 따라서 재그리기는 **같은 행렬·같은 스탬프 텍스처·같은 cAlpha·같은 높이 범위·같은 깊이 키**로 다시 그리고, 결과 차이는 목적지 텍스처(이전 색, 스텐실, 깊이)가 달라진 것에서만 생깁니다. 단 깊이 키가 요청 프레임에 고정되어 있으므로, 사이에 더 늦은 요청이 소유한 텍셀에서는 재그리기가 깊이 비교에 걸려 아무것도 바꾸지 못합니다(§3.5.3).
- **0x7102c50d18의 위치 [미확정]**: 호출자는 `0x710111773c` 하나이고(0x7101117930), 이 함수는 vtable 칸 0x7105561bc8에 있는 갱신 콜백입니다. 그 클래스와 게임 액터 갱신 대비 순서는 찾지 못했습니다 — 다음: vtable 0x7105561b40 근처의 클래스 생성자, 이 콜백을 부르는 시퀀서.
  - 2026-10-03 [r6 paint] 추적(여전히 **[미확정]**, 범위는 좁힘) **[판독]**:
    - vtable `0x7105561b68`(칸 0x7105561bc8 = 슬롯 12, +0x60)의 객체는 싱글턴 `*0x71058150c0`(0x4b8 B, 생성 `0x7101116b98` ← `0x7103446998`, 생성자 `0x7101116c70`)입니다. 같은 코드 범위가 `AglWork`·`DynamicTextureAllocatorMem`을 쓰는 그래픽 계열 엔진 모듈입니다.
    - 엔진 모듈 vtable 은 공통 슬롯 2 = `0x7103da6928`(모듈+0x10 문맥의 비활성 해시 표에서 모듈 해시(+0x18)를 찾아 꺼져 있으면 건너뛰고, 아니면 슬롯 11(+0x58)로 꼬리 호출)과 슬롯 12(+0x60)를 가집니다. `0x710111773c`도 같은 문맥(param_2+8 → {비트마스크, 해시 표})에서 해시 `0x56718537`이 꺼져 있으면 `0x7102c50d18`을 건너뜁니다.
    - 액터 프레임 그래프를 돌리는 엔진 모듈(vtable `0x710575b7b8`)은 슬롯 11 = `0x7103cdb41c`(그 안에서 그래프 구성 `0x7103c85fbc`, phive_controller.md §6.7)이고 슬롯 12 = `ret`(`0x7103cdb8b8`)입니다. 즉 **칠 시스템 갱신은 모듈의 슬롯 12 단계, 액터 그래프는 다른 모듈의 슬롯 11 단계**에서 돕니다. 두 단계의 선후는 모듈 실행기(`ModuleSystem::moduleCalc_` = `0x7103dac4a0` → `0x7103dac8b4`, 미리 만든 작업 그래프 +0x4c0 / +0x4b8 을 `0x7103acf4c8`로 실행하고 그 사이에 액터 그래프 `0x7103cdc608`)에서 정해지지만, 모듈 슬롯 11/12 를 작업 노드로 만드는 곳은 찾지 못했습니다 — 다음: `ModuleSystem` 초기화 `0x7103daae40`의 작업 그래프 구성, `0x7103d982c4`/`0x7103d554c4`(디컴파일 `analysis/decomp/r6_paint/modulecalc.c`).

## 4. 점수

### 4.1 면적 카운트 (0x7102c54b84) **[판독]**

```
paintSys = *( *(0x7105790c60) + 0x2f0 )
count = {a:0, b:0, c:0, d:0}                       // u32 4개
for target in [paintSys+0x2b0, paintSys+0x2b8, paintSys+0x2e0 의 트리 노드들(+0x28)]:
    if !target.vt[0x70] (&tmp): 실패 플래그
    count += tmp
```

- `a, b, c` = Alpha, Bravo, Charlie(트라이컬러 3팀) 팀이 칠한 텍셀 수, `d` = 전체(칠 가능) 텍셀 수. 근거: `0x7103092a4c`가 a/b/c를 `PaintPtAlpha/Bravo/Charlie`, d를 `PaintPtMax`로 기록 **[판독]**.
- 여기서 `paintSys`(관리자+0x2f0, 0x378 B, 생성자 0x7102c544e0)의 자식은 GPU 카운터 객체이고 vt+0x70 = `0x7102c25ed0`입니다. a/b/c는 모드 14/15/16(스텐실 EQUAL 팀비트), d는 모드 17(스텐실 NOTEQUAL 3/7 = 그 영역의 모든 조각) 그리기의 통과 조각 수입니다 — §3.5.4, §3.5.6. **팀 판정 규칙 = 셰이더 알파 테스트와 같은 "≥ 0.3 이고 최대"(스텐실 경유)** **[판독]** (2026-10-02 [paintgpu], 이전 "집계 임계 [추정]").
- 캐시 조회 `0x7102c54e0c`: +0x330 플래그가 켜져 있을 때만 동작, 직전 값(+0x2c0~+0x2d0)과 비교해 갱신 여부 결정 **[판독]**, 정확한 갱신 조건의 의도는 **[미확정]**.

### 4.2 p 환산 **[판독]**

```
teamP   = fcvtzu( (float)count * 0.015625f * 0.3030303f )   // = count / 64 / 3.3, 음수면 0
playerP = (int)( (float)player.paintCount / 211.2f )         // player.paintCount = 플레이어정보 +0xbd4 (u32)
```

- 64 = 8×8 텍셀, 3.3 = 1평(坪, ≈3.3 m²). 누적 통계 이름이 `TotalPaintTubo`/`total_paint_tubo`인 것과 맞습니다 **[데이터]**.
- 결과 기록 `0x7103092a4c`: 팀 결과 항목 +0x70 ← teamP(Alpha, Bravo, Charlie 순), 플레이어 결과 항목 +0x7c ← playerP. 같은 식을 HUD(`analysis/decomp/ui/hud_batch2.c`, `/211.2`)도 씁니다 **[판독]**.
- 결과 저장 키 `Result{ PaintPoint, PaintPermille, GachiLeftCount }`(0x710306a718, 객체 +0xa0/+0xa4/+0xa8) **[판독]**. PaintPermille(‰)은 심판 `0x710303bd80`이 `PaintPtMax`(=d/211.2)를 분모로 계산해 팀 결과 링(심판+0x128 → +0x10d0, 항목 0x80 B) +0x74에 씁니다. `permille = round_half_away(PaintPt / max(PaintPtMax,1) × 1000)`, 상위 두 팀이 같으면 정렬상 앞 팀 +1‰(그 팀 PaintPt도 다시 계산) **[실행(에뮬) — 2026-10-02 [gauge], 이전 [미확정]]**. 식·검증은 [special_gauge.md](special_gauge.md) §6.8.

### 4.3 경기 중 우세 단계 (VersusRefereePaint) **[판독]**

`VersusRefereePaint` vtable `0x71056a9460`, 슬롯19 `0x7103042394`:

```
if d == 0: 판정 안 함
ra = min(1, a/d);  rb = min(1, b/d)
diff = (int)(ra*10000) - (int)(rb*10000)      // 만분율 차
level = diff >= 1501 ? 0 : diff >= 1001 ? 1 : diff >= -1000 ? 2 : diff >= -1500 ? 3 : 4
0x710303e294(level) → 레이아웃 VS_MainTV_00 / Replay_Main_00 의 상태값 갱신
```

화면에서 무엇이 바뀌는지는 [ui] 담당 확인 대상입니다 **[추정 — 우세/열세 연출]**. 호출 주기도 **[미확정]**.

### 4.4 플레이어 칠한 포인트 누적 **[판독]** (2026-10-02 [gauge] 해소)

이전 판(“누적 경로 [미확정]”, 후보 `ResultCounter:ColPaint-Unit`·`spl::PaintedArea`)을 정정합니다. 두 후보는 경로가 아니었습니다: `0x7102c0c1cc`는 결과용 카운트 텍스처(크기 = 대상 크기/8/20 올림)를 만드는 함수이고, `spl::PaintedArea`(0x17a8 B)는 별도 컴포넌트입니다 **[판독]**.

- 저장 위치: 플레이어 본체(PlayerBehavior+0x108) +0xbd4 (u32, 텍셀). 이 주소는 스페셜 게이지 구조체 G의 +0이기도 합니다([special_gauge.md §4.1](special_gauge.md#41-게이지-구조체-g-기준-플레이어-본체--0xbd4)).
- 가산: `0x7102483134`가 매 프레임 `G+0 += C_i+4`. C_i = 칠 시스템(`*(*0x7105790c60+0x2d8)`) +0x5a708 + 플레이어번호×0xe18, +4 = 그 프레임 GPU 결과 합(반올림) **[판독]**. 사망 중에도 더합니다.
- 같은 카운터의 +8(“스페셜용” 목록만의 합)이 게이지로 갑니다. 요청 레코드 +0x6c가 0이면 p에만 들어가고 게이지에는 안 들어갑니다 **[판독]**. **+0x6c 세팅 경로(해소) [판독]+[실행(에뮬)]**: `D+0x6c = (N+0x44 != 1)`(0x7102c12310), N+0x44 = 요청 C+0(플레이어 칠일 때). 탄 경로에서 C+0 = !슬롯77 이고 슬롯77은 `spl::BulletSpJetpackLauncher`만 0 → **제트팩 탄의 칠만 p 전용**, 다른 탄(101개 vtable)은 p+게이지. 카운트되는 것은 큐0(N+0x44 ∈ {0,1})뿐이라 N+0x44 = 2(InkRut·비플레이어)·3(지우기)은 p에도 게이지에도 들어가지 않습니다. 0x7102c44e18의 다른 15개 호출자(폭발·롤러 등)가 C+0에 무엇을 넣는지는 **[미확정]**.
- C_i 엔트리 값 = 모드 4/5/6 스탬프의 GPU 통과 조각 수 = **새로 내 팀 소유가 된 텍셀 수**(자기 땅 덧칠 0) — §3.5.6 **[판독]**, 카운터 종류 이름 **[추정]**.
- +0xbe4(f32)는 G+0x10 게이지 비율, +0xbe8(f32)은 G+0x14 필요 p(SpecialPoint)입니다(이전 “의미 미확정” 정정).
- `0x71024981d0`의 `(int)(G+0x14 * 211.2)`는 리스폰이 아니라 "게이지를 가득 채우는" 이벤트 처리(명령 해시 0x6c2b6a0b 등)입니다. 게이지와 칠 p가 같은 211.2 단위를 쓴다는 이전 [추정]은 [판독]으로 올립니다.

### 4.5 스페셜

| 항목 | 값 | 근거 |
|---|---|---|
| 무기별 필요 포인트 `WeaponInfoMain.SpecialPoint` | 174행 중 200(153), 190(5), 180(16) | [데이터], 행 구조체 +0xcc (파서 0x71014199e4) [판독] |
| 기어 `SpecialIncrease_Up` 배율 | Low 1.0 / Mid 1.15 / High 1.3 (`IncreaseRt_Special_*`, 데이터 없음 = 기본값) | [판독] 생성자 0x710237d7f4 |
| `VersusConstant.SpecialGaugeAutoIncBasePoint` | 180 (기본값, 데이터 미기재; 생성자 `0x710305e014`가 +0x34에 0xb4) | [판독], 쓰임 [미확정] — 나와바리 심판의 자동 가산(vt+0x48)은 0.0 상수 |
| `SpecialGaugeAutoIncSec_Fast/_Slow` | 40 / 120 (같은 구조체 `DefaultSec 60, AdditionalTimeRate 0.75, DecSpd_Normal 10, ExtendKeepSec 10`) | [판독] 생성자 `0x71030601b4`, 쓰는 규칙 [미확정] |
| 무기 SpecialPoint → 게이지 | G+0x14 = (f32)SpecialPoint, 필요 텍셀 = (int)(SpecialPoint×211.2f) (200 → 42240) | [판독] `0x71024901c4`, [실행(에뮬 구간)] |
| `VersusConstant.Scorekeeper.ThresholdForArea` | 0.35 | [데이터], 쓰임 [미확정] |

기어 배율 계산 `0x7102663808` **[판독]**:

```
GP = min(57, mainPts[ability] + subPts[ability])     // 기어효과 객체 +0x3c[], +0x74[] (ability=5)
x  = clamp01( GP * (3.3 - 0.027*GP) / 100 )
t  = Mid 의 Low..High 역보간 (Low>High 이면 1 - High..Low 역보간), 범위 밖은 0/1
f  = |t-0.5| <= 0.001 ? x
   : |x| < 0.001      ? 0
   : t < 0.001        ? (|x| >= 0.999 ? 1 : 0)
   :                    expf( logf(|x|) * (logf(t) * -1.442695) )     // = x^(log t / log 0.5)
rate = Low + (High - Low) * f   → 기어효과 객체 +0xe8
```

- `0x710265ca04`가 능력 효과를 열거 순서(`MainInk_Save=0, SubInk_Save=1, InkRecovery_Up=2, HumanMove_Up=3, SquidMove_Up=4, SpecialIncrease_Up=5, …`)대로 계산하며 6번째 호출이 이 함수입니다 **[판독]**. 같은 블록의 다른 능력 함수도 같은 공식을 쓰는지는 **[추정]**(3.3 상수 사용 함수 21곳이 0x710265e040~0x710266d4cc에 모여 있음).
- GP의 단위(주 능력 10, 부 능력 3)는 57 상한에서 나온 **[추정]**.
- Mid=1.15는 Low/High 정중앙이라 선형(f = x) 경로를 탑니다.
- 이 배율(+0xe8)은 `0x7102483134`의 게이지 가산(`0x7102488d68`: `acc = G+8 + rate × 스페셜용 텍셀`)에서 곱해집니다 **[판독]+[실행(에뮬 구간) 400/400 비트 일치]** (2026-10-02 [gauge] 해소). 전체 가산식·비율식은 [special_gauge.md](special_gauge.md) §6.

## 5. 상태 수명

| 상태 | 생성·초기화 | 갱신 | 종료 |
|---|---|---|---|
| 도색 텍스처 | 대상 생성 시 `PaintTextureData::create` | 도색 요청마다 GPU 스탬프 | 대상 소멸 / PaintMgr 소멸자 0x7102c4fbe0 |
| 그리기 레코드 D | 0x7102c14dec(풀 할당, 대기 목록) | 렌더 패스마다 애니 프레임 조건에 맞으면 그림, 0x7102c13750이 D+0x48++ | 큐2는 한 번, 그 밖은 D+0x48 > (AF−1)×AS 또는 칠시스템+0x5a701 → 풀 반환(§3.5.7) |
| 팀 카운트 a,b,c,d | 텍스처에서 매 조회 시 합산 | 조회 시점(우세 판정, 결과) | 결과 기록 후 |
| 플레이어 paintCount(+0xbd4) | 경기 시작 0 | 매 프레임 += 칠 카운터 +4 (`0x7102483134`) | 결과 기록 |
| 스페셜 게이지(G+4/+8/+0x10) | 무기 장착 시 필요 p 설정 | [special_gauge.md](special_gauge.md) §5 | 스페셜 종료·사망 |
| 슈터 지연 도색(+0x1150) | 접촉 시 보관 | 다음 슬롯55에서 칠함 | ~~[미확정]~~ → 다음 슬롯54 첫머리 0x7101763a10(0x7101763a3c)에서 0 — [판독] (2026-10-03 [r5 paint], [paint_shape.md](paint_shape.md) §7.7) |

## 6. 웹 포팅 구조

원본은 GPU 텍스처에 칠하고 GPU에서 센 값을 읽습니다. 웹은 **판정·점수를 CPU 정수 격자로** 하고, 화면은 그 격자를 텍스처로 올려 그리는 구조를 권장합니다. 이유: 서버·클라이언트가 같은 결과를 내야 하고(점수·발밑 판정), WebGL 리드백은 느리고 기기마다 다를 수 있습니다.

### 6.1 모듈

| 모듈 | 책임 | 공유 |
|---|---|---|
| `paint/params.ts` | GameParameterTable 도색 파라미터 로드, `$parent` 필드 단위 상속 + 생성자 기본값 | 서버·클라 |
| `paint/shape.ts` | [paint_shape.md](paint_shape.md) 계산 → `PaintRequest` | 서버·클라 |
| `paint/atlas.ts` | 스테이지 충돌 삼각형 → 도색 아틀라스(삼각형/패널별 UV, 8 텍셀/단위) 사전 생성, `paintable` 마스크 | 빌드 도구 |
| `paint/grid.ts` | `Uint8Array` 팀 격자(0=없음, 1=Alpha, 2=Bravo, 3=Charlie), 팀별 카운트 증감 유지 | 서버·클라 |
| `paint/stamp.ts` | 요청 → 접촉 면들 → 아틀라스 텍셀 순회 → 스탬프 마스크 판정 → 격자 갱신, 바뀐 텍셀 수 반환 | 서버·클라 |
| `paint/score.ts` | teamP, playerP(211.2), 우세 단계, 기어 배율 | 서버·클라 |
| `paint/render.ts` | 격자 → `R8UI` 또는 RGBA 텍스처 업로드(변경 사각형만), 팀색 셰이더 | 클라 |

### 6.2 데이터 구조

```ts
interface PaintGrid { w: number; h: number; team: Uint8Array; paintable: Uint8Array;
                      count: [number, number, number]; total: number }   // total = paintable 텍셀 수 (원본 d)
interface PaintRequest { center: Vec3; normal: Vec3; forward: Vec3; size: [W: number, L: number];
                         team: 1|2|3; inkTexType: number; heightRange: [number, number]; ownerPlayer?: number }
```

| 원본 | 웹 이름 |
|---|---|
| 요청 A+0x00/+0x0c/+0x18/+0x24 | center / normal / forward / size |
| spawnInfo+0x2c (요청 C+4, N+0x34) | team (정정: 이전 판 spawnInfo+0x1c는 소유자 식별값) |
| 슬롯102 반환 | inkTexType |
| count a/b/c/d (0x7102c54b84) | grid.count[0..2] / grid.total |
| 플레이어정보 +0xbd4 | player.paintTexels |
| 기어효과 +0xe8 | gear.specialIncreaseRate |

### 6.3 갱신 순서 (1 게임 프레임)

1. 탄 이동 (bullet 담당) → 접촉 판정
2. 슬롯84: 즉시형(스플래시 등)은 `stamp()` 바로, 슈터는 `pending`에 보관
3. 같은 프레임 탄 후처리(슬롯55 위치)에서 이전에 보관된 슈터 요청을 구 질의로 `stamp()`
4. `stamp()`는 바뀐 텍셀 수를 돌려주고, 팀 카운트를 즉시 증감
5. HUD·우세 판정은 `grid.count/total`을 읽음

```ts
function stamp(g: PaintGrid, req: PaintRequest, faces: FaceHit[]): number {
  let changed = 0;
  for (const f of faces) for (const t of texelsInOrientedRect(f, req)) {
    if (!g.paintable[t] || !maskHit(req.inkTexType, t, req)) continue;
    const old = g.team[t]; if (old === req.team) continue;
    if (old) g.count[old - 1]--; g.count[req.team - 1]++; g.team[t] = req.team; changed++;
  }
  return changed;
}
const teamP = (n: number) => Math.max(0, Math.trunc(Math.fround(Math.fround(n * 0.015625) * Math.fround(0.3030303))));
const playerP = (n: number) => Math.trunc(Math.fround(n / Math.fround(211.2)));
```

- 위 `stamp()`는 개념 골격입니다. 원본과 같은 결과를 내려면 §3.5의 패스 구조를 CPU로 옮겨 **텍셀마다 색(RG 또는 RGB, 8비트로 추정)과 소유 스텐실(팀비트)을 따로** 둡니다 (2026-10-02 [paintgpu] 갱신):
  1. 이 프레임 요청을 큐 순서대로 모읍니다(큐0 = N+0x44 0/1, 큐1 = 2, 큐3 = InkRut, 큐2 = 지우기).
  2. 큐0의 플레이어 요청마다: 프레임 앞 색 D로 `overpaint(..., alphaTest=true)` 통과 && `(stencil & 팀비트) != 팀비트`이면 `stencil = 팀비트`, 그 플레이어 카운터 +1.
  3. 큐1 요청마다: 같은 알파 테스트 통과면 `stencil = 팀비트`(카운트 없음).
  4. 큐0 → 큐1 순서로 `overpaint(..., alphaTest=false)`를 현재 색에 순차 적용(그리기마다 배리어), RG(B)만 기록.
  5. 큐3 모드 8, 큐2 모드 11(스텐실 0) → 10(색).
  6. 팀 면적 = 스텐실 == 팀비트 개수, 전체 = 칠 가능 텍셀 수.
  `g.team[t]`(웹 소유 배열)은 원본의 스텐실과 같은 것입니다. 재구현·합성 테스트: `web/tools/paintgpu_frame_sim.py`(위 1~6을 한 텍셀로 실행), 셰이더 식 `web/tools/shader_paint_overpaint.py`.
- `player.paintTexels`에 더할 값 = 2단계에서 센 수(새로 내 팀이 된 텍셀, 자기 땅 덧칠 0) **[판독]** — 이전 판의 "원본 미확정, 설정값" 메모를 대체합니다. 요청이 AnimationFrame번 다시 그려지면 매번 2단계를 다시 합니다.
- 아틀라스 밀도는 원본 PaintTextureData 와 같은 "월드 1 단위당 8 텍셀"(§3.1, 오브젝트 대상 [판독])로 두면 p 환산식(÷64÷3.3)을 그대로 쓸 수 있습니다. 지형은 **실제 면적이 아니라 대표 방향 평면 투영 면적**으로 텍셀을 배정해야 원본 텍셀 수와 같아집니다(정정 [paint4], [colpaint_atlas.md](colpaint_atlas.md) §8).
- 웹에서 GPU를 쓰지 않으므로 원본의 1~2프레임 카운터 지연(이중 버퍼 읽기)은 따로 흉내 내야 같은 시점이 됩니다. 지연 프레임 수는 **[미확정]**(GPU 완료 시점 의존).
- **2026-10-03 [r5 paint] 추가 — 원본과 같게 하려면**:
  1. **텍셀 깊이 키**: 텍셀마다 `depthKey`(초기 0 = 가장 멂)를 둡니다. 레코드 키 = D+0x0c(오프라인 `frame×11/16`, 온라인 `(frame×11 + 플레이어)/16`, frame = GameFrame clamp). 모드 0~11은 `key >= depthKey`(카메라에 가깝거나 같음 = LEQUAL 통과)일 때만 그 텍셀을 처리합니다. 모드 0/1/2/3/7/11은 통과 텍셀(알파 테스트 포함)에 `depthKey = key`를 씁니다. 모드 13(초기화)은 `depthKey = 0`, 모드 12·14~17은 깊이 비교가 없습니다. 오프라인 1인 연습에서는 요청 번호가 늘기만 하므로 차이는 "이전 요청의 재그리기가 새 요청이 차지한 텍셀을 다시 칠하지 못함"으로만 나타납니다.
  2. **스탬프 방향**: 텍스처 첫 행(PNG 위) = 진행 방향 앞쪽, PNG 오른쪽 = 진행 × 면 법선. 지금 [impl/paint.md](../impl/paint.md) §1.3의 배치(오른쪽 = fwd × np, 꼬리가 앞쪽)는 이 결과와 방향이 같습니다.
  3. **경사 보정**: 요청 법선이 대상 대표 평면 법선과 다르면 등고선 방향(대표 평면 안에서 `n̂ × Z`)으로 `c = |n̂·Z|`배 압축합니다(§3.5.5). 웹 차트가 실제 면 평면이면 원본의 "대표 평면 투영 + 압축"과 결과가 다를 수 있습니다.
  4. **시드 위치**: Floor는 월드 위치 그대로입니다. Col은 패널 좌표에서 되돌린 위치를 씁니다(§3.5.3, colpaint_atlas.md §7). 강체·메시 변환이 단위일 때 월드 위치로 계산한 시드와 같을 확률은 실행 3000건 중 2995건(99.8%)입니다.

### 6.4 에셋 변환

1. `InkTexture.bfres.zs` → `web/tools/graphics_bntx.py png <out> <bfres>` → 스탬프 마스크 PNG(이미 `analysis/paint/inktex/`).
2. `InkTexInfo` → JSON(이미 `analysis/paint/InkTexInfo.json`).
3. 스테이지 충돌(Phive `.bphsh`, [gimmick] 해독 진행 중) → 삼각형 + 재질 → 아틀라스.
4. 무기 표 → `web/tools/paint_shape.py table` 결과 JSON을 그대로 웹 데이터로 사용 가능.

## 7. 다른 기능과의 연결

- **탄 이동**: travelDist(+0x1200), moveState(+0x198), maxYInState(+0x1204), 속도(슬롯49)를 읽습니다. 쓰기는 bullet 쪽.
- **네트워크**: 도색은 이벤트(`FloorPaintEvent` 등)로 복제됩니다. 실행 기기가 N 레코드를 보내고 받는 기기는 같은 큐(0x7102c3f4c8 → 0x7102c14dec)에 넣습니다. 복제 탄은 칠 요청을 하지 않습니다(§3, 슈터 [판독]). (정정: 이전 판 "원격 재생 요청은 flags[0]로 구분 [추정]"은 틀렸고 flags[0]은 게이지 제외 표시입니다.) 웹에서는 "요청"을 보내고 양쪽이 같은 파이프라인을 돌리는 방식이 원본 구조와 맞습니다. 다만 원본의 소유 판정은 기기마다 GPU에서 따로 나오므로 요청 도착 순서가 다르면 기기 간 결과가 다를 수 있습니다 **[추정]**.
- **플레이어 발밑 샘플**: PlayerStepPaint 갱신 `0x710268b3b8`은 `*(*(*(*(S+0xe8)+8)+0x20)+0xe8)` 객체(+8 ≠ 0일 때)의 +0x48 함수 객체를 불러 **팀0/1/2 텍셀 수와 전체 수(u32 4개)**를 받고, 비율 = 팀 수/전체, 덮임 = min(전체/15, 1)을 곱해 아군(S+0x3c)·적(S+0x48, 3팀이면 두 적 합) 값으로 씁니다. 전체가 0이면 직전 값(S+0xa0/+0xa4)을 한 번 재사용(S+0xa8) **[판독]**. 이 4개 값의 형식(팀 0/1/2/전체, 유효 바이트)은 GPU 카운터 객체 vt+0x70 `0x7102c25ed0` 출력과 같고, 매 프레임 비우는 모니터 목록(칠시스템+0x5a5b8, 모드 14~17)이 PlayerPaintMonitor 패스로 보이므로 **발밑 샘플 = 발밑 모니터 영역의 소유 스텐실 카운트**로 봅니다 **[추정 — 객체 연결 사슬 미확인]**. 즉 발밑 판정도 같은 0.3·최댓값 소유 규칙을 따릅니다(추정). 웹은 `grid.team`(소유 스텐실)을 모니터 원 영역에서 세면 됩니다. 원 반경(`GroundPaintMonitorRadius`)과 모니터 목록에 넣는 함수는 **[미확정]**.
  - 2026-10-03 [r5 paint] 추적 결과(여전히 **[미확정]**): `GroundPaintMonitorRadius`(1.0)·`GroundPaintMonitorHeight`(1.0)·`GroundPaintRateForVisible`(0.4)는 vtable 0x71055fc228 파라미터(필드 `VanishFrameNum`·`AirKd_Throwed`와 같은 구조체, 방문 0x7101f805e4)라 던지는 물체 쪽으로 보이고 플레이어 발밑 반경이 아닙니다 **[데이터]**. 이름 `PlayerPaintMonitor`를 단 0x248 B 객체(vtable 0x7105680730)를 만드는 함수 `0x7102c3d954`가 있습니다. 렌더 작업 등록 `0x7102c3e2f0`은 Paint 패스(콜백 → 0x7102c50f20)와 모니터 패스(0x7102c3e570)를 `0x71010f6bf8(0, …)`/`(2, …)`로 등록합니다. 다음: vtable 0x7105680730 슬롯(모니터 목록 +0x5a5b8 에 넣는 함수 후보), PlayerStepPaint 의 S+0xe8 writer.
  - **해소 (2026-10-03 [r6 paint]) — 발밑 샘플 사슬 [판독]+[실행 4000/4000]**. 위 "[추정 — 객체 연결 사슬 미확인]"과 "원 반경(GroundPaintMonitorRadius)"은 정정합니다: 사슬은 아래와 같이 끝까지 연결되고, 발밑 영역은 반경 파라미터가 아니라 **고정 크기 `Disk` 스탬프**입니다. `0x7102c3d954`(PlayerPaintMonitor 프로세스)는 이 사슬과 무관합니다(§3.1).

    | 단계 | 기준 객체·필드 | writer / 코드 | 확정 |
    |---|---|---|---|
    | 1 | PlayerStepPaint S(0xf0 B, vtable 0x710563eb68) **S+0xe8 = 액터 컴포넌트[10]+0x18 → +0x10** = 캐릭터 컨트롤러 래퍼 W | 바인드 슬롯25 `0x71024319f0`의 `0x7102431e00`(액터 +0x208 컴포넌트 표, 개수 +0x200 > 10). 같은 함수가 S+0xe0 = 컴포넌트[24]+0x20(플레이어 행동, 형 검사 0x71058bc2e0) | [판독] |
    | 2 | W+8 = ctrl, ctrl+0x20 = 컨트롤러 상태 S'(0x2a8 B, [../physics/phive_controller.md](../physics/phive_controller.md) §3.1), **S'+0xe8 = 접지 정보 O** | 같은 사슬을 접촉 필터 `0x71012d485c`도 씀(S'+0x20 == 1 일 때 O+8 과 상대 강체 +0x228 비교), CharacterControllerHelper 초기화 `0x710122f4d8`이 W 를 helper+0x130 에 둠 | [판독] |
    | 3 | **O+8 = 지지 강체 +0x228(u32)**, **O+0x48 = 델리게이트(vtable 0x7105681b90), O+0x50 = SplResultPlayer** | SplResultPlayer 슬롯7 `0x7102c5a3c8`: 접촉이 있으면 `0x7102c5d5dc` O+8 = 0 → 고른 접촉의 강체+0x228 (`0x7102c5d730`), `0x7102c5da58`(또는 0x7102c5db3c/0x7102c5db50) O+0x48/+0x50 | [판독] |
    | 4 | 델리게이트 slot0 `0x7102c5ec74`(x8 = 출력) | SplResultPlayer 의 모니터 칸 4개를 가중 합산(아래) | [판독]+[실행] |
    | 5 | 모니터 = 칠 모니터 객체(0x178 B, vtable 0x710567e9c8, 기반 생성자 `0x7102c25fc0`) 4개, 배열 = SplResultPlayer+0x1368 | 생성 `0x7102c598bc` → 배열 생성 `0x7102c70e80(arr, heap, 4)`, 배열+0x14 = 1/6(`0x3e2aaaab`), 배열+0x10 = 16, 배열+0x18 = 2 | [판독] |
    | 6 | 모니터 결과(+0x3c/+0x44/+0x4c/+0x54 값, +0x40/+0x48/+0x50/+0x58 유효) | GPU 카운터 읽기 `0x7102c25654`(§3.5.6) ← `PaintMonitor` 패스 `0x7102c3e570`의 모드 14/15/16/17 | [판독] |

    **모니터 배치 (SplResultPlayer 슬롯7 끝, `0x7102c5d5bc`~)** [판독]:
    ```
    if 접촉 수(R+0x1698) == 0: O 를 건드리지 않음
    O+8 = 0
    best = 접촉[0..n-1] (R+0x1418, 0x28 B, 16개 넘으면 [0]) 중 점수 최소:
        s += |c.pos − R+0x169c|² (+ R+0x16b4 이면 (R+0x16b8)² · dot(접촉 법선, R+0x16a8))
        // s 는 반복마다 누적되고 초기화되지 않음(0x7102c5d69c, 원본 그대로) → 보통 앞쪽 접촉이 유리
    O+8 = best.강체+0x228
    p = best 접촉점, n = 접촉 법선(0x7103c4988c), 진행 방향 = n × normalize(A × n), A = (|n.y| ≤ 0.999 ? Y : X)   // Disk 라 회전은 결과에 영향 없음
    q = 0x7102c3fef0(강체, 셰이프키, {p, n, dir, size (1.0, 1.0), −1.0})   // §3.5.1 대상 공간 변환 그대로
    id = 0x7102c71650(모니터 배열, 강체, 셰이프키, p, q, 높이 범위 없음)
         // 대상 (종류, id[, 패널]) 이 같은 모니터를 다시 쓰고, 없으면 가중치 ≤ 0 인 빈 칸에 새로 배치
         // 모니터 vt+0x80 = q(위치·법선·방향·크기 0x30 B → 모니터+0x128), vt+0xb0 = 16(InkTexType, 모니터+0x68)
    새 id 를 R+0x13c0/+0x13c8/+0x13d0/+0x13d8(유효 바이트 +4) 4칸 중 하나에 기록
    O+0x48 = 델리게이트(0x7105681b90), O+0x50 = R
    ```
    모니터의 칠 요청 형식은 기반 생성자 값 그대로입니다: 팀 −1, **InkTexType 16 = `Disk`**, cAlpha 0xff, **크기 (W, L) = (1.0, 1.0)**(스탬프 쿼드 꼭짓점 ±1 이므로 대상 평면에서 2×2 단위 사각형 안의 Disk 마스크 > 0 텍셀), 높이 범위 직접 지정 없음(→ InkTexInfo `Disk` 행 규칙). 제출 `0x7102c26128`(모니터 vt+0xc0) → N 레코드 `0x7102c3ea50` → `0x7102c15094(칠시스템, 항목, 모니터+0x38 == 0)`; 이 모니터는 +0x38 = 5 이므로 대기 목록 +0x5a5a0 → 실행 목록 +0x5a5b8 = **`PaintMonitor` 패스**에서 셉니다 **[판독]**. 제출을 매 프레임 누가 부르는지는 **[판독-부분]**(등록 목록 `*0x71058eed50`+0x310).

    **가중치 갱신** `0x7102c71330(dt = 0.016666668, 배열)` — SplResultPlayer 슬롯7 처음에 매 프레임 [판독]+[실행]:
    ```
    for 항목 e (0x50 B):
      if e.이번에배치(+0x38): e.프레임수(+0x3c)++ ; if e.프레임수 >= 배열+0x18(=2): e.가중치(+0x40) = 1.0, e.이번에배치 = 0
      else:
        if 배열+0x14 == 0: e.가중치 = 0
        else: e.가중치 = max(e.가중치 − dt / 배열+0x14, 0)        // 1/6 초 = 10 프레임에 걸쳐 1 → 0
        if e.가중치 <= 0 (위 0 대입 포함): e.이번에배치 = 0; e.등록(+0x4c)이면 해제 알림(0x7100f3e094) 후 e.등록 = 0
    ```
    즉 같은 대상 위에 계속 서 있으면 배치 2 프레임 뒤부터 가중치 1.0(GPU 결과가 1~2 프레임 늦는 것과 맞물림), 대상을 벗어나면 10 프레임 동안 서서히 줄어듭니다.

    **델리게이트 `0x7102c5ec74` (출력 u32 4개 + f32)** [판독]+[실행]:
    ```
    out[0..3] = 0, out.w = 0
    for k in 0..3:                                   // R+0x13c0+8k 의 id, +0x13c4+8k 유효
      if !유효[k]: continue
      e = 배열에서 (e.유효(+0x48) && e.id(+0x44) == id[k]) 인 항목; 없으면 R 캐시[k] = 0, 유효[k] = 0, continue
      0x7102c71bc4(e, R 캐시[k] = R+0x1370+0x14k):
          모니터 vt+0x60(0x7102c260c8: 유효 바이트 +0x40·+0x48·+0x58 모두 참 — +0x50 은 보지 않음, 원본 그대로)이면
              R 캐시[k] 의 직전 값 위에, 유효 바이트가 참인 칸만 vt+0x78(i) 값으로 덮고 e+8..+0x14 에 복사
          아니면 e+8..+0x14(직전 값)를 R 캐시[k] 에 복사
          R 캐시[k].w = e.가중치
      w = e.가중치; if !(w > 0): 유효[k] = 0, continue
      out.w = (처음이면 max(w, 0) 아니면 max(out.w, w))
      out[i] = fcvtzu(f32(w · f32(캐시[i])) + f32(out[i]))        // 곱·합 따로(FMA 없음)
    ```
    PlayerStepPaint 는 out[3](전체) ≠ 0 이면 팀 i 비율 = out[i]/out[3], 덮임 = min(out[3]/15, 1) 을 씁니다(위 판독 그대로). out.w 는 읽지 않습니다.

    - 원본 실행 `web/tools/r6_paint_footmon_emu.py`: 델리게이트(0x7102c5ec74 + 0x7102c71bc4 + 모니터 vt 0x7102c260c8/0x7102c26258 원본)와 가중치 갱신 0x7102c71330 을 무작위 상태 각 4000건 실행해 위 재구현과 **4000/4000, 4000/4000 일치**(유효 바이트·캐시·가중치·해제 알림 횟수 포함). 스텁: PLT 없음, 해제 알림 0x7100f3e094 만 즉시 반환(호출 수만 셈), 그 인자용 전역 `*0x71058150c0`은 빈 객체. GPU 카운트 자체·배치 함수 0x7102c71650·접촉 선택은 실행하지 않았습니다(판독). 결과 `analysis/paint/r6_footmon_emu_out.json`.
    - 결론: **발밑 샘플은 접지 접촉점 아래 대상(지형 패널/바닥/오브젝트)에 그린 1×1 `Disk` 스탬프 안의 소유 스텐실 카운트(모드 14~17)를 최대 4개 모니터에 걸쳐 가중 합한 값**입니다. 같은 0.3·최댓값 소유 규칙을 따른다는 이전 추정은 스텐실 경유가 확인되어 [판독]으로 올립니다.
- **UI**: playerP·teamP, 우세 단계(§4.3).
- **스테이지 기믹**: ChangePaintableArea, PaintTargetArea(에어리어), 리프트 PaintBancParam.

## 8. 검증

| 구분 | 내용 | 결과 |
|---|---|---|
| 재구현 계산 | `paint_shape.py check` (경계·성질·연속성) | 통과 |
| 실제 데이터 | `paint_shape.py table` 58개 표 풀이 → `shooter_paint_table.json` | 생성됨. 블래스터 8종 WidthHalf=0 확인 |
| 재구현 계산 | `paint_score.py` → `score_check.json` | 아래 표 |
| 데이터 교차 확인 | 슈터 패턴 경계(1.3/1.6/2.2/2.85)와 Shot01~04 텍스처 세로/가로 비(1.31/1.69/2.19/2.84) | 일치 |
| 원본 실행(에뮬) | PaintPermille 함수, 게이지 가산·비율·넷 % 명령 구간 (`web/tools/gauge_emu.py`) | 전부 재구현과 일치 — [special_gauge.md](special_gauge.md) §10 |
| 원본 실행(에뮬) | N → D 변환 `0x7102c11f80` 함수 전체, 무작위 600건(Floor 대상, 온라인/오프라인, 높이 유형 4종, 지우기, 시드 직접 지정 포함) — `web/tools/paintgpu_record_emu.py` | **600/600 일치**(시드·변형 텍스처·높이 범위·cAlpha·+0x6c 등). 결과 `analysis/paintgpu/record_emu_out.txt` |
| 원본 실행(에뮬) | 렌더 상태 18개 생성·설정 `0x7102c16e2c` + `0x7102c16ed0`(셰이더 표 등록 직전까지), 규칙 1/5 — `web/tools/paintgpu_renderstate_emu.py` | §3.5.4 표. 결과 `analysis/paintgpu/renderstate_emu_out.txt` |
| 원본 실행(에뮬) 2026-10-03 | 스탬프 배치: 카메라 LookAt 0x710358857c, 직교 투영 0x7103589f84+0x7103589b48, 회전 0x7102c1233c(Floor·Col 400건), 경사 0x7102c124bc(200건), 행렬 0x7102c17ae0(V·P 단위/실제 각 200건) — `web/tools/r5_paint_stamp_emu.py` | V·P 재구현 비트 일치, 행렬 **6400/6400 원소 비트 일치**(fmla 순서 반영), θ·φ 는 sincos 가 (y,x)/‖·‖ 와 1e-4 안 400/400·200/200, c 비트 일치, 방향 의미 200/200, 깊이 순서 200/200. 결과 `analysis/paint/r5_stamp_emu_out.txt` |
| 원본 실행(에뮬) 2026-10-03 | 지형 대상 변환 0x7102c3fef0(kind 2) → 되돌림 0x7102c4a6bc, 강체 단위/임의 반반 6000건 — `web/tools/r5_paint_colxform_emu.py` | 9성분 6000/6000, 3성분 6000/6000 비트 일치. 단위 변환에서 되돌린 위치가 원래 월드와 비트로 같은 경우 791/3000, 시드 같은 경우 2995/3000. 결과 `analysis/paint/r5_colxform_emu_out.txt` |
| 원본 실행(에뮬) 2026-10-03 [r6] | agl 이미지 크기 0x71035b519c(mode 0) × agl 포맷 0x5d개 × 크기 5 — `web/tools/r6_paint_texfmt_emu.py` | 465/465 = 포맷표 +8 × w × h. 도색 텍스처 4종 비트 폭 §3.1. 스텁 없음. `analysis/paint/r6_texfmt_emu_out.json` |
| 원본 실행(에뮬) 2026-10-03 [r6] | 렌더 패스 이름 배열 0x71010f7ba8 — `web/tools/r6_paint_uc.py`(공용 하네스) | [0] Paint, [1] PlayerPaintMonitor, [2] PaintMonitor, [3] PreMain. 스텁: PLT guard·mutex |
| 원본 실행(에뮬) 2026-10-03 [r6] | 발밑 샘플 델리게이트 0x7102c5ec74(+0x7102c71bc4, 모니터 vt 원본)·가중치 갱신 0x7102c71330, 무작위 상태 각 4000건 — `web/tools/r6_paint_footmon_emu.py` | 4000/4000, 4000/4000 비트 일치. 스텁: 해제 알림 0x7100f3e094 만. `analysis/paint/r6_footmon_emu_out.json` |
| 원본 실행(에뮬) 2026-10-03 [r6] | agl 이미지 크기 0x71035b519c(mode 0) × 포맷 0x5d × 크기 5 — `web/tools/r6_paint_texfmt_emu.py` | 465/465 = 포맷표 +8 × w × h. 스텁 없음 |
| 원본 실행(에뮬) 2026-10-03 [r6] | 렌더 패스 이름 배열 0x71010f7ba8 — `web/tools/r6_paint_uc.py` | [0] Paint, [1] PlayerPaintMonitor, [2] PaintMonitor. 스텁: PLT guard·mutex |
| 원본 실행(에뮬) 2026-10-03 [r6] | 발밑 델리게이트 0x7102c5ec74·가중치 갱신 0x7102c71330 각 4000건 — `web/tools/r6_paint_footmon_emu.py` | 4000/4000, 4000/4000. 스텁: 해제 알림 0x7100f3e094 만 |
| 재구현·합성 | 한 프레임 패스(소유 스텐실·카운트·색) 한 텍셀 9개 경우 — `web/tools/paintgpu_frame_sim.py` | 자기 땅 덧칠 카운트 0, ink 0.4로 상대 땅 못 뺏음, 0.29는 색만 남고 소유 없음, 같은 프레임 두 팀 겹침은 둘 다 카운트·스텐실은 뒤 팀 등. `analysis/paintgpu/frame_sim_out.txt` |

`paint_score.py` 기대값 (재구현):

| 입력 | 출력 |
|---|---|
| teamP(211) / teamP(212) / teamP(42240) | 0 / 1 / 200 |
| playerP(2112) | 10 |
| 우세 a/b/d = 50/50/100, 60/49/100, 60/50/100, 66/50/100, 50/66/100 | 2, 1, 2(경계 1000), 0, 4 |
| 우세 1501/0/10000, 1500/0/10000 | 0, 1 |
| 스페셜 배율 GP 0/10/20/30/57/60 | 1.0 / 1.0909 / 1.1656 / 1.2241 / 1.3 / 1.3 |

위 `paint_score.py` 항목은 함수 단위 재구현이며, 여러 함수 연결(요청 → 텍스처 → 카운트)은 실행하지 않았습니다. 게이지·PaintPermille의 원본 명령 실행 비교는 [special_gauge.md](special_gauge.md) §10에 있습니다.

`r5_paint_*` 원본 실행의 스텁·한계 (2026-10-03): `r5_paint_stamp_emu.py`는 PLT(sqrtf 등)를 파이썬 계산으로 바꾸고(이 경로는 NaN일 때만 부름), 기저 전역은 원본 정적 초기화 0x7102c2e270·0x7102bd77e0을 실행해 채웁니다. 투영 객체 필드(near/far/상하좌우, ZScale 1·ZOffset 0, posture 0)는 Floor vt+0x60 판독값을 직접 넣었고 0x7102c1b5a4 자체는 실행하지 않았습니다. θ·φ의 atan2 색인 함수 0x7101252998은 원본을 실행했지만 재구현은 비트가 아닌 허용 오차로만 비교했습니다. GPU 래스터·셰이더는 실행하지 않았습니다. `r5_paint_colxform_emu.py`는 0x7102c71e50(대상 정보)를 kind 2·id를 쓰는 스텁으로 바꾸고, 강체 +0x28 = 0(복합 형상 없음), 메시 트리(+0x3a8)·패널 트리(+0x3d8)를 비워 단위 행렬 경로만 실행했습니다. 실제 셀 → 패널 조회(0x7102c0e04c)와 비단위 메시 행렬은 검증하지 않았습니다.

`paintgpu_*` 원본 실행의 스텁·한계: `paintgpu_record_emu.py`는 `nn::os::GetSystemTick`을 0 반환으로 바꾸고, InkTexInfo 런타임 표(`*0x71058eeae8`)를 JSON에서 만든 가짜 표로, GameNet(`*0x71057908b8`)을 가짜 객체로 둡니다. 대상은 Floor(위치 그대로)만 실행해 Col/Obj 좌표 변환(0x7102c4a6bc)은 검증하지 않았습니다. `paintgpu_renderstate_emu.py`는 렌더러+0x8a8 객체 vt+0x20 호출을 ret으로 바꾸고 규칙 값을 직접 넣으며, 셰이더 변형 표 등록(0x71035aeb64 이후)은 실행하지 않습니다. GPU 셰이더·스텐실·카운터 자체는 실행하지 않았고(`paintgpu_frame_sim.py`는 판독한 상태로 만든 재구현), 텍스처 8비트 양자화는 추정입니다.

## 9. 미확정 사항과 필요한 근거

| 항목 | 다음 단계 |
|---|---|
| ~~마스크 임계~~ / ~~요청 → 렌더 패스 큐 연결~~ / ~~모드 0..17 ↔ 도색 종류~~ / ~~회전 인덱스~~ / ~~텍셀 A 채널~~ / ~~집계 임계~~ | 해소(2026-10-02 [paintgpu]): §3.5 전체, §3.1 A 채널, §4.1. 남은 것: 텍스처 비트 폭(8비트 UNORM)은 NVN 열거값 이름 추정, 카운터 종류 1 = SAMPLES_PASSED 추정, 모드 3·7·13의 용도, 회전 행렬 곱 순서 식 정리, 애니 프레임마다 바뀌는 값 |
| ~~PaintTextureData size 출처·단위~~ | 해소(§3.1): 대상+0x390, 오브젝트는 AABB 변 길이 올림(월드 단위), 8 텍셀/단위. 남은 것: ColPaint(kind 2) 대상의 size·아틀라스 밀도 |
| ~~패턴 변형 번호(Shot00_0~_11) 선택~~ | 해소(§3.5.3): sead::Random(시드).getU32() % PatternNum, 원본 실행 600/600. 남은 것: 텍스처 배열 순서 = 이름 번호 순서인지(로더) |
| 0x7102c44e18 다른 호출자(폭발·롤러 등)의 C+0/C+1/C+8 | 15개 호출자 디컴파일 — 게이지 제외·지우기·InkTexType 값 |
| ~~레코드 풀 크기(칠시스템 +0x2d8)~~ | 해소(2026-10-03 [r5 paint], §3.5.4): 2560개, 초기화 0x7102c130a0. (정정: 이전 판이 가리킨 0x7102c48110 에는 +0x2d8 쓰기가 없음) |
| ~~벽 낙하 방울 반경 출처~~ | 해소(§3.0) |
| ~~플레이어 paintCount 가산 경로~~ | 해소(§4.4). 남은 것: 칠 카운터 엔트리의 GPU 값 의미(`0x7101043cdc`) |
| ~~PaintPermille 계산식~~ | 해소(§4.2, `0x710303bd80`) |
| ~~스페셜 게이지 가산식~~ | 해소([special_gauge.md](special_gauge.md)). ~~요청 레코드 +0x6c 세팅~~·~~스페셜 시작(G+0x1c/+0x20)~~ 해소([paintgpu]). 남은 것: G+0xc/G+0x24 writer |
| ~~ColPaint UV 생성 알고리즘~~ | 대부분 해소([colpaint_atlas.md](colpaint_atlas.md), [paint4]). 남은 것: 연결·띠·패턴 인식, 200 단위 씬, 물 평면 포함 여부 — 같은 문서 §10 |
| 나와바리 승패·동률 | 해소 [판독] — [turf_result.md](turf_result.md): PaintPermille 보정 뒤 `A.p < B.p ? Bravo : Alpha`, 무승부 없음 |
| 우세 판정 호출 주기, 화면 효과 | VersusRefereePaint 다른 슬롯, [ui] |
| ~~모드 3·7·13 용도 / 회전 행렬 곱 순서 / 애니 프레임마다 바뀌는 값 / D+0x0c 소비처~~ | 해소(2026-10-03 [r5 paint]): §3.5.4(모드 7 = 깊이 키 기록, 13 = 초기화, 3 = 높이 텍스처 대상 초기화), §3.5.5(행렬 [실행] 6400/6400), §3.5.7(바뀌는 입력 없음), §3.5.3(깊이 키). 남은 것: 모드 3 COPY 셰이더가 스텐실 3을 남기는 텍셀 조건 — Hoian_Proc `PaintCopy` 역번역 |
| ~~텍스처 비트 폭~~·카운터 종류 1 = SAMPLES_PASSED 이름 | 비트 폭 해소(2026-10-03 [r6], §3.1 [데이터]+[실행]). 남은 것: 카운터 종류 1 의미 [미확정] — sdk.img 의 nvnCommandBufferReportCounter 구현 |
| 0x7102c50d18의 프레임 내 위치 | [미확정]. 엔진 모듈 슬롯 12 단계까지 확인(§3.5.7). 다음: ModuleSystem 0x7103daae40 / 0x7103dac8b4 |
| ~~관리자+0x30a/+0x30c writer~~ | 해소(§3.5.1): 수면 OceanMesh.OceanHeight(0x71011311a4/0x7101131424). 남은 것: 0x7101131424 동적 오프셋 출처 |
| ~~발밑 샘플 사슬·반경~~ | 해소(§7) [판독]+[실행]. 남은 것: 모니터 제출(vt+0xc0) 호출 위치, 배치 0x7102c71650 실행 검증 |
| 강체 +0x230 보유 충돌·물/KeepOut 포함 여부 | [미확정]. 물은 야가라에서 수면 높이 하한으로 칠 거부(§3.5.1). +0x230 writer 미발견 — 다음: ColPaint TargetCollisionList(0x7102bc7e88) |
| ColPaintMaskDrawer 높이 텍스처 내용 | [미확정] 0x7102bd919c (스텐실 3 조건은 §3.5.4 해소) |
