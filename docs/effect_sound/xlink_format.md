# XLink2 (ELink2 / SLink2) 바이너리와 실행 규칙

이펙트·사운드를 게임 이벤트에 연결하는 데이터 `romfs/ELink2/elink2.Product.100.belnk.zs`, `romfs/SLink2/slink2.Product.100.bslnk.zs`의 형식과, 키·액션·속성이 에셋 재생으로 바뀌는 규칙입니다. 상위 문서는 [effect_sound.md](effect_sound.md)입니다.

확정 수준 표기는 [../README.md](../README.md)를 따릅니다. 이 문서에서 **[참고]**는 공개 xlink2 디컴파일(Nitr4m12/xlink2, Splatoon 2 심볼 기반, 일부 NON-MATCHING) 사본 `analysis/effect_sound/ref_xlink2/`을 읽은 것입니다. 이 게임 코드에서 직접 확인한 것이 아니므로 [판독]과 구분합니다.

---

## 1. 개요

- XLink2는 Nintendo EAD 공용 라이브러리입니다. 액터 하나가 "사용자(User)" 하나를 가지고, 게임 코드가 **키 이름**을 방출(searchAndEmit)하거나 **액션**을 바꾸거나 **속성** 값을 바꾸면 그 사용자 데이터에 적힌 에셋(이펙트 이미터셋 / 사운드 이름)이 재생됩니다.
- ELink = 이펙트 연결, SLink = 사운드 연결. 파일 형식은 같고 파라미터 정의(ParamDefine)만 다릅니다 [데이터].
- 액터는 컴포넌트 `ELinkRef`/`SLinkRef` → `engine__component__ELinkParam`/`SLinkParam`의 `UserName`으로 사용자를 고릅니다. 사용자 이름은 파일에 문자열로 없고 **CRC32 해시**만 있습니다 [데이터].

```
Pack/Actor/WeaponShooterNormal.pack.zs
  Component/ELink/WeaponShooterNormal.engine__component__ELinkParam.bgyml  { UserName: "WeaponShooterNormal" }
  Component/SLink/WeaponShooterNormal.engine__component__SLinkParam.bgyml  { UserName: "WeaponShooterNormal" }
→ crc32("WeaponShooterNormal") = 0x171e020d → ELink 사용자 #59, SLink 사용자 #96
```

## 2. 자료와 도구

| 항목 | 위치 |
|---|---|
| ELink2 | `extracted/romfs/ELink2/elink2.Product.100.belnk.zs` (해제 667,512 B, version 0x22, 사용자 429) |
| SLink2 | `extracted/romfs/SLink2/slink2.Product.100.bslnk.zs` (해제 2,419,468 B, version 0x1F, 사용자 733) |
| 로드 경로(main 문자열) | `ELink2/elink2.%s.%s.belnk` (참조 0x7103d5a0e8, 함수 0x7103d59d5c), `SLink2/slink2.%s.bslnk` (0x7103916130, 함수 0x7103915d24) [데이터] |
| 파서 | `web/tools/effect_xlink.py` (info / check / user / dump / find) |
| 사람용 요약 | `web/tools/effect_xlink_summary.py <users.json> <이름>` |
| 평가기(합성) | `web/tools/effect_xlink_eval.py` (키+속성 → 에셋 목록) |
| 사용자 이름 수집 | `web/tools/effect_usernames.py` → `analysis/effect_sound/xlink_usernames.json`, 후보 전체 `xlink_names_all.txt` |
| 전체 덤프 | `analysis/effect_sound/elink2_users.json`, `slink2_users.json` (이름 복원 ELink 390/429, SLink 465/733, 나머지는 `#crc32`) |
| 참고 소스 | `analysis/effect_sound/ref_xlink2/*.h, *.cpp` |

이름 복원: 액터 팩 3,572개의 ELinkParam/SLinkParam UserName(ELink 409종, SLink 497종) + main 문자열 + 액터 이름 + 파라미터 문자열을 CRC32로 대조했습니다. 남은 39/268 사용자는 이름 미상입니다 [데이터].

## 3. 파일 형식 [데이터]

모두 리틀 엔디언. "위치(pos)"는 Splatoon 2판(u32)과 달리 **u64**입니다. 아래 표는 원본 파일 두 개 전체에 대한 일관성 검사(`effect_xlink.py check`)로 맞췄습니다.

- 에셋 파라미터 표 끝 = 트리거 덮어쓰기 표 시작, 그 끝 = 로컬 속성 이름 표 시작, 공통 표 끝 = exRegion 시작: 두 파일 모두 일치.
- 사용자 429/733개 전부: 마지막 트리거 레코드 끝이 다음 사용자 시작(마지막은 조건표 시작)과 정확히 일치.
- 콜 테이블 키 문자열의 CRC32 = 레코드 keyNameHash, 트리거의 assetCtbPos가 콜 테이블 경계를 가리킴: 오류 0.

### 3.1 헤더 (0x60 B)

