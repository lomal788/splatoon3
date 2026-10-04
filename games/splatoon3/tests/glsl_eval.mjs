// Small GLSL interpreter for numeric shader comparison (original decompiled GLSL and web GLSL).
// Values: float/int/bool = number|boolean, vecN = number[], matN = column arrays with isMat, arrays = JS arrays.
// Arithmetic runs in double precision; comparisons use tolerances. Not a bit-exact GPU model.

const TYPES = new Set(["void","float","int","uint","bool","vec2","vec3","vec4","ivec2","ivec3","ivec4","uvec2","uvec3","uvec4","bvec2","bvec3","bvec4","mat2","mat3","mat4","sampler2D","sampler2DArray","usampler2D","isampler2D","sampler3D","samplerCube"]);
const QUAL = new Set(["precise","highp","mediump","lowp","flat","smooth","noperspective","centroid","invariant","in","out","inout","uniform","attribute","varying","const","readonly","writeonly","coherent","restrict"]);
const SWZ = /^([xyzw]{1,4}|[rgba]{1,4}|[stpq]{1,4})$/;

function strip(src) {
  src = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
  src = src.split("\n").filter(l => !/^\s*#/.test(l)).join("\n");
  src = src.replace(/layout\s*\([^)]*\)/g, "");
  return src;
}

function tokenize(src) {
  const out = [];
  const re = /\s+|(0[xX][0-9a-fA-F]+[uU]?)|((?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fFuU]?)|([A-Za-z_]\w*)|(<<=|>>=|\+\+|--|\+=|-=|\*=|\/=|%=|&=|\|=|\^=|&&|\|\||==|!=|<=|>=|<<|>>|[-+*/%<>=!~&|^?:;,.(){}\[\]])/y;
  let m;
  while (re.lastIndex < src.length) {
    const at = re.lastIndex;
    m = re.exec(src);
    if (!m) throw new Error(`glsl tokenize at ${at}: ${src.slice(at, at + 30)}`);
    if (m[1]) { const x = parseInt(m[1].replace(/[uU]$/, ""), 16); out.push({ t: "num", v: String(/[uU]$/.test(m[1]) ? x >>> 0 : x | 0) }); }
    else if (m[2]) {
      const s = m[2];
      const isFloat = /[.eE]/.test(s.replace(/[fFuU]$/, "")) || /[fF]$/.test(s);
      out.push({ t: "num", v: String(Number(s.replace(/[fFuU]$/, ""))), f: isFloat });
    } else if (m[3]) out.push({ t: "id", v: m[3] });
    else if (m[4]) out.push({ t: "op", v: m[4] });
  }
  out.push({ t: "eof", v: "" });
  return out;
}

