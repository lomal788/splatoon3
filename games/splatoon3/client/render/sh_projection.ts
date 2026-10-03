// Hoian_Proc IrradianceCubeMapAllToSH, width 128, and 10325d4 CPU packing.
// Native shader equations; WebGL driver reduction/texture filtering are not NVN bit identity.
import * as THREE from "three";
import { mul, sub } from "./graphics_math.ts";

export const SH_CAPTURE_POLICY = Object.freeze({
  cubeWidth:256, projectionWidth:128, projectionMip:1,
  mip:"web mip 1; native cMipLevel reads texture-view +0xaa (live view unverified)",
  projection:"native angular sin directions + seven additive RGBA32F attachments",
  capture:"web stage/sky cube; native cube variants/Illuminate/saturation remain unverified",
});

/** Input has already passed the native float/half texture read conversion. */
export function packReadbackSH(t: readonly (readonly number[])[]):number[] {
  if(t.length!==7||t.some(row=>row.length!==4))throw new Error("SH requires seven vec4 texels");
  const out=Array<number>(28).fill(0),k0=.28175688,k1=.32534343,k2=.07875311,k3=.27280876,k4=.23625931,k5=.13640438;
  out[0]=mul(t[2][1],k1);out[1]=mul(t[0][3],k1);out[2]=mul(t[1][2],k1);out[3]=sub(mul(t[0][0],k0),mul(t[4][2],k2));
  out[4]=mul(t[2][2],k1);out[5]=mul(t[1][0],k1);out[6]=mul(t[1][3],k1);out[7]=sub(mul(t[0][1],k0),mul(t[4][3],k2));
  out[8]=mul(t[2][3],k1);out[9]=mul(t[1][1],k1);out[10]=mul(t[2][0],k1);out[11]=sub(mul(t[0][2],k0),mul(t[5][0],k2));
  out[12]=mul(t[3][0],k3);out[13]=mul(t[3][3],k3);out[14]=mul(t[4][2],k4);out[15]=mul(t[5][1],k3);
  out[16]=mul(t[3][1],k3);out[17]=mul(t[4][0],k3);out[18]=mul(t[4][3],k4);out[19]=mul(t[5][2],k3);
  out[20]=mul(t[3][2],k3);out[21]=mul(t[4][1],k3);out[22]=mul(t[5][0],k4);out[23]=mul(t[5][3],k3);
  out[24]=mul(t[6][0],k5);out[25]=mul(t[6][1],k5);out[26]=mul(t[6][2],k5);out[27]=1;return out;
}

export const SH_PROJECTION_FRAGMENT=/* glsl */`
precision highp float;precision highp int;
uniform samplerCube sourceCube;uniform float sourceMip;flat in int sampleId;
layout(location=0)out vec4 sh0;layout(location=1)out vec4 sh1;layout(location=2)out vec4 sh2;
layout(location=3)out vec4 sh3;layout(location=4)out vec4 sh4;layout(location=5)out vec4 sh5;layout(location=6)out vec4 sh6;
void main(){
  int j=sampleId&16383,face=sampleId/16384;
  float a=sin(((float(j/128)+.5)*.703125-45.)*.0174532924)*1.41419995;
  float b=sin(((float(j&127)+.5)*.703125-45.)*.0174532924)*1.41419995;
  vec3 d=face==0?vec3(-1.,a,b):face==1?vec3(1.,a,b):face==2?vec3(b,-1.,a):
    face==3?vec3(b,1.,a):face==4?vec3(b,a,1.):vec3(b,a,-1.);
  d=normalize(d);vec3 c=textureLod(sourceCube,d/max(abs(d.x),max(abs(d.y),abs(d.z))),sourceMip).rgb;
  float xy=d.x*d.y,yz=d.y*d.z,xz=d.x*d.z,zz=d.z*d.z*.00012095132-4.03171071e-5;
  float xx_yy=d.x*d.x-d.y*d.y;
  sh0=vec4(c*3.606069e-5,d.y*c.r*6.24589666e-5);
  sh1=vec4(d.y*c.gb*6.24589666e-5,d.z*c.rg*6.24589666e-5);
  sh2=vec4(d.z*c.b*6.24589666e-5,d.x*c*6.24589666e-5);
  sh3=vec4(c*xy*.000139662312,c.r*yz*.000139662312);
  sh4=vec4(c.gb*yz*.000139662312,c.rg*zz);
  sh5=vec4(c.b*zz,c*xz*.000139662312);
  sh6=vec4(c*xx_yy*6.9831156e-5,0.);
}`;

