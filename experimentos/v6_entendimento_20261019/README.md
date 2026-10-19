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
