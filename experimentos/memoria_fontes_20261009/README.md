# Hipóteses e validade das fontes

Continua o checkpoint próprio de retenção, que acertou 295/400 no painel de associação e 391/400 no contextual. Essa rodada não usa modelo, tokenizer, pesos ou API externos. NumPy, Torch e tokenizers são infraestrutura. Nenhum peso ativo do chat é alterado.

## Problemas investigados

No teste conhecido de retenção, hipóteses de requisitos acertavam 6/45: em 35 falhas os argumentos estavam certos, mas a resposta era marcada como fato. No retorno aos fatos, preços e requisitos faziam 11/35 cada; frequentemente copiavam uma fonte hipotética recente. Consultas como “Entre A e B, apresente a diferença.” não reorganizavam os símbolos: os 21 casos de preços com ordem invertida dos aliases acertavam 0/21.

A normalização local agora reconhece consultas explícitas terminadas em ponto e frases nominais com dois nomes sem números. Continua uma heurística limitada a oito nomes de uma palavra capitalizada, preservando os offsets das falas originais. Não é reconhecimento geral de entidades. A avaliação mede os mesmos pesos com preparo antigo e novo para separar essa alteração do treinamento.

## Arquitetura e treino

São **3.084.066 parâmetros**, sendo **135.692 treináveis** nesta rodada. O corpo e todas as cabeças anteriores permanecem congelados e com dropout desligado. O mesmo transformer próprio lê o histórico e a última fala, selecionada pelo delimitador inserido na entrada. Um MLP combina as duas representações. A nova cabeça de evento participa desse MLP compartilhado; um delta de escopo corrige a classificação anterior.

Uma cabeça de baixa dimensão prevê validade por token em três bancos — factual, alternativa e ativo — e quatro papéis — três argumentos e referente. As fontes de um banco podem se sobrepor às de outro; a supervisão é multi-label. A confirmação promove uma fonte da hipótese a fato sem repetir seu valor. Na inferência, só o banco ativo acrescenta um viés suave aos ponteiros anteriores. Não há exclusão por gold ou controlador de evento correto. A forma `2*(logsigmoid(validade)+log(2))` conserva logits na inicialização; permite aumentar no máximo 1,386 e penalizar sem limite negativo. Não usa o escopo previsto como gate de fonte.

Esses bancos são supervisão de uma representação neural recalculada do histórico; **não constituem memória persistente explícita**. A inferência recebe somente IDs e comprimentos derivados das falas. Evento, banco gold, trajetória (que contém futuros eventos) e spans corretos nunca entram nas features. Os testes verificam invariância das previsões quando os rótulos são alterados.

800 sessões de treino/3.700 prefixos, 80 de dev/370 prefixos; contraste de hipóteses que não aconteceram, correções que não são hipóteses, confirmação e retorno em ordens diferentes. Bancos de frases/vocabulários diferentes entre treino e dev. Replay: 2.000 exemplos de associação e 1.000 contextuais. Bancos factual/alternativo do replay são mascarados; só sua fonte ativa recebe supervisão. Os papéis de cada sessão de treino mantêm a mesma ordem das entidades. Nenhuma sessão foi truncada ou rejeitada. Não há diálogos privados, respostas de outro modelo ou treino causal de redação.

Ambos os braços usam a mesma arquitetura/inicialização, semente 20261015 e sequência de lotes. 400 atualizações, AdamW, lr0,0005, lote20: um exemplo de cada evento/domínio (12 novos), quatro de associação e quatro contextuais. Ponteiros0,8; escopo0,5 com peso de classes1/2; evento0,2; KL0,25 de escopo/ponteiros no replay usando a saída das próprias cabeças antigas congeladas como professor.

| Braço | BCE balanceada de bancos |
|---|---:|
| controle | 0 |
| fontes | 0,3 |

A BCE separa médias de tokens positivos e negativos por banco/papel, mascarando padding e bancos sem rótulos confiáveis. A comparação dos braços mede essa supervisão auxiliar. Ambos já incluem a nova adaptação de escopo/fontes; comparar com o checkpoint anterior mede o conjunto da adaptação. Não isola todas as causas.

Seleção a cada100: 60% da média dos quatro eventos críticos × dois domínios no novo dev, 25% da média das famílias de associação dev e 15% das contextuais. Empate mantém o primeiro checkpoint. A escolha entre braços para a inspeção também usa dev, antes de abrir o teste. Corpos e cabeças herdadas devem permanecer bit a bit iguais ao checkpoint inicial ao final.

## Avaliação prospectiva

