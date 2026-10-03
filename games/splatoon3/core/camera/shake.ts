// CameraModule rumble consumers. shake_rumble §3.2a-d and camera_feel §4.4.
// Curve termination comparison is unresolved: finite curves use MaxX as a web boundary.
import { F, add, sub, mul, div, mix, length } from "./native_math.ts";
import { clamp01 } from "./curves.ts";
export interface ShakeParam {
  Curve: { Type: string; Data: number[]; MaxX: number };
  Axis?: { X: number; Y: number; Z: number };
  Scale?: number; IsLooped?: boolean;
}
export function shakeCurve(type: string, d: number[], t: number): number {
  if (!d.length) return 0;
  if (type === "Linear") {
    if (t < 0) return F(d[0]);
    const x=mul(d.length-1,t),i=Math.trunc(x);
    return i<d.length-1 ? mix(d[i],d[i+1],sub(x,i)) : F(d[d.length-1]);
  }
  if (type === "Hermit") {
    if (d.length & 1) return 0;
    if (t < 0) return F(d[0]);
    const m=d.length/2-1,x=mul(m,t),i=Math.trunc(x);
    if (i>=m) return F(d[2*m]);
    const f=sub(x,i),f2=mul(f,f),f3=mul(f2,f);
    const h00=add(sub(mul(2,f3),mul(3,f2)),1),h01=sub(mul(3,f2),mul(2,f3));
    const h10=add(sub(f3,mul(2,f2)),f),h11=sub(f3,f2);
    return add(add(add(mul(h00,d[i*2]),mul(h10,d[i*2+1])),mul(h01,d[i*2+2])),mul(h11,d[i*2+3]));
  }
  if (type === "Step") return F(d[Math.trunc(mul(clamp01(t),d.length-1))]);
  const a=mul(mul(d[0],t),F(6.2831855));
  if (type === "Sin") return mul(F(Math.sin(a)),d[1]);
  if (type === "Cos") return mul(F(Math.cos(a)),d[1]);
  if (type === "SinPow2") { const v=F(Math.sin(a)); return mul(mul(v,v),d[1]); }
  return 0;
}
export function shakeDistanceGain(listener: ArrayLike<number>, emitter: ArrayLike<number>, enabled: number): number {
  if (enabled < 1) return 1;
  const d=length([0,1,2].map(i=>sub(listener[i],emitter[i])));
  return sub(1,clamp01(div(sub(d,15),10)));
}
export interface ShakeHandle { alive(): boolean; stop(): void }
interface Instance {
  param: ShakeParam; frame: number; elapsed: number; limit: number; active: boolean;
  emitter: () => ArrayLike<number>; attenuation: number;
}
export class CameraShakeMixer {
  readonly offset=Float32Array.of(0,0,0);
  private instances: Instance[]=[];
  readonly parameters: Record<string,ShakeParam>;
  constructor(parameters: Record<string,ShakeParam>) { this.parameters=parameters; }
  start(name: string, emitter: () => ArrayLike<number>, attenuation=1, limit=-1): ShakeHandle | null {
    const param=this.parameters[name];
    if (!param) return null;
    const inst: Instance={param,frame:0,elapsed:0,limit,active:true,emitter,attenuation};
    this.instances.push(inst);
    return { alive:()=>inst.active,stop:()=>{inst.active=false;} };
  }
  step(listener: ArrayLike<number>): void {
    this.offset.fill(0);
    for (const s of this.instances) {
      if (!s.active) continue;
      const p=s.param,c=p.Curve,axis=p.Axis ?? {X:0,Y:1,Z:0};
      if ((s.limit>=1 && s.elapsed>=s.limit) || (!p.IsLooped && s.frame>=c.MaxX)) {s.active=false;continue;}
      const t=["Linear","Hermit","Step"].includes(c.Type) ? div(s.frame,c.MaxX) : s.frame;
      const value=mul(mul(shakeCurve(c.Type,c.Data,t),shakeDistanceGain(listener,s.emitter(),s.attenuation)),p.Scale ?? 1);
      s.frame++;s.elapsed++;
      if (p.IsLooped && s.frame>=c.MaxX) s.frame=0;
      // Native module updates first, then sums only !isFinished instances.
      if ((s.limit>=1 && s.elapsed>=s.limit) || (!p.IsLooped && s.frame>=c.MaxX)) {s.active=false;continue;}
      const a=[axis.X,axis.Y,axis.Z];
      for (let i=0;i<3;i++) this.offset[i]=add(this.offset[i],mul(a[i],value));
    }
    this.instances=this.instances.filter(s=>s.active);
  }
}
