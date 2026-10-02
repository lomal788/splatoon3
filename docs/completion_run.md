# Lby_Lobby00 인수 분석 수행 기록

시작2026-10-02, 계속2026-10-03(Asia/Seoul). 분석만 수행한다. 모든 작업 파일은 `C:/dev/splatoon3` 안에 두었다. 보호 대상의 최초 SHA256은 `analysis/completion/protected_before.json`, 검증 결과는 `protected_verify.json`에 저장한다. 원본은 읽기만 사용했다. commit/push·삭제·이동을 수행하지 않았다.

## 1. 인수 읽기와 목록

사용자 지정 순서: `Get-Content web/README.md`, `Get-Content web/분석.txt`, `Get-Content web/docs/README.md`, `Get-Content web/docs/tools.md`, `Get-Content analysis/notes/SHARED.md`, `Get-Content analysis/notes/FUNCS.tsv`, `Get-Content web/docs/impl/*.md`를 분할해 끝까지 읽었다. 큰 출력은 잘린 구간을 다시 분할해 읽었다. 후속 원본 판독 전에는 공용노트와 `decomp_index.py --no-build`를 조회했다.

| 실제 명령·검사 | 결과 |
|---|---|
| `.venv/Scripts/python.exe --version` | Python3.13.2 |
| `git status --short` | 실패: 이 경로는 git repository가 아님. git변경작업 안 함 |
| `rg --files ... -g AGENTS.md` 및 C:/, C:/dev/, 저장소 지침 위치 확인 | 해당 추가 AGENTS 없음 |
| `.venv/Scripts/python.exe web/tools/analysis_completion.py inventory` | 출처레코드1119 생성, 초기범위1042·범위밖77 |
| 문서 미확정 table 출력 Python inline | 첫 시도 cp949 UnicodeEncodeError(U+2212). `PYTHONIOENCODING=utf-8` 설정 후 성공 |
| `rg -n -A45 -B8 'Main|ColBullet|ColGround|LayerHitMask' analysis/range/actor/Obj_SighterTarget*/*phive*` | 실패: PowerShell/rg 경로glob, os error123. 실제 `SighterTarget/Phive -g '*.json'` 경로로 재조회 성공 |
| `Get-Content web/分析.txt` | 실패: 잘못 쓴 파일명 없음. `Get-Content web/분석.txt`로 수정해 읽음 |
| `rg ... analysis/decomp/state/state_main.c` | 실패: 파일명 없음. decomp_index가 알려준 `state_big.c`/`state_big_full.c` 재사용 |
| `rg ... analysis/decomp/move/move_movement_all.c` | 실패: 파일명 없음. 기존 `move_full_main.c` 재사용 |

목록은 출처별 문장 단위로 반복질문을 보존한다. 전역기능 수를 추측한 수치가 아니다. 2026-10-03 범례2건을 `집계 제외`로 정정해 분모1040으로 변경했다. 원문/초기행/안정ID는 JSON에 남긴다. 기존해소 표기는 실제 근거문서 본문을 대조한 뒤만 확정 처리한다.

## 2. 이동 — 새 판독·원본 실행

```powershell
rg -n '266c6e4|246d060|SighterTarget|capsule' analysis/notes/SHARED.md analysis/notes/FUNCS.tsv
.venv/Scripts/python.exe web/tools/decomp_index.py --no-build 0x710266c6e4 0x710246d060 0x71021f0dcc
.venv/Scripts/python.exe web/tools/decomp_index.py --no-build 0x710265c230 0x710243e7d0
.venv/Scripts/python.exe web/tools/func_lookup.py 0x710266c6e4 0x710246d060
.venv/Scripts/python.exe web/tools/disasm.py 0x710266c6e4 -n 90
.venv/Scripts/python.exe web/tools/disasm.py 0x710246d060 -n 92
.venv/Scripts/python.exe web/tools/disasm.py 0x710246d1d0 -n 260
.venv/Scripts/python.exe web/tools/solo_move_emu.py
```

