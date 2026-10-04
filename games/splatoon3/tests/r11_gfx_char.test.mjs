// r11 gfx-char: web ports vs original v0 execution (web/tools/r11_gfx_char_emu.py → fixtures/r11_gfx_char_native.json).
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {TankGauge} from '../client/render/anim/tank_gauge.ts';
import {nativeHeadMatrix} from '../client/render/model.ts';
import {SeadRandom,seadRandomIndex} from '../client/render/teamcolor.ts';
import {hairArrangeLocal,nativePow,clothEffectiveDt,clothDampingCoefficient,clothIntegrateLane,standardLink,bendLink,f32bits,bitsf32} from '../client/render/anim/hair_cloth.ts';
import {nativeClipName} from "../client/render/anim/clip_name.ts";
import {lodStageDistance} from '../client/render/anim/lod.ts';
import {sampleNativeMaterialCurve} from '../client/render/anim/material_channels.ts';

const N=JSON.parse(readFileSync(new URL('./fixtures/r11_gfx_char_native.json',import.meta.url),'utf8'));
const B=bitsf32,U=f32bits;

test('tank gauge, lock, sub marker and InkShortage latch/request/stop/TankEmpty match original 0x71026fb6d0 sequences',()=>{
  const c=N.tank.constants;
  assert.deepEqual([c.followUp,c.followDown,c.lockStep,c.emptyFrames],[U(.5),U(.6),U(.1),60]);
  let frames=0;
  for(const seq of N.tank.sequences){
    const g=new TankGauge();
    for(const f of seq.frames){
      if(f.lack)g.lack();
      assert.equal(g.shortage,f.state.t0,'web lack/tick timer agrees with harness timer');
      g.subShortage=f.state.t4;
      const out=g.update({subCost:B(f.in[0]),remaining:B(f.in[1]),lock:B(f.in[2]),shortageEnabled:seq.shortageEnabled});
      const want=[['frame',0,U(out.gauge)],['frame',4,U(out.subMarker)],['frame',3,U(out.inkLock)]];
      if(out.tankEmpty)want.push(['xlink','TankEmpty']);
      for(const r of out.requests)want.push(['request',r,r==='InkShortage'?1:2]);
      if(out.stopShortage)want.push(['stop',1]);
      if(out.inkShortageGauge!==null)want.push(['frame',2,U(out.inkShortageGauge)]);
      const key=a=>a.map(x=>JSON.stringify(x)).sort();
      assert.deepEqual(key(want),key(f.calls),JSON.stringify({frames,f,out}));
      assert.deepEqual([U(g.r),U(g.lockValue),U(g.subCostLatched),+g.latch52c,+g.latch52d],[f.state.r,f.state.lock,f.state.sub,f.state.c,f.state.d]);
      g.tickTimers();frames++;
    }
  }
  assert.ok(frames>=4000);
});

test('hat Head·P·ManualBindSRT matrix is bit-identical to original 0x71026e613c (fused FMLA order)',()=>{
  for(const c of N.head.cases)assert.deepEqual(nativeHeadMatrix(c.B.map(B),c.S.map(B)).map(U),c.O);
  assert.ok(N.head.cases.length>150);
});

test('lobby team row draw: sead::Random xorshift128 and umull>>32 index match original 0x7101179c80 block',()=>{
  for(const c of N.teamRandom.cases){
    const r=new SeadRandom(c.state),v=r.nextU32();
    assert.equal(seadRandomIndex(v,c.n),c.index);assert.deepEqual(r.s,c.next);
  }
});

test('HairArrange bone local (rotation FMLA, 0.01 scale floor, +0x338 transform swap) matches original 0x71026df700',()=>{
  let n=0;
  for(const params of N.hairArrange.cases)for(const p of params){
    const out=hairArrangeLocal(p.bind.map(B),p.bindScale.map(B),{rotation:p.rotation.map(B),scale:p.scale.map(B),transform:p.transform.map(B),animReduceRt:1},p.swapTransform);
    assert.deepEqual(out.matrix.map(U),p.outMatrix);assert.deepEqual(out.scale.map(U),p.outScale);n++;
  }
  assert.ok(n>100);
});

test('clip name candidates/lookup order and no-entry fallback match original 0x710244d0b0',()=>{
  for(const c of N.clipName.cases){
    const set=new Set(c.clips);
    const r=nativeClipName(c.name,c.keys,{detail:c.detail,category:c.category,emote:c.emote},x=>set.has(x));
    assert.deepEqual(r.tried,c.tried,c.name+' '+c.keys);assert.equal(r.clip,c.returned);
  }
});

test('LOD distance selector (view Z, radius, bias, hysteresis) matches original 0x7103788760',()=>{
  for(const c of N.lod.cases)
    assert.equal(lodStageDistance({zView:B(c.zView),radius:B(c.radius),start:B(c.start),inverseGap:B(c.inverseGap),viewInput:B(c.viewInput),
      bias:B(c.bias),hysteresis:B(c.hysteresis),count:c.count,minimum:c.minimum,old:c.old}),c.stage,JSON.stringify(c));
});

test('tank Gauge/InkShortage curves sampled by the web reader equal original float reader 0x710088e380',()=>{
  const dump=JSON.parse(readFileSync(new URL('../assets/characters/Player00/data/tank_anim_native.json',import.meta.url),'utf8'));
  const curves=new Map();
  for(const b of dump.skeletal.Gauge.bones)for(const c of b.curves)curves.set('skeletal:Gauge:'+b.name,c);
  for(const a of dump.material.clips)for(const m of a.materials)m.curves.forEach((c,i)=>curves.set(`material:${a.name}:${m.material}:${i}`,c));
  let n=0;
  for(const s of N.curves.samples){const c=curves.get(s.curve);assert.ok(c,s.curve);assert.equal(U(sampleNativeMaterialCurve(c,B(s.frame))),s.result,s.curve+'@'+B(s.frame));n++;}
  assert.ok(n>600);
});

test('cloth damping pow, effectiveDt/coefficient, integration and Standard/Bend links match original hcl functions',()=>{
  for(const [b,e,r] of N.cloth.pow)assert.equal(U(nativePow(B(b),B(e))),r,`${B(b)}^${B(e)}`);
  for(const c of N.cloth.integrate){
    const eff=clothEffectiveDt(B(c.dt),c.kind,B(c.scale),c.substeps);assert.equal(U(eff),c.effectiveDt);
    const co=clothDampingCoefficient(B(c.damping),eff);assert.equal(U(co),c.coefficient);
    const n=c.current.length/4;
    for(let j=0;j<n;j++)for(let k=0;k<4;k++)
      assert.equal(U(clothIntegrateLane(B(c.current[4*j+k]),B(c.previous[4*j+k]),B(c.gravity[k]),B(c.props[4*j]),B(c.props[4*j+1]),co,eff)),c.out[4*j+k]);
  }
  for(const l of N.cloth.links){
    const a=l.a.map(B),b=l.b.map(B),[wa,wb]=l.invMass.map(B);
    if(l.bend)bendLink(a,b,B(l.bendMinLength),B(l.stretchMaxLength),B(l.bendStiffness),B(l.stretchStiffness),wa,wb,B(l.scalar));
    else standardLink(a,b,B(l.restLength),B(l.stiffness),wa,wb,B(l.scalar));
    assert.deepEqual([...a,...b].map(U),l.out);
  }
});
