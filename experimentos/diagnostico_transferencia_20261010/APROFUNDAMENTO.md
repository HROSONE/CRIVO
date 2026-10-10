# Aprofundamento: fixação da forma de resposta — 10/10/2026

Esta etapa só lê `resultados.json`; não executa o modelo, não treina e não altera pesos.

## Abertura da resposta

- Primeiros tokens distintos nos alvos: **20**.
- Primeiros tokens distintos nas gerações: **13**.
- Erros já no token 0: **84/93** respostas não-exatas.
- Erros no token 1: **4/93**.
- Erros no token 2: **5/93**.

Primeiros tokens mais comuns do alvo: `você`=16, `a`=10, `nubira-21`=9, `ocrélio-32`=9, `ainda`=6, `não`=6, `o`=6, `vocês`=4, `se`=4, `entendi`=3.

Primeiros tokens mais comuns gerados: `você`=35, `atualmente`=15, `qual`=12, `não`=10, `o`=6, `sozinho`=5, `morasse`=4, `quem`=2, `nubira-21`=1, `por`=1.

## Fixação dentro das sessões

- Turnos após o primeiro: **78**.
- Repete alguma resposta própria anterior: **14** (17.9%).
- Repete exatamente a primeira resposta gerada da sessão: **11** (14.1%).
- Repete literalmente um alvo correto de turno anterior: **3** (3.8%).

## Diversidade global

- Respostas-alvo distintas: **72**.
- Respostas geradas distintas: **55**.

Top respostas geradas:
- **15×** `atualmente você mora sozinho.`
- **4×** `morasse, pode me ajudar.`
- **3×** `sozinho, pode me ajudar.`
- **3×** `você pode me ajudar a possibilidade.`
- **3×** `você pode é a chegar.`
- **2×** `você pode me emprestar seu silêncio? podemos.`
- **2×** `não. você pode me me me escolha.`
- **2×** `você pode me emprestar seu respondeu.`
- **2×** `você pode me ajudar a escolha.`
- **2×** `você pode me emprestar seu pode participar.`

## Proximidade lexical com o treino

- Correlação Jaccard de entrada × CE: **-0.199**.
- Similaridade ≥0,50: **12** casos, CE média **3.340**, exatas **1**.
- Similaridade <0,50: **82** casos, CE média **4.270**, exatas **0**.

A proximidade é lexical/estrutural simples e usa somente a entrada. Não mede equivalência semântica.
