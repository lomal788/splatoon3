import * as THREE from "three";
import { directionalSH, F, mul, type V3 } from "./graphics_math.ts";
import { lightGrid, staticSpotRigs } from "./dynamic_lights.ts";
import { CubeSHProjection, SH_CAPTURE_POLICY } from "./sh_projection.ts";
import type { NativeShadowState } from "./shadows.ts";
import { NativeEnvironment } from "./env_prefilter.ts";

type Json=Record<string,unknown>;
const obj=(v: unknown):Json=>v&&typeof v==="object"?v as Json:{};
const number=(v:unknown,d:number):number=>typeof v==="number"?F(v):d;
function vector(v:unknown,d:number[]):number[] {
  if(Array.isArray(v))return v.map(Number);
  const o=obj(v);return d.map((x,i)=>number(o[["R","G","B","A"][i]]??o[["X","Y","Z","W"][i]],x));
}
export class LightingState {
  shadows:NativeShadowState|null=null;
  readonly projection=new CubeSHProjection();
  readonly env=new NativeEnvironment();
  readonly uniforms = {
    hLightColor:{value:new THREE.Vector3(1,1,1)}, hLightAlpha:{value:1}, hLightDirection:{value:new THREE.Vector3(0,-1,0)},
    hSH:{value:Array.from({length:7},()=>new THREE.Vector4())},
    hDepthFog:{value:new THREE.Vector4()}, hDepthRange:{value:new THREE.Vector3(10,1000,.3125)},
    hHeightFog:{value:new THREE.Vector4()}, hHeightRange:{value:new THREE.Vector2(15,90)},
    hBakeShadow:{value:new THREE.Vector4(1.875,-1.34765625,1.0625,-.1328125)}, hAOMain:{value:.03125},
    hGrid:{value:new THREE.DataTexture(new Uint32Array(400).fill(0xffffffff),20,20,THREE.RedIntegerFormat,THREE.UnsignedIntType)},
    hGridOrigin:{value:new THREE.Vector3(-100,-.5,-100)}, hInvCell:{value:new THREE.Vector3(.1,1,.1)},
    hDynColor:{value:Array.from({length:30},()=>new THREE.Vector4())},
    hDynAtt:{value:Array.from({length:30},()=>new THREE.Vector4())},
    hDynPos:{value:Array.from({length:30},()=>new THREE.Vector4())},
    hDynDir:{value:Array.from({length:30},()=>new THREE.Vector4())},
    ...this.env.uniforms,
  };
  readonly stats = { rigs:0, gridLights:0, occupiedCells:0, captures:0, shSource:"native startup fallback", environmentSource:"none", skyCapture:"Hoian cube27: native luminance/saturation; Illuminate and other cube materials remain" };
  private raw:unknown=null;
  private cube:THREE.WebGLCubeRenderTarget|null=null;
  private prefilter:THREE.WebGLRenderTarget|null=null;
  configure(raw:unknown,color:V3,intensity:number,direction:V3,highlight:THREE.Texture|null=null):void {
    this.raw=raw;
    const u=this.uniforms,r=obj(obj(raw).rendering),fog=obj(r.Fog),shadow=obj(obj(r.Shadow).BakeShadow);
    u.hLightColor.value.set(...color.map(v=>mul(v,intensity)) as V3);u.hLightDirection.value.set(...direction);
    // Env[5] is Intensity*DiffuseRGBA, not (Intensity*RGB,1).
    const tcl=obj(obj(raw).teamColorLight),main=obj(tcl.lobbyMainLight??obj(r.Lighting).MainLight);
    const rgba=main.Color??obj(tcl.defaultDay).DiffuseColor??[...color,1];
    const alpha=Array.isArray(rgba)?rgba[3]:obj(rgba).A??obj(rgba).a;
    u.hLightAlpha.value=mul(typeof alpha==="number"?alpha:1,intensity);
    const rgbaArray=Array.isArray(rgba)?rgba as number[]:[Number(obj(rgba).R??color[0]),Number(obj(rgba).G??color[1]),Number(obj(rgba).B??color[2]),typeof alpha==="number"?alpha:1];
    this.env.configure(raw,direction,rgbaArray,highlight);
    this.setSH(directionalSH([0,1,0],color.map(v=>mul(mul(.1,intensity),v)) as V3));
    const depth=obj(fog.DepthFog),height=obj(fog.HeightFog);
    u.hDepthFog.value.fromArray(vector(depth.Color,[0,0,0,0]));
    u.hDepthRange.value.set(number(depth.Start,10),number(depth.End,1000),number(depth.ScatteringCoeff,.3125));
    u.hHeightFog.value.fromArray(vector(height.Color,[0,0,0,0]));
    u.hHeightRange.value.set(number(height.Start,15),number(height.End,90));
    const shScale=number(shadow.BakeShadowIntensScale,1.875),shOff=number(shadow.BakeShadowIntensOffset,.71875);
    const aoScale=number(shadow.BakeAOIntensScale,1.0625),aoOff=number(shadow.BakeAOIntensOffset,.125);
    u.hBakeShadow.value.set(shScale,mul(-shOff,shScale),aoScale,mul(-aoOff,aoScale));
    u.hAOMain.value=number(shadow.BakeAOMainLightOcclude,.03125);
    u.hGrid.value.minFilter=u.hGrid.value.magFilter=THREE.NearestFilter;
    u.hGrid.value.needsUpdate=true;
  }
  setSH(coefficients:number[]):void {
    for(let i=0;i<7;i++)this.uniforms.hSH.value[i].fromArray(coefficients,i*4);
  }
  bindRigs(root:THREE.Object3D):void {
    const rigs=staticSpotRigs(this.raw,root);
    const dyn=obj(obj(obj(this.raw).rendering).Lighting).DynamicLight;
    const d=obj(dyn),cell=vector(d.GridSize,[10,1,10]) as V3,offset=vector(d.GridOffset,[0,0,0]) as V3;
    const g=lightGrid(rigs,cell,offset),u=this.uniforms;
    u.hGrid.value.image.data=g.grid;u.hGrid.value.needsUpdate=true;
    u.hGridOrigin.value.set(...g.origin);u.hInvCell.value.set(...g.cell.map(x=>F(1/x)) as V3);
    for(let i=0;i<g.lights.length;i++){
      const l=g.lights[i];u.hDynColor.value[i].set(...l.color,l.colorAlpha??1);
      u.hDynAtt.value[i].set(F(1/l.radius),l.damp,F(Math.cos(l.halfAngle)),l.angleDamp);
      u.hDynPos.value[i].set(...l.position,l.type);u.hDynDir.value[i].set(...l.direction,0);
    }
    this.stats.rigs=rigs.length;this.stats.gridLights=g.lights.length;this.stats.occupiedCells=g.grid.filter(x=>x!==0xffffffff).length;
  }
  /** Known mSky cube27 is connected; remaining cube input/prefilter still use the web renderer. */
  async capture(renderer:THREE.WebGLRenderer,scene:THREE.Scene,stage:THREE.Object3D,sky:THREE.Object3D|null,setSkyCapture:(capture:boolean)=>void):Promise<void> {
    const e=obj(obj(obj(this.raw).rendering).Lighting),p=vector(obj(e.EnvMap).CapturePos,[0,0,0]);
    this.cube=new THREE.WebGLCubeRenderTarget(256,{type:THREE.HalfFloatType,generateMipmaps:true,minFilter:THREE.LinearMipmapLinearFilter});
    this.cube.texture.colorSpace=THREE.LinearSRGBColorSpace;
    const cam=new THREE.CubeCamera(4,1024,this.cube);cam.position.fromArray(p);
    const hidden=scene.children.filter(o=>o!==stage && o!==sky && !(o as THREE.Light).isLight);
    const visibility=hidden.map(o=>o.visible);
    const pmrem=new THREE.PMREMGenerator(renderer);
    const oldTarget=renderer.getRenderTarget(),oldTone=renderer.toneMapping,oldAuto=renderer.autoClear;
    const oldViewport=renderer.getViewport(new THREE.Vector4()),oldScissor=renderer.getScissor(new THREE.Vector4()),oldScissorTest=renderer.getScissorTest();
    try {
      renderer.toneMapping=THREE.NoToneMapping;renderer.autoClear=true;renderer.setScissorTest(false);
      for(let pass=0;pass<2;pass++){
        hidden.forEach(o=>o.visible=false);setSkyCapture(true);
        cam.update(renderer,scene);
        hidden.forEach((o,i)=>o.visible=visibility[i]);setSkyCapture(false);
        // 1037098: Illuminate result is copied back to the base cube before SH projection and prefilter.
        const source=this.env.illuminate(renderer,this.cube.texture);
        const sh=await this.projection.project(renderer,source);this.setSH(sh);
        this.env.prefilter(renderer,source);
        this.prefilter?.dispose();this.prefilter=pmrem.fromCubemap(source);
        scene.environment=this.prefilter.texture;this.stats.captures++;
      }
      this.stats.shSource=SH_CAPTURE_POLICY.projection+" + native CPU packing; input cube remains web";
      this.stats.environmentSource="native 12-layer GGX prefilter (web atlas) + GGXEnvBRDF for Hoian forward; PMREM kept for non-native materials";
    } finally {
      hidden.forEach((o,i)=>o.visible=visibility[i]);setSkyCapture(false);pmrem.dispose();
      renderer.setRenderTarget(oldTarget);renderer.setViewport(oldViewport);renderer.setScissor(oldScissor);renderer.setScissorTest(oldScissorTest);
      renderer.toneMapping=oldTone;renderer.autoClear=oldAuto;
    }
  }
  dispose():void {this.env.dispose();this.uniforms.hGrid.value.dispose();this.cube?.dispose();this.prefilter?.dispose();this.projection.dispose();}
}
