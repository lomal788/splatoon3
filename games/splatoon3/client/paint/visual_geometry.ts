// Same visual triangle draw owns dry/painted pixels. Coordinate/layout candidate
// policy below is a web adapter for existing custom charts, not native ColPaint.
import * as THREE from "three";
import type { PaintSurfaces } from "../../core/paint/surface.ts";
import { nativePackPaintUv, nativePackPaintSwitch, nativePackPaintTangent, webDecodePaintTangent } from "../../core/paint/native_visual_uv.ts";
import { rankVisualChartCandidates, partitionVisualChartTriangle, visualChartUv, type VisualBarycentric } from "../../core/paint/visual_chart_adapter.ts";
import { fresOf } from "../render/model.ts";

export interface VisualPaintGeometryStats {
  policy: string;
  candidateMeshes: number;
  boundMeshes: number;
  visualTriangles: number;
  assignedTriangles: number;
  pieces: number;
  remainderPieces: number;
  pages: number;
  skipped: string[];
}
interface PieceArrays { attrs: Map<string,{size:number;array:number[]}>; paintUv:number[];paintSwitch:number[];paintTangent:number[] }

/** materialForPage owns cloned materials; this binding owns its generated geometry. */
export function bindVisualPaint(
  root: THREE.Object3D, surf: PaintSurfaces,
  materialForPage: (original: THREE.MeshStandardMaterial,page: number)=>THREE.Material,
): {stats: VisualPaintGeometryStats;dispose:()=>void} {
  const stats: VisualPaintGeometryStats={policy:"web custom charts: dot>.99, all depths<=.2, sphere radius+.2, plane-distance order, disjoint rectangle partition",candidateMeshes:0,boundMeshes:0,visualTriangles:0,assignedTriangles:0,pieces:0,remainderPieces:0,pages:0,skipped:[]};
  root.updateMatrixWorld(true);
  const meshes:THREE.Mesh[]=[];
  root.traverse(o=>{
    const m=o as THREE.Mesh;
    if(!m.isMesh||Array.isArray(m.material)||!m.visible)return;
    const mat=m.material as THREE.MeshStandardMaterial,f=fresOf(mat);
    if(!mat.isMeshStandardMaterial||!mat.userData.nativeForward||f?.shader?.options?.blitz_paint_type!=="1")return;
    meshes.push(m);
  });
  const records:{mesh:THREE.Mesh;visible:boolean;pieces:THREE.Mesh[]}[]=[];
  const usedPages=new Set<number>();
  for(const mesh of meshes) {
    stats.candidateMeshes++;
    if((mesh as THREE.SkinnedMesh).isSkinnedMesh||Object.keys(mesh.geometry.morphAttributes).length) {
      stats.skipped.push(mesh.name+": skinned/morph visual geometry");continue;
    }
    const original=mesh.geometry,position=original.getAttribute("position");
    if(!position){stats.skipped.push(mesh.name+": no positions");continue;}
    const attrs=Object.entries(original.attributes);
    const buckets=new Map<number|null,PieceArrays>();
    const getBucket=(page:number|null):PieceArrays=>{
      let b=buckets.get(page);
      if(!b) {
        b={attrs:new Map(attrs.map(([name,a])=>[name,{size:a.itemSize,array:[]}])),paintUv:[],paintSwitch:[],paintTangent:[]};
        buckets.set(page,b);
      }
      return b;
    };
    const world=new THREE.Vector3(),center=new THREE.Vector3(),inverse=mesh.matrixWorld.clone().invert();
    const inverseLinear=new THREE.Matrix3().setFromMatrix4(inverse);
    const index=original.index,count=index?.count??position.count;
    const first=Math.max(0,original.drawRange.start);
    const end=Math.min(count,Number.isFinite(original.drawRange.count)?first+original.drawRange.count:count);
    let assigned=0;
    for(let ti=first;ti+2<end;ti+=3) {
      const ids=[0,1,2].map(k=>index?index.getX(ti+k):ti+k);
      const points:number[]=[];
      for(const id of ids) {
        world.fromBufferAttribute(position,id).applyMatrix4(mesh.matrixWorld);
        points.push(world.x,world.y,world.z);
      }
      center.set((points[0]+points[3]+points[6])/3,(points[1]+points[4]+points[7])/3,(points[2]+points[5]+points[8])/3);
      let radius=0;
      for(let k=0;k<9;k+=3)radius=Math.max(radius,world.set(points[k],points[k+1],points[k+2]).distanceTo(center));
      const candidates=rankVisualChartCandidates(points,surf.chartsInSphere([center.x,center.y,center.z],radius+.2).map(id=>({id,chart:surf.charts[id]})));
      const pieces=partitionVisualChartTriangle(points,candidates);
      stats.visualTriangles++;
      if(pieces.some(p=>p.chartId!==null)){assigned++;stats.assignedTriangles++;}
      for(const piece of pieces) {
        const chart=piece.chartId===null?null:surf.charts[piece.chartId];
        const bucket=getBucket(chart?.page??null);
        const tangent=chart?world.set(...chart.e1).applyMatrix3(inverseLinear):null;
        // Native tangent writer gets object-space values. The inverse model
        // transform here is the WebGL object's transform, not a native matrix-lookup proof.
        const paintTangent=tangent?webDecodePaintTangent(nativePackPaintTangent([tangent.x,tangent.y,tangent.z],[1,0,0,0,1,0,0,0,1])):[0,0,0];
        const append=(weights:VisualBarycentric)=>{
          for(const [name,a] of attrs) {
            const out=bucket.attrs.get(name)!;
            for(let c=0;c<a.itemSize;c++)out.array.push(a.getComponent(ids[0],c)*weights[0]+a.getComponent(ids[1],c)*weights[1]+a.getComponent(ids[2],c)*weights[2]);
          }
          if(chart) {
            world.set(points[0]*weights[0]+points[3]*weights[1]+points[6]*weights[2],points[1]*weights[0]+points[4]*weights[1]+points[7]*weights[2],points[2]*weights[0]+points[5]*weights[1]+points[8]*weights[2]);
            const pg=surf.pages[chart.page],uv=visualChartUv([world.x,world.y,world.z],chart,pg.w,pg.h);
            bucket.paintUv.push(...nativePackPaintUv([uv[0],uv[1],uv[0],uv[1]]));
            bucket.paintSwitch.push(nativePackPaintSwitch(0));bucket.paintTangent.push(...paintTangent);
          }
        };
        for(let k=1;k+1<piece.vertices.length;k++){append(piece.vertices[0]);append(piece.vertices[k]);append(piece.vertices[k+1]);}
        stats.pieces++;
        if(chart)usedPages.add(chart.page);else stats.remainderPieces++;
      }
    }
    if(!assigned)continue;
    const generated:THREE.Mesh[]=[];
    for(const [page,bucket] of buckets) {
      const geo=new THREE.BufferGeometry();
      for(const [name,a] of bucket.attrs)geo.setAttribute(name,new THREE.Float32BufferAttribute(a.array,a.size));
      if(page!==null) {
        // Native CPU UV bytes are interpreted using explicit WebGL SNORM.
        geo.setAttribute("paintUv",new THREE.BufferAttribute(new Int16Array(new Uint16Array(bucket.paintUv).buffer),4,true));
        geo.setAttribute("paintUvSwitch",new THREE.BufferAttribute(new Int8Array(new Uint8Array(bucket.paintSwitch).buffer),1,true));
        geo.setAttribute("paintUvTangent",new THREE.Float32BufferAttribute(bucket.paintTangent,3));
      }
      geo.computeBoundingBox();geo.computeBoundingSphere();
      const part=new THREE.Mesh(geo,page===null?mesh.material:materialForPage(mesh.material as THREE.MeshStandardMaterial,page));
      part.name=mesh.name+(page===null?":paint-remainder":`:paint-page${page}`);
      part.userData={...mesh.userData,paintVisualGeometry:true,paintChartPolicy:stats.policy,paintPage:page};
      part.matrixAutoUpdate=mesh.matrixAutoUpdate;part.matrix.copy(mesh.matrix);part.matrixWorld.copy(mesh.matrixWorld);
      if(part.matrixAutoUpdate){part.position.copy(mesh.position);part.quaternion.copy(mesh.quaternion);part.scale.copy(mesh.scale);}
      part.castShadow=mesh.castShadow;part.receiveShadow=mesh.receiveShadow;part.frustumCulled=mesh.frustumCulled;part.renderOrder=mesh.renderOrder;part.layers.mask=mesh.layers.mask;
      mesh.parent?.add(part);generated.push(part);
    }
    records.push({mesh,visible:mesh.visible,pieces:generated});mesh.visible=false;stats.boundMeshes++;
  }
  stats.pages=usedPages.size;
  let disposed=false;
  return {stats,dispose:()=>{
    if(disposed)return;disposed=true;
    for(const {mesh,visible,pieces} of records){mesh.visible=visible;for(const part of pieces){part.removeFromParent();part.geometry.dispose();}}
  }};
}
