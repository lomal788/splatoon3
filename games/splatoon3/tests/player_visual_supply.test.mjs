import {test} from 'node:test';
import assert from 'node:assert/strict';
import {build} from '../../../node_modules/esbuild/lib/main.js';
import {createPlayerState,updateOrdinaryDisplay} from '../core/player/index.ts';
import {makePlayerParam} from '../core/player/gear.ts';
import {Layer} from '../core/types.ts';
const bundle=await build({entryPoints:[new URL('../client/render/anim/animator.ts',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1')],bundle:true,write:false,platform:'node',format:'esm'});
const {PlayerAnimator}=await import('data:text/javascript;base64,'+Buffer.from(bundle.outputFiles[0].text).toString('base64'));
const make=()=>{const p=createPlayerState(1,0);p.state=0x85;p.step.cls=0;return p;};
const res={supported:true,gtri:0,gn:[0,1,0],gp:[0,0,0],contacts:[]};

test('Ordinary contact adapter supplies sphere support to delayed display; missing support stays explicit',()=>{
 const p=make(),calls=[];const w={collision:{fallback:false,sweepSphere(...args){calls.push(args);return {t:.5};}}};
 updateOrdinaryDisplay(w,p,res);assert.equal(p.displayBinding.supported,true);assert.equal(p.display.hidden,true);assert.equal(p.display.delay,3);assert.equal(p.inkFastStealth,true);
 assert.equal(calls[0][2],Math.fround(.01));assert.equal(calls[0][3],Layer.Ground);assert.deepEqual(calls[0][4],{layerIndex:1,hitMask:8,subIndex:0,subMask:0xffffffff});
 const before={...p.display};w.collision.sweepSphere=()=>null;updateOrdinaryDisplay(w,p,res);assert.equal(p.displayBinding.supported,false);assert.deepEqual(p.display,before);assert.equal(p.inkFastStealth,undefined);
 // Leaving own paint does not require an invented edge value and uses the native delayed latch.
 p.step.cls=4;for(let k=0;k<3;k++)updateOrdinaryDisplay(w,p,res);assert.equal(p.display.hidden,false);assert.equal(p.inkFastStealth,false);
});

test('Actual WallJumpChargeFrm data endpoints feed the display cache rather than the old synthetic 60',()=>{
 assert.equal(makePlayerParam({actionUp:0}).wallJumpChargeFrames,45);
 assert.equal(makePlayerParam({actionUp:57}).wallJumpChargeFrames,5);
});

test('B7a0 hides the display while the original AS commands keep ticking; reset requests remain separate',()=>{
 const a=new PlayerAnimator(()=>({frames:135,loop:true}),()=>({frames:120,loop:true}),'Shtr');
 const input={state:0x85,speed:0,dead:false,formCounter:0,animRate:1,displayHidden:false};
 a.step(input);assert.equal(a.disp.squid,true);const before=a.squid.progress().cur;
 a.step({...input,displayHidden:true});assert.deepEqual(a.disp,{body:false,hlf:false,squid:false});assert.equal(a.f0,90);assert.ok(a.squid.progress().cur>before);assert.ok(a.displayResets.includes('squid'));
 a.step(input);assert.equal(a.disp.squid,true);assert.ok(a.squid.progress().cur>before);
});

test('Selected shooter supplies Shtr category/detail to actual ASB and produces a shooter Shoot skeletal leaf',()=>{
 const a=new PlayerAnimator(()=>({frames:135,loop:true}),()=>({frames:120,loop:true}),'Shtr');
 for(let k=0;k<5;k++)a.step({state:0x59,speed:0,dead:false,formCounter:0,animRate:1,displayHidden:false});
 assert.equal(a.bb.str.get('WeaponCategory'),'Shtr');assert.equal(a.bb.str.get('WeaponDetail'),'Shtr');
 assert.ok(a.humanLeaves(1).some(l=>l.type===3&&/Shoot_Shtr/.test(l.clip)),JSON.stringify(a.humanLeaves(1)));
});
