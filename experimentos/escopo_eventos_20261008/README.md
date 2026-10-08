# Correções, hipóteses e confirmação de fatos

Continuação dos pesos **próprios** de `associacao_fatos_20261008/candidato_normalizado`. Não usa modelo ou API externo. O corpo permanece o transformer causal próprio de 2.612.352 parâmetros; com ponteiros, operação, escopo e a nova cabeça auxiliar de seis eventos são 2.948.374 parâmetros. A cabeça auxiliar adiciona 1.158 parâmetros. Não há supervisão de redação causal nesta rodada.

## Problema e método

Na rodada anterior, o candidato normalizado acertou 248/400 contratos no painel de associação. Entre os erros de correção, 47 envolviam escopo; entre os de hipótese, 49. Os testes antigos passam a ser painéis conhecidos de regressão, não evidência nova e independente.

Agora as sessões têm quatro ou cinco falas, em oito ordens distintas: correções repetidas, hipótese antes da correção, consultas mantendo o cenário, retorno aos fatos e confirmação de uma alternativa como fato sem repetir seus valores. Uma correção explicitamente factual encerra o cenário hipotético; cada nova hipótese parte dos fatos; o retorno preserva a última correção ou confirmação real. O gerador registra a fonte de cada argumento.

Foram preparados 1.000/80/120 sessões de treino/validação/teste (4.623/369/552 prefixos). Vocabulários de entidades e bancos de frases são separados; valores do teste são de 351 a 549 e os de treino de 10 a 189. As oito regras de trajetória são compartilhadas. Autoria e gramática são compartilhadas: **não é avaliação independente**. Cada partição rejeitou uma sessão inteira; não houve truncamento. O manifesto conserva a contagem. Foram verificados 5.544 roundtrips de fonte e execuções de referência.

A normalização antiga confundia palavras funcionais, como `Estou` e `Refaça`, com entidades. A nova cópia local amplia a lista de palavras funcionais antes do treino, preservando offsets das falas brutas. É uma heurística de nomes de uma palavra capitalizada, até oito candidatos, e não reconhecimento geral de entidades. O código antigo permanece intacto.

## Dois braços controlados

Ambos começam com os mesmos pesos e inicialização da cabeça auxiliar. Semente 20261012, AdamW, lr 0,0001, 600 atualizações, lote 16. Cada lote contém dois exemplos de cada um dos seis eventos novos e quatro exemplos de replay do treino contextual antigo. A sequência de lotes é igual nos dois braços.

| Braço | Perda operação | Perda ponteiros | Perda escopo | Perda evento |
|---|---:|---:|---:|---:|
| controle | 1 | 0,8 | 0,2 | 0 |
| eventos | 1 | 0,8 | 1 | 0,5 |

A comparação muda conjuntamente a perda de escopo e a supervisão auxiliar; não isola qual das duas explica uma diferença. A cabeça de eventos não substitui o escopo ou fontes pelo alvo. Nenhum rótulo de evento, argumento ou escopo é fornecido como entrada neural. O decoder enumera trechos de gramática finita nas falas; a rede escolhe as fontes; um executor fechado calcula o resultado. Os números desse conjunto não medem só o transformer.

O checkpoint é escolhido a cada 100 atualizações por 70% da média de acerto dos seis eventos do novo dev e 30% da média das famílias do dev contextual. Os treinos não abrem o teste. Protocolo, hashes, critérios e orçamento foram congelados antes de pontuar o teste.

## Critério registrado

Exigir pelo menos 80% em cada evento crítico (correção, hipótese, retorno e confirmação), 80% em cada domínio, aumento de 20 pontos percentuais nas sessões completas versus os pesos iniciais com o mesmo preparo, e queda máxima de cinco pontos nos dois painéis conhecidos. Mesmo cumprir esse critério sintético não constitui aprovação para conversa livre.

A avaliação conserva quatro condições: anterior com preparo antigo, anterior com preparo novo, controle e eventos. Para cada uma publica saídas brutas e com cópia limitada nos três painéis. O acerto de contrato exige operação, valores, origem dos argumentos, referente e escopo corretos; o referente permite diferentes menções ao mesmo nome. Métricas só de resultado executado podem ser mais altas e não substituem o contrato.

## Reprodução

