import React from "react";
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";
import { cena, naFala } from "./base";
import { Carimbo } from "./Cenas1";
import { Rede3D } from "./Rede3D";
import { Celular, Cursor, JanelaApp, Moeda, Predio, Relogio, Vilao } from "./svg";

// "Isso é um perigo, porque uma grande empresa é dona de um grande aplicativo,
//  ela deveria simplesmente receber por isso, né?"
export const CenaPerigo: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("perigo");
  const fPerigo = naFala("perigo", "perigo");
  const fEmpresa = naFala("perigo", "empresa");
  const fReceber = naFala("perigo", "receber");
  const fNe = naFala("perigo", "né");
  const piscar = frame < fEmpresa ? (Math.floor(frame / 6) % 2 ? 0.25 : 0.05) : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="alarme" em={fPerigo - 2} volume={0.5} />
      <Som nome="boom" em={fPerigo} volume={0.8} />
      <Som nome="whoosh" em={fEmpresa - 6} />
      {Array.from({ length: 8 }, (_, i) => (
        <Som key={i} nome="moeda" em={fReceber + i * 5} tom={1 + (i % 3) * 0.08} volume={0.55} />
      ))}
      <Som nome="pop" em={fNe} />
      <AbsoluteFill style={{ backgroundColor: cor.vermelho, opacity: piscar }} />
      {frame < fEmpresa - 6 ? (
        <Camera chaves={[{ f: 0, s: 1.2 }, { f: fPerigo, s: 1 }, { f: fEmpresa, s: 1.1 }]} tremidas={[fPerigo]}>
          <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", paddingBottom: 90 }}>
            <svg width={300} height={270} viewBox="0 0 100 90" style={{ scale: estouro(frame, fPerigo - 4, 10) }}>
              <path d="M50 4 L96 86 L4 86 Z" fill={cor.vermelho} stroke={cor.texto} strokeWidth={3} strokeLinejoin="round" />
              <rect x={46} y={30} width={8} height={32} rx={3} fill={cor.fundo} />
              <circle cx={50} cy={73} r={5} fill={cor.fundo} />
            </svg>
            <Glitch semente="perigo" picos={[[fPerigo, fPerigo + 6]]}
              style={{ fontFamily: titulo, fontWeight: 700, fontSize: 210, color: cor.vermelho, letterSpacing: -6, lineHeight: 1 }}>
              PERIGO
            </Glitch>
          </AbsoluteFill>
        </Camera>
      ) : (
        <Camera chaves={[{ f: fEmpresa - 6, s: 1.2 }, { f: fEmpresa + 6, s: 1 }, { f: fReceber, s: 1 }, { f: fReceber + 8, s: 1.12, x: 200 }, { f: dur, s: 1.15, x: 200 }]}>
          <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 260, paddingBottom: 110 }}>
            {/* usuários pagando */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 110px)", gap: 30, opacity: surge(frame, fEmpresa, 10) }}>
              {Array.from({ length: 9 }, (_, i) => (
                <svg key={i} width={110} height={110} viewBox="0 0 40 40" style={{ scale: estouro(frame, fEmpresa + i * 2, 8) }}>
                  <circle cx={20} cy={13} r={8} fill={cor.apagado} />
                  <path d="M5 38 C5 26 35 26 35 38 Z" fill={cor.apagado} />
                </svg>
              ))}
            </div>
            <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", scale: estouro(frame, fEmpresa, 12) }}>
              <Predio altura={460} />
              <div style={{ fontFamily: titulo, fontSize: 44, color: cor.texto, marginTop: 10 }}>dona do app</div>
            </div>
          </AbsoluteFill>
          {/* moedas voando dos usuários para a empresa */}
          {Array.from({ length: 14 }, (_, i) => {
            const em = fReceber + i * 3;
            const p = interpolate(frame, [em, em + 22], [0, 1], { ...preso, easing: Easing.inOut(Easing.quad) });
            const x0 = 460 + random(`mx${i}`) * 260;
            const y0 = 330 + random(`my${i}`) * 300;
            return (
              <div key={i} style={{ position: "absolute", left: x0 + (1260 - x0) * p, top: y0 + (450 - y0) * p - Math.sin(p * Math.PI) * 180,
                opacity: p > 0 && p < 1 ? 1 : 0, rotate: `${p * 720}deg` }}>
                <Moeda tamanho={64} />
              </div>
            );
          })}
          <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 230 }}>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 70, color: cor.ambar, opacity: surge(frame, fReceber, 8) }}>
              deveria receber por isso
            </div>
          </AbsoluteFill>
        </Camera>
      )}
    </AbsoluteFill>
  );
};

