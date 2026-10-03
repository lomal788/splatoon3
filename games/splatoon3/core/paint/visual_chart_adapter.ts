// Web adapter only: clip actual visual triangles against the CURRENT custom
// collision charts. This is not native 42-direction ColPaint panel selection.
import type { Chart } from "./surface.ts";

export type VisualBarycentric = [number, number, number];
export interface VisualChartCandidate { id: number; chart: Chart }
export interface VisualChartPiece { chartId: number | null; vertices: VisualBarycentric[] }
const EPS = 1e-10; // Web geometry degeneracy tolerance, not a recovered native constant.
const coord = (p: ArrayLike<number>, k: number, axis: ArrayLike<number>, origin: ArrayLike<number>): number =>
  (p[k] - origin[0]) * axis[0] + (p[k + 1] - origin[1]) * axis[1] + (p[k + 2] - origin[2]) * axis[2];

/** Explicit web candidate policy: normal dot > .99 and all 3 depths <= .2. */
export function rankVisualChartCandidates(worldTriangle: ArrayLike<number>, candidates: VisualChartCandidate[]): VisualChartCandidate[] {
  const p = worldTriangle;
  const a = [p[3] - p[0], p[4] - p[1], p[5] - p[2]], b = [p[6] - p[0], p[7] - p[1], p[8] - p[2]];
  const n = [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const length = Math.hypot(...n);
  if (!(length > 0)) return [];
  const scored: {candidate: VisualChartCandidate; distance: number}[] = [];
  for (const candidate of candidates) {
    const ch = candidate.chart;
    if (!((n[0]*ch.n[0]+n[1]*ch.n[1]+n[2]*ch.n[2])/length > 0.99)) continue;
    const depths = [0,3,6].map(k => Math.abs(coord(p,k,ch.n,ch.o)));
    if (depths.some(depth => depth > 0.2)) continue;
    scored.push({candidate,distance:(depths[0]+depths[1]+depths[2])/3});
  }
  scored.sort((a,b)=>a.distance-b.distance || a.candidate.id-b.candidate.id);
  return scored.map(s=>s.candidate);
}

const valueAt = (v: VisualBarycentric, values: ArrayLike<number>): number => v[0]*values[0]+v[1]*values[1]+v[2]*values[2];
const interpolate = (a: VisualBarycentric,b: VisualBarycentric,t:number): VisualBarycentric =>
  [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t];

function halfPlane(poly: VisualBarycentric[], values: number[], threshold: number, greater: boolean): VisualBarycentric[] {
  const out: VisualBarycentric[] = [];
  if (!poly.length) return out;
  let a=poly[poly.length-1], da=(valueAt(a,values)-threshold)*(greater?1:-1), ina=da>=0;
  for (const b of poly) {
    const db=(valueAt(b,values)-threshold)*(greater?1:-1), inb=db>=0;
    if (ina!==inb) out.push(interpolate(a,b,da/(da-db)));
    if (inb) out.push(b);
    a=b;da=db;ina=inb;
  }
  return out;
}

function hasArea(poly: VisualBarycentric[]): boolean {
  if (poly.length < 3) return false;
  let twiceArea=0;
  for(let i=0;i<poly.length;i++) {
    const a=poly[i],b=poly[(i+1)%poly.length];
    twiceArea+=a[1]*b[2]-a[2]*b[1];
  }
  return Math.abs(twiceArea)>EPS;
}

/** Disjoint pieces cover the original triangle. Candidates must already be ranked.
 * Chart bounds include the CURRENT chart pad; its zero RGB keeps the ink branch off.
 */
export function partitionVisualChartTriangle(worldTriangle: ArrayLike<number>, candidates: VisualChartCandidate[]): VisualChartPiece[] {
  let remaining: VisualBarycentric[][]=[[[1,0,0],[0,1,0],[0,0,1]]];
  const result: VisualChartPiece[]=[];
  for(const {id,chart:ch} of candidates) {
    if (!remaining.length) break;
    const u=[0,3,6].map(k=>coord(worldTriangle,k,ch.e1,ch.o)*8);
    const v=[0,3,6].map(k=>coord(worldTriangle,k,ch.e2,ch.o)*8);
    const cuts:[number[],number,boolean][]=[[u,0,true],[u,ch.w,false],[v,0,true],[v,ch.h,false]];
    const next: VisualBarycentric[][]=[];
    for(const poly of remaining) {
      let inside=poly;
      for(const [values,threshold,greater] of cuts) {
        const outside=halfPlane(inside,values,threshold,!greater);
        if(hasArea(outside))next.push(outside);
        inside=halfPlane(inside,values,threshold,greater);
        if(!hasArea(inside)){inside=[];break;}
      }
      if(hasArea(inside))result.push({chartId:id,vertices:inside});
    }
    remaining=next;
  }
  for(const vertices of remaining)if(hasArea(vertices))result.push({chartId:null,vertices});
  return result;
}

/** CURRENT custom chart rows -> UV contract, not the recovered native atlas layout. */
export function visualChartUv(worldPosition: ArrayLike<number>, chart: Chart, pageWidth:number, pageHeight:number): [number,number] {
  const u=coord(worldPosition,0,chart.e1,chart.o)*8;
  const v=coord(worldPosition,0,chart.e2,chart.o)*8;
  return [(chart.x0+u)/pageWidth,1-(chart.y0+v)/pageHeight];
}
