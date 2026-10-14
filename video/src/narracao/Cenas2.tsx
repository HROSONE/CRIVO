import React from "react";
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { Camera } from "../comp/Camera";
import { Glitch } from "../comp/Glitch";
import { estouro, preso, saida, Som, surge } from "../comp/util";
import { cor, mono, titulo } from "../tema";
import { cena, naFala } from "./base";
import { Carimbo } from "./Cenas1";
import { CAMADAS, Camadas3D, projetarCamadas } from "./Camadas3D";
import { Rede3D } from "./Rede3D";
import { JanelaApp, Plugue } from "./svg";

const digitado = (texto: string, frame: number, em: number, porQuadro = 1.2) =>
  texto.slice(0, Math.max(0, Math.floor((frame - em) * porQuadro)));

// "Como é que você vai resistir à tentação de simplesmente pegar o MCP, colocar na sua IA
//  e pedir pra ela recriar aquele aplicativo ali do zero pra você usar?"
export const CenaTentacao: React.FC<{ energia: number[]; de: number }> = ({ energia, de }) => {
  const frame = useCurrentFrame();
  const { dur } = cena("tentacao");
  const fTent = naFala("tentacao", "tentação");
  const fMcp = naFala("tentacao", "mcp");
  const fColocar = naFala("tentacao", "colocar");
  const fRecriar = naFala("tentacao", "recriar");
  const fZero = naFala("tentacao", "zero");
  const pulso = energia[de + frame] ?? 0;
  const pedido = "recria esse app do zero pra mim";
  const encaixe = interpolate(frame, [fColocar - 4, fColocar + 8], [-520, 0], { ...preso, easing: Easing.out(Easing.back(1.2)) });
  const ligado = frame >= fColocar + 8;
  const construcao = interpolate(frame, [fZero - 6, dur - 12], [0, 1], preso);
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} volume={0.6} />
      <Som nome="boom" em={fTent} volume={0.7} />
      <Som nome="pop" em={fMcp} />
      <Som nome="whoosh" em={fColocar - 4} volume={0.7} />
      <Som nome="clique" em={fColocar + 8} volume={1} />
      <Som nome="ding" em={fColocar + 10} volume={0.4} />
      <Som nome="digitacao" em={fRecriar - 6} volume={0.6} />
      <Som nome="riser" em={fZero - 6} volume={0.3} />
      <Som nome="ding" em={dur - 14} volume={0.5} />

      {/* 1) "tentação" */}
      {frame < fMcp - 2 && (
        <Camera chaves={[{ f: 0, s: 1.1 }, { f: fTent, s: 1 }, { f: fMcp, s: 1.15 }]} tremidas={[fTent]}>
          <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", paddingBottom: 80 }}>
            <div style={{ fontFamily: titulo, fontSize: 70, color: cor.apagado, opacity: surge(frame, 0, 8) }}>
              como resistir à
            </div>
            <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 220, color: cor.ambar, letterSpacing: -8, lineHeight: 1, scale: estouro(frame, fTent, 10) }}>
              tentação?
            </div>
          </AbsoluteFill>
        </Camera>
      )}

      {/* 2) MCP + IA + pedido + app renascendo */}
      {frame >= fMcp - 2 && (
        <Camera
          chaves={[
            { f: fMcp - 2, s: 1.3, x: -300 },
            { f: fMcp + 10, s: 1.05, x: -200 },
            { f: fRecriar - 6, s: 1.05, x: -200 },
            { f: fRecriar + 4, s: 1 },
            { f: fZero, s: 1 },
            { f: fZero + 8, s: 1.2, x: 380 },
            { f: dur, s: 1.25, x: 380 },
          ]}
        >
          <AbsoluteFill>
            {/* cérebro da IA à esquerda (3D, pulsa com a voz) */}
            <div style={{ position: "absolute", left: 0, top: 0, width: 1000, height: 1080 }}>
              <Rede3D largura={1000} altura={1080} pulso={ligado ? pulso : 0.1} distancia={8}
                cor={ligado ? cor.lima : "#5b6478"} corLinha={ligado ? cor.ciano : "#3a4152"} />
            </div>
            <div style={{ position: "absolute", left: 360, top: 110, fontFamily: mono, fontSize: 40, color: ligado ? cor.lima : cor.apagado }}>
              sua IA
            </div>
            {/* plugue MCP entrando pela esquerda até a IA */}
            <div style={{ position: "absolute", left: 40, top: 470, translate: `${encaixe}px 0`, opacity: surge(frame, fMcp, 6) }}>
              <Plugue largura={420} />
            </div>
            {/* pedido digitado */}
            <div
              style={{
                position: "absolute",
                left: 1000,
                top: 170,
                width: 820,
                background: cor.painel,
                border: `2px solid ${cor.borda}`,
                borderRadius: 24,
                padding: "26px 32px",
                opacity: surge(frame, fRecriar - 8, 8),
              }}
            >
              <div style={{ fontFamily: mono, fontSize: 28, color: cor.apagado }}>você ›</div>
              <div style={{ fontFamily: mono, fontSize: 42, color: cor.texto, minHeight: 56 }}>
                {digitado(pedido, frame, fRecriar - 6)}
                <span style={{ opacity: Math.floor(frame / 8) % 2 ? 1 : 0, color: cor.lima }}>▍</span>
              </div>
            </div>
            {/* app sendo recriado do zero */}
            <div style={{ position: "absolute", left: 1090, top: 400, opacity: frame >= fZero - 8 ? 1 : 0 }}>
              <JanelaApp largura={640} titulo="clone_v1" destaque={cor.lima} desenho={construcao} />
              <div style={{ position: "absolute", right: 10, top: -50, fontFamily: titulo, fontWeight: 700, fontSize: 52,
                color: cor.lima, scale: estouro(frame, fZero, 10) }}>
                do zero
              </div>
            </div>
          </AbsoluteFill>
        </Camera>
      )}
    </AbsoluteFill>
  );
};

