// [fx] 합성 검증: node games/splatoon3/client/audio/selftest.mjs  (web/ 에서)
// 기대값 출처: docs/effect_sound/effect_sound.md §7, xlink_format.md §6, sound_resources.md §4.2, effect_resources.md §5.
// XLink 항목은 analysis/effect_sound/{slink2,elink2}_users.json 이 있을 때만 돈다(원본 실행 대조 아님).
import fs from "node:fs";
import { DEFAULT_ATTN_SETS, evalAadr, evalAroc, evalAudc, limiterOrder } from "./alto.ts";
import { HitEffectTable } from "./hiteffect.ts";
import { XLinkInstance, curveValue, seededRand } from "./xlink.ts";
import { InkActionState } from "../fx/inkaction.ts";
import { floorMatrix, hitTheta, isWall, pickSplash, splashKind, wallMatrix } from "../fx/splash.ts";

let ok = 0, fail = 0;
function check(label, got, exp) {
  const r = JSON.stringify(got) === JSON.stringify(exp);
  if (r) ok++;
  else fail++;
  console.log(r ? "OK  " : "FAIL", label, JSON.stringify(got), r ? "" : `(기대 ${JSON.stringify(exp)})`);
}
const r3 = (x) => Math.round(x * 1000) / 1000;
const deg = (d) => (d * Math.PI) / 180;

