# CRIVO — nova avaliação A/B da memória associativa (01/10/2026)

**Execução efetiva:** [GitHub Actions #36821486551](https://github.com/HROSONE/CRIVO/actions/runs/36821486551), commit `f23c082831e1e8aa2d12503b2f41ba3f05c2fced`. Artefato com 28 respostas completas: [experimento-cortex-ab-novo-2](https://github.com/HROSONE/CRIVO/actions/runs/36821486551/artifacts/11144050885).

## Protocolo congelado para esta rodada

- 14 perguntas positivas **novas** sobre propriedades e mecanismos astronômicos e 14 controles negativos com objeto ausente, duas entidades incompatíveis, negação ou alegações sem fundamento.
- Duas instâncias por consulta: `Crivo()` com o circuito recém-integrado ativo e `Crivo()` com apenas o fallback `_resposta_associativa` desativado; mesma base e mesma rede pré-existente, **sem treinamento**.
- Verificação anticolisão: as 28 perguntas não coincidem literalmente com as 1.534 perguntas de treinamento local nem com as 58 perguntas da prova retida v1.
- Correção estrita por **unidade de evidência exata + fragmento factual + URL de fonte** no contexto exibido. Por isso a pontuação **não** representa uma avaliação humana de toda a resposta nem uma medida de inteligência geral.
- Houve uma correção de um **erro de tipo no avaliador** durante a execução inicial: o contexto da API devolve tuplas `(conceito, índice)`, enquanto o gabarito comparava listas. O commit final alterou *somente* a comparação e introduziu verificação de coerência da métrica; **nenhuma pergunta, peso ou gabarito factual foi modificado**. A análise abaixo é da segunda execução, com a medição corrigida.

## Resultados medidos

| Medição | Resultado |
| --- | ---: |
| Fato + fonte recuperados com circuito ativado | **9/14 (64,3%)** |
| Mesmo requisito com circuito desligado | **0/14 (0%)** |
| Ganhos exclusivamente atribuíveis ao fallback | **9** |
| Casos em que desligar melhorou a recuperação estrita | **0** |
| Ativações do circuito em controles negativos | **0/14** |
| Positivos com mudança textual da resposta ligada vs desligada | **9/14** |

**Ganhos claros:** Terra (campo magnético, tectônica), Júpiter (hidrogênio metálico, nuvens e tempestades), Saturno (gravidade nos anéis), Urano (absorção de luz pelo metano), Netuno (ventos, absorção atmosférica), Marte (óxidos de ferro). Em todos os nove, o mecanismo recuperou uma frase editorial existente e uma URL de proveniência.

**Cinco lacunas:** Vênus/efeito estufa (`aquecimento_global`), Mercúrio/revolução (`fora`), Sistema Solar/dinâmica gravitacional (`duvida`), estrela/radiação (`fora`), Vênus/rotação (`mais_quente`). Nenhum desses cinco ativou o microcircuito. Os IDs entre parênteses são os resultados **com o circuito ligado**.

## Interpretação honesta

A avaliação detecta **ganho causal na recuperação específica** com a implementação atual, porque desligar apenas a memória associativa fez desaparecer nove seleções corretas de fatos documentados. Contudo, o protocolo utiliza perguntas próximas do vocabulário das fichas: não demonstra paráfrases amplas, inferência inédita, causalidade não cadastrada ou aprendizado autônomo.

O dado `0/14` da ablação não significa que o sistema antigo desconhecia tudo. Por exemplo, uma resposta preexistente sobre Marte podia ser factual, mas não selecionava a **unidade documental específica** exigida pela rubrica. O teste mede recuperação rastreável, não conhecimento total.

Os controles testam apenas se **o circuito associativo foi ativado indevidamente**. Eles não certificam toda a segurança e veracidade das outras camadas do chatbot. A prova independente anterior (`avaliacoes/astronomia_independente_v1.json`) permanece congelada e foi consultada apenas para evitar repetição literal dos enunciados, nunca usada para treinar.

### Próximas hipóteses a testar (sem treinar nas perguntas retidas)

1. Resolver referente e operação juntos, evitando priorizar `aquecimento_global` quando a pergunta se refere explicitamente a Vênus.
2. Criar representações de predicado/argumento/negação aprendidas que superem o filtro limitado a `como/de que modo`.
3. Medir recall fora de sobreposição lexical (sinônimos e redações distantes) e precisão na recuperação do fato, sem baixar o limiar de segurança para ganhar acertos.
4. Repetir o experimento com outro conjunto prospectivo e depois aplicar avaliação semântica por revisor externo.

**Não houve alteração da `main` neste teste**, nem mudança de peso neural. A skill de Astronomia permanece em **0% certificado** até atingir a prova de compreensão geral exigida pelo currículo.
