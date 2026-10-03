// nn::vfx 파티클 재현(VFXB v46 이미터 값). 근거: docs/effect_sound/effect_resources.md §2.2.3~2.2.6.
//   방출 0x710081c0b8 / 0x710081b784 · 파티클 생성 0x710081e3e4 · GPU_TIME 정점 셰이더(프로그램 1940)
//   P = P0 + m·(V0·f(t) + G·g(t)),  f = a==1 ? t : (1-a^t)/(1-a),  g = a==1 ? t²/2 : (t-(a^t-1)/ln a)/(1-a)
// 시간 단위 = 게임 프레임. 위치·속도 단위 = 원본 월드 단위(코어와 같음).
import * as THREE from "three";
import { VERT, FRAG } from "./particle_shaders.ts";
import { applyEmitterRender } from "./render_state.ts";
import { FX_PROGRAMS, FX_WEB_DEFAULTS } from "./shader_contract.ts";

export type Emitter = Record<string, unknown>;
type V3 = [number, number, number];

const n = (e: Emitter, k: string, d = 0): number => {
  const v = e[k];
  return typeof v === "number" && Number.isFinite(v) ? v : d;
};
const v3 = (e: Emitter, k: string, d: V3 = [0, 0, 0]): V3 => {
  const v = e[k];
  return Array.isArray(v) && v.length >= 3 ? [Number(v[0]), Number(v[1]), Number(v[2])] : d;
};
const keys = (e: Emitter, k: string): number[][] => {
  const v = e[k];
  return Array.isArray(v) ? (v as number[][]) : [];
};

/** 이미터 행렬(월드): 원점 + 기저 3축(열). follow ALL 이면 매 프레임 바뀐다. */
export interface EmitMatrix {
  o: V3;
  x: V3;
  y: V3;
  z: V3;
}

export function identityMatrix(o: V3): EmitMatrix {
  return { o, x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] };
}

export function mulDir(m: EmitMatrix, v: V3): V3 {
  return [
    m.x[0] * v[0] + m.y[0] * v[1] + m.z[0] * v[2],
    m.x[1] * v[0] + m.y[1] * v[1] + m.z[1] * v[2],
    m.x[2] * v[0] + m.y[2] * v[1] + m.z[2] * v[2],
  ];
}

/** 기저가 직교 정규라고 보고 월드 방향을 이미터 로컬로(전치 곱) */
function toLocal(m: EmitMatrix, v: V3): V3 {
  const d = (a: V3): number => a[0] * v[0] + a[1] * v[1] + a[2] * v[2];
  return [d(m.x), d(m.y), d(m.z)];
}

/** 이미터 회전 Rz·Ry·Rx. 원본 080e4cc 순서; 삼각함수/난수는 웹 경계 */
function applyEmitterRotate(m: EmitMatrix, r: V3): EmitMatrix {
  if (!r[0] && !r[1] && !r[2]) return m;
  const e = new THREE.Euler(r[0], r[1], r[2], "ZYX");
  const q = new THREE.Matrix4().makeRotationFromEuler(e);
  const b = new THREE.Matrix4().makeBasis(new THREE.Vector3(...m.x), new THREE.Vector3(...m.y), new THREE.Vector3(...m.z));
  b.multiply(q);
  const x = new THREE.Vector3(), y = new THREE.Vector3(), z = new THREE.Vector3();
  b.extractBasis(x, y, z);
  return { o: m.o, x: x.toArray() as V3, y: y.toArray() as V3, z: z.toArray() as V3 };
}

const ATTRS: [string, number][] = [
  ["aOrigin", 3],
  ["aBx", 3],
  ["aBy", 3],
  ["aBz", 3],
  ["aP0", 3],
  ["aV0", 3],
  ["aG", 3],
  ["aTime", 4],
  ["aScale0", 3],
  ["aRot0", 3],
  ["aRotAdd", 3],
  ["aRand", 4],
  ["aColor", 3],
];

function keyUniform(k: number[][]): THREE.Vector4[] {
  const out: THREE.Vector4[] = [];
  for (let i = 0; i < 8; i++) {
    const r = k[i] ?? k[k.length - 1] ?? [1, 1, 1, 0];
    out.push(new THREE.Vector4(r[0], r[1], r[2], r[3]));
  }
  return out;
}

