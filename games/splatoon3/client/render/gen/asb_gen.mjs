// ASB(v0x410) → render 용 JSON. 근거: docs/graphics/anim_state_machine.md §2 (헤더·커맨드·노드·자식 목록·값 슬롯·부착 목록).
// 사용: node games/splatoon3/client/render/gen/asb_gen.mjs <SplPlayer.root.asb> <SplPlayerSquid.root.asb> <출력.json>
// 원본 파일: C:/dev/splatoon3/extracted/actor/SplPlayer/AS/*.asb (SplPlayer.pack.zs 안 AS/)
import fs from "node:fs";

function parse(path) {
  const d = fs.readFileSync(path);
  const u = (o) => d.readUInt32LE(o);
  const f = (o) => d.readFloatLE(o);
  if (d.toString("latin1", 0, 4) !== "ASB ") throw new Error("ASB 아님 " + path);
  const H = [];
  for (let i = 0; i < 26; i++) H.push(u(i * 4));
  const [, ver, , ncmd, nnode, , , nrec, bbHdr, sp] = H;
  if (ver !== 0x410) throw new Error("버전 " + ver.toString(16));
  const str = (o) => {
    let e = sp + o;
    while (d[e]) e++;
    return d.toString("utf8", sp + o, e);
  };
  // 블랙보드 헤더: 타입 6개 × (u16 개수, u16 시작 순번, u32) — 이름 오프셋 표가 뒤따름 [판독 §2.6]
  const bbTypes = ["string", "int", "float", "bool", "t4", "t5"];
  const bbCount = bbTypes.map((_, i) => d.readUInt16LE(bbHdr + i * 8));
  const total = bbCount.reduce((a, b) => a + b, 0);
  const names = [];
  for (let i = 0; i < total; i++) names.push(str(u(bbHdr + 48 + i * 4)));
  const bb = {};
  let k = 0;
  bbTypes.forEach((t, i) => {
    bb[t] = names.slice(k, k + bbCount[i]);
    k += bbCount[i];
  });
  // 값 슬롯 [tag][const] (§2.7)
  const slot = (o, kind) => {
    const tag = u(o);
    const hi = tag >>> 28;
    if (tag === 0) {
      if (kind === "string") return { c: str(u(o + 4)) };
      if (kind === "float") return { c: f(o + 4) };
      return { c: u(o + 4) | 0 };
    }
    if (hi === 0x8 || hi === 0xa) return { bb: tag & 0x0fffffff, k: kind };
    if (hi === 0xd || hi === 0xe) return { fp: tag & 0x0fffffff };
    return { raw: [tag, u(o + 4)] };
  };
  const commands = {};
  for (let i = 0; i < ncmd; i++) {
    const o = 0x68 + i * 0x2c;
    commands[str(u(o))] = u(o + 0x28);
  }
  const nodeBase = 0x68 + ncmd * 0x2c;
  const recTbl = H[14], idxTbl = H[15];
  // 자식 목록 (n|n<<24, n<<8|n<<24, 오프셋×n) — §2.4
  const childList = (body, maxWords) => {
    for (let w = 0; w < maxWords; w++) {
      const a = u(body + w * 4);
      const n = a & 0xff;
      if (n && a === ((n | (n << 24)) >>> 0) && u(body + w * 4 + 4) === (((n << 8) | (n << 24)) >>> 0)) {
        const offs = [];
        for (let j = 0; j < n; j++) offs.push(u(body + w * 4 + 8 + j * 4));
        return offs;
      }
    }
    return [];
  };
  const attach = (o) => {
    const w = u(o);
    if (!w) return undefined;
    const ev = w & 0xff, ctrl = (w >>> 16) & 0xff;
    const n = ev + ctrl;
    const list = [];
    for (let j = 0; j < n; j++) list.push(u(u(o + 4 + j * 4)));
    return { events: list.slice(0, ev), ctrls: list.slice(ev) };
  };
  const nodes = [];
  for (let i = 0; i < nnode; i++) {
    const o = nodeBase + i * 0x24;
    const t = d.readUInt16LE(o), flag = d.readUInt16LE(o + 2), body = u(o + 8), recStart = d.readUInt16LE(o + 0x10);
    const n = { t };
    // 노드 파라미터 레코드(§2.3): 개수 = 플래그 하위 바이트, 표 +0x3c 의 u16 이 레코드 번호
    const nr = flag & 0xff;
    if (nr) {
      n.rec = [];
      for (let r = 0; r < nr; r++) {
        const ri = d.readUInt16LE(idxTbl + (recStart + r) * 2);
        if (ri >= nrec) continue;
        const ro = recTbl + ri * 0x18;
        n.rec.push({ type: u(ro), v: slot(u(ro + 4), "float") });
      }
    }
    if (t === 3 || t === 11 || t === 18) {
      n.clip = slot(body, "string");
      const at = attach(body + (t === 11 ? 6 : 10) * 4);
      if (at) n.attach = at;
    } else if (t === 2) {
      n.v = slot(body, "string");
      n.cases = childList(body, 16).map((e) => [str(u(e + 4)), u(e + 8)]);
    } else if (t === 21) {
      n.v = slot(body, "bool");
      n.kids = childList(body, 16).map((e) => u(e));
    } else if (t === 8) {
      n.v = slot(body, "int");
      n.cases = childList(body, 16).map((e) => [u(e + 4) | 0, u(e + 8)]);
    } else if (t === 6) {
      n.v = slot(body, "float");
      n.smooth = u(body + 8) === 1;
      n.kids = childList(body, 16).map((e) => [f(e + 4), f(e + 12), u(e + 16)]);
    } else if (t === 9 || t === 7) {
      n.kids = childList(body, 16).map((e) => u(e));
    } else if (t === 12) {
      // FrameController (§4.3): +0 rate, +8 start, +0x10 end, +0x18 mode
      n.rate = slot(body, "float");
      n.start = slot(body + 8, "float");
      n.end = slot(body + 0x10, "float");
      n.mode = u(body + 0x18);
    } else if (t === 10) {
      n.event = u(body);
    } else if (t === 19) {
      n.mode = u(body);
    }
    nodes.push(n);
  }
  const floatParams = [];
  for (let i = 0; i < H[17]; i++) {
    const o = H[18] + i * 0x20;
    floatParams.push({ bb: u(o), rate: f(o + 4), mode: u(o + 8), init: f(o + 12), scale: f(o + 16), offset: f(o + 20), min: f(o + 24), max: f(o + 28) });
  }
  return { commands, nodes, floatParams, bb };
}

const [h, s, out] = process.argv.slice(2);
if (!out) {
  console.log("node asb_gen.mjs <SplPlayer.root.asb> <SplPlayerSquid.root.asb> <out.json>");
  process.exit(1);
}
fs.writeFileSync(out, JSON.stringify({ source: "SplPlayer.pack AS/*.root.asb (gen/asb_gen.mjs)", human: parse(h), squid: parse(s) }));
console.log("ok", out, fs.statSync(out).size);