k1088건, 이동애니메이션2004건 반환·캐시 비트일치. 사용한 기존 디컴파일은 다시 생성하지 않았다. 새 도구는 원본 relocation 이미지와 기존 원본 초기화 하네스를 읽는다. 합성 객체·테이블, 제외한 libm NaN/다른무기 경로는 [player/solo_completion.md §10~§11](player/solo_completion.md)에 기록했다.

```powershell
.venv/Scripts/python.exe web/tools/decomp_index.py --no-build 0x7102475a54 0x710249f494 0x710249cb60 0x7102458cfc
.venv/Scripts/python.exe web/tools/decomp_index.py --no-build 0x7102459630
.venv/Scripts/python.exe web/tools/disasm.py 0x7102459ed0 -n 30
.venv/Scripts/python.exe web/tools/disasm.py 0x7102459b4c -n 46
.venv/Scripts/python.exe web/tools/disasm.py 0x71024a1910 -n 26
.venv/Scripts/python.exe web/tools/disasm.py 0x71024a1970 -n 44
.venv/Scripts/python.exe web/tools/solo_roll_counter_emu.py
```

롤 첫 실행 실패: `AssertionError: (-2147483648, 0.85, 0, 1065353216)`. 명령구간만 진입하면서 원본 선행 s8=1 입력을 제공하지 않은 하네스 오류였다. 해당초기값만 보충 후 카운터/시간쓰기1572건, 감쇠계수1020건 비트일치. 실제트리거/전체발사함수 실행은 아니다. reset조건은 명령판독만 했다. 버퍼producer는249f494이고 B+820 구조다. 기존 B+9dcc는 shifted-base 상대오프셋을 본체오프셋으로 오인한 표기라 정정했다.

문서 저장은 PowerShell here-string을 `.venv/Scripts/python.exe -`로 전달해 허용원본md와 analysis JSON만 작성했다. SHARED/FUNCS는 PowerShell `>>`로만 추가했다. 반복 `analysis_completion.py render` 성공. 웹 구현의 현재수준 표기는 원문을 수정하지 않고 감사표의 웹반영 열에 기록했다.

## 3. 병렬 분석

2026-10-03 사용자의 명시적 “병렬로 작업해” 요청 후 카메라/무기, 물리/충돌, 그래픽/효과를 독립분석했다. 공통표와 inventory는 root만 수정하며 각 담당은 별도 updates/commands 결과를 저장한다. 결과가 합쳐지기 전에는 완료비율에 포함하지 않는다.

- 카메라·무기: `analysis/completion/camera_weapon_commands.md`, `camera_weapon_updates.json`; [camera/solo_completion.md](camera/solo_completion.md)
- 물리·충돌: `analysis/completion/collision_commands.md`, `collision_updates.json`; 담당원본문서
- 그래픽·이펙트·효과음: `analysis/completion/graphics_fx_commands.md`, `graphics_fx_updates.json`; 담당원본문서

## 4. 보존 검증과 남은 작업

```powershell
.venv/Scripts/python.exe web/tools/analysis_completion.py render
.venv/Scripts/python.exe web/tools/analysis_completion.py verify
```

검증결과는 추후 실행값을 기록한다. 검증하기 전에 변경없음을 주장하지 않는다. 전체확정률은 [analysis_completion.md §2](analysis_completion.md)의 확정분자/범위분모를 사용한다. 미확정에 임의값을 채우지 않는다.

## 5. 회차 종료 및 병렬 결과 병합 (2026-10-03)

사용자가여기까지마무리를요청해신규분석을중단했다. 카메라/무기173행(확정24), 충돌17행(전체문장부분판독), 그래픽/효과28행(확정13)을안정ID로합쳤다. 추가이동X기저질문1행을확정했다. 최종계수는 [completion_summary.md](completion_summary.md)에있다.

마무리 JSON요약 첫읽기는encoding생략으로cp949 UnicodeDecodeError였다. 동일읽기에`encoding=utf-8`을명시해성공했다. 파생문서외새원본분석은수행하지않았다. 담당실패/실행기록3개는아래원문을이문서에옮겨보존한다.

