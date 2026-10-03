import * as THREE from "three";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import { fresOf } from "./model.ts";
import { parameter } from "./hoian.ts";

export class SkyView {
  readonly root:THREE.Object3D;
  private readonly exposure:{value:number}[]=[];
  private readonly saturation:{value:number}[]=[];
  private readonly capture:{value:boolean}[]=[];
  private visibleExposure=4;
  private captureExposure=80;
  private captureSaturation=1;
  constructor(gltf:GLTF,raw:unknown) {
    this.root=gltf.scene;this.root.name="splatoon3.sky";
    const data=raw as {rendering?:{Lighting?:{SkySphere?:{ExposureNotInEnvMap?:number;EmissionIntensInEnvMap?:number;SaturationInEnvMap?:number;Offset?:{X:number;Y:number;Z:number};Scale?:number}}}};
    const p=data?.rendering?.Lighting?.SkySphere;
    this.visibleExposure=Math.fround(2**Math.fround(p?.ExposureNotInEnvMap??0));
    this.captureExposure=p?.EmissionIntensInEnvMap??1;
    this.captureSaturation=p?.SaturationInEnvMap??1;
    // These scene transform writers remain unverified; record this web placement in impl/render.
    this.root.scale.multiplyScalar(p?.Scale??1);
    if(p?.Offset)this.root.position.set(p.Offset.X,p.Offset.Y,p.Offset.Z);
    this.root.traverse(o=>{
      const mesh=o as THREE.Mesh;if(!mesh.isMesh)return;
      mesh.frustumCulled=false;mesh.castShadow=false;mesh.receiveShadow=false;
      const old=mesh.material as THREE.MeshStandardMaterial,f=fresOf(old);
      const isSun=old.name==="mSun",texture=isSun?old.map:old.emissiveMap;
      const exp={value:this.visibleExposure};this.exposure.push(exp);
      const sat={value:1};this.saturation.push(sat);
      const cap={value:false};this.capture.push(cap);
      const intensity=f?parameter(f,"emission_intensity",isSun?10:1):(isSun?10:1);
      const color=f?.params?.emission_color?.value as number[]|undefined;
      const albedo=f?.params?.albedo_color?.value as number[]|undefined;
      const alpha=f?parameter(f,"opacity",1):1;
      mesh.material=new THREE.ShaderMaterial({
        name:old.name,uniforms:{source:{value:texture},exposure:exp,saturation:sat,envCapture:cap,intensity:{value:intensity},emissionColor:{value:new THREE.Vector3(...(color??[1,1,1]).slice(0,3))},albedoColor:{value:new THREE.Vector3(...(albedo??[0,0,0]).slice(0,3))},alpha:{value:alpha}},
        vertexShader:"varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
        fragmentShader:isSun?
          "uniform sampler2D source;uniform float intensity,alpha;varying vec2 vUv;void main(){vec3 c=texture2D(source,vUv).rgb;gl_FragColor=vec4(c*(intensity+1.),clamp(alpha,0.,1.));}":
          // Exact cube permutation 27; ordinary permutation 25 bypasses correction.
          // Native FMA rounding remains a GPU backend boundary (common_lighting_r6 §6).
          "uniform sampler2D source;uniform float exposure,intensity,saturation;uniform bool envCapture;uniform vec3 emissionColor,albedoColor;varying vec2 vUv;void main(){vec3 c=texture2D(source,vUv).rgb*emissionColor;if(envCapture){float y=c.r*.298911989+c.g*.586611+c.b*.114478;c=(c-vec3(y))*saturation+vec3(y);}gl_FragColor=vec4(c*(intensity*exposure)+albedoColor,1.);}",
        side:old.side,transparent:isSun,blending:isSun?THREE.AdditiveBlending:THREE.NormalBlending,depthWrite:!isSun,toneMapped:false,
      });
    });
  }
  setCapture(active:boolean):void {
    for(const x of this.exposure)x.value=active?this.captureExposure:this.visibleExposure;
    for(const x of this.saturation)x.value=active?this.captureSaturation:1;
    for(const x of this.capture)x.value=active;
  }
  dispose():void {this.root.traverse(o=>{if((o as THREE.Mesh).isMesh)((o as THREE.Mesh).material as THREE.Material).dispose();});}
}
