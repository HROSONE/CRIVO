# Pointer/Copy Causal v3 — resultado da execução de 12/10/2026

Execução no Colab (T4) do commit `e4b78c9`. Saída no Drive:
`CRIVO/checkpoints/experimento_pointer_copy_v3/pointer_copy_v3_20261012_045512/`
(`pointer_head_v3.pt`, `resultado_pointer_copy_v3.json`, `config_experimento_v3.json`,
`README_resultado_v3.txt`). Resumo sem as linhas por caso: `resultado_resumo_v3.json`.
A pasta do v2 e o `pointer_head.pt` do v2 não foram tocados.

Integridade: dados congelados conferidos pelos 4 SHA-256; base `c0a56b15…`;
fingerprint `257a4eb4…` antes = depois; cabeça reinicializada (24.961 parâmetros).

## Decisão

**Reprovado.** `gate_pass=false` (falharam `exact_name_fim_copia>=0.70` e
`exact_name_distant>=0.65`). `ativo_no_chat=false`, `promovido=false`. Não entra no chat.

## O que a rodada mostrou

1. **O gate de cópia era inalcançável por esta arquitetura.** Teto medido com a base real
   sob teacher forcing: exact-name+`<fim>` na cópia pura = **0/100**. A base nunca põe
   `<fim>` como top-1 depois de um nome solto (0%) e nunca põe o primeiro token do nome
   (sem `Ġ`) como top-1 no início da resposta (0%). Como a mistura não muda a ordem do
   vocabulário para alvos fora do prompt, nenhuma cabeça desta forma passaria.
   Nas frases completas a base para sozinha: `<fim>` é top-1 em 100% das outras tarefas.

2. **O treino piorou o dev e o protocolo escolheu o passo 1.** Dev cópia+fim = 0 em todas
   as avaliações; função no dev 87,5% no passo 1 → 18,8–37,5% nos passos 100–400; early
   stop no passo 400. O estado avaliado no blind é o do passo 1, praticamente sem treino,
   por isso o blind final ficou igual à base (diferenças de 0–2 pp). Os gates de regressão
   e posição "passaram" só por isso; não indicam benefício.

3. **O formato do v2 derrubava a própria base.** Mesmas 100 entidades do blind v2, base sem
   pointer:

   | | formato v2 (IDs colados) | formato real |
   |---|---|---|
   | nome exato em qualquer tarefa | 3,3% | 29,3% |
   | função (semântica) | 2% | 81% |
   | categoria (semântica) | 0% | 30% |
   | semântica geral | 0,6% | 22,2% |

   Parte grande dos 75% do v2 corrigia um artefato do formato, não a conversa real.
   O baseline legado reproduziu exatamente o do v2 (3,3% / 0% / 0,6%).

## Blind novo, formato real (base = pointer final, salvo onde indicado)

| Tarefa | exact-name | exact-name+fim | semântica |
|---|---|---|---|
| cópia | 0% | 0% | 0% |
| categoria | 66% | 0% | 24% |
| função | 77% | 0% | 71% → 69% |
| invariância | 2% | 0% | 0% |
| composição | 6% | 0% | 0% |
| negação | 3% | 0% | 0% |

Nome exato geral 25,7%; close = distant = 25,7%; semântica geral 19,0% → 18,6%.

Amostras (iguais na base e no pointer): a base acerta o nome quando o coloca no meio
da frase (`A função de vi-ce6 é transportar carga.`), mas abre respostas com uma palavra
inventada (`Trila é um instrumento usado para`, `Trilheiros é um objeto…`), não diz "Não."
em invariância/negação, e não responde só com o nome.

## Limites

- Holdout sintético de autoria do agente; não é conversa humana.
- O blind final mede a cabeça do passo 1; o comportamento da cabeça treinada aparece só
  no dev (16 + 16 casos).
- Não houve porta conversacional.

## Próxima intervenção (uma de cada vez, a decidir)

O gargalo está fora do alcance da cabeça atual: emitir a variante sem `Ġ` de um token do
prompt e emitir `<fim>`. Candidatas, cada uma isolada numa rodada:
(a) rota de cópia que leve `ĠX` do prompt para a variante `X` do próprio vocabulário;
(b) rota explícita de parada na mistura;
(c) mexer na base (descongelar topo/`lm_head`), o que muda a premissa deste experimento.
