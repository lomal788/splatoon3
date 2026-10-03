import * as THREE from "three";
import type { Emitter } from "./particles.ts";
/** NVN descriptor -> WebGL adapter. Raw bytes and native setters are preserved in userData. */
export function applyEmitterRender(material:THREE.ShaderMaterial,def:Emitter):void {
  const r=(def.render??def.nativeRender) as Record<string,unknown>|undefined;if(!r)return;
  const number=(k:string,d:number)=>typeof r[k]==="number"||typeof r[k]==="boolean"?Number(r[k]):d;
  const blend=number("blendEnable",1)!==0,mode=number("blendMode",0);
  material.transparent=blend;material.depthTest=number("depthTest",1)!==0;
  material.depthWrite=number("depthWrite",0)!==0;
  const depth=[THREE.NeverDepth,THREE.LessDepth,THREE.EqualDepth,THREE.LessEqualDepth,THREE.GreaterDepth,THREE.NotEqualDepth,THREE.GreaterEqualDepth,THREE.AlwaysDepth];
  material.depthFunc=depth[number("depthCompare",3)]??THREE.LessEqualDepth;
  // Native ResBDF1 -> NVNface2(BACK), ResBDF2 -> NVNface1(FRONT); frontFace1(CCW).
  // r8 original CPU setter capture + public SDK nvn.h enum labels (see shooter_web_port.md §4).
  const cull=number("cullMode",0);material.side=cull===1?THREE.FrontSide:cull===2?THREE.BackSide:THREE.DoubleSide;
  if(!blend)material.blending=THREE.NoBlending;
  else {
    material.blending=THREE.CustomBlending;
    // Original 082804c factors (NVN 1=zero,2=one,3=srcColor,5=srcAlpha,6=oneMinusSrcAlpha,10=oneMinusDstColor).
    const rows=[
      [THREE.SrcAlphaFactor,THREE.OneMinusSrcAlphaFactor,THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.AddEquation],
      [THREE.SrcAlphaFactor,THREE.OneFactor,THREE.OneFactor,THREE.OneFactor,THREE.AddEquation],
      [THREE.SrcAlphaFactor,THREE.OneFactor,THREE.OneFactor,THREE.OneFactor,THREE.ReverseSubtractEquation],
      [THREE.ZeroFactor,THREE.SrcColorFactor,THREE.ZeroFactor,THREE.SrcColorFactor,THREE.AddEquation],
      [THREE.OneMinusDstColorFactor,THREE.OneFactor,THREE.OneMinusDstColorFactor,THREE.OneFactor,THREE.AddEquation],
      [THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.OneFactor,THREE.OneMinusSrcAlphaFactor,THREE.AddEquation],
    ];
    const b=rows[mode]??rows[0];
    material.blendSrc=b[0] as THREE.BlendingSrcFactor;material.blendDst=b[1] as THREE.BlendingDstFactor;
    material.blendSrcAlpha=b[2] as THREE.BlendingSrcFactor;material.blendDstAlpha=b[3] as THREE.BlendingDstFactor;
    material.blendEquation=material.blendEquationAlpha=b[4] as THREE.BlendingEquation;
  }
  material.userData.nativeRender={...r};
}
