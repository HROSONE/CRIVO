import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Fontes locais (public/fontes), sem depender da rede na renderização.
export const titulo = "Space Grotesk";
export const mono = "JetBrains Mono";

for (const [familia, arquivo, peso] of [
  [titulo, "SpaceGrotesk-500", "500"],
  [titulo, "SpaceGrotesk-700", "700"],
  [mono, "JetBrainsMono-400", "400"],
  [mono, "JetBrainsMono-700", "700"],
]) {
  loadFont({ family: familia, url: staticFile(`fontes/${arquivo}.woff2`), weight: peso });
}

export const cor = {
  fundo: "#07080c",
  painel: "#10131b",
  borda: "#232838",
  texto: "#f2f4f8",
  apagado: "#8a93a8",
  lima: "#c6ff3d",
  ciano: "#3de0ff",
  vermelho: "#ff3b5c",
  ambar: "#ffb02e",
};

export const FPS = 30;

// Duração de cada cena, em quadros (múltiplos de 15 = um tempo a 120 BPM).
export const CENAS = {
  gancho: 120,
  rea: 330,
  binario: 240,
  clones: 390,
  mas: 240,
  modelos: 270,
  crivo: 420,
  final: 180,
} as const;

export const TOTAL = Object.values(CENAS).reduce((a, b) => a + b, 0);
