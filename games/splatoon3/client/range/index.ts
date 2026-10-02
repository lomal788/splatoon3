// 담당: [range] — docs/impl/range.md 에 구현 상태·미확정을 기록한다.
// 표적 표시와 데미지 숫자(원본 Shr_Points_00 레이아웃 대신 DOM).
// 모델: 맵 번들 parts/Obj_SighterTarget(.glb), parts/Obj_SighterTargetMove.glb (뼈 root·leg·burst·body·ear*). 없으면 임시 캡슐.
// 원본 스켈레탈 애니(DamageShot·DamageShotBend·Brust·Expand·Flick)는 아직 에셋에 없어서 아래는 임시 표시(원본 아님, 문서 §2):
//   - Burst·BurstWait 숨김, Expand 는 애니 진행 비율로 크기 0→1,
//   - 휨(DamageShotBend 각·무게)은 leg 뼈를 그 방향으로 기울임(최대각 PLACEHOLDER_MAX_TILT).
import * as THREE from "three";
import { clone as cloneSkinned } from "three/examples/jsm/utils/SkeletonUtils.js";
import type { RangeShared, RangeTargetView } from "../../core/range/index.ts";
import type { World } from "../../core/world.ts";
import type { ClientContext, View } from "../context.ts";
import { DEV } from "../env.ts";

/** 휨 표시의 최대 기울기(라디안) — DamageShotBend 클립이 없어서 쓰는 표시용 값, 원본 값 아님 */
const PLACEHOLDER_MAX_TILT = 0.35;

interface Entry {
  kind: string;
  model: string;
  root: THREE.Group;
  body: THREE.Object3D;
  /** 휨을 걸 대상(모델이면 leg 뼈, 임시면 body) */
  tilt: THREE.Object3D;
  tiltBase: THREE.Quaternion;
  real: boolean;
  label: HTMLDivElement;
  prev: THREE.Vector3;
  cur: THREE.Vector3;
  prevQ: THREE.Quaternion;
  curQ: THREE.Quaternion;
}

