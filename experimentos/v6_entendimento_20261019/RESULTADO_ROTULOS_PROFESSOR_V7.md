# v7e — rótulos do professor corrigidos (27/10/2026)

Pedido do criador: "pode analisar o crivo e me dizer se consegue treinar ele ou deixar ele mais inteligente?", depois
"faz tudo". Só a GPU T4 está disponível até a A100 voltar.

Nada foi treinado, promovido ou ligado. Todo o trabalho foi feito na CPU: ler os dados, gerar os dados e preparar o notebook.
O treino é do notebook `notebooks/treino_v7e_entendimento_colab.ipynb`, e os pesos só vão para o chat pela régua própria
e por decisão do criador.

## Resposta curta

A auditoria de 19/10 mostrou que o limite do CRIVO está no que ele entende das falas, e que isso vem dos dados. O v7c
foi o primeiro a passar porque trouxe falas novas, a maioria escritas pelo professor (Qwen3-32B-AWQ). Quem conferiu essas
falas foi o próprio professor. Li uma a uma, ao lado da resposta que cada situação ensina, as **6.838 falas do professor
que entraram no v7c** (4.769 no treino, 663 no dev e 1.406 no blind_v6). **601 tinham rótulo errado ou duvidoso (8,8%)**.
O erro se concentra nas situações de identidade e de conversa social, justamente as que o v7c perdeu (identidade −3,5 a
−4,4 pontos) ou nunca acertou (insulto 0%, perguntar_crivo 19%). O v7e repete a receita do v7c com essas falas
corrigidas. É um treino de 46M que cabe na T4.

## O que estava errado

| motivo | falas | exemplo (situação → o que a resposta ensina) |
|---|---|---|
| a pessoa conta algo dela | 145 | `nao_gosta`: "Me cansa muito quando as pessoas usam o tempo dos outros sem pedir." → "Não gosto de mentira… E você?" |
| estranha ou sem sentido | 126 | `posso_falar`: "pode pq eu sou pq nem tanto bom?"; `criador`: "Ateu que inventou você trabalha sozinho?" |
| é de outra situação | 73 | `fome`: "Qual o melhor lugar pra comer aqui perto?" → "Fome é sinal pra parar e cuidar de você" |
| pede um assunto específico | 44 | `o_que_faz`: "você sabe falar sobre como nasce uma montanha" → "Bato papo, explico assuntos…" |
| afirmação, não pergunta | 43 | `opiniao_vida`: "pra mim, viver é só ir passando o dia" → "Essa é das minhas perguntas favoritas" |
| vaga | 22 | `dinheiro_bom`: "estou mais tranquilo" |
| o pedido já veio dito | 21 | `sim_continuar`: "Vou viajar pra Argentina e quero planejar tudo direitinho, me dá dicas" → "O que você quer saber?" |
| o pedido ao professor vazou | 20 | `criador`: "…quem foi a pessoa que, com suas próprias mãos, criou o CRIVO, do zero, sem usar nada pré-existente?" |
| memória que não existe | 17 | `lembra`: "Você lembra que eu te disse que tenho dois irmãos e um cachorro chamado Ralf?" → "Nesta conversa eu lembro, sim." |
| a pessoa conta uma piada | 15 | `piada`: "pq o 8 ta sempre feliz? pq ele é 8-muito" → o CRIVO conta outra |
| sem pedido | 13 | `poema`: "Tive um dia sem compromissos e me senti tão leve…" |
| responde a um turno que não existe | 11 | `oi_tudo_bem`: "Estou bem, obrigado. E com você, como está o dia?" (sem histórico) |
| rótulo trocado | 9 | `amor_dor`: "ela me escolheu de novo" → `amor_bom`; `gosta`: "Admiro tu, sabe?" → `elogio_crivo` |
| fragmento sem contexto | 9 | `opiniao_politica`: "mt estranho isso" |
| "sim" falso | 9 | `ser_ia`: "Tu não é um chatbot desses do Google?" → "Sou, sim…" |
| insulto sem alvo | 7 | `insulto`: "péssimo pra caramba", "isso é um absurdo" |
| conteúdo adulto | 5 | `filme_visto`: "…filme pornô…" → "Quero saber! Como foi?" |
| preconceito | 4 | `opiniao_politica`: "Você acha que um nordestino pode governar direito o Brasil?" → "Prefiro não tomar partido" |
| outros (inapropriada, risco, pedido legítimo em `recusar`, erro de fato, resposta do CRIVO como fala da pessoa) | 8 | `piada`: "O que o zero disse pro oito? Que cinto bonito! Desculpa, essa foi fraca." |

Situações com mais correções: musica_crivo 41, criador 23, gosta 23, nunca_ensinaram 23, o_que_faz 22, ser_ia 22,
cor_favorita 21, opiniao_politica 20, lembra 18, opiniao_vida 18, piada 18, posso_falar 18.

