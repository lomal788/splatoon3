// GLSL 부분집합 CPU 해석기(r11 gfx-diff 광원). 원본 역번역 셰이더와 웹 셰이더 문자열을 같은 입력으로 계산해 비교한다.
// float 은 매 연산 f32 반올림(Math.fround), fma 는 한 번 반올림. 텍스처·외부 함수는 호출자가 mock 으로 준다.
const F = Math.fround;
export class I { constructor(v, u = false) { this.v = u ? v >>> 0 : v | 0; this.u = u; } }
export class Bits { constructor(bits) { this.bits = bits >>> 0; } }
export class Mat { constructor(m) { this.m = Array.from(m, F); this.n = Math.round(Math.sqrt(m.length)); } }
const f32 = new Float32Array(1), u32 = new Uint32Array(f32.buffer), i32 = new Int32Array(f32.buffer);
const bitsToF = b => { u32[0] = b >>> 0; return f32[0]; };
const fToBits = x => { f32[0] = x; return u32[0]; };
const num = x => x instanceof I ? x.v : x instanceof Bits ? bitsToF(x.bits) : typeof x === "boolean" ? (x ? 1 : 0) : x;
const isVec = x => Array.isArray(x);
const TYPES = new Set(["void", "float", "int", "uint", "bool", "vec2", "vec3", "vec4", "ivec2", "ivec3", "ivec4", "uvec2", "uvec3", "uvec4", "bvec2", "bvec3", "bvec4", "mat3", "mat4", "sampler2D", "samplerCube", "samplerCubeArray", "usampler2D", "sampler3D"]);
const QUAL = new Set(["precise", "const", "highp", "mediump", "lowp", "in", "out", "inout", "flat", "smooth"]);

function tokenize(src) {
  src = src.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/\/\/[^\n]*/g, " ").replace(/^\s*#[^\n]*/gm, " ");
  const re = /\s*(0[xX][0-9a-fA-F]+[uU]?|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[uUfF]?|[A-Za-z_]\w*|<<=|>>=|\+\+|--|\+=|-=|\*=|\/=|%=|&=|\|=|\^=|==|!=|<=|>=|&&|\|\||\^\^|<<|>>|[-+*\/%<>=!~&|^?:;,.(){}\[\]])/y;
  const out = []; re.lastIndex = 0;
  while (re.lastIndex < src.length) {
    const p = re.lastIndex, m = re.exec(src);
    if (!m) { if (/^\s*$/.test(src.slice(p))) break; throw new Error("tokenize at " + src.slice(p, p + 40)); }
    out.push(m[1]);
  }
  return out;
}

