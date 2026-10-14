import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

const Noticia: React.FC<{ em: number; fonte: string; data: string; children: React.ReactNode }> = ({
  em,
  fonte,
  data,
  children,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        flex: 1,
        background: cor.painel,
        border: `2px solid ${cor.borda}`,
        borderRadius: 24,
        padding: "30px 36px",
        opacity: surge(frame, em, 8),
        translate: `0 ${interpolate(frame, [em, em + 14], [120, 0], { ...preso, easing: saida })}px`,
      }}
    >
      <div style={{ fontFamily: mono, fontSize: 32, color: cor.ciano }}>
        {fonte} · {data}
      </div>
      <div style={{ fontFamily: titulo, fontSize: 44, color: cor.texto, marginTop: 12, lineHeight: 1.2 }}>
        {children}
      </div>
    </div>
  );
};

export const Modelos: React.FC = () => {
  const frame = useCurrentFrame();
  const fluxo = Array.from({ length: 28 }, (_, i) => {
    const inicio = 20 + i * 3;
    const p = interpolate(frame, [inicio, inicio + 30], [0, 1], preso);
    return { i, p, y: (random(`fy${i}`) - 0.5) * 120 };
  });
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} />
      <Som nome="riser" em={10} volume={0.35} />
      <Som nome="boom" em={110} volume={0.8} />
      <Som nome="whoosh" em={160} volume={0.7} />
      <Som nome="whoosh" em={185} volume={0.7} />
      <Som nome="glitch" em={245} />

      <Camera
        chaves={[
          { f: 0, s: 1.2, y: -120 },
          { f: 20, s: 1, y: -60 },
          { f: 100, s: 1.02, y: -60 },
          { f: 112, s: 1.3, x: 520, y: -140 },
          { f: 150, s: 1.3, x: 520, y: -140 },
          { f: 162, s: 1 },
          { f: 240, s: 1.02 },
          { f: 270, s: 2.4 },
        ]}
        tremidas={[110]}
      >
        <AbsoluteFill style={{ padding: "100px 120px", flexDirection: "column", gap: 40 }}>
          <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 92, color: cor.texto, letterSpacing: -2 }}>
            e tem quem clone o <span style={{ color: cor.ciano }}>cérebro</span>
          </div>

          {/* diagrama de destilação */}
          <div style={{ display: "flex", alignItems: "center", height: 330, position: "relative" }}>
            <div
              style={{
                width: 440,
                height: 280,
                borderRadius: 30,
                border: `4px solid ${cor.ciano}`,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                fontFamily: titulo,
                fontSize: 50,
                fontWeight: 700,
                color: cor.texto,
                scale: estouro(frame, 6),
                background: "#0b1a22",
              }}
            >
              modelo de ponta
              <div style={{ fontFamily: mono, fontSize: 30, color: cor.apagado, fontWeight: 400 }}>
                respostas + raciocínio
              </div>
            </div>
            <div style={{ flex: 1, position: "relative", height: "100%" }}>
              {fluxo.map(({ i, p, y }) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: `${p * 100}%`,
                    top: `calc(50% + ${y * Math.sin(p * Math.PI)}px)`,
                    width: 18,
                    height: 18,
                    borderRadius: 9,
                    background: cor.ciano,
                    opacity: p > 0 && p < 1 ? 1 : 0,
                    boxShadow: `0 0 20px ${cor.ciano}`,
                  }}
                />
              ))}
              <div
                style={{
                  position: "absolute",
                  width: "100%",
                  top: 20,
                  textAlign: "center",
                  fontFamily: mono,
                  fontSize: 34,
                  color: cor.ciano,
                  opacity: surge(frame, 30),
                }}
              >
                destilação adversarial
              </div>
            </div>
            <div
              style={{
                width: 300,
                height: 190,
                borderRadius: 24,
                border: `4px dashed ${cor.vermelho}`,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                fontFamily: titulo,
                fontSize: 46,
                fontWeight: 700,
                color: cor.texto,
                scale: estouro(frame, 110, 10),
                background: "#220b10",
              }}
            >
              cópia barata
            </div>
          </div>

          <div style={{ display: "flex", gap: 36 }}>
            <Noticia em={160} fonte="OpenAI" data="1º out">
              derrubou uma campanha de extração de raciocínio ligada a associados da Moonshot AI
            </Noticia>
            <Noticia em={185} fonte="Anthropic" data="segundo relatos">
              novas defesas contra destilação por concorrentes; a Zhipu AI foi citada
            </Noticia>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
