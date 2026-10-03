import type {NativeTexSrt} from "./material_channels.ts";
const F=Math.fround;
/** Original TexSrt30 -> 088efb0 -> Maya088f3d0, six active floats.
 * Zero rotation uses original SDK SinCosSampleTable[0] cos1/sin0.
 * The native writer returns 24 bytes. No claim about Mat padding/upload.
 */
export function nativeTexSrtRowsZeroRotation(raw:NativeTexSrt):number[]|null {
  if(raw.Mode!=="ModeMaya"||F(raw.Rotation)!==0)return null;
  const sx=F(raw.Scaling.X),sy=F(raw.Scaling.Y),tx=F(raw.Translation.X),ty=F(raw.Translation.Y);
  if(![sx,sy,tx,ty].every(Number.isFinite))return null;
  const c=F(1),s=F(0);
  // Preserve FMUL/FADD/FSUB order, including signed zero. No FMA/direct simplification.
  const linear=[F(sx*c),F(F(-sy)*s),F(sx*s),F(c*sy)];
  const q=F(F(s*F(.5))+F(-.5)),d=F(c*F(-.5));
  const u=F(sx*F(F(d-q)-tx));
  const v=F(F(sy*F(F(d+q)+ty))+F(1));
  return [...linear,u,v];
}
