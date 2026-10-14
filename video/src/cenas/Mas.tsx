import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, saida, Som } from "../comp/util";
import { cor, mono, titulo } from "../tema";

const AVISOS = [
  { em: 50, tag: "ALPHA", texto: "bugs e longe da paridade com os originais" },
  { em: 82, tag: "JURÍDICO", texto: "interfaces quase 1:1 com as de Adobe e Microsoft" },
  { em: 114, tag: "GOLPE", texto: "cópia falsa do REA com um “.exe” que seria trojan" },
  { em: 146, tag: "LIMITE", texto: "o REA diz não a DRM, anticheat e licenças" },
];

export const Mas: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: "#0c0507" }}>
      <Som nome="scratch" em={0} />
      {AVISOS.map((a) => (
        <Som key={a.tag} nome="erro" em={a.em} volume={0.7} />
      ))}
      <Som nome="boom" em={114} volume={0.6} />
      <Som nome="whoosh" em={215} />

      <Camera
        chaves={[
          { f: 0, s: 1.6 },
          { f: 8, s: 1.6 },
          { f: 40, s: 1 },
          { f: 108, s: 1 },
          { f: 118, s: 1.4, y: 130 },
          { f: 140, s: 1.4, y: 130 },
          { f: 150, s: 1 },
          { f: 215, s: 1.02 },
          { f: 240, s: 2, y: 300 },
        ]}
        tremidas={[0, 114]}
      >
        <AbsoluteFill style={{ padding: "120px 150px", flexDirection: "column", gap: 34 }}>
          <Glitch
            semente="mas"
            picos={[
              [0, 8],
              [114, 117],
            ]}
            style={{
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 200,
              lineHeight: 0.9,
              color: cor.vermelho,
              letterSpacing: -6,
              marginBottom: 20,
            }}
          >
            MAS…
          </Glitch>
          {AVISOS.map((a) => (
            <div
              key={a.tag}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 30,
                opacity: interpolate(frame, [a.em, a.em + 4], [0, 1], preso),
                translate: `${interpolate(frame, [a.em, a.em + 12], [-120, 0], { ...preso, easing: saida })}px 0`,
              }}
            >
              <div
                style={{
                  minWidth: 260,
                  textAlign: "center",
                  fontFamily: mono,
                  fontWeight: 700,
                  fontSize: 40,
                  color: cor.fundo,
                  background: a.tag === "GOLPE" ? cor.vermelho : cor.ambar,
                  padding: "10px 18px",
                  scale: estouro(frame, a.em, 10),
                }}
              >
                {a.tag}
              </div>
              <div style={{ fontFamily: titulo, fontSize: 52, color: cor.texto }}>{a.texto}</div>
            </div>
          ))}
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
