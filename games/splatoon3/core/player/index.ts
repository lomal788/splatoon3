// 담당: [physics] — docs/impl/physics.md 에 구현 상태·미확정을 기록한다.
// 플레이어 한 프레임 = 원본 PlayerBehavior 슬롯18(메인 계산 0x7102475a54) → Phive 캐릭터 컨트롤러 → 슬롯19(0x7102483134).
// 순서 근거: docs/player/movement_physics.md §3.3·§9.3.
import { MeshCollisionWorld, playerBodyFilter } from "../collision/index.ts";
import { f32, v3, type Vec3 } from "../fmath.ts";
import { Btn, type PadState } from "../input.ts";
import { Layer } from "../types.ts";
import type { System, World } from "../world.ts";
import { bodyOf, noCollisionStep, resetBody, stepBody, type BodyStepResult } from "./body.ts";
import * as C from "./consts.ts";
import { contactCleanup, groundReset, updateStepPaint } from "./contact.ts";
import { makePlayerParam } from "./gear.ts";
import { airCorrection, inputPost, inputStick, launchPre, updateInputDir, updateMove } from "./move.ts";
import { mainInput } from "../weapon/input.ts";
import { recoverInk } from "../weapon/ink.ts";
import { applyState, requestLandState, updateStateMachine } from "./sm.ts";
import { findSpawn } from "./spawn.ts";
import { createPlayerState, type PlayerState } from "./state.ts";
import { createPlayerDisplayState, nativeCornerProbe, nativeCornerZeroWitness, nativeSmDisplay, stepPlayerDisplay } from "./display.ts";
import { isSquidMove, stateName } from "./states.ts";
import { composeFinal, jumpHoldAdd, tryJump, verticalUpdate, wallChargeStage } from "./vertical.ts";

export { createPlayerState } from "./state.ts";
export type { PlayerState, PlayerWeaponLink, StepPaint, LaunchState } from "./state.ts";
export { stateName, isSquidMove, isSquidSM, STATE_TABLE } from "./states.ts";
export { apRate, gearLerp, makePlayerParam, type PlayerParam } from "./gear.ts";
export { CAPSULE_RADIUS, CAPSULE_B, BODY_OFFSET_Y } from "./body.ts";
export * as PlayerConst from "./consts.ts";

/** shared "camera" 에서 조준 수평 방향(본체+0x538 = PlayerCamera+0x1a4)과 오른쪽 벡터(PlayerCamera+0x68 → X 기저 [실행: player_camera §6.7]). */
export function readCamera(w: World, aim: Vec3, right: Vec3, up?: Vec3): void {
  const cam = w.shared.get("camera") as Record<string, unknown> | undefined;
  let fx = 0, fz = 1;
  const pick = (k: string): ArrayLike<number> | null => {
    const x = cam?.[k];
    return x && typeof x === "object" && typeof (x as ArrayLike<number>)[0] === "number" ? (x as ArrayLike<number>) : null;
  };
  const f = pick("rigForward") ?? pick("aimForward") ?? pick("forward") ?? pick("aimDir") ?? pick("dir");
  if (f) {
    const l = Math.hypot(f[0], f[2]);
    if (l > 1e-6) { fx = f[0] / l; fz = f[2] / l; }
  } else if (typeof cam?.yaw === "number") {
    fx = Math.sin(cam.yaw as number); fz = Math.cos(cam.yaw as number);
  }
  aim[0] = f32(fx); aim[1] = 0; aim[2] = f32(fz);
  const r = pick("right");
  if (r) {
    right[0] = f32(r[0]); right[1] = f32(r[1]); right[2] = f32(r[2]);
  } else {
    // 정면 (fx,0,fz) 의 오른쪽 = (−fz, 0, fx) (오른손 Y-up, 정면 +Z 일 때 오른쪽 −X)
    right[0] = f32(-fz); right[1] = 0; right[2] = f32(fx);
  }
  if (up) {
    const u = pick("up");
    if (u) { up[0] = f32(u[0]); up[1] = f32(u[1]); up[2] = f32(u[2]); }
    else { up[0] = 0; up[1] = 1; up[2] = 0; }
  }
}