// ---- 착탄 분류 (effect_sound.md §7) ----
check("θ=10° → Floor", splashKind(deg(10)), 0);
check("θ=45° → Near", splashKind(deg(45)), 1);
check("θ=80° → Dist", splashKind(deg(80)), 2);
check("θ=170° → Floor(a=10°)", splashKind(deg(170)), 0);
check("수직 낙하 v=(0,-1,0) θ=180°", r3((hitTheta([0, -1, 0], [0, 1, 0]) * 180) / Math.PI), 180);
check("스침 v=(1,-0.1,0) θ≈95.7°", Math.round((hitTheta([1, -0.1, 0], [0, 1, 0]) * 1800) / Math.PI) / 10, 95.7);
check("스침 → Dist", pickSplash([0, 1, 0], [1, -0.1, 0], true).eset, "CmnFloorSplashDist1Emit");
check("속도 0 → kind 0", pickSplash([0, 1, 0], [0, 0, 0], false).eset, "CmnNPFloorSplash1Emit");
check("n.y = 0.64144969 → 벽", isWall([0.767, 0.64144969, 0]), true);
check("n.y = 0.6414498 → 바닥", isWall([0.767, 0.6414498, 0]), false);
{
  const m = wallMatrix([0, 0, 0], [0, 0, -1]);
  check("벽 행렬 n=(0,0,-1) → 단위", [m.x, m.y, m.z].map((a) => a.map((x) => r3(x) + 0)), [[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
  for (const n of [[1, 0, 0], [0, 0.5, -0.8660254], [-0.6, 0.3, 0.7416198]]) {
    const w = wallMatrix([0, 0, 0], n);
    check(`벽 행렬 로컬 −Z = n ${JSON.stringify(n)}`, w.z.map((x, i) => r3(-x - n[i]) + 0), [0, 0, 0]);
  }
}
{
  const m = floorMatrix([0, 0, 0], [0, 1, 0], [0.5, -0.3, 0.2]);
  const t = [0.5, 0, 0.2].map((x) => x / Math.hypot(0.5, 0.2));
  check("바닥 행렬 n=위: Y = n, Z = 투영 진행 방향", [m.y.map((x) => r3(x) + 0), m.z.map((x, i) => r3(x - t[i]) + 0)], [[0, 1, 0], [0, 0, 0]]);
  const k = floorMatrix([0, 0, 0], [0, 1, 0], [0.2, -1.5, 0]); // |v·n| > 0.99999 → c = (0,0,1)
  check("바닥 행렬 |v·n|>0.99999 → Z 고정(+X)", k.z.map((x) => r3(x) + 0), [1, 0, 0]);
  const q = floorMatrix([0, 0, 0], [0.3, 0.9, 0.3162278], [1, -0.5, 0]);
  check("바닥 행렬 기울어진 면: Y = n", q.y.map((x, i) => r3(x - [0.3, 0.9, 0.3162278][i]) + 0), [0, 0, 0]);
}
check("벽 칠 불가 → CmnNpWallSplash1Emit", pickSplash([1, 0, 0], [1, 0, 0], false).eset, "CmnNpWallSplash1Emit");

// ---- Alto (sound_resources.md §4.2.1, §4.2.4, §4.2.5) ----
const A = DEFAULT_ATTN_SETS;
const r4 = (x) => Math.round(x * 1e4) / 1e4;
// analysis/effect_sound/alto_aroc_models.txt (sound_alto.py aroc) 와 같은 값
check("WpMuzzleVol d=2/4/8/16/32", [2, 4, 8, 16, 32].map((d) => r4(evalAroc(A.WpMuzzle_HighSensi.volume, d))), [0.6122, 0.3748, 0.2294, 0.1405, 0.086]);
check("CmnVol d=2/4/8/16 = 1/d", [2, 4, 8, 16].map((d) => r3(evalAroc(A.LowSensi.volume, d))), [0.5, 0.25, 0.125, 0.063]);
check("CmnFlt d=2/4/8/16", [2, 4, 8, 16].map((d) => r3(evalAroc(A.LowSensi.filter, d))), [0, 0, 0, 0.107]);
check("CmnPrio_High d=0/1/2/4/8", [0, 1, 2, 4, 8].map((d) => r3(evalAudc(A.WpMuzzle_HighSensi.priority, d))), [0.9, 0.637, 0.516, 0.433, 0.411]);
check("CmnPrio_Low d=0/1/2/4/8", [0, 1, 2, 4, 8].map((d) => Math.round(evalAudc(A.LowSensi.priority, d) * 1e4) / 1e4), [0.4, 0.1857, 0.0862, 0.0186, 0.0009]);
check("CmnPrio_Low cut 13.55 넘으면 0", evalAudc(A.LowSensi.priority, 13.6), 0);
check("AADR 앞(0°) 1", evalAadr(A.WpMuzzle_HighSensi.directivity, [0, 0, 1], [0, 0, 5]).gain, 1);
check("AADR 뒤(180°) 0.8", r3(evalAadr(A.WpMuzzle_HighSensi.directivity, [0, 0, 1], [0, 0, -5]).gain), 0.8);
check("AADR 110° 선형", r3(evalAadr(A.WpMuzzle_HighSensi.directivity, [0, 0, 1], [Math.sin(deg(110)), 0, Math.cos(deg(110))]).gain), 0.9);
// 제한기: seq 1..5, 우선순위 같음 → 2 = 나중 것 남김, 1 = 먼저 것 남김
const vs = [1, 2, 3, 4, 5].map((s) => ({ seq: s, priority: 0.5 }));
check("제한기 1(같은 우선순위 → 먼저 시작한 것 우선)", limiterOrder(1, vs).map((v) => v.seq), [1, 2, 3, 4, 5]);
check("제한기 2(같은 우선순위 → 나중 것 우선)", limiterOrder(2, vs).map((v) => v.seq), [5, 4, 3, 2, 1]);

// ---- HitEffectConfig ----
const ht = new HitEffectTable();
check("Shooter Constant_Default → E2 Splash, S2 インクヒット", ht.cell("Shooter", "Constant", "Default"), { E2: "Splash", S2: "インクヒット" });
check("Shooter Damaged_(없는 대상) → Damaged_Default", ht.cell("Shooter", "Damaged", "Nope")?.S1, "ヒット");
const ht2 = new HitEffectTable({ rowKeys: ["Shooter"], colKeys: ["Constant_Default"], rows: { Shooter: { Constant_Default: { E2: "Splash" } } } });
check("assets 형식 rows 읽기", ht2.cell("Shooter", "Constant", "Default"), { E2: "Splash" });

// ---- InkAction (effect_sound.md §3.2) ----
{
  const seen = [];
  const s = new InkActionState([{ changeAction: (_slot, n) => seen.push(n) }]);
  s.set(1, 10); // 앞부분 FireOn 요청(보류)
  s.set(0, 10); // 쏨 → FireImpact 즉시
  s.applyPending(); // 보류 FireOn 적용
  s.set(1, 11);
  s.applyPending(); // 같은 액션 — 변화 없음
  s.set(1, 14);
  s.set(0, 14); // 다시 쏨
  s.applyPending();
  s.set(2, 20); // 놓음
  s.applyPending();
  check("액션 변경 순서", seen, ["FireImpact", "FireOn", "FireImpact", "FireOn", "FireOff"]);
  const t = new InkActionState([{ changeAction: (_s, n) => seen.push(n) }]);
  t.set(0, 5);
  t.set(2, 5); // 같은 프레임 FireImpact 뒤 FireOff 무시
  t.applyPending();
  check("같은 프레임 FireImpact 뒤 요청 무시", t.action, 0);
}

// ---- XLink (xlink_format.md §6 / effect_xlink_eval.py --selftest 와 같은 항목) ----
const SL = "C:/dev/splatoon3/analysis/effect_sound/slink2_users.json";
const EL = "C:/dev/splatoon3/analysis/effect_sound/elink2_users.json";
if (fs.existsSync(SL) && fs.existsSync(EL)) {
  const U = JSON.parse(fs.readFileSync(SL, "utf8"));
  const E = JSON.parse(fs.readFileSync(EL, "utf8"));
  const mk = (user, rand = seededRand(1)) => {
    const played = [];
    const inst = new XLinkInstance(user, { play(a) { played.push(a); let alive = true; return { alive: () => alive, fade() { alive = false; } }; } }, rand);
    return { inst, played };
  };
  for (const [st, exp] of [["Focused", "Wp_ShooterNormal_Shot_00"], ["Enemy", "Wp_NormalShot_02"], ["Friend", "Wp_NormalShot_Blurred_02"]]) {
    const { inst, played } = mk(U.WeaponShooterNormal);
    inst.props.set("SubjectiveType", st);
    inst.searchAndEmit("Fire");
    check(`SLink Fire ${st}`, played.map((p) => p.name), [exp]);
  }
  { const { inst, played } = mk(U.WeaponShooterNormal); inst.searchAndEmit("Fire"); check("SubjectiveType 없음 → 무음", played.length, 0); }
  {
    const r = seededRand(7);
    let vmin = 9, vmax = -9, pmin = 9, pmax = -9, mid = 0;
    const N = 20000;
    for (let i = 0; i < N; i++) {
      const { inst, played } = mk(U.WeaponShooterNormal, r);
      inst.props.set("SubjectiveType", "Focused");
      inst.searchAndEmit("Fire");
      const v = played[0].params.Volume, p = played[0].params.Pitch;
      vmin = Math.min(vmin, v); vmax = Math.max(vmax, v); pmin = Math.min(pmin, p); pmax = Math.max(pmax, p);
      if (Math.abs(p - 0.975) < 0.0275) mid++;
    }
    check("Volume ∈ [0.9,1.1], Pitch ∈ [0.7,1.25]", [vmin >= 0.9, vmax <= 1.1, pmin >= 0.7, pmax <= 1.25], [true, true, true, true]);
    check("Random2Pow 중앙 10% 구간 ≈ √0.1", mid / N > 0.28 && mid / N < 0.35, true);
  }
  const mz = E.WeaponShooterNormal.callTables.find((c) => c.key === "マズルフラッシュ");
  check("머즐 Delay 커브 dot=1/0.75/0.875/0.5", [1, 0.75, 0.875, 0.5].map((x) => r3(curveValue(mz.params.Delay.curve, x))), [0, 2, 1, 2]);
  for (const [sm, st, exp] of [["Versus", "Focused", ["Wp_MarkingFly_00"]], ["Versus", "Friend", []], ["Coop", "Friend", ["Wp_MarkingFly_00"]]]) {
    const { inst, played } = mk(U.BulletPointSensor);
    inst.global = (n) => (n === "SpecMode" ? sm : undefined);
    inst.props.set("SubjectiveType", st);
    inst.searchAndEmit("OnActivate");
    check(`Grid ${sm}×${st}`, played.map((p) => p.name), exp);
  }
  { const { inst, played } = mk(U.HitEffect, seededRand(3)); for (let i = 0; i < 2000; i++) inst.searchAndEmit("水没"); let d = 0; for (let i = 1; i < played.length; i++) if (played[i].name === played[i - 1].name) d++; check("Random2 水没 연속 중복 0", d, 0); }
  {
    const { inst, played } = mk(U.HitEffect);
    inst.props.set("SubjectiveType", "Focused"); inst.props.set("IsPaintable", "True"); inst.props.set("Velocity", 2);
    inst.searchAndEmit("インクヒット");
    check("インクヒット Focused 칠가능 v>0.9 → Strong + 飛沫(Blend)", [/Strong/.test(played[0]?.name), /InkSpray/.test(played[1]?.name)], [true, true]);
    check("インクヒット DistCoef = Curve(Velocity 2) = 11.667", r3(played[0].params.DistCoef), 11.667);
  }
  { const { inst, played } = mk(U.HitEffect); inst.props.set("SubjectiveType", "Focused"); inst.searchAndEmit("インク被弾"); check("インク被弾 Focused → 무음", played.length, 0); }
  {
    const { inst, played } = mk(E.WeaponShooterNormal);
    for (const a of ["FireImpact", "FireOn", "FireImpact", "FireOn"]) inst.changeAction("State[0]", a);
    check("FireImpact↔FireOn 넘겨받기: 머즐 이벤트 1회", played.map((p) => p.name), ["WpShtrMzfNml"]);
    inst.changeAction("State[0]", "FireOff");
    inst.changeAction("State[0]", "FireImpact");
    check("FireOff 뒤 FireImpact → 새 이벤트", played.length, 2);
  }
  {
    const { inst, played } = mk(U.PlayerFoot);
    inst.props.set("SubjectiveType", "Focused");
    inst.changeAction("State", "Human_JumpEd");
    const before = played.length;
    inst.calc(); // 프레임 1
    const at1 = played.length;
    inst.calc(); // 프레임 2 = 着地 startFrame
    check("PlayerFoot State Human_JumpEd: 着地(startFrame 2) 는 프레임 0·1 에서 나오지 않음", [before, at1], [0, 0]);
  }
} else console.log("(XLink 항목 건너뜀: analysis 덤프 없음)");

console.log(`${ok}/${ok + fail} PASS`);
if (fail) process.exitCode = 1;