export interface ParticleInputs {
  samplers?: ReadonlyMap<number,THREE.Texture>;
  lighting?: Record<string,THREE.IUniform>;
  depth?: Record<string,THREE.IUniform>;
}
/** 이미터 하나의 파티클 묶음(인스턴스 메시 하나). */
export class ParticleBatch {
  readonly name: string;
  readonly def: Emitter;
  readonly mesh: THREE.Mesh;
  private readonly geo: THREE.InstancedBufferGeometry;
  private readonly attrs = new Map<string, THREE.InstancedBufferAttribute>();
  private readonly owner: (EmitterInstance | null)[];
  private readonly cap: number;
  private next = 0;
  private readonly particleData: Float32Array;
  private readonly particleTexture: THREE.DataTexture;
  private readonly emptyGrid: THREE.DataTexture;
  private readonly attrColumns=new Map(ATTRS.map(([name],i)=>[name,i]));
  readonly uniforms: Record<string, THREE.IUniform>;

  /**
   * prim = G3PR 프리미티브 형상(없으면 1×1 사각형). sphere = 프리미티브가 없는 탄 ball 의 구 근사.
   * billboardType: nn::vfx 순서 0 Billboard, 2 YBillboard, 3 PolygonXY, 4 PolygonXZ, 5 VelLook [3·4 는 셰이더 옵션, 나머지 추정].
   */
  constructor(name: string, def: Emitter, cap: number, map: THREE.Texture | null, prim: THREE.BufferGeometry | null, sphere: boolean,inputs:ParticleInputs={}) {
    this.name = name;
    this.def = def;
    this.cap = cap;
    this.owner = new Array(cap).fill(null);
    const base: THREE.BufferGeometry = prim ?? (sphere ? new THREE.IcosahedronGeometry(0.5, 1) : new THREE.PlaneGeometry(1, 1));
    this.geo = new THREE.InstancedBufferGeometry();
    this.geo.index = base.index;
    // Keep every decoded G3PR attribute. Native VAT row is separate from UV.xy.
    for(const [key,attribute] of Object.entries(base.attributes))this.geo.setAttribute(key,attribute);
    const vertexCount=base.getAttribute("position").count;
    if(!this.geo.hasAttribute("normal"))this.geo.computeVertexNormals();
    if(!this.geo.hasAttribute("tangent")){
      const fallbackTangent=new Float32Array(vertexCount*4);
      for(let i=0;i<vertexCount;i++)fallbackTangent[i*4+3]=1;
      // Zero XYZ selects the derivative basis; positive handedness is its web adapter default.
      this.geo.setAttribute("tangent",new THREE.BufferAttribute(fallbackTangent,4));
    }
    const c=base.getAttribute("color"),colors=new Float32Array(vertexCount*4);
    for(let i=0;i<vertexCount;i++)colors.set(c?[c.getX(i),c.getY(i),c.getZ(i),c.itemSize>3?c.getW(i):1]:[1,1,1,1],i*4);
    this.geo.setAttribute("fxVertexColor",new THREE.BufferAttribute(colors,4));
    if(!this.geo.hasAttribute("uv1"))this.geo.setAttribute("uv1",new THREE.BufferAttribute(new Float32Array(vertexCount*2),2));
    // Original 082c0a0 merges f32x2 _u0/_u1 as a vec4 at offset12: native z == _u1.x.
    const row=base.getAttribute("vatRow")??base.getAttribute("_vat_row")??([1383,1385].includes(n(def,"shaderIndex"))?base.getAttribute("uv1"):undefined);
    const vatRows=new Float32Array(vertexCount);
    if(row)for(let i=0;i<vertexCount;i++)vatRows[i]=row.getX(i);
    this.geo.setAttribute("vatRow",new THREE.BufferAttribute(vatRows,1));
    const uvA = base.getAttribute("uv");
    if (uvA) this.geo.setAttribute("uv", uvA);
    else this.geo.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(base.getAttribute("position").count * 2), 2));
    this.geo.instanceCount = cap;
    // Thirteen instance fields plus surface attributes exceed WebGL's 16-location minimum.
    // A state texture leaves one aSlot location while preserving all primitive attributes.
    this.particleData=new Float32Array(cap*ATTRS.length*4);
    this.particleTexture=new THREE.DataTexture(this.particleData,ATTRS.length,cap,THREE.RGBAFormat,THREE.FloatType);
    this.particleTexture.minFilter=this.particleTexture.magFilter=THREE.NearestFilter;
    this.particleTexture.generateMipmaps=false;this.particleTexture.needsUpdate=true;
    this.geo.setAttribute("aSlot",new THREE.InstancedBufferAttribute(Float32Array.from({length:cap},(_,i)=>i),1));
    for (const [a, s] of ATTRS) {
      const attr = new THREE.InstancedBufferAttribute(new Float32Array(cap * s), s);
      attr.setUsage(THREE.DynamicDrawUsage);
      this.attrs.set(a, attr);
      this.geo.setAttribute(a, attr);
    }
    const loop = keys(def, "loopRate_c0_a0_c1_a1_scale");
    const loopR = keys(def, "loopRandom_c0_a0_c1_a1_scale");
    const periods=loop as unknown as number[],phases=loopR as unknown as number[];
    const modes=(def.keyInterpolation??def.keyInterpolationTypes??[0,0,0,0,0]) as number[];
    const maps=inputs.samplers??new Map<number,THREE.Texture>();
    const program=n(def,"shaderIndex");
    const contractReady=["scaleKeys","color0Keys","color1Keys","alpha0Keys","alpha1Keys"].every(k=>keys(def,k).length>0);
    // An old or incomplete loader cannot supply the native combiner contract. Keep its prior web fallback.
    const known=FX_PROGRAMS.has(program)&&contractReady;
    const vat=maps.get(2)??null,hasVat=known&&(program===1383||program===1385)&&!!vat&&!!row;
    const near=Array.isArray(def.nearFade)?def.nearFade as number[]:[0,0];
    this.emptyGrid=new THREE.DataTexture(new Uint32Array(400).fill(0xffffffff),20,20,THREE.RedIntegerFormat,THREE.UnsignedIntType);
    this.emptyGrid.minFilter=this.emptyGrid.magFilter=THREE.NearestFilter;this.emptyGrid.needsUpdate=true;
    this.uniforms = {
      uNow: { value: 0 },
      uParticles:{value:this.particleTexture},uProgram:{value:known?program:0},
      uVat:{value:vat},uHasVat:{value:hasVat?1:0},uVatRate:{value:FX_WEB_DEFAULTS.vatRate},uVatNormalOffset:{value:n(def,"vatNormalOffset")},
      uLinkedAlpha:{value:FX_WEB_DEFAULTS.linkedAlpha},uAlphaRemap:{value:new THREE.Vector2(...FX_WEB_DEFAULTS.alphaRemap as [number,number])},
      uFade:{value:1},uNearFade:{value:new THREE.Vector2(near[0]??0,near[1]??0)},uSoftDistance:{value:n(def,"softDistance")},
      uAlphaThreshold:{value:n(def,"alphaThreshold",program===1202?.5:0)},
      uColor1K:{value:keyUniform(keys(def,"color1Keys"))},uAlpha1K:{value:keyUniform(keys(def,"alpha1Keys"))},
      uColor1N:{value:n(def,"numColor1Keys",Math.max(1,keys(def,"color1Keys").length))},
      uAlpha1N:{value:n(def,"numAlpha1Keys",Math.max(1,keys(def,"alpha1Keys").length))},
      uColor1Type:{value:n(def,"color1Type")},uAlpha1Type:{value:n(def,"alpha1Type")},
      uPeriods:{value:new THREE.Vector4(...[0,1,2,3].map(i=>periods[i]??0) as [number,number,number,number])},
      uPhases:{value:new THREE.Vector4(...[0,1,2,3].map(i=>phases[i]??0) as [number,number,number,number])},
      uKeyModes:{value:new THREE.Vector4(...[0,1,2,3].map(i=>modes[i]??0) as [number,number,number,number])},uScaleMode:{value:modes[4]??0},
      uMap1:{value:maps.get(1)??null},uMap2:{value:maps.get(2)??null},uHasNormal:{value:maps.has(1)?1:0},
      uLightingAvailable:{value:known&&inputs.lighting?1:0},
      uSceneDepth:{value:null},uDepthNear:{value:.1},uDepthFar:{value:3000},uDepthResolution:{value:new THREE.Vector2(1,1)},uDepthAvailable:{value:0},
      uWebRoughness:{value:FX_WEB_DEFAULTS.roughness},uWebFresnel:{value:FX_WEB_DEFAULTS.fresnel},
      hLightColor:{value:new THREE.Vector3(1,1,1)},hLightDirection:{value:new THREE.Vector3(0,-1,0)},hSH:{value:Array.from({length:7},()=>new THREE.Vector4())},
      hGrid:{value:this.emptyGrid},hGridOrigin:{value:new THREE.Vector3()},hInvCell:{value:new THREE.Vector3(1,1,1)},
      hDynColor:{value:Array.from({length:30},()=>new THREE.Vector4())},hDynAtt:{value:Array.from({length:30},()=>new THREE.Vector4())},
      hDynPos:{value:Array.from({length:30},()=>new THREE.Vector4())},hDynDir:{value:Array.from({length:30},()=>new THREE.Vector4())},
      hDepthFog:{value:new THREE.Vector4()},hHeightFog:{value:new THREE.Vector4()},hDepthRange:{value:new THREE.Vector3(10,1000,.3125)},hHeightRange:{value:new THREE.Vector2(15,90)},
      uAir: { value: n(def, "airRegist", 1) },
      uRotRegist: { value: n(def, "rotateRegist", 1) },
      uScaleK: { value: keyUniform(keys(def, "scaleKeys")) },
      uScaleN: { value: n(def, "numScaleKeys", Math.max(1,keys(def,"scaleKeys").length)) },
      uAlphaK: { value: keyUniform(keys(def, "alpha0Keys")) },
      uAlphaN: { value: n(def, "numAlpha0Keys", Math.max(1,keys(def,"alpha0Keys").length)) },
      uAlphaType: { value: n(def, "alpha0Type", 0) },
      uColorK: { value: keyUniform(keys(def, "color0Keys")) },
      uColorN: { value: n(def, "numColor0Keys", Math.max(1,keys(def,"color0Keys").length)) },
      uColorType: { value: n(def, "color0Type", 0) },
      uPivot: { value: new THREE.Vector3(...v3(def, "pivotOffset")) },
      uPlane: { value: !prim && sphere ? 2 : n(def, "billboardType", 3) === 4 ? 1 : 0 },
      uBill: { value: n(def, "billboardType", 3) },
      uRotOrder: { value: n(def, "rotType", 0) },
      uLoopRate: { value: Number((loop as unknown as number[])[4] ?? 0) },
      uLoopRandom: { value: Number((loopR as unknown as number[])[4] ?? 0) },
      uMap: { value: maps.get(0)??map },
      uHasMap: { value: maps.has(0)||map ? 1 : 0 },
      uColorScale: { value: n(def, "colorScale", 1) },
    };
    Object.assign(this.uniforms,inputs.lighting,inputs.depth);
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: this.uniforms,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      toneMapped:false,
    });
    applyEmitterRender(mat,def);
    mat.userData.portRemaining=["native dynamic0/1 and Custom1 producer","native env array layer6","FX-specific BRDF/light coefficients","GPU linked/default alpha","CPU full particle trajectory","sampler texture scroll","unknown shader programs retain web fallback","volume2 and native direction table remain unknown","emitter SRT random/poly trig"];
    mat.userData.nativeProgram=program;mat.userData.knownShaderContract=known;mat.userData.contractInputsReady=contractReady;
    mat.userData.vat={enabled:hasVat,rowSource:row?(base.hasAttribute("vatRow")?"native primitive VAT row":"082c0a0 packed _u0/_u1: uv1.x"):"missing",rateSource:"FX_WEB_DEFAULTS.vatRate (native producer unknown)"};
    mat.userData.webDefaults=FX_WEB_DEFAULTS;
    this.mesh = new THREE.Mesh(this.geo, mat);
    this.mesh.frustumCulled = false;
    this.mesh.name = `fx:${name}`;
    if (!prim) base.dispose();
  }

  private set(a: string, i: number, v: ArrayLike<number>): void {
    const at = this.attrs.get(a)!;
    const arr = at.array as Float32Array;
    const s = at.itemSize;
    const dst=(i*ATTRS.length+this.attrColumns.get(a)!)*4;
    for (let k = 0; k < s; k++) {arr[i * s + k] = v[k] ?? 0;this.particleData[dst+k]=arr[i*s+k];}
    this.particleTexture.needsUpdate=true;
    at.addUpdateRange(i * s, s);
    at.needsUpdate = true;
  }

  private writeMatrix(i: number, m: EmitMatrix): void {
    this.set("aOrigin", i, m.o);
    this.set("aBx", i, m.x);
    this.set("aBy", i, m.y);
    this.set("aBz", i, m.z);
  }

  /** 파티클 하나 생성(0x710081e3e4). rnd = 0..1 난수기. */
  spawn(inst: EmitterInstance, now: number, rnd: () => number): void {
    const e = this.def;
    const i = this.next;
    this.next = (this.next + 1) % this.cap;
    this.owner[i] = inst;
    const m = inst.matrix;
    // 위치: 형상(volumeType) 식은 미판독 — 대상 이미터는 전부 0(점)으로 본다. + 난수 단위 벡터 × positionRandom
    const pr = n(e, "positionRandom");
    let p0: V3 = [0, 0, 0];
    if (pr) {
      const u = [rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1];
      const l = Math.hypot(u[0], u[1], u[2]) || 1;
      p0 = [(u[0] / l) * pr, (u[1] / l) * pr, (u[2] / l) * pr];
    }
    // 속도: 지정 방향 × 배율 (+ 확산 원뿔), velRandom
    const dd = v3(e, "designatedDir", [0, 1, 0]);
    const ds = n(e, "designatedDirScale");
    let vel: V3 = [dd[0] * ds, dd[1] * ds, dd[2] * ds];
    const ang = n(e, "diffusionDirAngle");
    if (ang > 0 && ds) {
      const c = 1 - (ang / 90) * rnd();
      const s = Math.sqrt(Math.max(0, 1 - c * c));
      const ph = 2 * Math.PI * rnd();
      const d = new THREE.Vector3(...dd).normalize();
      const t1 = new THREE.Vector3(1, 0, 0);
      if (Math.abs(d.x) > 0.9) t1.set(0, 1, 0);
      const a1 = t1.clone().cross(d).normalize();
      const a2 = d.clone().cross(a1);
      const w = d.multiplyScalar(c).add(a1.multiplyScalar(s * Math.cos(ph))).add(a2.multiplyScalar(s * Math.sin(ph)));
      vel = [w.x * ds, w.y * ds, w.z * ds];
    }
    const vr = n(e, "velRandom");
    if (vr) {
      const k = 1 - (rnd() * vr) / 100;
      vel = [vel[0] * k, vel[1] * k, vel[2] * k];
    }
    const dv = v3(e, "diffusionVel");
    if (dv[0] || dv[1] || dv[2]) vel = [vel[0] + (rnd() * 2 - 1) * dv[0], vel[1] + (rnd() * 2 - 1) * dv[1], vel[2] + (rnd() * 2 - 1) * dv[2]];
    // 중력: WORLD_GRAVITY 면 월드 방향을 이미터 로컬로 되돌린다
    const gs = n(e, "gravityScale");
    const gd = v3(e, "gravityDir", [0, -1, 0]);
    let g: V3 = [gd[0] * gs, gd[1] * gs, gd[2] * gs];
    if (n(e, "isWorldGravity") && gs) g = toLocal(m, g);
    // 수명: int(L·(1 − floor(u·lifeRandom)/100))
    const L = n(e, "life", 1);
    const life = n(e, "infiniteLife") ? 2.68e8 : Math.trunc(L * (1 - Math.floor(rnd() * n(e, "lifeRandom")) / 100));
    const mr = n(e, "momentumRandom");
    const mom = 1 + mr - 2 * mr * rnd();
    // 크기: particleScale·(1 − u·random%/100), 세 값이 같으면 u 공유
    const ps = v3(e, "particleScale", [1, 1, 1]);
    const psr = v3(e, "particleScaleRandom");
    const shared = psr[0] === psr[1] && psr[1] === psr[2];
    const u0 = shared?rnd():0;
    const sc: V3 = [0, 1, 2].map((k) => ps[k] * (1 - ((shared ? u0 : rnd()) * psr[k]) / 100)) as V3;
    const es = v3(e, "emitterScale", [1, 1, 1]);
    const scale: V3 = [sc[0] * es[0] * inst.scale, sc[1] * es[1] * inst.scale, sc[2] * es[2] * inst.scale];
    // 회전: 초기 + (rand − 0.5)·initRand, 추가 = rotateAdd + (r1 + r2 − 1)·addRand
    const ri = v3(e, "rotateInit");
    const rir = v3(e, "rotateInitRand");
    const ra = v3(e, "rotateAdd");
    const rar = v3(e, "rotateAddRand");
    const rot0: V3 = [0, 1, 2].map((k) => ri[k] + (rnd() - 0.5) * rir[k]) as V3;
    const radd: V3 = [0, 1, 2].map((k) => ra[k] + (rnd() + rnd() - 1) * rar[k]) as V3;
    this.writeMatrix(i, m);
    this.set("aP0", i, p0);
    this.set("aV0", i, vel);
    this.set("aG", i, g);
    this.set("aTime", i, [now, Math.max(1, life), mom, 1]);
    this.set("aScale0", i, scale);
    this.set("aRot0", i, rot0);
    this.set("aRotAdd", i, radd);
    this.set("aRand", i, [rnd(), rnd(), rnd(), rnd()]);
    this.set("aColor", i, inst.color);
  }

  /** follow ALL: 살아 있는 파티클의 이미터 행렬을 현재 값으로 */
  follow(inst: EmitterInstance): void {
    for (let i = 0; i < this.cap; i++) if (this.owner[i] === inst) this.writeMatrix(i, inst.matrix);
  }

  /** POS keeps birth rotation/scale and follows current origin only (08157b0). */
  followPosition(inst:EmitterInstance):void {
    for(let i=0;i<this.cap;i++)if(this.owner[i]===inst)this.set("aOrigin",i,inst.matrix.o);
  }
  kill(inst: EmitterInstance): void {
    const at = this.attrs.get("aTime")!;
    const arr = at.array as Float32Array;
    for (let i = 0; i < this.cap; i++) {
      if (this.owner[i] !== inst) continue;
      this.owner[i] = null;
      arr[i * 4 + 3] = 0;
      this.particleData[(i*ATTRS.length+7)*4+3]=0;this.particleTexture.needsUpdate=true;
      at.addUpdateRange(i * 4, 4);
      at.needsUpdate = true;
    }
  }

  dispose(): void {
    this.geo.dispose();this.particleTexture.dispose();this.emptyGrid.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}