// "Mas se todo mundo agora começasse a clonar aplicativo em aplicativo,
//  cada pessoa consegue fazer ele em menos de 1 hora."
export const CenaUmaHora: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("umaHora");
  const fClonar = naFala("umaHora", "clonar");
  const fHora = naFala("umaHora", "hora");
  const voltas = interpolate(frame, [0, fHora], [0, 0.97], { ...preso, easing: Easing.in(Easing.quad) });
  const minutos = Math.max(0, Math.round(60 * (1 - voltas)));
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="tictac" em={0} volume={0.6} />
      <Som nome="tictac" em={60} volume={0.6} />
      {Array.from({ length: 10 }, (_, i) => (
        <Som key={i} nome="clique" em={fClonar + i * 4} tom={0.9 + i * 0.05} volume={0.45} />
      ))}
      <Som nome="carimbo" em={fHora} />
      <Som nome="boom" em={fHora} volume={0.6} />
      <Camera chaves={[{ f: 0, s: 1.1 }, { f: 10, s: 1 }, { f: fHora, s: 1.02 }, { f: fHora + 6, s: 1.14, x: -330 }, { f: dur, s: 1.18, x: -330 }]} tremidas={[fHora]}>
        <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 120, paddingBottom: 110 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
            <Relogio voltas={voltas} tamanho={460} />
            <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 64, color: cor.lima }}>
              {String(minutos).padStart(2, "0")}:00
            </div>
          </div>
          {/* grade de clones surgindo, "app em app" */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 170px)", gap: 22 }}>
            {Array.from({ length: 16 }, (_, i) => (
              <div key={i} style={{ scale: estouro(frame, fClonar + i * 2, 8) }}>
                <JanelaApp largura={170} titulo="" destaque={[cor.lima, cor.ciano, cor.ambar, "#ff4fa3"][i % 4]} />
              </div>
            ))}
          </div>
        </AbsoluteFill>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 110 }}>
          <Carimbo em={fHora} corFundo={cor.lima} tamanho={140} rot={-7}>
            &lt; 1 HORA
          </Carimbo>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

const Estrelas: React.FC<{ nota: number; corEstrela: string }> = ({ nota, corEstrela }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
    <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 80, color: corEstrela }}>{nota.toFixed(1).replace(".", ",")}</div>
    <svg width={260} height={52} viewBox="0 0 130 26">
      {Array.from({ length: 5 }, (_, i) => (
        <path key={i} transform={`translate(${i * 26} 0)`} d="M13 1 L16.5 9 L25 9.6 L18.5 15 L20.5 24 L13 19 L5.5 24 L7.5 15 L1 9.6 L9.5 9 Z"
          fill={i < Math.round(nota) ? corEstrela : "#2a2f3d"} />
      ))}
    </svg>
  </div>
);

