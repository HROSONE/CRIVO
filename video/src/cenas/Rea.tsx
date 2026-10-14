import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

// Estrelas no GitHub: <10 mil em 6/10, >115 mil em 12/10 (contagens variam por fonte).
const PONTOS = [9.8, 12.9, 21, 29, 52, 84, 115];
const DIAS = ["6 OUT", "7", "8", "9", "10", "11", "12 OUT"];

const Pilula: React.FC<{ em: number; children: React.ReactNode; corFundo: string }> = ({
  em,
  children,
  corFundo,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        scale: estouro(frame, em),
        background: corFundo,
        color: cor.fundo,
        fontFamily: titulo,
        fontWeight: 700,
        fontSize: 44,
        padding: "18px 34px",
        borderRadius: 999,
      }}
    >
      {children}
    </div>
  );
};

export const Rea: React.FC = () => {
  const frame = useCurrentFrame();
  const prog = interpolate(frame, [50, 170], [0, 1], {
    ...preso,
    easing: Easing.in(Easing.quad),
  });
  const estrelas = interpolate(prog, [0, 1], [9800, 115000]);
  const L = 820;
  const A = 360;
  const caminho = PONTOS.map((p, i) => {
    const x = (i / (PONTOS.length - 1)) * L;
    const y = A - (p / 120) * A;
    return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} volume={0.8} />
      <Som nome="digitacao" em={8} volume={0.6} />
      {Array.from({ length: 16 }, (_, i) => (
        <Som key={i} nome="tique" em={52 + Math.round(i * 7.2)} tom={1 + i * 0.04} volume={0.6} />
      ))}
      <Som nome="boom" em={172} />
      <Som nome="pop" em={225} />
      <Som nome="pop" em={237} tom={1.2} />
      <Som nome="pop" em={249} tom={1.4} />
      <Som nome="whoosh-desce" em={300} />

      <Camera
        chaves={[
          { f: 0, s: 1.15 },
          { f: 20, s: 1 },
          { f: 150, s: 1.05 },
          { f: 172, s: 1.55, x: 420, y: -10 },
          { f: 215, s: 1.55, x: 420, y: -10 },
          { f: 228, s: 1 },
          { f: 300, s: 1.04 },
          { f: 330, s: 1.5, y: 200 },
        ]}
        tremidas={[172]}
      >
        <AbsoluteFill style={{ padding: "110px 120px", flexDirection: "column", gap: 40 }}>
          {/* cartão do repositório */}
          <div
            style={{
              opacity: surge(frame, 0),
              translate: `0 ${interpolate(frame, [0, 16], [60, 0], { ...preso, easing: saida })}px`,
              display: "flex",
              alignItems: "center",
              gap: 28,
            }}
          >
            <div
              style={{
                fontFamily: titulo,
                fontWeight: 700,
                fontSize: 128,
                color: cor.lima,
                letterSpacing: -4,
                lineHeight: 1,
              }}
            >
              REA
            </div>
            <div style={{ fontFamily: titulo, fontSize: 54, color: cor.texto, lineHeight: 1.1 }}>
              Reverse
              <br />
              Engineer Anything
            </div>
            <div
              style={{
                marginLeft: "auto",
                fontFamily: mono,
                fontSize: 36,
                color: cor.apagado,
                border: `2px solid ${cor.borda}`,
                padding: "12px 22px",
                borderRadius: 14,
              }}
            >
              github.com/morluto/rea
            </div>
          </div>

          <div style={{ display: "flex", gap: 70, alignItems: "flex-end", flex: 1 }}>
            {/* gráfico */}
            <div style={{ opacity: surge(frame, 30) }}>
              <svg width={L + 40} height={A + 70} style={{ overflow: "visible" }}>
                {[0, 40, 80, 120].map((v) => (
                  <line
                    key={v}
                    x1={0}
                    x2={L}
                    y1={A - (v / 120) * A}
                    y2={A - (v / 120) * A}
                    stroke={cor.borda}
                    strokeWidth={2}
                  />
                ))}
                <path
                  d={caminho}
                  fill="none"
                  stroke={cor.lima}
                  strokeWidth={10}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  pathLength={1}
                  strokeDasharray={1}
                  strokeDashoffset={1 - prog}
                />
                {DIAS.map((d, i) => (
                  <text
                    key={d}
                    x={(i / (DIAS.length - 1)) * L}
                    y={A + 55}
                    fill={cor.apagado}
                    fontFamily={mono}
                    fontSize={30}
                    textAnchor="middle"
                  >
                    {d}
                  </text>
                ))}
              </svg>
            </div>

            {/* contador */}
            <div style={{ flex: 1, paddingBottom: 60 }}>
              <div style={{ fontFamily: mono, fontSize: 40, color: cor.apagado }}>estrelas ★</div>
              <div
                style={{
                  fontFamily: titulo,
                  fontWeight: 700,
                  fontSize: 170,
                  lineHeight: 1,
                  color: frame >= 172 ? cor.lima : cor.texto,
                  letterSpacing: -5,
                }}
              >
                {Math.round(estrelas).toLocaleString("pt-BR")}
                {frame >= 172 ? "+" : ""}
              </div>
              <div
                style={{
                  fontFamily: titulo,
                  fontSize: 48,
                  color: cor.texto,
                  opacity: surge(frame, 176),
                }}
              >
                em uma semana · 25 mil forks
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 26, justifyContent: "center" }}>
            <Pilula em={225} corFundo={cor.lima}>
              servidor MCP
            </Pilula>
            <Pilula em={237} corFundo={cor.ciano}>
              Claude Code · Codex · Cursor
            </Pilula>
            <Pilula em={249} corFundo={cor.ambar}>
              Ghidra · IDA · Hopper
            </Pilula>
          </div>
          <div
            style={{
              textAlign: "center",
              fontFamily: mono,
              fontSize: 30,
              color: cor.apagado,
              opacity: surge(frame, 262),
            }}
          >
            agentes analisam binários, APKs e apps Electron sem o código-fonte · MIT · roda local
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
