// Hoian_UBER 1714/946 ink branch; docs/graphics/reference_ink_surface.md.
// CPU reconstructions are references, not native GPU or SDK sinf bit equivalence.
import { F, add, sub, mul, clamp, type V3 } from "./graphics_math.ts";

export const INK_DAY_PARAMS = Object.freeze({
  threshold:F(.3), roughness:F(.05), fresnel:F(.015), anisotropy:F(.5),
  normalIntensity:F(1.8), rimIntensity:F(.625), rimBlend:F(.875),
  thicknessFloor:F(.95), thicknessWall:F(.75), thicknessAmplitude:F(.015625), thicknessPeriod:F(.03125),
  mottariBase:F(1.75), mottariAmplitude:F(.0625), mottariPeriod:F(.08),
});
/** Native initialization/texel/pack path, NOT the normalized step of a web atlas. */
export const NATIVE_LOBBY_INK_STEP = Object.freeze([F(1/3200),0] as const);
const mad=(a:number,b:number,c:number):number=>F(F(a)*F(b)+F(c));
const d3=(a:V3,b:V3):number=>mad(a[2],b[2],mad(a[1],b[1],mul(a[0],b[0])));
const normalize=(v:V3):V3=>{const r=F(1/Math.sqrt(d3(v,v)));return v.map(x=>mul(x,r)) as V3;};
const cross=(a:V3,b:V3):V3=>[
  mad(a[1],b[2],-mul(a[2],b[1])),mad(a[2],b[0],-mul(a[0],b[2])),mad(a[0],b[1],-mul(a[1],b[0])),
];

export function inkSurfaceFrame(frame:number):[number,number,number,number] {
  const p=INK_DAY_PARAMS,f=F(Math.trunc(frame));
  const thickness=mul(p.thicknessAmplitude,F(Math.sin(mul(p.thicknessPeriod,f))));
  return [clamp(add(p.thicknessFloor,thickness)),clamp(add(p.thicknessWall,thickness)),
    Math.max(0,add(p.mottariBase,mul(p.mottariAmplitude,F(Math.sin(mul(p.mottariPeriod,f)))))),F(f/60)];
}
/** The narrow ramp adds ties. Do not pick one channel or divide by sum(weights). */
export function inkNearMaxWeights(c:V3):V3 {
  c=c.map(F) as V3;const m=Math.max(c[2],Math.max(c[0],c[1]));
  return c.map(x=>clamp(mul(add(sub(x,m),F(9.99999975e-5)),100000000))) as V3;
}
export function inkSurfaceGate(maximum:number,threshold=INK_DAY_PARAMS.threshold):boolean {
  return Math.min(mul(clamp(sub(maximum,threshold)),1000),1)>.5;
}
export interface InkSurfaceSample {
  color:V3; neighborU:V3; neighborV:V3;
  vertexNormal:V3; materialNormal:V3; tangent:V3;
  ink:readonly V3[]; inkBright:readonly V3[];
  frame:number; emission:number;
}
export function inkSurfaceSample(input:InkSurfaceSample):{
  active:boolean; weights:V3; albedo:V3; normal:V3; irradianceNormal:V3; emission:V3; thickness:number; roughness:number; fresnel:number;
} {
  const p=INK_DAY_PARAMS,c=input.color.map(F) as V3,w=inkNearMaxWeights(c),m=Math.max(c[2],Math.max(c[0],c[1]));
  const a=clamp(sub(m,p.threshold)),t=clamp(mul(a,p.rimBlend)),nv=normalize(input.vertexNormal),nm=normalize(input.materialNormal);
  const frame=inkSurfaceFrame(input.frame),q=mad(clamp(nv[1]),sub(frame[0],frame[1]),frame[1]);
  const weighted=(values:readonly V3[],channel:number):number=>mad(w[2],values[2][channel],mad(w[0],values[0][channel],mul(w[1],values[1][channel])));
  const albedo=[0,1,2].map(ch=>{const bright=weighted(input.inkBright,ch),ink=weighted(input.ink,ch),rim=mul(bright,p.rimIntensity);
    return mad(mad(bright,-p.rimIntensity,ink),t,rim);}) as V3;
  const gradient=(n:V3):number=>mul(mad(sub(c[2],n[2]),w[2],mad(sub(c[0],n[0]),w[0],mul(sub(c[1],n[1]),w[1]))),p.normalIntensity);
  const gu=gradient(input.neighborU),gv=gradient(input.neighborV),b=cross(nv,input.tangent);
  const ni=normalize(nv.map((n,ch)=>add(n,mad(input.tangent[ch],gu,mul(b[ch],gv)))) as V3);
  const normal=nm.map((n,ch)=>mad(q,sub(ni[ch],n),n)) as V3;
  const irr:[number,number,number]=[mul(normal[0],p.anisotropy),mad(sub(normal[1],1),p.anisotropy,1),mul(normal[2],p.anisotropy)];
  return {active:inkSurfaceGate(m),weights:w,albedo,normal,irradianceNormal:irr,emission:albedo.map(x=>mul(x,input.emission)) as V3,
    thickness:q,roughness:p.roughness,fresnel:p.fresnel};
}