// "E se a pessoa que fizer esse clone for mal-intencionada, ela com certeza vai acabar fazendo o
//  aplicativo melhor do que o original, criando uma situação que simplesmente não tem controle."
export const CenaMalIntencionada: React.FC<{ energia: number[]; de: number }> = ({ energia, de }) => {
  const frame = useCurrentFrame();
  const { dur } = cena("malIntencionada");
  const fMal = naFala("malIntencionada", "mal-intencionada");
  const fMelhor = naFala("malIntencionada", "melhor");
  const fCriando = naFala("malIntencionada", "criando");
  const fControle = naFala("malIntencionada", "controle");
  const pulso = energia[de + frame] ?? 0;
  const parte = frame < fMelhor - 8 ? 0 : frame < fCriando - 4 ? 1 : 2;
  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0405" }}>
      <Som nome="scratch" em={fMal - 4} volume={0.5} />
      <Som nome="boom" em={fMal} />
      <Som nome="whoosh" em={fMelhor - 8} />
      <Som nome="pop" em={fMelhor} />
      <Som nome="ding" em={fMelhor + 4} volume={0.4} />
      <Som nome="glitch" em={fCriando - 4} />
      <Som nome="glitch" em={fControle} />
      <Som nome="boom" em={fControle} volume={0.8} />
      <Som nome="alarme" em={fControle + 2} volume={0.35} />

      {parte === 0 && (
        <Camera chaves={[{ f: 0, s: 1.2 }, { f: 12, s: 1 }, { f: fMal, s: 1.02 }, { f: fMal + 6, s: 1.1, x: -60, y: -40 }, { f: fMelhor, s: 1.13, x: -60, y: -40 }]} tremidas={[fMal]}>
          <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 80, paddingBottom: 60 }}>
            <Vilao olhos={interpolate(frame, [fMal - 2, fMal + 3], [0, 1], preso) * (0.85 + Math.sin(frame / 3) * 0.15)} altura={620} />
            <div style={{ display: "flex", flexDirection: "column", opacity: surge(frame, 4, 10) }}>
              <div style={{ fontFamily: titulo, fontSize: 60, color: cor.apagado }}>e se quem clonar for</div>
              <Glitch semente="mal" picos={[[fMal, fMal + 5]]}
                style={{ fontFamily: titulo, fontWeight: 700, fontSize: 120, color: cor.vermelho, letterSpacing: -4, lineHeight: 1, opacity: frame >= fMal - 2 ? 1 : 0 }}>
                mal-intencionado?
              </Glitch>
            </div>
          </AbsoluteFill>
        </Camera>
      )}

      {parte === 1 && (
        <Camera chaves={[{ f: fMelhor - 8, s: 1.2 }, { f: fMelhor + 2, s: 1 }, { f: fCriando - 4, s: 1.05 }]}>
          <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 100, paddingBottom: 130 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 16, opacity: 0.7 }}>
              <div style={{ fontFamily: mono, fontSize: 40, color: cor.apagado }}>original</div>
              <JanelaApp largura={520} titulo="app_original" destaque={cor.apagado} />
              <Estrelas nota={4.1} corEstrela={cor.apagado} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 16, scale: estouro(frame, fMelhor - 4, 12) }}>
              <div style={{ fontFamily: mono, fontSize: 40, color: cor.lima }}>clone</div>
              <JanelaApp largura={600} titulo="app_clone_PRO" destaque={cor.lima} />
              <Estrelas nota={4.9} corEstrela={cor.lima} />
              <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 64, color: cor.fundo, background: cor.lima, padding: "6px 24px",
                alignSelf: "flex-start", rotate: "-3deg", scale: estouro(frame, fMelhor, 10) }}>
                MELHOR QUE O ORIGINAL
              </div>
            </div>
          </AbsoluteFill>
        </Camera>
      )}

      {parte === 2 && (
        <Camera chaves={[{ f: fCriando - 4, s: 1.3 }, { f: fCriando + 6, s: 1 }, { f: fControle, s: 1.05 }, { f: fControle + 6, s: 1.3 }, { f: dur, s: 1.4 }]}
          tremidas={[fCriando - 4, fControle, fControle + 10, fControle + 22]}>
          <AbsoluteFill>
            <Rede3D abertura={interpolate(frame, [fCriando, fControle + 6], [0.1, 1.4], { ...preso, easing: saida })}
              pulso={pulso} cor={cor.vermelho} corLinha="#ff8a3d" giro={4} distancia={9} />
          </AbsoluteFill>
          <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 120 }}>
            <Glitch semente="controle" picos={[[fControle, fControle + 8], [fControle + 18, fControle + 22]]}
              style={{ fontFamily: titulo, fontWeight: 700, fontSize: 200, color: cor.texto, letterSpacing: -6, lineHeight: 1,
                opacity: frame >= fControle - 2 ? 1 : 0, textShadow: "0 0 60px #000" }}>
              SEM CONTROLE
            </Glitch>
          </AbsoluteFill>
        </Camera>
      )}
    </AbsoluteFill>
  );
};

const ICONES_DADOS = ["senha", "fotos", "contatos", "cartão", "e-mail", "localização", "conversas", "PIX"];

