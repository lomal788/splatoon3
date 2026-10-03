import { readFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';
import { build } from '../../../node_modules/esbuild/lib/main.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
const fixtures = JSON.parse(await readFile(new URL('./fixtures/fx_emitter_fixture.json', import.meta.url), 'utf8'));
const assetPath = resolve(root, 'web/games/splatoon3/assets/effects/shooter');
const asset = JSON.parse(await readFile(resolve(assetPath, 'emitters.json'), 'utf8'));
const dataPath = resolve(root, 'web/games/splatoon3/client/audio/data.ts');
// Execute the shipped loader, including fallback JSON and its real asynchronous bundle path.
const runtime = await build({ entryPoints: [dataPath], bundle: true, write: false, platform: 'node', format: 'esm',
  define: { __GAME_BASE__: '"/game/splatoon3/"', __DEV__: 'false' }, logLevel: 'silent' });
const { fxData } = await import('data:text/javascript;base64,' + Buffer.from(runtime.outputFiles[0].contents).toString('base64'));
const files = new Map([['emitters.json', asset]]);
for (const info of Object.values(asset.textures)) if (info.kind === 'vat') {
  const bytes = await readFile(resolve(assetPath, info.file));
  files.set(info.file, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
}
async function load(reverse = false) {
  const b = { names: () => [...files.keys()].sort().toReversed().slice().sort((a,b) => reverse ? b.localeCompare(a) : a.localeCompare(b)),
    json: (name) => files.get(name), bytes: (name) => files.get(name), has: (name) => files.has(name) };
  const cat = { version: 1, bundles: { 'effect/shooter': {dir:'effects/shooter/',files:[...files.keys()]} } };
  const loader = { catalog:cat, loadCatalog:async()=>cat, load:async()=>new Map([['effect/shooter', b]]) };
  const data = fxData(loader, { data: { map:'Lby_Lobby00', players:[], tables:{} } });
  for (let i=0; !data.ready && i<10; i++) await new Promise(setImmediate);
  assert(data.ready); return data;
}
const data = await load();
function bits(value) { const a = new Float32Array([value]); return new Uint32Array(a.buffer)[0]; }
function keyBits(keys) { return keys.map(key => key.map(bits)); }

for (const row of fixtures.rows) test(`FX native keys reach actual loader: ${row.key}`, () => {
  const def = data.emitters.get(row.key); assert(def);
  assert.deepEqual(keyBits(def.scaleKeys), keyBits(row.scale.keys));
  assert.equal(def.numScaleKeys, row.scale.numKeys);
  for (const channel of ['color0','alpha0','color1','alpha1']) {
    assert.deepEqual(keyBits(def[channel+'Keys']), keyBits(row.color[channel].keys));
    assert.equal(def['num'+channel[0].toUpperCase()+channel.slice(1)+'Keys'], row.color[channel].numKeys);
    assert.equal(def[channel+'Type'], {FIXED:0,RANDOM:1,ANIM:2}[row.color[channel].type]);
  }
  assert.deepEqual(def.nativeRender, row.nativeRender);
  assert.deepEqual(def.keyInterpolation, row.fields.keyInterpolation);
});

test('FX FIXED patch differs from serialized animation; ANIM alpha1 remains', () => {
  assert.equal(data.emitters.get('WpShtrBullet1Emit/ball').alpha0Keys[0][0],1);
  assert.equal(data.emitters.get('WpShtrBullet1Emit/ball').alpha1Keys[0][0],5);
  assert.equal(data.emitters.get('WpCmnBulletSplash1Emit/ball_Copy1').alpha0Keys[0][0],1);
  assert.equal(data.emitters.get('WpCmnBulletSplash1Emit/ball_Copy1').alpha1Keys[0][0],3);
  assert.equal(data.emitters.get('CmnWallSplash1Emit/Ripple').alpha1Type,2);
  assert.equal(data.emitters.get('CmnWallSplash1Emit/Ripple').alpha1Keys[0][0],2);
});

test('FX Flash sampler slots keep normal and alpha masks separate', () => {
  assert.deepEqual(data.emitterSamplers.get('WpShtrMzfNml/Flash').map(t=>[t.slot,t.name]),
    [[0,'gradation02_fi'],[1,'splash04_nrm'],[2,'splash04_fi']]);
  assert.deepEqual(data.textureInfo.get('splash04_fi').componentSelectors,[2,2,2,2]);
  assert.deepEqual(data.textureInfo.get('splash09_fia').componentSelectors,[2,2,2,3]);
  assert.equal(data.textureInfo.get('splash09_fia').componentSelectorsApplied,true);
});

for (const name of ['bulletshtr_vsp','bulletcmn_vsp']) test(`FX VAT raw half and row orientation: ${name}`, () => {
  const texture = data.textures.get(name), info = data.textureInfo.get(name);
  assert(texture?.isDataTexture); assert.equal(texture.type,1016); // THREE.HalfFloatType
  assert.equal(texture.image.width,info.width); assert.equal(texture.image.height,info.height);
  assert.deepEqual(texture.image.data,new Uint16Array(files.get(info.file)));
  assert.equal(texture.flipY,false); assert.equal(texture.generateMipmaps,false);
  assert.equal(texture.colorSpace,''); assert.equal(texture.minFilter,1003); assert.equal(texture.magFilter,1003);
});

test('FX JSON and VAT loading works when bundle iteration is reversed', async () => {
  const reversed = await load(true);
  assert.deepEqual(reversed.textures.get('bulletshtr_vsp').image.data,data.textures.get('bulletshtr_vsp').image.data);
  assert.deepEqual(reversed.emitters.get('WpShtrMzfNml/Flash').scaleKeys,data.emitters.get('WpShtrMzfNml/Flash').scaleKeys);
});