class Parser {
  constructor(t) { this.t = t; this.i = 0; }
  peek(k = 0) { return this.t[this.i + k]; }
  next() { return this.t[this.i++]; }
  eat(s) { if (this.t[this.i] !== s) throw new Error(`expected ${s} got ${this.t[this.i]} near ${this.t.slice(this.i - 8, this.i + 8).join(" ")}`); this.i++; }
  isTypeAt(k) { let j = this.i + k; while (QUAL.has(this.t[j])) j++; return TYPES.has(this.t[j]) && /^[A-Za-z_]/.test(this.t[j + 1] ?? "") && this.t[j + 2] !== "("; }
  block() { this.eat("{"); const b = []; while (this.peek() !== "}") b.push(this.stmt()); this.eat("}"); return { k: "block", b }; }
  stmt() {
    const t = this.peek();
    if (t === "{") return this.block();
    if (t === ";") { this.next(); return { k: "block", b: [] }; }
    if (t === "if") { this.next(); this.eat("("); const c = this.expr(); this.eat(")"); const a = this.stmt(); let e = null; if (this.peek() === "else") { this.next(); e = this.stmt(); } return { k: "if", c, a, e }; }
    if (t === "for") { this.next(); this.eat("("); const init = this.peek() === ";" ? (this.next(), null) : this.simple(); const c = this.peek() === ";" ? null : this.expr(); this.eat(";"); const inc = this.peek() === ")" ? null : this.expr(); this.eat(")"); return { k: "for", init, c, inc, body: this.stmt() }; }
    if (t === "while") { this.next(); this.eat("("); const c = this.expr(); this.eat(")"); return { k: "while", c, body: this.stmt() }; }
    if (t === "do") { this.next(); const body = this.stmt(); this.eat("while"); this.eat("("); const c = this.expr(); this.eat(")"); this.eat(";"); return { k: "do", c, body }; }
    if (t === "break" || t === "continue" || t === "discard") { this.next(); this.eat(";"); return { k: t }; }
    if (t === "return") { this.next(); const e = this.peek() === ";" ? null : this.expr(); this.eat(";"); return { k: "return", e }; }
    return this.simple();
  }
  simple() {
    if (this.isTypeAt(0)) {
      while (QUAL.has(this.peek())) this.next();
      const type = this.next(), vars = [];
      do { const name = this.next(); let size = null; if (this.peek() === "[") { this.next(); size = this.expr(); this.eat("]"); } const init = this.peek() === "=" ? (this.next(), this.assign()) : null; vars.push({ name, init, size }); } while (this.peek() === "," && this.next());
      this.eat(";"); return { k: "decl", type, vars };
    }
    const e = this.expr(); this.eat(";"); return { k: "expr", e };
  }
  expr() { let e = this.assign(); while (this.peek() === ",") { this.next(); e = { k: "seq", a: e, b: this.assign() }; } return e; }
  assign() {
    const l = this.ternary(), op = this.peek();
    if (["=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="].includes(op)) { this.next(); return { k: "assign", op, l, r: this.assign() }; }
    return l;
  }
  ternary() { const c = this.bin(0); if (this.peek() === "?") { this.next(); const a = this.assign(); this.eat(":"); const b = this.assign(); return { k: "tern", c, a, b }; } return c; }
  bin(level) {
    const L = [["||"], ["^^"], ["&&"], ["|"], ["^"], ["&"], ["==", "!="], ["<", ">", "<=", ">="], ["<<", ">>"], ["+", "-"], ["*", "/", "%"]];
    if (level >= L.length) return this.unary();
    let a = this.bin(level + 1);
    while (L[level].includes(this.peek())) { const op = this.next(); a = { k: "bin", op, a, b: this.bin(level + 1) }; }
    return a;
  }
  unary() {
    const t = this.peek();
    if (t === "-" || t === "+" || t === "!" || t === "~") { this.next(); return { k: "un", op: t, a: this.unary() }; }
    if (t === "++" || t === "--") { this.next(); return { k: "pre", op: t, a: this.unary() }; }
    return this.postfix();
  }
  postfix() {
    let e = this.primary();
    for (;;) {
      const t = this.peek();
      if (t === "[") { this.next(); const i = this.expr(); this.eat("]"); e = { k: "idx", a: e, i }; }
      else if (t === ".") { this.next(); e = { k: "mem", a: e, n: this.next() }; }
      else if (t === "++" || t === "--") { this.next(); e = { k: "post", op: t, a: e }; }
      else return e;
    }
  }
  primary() {
    const t = this.next();
    if (t === "(") { const e = this.expr(); this.eat(")"); return e; }
    if (/^(0[xX]|\d|\.\d)/.test(t)) {
      if (/^0[xX]/.test(t)) return { k: "lit", v: new I(parseInt(t.replace(/[uU]$/, ""), 16), /[uU]$/.test(t)) };
      if (/[.eE]/.test(t.replace(/[fF]$/, "")) || /[fF]$/.test(t)) return { k: "lit", v: F(parseFloat(t)) };
      return { k: "lit", v: new I(parseInt(t), /[uU]$/.test(t)) };
    }
    if (t === "true" || t === "false") return { k: "lit", v: t === "true" };
    if (this.peek() === "(") { this.next(); const args = []; while (this.peek() !== ")") { args.push(this.assign()); if (this.peek() === ",") this.next(); } this.eat(")"); return { k: "call", n: t, args }; }
    return { k: "var", n: t };
  }
}

