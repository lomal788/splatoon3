// 에셋 카탈로그와 번들 로더. 판 시작 때 필요한 번들(맵·캐릭터·무기 + 의존)만 받는다.
// 형식·폴더 규칙: DESIGN.md "에셋" 절, 생성: tools/asset_*.  URL 기준: env.ts ASSETS.
import * as THREE from "three";
import { GLTFLoader, type GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import { KTX2Loader } from "three/examples/jsm/loaders/KTX2Loader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { ASSETS } from "./env.ts";

export interface BundleEntry {
  /** assets/ 기준 폴더 (끝 슬래시) */
  dir: string;
  /** 폴더 기준 파일 목록 */
  files: string[];
  /** 함께 받아야 하는 번들 id */
  deps?: string[];
  /** 전송 바이트 합(진행률 표시용) */
  bytes?: number;
}

export interface Catalog {
  version: number;
  bundles: Record<string, BundleEntry>;
}

/** 경기 구성 → 받을 번들. */
export interface MatchSpec {
  map: string;
  players: { character: string; weapon: string; team: 0 | 1 | 2 }[];
}

export function bundlesFor(spec: MatchSpec): string[] {
  const ids = new Set<string>(["common", `map/${spec.map}`]);
  for (const p of spec.players) {
    ids.add(`character/${p.character}`);
    ids.add(`weapon/${p.weapon}`);
  }
  return [...ids];
}

export class Bundle {
  readonly id: string;
  readonly entry: BundleEntry;
  private readonly files = new Map<string, unknown>();
  constructor(id: string, entry: BundleEntry) {
    this.id = id;
    this.entry = entry;
  }
  set(name: string, value: unknown): void {
    this.files.set(name, value);
  }
  has(name: string): boolean {
    return this.files.has(name);
  }
  json<T = unknown>(name: string): T {
    return this.need(name) as T;
  }
  gltf(name: string): GLTF {
    return this.need(name) as GLTF;
  }
  audio(name: string): AudioBuffer {
    return this.need(name) as AudioBuffer;
  }
  texture(name: string): THREE.Texture {
    return this.need(name) as THREE.Texture;
  }
  bytes(name: string): ArrayBuffer {
    return this.need(name) as ArrayBuffer;
  }
  names(): string[] {
    return [...this.files.keys()];
  }
  private need(name: string): unknown {
    if (!this.files.has(name)) throw new Error(`번들 ${this.id}에 ${name} 없음`);
    return this.files.get(name);
  }
}

export class AssetLoader {
  catalog: Catalog | null = null;
  onProgress: (done: number, total: number) => void = () => {};
  private readonly bundles = new Map<string, Promise<Bundle>>();
  private readonly gltfLoader: GLTFLoader;
  private readonly ktx2: KTX2Loader;
  private readonly audio: AudioContext;
  private done = 0;
  private total = 0;

  constructor(renderer: THREE.WebGLRenderer, audio: AudioContext) {
    this.audio = audio;
    this.ktx2 = new KTX2Loader().setTranscoderPath(ASSETS + "common/lib/basis/").detectSupport(renderer);
    this.gltfLoader = new GLTFLoader().setKTX2Loader(this.ktx2).setMeshoptDecoder(MeshoptDecoder);
  }

  async loadCatalog(): Promise<Catalog> {
    this.catalog ??= (await (await this.fetchOk(ASSETS + "catalog.json")).json()) as Catalog;
    return this.catalog;
  }

  /** 의존까지 펼친 번들을 모두 읽는다. 카탈로그에 없는 번들은 경고만 하고 건너뛴다. */
  async load(ids: string[]): Promise<Map<string, Bundle>> {
    const cat = await this.loadCatalog();
    const all = new Set<string>();
    const visit = (id: string): void => {
      if (all.has(id)) return;
      const e = cat.bundles[id];
      if (!e) {
        console.warn(`[assets] 카탈로그에 없는 번들: ${id}`);
        return;
      }
      all.add(id);
      for (const d of e.deps ?? []) visit(d);
    };
    ids.forEach(visit);
    for (const id of all) this.total += cat.bundles[id].files.length;
    const out = new Map<string, Bundle>();
    await Promise.all([...all].map(async (id) => out.set(id, await this.bundle(id, cat.bundles[id]))));
    return out;
  }

  private bundle(id: string, e: BundleEntry): Promise<Bundle> {
    let p = this.bundles.get(id);
    if (!p) {
      p = (async () => {
        const b = new Bundle(id, e);
        await Promise.all(e.files.map(async (f) => b.set(f, await this.file(e.dir + f))));
        return b;
      })();
      this.bundles.set(id, p);
    }
    return p;
  }

  private async file(path: string): Promise<unknown> {
    const url = ASSETS + path;
    const ext = path.slice(path.lastIndexOf(".") + 1).toLowerCase();
    try {
      if (ext === "json") return await (await this.fetchOk(url)).json();
      if (ext === "glb" || ext === "gltf") return await this.gltfLoader.loadAsync(url);
      if (ext === "ktx2") return await this.ktx2.loadAsync(url);
      if (ext === "ogg" || ext === "opus" || ext === "wav") {
        return await this.audio.decodeAudioData(await (await this.fetchOk(url)).arrayBuffer());
      }
      return await (await this.fetchOk(url)).arrayBuffer();
    } finally {
      this.onProgress(++this.done, this.total);
    }
  }

  private async fetchOk(url: string): Promise<Response> {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r;
  }

  dispose(): void {
    this.ktx2.dispose();
  }
}
