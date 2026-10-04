// Map part models (range SighterTarget etc.) drawn outside visual.glb: same Hoian_UBER material chain as the stage/player.
// Original program for SighterTarget M_Body = Hoian_UBER 3443 (team_color_map_type 2: mix(Alb, my_team_color, clamp(Tcl.x + team_color_blend_alpha))).
import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { applyHoian, textureForSlot, type FresMaterial } from "./hoian.ts";
import { applyForward } from "./forward.ts";
import { fresOf, shareMaterialSamplers, textureResolver } from "./model.ts";
import { materialTeamParams, type TeamSet } from "./teamcolor.ts";
import type { LightingState } from "./lighting.ts";

/** Original BNTX format per texture name (tex/<owner>/native_formats.json written by web/tools/asset_r11_target_tex.py). */
export interface NativeTextureFormats { textures: Record<string, { format: string; comp?: string; srgb?: boolean }> }

/** Exact sRGB EOTF the GPU applies when sampling a *_SRGB block format. */
export const NATIVE_SRGB_EOTF_GLSL = "float hNativeSrgbToLinear(float c){return c<=.04045?c/12.92:pow((c+.055)/1.055,2.4);}\n";

/** The glTF ".mr" pack stores _r0 texels as raw bytes in G. When the original _r0 is a *_SRGB format the shader
 * received the sRGB-decoded value; decode G the same way (metalness B keeps its own linear source). */
export function applyNativeRoughnessColorSpace(mat: THREE.MeshStandardMaterial, f: FresMaterial, formats: NativeTextureFormats | null): boolean {
  const name = textureForSlot(f, "_r0"), fmt = name ? formats?.textures[name]?.format : undefined;
  if (!mat.roughnessMap || !fmt || !/_SRGB$/.test(fmt)) return false;
  const prev = mat.onBeforeCompile, key = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, renderer) => {
    prev.call(mat, sh, renderer);
    const chunk = THREE.ShaderChunk.roughnessmap_fragment;
    if (!chunk.includes("roughnessFactor *= texelRoughness.g;")) throw new Error("three roughnessmap_fragment changed: native sRGB roughness hook missing");
    sh.fragmentShader = NATIVE_SRGB_EOTF_GLSL + sh.fragmentShader.replace("#include <roughnessmap_fragment>",
      chunk.replace("roughnessFactor *= texelRoughness.g;", "roughnessFactor *= hNativeSrgbToLinear(texelRoughness.g);"));
  };
  mat.customProgramCacheKey = () => key.call(mat) + ":nativeSrgbRoughness";
  mat.userData.nativeRoughnessFormat = fmt;
  mat.needsUpdate = true;
  return true;
}

export interface PartMaterialStats { materials: number; skipped: string[]; srgbRoughness: string[]; shared: string[] }

/** Clone and convert every Hoian_UBER material under root once. The actor team selects the team set (0x71011024d0 actor team). */
export function applyPartMaterials(root: THREE.Object3D, opts: { gltf: GLTF; bundle: Bundle; owner: string; lighting: LightingState; teamSet: TeamSet; formats: NativeTextureFormats | null }): PartMaterialStats {
  const stats: PartMaterialStats = { materials: 0, skipped: [], srgbRoughness: [], shared: [] };
  // Owner folder first (M_Body_Tcl lives in tex/Obj_SighterTarget/), then the part glb. Colour spaces stay as the KTX2/glTF
  // declare them: SighterTarget _Emm/_Tcl are BC1_SRGB, unlike the BC4 stage/character ones nativeLinear targets.
  const tex = textureResolver(opts.gltf, opts.bundle, opts.owner, false);
  const done = new Map<THREE.Material, THREE.Material>();
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const list = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const out = list.map((m) => {
      const hit = done.get(m);
      if (hit) return hit;
      const f = fresOf(m);
      if (!f || f.shader?.archive !== "Hoian_UBER" || !(m as THREE.MeshStandardMaterial).isMeshStandardMaterial) { done.set(m, m); return m; }
      const mat = (m as THREE.MeshStandardMaterial).clone();
      mat.userData = { ...m.userData, __fres: f };
      const u = applyHoian(mat, f, materialTeamParams(opts.teamSet, f.renderInfo), tex, stats.skipped, mesh.geometry);
      applyForward(mat, f, opts.lighting, null);
      if (applyNativeRoughnessColorSpace(mat, f, opts.formats)) stats.srgbRoughness.push(mat.name);
      if (u) stats.shared.push(...shareMaterialSamplers(mat, f).map((r) => mat.name + ": " + r));
      stats.materials++;
      done.set(m, mat);
      return mat;
    });
    mesh.material = Array.isArray(mesh.material) ? out : out[0];
  });
  return stats;
}
