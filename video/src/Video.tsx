import React from "react";
import { AbsoluteFill, interpolate, Series, staticFile } from "remotion";
import { Audio } from "@remotion/media";
import { Acabamento, Clarao } from "./comp/Acabamento";
import { Binario } from "./cenas/Binario";
import { Clones } from "./cenas/Clones";
import { Crivo } from "./cenas/Crivo";
import { Final } from "./cenas/Final";
import { Gancho } from "./cenas/Gancho";
import { Mas } from "./cenas/Mas";
import { Modelos } from "./cenas/Modelos";
import { Rea } from "./cenas/Rea";
import { CENAS, TOTAL } from "./tema";

const Cena: React.FC<{ children: React.ReactNode; clarao?: boolean }> = ({ children, clarao = true }) => (
  <AbsoluteFill>
    {children}
    {clarao && <Clarao />}
  </AbsoluteFill>
);

/** Cortes secos entre as cenas, cada um marcado por um clarão. */
export const Video: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    <Audio
      src={staticFile("sfx/trilha.wav")}
      volume={(f) => interpolate(f, [0, 10, TOTAL - 10, TOTAL], [0.5, 0.5, 0.5, 0])}
    />
    <Series>
      <Series.Sequence name="Gancho" durationInFrames={CENAS.gancho}>
        <Cena clarao={false}>
          <Gancho />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="REA" durationInFrames={CENAS.rea}>
        <Cena>
          <Rea />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="Binário" durationInFrames={CENAS.binario}>
        <Cena>
          <Binario />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="Clones" durationInFrames={CENAS.clones}>
        <Cena>
          <Clones />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="Mas" durationInFrames={CENAS.mas}>
        <Cena>
          <Mas />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="Modelos" durationInFrames={CENAS.modelos}>
        <Cena>
          <Modelos />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="CRIVO" durationInFrames={CENAS.crivo}>
        <Cena>
          <Crivo />
        </Cena>
      </Series.Sequence>
      <Series.Sequence name="Final" durationInFrames={CENAS.final}>
        <Cena>
          <Final />
        </Cena>
      </Series.Sequence>
    </Series>
    <Acabamento />
  </AbsoluteFill>
);
