# 팀 컬러 — 데이터 → 4세트 × 14색 → 재질 파라미터

[목차](model_character.md)

## 1. 기능 개요

경기마다 고른 `TeamColorDataSet` 한 행(알파/브라보/찰리/중립 색)에서 팀마다 14가지 변형 색을 계산해 두고, 모델의 Hoian_UBER 재질마다 `my_team_color` 등 셰이더 파라미터에 넣습니다. 머리카락·눈썹·이빨·오징어 몸·탱크 잉크·무기 잉크통이 이 값으로 칠해집니다. 셰이더 안 혼합식은 BFSHA 역번역으로 확인했습니다 — §7.3, [shaders.md §3.6](shaders.md) [판독].

## 2. 자료

| 자료 | 내용 [데이터] |
|---|---|
| `RSDB/TeamColorDataSet.Product.100.rstbl.byml.zs` | 36행. 행 키 `Work/Gyml/<이름>.game__gfx__parameter__TeamColorDataSet.gyml`. 필드 `Alpha/Bravo/CharlieTeamColor`, `NeutralColor`(RGBA 0~1), `Alpha/Bravo/Charlie/NeutralHueOffset`, `HueOffsetEnable`(36행 모두 false), `Alpha/Bravo/CharlieUIColor`, `IsSetUIColor`, `Tag` |
| `Tag` 분포 | VersusRegular 10, Mission 10, Coop 7, Gambit 3, VersusTricolor 2, Blitz 1, CoopOption 1, MissionOption 1, VersusOption 1 |
| `Gyml/*.TeamColorDataSet.bgyml` (romfs 루트 24개) | 일부 행의 사본(예 GreenPurple은 RSDB와 Alpha 값이 다름 — 어느 쪽을 쓰는지 [미확정]) |
| `RSDB/TeamColorOffset` | 12행 (Brightness, Hue, Saturation): Bright(0.1,0,0) Dark(-0.2,0,0.5) HueBright(0.05,0.1,0) HueBrightHalf(0,0.05,0) HueDark(0.05,-0.1,0) HueDarkHalf(0,-0.05,0) Ink(-0.25,0,0) InkBright(0,0,0) InkLame(0.1,0,0) InkLameRare(0.05,0.1,0) Pale(0.1,0,-0.05) Silhouette(0,0,-0.6) |
| `SingletonParam` `game__gfx__parameter__TeamColorHueDirPeak` | BrightPeak 0.2, DarkPeak 0.72 |
| `SingletonParam` `game__gfx__InkColorCorrection` | `CorrectionInkMain{DownBrightnessLuminanceRate 0.5, DownBrightnessRate1 0.2, DownBrightnessRate6 0.55, MaxSaturation 0.99}` (MinBright는 데이터에 없음 → 기본 0.01) |

열거형(문자열 0x7104930012 근처 `main_strings` 30012행): `Tag` = `VersusRegular , VersusOption , Mission , MissionOption , VersusTricolor , VersusTricolorOption , Coop , CoopOption , Gambit , Blitz` (0..9) [데이터].

## 3. 호출 흐름 [판독]

```
TeamColorDataSet 행 ─ 0x7101176830(mgr, row, swap)
   ├ set0 = 0x71011743a0(hue0, mgr+0x2a8, swap ? Bravo : Alpha)
   ├ set1 = 0x71011743a0(hue1, mgr+0x398, swap ? Alpha : Bravo)
   ├ set2 = 0x71011743a0(hue2, mgr+0x488, Tag∈{4,5} ? Charlie : Neutral)
   └ set3 = 0x71011743a0(hue3, mgr+0x578, Neutral);  mgr+0x668 = Tag
0x71011743a0(s0=hueExtra, set, color): set+0xe0 = color(raw); lin = (powf(r,2.2), powf(g,2.2), powf(b,2.2), a)
   for i in 0..13: set+i*0x10 = 0x7101174534(s0, lin, i)
재질 적용: 모델 재질 방문자
   0x7101104258 (vtable 0x71055601b0): 공급자 0x71055601e8 → 0x710110451c = 전역(*0x7105793648)+0x560 + team*0xF0 의 [i]
   0x71011045e0 (vtable 0x7105560220): 공급자 0x7105560258 → 0x71011046a8 = 주어진 lin 색에서 즉석 계산(hueExtra 0)
     둘 다 → 0x7101103490(model, matIndex, Original lin, provider)
```

