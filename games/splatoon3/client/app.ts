// 페이지 조립: 판 구성 → 필요한 번들만 받기 → 월드(고정 60Hz) + 뷰 → 루프.
import * as THREE from "three";
import { ParamStore, type ParamTable } from "../core/params.ts";
import { createSystems } from "../core/systems.ts";
import { World, type MatchData } from "../core/world.ts";
import { AssetLoader, bundlesFor, type Bundle, type MatchSpec } from "./assets.ts";
import type { ClientContext, View } from "./context.ts";
import { DEV } from "./env.ts";
import { InputDevice } from "./input.ts";
import { createViews } from "./views.ts";

/** 지금은 시험 사격장(대전 로비 Lby_Lobby00) 1인 연습만. */
export const PRACTICE: MatchSpec = {
  map: "Lby_Lobby00",
  players: [{ character: "Player00", weapon: "Shooter_Normal_00", team: 0 }],
};

const STEP = 1 / 60;
const MAX_STEPS = 5;

export async function boot(root: HTMLElement, spec: MatchSpec = PRACTICE): Promise<void> {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  root.appendChild(renderer.domElement);
  const overlay = document.createElement("div");
  overlay.className = "s3-overlay";
  root.appendChild(overlay);
  const loading = div(overlay, "s3-loading", "불러오는 중…");

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, 16 / 9, 0.2, 2000);
  const audio = new AudioContext();
  const assets = new AssetLoader(renderer, audio);
  assets.onProgress = (d, t) => (loading.textContent = `불러오는 중… ${d}/${t}`);

  const bundles = await assets.load(bundlesFor(spec));
  const world = new World(matchData(spec, bundles));
  for (const s of createSystems()) world.add(s);
  world.init();

  const ctx: ClientContext = { renderer, scene, camera, assets, world, overlay, audio };
  const views: View[] = createViews(ctx);
  const input = new InputDevice(renderer.domElement);
  loading.remove();
  const click = div(overlay, "s3-click", "클릭해서 시작 (WASD 이동 · 마우스 조준 · 좌클릭 사격 · Shift 오징어 · Space 점프 · R 처음 위치)");
  div(overlay, "s3-crosshair", "");
  const debug = DEV ? div(overlay, "s3-debug", "") : null;

  const resize = (): void => {
    const w = root.clientWidth, h = root.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  addEventListener("resize", resize);
  resize();

  let acc = 0;
  let last = performance.now();
  const frame = (now: number): void => {
    acc += Math.min((now - last) / 1000, MAX_STEPS * STEP);
    last = now;
    click.style.display = input.locked ? "none" : "";
    if (input.locked && audio.state === "suspended") void audio.resume();
    // Preserve the entire accumulated mouse motion across catch-up steps.
    // Each sample receives the number of fixed steps still to run this frame.
    let pendingSteps = Math.floor(acc / STEP);
    while (acc >= STEP) {
      world.step(input.sample(pendingSteps--));
      acc -= STEP;
    }
    const alpha = acc / STEP;
    for (const v of views) v.update(world, alpha);
    if (ctx.renderScene) ctx.renderScene();
    else renderer.render(scene, camera);
    if (debug) debug.textContent = debugText(world);
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
  if (DEV) (globalThis as Record<string, unknown>).__splatoon3 = { world, scene, camera, renderer, bundles, input, views };
}

/** 번들 → 코어 데이터. 규칙: 어느 번들이든 params/<표>.json 은 파라미터 표, data/<이름>.json 은 표·상수. */
function matchData(spec: MatchSpec, bundles: Map<string, Bundle>): MatchData {
  const tables: Record<string, ParamTable> = {};
  const data: Record<string, unknown> = {};
  for (const b of bundles.values()) {
    for (const name of b.names()) {
      if (!name.endsWith(".json")) continue;
      const base = name.slice(name.lastIndexOf("/") + 1, -5);
      if (name.startsWith("params/")) tables[base] = b.json<ParamTable>(name);
      else if (name.startsWith("data/")) data[base] = b.json(name);
    }
  }
  const map = bundles.get(`map/${spec.map}`);
  const defaults = (data["param_defaults"] ?? {}) as Record<string, Record<string, unknown>>;
  return {
    map: spec.map,
    placement: map?.has("placement.json") ? map.json("placement.json") : null,
    collision: map?.has("collision.json")
      ? { meta: map.json("collision.json"), bin: map.has("collision.bin") ? map.bytes("collision.bin") : null }
      : null,
    params: new ParamStore(tables, defaults),
    tables: data,
    players: spec.players,
  };
}

function debugText(w: World): string {
  const lines = [`frame ${w.frame}`];
  const dbg = w.shared.get("debug") as Record<string, unknown> | undefined;
  if (dbg) for (const [k, v] of Object.entries(dbg)) lines.push(`${k}: ${typeof v === "number" ? v.toFixed(4) : String(v)}`);
  return lines.join("\n");
}

function div(parent: HTMLElement, cls: string, text: string): HTMLDivElement {
  const d = document.createElement("div");
  d.className = cls;
  d.textContent = text;
  parent.appendChild(d);
  return d;
}