| 오프셋 | 타입 | 이름(참고 소스) | ELink 값 | SLink 값 |
|---|---|---|---|---|
| 0x00 | char[4] | magic | `XLNK` | `XLNK` |
| 0x04 | u32 | dataSize | 0xa2f78 | 0x24eb0c |
| 0x08 | u32 | version | 0x22 | 0x1f |
| 0x0C | u32 | numResParam | 16,893 | 138,491 |
| 0x10 | u32 | numResAssetParam | 2,822 | 14,591 |
| 0x14 | u32 | numResTriggerOverwriteParam | 60 | 41 |
| 0x18 | u64 | triggerOverwriteParamTablePos | 0x17c34 | 0xa6464 |
| 0x20 | u64 | localPropertyNameRefTablePos | 0x17ed4 | 0xa65c4 |
| 0x28 | u32 | numLocalPropertyNameRefTable | 187 | 173 |
| 0x2C | u32 | numLocalPropertyEnumNameRefTable | 175 | 213 |
| 0x30 | u32 | numDirectValueTable | 580 | 467 |
| 0x34 | u32 | numRandomTable | 3 | 306 |
| 0x38 | u32 | numCurveTable | 131 | 207 |
| 0x3C | u32 | numCurvePointTable | 377 | 680 |
| 0x40 | u64 | exRegionPos (사용자 블록 시작) | 0x1ab5c | 0xaab58 |
| 0x48 | u32 | numUser | 429 | 733 |
| 0x50 | u64 | conditionTablePos | 0x829c8 | 0x1fb58c |
| 0x58 | u64 | nameTablePos | 0x86f78 | 0x20d774 |

- numResParam은 실제 에셋+덮어쓰기 파라미터 합(ELink 17,001 / SLink 138,538)과 다릅니다. 의미는 [미확정].

### 3.2 헤더 뒤 배치

```
0x60                       u32 userNameHash[numUser]   (CRC32, 오름차순 정렬 → 이진 탐색)
align 8                    u64 userOffset[numUser]     (파일 시작 기준, exRegion 안)
ParamDefineTable           (3.3)
ResAssetParam[numResAssetParam]       {u64 mask; u32 ResParam[popcount(mask)]}  정렬 없음
ResTriggerOverwriteParam[n]           {u32 mask; u32 ResParam[popcount(mask)]}  (= triggerOverwriteParamTablePos)
u64 localPropertyNameRef[numLPN]      이름표 오프셋
u64 localPropertyEnumNameRef[numLPEN] 이름표 오프셋
u32 directValue[numDirect]            값(float 는 f32 비트, string 은 이름표 오프셋)
{f32 min, f32 max} random[numRandom]
ResCurveCallTable[numCurve]  0x18 B   {u16 pointStart, u16 numPoint, u16 curveType, u16 isPropGlobal, u64 propNamePos, s32 propIdx, s16 localPropertyNameIdx, pad}
{f32 x, f32 y} curvePoint[numCurvePoint]
exRegion: 사용자 블록들 (3.5)
조건표 (conditionTablePos, 3.7)
이름표 (nameTablePos): NUL 종료 UTF-8 문자열(일본어 키 다수)
```

### 3.3 ParamDefineTable

헤더 0x18 B: `u32 size, u32 numUserParam, u32 numAssetParam, u32 numCustomAssetParam, u32 numTriggerParam, u32 pad`. 뒤에 정의 0x18 B × (user+asset+trigger) = `{u64 namePos(표 뒤 문자열 영역 기준), u32 type, u32 pad, u64 default}`. **기본값은 64비트**: Float는 f64, 정수형은 s64 [데이터].

type: 0 UInt32(정수), 1 Float, 2 Bool, 3 Enum, 4 String, 5 Arrange [참고: 이름 / 데이터: 필드명과 일치].

**ELink** (user 0, asset 44 중 custom 13, trigger 14):

| 비트 | 에셋 파라미터 | 형 | 기본 |
|---|---|---|---|
| 0 | AssetName | String | "" |
| 1 | RuntimeAssetName | String | "" (= 이펙트 이미터셋 이름) |
| 2 | Eset | UInt32 | 0 |
| 3,4 | EffectGroup / GroupId | String / UInt32 | |
| 5,6 | EffectPauseGroup / EffectPauseGroupId | String / UInt32 | |
| 7 | Delay | Float | 0.0 |
| 8 | Duration | Float | 0.0 |
| 9 | Clip | Enum | 0 |
| 10 | ForceCalc | UInt32 | 0 |
| 11 | Matrix | Enum | 1 |
| 12 | RotateSource | Enum | 0 |
| 13 | Bone | String | "" |
| 14 | Scale | Float | 1.0 |
| 15–17 | PositionX/Y/Z | Float | 0 |
| 18–20 | RotationX/Y/Z | Float | 0 |
| 21–24 | Red/Green/Blue/Alpha | Float | 1.0 |
| 25–29 | EmissionRate / EmissionScale / EmissionInterval / DirectionalVel / LifeScale | Float | 1.0 |
| 30 | BitFlag | UInt32 | 0 |
| 31 | ForceTeam | Float | -1.0 |
| 32 | ShaderGraphParam | Float | -1.0 |
| 33 | CameraRumble | UInt32 | -1 |
| 34 | DistanceAttenuate | UInt32 | 1 |
| 35 | CameraRumbleFrame | UInt32 | 0 |
| 36–39 | CtrlRumblePattern / Gain / Pitch / Stretch | | -1 / 1 / 1 / 1 |
| 40 | CtrlRumbleExtra | Bool | 0 |
| 41 | CullingDistance | Float | -1.0 |
| 42 | CtrlRumbleName | String | "" (bnvib) |
| 43 | CameraRumbleName | String | "" |

트리거 덮어쓰기(14): Delay, Bone, Scale, PositionX–Z, RotationX–Z, Red, Green, Blue, Alpha, EmissionRate.

**SLink** (user 8, asset 29 중 custom 9, trigger 9):