export function createRangeView(ctx: ClientContext): View {
  const group = new THREE.Group();
  group.name = "range";
  ctx.scene.add(group);
  const entries = new Map<number, Entry>();
  const models = new Map<string, THREE.Object3D>();
  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xe8e2d0, roughness: 0.6 });
  const capsule = new THREE.CapsuleGeometry(0.35, 0.95, 6, 16);
  let lastFrame = -1;
  const tmp = new THREE.Vector3();
  const tq = new THREE.Quaternion();

  // 맵 번들의 표적 모델(이미 받은 번들이면 캐시에서 바로)
  const mapId = `map/${ctx.world.data.map}`;
  ctx.assets
    .load([mapId])
    .then((b) => {
      const bundle = b.get(mapId);
      if (!bundle) return;
      for (const name of ["Obj_SighterTarget", "Obj_SighterTargetMove"]) {
        const f = `parts/${name}.glb`;
        if (bundle.has(f)) models.set(name, bundle.gltf(f).scene);
      }
      for (const e of entries.values()) upgrade(e);
    })
    .catch((err) => console.warn("[range] 표적 모델 없음 — 임시 모델 사용", err));

  const placeholderBody = (): THREE.Object3D => {
    const g = new THREE.Group();
    const cap = new THREE.Mesh(capsule, bodyMat);
    cap.position.y = 0.825;
    g.add(cap);
    return g;
  };

  const upgrade = (e: Entry): void => {
    const src = models.get(e.model);
    if (!src || e.real) return;
    const m = cloneSkinned(src);
    m.traverse((o) => {
      if ((o as THREE.SkinnedMesh).isSkinnedMesh) o.frustumCulled = false;
    });
    e.root.remove(e.body);
    e.body = m;
    e.root.add(m);
    const leg = m.getObjectByName("leg");
    e.tilt = leg ?? m;
    e.tiltBase = e.tilt.quaternion.clone();
    e.real = true;
  };

  const make = (t: RangeTargetView): Entry => {
    const root = new THREE.Group();
    const body = placeholderBody();
    root.add(body);
    group.add(root);
    const label = document.createElement("div");
    label.style.cssText =
      "position:absolute;left:0;top:0;transform:translate(-50%,-100%);font:700 20px/1 system-ui,sans-serif;color:#fff;" +
      "text-shadow:0 0 3px #000,0 0 6px #000;pointer-events:none;white-space:nowrap;display:none";
    ctx.overlay.appendChild(label);
    const p = new THREE.Vector3(...t.pos);
    const q = new THREE.Quaternion(...t.rot);
    const e: Entry = { kind: t.kind, model: t.model, root, body, tilt: body, tiltBase: new THREE.Quaternion(), real: false, label, prev: p.clone(), cur: p.clone(), prevQ: q.clone(), curQ: q.clone() };
    upgrade(e);
    return e;
  };

  const view: View = {
    update(w: World, alpha: number): void {
      const range = w.shared.get("range") as RangeShared | undefined;
      if (!range) return;
      const stepped = w.frame !== lastFrame;
      lastFrame = w.frame;
      const rect = ctx.renderer.domElement.getBoundingClientRect();
      for (const t of range.targets) {
        let e = entries.get(t.id);
        if (!e) {
          e = make(t);
          entries.set(t.id, e);
        }
        if (stepped) {
          e.prev.copy(e.cur);
          e.prevQ.copy(e.curQ);
          e.cur.set(t.pos[0], t.pos[1], t.pos[2]);
          e.curQ.set(t.rot[0], t.rot[1], t.rot[2], t.rot[3]);
        }
        e.root.position.lerpVectors(e.prev, e.cur, alpha);
        e.root.quaternion.slerpQuaternions(e.prevQ, e.curQ, alpha);
        let s = t.scale;
        if (t.stateName === "Expand" && t.animFrames > 0) s *= Math.min(1, t.animFrame / t.animFrames);
        e.root.scale.setScalar(s);
        e.body.visible = !(t.stateName === "Burst" || t.stateName === "BurstWait");
        // 휨: 방향 각 θ(로컬 +Z 에서 +X 쪽으로), 무게 w → 그 방향으로 기울임(임시)
        if (t.bend.on && t.bend.weight > 0) {
          const th = (t.bend.angleDeg * Math.PI) / 180;
          tq.setFromAxisAngle(tmp.set(Math.cos(th), 0, -Math.sin(th)), t.bend.weight * PLACEHOLDER_MAX_TILT);
          e.tilt.quaternion.copy(e.tiltBase).premultiply(tq);
        } else e.tilt.quaternion.copy(e.tiltBase);
        // 데미지 숫자: 표시 대상 && 카메라 거리 ≤ DrawDamageInfoDistance (0x71021efc24)
        const d = t.damageInfo;
        const near = ctx.camera.position.distanceTo(tmp.set(t.pos[0], t.pos[1], t.pos[2])) <= d.distance;
        let show = false;
        if (d.active && near) {
          tmp.set(d.pos[0], d.pos[1], d.pos[2]).project(ctx.camera);
          if (tmp.z < 1) {
            show = true;
            e.label.style.left = `${((tmp.x + 1) / 2) * rect.width}px`;
            e.label.style.top = `${((1 - tmp.y) / 2) * rect.height}px`;
            // 메시지 Shr_Points_00 "000" = "[정수].[소수]" (소수 자릿수 1 [추정])
            e.label.textContent = d.value.toFixed(1);
            e.label.style.color = d.isMax ? "#ffd84a" : "#fff"; // isMax 표현은 임시(원본은 레이아웃 애니 전환)
          }
        }
        e.label.style.display = show ? "" : "none";
      }
    },
    dispose(): void {
      for (const e of entries.values()) e.label.remove();
      ctx.scene.remove(group);
      capsule.dispose();
      bodyMat.dispose();
    },
  };
  // 개발용: 헤드리스 확인 스크립트(dev/shot.mjs)가 다른 뷰와 분리해 이 뷰만 돌릴 수 있게
  if (DEV) (globalThis as Record<string, unknown>).__splatoon3_rangeView = view;
  return view;
}
