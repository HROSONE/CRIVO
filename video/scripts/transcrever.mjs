// Transcreve a narração com Whisper.cpp (autorizado pelo criador só para este
// vídeo; fica fora do CRIVO). Uso: node scripts/transcrever.mjs <pasta-whisper> <wav-16k>
import fs from "fs";
import path from "path";
import {
  downloadWhisperModel,
  installWhisperCpp,
  toCaptions,
  transcribe,
} from "@remotion/install-whisper-cpp";

const [pasta, entrada] = process.argv.slice(2);
const versao = "1.5.5";
const modelo = "medium";

await installWhisperCpp({ to: pasta, version: versao });
// Se o Node não alcançar huggingface.co (proxy), baixe antes com curl:
// curl -L -o <pasta>/ggml-medium.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
if (!fs.existsSync(path.join(pasta, `ggml-${modelo}.bin`))) {
  await downloadWhisperModel({ model: modelo, folder: pasta });
}

const saida = await transcribe({
  model: modelo,
  whisperPath: pasta,
  whisperCppVersion: versao,
  inputPath: entrada,
  tokenLevelTimestamps: true,
  language: "pt",
});

const { captions } = toCaptions({ whisperCppOutput: saida });
const destino = path.join(process.cwd(), "public", "voz", "legendas.json");
fs.writeFileSync(destino, JSON.stringify(captions, null, 2));
console.log("legendas gravadas em", destino, captions.length, "palavras");
