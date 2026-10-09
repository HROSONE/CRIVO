# Confirmar e descartar hipóteses na conversa

O motor do `main` calculava uma hipótese numa cópia, mas descartava essa cópia ao responder. “Confirmo essa hipótese como fato.” não era atendido. A pergunta seguinte voltava aos valores antigos. O controle foi fixado no commit `c142b71`, antes de alterar o motor; o baseline usa o código do `main` `836d351`.

A alteração mantém uma alternativa pendente por instância para custos, tempo, agendas ou requisitos. Consultas seguintes do mesmo domínio usam essa alternativa e continuam identificadas como hipotéticas. Uma confirmação explícita promove os dados, preservando a fala da hipótese e registrando a confirmação como outra fonte. Descartar a alternativa recupera os fatos, incluindo valores já confirmados. Uma nova hipótese parte dos fatos, sem acumular outra simulação anterior.

Exemplo verificado pelo motor, pelo adaptador web e pelo endpoint HTTP:

1. “Tenho 80 minutos. A ida leva 12 minutos e a tarefa leva 14 minutos. Quanto sobra?” → 54 minutos.
2. “Se eu tivesse 32 minutos, caberia?” → 6 minutos nessa hipótese; os fatos ainda conservam 80 disponíveis.
3. “Confirmo essa hipótese como fato.” → 32 disponíveis, 26 gastos, 6 restantes.
4. “Quanto tempo real sobra?” → continua respondendo 6, com a origem da hipótese e a confirmação registradas.

Confirmações genéricas (“Sim”, “Confirmado”), perguntas, negações, citações e afirmações incertas não promovem dados. Uma declaração factual reconhecida encerra a alternativa anterior; uma nova tentativa condicional sem interpretação segura também invalida a alternativa anterior, evitando confirmar o cenário errado. Reinício e instâncias diferentes isolam os dados. Sem alternativa pendente, confirmar pede que a pessoa identifique a hipótese. “Volte aos fatos” continua consultando os valores já confirmados.

| Controle de desenvolvimento | Antes | Depois |
| --- | ---: | ---: |
| Contratos de cálculo/escopo | 12/32 | 32/32 |
| Sessões completas | 0/4 | 4/4 |
| Motor completo | não coletado | 32/32 |
| Adaptador web | não coletado | 32/32 |
| Transferência anterior conhecida | 24/24 publicados anteriormente | 24/24 |

`baseline_componente.json` conserva falhas e respostas anteriores. `motor_final.json` e `web_final.json` incluem o SHA256 do código efetivamente executado, todos os turnos, respostas, cálculos, fontes e erros. `transferencia_final.json` conserva a regressão do conjunto anterior. O avaliador pode exigir todos os contratos, depois de escrever o relatório integral; o CI usa essa opção.

São 17 novos testes: confirmação/descarte, origem das fontes, correções reais, troca de hipótese em componentes diferentes, ambiguidade, consulta factual, isolamento, reinício, memória limitada, 80 cenários numéricos parametrizados, equivalência entre motor/web e uma requisição HTTP real. Os testes anteriores de conversa, argumentos, diálogo situado, lógica e web também foram executados. Na coleta ampla, o socket HTTP foi bloqueado pela sandbox; os cinco testes dessa classe passaram na repetição com acesso ao socket local.

Esta é uma melhoria da memória e do executor estrutural próprios. Não houve treino ou alteração de pesos, tokenizer externo, APIs de modelos ou promoção dos candidatos reprovados. O controle tem quatro sessões autorais, da mesma autoria do código, e virou desenvolvimento conhecido; não mede generalização independente, geração livre ou raciocínio neural geral. O parser ainda aceita uma gramática limitada, com uma alternativa ativa. No navegador, a reconstrução continua limitada às dez mensagens anteriores; não foi implementada persistência além dessa janela.

## Reproduzir

Na raiz, com os requisitos próprios do projeto, escolha saídas novas:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_hipoteses_confirmadas testes_raciocinio_conversa -v
python -S -m unittest testes_hipoteses_confirmadas.TestesHipotesesConfirmadas testes_raciocinio_conversa.TestesRaciocinioConversa -v
python experimentos/confirmacao_hipoteses_20261009/avaliar.py --raiz . --modo motor --exigir-todos --saida /tmp/hipoteses-motor-novo.json
python experimentos/confirmacao_hipoteses_20261009/avaliar.py --raiz . --modo web --exigir-todos --saida /tmp/hipoteses-web-novo.json
```

O teste HTTP precisa permitir a criação de um servidor em `127.0.0.1`. Não publica serviço nem usa modelos externos.
