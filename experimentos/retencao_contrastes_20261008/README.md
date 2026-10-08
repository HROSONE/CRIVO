# Retenção própria e contrastes negados

Terceiro treino desta rodada, motivado pelos dois treinos de eventos e pelo piloto de composição que falharam nas regressões. Não usa modelos ou APIs externos. Começa novamente nos pesos próprios anteriores de `associacao_fatos_20261008/candidato_normalizado`. O professor é uma cópia congelada dos mesmos pesos próprios; sua previsão orienta retenção, não criação de dados ou respostas externas. O candidato mantém a arquitetura anterior com a cabeça auxiliar adicional presente mas sem perda de evento; 2.948.374 parâmetros. A cópia professora só é necessária no treino.

## Mudança

A tentativa primária usava replay apenas do treino contextual inicial. Isso não cobria a associação de fatos aprendida na segunda rodada. Agora metade de cada lote é replay próprio: quatro exemplos da associação e quatro contextuais. Os oito restantes são críticos novos, dois de cada correção, hipótese, retorno e confirmação. A seleção inclui também a validação de associação, antes ausente.

Foram adicionadas versões das sessões novas com contrastes negados: uma hipótese pode começar com “Não estou dizendo que aconteceu”, enquanto uma correção factual pode começar com “Não estou propondo uma hipótese”. Os mesmos valores, fontes e regras são conservados; os offsets são deslocados e verificados. Essas versões são aumento de dados, não novas conversas independentes. Algumas perguntas têm a pontuação final alterada para variar a ordem de símbolos locais sem mudar os fatos.

O treino contém 9.246 prefixos (4.623 originais e 4.623 versões), a validação 738 (369+369). As declarações iniciais podem repetir entradas; não há alegação de 9.246 exemplos semanticamente únicos. Replay: 2.000 prefixos do treino de associação e 1.000 contextuais. O novo teste prospectivo contém 80 sessões/370 prefixos, com novas entidades e frases. Compartilha autoria, regras e gramática; não é independente. Nomes de uma palavra, valores inteiros e contexto até 256 tokens. Nenhuma sessão foi truncada/rejeitada neste preparo. Os testes anteriores são painéis conhecidos de regressão.

## Treino e critérios

400 atualizações, semente 20261014, AdamW, lr 0,00005, lote 16. Perdas supervisionadas: operação 1, escopo 0,2, ponteiros 0,8. Além disso, divergência KL de operação, escopo e ponteiros com o professor próprio congelado, peso 0,25 em cada uma, apenas nos exemplos de replay. Preservar distribuições não certifica correção: o professor também erra, e a supervisão de referência permanece.

Escolha a cada 100 atualizações: 50% média dos seis eventos do novo dev, 30% média das famílias do dev de associação e 20% do dev contextual. A regra e o novo teste foram registrados antes do treino; o treino não abre teste. Não isola o efeito de replay, retenção, contrastes, taxa e orçamento, que mudam conjuntamente. Uma semente; sem intervalo de confiança. Não recebe supervisão causal de redação e não mede conversa livre.

Critério prévio: pelo menos 80% em cada evento crítico e família; aumento de 20 pontos percentuais nas sessões completas versus o modelo anterior com o mesmo preparo; queda máxima de cinco pontos nos dois painéis conhecidos. Mesmo passar o critério sintético não autoriza ativar chat. Os pesos ativos permanecem preservados.

## Reproduzir

Na raiz do repositório, com Torch, NumPy e tokenizers:

```bash
python experimentos/retencao_contrastes_20261008/rodada.py preparar --laboratorio /tmp/crivo-retencao-repro
python experimentos/retencao_contrastes_20261008/rodada.py treinar --laboratorio /tmp/crivo-retencao-repro
python experimentos/retencao_contrastes_20261008/rodada.py avaliar --laboratorio /tmp/crivo-retencao-repro
```

Crie a pasta do laboratório antes de preparar. O roteiro conserva checkpoints com Adam/RNG a cada 100 passos localmente; nesta tentativa não implementa uma opção de retomada automática. São publicados pesos escolhidos, dados, relatórios e protocolo, sem checkpoint completo de otimização. Dependências de arquitetura, normalização e decoder vêm das rodadas próprias conservadas na mesma branch. Mudança de plataforma/versão de Torch pode mudar os pesos resultantes.

A pontuação nas versões aumentadas é perturbada por prefixo: elas são exemplos supervisionados independentes com os mesmos fatos, não rollouts de um histórico textual idêntico entre prefixos. A seleção usa médias de contratos, não as sessões completas do dev. As sessões completas do teste prospectivo e dos painéis conhecidos usam históricos consistentes.

## Resultado executado

| Condição | Novo | Sessões completas novas | Associação conhecida | Contextual conhecido |
|---|---:|---:|---:|---:|
| anterior | 148/370 (40.0%) | 0/80 | 248/400 | 379/400 |
| retencao | 211/370 (57.0%) | 8/80 | 295/400 | 391/400 |

| Evento novo | Anterior | Retenção |
|---|---:|---:|
| confirmacao | 4/20 | 16/20 |
| consulta | 4/20 | 9/20 |
| correcao | 47/90 | 69/90 |
| declaracao | 65/80 | 60/80 |
| hipotese | 14/90 | 35/90 |
| retorno | 14/70 | 22/70 |

400 atualizações concluídas; checkpoint selecionado no passo 400; 499.3 segundos de CPU; 657,047 apresentações de tokens de entrada, incluindo repetições; 4,236 índices de exemplos distintos vistos (não semanticamente únicos).

Critérios: `{"cada_evento_critico_80pct": false, "cada_familia_80pct": false, "aumento_sessoes_pp": 10.0, "queda_maxima_regressoes_pp": -3.0000000000000027}`. Passou o critério sintético: `False`. **Sem aprovação/ativação para chat.**

As previsões completas estão em `avaliacao/`. Não compare os percentuais dos diferentes novos painéis como se fossem o mesmo teste. O novo Colab permite inspecionar esses pesos treinados em CPU; foi conferido localmente, não executado em Colab real.

A verificação local do runner do caderno executou os cinco turnos guiados. Nos quatro primeiros os valores/escopo foram corretos; no quinto voltou a 41, embora 19 já tivesse sido confirmado como fato. Essa falha foi conservada em `verificacao_caderno.json` e indicada no notebook. Validação funcional do caderno não é aprovação semântica do modelo.
