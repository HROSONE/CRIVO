import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { embaralhado, estouro, preso, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";

const CODIGO = [
  "void Jogador::atirar(Arma* a) {",
  "  if (a->municao <= 0) {",
  "    tocarSom(SOM_VAZIO);",
  "    return;",
  "  }",
  "  a->municao--;",
  "  Projetil p = a->disparar(mira);",
  "  mundo->adicionar(p);",
  "}",
];

export const Binario: React.FC = () => {
  const frame = useCurrentFrame();
  const varre = interpolate(frame, [20, 110], [0, 100], preso);
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} volume={0.7} />
      <Som nome="digitacao" em={22} volume={0.7} />
      <Som nome="digitacao" em={70} volume={0.7} />
      <Som nome="boom" em={132} />
      <Som nome="pop" em={168} />
      <Som nome="whoosh" em={215} />

      <Camera
        chaves={[
          { f: 0, s: 1.3, x: -300 },
          { f: 20, s: 1.05, x: -150 },
          { f: 110, s: 1.05, x: 150 },
          { f: 132, s: 1 },
          { f: 215, s: 1.03 },
          { f: 240, s: 1.6 },
        ]}
        tremidas={[132]}
      >
        <AbsoluteFill style={{ padding: "100px 120px", flexDirection: "column" }}>
          <div
            style={{
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 92,
              color: cor.texto,
              letterSpacing: -2,
              opacity: surge(frame, 0, 10),
            }}
          >
            do <span style={{ color: cor.ambar }}>binário</span> ao{" "}
            <span style={{ color: cor.lima }}>código</span>
          </div>

          <div
            style={{
              marginTop: 40,
              position: "relative",
              background: cor.painel,
              border: `2px solid ${cor.borda}`,
              borderRadius: 24,
              padding: "36px 46px",
              fontFamily: mono,
              fontSize: 40,
              lineHeight: "60px",
              whiteSpace: "pre",
              overflow: "hidden",
              opacity: interpolate(frame, [125, 135], [1, 0.08], preso),
            }}
          >
            {CODIGO.map((linha, i) => {
              const revela = 22 + i * 10;
              const pronto = frame >= revela + linha.length * 0.6;
              return (
                <div key={i} style={{ color: pronto ? cor.texto : cor.ambar }}>
                  {embaralhado(linha, frame, revela, `cod${i}`)}
                </div>
              );
            })}
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                left: `${varre}%`,
                width: 6,
                background: cor.lima,
                boxShadow: `0 0 40px 10px ${cor.lima}`,
                opacity: frame < 112 ? 0.9 : 0,
              }}
            />
          </div>
        </AbsoluteFill>

        {/* estatística por cima */}
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            flexDirection: "column",
            opacity: frame >= 132 ? 1 : 0,
          }}
        >
          <div
            style={{
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 330,
              lineHeight: 1,
              color: cor.lima,
              letterSpacing: -12,
              scale: estouro(frame, 132, 10),
              textShadow: "0 20px 80px rgba(0,0,0,0.9)",
            }}
          >
            99%
          </div>
          <div
            style={{
              fontFamily: titulo,
              fontSize: 60,
              color: cor.texto,
              textAlign: "center",
              whiteSpace: "nowrap",
              opacity: surge(frame, 140),
              textShadow: "0 10px 40px rgba(0,0,0,0.9)",
            }}
          >
            das funções de um jogo de tiro reconstruídas em C++
          </div>
          <div
            style={{
              marginTop: 30,
              fontFamily: mono,
              fontSize: 40,
              color: cor.fundo,
              background: cor.ambar,
              padding: "10px 26px",
              scale: estouro(frame, 168),
              rotate: `${(random("rot") - 0.5) * 4}deg`,
            }}
          >
            uma dúzia de agentes Claude Code + Codex em paralelo
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