- 세트 구조(0xF0 B) [판독]: `+0x00 + i*0x10` = 색 i(RGBA f32, i=0..13), `+0xe0` = 원본 데이터 색(RGBA).
- `hueN` = `HueOffsetEnable ? <팀>HueOffset : 0`. 원본은 `swap`일 때 색만 바꾸고 hue0은 계속 Alpha의 HueOffset, hue1은 Bravo의 것을 씁니다(웹에서도 그대로) [판독: 0x7101176830 의 uVar7/uVar3 선택]. 현재 데이터는 전부 HueOffsetEnable=false라 관측 차이 없음.
- `swap` 인자 출처: 호출자 0x71026da7e0 에서는 전역 `+0x936` 바이트 [판독], 의미(내 팀이 Bravo인 경우 등)는 [추정].
- 플레이어 모델의 특수 경로(0x71026da7e0)는 모델 `+0x11c == 26000`이고 특정 조건일 때 다른 TeamColorDataSet 행을 찾아 세트를 만들고 0x7105560220 방문자로 칠합니다 — 조건 의미 [미확정].

## 4. 14색 정의 [판독]

이름표 문자열 0x7104928e72: `Original , Pale , Bright , Dark , HueBright , HueBrightHalf , HueDark , HueDarkHalf , Model , Ink , InkBright , InkLame , InkLameRare , Silhouette` (인덱스 0..13). 0x7101174534 가 이 이름으로 `Work/Gyml/<이름>.game__gfx__parameter__TeamColorOffset.gyml`(형식 `"Work/%s.%s.%s"`, `"Gyml/"+이름`, `"game__gfx__parameter__TeamColorOffset"`, `"gyml"`) 행을 찾습니다.

```
derive(hueExtra, lin, i):
  row = TeamColorOffset[name(i)]          // +8 Brightness, +0xc Hue, +0x10 Saturation (없으면 hue 0)
  hue = row.Hue; if |hue| > 1.1920929e-7: hue += (hue > 0 ? +hueExtra : -hueExtra)
  if i == 9 or i == 10: return inkCorrection(lin, P = 활성 env 의 DirectionalLight, bright = (i == 10))   // §5.3, 없으면 출력 안 씀
  if i == 8:            return inkCorrection(lin, P = {color 0, scale 0, flag 0}, bright = false) // "Model"
  if i == 0:            return lin
  if row 없음:          출력 안 씀(이전 값 유지)
  return hsvOffset(hue, row.Saturation, row.Brightness, lin)
```

`InkLame`/`InkLameRare`도 TeamColorOffset 행 그대로입니다(값이 Bright/HueBright와 같아서 결과도 같음) [데이터].

## 5. 계산식

### 5.1 hsvOffset — 0x7101188334(hueOff s0, satOff s1, brightOff s2, out x0, in x1) [판독]

```
// RGB → HSV (분기 없는 형태)
r,g,b = in.rgb; K = 0
if g < b: swap(g,b); K = -1
if r < g: swap(r,g); K = -1/3 - K
chroma = r - min(g,b)
h = clamp(|K + (g-b)/(chroma*6 + 1e-20)|, 0, 1)
s = clamp(chroma/(r + 1e-20), 0, 1);  v = r
// 색상 방향 반전 (TeamColorHueDirPeak 싱글턴 0x7101173e70, 로드된 경우만)
if BrightPeak(0.2) < h && h < DarkPeak(0.72): hueOff = -hueOff
s' = clamp(satOff - |brightOff| + s, 0, 1)
v' = (v + brightOff <= 0) ? 0 : v + brightOff        // 위쪽 클램프 없음
if s' == 0: out = (v', v', v', 1.0)                   // ★ 알파를 1로, RGB 클램프 없음
else:
  x = fmodf(h + hueOff, 1.0) / 0.16666667              // fmodf: 음수 유지
  i = fcvtzs(x) (0 쪽 버림); f = x - i
  p = v'(1-s'), q = v'(1-s' f), t = v'(1-s'(1-f))
  (R,G,B) = i==0:(v',t,p) 1:(q,v',p) 2:(p,v',t) 3:(p,q,v') 4:(t,p,v')  그 외(음수 포함, 부호 없는 비교 i>4):(v',p,q)
  out = (clamp01 R, clamp01 G, clamp01 B, in.a)
```

