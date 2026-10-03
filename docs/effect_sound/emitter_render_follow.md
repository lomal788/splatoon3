# 이미터 렌더 설정·추종·초기 회전 — r8 (2026-10-03)

## 1. 기능 개요와 사용자에게 보이는 동작

[판독]+[실행]+[데이터] 원본 이미터는 깊이 검사·쓰기와 블렌드를 각자 설정한다. `followType=2`는 원본 `POS` 옵션이고, 초기 회전은 파일 값에 이미터셋 동적 회전을 더해 입자 정점 속성 5에 기록한다. 이 문서는 필드표의 남은 추정을 소비 코드와 대조한다. GPU 래스터화 실행은 하지 않았다.

## 2. 분석 대상 원본·버전·자료 위치

Splatoon 3 v0 `extracted/exefs/main.reloc.img`, 실제 `extracted/romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs`의 VFXB v46. 기존 `analysis/decomp/vfx/vfx_lib_00..02.c`, `vfx_b1.c` 재사용. 추출은 `analysis/completion/r8/static.vfxb`, GRSN은 같은 폴더 `static_grsn.bfsha`, 새 셰이더는 `shader/p364.*`다. 중간 파일을 삭제·이동하지 않았다.

## 3. 진입점과 전체 호출 흐름

[판독] `08182f4(EmitterResource,device)` → `082804c(ER+148,device,*(ER+10)+BD8)` → `08281fc` blend descriptor → `08442d0`, `08444f4` depth/stencil, `08440e4` polygon/multisample. `083eb80`의 원본 문자열로 각 동적 함수 포인터가 NVN 어떤 setter인지 대응했다. `081a6f0`는 원본 shader-key builder이고, `08190fc`의 `081a0a0..b8`은 Res+A00을 ER+360으로 복사한다. 원본 입자 생성 `081e3e4`는 이 값과 EmitterSet+140을 정점 속성 5에 더해 쓴다.

주소는 모두 `0x7100000000` 기준이다. 함수 시작·기존 decomp·SHARED/FUNCS 중복을 먼저 확인했으며 기존 902개 라이브러리 디컴파일을 다시 만들지 않았다.

## 4. 구조체·필드·상수·열거형 표

[판독]+[실행] 실제 render builder의 읽기:

| ResEmitter | 의미·정확한 소비 |
|---|---|
| +BD8 u8 | 0이면 blend off, 나머지는 on |
| +BD9 u8 | 0이면 depth test off, 나머지는 on |
| +BDA u8 | 0..7 → NVN depth comparison 1..8; 범위 밖은 UnexpectedDefault |
| +BDB u8 | 0이면 depth write off, 나머지는 on. `080f0bc` 입자 정렬의 방향 선택에도 사용 |
| +BDE u8 | 0..5 blend mode. 범위 밖은 UnexpectedDefault |
| +BDF u8 | 1→NVN cull 2, 2→cull 1, 나머지→0 |

[판독]+[실행] blend mode 0..5의 실제 NVN 인자:

| mode | RGB src,dst | alpha src,dst | RGB/alpha equation |
|---|---|---|---|
| 0 | 5,6 | 2,6 | 1,1 |
| 1 | 5,2 | 2,2 | 1,1 |
| 2 | 5,2 | 2,2 | 3,3 |
| 3 | 1,3 | 1,3 | 1,1 |
| 4 | 10,2 | 10,2 | 1,1 |
| 5 | 2,6 | 2,6 | 1,1 |

수치는 원본 `08426d4` table `4a7c6a4`와 `08426c4` table `4a7c690`의 결과다. 외부 SDK enum 이름을 추측해 붙이지 않았다. mode2의 equation은 3이다. stencil test는 0, color channel mask는 RGBA 전부 on, polygon fill/frontface·offset·multisample 기본 설정은 builder의 원본 descriptor에 따른다. +BDC/+BDD/+BE0..BE7은 이 builder가 읽지 않는다. 이 사실만으로 모든 경로에서 padding이라고 단정하지 않는다.

## 5. 상태 전이와 전체 수명

