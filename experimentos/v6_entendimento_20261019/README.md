# Treino v6 "entendimento" — plano e critérios, registrados antes de rodar (19/10/2026)

Pedido do criador: "monta o notebook do treino v6 entendimento, permito que você escreva as frases que seriam
minhas porque confio em você". Origem: a auditoria `experimentos/auditoria_treino_20261019/RELATORIO.md`.

**Ainda não foi executado.** Nenhum peso foi treinado, alterado ou ligado.

## Hipótese

O 46M do chat entende a situação certa em 69% das frases nunca vistas (sonda linear) e acerta 66% respondendo. O
limite é o entendimento, e o único salto grande registrado (fase 5 v2) veio de mais jeitos de a pessoa dizer a mesma
coisa. **Se a hipótese estiver certa, falas novas da pessoa, com as mesmas respostas, sobem o blind v3** (que não tem
nenhuma dessas falas) sem piorar o resto.

## O que foi feito

| arquivo | o que é |
|---|---|
| `formas_v6.py` | 876 falas da pessoa em 61 situações, **escritas pelo assistente de programação (Claude) com autorização do criador. Não são falas humanas.** |
| `gerar_v6.py` | monta os casos, com as respostas das listas existentes, e confere conflitos e vazamentos |
| `dados_v6.json.gz`, `manifesto_v6.json` | dados gerados (reproduzem byte a byte) |
| `comparar_v6.py` | IC 95%, comparação pareada, vizinhas aceitas e critérios |
| `notebooks/treino_v6_entendimento_colab.ipynb` | o treino |

**Falas:** foco nas situações em que o 46M e a v3 D mais erram (cansado, insulto, seja_breve, sem_sentido,
trabalho_ruim, flerte, perguntar_crivo, despedida…) e nos pares que eles confundem (oi × oi_tudo_bem × estou_bem,
tenho_bicho × gosto_bichos × bicho_favorito, comida_crivo × comida_favorita, amor_bom × amor_dor, "você viaja" ×
viagem, "cheguei" × despedida, desisto × desisto_despedida, insulto × despedida_rude). Cada fala é outra construção,
não a mesma frase com erro de digitação; o ruído de digitação e as molduras ("olha, …", "… cara") vêm depois.

**Conferências do gerador (param a geração se falharem):**
- nenhuma fala em duas situações; nenhuma fala que já esteja no treino v3 com outra situação (4 conflitos achados e
  resolvidos seguindo o rótulo antigo);
- nenhuma fala igual a uma frase das réguas congeladas (blind v1, paráfrases, Grok, blind e dev v3, dev e blind v4,
  frases reais do criador): 62 falas saíram por isso;
- respostas só das listas existentes; todos os 9.613 alvos são reconhecidos pela régua de sentido;
- situações com encaixe, de saúde/urgência (crise.py responde antes) e as do IDENTIDADE.md ficam de fora.

**Divisão por fala, antes do ruído:** 558 falas treinam (8.926 casos), 81 vão para o dev (162 casos) e 175 formam o
**blind_v6** (525 casos), que o treino nunca viu em nenhuma grafia.

## Receita (notebook)

A da 6b v4, que está no chat, com estas mudanças:
1. **v6 ×4 no treino** (ocupa o lugar de parte das legendas; o resto não muda);
2. **escolha** pelo sentido em 1.162 frases novas (1.000 do dev da fase 5 + 162 do dev v6), não 400;
3. **duas rodadas**, sementes 20261019 e 20261020;
4. **linha de base pareada:** o 46M v4 é medido no próprio notebook, nas mesmas frases, com o mesmo freio.

Proporção do treino: dados do professor 0%. Falas do v6 ≈ 9 mil casos ×4, contra ~240 mil da fase 5 ×3.

## Critérios para virar candidata (fixados agora, em `comparar_v6.py`)

Nas **duas** rodadas:
1. blind v3: diferença pareada v6 − v4 com limite inferior do IC 95% acima de zero;
2. blind v1, paráfrases, Grok e v4: diferença ≥ −1,5 ponto;
3. frases reais do criador ≥ 12/15;
4. fatos do acervo, "usa o fato" ≥ 0,85.

A conta estrita decide. A conta com vizinhas (lista em `comparar_v6.VIZINHAS`, escrita antes) só é mostrada. O
**blind_v6 não decide**: as falas são do mesmo autor das de treino e medem a lista, não a generalização. Passar nos
critérios não liga nada: `ativo_no_chat` fica falso e quem decide é o criador, depois de ler o lado a lado.

