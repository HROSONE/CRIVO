import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

type Dado = { em: number; valor: (p: number) => string; texto: string; destaque: string };

const DADOS: Dado[] = [
  {
    em: 130,
    valor: (p) => `17M → ${Math.round(17 + 29 * p)}M`,
    texto: "parâmetros num Transformer próprio, treinado do zero",
    destaque: cor.lima,
  },
  {
    em: 150,
    valor: (p) => `~${(2.5 * p).toFixed(1).replace(".", ",")} bi`,
    texto: "tokens de português lidos no pré-treino",
    destaque: cor.ciano,
  },
  {
    em: 170,
    valor: (p) => Math.round(3947 * p).toLocaleString("pt-BR"),
    texto: "fatos com fonte, em 680 conceitos",
    destaque: cor.ambar,
  },
  {
    em: 190,
    valor: () => "offline",
    texto: "app Android: Python, NumPy e os pesos no aparelho",
    destaque: cor.lima,
  },
  {
    em: 210,
    valor: () => "0",
    texto: "modelos ou APIs de terceiros: tokenizador e pesos próprios",
    destaque: cor.vermelho,
  },
];

const Cartao: React.FC<{ d: Dado }> = ({ d }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [d.em, d.em + 40], [0, 1], { ...preso, easing: Easing.out(Easing.cubic) });
  return (
    <div
      style={{
        width: 520,
        minHeight: 250,
        background: cor.painel,
        border: `2px solid ${cor.borda}`,
        borderTop: `8px solid ${d.destaque}`,
        borderRadius: 24,
        padding: "28px 34px",
        scale: estouro(frame, d.em, 10),
      }}
    >
      <div
        style={{
          fontFamily: titulo,
          fontWeight: 700,
          fontSize: 86,
          color: d.destaque,
          letterSpacing: -3,
          lineHeight: 1,
          whiteSpace: "nowrap",
        }}
      >
        {d.valor(p)}
      </div>
      <div style={{ fontFamily: titulo, fontSize: 38, color: cor.texto, marginTop: 14, lineHeight: 1.2 }}>
        {d.texto}
      </div>
    </div>
  );
};

export const Crivo: React.FC = () => {
  const frame = useCurrentFrame();
  const parte = frame < 60 ? 0 : frame < 120 ? 1 : frame < 330 ? 2 : 3;
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo, overflow: "hidden" }}>
      <Som nome="glitch" em={0} volume={0.6} />
      <Som nome="boom" em={60} />
      <Som nome="whoosh" em={115} />
      {DADOS.map((d) => (
        <Som key={d.em} nome="pop" em={d.em} tom={1 + (d.em - 130) / 200} />
      ))}
      <Som nome="whoosh" em={245} volume={0.6} />
      <Som nome="whoosh-desce" em={280} volume={0.6} />
      <Som nome="whoosh" em={325} />
      <Som nome="ding" em={340} volume={0.6} />
      <Som nome="clique" em={372} />

      {/* "enquanto o mundo clona…" */}
      {parte === 0 && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <Camera chaves={[{ f: 0, s: 1 }, { f: 60, s: 1.25 }]}>
            <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
              <Glitch
                semente="clona"
                picos={[[0, 5]]}
                style={{ fontFamily: titulo, fontWeight: 500, fontSize: 120, color: cor.apagado }}
              >
                enquanto o mundo clona…
              </Glitch>
            </AbsoluteFill>
          </Camera>
        </AbsoluteFill>
      )}

      {/* revelação */}
      {parte === 1 && (
        <Camera chaves={[{ f: 60, s: 1.4 }, { f: 70, s: 1 }, { f: 120, s: 1.12 }]} tremidas={[60]}>
          <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
            <div style={{ fontFamily: titulo, fontSize: 90, color: cor.texto }}>…o</div>
            <div
              style={{
                fontFamily: titulo,
                fontWeight: 700,
                fontSize: 340,
                lineHeight: 0.9,
                color: cor.lima,
                letterSpacing: -14,
                scale: estouro(frame, 60, 8),
              }}
            >
              CRIVO
            </div>
            <div style={{ fontFamily: titulo, fontSize: 90, color: cor.texto, opacity: surge(frame, 72, 8) }}>
              cresce do zero.
            </div>
          </AbsoluteFill>
        </Camera>
      )}

      {/* números do repositório */}
      {parte === 2 && (
        <Camera
          chaves={[
            { f: 120, s: 1.2 },
            { f: 135, s: 1 },
            { f: 235, s: 1 },
            { f: 247, s: 1.7, x: -560, y: -150 },
            { f: 270, s: 1.7, x: -560, y: -150 },
            { f: 282, s: 1.7, x: 280, y: 170 },
            { f: 315, s: 1.7, x: 280, y: 170 },
            { f: 328, s: 1 },
          ]}
        >
          <AbsoluteFill style={{ padding: "90px 110px", flexDirection: "column", gap: 34 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 24, opacity: surge(frame, 120, 10) }}>
              <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 80, color: cor.texto }}>
                hrosone/crivo
              </div>
              <div style={{ fontFamily: mono, fontSize: 34, color: cor.apagado }}>
                IA de conversa em português · v0.4
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 34, justifyContent: "center" }}>
              {DADOS.map((d) => (
                <Cartao key={d.em} d={d} />
              ))}
            </div>
          </AbsoluteFill>
        </Camera>
      )}

      {/* identidade */}
      {parte === 3 && (
        <Camera chaves={[{ f: 330, s: 1.3 }, { f: 340, s: 1 }, { f: 395, s: 1.05 }, { f: 420, s: 1.8, y: -80 }]}>
          <AbsoluteFill
            style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 30, padding: 120 }}
          >
            <div style={{ fontFamily: mono, fontSize: 36, color: cor.apagado, opacity: surge(frame, 332, 8) }}>
              IDENTIDADE.md
            </div>
            <div
              style={{
                fontFamily: titulo,
                fontWeight: 700,
                fontSize: 128,
                color: cor.texto,
                letterSpacing: -4,
                textAlign: "center",
                lineHeight: 1,
                scale: estouro(frame, 340, 10),
              }}
            >
              verdade acima de <span style={{ color: cor.lima }}>agradar</span>
            </div>
            <div
              style={{
                fontFamily: titulo,
                fontSize: 54,
                color: cor.apagado,
                textAlign: "center",
                opacity: surge(frame, 372, 10),
                translate: `0 ${interpolate(frame, [372, 384], [30, 0], { ...preso, easing: saida })}px`,
              }}
            >
              quando não sabe, diz que não sabe · cada resultado registrado com seus limites
            </div>
          </AbsoluteFill>
        </Camera>
      )}
    </AbsoluteFill>
  );
};