/** All 6*128^2 points land on one texel, as in the native seven-MRT additive draw. */
export class CubeSHProjection {
  readonly target=new THREE.WebGLRenderTarget(1,1,{count:7,type:THREE.FloatType,depthBuffer:false});
  readonly material=new THREE.RawShaderMaterial({
    glslVersion:THREE.GLSL3,uniforms:{sourceCube:{value:null},sourceMip:{value:SH_CAPTURE_POLICY.projectionMip}},
    vertexShader:"precision highp float;precision highp int;in vec3 position;flat out int sampleId;void main(){gl_Position=vec4(0.,0.,0.,1.);gl_PointSize=1.;sampleId=gl_VertexID;}",
    fragmentShader:SH_PROJECTION_FRAGMENT,depthTest:false,depthWrite:false,toneMapped:false,
    transparent:true,blending:THREE.CustomBlending,blendEquation:THREE.AddEquation,blendSrc:THREE.OneFactor,blendDst:THREE.OneFactor,
    blendEquationAlpha:THREE.AddEquation,blendSrcAlpha:THREE.OneFactor,blendDstAlpha:THREE.OneFactor,
  });
  private readonly geometry=new THREE.BufferGeometry().setAttribute("position",new THREE.BufferAttribute(new Float32Array(6*128*128*3),3));
  private readonly scene=new THREE.Scene();private readonly camera=new THREE.Camera();
  readonly stats={draws:0,samples:6*128*128,attachments:7,raw:[] as number[][]};
  constructor(){const points=new THREE.Points(this.geometry,this.material);points.frustumCulled=false;this.scene.add(points);}
  async project(renderer:THREE.WebGLRenderer,cube:THREE.CubeTexture):Promise<number[]> {
    const gl=renderer.getContext() as WebGL2RenderingContext;
    if(gl.getParameter(gl.MAX_DRAW_BUFFERS)<7||!renderer.extensions.has("EXT_color_buffer_float")||!renderer.extensions.has("EXT_float_blend"))throw new Error("Native SH adapter requires seven float MRTs and float additive blending");
    const oldTarget=renderer.getRenderTarget(),oldAuto=renderer.autoClear,oldTone=renderer.toneMapping;
    const clear=renderer.getClearColor(new THREE.Color()),alpha=renderer.getClearAlpha();
    const viewport=renderer.getViewport(new THREE.Vector4()),scissor=renderer.getScissor(new THREE.Vector4()),scissorTest=renderer.getScissorTest();
    try{
      this.material.uniforms.sourceCube.value=cube;renderer.setRenderTarget(this.target);renderer.setScissorTest(false);
      renderer.setClearColor(0,0);renderer.autoClear=false;renderer.toneMapping=THREE.NoToneMapping;renderer.clear(true,false,false);
      renderer.render(this.scene,this.camera);
      const raw:number[][]=[];
      for(let i=0;i<7;i++){const data=new Float32Array(4);await renderer.readRenderTargetPixelsAsync(this.target,0,0,1,1,data,undefined,i);raw.push([...data]);}
      if(raw.flat().some(v=>!Number.isFinite(v))||raw[0].slice(0,3).every(v=>v===0))throw new Error("SH projection produced invalid/empty lighting");
      this.stats.draws++;this.stats.raw=raw;return packReadbackSH(raw);
    }finally{
      renderer.setRenderTarget(oldTarget);renderer.setViewport(viewport);renderer.setScissor(scissor);renderer.setScissorTest(scissorTest);
      renderer.setClearColor(clear,alpha);renderer.autoClear=oldAuto;renderer.toneMapping=oldTone;
    }
  }
  dispose():void{this.target.dispose();this.material.dispose();this.geometry.dispose();}
}
