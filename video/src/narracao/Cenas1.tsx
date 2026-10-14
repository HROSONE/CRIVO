import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";
import { cena, naFala } from "./base";
import { GradeClones3D } from "./GradeClones3D";
import { Carteira, Caveira, JanelaApp } from "./svg";

const Carimbo: React.FC<{ em: number; corFundo?: string; children: React.ReactNode; rot?: number; tamanho?: number }> = ({
  em,
  corFundo = cor.vermelho,
  children,
  rot = -6,
  tamanho = 120,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        fontFamily: titulo,
        fontWeight: 700,
        fontSize: tamanho,
        lineHeight: 1,
        color: corFundo,
        border: `10px solid ${corFundo}`,
        borderRadius: 18,
        padding: "8px 34px",
        rotate: `${rot}deg`,
        scale: interpolate(frame, [em, em + 6], [2.6, 1], { ...preso, easing: Easing.in(Easing.quad) }),
        opacity: frame >= em ? 1 : 0,
        letterSpacing: -2,
        background: "rgba(7,8,12,0.75)",
      }}
    >
      {children}
    </div>
  );
};
export { Carimbo };

// "Na última semana, milhares de programas e softwares simplesmente foram clonados pela IA."
export const CenaClonados: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("clonados");
  const fMilhares = naFala("clonados", "milhares");
  const fClonados = naFala("clonados", "clonados");
  const quantos = Math.floor(
    interpolate(frame, [0, fMilhares, fMilhares + 25, fClonados, dur], [1, 1, 40, 300, 576], {
      ...preso,
      easing: Easing.in(Easing.quad),
    }),
  );
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="pop" em={2} />
      {Array.from({ length: 14 }, (_, i) => (
        <Som key={i} nome="clique" em={fMilhares + Math.round(Math.sqrt(i) * 12)} tom={0.8 + i * 0.05} volume={0.5} />
      ))}
      <Som nome="boom" em={fClonados} />
      <Som nome="carimbo" em={fClonados} />
      <Camera chaves={[{ f: 0, s: 1 }, { f: dur, s: 1.06 }]} tremidas={[fClonados]}>
        <GradeClones3D
          quantos={quantos}
          recuo={interpolate(frame, [0, fMilhares, dur], [5, 7, 34], { ...preso, easing: Easing.inOut(Easing.cubic) })}
        />
      </Camera>
      <AbsoluteFill style={{ alignItems: "center", paddingTop: 90 }}>
        <div
          style={{
            fontFamily: mono,
            fontSize: 44,
            color: cor.fundo,
            background: cor.texto,
            padding: "8px 24px",
            opacity: surge(frame, 0, 6),
          }}
        >
          NA ÚLTIMA SEMANA
        </div>
        <div
          style={{
            marginTop: 20,
            fontFamily: titulo,
            fontWeight: 700,
            fontSize: 110,
            color: cor.texto,
            letterSpacing: -3,
            textShadow: "0 10px 50px #000",
            scale: estouro(frame, fMilhares, 10),
          }}
        >
          milhares de programas
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingTop: 160 }}>
        <Carimbo em={fClonados} tamanho={150}>
          CLONADOS
        </Carimbo>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// "É praticamente a pirataria da IA."
export const CenaPirataria: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("pirataria");
  const fPir = naFala("pirataria", "pirataria");
  return (
    <AbsoluteFill style={{ backgroundColor: "#050607" }}>
      <Som nome="glitch" em={0} volume={0.6} />
      <Som nome="boom" em={fPir} />
      <Camera chaves={[{ f: 0, s: 1.25 }, { f: 8, s: 1 }, { f: fPir, s: 1.02 }, { f: fPir + 5, s: 1.12 }, { f: dur, s: 1.18 }]} tremidas={[fPir]}>
        <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 60, paddingBottom: 80 }}>
          <Caveira p={interpolate(frame, [0, fPir + 6], [0, 1], preso)} tamanho={460} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontFamily: titulo, fontSize: 64, color: cor.apagado }}>é praticamente a</div>
            <Glitch
              semente="pirataria"
              picos={[[fPir, fPir + 5]]}
              style={{ fontFamily: titulo, fontWeight: 700, fontSize: 190, lineHeight: 0.95, color: cor.lima, letterSpacing: -6 }}
            >
              PIRATARIA
            </Glitch>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 130, color: cor.texto, opacity: surge(frame, fPir + 4, 6) }}>
              da IA
            </div>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "Infelizmente, essa prática vai ficar cada vez mais comum, porque, imagina:"
