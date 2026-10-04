import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HDRCompose,tone4} from '../client/render/post.ts';
import {colorCorrectionPacket,colorCorrectionLUT,ccPixel,sampleColorLUT} from '../client/render/post_math.ts';
import {bloomPacket,bloomMask,bloomGameApply,NativeBloom} from '../client/render/bloom.ts';

const fx=JSON.parse(readFileSync(new URL('./fixtures/r11_post_native.json',import.meta.url),'utf8'));
const env=JSON.parse(readFileSync(new URL('../assets/maps/Lby_Lobby00/env.json',import.meta.url),'utf8'));
const F=Math.fround;
const bits=x=>new Uint32Array(new Float32Array([x]).buffer)[0];
const packet=colorCorrectionPacket(env.rendering.PostEffect.ColorGrading);
const lut=colorCorrectionLUT(packet);

function webShader(h,b,exposure){
 const x=[0,1,2].map(i=>F(F(h[i]*exposure)+b[i]));
 const l=F(F(F(x[0]*.2989)+F(x[1]*.5866))+F(x[2]*.1144));
 const t=F(1-F(2**F(l*-1.44269502)));
 const zero=l===0&&x.every(v=>v===0);
 const c=x.map(v=>{if(zero)return 0;const y=F(v*F(t/l));return Math.min(1,Math.max(0,F(y+F(F(F(1-F(2**F(v*-1.44269502)))-y)*F(t*t)))));});
 const coord=c.map(v=>F(F(v*.875)+.0625));
 const s=sampleColorLUT(lut,c);
 return {c,coord,out:s.map(v=>F(Math.abs(v)**F(1/2.2)))};
}

test('r11 CC LUT: web 8³ bake = native color_correction_map shader run (1536/1536 f32 bits), R11G11B10F storage bits',()=>{
 const inv=F(1/7);let zc=0,eq=0;
 for(let z=0;z<8;z++){for(let y=0;y<8;y++)for(let x=0;x<8;x++){const i=x+8*(y+8*z);
  const w=ccPixel([F(x*inv),F(y*inv),zc],packet);
  for(let c=0;c<3;c++){assert.equal(bits(w[c]),bits(fx.lutNativeRaw[i][c]),`texel ${i} ch ${c}`);eq++;
   assert.equal(bits(lut.rgba[i*4+c]),bits(fx.lutQuantized[i][c]),`quantized ${i} ${c}`);}}
  zc=F(zc+inv);}
 assert.equal(eq,1536);
});

test('r11 HDRCompose#201: web shader expression and tone4 match native GLSL on dark→bright and ink samples',()=>{
 let maxCoord=0,maxOut=0;
 fx.hdr.forEach((h,i)=>{
  const n=fx.hdrcompose[i],w=webShader(h,fx.bloom[i],fx.exposure);
  for(let c=0;c<3;c++){maxCoord=Math.max(maxCoord,Math.abs(w.coord[c]-n.lutCoord[c]));maxOut=Math.max(maxOut,Math.abs(w.out[c]-n.out[c]));}
  assert.equal(n.out[3],h[3]);
  const cpu=tone4([0,1,2].map(k=>F(F(h[k]*fx.exposure)+fx.bloom[i][k])),1);
  for(let c=0;c<3;c++)assert.ok(Math.abs(cpu[c]-n.toneFromCoord[c])<4e-6,`tone4 ${i}/${c} ${cpu[c]} ${n.toneFromCoord[c]}`);
 });
 assert.ok(maxCoord<=2e-7,`LUT coord ${maxCoord}`);
 assert.ok(maxOut<=2e-6,`final ${maxOut}`);
 const src=new HDRCompose().material.fragmentShader;
 for(const s of ['vec3(.2989,.5866,.1144)','exp2(l*-1.44269502)','c*ccCoeff.x+ccCoeff.y','pow(abs(c),vec3(1./2.2))','postColor=vec4(c,h.a)'])assert.ok(src.includes(s),s);
});

test('r11 bloom apply 0x7102b699c0: +0x5a0 = lerp(old.ClampedLuminance, new.Intensity, t) (259 native runs)',()=>{
 for(const k of fx.bloomApply.cases){
  const s=bloomGameApply(k.A,k.B,k.t);
  assert.equal(bits(s.Threshold),bits(k.native['0x48']));assert.equal(bits(s.ThresholdRange),bits(k.native['0x68']));
  assert.equal(bits(s.Intensity),bits(k.native['0x88']));assert.equal(bits(s.ClampedLuminance),bits(k.native['0x5a0']));
 }
 assert.equal(bloomGameApply().ClampedLuminance,1);
 const b=new NativeBloom();b.configure(env.rendering.PostEffect.Bloom,true);
 assert.equal(b.packet.threshold[0],1);assert.equal(b.packet.threshold[2],1);b.dispose();
});

test('r11 bloom_mask#129: web mask = native GLSL for clamp 5 (agl default) and Lby clamp 1',()=>{
 const packets=[bloomPacket({ClampedLuminance:5}),bloomPacket(bloomGameApply())];
 fx.mask.forEach((m,j)=>{
  assert.deepEqual(packets[j].weight.map(bits),m.weight.map(bits));assert.deepEqual(packets[j].threshold.map(bits),m.threshold.map(bits));
  fx.hdr.forEach((h,i)=>{const w=bloomMask(h,packets[j]);for(let c=0;c<4;c++)assert.ok(Math.abs(w[c]-m.out[i][c])<=Math.abs(m.out[i][c])*2e-7+1e-12,`mask ${j} ${i} ${c} ${w[c]} ${m.out[i][c]}`);});
 });
});
