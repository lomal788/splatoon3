// 상태 표 0x7105630270 → render 용 JSON. 근거: docs/player/player_state.md §4·부록(생성 원본 web/tools/state_table.py --md).
// 사용: node games/splatoon3/client/render/gen/state_table_gen.mjs <player_state.md> <출력.json>
// 출력: { "<번호>": [커맨드, 모델(0 사람 / 1 오징어), 블렌드 프레임, 플래그] }
import fs from "node:fs";

const [src, out] = process.argv.slice(2);
if (!out) {
  console.log("node state_table_gen.mjs <player_state.md> <out.json>");
  process.exit(1);
}
const md = fs.readFileSync(src, "utf8");
const at = md.indexOf("## 부록: 상태 번호 표");
const rows = {};
for (const line of md.slice(at).split("\n")) {
  const m = /^\|\s*(0x[0-9a-f]+)\s*\|\s*([^|]*?)\s*\|\s*(사람|오징어)?\s*\|\s*(-?\d+)?\s*\|\s*(0x[0-9a-f]+)\s*\|/.exec(line);
  if (!m) continue;
  rows[parseInt(m[1], 16)] = [m[2], m[3] === "오징어" ? 1 : 0, m[4] === undefined ? 0 : +m[4], parseInt(m[5], 16)];
}
fs.writeFileSync(out, JSON.stringify({ source: "docs/player/player_state.md 부록 (gen/state_table_gen.mjs)", rows }));
console.log("ok", Object.keys(rows).length);
