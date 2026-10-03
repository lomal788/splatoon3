// Paint textures feed the actual stage material draw. Native atlas construction remains separate.
import * as THREE from "three";
import type { PaintSurfacesShared } from "../../core/paint/index.ts";
import type { World } from "../../core/world.ts";
import type { ClientContext, View } from "../context.ts";
import { DEV } from "../env.ts";
import { applyInkSurface, type InkSurfaceBinding } from "../render/ink_surface.ts";
import { buildTeamSets, FALLBACK_ROW, type TeamColorRow } from "../render/teamcolor.ts";
import { bindVisualPaint } from "./visual_geometry.ts";

/** Native lobby team-row selector remains unconfirmed; keep the same row as render. */
const TEAM_ROW="OrangeBlue";
interface PageView { tex:THREE.DataTexture; }

export function createPaintView(ctx:ClientContext):View {
  let pages:PageView[]|null=null;
  let visual:ReturnType<typeof bindVisualPaint>|null=null;
  const materials=new Map<string,{material:THREE.MeshStandardMaterial;binding:InkSurfaceBinding}>();
  const stats={ready:false,legacyOverlayMeshes:0,frame:-1,textureUpdates:0,
    atlas:"web coplanar charts/shelf packing; native whole ColPaint builder remains",
    emission:"native member18 initializer0; active env Ink reader remains unconfirmed",
    normalStep:"web atlas inverse width / W initializer0; not native1/3200 coordinates",
    nativeGPUEquivalent:false};

  const dispose=():void=>{
    // Restore stage geometry/materials before MapView releases its own resources.
    visual?.dispose();visual=null;
    for(const {material,binding} of materials.values()){binding.dispose();material.dispose();}
    materials.clear();for(const p of pages??[])p.tex.dispose();pages=null;stats.ready=false;
    if(ctx.paintMap?.disposePaint===dispose)ctx.paintMap.disposePaint=undefined;
    if(DEV)delete (globalThis as Record<string,unknown>).__splatoon3_paint;
  };

  return {
    update(w:World):void {
      const sh=w.shared.get("paintSurfaces") as PaintSurfacesShared|undefined;
      const map=ctx.paintMap;
      if(!sh||!map||!map.root.children.length)return;
      pages??=sh.surfaces.pages.map(pg=>{
        const tex=new THREE.DataTexture(pg.color,pg.w,pg.h,THREE.RGBAFormat,THREE.UnsignedByteType);
        tex.magFilter=tex.minFilter=THREE.LinearFilter;tex.generateMipmaps=false;
        tex.colorSpace=THREE.NoColorSpace;tex.flipY=false;tex.needsUpdate=true;
        return {tex};
      });
      // Empty-ink startup captures complete before changing the stage draw geometry.
      if(!visual&&map.environmentReady){
        const table=w.data.tables.team_color as {dataSets?:(TeamColorRow&{name?:string})[]}|undefined;
        const row=table?.dataSets?.find(r=>r.name===TEAM_ROW)??FALLBACK_ROW;
        const sets=buildTeamSets(row,false,map.env.light);
        const ink=sets.slice(0,3).map(s=>s.colors[9]!.slice(0,3) as [number,number,number]);
        const bright=sets.slice(0,3).map(s=>s.colors[10]!.slice(0,3) as [number,number,number]);
        visual=bindVisualPaint(map.root,sh.surfaces,(original,page)=>{
          const key=original.uuid+":"+page;const cached=materials.get(key);if(cached)return cached.material;
          const material=original.clone();
          // THREE.Material.clone does not copy compile hooks. Keep the original Hoian/bake/forward chain.
          material.onBeforeCompile=original.onBeforeCompile;
          material.customProgramCacheKey=original.customProgramCacheKey.bind(original);
          // MeshStandardMaterial.copy also omits custom defines; these must exist before WebGL builds its attribute prefix.
          const sourceDefines=(original as unknown as {defines?:Record<string,string>}).defines;
          if(sourceDefines)(material as unknown as {defines:Record<string,string>}).defines={...sourceDefines};
          const binding=applyInkSurface(material,{texture:pages![page].tex,ink,inkBright:bright,
            textureStep:[Math.fround(1/sh.surfaces.pages[page].w),0],emission:0,
            attributeNames:{uv:"paintUv",selector:"paintUvSwitch",tangent:"paintUvTangent"}});
          material.name=original.name+":ink.page"+page;
          materials.set(key,{material,binding});return material;
        });
        map.disposePaint=dispose;stats.ready=true;
        if(DEV)(globalThis as Record<string,unknown>).__splatoon3_paint={pages,visual,materials,stats};
      }
      for(const {binding} of materials.values())binding.updateFrame(w.frame);
      stats.frame=w.frame;
      for(let p=0;p<pages.length;p++){
        const dirty=sh.takeDirty(p);if(!dirty)continue;
        const tex=pages[p].tex,img=tex.image,[x0,y0,x1,y1]=dirty;
        if((x1-x0+1)*(y1-y0+1)*4<img.width*img.height){
          for(let y=y0;y<=y1;y++)tex.addUpdateRange((y*img.width+x0)*4,(x1-x0+1)*4);
        }else tex.clearUpdateRanges();
        tex.needsUpdate=true;stats.textureUpdates++;
      }
    },dispose,
  };
}
