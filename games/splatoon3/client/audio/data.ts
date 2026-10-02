// fx·audio 가 함께 쓰는 자료 모음. effect/* · sfx/* 번들(및 common)에서 XLink 사용자, HitEffectConfig,
// 감쇠 세트, 그룹, 소리 버퍼, 이미터 값, 텍스처를 찾는다. 형식은 docs/impl/fx.md "에셋 형식" 절.
// 번들이 없거나 비어 있으면 빈 자료로 시작하고(이벤트 로그·placeholder 로 동작), 도착하면 채운다.
import type * as THREE from "three";
import { bundlesFor, type AssetLoader, type Bundle } from "../assets.ts";
import type { World } from "../../core/world.ts";
import { DEFAULT_ATTN_SETS, DEFAULT_GROUPS, type AttnSet, type GroupRule } from "./alto.ts";
import { HitEffectTable, isHitEffectConfig } from "./hiteffect.ts";
import type { XUser } from "./xlink.ts";
import fallback from "../fx/fallback.json";

export interface FxData {
  slink: Map<string, XUser>;
  elink: Map<string, XUser>;
  hit: HitEffectTable;
  attn: Record<string, AttnSet>;
  groups: Record<string, GroupRule>;
  sounds: Map<string, AudioBuffer>;
  /** "Eset/Emitter" → 이미터 값(vfx_emitter46.py fields 형식) */
  emitters: Map<string, Record<string, unknown>>;
  textures: Map<string, THREE.Texture>;
  /** "Eset/Emitter" → 샘플러 텍스처 이름(effect_vfxb46.py eset 순서) */
  emitterTex: Map<string, string[]>;
  /** "Eset/Emitter" → 프리미티브(G3PR) 파일, 파일 → 형상 */
  emitterPrim: Map<string, string>;
  prims: Map<string, THREE.BufferGeometry>;
  /** 팀 색(선형 RGB) 표가 있으면 */
  teamColors: Record<string, number[]> | null;
  bundles: string[];
  ready: boolean;
}

function empty(): FxData {
  const d: FxData = {
    slink: new Map(),
    elink: new Map(),
    hit: new HitEffectTable(),
    attn: { ...DEFAULT_ATTN_SETS },
    groups: { ...DEFAULT_GROUPS },
    sounds: new Map(),
    emitters: new Map(),
    textures: new Map(),
    emitterTex: new Map(),
    emitterPrim: new Map(),
    prims: new Map(),
    teamColors: null,
    bundles: [],
    ready: false,
  };
  // 번들이 오기 전·없을 때의 개발용 기본 자료(분석 산출물 사본, client/fx/fallback.json). 번들 값이 덮어쓴다.
  const fb = fallback as unknown as Record<string, unknown>;
  collectUsers(fb.slink, "slink", d);
  collectUsers(fb.elink, "elink", d);
  collectEmitters({ emitters: fb.emitters, emitterTextures: fb.emitterTextures }, d);
  return d;
}

const cache = new WeakMap<AssetLoader, FxData>();

function isUser(j: unknown): j is XUser {
  return !!j && typeof j === "object" && Array.isArray((j as XUser).callTables);
}

/** JSON 안의 XLink 사용자 덤프를 찾아 넣는다. {slink:{이름:사용자}} / {elink:...} / {users:{...}} / 사용자 하나 */
function collectUsers(j: unknown, kind: "slink" | "elink", d: FxData): void {
  if (!j || typeof j !== "object") return;
  const o = j as Record<string, unknown>;
  if (isUser(o)) {
    if (o.name) d[kind].set(o.name, o);
    return;
  }
  for (const [k, v] of Object.entries(o)) {
    if (k === "slink" || k === "elink") collectUsers(v, k, d);
    else if (isUser(v)) d[kind].set(v.name ?? k, v);
    else if (k === "users") collectUsers(v, kind, d);
  }
}