// "Diga, gente: não, tá falando da IA simplesmente fazer um clone? Parece."
export const CenaParece: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("parece");
  const fClone = naFala("parece", "clone");
  const fParece = naFala("parece", "parece");
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo, overflow: "hidden" }}>
      <Som nome="pop" em={0} />
      <Som nome="whoosh" em={fClone - 4} />
      <Som nome="carimbo" em={fParece} />
      <Som nome="boom" em={fParece} volume={0.5} />
      {Array.from({ length: 14 }, (_, i) => {
        const em = i * 4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${8 + random(`qx${i}`) * 84}%`,
              top: `${8 + random(`qy${i}`) * 70}%`,
              fontFamily: titulo,
              fontWeight: 700,
              fontSize: 80 + random(`qs${i}`) * 120,
              color: i % 3 ? cor.borda : cor.apagado,
              scale: estouro(frame, em, 10),
              rotate: `${(random(`qr${i}`) - 0.5) * 40 + Math.sin((frame + i * 10) / 12) * 6}deg`,
            }}
          >
            ?
          </div>
        );
      })}
      <Camera chaves={[{ f: 0, s: 1 }, { f: fClone, s: 1.04 }, { f: fClone + 6, s: 1.2 }, { f: dur, s: 1.28 }]} tremidas={[fParece]}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", paddingBottom: 100 }}>
          <div style={{ fontFamily: titulo, fontSize: 70, color: cor.texto, opacity: surge(frame, 2, 8) }}>
            “tá falando de a IA fazer um…”
          </div>
          <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 250, color: cor.ciano, letterSpacing: -10, lineHeight: 1, scale: estouro(frame, fClone, 10) }}>
            CLONE?
          </div>
          <div style={{ marginTop: 20 }}>
            <Carimbo em={fParece} corFundo={cor.lima} rot={-4} tamanho={110}>
              PARECE.
            </Carimbo>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "Quando você pede pra IA fazer um clone, ela vai simplesmente copiar o comportamento daquele aplicativo ali."
export const CenaComportamento: React.FC = () => {
  const frame = useCurrentFrame();
  const { dur } = cena("comportamento");
  const fClone = naFala("comportamento", "clone");
  const fCopiar = naFala("comportamento", "copiar");
  const fComp = naFala("comportamento", "comportamento");
  const varre = interpolate(frame, [fCopiar - 4, fComp + 10], [0, 1], preso);
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} volume={0.6} />
      <Som nome="pop" em={fClone} />
      <Som nome="digitacao" em={fCopiar - 4} volume={0.5} />
      <Som nome="ding" em={fComp + 2} volume={0.5} />
      <Camera chaves={[{ f: 0, s: 1.1 }, { f: 10, s: 1 }, { f: fComp, s: 1 }, { f: fComp + 8, s: 1.1, y: -20 }, { f: dur, s: 1.12, y: -20 }]}>
        <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 90, paddingTop: 60, paddingBottom: 120 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
            <div style={{ fontFamily: mono, fontSize: 38, color: cor.apagado }}>original</div>
            <JanelaApp largura={620} titulo="app_original" destaque={cor.ciano} />
          </div>
          <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: 20, opacity: surge(frame, fClone - 4, 8) }}>
            <div style={{ fontFamily: mono, fontSize: 38, color: cor.lima }}>clone</div>
            <div style={{ position: "relative" }}>
              <JanelaApp largura={620} titulo="app_clone" destaque={cor.lima} desenho={varre} />
              {/* por dentro, o clone não sabe como o original funciona */}
              <div style={{ position: "absolute", inset: "70px 20px 20px 20px", display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: titulo, fontWeight: 700, fontSize: 110, color: cor.borda, opacity: varre > 0.95 ? 1 : 0 }}>
                ?
              </div>
              <div style={{ position: "absolute", left: 0, right: 0, top: `${varre * 100}%`, height: 6, background: cor.lima,
                boxShadow: `0 0 40px 10px ${cor.lima}`, opacity: varre > 0 && varre < 1 ? 1 : 0 }} />
            </div>
          </div>
        </AbsoluteFill>
        <AbsoluteFill style={{ alignItems: "center", paddingTop: 70 }}>
          <div style={{ fontFamily: titulo, fontWeight: 700, fontSize: 72, color: cor.texto, opacity: surge(frame, fComp - 2, 8) }}>
            copia só o <span style={{ color: cor.lima }}>comportamento</span>
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};

// "Mas se você pedir pra ela analisar, fazendo engenharia reversa, ela não vai pegar somente o
//  comportamento, ela vai analisar toda a estrutura do site, programa ou software."
export const CenaEngenharia: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { dur } = cena("engenharia");
  const fEng = naFala("engenharia", "engenharia");
  const fComp = naFala("engenharia", "comportamento");
  const fEstr = naFala("engenharia", "estrutura");
  const fSite = naFala("engenharia", "site");
  const abertura = interpolate(frame, [fEng, fEng + 30, fComp, fComp + 20], [0, 0.35, 0.35, 1], { ...preso, easing: saida });
  const visiveis = Math.round(interpolate(frame, [fEng - 2, fComp + 30], [1, CAMADAS.length], preso));
  const varre = interpolate(frame, [fEstr - 10, fEstr + 50], [0, 1], preso);
  const giro = interpolate(frame, [0, dur], [-0.5, 0.35]);
  const rotulos = projetarCamadas(abertura, giro, width, height);
  return (
    <AbsoluteFill style={{ backgroundColor: cor.fundo }}>
      <Som nome="whoosh" em={0} volume={0.6} />
      <Som nome="scratch" em={fEng - 3} volume={0.6} />
      <Som nome="boom" em={fEng + 2} />
      {CAMADAS.map((c, i) =>
        i > 0 ? <Som key={c.nome} nome="tique" em={Math.round(interpolate(i, [1, CAMADAS.length - 1], [fComp, fComp + 30]))} tom={1 + i * 0.1} /> : null,
      )}
      <Som nome="riser" em={fEstr - 10} volume={0.3} />
      <Som nome="ding" em={fEstr + 50} volume={0.45} />
      <Som nome="pop" em={fSite} />
      <Camera chaves={[{ f: 0, s: 1.2 }, { f: fEng, s: 1 }, { f: fEstr, s: 1.02 }, { f: fEstr + 10, s: 1.08 }, { f: dur, s: 1.12 }]} tremidas={[fEng + 2]}>
        <AbsoluteFill style={{ translate: "110px 20px" }}>
          <Camadas3D abertura={abertura} varre={varre} visiveis={visiveis} giro={giro} />
          {CAMADAS.map((c, i) => (
            <div
              key={c.nome}
              style={{
                position: "absolute",
                left: rotulos[i].x + 60,
                top: rotulos[i].y - 26,
                display: "flex",
                alignItems: "center",
                gap: 14,
                opacity: i < visiveis ? 1 : 0,
                translate: `${interpolate(frame, [fComp + i * 7 - 6, fComp + i * 7], [40, 0], preso)}px 0`,
              }}
            >
              <div style={{ width: 60, height: 3, background: c.cor }} />
              <div style={{ fontFamily: mono, fontWeight: 700, fontSize: 36, color: c.cor, background: "rgba(7,8,12,0.7)", padding: "2px 10px" }}>
                {c.nome}
              </div>
            </div>
          ))}
        </AbsoluteFill>
        <AbsoluteFill style={{ padding: "90px 110px" }}>
          <Glitch
            semente="eng"
            picos={[[fEng, fEng + 5]]}
            style={{ fontFamily: titulo, fontWeight: 700, fontSize: 110, color: cor.texto, letterSpacing: -3, lineHeight: 1, opacity: frame >= fEng - 2 ? 1 : 0 }}
          >
            ENGENHARIA REVERSA
          </Glitch>
          <div style={{ fontFamily: titulo, fontSize: 54, color: cor.apagado, marginTop: 14, opacity: surge(frame, fEstr - 4, 8) }}>
            toda a <span style={{ color: cor.lima, fontWeight: 700 }}>estrutura</span>, não só o comportamento
          </div>
          <div style={{ display: "flex", gap: 18, marginTop: 24 }}>
            {["site", "programa", "software"].map((t, i) => (
              <div key={t} style={{ fontFamily: mono, fontWeight: 700, fontSize: 36, color: cor.fundo, background: cor.lima,
                padding: "6px 20px", borderRadius: 999, scale: estouro(frame, fSite + i * 7, 10) }}>
                {t}
              </div>
            ))}
          </div>
        </AbsoluteFill>
      </Camera>
    </AbsoluteFill>
  );
};
