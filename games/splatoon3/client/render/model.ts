// 모델 공용: 텍스처 찾기, 바인드 행렬, 파츠 결합. 결합식 근거: docs/graphics/player_assembly.md §6.3
// (검증 페이지 web/tools/graphics_verify/view.html 의 attach() 를 TS 로 옮김).
import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import { option, textureForSlot, textureUvSelector, type FresMaterial, type TexResolver } from "./hoian.ts";
import { fma32 } from "./anim/native_f32.ts";

const F = Math.fround;

/** Animation libraries may share a model basename but contain no render meshes. */
export function playerModelFile(files:string[],pattern:RegExp):string|undefined {
  return files.find(n=>!n.startsWith("anim/")&&pattern.test(n.slice(n.lastIndexOf("/")+1).replace(/\.glb$/i,"")));
}

interface GltfJson {
  images?: { name?: string; uri?: string; mimeType?: string }[];
  textures?: { source?: number; name?: string; extensions?: Record<string, { source?: number }> }[];
}
interface Parser {
  json: GltfJson;
  getDependency(type: "texture", i: number): Promise<THREE.Texture>;
}

const baseName = (s: string): string => s.slice(s.lastIndexOf("/") + 1).replace(/\.(png|ktx2|jpg)$/i, "");

/** Original BNTX formats of the shipped character/weapon textures (analysis/graphics/web/<model>/tex/*.json):
 * every `_Emm`(3) and `_Tcl`(6) is BC4_UNORM. gltfpack tags glTF emissive/color slots sRGB, so such a texture
 * must be sampled as stored values, not sRGB-decoded. */
export function nativeLinearTextureName(name: string): boolean {
  return /_(Emm|Tcl)(\.\d+)?$/.test(name);
}
export function applyNativeTextureColorSpace(t: THREE.Texture | null, name: string): THREE.Texture | null {
  if (t && nativeLinearTextureName(name) && t.colorSpace === THREE.SRGBColorSpace) {
    t.colorSpace = THREE.NoColorSpace;
    t.needsUpdate = true;
  }
  return t;
}

/**
 * 텍스처 이름 → THREE.Texture. 소유 모델별 번들 경로가 있으면 우선하고,
 * 없으면 glb 이미지, 번들 이름 순서로 찾는다.
 * 팀색 마스크(_su0 Tcl) 처럼 glTF PBR 슬롯이 아닌 텍스처를 쓰려고 둔다.
 */
export function textureResolver(gltf: GLTF | null, bundle: Bundle | null, owner?: string, nativeLinear = false): TexResolver {
  const cache = new Map<string, Promise<THREE.Texture | null>>();
  const space = (t: THREE.Texture | null, name: string): THREE.Texture | null => nativeLinear ? applyNativeTextureColorSpace(t, name) : t;
  return (name) => {
    let p = cache.get(name);
    if (!p) {
      p = (async () => {
        // FRES sampler names are local to each model. A shared name (M_Body_MAi)
        // must not replace a selected Tnk_Simple resource with Player00's skin map.
        // Same applies to tex/<owner>/: Har_/Eyb_/body/squid all own an M_TeamColor_Tcl or M_Body_2cl.
        for (const scoped of owner ? [`tex/resources/${owner}/${name}.ktx2`, `tex/${owner}/${name}.ktx2`] : [])
          if (bundle?.has(scoped)) return space(bundle.texture(scoped), name);
        const parser = gltf?.parser as unknown as Parser | undefined;
        const js = parser?.json;
        if (parser && js?.images) {
          const img = js.images.findIndex((im) => im.name === name || (im.uri && baseName(im.uri) === name));
          if (img >= 0) {
            js.textures ??= [];
            let ti = js.textures.findIndex((t) => t.source === img || Object.values(t.extensions ?? {}).some((e) => e.source === img));
            if (ti < 0) {
              const ktx = js.images[img].mimeType === "image/ktx2" || /\.ktx2$/i.test(js.images[img].uri ?? "");
              js.textures.push(ktx ? { extensions: { KHR_texture_basisu: { source: img } } } : { source: img });
              ti = js.textures.length - 1;
            }
            try {
              const t = await parser.getDependency("texture", ti);
              t.flipY = false;
              return space(t, name);
            } catch {
              /* 다음 경로 */
            }
          }
        }
        if (bundle) {
          const f = bundle.names().find((n) => /\.(ktx2)$/i.test(n) && baseName(n) === name);
          if (f) return space(bundle.texture(f), name);
        }
        // ③ Standalone analysis GLB only. Bundles are authoritative; missing slots return null.
        const dir = (gltf?.parser as unknown as { options?: { path?: string } } | undefined)?.options?.path;
        if (dir && !bundle) {
          try {
            const t = await new THREE.TextureLoader().loadAsync(`${dir}tex/${name}.png`);
            t.flipY = false;
            return t;
          } catch {
            /* 없음 */
          }
        }
        return null;
      })();
      cache.set(name, p);
    }
    return p;
  };
}

