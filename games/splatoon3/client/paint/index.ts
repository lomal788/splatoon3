// 담당: [paint] — docs/impl/paint.md 에 구현 상태·미확정을 기록한다.
// 도색 표시: core 도색 아틀라스(페이지별 RGBA8, R/G/B = 팀 0/1/2 잉크량) → three DataTexture,
// 칠 가능 충돌 삼각형으로 만든 오버레이 메시(법선 방향으로 조금 띄움)에 팀 Ink 색으로 그린다.
// 원본은 시각 메시가 도색 텍스처를 직접 샘플한다(ColPaint UV, 셰이더 경로 미판독) — 차이는 docs/impl/paint.md.
import * as THREE from "three";
import type { PaintSurfacesShared } from "../../core/paint/index.ts";
import type { World } from "../../core/world.ts";
import type { ClientContext, View } from "../context.ts";
import { parseEnv } from "../render/map.ts";
import { buildTeamSets, FALLBACK_ROW, type EnvLight, type TeamColorRow } from "../render/teamcolor.ts";

/** 오버레이를 충돌 면에서 띄우는 거리(단위). 충돌↔시각 표면 거리 중앙값 7mm(collision_mesh.md §5) 위로. */
const LIFT = 0.02;
/** 표시 문턱: 소유 판정과 같은 "채널 ≥ 0.3 이고 최대" (cTeamAlphaTestThreshold) [추정: 원본 지면 셰이더 미판독]. */
const SHOW_TH = 0.3;
/** 연습장 팀 컬러 행 — render 와 같은 행([미확정], client/render/index.ts TEAM_ROW). */
const TEAM_ROW = "OrangeBlue";
/** Ink 조명 입력 대체: 기본 env 낮 DirectionalLight (DiffuseColor (1,1,1), Intensity 4.0) [데이터, team_color.md §5.3]. */
const DAY_LIGHT: EnvLight = { color: [1, 1, 1], intensity: 4.0, skyUp: null };

interface PageView {
  tex: THREE.DataTexture;
  mat: THREE.MeshStandardMaterial;
  mesh: THREE.Mesh | null;
}

export function createPaintView(ctx: ClientContext): View {
  let pages: PageView[] | null = null;
  const root = new THREE.Group();
  root.name = "paint";
  ctx.scene.add(root);
  // Ink 색의 조명 입력은 render 와 같은 env.json 해석(parseEnv)을 쓴다. 번들은 이미 받아 둔 것(캐시)
  let light: EnvLight | null = null;
  let ready = false;
  void (async () => {
    try {
      const b = (await ctx.assets.load([`map/${ctx.world.data.map}`])).get(`map/${ctx.world.data.map}`);
      if (b?.has("env.json")) light = parseEnv(b.json("env.json")).light;
    } catch (e) {
      console.warn("[paint] env.json 읽기 실패 — 기본 낮 조명으로 Ink 색 계산", e);
    }
    ready = true;
  })();

  const build = (w: World, sh: PaintSurfacesShared): PageView[] => {
    const ink = inkColors(w, light ?? DAY_LIGHT);
    const out: PageView[] = sh.surfaces.pages.map((pg) => {
      const tex = new THREE.DataTexture(pg.color, pg.w, pg.h, THREE.RGBAFormat, THREE.UnsignedByteType);
      tex.magFilter = THREE.LinearFilter;
      tex.minFilter = THREE.LinearFilter;
      tex.generateMipmaps = false;
      tex.colorSpace = THREE.NoColorSpace;
      tex.needsUpdate = true;
      return { tex, mat: inkMaterial(tex, ink), mesh: null };
    });
    for (const m of sh.surfaces.meshes) {
      const g = new THREE.BufferGeometry();
      const pos = new Float32Array(m.positions.length);
      for (let i = 0; i < pos.length; i++) pos[i] = m.positions[i] + m.normals[i] * LIFT;
      g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      g.setAttribute("normal", new THREE.BufferAttribute(m.normals, 3));
      g.setAttribute("paintUv", new THREE.BufferAttribute(m.uvs, 2));
      g.computeBoundingSphere();
      const mesh = new THREE.Mesh(g, out[m.page].mat);
      mesh.name = `paint.page${m.page}`;
      mesh.receiveShadow = true;
      mesh.frustumCulled = false;
      out[m.page].mesh = mesh;
      root.add(mesh);
    }
    return out;
  };

  return {
    update(w: World): void {
      const sh = w.shared.get("paintSurfaces") as PaintSurfacesShared | undefined;
      if (!sh || !ready) return;
      pages ??= build(w, sh);
      for (let p = 0; p < pages.length; p++) {
        const d = sh.takeDirty(p);
        if (!d) continue;
        const pv = pages[p], img = pv.tex.image;
        const [x0, y0, x1, y1] = d;
        const area = (x1 - x0 + 1) * (y1 - y0 + 1);
        if (area * 4 < img.width * img.height) {
          // 바뀐 사각형만 행 단위로 올림(three updateRanges → texSubImage2D)
          for (let y = y0; y <= y1; y++) pv.tex.addUpdateRange((y * img.width + x0) * 4, (x1 - x0 + 1) * 4);
        } else pv.tex.clearUpdateRanges();
        pv.tex.needsUpdate = true;
      }
    },
    dispose(): void {
      ctx.scene.remove(root);
      for (const p of pages ?? []) {
        p.tex.dispose();
        p.mat.dispose();
        p.mesh?.geometry.dispose();
      }
    },
  };
}