/** 입력 0x710249f494 일부: 스틱, 점프 버튼, 오징어 요청(InputSender 우선순위 → 본체+0x784). */
export function readInput(p: PlayerState, pad: PadState): void {
  inputStick(p, pad.moveX, pad.moveY);
  p.jumpHeld = (pad.hold & Btn.Jump) !== 0;
  p.jumpPressed = (pad.trigger & Btn.Jump) !== 0;
  p.fireHeld = (pad.hold & Btn.Fire) !== 0;
  // 새로 누른 버튼이 우선순위 목록 맨 앞(InputSender+0x30..). 종류: 오징어·사격·서브 [버튼 대응 추정]
  for (const b of [Btn.Squid, Btn.Fire, Btn.Sub]) {
    if (pad.trigger & b) {
      const i = p.inputOrder.indexOf(b);
      if (i >= 0) p.inputOrder.splice(i, 1);
      p.inputOrder.unshift(b);
    }
  }
  p.inputOrder = p.inputOrder.filter((b) => (pad.hold & b) !== 0);
  const first = p.inputOrder[0] ?? 0;
  p.inputFirst = first;
  p.squidButton = (pad.hold & Btn.Squid) !== 0;
  p.squidInput = first === Btn.Squid; // +0x785 = Sender+0x55
  const lock = p.squidLock;
  let c: boolean;
  if (lock < 11) {
    if (p.squidLatch) { p.squidInput = true; c = true; } else c = p.squidInput;
  } else {
    p.squidLatch = false;
    c = p.squidInput;
  }
  p.squidRequest = c;
  if (lock > 0 && c) { p.squidRequest = false; p.squidLatch = true; }
  if (p.squidRequest && lock < 1) p.squidLatch = false;
  p.squidLock = Math.max(p.squidLock, 1) - 1;
  const main = mainInput(p.mainInputFrames, first === Btn.Fire, { ...p.mainInputGates, blocked: p.mainInputGates.blocked || p.squidRequest });
  p.mainInputFrames = main.frames;
  p.clearMainLatches = main.clearLatches;
}

interface Ctx {
  aim: Vec3;
  right: Vec3;
  up: Vec3;
  swimWas: boolean;
  weaponTable: string;
}

export function createPlayerSystem(): System {
  let p: PlayerState | null = null;
  const ctx: Ctx = { aim: v3(0, 0, 1), right: v3(-1, 0, 0), up: v3(0, 1, 0), swimWas: false, weaponTable: "" };
  return {
    id: "player",
    init(w: World) {
      const spec = w.data.players[0];
      const team = (spec?.team ?? 0) as 0 | 1 | 2;
      p = createPlayerState(w.newId(), team);
      setupWeapon(w, p, spec?.weapon ?? "");
      const sp = findSpawn(w.data.placement, team);
      if (sp) {
        p.spawnPos[0] = sp.pos[0]; p.spawnPos[1] = sp.pos[1]; p.spawnPos[2] = sp.pos[2];
        p.spawnYaw = sp.yaw;
      } else {
        console.warn("[physics] placement 에 StartPos 없음 — 원점에서 시작");
      }
      respawn(w, p);
      w.shared.set("player", p);
    },
    step(w: World) {
      if (p) stepPlayer(w, p, ctx);
    },
  };
}

/** 무기 표: 무기 id "Shooter_Normal_00" → 표 "WeaponShooterNormal" (번들 params 규칙). */
function setupWeapon(w: World, p: PlayerState, weapon: string): void {
  const parts = weapon.split("_");
  const table = parts.length >= 2 ? `Weapon${parts[0]}${parts[1]}` : "";
  p.weaponTable = table;
  let speedType = 1, accType = 1;
  let moveSpeed = C.SHOT_CLAMP;
  let shotRateOverwrite: [number, number, number] | undefined;
  const params = w.data.params;
  if (table && params.has(table)) {
    const ws = params.get(table, "MainWeaponSetting");
    speedType = enumIndex(ws.WeaponSpeedType, ["Slow", "Mid", "Fast"], 1);
    accType = enumIndex(ws.WeaponAccType, ["Slow", "Mid", "Fast"], 1);
    const ow = [ws.Overwrite_MoveVelRt_Shot_Low, ws.Overwrite_MoveVelRt_Shot_Mid, ws.Overwrite_MoveVelRt_Shot_High];
    if (ow.every((x) => typeof x === "number")) shotRateOverwrite = ow as [number, number, number];
    const wp = params.get(table, "WeaponParam");
    if (typeof wp.MoveSpeed === "number") moveSpeed = f32(wp.MoveSpeed);
  } else if (table) {
    console.warn(`[physics] 무기 표 ${table} 없음 — 생성자 기본값(Mid, Acc 1, MoveSpeed 0.072)`);
  }
  p.gear = makePlayerParam({}, { speedType, accType, shotRateOverwrite });
  p.weaponMoveSpeed = moveSpeed;
}

