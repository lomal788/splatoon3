// node web/tools/graphics_verify/teamcolor_test.mjs [RowName] : prints the 4 team sets (14 colors each) and material params.
import fs from 'node:fs';
import { buildTeamSets, materialTeamParams, TYPE_NAMES, hsvOffset, rgbToHsv } from './teamcolor.mjs';
const rows = JSON.parse(fs.readFileSync('C:/dev/splatoon3/analysis/graphics/rsdb/TeamColorDataSet.json', 'utf8'));
const want = process.argv[2] || 'OrangeBlue';
const row = rows.find((r) => r.__RowId.includes('/' + want + '.'));
const f = (c) => (c ? c.slice(0, 4).map((x) => x.toFixed(4)).join(' ') : '(unresolved)');
const sets = buildTeamSets(row, false);
const out = { row: row.__RowId, tag: row.Tag, sets: [] };
sets.forEach((s, i) => {
  console.log(`set${i} raw ${f(s.raw)}  linear ${f(s.linear)}`);
  TYPE_NAMES.forEach((n, k) => console.log(`   ${String(k).padStart(2)} ${n.padEnd(14)} ${f(s.colors[k])}`));
  const mp = materialTeamParams(s, {});
  out.sets.push({ raw: s.raw, linear: s.linear, colors: Object.fromEntries(TYPE_NAMES.map((n, k) => [n, s.colors[k]])), material: mp });
});
// boundary checks
const checks = {
  grayHueBright: hsvOffset(0.1, 0, 0.05, [0.5, 0.5, 0.5, 0.7]),       // s == 0 path: alpha forced 1, no clamp
  brightOver1Gray: hsvOffset(0, 0, 0.5, [0.8, 0.8, 0.8, 1]),          // v' = 1.3 stays unclamped (s == 0)
  redHueDark: hsvOffset(-0.1, 0, 0.05, [0.8, 0.1, 0.1, 1]),           // negative hue -> trunc 0, f < 0 path
  greenFlip: { hsv: rgbToHsv(0.1, 0.8, 0.1), out: hsvOffset(0.1, 0, 0, [0.1, 0.8, 0.1, 1]) }, // h = 1/3 in (0.2,0.72): offset flipped
};
for (const [k, v] of Object.entries(checks)) console.log(k, JSON.stringify(v));
out.checks = checks;
fs.mkdirSync('C:/dev/splatoon3/analysis/graphics/teamcolor', { recursive: true });
fs.writeFileSync(`C:/dev/splatoon3/analysis/graphics/teamcolor/${want}.json`, JSON.stringify(out, null, 1));
