# Fala informal e pronomes (2026-10-02)

## O que muda

- **Abreviações no tokenizador** (`analisador_frases.INFORMAL`): "pq",
  "msm", "td", "dps", "agr", "cmg", "qnd", "oq", "naum", "vdd", "fds",
  "sla"… viram a forma por extenso antes da análise. "pq" no começo de uma
  pergunta vira "por que" ("pq ele ligou?"); no meio de uma afirmação,
  "porque" ("me ligou pq o sistema caiu"). Nada muda nos pesos do
  analisador: a fala informal chega a ele já normalizada.
- **"ele", "ela", "eles", "elas"** (`sentido_frases.MemoriaRelatos`): quando
  o sujeito de um relato é um pronome, ele aponta para o referente mais
  recente da mesma conversa com o mesmo gênero e número, pelo determinante
  ("minha vó" → feminino singular, "meus pais" → masculino plural; nome
  próprio serve para os dois). "meu irmão chegou" + "ele trouxe um presente"
  → "quem trouxe o presente?" → "Pelo que você me contou, foi seu irmão."
  Sem referente compatível, o pronome fica como está; relato de outra
  conversa nunca é usado.
- **"tô cansada"**: a pessoa está no verbo de ligação, não no adjetivo; o
  relato fica marcado como primeira pessoa e "pq eu tô cansada?" encontra
  o motivo contado.

## Medição

Conjuntos novos `informal_dev` e `informal_retido` em
`avaliacoes/memoria_relatos_v1`, escritos antes das mudanças:

| | antes | depois |
|---|---|---|
| informal dev | 2/8 | 8/8 |
| informal retido (agregado) | 1/7 | 5/7 |

Sem perda: memória de relatos 12/12, 8/8, 10/10; presença 35/35, 15/19,
retido2 27 → 28/29; diálogo único 21/21, 16/18; conversa cotidiana 36/36,
23/24, 12/15.

## Por que não um novo treino do analisador

O plano previa anotar frases informais e treinar de novo no Colab. A maior
parte dos erros vinha de abreviações que o analisador nunca viu, e isso se
resolve antes dele, sem dados anotados à mão nem rodada de GPU. Um
treino com frases informais anotadas continua possível se a medição
mostrar erros de estrutura (e não de vocabulário) na fala informal.
