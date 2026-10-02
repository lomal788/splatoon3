# 00. 추출 파이프라인

원본 XCI에서 분석용 파일을 꺼내는 과정과 검증 결과입니다. 모든 산출물은 `c:/dev/splatoon3/extracted/` 아래에 있고, 이 문서의 명령으로 다시 만들 수 있습니다.

## 1. 원본

| 파일 | 크기 | 비고 |
|---|---|---|
| `c:/dev/splatoon3/original/Splatoon 3 [0100C2500FC20000][v0].xci` | 5,100,583,936 | 분석 대상. **읽기 전용** |
| `c:/dev/splatoon3/original/prod.keys`, `title.keys` | — | 사용자 제공. 키 값은 문서·로그에 옮기지 않음 |

원본 폴더에는 아무것도 쓰지 않습니다.

## 2. XCI 구성 [데이터]

루트 HFS0 아래 `update`·`logo`·`secure` 파티션. 결과 전체: `extracted/xci_info.json`.

| 파티션 | 내용 |
|---|---|
| update | 시스템 업데이트 NCA 225개 (Meta 114, Program 72, Data 36, PublicData 3). 게임 분석과 무관 |
| logo | `NintendoLogo.png`, `StartupMovie.gif` |
| secure | 게임 NCA 4개 (아래) |

| NCA | XCI 오프셋 | 크기 | Type | 비고 |
|---|---|---|---|---|
| `f6e46265849db31008d3de7091299d7c.nca` | 0x17018200 | 4,712,873,984 | Program | TitleID `0100c2500fc20000`, SDK 13.3.6.0, KeyGeneration 14 |
| `a774588701df50ebcd054c9e5da3ac72.nca` | 0x12fea4200 | 1,475,072 | Control | |
| `5b26287fc8d5f93e65a37009718f7e94.nca` | 0x13000c400 | 256,512 | Manual | |
| `511c91def865e2cb47180577f896eb47.cnmt.nca` | 0x13004ae00 | 3,584 | Meta | SDK 14.2.0.0 |

모든 secure NCA는 RightsId가 0이고(게임카드 배포) 콘텐츠 키는 NCA 헤더 key area를 `key_area_key_application_0d`(KeyGeneration 14 − 1)로 AES-ECB 복호화해서 얻습니다. 티켓은 쓰지 않습니다.

### Program NCA 섹션 [데이터]

| 섹션 | NCA 오프셋 | 크기 | FS | 해시 | 암호 |
|---|---|---|---|---|---|
| 0 ExeFS | 0x115f70000 | 0x2f1c000 | PFS0 | HierarchicalSha256 | AES-CTR |
| 1 RomFS | 0x1c000 | 0x115f54000 | RomFS | IVFC 6레벨 | AES-CTR, **NCA 압축 없음**(BucketTree 테이블 크기 0) |
| 2 Logo | 0x4000 | 0x18000 | PFS0 | HierarchicalSha256 | 없음 |

Jamboree(mpj)와 달리 RomFS가 압축되어 있지 않습니다.

## 3. 무결성 검증 [실행 — 자체 스크립트]

`xci.py romfs-verify`로 IVFC 전 레벨을 SHA-256 검증했습니다(로그 `extracted/verify_romfs.log`).

| 레벨 | 오프셋 | 크기 | 블록 수 | 불일치 |
|---|---|---|---|---|
| 0 | 0x0 | 0x4000 | 1 | 0 |
| 1 | 0x4000 | 0x4000 | 1 | 0 |
| 2 | 0x8000 | 0x4000 | 1 | 0 |
| 3 | 0xc000 | 0x8000 | 2 | 0 |
| 4 | 0x14000 | 0x8ac000 | 555 | 0 |
| 5 (데이터) | 0x8c0000 | 0x115693fec | 284,069 | **0** |

ExeFS NSO는 세그먼트(text/rodata/data)마다 헤더의 SHA-256과 일치합니다(`xci.py exefs` 출력의 `True`).

## 4. 산출물 [데이터]