| 구분 | 파라미터 (기본값) |
|---|---|
| 사용자 | GroupName "", DistanceParamSetName "", LimitType(Enum 0), PlayableLimitNum -1, Priority 0.5, DopplerFactor -1.0, ArrangeGroupParams(Arrange), BitFlag 0 |
| 에셋 0–28 | AssetName, RuntimeAssetName(= BARS 안 사운드 이름), GroupName, Volume 1.0, VolumeTV 1.0, VolumeDRC -1.0, Pitch 1.0, Lpf 0.0, StartTimePos 0.0, StopFrame 0.0, FadeInTime 0.0, FadeType(Enum 0), Delay 0.0, Duration 0.0, Priority 0.5, DopplerFactor -1.0, StereoWidth 1.0, Bone "", DistanceParamSetName "", BitFlag 0, Shape "", DistCoef 10.0, Volume2 1.0, Pitch2 1.0, UseFriendCoef(Bool 1), UseOcclusion(Bool 1), SoundSourceSize 0.0, SpeakerBalanceType 0, Pan 0.0 |
| 트리거 덮어쓰기 | Volume, Pitch, Lpf, StartTimePos, StopFrame, FadeInTime, Delay, Priority, Bone |

### 3.4 ResParam (u32)

`value = raw & 0xFFFFFF`, `refType = raw >> 24` [참고, 데이터와 일치].

| refType | 이름 | value 의미 |
|---|---|---|
| 0 | Direct | directValue 인덱스(형은 ParamDefine type으로 해석) |
| 1 | String | 이름표 오프셋 |
| 2 | Curve | curve 표 인덱스 |
| 3 | Random | random 표 인덱스 (균등) |
| 4 | ArrangeGroup | 그대로 |
| 5 | Bitflag | 비트값 그대로 |
| 6–9 | Random2Pow / 3Pow / 4Pow / 1.5Pow | random 표 인덱스 |
| 10–17 | Random*PowWeightMin / WeightMax | random 표 인덱스 |

### 3.5 사용자 블록 (exRegion 안, 사용자 오프셋 기준)

| 오프셋 | 내용 |
|---|---|
| 0x00 | `u32 isSetup, numLocalProperty, numCallTable, numAsset, numRandomContainer, numActionSlot, numAction, numActionTrigger, numProperty, numPropertyTrigger, numAlwaysTrigger, pad` |
| 0x30 | `u64 triggerTablePos` (사용자 시작 기준) |
| 0x38 | `u64 localPropertyNamePos[numLocalProperty]` |
| | `u32 userParam[numUserParam]` (SLink 8개, ELink 0개) |
| | `u16 sortedCallTableIdx[numCallTable]` (키 이진 탐색용), 4 정렬 |
| | ResAssetCallTable × numCallTable (0x30 B, 3.6) |
| | 컨테이너 파라미터 영역 (콜 테이블 paramStartPos 기준) |
| triggerTablePos | ActionSlot[ ] 0x10 → Action[ ] 0x10 → ActionTrigger[ ] 0x28 → Property[ ] 0x18 → PropertyTrigger[ ] 0x20 → AlwaysTrigger[ ] 0x18 |

### 3.6 레코드

**ResAssetCallTable (0x30)**

| 오프셋 | 타입 | 필드 | 비고 |
|---|---|---|---|
| 0x00 | u64 | keyNamePos | 이름표 기준 |
| 0x08 | s16 | assetId | 컨테이너면 -1 |
| 0x0A | u16 | flag | bit0 = 컨테이너 |
| 0x0C | s32 | duration | 재생 횟수. 컨테이너의 자식이 끝날 때마다 >0 이면 1 감소, 0 이 아니면 다시 start(-1 = 무한 반복) [판독 0x710389250c]. 분포: ELink 전부 1(5,733), SLink 1 21,142 / -1 233 / 2·3·6 각 2 [데이터]. ※ 1차 문서의 "전부 1"은 SLink를 세지 않은 오류라 정정 |
| 0x10 | s32 | parentIndex | 최상위 -1 |
| 0x14 | u32 | guid | |
| 0x18 | u32 | keyNameHash | CRC32(key) |
| 0x1C | u32 | pad | |
| 0x20 | s64 | paramStartPos | 에셋: 에셋 파라미터 표 시작 기준 / 컨테이너: 컨테이너 영역 기준, -1 없음 |
| 0x28 | s64 | conditionPos | 조건표 기준, 0xFFFFFFFF 없음 |

**컨테이너 파라미터**: `u8 type, u8 blendMode, u16 pad, s32 childStart, s32 childEnd, u32 pad` (0x10). 자식 범위는 콜 테이블 인덱스 [start, end] 양끝 포함. type 은 **u8**입니다(생성 함수 `0x710388e468`이 `ldrb`로 읽고 점프 표 `0x7104af2b9c`로 분기) [판독].

| type | 이름(웹 권장) | vtable(+0x10 적용) | start / calc | 근거 |
|---|---|---|---|---|
| 0 | Switch | 0x7105736890 | 0x7103897e1c / 0x71038976d4 (선택 0x71038978bc) | [판독] |
| 1 | Random | 0x7105736748 | 0x71038925a0 / 0x710389250c | [판독] |
| 2 | Random2 | 0x71057367a8 | 0x7103892874 / 0x710389250c | [판독] |
| 3 | Blend (blendMode 0) / 값 블렌드 (blendMode≠0) | 0x7105736608 / 0x71057365a8 | 0x710388f59c / 0x710388e8fc (선택 0x710388ea98) | [판독]. 데이터의 Blend 637개는 전부 blendMode 0 [데이터] |
| 4 | Sequence | 0x7105736830 | 0x7103897644 / 0x71038972fc | [판독] |
| 5 | **Grid** (2차원 표) | 0x7105736688 | 0x7103890ca4 (선택 0x71038909a4) | [판독]. ELink 32개, SLink 158개 사용 [데이터] |
| (컨테이너 아님) | 에셋(Mono) | 0x71057366e8 | 0x710389214c 등 | [판독: 생성 분기만] |

