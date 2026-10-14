import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Rede3D } from "./Rede3D";

export const Teste3D: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: "#07080c" }}>
      <Rede3D abertura={interpolate(frame, [0, 60], [0, 1], { extrapolateRight: "clamp" })} pulso={0.5} />
    </AbsoluteFill>
  );
};
