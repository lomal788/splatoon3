// 에셋 검증: catalog 의 모든 GLB 를 three GLTFLoader(node)로 읽어 메시·뼈·클립 수, 모든 KTX2(단독 + GLB 내장)를
// basis 트랜스코더로 RGBA 디코드, Opus(.ogg) 길이(Ogg granule − pre-skip) 와 ffmpeg 디코드, collision 삼각형·재질 분포를 확인한다.
// 사용: node web/tools/asset_verify.mjs   → analysis/assets_work/verify.json
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";

globalThis.self ??= globalThis; // GLTFLoader(텍스처 로더 선택)가 self 를 참조
const here = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.resolve(here, "..");
const ROOT = path.resolve(WEB, "..");
const ASSETS = path.join(WEB, "games/splatoon3/assets");
const require = createRequire(import.meta.url);
const FFMPEG = path.join(WEB, "node_modules/ffmpeg-static/ffmpeg.exe");

// ---- basis 트랜스코더 (assets/common/lib/basis)
const BASIS = (() => {
  // web/ 는 "type":"module" 이라 require 로는 CJS 로 안 읽힘 → 소스를 함수로 감싸 실행
  const src = readFileSync(path.join(ASSETS, "common/lib/basis/basis_transcoder.js"), "utf8");
  const mod = { exports: {} };
  new Function("module", "exports", "require", "__filename", "__dirname", src)(mod, mod.exports, require, "basis_transcoder.js", ".");
  return mod.exports;
})();
const basis = await BASIS({ wasmBinary: readFileSync(path.join(ASSETS, "common/lib/basis/basis_transcoder.wasm")) });
basis.initializeBasis();
function ktx2Decode(u8) {
  const f = new basis.KTX2File(u8);
  try {
    if (!f.isValid()) throw new Error("invalid ktx2");
    const w = f.getWidth(), h = f.getHeight(), levels = f.getLevels();
    if (!f.startTranscoding()) throw new Error("startTranscoding failed");
    const RGBA32 = 13;
    const size = f.getImageTranscodedSizeInBytes(0, 0, 0, RGBA32);
    const dst = new Uint8Array(size);
    if (!f.transcodeImage(dst, 0, 0, 0, RGBA32, 0, -1, -1)) throw new Error("transcode failed");
    let nz = 0;
    for (let i = 0; i < dst.length; i += 4) if (dst[i] | dst[i + 1] | dst[i + 2]) nz++;
    return { w, h, levels, uastc: f.isUASTC ? f.isUASTC() : undefined, bytes: size, nonBlackTexels: nz };
  } finally {
    f.close();
    f.delete();
  }
}

