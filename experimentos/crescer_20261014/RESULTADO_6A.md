# Fase 6a — resultado (14/10/2026)

O CRIVO cresceu de 17M para **46,1M de parâmetros** (24 camadas, contexto 1024) a partir dos próprios
pesos (base `57e809f4…`) e leu **3,6 bilhões de tokens** (55 mil passos de 64 × 1024; 70% FineWeb-2
português, 30% corpus próprio) numa A100 40 GB, em cerca de 3h20 de treino.

- Pesos: `CRIVO/transformer-crivo-46m/base_20261014_054004/pesos.pt` (184 MB, SHA
  `fcf396b9cbf749fc600a704faeb2bbd3e638d5b289e4d9e087bdfe3e055623d8`), conta hr87676620.
- Resumo completo: `resumo_fase6a.json` (nesta pasta, cópia do Drive).

| passo | tokens lidos | perda corpus próprio (256) | perda web (1024) | cópia top-1 |
|---|---|---|---|---|
| 0 (crescido, igual à base) | 0 | 2,962 | 4,991 | 59,3% |
| 6 000 | 0,39 bi | 2,997 | 3,092 | 55,9% |
| 18 000 | 1,18 bi | 2,887 | 2,928 | 60,6% |
| 30 000 | 1,97 bi | 2,815 | 2,847 | 61,3% |
| 42 000 | 2,75 bi | 2,754 | 2,788 | 64,3% |
| 55 000 | 3,60 bi | **2,723** | **2,756** | 66,2% |

## Leitura

- No corpus próprio, a perda caiu 0,239 (perplexidade de ~19,3 para ~15,2, 21% menor) na mesma régua
  de janelas de 256 tokens da base.
- Na web com 1024 tokens, a base não sabia usar as posições novas (4,99). Agora usa (2,76).
- Nos primeiros 4 mil passos, a perda no corpus próprio subiu (até 3,06) e a cópia caiu (44%),
  enquanto as camadas novas acordavam. A base foi superada perto do passo 10 mil, e a melhora não
  parou até o fim.
- A sonda de cópia (repetir 50 tokens aleatórios) oscila ±3 pontos entre medidas. A tendência foi de
  ~55% para ~66%.

## Limites

- A perda ainda caía no fim (−0,003 nos últimos 2 mil passos): ler mais ajudaria.
- Perda baixa não prova que ele conversa bem. Esta base só lê; conversar é a 6b.
- Na CPU, nada foi medido com estes pesos ainda: a estimativa (~190 tokens/s, ~220 MB) é a do
  modelo de 42M do mesmo formato. Será medido na 6c.
- Não está no chat (`ativo_no_chat: false`).
