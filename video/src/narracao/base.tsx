import { CENAS_NARRACAO, PALAVRAS } from "./dados.gen";

export type IdCena = (typeof CENAS_NARRACAO)[number]["id"];

export const cena = (id: IdCena) => {
  const c = CENAS_NARRACAO.find((x) => x.id === id);
  if (!c) throw new Error(`cena ${id}`);
  return c;
};

/**
 * Quadro, relativo ao início da cena, em que a palavra é dita (n-ésima vez
 * dentro da cena). Usado para cair efeito e animação em cima da fala.
 */
export const naFala = (id: IdCena, palavra: string, n = 1) => {
  const c = cena(id);
  const achadas = PALAVRAS.filter((p) => p.t === palavra && p.f >= c.de - 2 && p.f < c.de + c.dur);
  const p = achadas[n - 1] ?? achadas[achadas.length - 1];
  if (!p) throw new Error(`palavra "${palavra}" não está na cena ${id}`);
  return Math.max(0, p.f - c.de);
};