[판독]+[실행]+[데이터] `followType` 0/1/2는 `081a6f0`가 shader key word2에 각각 `0x200/0x800/0x400`을 OR한다. 3..127 및 signed-negative byte는 해당 비트를 추가하지 않는다. 실제 PlayerMetmDive/splash의 byte2, 프로그램364(variation3837)은 `_EMITTER_FOLLOW_TYPE_POS_CONVERTER=1`, ALL/NONE=0이다. 기존 프로그램1383/1747의 byte0 ALL과 프로그램1886의 byte1 NONE 대응도 유지된다. 다른 모드의 실제 행동 분석으로 확대하지 않고 공통 SDK 값2의 대응 데이터로 사용했다.

[판독] 원본 `08157b0`의 위치 입력 변환에서도 2는 입자가 가진 행렬의 회전 축과 **현재 emitter+490 이동**을 함께 고른다. 0은 현재 emitter+460..498 행렬 전체, 1은 입자가 가진 행렬 전체를 고른다. 생성 함수 `081e3e4`에도 별도의 `follow==2` 분기가 있다. key/옵션의 POS 명칭 확정과 이 분기 판독은 원본 전 프레임 궤적 실행을 의미하지 않는다.

## 6. 계산식·조건·상세 의사코드

[판독]+[실행] 초기 회전:

```text
ER[360.xyz] = Res[A00.xyz]       // A0C는 0으로 복사
particle.attribute5.xyz = f32(ER[360.xyz] + EmitterSet[140.xyz])
```

원본 p1383 vertex의 location5 `sysInitRotateAttr.xyz`가 이 값을 읽는다. 회전 반전 비트에 따른 부호 선택 뒤 `(rand−0.5)*Res[A10.xyz]`와 시간 회전을 합성한다. 실제 sin/cos 회전이므로 값은 라디안이다. 원본 A00은 GPU UBO의 data[160]을 직접 읽는다고 설명하면 잘못이다. CPU의 속성 공급 경로가 확인됐다. shader의 FMA·sin/cos·전체 GPU bit match는 주장하지 않는다.

[판독]+[실행] `0822290`의 원본 key interpolation: key {x,y,z,time}, 1개 또는 첫 time 앞은 첫 xyz; 마지막 time 이상은 마지막 xyz와 finished=1; 내부 구간 `[t_i,t_{i+1})`에서 mode0은 **FSUB→FDIV→FMUL→FADD**, mode1은 왼쪽 xyz. mode2/255는 내부 구간에서 출력과 finished를 바꾸지 않는다. 모든 mode에 앞/뒤 경계 처리는 먼저 적용된다. 정렬되지 않아 구간을 못 찾으면 오류 경로다.

## 7. 애니메이션·이펙트·소리·카메라·에셋 연결

[실행]+[데이터] 실제 WpShtrBullet1Emit, CmnFloorSplash1Emit/Near/Dist, CmnWallSplash1Emit, WpShtrMzfNml의 자식 포함 **11개**가 render caller `08182f4`까지 통과했다. 각 16바이트와 NVN 전달 인자 전체는 `vfx_state_emu.json`의 actual 배열에 보존했다. 최초 필드표의 9개 표본 수와 이 검증의 자식 포함 11개를 혼동하지 않는다.

## 8. 다른 기능과의 상호작용

[판독, 부분] 기존 표의 **“Combiner=0xC30..C40”은 v53 순서를 잘못 옮긴 추정**이었다. `08190fc`와 `08258d4 등` 계열 소비에서 +C30 s32는 alpha1 loop period, +C34 s32는 scale loop period, +C38..C3C는 color0/alpha0/color1/alpha1/scale key interpolation byte다. +C30의 값은 alpha1 loop enable(+C1B)이 켜진 때 정적 +AC f32로도 변환된다. +C34는 +C1C가 켜진 때 +B0으로 변환된다. +C3D..C3F의 전체 의미와 실제 combiner 옵션 필드 위치는 아직 미확정이므로 이 질문은 부분 상태로 유지한다.

## 9. 웹 포팅 구조와 구현 순서