※ 정정: 1차 문서와 파서는 type 5를 Splatoon 2 참고 소스대로 `Asset`이라 했지만, 이 게임의 5는 두 속성 값으로 자식을 고르는 표 컨테이너입니다. 근거는 위 생성 분기와 선택 함수, 그리고 type 5 레코드 190개의 표 값 1,616칸이 전부 자식 범위 안(빈칸 -1 179칸)이라는 데이터 검사입니다(`effect_xlink.py` 갱신).

Switch(type 0)는 이어서 `u64 watchPropertyNamePos(+0x10), s32 watchPropertyId(+0x18), s16 localPropertyNameIdx(+0x1C), u8 isGlobal(+0x1E), u8 watchActionSlot(+0x1F)` (총 0x20). **watchActionSlot ≠ 0**이면 속성 대신 이름이 `watchPropertyNamePos`인 **액션 슬롯**(예 `Skl[0]`, `HFSM[0]`)의 현재 액션 번호를 조건 `+8` 정수와 비교합니다. 비교는 0(==)과 5(!=)만 합니다 [판독 0x71038978bc, 데이터: ELink 27개, SLink 32개].

Grid(type 5) 레코드 [판독 0x71038909a4 + 데이터]:

| 오프셋 | 타입 | 내용 |
|---|---|---|
| +0x10 / +0x18 | u64 | 속성1 / 속성2 이름표 오프셋 |
| +0x20 / +0x22 | s16 | 속성1 / 속성2 로컬 속성 이름 인덱스(전역이면 -1) |
| +0x24 | u16 | bit0 = 속성1 전역, bit1 = 속성2 전역 |
| +0x26 / +0x27 | u8 | 값 개수 n1 / n2 |
| +0x28 | u32[n1+n2] | 속성 값. 전역이면 이름표 오프셋(열거 이름), 로컬이면 `localPropertyEnumNameRef` 인덱스 |
| 뒤 | s32[n1·n2] | 자식 콜 테이블 인덱스, 행 = 속성1 값 순서, 열 = 속성2 값 순서. -1 = 없음 |

예: SLink `BulletPointSensor` / `OnActivate` = SpecMode(전역) × SubjectiveType. Versus·Mission·Other에서 Friend는 -1(무음), Coop에서 Friend는 Focused와 같은 자식입니다 [데이터].

**ActionSlot (0x10)**: `u64 namePos, s16 actionStart, s16 actionEnd, pad`.
**Action (0x10)**: `u64 namePos, s32 triggerStart, s32 triggerEnd`.

**ActionTrigger (0x28)**

| 오프셋 | 타입 | 필드 | 분포(ELink 1,267 / SLink 2,548) |
|---|---|---|---|
| 0x00 | u32 | guid | |
| 0x04 | u32 | 0 | 전부 0 |
| 0x08 | u64 | assetCtbPos | 콜 테이블 배열 시작 기준 바이트(= 인덱스×0x30) |
| 0x10 | s32 / u64 | startFrame, **flag bit4(0x10)일 때는 u64 이름표 오프셋 = 직전 액션 이름** | 대부분 0. 예: SLink `Stop` 액션의 트리거가 `Move`/`Rotate` 이름을 가리킴 → "Move→Stop 전환 때만" |
| 0x14 | s32 | 0 | 전부 0 |
| 0x18 | s32 | endFrame | 0x7FFFFFFF(액션 끝까지) 91–97%, 그 밖 유한값 |
| 0x1C | u16 | flag | 0, 1, 4, 5, 8, 0x10 등 |
| 0x1E | u16 | 파일 공통 값 | ELink 0x4c8d, SLink 0x081f 가 대부분 [미확정] |
| 0x20 | s32 | overwriteParamPos | -1 없음, 아니면 덮어쓰기 표 기준 |
| 0x24 | u32 | pad | |

**Property (0x18)**: `u64 watchPropertyNamePos, s32 isGlobal, s32 triggerStart, s32 triggerEnd, pad`.
**PropertyTrigger (0x20)**: `u32 guid, u16 flag, u16 (공통 값), u64 assetCtbPos, u64 conditionPos, s32 overwriteParamPos, pad`.
**AlwaysTrigger (0x18)**: `u32 guid, u16 flag, u16 (공통 값), u64 assetCtbPos, s32 overwriteParamPos, pad`.

flag 비트 의미는 이 게임의 ActionTriggerCtrl 코드로 판독했습니다. §4.4를 보세요 [판독]. (1차의 참고 소스 해석 "bit1 재발생 억제, bit4 관찰 필요"는 이 게임 코드와 다릅니다: bit4는 직전 액션 이름 조건이고, bit1은 이 함수들에서 쓰이지 않습니다.)

### 3.7 조건 레코드 (조건표)

| 형 | 크기 | 배치 |
|---|---|---|
| Switch, Enum 속성 | 0x18 | `s32 parentType(0)`, `u8 propertyType(0)`, `u8 compare`, `u8 isSolved`, `u8 isGlobal`, `s32 localPropertyEnumNameIdx`, `u32 pad`, `u64 값 = 이름표 오프셋(열거 이름)` |
| Switch, S32/F32 속성 | 0x10 | `s32 0`, `u8 propertyType(1 S32 / 2 F32)`, `u8 compare`, `u8`, `u8 isGlobal`, `s32 idx(-1)`, `s32 또는 f32 값` |
| Random/Random2 | 0x08 | `s32 parentType(1/2)`, `f32 weight` |

**compare 번호** [판독: Switch 자식 선택 `0x71038978bc`] — 비교식은 **(속성 현재값) OP (조건값)** 입니다.

| 번호 | 연산 | 디스어셈블 근거(정수형 분기) |
|---|---|---|
| 0 | == | `0x7103897bf8: cmp w10,w5; b.eq 일치` |
| 1 | > | `0x7103897d40: cmp w10,w5; b.le 불일치` |
| 2 | >= | `0x7103897d4c: b.lt 불일치` |
| 3 | < | `0x7103897d58: b.ge 불일치` |
| 4 | <= | `0x7103897d64: b.gt 불일치` |
| 5 | != | `0x7103897d70: b.eq 불일치` |

