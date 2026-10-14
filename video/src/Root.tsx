import React from "react";
import { Composition, Folder } from "remotion";
import { Binario } from "./cenas/Binario";
import { Clones } from "./cenas/Clones";
import { Crivo } from "./cenas/Crivo";
import { Final } from "./cenas/Final";
import { Gancho } from "./cenas/Gancho";
import { Mas } from "./cenas/Mas";
import { Modelos } from "./cenas/Modelos";
import { Rea } from "./cenas/Rea";
import { CENAS, FPS, TOTAL } from "./tema";
import { Video } from "./Video";

const base = { width: 1920, height: 1080, fps: FPS };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="EngenhariaReversa" component={Video} durationInFrames={TOTAL} {...base} />
    <Folder name="Cenas">
      <Composition id="Gancho" component={Gancho} durationInFrames={CENAS.gancho} {...base} />
      <Composition id="REA" component={Rea} durationInFrames={CENAS.rea} {...base} />
      <Composition id="Binario" component={Binario} durationInFrames={CENAS.binario} {...base} />
      <Composition id="Clones" component={Clones} durationInFrames={CENAS.clones} {...base} />
      <Composition id="Mas" component={Mas} durationInFrames={CENAS.mas} {...base} />
      <Composition id="Modelos" component={Modelos} durationInFrames={CENAS.modelos} {...base} />
      <Composition id="CRIVO" component={Crivo} durationInFrames={CENAS.crivo} {...base} />
      <Composition id="Final" component={Final} durationInFrames={CENAS.final} {...base} />
    </Folder>
  </>
);
