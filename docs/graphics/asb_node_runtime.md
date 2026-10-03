# ASB FloatBlend 프레임 동기화와 Sequence 진행

## 1. 개요와 화면 동작

걷기·달리기 등 FloatBlend 자식은 부모의 정규화 진행률을 공유한다 [판독]. 같은 절대 프레임을 복사하는 방식은 아니다. Sequence는 현재 자식의 완료 표시를 보고 다음 자식으로 넘어간다 [판독]. 이 문서는 원본 노드 제어와 프레임 변환을 다룬다. 다층 포즈 합성은 계속 [미확정]이다.

## 2. 원본·자료

Splatoon 3 v0 main. 기존 FloatBlend 가중은 `analysis/decomp/render/r4_asnode.c`, 프레임 reader는 `r4_asnode2.c`(39bcdbc), 진행률 공급은 `analysis/decomp/r6_gfx_char/batch1.c`(39bf1b8)다. 새 원본 C는 `analysis/decomp/r8_graphics/asb_sequence_{ink,enter,sync,init}.c`, `asb_nodes.c`, `asb_normframe.c`다. ASB 노드 데이터는 `analysis/assets_work/asb/SplPlayer.json`.

## 3. 호출 흐름 [판독]

FloatBlend: vt+B0 39c8d30 → 39c890c(가중·자식 활성화·진행률 전달) → 39bb6b8 → 39bb2c8(자식 틱) → 스켈레탈 잎 39d3b10 → 39bcdbc → 진행률 소비 39ab3fc. FrameController 부착이 있으면 39c9ac4가 별도 프레임·진행률을 공급할 수 있다.

Sequence: 진입 vt+A8 39ce614 → 자식 부착 39bf2d8. 틱 vt+B0 39cf644 → 동기화 지정이면 39ce888 → 39cf020 → 완료에 따라 39cf2c4. 39c06d4는 다음 노드가 기존 네 층 중 하나에 있으면 그 인스턴스를 다시 연결·초기화하는 경로다. 없으면 false를 반환하고 39bf2d8로 새 층을 붙인다.

## 4. 구조체·필드 [판독]

| 기준 | 필드 | 의미·writer/reader |
|---|---|---|
| 노드 holder H | +8/+10/+18/+20 | 활성 자식 노드 네 층, 39be754/39bf2d8 writer |
| H | +30/+38/+40/+48 | 각 자식 holder |
| H | +28..+2E s16 네 개 | 각 층의 자식 번호 |
| H | +90 s8 | Sequence 현재 자식 번호 |
| H | +96 u16 bit0/6/7 | 완료/자식 완료 래치/진행률 지정 |
| H | +A4/+A8/+AC f32 | 지정 현재/보고 현재/직전 진행률 |
| H | +B4 s32 | Sequence 반복 완료 횟수 |
| Sequence 본문 | +4 bool,+C s32,+14 bool | 반복 여부/반복 횟수/완료 래치 다음 틱 처리 |
| Sequence 본문 | +1C u8 | 자식 수 |
| 애니 엔트리 E | +10/+14/+20/+28 | 하한/끝/구간 시작/끝 override |

bool 값 슬롯의 태그는 값보다 4바이트 앞이다. H+96 bit3의 전체 이름은 [미확정]이며 비트 조건 자체를 보존한다.

## 5. 수명·전이 [판독]

FloatBlend는 매 틱 39bf1b8로 부모 진행률 P를 얻고 H.flags|=0x80으로 지정 모드에 들어간다. 자식 활성화를 마친 뒤 bit3이 꺼진 자식에 현재 P와 부모 직전 진행률을 쓴다. 이어 39bb2c8의 동기화 인자 true 경로가 부모+ A4(음수면 +A8) 및 +AC를 자식에 전달한다. 부모 지정 모드가 없으면 자식 지정 bit7을 끄고 +A4=−1로 되돌린다.

Sequence 진입은 반복 완료 횟수를 0으로 만들고 자식 0부터 부착을 시도한다. 원본 슬롯+FC가 바뀌면 그 지점에서 진입 루프가 멈춘다. 현재 선택 번호와 일치하는 층의 자식 완료 bit0을 발견하면 부모 bit6을 세운다. 본문+14=false는 같은 틱에 다음 자식으로 진행하고, true는 그 래치를 다음 틱 초반에 처리한다. 진행한 틱에는 새 애니 엔트리(+32)에 bit0을 세우며 문맥+2E를 일시적으로 1로 놓았다가 복원한다.

끝 자식 다음에서 반복이 꺼지면 부모 완료 bit0이다. 반복 true이고 횟수 0이면 제한 없이 다시 자식 0이다. 양수 횟수면 끝을 지날 때 +B4를 증가시키고 지정 횟수 미만일 때만 다시 0으로 간다. 다시 시작할 때 +68을 0으로 만들고, 기존 flags bit8이면 bit9도 세운다. 부착을 못 하는 자식을 연속해서 건너뛰는 탐색은 자식 수+1회까지이며 그 뒤 완료로 끝낸다.