/** 이미터 인스턴스(이미터셋 안 이미터 하나의 방출 상태). */
export class EmitterInstance {
  readonly batch: ParticleBatch;
  matrix: EmitMatrix;
  color: V3;
  scale: number;
  private readonly born: number;
  private nextEmit: number;
  private emissionDebt=0;
  emitting = true;
  done = false;
  stoppedAt = -1;
  /** 매 프레임 이미터 행렬을 다시 얻는 함수(뼈 부착) */
  followFn: (() => EmitMatrix) | null = null;

  constructor(batch: ParticleBatch, matrix: EmitMatrix, color: V3, now: number, delay: number, scale = 1) {
    this.batch = batch;
    this.matrix = applyEmitterRotate(matrix, v3(batch.def, "emitterRotate"));
    this.color = color;
    this.scale = scale;
    this.born = now + delay;
    this.nextEmit = this.born + n(batch.def, "emitStart");
  }

  get followAll(): boolean {
    return n(this.batch.def, "followType") === 0;
  }

  setMatrix(m: EmitMatrix): void {
    this.matrix = applyEmitterRotate(m, v3(this.batch.def, "emitterRotate"));
  }

  /** 정수 프레임 now 에서 방출(0x710081b784). 무한 방출(hasEmitEnd 0)은 stop() 까지. */
  step(now: number, rnd: () => number): void {
    if (!this.emitting) return;
    const e = this.batch.def;
    const start = this.born + n(e, "emitStart");
    if (n(e, "hasEmitEnd") && now >= start + n(e, "emitDuration", 1)) {
      this.stop(now);
      return;
    }
    if (now < start || now < this.nextEmit) return;
    const rate = n(e, "emitRate", 1) * (1 - (n(e, "emitRateRandom") / 100) * rnd());
    this.emissionDebt+=rate;
    const cnt=Math.max(0,Math.floor(this.emissionDebt));this.emissionDebt-=cnt;
    for (let k = 0; k < cnt; k++) this.batch.spawn(this, now, rnd);
    // 다음 간격 = interval + 1 + floor(u·intervalRandom) (0x710080e9a4)
    this.nextEmit = now + n(e, "emitInterval") + 1 + Math.floor(rnd() * n(e, "emitIntervalRandom"));
  }

  /** ELink 이벤트 페이드(+8 |= 0x90): 방출만 멈추고 남은 파티클은 수명대로 */
  stop(now: number): void {
    if (!this.emitting) return;
    this.emitting = false;
    this.stoppedAt = now;
  }

  /** OneEmitter 핸들 반환: 인스턴스 즉시 제거 */
  kill(): void {
    this.batch.kill(this);
    this.done = true;
    this.emitting = false;
  }

  finishedBy(now: number): boolean {
    if (this.done) return true;
    if (this.emitting) return false;
    const last = this.stoppedAt >= 0 ? this.stoppedAt : now;
    return now > last + n(this.batch.def, "life", 1) + 1;
  }
}
