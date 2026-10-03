# 팀 컬러의 RSDB 파일 공급과 Gyml 사본 — r8

## 1. 기능 개요와 사용자에게 보이는 동작

Lby_Lobby00에서 쓰는 일반 팀색 조회의 데이터 공급을 확정한다. r7 고정 질문 `graphics/team_color.md:L15`와 `L253`의 전체 질문인 RSDB 대 romfs Gyml 선택만 다룬다. 신규 판독으로 **RSDB 파일→TeamColorDataSetTable→이름 조회**를 연결했고, 원본 typed loader와 이름 조회를 36행 모두 실행했다. 다른 색 파생 계산·swap·26000 특수 모델 조건은 기존 근거 또는 별도 질문이다.

## 2. 분석 대상 원본·버전·자료 위치

2026-10-03 SHARED.md/FUNCS.tsv의 TeamColor 항목과 `decomp_index.py --no-build <주소>`를 먼저 확인했다. `1424e88` metadata, `140946c` 조회, `1179a24/1179fd0` 로비 선택, `1176830` 색 계산은 기존 근거를 재사용한다. 신규 근거는 `3df331c/38ca19c/3df432c/3df4504`, `14071a0/14092a8/14076b8/1407364/1407e58/14081c8/14097cc` 원본 명령 및 실제 파일 비교다.

- `extracted/romfs/RSDB/TeamColorDataSet.Product.100.rstbl.byml.zs`: 36행, SHA256 `3fe44f9a65af13f561195cf7c7868f8eb19290fc1062503952721568051b36e1`.
- 같은 추출본의 `Gyml/*.game__gfx__parameter__TeamColorDataSet.bgyml`: **15개**. 해당 파일이 가진 196개 원소를 대응 RSDB 행과 대조하면 모두 같다. 부동소수점은 f32 비트로 비교했다. 파일별 해시는 `analysis/completion/r8/graphics_teamcolor_rsdb_emu.json`.
- 디컴파일: `analysis/decomp/r8_combat/teamcolor_source.c`, `teamcolor_loader.c`, `teamcolor_registry.c`, `teamcolor_preload.c`, `teamcolor_source_binding.c`, `teamcolor_module_init.c`. 원본 NSO/데이터는 수정하지 않았다.

## 3. 진입점과 전체 호출 흐름 [판독]

```text
3df2d5c RSDB preloader
  → typed metadata manager(1424e88 기존): index5
       class=game__TeamColorDataSetTable
       basename=TeamColorDataSet
       namespace=Work/Gyml
       rowtype=game__gfx__parameter__TeamColorDataSet
3df331c(module, setup)
  → 38ca19c(manager, {heap, setup, module+20, 0})
  → manager에 metadata 없으면 manager VT+20(1424e88) 호출
  → metadata 각 행의 class(+0)와 basename(+8)를 공급자 VT+10에 전달
  → module+20 VT5766858 +10=3df49d0
  → thunk는 this−20 → 3df432c
  → class 문자열 해시로 등록 factory 조회 → typed table ctor
  → 3df4504(module, typedTable, basenameSafeString, heap, ...)
  → 버전 공급자가 반환한 목록 각각에 RSDB/%s.%s.rstbl.byml 구성
  → resource 경로 해석·로드·타입검사 성공 뒤 resource+8의 BYML bytes
  → 파일 한 개면 typedTable VT+38(bytes), 둘 이상이면 VT+40(bytesList)
```

`3df4504`의 경로 형식은 RSDB이다. 타입 로더에 넘길 자료를 직접 `Gyml/<이름>.bgyml`로 바꾸거나 키별 두 파일을 경쟁시키는 분기는 이 확인된 일반 경로에 없다. preloader도 같은 RSDB 경로를 구성한다. `2afa780/2afab90`의 archive 경로 형식은 `RSDB/%s.%s.rstbl.byml.zs`로 판독했다. 여러 RSDB 버전/개발 공급자 설정의 모든 변형을 실행한 것으로 확대하지 않는다.

## 4. 구조체·필드·상수·열거형 [판독]+[실행]

