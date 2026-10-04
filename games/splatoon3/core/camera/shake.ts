// CameraModule: r10_shake_shooter §4-6,8.1; original10182e8/1018b4c/1010f14.
// Offsets are world translation, not quaternion rotation or weapon spread.
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
    const f=sub(x,i),f2=mul(f,f),twice2=mul(f,add(f,f)),twice3=mul(f,twice2);
    const three2=mul(f,mul(f,3)),f3=mul(f,f2);
    const h00=add(sub(twice3,three2),1),h01=sub(three2,twice3);
    const h10=add(f,sub(f3,twice2)),h11=sub(f3,f2);
    // Value terms precede tangent terms in the original; reassociation changes bits.
    return add(add(add(mul(h00,d[i*2]),mul(h01,d[i*2+2])),mul(h10,d[i*2+1])),mul(h11,d[i*2+3]));
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
/** Supplied producer contract. A generation mismatch invalidates a native SafePtr. */
export interface ShakeParameterRef { value: ShakeParam | null; generation: number }
export interface ShakeOwner { generation: number }
export interface ShakeStartOptions {
  listener?: ArrayLike<number>;
  gain?: number;
  parameterRef?: ShakeParameterRef;
  owner?: () => ShakeOwner | null;
  followOwner?: boolean;
}
export interface ShakeHandle { readonly slot: number; readonly serial: number; alive(): boolean; stop(): void }
export interface ShakeInstanceState {
  frame: number; elapsed: number; valid: boolean; finished: boolean; serial: number;
  gain: number; frameLimit: number; output: number[];
}
interface Instance {
  parameterRef: ShakeParameterRef | null; generation: number; serial: number;
  frame: number; elapsed: number; limit: number; gain: number; output: Float32Array;
  followOwner: boolean; owner: (() => ShakeOwner | null) | null; ownerGeneration: number;
}
export class CameraShakeMixer {
  readonly offset=Float32Array.of(0,0,0);
  private readonly instances: Instance[]=[];
  private serial: number;
  private readonly capacity: number;
  private readonly listener=Float32Array.of(0,0,0);
  readonly parameters: Record<string,ShakeParam>;
  constructor(parameters: Record<string,ShakeParam>, options: { capacity?: number; initialSerial?: number }={}) {
    this.parameters=parameters;
    // Actual Module pool capacity has not been supplied. Dynamic allocation is a web adapter.
    this.capacity=options.capacity ?? Infinity;
    this.serial=(options.initialSerial ?? 0)>>>0;
  }
  private parameter(s: Instance): ShakeParam | null {
    const r=s.parameterRef;
    return r && (r.generation>>>0)===s.generation ? r.value : null;
  }
  private finished(s: Instance): boolean {
    if (s.limit>=1 && s.elapsed>=s.limit) return true;
    const p=this.parameter(s);
    return !p || (!p.IsLooped && F(p.Curve.MaxX)<=F(s.frame));
  }
  start(name: string, emitter: () => ArrayLike<number>, attenuation=1, limit=-1, options: ShakeStartOptions={}): ShakeHandle | null {
    const ref=options.parameterRef ?? { value:this.parameters[name] ?? null,generation:0 };
    if (!name || !ref.value) return null;
    let index=this.instances.findIndex(s=>this.finished(s));
    if (index<0) {
      if (this.instances.length>=this.capacity) return null;
      index=this.instances.length;
      this.instances.push({parameterRef:null,generation:0,serial:0,frame:0,elapsed:0,limit:-1,gain:1,
        output:Float32Array.of(0,0,0),followOwner:false,owner:null,ownerGeneration:0});
    }
    const inst=this.instances[index],serial=this.serial;
    inst.parameterRef=ref;inst.generation=ref.generation>>>0;inst.serial=serial;
    this.serial=(serial+1)>>>0;
    inst.frame=0;inst.elapsed=0;inst.limit=limit>=1 ? limit|0 : -1;
    // ELink gain is sampled at admission. Emitter motion does not resample camera gain.
    inst.gain=F(options.gain ?? shakeDistanceGain(options.listener ?? this.listener,emitter(),attenuation));
    inst.followOwner=options.followOwner ?? (options.owner!==undefined);
    // Native start preserves previous output and owner fields unless the caller writes them.
    if (options.owner!==undefined) {
      inst.owner=options.owner;inst.ownerGeneration=(options.owner()?.generation ?? 0)>>>0;
    }
    return {slot:index,serial,
      alive:()=>inst.serial===serial && !this.finished(inst),
      stop:()=>{if(inst.serial===serial)inst.parameterRef=null;}};
  }
  inspect(handle: ShakeHandle): ShakeInstanceState | null {
    const s=this.instances[handle.slot];
    if (!s || s.serial!==handle.serial) return null;
    return {frame:s.frame,elapsed:s.elapsed,valid:this.parameter(s)!==null,finished:this.finished(s),
      serial:s.serial,gain:s.gain,frameLimit:s.limit,output:Array.from(s.output)};
  }
  step(listener: ArrayLike<number>): void {
    for(let i=0;i<3;i++)this.listener[i]=listener[i];
    this.offset.fill(0);
    for (const s of this.instances) {
      const p=this.parameter(s);
      if (p) {
        const c=p.Curve,axis=p.Axis ?? {X:0,Y:1,Z:0};
        const t=["Linear","Hermit","Step"].includes(c.Type) ? div(s.frame,c.MaxX) : F(s.frame);
        const value=mul(shakeCurve(c.Type,c.Data,t),mul(s.gain,p.Scale ?? 1));
        const a=[axis.X,axis.Y,axis.Z];
        for(let i=0;i<3;i++)s.output[i]=mul(a[i],value);
        if(s.followOwner && p.IsLooped) {
          const owner=s.owner?.();
          if(!owner || (owner.generation>>>0)!==s.ownerGeneration)s.parameterRef=null;
        }
      }
      // Empty/finished slots still increment; output is retained when the SafePtr is invalid.
      s.frame=(s.frame+1)|0;s.elapsed=(s.elapsed+1)|0;
      const current=this.parameter(s);
      if(current?.IsLooped && F(current.Curve.MaxX)<=F(s.frame))s.frame=0;
    }
    // All updates finish before Module performs its eligibility/sum pass.
    for(const s of this.instances) {
      if(this.finished(s))continue;
      for(let i=0;i<3;i++)this.offset[i]=add(this.offset[i],s.output[i]);
    }
  }
}

/** 137b000 camera admission. Legacy CameraRumble/CtrlRumblePattern numbers are not names. */
export function admitCameraShake(mixer: CameraShakeMixer, params: Record<string,unknown>,
  listener: ArrayLike<number>, emitter: () => ArrayLike<number>, owner?: () => ShakeOwner | null): ShakeHandle | null {
  const name=typeof params.CameraRumbleName==="string" ? params.CameraRumbleName : "";
  if(!name)return null;
  const attenuation=typeof params.DistanceAttenuate==="number" ? params.DistanceAttenuate : 1;
  const limit=typeof params.CameraRumbleFrame==="number" ? params.CameraRumbleFrame : -1;
  return mixer.start(name,emitter,attenuation,limit,{listener,owner:owner ?? (()=>null),followOwner:true});
}
