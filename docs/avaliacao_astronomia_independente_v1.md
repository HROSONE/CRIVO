# Astronomia — avaliação retida independente v1

**Data:** 01/10/2026. **Modelo avaliado:** `rede_crivo.json` da branch do PR #39, checkpoint autoral de 193 classes gerado **antes** da elaboração da prova. **Commit executado:** `924afc06138687b0e45e84d373c55efc7228fb1d`. **Execução:** https://github.com/HROSONE/CRIVO/actions/runs/36819092257.

## O que significa independência neste relatório

As 58 perguntas e os critérios foram escritos em `avaliacoes/astronomia_independente_v1.json` após o treino do checkpoint, separados dos exemplos de `conhecimento.json` e `curriculo_mundo.py`. O avaliador impede coincidência exata (com normalização) entre os enunciados retidos e as perguntas usadas no treino; não recalcula nem ajusta pesos e cria um CRIVO novo para cada caso. O modelo e o teste são identificados por SHA-256 no relatório integral.

**Não** se trata de auditoria conduzida por um especialista externo, estudo cego com pessoas, prova de raciocínio irrestrito ou julgamento semântico automatizado. A rubrica pontua ID correto mais palavras-chave indispensáveis; pode penalizar respostas corretas com identificador diferente ou sinônimos não previstos e pode aprovar textos que contenham palavras certas sem raciocínio válido. A revisão científica humana permanece pendente. A prova agora está **congelada**: não treinar com seus enunciados nem modificar o gabarito para aumentar uma nota; uma futura prova v2 deve utilizar enunciados novos, também posteriores ao próximo modelo.

## Métricas observadas

| Coorte | Acertos / total | Percentual | Limiar do currículo | Situação |
| --- | ---: | ---: | --- | --- |
| Vocabulário, 24 definições novas | 11/24 | 45,8% | ≥90% | Não atingido |
| Sistema Solar, 20 questões de planeta/mecanismo | 2/20 | 10,0% | ≥90% | Não atingido |
| Controles sem evidência, objetos inventados e premissas especulativas | 14/14 | 100% | 100% de abstenções | Atingido nesta amostra |
| Rede neural isolada, apenas 29 perguntas com label definido no classificador | 22/29 | 75,9% | Métrica separada | Insuficiente para demonstrar conversação |

**Total dos positivos:** 13/44 na rubrica automática (29,5%). **Critério de 10%:** NÃO certificado. **Critério de 20%:** NÃO certificado. O CI geral anteriormente verde prova a ausência de regressões cobertas, não suficiência de conhecimento independente.

### Falhas a investigar por mecanismo, sem decorar a prova

1. **Extração do alvo sob reformulações:** o pedido educado `Defina galáxia, por gentileza` terminou interpretando `por gentileza` como alvo; `O que quer dizer o termo estrela?` não encontrou a definição. Tratar estrutura, escopo e marcadores discursivos de modo geral, sem inserir os enunciados retidos na base.
2. **Ambiguidade entre conceitos e fatos relacionados:** `Consegue definir um planeta?` devolveu a contagem de planetas, não a definição; `Descreva Júpiter como planeta` ativou a ficha antiga sobre ser o maior, mas não cobriu composição. Verificar intenção e entidades sem usar ranking isolado como prova.
3. **Relações e mecanismos com predicado novo:** consultas sobre o campo magnético terrestre e as partículas dos anéis de Saturno não recuperaram o mecanismo solicitado. A resposta sobre anéis citou gelo e rocha, não força gravitacional; isso é resposta ao tópico, não à pergunta inteira.
4. **Confusão de tema:** pergunta sobre aquecimento de Vênus foi confundida com aquecimento global terrestre. Falta correspondência predicado–entidade–condição.
5. **Abstenções adequadas na amostra limitada:** 14/14 casos inventados ou com qualificadores absurdos foram recusados ou pedidos de esclarecimento. Isto não assegura ausência de alucinações fora dos 14 casos.

### Evidências reproduzíveis e fontes do gabarito

- Questões imutáveis: `avaliacoes/astronomia_independente_v1.json`.
- Executador: `scripts/avaliar_astronomia_independente.py`.
- Relatório com **58 registros integrais**, incluindo IDs, respostas, critérios de palavras, classificação e métricas da rede: artefato `relatorio-astronomia-independente-v1-1`, disponível na execução do GitHub Actions.
- SHA-256 do checkpoint: `05a42345ae459b963965876f844d0a371eee1c1a46d3359a16a998189d7f53a5`.
- SHA-256 da prova: `1d253a572af09333f7d61c07b47221fbce775d72fffb54ddd3261c3a2f0e3c51`.
- Referências para revisão do gabarito: [NASA — fatos do Sistema Solar](https://science.nasa.gov/solar-system/solar-system-facts/), [NASA — temperaturas planetárias](https://science.nasa.gov/resource/solar-system-temperatures/), [NASA — técnicas de detecção de exoplanetas](https://science.nasa.gov/exoplanets/facts/). A seleção de palavras-chave da prova não equivale a revisão externa.

**Próximo marco:** corrigir parsing genérico de português, correspondência composicional da intenção, evidência causal e integração dos mecanismos já catalogados, mantendo o modelo treinado sem acesso à prova v1. Após modificar o sistema, criar **outro conjunto retido v2**, revisão humana e nova matriz CI antes de reconsiderar 10% ou 20%. Não mover percentual pela simples adição de conceitos.
