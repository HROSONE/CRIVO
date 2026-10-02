"use strict";

(function () {
  const ui = {
    status: document.getElementById("status"),
    statusText: document.getElementById("status-text"),
    chat: document.getElementById("conversation"),
    welcome: document.getElementById("welcome"),
    messages: document.getElementById("messages"),
    composer: document.getElementById("composer"),
    question: document.getElementById("question"),
    send: document.getElementById("send-button"),
    clear: document.getElementById("clear-button"),
    info: document.getElementById("info-button"),
    dialog: document.getElementById("about-dialog")
  };
  const state = { history: [], busy: false, controller: null, generation: 0, experimental: false,
    remember: false, memory: null };
  const KEY_REMEMBER = "crivo_lembrar";
  const KEY_MEMORY = "crivo_memoria";
  const KEY_FEEDBACK = "crivo_avaliacoes";

  // Armazenamento local: pode estar bloqueado (aba privada, política do navegador).
  function lerLocal(chave, padrao) {
    try {
      const bruto = window.localStorage.getItem(chave);
      return bruto === null ? padrao : JSON.parse(bruto);
    } catch (_err) { return padrao; }
  }
  function gravarLocal(chave, valor) {
    try { window.localStorage.setItem(chave, JSON.stringify(valor)); } catch (_err) { /* sem armazenamento */ }
  }
  function apagarLocal(chave) {
    try { window.localStorage.removeItem(chave); } catch (_err) { /* sem armazenamento */ }
  }
  state.remember = lerLocal(KEY_REMEMBER, false) === true;
  state.memory = state.remember ? lerLocal(KEY_MEMORY, {}) : null;

  function avaliacoes() {
    const lista = lerLocal(KEY_FEEDBACK, []);
    return Array.isArray(lista) ? lista : [];
  }
  function atualizarContagem() {
    const alvo = document.getElementById("feedback-count");
    if (alvo) alvo.textContent = String(avaliacoes().length);
  }
  function registrarAvaliacao(registro) {
    const lista = avaliacoes().filter(function (r) { return r.chave !== registro.chave; });
    lista.push(registro);
    gravarLocal(KEY_FEEDBACK, lista.slice(-500));
    atualizarContagem();
  }
  const API = "/api/chat";
  const MAX_HISTORY = 10;

  function setStatus(kind, label) {
    ui.status.className = "status status-" + kind;
    ui.statusText.textContent = label;
    ui.status.setAttribute("title", label);
  }

  function scrollToLatest() {
    ui.chat.scrollTop = ui.chat.scrollHeight;
  }

  function updateComposer() {
    ui.send.disabled = state.busy || !ui.question.value.trim();
    ui.question.style.height = "auto";
    ui.question.style.height = Math.min(ui.question.scrollHeight, 142) + "px";
  }

  async function checkHealth() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(function () { controller.abort(); }, 12000);
      try {
        const response = await fetch(API, {
          method: "GET", cache: "no-store", signal: controller.signal
        });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") throw new Error("Sem resposta");
        state.experimental = data.experimental_dialogue === true;
      } finally { clearTimeout(timeout); }
      setStatus("online", state.experimental ? "CRIVO experimental conectado" : "CRIVO conectado");
    } catch (_error) {
      setStatus("offline", "Servidor indisponível");
    }
  }

  async function copyText(value, button) {
    try {
      await navigator.clipboard.writeText(value);
      const old = button.textContent;
      button.textContent = "Copiado!";
      setTimeout(function () { button.textContent = old; }, 1600);
    } catch (_err) {
      button.textContent = "Não foi possível copiar";
    }
  }

  function addBlocks(container, text) {
    const fence = /(\x60{3}[\s\S]*?\x60{3})/g;
    const pieces = String(text).split(fence);
    pieces.forEach(function (piece) {
      if (!piece) return;
      if (/^\x60{3}/.test(piece)) {
        const match = piece.match(/^\x60{3}([^\n]*)\n?([\s\S]*?)\x60{3}$/);
        const language = match ? match[1].trim() : "";
        const codeText = match ? match[2].trimEnd() : piece;
        const pre = document.createElement("pre");
        if (language) {
          const label = document.createElement("span");
          label.className = "code-language";
          label.textContent = language;
          pre.appendChild(label);
        }
        const code = document.createElement("code");
        code.textContent = codeText;
        pre.appendChild(code);
        container.appendChild(pre);
      } else {
        piece.trim().split(/\n\n+/).forEach(function (para) {
          if (!para) return;
          const p = document.createElement("p");
          p.textContent = para;
          container.appendChild(p);
        });
      }
    });
  }

  function createMessage(role, text, extra) {
    if (!ui.welcome.hidden) ui.welcome.hidden = true;
    const outer = document.createElement("div");
    outer.className = "message " + role;
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "EU" : "◈";
    avatar.setAttribute("aria-hidden", "true");
    const main = document.createElement("div");
    main.className = "message-main";
    const name = document.createElement("div");
    name.className = "message-name";
    name.textContent = role === "user" ? "VOCÊ" : "CRIVO";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    addBlocks(bubble, text);
    main.appendChild(name);
    main.appendChild(bubble);
    if (role === "assistant" && extra) {
      const row = document.createElement("div");
      row.className = "message-extra";
      const tag = document.createElement("span");
      tag.className = "mechanism";
      if (extra.has_proof) {
        tag.classList.add("proof");
        tag.textContent = "◈ Prova lógica";
      } else if (extra.id === "fora" || extra.id === "duvida") {
        tag.textContent = "◇ Limite de conhecimento";
      } else if (extra.id && /^memoria:/.test(extra.id)) {
        tag.textContent = "◇ Do que você contou";
      } else if (extra.id && /^nocao:/.test(extra.id)) {
        tag.textContent = "◇ Conversa · noção";
      } else if (extra.id && /^(social|conversa|estudo):/.test(extra.id)) {
        tag.textContent = "◇ Conversa";
      } else {
        tag.textContent = "◇ Base de conhecimento";
      }
      tag.title = "Motor: " + (extra.mechanism || "recuperador");
      row.appendChild(tag);
      if (extra.question) {
        const chave = String(Date.now()) + "-" + Math.random().toString(36).slice(2, 8);
        [["👍", 1, "Boa resposta"], ["👎", -1, "Resposta ruim"]].forEach(function (opcao) {
          const botao = document.createElement("button");
          botao.type = "button";
          botao.className = "feedback-button";
          botao.textContent = opcao[0];
          botao.title = opcao[2];
          botao.setAttribute("aria-label", opcao[2]);
          botao.setAttribute("aria-pressed", "false");
          botao.addEventListener("click", function () {
            row.querySelectorAll(".feedback-button").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
            botao.setAttribute("aria-pressed", "true");
            registrarAvaliacao({
              chave: chave, quando: new Date().toISOString(), nota: opcao[1],
              pergunta: extra.question, resposta: text, id: extra.id,
              historico: (extra.history || []).slice(-4)
            });
          });
          row.appendChild(botao);
        });
      }
      const copy = document.createElement("button");
      copy.className = "copy-button";
      copy.type = "button";
      copy.textContent = "Copiar resposta";
      copy.addEventListener("click", function () { copyText(text, copy); });
      row.appendChild(copy);
      main.appendChild(row);
    }
    outer.appendChild(avatar);
    outer.appendChild(main);
    ui.messages.appendChild(outer);
    scrollToLatest();
    return outer;
  }

  function createPending() {
    if (!ui.welcome.hidden) ui.welcome.hidden = true;
    const container = document.createElement("div");
    container.className = "message assistant";
    container.setAttribute("aria-label", "CRIVO está respondendo");
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.textContent = "◈";
    avatar.setAttribute("aria-hidden", "true");
    const main = document.createElement("div");
    main.className = "message-main";
    const name = document.createElement("div");
    name.className = "message-name";
    name.textContent = "CRIVO";
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    const dots = document.createElement("span");
    dots.className = "typing";
    for (let n = 0; n < 3; n += 1) {
      dots.appendChild(document.createElement("i"));
    }
    bubble.appendChild(dots);
    main.appendChild(name);
    main.appendChild(bubble);
    container.appendChild(avatar);
    container.appendChild(main);
    ui.messages.appendChild(container);
    scrollToLatest();
    return container;
  }

  async function sendQuestion(override) {
    if (state.busy) return;
    const question = String(override === undefined ? ui.question.value : override).trim();
    if (!question || question.length > 1200) return;
    state.busy = true;
    const generation = state.generation;
    const controller = new AbortController();
    state.controller = controller;
    ui.question.value = "";
    ui.question.disabled = true;
    updateComposer();
    createMessage("user", question);
    const pending = createPending();

    const timeout = setTimeout(function () { controller.abort(); }, 40000);
    try {
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify(Object.assign({
          message: question,
          history: state.history.slice(-MAX_HISTORY)
        }, state.remember ? { memory: state.memory || {} } : {})),
        signal: controller.signal
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(typeof data.error === "string" ?
          data.error : "Não foi possível concluir a pergunta.");
      }
      if (!data || typeof data.response !== "string" || typeof data.id !== "string") {
        throw new Error("O servidor devolveu uma resposta inválida.");
      }
      if (generation !== state.generation) return;
      pending.remove();
      createMessage("assistant", data.response, Object.assign({}, data, {
        question: question, history: state.history.slice(-MAX_HISTORY)
      }));
      if (state.remember && data.memory && typeof data.memory === "object") {
        state.memory = data.memory;
        gravarLocal(KEY_MEMORY, data.memory);
      }
      state.experimental = data.experimental_dialogue === true;
      state.history.push(question);
      state.history = state.history.slice(-MAX_HISTORY);
      setStatus("online", state.experimental ? "CRIVO experimental conectado" : "CRIVO conectado");
    } catch (error) {
      if (generation !== state.generation) return;
      pending.remove();
      if (controller.signal.aborted) {
        createMessage("assistant", "A solicitação demorou demais ou foi interrompida. Tente novamente.");
      } else {
        createMessage("assistant", "Não consegui responder agora. " +
          (error instanceof Error ? error.message : "Confira a conexão."));
      }
      const last = ui.messages.lastElementChild;
      if (last) last.classList.add("message-error");
      if (error instanceof TypeError) setStatus("offline", "Servidor indisponível");
      // Falhas não são reenviadas como perguntas respondidas no próximo turno.
    } finally {
      clearTimeout(timeout);
      if (generation !== state.generation) return;
      state.controller = null;
      state.busy = false;
      ui.question.disabled = false;
      updateComposer();
      if (window.matchMedia("(pointer: fine)").matches) ui.question.focus();
    }
  }

  ui.composer.addEventListener("submit", function (event) {
    event.preventDefault();
    sendQuestion();
  });
  ui.question.addEventListener("input", updateComposer);
  ui.question.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      sendQuestion();
    }
  });
  document.querySelectorAll("[data-prompt]").forEach(function (button) {
    button.addEventListener("click", function () {
      sendQuestion(button.getAttribute("data-prompt"));
    });
  });
  ui.clear.addEventListener("click", function () {
    state.generation += 1;
    if (state.controller) state.controller.abort();
    state.history = [];
    state.busy = false;
    state.controller = null;
    ui.question.value = "";
    ui.question.disabled = false;
    ui.messages.replaceChildren();
    ui.welcome.hidden = false;
    updateComposer();
  });
  const toggle = document.getElementById("remember-toggle");
  toggle.checked = state.remember;
  toggle.addEventListener("change", function () {
    state.remember = toggle.checked;
    gravarLocal(KEY_REMEMBER, state.remember);
    if (state.remember) {
      state.memory = lerLocal(KEY_MEMORY, {});
    } else {
      state.memory = null;
      apagarLocal(KEY_MEMORY);
    }
  });
  document.getElementById("forget-button").addEventListener("click", function () {
    state.memory = state.remember ? {} : null;
    apagarLocal(KEY_MEMORY);
    const botao = document.getElementById("forget-button");
    botao.textContent = "Esquecido!";
    setTimeout(function () { botao.textContent = "Esquecer tudo"; }, 1600);
  });
  document.getElementById("export-button").addEventListener("click", function () {
    const dados = JSON.stringify({ formato: "crivo-avaliacoes-v1", avaliacoes: avaliacoes() }, null, 1);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([dados], { type: "application/json" }));
    link.download = "crivo-avaliacoes.json";
    document.body.appendChild(link);
    link.click();
    setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 1000);
  });
  atualizarContagem();
  ui.info.addEventListener("click", function () { atualizarContagem(); ui.dialog.showModal(); });
  document.getElementById("about-close").addEventListener("click", function () {
    ui.dialog.close();
  });
  document.getElementById("about-ok").addEventListener("click", function () {
    ui.dialog.close();
  });
  ui.dialog.addEventListener("click", function (event) {
    if (event.target === ui.dialog) ui.dialog.close();
  });
  updateComposer();
  checkHealth();
}());