- `fmodf`·`powf`는 libc 임포트(GOT 0x710576fdc0, 0x710576fdd0)로 확인 [판독, `web/tools/paint_imports.py`].
- 특이점(그대로 재현할 것): ① s'==0이면 알파 1·RGB 비클램프, ② 음의 hue(예 빨강 + HueDark −0.1)는 감싸지지 않고 i=0, f<0 경로로 계산되어 G가 0으로 잘림, ③ 색상 오프셋 방향이 h∈(0.2,0.72)에서 뒤집힘(밝은 쪽 Hue는 노랑(~1/6) 쪽으로 이동하는 효과 [추정: 의도]).

### 5.2 inkCorrection — 0x7101174afc(out, in, P, _, bright) [판독, 필드 대응은 아래 표]

```
(h, s, v) = RGB→HSV(in)           // 5.1과 같은 식
Lf(Y) = Y >= 0.008856452 ? cbrt(Y) : Y*7.7870374 + 0.13793103      // powf(Y, 1/3)
L*(c) = 116*Lf(0.2126c.r + 0.7152c.g + 0.0722c.b) - 16
t    = P.scale(+0x18) * L*(P.color(+0x8..)) / 100  (+ L*(전역색 0x71058186e4..ec)/100  if P.flag(+0x1c))
dark = 1 - L*(in)/100
k    = clamp01(1 - M.LumRate * dark)
r    = clamp((6*M.Rate1 - M.Rate6)/5 + ((M.Rate6 - M.Rate1)/5) * t, 0, M.Rate6)    // t=1 → Rate1, t=6 → Rate6
d    = min(v, r*k)
if bright: d = d - S.BrightnessOffset * (1 - S.BrightnessOffsetLuminance * dark)   // InkBright 만 (0.1, 0.5)
v'   = max(clamp01(v - d), M.MinBright)
s'   = min(s, M.MaxSaturation)
out  = HSV→RGB(h, s', v')   // 5.1과 같은 변환·특이점(hueOff 0)
```

| 기호 | 출처 | 값 |
|---|---|---|
| M.LumRate/Rate6/Rate1/MaxSaturation/MinBright | InkColorCorrection 루트 +0x30 포인터 하위 구조 `+0x30/+0x38/+0x34/+0x3c/+0x40`(설정 플래그 +0x44..+0x48). 리플렉션 방문 함수 0x71011ae1dc, 생성자 0x71011ae104 기본값 0.35/0.5/0.1/1.0/0.01 [판독] | 데이터 CorrectionInkMain 0.5/0.55/0.2/0.99, MinBright 기본 0.01. 루트 +0x30 = CorrectionInkMain 이라는 대응은 [추정: 데이터 키가 이것 하나] |
| S.BrightnessOffset, S.BrightnessOffsetLuminance | 루트 +0x38 포인터 하위 구조 `game::gfx::InkColorCorrectionSSS`(`CorrectionInkSSS`) +0x30/+0x34. 생성자 0x71011af154 기본값 0x3dcccccd/0x3f000000, 리플렉션 0x71011af210 이 +0x30 `"BrightnessOffset"`, +0x34 `"BrightnessOffsetLuminance"` 등록 [판독] | **0.1 / 0.5** — SingletonParam 데이터에 `CorrectionInkSSS` 키가 없어 기본값 그대로 [판독+데이터] (InkBright 전용) |
| P (Model, i=8) | color (0,0,0), scale 0, flag 0 → t = 0 | r = (6·0.2−0.55)/5 = 0.13 |
| P (Ink/InkBright) | 활성 env 의 첫 `agl::env::DirectionalLight` — color = `DiffuseColor`(+0x128), scale = `Intensity`(+0x1a0), flag 1(하늘 SH 항 더함). §5.3 [판독] | 런타임(스테이지 조명) 값. 정정: 이전 판의 "도색 관리자"는 틀림 — `*0x71057907e8` 는 GOT 이고 가리키는 전역 0x71059a7838 은 env 관리자(+0x4bd0 타입별 색인표, +0x4be0 객체 배열)다 |

