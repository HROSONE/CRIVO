"use strict";
/* Contrato de seleção, NÃO um sintetizador. Não faz fetch nem envia texto. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.CrivoOfflineTts = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function isLocalAssetUrl(url) {
    return typeof url === "string" &&
      (/^\/(?!\/)[\w./%-]+$/.test(url) || /^\.\/(?!\/)[\w./%-]+$/.test(url)) &&
      !url.split("/").includes("..");
  }
  function selectOfflineTts(options) {
    const candidates = (options && options.available || []).filter(function (voice) {
      return voice && ["piper", "kokoro"].includes(voice.id) &&
        voice.local === true && voice.cached === true &&
        voice.language === "pt-BR";
    });
    const kokoro = candidates.find(function (voice) {
      return voice.id === "kokoro" && options.webgpu === true && voice.supportsWebGPU === true;
    });
    return kokoro || candidates.find(function (voice) { return voice.id === "piper"; }) ||
      candidates.find(function (voice) { return voice.id === "kokoro"; }) || null;
  }
  function splitSpeechText(text, maxLength) {
    const clean = String(text || "").trim().replace(/\s+/g, " ");
    if (!clean) return [];
    const limit = Math.max(16, Number(maxLength) || 180);
    const sentences = clean.match(/[^.!?]+[.!?]*|[.!?]+/g) || [];
    const chunks = [];
    sentences.forEach(function (part) {
      const sentence = part.trim();
      if (!sentence) return;
      if (sentence.length <= limit) { chunks.push(sentence); return; }
      let buffer = "";
      sentence.split(/\s+/).forEach(function (word) {
        if (buffer && (buffer.length + word.length + 1 > limit)) {
          chunks.push(buffer);
          buffer = word;
        } else buffer = buffer ? buffer + " " + word : word;
      });
      if (buffer) chunks.push(buffer);
    });
    return chunks;
  }
  return { isLocalAssetUrl, selectOfflineTts, splitSpeechText };
}));