- 감시 속성의 정의 형(속성 정의 +0x60)이 0(Enum)·1·3·4이면 32비트 **정수 비교**, 2·5면 **float 비교**(`fcmp`)입니다. 3·4·5는 값이 포인터로 연결된 참조형(3 = u8, 4 = s32, 5 = f32)입니다 [판독].
- 로컬 Enum 조건은 로드 때 이름을 번호로 풀어 둔 표(사용자 리소스 +0x80의 s16, 자식 인덱스별)와 비교합니다. 전역 Enum은 조건 +8의 정수와 비교합니다 [판독].
- 사용자 인스턴스별 속성 덮어쓰기 목록(시스템 +0xC0부터 8 B 노드 `{s16 next, u16 propIdx, f32 value}`, 시작 인덱스 = 인스턴스 +0x60)이 있으면 그 값이 먼저입니다 [판독].
- 1차 문서의 1–4 추정(Splatoon 2 열거형을 뒤집은 순서)은 판독 결과와 같습니다. 근거 수준만 [추정]→[판독]으로 올립니다.

## 4. 실행 규칙

### 4.1 이 게임 코드에서 확인한 것 [판독]

| 주소 | 내용 |
|---|---|
| 0x7103e1e37c | xlink 컴포넌트(이하 XC)의 키 방출: `mode 0` → XC+0x78(ELink 사용자 인스턴스)만, `mode 1` → XC+0x80(SLink)만, `mode 2` → 둘 다. 각각 searchAndEmit 호출 뒤, 인스턴스가 처음 활성화되면(+0x100 참조 카운트 0→1) 전역 calc 큐(ring buffer)에 넣음. SLink 쪽 출력 핸들은 `handle+0x10` |
| 0x7103e1e5d0 / 0x7103e1e61c | XC의 ELink만 / SLink만 searchAndEmit 하는 단축 함수. 액터 +0x520의 16 B 래퍼(vtable 0x71055408b0, 생성 0x7100f765bc, `{vtable, XC}`)가 슬롯 2·3으로 이것을 부름. 슬롯 0 = 0x7100f797bc(키, mode), 슬롯 1 = 0x7100f797dc |
| 0x710389e6e8 | **searchAndEmit(instance, key, outHandle, 0)**: 시스템 호출 허용(+0x98) 확인 → 로그 판정 → 사용자 리소스(+0x38→+0x18)의 정렬 인덱스 표(u16)로 키 이름 **이진 탐색**(`strcmp` 0x7103e9a240) → 찾으면 emit(0x710389e90c). 없으면 아무것도 안 함 |
| 0x710388e468 | 컨테이너 생성: 콜 테이블 flag bit0이 컨테이너면 파라미터 +0 u8 type으로 위 표의 클래스, 아니면 에셋 컨테이너. 생성 뒤 initialize(vt+0x10)에 콜 테이블과 가중치 f32 전달 |
| 0x71038978bc | Switch 자식 선택: §4.2 |
| 0x7103888b04 | ResParam 값 해석(refType 분기 0..17): §4.3 |
| 0x710389b61c | 액션 변경: (TriggerCtrlMgr = 인스턴스+0x98, 액션 이름, 시작 프레임, 슬롯 번호). 슬롯의 ActionTriggerCtrl에 `0x71038964b8`로 이름을 넘기고, 그 액션이 관찰 필요 액션이면 관리자 +0x18 비트마스크의 슬롯 비트를 켬 |
| 0x7102865628 | 무기 장착 시 `OnAttach` 키를 mode 2로 방출(→ SLink `OnAttach_00` = `Wp_Shooter_Attach_00`) |
| 0x7102864594 | `InkActionID::FireImpact` 같은 열거형 문자열에서 `::` 뒤를 잘라 무기 +0x318 상태 이름 표(+0x358 버퍼, +0x350 개수)를 만듦 |
| 0x7102864104 | 무기 InkAction 변경([effect_sound.md](effect_sound.md) §3.2): 새 액션이면 이름 표에서 이름을 꺼내 XC+0x78(ELink)·XC+0x80(SLink) 양쪽 TriggerCtrlMgr에 `0x710389b61c(mgr, 이름, (int)무기+0x324, 슬롯 0)` |
| 0x710280919c | 사용자에게 로컬 속성 인덱스를 이름으로 물어 저장: Enum 속성(vt+0x288) `SubjectiveType`→+0x52, `StandAloneType`→+0x53, F32 속성(vt+0x290) `MuzzleShotDirXZDot`→+0x5e, `OpenRt`→+0x5f. 이 객체(0x68 B, 생성 0x7102809354, vtable 0x710564c298 슬롯 16)는 +0x28에 대상 인스턴스를 둠 |
| 0x71028089c0 | 위 F32 속성 정의(static init): 범위 -1.0..1.0 |
| 0x71027b5980 | HitEffect 조합표 로더: 사용자 이름 `HitEffect`, 속성 `SubjectiveType` 사용 ([effect_resources.md](effect_resources.md) §4) |

### 4.2 컨테이너 규칙 [판독]