/** 스킨 메시의 바인드 월드 행렬(뼈 이름 → 행렬) */
export function bindWorld(root: THREE.Object3D): Record<string, THREE.Matrix4> {
  const out: Record<string, THREE.Matrix4> = {};
  root.traverse((o) => {
    const sm = o as THREE.SkinnedMesh;
    if (!sm.isSkinnedMesh) return;
    sm.skeleton.bones.forEach((b, i) => {
      out[b.name] ??= sm.skeleton.boneInverses[i].clone().invert();
    });
  });
  return out;
}

export interface AttachOpt {
  /** 파츠 뼈 → 몸 뼈 이름 */
  map?: Record<string, string>;
  /** A 를 정하는 파츠 뼈 */
  attachPart: string;
  /** A 를 정하는 몸 뼈(없으면 map(attachPart)) */
  attachBody?: string;
  /** full = 회전 포함, translate = 평행이동만, head = 모자 슬롯49(Head · P · ManualBindSRT) */
  mode?: "full" | "translate" | "head";
  /** head 모드의 ManualBindSRT 3×4(행 우선, 평행이동 [3],[7],[11]). 없으면 단위행렬(키 없음) */
  headSrt?: readonly number[];
  mirrorX?: boolean;
}

/**
 * 파츠 glb 를 몸 스켈레톤에 붙인다(§6.3). 붙인 메시 목록을 돌려준다.
 *   A = bodyBind[attachBody] · partBind[attachPart]⁻¹ (translate 면 평행이동만, mirrorX 면 Scale(−1,1,1)·A)
 *   몸에 있는 뼈: inverse = bodyBind⁻¹ · A, 없는 뼈(머리카락 고유): 부모 아래 새 뼈 local = parentBind⁻¹ · A · partBind
 */
