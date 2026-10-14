// Renderiza alguns quadros de uma composição para revisão (um bundle só).
// Uso: node scripts/quadros.mjs <composição> <saída> <q1,q2,...> [navegador]
import path from "path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const [id, saida, lista, navegador] = process.argv.slice(2);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const opcoes = { serveUrl, browserExecutable: navegador, chromiumOptions: { gl: "swiftshader" } };
const composition = await selectComposition({ ...opcoes, id });
for (const q of lista.split(",").map(Number)) {
  await renderStill({ ...opcoes, composition, frame: q, scale: 0.5, output: path.join(saida, `q${String(q).padStart(4, "0")}.png`) });
  process.stdout.write(`${q} `);
}
console.log();