- **Switch** (`0x71038978bc`): 자식을 childStart→childEnd 순서로 봅니다. **조건이 없는 자식(conditionPos 0)을 만나면 그 자리에서 바로 고릅니다.** 조건이 있으면 §3.7 비교가 참인 첫 자식을 고릅니다. 아무것도 없으면 시작 실패입니다. 1차 문서의 "조건 없는 자식 = 기본값(마지막)" 추정은 데이터에서 무조건 자식이 거의 항상 마지막(2,066개 중 2,061개)이라 결과가 같습니다. 예외 5개(자식 전부 무조건)는 **첫 자식**이 선택됩니다.
- **Switch calc** (`0x71038976d4`): 감시 속성이 바뀌어 선택 결과가 달라지면 현재 자식을 끄고 새 자식을 시작합니다(참고 소스와 같은 구조, 세부 페이드 조건은 미판독).
- **Random** (`0x71038925a0`): 자식 조건 weight(조건 +4 f32) 합 W. W ≤ 0이면 실패. `r = W·(f − 1)` (f = sead xorshift128 출력 `(u>>9)|0x3F800000`을 float로 본 값, 시스템 +0x908..+0x914 상태). 누적 weight가 **r보다 큰** 첫 자식을 고릅니다.
- **Random2** (`0x7103892874`): Random과 같되, 자식이 2개 이상이면 **직전에 고른 자식을 후보와 가중치 합에서 뺍니다**. 직전 선택은 사용자 인스턴스(+0xF8 bit0으로 고른 +0x28/+0x30 객체)의 `{컨테이너 콜 테이블 번호, 선택 번호}` 표에 저장합니다(없으면 빈 칸에 추가). 1차 문서 [미확정] → [판독].
- **Blend** (`0x710388f59c`, blendMode 0): 자식 전부를 시작합니다. 하나라도 시작되면 성공. **값 블렌드**(blendMode ≠ 0, `0x710388e8fc`/`0x710388ea98`)는 감시 속성 값이 자식 조건 `[min(+4), max(+8))` 안에 드는 자식 둘을 골라 곡선(+0xC 들어감 / +0xD 나감: 0 선형, 1 제곱, 2 제곱근, 3 sin(x·π/2), 4 min(2x,1), 5 1)으로 가중치를 줍니다. 이 게임 데이터에는 없습니다.
- **Sequence** (`0x7103897644`, `0x7103897488`, calc `0x71038972fc`): 현재 순번(+0x30, 처음 -1)을 1 올리며 자식을 하나 시작합니다. 시작에 실패한 자식은 건너뜁니다. 자식이 끝나면 다음 자식으로 넘어가고, 끝까지 가면 duration 규칙으로 처음부터 반복하거나 끝납니다.
- **Grid** (`0x7103890ca4` → `0x71038909a4`): 속성1·속성2의 현재 값을 각 값 목록에서 찾아(목록에 없으면 실패) 표 칸의 자식 하나를 시작합니다. 칸이 -1이거나 자식 범위 밖이면 실패입니다.
- **duration** (`0x710389250c` 등 calc 공통): 자식이 끝나면 `duration > 0`일 때 1 줄이고, 0이 아니면 같은 컨테이너를 다시 start합니다. 그래서 1 = 한 번, -1 = 무한 반복입니다.

### 4.3 값 해석 `0x7103888b04` [판독]

| refType | 계산 |
|---|---|
| 0 Direct | directValue 표 f32 |
| 2 Curve | 아래 커브 규칙. 커브의 속성 인덱스 < 0이거나 속성이 없으면 +∞를 돌려주고 호출자가 처리 |
| 3 Random | `min ≤ max`이면 `min + (max − min)·r`, 아니면 `min` |
| 6–9 RandomNPow (N = 2, 3, 4, 1.5) | `h = abs(max − min)/2`, `u = 2r − 1`, `min + h + sign(u)·h·abs(u)^N` (N=2는 `u²`, 나머지 `powf`) |
| 10–13 WeightMin | `min + abs(max − min)·r^N` (N=2는 `r²`) |
| 14–17 WeightMax | `min + abs(max − min)·(1 − r^N)` |

`r`은 모두 같은 xlink 시스템 난수기(xorshift128)의 `[0,1)` float입니다. 호출 순서를 원본과 맞출 근거는 없으므로 웹은 아무 난수기나 씁니다(연출값). 1차 문서의 [참고] 식은 판독 결과와 같습니다. 단 Random(3)의 `min > max`일 때 `min` 고정은 새로 확인한 것입니다.

**Curve** (커브 호출 표 0x18 B: `u16 pointStart, u16 numPoint, u16 curveType, u16 isPropGlobal, u64 propName, s32 propIdx, s16 localPropertyNameIdx`):
- 속성 값 x: isPropGlobal == 1이면 전역 속성, 아니면 로컬 속성(인스턴스 덮어쓰기 목록 우선). 정의 형이 0·1·3·4(정수형)이면 정수를 float로 바꿉니다.
- `curveType == 0`이고 점이 있으면: 점 i를 앞에서부터 봅니다. `x == xᵢ`이면 다음 점의 x도 같을 때 **다음 점의 y**(계단), 아니면 yᵢ. `x < xᵢ`이면 i = 0일 때 y₀, 아니면 (xᵢ₋₁, yᵢ₋₁)–(xᵢ, yᵢ) **선형 보간** `yᵢ₋₁ + (x − xᵢ₋₁)·((yᵢ − yᵢ₋₁)/(xᵢ − xᵢ₋₁))`. 끝까지 못 찾으면 마지막 점 y.
- `curveType ≠ 0`이면 마지막 점 y입니다. 데이터의 커브 338개(ELink 131, SLink 207)는 전부 curveType 0입니다 [데이터]. sead 곡선 평가표(0x7105738610)와는 별개입니다.
- 머즐 플래시 Delay 커브 (0.75→2.0), (1.0→0.0)은 그래서 x ≤ 0.75면 2.0, 1.0 이상이면 0, 사이 선형입니다 [판독+데이터]. 1차 문서 [추정] → [판독].

### 4.4 액션 트리거 실행 규칙 [판독]

