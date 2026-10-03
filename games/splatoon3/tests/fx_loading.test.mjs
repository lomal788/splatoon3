import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from '../../../node_modules/esbuild/lib/main.js';

const runtime = await build({
  entryPoints: [fileURLToPath(new URL('../client/fx/index.ts', import.meta.url))],
  bundle: true, write: false, platform: 'node', format: 'esm',
  define: { __GAME_BASE__: '"/game/splatoon3/"', __DEV__: 'true' }, logLevel: 'silent',
});
const work = new URL('../../../../analysis/port_priority_r4/fx_loading/', import.meta.url);
mkdirSync(work, { recursive:true });
const runtimePath = fileURLToPath(new URL('actual_runtime.mjs', work));
writeFileSync(runtimePath, runtime.outputFiles[0].contents);
const { FxSystem, createFxView } = await import(pathToFileURL(runtimePath).href);
const THREE = await import('three');
const fixture = JSON.parse(readFileSync(new URL('./fixtures/fx_native_port.json', import.meta.url)));
const row = fixture.rows.find(r => r.def.shaderIndex === 1897);
const matrix = { o: [0,0,0], x:[1,0,0], y:[0,1,0], z:[0,0,1] };
const world = () => ({ data: { map:'Lby_Lobby00', players:[], tables:{} }, shared:new Map(), frame:0,
  events:{list:[],clear(){this.list.length=0;}} });
const data = ready => ({ ready, emitters:new Map([[row.key, {shaderIndex:1897, life:10, emitRate:1}]]),
  emitterTex:new Map(), emitterSamplers:new Map(), emitterPrim:new Map(), prims:new Map(), textures:new Map(),
  elink:new Map(), slink:new Map(), teamColors:null });
const eset = row.key.slice(0, row.key.indexOf('/'));

test('slow FX loading never caches placeholder material before native keys arrive', () => {
  const d=data(false), sys=new FxSystem(world(), new THREE.PerspectiveCamera(), d);
  assert.equal(sys.spawnEset(eset,matrix,[1,0,0]),null);
  assert.deepEqual(sys.stats(),{emitters:0,bullets:0,batches:0});
  assert.equal(sys.missing.size,0);
  d.emitters.set(row.key,row.def); d.ready=true;
  const h=sys.spawnEset(eset,matrix,[1,0,0]); assert(h?.alive());
  assert.equal(sys.root.children[0].material.userData.knownShaderContract,true);
  assert.equal(sys.root.children[0].material.uniforms.uAlphaN.value,row.def.numAlpha0Keys);
  sys.dispose();
});

test('settled failed/empty loading still permits the explicit legacy fallback', () => {
  const sys=new FxSystem(world(),new THREE.PerspectiveCamera(),data(true));
  assert(sys.spawnEset(eset,matrix,[1,0,0])?.alive());
  assert.equal(sys.stats().batches,1);
  assert.equal(sys.root.children[0].material.userData.knownShaderContract,false);
  sys.dispose();
});

test('actual view postpones owner/event construction while the bundle promise is pending', () => {
  const w=world(), scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera();
  const loader={loadCatalog:()=>new Promise(()=>{})};
  const view=createFxView({world:w,scene,camera,assets:loader});
  w.frame=20; view.update(w,1);
  const sys=globalThis.__splatoon3_fx;
  assert.equal(sys.lastFrame,-1);
  assert.equal(sys.root.children.length,0);
  assert.equal(sys.missing.size,0);
  view.dispose(); delete globalThis.__splatoon3_fx;
});