**Fora do treino, mas importante:** duas falas de risco estavam rotuladas como insulto: "Não vejo como seguir com isso"
e "não me aguento mais". O `crise.py` não pegava "não me aguento mais", "não vejo como seguir com a vida" nem "não vejo
sentido em continuar". Isso foi corrigido no mesmo PR, com testes. Uma varredura de 428 mil falas do repositório e do
professor mudou o resultado de só duas, e as duas estavam erradas antes.

## O que foi feito

- `rotulos_professor_v7.py` e `correcoes_professor_v7.json`: 601 decisões, 592 "fora" e 9 com troca de situação. Uma fala
  repetida no arquivo do professor faz 602 linhas saírem. No repositório fica só o sha256 de "situação<TAB>fala", e o
  texto do professor continua fora do git, como o arquivo dele. A lista legível, com as falas, fica em
  `correcoes_professor_v7_legivel.csv`, ao lado do arquivo do professor.
- `gerar_v7e.py`: o `gerar_v7c.py` com as correções aplicadas **antes de qualquer filtro**, a mesma semente e o manifesto
  separando o dev e o blind_v6 por origem. Sem o professor, os dados do v7e são caso a caso iguais aos do v7c. O sha do gz
  muda só porque o nome do arquivo vai no cabeçalho do gzip.
- `notebooks/treino_v7e_entendimento_colab.ipynb`: a receita do v7c, com quatro mudanças fixadas antes de rodar: os dados
  v7e, a régua contra o v7c do chat (como na fase 7d), a guarda do dev sem as falas do professor e o checkpoint a cada 150
  passos em GPU com menos de 20 GB.
- `testes_rotulos_professor.py`: o arquivo de correções só tem hashes, as decisões são válidas, `aplicar()` funciona e o
  manifesto confere.

## Números (gerados aqui com o arquivo do professor, sha `b980bae0dc45…`)

| | v7c | v7e |
|---|---|---|
| treino: casos (professor / assistente) | 31.205 (19.076 / 12.129) | 29.514 (17.364 / 12.150) |
| treino: falas do professor | 4.769 | 4.341 |
| dev: casos (professor / assistente) | 875 (663 / 212) | 819 (607 / 212) |
| blind_v6: casos (professor / assistente) | 2.090 (1.406 / 684) | 1.978 (1.294 / 684) |

A geração do v7c reproduzida aqui (Python 3.8, CPU) deu 31.205 casos de treino contra 31.201 no log do Colab, e 4.769
falas do professor contra 4.768. A diferença deve ser de ambiente e não muda a conclusão. O v7e no Colab vai ser gerado de
novo lá, com o manifesto e os shas conferidos.

**O dev da guarda:** no v7c, 76% do dev era do professor, e a guarda escolhia o passo pelo jeito de falar dele. No v7e, a
guarda usa o dev da fase 5 mais as 212 falas do assistente no dev, e as do professor seguem nos relatórios. Não dá para
saber, sem os checkpoints do v7c no Drive, se a guarda antiga teria escolhido outro passo.

## Limites

- **A revisão é do assistente (Claude), não humana nem cega.** O critério foi a resposta da situação servir ou não para a
  fala. Em casos de fronteira (insulto × queixa de não entender, entediante × insulto), deixei o rótulo do professor.
- **O blind_v6 também mudou** (112 casos a menos). O blind_v6 do v7e não é o mesmo do v7c, mas os blinds que decidem
  (v1, v3, paráfrases, Grok, v4 e frases reais) não mudaram.
- **Não resolve tudo:**
  - insulto, entediante, nao_entendeu_queixa e voce_confunde se sobrepõem na própria definição das situações, e mais
    dados não resolvem isso;
  - `sem_sentido` continua sendo quase só teclado aleatório ("asdfghjkl"), e frase sem sentido de verdade (como
    "Palarerepípedo") continua sem exemplos;
  - falas que não são do professor (assistente, fase 5) não foram relidas.
- Se o v7e não passar na régua, a conclusão é que limpar 9% do professor não basta, e o v7c continua no chat.

## Como rodar (T4)

1. Colab → Ambiente de execução → **T4** → Executar tudo (rodada 1). Precisa da fase 6a, do v7c do chat
   (`transformer-crivo-46m-conversa-v7c`, sha `e4067e3b…`) e de `dados-professor-v7/falas_professor_v7.jsonl.gz` no Drive.
   São os mesmos arquivos do v7c, e nada novo precisa ser enviado.
2. Se o Colab cair, "Executar tudo" de novo continua do último checkpoint (a cada 150 passos na T4).
3. Quando a rodada 1 terminar, Executar tudo de novo faz a rodada 2 (o notebook escolhe sozinho). O resumo diz se
   passou nas duas rodadas contra o v7c.