리소스가 로드되지 않았으면 MaxSaturation 1.0, MinBright 0.01과 전역 객체(*0x71057940a8 +0x2c/+0x38/+0x3c/+0x40/+0x44)의 값을 씁니다 [판독].

### 5.3 Ink(9)/InkBright(10) 의 조명 입력 — 0x7101174534 Ink 분기 [판독]

```
env = **(*0x71057907e8 + 0x48)            // 전역 0x71059a7838 의 +0x48 배열 [0] (활성 env 집합). 0 이면 return(출력 안 씀)
id  = *(s16*)0x7105999180                 // DirectionalLight 타입 ID (등록 0x71035d9320, 문자열 "DirectionalLight")
e   = env+0x4bd0 [id < env+0x4bc8 ? id : 0] // {u16 시작, u16 개수}
L   = e.개수 ? (env+0x4be0)[e.시작] : null  // 그 타입의 첫 객체
if L == null or !L->vt[0x48](typeInfo 0x7105814c50): return   // RTTI 확인(0x71035d8354), 실패 시 출력 안 씀
P = { vt 0x7105565778, color = L+0x128 (16 B), scale = *(f32*)(L+0x1a0), flag = 1 }
inkCorrection(out, lin, P, _, bright = (i == 10))
```

| 기호 | 정체 | 근거 |
|---|---|---|
| `L` | `agl::env::DirectionalLight` (vtable 0x7105723008, 객체 0x258 B, 팩토리 0x71035d8c60) | 0x71035d9320 이 이름 문자열과 함께 등록해 반환 ID 를 0x7105999180 에 저장, RTTI 확인 함수 0x71035d8354 가 같은 vtable 슬롯 +0x48 [판독] |
| `L+0x128` | 파라미터 `DiffuseColor`(파라미터 객체 +0x110, 값 +0x128 vec4, 기본 (1,1,1,1)) | 생성자가 이름 CRC32 를 즉석 계산(`D,i,f,f,u,s,e,C,o,l,o,r`) [판독] |
| `L+0x1a0` | 파라미터 `Intensity`(객체 +0x188, 값 +0x1a0, 기본 1.0) | 같은 생성자(`I,n,t,e,n,s,i,t,y`) [판독]. 다른 소비자(0x7101134c40)도 `Intensity × DiffuseColor` 를 광원 색으로 씀 |
| 하늘 항 | 전역 0x71058186e4 (vec4, 초기 (0,0,0,1)) = SH9 조도(0x7101033dc0, 7×vec4 형식 cAr/cAg/cAb/cBr/cBg/cBb/cC)를 **위쪽 (0,1,0)** 으로 평가한 값 | 팀색 관리자 생성자 0x710117649c 가 등록한 콜백 0x71011767f8 이 이벤트 객체 +0x18 의 SH 계수로 갱신 [판독]. 이벤트 종류(어느 시스템이 SH 를 보내는지)는 [미확정] |

```
t = Intensity · L*(DiffuseColor.rgb)/100 + L*(skyUp.rgb)/100            // §5.2 의 t (flag = 1)
r = clamp((6·Rate1 − Rate6)/5 + (Rate6 − Rate1)/5 · t, 0, Rate6) = clamp(0.13 + 0.07·t, 0, 0.55)
```