## 6. 프레임·조건 식 [실행]+[판독]

일반 잎의 지정 진행률 P는 39ab3fc에서 아래처럼 소비한다. `round4(x)=frinta(f32(x*10000))/10000`이다. 정확히 절반일 때 0에서 멀어지는 방향이다.

```text
endForProgress = useOverride && E.endOverride >= 0 ? E.endOverride : E.end
raw = round4(E.rangeStart + (endForProgress-E.rangeStart)*P)
if (!E.loop || E.endOverride>=0) && raw<E.lower: raw=E.lower
raw=round4(raw)
E.cur = E.report = raw
# 이후 loop이면 원본 구간폭으로 접고, 아니면 끝에서 멈춤
# E.report는 끝 override 이상이면 override로 제한
```

이 함수는 음수·1보다 큰 P를 미리 [0,1]로 제한하지 않는다. 반복 접기에서 큰 진행률은 `int(raw/(end-rangeStart))`로 배수를 구한다. 이 계산의 나눗셈 결과→정수는 fcvtzs이고, 소수 네 자리 반올림은 frinta다.

39bcdbc는 직전 진행률 H+AC도 구간 시작과 끝으로 변환하고 네 자리 반올림해 이벤트 직전 프레임에 쓴다. FrameController가 공급한 절대 프레임(local68)이 있으면 그 경로가 우선한다. 따라서 일반 FloatBlend와 FrameController override를 한 규칙으로 합치면 안 된다.

Sequence의 동기화 39ce888는 자식 duration 합과 마지막 end를 써 전체 프레임을 구성하고, 해당 duration 구간의 자식을 고른 뒤 그 자식 end로 나눈 진행률을 전달한다. 자식 밖 직전 프레임은 −1 또는 2 센티널로 전달한다. 이 경로는 명령 판독만 했으며 실제 전체 노드 실행은 하지 않았다.

## 7. 에셋·애니메이션 연결 [데이터]

사람 ASB의 Sequence 노드 80은 자식 84와 81이다. 둘은 각각 동시 노드이며 실제 스켈레탈 잎 78(`Emote_@`)과 79(`Emote_@_EdWait`)뿐 아니라 재질/가시성 자식도 갖는다. 본문 반복 bool·횟수·완료 래치 방식은 모두 0이다. 기존 '잎 두 개' 설명은 트리 아래 실제 스켈레탈 이름을 단순화한 것이며 직접 자식은 동시 노드다.

## 8. 다른 기능과 상호작용

종류 9 노드는 네 층을 모두 같은 틱에 갱신한다. 본문 모드 1은 첫 nonnull 층이 완료되면 종료하고, 그 밖은 완료 집계 byte를 쓴다 [판독:39d23b4/39bb2c8]. 끝 프레임은 39d30e4의 자식 최대값이다. Simultaneous라는 이름은 웹 권장 이름으로 유지하며 원본 이름 문자열은 확보하지 못했다. 전체 포즈의 정규화/합성 결과를 이 제어 판독으로 확정하지 않는다.

## 9. 웹 포팅 명세

권장 `NodeHolder`에 현재/직전 정규화 진행률과 지정 여부를 둔다. FloatBlend는 부모 진행률을 자식 틱 전에 전달하고, 각 잎에서 자기 구간으로 변환한다. Sequence는 현재 번호·완료 래치·반복 횟수 및 즉시/다음 틱 진행 조건을 보존한다. 모든 자식 애니메이션을 독립 시계로 계속 전진시키는 근사와 다르다. 최종 포즈 합성은 별도 조사 결과가 필요하다.

## 10. 검증

`web/tools/r8_gfx_frame_suffix_emu.py` → `analysis/completion/r8/graphics_frame_suffix_emu.json`. 정규화 프레임 소비 39ab3fc 전체를 **2048/2048** 엔트리 64B 비트 일치로 대조했다. 스텁 없음. P<0/P>1, 반복 여부, 끝 override/하한, 큰 진행률을 포함했다. FloatBlend 활성화·전파·전체 잎 틱·Sequence 전체 실행까지 연결한 검증은 아니다. 그 연결은 원본 C와 명령의 [판독]이다.

## 11. 정정·미확정·다음 근거

2026-10-03 r8: 종전 FloatBlend 자식 동기화와 Sequence 진행 조건 [추정]/[미확정]을 위 경로로 확정했다. 39bcb9c가 동기화 함수라는 기존 오류는 r6 정정대로 유지한다. Sequence/Simultaneous 이름은 웹 권장으로만 쓴다. 다층 포즈 샘플러와 재질·가시성·스켈레탈 기여 합성, 노드 종류의 원본 명칭 및 타 노드 제어 전체는 [미확정]. 다음은 게임 바인더 뒤 SDK 애니메이션 합성 함수들이다. 39cd350은 보고/가중 전파이므로 거기만 읽어 포즈 합성 완료로 올리지 않는다.
