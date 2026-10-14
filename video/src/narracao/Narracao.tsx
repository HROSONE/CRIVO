import React from "react";
import { AbsoluteFill, interpolate, Sequence, staticFile } from "remotion";
import { Audio } from "@remotion/media";
import { Acabamento, Clarao } from "../comp/Acabamento";
import { Som } from "../comp/util";
import { CenaAssinatura, CenaClonados, CenaComum, CenaPirataria } from "./Cenas1";
import { CenaComportamento, CenaEngenharia, CenaParece, CenaTentacao } from "./Cenas2";
import { CenaFavorContra, CenaInscreva, CenaMalIntencionada, CenaPerigo, CenaRoubo, CenaUmaHora } from "./Cenas3";
import { CENAS_NARRACAO, TOTAL_NARRACAO } from "./dados.gen";
import { useJson } from "./energia";
import { Legendas } from "./Legendas";

/**
 * O vídeo narrado: a voz do criador (public/voz/narracao.ogg) por cima, as
 * cenas trocando no início de cada frase, legendas, trilha baixa e efeitos.
 */
export const Narracao: React.FC = () => {
  const energia = useJson<number[]>("voz/energia.json");
  if (!energia) return null;
  const desenhar = (id: string, de: number) => {
    switch (id) {
      case "clonados": return <CenaClonados />;
      case "pirataria": return <CenaPirataria />;
      case "comum": return <CenaComum />;
      case "assinatura": return <CenaAssinatura />;
      case "tentacao": return <CenaTentacao energia={energia} de={de} />;
      case "parece": return <CenaParece />;
      case "comportamento": return <CenaComportamento />;
      case "engenharia": return <CenaEngenharia />;
      case "perigo": return <CenaPerigo />;
      case "umaHora": return <CenaUmaHora />;
      case "malIntencionada": return <CenaMalIntencionada energia={energia} de={de} />;
      case "roubo": return <CenaRoubo />;
      case "favorContra": return <CenaFavorContra />;
      case "inscreva": return <CenaInscreva />;
      default: return null;
    }
  };
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio src={staticFile("voz/narracao.ogg")} volume={0.72} />
      <Audio
        src={staticFile("sfx/trilha_narracao.wav")}
        volume={(f) => interpolate(f, [0, 15, TOTAL_NARRACAO - 20, TOTAL_NARRACAO], [0, 0.16, 0.16, 0])}
      />
      {CENAS_NARRACAO.map((c, i) => (
        <Sequence key={c.id} name={c.id} from={c.de} durationInFrames={c.dur}>
          {desenhar(c.id, c.de)}
          {i > 0 && <Clarao />}
          {i > 0 && <Som nome="whoosh" em={0} volume={0.35} />}
        </Sequence>
      ))}
      <Legendas />
      <Acabamento />
    </AbsoluteFill>
  );
};
