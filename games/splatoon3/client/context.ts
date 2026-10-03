import type * as THREE from "three";
import type { World } from "../core/world.ts";
import type { AssetLoader } from "./assets.ts";
import type { MapView } from "./render/map.ts";

export interface ClientContext {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  assets: AssetLoader;
  world: World;
  overlay: HTMLElement;
  audio: AudioContext;
  /** Graphics can provide the linear HDR -> final compose draw. */
  renderScene?: () => void;
  /** Shared existing lighting inputs for the known FX material consumers. */
  fxLighting?: Record<string, THREE.IUniform>;
  /** Web scene-depth supply for original soft-particle equations; native pass order remains unknown. */
  fxDepth?: Record<string, THREE.IUniform>;
  /** Visual stage and native lighting for the paint material branch; read by paint only. */
  paintMap?: MapView;
}

export interface View {
  /** 고정 스텝 뒤 매 렌더 프레임 호출. alpha = 다음 스텝까지의 보간 비율(0..1). */
  update(w: World, alpha: number): void;
  dispose?(): void;
}
