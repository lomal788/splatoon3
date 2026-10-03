// Raw v0 FMAA channels. Native curve readers 088e380/088e4b0; r9 fixture.
// No guessed CP intensity, skin selection, frame resampling or material mixing.
const F=Math.fround;
export interface MaterialCurve {
  target:string;type:string;frameType:string;keyType:string;start:number;end:number;
  scale:number;offset:number;offsetInt:number;pre:string;post:string;frames:number[];keys:number[][];
}
export interface RawMaterialChannels {
  material:string;
  params:{name:string;beginCurve:number;floatCurves:number;intCurves:number;beginConstant:number;constants:number}[];
  patterns:{name:string;curve:number;beginConstant:number}[];
  patternBase:number[];constants:{target:string;f:number;i:number}[];curves:MaterialCurve[];
}
export interface RawMaterialClip {name:string;frames:number;loop:boolean;textureNames:string[];materials:RawMaterialChannels[]}
export interface MaterialAnimationGroup {clips:RawMaterialClip[];materials?:{name:string;params?:Record<string,{type?:string;value?:unknown}>}[]}
export interface MaterialAnimationBank {schema:number;groups:Record<string,MaterialAnimationGroup>}
export interface MaterialPatch {material:string;params:Record<string,Record<string,number>>;patterns:Record<string,string>}
export type MaterialSample={supported:true;clip:RawMaterialClip;patches:MaterialPatch[]}|{supported:false;reason:string};

/** Clamp curves only, finite selected v0 Cubic/Linear/StepInt. Each operation is f32. */
export function sampleNativeMaterialCurve(c:MaterialCurve,frame:number):number {
  if(c.pre!=="Clamp"||c.post!=="Clamp")throw new Error("native curve wrap mode unsupported: "+c.pre+"/"+c.post);
  if(!Number.isFinite(frame)||!c.frames.length||!c.frames.every(Number.isFinite))throw new Error("native material curve finite frame/key range required");
  if(!["Cubic","Linear","StepInt"].includes(c.type))throw new Error("native curve type unsupported: "+c.type);
  const f=F(Math.min(Math.max(F(frame),F(c.start)),F(c.end)));
  let k=0;while(k+1<c.frames.length&&F(c.frames[k+1])<=f)k++;
  const keys=c.keys[k];if(!keys?.length)throw new Error("native material curve keys missing");
  if(c.type==="StepInt")return ((keys[0]|0)+(c.offsetInt|0))|0;
  let value=F(keys[0]);
  if(k+1<c.frames.length) {
    // Native computes a reciprocal then multiplies; do not substitute direct division.
    const t=F(F(f-F(c.frames[k]))*F(1/F(F(c.frames[k+1])-F(c.frames[k]))));
    if(c.type==="Linear")value=F(F(keys[0])+F(t*F(keys[1])));
    else {
      const high=F(t*F(t*F(F(keys[2])+F(t*F(keys[3])))));
      value=F(F(F(keys[0])+F(t*F(keys[1])))+high);
    }
  }
  // Original generic float reader applies scale to the complete polynomial, then offset.
  return F(F(value*F(c.scale))+F(c.offset));
}

export function materialClipInfo(group:MaterialAnimationGroup|null|undefined,name:string):{frames:number;loop:boolean}|null {
  const c=group?.clips.find(a=>a.name===name);return c?{frames:c.frames,loop:c.loop}:null;
}

/** Preserve parameter byte offsets. The consumer chooses typed fields from actual FRES metadata. */
export function sampleMaterialClip(group:MaterialAnimationGroup|null|undefined,name:string,frame:number):MaterialSample {
  const clip=group?.clips.find(a=>a.name===name);if(!clip)return {supported:false,reason:"FMAA clip unavailable: "+name};
  try {
    const patches:MaterialPatch[]=clip.materials.map(m=>{
      const params:MaterialPatch["params"]={};const patterns:MaterialPatch["patterns"]={};
      for(const p of m.params) {
        const offsets:Record<string,number>={};
        for(let k=0;k<p.constants;k++){const c=m.constants[p.beginConstant+k];if(!c)throw new Error("FMAA constant missing: "+p.name);offsets[c.target]=F(c.f);}
        for(let k=0;k<p.floatCurves+p.intCurves;k++){const c=m.curves[p.beginCurve+k];if(!c)throw new Error("FMAA curve missing: "+p.name);offsets[c.target]=sampleNativeMaterialCurve(c,frame);}
        params[p.name]=offsets;
      }
      for(let k=0;k<m.patterns.length;k++) {
        const p=m.patterns[k],c=p.curve>=0?m.curves[p.curve]:undefined;
        const index=c?sampleNativeMaterialCurve(c,frame):m.patternBase[k];
        const texture=clip.textureNames[index];
        if(texture===undefined)throw new Error("FMAA texture index unavailable: "+p.name+"="+index);
        patterns[p.name]=texture;
      }
      return {material:m.material,params,patterns};
    });
    return {supported:true,clip,patches};
  } catch(e) {return {supported:false,reason:e instanceof Error?e.message:String(e)};}
}

export interface NativeTexSrt {Mode:string;Scaling:{X:number;Y:number};Rotation:number;Translation:{X:number;Y:number}}
/** Raw TexSrt update only. SRT-to-Mat matrix producer is a separate native contract. */
export function patchTexSrt(base:NativeTexSrt,offsets:Record<string,number>):NativeTexSrt {
  const out={Mode:base.Mode,Scaling:{...base.Scaling},Rotation:base.Rotation,Translation:{...base.Translation}};
  for(const [key,value] of Object.entries(offsets)) {
    switch(Number(key)) {
      case 0:if(value!==0&&value!==1&&value!==2)throw new Error("native TexSrt mode unsupported: "+value);out.Mode=["ModeMaya","Mode3dsMax","ModeSoftimage"][value];break;
      case 4:out.Scaling.X=F(value);break;case 8:out.Scaling.Y=F(value);break;
      case 12:out.Rotation=F(value);break;case 16:out.Translation.X=F(value);break;case 20:out.Translation.Y=F(value);break;
      default:throw new Error("native TexSrt byte offset unsupported: "+key);
    }
  }
  return out;
}

/** Original initialized holder 14522b0 keeps the previous frame outside [0,FrameCount). */
export function nativeSkinIndex(previous:number,index:number,frameCount:number):{accepted:boolean;frame:number} {
  const i=index|0,n=frameCount|0;return i>=0&&i<n?{accepted:true,frame:F(i)}:{accepted:false,frame:previous};
}

/** One full-weight type11 leaf is supported. Native multi-leaf material blending remains unresolved. */
export function sampleOrdinaryMaterialLeaves(group:MaterialAnimationGroup|null|undefined,leaves:{type:number;clip:string;frame:number;weight:number}[]):MaterialSample|null {
  const a=leaves.filter(l=>l.type===11&&l.weight>0);
  if(!a.length)return null;
  if(a.length!==1||F(a[0].weight)!==1)return {supported:false,reason:"native material multi-leaf/weighted blend unsupported"};
  return sampleMaterialClip(group,a[0].clip,a[0].frame);
}