### camera_weapon 명령 원문

#### 카메라·무기 담당 명령과 결과 (2026-10-03)

모든 명령의 작업 디렉터리는 C:/dev/splatoon3. PY=.venv/Scripts/python, sh=C:/Program Files/Git/bin/sh.exe. 쓰기·실행 결과는 사용자 허가 범위(analysis, web/docs/impl 제외, web/tools)만 사용했다.

## 읽기·기분석 조회

`Get-Content web/README.md -Raw -Encoding UTF8`, 이어 web/분석.txt, web/docs/README.md, web/docs/tools.md 읽음. SHARED/FUNCS의 spawnpos, FOV, InkConsume, PlayerCamera, 16e3af4, 24df4e8, 3a66ea4, 4d0/a90을 `rg -n`으로 조회. impl/camera.md·impl/weapon.md는 읽기만 했다. shooter_bullet·camera 문서와 inventory 원문 173행을 조회했다.

실행한 색인 조회(모두 `PY web/tools/decomp_index.py --no-build`):

- `0x71016e3af4 0x7102552170 0x7102624d58 0x7102492120 0x71024b28b0 0x7102353718 0x7102580780 0x71024a2c98 0x71024df4e8`
- `0x7103a66ea4 0x71024d5c6c`
- `0x7103a72e1c 0x71013a0cb0 0x7101254324 0x71016e3af4`
- `0x7103c27ae4`
- `0x710092efbc`
- `0x7100929788 0x71009258dc`
- `0x71025823b0 0x7102583008 0x7102483134 0x710258295c`
- `0x71012507e0`

기존 ink_consume/shooter_ink_action/shotdir_spawnpos, camera/batch1, camrest/cam_main_full, phys4/p4_phases를 재사용. 같은 함수 재디컴파일하지 않았다. `24df4e8` 색인에서 없음이었지만 func_lookup으로 메인 함수 내부 구간을 확인해 별도 함수로 분석하지 않았다.

`PY web/tools/func_lookup.py 0x71016e3af4 0x71024df4e8 0x7103a66ea4` → 시작/크기:16e3af4 2516 B, 24df4e8은24d9ae8 25840 B,3a66ea4 396 B.
`func_lookup.py 0x7103a72e1c` →360 B, `0x7103c27ae4` →196 B, `0x710092efbc` →188 B, `0x71012507e0` →256 B.
`PY web/tools/bl_callers.py 0x71016e3af4` →17540ec의1754d14 및 다수 생성 호출부 확인.

## 새 디컴파일

실제 실행(`sh web/tools/full_decomp.sh <출력> <주소...>`):

- `C:/dev/splatoon3/analysis/decomp/completion/camera_weapon_pool.c 0x71016e3af4 0x71024d5c6c` →2개 함수 파일 생성·본문 확인. 최초 tool 응답에는 stdout가 아직 없어 결과 파일 생성으로 완료를 확인했다.
- `C:/dev/splatoon3/analysis/decomp/completion/camera_shape.c 0x7103a72e1c 0x71013a0cb0` →exit0,2함수,INDEX4660.
- `C:/dev/splatoon3/analysis/decomp/completion/camera_shape_factory.c 0x7103c27ae4` →exit0,1함수,INDEX4666.
- `C:/dev/splatoon3/analysis/decomp/completion/camera_sphere.c 0x710092efbc` →exit0,1함수,INDEX4667.
- `C:/dev/splatoon3/analysis/decomp/completion/camera_basis.c 0x71012507e0` →exit0,1함수,INDEX4673.

INDEX 숫자는 같은 시간에 다른 담당자가 추가한 함수를 포함한 당시 전역 색인 수이며 본 담당자 분석 개수가 아니다.