class Parser {
  constructor(tokens) { this.k = tokens; this.i = 0; this.structTypes = new Set(); }
  peek(o = 0) { return this.k[this.i + o]; }
  next() { return this.k[this.i++]; }
  is(v, o = 0) { const t = this.peek(o); return t.v === v && t.t !== "num"; }
  eat(v) { const t = this.next(); if (t.v !== v) throw new Error(`glsl parse: expected ${v}, got ${t.v} near token ${this.i}: ${this.k.slice(this.i - 5, this.i + 5).map(x => x.v).join(" ")}`); return t; }
  isType(o = 0) { const t = this.peek(o); return t.t === "id" && (TYPES.has(t.v) || QUAL.has(t.v)); }
  // ---------- top level ----------
  program() {
    const items = [];
    while (this.peek().t !== "eof") {
      if (this.is(";")) { this.next(); continue; }
      if (this.is("precision")) { while (!this.is(";")) this.next(); this.next(); continue; }
      const quals = [];
      while (this.peek().t === "id" && QUAL.has(this.peek().v)) quals.push(this.next().v);
      // uniform block: uniform _Name { ... } Name;
      if (this.peek().t === "id" && !TYPES.has(this.peek().v) && this.is("{", 1)) {
        this.next(); this.eat("{");
        let depth = 1; while (depth) { const t = this.next(); if (t.v === "{") depth++; else if (t.v === "}") depth--; }
        const name = this.peek().t === "id" ? this.next().v : null; this.eat(";");
        items.push({ k: "block", name });
        continue;
      }
      const type = this.next().v;
      const name = this.next().v;
      if (this.is("(")) {
        this.eat("(");
        const params = [];
        while (!this.is(")")) {
          while (this.peek().t === "id" && QUAL.has(this.peek().v)) this.next();
          const pt = this.next().v;
          if (pt === "void" && this.is(")")) break;
          const pn = this.next().v;
          if (this.is("[")) { this.next(); this.next(); this.eat("]"); }
          params.push({ type: pt, name: pn });
          if (this.is(",")) this.next();
        }
        this.eat(")");
        if (this.is(";")) { this.next(); continue; }
        items.push({ k: "func", type, name, params, body: this.block() });
        continue;
      }
      // global variable(s)
      this.i--;
      items.push({ k: "global", quals, decl: this.declRest(type) });
    }
    return items;
  }
  declRest(type) {
    const vars = [];
    for (;;) {
      const name = this.next().v;
      let size = null;
      if (this.is("[")) { this.next(); size = this.is("]") ? null : this.expr(); this.eat("]"); }
      let init = null;
      if (this.is("=")) { this.next(); init = this.assign(); }
      vars.push({ name, size, init });
      if (this.is(",")) { this.next(); continue; }
      break;
    }
    this.eat(";");
    return { k: "decl", type, vars };
  }
  block() {
    this.eat("{");
    const body = [];
    while (!this.is("}")) body.push(this.stmt());
    this.eat("}");
    return { k: "block", body };
  }
  stmt() {
    const t = this.peek();
    if (t.v === "{") return this.block();
    if (t.v === ";") { this.next(); return { k: "empty" }; }
    if (t.t === "id") {
      switch (t.v) {
        case "if": { this.next(); this.eat("("); const c = this.expr(); this.eat(")"); const a = this.stmt(); let b = null; if (this.is("else")) { this.next(); b = this.stmt(); } return { k: "if", c, a, b }; }
        case "for": {
          this.next(); this.eat("(");
          let init = null;
          if (this.isType()) { while (QUAL.has(this.peek().v)) this.next(); const ty = this.next().v; init = this.declRest(ty); }
          else if (this.is(";")) this.next(); else { init = { k: "expr", e: this.expr() }; this.eat(";"); }
          const c = this.is(";") ? null : this.expr(); this.eat(";");
          const u = this.is(")") ? null : this.expr(); this.eat(")");
          return { k: "for", init, c, u, body: this.stmt() };
        }
        case "while": { this.next(); this.eat("("); const c = this.expr(); this.eat(")"); return { k: "while", c, body: this.stmt() }; }
        case "do": { this.next(); const body = this.stmt(); this.eat("while"); this.eat("("); const c = this.expr(); this.eat(")"); this.eat(";"); return { k: "do", c, body }; }
        case "return": { this.next(); const e = this.is(";") ? null : this.expr(); this.eat(";"); return { k: "return", e }; }
        case "break": this.next(); this.eat(";"); return { k: "break" };
        case "continue": this.next(); this.eat(";"); return { k: "continue" };
        case "discard": this.next(); this.eat(";"); return { k: "discard" };
      }
      if (this.isType() && (this.peek(1).t === "id" || QUAL.has(t.v))) {
        while (QUAL.has(this.peek().v)) this.next();
        const ty = this.next().v;
        return this.declRest(ty);
      }
    }
    const e = this.expr(); this.eat(";");
    return { k: "expr", e };
  }
  // ---------- expressions ----------
  expr() { let e = this.assign(); while (this.is(",")) { this.next(); e = { k: "seq", a: e, b: this.assign() }; } return e; }
  assign() {
    const lhs = this.ternary();
    const t = this.peek();
    if (t.t === "op" && ["=","+=","-=","*=","/=","%=","&=","|=","^=","<<=",">>="].includes(t.v)) { this.next(); return { k: "assign", op: t.v, l: lhs, r: this.assign() }; }
    return lhs;
  }
  ternary() {
    const c = this.binary(0);
    if (this.is("?")) { this.next(); const a = this.assign(); this.eat(":"); const b = this.assign(); return { k: "cond", c, a, b }; }
    return c;
  }
  binary(level) {
    const L = [["||"],["^^"],["&&"],["|"],["^"],["&"],["==","!="],["<",">","<=",">="],["<<",">>"],["+","-"],["*","/","%"]];
    if (level >= L.length) return this.unary();
    let a = this.binary(level + 1);
    while (this.peek().t === "op" && L[level].includes(this.peek().v)) { const op = this.next().v; a = { k: "bin", op, a, b: this.binary(level + 1) }; }
    return a;
  }
  unary() {
    const t = this.peek();
    if (t.t === "op" && ["-","+","!","~","++","--"].includes(t.v)) { this.next(); return { k: "un", op: t.v, a: this.unary() }; }
    return this.postfix();
  }
  postfix() {
    let e = this.primary();
    for (;;) {
      if (this.is(".")) { this.next(); e = { k: "mem", a: e, n: this.next().v }; }
      else if (this.is("[")) { this.next(); const i = this.expr(); this.eat("]"); e = { k: "idx", a: e, i }; }
      else if (this.is("++") || this.is("--")) { e = { k: "post", op: this.next().v, a: e }; }
      else return e;
    }
  }
  primary() {
    const t = this.next();
    if (t.t === "num") return { k: "num", v: t.v };
    if (t.v === "(") { const e = this.expr(); this.eat(")"); return e; }
    if (t.t === "id") {
      if (t.v === "true" || t.v === "false") return { k: "num", v: t.v };
      if (this.is("(")) {
        this.next(); const args = [];
        while (!this.is(")")) { args.push(this.assign()); if (this.is(",")) this.next(); }
        this.eat(")");
        return { k: "call", n: t.v, args };
      }
      return { k: "id", n: t.v };
    }
    throw new Error(`glsl parse: unexpected ${t.v} at token ${this.i}`);
  }
}

