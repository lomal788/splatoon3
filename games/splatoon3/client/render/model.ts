// 모델 공용: 텍스처 찾기, 바인드 행렬, 파츠 결합. 결합식 근거: docs/graphics/player_assembly.md §6.3
// (검증 페이지 web/tools/graphics_verify/view.html 의 attach() 를 TS 로 옮김).
import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Bundle } from "../assets.ts";
import type { FresMaterial, TexResolver } from "./hoian.ts";

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

/**
 * 텍스처 이름 → THREE.Texture. 소유 모델별 번들 경로가 있으면 우선하고,
 * 없으면 glb 이미지, 번들 이름 순서로 찾는다.
 * 팀색 마스크(_su0 Tcl) 처럼 glTF PBR 슬롯이 아닌 텍스처를 쓰려고 둔다.
 */
export function textureResolver(gltf: GLTF | null, bundle: Bundle | null, owner?: string): TexResolver {
  const cache = new Map<string, Promise<THREE.Texture | null>>();
  return (name) => {
    let p = cache.get(name);
    if (!p) {
      p = (async () => {
        // FRES sampler names are local to each model. A shared name (M_Body_MAi)
        // must not replace a selected Tnk_Simple resource with Player00's skin map.
        const scoped = owner ? `tex/resources/${owner}/${name}.ktx2` : null;
        if (scoped && bundle?.has(scoped)) return bundle.texture(scoped);
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
              return t;
            } catch {
              /* 다음 경로 */
            }
          }
        }
        if (bundle) {
          const f = bundle.names().find((n) => /\.(ktx2)$/i.test(n) && baseName(n) === name);
          if (f) return bundle.texture(f);
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
  /** full = 회전 포함, translate = 평행이동만 */
  mode?: "full" | "translate";
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