const SW = { x: 0, y: 1, z: 2, w: 3, r: 0, g: 1, b: 2, a: 3, s: 0, t: 1, p: 2, q: 3 };
function arith(op, a, b) {
  if (isVec(a) || isVec(b)) {
    if (a instanceof Mat || b instanceof Mat) throw new Error("mat arith");
    const n = isVec(a) ? a.length : b.length;
    return Array.from({ length: n }, (_, i) => arith(op, isVec(a) ? a[i] : a, isVec(b) ? b[i] : b));
  }
  if (a instanceof I && b instanceof I) {
    const u = a.u || b.u, x = a.v, y = b.v;
    switch (op) {
      case "+": return new I(x + y, u); case "-": return new I(x - y, u); case "*": return new I(Math.imul(x, y), u);
      case "/": return new I(u ? Math.trunc((x >>> 0) / (y >>> 0)) : Math.trunc(x / y), u); case "%": return new I(x % y, u);
      case "&": return new I(x & y, u); case "|": return new I(x | y, u); case "^": return new I(x ^ y, u);
      case "<<": return new I(x << (y & 31), u); case ">>": return new I(u ? x >>> (y & 31) : x >> (y & 31), u);
    }
  }
  const x = num(a), y = num(b);
  switch (op) { case "+": return F(x + y); case "-": return F(x - y); case "*": return F(x * y); case "/": return F(x / y); case "%": return F(x - y * Math.floor(x / y)); }
  throw new Error("op " + op);
}
function cmp(op, a, b) {
  const x = num(a), y = num(b);
  switch (op) { case "<": return x < y; case ">": return x > y; case "<=": return x <= y; case ">=": return x >= y; case "==": return x === y; case "!=": return x !== y; }
}
const map1 = (a, fn) => isVec(a) ? a.map(v => fn(num(v))) : fn(num(a));
const map2 = (a, b, fn) => (isVec(a) || isVec(b)) ? Array.from({ length: (isVec(a) ? a : b).length }, (_, i) => fn(num(isVec(a) ? a[i] : a), num(isVec(b) ? b[i] : b))) : fn(num(a), num(b));
const map3 = (a, b, c, fn) => [a, b, c].some(isVec) ? Array.from({ length: [a, b, c].find(isVec).length }, (_, i) => fn(...[a, b, c].map(v => num(isVec(v) ? v[i] : v)))) : fn(num(a), num(b), num(c));
const dot = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s = F(s + F(num(a[i]) * num(b[i]))); return s; };
const roundEven = x => { const r = Math.round(x); return (Math.abs(x % 1) === 0.5 && r % 2 !== 0) ? r - 1 : r; };
function construct(n, args) {
  const flat = [];
  for (const a of args) { if (a instanceof Mat) flat.push(...a.m); else if (isVec(a)) flat.push(...a); else flat.push(a); }
  const size = { vec2: 2, vec3: 3, vec4: 4, ivec2: 2, ivec3: 3, ivec4: 4, uvec2: 2, uvec3: 3, uvec4: 4 }[n];
  const kind = n[0] === "i" ? "i" : n[0] === "u" ? "u" : "f";
  const conv = v => kind === "f" ? F(num(v)) : new I(Math.trunc(num(v)), kind === "u");
  if (flat.length === 1) return Array.from({ length: size }, () => conv(flat[0]));
  return flat.slice(0, size).map(conv);
}
const BUILTIN = {
  fma: (a, b, c) => map3(a, b, c, (x, y, z) => F(x * y + z)),
  clamp: (a, b, c) => map3(a, b, c, (x, lo, hi) => F(Math.min(Math.max(x, lo), hi))),
  max: (a, b) => (a instanceof I && b instanceof I) ? new I(Math.max(a.v, b.v), a.u) : map2(a, b, (x, y) => F(Math.max(x, y))),
  min: (a, b) => (a instanceof I && b instanceof I) ? new I(Math.min(a.v, b.v), a.u) : map2(a, b, (x, y) => F(Math.min(x, y))),
  sqrt: a => map1(a, x => F(Math.sqrt(x))), inversesqrt: a => map1(a, x => F(1 / Math.sqrt(x))),
  exp: a => map1(a, x => F(Math.exp(x))), exp2: a => map1(a, x => F(2 ** x)), log: a => map1(a, x => F(Math.log(x))), log2: a => map1(a, x => F(Math.log2(x))),
  pow: (a, b) => map2(a, b, (x, y) => F(x ** y)), sin: a => map1(a, x => F(Math.sin(x))), cos: a => map1(a, x => F(Math.cos(x))),
  abs: a => a instanceof I ? new I(Math.abs(a.v)) : map1(a, x => F(Math.abs(x))), sign: a => map1(a, Math.sign), floor: a => map1(a, Math.floor), ceil: a => map1(a, Math.ceil),
  fract: a => map1(a, x => F(x - Math.floor(x))), trunc: a => map1(a, Math.trunc), roundEven: a => map1(a, roundEven), round: a => map1(a, roundEven),
  mod: (a, b) => map2(a, b, (x, y) => F(x - y * Math.floor(x / y))), step: (e, x) => map2(e, x, (a, b) => b < a ? 0 : 1),
  mix: (a, b, t) => map3(a, b, t, (x, y, s) => F(x + F(F(y - x) * s))),
  dot: (a, b) => dot(a, b), length: a => F(Math.sqrt(dot(a, a))), distance: (a, b) => BUILTIN.length(arith("-", a, b)),
  normalize: a => { const l = F(Math.sqrt(dot(a, a))); return a.map(v => F(num(v) / l)); },
  cross: (a, b) => [F(a[1] * b[2] - a[2] * b[1]), F(a[2] * b[0] - a[0] * b[2]), F(a[0] * b[1] - a[1] * b[0])],
  reflect: (i, n) => { const d = F(2 * dot(n, i)); return i.map((v, k) => F(v - F(d * n[k]))); },
  float: a => isVec(a) ? F(num(a[0])) : F(a instanceof I && a.u ? a.v >>> 0 : num(a)),
  int: a => new I(Math.trunc(num(a))), uint: a => a instanceof I ? new I(a.v, true) : new I(Math.trunc(num(a)) >>> 0, true), bool: a => !!num(a),
  floatBitsToInt: a => new I(a instanceof Bits ? a.bits | 0 : (f32[0] = num(a), i32[0])), floatBitsToUint: a => new I(a instanceof Bits ? a.bits : fToBits(num(a)), true),
  intBitsToFloat: a => bitsToF(num(a)), uintBitsToFloat: a => bitsToF(num(a)),
  any: a => a.some(Boolean), all: a => a.every(Boolean), isnan: a => map1(a, Number.isNaN),
  lessThan: (a, b) => a.map((v, i) => num(v) < num(b[i])), greaterThan: (a, b) => a.map((v, i) => num(v) > num(b[i])),
  inverseTransformDirection: (dir, m) => BUILTIN.normalize(mulVecMat([...dir, 0], m).slice(0, 3)),
};
for (const n of ["vec2", "vec3", "vec4", "ivec2", "ivec3", "ivec4", "uvec2", "uvec3", "uvec4"]) BUILTIN[n] = (...a) => construct(n, a);
function mulMatVec(m, v) { const n = m.n; return Array.from({ length: n }, (_, r) => { let s = 0; for (let c = 0; c < n; c++) s = F(s + F(m.m[c * n + r] * num(v[c]))); return s; }); }
function mulVecMat(v, m) { const n = m.n; return Array.from({ length: n }, (_, c) => { let s = 0; for (let r = 0; r < n; r++) s = F(s + F(num(v[r]) * m.m[c * n + r])); return s; }); }
class Ret { constructor(v) { this.v = v; } }
const BRK = Symbol("break"), CNT = Symbol("continue");
const ZERO = { float: 0, int: new I(0), uint: new I(0, true), bool: false, vec2: [0, 0], vec3: [0, 0, 0], vec4: [0, 0, 0, 0], ivec2: [new I(0), new I(0)] };

