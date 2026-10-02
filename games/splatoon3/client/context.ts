import type * as THREE from "three";
import type { World } from "../core/world.ts";
import type { AssetLoader } from "./assets.ts";

export interface ClientContext {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  assets: AssetLoader;
  world: World;
  overlay: HTMLElement;
  audio: AudioContext;
}

export interface View {
  /** 고정 스텝 뒤 매 렌더 프레임 호출. alpha = 다음 스텝까지의 보간 비율(0..1). */
  update(w: World, alpha: number): void;
  dispose?(): void;
}
