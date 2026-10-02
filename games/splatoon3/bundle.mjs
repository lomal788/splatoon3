import path from "node:path";
import { fileURLToPath } from "node:url";
import * as esbuild from "esbuild";

const root = path.dirname(fileURLToPath(import.meta.url));
export const SPLATOON3 = "/game/splatoon3/";
export const SPLATOON3_BUNDLE = ["app.js", "app.css"];

const options = (dev) => ({
  entryPoints: { app: path.join(root, "../../scripts/app/games/splatoon3/main.ts") },
  outdir: root,
  tsconfig: path.join(root, "tsconfig.json"),
  write: false,
  bundle: true,
  format: "esm",
  target: "es2022",
  charset: "utf8",
  minify: !dev,
  sourcemap: dev ? "inline" : false,
  legalComments: "none",
  logLevel: "silent",
  define: { __DEV__: JSON.stringify(dev), __GAME_BASE__: JSON.stringify(SPLATOON3) },
});

const files = (result) =>
  Object.fromEntries(result.outputFiles.map((f) => [path.basename(f.path), f.contents]));

export async function bundleSplatoon3() {
  return files(await esbuild.build(options(false)));
}

export function splatoon3Dev() {
  let context = null,
    pending = null;
  return () =>
    (pending ??= (context ??= esbuild.context(options(true)))
      .then((c) => c.rebuild())
      .then(files)
      .finally(() => {
        pending = null;
      }));
}