export const CenaComum: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("comum");
  const p = interpolate(frame, [4, dur - 10], [0, 1], { ...preso, easing: Easing.in(Easing.quad) });
  const L = 1300;
  const A = 560;
  const pontos = Array.from({ length: 60 }, (_, i) => {
    const x = i / 59;
    return `${i ? "L" : "M"}${(x * L).toFixed(1)},${(A - (Math.exp(x * 4) - 1) / (Math.exp(4) - 1) * A).toFixed(1)}`;
  }).join(" ");
  const ponta = { x: p * L, y: A - ((Math.exp(p * 4) - 1) / (Math.exp(4) - 1)) * A };
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="riser" em={0} volume={0.35} />
      <Som nome="whoosh" em={dur - 10} />
      <Camera chaves={[{ f: 0, s: 1 }, { f: dur - 14, s: 1.08 }, { f: dur, s: 1.9, x: 520, y: -260 }]}>
        <AbsoluteFill style={{ padding: "110px 200px", flexDirection: "column" }}>
          <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 92, color: cor.texto, letterSpacing: -2 }}>
            cada vez mais <span style={{ color: cor.vermelho }}>comum</span>
          </div>
          <svg width={L} height={A + 40} style={{ marginTop: 50, overflow: "visible" }}>
            {[0, 0.25, 0.5, 0.75, 1].map((v) => (
              <line key={v} x1={0} x2={L} y1={A - v * A} y2={A - v * A} stroke={cor.borda} strokeWidth={2} />
            ))}
            <path d={pontos} fill="none" stroke={cor.vermelho} strokeWidth={12} strokeLinecap="round"
              pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
            <circle cx={ponta.x} cy={ponta.y} r={18} fill={cor.vermelho} />
            <circle cx={ponta.x} cy={ponta.y} r={18 + (frame % 15) * 2.4} fill="none" stroke={cor.vermelho}
              strokeWidth={3} opacity={1 - (frame % 15) / 15} />
            <text x={0} y={A + 40} fill={cor.apagado} fontFamily={mono} fontSize={30}>clones de apps</text>
          </svg>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "só você tem aquele programa que você gosta muito, pra ele tem assinatura e você não tem dinheiro pra pagar."
export const CenaAssinatura: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("assinatura");
  const fAss = naFala("assinatura", "assinatura");
  const fDin = naFala("assinatura", "dinheiro");
  const desce = interpolate(frame, [fAss - 4, fAss + 8], [-700, 0], { ...preso, easing: Easing.out(Easing.back(1.4)) });
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="pop" em={4} />
      <Som nome="whoosh-desce" em={fAss - 4} />
      <Som nome="carimbo" em={fAss + 6} />
      <Som nome="erro" em={fDin} volume={0.6} />
      <Camera
        chaves={[
          { f: 0, s: 1.15, x: -250 },
          { f: 12, s: 1, x: -250 },
          { f: fDin - 4, s: 1, x: -250 },
          { f: fDin + 6, s: 1.25, x: 380 },
          { f: dur, s: 1.3, x: 380 },
        ]}
        tremidas={[fAss + 6]}
      >
        <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 120, paddingBottom: 90 }}>
          <div style={{ position: "relative", scale: estouro(frame, 2, 12) }}>
            <JanelaApp largura={720} titulo="seu programa favorito" destaque={cor.ciano} />
            <div style={{ position: "absolute", top: 120, left: 60, fontSize: 90, color: cor.vermelho, scale: 1 + Math.sin(frame / 4) * 0.06 }}>
              ♥
            </div>
            {/* paywall */}
            <div
              style={{
                position: "absolute",
                inset: "60px 0 0 0",
                borderRadius: "0 0 22px 22px",
                background: "rgba(7,8,12,0.88)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                translate: `0 ${desce}px`,
                opacity: frame >= fAss - 4 ? 1 : 0,
              }}
            >
              <svg width={110} height={120} viewBox="0 0 44 48" fill="none" stroke={cor.ambar} strokeWidth={4}>
                <path d="M10 22 V14 a12 12 0 0 1 24 0 V22" />
                <rect x={4} y={22} width={36} height={24} rx={5} fill={cor.ambar} />
              </svg>
              <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 64, color: cor.texto }}>assinatura</div>
              <div style={{ fontFamily: mono, fontSize: 48, color: cor.ambar, marginTop: 8 }}>R$ 99,90/mês</div>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: surge(frame, fDin - 6, 8) }}>
            <Carteira abre={interpolate(frame, [fDin, fDin + 10], [0, 1], { ...preso, easing: saida })} />
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 96, color: cor.vermelho, marginTop: 10 }}>
              R$ 0,00
            </div>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
