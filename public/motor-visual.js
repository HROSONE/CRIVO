"use strict";

(function () {
  const palco = document.getElementById("palco");
  const painel = document.getElementById("painel");
  const input = document.getElementById("json-input");
  const erroEl = document.getElementById("erro");
  const btnUi = document.getElementById("btn-ui");
  const btnFechar = document.getElementById("btn-fechar");
  const btnRodar = document.getElementById("btn-rodar");
  const SVG_NS = "http://www.w3.org/2000/svg";
  const TIPOS_3D = new Set(["esfera", "cubo", "cilindro", "anel", "particulas"]);
  const TIPOS_SVG = new Set(["onda", "circulo", "retangulo", "linha", "seta"]);
  const FORMATOS = new Set(["9:16", "16:9", "1:1"]);

  const PRESETS = {
    orbita: {
      modo: "3d", formato: "9:16", fundo: "#05070f", camera: "orbita_lenta",
      objetos: [
        { tipo: "esfera", tam: 1.3, cor: "#ffae33", brilho: 1.0, anim: "pulsar", vel: 0.6 },
        { tipo: "esfera", tam: 0.42, cor: "#4da6ff", anim: "orbita", raio_orbita: 3.8, vel: 0.7 },
        { tipo: "anel", tam: 0.8, cor: "#d9c29c", segue: 1, inclinacao: 28, opacidade: 0.85 },
        { tipo: "particulas", qtd: 500, tam: 14, cor: "#ffffff", anim: "girar", vel: 0.04 }
      ]
    },
    buraco: {
      modo: "3d", formato: "9:16", fundo: "#020308", camera: "zoom_suave",
      objetos: [
        { tipo: "esfera", tam: 1.15, cor: "#000000", brilho: 0.0 },
        { tipo: "anel", tam: 2.3, cor: "#ff6b1a", brilho: 0.9, inclinacao: 72, anim: "girar", vel: 1.2 },
        { tipo: "anel", tam: 3.1, cor: "#ffaa44", brilho: 0.5, inclinacao: 72, opacidade: 0.55, anim: "girar", vel: -0.7 },
        { tipo: "particulas", qtd: 700, tam: 10, cor: "#ff9955", anim: "girar", vel: 0.25 }
      ]
    },
    ondas: {
      modo: "svg", formato: "9:16", fundo: "#070b14",
      objetos: [
        { tipo: "onda", pos: [0, 42], tam: [100, 10], cor: "#38bdf8", espessura: 1.4, anim: "fluir", vel: 1.4 },
        { tipo: "onda", pos: [0, 58], tam: [100, 7], cor: "#a78bfa", espessura: 1.2, anim: "fluir", vel: -0.9 },
        { tipo: "circulo", pos: [50, 50], tam: 12, cor: "#f472b6", preenchido: false, espessura: 1.2, anim: "pulsar", vel: 1.2 },
        { tipo: "seta", pos: [20, 78], pos2: [80, 78], cor: "#34d399", espessura: 1.4, anim: "desenhar", vel: 1.0 }
      ]
    }
  };

  let animId = 0;
  let renderer = null;
  let scene = null;
  let camera = null;
  let relogio = null;

  function abrirPainel(aberto) {
    painel.classList.toggle("aberto", aberto);
    painel.setAttribute("aria-hidden", String(!aberto));
    btnUi.setAttribute("aria-expanded", String(aberto));
  }

  function mensagemErro(texto) {
    erroEl.textContent = texto || "";
  }

  function numero(valor, padrao) {
    return typeof valor === "number" && Number.isFinite(valor) ? valor : padrao;
  }

  function validarConfig(cfg) {
    if (!cfg || typeof cfg !== "object" || Array.isArray(cfg)) {
      throw new Error("A configuração precisa ser um objeto JSON.");
    }
    if (cfg.modo !== "3d" && cfg.modo !== "svg") {
      throw new Error('O campo "modo" deve ser "3d" ou "svg".');
    }
    cfg.formato = cfg.formato || "9:16";
    if (!FORMATOS.has(cfg.formato)) throw new Error('Formato inválido. Use "9:16", "16:9" ou "1:1".');
    if (typeof cfg.fundo !== "string" || cfg.fundo.length > 48) {
      throw new Error('O campo "fundo" deve ser uma cor CSS curta, como "#05070f".');
    }
    if (!Array.isArray(cfg.objetos)) throw new Error('O campo "objetos" precisa ser uma lista.');
    if (cfg.objetos.length > 200) throw new Error("Limite de 200 objetos por cena.");
    const tipos = cfg.modo === "3d" ? TIPOS_3D : TIPOS_SVG;
    cfg.objetos.forEach(function (o, i) {
      if (!o || typeof o !== "object" || !tipos.has(o.tipo)) {
        throw new Error("Tipo de objeto inválido na posição " + i + ".");
      }
      if (o.pos !== undefined && (!Array.isArray(o.pos) || o.pos.length < 2 ||
          !o.pos.every(Number.isFinite))) {
        throw new Error("Posição inválida no objeto " + i + ".");
      }
      if (o.pos2 !== undefined && (!Array.isArray(o.pos2) || o.pos2.length < 2 ||
          !o.pos2.every(Number.isFinite))) {
        throw new Error("Posição final inválida no objeto " + i + ".");
      }
      if (typeof o.tam === "number" && (!Number.isFinite(o.tam) || o.tam <= 0 || o.tam > 100)) {
        throw new Error("Tamanho inválido no objeto " + i + ".");
      }
      if (o.tipo === "particulas") {
        const qtd = numero(o.qtd, 400);
        if (!Number.isInteger(qtd) || qtd < 1 || qtd > 5000) {
          throw new Error("Use entre 1 e 5.000 partículas.");
        }
      }
      if (o.cor !== undefined && (typeof o.cor !== "string" || o.cor.length > 48)) {
        throw new Error("Cor inválida no objeto " + i + ".");
      }
    });
    return cfg;
  }

  function limparCena() {
    if (animId) cancelAnimationFrame(animId);
    animId = 0;
    if (scene) {
      scene.traverse(function (obj) {
        if (obj.geometry && typeof obj.geometry.dispose === "function") obj.geometry.dispose();
        if (obj.material) {
          const materiais = Array.isArray(obj.material) ? obj.material : [obj.material];
          materiais.forEach(function (m) {
            if (m && typeof m.dispose === "function") m.dispose();
          });
        }
      });
    }
    scene = null;
    camera = null;
    relogio = null;
    if (renderer) {
      renderer.dispose();
      renderer.domElement.remove();
      renderer = null;
    }
    palco.replaceChildren();
  }

  function aplicarFormato(formato, fundo) {
    palco.className = formato === "9:16" ? "f-9-16" :
      (formato === "16:9" ? "f-16-9" : "f-1-1");
    palco.style.background = fundo;
  }

  function renderizar3D(cfg) {
    if (!window.THREE) {
      throw new Error("A biblioteca 3D local não carregou. Recarregue a página.");
    }

    const largura = palco.clientWidth || 360;
    const altura = palco.clientHeight || 640;
    scene = new THREE.Scene();
    scene.background = new THREE.Color(cfg.fundo);
    camera = new THREE.PerspectiveCamera(50, largura / altura, 0.1, 200);
    camera.position.set(0, 2.5, 9);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(largura, altura);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    palco.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.45));
    const luz = new THREE.PointLight(0xffffff, 2.2, 50);
    luz.position.set(0, 2, 4);
    scene.add(luz);

    const itens = [];
    cfg.objetos.forEach(function (o, idx) {
      const cor = new THREE.Color(o.cor || "#4da6ff");
      const tam = typeof o.tam === "number" ? o.tam : 1;
      const brilho = numero(o.brilho, 0);
      const opacidade = Math.max(0, Math.min(1, numero(o.opacidade, 1)));
      let mesh;

      if (o.tipo === "particulas") {
        const qtd = numero(o.qtd, 400);
        const espalhamento = numero(o.tam, 8);
        const posicoes = new Float32Array(qtd * 3);
        for (let i = 0; i < qtd * 3; i++) {
          posicoes[i] = (Math.random() - 0.5) * espalhamento * 2;
        }
        const geometria = new THREE.BufferGeometry();
        geometria.setAttribute("position", new THREE.BufferAttribute(posicoes, 3));
        const materialPontos = new THREE.PointsMaterial({
          color: cor, size: Math.max(0.01, numero(o.tamanho_particula, 0.08)),
          transparent: true, opacity: opacidade, sizeAttenuation: true
        });
        mesh = new THREE.Points(geometria, materialPontos);
      } else {
        let geometria;
        if (o.tipo === "cubo") geometria = new THREE.BoxGeometry(tam, tam, tam);
        else if (o.tipo === "cilindro") {
          geometria = new THREE.CylinderGeometry(tam * 0.6, tam * 0.6, tam * 1.6, 32);
        } else if (o.tipo === "anel") {
          geometria = new THREE.RingGeometry(tam * 0.65, tam, 64);
        } else geometria = new THREE.SphereGeometry(tam, 32, 32);

        const material = new THREE.MeshStandardMaterial({
          color: cor, emissive: cor, emissiveIntensity: brilho,
          transparent: opacidade < 1, opacity: opacidade,
          wireframe: Boolean(o.arame), side: THREE.DoubleSide
        });
        mesh = new THREE.Mesh(geometria, material);
      }

      const p = o.pos || [0, 0, 0];
      mesh.position.set(numero(p[0], 0), numero(p[1], 0), numero(p[2], 0));
      if (o.tipo === "anel") {
        mesh.rotation.x = Math.PI / 2;
        mesh.rotation.x += THREE.MathUtils.degToRad(numero(o.inclinacao, 0));
      }
      scene.add(mesh);
      itens.push({ mesh: mesh, o: o, basePos: mesh.position.clone(), indice: idx });
    });

    relogio = new THREE.Clock();

    function loop() {
      animId = requestAnimationFrame(loop);
      const t = relogio.getElapsedTime();

      itens.forEach(function (item) {
        const mesh = item.mesh;
        const o = item.o;
        const v = numero(o.vel, 1);
        if (o.anim === "girar") mesh.rotation.y = t * v;
        else if (o.anim === "pulsar") {
          const escala = 1 + Math.sin(t * v * 3) * 0.08;
          mesh.scale.set(escala, escala, escala);
        } else if (o.anim === "flutuar") {
          mesh.position.y = item.basePos.y + Math.sin(t * v * 2) * 0.4;
        } else if (o.anim === "orbita") {
          const r = numero(o.raio_orbita, 3);
          mesh.position.set(Math.cos(t * v) * r, item.basePos.y, Math.sin(t * v) * r);
        }
      });

      itens.forEach(function (item) {
        const seguir = item.o.segue;
        if (Number.isInteger(seguir) && itens[seguir] && seguir !== item.indice) {
          item.mesh.position.copy(itens[seguir].mesh.position);
        }
      });

      if (cfg.camera === "orbita_lenta") {
        camera.position.x = Math.sin(t * 0.25) * 9.5;
        camera.position.z = Math.cos(t * 0.25) * 9.5;
        camera.lookAt(0, 0, 0);
      } else if (cfg.camera === "zoom_suave") {
        camera.position.z = 9 - Math.sin(t * 0.35) * 2.2;
        camera.lookAt(0, 0, 0);
      }
      renderer.render(scene, camera);
    }
    loop();
  }

  function criarOnda(o, t) {
    const p = o.pos || [50, 50];
    const dimensoes = Array.isArray(o.tam) ? o.tam : [100, 8];
    const largura = Math.max(1, numero(dimensoes[0], 100));
    const amplitude = numero(dimensoes[1], 8);
    const velocidade = numero(o.vel, 1);
    let d = "";
    for (let x = 0; x <= largura; x += 2) {
      const y = p[1] + Math.sin((x / largura) * Math.PI * 4 + t * velocidade * 3) * amplitude;
      d += (x === 0 ? "M" : "L") + (p[0] + x) + " " + y.toFixed(2) + " ";
    }
    return d;
  }

  function renderizarSVG(cfg) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    const defs = document.createElementNS(SVG_NS, "defs");
    svg.appendChild(defs);
    palco.appendChild(svg);

    const nos = [];
    cfg.objetos.forEach(function (o, i) {
      const cor = o.cor || "#4da6ff";
      const esp = numero(o.espessura, 1.5);
      const p = o.pos || [50, 50];
      let el;

      if (o.tipo === "circulo") {
        el = document.createElementNS(SVG_NS, "circle");
        el.setAttribute("cx", p[0]);
        el.setAttribute("cy", p[1]);
        el.setAttribute("r", numero(o.tam, 12));
        el.setAttribute("fill", o.preenchido === false ? "none" : cor);
        el.setAttribute("stroke", cor);
        el.setAttribute("stroke-width", esp);
      } else if (o.tipo === "retangulo") {
        const t = Array.isArray(o.tam) ? o.tam : [numero(o.tam, 20), numero(o.tam, 12)];
        const largura = numero(t[0], 20);
        const altura = numero(t[1], 12);
        el = document.createElementNS(SVG_NS, "rect");
        el.setAttribute("x", p[0] - largura / 2);
        el.setAttribute("y", p[1] - altura / 2);
        el.setAttribute("width", largura);
        el.setAttribute("height", altura);
        el.setAttribute("rx", 2);
        el.setAttribute("fill", o.preenchido === false ? "none" : cor);
        el.setAttribute("stroke", cor);
        el.setAttribute("stroke-width", esp);
      } else if (o.tipo === "linha" || o.tipo === "seta") {
        const p2 = o.pos2 || [80, 50];
        el = document.createElementNS(SVG_NS, "line");
        el.setAttribute("x1", p[0]);
        el.setAttribute("y1", p[1]);
        el.setAttribute("x2", p2[0]);
        el.setAttribute("y2", p2[1]);
        el.setAttribute("stroke", cor);
        el.setAttribute("stroke-width", esp);
        el.setAttribute("stroke-linecap", "round");
        if (o.tipo === "seta") {
          const marcador = document.createElementNS(SVG_NS, "marker");
          marcador.setAttribute("id", "seta-" + i);
          marcador.setAttribute("markerWidth", "6");
          marcador.setAttribute("markerHeight", "6");
          marcador.setAttribute("refX", "5");
          marcador.setAttribute("refY", "3");
          marcador.setAttribute("orient", "auto");
          const poligono = document.createElementNS(SVG_NS, "polygon");
          poligono.setAttribute("points", "0 0, 6 3, 0 6");
          poligono.setAttribute("fill", cor);
          marcador.appendChild(poligono);
          defs.appendChild(marcador);
          el.setAttribute("marker-end", "url(#seta-" + i + ")");
        }
      } else if (o.tipo === "onda") {
        el = document.createElementNS(SVG_NS, "path");
        el.setAttribute("fill", "none");
        el.setAttribute("stroke", cor);
        el.setAttribute("stroke-width", esp);
        el.setAttribute("stroke-linecap", "round");
        el.setAttribute("d", criarOnda(o, 0));
      }

      if (el) {
        svg.appendChild(el);
        nos.push({ el: el, o: o, indice: i, p: p });
      }
    });

    const inicio = performance.now();
    function loop(agora) {
      animId = requestAnimationFrame(loop);
      const t = (agora - inicio) / 1000;
      nos.forEach(function (no) {
        const el = no.el;
        const o = no.o;
        const p = no.p;
        const v = numero(o.vel, 1);
        if (o.tipo === "onda") {
          if (o.anim === "fluir") el.setAttribute("d", criarOnda(o, t));
        } else if (o.anim === "pulsar") {
          const escala = 1 + Math.sin(t * v * 3) * 0.12;
          el.setAttribute("transform", "translate(" + p[0] + " " + p[1] + ") scale(" + escala + ") translate(" + (-p[0]) + " " + (-p[1]) + ")");
        } else if (o.anim === "girar") {
          el.setAttribute("transform", "rotate(" + ((t * v * 60) % 360) + " " + p[0] + " " + p[1] + ")");
        } else if (o.anim === "desenhar" && typeof el.getTotalLength === "function") {
          const comprimento = el.getTotalLength();
          const progresso = (Math.sin(t * v * 1.5 - Math.PI / 2) + 1) / 2;
          el.setAttribute("stroke-dasharray", String(comprimento));
          el.setAttribute("stroke-dashoffset", String(comprimento * (1 - progresso)));
        }
      });
    }
    animId = requestAnimationFrame(loop);
  }

  function renderizar(cfg) {
    limparCena();
    aplicarFormato(cfg.formato, cfg.fundo);
    if (cfg.modo === "svg") renderizarSVG(cfg);
    else renderizar3D(cfg);
  }

  function renderizarDoEditor() {
    try {
      mensagemErro("");
      const cfg = validarConfig(JSON.parse(input.value));
      renderizar(cfg);
    } catch (err) {
      mensagemErro("Não foi possível renderizar: " + (err && err.message ? err.message : "erro desconhecido"));
    }
  }

  function carregarPreset(nome) {
    if (!Object.prototype.hasOwnProperty.call(PRESETS, nome)) return;
    input.value = JSON.stringify(PRESETS[nome], null, 2);
    renderizarDoEditor();
  }

  function redimensionar() {
    if (!renderer || !camera) return;
    const largura = palco.clientWidth || 360;
    const altura = palco.clientHeight || 640;
    camera.aspect = largura / altura;
    camera.updateProjectionMatrix();
    renderer.setSize(largura, altura, false);
  }

  btnUi.addEventListener("click", function () {
    abrirPainel(!painel.classList.contains("aberto"));
  });
  btnFechar.addEventListener("click", function () { abrirPainel(false); });
  btnRodar.addEventListener("click", renderizarDoEditor);
  document.querySelectorAll("[data-preset]").forEach(function (botao) {
    botao.addEventListener("click", function () { carregarPreset(botao.dataset.preset); });
  });
  window.addEventListener("resize", redimensionar);
  window.addEventListener("keydown", function (evento) {
    const alvo = document.activeElement;
    const digitando = alvo && (alvo.tagName === "TEXTAREA" || alvo.tagName === "INPUT" ||
      alvo.isContentEditable);
    if (evento.key.toLowerCase() === "e" && !digitando) {
      abrirPainel(!painel.classList.contains("aberto"));
    }
    if (evento.key === "Escape") abrirPainel(false);
  });
  window.addEventListener("pagehide", limparCena);

  input.value = JSON.stringify(PRESETS.orbita, null, 2);
  renderizarDoEditor();
})();
