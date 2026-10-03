import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  nativeVisualUv, nativeVisualTangent, nativeVisualWorld,
  nativePackPaintUv, nativePackPaintSwitch, nativePackPaintTangent, nativeChoosePaintUv,
  webDecodePaintUv, webDecodePaintSwitch, webDecodePaintTangent,
} from '../core/paint/native_visual_uv.ts';

const fixture=JSON.parse(readFileSync(new URL('./fixtures/native_visual_uv.json',import.meta.url),'utf8'));
const fromBits=b=>new Float32Array(new Uint32Array([b]).buffer)[0];
const bits=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
const vec=bs=>bs.map(fromBits);

test('ColPaint original UV/switch/tangent writers match 277 inputs including NaN/infinity and signed wrapping',()=>{
  for (const [i,c] of fixture.writers.entries()) {
    assert.deepEqual([...nativePackPaintUv(vec(c.uvBits))],c.uvExpected,`UV writer ${i}`);
    assert.equal(nativePackPaintSwitch(fromBits(c.switchBits)),c.switchExpected,`switch writer ${i}`);
    assert.equal(nativePackPaintTangent(vec(c.tangentBits),vec(c.matrixBits)),c.tangentExpected,`tangent writer ${i}`);
  }
});

test('ColPaint original finite panel UV/tangent leaves match all f32 output bits for 256 inputs and 42 directions',()=>{
  for (const [i,c] of fixture.panels.entries()) {
    const basis=c.basisBits.map(vec),m=vec(c.matrixBits);
    assert.deepEqual(nativeVisualUv(vec(c.positionBits),basis,vec(c.minBits),vec(c.maxBits),m).map(bits),c.uvExpectedBits,`panel UV ${i}`);
    assert.deepEqual(nativeVisualTangent(basis,m)?.map(bits),c.tangentExpectedBits,`panel tangent ${i}`);
  }
});

test('ColPaint decoded vertex NaN guard, optional shape, then root match 128 original instruction-block outputs',()=>{
  for (const [i,c] of fixture.worldBlocks.entries()) {
    assert.deepEqual(nativeVisualWorld(vec(c.positionBits),vec(c.rootBits),c.shapeBits?vec(c.shapeBits):undefined).map(bits),c.expectedBits,`world transform ${i}`);
  }
});

test('singular native tangent remains unconfirmed while absent UV matrix retains native explicit defaults',()=>{
  const basis=[[1,0,0],[0,1,0],[0,0,1]];
  assert.equal(nativeVisualTangent(basis,[1,2,0,2,4,0]),undefined);
  assert.deepEqual(nativeVisualTangent(basis,null),[0,1,0]);
  assert.deepEqual(nativeVisualUv([3,4,5],basis,[0,0,0],[1,1,1],null),[0,0]);
});

test('paint shader selection uses strict negative switch and applies offset before Y flip',()=>{
  assert.deepEqual(nativeChoosePaintUv([.1,.2,.3,.4],-1,[.01,.02]),[Math.fround(Math.fround(.3)+Math.fround(.01)),Math.fround(1-Math.fround(Math.fround(.4)+Math.fround(.02)))]);
  assert.deepEqual(nativeChoosePaintUv([.1,.2,.3,.4],-0,[0,0]),[Math.fround(.1),Math.fround(1-Math.fround(.2))]);
});

test('WebGL SNORM adapters preserve negative packed bytes and clamp only the signed minimum',()=>{
  assert.deepEqual(webDecodePaintUv([0,32767,32768,65535]),[0,1,-1,Math.fround(-1/32767)]);
  assert.equal(webDecodePaintSwitch(127),1);assert.equal(webDecodePaintSwitch(128),-1);
  assert.equal(webDecodePaintSwitch(255),Math.fround(-1/127));
  assert.deepEqual(webDecodePaintTangent(511|(512<<10)|(1023<<20)),[1,-1,Math.fround(-1/511)]);
  // An out-of-range UV wraps in the native CPU writer before GPU normalization.
  const u=nativePackPaintUv([1.2,0,0,0]);assert.ok(webDecodePaintUv(u)[0]<0);
});
