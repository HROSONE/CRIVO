import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { preso, soco } from "./util";

export type Chave = { f: number; s: number; x?: number; y?: number };

/**
 * Câmera virtual: zoom e enquadramento por chaves (com "soco" rápido entre
 * elas) e tremidas que decaem em poucos quadros.
 */
export const Camera: React.FC<{
  chaves: Chave[];
  tremidas?: number[];
  children: React.ReactNode;
}> = ({ chaves, tremidas = [], children }) => {
  const frame = useCurrentFrame();
  const fs = chaves.map((c) => c.f);
  const anima = (valores: number[]) =>
    chaves.length === 1
      ? valores[0]
      : interpolate(frame, fs, valores, { ...preso, easing: soco });
  const s = anima(chaves.map((c) => c.s));
  const x = anima(chaves.map((c) => c.x ?? 0));
  const y = anima(chaves.map((c) => c.y ?? 0));

  let dx = 0;
  let dy = 0;
  for (const t of tremidas) {
    const d = frame - t;
    if (d >= 0 && d < 18) {
      const amp = 22 * Math.exp(-d / 4);
      dx += amp * Math.sin(d * 2.7);
      dy += amp * Math.cos(d * 3.3);
    }
  }

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${dx}px, ${dy}px) scale(${s}) translate(${-x}px, ${-y}px)`,
        transformOrigin: "50% 50%",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
