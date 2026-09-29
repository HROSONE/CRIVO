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
  const state = { history: [], busy: false, controller: null };
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
      } finally { clearTimeout(timeout); }
      setStatus("online", "CRIVO conectado");
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
      } else if (extra.id && extra.id.indexOf("social:") === 0) {
        tag.textContent = "◇ Conversa";
      } else {
        tag.textContent = "◇ Base de conhecimento";
      }
      tag.title = "Motor: " + (extra.mechanism || "recuperador");
      row.appendChild(tag);
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
    state.controller = new AbortController();
    ui.question.value = "";
    ui.question.disabled = true;
    updateComposer();
    createMessage("user", question);
    const pending = createPending();

    const timeout = setTimeout(function () {
      if (state.controller) state.controller.abort();
    }, 40000);
    try {
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({
          message: question,
          history: state.history.slice(-MAX_HISTORY)
        }),
        signal: state.controller.signal
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(typeof data.error === "string" ?
          data.error : "Não foi possível concluir a pergunta.");
      }
      if (!data || typeof data.response !== "string" || typeof data.id !== "string") {
        throw new Error("O servidor devolveu uma resposta inválida.");
      }
      pending.remove();
      createMessage("assistant", data.response, data);
      state.history.push(question);
      state.history = state.history.slice(-MAX_HISTORY);
      setStatus("online", "CRIVO conectado");
    } catch (error) {
      pending.remove();
      if (state.controller && state.controller.signal.aborted) {
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
  ui.info.addEventListener("click", function () { ui.dialog.showModal(); });
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