`14071a0`는 클래스 hash `0x2f368919e2207bcb`와 생성자 `14092a8`를 등록한다. 실행한 원본 `38a0d98(className)`의 결과도 해당 hash와 같다. 실제 ctor는 0x78 B 테이블을 생성하고 VT `55820a8`를 기록한다.

| 테이블 슬롯/멤버 | 원본 |
|---|---|
| VT+38 / VT+40 | `14076b8` 한 BYML / `14081c8` BYML 목록 파서 |
| +20 / +28 | 행 수 / 0x90 B 행 배열 |
| +38/+40 | 이름 조회용 정렬 포인터 배열 |
| +58/+60 | Tag 조회용 정렬 포인터 배열 |
| VT+60 / VT+80 | `1409850` 행 수 / `14098f8` 행 주소 |

| 0x90 B 행 오프셋 | 필드 |
|---|---|
| 0 | `__RowId` 문자열 |
| 8 / C / 1C | AlphaHueOffset / AlphaTeamColor RGBA / AlphaUIColor RGBA |
| 2C / 30 / 40 | BravoHueOffset / BravoTeamColor / BravoUIColor |
| 50 / 54 / 64 | CharlieHueOffset / CharlieTeamColor / CharlieUIColor |
| 74 / 84 / 88 | NeutralColor RGBA / NeutralHueOffset / Tag |
| 8C / 8D | HueOffsetEnable / IsSetUIColor |

`14097d0`은 함수 시작이 아니다. 실제 `14097cc`는 `game__TeamColorDataSetTable` 문자열을 반환하는 leaf이며 파일 로더가 아니다. 이 정정으로 기존 다음 주소를 대체한다.

## 5. 상태 전이와 전체 수명 [판독]

제품 RSDB 모듈 preloader→파일 준비 대기→metadata 초기화→typed table 생성→행/인덱스 로드→로비 이름/Tag 조회 순서다. 3df331c는 preloaded resource의 이벤트를 기다리고 38ca19c에 실제 공급자를 넘긴다. 14076b8/14081c8은 기존 행 배열을 해제하고 행 수를0으로 만든 뒤 새 자료를 파싱해 인덱스를 재작성한다. 3df49d8은 typedTable VT+58로 기존 자료를 정리한 뒤 동일3df4504를 호출하는 reload 경로다. 파일 타입 검사가 실패하면 loader는0을 반환한다. 모든 reload 시나리오를 실행한 것으로 확대하지 않는다.

## 6. 계산식·조건·상세 의사코드 [판독]+[실행]

파일 bytes→`14076b8`→BYML validation/array visitor→`1407364` 명명 키 파싱→행 배열→`1407e58` 정렬 인덱스 작성→`140946c` 이름 조건 조회→행 포인터다. 실제 36행의 각 `Work/Gyml/...gyml` 키를 조회해 배열의 대응 행 주소가 반환되는 것을 실행했다. 이 `Work/Gyml`은 **RSDB 안의 행 키 namespace**다. 조회 함수가 그 경로의 개별 Gyml 파일을 여는 뜻이 아니다.

로비 `1179fd0`의 global RSDB manager→index5 typedTable→`140946c`→`1176830` 연결은 기존 로비 selector 판독/실행 근거와 결합한다. 기존 selector/색 계산을 신규 확정 행으로 재계상하지 않는다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결 [데이터]

GreenPurple의 Alpha RGBA는 두 파일 모두 `(0.6274510025978088, 0.7882353067398071, 0.21960780024528503, 1)`이다. Bravo·Neutral도 같다. Gyml 파일은 일부 필드만 가진 사본이고, RSDB는 UI색·hue·Tag·bool 등을 포함한 완성된 typed 행이다. 사본에 없는 필드가 있다는 사실은 값 충돌이 아니다.

2026-10-03 정정: 기존 §2의 **“24개, GreenPurple Alpha가 RSDB와 다름”**은 현재 v0 원본 파일 대조에서 재현되지 않았다. 원문은 부모 문서에 정정 이력으로 남긴다. 과거 값/개수의 출처는 증명하지 못했으며 원인을 임의로 채우지 않는다. 현재 결론은 경로 판독과 파일 해시로 검증한 위 실제 자료에 한정한다.

