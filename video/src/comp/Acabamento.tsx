import React from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";

const granulado = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.55 0'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>`,
)}")`;

/** Granulado de filme, vinheta e linhas de varredura sobre o vídeo inteiro. */
export const Acabamento: React.FC = () => {
  const frame = useCurrentFrame();
  const x = Math.floor(random(`gx${frame}`) * 300);
  const y = Math.floor(random(`gy${frame}`) * 300);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill
        style={{
          backgroundImage: granulado,
          backgroundPosition: `${x}px ${y}px`,
          opacity: 0.09,
          mixBlendMode: "overlay",
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 4px)",
          opacity: 0.35,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.75) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/** Clarão branco e fatias deslocadas logo depois de um corte seco. */
export const Clarao: React.FC = () => {
  const frame = useCurrentFrame();
  const op = Math.max(0, 0.85 - frame * 0.22);
  if (op <= 0) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ backgroundColor: "white", opacity: op * 0.7 }} />
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: `${random(`cf${i}`) * 90}%`,
            height: 30 + random(`ch${i}`) * 80,
            background: i % 2 ? "rgba(61,224,255,0.5)" : "rgba(255,59,92,0.5)",
            transform: `translateX(${(random(`cx${i}${frame}`) - 0.5) * 300}px)`,
            opacity: op,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};