Na raiz do repositório, com Torch, NumPy e tokenizers disponíveis:

```bash
python experimentos/escopo_eventos_20261008/test_contratos.py
python experimentos/escopo_eventos_20261008/dados.py /tmp/crivo-eventos-repro/dados
python experimentos/escopo_eventos_20261008/treino.py --dados /tmp/crivo-eventos-repro/dados --saida /tmp/crivo-eventos-repro/controle --braco controle
python experimentos/escopo_eventos_20261008/treino.py --dados /tmp/crivo-eventos-repro/dados --saida /tmp/crivo-eventos-repro/eventos --braco eventos
```

`--retomar` exige o checkpoint completo local `retomada.pt` da mesma execução e verifica a assinatura. Esses checkpoints de Adam/RNG ficam no laboratório local; são publicados os pesos escolhidos, dados, protocolo e relatórios. Para repetir a avaliação, copie o `protocolo.json` publicado para a raiz do laboratório da reprodução; execute `avaliar_eventos.py --laboratorio /tmp/crivo-eventos-repro`. A avaliação recusa pesos sem os dois treinos completos e sem os hashes correspondentes. Não espera reproduzir exatamente pesos em outra plataforma/versão de Torch.

O caderno `notebooks/crivo_correcoes_hipoteses.ipynb` carrega os candidatos treinados e inspeciona falas editáveis em CPU. Não inicia treino. Foi conferido localmente; não foi executado numa sessão real do Colab. Os pesos ativos de `artefatos/linguagem_profunda` permanecem intactos. A geração livre da rodada anterior não recebeu novo treino aqui, e suas falhas continuam registradas.

## Resultados da execução

| Condição | Novo: contratos | Novo: sessões completas | Associação conhecida | Contextual conhecido |
|---|---:|---:|---:|---:|
| anterior_preparo_antigo | 299/552 (54.2%) | 17/120 | 248/400 | 379/400 |
| anterior_preparo_novo | 290/552 (52.5%) | 21/120 | 248/400 | 379/400 |
| controle | 281/552 (50.9%) | 8/120 | 219/400 | 370/400 |
| eventos | 272/552 (49.3%) | 8/120 | 216/400 | 373/400 |

| Evento novo | Anterior/preparo novo | Controle | Eventos |
|---|---:|---:|---:|
| declaracao | 107/120 | 107/120 | 99/120 |
| correcao | 51/136 | 77/136 | 76/136 |
| hipotese | 59/134 | 34/134 | 21/134 |
| retorno | 51/107 | 27/107 | 38/107 |
| consulta | 17/28 | 13/28 | 16/28 |
| confirmacao | 5/27 | 23/27 | 22/27 |

**controle**: 600 atualizações completas; checkpoint escolhido no passo 300; 707.0 segundos em CPU; 912,627 apresentações de tokens de entrada (inclui repetições), 4,248 entradas distintas amostradas. Critérios: `{"eventos_criticos_80pct": false, "familias_80pct": false, "aumento_sessoes_completas_pp": -10.833333333333332, "queda_maxima_paineis_conhecidos_pp": 7.250000000000001, "passou_criterio_sintetico": false, "aprovado_para_chat": false}`.

**eventos**: 600 atualizações completas; checkpoint escolhido no passo 600; 877.9 segundos em CPU; 912,627 apresentações de tokens de entrada (inclui repetições), 4,248 entradas distintas amostradas. Critérios: `{"eventos_criticos_80pct": false, "familias_80pct": false, "aumento_sessoes_completas_pp": -10.833333333333332, "queda_maxima_paineis_conhecidos_pp": 7.9999999999999964, "passou_criterio_sintetico": false, "aprovado_para_chat": false}`.

Contagens por evento usam só os prefixos daquele evento. A coluna de sessões exige todos os quatro ou cinco prefixos corretos. As cabeças auxiliares dos pesos anteriores e do controle não foram treinadas; sua acurácia de evento não serve como evidência de capacidade. Uma semente, nenhum intervalo de confiança.

**Nenhum peso foi aprovado para chat ou copiado para os artefatos ativos.** `avaliacao/resumo.json` registra os resultados brutos e limitados, critérios e diagnóstico por escopo/argumento. Os traces completos e os dados permitem reconstruir cada falha.
