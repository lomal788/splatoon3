import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeTexSrtRowsZeroRotation} from '../client/render/anim/material_texsrt.ts';
const fixture=JSON.parse(readFileSync(new URL('./fixtures/material_texsrt_r9_native.json',import.meta.url),'utf8'));
const bits=n=>new Uint32Array(new Float32Array([n]).buffer)[0];
test('Maya zero rotation matches 313 original callback converter outputs, six f32 lanes/24 bytes',()=>{
 assert.equal(fixture.samples.length,313);assert.deepEqual(fixture.stubs,[]);assert.equal(fixture.table0[0],1);assert.equal(fixture.table0[1],0);
 for(const s of fixture.samples){const rows=nativeTexSrtRowsZeroRotation(s.srt);assert.ok(rows,s.label);assert.deepEqual(rows.map(bits),s.bits,s.label);assert.equal(s.returnedBytes,24);}
});
test('actual Tank/Bottle active matrix lanes differ from identity and unsupported modes remain explicit',()=>{
 const t=fixture.samples.find(s=>s.label==='native static Tank tex_mtx1'),b=fixture.samples.find(s=>s.label==='native static Bottle tex_mtx0');
 assert.ok(Math.abs(nativeTexSrtRowsZeroRotation(t.srt)[5]+.6)<1e-6);assert.equal(nativeTexSrtRowsZeroRotation(b.srt)[5],-1);
 assert.equal(nativeTexSrtRowsZeroRotation({...t.srt,Rotation:.1}),null);assert.equal(nativeTexSrtRowsZeroRotation({...t.srt,Mode:'Mode3dsMax'}),null);
 assert.equal(nativeTexSrtRowsZeroRotation({...t.srt,Scaling:{X:Infinity,Y:1}}),null);
});
