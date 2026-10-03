// Confirmed shader consumers; runtime Custom1/dynamic inputs remain a web bridge.
// docs/effect_sound/effect_resources.md §2.1.1/2.2.5.1, fx_shader_inputs_r2.md §6.
export const FX_PROGRAMS = new Set([1383,1385,1202,1747,1897,1940,1885,1886]);
export const FX_WEB_DEFAULTS = Object.freeze({ vatRate:1, linkedAlpha:1, alphaRemap:[1,0], roughness:.25, fresnel:.04 });
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
export function vatColumns(width:number,age:number,rate:number): {x0:number;x1:number;blend:number} {
  const q=clamp(Math.min(age*rate/(width+.00001)+.00001,.99999));
  const f=width*(q-Math.floor(q)),x0=Math.trunc(f);
  return {x0,x1:x0<Math.trunc(width-1)?x0+1:x0,blend:f-Math.floor(f)};
}
/** Native compact normal decoded from the A half bits. Actual local axes are X,Y(polar),Z. */
export function decodeVatNormal(h:number):[number,number,number] {
  const j=(h<0x8000?h-0x400:0x8400-h)+0x77ff,phi=j*3.88322115;
  const z=j*2*(-1.6276572e-5)+.999983728,x=Math.abs(z);
  const a=(((x*(-.0187293)+.0742610022)*x-.2121144)*x+1.5707288)*Math.sqrt(1-x);
  const theta=z<0?Math.PI-2*a+a:a;
  return [Math.sin(theta)*Math.cos(phi),z,Math.sin(theta)*Math.sin(phi)];
}
export function shaderAlpha(program:number,t0a:number,t1a:number,t2a:number,vertexAlpha:number,a0:number,a1:number,fade:number,soft:number,linkedAlpha:number,remap:[number,number]=[1,0]): {raw:number;out:number} {
  let raw:number;
  switch(program){
    case 1383:case 1385:raw=clamp(a0*linkedAlpha)*fade;break;
    case 1202:raw=clamp(t1a*t2a*linkedAlpha*a0)*fade;break;
    case 1747:raw=clamp(t0a*linkedAlpha*a0)*fade;break;
    case 1897:raw=soft*clamp((t0a*vertexAlpha-a0)*a1)*fade;break;
    case 1885:case 1886:raw=clamp((t0a*vertexAlpha-a0)*a1)*fade;break;
    default:raw=clamp(t0a*vertexAlpha*a0)*fade;
  }
  return {raw,out:clamp(raw*remap[0]+remap[1])};
}
/** Independently timed C0,A0,C1,A1,scale channels (no shared scale period). */
export function animationTime(age:number,life:number,random:number,period:number,phase:number):number {
  if(period<=0)return age/life;
  const t=(random*phase*period+age)/period;return t-Math.floor(t);
}
export function sampleKey(k:number[][],t:number,mode=0):number[] {
  if(!k.length)return [1,1,1];if(k.length===1||t<k[0][3])return k[0].slice(0,3);
  for(let i=1;i<k.length;i++)if(t<k[i][3]){
    if(mode===1)return k[i-1].slice(0,3);
    const f=(t-k[i-1][3])/(k[i][3]-k[i-1][3]);
    return [0,1,2].map(c=>k[i-1][c]+(k[i][c]-k[i-1][c])*f);
  }
  return k[k.length-1].slice(0,3);
}