- 스테이지 조명 값의 출처: env 파라미터 접근자 두 클래스가 그룹 이름 `"MainLight"` 로 DirectionalLight 를 읽고 쓴다 — ID 0x53 get/set 0x710104d8e4/0x710104d9b4 = `Intensity`(+0x1a0, f32), ID 0x54 get/set 0x710104da84/0x710104db54 = `DiffuseColor`(+0x128, 16 B) [판독]. 스테이지 씬 팩의 `game__gfx__parameter__RenderingDay/Night/Sunset` 에 `Lighting.MainLight{Color, Intens, Latitude, Longitude, CubeMapIntens, IsUseCubeMapIntens}`(리플렉션 0x71011bc170: Color +0x30, CubeMapIntens +0x40, Intens +0x44, Latitude +0x48, Longitude +0x4c, IsUseCubeMapIntens +0x50)가 있어, `MainLight.Color → DiffuseColor`, `MainLight.Intens → Intensity` 로 들어간다. **[판독]으로 정정**: 렌더링 파라미터 적용 0x7102b5fe88 → 0x7102b5ff94 → 0x7102b607c4 가 env 첫 DirectionalLight 의 +0x128 = lerp(MainLight.Color), +0x1a0 = lerp(MainLight.Intens) 를 접근자를 거치지 않고 직접 쓰고, 0x7102b60ea0 이 +0x1c0 Direction = (−sin Lon·cos Lat, −sin Lat, −cos Lon·cos Lat) 를 쓴다([stage_rendering.md §4](stage_rendering.md)). 대전 로비(`LobbyVersusLockerTest.RenderingDay`)는 Color (0.6706, 0.8510, 1.0), Intens 10. 예: `Vss_Yagara` 낮(`Vss_YagaraDay00`) MainLight Color (0.902, 0.827, 0.616), Intens 6.0 [데이터] → 앞 항 6·L*/100 = 5.58.
- 기본 env 값 [데이터]: `Env/Default.Nin_NX_NVN.genvb.zs`(SARC) 안 `*/default*.baglenv`(AAMP v2, 이름 CRC32)를 `PY web/tools/render_aamp.py` 로 풀면 `DirectionalLight/DirectionalLight0`(name `Main`)이 하나씩 있다 — Day: DiffuseColor (1,1,1), Intensity 4.0, Direction (−0.3,−0.7,−0.6) / Sunset: (1, 0.889, 0.803), 4.0 / Night: (0.635, 0.466, 1.0), 0.1 / Viewer: (1, 0.95, 0.7), 4.0. 기본 낮이면 앞 항 = 4·100/100 = 4.0(r = 0.41 + 0.07·하늘 항). 스테이지 `MainLight`(예 Yagara Intens 6)가 이것을 덮는지는 위 [추정]에 달려 있다.
- **소비처** [판독]: 재질 파라미터에는 `my_team_color_type == "8"` 일 때만 Ink 가 들어가고(§6), 주된 소비처는 셰이더 사용자 블록 BlitzUBO0 이다 — 팀 세트 0/1/2 의 Ink/InkBright 가 data[3]/[4], [10]/[11], [62]/[63] 으로 복사되어 몸·옷에 묻은 잉크(2cl 분기)와 미니맵 셰이더 색으로 쓰인다([shaders.md §3.9](shaders.md)).
- **계산 시점**: 팀 세트를 만들 때(0x7101176830 → 0x71011743a0) 그 순간의 env 값으로 한 번 계산한다. env 나 DirectionalLight 가 없으면 Ink/InkBright 칸은 **쓰지 않고 이전 값이 남는다** [판독: 조기 return]. 조명이 바뀐 뒤 다시 계산하는 경로는 [미확정].
- 민감도: r 은 t ≥ 6 에서 0.55 로 포화한다. Yagara 낮 가정에서 앞 항만으로 t = 5.58(r = 0.520)이고, 하늘 항(L*/100)이 0.424 이상(위쪽 조도 휘도 Y ≥ 약 0.128)이면 포화한다. 하늘 SH 값은 런타임이라 미상이므로 이 스테이지의 r 은 **0.520 ~ 0.55** 범위다(Ink R 채널 기준 약 7% 차이) [재구현 계산 + 추정 입력]. 표는 §8.


## 6. 재질 파라미터 쓰기 — 0x7101103490 [판독]

대상: 셰이더 아카이브 이름이 `"Hoian_UBER"`인 재질만(문자열 비교). 공급자 `provider(i)`(vtable 슬롯 0)로 색을 얻어 이름 해시 + 이름으로 파라미터를 찾아 16 B를 씁니다(0x7101103a10).

| 파라미터 | 값 |
|---|---|
| `my_team_color` | provider(8) **Model** |
| `my_team_color_bright` | provider(2) Bright |
| `my_team_color_hue_bright` | provider(4) HueBright |
| `my_team_color_hue_bright_half` | provider(5) HueBrightHalf |
| `my_team_color_hue_dark` | provider(6) HueDark |
| `my_team_color_hue_dark_half` | provider(7) HueDarkHalf |
| `my_team_color_hue_complement` | hsvOffset(0.5, 0, 0, Original lin) |
| `my_team_color_dark` | **쓰지 않음**. main 문자열에 `my_team_color_dark`가 아예 없음(`main_strings.txt` 0건) → 런타임이 이 파라미터를 채우지 않고 파일 값(1,1,1,1)이 남는 것으로 봄 [데이터+추정] |