/** 팀 0/1/2 의 Ink(9) 색(선형). team_color.md §5.3, 계산은 render 의 teamcolor.ts(같은 원본 식)를 그대로 쓴다. */
function inkColors(w: World, light: EnvLight): THREE.Color[] {
  const t = w.data.tables["team_color"] as { dataSets?: (TeamColorRow & { name?: string })[] } | undefined;
  const row = t?.dataSets?.find((r) => r.name === TEAM_ROW) ?? FALLBACK_ROW;
  const sets = buildTeamSets(row, false, light);
  return [0, 1, 2].map((i) => {
    const c = sets[i].colors[9] ?? sets[i].linear;
    return new THREE.Color().setRGB(c[0], c[1], c[2], THREE.LinearSRGBColorSpace);
  });
}

function inkMaterial(tex: THREE.Texture, ink: THREE.Color[]): THREE.MeshStandardMaterial {
  // 재질(거칠기 등)은 원본 InkUBOParam 을 옮기지 않은 근사 — render 의 조명 아래 보이게만 한다.
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -4 });
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.paintTex = { value: tex };
    sh.uniforms.paintInk = { value: ink.map((c) => new THREE.Vector3(c.r, c.g, c.b)) };
    sh.uniforms.paintTh = { value: SHOW_TH };
    sh.vertexShader = "attribute vec2 paintUv;\nvarying vec2 vPaintUv;\n" + sh.vertexShader.replace("#include <uv_vertex>", "#include <uv_vertex>\nvPaintUv = paintUv;");
    sh.fragmentShader =
      "uniform sampler2D paintTex;\nuniform vec3 paintInk[3];\nuniform float paintTh;\nvarying vec2 vPaintUv;\n" +
      sh.fragmentShader.replace(
        "#include <map_fragment>",
        [
          "vec4 inkT = texture2D(paintTex, vPaintUv);",
          "float inkM = max(max(inkT.r, inkT.g), inkT.b);",
          "if (inkM < paintTh) discard;",
          "diffuseColor.rgb = inkT.r >= inkM ? paintInk[0] : (inkT.g >= inkM ? paintInk[1] : paintInk[2]);",
        ].join("\n"),
      );
  };
  mat.customProgramCacheKey = () => "splatoon3.paint";
  return mat;
}
