// Selected body5549/face1115/squid3358/hair2855 consumers, not generic Hoian inference.
import {F,clamp,type V3} from "./graphics_math.ts";
export interface CharacterParameters {
  transmissionRate:number;scatteringRate:number;scatterDistance:number;scatteringColor:V3;edgePower:number;
  filmRate:number;filmPower:number;manualFresnel:number;manualFresnelColor:V3;
}
export function characterDirectColor(nDotL:number,color:V3,mask:number,p:CharacterParameters):V3 {
  const n=clamp(nDotL),wrapped=clamp(nDotL+p.scatterDistance)/(1+p.scatterDistance);
  return color.map((c,i)=>F(((clamp(n+p.scatteringColor[i])*wrapped*c-n*c)*mask+n*c))) as V3;
}
export function characterEdge(noV:number,normalDotLight:number,viewDotLight:number,thicknessFactor:number,p:CharacterParameters):number {
  const q=(p.scatteringRate-1)*(p.scatteringRate-1);
  return F(Math.pow(clamp(1-noV*clamp(-normalDotLight)),p.edgePower)*
    (q*(Math.pow(clamp(Math.max(-viewDotLight,.001)),1/p.scatteringRate)-.2)+.200000003)*thicknessFactor);
}
/** Native tank2419/harness4526/bottle320 disable the additional angular edge factor. */
export function characterScatterLobe(viewDotLight:number,scatteringRate:number):number {
  const q=(scatteringRate-1)*(scatteringRate-1);
  return F(q*Math.pow(clamp(Math.max(-viewDotLight,.001)),1/scatteringRate)-q*.2+.200000003);
}
export function characterFilmTau(film:number,transmissionMask:number,p:CharacterParameters):number {
  return F(p.transmissionRate*transmissionMask*(1-film));
}
export function characterFilm(noV:number,mask:number,thicknessFactor:number,p:CharacterParameters):number {
  return F(clamp(Math.pow(clamp(Math.max(noV,.001)),p.filmPower)*p.filmRate*mask)*thicknessFactor);
}
export function characterNormalCorrection(normalY:number,compNormalDotLight:number,paintSigned:number):number {
  const c=normalY*(1-compNormalDotLight);return F(clamp(c*clamp(paintSigned*-7)-c+1.16));
}
export function characterBacklight(noV:number,noL:number,voL:number,thickness:number,transmission:V3,lightAlpha:number,tau:number,aoLight:number,p:CharacterParameters):V3 {
  const edge=characterEdge(noV,noL,voL,thickness,p);return transmission.map(t=>F(aoLight*edge*t*lightAlpha*tau)) as V3;
}