renderInfo `my_team_color_type`에 따른 덮어쓰기:

| 값 | 동작 |
|---|---|
| `"7"` | hue = renderInfo `my_team_color_hue_offset`(없거나 0이면 0), bo = `my_team_color_bright_offset`. 둘 다 0이면 그대로, 아니면 `my_team_color = hsvOffset(hue, 0, bo≠0 ? max(-1,bo) : 0, Original lin)` |
| `"10"` | `my_team_color_hue_complement = hsvOffset(hue_offset, 0, 0, Original lin)` |
| `"8"` | `my_team_color = provider(9)` (Ink) |

이어서 0x7101104258 경로에서 팀 인덱스가 0~2이고 renderInfo `enable_overlay_paint_on_emission == "2"`이면 `team_flag = (team==0, team==1, team==2)`(vec3 0/1)를 씁니다 [판독].

## 7. 웹 포팅 명세

### 7.1 모듈 (웹 권장 이름)

| 이름 | 입력 → 출력 |
|---|---|
| `TeamColorService.buildTeamSets(row, swap, envLight)` | TeamColorDataSet 행 → `[set0..set3]`, set = `{raw, linear, colors[14]}`. `envLight = {color: DirectionalLight.DiffuseColor, intensity, skyUp}`(§5.3)가 없으면 Ink/InkBright 칸은 비워 둔다(원본도 env 가 없으면 쓰지 않음) |
| `TeamColorService.materialParams(set, renderInfo)` | → `{my_team_color, ..., hue_complement}` (선형 RGBA) |
| `HoianMaterial.setTeam(params, teamIndex)` | 셰이더 유니폼 갱신, `team_flag` |

참조 구현: `web/tools/graphics_verify/teamcolor.mjs` (함수 `hsvOffset`, `inkCorrection`(Model·Ink·InkBright 공용, 0x7101174afc), `modelCorrection`, `deriveTeamColor`, `buildTeamSet`, `buildTeamSets`, `materialTeamParams`). 웹에서 스테이지 조명이 바뀌면 원본처럼 세트를 만들 때의 값으로 고정할지(원본 재계산 경로 [미확정]) 정해야 한다.

### 7.2 순서·정밀도

- 계산은 경기 시작(팀색 결정)·스왑 시 한 번. 매 프레임 아님 [추정: 호출자들이 초기화·설정 함수].
- 원본은 f32. JS는 double로 계산하므로 마지막 자리 오차가 날 수 있습니다. 비트 일치가 필요하면 연산마다 `Math.fround` [추정: 이 함수들에 FMA가 있는지 미확인].
- 색 공간: 데이터 색은 `powf(c, 2.2)`로 선형화한 뒤 모든 오프셋을 **선형 공간에서** HSV 처리합니다. 웹 셰이더에는 선형 값으로 넘깁니다.

### 7.3 셰이더 안 혼합식 [판독 — 셰이더 역번역, [shaders.md §3.6](shaders.md)]

샘플 36재질의 실제 프로그램(Hoian_UBER.Product)을 GLSL로 역번역한 결과입니다.

- `team_color_map_type = 2`: `k = clamp(Tcl.r + team_color_blend_alpha, 0, 1)`, `albedo = mix(base, my_team_color, k)`. `base`는 `enable_albedo_tex`가 1이면 `_a0` 텍스처, 0이면 `Mat.albedo_color`(눈썹: 0.0039 ≈ 검정).
- `team_color_map_type = 3`: 텍스처 없이 `k = clamp(team_color_blend, 0, 1)`, `albedo = mix(albedo_color, my_team_color, k)`(탱크 잉크 0.5, 무기 잉크병은 calc_color 결과에 `my_team_color`를 한 번 더 더함).
- `emission_color_type = 1`(머리카락): 방출 = 혼합된 albedo × `_e0`. `= 2`(눈썹·플레이어 팀색): 방출 색 = `my_team_color`.
- 투과 필름(`enable_transfilm`, 머리카락·오징어 몸): 필름 아래 색 = `(_re0.rgb + my_team_color_hue_complement) * under_film_color`.
- 샘플 프로그램 전체에서 쓰이는 팀색 uniform은 **`my_team_color`(63곳)와 `my_team_color_hue_complement`(9곳)뿐**입니다. `_bright`, `_hue_bright(_half)`, `_hue_dark(_half)`, `my_alpha/bravo/charlie_team_color`, `team_flag`는 샘플 재질 프로그램에서 읽지 않습니다(다른 옵션 조합 재질에서 쓰일 수 있음).
- 정정: 이전 근사(알베도가 없으면 `my_team_color * tcl`)는 원본과 다릅니다. 원본은 `mix(albedo_color, my_team_color, k)`이고, 눈썹은 albedo_color가 거의 0이라 결과가 비슷했을 뿐입니다.