function collectEmitters(j: unknown, d: FxData): void {
  if (!j || typeof j !== "object") return;
  const root = j as Record<string, unknown>;
  const o = root.emitters ?? j;
  for (const [k, v] of Object.entries(o as Record<string, unknown>)) {
    if (!v || typeof v !== "object" || !("life" in (v as object)) || !k.includes("/")) continue;
    d.emitters.set(k, v as Record<string, unknown>);
    const tex = (v as Record<string, unknown>).textures;
    if (Array.isArray(tex)) d.emitterTex.set(k, tex.map(String));
  }
  // assets 형식: emitterSets { 이미터셋: [{ name, fields, textures:[{slot,name}], primitive:{file} }] } (docs/impl/assets.md)
  const sets = root.emitterSets;
  if (sets && typeof sets === "object") {
    for (const [eset, list] of Object.entries(sets as Record<string, unknown>)) {
      if (!Array.isArray(list)) continue;
      for (const em of list as Record<string, unknown>[]) {
        const key = `${eset}/${String(em.name)}`;
        const f = em.fields as Record<string, unknown> | undefined;
        if (f && typeof f === "object") d.emitters.set(key, f);
        if (Array.isArray(em.textures)) d.emitterTex.set(key, (em.textures as { name: string }[]).map((t) => String(t.name)));
        const pr = em.primitive as { file?: string } | undefined;
        if (pr?.file) d.emitterPrim.set(key, pr.file);
        else d.emitterPrim.delete(key);
      }
    }
  }
  const et = root.emitterTextures;
  if (et && typeof et === "object") for (const [k, v] of Object.entries(et)) if (Array.isArray(v)) d.emitterTex.set(k, v.map(String));
}

function stem(name: string): string {
  const b = name.slice(name.lastIndexOf("/") + 1);
  const dot = b.lastIndexOf(".");
  return dot > 0 ? b.slice(0, dot) : b;
}

function absorb(id: string, b: Bundle, d: FxData): void {
  const kind: "slink" | "elink" = id.startsWith("effect/") ? "elink" : "slink";
  for (const name of b.names()) {
    const lower = name.toLowerCase();
    if (lower.endsWith(".json")) {
      const j = b.json(name);
      if (isHitEffectConfig(j) && /hit/i.test(name)) d.hit = new HitEffectTable(j);
      collectUsers(j, kind, d);
      collectEmitters(j, d);
      const o = j as Record<string, unknown>;
      if (o && typeof o === "object") {
        if (o.attenuation && typeof o.attenuation === "object") Object.assign(d.attn, convertAttn(o.attenuation as Record<string, unknown>));
        if (o.groups && typeof o.groups === "object") Object.assign(d.groups, o.groups);
        if (o.teamColors && typeof o.teamColors === "object") d.teamColors = o.teamColors as Record<string, number[]>;
        // sounds: { 런타임 이름: 파일 } 이 있으면 그 매핑을 쓴다
        if (o.sounds && typeof o.sounds === "object") {
          for (const [rt, file] of Object.entries(o.sounds as Record<string, string>)) {
            if (b.has(file)) d.sounds.set(rt, b.audio(file));
          }
        }
        // assets 형식: assets { 런타임 이름: { file } | null }
        if (o.assets && typeof o.assets === "object") {
          for (const [rt, a] of Object.entries(o.assets as Record<string, { file?: string } | null>)) {
            if (a?.file && b.has(a.file)) d.sounds.set(rt, b.audio(a.file));
          }
        }
      }
    } else if (lower.endsWith(".ogg") || lower.endsWith(".opus") || lower.endsWith(".wav")) {
      if (!d.sounds.has(stem(name))) d.sounds.set(stem(name), b.audio(name));
    } else if (lower.endsWith(".glb")) {
      let geo: THREE.BufferGeometry | null = null;
      b.gltf(name).scene.traverse((ob) => {
        const m = ob as THREE.Mesh;
        if (!geo && m.isMesh) geo = m.geometry;
      });
      if (geo) d.prims.set(name, geo);
    } else if (lower.endsWith(".ktx2") || lower.endsWith(".png")) {
      try {
        d.textures.set(stem(name), b.texture(name));
      } catch {
        // png 는 로더가 ArrayBuffer 로 준다 — 쓰지 않음
      }
    }
  }
}

