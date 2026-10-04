// 담당: [camera] — docs/impl/camera.md 에 구현 상태·미확정을 기록한다.
// shared "camera" = CameraShared(쓰기), shared "player" = CameraPlayerInput 필드(읽기, physics 담당).
import { Btn } from "../input.ts";
import type { System, World } from "../world.ts";
import { PlayerCamera, type CameraPlayerInput, type CameraNativeInput } from "./camera.ts";

export { PlayerCamera, BOOM_PROBE_MASK, BOOM_PROBE_RADIUS, BOOM_QUERY } from "./camera.ts";
export type { CameraPlayerInput, CameraShared, CameraNativeInput } from "./camera.ts";
export { DEFAULT_AIM_PITCH, aimDirection, aimPitchDeg, pitchAngleToP, pitchMaxDeg, sensK, yawMaxDeg } from "./pitch.ts";
export type { AimPitchCurve } from "./pitch.ts";
export { RIG, baseRig, blendedRig, elevationDeg, rigPose, squidRig } from "./rig.ts";
export { bias, pieceBez } from "./curves.ts";

/** 카메라 오징어 리그 조건의 상태 집합 Sq(0x71024d9ae8 503~506행): 0x82..0x90, 0xaa..0xac, 0xed, 0xee, 0x10c. */
export function isCameraSquidState(s: number): boolean {
  return (s >= 0x82 && s <= 0x90) || (s >= 0xaa && s <= 0xac) || s === 0xed || s === 0xee || s === 0x10c;
}

/** physics 의 shared "player"(core/player/state.ts PlayerState) 중 카메라가 읽는 필드. 이름이 바뀌면 여기만 고친다. */
interface PlayerLike {
  pos?: ArrayLike<number>;
  facing?: ArrayLike<number>;
  floorN?: ArrayLike<number>;
  surfN?: ArrayLike<number>;
  vy?: number;
  jump3d?: ArrayLike<number>;
  vel?: ArrayLike<number>;
  final?: ArrayLike<number>;
  cameraNative?: CameraNativeInput;
  displayBinding?: { supported: boolean } | null;
  display?: { hidden: boolean };
  airFrames?: number;
  airRatio?: number;
  state?: number;
  squid?: boolean;
  formHeight?: number;
  respawns?: number;
}

const view: CameraPlayerInput = { pos: [0, 0, 0] };

export function readPlayer(w: World): CameraPlayerInput | null {
  const p = w.shared.get("player") as PlayerLike | undefined;
  if (!p || !p.pos || p.pos.length < 3) return null;
  view.pos = p.pos;
  view.forward = p.facing;
  view.floorNormal = p.floorN;
  view.surfaceNormalY = p.surfN ? p.surfN[1] : undefined;
  view.velY = p.vy;
  view.jumpVel3dY = p.jump3d ? p.jump3d[1] : undefined;
  view.moveVel = p.vel;
  view.finalVel = p.final;
  // B7a0 is the verified display producer, also true in ordinary ally ink.
  // wallCling is a different field and cannot substitute for it.
  view.native = p.displayBinding?.supported && p.display
    ? { ...p.cameraNative, wall7a0: p.cameraNative?.wall7a0 ?? p.display.hidden }
    : p.cameraNative;
  view.airFrames = p.airFrames;
  view.airRatio = p.airRatio;
  view.squid = typeof p.state === "number" ? isCameraSquidState(p.state) : !!p.squid;
  view.formHeight = p.formHeight;
  return view;
}

function respawnCount(w: World): number | undefined {
  const p = w.shared.get("player") as PlayerLike | undefined;
  return typeof p?.respawns === "number" ? p.respawns : undefined;
}

export function createCameraSystem(): System {
  const cam = new PlayerCamera();
  let pendingRestart = false;
  let sawPlayer = false;
  let lastRespawns: number | undefined;
  return {
    id: "camera",
    init(w) {
      w.shared.set("camera", cam.out);
    },
    step(w) {
      const pl = readPlayer(w);
      const rc = respawnCount(w);
      if (pl && !sawPlayer) {
        sawPlayer = true;
        cam.reset(pl, false);
      } else if (pendingRestart || (rc !== undefined && lastRespawns !== undefined && rc !== lastRespawns)) {
        cam.reset(pl, true);
        pendingRestart = false;
      }
      lastRespawns = rc;
      cam.step(pl, w.pad, w.collision);
      if (rc === undefined && w.pad.trigger & Btn.Reset) pendingRestart = true;
      w.shared.set("camera", cam.out);
      let dbg = w.shared.get("debug") as Record<string, unknown> | undefined;
      if (!dbg) w.shared.set("debug", (dbg = {}));
      dbg["camera.p"] = cam.out.pitchNorm;
      dbg["camera.s"] = cam.out.pitchAngleDeg;
      dbg["camera.squid"] = cam.out.squidBlend;
      dbg["camera.boom"] = cam.out.boomRatio;
    },
  };
}
