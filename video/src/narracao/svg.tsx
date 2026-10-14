import React from "react";
import { cor, mono, titulo } from "../tema";

/** Traço que se desenha: passe `p` de 0 a 1. */
export const tracado = (p: number) => ({
  pathLength: 1,
  strokeDasharray: 1,
  strokeDashoffset: 1 - Math.max(0, Math.min(1, p)),
});

/** Janela de aplicativo genérica. `oco` desenha só o contorno tracejado. */
export const JanelaApp: React.FC<{
  largura?: number;
  titulo?: string;
  destaque?: string;
  oco?: boolean;
  desenho?: number;
  children?: React.ReactNode;
}> = ({ largura = 560, titulo: nome = "app", destaque = cor.ciano, oco = false, desenho = 1, children }) => {
  const a = largura * 0.68;
  const traco = oco ? { strokeDasharray: "14 10" } : tracado(desenho);
  return (
    <svg width={largura} height={a} viewBox={`0 0 ${largura} ${a}`} style={{ overflow: "visible" }}>
      <rect x={2} y={2} width={largura - 4} height={a - 4} rx={22} fill={oco ? "none" : cor.painel}
        stroke={destaque} strokeWidth={4} {...traco} />
      <line x1={2} x2={largura - 2} y1={56} y2={56} stroke={destaque} strokeWidth={3} opacity={desenho} />
      {[0, 1, 2].map((i) => (
        <circle key={i} cx={34 + i * 30} cy={29} r={9} opacity={desenho}
          fill={oco ? "none" : [cor.vermelho, cor.ambar, cor.lima][i]} stroke={destaque} strokeWidth={oco ? 2 : 0} />
      ))}
      <text x={largura / 2} y={38} fill={cor.apagado} fontFamily={mono} fontSize={24} textAnchor="middle" opacity={desenho}>
        {nome}
      </text>
      {!oco && (
        <g opacity={desenho}>
          <rect x={32} y={84} width={largura * 0.32} height={a - 120} rx={12} fill={destaque} opacity={0.18} />
          {[0, 1, 2, 3].map((i) => (
            <rect key={i} x={largura * 0.4} y={90 + i * ((a - 130) / 4)} width={largura * (0.5 - i * 0.07)}
              height={22} rx={11} fill={destaque} opacity={0.35} />
          ))}
        </g>
      )}
      {children}
    </svg>
  );
};

export const Caveira: React.FC<{ p: number; tamanho?: number; corTraco?: string }> = ({ p, tamanho = 420, corTraco = cor.lima }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 200 200" fill="none" stroke={corTraco} strokeWidth={5}
    strokeLinecap="round" strokeLinejoin="round">
    <path d="M60 150 L140 190 M140 150 L60 190" {...tracado(p * 1.4 - 0.4)} />
    <path d="M100 20 C55 20 40 55 45 85 C48 100 60 105 62 118 L62 135 L138 135 L138 118 C140 105 152 100 155 85 C160 55 145 20 100 20 Z" {...tracado(p * 1.3)} />
    <circle cx={78} cy={82} r={14} {...tracado(p * 1.5 - 0.3)} />
    <circle cx={122} cy={82} r={14} {...tracado(p * 1.5 - 0.3)} />
    <path d="M100 98 L92 114 L108 114 Z" {...tracado(p * 1.6 - 0.5)} />
    <path d="M78 135 L78 122 M92 135 L92 122 M108 135 L108 122 M122 135 L122 122" {...tracado(p * 1.6 - 0.6)} />
    {/* trilhas de circuito */}
    <path d="M45 85 L15 85 L15 60 M155 85 L185 85 L185 110 M100 20 L100 5" strokeWidth={3} {...tracado(p * 1.8 - 0.8)} />
    <circle cx={15} cy={58} r={4} fill={corTraco} opacity={p > 0.9 ? 1 : 0} />
    <circle cx={185} cy={112} r={4} fill={corTraco} opacity={p > 0.9 ? 1 : 0} />
  </svg>
);

export const Carteira: React.FC<{ abre: number }> = ({ abre }) => (
  <svg width={360} height={280} viewBox="0 0 180 140" fill="none" strokeWidth={5} strokeLinejoin="round">
    <rect x={10} y={30} width={160} height={100} rx={14} stroke={cor.ambar} fill="#1c1408" />
    <path d={`M10 ${50 - abre * 30} L150 ${50 - abre * 30} L150 30`} stroke={cor.ambar} />
    <rect x={120} y={65} width={50} height={32} rx={8} stroke={cor.ambar} fill={cor.fundo} />
    <circle cx={138} cy={81} r={5} fill={cor.ambar} />
    {/* traça saindo da carteira vazia */}
    <g opacity={abre} transform={`translate(${60 + abre * 10} ${10 - abre * 30})`}>
      <path d="M0 10 Q-14 -4 -20 10 Q-14 18 0 10 Q14 -4 20 10 Q14 18 0 10" stroke={cor.apagado} strokeWidth={2.5} />
    </g>
  </svg>
);

export const Plugue: React.FC<{ largura?: number }> = ({ largura = 360 }) => (
  <svg width={largura} height={largura * 0.5} viewBox="0 0 200 100" fill="none" strokeLinecap="round">
    <path d="M0 50 C40 50 50 50 70 50" stroke={cor.apagado} strokeWidth={8} />
    <rect x={70} y={22} width={80} height={56} rx={12} fill={cor.ciano} />
    <text x={110} y={58} fill={cor.fundo} fontFamily={titulo} fontWeight={700} fontSize={22} textAnchor="middle">MCP</text>
    <rect x={150} y={34} width={36} height={9} rx={3} fill={cor.texto} />
    <rect x={150} y={57} width={36} height={9} rx={3} fill={cor.texto} />
  </svg>
);