| 경로 | 내용 |
|---|---|
| `extracted/exefs/main` (+`main.nso` 복사본) | 게임 NSO 43,354,031 B. build_id `19fe149d2955756c21eef824f9c7d966343b4a53` |
| `extracted/exefs/main.img` | 압축 해제 메모리 이미지 0x59ad000 (text 0x0+0x3e9df50, rodata 0x3e9e000+0x14e9ae4, data 0x5388000+0x432cb0, bss 포함). 로드 기준 0x7100000000 |
| `extracted/exefs/main.reloc.img` | 위 이미지에 RELA/JMPREL 재배치를 적용한 것. 포인터 테이블(vtable 등) 판독용 |
| `extracted/exefs/sdk`, `rtld`, `main.npdm` | SDK·런타임 링커. subsdk 없음 |
| `extracted/romfs/` | RomFS 7,199 파일, 4,653,654,885 B (`extracted/romfs_list.txt`) |
| `extracted/params/` | `Pack/Params.pack.zs` 해제 + BYML→JSON (GameParameterTable 282개, Banc 8개) |
| `extracted/actor/<이름>/` | 분석에 쓴 Actor 팩 해제본 |
| `extracted/main_strings.txt` | main rodata의 출력 가능 문자열 54,830개 |
| `extracted/typeinfo_names.txt` | main에 남은 Itanium typeinfo 이름 4,457개(nn·grpc·Havok 등 라이브러리뿐, 게임 클래스는 없음) |

## 5. 도구

| 도구 | 출처 | 용도 |
|---|---|---|
| `web/tools/nca_romfs.py` | `c:/dev/mpj/tools`에서 복사 | NCA 헤더 XTS 복호화, AES-CTR, IVFC 검증, RomFS 순회 |
| `web/tools/xci.py` | 자체 | XCI/HFS0 파싱, NCA key area 복호화, ExeFS PFS0 추출, NSO LZ4 해제·해시 검증, RomFS 검증·목록·추출 |
| `web/tools/spl_data.py` | 자체 | zstd(.zs, 사전 없음) 해제, SARC(.pack) 목록·해제, BYML v7(.bgyml/.byml) → JSON |
| `web/tools/xref.py` | 자체 | main 재배치 이미지 생성, ADRP+ADD/LDR 참조 색인(`analysis/xref_adrp.npz`, 1,814,365건), 문자열·주소 참조 조회 |
| `web/tools/disasm.py` | 자체 (capstone) | 주소 구간 디스어셈블, 문자열·상수 주석 |
| `web/tools/param_reflect.py`, `param_reflect_batch.py` | 자체 | 파라미터 구조체 리플렉션 방문 함수·생성자 판독 → 필드 오프셋·타입·기본값 ([02](02_code_and_params.md)) |
| Ghidra 12.1.2 + SwitchLoader | `c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC` (그대로 사용) | main NSO 분석, 프로젝트 `c:/dev/splatoon3/ghidra_proj/spl3_main` |

파이썬은 `c:/dev/splatoon3/.venv`(cryptography, zstandard, lz4, capstone, numpy, pillow, texture2ddecoder)를 씁니다. Ghidra는 JDK 21(`C:/Program Files/Java/jdk-21`)이 필요해서 `web/tools/ghidra_main_import.sh`에서 `JAVA_HOME`을 지정합니다.

## 6. 재현 명령

```sh
cd c:/dev/splatoon3
PY=.venv/Scripts/python
X="C:/dev/splatoon3/original/Splatoon 3 [0100C2500FC20000][v0].xci"
K=C:/dev/splatoon3/original/prod.keys

$PY web/tools/xci.py "$X" --keys $K info > extracted/xci_info.json
$PY web/tools/xci.py "$X" --keys $K exefs --nca f6e4 --section 0 --out extracted/exefs
$PY web/tools/xci.py "$X" --keys $K romfs-verify --nca f6e4 > extracted/verify_romfs.log
$PY web/tools/xci.py "$X" --keys $K romfs-list --nca f6e4 > extracted/romfs_list.txt
$PY web/tools/xci.py "$X" --keys $K romfs-extract --nca f6e4 --out extracted/romfs

$PY web/tools/xref.py build                     # main.reloc.img + 참조 색인
$PY web/tools/spl_data.py unpack extracted/romfs/Pack/Params.pack.zs extracted/params --json
sh web/tools/ghidra_main_import.sh              # 수 시간 걸림
```

Git Bash에서는 윈도우 경로(`C:/...`)로 넘겨야 합니다. `/c/...` 경로는 Windows 파이썬이 열지 못합니다.
