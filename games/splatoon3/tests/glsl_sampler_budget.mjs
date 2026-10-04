// Static fragment-sampler counter for three.js material hooks: resolves #include, evaluates the preprocessor with the
// defines three would set for the material, then counts sampler uniforms reachable from main() (call graph). This is
// what the GLSL linker keeps active, as an upper bound (no dead-code elimination inside reachable functions).
import * as THREE from 'three';

const SAMPLER=/\buniform\s+(?:(?:highp|mediump|lowp)\s+)?(sampler2D|usampler2D|isampler2D|samplerCube|sampler2DShadow|sampler3D|sampler2DArray|sampler2DArrayShadow|samplerCubeShadow)\s+([^;]+);/g;

export function resolveIncludes(src){
  return src.replace(/^[ \t]*#include +<([\w\d./]+)>/gm,(m,name)=>{const c=THREE.ShaderChunk[name];if(c===undefined)throw new Error('chunk '+name);return resolveIncludes(c);});
}

function evalExpr(expr,defs){
  let e=expr.replace(/defined\s*\(\s*(\w+)\s*\)/g,(m,n)=>n in defs?'1':'0').replace(/defined\s+(\w+)/g,(m,n)=>n in defs?'1':'0');
  e=e.replace(/\b[A-Za-z_]\w*\b/g,n=>{const v=defs[n];return v===undefined||v===''?(v===''?'1':'0'):String(v);});
  if(!/^[\d\s()!<>=&|+\-*/.]*$/.test(e))throw new Error('preprocessor expression: '+expr+' → '+e);
  return !!Function('return ('+e+')')();
}

export function preprocess(src,defines){
  const defs={...defines};const out=[];const stack=[];
  const active=()=>stack.every(s=>s.on);
  for(const line of src.split('\n')){
    const t=line.trim();
    let m;
    if((m=t.match(/^#\s*ifdef\s+(\w+)/))){stack.push({on:active()&&m[1] in defs,done:m[1] in defs,parent:active()});continue;}
    if((m=t.match(/^#\s*ifndef\s+(\w+)/))){stack.push({on:active()&&!(m[1] in defs),done:!(m[1] in defs),parent:active()});continue;}
    if((m=t.match(/^#\s*if\s+(.*)$/))){const p=active(),v=p&&evalExpr(m[1],defs);stack.push({on:v,done:v,parent:p});continue;}
    if((m=t.match(/^#\s*elif\s+(.*)$/))){const s=stack.at(-1);const v=s.parent&&!s.done&&evalExpr(m[1],defs);s.on=v;s.done||=v;continue;}
    if(/^#\s*else\b/.test(t)){const s=stack.at(-1);s.on=s.parent&&!s.done;s.done=true;continue;}
    if(/^#\s*endif\b/.test(t)){stack.pop();continue;}
    if(!active())continue;
    if((m=t.match(/^#\s*define\s+(\w+)(?:\s+(.*))?$/))){defs[m[1]]=(m[2]??'').trim();continue;}
    if((m=t.match(/^#\s*undef\s+(\w+)/))){delete defs[m[1]];continue;}
    if(/^#/.test(t))continue;
    out.push(line);
  }
  if(stack.length)throw new Error('unbalanced #if');
  return out.join('\n');
}

const stripComments=s=>s.replace(/\/\*[\s\S]*?\*\//g,' ').replace(/\/\/[^\n]*/g,' ');

export function activeSamplers(fragment,defines){
  const code=stripComments(preprocess(resolveIncludes(fragment),defines));
  const samplers=new Map();
  for(const m of code.matchAll(SAMPLER))for(const raw of m[2].split(',')){const n=raw.trim().replace(/\[.*$/,'');if(n)samplers.set(n,m[1]);}
  // top-level function bodies
  const fns=new Map();let depth=0;
  for(let i=0;i<code.length;i++){
    const c=code[i];
    if(c==='{'){
      if(depth===0){const head=code.slice(Math.max(0,i-400),i);const mm=head.match(/(\w+)\s*\([^()]*\)\s*$/);
        let j=i,d=0;for(;j<code.length;j++){if(code[j]==='{')d++;else if(code[j]==='}'&&--d===0)break;}
        if(mm&&!/\bstruct\s+\w+\s*$/.test(head)){const prev=fns.get(mm[1])??'';fns.set(mm[1],prev+code.slice(i,j+1));}
        i=j;continue;}
      depth++;
    }else if(c==='}')depth--;
  }
  if(!fns.has('main'))throw new Error('main() missing');
  const seen=new Set(['main']),todo=['main'];
  while(todo.length){const body=fns.get(todo.pop());for(const m of body.matchAll(/\b(\w+)\s*\(/g))if(fns.has(m[1])&&!seen.has(m[1])){seen.add(m[1]);todo.push(m[1]);}}
  const used=new Set();
  for(const f of seen)for(const m of fns.get(f).matchAll(/\b\w+\b/g))if(samplers.has(m[0]))used.add(m[0]);
  return [...used].sort();
}

/** Defines three r180 WebGLProgram derives for a MeshStandardMaterial (the subset that gates samplers). */
export function standardDefines(mat,{envMap=true,skinning=false}={}){
  const d={STANDARD:'',...(mat.defines??{})};
  if(mat.map)d.USE_MAP='';if(mat.normalMap){d.USE_NORMALMAP='';d.USE_NORMALMAP_TANGENTSPACE='';}
  if(mat.roughnessMap)d.USE_ROUGHNESSMAP='';if(mat.metalnessMap)d.USE_METALNESSMAP='';
  if(mat.emissiveMap)d.USE_EMISSIVEMAP='';if(mat.aoMap)d.USE_AOMAP='';if(mat.alphaMap)d.USE_ALPHAMAP='';
  if(mat.lightMap)d.USE_LIGHTMAP='';if(mat.bumpMap)d.USE_BUMPMAP='';if(mat.displacementMap)d.USE_DISPLACEMENTMAP='';
  if(mat.alphaTest>0)d.USE_ALPHATEST='';
  if(envMap||mat.envMap){d.USE_ENVMAP='';d.ENVMAP_TYPE_CUBE_UV='';d.ENVMAP_MODE_REFLECTION='';d.ENVMAP_BLENDING_NONE='';d.CUBEUV_TEXEL_WIDTH='0.0';d.CUBEUV_TEXEL_HEIGHT='0.0';d.CUBEUV_MAX_MIP='8.0';}
  if(skinning)d.USE_SKINNING='';
  for(const k of ['NUM_DIR_LIGHTS','NUM_POINT_LIGHTS','NUM_SPOT_LIGHTS','NUM_RECT_AREA_LIGHTS','NUM_HEMI_LIGHTS','NUM_DIR_LIGHT_SHADOWS','NUM_POINT_LIGHT_SHADOWS','NUM_SPOT_LIGHT_SHADOWS','NUM_SPOT_LIGHT_MAPS','NUM_SPOT_LIGHT_COORDS','NUM_LIGHT_PROBES','NUM_CLIPPING_PLANES','UNION_CLIPPING_PLANES'])d[k]='0';
  return d;
}

/** Run a material's onBeforeCompile chain on MeshStandardMaterial sources and count active fragment samplers. */
export function materialFragmentSamplers(mat,opts){
  const sh={uniforms:{},defines:mat.defines,vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  mat.onBeforeCompile(sh,{});
  return activeSamplers(sh.fragmentShader,standardDefines(mat,opts));
}