impl/fx.md·impl/assets.md 변경 없이, 반영 필요를 inventory에 기록했다. follow2를 임의로 ALL/NONE으로 대체하지 않고 POS를 구분할 것. 초기 회전은 정점 속성의 원본 base+dynamic 합에서 시작할 것. 렌더 설정은 원본 depth/write/blend/cull 각각을 보존할 것. key mode1은 왼쪽 유지이며 mode0 계산을 FMA로 바꾸지 않을 것.

## 10. 검증 코드·실행 결과·기대값

```powershell
.venv/Scripts/python.exe web/tools/decomp_index.py 0x710082804c --no-build
.venv/Scripts/python.exe web/tools/decomp_index.py 0x710081a6f0 --no-build
.venv/Scripts/python.exe web/tools/func_lookup.py 0x710082804c 0x710081a6f0
.venv/Scripts/python.exe web/tools/effect_esetb.py ptcl extracted/romfs/Effect/static.Nin_NX_NVN.esetb.byml.zs analysis/completion/r8/static.vfxb
& 'C:\Program Files\dotnet\dotnet.exe' analysis/shader/build/bin/Release/net7.0/shader_dump.dll prog-bfsha C:/dev/splatoon3/analysis/completion/r8/static_grsn.bfsha VfxGeneralShader - analysis/completion/r8/shader/p364 --index 364
.venv/Scripts/python.exe web/tools/r8_vfx_state_emu.py
.venv/Scripts/python.exe web/tools/r8_vfx_rotate_keys_emu.py
```

[실행] render **832 조합+실제11이미터**, follow key **896 조합**, mismatch0. 원본 descriptor/default/table 변환과 caller를 실행했고 native NVN setter 24개는 인자를 기록하는 스텁이다. 실제 렌더 결과로 확대하지 않는다. 초기 회전 copy block→전체 원본 birth+점 형상 **768건**, key helper **320건(미지원 내부 mode112건 포함)**, 스텁 없이 비트/flag mismatch0. birth는 합성 이미터·난수 표·follow NONE·자식 없음으로 제한한다. 기존 r7의 방향/scale 테스트를 신규 확정으로 재집계하지 않았다.

실패: Sec 객체를 byte 배열로 읽어 TypeError가 났고 v.d[bo:bo+EF0]으로 고쳤다. shader 출력 폴더가 없어 DirectoryNotFoundException 후 폴더를 만들고 재실행했다. Unicorn mem_write에 bytearray를 넣어 ctypes.ArgumentError 후 bytes로 고쳤다. xref.py subcommand를 누락해 usage 오류가 났다. 080f0bc를 lib_01에서 찾은 검색은 실패했으며 decomp_index로 실제 vfx_b1.c를 찾았다. PowerShell wildcard 경로를 rg에 넣은 검색도 실패했다. 모든 파일은 C:/dev/splatoon3 안에 저장했다.

## 11. 미확정 사항과 추가 분석에 필요한 근거

| 항목 | 이유·시도·다음 근거 |
|---|---|
| Render 나머지 byte | builder에서 안 읽음. 전체 runtime의 포인터 별칭 접근·데이터 writer가 아직 부족; +BDC/BDD/BE0..BE7은 unknown 유지. Render 전체 질문은 부분 처리 |
| 잘못된 Combiner 구역의 끝3byte/실제옵션 위치 | C30/C34/C38..3C는 직접 consumer로 정정, 마지막3byte와 실제 옵션 위치를 모두 알았다고 승격하지 않음; shader-key/옵션 registry와 +C40 이후 reader |
| 모든 POS emitter의 전체 frame trajectory | key·실제 옵션 대응 확정, 08157b0/081e3e4의 행렬 공급·GPU motion 전체를 추가 실행해야 함 |
| 정적 param940과 fluctuation100..12C | key 복제만으로 shader/CPU 의미는 해결 안 됨. 해당 원본 consumer 계속 추적 |
| 원본 GPU pixels | NVN setter 기록과 shader 판독만 했음. 이 문서의 실행 비트일치는 CPU 산술·descriptor/인자 범위 |