function enumIndex(v: unknown, names: string[], def: number): number {
  if (typeof v === "number") return v;
  if (typeof v === "string") {
    const i = names.indexOf(v);
    if (i >= 0) return i;
    // param_defaults 의 열거 기본값은 4바이트 리틀엔디언 16진 문자열(예: "01000000" = 1)
    if (/^[0-9a-f]{8}$/i.test(v)) return parseInt(v.slice(6, 8) + v.slice(4, 6) + v.slice(2, 4) + v.slice(0, 2), 16);
  }
  return def;
}

/** 리스폰·리셋 0x710249cb60 (cRespawn): 위치·속도·상태 초기화, 상태 WaitHold(0x56). */
export function respawn(w: World, p: PlayerState): void {
  p.pos[0] = p.spawnPos[0]; p.pos[1] = p.spawnPos[1]; p.pos[2] = p.spawnPos[2];
  p.prevPos.set(p.pos);
  // 몸체 리셋 0x71024f4440: 몸체 원점 = 위치 + (0, r, 0) [실행] (body.ts)
  resetBody(bodyOf(p), p.pos);
  p.facing[0] = f32(Math.sin(p.spawnYaw)); p.facing[1] = 0; p.facing[2] = f32(Math.cos(p.spawnYaw));
  p.vel.fill(0); p.desired.fill(0); p.final.fill(0); p.jump3d.fill(0); p.takeoff.fill(0); p.slide.fill(0);
  p.knock.fill(0); p.unexplained.fill(0);
  p.cap = 0; p.vy = 0; p.vySum = 0; p.slideAmt = 0; p.ceilTimer = 0; p.landStiff = 0; p.wallJumpCharge = 0;
  p.airFrames = 0; p.airFrames2 = 0; p.airRatio = 0; p.airStep = 0; p.airStepRatio = 0; p.groundFrames = 0;
  // 리스폰 이동 리셋 0x71023547bc: +0x734 = 9999, +0x774..+0x782·입력 구조체 +0x470..+0x497·+0xaec·발사 구조체 0, 이동 이력은 유지
  p.sinceJump = 9999; p.riseFrames = 0; p.jumpKeep = 0; p.jump3dHold = false; p.holdBlock = false; p.wallJumpOff = 0;
  p.stick[0] = 0; p.stick[1] = 0; p.stickMag01 = 0; p.stickMagSmooth = 0; p.wallInputDir = 0; p.wallInput = 0;
  p.stickLock = 0; p.squidHoldFrames = 0; p.squidInkFrames = 0;
  p.floorN.set([0, 1, 0]); p.floorNRaw.set([0, 1, 0]); p.surfN.set([0, 1, 0]); p.groundN.set([0, 1, 0]);
  p.onGround = true; p.prevOnGround = true; p.wallCling = false;
  { const L = p.launch; L.vel.fill(0); L.active = L.active2 = L.apply = L.wallJump = L.wasSquid = false; L.count = 0; L.frame = 0; L.speed = 0; L.lock = 0; L.lockStick[0] = 0; L.lockStick[1] = 0; }
  p.transform = 0; p.squidBuf = 0;
  p.ink = 1; p.inkRecoverStop = 0; p.inkRecoverStopNoInk = 0; p.inkRecoverStopSquid = 0;
  p.inkConsumeHold = 0; p.inkStealthFrames = 0; p.inkStealthBlend = 0;
  p.display = createPlayerDisplayState(); p.displayBinding = null; p.inkFastStealth = undefined;
  p.mainInputFrames = 0; p.clearMainLatches = false;
  applyState(p, C.STATE_RESET);
  p.respawns++;
  // 시작 위치가 바닥 위 조금 떠 있으면(StartPos y=0.01) 접지 처리로 내려앉는다
  void w;
}