명령 판독: `PY web/tools/disasm.py 0x71024d601c -n 45`, `0x710092efbc -n 47`, `0x71024df4c0 -n 45`, `0x71024df670 -n 26`, `0x71012507e0 -n 40`, `0x71024d5c6c -n 40` 실행. 생성자 반경, 기저 포인터·부호·eps·malloc진입점 확인.

RTTI 확인은 Python struct로 main.reloc.img의 vtable5466fd0−8을 읽음 →5487628 →이름4a8a050 → `15hknpSphereShape`. 원본 데이터 `PY web/tools/spl_data.py cat analysis/render/asb/pack/GameParameter/SplPlayer.spl__BulletShotDirAllInkActionParam.bgyml` →17항목, Shooter 없음. 키 파일은 읽거나 출력하지 않았다.

## 원본 실행과 실패

`PY web/tools/camera_weapon_completion_emu.py` 최초 →`UC_ERR_WRITE_UNMAPPED`. malloc을 PLT 범위로만 후킹한 도구 오류. 원본 24d5ce8 BL 대상083d2f0를 확인해 그 할당 스텁을 추가했다. 원본 함수를 수정한 것이 아니다.

수정 후 →`PASS permit 6/6, camera factory +0x68 and radius descriptor`.
local+manager존재·반경 경계값을 추가한 후 →`PASS permit 9/9, camera factory 4/4`.
기저 구간+원본 helper 비트 대조를 추가한 최종 실행 →**`PASS permit 9/9, basis 260/260 bit exact, camera factory 4/4`**, exit0. JSON 읽기로 입력·원본/재구현비트·스텁 리스트 확인.

검증 조건·스텁 한계는 camera/solo_completion.md §10, weapon/solo_shooter.md §10. 기존 weapon_ink_emu·weapon_spawnpos_emu·weapon_splash_emu는 이미 원본 실행된 것이므로 재실행하지 않았다.

## 그대로 남긴 도구/조회 실패

- `rg -n '^#|\[미확정\]|\[추정' web/docs/weapon/shooter_bullet.md web/docs/camera/*.md` →Windows에서 wildcard 경로 os error123. `rg ... web/docs/camera` 디렉터리 조회로 수정.
- `rg -n 'InkRecoverStop|MainInkSave|PostDelayFrame|InkConsume' extracted/params/Component/GameParameterTable/WeaponShooter_Normal* -g '*.json'` →wildcard 경로 os error123. 이미 확보된 원본 파라미터·ink_consume 근거만 사용, 이 조회를 성공으로 기록하지 않음.
- 디컴파일 완료 후 `Get-Content ghidra_proj/full_last_24171.log -Tail 15` →log없음. full_decomp가 정상적으로 임시log를 지우는 구조라 원문 c와 다음 session exit0 결과로 검증했다.

## 문서 반영

`PY analysis/completion/update_camera_weapon.py` →2개11절 보강문서 생성, 기존 player_camera/aim_swerve/shooter_bullet 정정 반영. 공유 completion 표·impl·games·scripts·package·original은 이 담당자가 수정하지 않았다.


### collision 명령 원문

#### Collision 담당 명령 기록 (2026-10-03)

