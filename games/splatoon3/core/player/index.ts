// 담당: [physics] — docs/impl/physics.md 에 구현 상태·미확정을 기록한다.
// 플레이어 한 프레임 = 원본 PlayerBehavior 슬롯18(메인 계산 0x7102475a54) → Phive 캐릭터 컨트롤러 → 슬롯19(0x7102483134).
// 순서 근거: docs/player/movement_physics.md §3.3·§9.3.
import { MeshCollisionWorld, playerBodyFilter } from "../collision/index.ts";
import { f32, v3, type Vec3 } from "../fmath.ts";
import { Btn, type PadState } from "../input.ts";
import { Layer } from "../types.ts";
import type { System, World } from "../world.ts";
import { stepBody, type BodyStepResult } from "./body.ts";
import * as C from "./consts.ts";
import { contactCleanup, groundReset, updateStepPaint } from "./contact.ts";
import { gearLerp, makePlayerParam } from "./gear.ts";
import { airCorrection, updateInputDir, updateMove } from "./move.ts";
import { applyState, requestJumpState, requestLandState, updateStateMachine } from "./sm.ts";
import { findSpawn } from "./spawn.ts";
import { createPlayerState, type PlayerState } from "./state.ts";
import { isSquidMove, stateName } from "./states.ts";
import { composeFinal, jumpHoldAdd, tryJump, verticalUpdate, wallKickStick } from "./vertical.ts";

export { createPlayerState } from "./state.ts";
export type { PlayerState, PlayerWeaponLink, StepPaint, LaunchState } from "./state.ts";
export { stateName, isSquidMove, isSquidSM, STATE_TABLE } from "./states.ts";
export { apRate, gearLerp, makePlayerParam, type PlayerParam } from "./gear.ts";
export { CAPSULE_RADIUS, CAPSULE_B, BODY_OFFSET_Y } from "./body.ts";
export * as PlayerConst from "./consts.ts";

/** 잉크 회복 프레임(0AP) — PlayerGearSkillParam_InkRecoveryUp 생성자 기본값 [판독: param_reflect] */
const INK_RECOVER_STD = [600, 410, 220] as const; // InkRecoverFrm_Std_Low/Mid/High
const INK_RECOVER_STEALTH = [180, 148.5, 117] as const; // InkRecoverFrm_Stealth_Low/Mid/High

/** shared "camera" 에서 조준 수평 방향(본체+0x538 = PlayerCamera+0x1a4)과 오른쪽 벡터(PlayerCamera+0x68 → X 기저 [실행: player_camera §6.7]). */
export function readCamera(w: World, aim: Vec3, right: Vec3): void {
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
}

/** 입력 0x710249f494 일부: 스틱, 점프 버튼, 오징어 요청(InputSender 우선순위 → 본체+0x784). */
export function readInput(p: PlayerState, pad: PadState): void {
  p.stick[0] = f32(pad.moveX);
  p.stick[1] = f32(pad.moveY);
  const sl = f32(Math.sqrt(f32(f32(p.stick[0] * p.stick[0]) + f32(p.stick[1] * p.stick[1]))));
  let m = f32(f32(sl - C.STICK_DEADZONE) / C.STICK_RANGE);
  m = m < 0 ? 0 : m > 1 ? 1 : m;
  p.stickMag01 = m;
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
}

interface Ctx {
  aim: Vec3;
  right: Vec3;
  clingRecent: number;
  swimWas: boolean;
  weaponTable: string;
}

