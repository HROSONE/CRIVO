import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, Som } from "../comp/util";
import { cor, mono, titulo } from "../tema";

const linhaHex = (i: number) =>
  Array.from({ length: 24 }, (_, j) =>
    Math.floor(random(`hex${i}-${j}`) * 256)
      .toString(16)
      .padStart(2, "0")
      .toUpperCase(),
  ).join(" ");

export const Gancho: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo, overflow: "hidden" }}>
      <Som nome="boom" em={0} />
      <Som nome="glitch" em={0} volume={0.7} />
      <Som nome="glitch" em={14} volume={0.8} />
      <Som nome="pop" em={48} />
      <Som nome="whoosh" em={100} />

      {/* despejo hexadecimal rolando ao fundo */}
      <AbsoluteFill
        style={{
          fontFamily: mono,
          fontSize: 30,
          lineHeight: "44px",
          color: cor.lima,
          opacity: 0.1,
          padding: 40,
          transform: `translateY(${-frame * 6}px)`,
          whiteSpace: "pre",
        }}
      >
        {Array.from({ length: 60 }, (_, i) => (
          <div key={i}>
            {(i * 16).toString(16).padStart(8, "0")}  {linhaHex(i)}
          </div>
        ))}
      </AbsoluteFill>

      <Camera
        chaves={[
          { f: 0, s: 1.25 },
          { f: 10, s: 1 },
          { f: 85, s: 1.08 },
          { f: 120, s: 2.6, y: 40 },
        ]}
        tremidas={[0, 14]}
      >
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            fontFamily: titulo,
            fontWeight: 700,
            textAlign: "center",
          }}
        >
          <Glitch
            semente="eng"
            picos={[
              [0, 6],
              [40, 42],
              [96, 100],
            ]}
            style={{ fontSize: 180, lineHeight: 1, letterSpacing: -4, color: cor.texto }}
          >
            ENGENHARIA
          </Glitch>
          <div style={{ opacity: frame >= 14 ? 1 : 0 }}>
            <Glitch
              semente="rev"
              picos={[
                [14, 20],
                [70, 72],
              ]}
              style={{ fontSize: 180, lineHeight: 1, letterSpacing: -4, color: cor.lima }}
            >
              REVERSA
            </Glitch>
          </div>
          <div
            style={{
              marginTop: 50,
              fontFamily: mono,
              fontSize: 46,
              fontWeight: 700,
              color: cor.fundo,
              background: cor.texto,
              padding: "10px 28px",
              scale: estouro(frame, 48),
              rotate: `${interpolate(frame, [48, 60], [-8, -2], preso)}deg`,
            }}
          >
            O QUE ROLOU NOS ÚLTIMOS 7 DIAS
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