// "Porque imagina: só você usa um aplicativo que é melhor que o original. E esse, infelizmente,
//  tem a capacidade de roubar todos os seus dados, tirar todo dinheiro do seu banco."
export const CenaRoubo: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("roubo");
  const fMelhor = naFala("roubo", "melhor");
  const fRoubar = naFala("roubo", "roubar");
  const fDinheiro = naFala("roubo", "dinheiro");
  const fBanco = naFala("roubo", "banco");
  const saldo = interpolate(frame, [fDinheiro - 4, fBanco + 10], [12480, 0], { ...preso, easing: Easing.in(Easing.cubic) });
  const alerta = frame >= fRoubar;
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="pop" em={2} />
      <Som nome="sino" em={fMelhor} volume={0.4} />
      <Som nome="glitch" em={fRoubar - 2} />
      <Som nome="whoosh" em={fRoubar} volume={0.7} />
      {Array.from({ length: 12 }, (_, i) => (
        <Som key={i} nome="tique" em={fDinheiro + i * 3} tom={1.4 - i * 0.04} volume={0.5} />
      ))}
      <Som nome="alarme" em={fBanco} volume={0.5} />
      <Som nome="erro" em={fBanco + 8} volume={0.5} />
      <AbsoluteFill style={{ backgroundColor: cor.vermelho, opacity: frame >= fBanco ? (Math.floor(frame / 5) % 2 ? 0.18 : 0.04) : 0 }} />
      <Camera
        chaves={[
          { f: 0, s: 1.15 },
          { f: 12, s: 1 },
          { f: fRoubar - 4, s: 1 },
          { f: fRoubar + 6, s: 1.08 },
          { f: fDinheiro - 4, s: 1.08 },
          { f: fDinheiro + 6, s: 1.3, x: 330, y: -40 },
          { f: dur, s: 1.36, x: 330, y: -40 },
        ]}
        tremidas={[fRoubar, fBanco]}
      >
        <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 160, paddingBottom: 110 }}>
          <div style={{ position: "relative" }}>
            <Celular altura={700}>
              <div style={{ width: "100%", height: "100%", background: alerta ? "#2a0a10" : "#0e1a14", display: "flex",
                flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 18, padding: 20 }}>
                <div style={{ width: 120, height: 120, borderRadius: 30, background: alerta ? cor.vermelho : cor.lima,
                  display: "flex", alignItems: "center", justifyContent: "center", fontFamily: titulo, fontWeight: 700, fontSize: 60, color: cor.fundo }}>
                  {alerta ? "!" : "★"}
                </div>
                <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 34, color: cor.texto, textAlign: "center" }}>
                  {alerta ? "enviando seus dados…" : "app clone PRO"}
                </div>
                <div style={{ fontFamily: mono, fontSize: 22, color: alerta ? cor.vermelho : cor.lima }}>
                  {alerta ? `${Math.min(100, Math.round(interpolate(frame, [fRoubar, fDinheiro], [3, 100], preso)))}%` : "melhor que o original"}
                </div>
              </div>
            </Celular>
            {/* dados saindo do celular */}
            {ICONES_DADOS.map((d, i) => {
              const em = fRoubar + i * 4;
              const p = interpolate(frame, [em, em + 30], [0, 1], { ...preso, easing: Easing.in(Easing.quad) });
              return (
                <div key={d} style={{ position: "absolute", left: 60 + p * (-620 + random(`dx${i}`) * 200), top: 200 + (random(`dy${i}`) - 0.5) * 700 * p,
                  opacity: p > 0 && p < 0.95 ? 1 : 0, fontFamily: mono, fontWeight: 700, fontSize: 30, color: cor.fundo,
                  background: cor.vermelho, padding: "4px 14px", borderRadius: 10, whiteSpace: "nowrap" }}>
                  {d}
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14, opacity: surge(frame, fDinheiro - 8, 8) }}>
            <div style={{ fontFamily: mono, fontSize: 40, color: cor.apagado }}>saldo no banco</div>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 130, letterSpacing: -4,
              color: saldo < 1 ? cor.vermelho : cor.texto }}>
              R$ {saldo.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 48, color: cor.vermelho, opacity: surge(frame, fBanco, 6) }}>
              PIX enviado · PIX enviado · PIX enviado
            </div>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "E aí, você é a favor ou contra?"