// ---------- runtime ----------
const isArr = Array.isArray;
const dv = new DataView(new ArrayBuffer(4));
const comp = c => "xyzwrgbastpq".indexOf(c) % 4;
function cp(v) { if (!isArr(v)) return v; const o = v.map(cp); if (v.isMat) o.isMat = true; return o; }
function map1(f, a) { return isArr(a) ? a.map(x => map1(f, x)) : f(a); }
function map2(f, a, b) {
  if (isArr(a) && isArr(b)) return a.map((x, i) => map2(f, x, b[i]));
  if (isArr(a)) return a.map(x => map2(f, x, b));
  if (isArr(b)) return b.map(y => map2(f, a, y));
  return f(a, b);
}
function map3(f, a, b, c) {
  const n = isArr(a) ? a.length : isArr(b) ? b.length : isArr(c) ? c.length : 0;
  if (!n) return f(a, b, c);
  const g = (v, i) => isArr(v) ? v[i] : v;
  return Array.from({ length: n }, (_, i) => f(g(a, i), g(b, i), g(c, i)));
}
function matMul(a, b) {
  if (a.isMat && b.isMat) { const o = b.map(col => matVec(a, col)); o.isMat = true; return o; }
  if (a.isMat) return matVec(a, b);
  return a.length ? b.map(col => col.reduce((s, x, i) => s + x * a[i], 0)) : null;
}
function matVec(m, v) { const n = m[0].length; const o = new Array(n).fill(0); for (let c = 0; c < m.length; c++) for (let r = 0; r < n; r++) o[r] += m[c][r] * v[c]; return o; }
function half(x) {
  dv.setFloat32(0, x); const f = dv.getUint32(0);
  const s = (f >>> 16) & 0x8000; let e = ((f >>> 23) & 0xff) - 127 + 15; let m = f & 0x7fffff;
  if (((f >>> 23) & 0xff) === 0xff) return s | 0x7c00 | (m ? 0x200 : 0);
  if (e >= 31) return s | 0x7c00;
  if (e <= 0) { if (e < -10) return s; m |= 0x800000; const sh = 14 - e; let h = m >> sh; const rem = m & ((1 << sh) - 1), hf = 1 << (sh - 1); if (rem > hf || (rem === hf && (h & 1))) h++; return s | h; }
  let h = s | (e << 10) | (m >> 13); const rem = m & 0x1fff; if (rem > 0x1000 || (rem === 0x1000 && (h & 1))) h++; return h;
}
export function halfToFloat(h) {
  const s = h & 0x8000 ? -1 : 1, e = (h >> 10) & 31, m = h & 1023;
  if (e === 0) return s * m * 2 ** -24; if (e === 31) return m ? NaN : s * Infinity;
  return s * (1 + m / 1024) * 2 ** (e - 15);
}
const ctorN = { vec2: 2, vec3: 3, vec4: 4, ivec2: 2, ivec3: 3, ivec4: 4, uvec2: 2, uvec3: 3, uvec4: 4, bvec2: 2, bvec3: 3, bvec4: 4 };
function construct(type, args) {
  if (type === "float") return Number(args[0]);
  // Maxwell F2I semantics: NaN -> 0, out of range saturates (cvt.rzi.sat).
  if (type === "int") { const x = Number(args[0]); if (typeof args[0] === "number" && Number.isInteger(x) && Math.abs(x) < 2 ** 32) return x | 0; return Number.isNaN(x) ? 0 : x >= 2147483647 ? 2147483647 : x <= -2147483648 ? -2147483648 : Math.trunc(x) | 0; }
  if (type === "uint") { const x = Number(args[0]); if (Number.isInteger(x) && x < 0) return x >>> 0; return Number.isNaN(x) || x <= 0 ? 0 : x >= 4294967295 ? 4294967295 : Math.trunc(x) >>> 0; }
  if (type === "bool") return !!args[0];
  if (type in ctorN) {
    const n = ctorN[type], flat = [];
    for (const a of args) isArr(a) ? flat.push(...a.flat()) : flat.push(a);
    let o = flat.length === 1 ? new Array(n).fill(flat[0]) : flat.slice(0, n);
    if (type[0] === "i") o = o.map(x => Math.trunc(Number(x)) | 0);
    else if (type[0] === "u") o = o.map(x => Math.trunc(Number(x)) >>> 0);
    else if (type[0] === "b") o = o.map(Boolean);
    else o = o.map(Number);
    return o;
  }
  if (type === "mat3" || type === "mat4" || type === "mat2") {
    const n = +type[3];
    let o;
    if (args.length === 1 && args[0].isMat) o = Array.from({ length: n }, (_, c) => Array.from({ length: n }, (_, r) => args[0][c]?.[r] ?? (c === r ? 1 : 0)));
    else if (args.length === 1 && !isArr(args[0])) o = Array.from({ length: n }, (_, c) => Array.from({ length: n }, (_, r) => c === r ? args[0] : 0));
    else { const flat = []; for (const a of args) isArr(a) ? flat.push(...a) : flat.push(a); o = Array.from({ length: n }, (_, c) => flat.slice(c * n, c * n + n)); }
    o.isMat = true; return o;
  }
  throw new Error(`glsl ctor ${type}`);
}
function zero(type, size) {
  const one = () => {
    if (type in ctorN) return new Array(ctorN[type]).fill(type[0] === "b" ? false : 0);
    if (/^mat/.test(type)) return construct(type, [0]);
    if (type === "bool") return false;
    return 0;
  };
  return size == null ? one() : Array.from({ length: size }, one);
}
export const DISCARD = Symbol("discard");
const F = {
  fma: (a, b, c) => map3((x, y, z) => x * y + z, a, b, c),
  sqrt: a => map1(Math.sqrt, a), inversesqrt: a => map1(x => 1 / Math.sqrt(x), a),
  abs: a => map1(Math.abs, a), sign: a => map1(Math.sign, a), floor: a => map1(Math.floor, a), ceil: a => map1(Math.ceil, a),
  trunc: a => map1(Math.trunc, a), fract: a => map1(x => x - Math.floor(x), a),
  roundEven: a => map1(x => { const r = Math.round(x); return Math.abs(x % 1) === 0.5 ? 2 * Math.round(x / 2) : r; }, a),
  round: a => map1(Math.round, a),
  exp2: a => map1(x => 2 ** x, a), log2: a => map1(Math.log2, a), exp: a => map1(Math.exp, a), log: a => map1(Math.log, a),
  pow: (a, b) => map2((x, y) => x ** y, a, b), sin: a => map1(Math.sin, a), cos: a => map1(Math.cos, a), tan: a => map1(Math.tan, a),
  asin: a => map1(Math.asin, a), acos: a => map1(Math.acos, a), atan: (a, b) => b === undefined ? map1(Math.atan, a) : map2(Math.atan2, a, b),
  min: (a, b) => map2((x, y) => (y < x ? y : x), a, b), max: (a, b) => map2((x, y) => (y > x ? y : x), a, b),
  clamp: (a, lo, hi) => map3((x, l, h) => Math.min(Math.max(x, l), h), a, lo, hi),
  mix: (a, b, t) => map3((x, y, s) => typeof s === "boolean" ? (s ? y : x) : x + (y - x) * s, a, b, t),
  step: (e, x) => map2((ee, xx) => (xx < ee ? 0 : 1), e, x),
  smoothstep: (e0, e1, x) => map3((a, b, v) => { const t = Math.min(Math.max((v - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); }, e0, e1, x),
  dot: (a, b) => a.reduce((s, x, i) => s + x * b[i], 0), length: a => isArr(a) ? Math.hypot(...a) : Math.abs(a),
  distance: (a, b) => Math.hypot(...a.map((x, i) => x - b[i])),
  normalize: a => { const l = Math.hypot(...a); return a.map(x => x / l); },
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  transpose: m => { const o = m[0].map((_, r) => m.map(c => c[r])); o.isMat = true; return o; },
  any: v => v.some(Boolean), all: v => v.every(Boolean), not: v => v.map(x => !x),
  notEqual: (a, b) => a.map((x, i) => x !== b[i]), equal: (a, b) => a.map((x, i) => x === b[i]),
  lessThan: (a, b) => a.map((x, i) => x < b[i]), greaterThan: (a, b) => a.map((x, i) => x > b[i]),
  floatBitsToInt: a => map1(x => (dv.setFloat32(0, x), dv.getInt32(0)), a),
  floatBitsToUint: a => map1(x => (dv.setFloat32(0, x), dv.getUint32(0)), a),
  intBitsToFloat: a => map1(x => (dv.setInt32(0, x | 0), dv.getFloat32(0)), a),
  uintBitsToFloat: a => map1(x => (dv.setUint32(0, x >>> 0), dv.getFloat32(0)), a),
  packHalf2x16: v => ((half(v[1]) << 16) | half(v[0])) >>> 0,
  unpackHalf2x16: u => [halfToFloat(u & 0xffff), halfToFloat(u >>> 16)],
  texture: (s, uv, bias) => s.sample(uv, bias), texture2D: (s, uv) => s.sample(uv), textureLod: (s, uv, l) => s.sample(uv, l),
  texelFetch: (s, p, l) => s.fetch(p, l), textureSize: (s, l) => s.size(l),
  dFdx: a => map1(() => 0, a), dFdy: a => map1(() => 0, a),
};
function mem(a, n) {
  if (isArr(a) && SWZ.test(n)) { if (n.length === 1) return a[comp(n)]; return [...n].map(c => a[comp(c)]); }
  return a[n];
}
function setsw(a, n, v) {
  if (n.length === 1) { a[comp(n)] = isArr(v) ? v[0] : v; return v; }
  [...n].forEach((c, i) => { a[comp(c)] = isArr(v) ? v[i] : v; });
  return v;
}
const R = {
  cp, mem, setsw, construct, zero, F, DISCARD,
  add: (a, b) => (typeof a === "number" && typeof b === "number") ? a + b : map2((x, y) => x + y, a, b),
  sub: (a, b) => (typeof a === "number" && typeof b === "number") ? a - b : map2((x, y) => x - y, a, b),
  mul: (a, b) => {
    if (typeof a === "number" && typeof b === "number") return a * b;
    if ((a && a.isMat && isArr(b)) || (b && b.isMat && isArr(a))) return matMul(a, b);
    const o = map2((x, y) => x * y, a, b); if ((a && a.isMat) || (b && b.isMat)) o.isMat = true; return o;
  },
  div: (a, b) => (typeof a === "number" && typeof b === "number") ? a / b : map2((x, y) => x / y, a, b),
  mod: (a, b) => map2((x, y) => x % y, a, b),
  neg: a => (typeof a === "number" ? -a : map1(x => -x, a)),
};

// ---------- codegen ----------
function gen(items, opts = {}) {
  const globals = [], funcs = [], exposed = [];
  let inMain = false;
  const E = e => {
    switch (e.k) {
      case "num": return e.v;
      case "id": return e.n;
      case "seq": return `(${E(e.a)},${E(e.b)})`;
      case "cond": return `(${E(e.c)}?${E(e.a)}:${E(e.b)})`;
      case "bin": {
        const a = E(e.a), b = E(e.b);
        switch (e.op) {
          case "+": return `$.add(${a},${b})`; case "-": return `$.sub(${a},${b})`;
          case "*": return `$.mul(${a},${b})`; case "/": return `$.div(${a},${b})`; case "%": return `$.mod(${a},${b})`;
          case "^^": return `(!!(${a})!==!!(${b}))`;
          default: return `(${a}${e.op}${b})`;
        }
      }
      case "un": if (e.op === "-") return `$.neg(${E(e.a)})`; if (e.op === "+") return E(e.a); return `(${e.op}${E(e.a)})`;
      case "post": return `(${E(e.a)}${e.op})`;
      case "mem": return `$.mem(${E(e.a)},${JSON.stringify(e.n)})`;
      case "idx": return `${E(e.a)}[${E(e.i)}]`;
      case "call": {
        const args = e.args.map(E).join(",");
        if (TYPES.has(e.n)) return `$.construct(${JSON.stringify(e.n)},[${args}])`;
        if (funcs.includes(e.n) || !(e.n in F)) return `${e.n}(${args})`;
        return `$.F.${e.n}(${args})`;
      }
      case "assign": {
        const op = e.op.slice(0, -1), l = e.l;
        const rhs = r => {
          if (!op) return r;
          const m = { "+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod" }[op];
          return m ? `$.${m}(${E(l)},${r})` : `(${E(l)}${op}${r})`;
        };
        const r = rhs(E(e.r));
        if (l.k === "mem" && SWZ.test(l.n)) return `$.setsw(${E(l.a)},${JSON.stringify(l.n)},${r})`;
        return `(${E(l)}=$.cp(${r}))`;
      }
    }
    throw new Error(`glsl gen ${e.k}`);
  };
  const S = s => {
    switch (s.k) {
      case "block": return `{${s.body.map(S).join("\n")}}`;
      case "empty": return ";";
      case "expr": return `${E(s.e)};`;
      case "decl":
        if (inMain && opts.expose) { for (const v of s.vars) exposed.push({ name: v.name, type: s.type, size: v.size ? Number(v.size.v) : null }); return s.vars.filter(v => v.init).map(v => `${v.name}=$.cp(${E(v.init)});`).join(""); }
        return `let ${s.vars.map(v => `${v.name}=${v.init ? `$.cp(${E(v.init)})` : `$.zero(${JSON.stringify(s.type)},${v.size ? E(v.size) : "null"})`}`).join(",")};`;
      case "if": return `if(${E(s.c)})${S(s.a)}${s.b ? `else ${S(s.b)}` : ""}`;
      case "for": return `for(${s.init ? S(s.init).replace(/;$/, "") : ""};${s.c ? E(s.c) : ""};${s.u ? E(s.u) : ""})${S(s.body)}`;
      case "while": return `while(${E(s.c)})${S(s.body)}`;
      case "do": return `do ${S(s.body)} while(${E(s.c)});`;
      case "return": return s.e ? `return ${E(s.e)};` : "return;";
      case "break": return "break;"; case "continue": return "continue;";
      case "discard": return "throw $.DISCARD;";
    }
    throw new Error(`glsl gen stmt ${s.k}`);
  };
  for (const it of items) if (it.k === "func") funcs.push(it.name);
  const decls = [], inits = [];
  for (const it of items) {
    if (it.k === "block") { if (it.name) globals.push(it.name); continue; }
    if (it.k === "global") for (const v of it.decl.vars) {
      globals.push(v.name);
      decls.push({ name: v.name, type: it.decl.type, size: v.size ? Number(v.size.v) : null });
      if (v.init) inits.push(`if(!(${JSON.stringify(v.name)} in __in))G.${v.name}=$.cp(${E(v.init)});`);
    }
  }
  const fnSrc = items.filter(i => i.k === "func").map(f => { inMain = f.name === "main"; const body = S(f.body).slice(1, -1); inMain = false; return { f, body }; }).map(({ f, body }) => `const ${f.name}=function(${f.params.map(p => p.name).join(",")}){${f.params.map(p => `${p.name}=$.cp(${p.name});`).join("")}${body}};`).join("\n");
  const body = `with(G){${inits.join("\n")}\n${fnSrc}\ntry{main();}catch(err){if(err===$.DISCARD)G.__discard=true;else throw err;}}`;
  return { decls: decls.concat(exposed), globals, body };
}

/** Compile GLSL source. run(inputs) returns the global environment after main(). */
export function compileGLSL(src, { extraGlobals = {}, expose = false } = {}) {
  const items = new Parser(tokenize(strip(src))).program();
  const g = gen(items, { expose });
  const fn = new Function("G", "$", "__in", g.body);
  return {
    decls: g.decls,
    run(inputs = {}) {
      const G = { __discard: false };
      for (const d of g.decls) G[d.name] = /sampler/.test(d.type) ? { sample: () => [0, 0, 0, 0], fetch: () => [0, 0, 0, 0], size: () => [1, 1, 1] } : zero(d.type, d.size);
      for (const name of g.globals) if (!(name in G)) G[name] = undefined;
      G.gl_Position = [0, 0, 0, 1]; G.gl_FragCoord = [0, 0, 0.5, 1]; G.gl_FrontFacing = true; G.gl_PointSize = 1;
      G.gl_FragColor = [0, 0, 0, 0];
      Object.assign(G, extraGlobals);
      for (const [k, v] of Object.entries(inputs)) if (v !== undefined) G[k] = cp(v);
      fn(G, R, inputs);
      return G;
    },
  };
}

/** UBO helper: flat number array -> {data:[vec4...]} */
export function ubo(rows) { return { data: new Proxy(rows, { get: (t, k) => (typeof k === "string" && /^\d+$/.test(k)) ? (t[k] ?? [0, 0, 0, 0]) : t[k] }) }; }
/** Texture stub sampling a function of uv (nearest/linear is up to the caller). */
export function texFn(f, size = [1, 1]) { return { sample: uv => f(uv), fetch: p => f(p), size: () => size }; }
export { matMul, construct };
