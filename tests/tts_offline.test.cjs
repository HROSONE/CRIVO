"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { selectOfflineTts, splitSpeechText, isLocalAssetUrl } = require("../public/tts/offline-core.js");

test("nunca seleciona voz que exige API ou download em tempo de fala", () => {
  const result = selectOfflineTts({ online: false, webgpu: false, available: [
    { id: "kokoro", cached: false, local: false, language: "pt-BR" },
    { id: "piper", cached: true, local: true, language: "pt-BR" }
  ] });
  assert.equal(result.id, "piper");
});
test("prefere Kokoro local quando disponivel e compativel", () => {
  assert.equal(selectOfflineTts({ online: false, webgpu: true, available: [
    { id: "piper", cached: true, local: true, language: "pt-BR" },
    { id: "kokoro", cached: true, local: true, language: "pt-BR", supportsWebGPU: true }
  ] }).id, "kokoro");
});
test("nao inventa suporte a portugues, nem voz offline", () => {
  assert.equal(selectOfflineTts({ online: false, available: [
    { id: "kokoro", cached: true, local: true, language: "en-US" }
  ] }), null);
  assert.equal(selectOfflineTts({ online: false, available: [] }), null);
});
test("recusa URL remota de pesos e scripts, inclusive protocolo relativo", () => {
  for (const url of ["https://example.com/model.onnx", "//example.com/model.onnx", "data:text/plain,x", "javascript:alert(1)"]) {
    assert.equal(isLocalAssetUrl(url), false);
  }
  for (const url of ["/tts/models/piper.onnx", "./models/voz.bin"]) {
    assert.equal(isLocalAssetUrl(url), true);
  }
});
test("segmenta texto sem destruir acentos, pontuacao e palavras", () => {
  const input = "Olá, Henrique! A Lua não é uma estrela. Ela orbita a Terra?";
  assert.deepEqual(splitSpeechText(input, 40), [
    "Olá, Henrique!", "A Lua não é uma estrela.", "Ela orbita a Terra?"
  ]);
});
test("limites pequenos e texto vazio nao causam loop", () => {
  assert.deepEqual(splitSpeechText(" ", 40), []);
  assert.deepEqual(splitSpeechText("anticonstitucionalissimamente", 5), ["anticonstitucionalissimamente"]);
});
