// Independent load check of converted glb with three.js GLTFLoader (node, textures stubbed).
// usage: node web/tools/graphics_verify/check.mjs <Model>...   -> analysis/graphics/verify/<Model>.json
// three is imported read-only from c:/dev/mpj/web/node_modules.
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const M = 'C:/dev/mpj/web/node_modules/three/';
const THREE = await import(pathToFileURL(M + 'build/three.module.js').href);
const { GLTFLoader } = await import(pathToFileURL(M + 'examples/jsm/loaders/GLTFLoader.js').href);
const W = 'C:/dev/splatoon3/analysis/graphics/web/';
const OUT = 'C:/dev/splatoon3/analysis/graphics/verify/';
fs.mkdirSync(OUT, { recursive: true });

const stub = () => ({ name: 'stub', loadTexture: () => Promise.resolve(new THREE.Texture()) });
const parse = (buf) => new Promise((res, rej) => {
  const l = new GLTFLoader(); l.register(stub);
  l.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '', res, rej);
});

let fails = 0;
for (const name of process.argv.slice(2)) {
  const meta = JSON.parse(fs.readFileSync(`${W}${name}/${name}.meta.json`, 'utf8'));
  const g = await parse(fs.readFileSync(`${W}${name}/${name}.glb`));
  g.scene.updateMatrixWorld(true);
  const r = { model: name, errors: [] };
  let verts = 0, tris = 0, meshes = 0, skinned = 0, maxBindErr = 0;
  g.scene.traverse((o) => {
    if (!o.isMesh) return;
    meshes++; verts += o.geometry.attributes.position.count; tris += o.geometry.index.count / 3;
    if (o.isSkinnedMesh) {
      skinned++;
      o.skeleton.update();
      const pos = o.geometry.attributes.position, v = new THREE.Vector3(), w = new THREE.Vector3();
      for (let i = 0; i < pos.count; i += Math.max(1, Math.floor(pos.count / 400))) {
        v.fromBufferAttribute(pos, i); w.copy(v); o.applyBoneTransform(i, w);
        maxBindErr = Math.max(maxBindErr, w.distanceTo(v));
      }
    }
  });
  Object.assign(r, { meshes, vertices: verts, triangles: tris, skinnedMeshes: skinned, bindPoseSkinErr: maxBindErr, bones: meta.bones });
  if (meshes !== meta.meshes.length) r.errors.push(`mesh count ${meshes} != ${meta.meshes.length}`);
  if (verts !== meta.vertexCount) r.errors.push(`vertices ${verts} != ${meta.vertexCount}`);
  if (tris !== meta.triangleCount) r.errors.push(`triangles ${tris} != ${meta.triangleCount}`);
  if (maxBindErr > 1e-4) r.errors.push('bind pose skin error ' + maxBindErr);
  r.clips = g.animations.map((c) => {
    const mc = meta.clips.find((x) => x.name === c.name);
    if (mc && Math.abs(c.duration - mc.frames / 60) > 1e-5 && mc.frames) r.errors.push(`clip ${c.name} duration`);
    return { name: c.name, duration: +c.duration.toFixed(4), frames: mc?.frames, tracks: c.tracks.length, loop: mc?.loop };
  });
  const box = new THREE.Box3().setFromObject(g.scene);
  r.bbox = { min: box.min.toArray().map((x) => +x.toFixed(4)), max: box.max.toArray().map((x) => +x.toFixed(4)) };
  fails += r.errors.length;
  fs.writeFileSync(`${OUT}${name}.json`, JSON.stringify(r, null, 1));
  console.log(`${name}: meshes=${meshes} verts=${verts} tris=${tris} skinned=${skinned} bones=${meta.bones} bindErr=${maxBindErr.toExponential(2)} clips=${r.clips.map((c) => c.name + ':' + c.frames).join(',')} errors=${r.errors.length} ${r.errors.join('; ')}`);
}
console.log('total errors', fails);