## 8. 검증 — 재구현 계산 (원본 실행 대조 없음)

`node web/tools/graphics_verify/teamcolor_test.mjs OrangeBlue` → `analysis/graphics/teamcolor/OrangeBlue.json`. 행 OrangeBlue(VersusRegular): Alpha (0.8745, 0.4, 0.1451), Bravo (0.2078, 0.2353, 0.7725), Neutral (0.8039, 0.8039, 0.2039).

선형 RGB(소수 4자리):

| # | 이름 | set0 Alpha | set1 Bravo | set2 Neutral | set3 Neutral |
|---|---|---|---|---|---|
| 0 | Original | 0.7445, 0.1332, 0.0143 | 0.0316, 0.0415, 0.5668 | 0.6187, 0.6187, 0.0303 | 0.6187, 0.6187, 0.0303 |
| 1 | Pale | 0.8445, 0.2572, 0.1429 | 0.1371, 0.1469, 0.6668 | 0.7187, 0.7187, 0.1429 | 0.7187, 0.7187, 0.1429 |
| 2 | Bright | 0.8445, 0.2218, 0.1007 | 0.1038, 0.1142, 0.6668 | 0.7187, 0.7187, 0.1070 | 0.7187, 0.7187, 0.1070 |
| 3 | Dark | 0.5445, 0.0887, 0.0000 | 0.0000, 0.0068, 0.3668 | 0.4187, 0.4187, 0.0000 | 0.4187, 0.4187, 0.0000 |
| 4 | HueBright | 0.7945, 0.6191, 0.0550 | 0.0652, 0.4064, 0.6168 | 0.3072, 0.6687, 0.0661 | 0.3072, 0.6687, 0.0661 |
| 5 | HueBrightHalf | 0.7445, 0.3523, 0.0143 | 0.0316, 0.2020, 0.5668 | 0.4422, 0.6187, 0.0303 | 0.4422, 0.6187, 0.0303 |
| 6 | HueDark | 0.7945, 0.0000, 0.0550 | 0.3860, 0.0652, 0.6168 | 0.6687, 0.3072, 0.0661 | 0.6687, 0.3072, 0.0661 |
| 7 | HueDarkHalf | 0.7445, 0.0000, 0.0143 | 0.1822, 0.0316, 0.5668 | 0.6187, 0.4422, 0.0303 | 0.6187, 0.4422, 0.0303 |
| 8 | Model | 0.6421, 0.1149, 0.0123 | 0.0267, 0.0351, 0.4801 | 0.5013, 0.5013, 0.0245 | 0.5013, 0.5013, 0.0245 |
| 9 | Ink | 조명 의존 — 아래 표 | | | |
| 10 | InkBright | 조명 의존 — 아래 표 | | | |
| 11 | InkLame | 0.8445, 0.2218, 0.1007 | 0.1038, 0.1142, 0.6668 | 0.7187, 0.7187, 0.1070 | 0.7187, 0.7187, 0.1070 |
| 12 | InkLameRare | 0.7945, 0.6191, 0.0550 | 0.0652, 0.4064, 0.6168 | 0.3072, 0.6687, 0.0661 | 0.3072, 0.6687, 0.0661 |
| 13 | Silhouette | 0.7445, 0.5072, 0.4610 | 0.3716, 0.3752, 0.5668 | 0.6187, 0.6187, 0.4015 | 0.6187, 0.6187, 0.4015 |