export const Predio: React.FC<{ altura?: number }> = ({ altura = 460 }) => (
  <svg width={altura * 0.6} height={altura} viewBox="0 0 120 200" fill="none" stroke={cor.ciano} strokeWidth={3}>
    <rect x={10} y={20} width={100} height={178} fill="#0b1a22" />
    {Array.from({ length: 24 }, (_, i) => (
      <rect key={i} x={22 + (i % 4) * 22} y={34 + Math.floor(i / 4) * 24} width={12} height={14}
        fill={i % 3 === 0 ? cor.ciano : "none"} strokeWidth={1.5} opacity={0.8} />
    ))}
    <rect x={46} y={168} width={28} height={30} fill={cor.ciano} />
    <rect x={30} y={2} width={60} height={18} rx={4} fill={cor.ciano} stroke="none" />
    <text x={60} y={15} fill={cor.fundo} fontFamily={mono} fontSize={11} fontWeight={700} textAnchor="middle" stroke="none">BIG TECH</text>
  </svg>
);

export const Moeda: React.FC<{ tamanho?: number }> = ({ tamanho = 60 }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 40 40">
    <circle cx={20} cy={20} r={18} fill={cor.ambar} stroke="#a86a00" strokeWidth={3} />
    <text x={20} y={27} fontFamily={titulo} fontWeight={700} fontSize={20} textAnchor="middle" fill="#6b4300">$</text>
  </svg>
);

export const Relogio: React.FC<{ voltas: number; tamanho?: number }> = ({ voltas, tamanho = 420 }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 200 200">
    <circle cx={100} cy={100} r={90} fill={cor.painel} stroke={cor.lima} strokeWidth={6} />
    {Array.from({ length: 12 }, (_, i) => {
      const a = (i / 12) * Math.PI * 2;
      return <line key={i} x1={100 + Math.sin(a) * 72} y1={100 - Math.cos(a) * 72} x2={100 + Math.sin(a) * 82}
        y2={100 - Math.cos(a) * 82} stroke={cor.texto} strokeWidth={i % 3 === 0 ? 6 : 3} strokeLinecap="round" />;
    })}
    {/* setor de tempo já gasto */}
    <path d={(() => {
      const f = Math.min(voltas, 0.999);
      const a = f * Math.PI * 2;
      return `M100 100 L100 30 A70 70 0 ${f > 0.5 ? 1 : 0} 1 ${100 + Math.sin(a) * 70} ${100 - Math.cos(a) * 70} Z`;
    })()} fill={cor.lima} opacity={0.25} />
    <line x1={100} y1={100} x2={100 + Math.sin(voltas * Math.PI * 2) * 66} y2={100 - Math.cos(voltas * Math.PI * 2) * 66}
      stroke={cor.lima} strokeWidth={6} strokeLinecap="round" />
    <line x1={100} y1={100} x2={100 + Math.sin(voltas * Math.PI * 24) * 50} y2={100 - Math.cos(voltas * Math.PI * 24) * 50}
      stroke={cor.texto} strokeWidth={4} strokeLinecap="round" />
    <circle cx={100} cy={100} r={8} fill={cor.lima} />
  </svg>
);

export const Vilao: React.FC<{ olhos: number; altura?: number }> = ({ olhos, altura = 560 }) => (
  <svg width={altura * 0.8} height={altura} viewBox="0 0 160 200">
    <defs>
      <radialGradient id="brilho">
        <stop offset="0%" stopColor={cor.vermelho} stopOpacity={1} />
        <stop offset="100%" stopColor={cor.vermelho} stopOpacity={0} />
      </radialGradient>
    </defs>
    <path d="M80 8 C35 8 22 60 24 100 C10 130 4 170 0 200 L160 200 C156 170 150 130 136 100 C138 60 125 8 80 8 Z"
      fill="#14070a" stroke={cor.vermelho} strokeWidth={2.5} />
    <path d="M80 40 C56 40 48 70 50 96 C54 118 66 128 80 128 C94 128 106 118 110 96 C112 70 104 40 80 40 Z" fill="#000" />
    <g opacity={olhos}>
      <circle cx={67} cy={90} r={16} fill="url(#brilho)" />
      <circle cx={93} cy={90} r={16} fill="url(#brilho)" />
      <ellipse cx={67} cy={90} rx={7} ry={3.5} fill="#ffd0d8" />
      <ellipse cx={93} cy={90} rx={7} ry={3.5} fill="#ffd0d8" />
    </g>
  </svg>
);

export const Celular: React.FC<{ altura?: number; children?: React.ReactNode }> = ({ altura = 640, children }) => (
  <div style={{ position: "relative", width: altura * 0.5, height: altura }}>
    <svg width={altura * 0.5} height={altura} viewBox="0 0 160 320" style={{ position: "absolute", inset: 0 }}>
      <rect x={3} y={3} width={154} height={314} rx={26} fill={cor.painel} stroke={cor.borda} strokeWidth={5} />
      <rect x={58} y={12} width={44} height={10} rx={5} fill={cor.fundo} />
    </svg>
    <div style={{ position: "absolute", inset: `${altura * 0.08}px ${altura * 0.035}px`, overflow: "hidden", borderRadius: 18 }}>
      {children}
    </div>
  </div>
);

export const Cursor: React.FC<{ tamanho?: number }> = ({ tamanho = 70 }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 24 24">
    <path d="M4 2 L4 20 L9 15 L12.5 22 L15.5 20.5 L12 13.5 L19 13.5 Z" fill="#fff" stroke="#000" strokeWidth={1.4} strokeLinejoin="round" />
  </svg>
);