export function attach(body: THREE.Object3D, bodyBind: Record<string, THREE.Matrix4>, part: THREE.Object3D, opt: AttachOpt): THREE.Mesh[] {
  const partBind = bindWorld(part);
  const mapName = (n: string): string => opt.map?.[n] ?? n;
  const findBody = (n: string): THREE.Object3D | undefined => {
    const t = body.getObjectByName(mapName(n));
    return t && (t as THREE.Bone).isBone ? t : undefined;
  };
  part.updateMatrixWorld(true);
  const pBindOf = (n: string): THREE.Matrix4 => partBind[n] ?? part.getObjectByName(n)?.matrixWorld.clone() ?? new THREE.Matrix4();
  const aBody = opt.attachBody ?? mapName(opt.attachPart);
  let A = (bodyBind[aBody] ?? new THREE.Matrix4()).clone().multiply(pBindOf(opt.attachPart).clone().invert());
  if (opt.mode === "translate") A = new THREE.Matrix4().makeTranslation(new THREE.Vector3().setFromMatrixPosition(A));
  // Hat world = Head world · P · S, so every hat-model node sits under Head as P·S·node (part bind of Root ignored, as in slot49).
  if (opt.mode === "head") A = (bodyBind[aBody] ?? new THREE.Matrix4()).clone().multiply(headInverse(opt.headSrt));
  if (opt.mirrorX) A = new THREE.Matrix4().makeScale(-1, 1, 1).multiply(A);
  const own: Record<string, THREE.Bone> = {};
  const nodeFor = (b: THREE.Object3D): THREE.Object3D => {
    const tb = findBody(b.name);
    if (tb) return tb;
    if (own[b.name]) return own[b.name];
    const parentNode = b.parent && (b.parent as THREE.Bone).isBone ? nodeFor(b.parent) : body;
    const nb = new THREE.Bone();
    nb.name = "part:" + b.name;
    const parentBind = (parentNode as THREE.Bone).isBone
      ? bodyBind[parentNode.name] ?? (parentNode.userData.bindWorld as THREE.Matrix4)
      : new THREE.Matrix4();
    const want = A.clone().multiply(pBindOf(b.name));
    nb.userData.bindWorld = want;
    nb.matrix.copy(parentBind.clone().invert().multiply(want));
    nb.matrix.decompose(nb.position, nb.quaternion, nb.scale);
    parentNode.add(nb);
    own[b.name] = nb;
    return nb;
  };
  const meshes: THREE.Mesh[] = [];
  part.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) meshes.push(o as THREE.Mesh);
  });
  const out: THREE.Mesh[] = [];
  for (const o of meshes) {
    const sm0 = o as THREE.SkinnedMesh;
    if (sm0.isSkinnedMesh) {
      const bones = sm0.skeleton.bones.map((b) => nodeFor(b) as THREE.Bone);
      const inv = sm0.skeleton.bones.map((_, i) => {
        const nb = bones[i];
        const bb = nb.userData.bindWorld ? null : bodyBind[nb.name];
        return bb ? bb.clone().invert().multiply(A) : sm0.skeleton.boneInverses[i].clone();
      });
      const sm = new THREE.SkinnedMesh(sm0.geometry, sm0.material);
      sm.name = o.name;
      sm.userData = { ...o.userData };
      sm.frustumCulled = false;
      if (opt.mirrorX) {
        // 미러: 행렬식 음수 → 감김 반전(§6.1 신발)
        const m = (Array.isArray(sm0.material) ? sm0.material[0] : sm0.material).clone();
        m.side = THREE.BackSide;
        sm.material = m;
      }
      body.add(sm);
      sm.bind(new THREE.Skeleton(bones, inv), new THREE.Matrix4());
      out.push(sm);
    } else {
      // 리지드: v_world = B_cur · Bbind⁻¹ · A · Pnode · v
      let n: THREE.Object3D | null = o.parent;
      while (n && !partBind[n.name] && !(n.name && findBody(n.name)) && n.parent) n = n.parent;
      const tb = n ? findBody(n.name) : undefined;
      if (!n || !tb) continue;
      const m = (bodyBind[tb.name] ?? new THREE.Matrix4()).clone().invert().multiply(A).multiply(pBindOf(n.name).clone())
        .multiply(o.matrixWorld.clone().premultiply(n.matrixWorld.clone().invert()));
      const mesh = new THREE.Mesh(o.geometry, o.material);
      mesh.name = o.name;
      mesh.userData = { ...o.userData };
      mesh.matrixAutoUpdate = false;
      mesh.matrix.copy(m);
      tb.add(mesh);
      out.push(mesh);
    }
  }
  return out;
}

/** 에셋 담당 변환기(tools/asset_*) 의 material.extras.hoian 형식 */
interface HoianExtras {
  shader?: string;
  options?: Record<string, string>;
  samplers?: Record<string, string>;
  renderInfo?: Record<string, unknown>;
  params?: Record<string, unknown>;
}

/**
 * 메시의 glTF 재질 extras → FresMaterial. 두 형식을 받는다:
 *   extras.fres  (graphics_bfres2gltf: params = {type, value}, samplers = [{sampler, texture, slots}])
 *   extras.hoian (에셋 번들: shader "Hoian_UBER/hoian_uber", params = 값, samplers = {슬롯: 텍스처})
 */