export class Program {
  constructor(src) {
    this.funcs = new Map(); this.main = null;
    const t = tokenize(src); let i = 0;
    while (i < t.length) {
      if (["uniform", "varying", "precision", "layout", "in", "out", "flat", "const", "struct", "attribute"].includes(t[i]) && !(TYPES.has(t[i + 1]) && t[i + 3] === "(")) {
        let depth = 0; while (i < t.length) { if (t[i] === "{") depth++; else if (t[i] === "}") depth--; else if (t[i] === ";" && depth === 0) break; i++; } i++; continue;
      }
      if (t[i] === ";") { i++; continue; }
      if (TYPES.has(t[i]) && t[i + 2] === "(") {
        const name = t[i + 1]; let j = i + 3; const params = []; let cur = [];
        while (t[j] !== ")") { if (t[j] === ",") { params.push(cur); cur = []; } else cur.push(t[j]); j++; }
        if (cur.length) params.push(cur);
        j++;
        if (t[j] === ";") { i = j + 1; continue; }
        const start = j; let depth = 0;
        do { if (t[j] === "{") depth++; else if (t[j] === "}") depth--; j++; } while (depth > 0);
        this.funcs.set(name, { params: params.filter(p => !(p.length === 1 && p[0] === "void")).map(p => p[p.length - 1]), toks: t.slice(start, j), body: null });
        i = j; continue;
      }
      throw new Error("top-level near " + t.slice(i, i + 10).join(" "));
    }
  }
  run(globals, natives = {}, entry = "main", args = []) {
    this.g = globals; this.natives = natives;
    return this.call(entry, args);
  }
  call(name, args) {
    if (this.natives[name]) return this.natives[name](...args);
    const f = this.funcs.get(name);
    if (!f) { if (BUILTIN[name]) return BUILTIN[name](...args); throw new Error("no function " + name); }
    if (!f.body) f.body = new Parser(f.toks).block();
    const scope = [new Map(f.params.map((p, k) => [p, args[k]]))];
    const r = this.exec(f.body, scope);
    return r instanceof Ret ? r.v : undefined;
  }
  lookup(n, scope) {
    for (let k = scope.length - 1; k >= 0; k--) if (scope[k].has(n)) return { m: scope[k] };
    if (n in this.g) return { m: null };
    throw new Error("undefined " + n);
  }
  get(n, scope) { const r = this.lookup(n, scope); return r.m ? r.m.get(n) : this.g[n]; }
  setVar(n, v, scope) { const r = this.lookup(n, scope); if (r.m) r.m.set(n, v); else this.g[n] = v; }
  exec(s, scope) {
    switch (s.k) {
      case "block": { scope.push(new Map()); try { for (const x of s.b) { const r = this.exec(x, scope); if (r !== undefined) return r; } } finally { scope.pop(); } return; }
      case "decl": for (const v of s.vars) scope[scope.length - 1].set(v.name, v.init ? this.conv(s.type, this.ev(v.init, scope)) : structuredCloneVal(ZERO[s.type] ?? 0)); return;
      case "expr": this.ev(s.e, scope); return;
      case "if": { const r = num(this.ev(s.c, scope)) ? this.exec(s.a, scope) : s.e ? this.exec(s.e, scope) : undefined; return r; }
      case "for": { scope.push(new Map()); try { if (s.init) this.exec(s.init, scope); for (let n = 0; ; n++) { if (n > 1e6) throw new Error("loop"); if (s.c && !num(this.ev(s.c, scope))) break; const r = this.exec(s.body, scope); if (r === BRK) break; if (r instanceof Ret) return r; if (s.inc) this.ev(s.inc, scope); } } finally { scope.pop(); } return; }
      case "while": for (;;) { if (!num(this.ev(s.c, scope))) break; const r = this.exec(s.body, scope); if (r === BRK) break; if (r instanceof Ret) return r; } return;
      case "do": for (;;) { const r = this.exec(s.body, scope); if (r === BRK) break; if (r instanceof Ret) return r; if (!num(this.ev(s.c, scope))) break; } return;
      case "break": return BRK; case "continue": return CNT; case "discard": return new Ret("discard");
      case "return": return new Ret(s.e ? this.ev(s.e, scope) : undefined);
    }
    throw new Error("stmt " + s.k);
  }
  conv(type, v) {
    if (type === "float") return isVec(v) ? F(num(v[0])) : F(v instanceof I && v.u ? v.v >>> 0 : num(v));
    if (type === "int") return v instanceof I ? new I(v.v) : new I(Math.trunc(num(v)));
    if (type === "uint") return v instanceof I ? new I(v.v, true) : new I(Math.trunc(num(v)), true);
    return v;
  }
  ref(e, scope) {
    if (e.k === "var") return { get: () => this.get(e.n, scope), set: v => this.setVar(e.n, v, scope) };
    if (e.k === "mem") {
      const base = this.ref(e.a, scope), cur = base.get();
      if (isVec(cur)) {
        const idx = [...e.n].map(c => SW[c]);
        return { get: () => { const c = base.get(); return idx.length === 1 ? c[idx[0]] : idx.map(i => c[i]); },
          set: v => { const c = base.get().slice(); idx.forEach((i, k) => { c[i] = idx.length === 1 ? v : v[k]; }); base.set(c); } };
      }
      return { get: () => base.get()[e.n], set: v => { base.get()[e.n] = v; } };
    }
    if (e.k === "idx") {
      const base = this.ref(e.a, scope), i = num(this.ev(e.i, scope));
      return { get: () => base.get()[i], set: v => { const c = base.get(); if (Array.isArray(c) && typeof c[0] !== "object") { const d = c.slice(); d[i] = v; base.set(d); } else c[i] = v; } };
    }
    throw new Error("lvalue " + e.k);
  }
  ev(e, scope) {
    switch (e.k) {
      case "lit": return e.v;
      case "var": return this.get(e.n, scope);
      case "seq": this.ev(e.a, scope); return this.ev(e.b, scope);
      case "tern": return num(this.ev(e.c, scope)) ? this.ev(e.a, scope) : this.ev(e.b, scope);
      case "assign": {
        const r = this.ref(e.l, scope); let v = this.ev(e.r, scope);
        if (e.op !== "=") v = this.binop(e.op.slice(0, -1), r.get(), v);
        const old = r.get();
        if (old instanceof I && !(v instanceof I)) v = new I(Math.trunc(num(v)), old.u);
        else if (typeof old === "number" && v instanceof I) v = F(v.u ? v.v >>> 0 : v.v);
        r.set(v); return v;
      }
      case "pre": case "post": { const r = this.ref(e.a, scope), o = r.get(), n = this.binop(e.op[0], o, o instanceof I ? new I(1) : 1); r.set(n); return e.k === "pre" ? n : o; }
      case "un": { const a = this.ev(e.a, scope); if (e.op === "-") return a instanceof I ? new I(-a.v, a.u) : map1(a, x => F(-x)); if (e.op === "!") return !num(a); if (e.op === "~") return new I(~a.v, a.u); return a; }
      case "bin": {
        if (e.op === "&&") return !!num(this.ev(e.a, scope)) && !!num(this.ev(e.b, scope));
        if (e.op === "||") return !!num(this.ev(e.a, scope)) || !!num(this.ev(e.b, scope));
        return this.binop(e.op, this.ev(e.a, scope), this.ev(e.b, scope));
      }
      case "idx": { const a = this.ev(e.a, scope), i = num(this.ev(e.i, scope)); if (a instanceof Mat) return a.m.slice(i * a.n, i * a.n + a.n); return a[i]; }
      case "mem": { const a = this.ev(e.a, scope); if (isVec(a)) { const idx = [...e.n].map(c => SW[c]); return idx.length === 1 ? a[idx[0]] : idx.map(i => a[i]); } return a[e.n]; }
      case "call": {
        const args = e.args.map(a => this.ev(a, scope));
        if (["texture", "texture2D", "textureLod", "texelFetch", "textureGrad"].includes(e.n)) { const s = args[0]; if (typeof s !== "function") throw new Error("sampler not mocked in " + e.n); return s(...args.slice(1)); }
        return this.call(e.n, args);
      }
    }
    throw new Error("expr " + e.k);
  }
  binop(op, a, b) {
    if (["<", ">", "<=", ">=", "==", "!="].includes(op)) return cmp(op, a, b);
    if (op === "^^") return !!num(a) !== !!num(b);
    if (op === "*" && (a instanceof Mat || b instanceof Mat)) return a instanceof Mat ? mulMatVec(a, b) : mulVecMat(a, b);
    return arith(op, a, b);
  }
}
function structuredCloneVal(v) { return isVec(v) ? v.slice() : v; }
export { F, bitsToF, fToBits };