**Leitura da hipótese, também fixada agora:**
- blind v3 sobe ≥ 5 pontos nas duas rodadas → apoio forte;
- sobe, mas < 5 pontos, com IC acima de zero → apoio fraco; o próximo passo é mais falas (ver limites);
- IC cruza zero → sem efeito medido com este volume de falas; não conclui que a hipótese caiu.

## Limites conhecidos antes de rodar

- **Volume pequeno:** 558 falas novas de treino, contra ~17 mil frases diferentes que o treino v3 já tem. A auditoria
  pedia ≥ 500 falas por situação; aqui são 2 a 33 no treino (mediana 7). É um teste da direção, não da dose.
- As falas são de um autor só (o assistente), então têm o jeito dele de escrever. Falas do criador e de outras pessoas
  seriam melhores, e as do professor autorizado (só escrevendo a fala da pessoa) multiplicariam o volume.
- A régua continua sendo a de listas fechadas; respostas boas e diferentes contam como erro.
- As 15 frases reais continuam sendo poucas; juntar 150–300 frases reais do criador é o passo seguinte da régua.

## v6b — correção da rodada 1 (20/10/2026, registrado antes de rodar)

Pedido do criador: "faça direito e conserte onde você piorou". Diagnóstico em `RESULTADO_RODADA1.md`.

| arquivo | o que é |
|---|---|
| `formas_v6b.py` | as falas do v6 sem as que criavam gatilhos (`REMOVER`) e com pares mínimos para as vizinhas que perderam (`ACRESCENTAR`) |
| `gerar_v6b.py` | gerador do v6b; `gerar_v6.py` fica intacto para a rodada 1 continuar reproduzível |
| `dados_v6b.json.gz`, `manifesto_v6b.json` | dados (reproduzem byte a byte) |
| `diagnosticar_v6.py` | o diagnóstico da rodada 1 |
| `notebooks/treino_v6b_entendimento_colab.ipynb` | o treino |

**Mudanças:**
1. **Gatilhos removidos** (13 falas) e **pares mínimos** para amor_bom, estou_bem × reciproco, boa_noite,
   desisto_despedida, nao_consegue, dificil_falar, o_que_faz, quem_sou_eu, estou_mal, voce_confunde e motivacao.
   Nenhuma fala nova fica perto de saúde ou urgência.
2. **Filtro de parecença:** sai toda fala com cosseno de n-gramas ≥ 0,7 com qualquer frase de teste ou dev congelada.
   Saíram 185, inclusive 160 da rodada 1. Assim, ganho no blind não pode vir de quase-cópia.
3. **Equilíbrio:** toda situação de cena fica com pelo menos 112 casos (a média das reforçadas). O que falta é completado
   com falas que já estavam no treino v3: 6.272 casos em 78 situações, nenhum texto novo.
4. Resultado: 462 falas novas no treino (7.390 casos) + 6.272 de equilíbrio; 75 falas no dev (150 casos); 146 falas no
   blind_v6b (438 casos).

**Critérios:** os quatro do v6 e mais um, fixado agora porque a rodada 1 piorou nisso: **urgência sem piorar** (acertos
somados de saude_urgente, ajuda_socorro e ansioso_peito nos blinds ≥ os do v4). Com esse critério, a rodada 1 também
seria reprovada (88 contra 102).

**Limite declarado antes:** as correções foram orientadas pelos erros da rodada 1 nos blinds antigos. O filtro impede
cópia, mas esses blinds deixam de ser totalmente independentes. Por isso, as 15 frases reais e, de preferência, novas
frases reais do criador pesam mais na decisão de levar ao chat.

## v6c — sem sair perdendo (20/10/2026, registrado antes de rodar)

Pedido do criador: "monta o v6c [...] tenta fazer completo pra não sair perdendo". Diagnóstico em `RESULTADO_V6B_RODADA1.md`.

| arquivo | o que é |
|---|---|
| `formas_v6c.py` | as falas do v6b sem 5 gatilhos que o diagnóstico do v6b achou ("tô muito apaixonada" → "tô sangrando muito"…) |
| `gerar_v6c.py` | as regras do v6b, sem equilíbrio; `dados_v6c.json.gz` e `manifesto_v6c.json` reproduzem byte a byte |
| `substituicao_v6c.py` | cada caso novo entra no lugar de casos antigos da fase 5 da mesma situação (as falas antigas mais repetidas saem primeiro) |
| `notebooks/treino_v6c_entendimento_colab.ipynb` | o treino |

**Três proteções:**
1. **Substituição:** o peso de cada situação no treino, contando repetições, fica igual ao da v4. Conferido na CPU com os
   dados da fase 5 v3: mudança máxima 0,00%; falas distintas no treino 34.834 → 37.386. Urgência, saúde, identidade e
   situações da v4 ficam com o mesmo peso;
