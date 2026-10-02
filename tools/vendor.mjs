// three 의 basis(KTX2) 트랜스코더와 meshopt 디코더는 런타임에 별도 파일로 받는다.
// 포털 이식 시에도 경로가 같도록 게임 에셋 폴더(assets/common/lib/)에 복사해 둔다.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const web = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const three = path.join(web, "node_modules/three/examples/jsm/libs");
const out = path.join(web, "games/splatoon3/assets/common/lib");

export function vendor() {
  const jobs = [
    ["basis/basis_transcoder.js", "basis/basis_transcoder.js"],
    ["basis/basis_transcoder.wasm", "basis/basis_transcoder.wasm"],
  ];
  for (const [from, to] of jobs) {
    const src = path.join(three, from);
    const dst = path.join(out, to);
    if (!fs.existsSync(src)) throw new Error(`없음: ${src} (npm install 먼저)`);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    if (!fs.existsSync(dst) || fs.statSync(dst).size !== fs.statSync(src).size) fs.copyFileSync(src, dst);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  vendor();
  console.log("vendor ->", out);
}