export function fresOf(m: THREE.Material): FresMaterial | null {
  const u = m.userData as { fres?: FresMaterial; hoian?: HoianExtras; __fres?: FresMaterial };
  if (u.__fres) return u.__fres;
  if (u.fres) return u.fres;
  const h = u.hoian;
  if (!h || typeof h !== "object") return null;
  const f: FresMaterial = {
    shader: { archive: (h.shader ?? "").split("/")[0], options: h.options ?? {} },
    renderInfo: h.renderInfo ?? {},
    params: Object.fromEntries(Object.entries(h.params ?? {}).map(([k, v]) => [k, { value: v }])),
    samplers: Object.entries(h.samplers ?? {}).map(([slot, texture]) => ({ sampler: slot, texture, slots: [slot] })),
  };
  u.__fres = f;
  return f;
}

/** Hat slot 49 0x71026e613c: O = [B·P | t_B]·[S | t_S]. B = Head bone-get world, S = ManualBindSRT, both row-major 3×4.
 * Per row: FMUL(S[c],b2) → FMLA(S[4+c],b0) → FMLA(S[8+c],b1) → FADD(t). */
export function nativeHeadMatrix(B: readonly number[], S: readonly number[]): number[] {
  const out: number[] = [];
  for (let r = 0; r < 3; r++) {
    const b = [F(B[4 * r]), F(B[4 * r + 1]), F(B[4 * r + 2]), F(B[4 * r + 3])];
    for (let c = 0; c < 4; c++) {
      let p = F(F(S[c]) * b[2]);
      p = fma32(S[4 + c], b[0], p);
      p = fma32(S[8 + c], b[1], p);
      out.push(F(p + (c === 3 ? b[3] : 0)));
    }
  }
  return out;
}

/** Column permutation P of slot 49: new column 0/1/2 = Head column 2/0/1. */
export const HEAD_P = [0, 1, 0, 0, 0, 1, 1, 0, 0] as const;

/** P · S as a skin inverse under the Head bone (Head_world · P · S = O). */
export function headInverse(S: readonly number[] = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]): THREE.Matrix4 {
  const m = new THREE.Matrix4();
  const e: number[] = [];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++)
    e.push(HEAD_P[3 * r] * S[c] + HEAD_P[3 * r + 1] * S[4 + c] + HEAD_P[3 * r + 2] * S[8 + c]);
  m.set(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], 0, 0, 0, 1);
  return m;
}

/** ManualBindSRT 0x71026e4e80 [판독]: T · Rz · Ry · Rx · S, angles in degrees × 0.017453292. Missing key = identity. */
export function manualBindSrt(srt?: { Rotate?: { X?: number; Y?: number; Z?: number }; Scale?: { X?: number; Y?: number; Z?: number }; Translate?: { X?: number; Y?: number; Z?: number } }): number[] {
  if (!srt) return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0];
  const k = F(0.017453292);
  const [x, y, z] = [srt.Rotate?.X ?? 0, srt.Rotate?.Y ?? 0, srt.Rotate?.Z ?? 0].map(a => F(F(a) * k));
  const [sx, sy, sz] = [srt.Scale?.X ?? 1, srt.Scale?.Y ?? 1, srt.Scale?.Z ?? 1].map(F);
  const t = [srt.Translate?.X ?? 0, srt.Translate?.Y ?? 0, srt.Translate?.Z ?? 0].map(F);
  const [cx, cy, cz, snx, sny, snz] = [Math.cos(x), Math.cos(y), Math.cos(z), Math.sin(x), Math.sin(y), Math.sin(z)].map(F);
  const r = [
    [F(cy * cz), F(F(F(snx * sny) * cz) - F(cx * snz)), F(F(F(cx * sny) * cz) + F(snx * snz))],
    [F(cy * snz), F(F(F(snx * sny) * snz) + F(cx * cz)), F(F(F(cx * sny) * snz) - F(snx * cz))],
    [F(-sny), F(snx * cy), F(cx * cy)],
  ];
  return [F(r[0][0] * sx), F(r[0][1] * sy), F(r[0][2] * sz), t[0], F(r[1][0] * sx), F(r[1][1] * sy), F(r[1][2] * sz), t[1], F(r[2][0] * sx), F(r[2][1] * sy), F(r[2][2] * sz), t[2]];
}

