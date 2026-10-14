import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

const LETRAS = ["C", "R", "I", "V", "O"];

export const Final: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo, overflow: "hidden" }}>
      {LETRAS.map((l, i) => (
        <Som key={l} nome="clique" em={i * 4} tom={0.8 + i * 0.1} />
      ))}
      <Som nome="boom" em={20} />
      <Som nome="whoosh" em={44} volume={0.6} />
      <Som nome="ding" em={80} volume={0.7} />

      {/* crivo = peneira: grade de furos ao fundo */}
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(circle, ${cor.lima} 3px, transparent 4px)`,
          backgroundSize: "48px 48px",
          opacity: interpolate(frame, [0, 30, 150, 180], [0, 0.14, 0.14, 0], preso),
          scale: interpolate(frame, [0, 180], [1.3, 1], preso),
        }}
      />

      <Camera chaves={[{ f: 0, s: 1.15 }, { f: 22, s: 1 }, { f: 150, s: 1.06 }, { f: 180, s: 1.1 }]} tremidas={[20]}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
          <div style={{ display: "flex", gap: 6 }}>
            {LETRAS.map((l, i) => (
              <div
                key={l}
                style={{
                  fontFamily: titulo,
                  fontWeight: 700,
                  fontSize: 300,
                  lineHeight: 1,
                  color: cor.lima,
                  translate: `0 ${interpolate(frame, [i * 4, i * 4 + 12], [-700, 0], { ...preso, easing: saida })}px`,
                }}
              >
                {l}
              </div>
            ))}
          </div>
          <div
            style={{
              marginTop: 30,
              fontFamily: titulo,
              fontSize: 64,
              color: cor.texto,
              textAlign: "center",
              opacity: surge(frame, 44, 10),
            }}
          >
            a engenharia reversa desmonta.
            <br />
            <span style={{ color: cor.lima, fontWeight: 700 }}>o CRIVO constrói o próprio.</span>
          </div>
          <div style={{ marginTop: 40, fontFamily: mono, fontSize: 38, color: cor.apagado, opacity: surge(frame, 80) }}>
            github.com/hrosone/crivo
          </div>
        </AbsoluteFill>
      </Camera>

      <AbsoluteFill
        style={{ backgroundColor: "black", opacity: interpolate(frame, [158, 180], [0, 1], preso) }}
      />
    </AbsoluteFill>
  );
};