export const CenaFavorContra: React.FC = () => {
  const frame = useCurrentFrame();
  const fFavor = naFala("favorContra", "favor");
  const fContra = naFala("favorContra", "contra");
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="pop" em={fFavor} />
      <Som nome="pop" em={fContra} tom={0.8} />
      <Camera chaves={[{ f: 0, s: 1.1 }, { f: 12, s: 1 }, { f: 42, s: 1.05 }]}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 50, paddingBottom: 120 }}>
          <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 90, color: cor.texto }}>e aí, você é…</div>
          <div style={{ display: "flex", gap: 60 }}>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 110, color: cor.fundo, background: cor.lima, padding: "20px 60px",
              borderRadius: 30, scale: estouro(frame, fFavor - 2, 8) }}>A FAVOR</div>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 110, color: cor.texto, background: cor.vermelho, padding: "20px 60px",
              borderRadius: 30, scale: estouro(frame, fContra - 2, 8) }}>CONTRA</div>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "Deixa sua opinião nos comentários e se inscreve no canal pra ajudar."
export const CenaInscreva: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("inscreva");
  const fCom = naFala("inscreva", "comentários");
  const fInsc = naFala("inscreva", "inscreve");
  const clique = fInsc + 6;
  const inscrito = frame >= clique;
  const comentario = "sou contra! quem cria tem que receber…";
  const cx = interpolate(frame, [fInsc - 14, clique], [1500, 1080], { ...preso, easing: saida });
  const cy = interpolate(frame, [fInsc - 14, clique], [980, 690], { ...preso, easing: saida });
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="pop" em={2} />
      <Som nome="digitacao" em={fCom - 6} volume={0.5} />
      <Som nome="clique" em={clique} volume={1} />
      <Som nome="sino" em={clique + 3} volume={0.6} />
      <Som nome="ding" em={clique + 20} volume={0.4} />
      <Camera chaves={[{ f: 0, s: 1.1 }, { f: 12, s: 1 }, { f: clique, s: 1.03 }, { f: clique + 5, s: 1.12, y: 120 }, { f: dur, s: 1.15, y: 120 }]} tremidas={[clique]}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 60, paddingBottom: 120 }}>
          <div style={{ display: "flex", gap: 24, alignItems: "flex-start", width: 1200, background: cor.painel, border: `2px solid ${cor.borda}`,
            borderRadius: 28, padding: "30px 36px", opacity: surge(frame, 0, 10) }}>
            <div style={{ width: 80, height: 80, borderRadius: 40, background: cor.ciano, flexShrink: 0 }} />
            <div>
              <div style={{ fontFamily: mono, fontSize: 30, color: cor.apagado }}>@voce · agora</div>
              <div style={{ fontFamily: titulo, fontSize: 50, color: cor.texto, minHeight: 64 }}>
                {comentario.slice(0, Math.max(0, Math.floor((frame - fCom + 6) * 1.3)))}
                <span style={{ opacity: Math.floor(frame / 8) % 2 ? 1 : 0, color: cor.lima }}>▍</span>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 70, color: inscrito ? cor.texto : "#fff",
              background: inscrito ? "#2a2f3d" : cor.vermelho, padding: "20px 56px", borderRadius: 999,
              scale: inscrito ? interpolate(frame, [clique, clique + 4, clique + 10], [0.88, 1.08, 1], preso) : estouro(frame, fInsc - 16, 10) }}>
              {inscrito ? "INSCRITO ✓" : "INSCREVA-SE"}
            </div>
            <svg width={90} height={90} viewBox="0 0 24 24" style={{ rotate: `${inscrito ? Math.sin((frame - clique) / 2) * 25 * Math.exp(-(frame - clique) / 12) : 0}deg`,
              opacity: surge(frame, fInsc - 10, 8) }}>
              <path d="M12 2 C8 2 6 5 6 9 L6 14 L4 17 L20 17 L18 14 L18 9 C18 5 16 2 12 2 Z M10 19 a2 2 0 0 0 4 0 Z" fill={inscrito ? cor.ambar : cor.apagado} />
            </svg>
          </div>
        </AbsoluteFill>
        <div style={{ position: "absolute", left: cx, top: cy, opacity: frame >= fInsc - 14 ? 1 : 0,
          scale: frame >= clique && frame < clique + 4 ? 0.85 : 1 }}>
          <Cursor tamanho={80} />
        </div>
      </Camera>
      <AbsoluteFill style={{ backgroundColor: "black", opacity: interpolate(frame, [dur - 15, dur], [0, 1], preso) }} />
    </AbsoluteFill>
  );
};