// ---- GLB
const ktxStub = {
  load(url, onLoad) {
    const t = new THREE.CompressedTexture([], 1, 1);
    t.userData.url = url;
    setTimeout(() => onLoad(t), 0);
  },
};
const loader = new GLTFLoader().setKTX2Loader(ktxStub).setMeshoptDecoder(MeshoptDecoder);
function glbJson(buf) {
  const jl = buf.readUInt32LE(12);
  return { json: JSON.parse(buf.subarray(20, 20 + jl).toString("utf8")), bin: buf.subarray(20 + jl + 8) };
}
async function checkGlb(file) {
  const buf = readFileSync(file);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  const gltf = await loader.parseAsync(ab, "");
  let meshes = 0, skinned = 0, tris = 0, bones = new Set(), mats = new Set();
  gltf.scene.traverse((o) => {
    if (o.isMesh) {
      meshes++;
      if (o.isSkinnedMesh) { skinned++; o.skeleton.bones.forEach((b) => bones.add(b.name)); }
      const g = o.geometry;
      tris += (g.index ? g.index.count : g.attributes.position.count) / 3;
      (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => mats.add(m.name));
    }
    if (o.isBone) bones.add(o.name);
  });
  let nodes = 0;
  gltf.scene.traverse(() => nodes++);
  const clips = gltf.animations.map((a) => ({ name: a.name, duration: +a.duration.toFixed(4), frames: a.userData?.frames ?? null }));
  // 내장 KTX2 디코드
  const { json, bin } = glbJson(buf);
  const ktx = [];
  for (const im of json.images ?? []) {
    if (im.mimeType !== "image/ktx2") continue;
    const bv = json.bufferViews[im.bufferView];
    let data = bin.subarray(bv.byteOffset ?? 0, (bv.byteOffset ?? 0) + bv.byteLength);
    if (bv.extensions?.EXT_meshopt_compression) { /* 이미지는 meshopt 대상 아님 */ }
    ktx.push({ name: im.name, ...ktx2Decode(new Uint8Array(data)) });
  }
  const ext = json.extensionsUsed ?? [];
  return {
    bytes: buf.length, nodes, meshes, skinned, triangles: tris, bones: bones.size, materials: mats.size,
    clips: clips.length, clipSample: clips.slice(0, 3), extensions: ext,
    embeddedKtx2: ktx.length, embeddedKtx2Failed: ktx.filter((k) => !k.nonBlackTexels && k.w > 4).length,
    blackTextures: ktx.filter((k) => !k.nonBlackTexels).map((k) => `${k.name} ${k.w}x${k.h}`),
  };
}

// ---- Ogg Opus
function oggInfo(buf) {
  const head = buf.indexOf("OpusHead");
  const preSkip = buf.readUInt16LE(head + 10);
  const last = buf.lastIndexOf("OggS");
  const granule = Number(buf.readBigInt64LE(last + 6));
  return { preSkip, duration: (granule - preSkip) / 48000 };
}
function ffmpegDecodeSeconds(file) {
  const out = execFileSync(FFMPEG, ["-hide_banner", "-i", file, "-f", "s16le", "-ac", "1", "-ar", "48000", "-"], { maxBuffer: 1 << 28, stdio: ["ignore", "pipe", "ignore"] });
  return out.length / 2 / 48000;
}