2. **Parte do 46M do chat** (6b v4, `45825352…`) com ajuste leve: LR 3e-5 → 3e-6, ~1.300 passos, uma volta na fase 5,
   falas novas ×3 no lugar das antigas. (`PARTIDA = "6a"` roda a receita longa desde a base, também com substituição.)
3. **Catraca:** o 46M do chat concorre na escolha (passo 0). Se nenhum passo tiver mais sentido no dev, fica ele e o
   resumo marca `escolhida_e_o_chat: true`.

**Critérios:** os mesmos do v6b, sem mudança: nas duas rodadas, blind v3 com IC > 0; v1, paráfrases, Grok e v4 ≥ −1,5;
frases reais ≥ 12/15; "usa o fato" ≥ 0,85; urgência sem piorar.

**Diferença de desenho em relação ao v6/v6b:** partir do 46M do chat mede "o 46M do chat + um ajuste com falas novas",
não "a receita da v4 com falas novas". Isso é o que interessa para o chat, mas o efeito do ajuste e o das falas não se
separam aqui.

## v7 — volume, com o professor só para falas da pessoa (20/10/2026, registrado antes de rodar)

Pedido do criador: "não tá parecendo que você tá se esforçando pra fazer ele ganhar". Reconhecimento: o v6–v6c testaram
uma dose pequena demais (mediana de 7 falas novas por situação, contra centenas pedidas pela auditoria), e os gatilhos só
foram achados depois de gastar GPU. O v7 ataca as duas coisas.

| arquivo | o que é |
|---|---|
| `formas_v7_a.py` … `formas_v7_e.py`, `formas_v7.py` | 1.956 falas escritas pelo assistente nas 108 situações elegíveis (com as do v6c) |
| `detector_gatilhos.py` | barra, ANTES do treino, falas mais parecidas com o treino de outra situação do que com o da própria (≥ 0,5), ou perto de saúde/urgência (≥ 0,4); situações compostas (despedida rude, "tô bem, e você?"…) liberadas. Sem olhar os testes, pegou 9 dos 17 culpados conhecidos do v6/v6b |
| `professor_v7.py` | o professor escreve só falas da pessoa (8 estilos × 108 situações × 25) e confere o próprio rótulo entre 5 respostas (as alternativas são as confusões medidas) |
| `gerar_v7.py` | junta as falas, com filtros de conflito, parecença com testes (≥ 0,7), gatilhos e saúde; `--professor` acrescenta as do professor, cada uma com origem |
| `notebooks/professor_v7_colab.ipynb` | o professor (vLLM 0.31.0, a versão que funcionou na destilação), em sessão própria, com a saída ao vivo |
| `notebooks/treino_v7_entendimento_colab.ipynb` | lê as falas do professor do Drive → dados → treino desde a base 6a com substituição → régua |

**Sem o professor** (conferido aqui): 760 falas minhas no treino, 113 no dev, 227 no blind. **Com professor falso no
ensaio de CPU**, a cadeia inteira rodou (pedidos, leitura, filtro de saúde, conferência, arquivo com origem, gerar_v7,
manifesto); o número real de falas do professor só sai no Colab.

**Regras do professor (AGENTS.md):** Qwen3 (Apache 2.0), escolhido o maior que couber; pesos só no disco do Colab;
`CRIVO/dados-professor-v7/` com modelo, revisão, data e licença em cada linha; nunca chamado de humano; respostas do CRIVO
nunca vêm dele; a fração do treino de conversa vinda dele vai para o resumo (`professor_fracao_exposicoes`).

**Critérios:** os mesmos do v6b/v6c, sem mudança (blind v3 com IC > 0 nas duas rodadas; v1, paráfrases, Grok e v4 ≥ −1,5;
frases reais ≥ 12/15; "usa o fato" ≥ 0,85; urgência sem piorar). O blind v7 (falas novas minhas e do professor) é mostrado,
não decide.

**Limites declarados antes:** a conferência de rótulo é do próprio professor (não é humana); as falas do professor têm o
jeito dele; as correções do v6b/v6c foram guiadas por erros nos blinds antigos (o filtro de parecença impede cópia).

**Correção de 20/10 (primeira tentativa no Colab):** com o professor num ambiente `uv` separado, nenhum dos quatro modelos
carregou, e o notebook não mostrava o motivo (a saída do processo filho não aparecia). O professor passou para um notebook
próprio, com o vLLM instalado como na destilação e a saída ao vivo; o treino roda depois, numa sessão nova, sem vLLM.