디컴파일: `analysis/decomp/vfx/vfx_b1.c`(0x71038964b8), `snd_xlink_b1.c`(0x7103896874, 0x7103895f64, 0x710389662c).

**액션 변경** `0x71038964b8(ctrl, 이름, 시작 프레임)` (ctrl = ActionTriggerCtrl, 슬롯마다 하나):
1. 슬롯의 액션 목록에서 이름을 찾습니다(`strcmp`, 일부는 직접 비교).
2. ctrl+0x20에 **새 이름의 CRC32**를 저장하고, 직전 값을 따로 둡니다(아래 bit4 조건에 씀).
3. 못 찾으면 `0x710389662c`(현재 액션의 이벤트를 정리)만 합니다.
4. 찾았는데 **현재 액션(ctrl+0x30)과 같으면 아무것도 하지 않습니다**(재시작 없음).
5. 다르면 `0x7103896874(ctrl, 새 액션, 시작 프레임, 직전 CRC)`.

**새 액션 시작** `0x7103896874` — 새 액션의 트리거마다 상태(인스턴스별 0x28 B: +0x10 이벤트 핸들, +0x18 세대, +0x24 발생함, +0x25 넘겨줌, +0x26 이름 조건 일치)를 0으로 지우고 flag로 종류를 나눕니다.

| flag | 종류 | 시작 시 동작 |
|---|---|---|
| bit2 (0x4) | 액션 시작 | 무조건 방출 |
| bit3 (0x8), bit2 없음 | 액션 종료 | 시작 시에는 방출하지 않음. 직전 액션의 이런 트리거는 이 시점에 "종료 발생" 표시(`(flag & 0xC) == 8`) |
| bit4 (0x10) | 직전 액션 조건 | 트리거 +0x10의 이름 CRC32가 **직전 액션 이름 CRC32**와 같을 때만 방출 |
| 그 밖 | 프레임 범위 | 에셋 속성 바이트(+2) bit1이 켜져 있으면 `startFrame <= 시작 프레임 < endFrame`, 아니면 `startFrame == 시작 프레임`일 때 방출. bit1을 "반복형 에셋"으로 보는 것은 [추정] |
| **bit0 (0x1)** | 넘겨받기 | 방출하기 전에 **직전 액션의 트리거 중 같은 에셋(assetCtbPos)을 이미 발생시킨 것(+0x24)이 있으면, 그 이벤트 핸들을 넘겨받고(살아 있으면) 새로 방출하지 않습니다.** 이벤트가 이미 끝났어도 방출하지 않습니다 |

넘겨받지 않은 직전 액션의 이벤트는 끝에서 정리됩니다(이벤트 +8 |= 0x90, 페이드) [판독-부분: 함수 뒷부분].

**매 프레임** `0x7103895f64` [판독-부분: 분기 대부분은 읽었고 종류별 건너뛰기 조건 일부는 정리하지 않음] — ctrl+0x24 = 현재 액션 프레임, +0x28 = 직전 프레임. 트리거마다:
- 프레임 범위 트리거(종류 0)와 bit4 일치 트리거: 에셋 bit1이면 `start <= 현재 < end`이고 이벤트가 죽어 있을 때 다시 방출합니다. 아니면 `직전 < start <= 현재 < end`일 때(시작 프레임을 지나는 순간) 한 번 방출합니다. bit0이고 이미 발생했으면(+0x24) 방출하지 않습니다.
- `직전 < end <= 현재`이면 이벤트를 끕니다(+8 |= 0x90).
- 프레임이 뒤로 갔으면(현재 < 직전) bit0이 아닌 발생한 트리거의 이벤트를 끕니다.

**상시 트리거**는 참고 소스대로 인스턴스 활성 동안 이벤트가 없으면 다시 방출한다고 봅니다 [참고]. 이 게임의 상시 트리거 calc는 판독하지 않았습니다.

웹 구현(액션 슬롯):

```ts
changeAction(slot: Slot, name: string, startFrame: number) {           // 0x71038964b8
  const act = slot.actions.find(a => a.name === name);
  const prevCrc = slot.nameCrc; slot.nameCrc = crc32(name);
  if (!act) { slot.stopAll(); return; }
  if (slot.current === act) return;                                       // 같은 액션: 재시작 없음
  for (const tr of act.triggers) {
    tr.state = { handle: null, fired: false, handed: false };
    const kind = tr.flag & 4 ? 'start' : tr.flag & 8 ? 'end' : tr.flag & 0x10 ? 'prev' : 'frame';
    let fire = kind === 'start' || (kind === 'prev' && crc32(tr.prevActionName) === prevCrc)
      || (kind === 'frame' && (tr.asset.loop ? tr.start <= startFrame && startFrame < tr.end : tr.start === startFrame));
    if (tr.flag & 1) {                                                    // 넘겨받기
      const old = slot.current?.triggers.find(o => !o.state.handed && o.assetCtb === tr.assetCtb && o.state.fired);
      if (old) { old.state.handed = true; tr.state.handle = old.state.handle; old.state.handle = null; tr.state.fired = true; fire = false; }
    }
    if (fire) { tr.state.handle = emit(tr); tr.state.fired = true; }
  }
  slot.current?.triggers.forEach(o => { if (!o.state.handed) o.state.handle?.fadeOut(); });
  slot.current = act; slot.frame = startFrame;
}
```

## 5. 웹 구현 — XLink 디스패처