- 사전 조회 성공: `rg -n '3aca|3ac9|3db4efc|3db5218|12e4d88|12e4acc|3af44e8|3ae53f0|Phive' analysis/notes/SHARED.md analysis/notes/FUNCS.tsv`, `.venv/Scripts/python web/tools/decomp_index.py --no-build <해당 주소>`.
- `player_vt.py 0x71055765e0`: 출력 `vtable 못 찾음`(exit 0). 원본 이미지에서 struct.unpack('<Q')로 해당 vtable 8개 슬롯을 읽어 보완했다.
- `bl_callers.py 0x7103db4efc 0x7103db5218 0x71012e4d88 0x7103acaee0 0x7103ae53f0`: 3acaee0 호출자는 3db4efc/3db5218, setter 호출자 11개 출력, 성공.
- `func_lookup.py 0x7103aca94c 0x7103ac9a00`: 앞 함수 3aca5d8/3ac971c로 출력. 월드 등록부가 정확한 callback 주소를 담고 있고 해당 주소의 독립 prologue를 `disasm.py`로 확인했다. Ghidra 함수 경계만으로 작은 콜백 시작을 결론 내리지 않았다.
- PowerShell double-quoted inline Python의 `struct.unpack_from("<Q",...)` 명령은 **ParserError: '<' operator reserved**로 실패. here-string 파이프로 재실행 성공. 키·원본 값 출력은 없었다.
- `func_lookup.py 0x71012eab48 0x71012eac1c 0x71021f2e0c 0x7103c34b7c 0x7103b02470`: 성공.
- `& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/completion/collision_filter_followup.c 0x71012eab48 0x71012eac1c 0x71021f2e0c 0x7103c34b7c 0x7103b02470`: 5함수 출력, exit0, 4665함수 색인. 12eac1c/21f2e0c는 destructor였으므로 실제 branch 시작 12eac80/21f2e70은 `disasm.py ... -n 16`으로 정정 판독.
- `& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/completion/collision_shape_filter.c 0x7103ad658c 0x7103b0158c 0x7103b02208`: 3함수, exit0, 4670색인.
- `& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/completion/collision_shape_tag.c 0x7103ad677c 0x7103ad6a70`: 2함수, exit0, 4672색인.
- `& 'C:\Program Files\Git\bin\sh.exe' web/tools/full_decomp.sh C:/dev/splatoon3/analysis/decomp/completion/collision_player_reset.c 0x71024f4440 0x71024f56d4`: 24f56d4는 기존 파일 표시 후 건너뜀, 신규1함수, exit0, 4674색인.
- `disasm.py 0x7103c4dd30 -n 100`, `disasm.py 0x7103af44e8 -n 65`, `disasm.py 0x7103ad6a70 -n 90`, `disasm.py 0x7103aca9e0 --end 0x7103acac60`, `disasm.py 0x7103ac9a20 -n 55`, `disasm.py 0x71024f4610 -n 35`: 판독 성공.
- `.venv/Scripts/python web/tools/collision_filter_completion_emu.py`: 첫 실행4096/4096; shapeTag 테스트 추가 후 재실행4096/4096 + 1024/1024, 실패0, exit0. 스텁은 결과 JSON과 docs §10에 기록.
- `.venv/Scripts/python web/tools/collision_origin_completion_emu.py`: 1024/1024 f32 bit match, 실패0, exit0.

모든 생성·저장은 C:/dev/splatoon3 안. 원본과 게임/scripts/impl/package 수정·commit/push 없음.


### graphics_fx 명령 원문

#### graphics / effect_sound 실행 명령 기록 — 2026-10-03

cwd는 모두 C:/dev/splatoon3. PY=.venv/Scripts/python.exe. Python 출력은 PYTHONIOENCODING=utf-8, 새 도구 실행은 PYTHONDONTWRITEBYTECODE=1. 분석 파일 기록만 require_escalated로 실행했다.

## 사전 확인·기존 근거 조회

