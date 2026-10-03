
// Native static rig -> dynamic light grid consumers (graphics/light_rig_runtime,
// dynamic_lighting §5..8). Original XZ iteration/order and unnormalized cone cross.
import * as THREE from "three";
import { F, add, sub, mul, div, dot, norm, type V3 } from "./graphics_math.ts";
export interface DynamicLight {
  position: V3; direction: V3; color: V3; radius: number; halfAngle: number;
  /** Native RGBA.w participates in character transmission; RGB-only web fixtures may omit it. */
  colorAlpha?:number;
  damp: number; angleDamp: number; type: number;
}
export function coneCell(center: V3, position: V3, direction: V3, radius: number, angle: number, margin: number): boolean {
  const delta = center.map((v,i) => sub(v,position[i])) as V3;
  const distance = F(Math.sqrt(dot(delta,delta)));
  const v = distance !== 0 ? norm(delta) : direction;
  const d = norm(direction);
  let length = radius;
  if (Math.max(-1, Math.min(1,dot(v,d))) <= F(Math.cos(F(angle)))) {
    // 1048fa8's quaternion-like rotation does not normalize cross(v,d).
    const cs = F(Math.cos(mul(angle,.5))), sn = F(Math.sin(mul(angle,.5)));
    const a = mul(sub(mul(v[2],d[1]),mul(v[1],d[2])),sn);
    const b = mul(sub(mul(v[0],d[2]),mul(v[2],d[0])),sn);
    const c = mul(sub(mul(v[1],d[0]),mul(v[0],d[1])),sn);
    const a2=add(a,a), b2=add(b,b), c2=add(c,c), w2=add(cs,cs);
    const cc=mul(c,c2),bb=mul(b,b2),cb=mul(c,b2),oneAA=sub(1,mul(a,a2));
    const r0=add(add(mul(d[2],add(mul(w2,b),mul(c,a2))),mul(d[1],sub(mul(b,a2),mul(w2,c)))),mul(d[0],sub(sub(1,bb),cc)));
    const r1=add(add(mul(d[2],sub(cb,mul(w2,a))),mul(d[0],add(mul(w2,c),mul(b,a2)))),mul(d[1],sub(oneAA,cc)));
    const r2=add(add(mul(d[0],sub(mul(c,a2),mul(w2,b))),mul(d[1],add(mul(w2,a),cb))),mul(d[2],sub(oneAA,bb)));
    length = Math.max(0,add(add(mul(mul(v[2],radius),r2),mul(mul(v[0],radius),r0)),mul(mul(v[1],radius),r1)));
  }
  return distance < add(length,margin);
}
export function lightGrid(lights: DynamicLight[], cell: V3 = [10,1,10], offset: V3 = [0,0,0]): { grid: Uint32Array; lights: DynamicLight[]; origin: V3; cell: V3 } {
  cell=cell.map(v=>Math.abs(v)<=F(2**-23)?1:F(v)) as V3;
  const origin = offset.map((v,i)=>sub(v,mul(mul(cell[i],i===1?1:20),.5))) as V3;
  const grid=new Uint32Array(400).fill(0xffffffff), accepted: DynamicLight[]=[];
  for (const l of lights) {
    if (accepted.length>=30) break;
    if (l.position.some(Number.isNaN)) continue;
    const local: V3=[sub(l.position[0],origin[0]),mul(cell[1],.5),sub(l.position[2],origin[2])];
    const cx=Math.floor(div(local[0],cell[0])),cz=Math.floor(div(local[2],cell[2]));
    const rx=Math.ceil(div(l.radius,cell[0])),rz=Math.ceil(div(l.radius,cell[2]));
    const margin=mul(Math.max(0,cell[0],cell[2]),.70710677);
    let inserted=false;
    for(let x=cx-rx;x<=cx+rx;x++) for(let z=cz-rz;z<=cz+rz;z++) {
      if(x<0||x>=20||z<0||z>=20)continue;
      const center: V3=[mul(add(x,.5),cell[0]),mul(cell[1],.5),mul(add(z,.5),cell[2])];
      const hit=l.type===1||l.type===2?coneCell(center,local,l.direction,l.radius,l.halfAngle,margin):
        l.type===0 && F(Math.sqrt(dot(center.map((v,i)=>sub(v,local[i])) as V3,center.map((v,i)=>sub(v,local[i])) as V3)))<add(l.radius,margin);
      const i=z*20+x;
      if(hit&&(grid[i]>>>24)===255){grid[i]=((grid[i]<<8)|accepted.length)>>>0;inserted=true;}
    }
    if(inserted)accepted.push({...l,direction:norm(l.direction)});
  }
  return {grid,lights:accepted,origin,cell};
}
type Json=Record<string,unknown>;
function tuple(v: unknown, fallback: V3): V3 {
  if(Array.isArray(v))return v.slice(0,3).map(Number) as V3;
  const q=v as Json|undefined;
  return q?[Number(q.X??q.x??fallback[0]),Number(q.Y??q.y??fallback[1]),Number(q.Z??q.z??fallback[2])]:fallback;
}
function transform(m: THREE.Matrix4,v: V3,translation:boolean): V3 {
  const a=m.elements;
  return [0,1,2].map(i=>add(add(add(mul(a[i],v[0]),mul(a[4+i],v[1])),mul(a[8+i],v[2])),translation?a[12+i]:0)) as V3;
}
export function staticSpotRigs(env: unknown, root: THREE.Object3D): DynamicLight[] {
  const e=env as { sceneEnv?: { params?: { SpotLightRig?: { objects?: Record<string,Json> } } } };
  const out: DynamicLight[]=[];
  root.updateMatrixWorld(true);
  for(const p of Object.values(e?.sceneEnv?.params?.SpotLightRig?.objects??{})) {
    if(!p.enable||Number(p.AnmType??p["0x21e45b6e"]??0)!==0)continue;
    const model=String(p.ModelName??""),prefix=String(p.BonePrefix??p["0xc32f024e"]??"");
    root.traverse(o=>{
      if(!o.name.startsWith(prefix))return;
      let parent: THREE.Object3D|null=o;
      while(parent && parent.userData.originalModelName!==model)parent=parent.parent;
      if(!parent)return;
      const m=o.matrixWorld, off=tuple(p.Offset,[0,0,0]), world=!!(p.IsOffsetWorld??p["0x86fe9c49"]);
      const position=world?off.map((v,i)=>add(v,m.elements[12+i])) as V3:transform(m,off,true);
      const rawDirection=tuple(p.Direction,[0,1,0]),follow=p.IsFollowDir??p["0xdcb2146c"]??true;
      const radius=F(Number(p.Radius??10)),inputAngle=F(Number(p.Angle??.8)),intensity=F(Number(p.Intensity??1));
      const rawColor=p.Color as number[]|undefined;
      out.push({position,direction:follow?transform(m,rawDirection,false):rawDirection,color:tuple(p.Color,[1,1,1]).map(v=>mul(v,intensity)) as V3,
        colorAlpha:mul(Array.isArray(rawColor)&&typeof rawColor[3]==="number"?rawColor[3]:1,intensity),
        radius,halfAngle:mul(inputAngle,.5),damp:F(Number(p.DampParam??p["0x3b6c62f4"]??1.2)),
        angleDamp:mul(Number(p.AngleDamp??p["0x5741febf"]??1),radius===0?radius:mul(radius,div(1,radius))),type:1});
    });
  }
  return out;
}
