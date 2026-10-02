// node web/tools/graphics_verify/teamcolor_ink_test.mjs [RowName]
// Ink(9)/InkBright(10) 재구현 계산: 조명 입력 t 에 대한 민감도 표 + 스테이지 MainLight 를 DirectionalLight 로 가정한 예.
// 입력 t = Intensity * L*(DiffuseColor)/100 + L*(skyUp)/100 (0x7101174afc). 흰색(1,1,1)의 L* = 100 이므로
// light = { color:[1,1,1], intensity:t, skyUp:null } 로 t 를 직접 넣을 수 있다. [재구현 계산, 원본 실행 대조 없음]
import fs from 'node:fs';
import { buildTeamSets, inkCorrection, INK_CORR_MAIN } from './teamcolor.mjs';

const rows = JSON.parse(fs.readFileSync('C:/dev/splatoon3/analysis/graphics/rsdb/TeamColorDataSet.json', 'utf8'));
const want = process.argv[2] || 'OrangeBlue';
const row = rows.find((r) => r.__RowId.includes('/' + want + '.'));
const f = (c) => c.slice(0, 3).map((x) => x.toFixed(4)).join(', ');
const sets = buildTeamSets(row, false);
const P = INK_CORR_MAIN;
const rOf = (t) => Math.min(Math.max((P.rate1 * 6 - P.rate6) / 5 + ((P.rate6 - P.rate1) / 5) * t, 0), P.rate6);
const out = { row: row.__RowId, sweep: [] };
for (const t of [0, 1, 3, 5.5714, 6, 10]) {
  const light = { color: [1, 1, 1], intensity: t, skyUp: null };
  const line = { t, r: rOf(t), sets: sets.map((s) => ({ Ink: inkCorrection(s.linear, light, false), InkBright: inkCorrection(s.linear, light, true) })) };
  out.sweep.push(line);
  console.log(`t=${t} r=${line.r.toFixed(4)}  set0 Ink ${f(line.sets[0].Ink)} | InkBright ${f(line.sets[0].InkBright)}  set1 Ink ${f(line.sets[1].Ink)} | InkBright ${f(line.sets[1].InkBright)}`);
}
// [추정 입력] Vss_Yagara RenderingDay Lighting.MainLight Color(0.90196,0.82745,0.61569) Intens 6 를 DirectionalLight 로 본 경우 (skyUp 미상 → 0)
const yag = { color: [0.9019607901573181, 0.8274509906768799, 0.615686297416687], intensity: 6, skyUp: null };
const lab = (c) => { const Y = c[0] * 0.2126 + c[1] * 0.7152 + c[2] * 0.0722; return (Y >= 0.008856452 ? Math.cbrt(Y) : Y * 7.7870374 + 0.13793103) * 116 - 16; };
out.yagaraDayAssumed = { t: 6 * lab(yag.color) / 100, sets: sets.map((s) => ({ Ink: inkCorrection(s.linear, yag, false), InkBright: inkCorrection(s.linear, yag, true) })) };
console.log('Yagara Day (가정) t =', out.yagaraDayAssumed.t.toFixed(4), 'set0 Ink', f(out.yagaraDayAssumed.sets[0].Ink), 'InkBright', f(out.yagaraDayAssumed.sets[0].InkBright));
fs.mkdirSync('C:/dev/splatoon3/analysis/render', { recursive: true });
fs.writeFileSync(`C:/dev/splatoon3/analysis/render/teamcolor_ink_${want}.json`, JSON.stringify(out, null, 1));
