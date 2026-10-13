# Salto do Transformer 17M do CRIVO

## Onde queremos chegar

Um modelo próprio do CRIVO (arquitetura, tokenizador e pesos próprios, sem modelo ou API
externa) que converse em português no chat, preserve nomes e fatos que o usuário acabou de
dizer, pare quando terminou e não invente — com aprovação real, não com gate fácil.

## Insight (skill `insight-entidade-internet`)

- **Antes eu acreditava:** a base sabe ler o contexto e o problema é a interface de saída
  (tokenização do nome, falta de parada); por isso valia pôr cabeças em cima da base congelada.
- **A pesquisa mostrou:** a cópia em contexto (`[A][B] … [A] → [B]`, *induction heads*) é uma
  capacidade do próprio Transformer que se forma no pré-treino, numa mudança de fase visível
  como um degrau na perda; na fonte original ela aparece por volta de 2,5–5 bilhões de tokens,
  e um estudo com modelos de 1B a situa perto de 20B. O ponto de formação depende de lote,
  contexto e da frequência/confiabilidade de repetições nos dados — não do tamanho do modelo.
  Esquecimento no ajuste fino é sobretudo problema de capacidade, pior em modelos pequenos, e
  é reduzido por replay de dados de pré-treino ou do próprio modelo com KL.
- **Eu não sabia:** que essa capacidade tinha um "momento" mensurável de formação, nem a escala
  em que ela costuma aparecer; e que a base do CRIVO tinha visto só ~0,33 bilhão de tokens
  (20.000 passos × 64 × 256), menos da metade do corpus próprio já montado (~0,9 bilhão).
- **Medição feita aqui (CPU, pesos do leitor 17M do repositório):** repetindo 50 tokens
  aleatórios, o modelo acerta **26,7%** na 2ª vez (controle aleatório: 0%); nome inventado
  cai de 7,7 para 2,6 nats na 2ª menção. A capacidade existe, mas fraca.
  Arquivo: `sonda_copia_leitor_17m.json`.
- **Isso muda:** o gargalo não é falta de cabeça, é a base sub-treinada para copiar. As nove
  rodadas compensavam de fora uma habilidade fraca por dentro; o v4 mostrou o custo disso
  (as cabeças aprendem a tarefa e quebram o resto). A prioridade passa a ser fortalecer a
  própria base e só depois ajustar o diálogo **com a base inteira treinável e replay**.

Previsão testável: com mais pré-treino (e repetição nos dados), a cópia top-1 da sonda sobe;
se subir, as tarefas de nome do v3 melhoram na própria base, sem cabeça. Se não subir, a
hipótese cai e o limite está em outra parte (capacidade, contexto de 256, dados).

Fontes: [In-context Learning and Induction Heads](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html),
[Predicting the Emergence of Induction Heads in Language Model Pretraining](https://arxiv.org/pdf/2511.16893),
[When Do Attention Circuits Form? (1B-class)](https://arxiv.org/pdf/2606.02378),
[TinyStories](https://arxiv.org/pdf/2305.07759),
[Mix Early, Forget Less](https://iclr.cc/virtual/2026/10019715),
[Byte BPE Tokenization as an Inverse String Homomorphism](https://arxiv.org/pdf/2412.03160).

## Fases

| Fase | O que faz | Meta para avançar | Estado |
|---|---|---|---|
| 1. Diagnóstico | sonda de cópia (`scripts/sonda_copia_17m.py`) em todo checkpoint | linha de base registrada | **feito** no leitor: 26,7% |
| 2. Pré-treino continuado | mesmo 17M, mesmos dados próprios, +40.000 passos (~655M tokens), 5% de janelas com trecho repetido, sonda a cada 2.500 passos (`notebooks/salto_17m_fase2_pretreino_continuo_colab.ipynb`) | cópia top-1 ≥ 80% e nome 2ª menção ≤ 1,0 nat, validação sem piorar | **concluída, metas não atingidas**: cópia 11,0% → 50,9%, nome 2ª menção 2,54 → 2,14 nats, validação 3,225 → 2,946 ([resultado](RESULTADO_fase2.md)); base exportada, fora do chat |
| 3. Realizador do quadro | o 17M passa a ser a **rede da linguagem** do CRIVO: ajuste fino completo (sem congelar) para verbalizar o conteúdo que o quadro (`estado_interno.py`) já decidiu — ato de fala, fatos verificados, nomes, motivo, pergunta de esclarecimento — no tom de `IDENTIDADE.md`, com replay do pré-treino. Raciocínio continua nos módulos. Implementação: `experimentos/fase3_realizador_20261012/` e `notebooks/salto_17m_fase3_realizador_colab.ipynb`. Ver `docs/pesquisa_mente_artificial_20261012.md` | blind (assuntos, nomes e frases não vistos): tudo ok ≥ 85%, fatos fiéis ≥ 90%, nome exato ≥ 90%, parada ≥ 95%, sem nome inventado ≥ 95%, cada ato ≥ 70%, perda de LM ≤ 105% da base | **pronta para rodar** depois que a fase 2 exportar `CRIVO/transformer-17m-continuo/base` |
| 4. Porta conversacional | testes de conversa do repositório + conjunto prospectivo congelado, comparação direta com o motor atual | nenhuma regressão relevante | depois da fase 3 |
| 5. Opt-in experimental | integração como no #168 (dupla trava, SHA exato) para conversar no CRIVO | — | depois da fase 4 |

O v5 (cabeças + âncora KL) continua pronto como alternativa barata (~1h) e como controle:
se a fase 2 der certo, ele mostra quanto a base fortalecida dispensa as cabeças.

## Regras mantidas

Origem `CRIVO/transformer-leitor/checkpoint.pt` só leitura; tudo novo em
`CRIVO/transformer-17m-continuo/`. Nenhum peso externo. `ativo_no_chat=false` e
`promovido=false` até a fase 5. Resultados registrados com limites, inclusive os negativos.

## Verificação feita antes de publicar

- `scripts/continuar_pretreino_17m.py` em CPU com a origem montada dos pesos do leitor e
  texto do repositório: sonda inicial reproduziu 26,7%; retomada pelo checkpoint funciona;
  origem com SHA idêntico depois do treino; base exportada carrega por
  `linguagem_profunda.carregar` e gera por `conversar`.
- Células 2–4 do notebook simuladas em CPU com Drive falso (cache de dados, treino curto,
  tabela da sonda, exportação). Células de GPU/Drive/clone só rodam no Colab.
- Nenhum número de capacidade foi medido nesta simulação.

## Revisão de 12/10 (pesquisa sobre mentes artificiais)

A neurociência separa competência linguística formal (rede da linguagem) de competência funcional (raciocínio, mundo, pessoas), e a ciência cognitiva associa mentes a módulos + área de trabalho global. O CRIVO já tem os módulos e o quadro; por isso a fase 3 deixou de ser diálogo de ponta a ponta e passou a ser o 17M como realizador do quadro. Detalhes e fontes: `docs/pesquisa_mente_artificial_20261012.md`.