/** Hoian-bound sampler keys (applyHoian bind()) and their UV selector options. */
const HOIAN_KEYS: [slot: string, key: string, select: string, legacy?: string][] = [
  ["_su0", "hTcl", "texcoord_select_teamcolormap"], ["_re0", "hResource0Tex", "texcoord_select_res0", "texcoord_select_resource0"],
  ["_re1", "hResource1Tex", "texcoord_select_res1", "texcoord_select_resource1"], ["_t0", "hTransmissionTex", "texcoord_select_trsmap", "texcoord_select_transmission"],
];

/** Fragment texture-unit budget (MAX_TEXTURE_IMAGE_UNITS 16 on d3d11/most GPUs) without changing any texel read:
 * - glTF "Rgh__Mtl.mr": roughnessMap and metalnessMap are one texture on the same UV → read .g and .b from one fetch.
 * - emissiveMap holding the same FRES texture as a Hoian-bound sampler on the same UV → reuse that sampler.
 * Call after applyHoian/applyForward/applyCharacterMaterial (chains their onBeforeCompile). Returns the removed units. */
export function shareMaterialSamplers(mat: THREE.MeshStandardMaterial, f: FresMaterial): string[] {
  const removed: string[] = [];
  let mergeMr = !!mat.metalnessMap && mat.metalnessMap === mat.roughnessMap &&
    textureUvSelector(f, "texcoord_select_rghmap") === textureUvSelector(f, "texcoord_select_mtlmap");
  if (mat.metalnessMap && mat.metalness === 0) { mat.metalnessMap = null; mergeMr = false; removed.push("metalnessMap(metalness 0)"); }
  else if (mergeMr) { mat.metalnessMap = null; removed.push("metalnessMap→roughnessMap texel .b"); }
  let emissiveKey: string | null = null, emissiveUv = 0;
  const em = mat.emissiveMap?.name;
  if (em) {
    const emmUv = textureUvSelector(f, "texcoord_select_emmmap");
    const calc22 = [0, 1, 2, 3].some(i => ["True", "1"].includes(option(f, "enable_calc_color" + i, "False")) && option(f, "blitz_calc_color" + i + "_calc_type", "0") === "22");
    const keys = calc22 ? [...HOIAN_KEYS, ["_e0", "hNativeEmissionTex", "texcoord_select_emmmap"] as [string, string, string]] : HOIAN_KEYS;
    for (const [slot, key, select, legacy] of keys)
      if (textureForSlot(f, slot) === em && textureUvSelector(f, select, legacy) === emmUv && emmUv === 0) { emissiveKey = key; emissiveUv = emmUv; break; }
    if (emissiveKey) { mat.emissiveMap = null; removed.push("emissiveMap→" + emissiveKey); }
  }
  if (!removed.length) return removed;
  const prev = mat.onBeforeCompile, key = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, renderer) => {
    prev.call(mat, sh, renderer);
    if (mergeMr) sh.fragmentShader = sh.fragmentShader.replace("#include <metalnessmap_fragment>", "#include <metalnessmap_fragment>\n#ifdef USE_ROUGHNESSMAP\nmetalnessFactor*=texelRoughness.b;\n#endif\n");
    if (emissiveKey) sh.fragmentShader = sh.fragmentShader.replace("#include <emissivemap_fragment>", "totalEmissiveRadiance*=texture2D(" + emissiveKey + ",hUV" + emissiveUv + ").rgb;\n");
  };
  mat.customProgramCacheKey = () => key.call(mat) + ":sharedSamplers:" + removed.join(",");
  mat.needsUpdate = true;
  return removed;
}
