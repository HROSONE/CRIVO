import React from "react";
import { Easing, interpolate, random, staticFile } from "remotion";
import { Audio } from "@remotion/media";

export const preso = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const saida = Easing.bezier(0.16, 1, 0.3, 1);
export const soco = Easing.bezier(0.7, 0, 0.2, 1);

/** Entrada com "estouro": cresce além do tamanho e assenta. */
export const estouro = (frame: number, em: number, dur = 12) =>
  interpolate(frame, [em, em + dur * 0.6, em + dur], [0, 1.12, 1], {
    ...preso,
    easing: Easing.out(Easing.cubic),
  });

export const surge = (frame: number, em: number, dur = 14) =>
  interpolate(frame, [em, em + dur], [0, 1], { ...preso, easing: saida });

/** Efeito sonoro de public/sfx, a partir de um quadro da cena. */
export const Som: React.FC<{
  nome: string;
  em: number;
  volume?: number;
  tom?: number;
}> = ({ nome, em, volume = 1, tom }) => (
  <Audio
    src={staticFile(`sfx/${nome}.wav`)}
    from={em}
    volume={volume * 0.8}
    toneFrequency={tom}
  />
);

/** Caractere aleatório estável por quadro. */
export const embaralhado = (alvo: string, frame: number, revela: number, semente: string) => {
  const sinais = "0123456789ABCDEF<>/{}[]#$%&*";
  return alvo
    .split("")
    .map((c, i) => {
      if (c === " " || frame >= revela + i * 0.6) return c;
      const r = random(`${semente}-${i}-${Math.floor(frame / 2)}`);
      return sinais[Math.floor(r * sinais.length)];
    })
    .join("");
};