export function createPlayerSystem(): System {
  let p: PlayerState | null = null;
  const ctx: Ctx = { aim: v3(0, 0, 1), right: v3(-1, 0, 0), clingRecent: 0, swimWas: false, weaponTable: "" };
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
  p.facing[0] = f32(Math.sin(p.spawnYaw)); p.facing[1] = 0; p.facing[2] = f32(Math.cos(p.spawnYaw));
  p.vel.fill(0); p.desired.fill(0); p.final.fill(0); p.jump3d.fill(0); p.takeoff.fill(0); p.slide.fill(0);
  p.knock.fill(0); p.unexplained.fill(0);
  p.cap = 0; p.vy = 0; p.vySum = 0; p.slideAmt = 0; p.ceilTimer = 0; p.landStiff = 0; p.wallJumpCharge = 0;
  p.airFrames = 0; p.airFrames2 = 0; p.airRatio = 0; p.airStep = 0; p.airStepRatio = 0; p.groundFrames = 0;
  p.sinceJump = 100; p.riseFrames = 0; p.jumpKeep = 0; p.jump3dHold = false;
  p.floorN.set([0, 1, 0]); p.floorNRaw.set([0, 1, 0]); p.surfN.set([0, 1, 0]); p.groundN.set([0, 1, 0]);
  p.onGround = true; p.prevOnGround = true; p.wallCling = false;
  p.launch.active = false; p.launch.apply = false;
  p.transform = 0; p.squidBuf = 0;
  p.ink = 1; p.inkRecoverStop = 0;
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
  readCamera(w, ctx.aim, ctx.right);
  const sq = isSquidMove(p.state);
  // 아군 잉크 속 잠복 0x7102458cfc: 상태 ∈ S(Surprise 제외) && 천장 타이머 0 && 발밑 분류 아군
  p.swimming = sq && p.state !== 0x88 && p.ceilTimer <= 0 && p.step.cls < 2;
  const weaponActive = p.weapon.frame >= 0;
  const shooting = !sq && (weaponActive ? p.weapon.shooting : p.fireHeld && !p.squidRequest);
  // 모델 정면 [추정]: 사람은 조준 방향, 오징어는 이동 방향
  if (!sq) p.facing.set(ctx.aim);
  else {
    const l = Math.hypot(p.vel[0], p.vel[2]);
    if (l > 0.001) { p.facing[0] = f32(p.vel[0] / l); p.facing[1] = 0; p.facing[2] = f32(p.vel[2] / l); }
  }
  const bodyInAir = !p.onGround;
  verticalUpdate(p, bodyInAir);
  // 벽 점프: 이번 프레임 점프 눌림 && 바닥 법선이 벽 && 최근 6프레임 안 벽 붙기 && 스틱이 벽 반대쪽 [추정: 입력 링 버퍼]
  const wallKick = sq && p.jumpPressed && p.floorN[1] < C.FLOOR_NY && ctx.clingRecent > 0 && wallKickStick(p, ctx.aim);
  const j = tryJump(p, wallKick);
  if (j !== "none") {
    p.sinceJump = 0;
    groundReset(p, true);
    requestJumpState(p, shooting);
    w.events.emit({ type: "Jump", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]), wall: j === "wall" });
  }
  jumpHoldAdd(p);
  if (C.VY_EPS < p.vy || 0 < p.airFrames) p.riseFrames++;
  else p.riseFrames = 0;
  updateInputDir(p, ctx.aim, ctx.right);
  updateMove(p, { shooting, aimFold: shooting });
  if (p.launch.apply) {
    p.vel.set(p.launch.vel);
    if (!sq) airCorrection(p, p.vel);
    p.cap = f32(Math.hypot(p.launch.vel[0], p.launch.vel[1], p.launch.vel[2]));
    p.launch.apply = false;
  }
  composeFinal(p);
  p.forceAir = C.VY_EPS < p.vy;

  // ===== Phive 캐릭터 컨트롤러 =====
  p.prevPos.set(p.pos);
  let res: BodyStepResult;
  const onGroundMode = !p.forceAir && p.onGround;
  if (col) {
    const limit = p.wallCling ? C.OVERHANG_NY : C.FLOOR_NY;
    const disp = onGroundMode ? [p.final[0], f32(p.final[1] - p.vy), p.final[2]] : p.final;
    const filter = col.bodyFilter(playerBodyFilter(sq));
    res = stepBody(col, p.pos, disp, { groundLimit: limit, up: onGroundMode ? p.floorN : UP, onGround: onGroundMode, filter });
  } else {
    for (let i = 0; i < 3; i++) p.pos[i] = f32(p.pos[i] + p.final[i]);
    res = { supported: p.pos[1] <= 0, gn: [0, 1, 0], gp: [p.pos[0], 0, p.pos[2]], gtri: -1, contacts: [] };
    if (p.pos[1] < 0) p.pos[1] = 0;
  }
  for (let i = 0; i < 3; i++) p.unexplained[i] = f32(f32(p.pos[i] - p.prevPos[i]) - p.final[i]);

  // ===== 슬롯19 =====
  const wasGround = p.onGround;
  const co = contactCleanup(p, res, p.forceAir);
  p.groundMaterial = p.onGround && col && res.gtri >= 0 ? col.mesh.mat[res.gtri] : p.onGround ? p.groundMaterial : -1;
  if (co.landed && !wasGround) w.events.emit({ type: "Land", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]), air: co.landedAir });
  // 발밑 잉크·벽 붙기
  updateStepPaint(p, w.paint, p.onGround ? p.groundP : p.pos);
  updateCling(w, p, res);
  ctx.clingRecent = p.wallCling ? C.WALLKICK_RING : Math.max(0, ctx.clingRecent - 1);
  // 상태기계
  if (co.landedAir > 0) requestLandState(p, shooting);
  const want = p.squidRequest && p.squidLock < 1;
  // SM+0xd4 이동 애니 속도값(0x710246d060 미판독) — 이동 속도 크기로 근사(벽 위에서도 움직임이 보이게 3D)
  const hv = Math.hypot(p.vel[0], p.vel[1], p.vel[2]);
  p.animSpeed = hv;
  const ev = updateStateMachine(p, { want, shoot: shooting, animSpeed: hv, aim: ctx.aim, frame: w.frame });
  if (ev.toSquid) w.events.emit({ type: "ToSquid", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  if (ev.toHuman) w.events.emit({ type: "ToHuman", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  const swimNow = isSquidMove(p.state) && p.onGround && p.step.cls < 2 && hv > 0.001;
  if (swimNow && !ctx.swimWas) w.events.emit({ type: "Swim", owner: p.id, pos: v3(p.pos[0], p.pos[1], p.pos[2]) });
  ctx.swimWas = swimNow;
  // 잉크 탱크 회복 [추정: 회복식] — weapon 이 소비·회복 정지를 쓴다
  if (p.inkRecoverStop > 0) p.inkRecoverStop--;
  else if (p.ink < 1) {
    const frames = p.swimming ? gearLerp(INK_RECOVER_STEALTH[0], INK_RECOVER_STEALTH[1], INK_RECOVER_STEALTH[2], 0) : gearLerp(INK_RECOVER_STD[0], INK_RECOVER_STD[1], INK_RECOVER_STD[2], 0);
    p.ink = Math.min(1, f32(p.ink + f32(1 / frames)));
  }
  // 낙하·물·장외 → 리스폰
  if (col && fellOut(col, p, co.tris)) respawn(w, p);

  const dbg = (w.shared.get("debug") as Record<string, unknown> | undefined) ?? {};
  dbg["physics.state"] = `${p.state.toString(16)} ${stateName(p.state)}${p.squidModel ? "(squid)" : ""}`;
  dbg["physics.pos"] = `${p.pos[0].toFixed(3)} ${p.pos[1].toFixed(3)} ${p.pos[2].toFixed(3)}`;
  dbg["physics.speed"] = Math.hypot(p.vel[0], p.vel[2]);
  dbg["physics.vy"] = p.vy;
  dbg["physics.air"] = p.airFrames;
  dbg["physics.ink"] = `own ${p.step.own.toFixed(2)} enemy ${p.step.enemyMove.toFixed(2)} cls ${p.step.cls}`;
  if (col?.fallback) dbg["physics.collision"] = "placeholder 평면";
  w.shared.set("debug", dbg);
}

const UP = [0, 1, 0];
const DOWN = v3(0, -1, 0);
const O = v3();

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
