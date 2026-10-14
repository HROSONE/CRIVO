import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

type App = { nome: string; original: string; cor: string };

const FILEIRAS: { rotulo: string; em: number; apps: App[] }[] = [
  {
    rotulo: "contra a Adobe",
    em: 70,
    apps: [
      { nome: "PhotoCraft", original: "Photoshop", cor: "#3d9bff" },
      { nome: "VectorCraft", original: "Illustrator", cor: "#ff9a3d" },
      { nome: "FilmCraft", original: "Premiere", cor: "#a77bff" },
      { nome: "LightCraft", original: "Lightroom", cor: "#3de0ff" },
    ],
  },
  {
    rotulo: "contra o Office",
    em: 160,
    apps: [
      { nome: "WordCraft", original: "Word", cor: "#4d7cff" },
      { nome: "GridCraft", original: "Excel", cor: "#2fd07a" },
      { nome: "DeckCraft", original: "PowerPoint", cor: "#ff6a3d" },
    ],
  },
  {
    rotulo: "e o que a comunidade pedir",
    em: 235,
    apps: [
      { nome: "FigCraft", original: "Figma", cor: "#ff4fa3" },
      { nome: "CADCraft", original: "AutoCAD", cor: "#ff3b5c" },
    ],
  },
];

const Cartao: React.FC<{ app: App; em: number }> = ({ app, em }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        width: 350,
        scale: estouro(frame, em, 10),
        rotate: `${interpolate(frame, [em, em + 10], [-10, 0], preso)}deg`,
        background: cor.painel,
        border: `3px solid ${app.cor}`,
        borderRadius: 26,
        padding: "20px 28px",
        boxShadow: `0 0 60px ${app.cor}33`,
      }}
    >
      <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 48, color: cor.texto }}>
        {app.nome}
      </div>
      <div style={{ fontFamily: mono, fontSize: 30, color: cor.apagado, marginTop: 6 }}>
        clone do <span style={{ color: app.cor }}>{app.original}</span>
      </div>
    </div>
  );
};

export const Clones: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo, overflow: "hidden" }}>
      <Som nome="boom" em={0} />
      <Som nome="whoosh" em={4} />
      {FILEIRAS.flatMap((f) => f.apps.map((_, i) => f.em + i * 8)).map((em, i) => (
        <Som key={i} nome="clique" em={em} tom={0.9 + (i % 4) * 0.08} />
      ))}
      <Som nome="whoosh" em={60} volume={0.6} />
      <Som nome="whoosh-desce" em={150} volume={0.6} />
      <Som nome="whoosh-desce" em={225} volume={0.6} />
      <Som nome="pop" em={300} />
      <Som nome="whoosh" em={365} />

      {/* título "clonado" que se multiplica */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          opacity: interpolate(frame, [48, 58], [1, 0], preso),
        }}
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 300,
              letterSpacing: -10,
              color: i === 0 ? cor.texto : "transparent",
              WebkitTextStroke: i === 0 ? undefined : `3px ${cor.lima}`,
              opacity: i === 0 ? 1 : 0.7 - i * 0.12,
              translate: `0 ${interpolate(frame, [6, 30], [0, (i % 2 ? -1 : 1) * Math.ceil(i / 2) * 150], {
                ...preso,
                easing: saida,
              })}px`,
              zIndex: 5 - i,
            }}
          >
            CLONES
          </div>
        ))}
      </AbsoluteFill>

      <Camera
        chaves={[
          { f: 58, s: 1.15, y: -230 },
          { f: 150, s: 1.15, y: -230 },
          { f: 165, s: 1.35, y: 0 },
          { f: 225, s: 1.35, y: 0 },
          { f: 240, s: 1.35, y: 260 },
          { f: 290, s: 1.35, y: 260 },
          { f: 305, s: 0.95, y: 20 },
          { f: 360, s: 1 },
          { f: 390, s: 1.5, y: 380 },
        ]}
      >
        <AbsoluteFill
          style={{
            opacity: frame >= 58 ? 1 : 0,
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            gap: 26,
          }}
        >
          <div
            style={{
              fontFamily: mono,
              fontSize: 38,
              color: cor.lima,
              opacity: surge(frame, 58),
            }}
          >
            ArtCraft · Brandon Thomas · 100% open source, em Rust, feito com Claude
          </div>
          {FILEIRAS.map((f) => (
            <div key={f.rotulo} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  fontFamily: titulo,
                  fontSize: 40,
                  color: cor.apagado,
                  opacity: surge(frame, f.em - 6),
                }}
              >
                {f.rotulo}
              </div>
              <div style={{ display: "flex", gap: 26 }}>
                {f.apps.map((a, i) => (
                  <Cartao key={a.nome} app={a} em={f.em + i * 8} />
                ))}
              </div>
            </div>
          ))}
          <div
            style={{
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 50,
              color: cor.fundo,
              background: cor.lima,
              padding: "14px 30px",
              borderRadius: 14,
              scale: estouro(frame, 300),
            }}
          >
            o próximo clone é escolhido por votação no Discord
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
