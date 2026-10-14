import React from "react";
import { random, useCurrentFrame } from "remotion";
import { cor } from "../tema";

/**
 * Texto com separação RGB. Nos quadros listados em `picos` a separação e o
 * recorte em fatias ficam fortes; fora deles, um tremor leve.
 */
export const Glitch: React.FC<{
  children: string;
  style?: React.CSSProperties;
  picos?: [number, number][];
  semente?: string;
}> = ({ children, style, picos = [], semente = "g" }) => {
  const frame = useCurrentFrame();
  const forte = picos.some(([a, b]) => frame >= a && frame <= b);
  const r = (k: string) => random(`${semente}-${k}-${frame}`) - 0.5;
  const sep = forte ? 26 : 3;
  const camada = (
    corTexto: string,
    dx: number,
    dy: number,
    mistura: React.CSSProperties["mixBlendMode"],
    clip?: string,
  ) => (
    <div
      style={{
        position: "absolute",
        inset: 0,
        color: corTexto,
        transform: `translate(${dx}px, ${dy}px)`,
        mixBlendMode: mistura,
        clipPath: clip,
      }}
    >
      {children}
    </div>
  );
  const fatia = forte
    ? `inset(${Math.floor((r("a") + 0.5) * 70)}% 0 ${Math.floor((r("b") + 0.5) * 30)}% 0)`
    : undefined;
  return (
    <div style={{ position: "relative", ...style }}>
      <div style={{ visibility: "hidden" }}>{children}</div>
      {camada(cor.vermelho, r("x1") * sep, r("y1") * sep * 0.3, "screen")}
      {camada(cor.ciano, r("x2") * sep, r("y2") * sep * 0.3, "screen")}
      {camada(style?.color ?? cor.texto, 0, 0, "normal")}
      {forte && camada(cor.texto, r("x3") * 60, 0, "normal", fatia)}
    </div>
  );
};
