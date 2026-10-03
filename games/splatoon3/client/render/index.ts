// 담당: [render] — docs/impl/render.md 에 구현 상태·미확정을 기록한다.
// 맵(visual.glb·env 조명) + 로컬 플레이어(몸·파츠·_Hlf·오징어·무기, 팀색, ASB 애니).
import * as THREE from "three";
import type { World } from "../../core/world.ts";
import { type Bundle, bundlesFor } from "../assets.ts";
import type { ClientContext, View } from "../context.ts";
import { DEV } from "../env.ts";
import { MapView, parseEnv } from "./map.ts";
import { HDRCompose } from "./post.ts";
import { FxSceneDepth } from "./fx_depth.ts";
import { applyCommonShadowReceivers } from "./forward.ts";
import { PlayerView } from "./player.ts";
import type { MuzzlePose } from "../fx/muzzle.ts";
import { readPlayer } from "./shared.ts";
import { buildTeamSets, FALLBACK_ROW, materialTeamParams, type TeamColorRow, type TeamSet } from "./teamcolor.ts";

/** 연습장에서 쓰는 TeamColorDataSet 행. 로비 시험 사격장이 어느 행을 쓰는지는 [미확정] */
const TEAM_ROW = "OrangeBlue";
/** 무기 분류 → 애니 약어(_Nrml 치환). 슈터 = Shtr (anim_state_machine.md §3 기본값) */
const WEAPON_ABBR = "Shtr";

function teamRow(w: World): TeamColorRow {
  const t = w.data.tables["team_color"] as { dataSets?: (TeamColorRow & { name?: string })[] } | undefined;
  return t?.dataSets?.find((r) => r.name === TEAM_ROW) ?? FALLBACK_ROW;
}

export function createRenderView(ctx: ClientContext): View {
  const { scene, world, renderer } = ctx;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const map = new MapView(scene);
  ctx.paintMap = map;
  const post = new HDRCompose();
  const fxDepth = new FxSceneDepth();
  ctx.fxLighting = map.lighting.uniforms;
  ctx.fxDepth = fxDepth.uniforms;
  let capturingEnvironment = false;
  ctx.renderScene = () => {
    if(capturingEnvironment)return;
    applyCommonShadowReceivers(scene,map.lighting);
    map.shadows.capture(renderer,scene,ctx.camera,map.env.direction);
    fxDepth.capture(renderer, scene, ctx.camera);
    post.render(renderer, scene, ctx.camera);
  };
  const player = new PlayerView(scene);
  let sets: TeamSet[] | null = null;
  let ready = false;
  let lastFrame = -1;
  const p0 = world.data.players[0];

  void (async () => {
    // 번들은 app.ts 가 이미 받았다 — 같은 id 로 다시 부르면 캐시된 Bundle 을 돌려준다
    const spec = { map: world.data.map, players: world.data.players };
    let bundles = new Map<string, Bundle>();
    try {
      bundles = await ctx.assets.load(bundlesFor(spec));
    } catch (e) {
      console.warn("[render] 번들 읽기 실패 — placeholder 로 표시", e);
    }
    // 팀 세트: 조명(Ink/InkBright 입력)은 맵 env 의 주 방향광 (team_color.md §5.3). 경기 시작 때 한 번 계산
    const mapB = bundles.get(`map/${spec.map}`);
    const rawEnv = mapB?.has("env.json") ? mapB.json("env.json") : null;
    sets = buildTeamSets(teamRow(world), false, parseEnv(rawEnv).light);
    map.load(scene, mapB, materialTeamParams(sets[0]), sets[0]);
    post.configure(rawEnv);
    const myTeam = Math.max(0, Math.min(2, p0?.team ?? 0));
    const team = materialTeamParams(sets[myTeam]);
    player.load(p0 ? bundles.get(`character/${p0.character}`) : undefined, p0 ? bundles.get(`weapon/${p0.weapon}`) : undefined, team, WEAPON_ABBR, undefined, map.lighting, sets[myTeam]);
    await player.materialReady;
    capturingEnvironment = true;
    try { await map.captureEnvironment(renderer, scene); }
    catch (error) { console.warn("[render] environment capture failed; last valid SH retained", error); }
    finally {capturingEnvironment=false;ready=true;}
    if (DEV) {
      (globalThis as Record<string, unknown>).__splatoon3_render = { map, player, sets, team, post, fxDepth, shadows:map.shadows };
      console.info("[render]", { map: map.stats, env: map.env.source, player: player.info });
    }
  })();

  return {
    update(w: World, alpha: number): void {
      if (!ready) return;
      // 게임 프레임마다 한 번 진행(원본 60Hz). 한 렌더 프레임에 여러 스텝이 지나가면 마지막 상태로 그만큼 진행
      const steps = lastFrame < 0 ? 1 : Math.min(w.frame - lastFrame, 5);
      if (steps > 0) {
        const snap = readPlayer(w) ?? { pos: [0, 0, 0], yaw: 0, speed: 0, state: null, sub: null, squid: false, team: 0, dead: false, formCounter: null, animSpeed: null, animRate: null, displayHidden: null };
        for (let i = 0; i < steps; i++) player.step(snap);
        lastFrame = w.frame;
      }
      player.draw(alpha);
      const muzzle = player.muzzleMatrix();
      const owner = (w.shared.get("player") as { id?: unknown } | undefined)?.id;
      if (muzzle && owner !== undefined) w.shared.set("muzzle", { owner, frame: w.frame, source: "Weapon_R/Root/Muzzle", matrix: muzzle } satisfies MuzzlePose);
      else w.shared.delete("muzzle");
      map.follow(player.root.position);
      if (DEV) {
        const dbg = (w.shared.get("debug") as Record<string, unknown> | undefined) ?? {};
        const a = player.animator;
        if (a) {
          dbg["render.state"] = "0x" + a.state.toString(16);
          dbg["render.disp"] = `${a.disp.body ? "B" : "-"}${a.disp.hlf ? "H" : "-"}${a.disp.squid ? "S" : "-"} f0=${a.f0}`;
        }
        if (!w.shared.has("debug")) w.shared.set("debug", dbg);
      }
    },
    dispose(): void {
      map.dispose(scene); player.dispose(); post.dispose(); fxDepth.dispose();
      world.shared.delete("muzzle");
      ctx.renderScene = undefined; ctx.fxLighting = undefined; ctx.fxDepth = undefined; ctx.paintMap = undefined;
    },
  };
}
