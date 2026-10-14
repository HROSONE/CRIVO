import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { preso } from "../comp/util";
import { cor, titulo } from "../tema";
import { PAGINAS } from "./dados.gen";

/**
 * Legenda por frase curta. O alinhamento é estimado (perto da sílaba), então
 * a página inteira entra junto em vez de destacar palavra por palavra.
 */
export const Legendas: React.FC = () => {
  const frame = useCurrentFrame();
  const pagina = PAGINAS.find((p) => frame >= p.de && frame < p.ate);
  if (!pagina) return null;
  const t = frame - pagina.de;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70, pointerEvents: "none" }}>
      <div
        style={{
          maxWidth: 1500,
          textAlign: "center",
          fontFamily: titulo,
          fontWeight: 700,
          fontSize: 60,
          lineHeight: 1.15,
          color: cor.texto,
          background: "rgba(7,8,12,0.78)",
          borderRadius: 18,
          padding: "12px 30px",
          scale: interpolate(t, [0, 5], [0.92, 1], { ...preso, easing: Easing.out(Easing.back(2)) }),
          opacity: interpolate(t, [0, 3], [0, 1], preso),
        }}
      >
        {pagina.palavras.map((w, i) => (
          <span key={i} style={{ color: w.d ? cor.lima : cor.texto }}>
            {i ? " " : ""}
            {w.t}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};