```ts
// 원본 대응: XC(+0x78 ELink, +0x80 SLink) ~ XLinkComponent, UserInstance ~ XLinkUserInstance
interface XLinkUser { callTables: CallTable[]; actionSlots: Slot[]; actions: Action[];
                      actionTriggers: ActionTrigger[]; properties: Prop[]; propertyTriggers: PropTrigger[];
                      alwaysTriggers: AlwaysTrigger[]; localProperties: string[]; userParams: Record<string, any>; }

class XLinkUserInstance {
  props = new Map<string, number|string>();     // 로컬 속성(SubjectiveType 등) + 전역 속성 참조
  constructor(public user: XLinkUser, public sink: AssetSink /* EffectPlayer | SoundPlayer */) {}

  searchAndEmit(key: string, handleOut?: Handle) {   // 0x710389e6e8 대응
    const root = this.user.callTables.find(c => c.parent === -1 && c.key === key);
    if (!root) return false;                            // 키 없음 = 조용히 무시
    this.run(root, handleOut); return true;
  }
  private run(ct: CallTable, h?: Handle) {
    if (!ct.container) { this.sink.play(resolveParams(ct.params, this.props, rng), h); return; }
    const kids = range(ct.container.children).map(i => this.user.callTables[i]);
    switch (ct.container.type) {
      case 'Switch':  { const v = this.props.get(ct.container.watchProperty);   // 0x71038978bc
                        const c = kids.find(k => !k.condition || compare(v, k.condition)); if (c) this.run(c, h); break; }
      case 'Random': case 'Random2': {                                         // 0x71038925a0 / 0x7103892874
                        const excl = ct.container.type === 'Random2' && kids.length > 1 ? this.lastPick.get(ct.i) : undefined;
                        const cand = kids.filter(k => k.i !== excl), W = cand.reduce((a, k) => a + k.condition.weight, 0);
                        if (W <= 0) break; const r = W * rand(); let acc = 0;
                        for (const k of cand) { acc += k.condition.weight; if (r < acc) { this.lastPick.set(ct.i, k.i); this.run(k, h); break; } }
                        break; }
      case 'Grid':    { const g = ct.container, a = g.values1.indexOf(this.props.get(g.props[0])),   // 0x71038909a4
                        b = g.values2.indexOf(this.props.get(g.props[1]));
                        const ci = a < 0 || b < 0 ? -1 : g.table[a][b]; if (ci >= 0) this.run(this.user.callTables[ci], h); break; }
      case 'Blend':   kids.forEach(k => this.run(k, h)); break;
      case 'Sequence': /* 끝나면 다음: sink 의 onEnd 콜백으로 진행 */ break;
    }
  }
  changeAction(slot: string, name: string) { /* 4.2 액션 규칙, 매 프레임 calc() 에서 frame 증가 */ }
}
function emitXLink(xc: XLinkComponent, key: string, mode: 0|1|2) {   // 0x7103e1e37c
  if (mode !== 1) xc.elink?.searchAndEmit(key);
  if (mode !== 0) xc.slink?.searchAndEmit(key);
}
```

- 사용자 데이터는 빌드 때 `effect_xlink.py dump` JSON을 사용자별로 잘라 씁니다. 이름이 없는 사용자는 `#crc32` 키로 둡니다.
- 비교는 `compare(속성값, 조건)` = §3.7 표(0 ==, 1 >, 2 >=, 3 <, 4 <=, 5 !=)를 그대로 씁니다 [판독].
- 컨테이너가 끝날 때 duration 규칙(§4.2)으로 반복합니다. SLink의 duration -1(233개)은 루프 사운드입니다. 원샷 에셋만 즉시 재생하는 단순 구현이면 이 233개를 따로 처리해야 합니다.
- `lastPick`(Random2 직전 선택)은 사용자 인스턴스마다 둡니다(원본은 인스턴스 +0x28/+0x30 객체의 표).

## 6. 검증

| 검증 | 방법 | 결과 |
|---|---|---|
| 형식 전수 | `effect_xlink.py check` 두 파일 | 표 경계 3곳 일치, 사용자 경계 429+733 일치, 키 CRC 불일치 0, 트리거 참조 오류 0 [실행: 자체 파서] |
| 사용자 이름 = CRC32 | WeaponShooterNormal 0x171e020d가 두 파일 정렬표에 있음 | 일치 [실행] |
| 평가기 | `effect_xlink_eval.py --selftest` (결과 `analysis/effect_sound/selftest_xlink_eval.txt`) | 26항목 PASS [합성 테스트: §4.2/4.3 판독 규칙의 재구현이며 원본 실행 아님]. 추가 7항목 = Grid 4(BulletPointSensor SpecMode×SubjectiveType), Random2 연속 중복 0회(水没 2000회), Curve 계단·선형·끝값 |
| Grid 표 | 190개 레코드, 1,616칸 | 자식 범위 밖 0, 빈칸 -1 179 [실행: 자체 파서] |

## 7. 미확정

| 항목 | 상태 | 다음 근거 |
|---|---|---|
| compare 1–4, Switch 순서, Curve 보간, Random2, duration | **해소** [판독] (§3.7, §4.2, §4.3) | — |
| 트리거 flag 비트 | **해소** [판독] §4.4: bit0 같은 에셋 넘겨받기, bit2 시작, bit3 종료, bit4 직전 액션 이름. bit1은 이 경로에서 안 씀 | 액션 종료(bit3) 방출 위치, 상시 트리거 calc |
| 액션 변경 뒤 트리거 발생 규칙(같은 액션 재설정, startFrame/endFrame 처리) | **해소** [판독] §4.4 | 액션 프레임(ctrl+0x24)을 올리는 함수 |
| ActionTrigger +0x1E 공통 u16, numResParam 불일치 | [미확정] | 리소스 로더 |
| 값 블렌드(blendMode≠0) 조건 레코드 배치 | 판독했으나 데이터에 없음 | 필요 없음 |
| Switch calc 의 페이드 조건(관찰 필요 비트) | [미확정] | `0x71038976d4` 세부 |