/** 판 구성의 의존을 펼쳐 effect/·sfx/ 번들 id 를 고른다. 없으면 카탈로그의 effect/·sfx/ 전부. */
function pickBundles(loader: AssetLoader, w: World): string[] {
  const cat = loader.catalog;
  if (!cat) return [];
  const seen = new Set<string>();
  const visit = (id: string): void => {
    if (seen.has(id) || !cat.bundles[id]) return;
    seen.add(id);
    for (const dep of cat.bundles[id].deps ?? []) visit(dep);
  };
  bundlesFor({ map: w.data.map, players: w.data.players }).forEach(visit);
  const want = (id: string): boolean => id.startsWith("effect/") || id.startsWith("sfx/");
  let ids = [...seen].filter(want);
  if (!ids.length) ids = Object.keys(cat.bundles).filter(want);
  if (seen.has("common")) ids.push("common");
  return ids;
}

export function fxData(loader: AssetLoader, w: World): FxData {
  let d = cache.get(loader);
  if (d) return d;
  const data = empty();
  cache.set(loader, data);
  d = data;
  void (async () => {
    try {
      await loader.loadCatalog();
      const ids = pickBundles(loader, w);
      data.bundles = ids;
      const got = ids.length ? await loader.load(ids) : new Map<string, Bundle>();
      for (const [id, b] of got) absorb(id, b, data);
      // 판 데이터 표(world.data.tables)에 HitEffectConfig 가 있으면 그것을 쓴다
      for (const [k, v] of Object.entries(w.data.tables)) if (isHitEffectConfig(v) && /hit/i.test(k)) data.hit = new HitEffectTable(v);
    } catch (e) {
      console.warn("[fx] 이펙트·효과음 번들을 읽지 못함 — placeholder 로 동작", e);
    }
    data.ready = true;
    console.info(
      `[fx] 자료: 번들 ${data.bundles.join(",") || "(없음)"} · SLink ${data.slink.size} · ELink ${data.elink.size} · 소리 ${data.sounds.size} · 이미터 ${data.emitters.size} · 텍스처 ${data.textures.size} · HitEffectConfig ${data.hit.fromData ? "데이터" : "내장 Shooter 행"}`,
    );
  })();
  return data;
}

/**
 * assets 형식 감쇠 세트 {refs:{volume:[커브,_], filter, priority, directivity, culling}, curves:{이름:{kind ROC|UDC|ADR|ACL,...}}}
 * → AttnSet. ROC flag = mixMode(+0x1c), ADR/ACL 은 f32 배열(sound_resources.md §4.2 표 순서).
 */
function convertAttn(src: Record<string, unknown>): Record<string, AttnSet> {
  const out: Record<string, AttnSet> = {};
  for (const [name, v] of Object.entries(src)) {
    const o = v as { refs?: Record<string, unknown>; curves?: Record<string, Record<string, unknown>>; volume?: unknown };
    if (!o || typeof o !== "object") continue;
    if (!o.refs || !o.curves) {
      out[name] = o as AttnSet; // 이미 AttnSet 형식
      continue;
    }
    const ref = (k: string): Record<string, unknown> | null => {
      const r = o.refs![k];
      const n = Array.isArray(r) ? r[0] : r;
      return typeof n === "string" && n ? o.curves![n] ?? null : null;
    };
    const roc = (c: Record<string, unknown> | null) =>
      c && c.kind === "ROC" ? { model: Number(c.type), A: Number(c.A), B: Number(c.B), C: Number(c.C), D: Number(c.D), mixMode: Number(c.flag ?? 0) } : undefined;
    const udc = (c: Record<string, unknown> | null) =>
      c && c.kind === "UDC" ? { type: Number(c.type), A: Number(c.A), B: Number(c.B), C: Number(c.C), D: Number(c.D), E: Number(c.E) } : undefined;
    const adr = ref("directivity");
    const acl = ref("culling");
    const af = (adr?.f32 as number[] | undefined) ?? null;
    const cf = (acl?.f32 as number[] | undefined) ?? null;
    out[name] = {
      volume: roc(ref("volume")),
      filter: roc(ref("filter")),
      priority: udc(ref("priority")),
      directivity: af ? { inner: af[0], outer: af[1], outerGain: af[2], outerFilter: af[3] ?? 0 } : undefined,
      culling: cf ? { dist: cf[0], fade: cf[1], apply: cf[2] ?? 0 } : undefined,
    };
  }
  return out;
}