// ---- 실행
const cat = JSON.parse(readFileSync(path.join(ASSETS, "catalog.json"), "utf8"));
const report = { glb: {}, ktx2: {}, opus: { count: 0, maxDurationErr: 0, maxDecodeErr: 0, failed: [] }, collision: null, bundles: {} };
for (const [id, b] of Object.entries(cat.bundles)) {
  report.bundles[id] = { files: b.files.length, bytes: b.bytes };
  for (const f of b.files) {
    const full = path.join(ASSETS, b.dir, f);
    if (f.endsWith(".glb")) {
      try { report.glb[b.dir + f] = await checkGlb(full); } catch (e) { report.glb[b.dir + f] = { error: String(e) }; }
    } else if (f.endsWith(".ktx2")) {
      try { report.ktx2[b.dir + f] = ktx2Decode(new Uint8Array(readFileSync(full))); } catch (e) { report.ktx2[b.dir + f] = { error: String(e) }; }
    } else if (f.endsWith(".ogg")) {
      report.opus.count++;
      try {
        const buf = readFileSync(full);
        const info = oggInfo(buf);
        const sfx = JSON.parse(readFileSync(path.join(ASSETS, b.dir, "sfx.json"), "utf8"));
        const name = f.slice(0, -4);
        const a = sfx.assets[name];
        const err = Math.abs(info.duration - a.duration);
        report.opus.maxDurationErr = Math.max(report.opus.maxDurationErr, err);
        const dec = ffmpegDecodeSeconds(full);
        report.opus.maxDecodeErr = Math.max(report.opus.maxDecodeErr, Math.abs(dec - a.duration));
      } catch (e) { report.opus.failed.push(`${f}: ${e}`); }
    }
  }
}
// ---- collision
{
  const dir = path.join(ASSETS, "maps/Lby_Lobby00");
  const meta = JSON.parse(readFileSync(path.join(dir, "collision.json"), "utf8"));
  const bin = readFileSync(path.join(dir, "collision.bin"));
  const L = meta.layout;
  const ab = bin.buffer.slice(bin.byteOffset, bin.byteOffset + bin.byteLength);
  const pos = new Float32Array(ab, L.positions.offset, L.positions.count * 3);
  const idx = new Uint32Array(ab, L.indices.offset, L.indices.count);
  const tm = new Uint16Array(ab, L.triMaterial.offset, L.triMaterial.count);
  const ts = new Uint16Array(ab, L.triSource.offset, L.triSource.count);
  let maxIdx = 0;
  for (const i of idx) maxIdx = Math.max(maxIdx, i);
  const bySource = {}, fldByMat = {};
  for (let t = 0; t < tm.length; t++) {
    const s = meta.sources[ts[t]];
    bySource[s.gyml] = (bySource[s.gyml] ?? 0) + 1;
    if (s.gyml === "Fld_VSLobby") {
      const m = meta.materials[tm[t]];
      const k = `${m.name}|${[...m.flags.userShapeTags].sort().join(",")}|${m.flags.layerHitMask}`;
      fldByMat[k] = (fldByMat[k] ?? 0) + 1;
    }
  }
  // collision_mesh.py 결과(by_shape_tag)와 비교
  let refMatch = null;
  const refFile = path.join(ROOT, "analysis/assets_work/vslobby_col.json");
  if (existsSync(refFile)) {
    const ref = Object.values(JSON.parse(readFileSync(refFile, "utf8")))[0];
    const refByMat = {};
    for (const r of ref.by_shape_tag) {
      const k = `${r.material}|${[...(r.userShapeTags ?? [])].sort().join(",")}|${r.filter?.layerHitMask}`;
      refByMat[k] = (refByMat[k] ?? 0) + r.triangles;
    }
    const keys = new Set([...Object.keys(refByMat), ...Object.keys(fldByMat)]);
    const diff = [...keys].filter((k) => refByMat[k] !== fldByMat[k]);
    refMatch = { refTriangles: ref.triangles, refMaterials: ref.by_shape_tag.length, diffKeys: diff };
  }
  const layers = {};
  for (let t = 0; t < tm.length; t++) layers[meta.materials[tm[t]].layer] = (layers[meta.materials[tm[t]].layer] ?? 0) + 1;
  report.collision = {
    vertexCount: meta.vertexCount, triangleCount: meta.triangleCount, idxCountOk: idx.length === meta.triangleCount * 3,
    maxIndexOk: maxIdx < meta.vertexCount, finite: pos.every(Number.isFinite), bySource, layers, refMatch,
  };
}
writeFileSync(path.join(ROOT, "analysis/assets_work/verify.json"), JSON.stringify(report, null, 1));
// 요약
const g = Object.entries(report.glb);
console.log(`GLB ${g.length} (오류 ${g.filter(([, v]) => v.error).length})`);
for (const [k, v] of g) console.log(v.error ? `  ✗ ${k} ${v.error}` : `  ${k}: mesh ${v.meshes} skinned ${v.skinned} tri ${v.triangles} bones ${v.bones} clips ${v.clips} ktx2 ${v.embeddedKtx2}${v.embeddedKtx2Failed ? " (빈 " + v.embeddedKtx2Failed + ")" : ""}`);
const kt = Object.entries(report.ktx2);
console.log(`KTX2 단독 ${kt.length} (오류 ${kt.filter(([, v]) => v.error).length})`);
console.log(`Opus ${report.opus.count}, Ogg 길이 최대 오차 ${report.opus.maxDurationErr.toFixed(6)} s, ffmpeg 디코드 길이 최대 오차 ${report.opus.maxDecodeErr.toFixed(6)} s, 실패 ${report.opus.failed.length}`);
console.log("collision", JSON.stringify(report.collision));