Ink/InkBright 는 §5.3 의 조명 입력 t 의 함수다. `node web/tools/graphics_verify/teamcolor_ink_test.mjs OrangeBlue` → `analysis/render/teamcolor_ink_OrangeBlue.json` (t 를 흰색 광원 세기로 직접 넣음, 원본 실행 대조 없음 [재구현 계산]):

| t | r | set0 Ink | set0 InkBright | set1 Ink | set1 InkBright |
|---|---|---|---|---|---|
| 0 | 0.13 | 0.6421, 0.1149, 0.0123 (= Model) | 0.7209, 0.1290, 0.0139 | 0.0267, 0.0351, 0.4801 | 0.0304, 0.0400, 0.5468 |
| 1 | 0.20 | 0.5870, 0.1050, 0.0113 | 0.6658, 0.1191, 0.0128 | 0.0241, 0.0317, 0.4334 | 0.0278, 0.0366, 0.5001 |
| 3 | 0.34 | 0.4767, 0.0853, 0.0092 | 0.5555, 0.0994, 0.0107 | 0.0189, 0.0249, 0.3400 | 0.0226, 0.0297, 0.4067 |
| 5.58 (Yagara 낮, 하늘 항 0 가정) | 0.52 | 0.3347, 0.0599, 0.0064 | 0.4135, 0.0740, 0.0079 | | |
| ≥ 6 | 0.55 | 0.3114, 0.0557, 0.0060 | 0.3901, 0.0698, 0.0075 | 0.0111, 0.0146, 0.1999 | 0.0148, 0.0195, 0.2666 |

t = 0 의 Ink 가 Model 과 같은 것(같은 함수, 같은 P=0)으로 재구현 일관성을 확인했다. InkBright 는 `d` 에서 `0.1·(1 − 0.5·dark)` 를 빼므로 Ink 보다 밝다.

set0 `my_team_color_hue_complement` = (0.0143, 0.6256, 0.7445). Alpha HueDark/HueDarkHalf의 G=0은 §5.1 특이점 ②(음의 hue) 때문입니다.

경계 검사(같은 실행):

| 입력 | 결과 | 확인한 것 |
|---|---|---|
| hsvOffset(0.1, 0, 0.05, (0.5,0.5,0.5,0.7)) | (0.55, 0.55, 0.55, **1**) | s'=0 → 알파 1 |
| hsvOffset(0, 0, 0.5, (0.8,0.8,0.8,1)) | (**1.3**, 1.3, 1.3, 1) | s'=0 → 클램프 없음 |
| hsvOffset(−0.1, 0, 0.05, (0.8,0.1,0.1,1)) | (0.85, 0, 0.14875, 1) | 음의 hue → i=0, f<0 |
| hsvOffset(0.1, 0, 0, (0.1,0.8,0.1,1)) | h=1/3 → hueOff 반전 → (0.52, 0.8, 0.1, 1) | HueDirPeak 반전 |

조립 렌더(`analysis/graphics/shots/scene_assembled*.png`)에서 머리카락·눈썹·탱크·무기 잉크통·오징어 몸이 set0 Model 색(주황)으로 칠해지는 것을 확인했습니다 [실행: 재구현 렌더].

## 9. 미확정과 필요한 근거

| 항목 | 필요한 것 |
|---|---|
| ~~Ink(9)/InkBright(10) 값, S.a/S.b~~ | **해소(입력 경로)** — §5.3: P = 활성 env DirectionalLight(DiffuseColor·Intensity) + 하늘 SH 위쪽 조도, S = CorrectionInkSSS 기본 0.1/0.5. 남은 것: ① ~~스테이지 `RenderingDay.MainLight` 값이 들어가는 호출 경로~~ 해소(0x7102b607c4 직접 기록, §5.3), ② 하늘 SH 를 보내는 이벤트·값(런타임), ③ 기본 env `.baglenv`(AAMP, 해시 이름) 의 DirectionalLight 값, ④ 조명 변경 뒤 재계산 여부 |
| ~~셰이더 안 혼합식~~ | 해소 — §7.3 |
| RSDB 행 vs romfs `Gyml/*.TeamColorDataSet.bgyml` 우선순위 | 로더(0x710140946c, 0x71014097d0) 판독 |
| `swap` 플래그 의미, 26000 조건 | 0x71026da7e0 호출자 추적 |