선택된 typed 행은 로비의14색 생성과 캐릭터·지형/도색 재질의 팀색 공급으로 이어진다. 해당색 파생/GPU 식은 부모 team_color.md의 기존 근거를 재사용하며 이번 source 선택 분석의 신규 범위로 재계상하지 않는다.

## 8. 다른 기능과의 상호작용·고정 inventory

- [판독]: 실제 모듈 초기화·metadata·class factory·RSDB 파일 경로·typed vtable 연결. 고정 두 질문의 일반 사격장 데이터 공급은 RSDB typed 행으로 해소.
- [실행]: 원본 metadata/hash/classname/whole ctor/whole typed loader/whole name query. 원본 bytes의 36행, **1,296개 행 검사 불일치 0**, 널 읽기 0. 행 검사는 32개 f32+bool2+Tag1+query1이다.
- [데이터]: Gyml15개·196개 제공 원소 모두 대응 RSDB와 동일.
- r7 `L15/L253` 두 기존 행만 전체 확정으로 갱신한다. 분모·질문 단위는 보존한다. swap·재계산 주기·26000 복합은 승격하지 않는다.

## 9. 웹 포팅 구조와 구현 순서

`impl/render.md`, `impl/assets.md`에서 일반 팀색의 공급을 원본 RSDB36행 및 typed 필드로 연결하고, `Work/Gyml/...gyml` 문자열을 개별 파일 우선 선택으로 해석하지 않아야 한다. 현재 v0 사본만 보고 빠진 UI색/Tag/bool 기본값을 임의로 채우지 않는다. 구현 코드와 impl 문서는 변경하지 않았다.

권장구조: RSDB typed데이터 테이블→로비selector→팀별14색 생성→재질/도색 소비자. 이름 조회 입력은 __RowId이고 출력은 typed행이며, 행 RGBA/f32·Tag/bool 오프셋 대응은 §4를 따른다. 웹 권장 이름은 원본 클래스 이름과 구분한다.

## 10. 검증 코드·실행 결과·기대값

`PY web/tools/r8_graphics_teamcolor_rsdb_emu.py` exit 0. 상세 명령·실패·재실행은 `analysis/completion/r8/graphics_teamcolor_commands.md`, 결과는 같은 디렉터리 JSON이다. 최초 검증기는 AlphaTeamColor를 +8로 잘못 기대해 assertion 실패했다. 새 원본1407364를 판독해 +C(AlphaHue+8), Bravo/Charlie도 정정한 뒤 재실행했다.

원본 함수 코드는 패치하지 않았다. 하네스는 main image/BSS snapshot과 실제 압축 해제된 BYML을 사용했다. SDK strcmp/memcpy/guard/mutex를 경계 처리하고, `083d2f0` 메모리 할당 5회와 `0000250` 종료 destructor 등록 1회를 경계 처리했다. `3585094` disposer 초기화는 최종 검증에서 원본 실행했다. 초기 heap manager=0, 제품 파일 bytes는 공급했다. **상위 resource filesystem/압축 로딩과 live 시작 전체는 Unicorn 실행하지 않았으며 이 연결은 [판독]**이다. 검증 성공을 GPU 출력이나 모든 입력 동작의 실행으로 확대하지 않는다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

[미확정] developer/다중 RSDB 버전의 모든 실제 설정, 과거 “24개/GreenPurple 차이” 주장 발생 원인은 이 분석으로 확정하지 않았다. 일반 사격장 RSDB 대 개별 Gyml 공급 질문과는 별개다. 다음 근거는 version supplier와 resource resolver 설정 writer. 또한 swap/26000 특수 경로/팀색 재계산 주기 질문은 부모 §9에 유지한다.

2026-10-03 r8 신규 연결·실행·데이터 정정. [team_color.md](team_color.md) §2·§8·§9·§11, [analysis_completion.md](../analysis_completion.md), [completion_r8.md](../completion_r8.md). 기존 색 파생/로비 selector 증거는 부모 문서와 SHARED/FUNCS에 남아 있다.