- `Get-Content web/README.md -Raw -Encoding UTF8`, 이어서 `web/분석.txt`, `web/docs/README.md`, `web/docs/tools.md` 읽기: 성공. 부모 작업에서 읽은 SHARED/FUNCS 전체와 상속된 요약을 재사용하고 아래 관련 항목 rg로 대조했다.
- `rg -n 'MainLight|10fe270|26e613c|HairArrange|DistCoef|limiter|color0|color1|alpha0|alpha1|VAT|2b5fe88|2b607c4|2b60ea0' analysis/notes/SHARED.md analysis/notes/FUNCS.tsv`: 성공. 기존 MainLight/LOD 정정·HairArrange 미독·limiter impl판독 확인.
- `Get-Content web/docs/impl/{render,assets,fx}.md -Raw -Encoding UTF8`: 읽기만. 병렬 묶음의 출력이 일부 잘려 fx 마지막100행 및 해당 source문서 구간을 후속 읽기했다. impl 수정 없음.
- `PY web/tools/decomp_index.py --no-build 0x71026e613c 0x71026e5e00 0x71026e5ccc 0x71026e2bdc 0x71026e3118 0x71026e3728 0x71026e382c 0x7102b8c668 0x7102b8c800`: 모두 gfx4/p_batch1.c에 있음. 재디컴파일 없음.
- `PY web/tools/decomp_index.py --no-build 0x71026e4e80 0x71026e44a0 0x71010fe270 0x7102b5fe88 0x7102b607c4 0x7102b60ea0`: 기존 색인 사용.
- `PY web/tools/decomp_index.py --no-build 0x71026e5c00 0x71026e5b18 0x71026e5af0 0x71026e6c90 0x71026e6cc4 0x71026ed214`: 앞5개 없음, 26ed214는 bullet/WeaponShooter_vt.c. 생성하지 않았음.
- `PY web/tools/decomp_index.py --no-build 0x71026ceca0 0x71026ceca8 0x71026ce890 0x71026ce898`: 색인 없음. 아래 disasm 일부만 읽고 추가 디컴파일 안함.
- `PY web/tools/decomp_index.py --no-build 0x710081aee4 0x71008190fc 0x7103848c88 0x7103848e34 0x7103849000 0x7103129c98`: 기존 vfx_lib_01.c, limiter_cmp.c, snd_xlink_b1.c 재사용.

## 함수 경계·명령 판독

- `PY web/tools/func_lookup.py 0x71026e5cfc`: 26e5ccc 함수,size308. 따라서 add+360은 destructor 내부.
- `PY web/tools/class_info.py spl::PlayerCustomHead`, `... spl::PlayerCustomHair`: 성공, vt5641998/56416f8 각각63슬롯.
- `PY web/tools/player_vt.py 0x7105641998`, `... 0x71056416f8`: **인자 사용 실패**. 주소를 클래스명으로 해석해서 “vtable 못 찾음”. 원본 오류 아님.
- `PY web/tools/player_vt.py --vt --unique 0x7105641998 0x71056416f8`: 성공, 고유 슬롯별 함수 확인.
- `PY web/tools/disasm.py 0x71026e613c -n 160`: 성공, 뼈get 버퍼 재배치·SIMD FMUL/FMLA/FMLA/FADD·모델 기록 확인.
- `PY web/tools/disasm.py 0x71026ceca0 -n 10`, `... 0x71026ce890 -n 10`: 성공, 일부슬롯만 확인. HairArrange 의미 결론 없음.
- `PY web/tools/disasm.py 0x71008190fc -n 135`: 성공. 이어서 `... 0x7100819190 -n 41`, `... 0x7100819d5c -n 28`: FIXED 네 guard와 load/store 확인.
- `PY web/tools/func_lookup.py 0x71008190fc 0x71026e613c`: 함수 시작/size5504,1272 확인.
- `Get-Content analysis/decomp/gfx4/p_batch1.c`의 1–102,747–1062,1063–1328,1424–1548,1720–1791,1792–2387 구간 읽기: 성공. HairArrange/마스크 기존 후보의 역할 정정.
- `Get-Content analysis/decomp/vfx/vfx_lib_01.c`의 18176–18253,19609–19813,36696–36740 구간 및 헤더 rg: 성공. 08190fc patch 및082a29c 호출 확인.
- `Get-Content analysis/decomp/fx/limiter.c` 첫220행·`limiter_cmp.c` 본문: 성공. guard/키순서/종류별 비교 판독.

## 셰이더·원본 데이터 소비 판독