80 sessões/408 prefixos, 4–6 turnos, escritas por outro agente sem acesso a previsões; casos, gerador e protocolo ficaram fechados para a raiz até concluir os dois treinos e a seleção. Isso oferece outra autoria dentro da mesma equipe e gramática limitada, **não avaliação externa independente**. Preços/requisitos, nomes de uma palavra, valores inteiros, dois itens de requisitos, contexto máximo de226 tokens no preparo original. Há distratores, consultas, confirmação e retorno. Uma semente; prefixos correlacionados, sem intervalo de confiança.

Critério registrado antes dos treinos: pelo menos80% em cada correção/hipótese/retorno/confirmação e família; aumento de20 pontos percentuais nas sessões completas versus os pesos anteriores com o mesmo preparo; queda máxima de5 pontos nos três painéis conhecidos. Mesmo cumprir esse critério sintético não aprova o chat ou conversa livre.

Quatro condições × quatro painéis × bruto/limitado. Os painéis de retenção370, associação400 e contextual400 já eram conhecidos e servem à regressão. O contrato exige operação, literal e turno dos argumentos, referente literal e escopo; a origem exata por turno/início/fim/literal também é publicada separadamente. Os acertos com cópia limitada combinam rede, enumerador de trechos da gramática e executor fechado.

## Reprodução

Na raiz, com Torch, NumPy e tokenizers, em uma pasta nova:

```bash
mkdir -p /tmp/crivo-memoria-repro
python experimentos/memoria_fontes_20261009/corpus_memoria.py /tmp/crivo-memoria-repro/dados_validos
```

Copie `protocolo.json` publicado e `avaliacao_autoria/` para essa pasta. Os hashes devem corresponder. Então:

```bash
python experimentos/memoria_fontes_20261009/test_integridade.py
python experimentos/memoria_fontes_20261009/treino_memoria.py --laboratorio /tmp/crivo-memoria-repro --braco controle
python experimentos/memoria_fontes_20261009/treino_memoria.py --laboratorio /tmp/crivo-memoria-repro --braco fontes
python experimentos/memoria_fontes_20261009/avaliar_memoria.py --laboratorio /tmp/crivo-memoria-repro --protocolo-sha256 6b20ecef9f61b5bfb51731a0c5c8a17d5dd7e17a7c055b211760f3fb65228fb8
```

`--retomar` no treino conserva Adam, RNG, estado corrente, melhor estado e histórico. Checkpoints completos permanecem no laboratório local; publicam-se pesos escolhidos, dados, relatórios, protocolos e todos os traços. Outra plataforma/versão pode mudar os pesos treinados. O notebook `notebooks/crivo_memoria_fontes.ipynb` carrega os candidatos já treinados em CPU, sem iniciar treinos. É verificado localmente, não numa sessão real do Colab.

## Resultado concluído e decisão

Ambos terminaram400 passos e viram os mesmos766.693 tokens/4.334 entradas distintas. O controle escolheu400 e o braço fontes300. A escolha anterior ao teste foi controle, notaDEV0,753880 contra0,749186; isso permanece registrado, mesmo com o resultado abaixo. Tempo de treino: controle393s, fontes343s, concorrentes em duas CPUs.

| Condição | Prospectivo408 | Sessões80 | Retenção conhecida370 | Associação400 | Contextual400 |
|---|---:|---:|---:|---:|---:|
| anterior_preparo_antigo | 247 | 14 | 211 | 295 | 391 |
| anterior_preparo_novo | 247 | 14 | 230 | 295 | 391 |
| controle | 229 | 6 | 248 | 255 | 356 |
| fontes | 240 | 9 | 253 | 263 | 376 |

**Rejeitados os dois candidatos.** O controle melhora hipóteses68→90/104, mas piora correções36→23/64 e confirmações26→12/40. O braço fontes também fica abaixo do anterior no total. Nenhum cumpre o critério registrado. O controle perde10pp em associação e8,75pp no contextual. A supervisão auxiliar não demonstrou melhora geral. Não use essas notas de dev como aprovação de generalização.

O preparo novo sozinho recupera19 contratos no painel conhecido de retenção,211→230/370, e conserva os outros três totais. É efeito da normalização heurística, não do treino, e não é ganho prospectivo. Preservam-se os pesos anteriores para continuidade.

Na sequência de inspeção do notebook,23→41→hipótese19→confirmação19, o retorno final ainda copia41 quando deveria manter19. Ambos anterior/controle passam quatro primeiros passos e falham o quinto. `verificacao_caderno.json` conserva fontes e resultados. O evento do baseline fica sem previsão útil, pois sua cabeça nova não foi treinada.

A continuação em `../memoria_explicita_20261009` investiga estado factual e alternativo explícito, mantendo esta rodada e seus erros intactos. Seus resultados serão de sistema híbrido, sem atribuir regras de memória a aprendizado neural.