function stepPlayer(w: World, p: PlayerState, ctx: Ctx): void {
  const pad = w.pad;
  const col = w.collision as MeshCollisionWorld | null;
  if (pad.trigger & Btn.Reset) respawn(w, p);
  p.stateChanged = false;

  // ===== 슬롯18 메인 계산 =====
  readInput(p, pad);
  readCamera(w, ctx.aim, ctx.right, ctx.up);
  const sq = isSquidMove(p.state);
  // 아군 잉크 속 잠복 0x7102458cfc: 상태 ∈ S(Surprise 제외) && 천장 타이머 0 && 발밑 분류 아군
  p.swimming = sq && p.state !== 0x88 && p.ceilTimer <= 0 && p.step.cls < 2;
  const weaponActive = p.weapon.frame >= 0;
  const shooting = !sq && (weaponActive ? p.weapon.shooting : p.fireHeld && !p.squidRequest);
  // +0xad8 조건값은 [미확정] — 사격 자세면 1 로 둔다
  inputPost(p, ctx.up, w.frame, shooting ? 1 : 0);
  launchPre(p);
  // 모델 정면 [추정]: 사람은 조준 방향, 오징어는 이동 방향
  if (!sq) p.facing.set(ctx.aim);
  else {
    const l = Math.hypot(p.vel[0], p.vel[2]);
    if (l > 0.001) { p.facing[0] = f32(p.vel[0] / l); p.facing[1] = 0; p.facing[2] = f32(p.vel[2] / l); }
  }
  const bodyInAir = !p.onGround;
  verticalUpdate(p, bodyInAir);
  const jctx = { aim: ctx.aim, frame: w.frame, shooting };
  const j = tryJump(p, jctx);
  if (j.kind === "jump") groundReset(p, true);
  if (j.kind !== "none") w.events.emit({ type: "Jump", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]), wall: j.kind === "wall" });
  jumpHoldAdd(p);
  const wc = wallChargeStage(p, jctx);
  if (wc === "wall" || wc === "latch") w.events.emit({ type: "Jump", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]), wall: true });
  if (C.VY_EPS < p.vy || 0 < p.airFrames) p.riseFrames++;
  else p.riseFrames = 0;
  updateInputDir(p, ctx.aim, ctx.right);
  updateMove(p, { shooting });
  if (p.launch.apply) {
    const v = p.vel;
    v.set(p.launch.vel);
    if (!p.launch.wasSquid) airCorrection(p, v);
    p.cap = f32(Math.sqrt(f32(f32(f32(v[0] * v[0]) + f32(v[1] * v[1])) + f32(v[2] * v[2]))));
    p.launch.apply = false;
  }
  composeFinal(p);
  p.forceAir = C.VY_EPS < p.vy;

  // ===== Phive Entity 월드(단계0 그룹6): 캐릭터 컨트롤러 → native 솔버 → SplResultPlayer → write-back (body.ts) =====
  // 원본 순서 phive_controller.md §6.7: 슬롯18 → Phive → 접촉 반응 큐(플레이어 몸체 콜백 없음) → 슬롯19/20/21
  p.prevPos.set(p.pos);
  let res: BodyStepResult;
  if (col) {
    const fallbackMask = playerBodyFilter(sq).fallbackMask;
    const paint = w.paint as { monitorCounts?: (pos: ArrayLike<number>, n: ArrayLike<number>) => [number, number, number, number] } | null;
    res = stepBody(col, bodyOf(p), p.pos, {
      final: p.final, vy: p.vy, forceAir: p.forceAir, state: p.state, inputDir: p.dir, inputMag: p.inputMag,
      team: p.team, ownThr: p.step.ownThr, enemyThr: p.step.enemyThr,
      inkCounts: paint ? (typeof paint.monitorCounts === "function" ? paint.monitorCounts.bind(paint) : sampleCounts(w)) : null,
      materialOf: (tri) => col.material(col.mesh.mat[tri]),
    }, (sub) => col.playerTerrainFilter(sub, fallbackMask));
  } else {
    res = noCollisionStep(p.pos, p.final);
  }
  for (let i = 0; i < 3; i++) p.unexplained[i] = f32(f32(p.pos[i] - p.prevPos[i]) - p.final[i]);

  // ===== 슬롯19 =====
  const wasGround = p.onGround;
  const co = contactCleanup(p, res, p.forceAir);
  p.groundMaterial = p.onGround && col && res.gtri >= 0 ? col.mesh.mat[res.gtri] : p.onGround ? p.groundMaterial : -1;
  if (co.landed && !wasGround) w.events.emit({ type: "Land", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]), air: co.landedAir });
  // 발밑 잉크·벽 붙기
  // 발밑 샘플 = 접지 정보 O+0x48 델리게이트(Disk 1×1 모니터 4개 가중 합, body.ts/contact.ts)
  updateStepPaint(p, bodyOf(p).monitors.sample());
  updateCling(w, p, res);
  updateOrdinaryDisplay(w, p, res);
  // 상태기계
  if (co.landedAir > 0) requestLandState(p, shooting);
  const want = p.squidRequest && p.squidLock < 1;
  // SM+0xd4 이동 애니 속도값(0x710246d060 미판독) — 이동 속도 크기로 근사(벽 위에서도 움직임이 보이게 3D)
  const hv = Math.hypot(p.vel[0], p.vel[1], p.vel[2]);
  p.animSpeed = hv;
  const ev = updateStateMachine(p, { want, shoot: shooting, animSpeed: hv, aim: ctx.aim, frame: w.frame });
  // Native 249648c invokes display after the state update. Hidden forces both human flags off,
  // so this ordinary alive counter write does not require the absent AS wrapper inputs.
  if (p.displayBinding?.supported && p.display.hidden) p.transform = nativeSmDisplay({ hidden: true, humanCommand: false, squidCommand: false,
    formCounter: p.transform, modelKind: 0, dead: false, state: p.state,
    old: { body: false, hlf: false, squid: false, rail: false } }).formCounter;
  if (ev.toSquid) w.events.emit({ type: "ToSquid", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  if (ev.toHuman) w.events.emit({ type: "ToHuman", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  const swimNow = isSquidMove(p.state) && p.onGround && p.step.cls < 2 && hv > 0.001;
  if (swimNow && !ctx.swimWas) w.events.emit({ type: "Swim", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  ctx.swimWas = swimNow;
  // Ordinary supported B7a0 supply; unsupported producer inputs retain the stated legacy recovery adapter.
  recoverInk(p, { state: p.state, fastStealth: p.inkFastStealth ?? p.swimming, airFrames: p.airFrames });
  // 낙하·물·장외 → 리스폰
  if (col && fellOut(col, p, co.tris)) respawn(w, p);

  const dbg = (w.shared.get("debug") as Record<string, unknown> | undefined) ?? {};
  dbg["physics.state"] = `${p.state.toString(16)} ${stateName(p.state)}${p.squidModel ? "(squid)" : ""}`;
  dbg["physics.pos"] = `${p.pos[0].toFixed(3)} ${p.pos[1].toFixed(3)} ${p.pos[2].toFixed(3)}`;
  dbg["physics.speed"] = Math.hypot(p.vel[0], p.vel[2]);
  dbg["physics.vy"] = p.vy;
  dbg["physics.air"] = p.airFrames;
  dbg["physics.ink"] = `own ${p.step.own.toFixed(2)} enemy ${p.step.enemyMove.toFixed(2)} cls ${p.step.cls}`;
  dbg["render.hidden"] = p.displayBinding?.supported ? `${p.display.hidden} delay=${p.display.delay} age=${p.display.age}` : p.displayBinding?.reason;
  if (col?.fallback) dbg["physics.collision"] = "placeholder 평면";
  w.shared.set("debug", dbg);
}

const DOWN = v3(0, -1, 0);
const O = v3();
const DISPLAY_PROBE_START = v3();
const DISPLAY_PROBE_END = v3();

/** PaintWorld 가 모니터 카운트를 주지 않으면(대체 구현) sample(반경 1) 비율을 카운트 형식으로 바꾼다 — 웹 대체 경로. */
function sampleCounts(w: World): (pos: ArrayLike<number>, n: ArrayLike<number>) => [number, number, number, number] {
  return (pos) => {
    O[0] = pos[0]; O[1] = pos[1]; O[2] = pos[2];
    const r = w.paint ? w.paint.sample(O, 1).ratio : [0, 0, 0];
    return [Math.round(r[0] * 1000), Math.round((r[1] ?? 0) * 1000), Math.round((r[2] ?? 0) * 1000), 1000];
  };
}

/** Ordinary static-ground supplier. Sphere geometry follows the native probe, but PC contact
 * comes from the web collision adapter. This is not a whole Phive corner query or a wall-edge producer. */
export function updateOrdinaryDisplay(w: World, p: PlayerState, res: BodyStepResult): void {
  const col = w.collision as MeshCollisionWorld | null;
  let edge: { edgeBlend: 0; edgeTarget: 0 } | undefined;
  if (col && !col.fallback && p.onGround && res.gtri >= 0 && p.floorN[1] >= C.FLOOR_NY && !p.wallCling) {
    // Static stage only: web contact/body position and zero platform velocity are adapter inputs.
    const probe = nativeCornerProbe({ contact: res.gp, bodyPosition: p.pos, platformVelocity: [0, 0, 0], worldTolerance: f32(.01) });
    if (probe) { DISPLAY_PROBE_START.set(probe.start); DISPLAY_PROBE_END.set(probe.end); }
    if (probe && col.sweepSphere(DISPLAY_PROBE_START, DISPLAY_PROBE_END, probe.radius, Layer.Ground,
      { layerIndex: 1, hitMask: 8, subIndex: 0, subMask: 0xffffffff })) {
      // Conditional native zero leaf: probe reduces a7c to <=.01; native lo>=.06 and
      // the ordinary nonnegative blend update yield zero. Bounds here are witnesses,
      // not captured values for the missing live Ba7c/Ba74 or platform velocity B108.
      edge = nativeCornerZeroWitness(f32(.01), f32(.06), 0, 0);
    }
  }
  p.displayBinding = stepPlayerDisplay(p.display, {
    state: p.state, paintClass: p.step.cls, airFrames: p.airFrames, ceilingTimer: p.ceilTimer,
    chargeFrames: p.wallJumpCharge, chargeMax: p.gear.wallJumpChargeFrames,
    normal: p.floorN, rawNormal: p.floorNRaw, verticalVelocity: p.vy, ...edge,
    b781: false, b7f4: false, b7f9: false, railLatch: false, forceByte: false,
    launchActive: p.launch.active, wallChargeRelease: false, debugForce: false,
    dokanKind: 0, grindActive: false, warpActive: false, specialCandidate: false,
  });
  p.inkFastStealth = p.displayBinding.supported ? p.display.hidden : undefined;
}

/** 오징어 벽 붙기 판정(0x710268c3fc 요약): 벽 접촉점의 아군 잉크가 임계를 넘으면 다음 프레임 지면 한계 −0.2571. */
function updateCling(w: World, p: PlayerState, res: BodyStepResult): void {
  if (!isSquidMove(p.state) || !w.paint) {
    p.wallCling = false;
    return;
  }
  let best: { nx: number; ny: number; nz: number; px: number; py: number; pz: number } | null = null;
  if (p.onGround && p.groundN[1] < C.WALL_SAMPLE_NY) best = { nx: p.groundN[0], ny: p.groundN[1], nz: p.groundN[2], px: p.groundP[0], py: p.groundP[1], pz: p.groundP[2] };
  else {
    for (const c of res.contacts) {
      if (c.ny < C.WALL_SAMPLE_NY && c.ny > C.CEIL_NY) { best = c; break; }
    }
  }
  if (!best) {
    if (!p.onGround || p.floorN[1] >= C.FLOOR_NY) p.wallCling = false;
    return;
  }
  O[0] = best.px; O[1] = best.py; O[2] = best.pz;
  const s = w.paint.sample(O, 0.6);
  const own = s.ratio[p.team as 0 | 1 | 2] ?? 0;
  const ny = best.ny;
  const wv = ny >= C.FLOOR_NY ? 0 : ny <= C.WALL_NY ? 1 : (C.FLOOR_NY - ny) / (C.FLOOR_NY - C.WALL_NY);
  const thr = f32(C.STEP_OWN_THR_BASE - f32(C.STEP_THR_W * wv));
  p.wallCling = thr < own;
}

/** 물(Water 레이어) 아래로 내려감·PlayerDead 태그 접촉·맵 아래로 크게 벗어남 → 리스폰 (낙하 사망 연출·타이머는 미구현). */
function fellOut(col: MeshCollisionWorld, p: PlayerState, tris: number[]): boolean {
  for (const t of tris) {
    const m = col.material(col.mesh.mat[t]);
    if (m?.tags.includes("PlayerDead")) return true;
  }
  const dy = p.prevPos[1] - p.pos[1];
  if (dy > 0) {
    const h = col.raycast(p.prevPos, DOWN, dy, Layer.Water);
    if (h) return true;
  }
  return p.pos[1] < col.bounds().min[1] - 10;
}