- `rg --files analysis/shader analysis/vfx analysis/effect_sound`: 기존 p1383/p1940/p1897 및 npy 위치 확인.
- `Get-Content analysis/vfx/shader/p1940.options.txt -Raw`, `p1940.frag` 마지막150행 및 241–338행, `p1940.vert` 끝/색 출력 rg: 성공. 첫 묶음 출력잘림 후 필요한 구간 별도로 읽음.
- `Get-Content analysis/vfx/shader/p1383.vert` 300–434,480–564행, `p1383.frag` normal·최종alpha 구간, options의 색/alpha rg: 성공. A→half→방향→normal 소비와 clamp시간 확인.
- `rg 'data[128/129]|out_attr1.w' analysis/vfx/shader/p1897.vert` 및 `p1897.frag` alpha/최종색 구간: 성공. Crown alpha1 키 값·시간 및 subtract-A0/multiply-A1 확인.
- Python json 읽기로 `analysis/vfx/emitters_v46_fields.json`의 shaderIndex/volumeType 및 ball/Splash 고정값 비교: 표본11이미터 모두volume0. 범위전체전수로 확대하지 않음.
- `rg -n ... analysis/decomp/gfx4/p_hat*.c`: **실패 os error123**, PowerShell glob 전달로 경로문법잘못됨. decomp_index가 알려준 render/r4_hat.c를 직접 읽어서 복구.
- `rg ... analysis/vfx/shader/p1897.body.txt`: **실패 파일없음**. p1897.vert/.frag 실파일을 읽어 복구.

## 새 실행·결과

- `PY web/tools/completion_head_matrix_emu.py`: 성공. 원본26e613c 행렬259/259 비트 일치, 몸없음1건, 분리f32계산과254건 차이. 결과 graphics_head_matrix_emu.json. 스텁·우회경로는 결과파일/solo_graphics_audit §10.
- `PY web/tools/completion_vat_normal_check.py`: 성공. 실제 VAT A 498/498 half복원 일치, normal 길이² 최대오차4.076190837887239e-5. 결과 fx_vat_normal_check.json. **재구현·데이터대조, GPU원본실행아님**.
- `PY web/tools/completion_limiter_compare_emu.py`: 성공. 원본3848c88/3848e34/3849000 각768, 합계2304/2304 정수비트 일치,null6. 스텁없음. vt180 factor·정렬·정지caller는 미실행.
- `PY analysis/completion/graphics_fx_doc_update.py`: 성공. 새11절문서2개, 기존본문5문서 보완. root인벤토리 수정하지 않고 독립 updates28개(확정13,조사중15) 저장.

## 저장 범위와 중단

원본/웹코드/impl/package.json 수정없음. decomp_index --no-build로 INDEX재생성안함. full_decomp 신규실행없음. 삭제·이동·commit·push 없음. 사용자가 여기까지 마무리를 요청한 이후 추가분석을 중단하고 확보근거의 문서 반영만 했다. 미발견/미실행은 조사중이며 확정불가로 올리지 않았다.


## 최종 통합·문서 검증 — 2026-10-03

사용자의 중단·마무리 요청 후 신규 원본 분석을 멈췄다. 담당별 결과를 본문과 목록에 통합하고 요약 문서에 영역별 수치, 실행 결과의 경계, 미확정과 다음 근거, 웹 반영 필요를 기록했다.

- `.venv/Scripts/python.exe web/tools/analysis_completion.py render`: 성공. 1119개 기록, 범위 내 1031개, 범위 밖 85개, 집계 제외 3개. 확정 56개(5.43%). 원문 발췌의 상대 링크·잘린 링크는 목록 셀에서 일반 텍스트로 표시하고, 생성한 근거 링크만 활성화했다.
- `.venv/Scripts/python.exe analysis/completion/validate_docs.py`: 성공. 새 분석 본문 6개 모두 1~11절, 본문·목차·보고서 로컬 링크 오류 0건. `analysis/completion/docs_verify.json` 저장.
- `.venv/Scripts/python.exe web/tools/analysis_completion.py verify`: 성공. 보호 파일 592개 SHA-256 대조, 변경 0건·추가 0건. `analysis/completion/protected_verify.json` 저장.

분석 전체 100%는 미달성이다. 확정 불가 종결 0건이며, 조사 중·부분 확정·대기 항목을 확정으로 올리지 않았다. 웹 소스/impl 수정과 commit/push 없이 이번 회차를 마무리했다.
