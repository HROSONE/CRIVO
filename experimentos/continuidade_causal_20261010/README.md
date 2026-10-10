# Continuidade de acontecimento — 10/10/2026

Base publicada: #134, `04f2be154850202c2831e426b23db0741d4dc74f`.
Objetivo desta rodada da Fase 3: continuar a tarefa/acontecimento selecionado,
esclarecer contexto incerto e verificar a guarda de conversa, com pesos próprios.
Não acrescenta memória, acervo, arquitetura, tokens ou parâmetros.

## Antes, entradas congeladas

`sondas.json` contém dez conversas autorais de oito turnos + duas sondas de
fronteira, 88 turnos. Foram realmente submetidas ao HTTP público na base
acima, health antes/depois confirmado, e ao motor sem as mudanças.
Ambos produziram os mesmos 88 textos: **0/10** mantêm o fio, **10** trocas
de domínio, **60** turnos sem algum referente exigido; esclarecimento **0/2**.
Exemplo observado: após perder um apito turquesa, “E depois?” ofereceu
répteis/anfíbios ou manchas de roupa. Não são sessões de participantes humanos.

As entradas e os critérios centrais de continuidade permanecem congelados.
O primeiro juiz exigia indevidamente URL na própria resposta a uma pergunta
que não pediu fonte; esse erro marcava duas sondas de fronteira. Foi corrigido
para conferir o executor factual antes da avaliação HTTP. A fonte explícita
continua nos contratos e smoke de publicação existentes. Outra correção trata
`natural_routing=null` do motor como rota ausente. Versões/hashes anteriores,
primeiras métricas e explicação estão preservados em `correcao_juiz.json`.
Nenhuma dessas correções muda os 0/10 → 10/10, referências ou domínio.

## Mecanismo e treino realmente executado

A continuação elíptica exige que a última tarefa respondida seja escrita.
Seleciona classe e objeto literalmente declarado no acontecimento ativo,
utilizando a `ultima_escrita` existente. Depois de um fato ou sem objeto
selecionável, esclarece em vez de escolher um assunto arbitrário.

A GRU própria recebe ato, referentes, estado selecionado e passo do arco.
A rede realiza esse contexto; a seleção do estado/objeto/passo é **estrutural**.
Quatro passos condicionados evitam reiniciar a cena. Além de “E depois?”,
“Continue a história”, “Continue mais um pouco”, “Continue de onde parou”
e “Não repita a cena anterior” usam o mesmo estado quando ele é resolvível. No quinto, pede novo
acontecimento; um final explícito pode fechar o trecho. Relato completo não
é recopiado em cada continuação. Guarda impede inversões conhecidas de perda/
recuperação, preserva slots e bloqueia nomes/números literais não fornecidos.
Fatos, preferências e cálculos permanecem com os executores/guardas anteriores.

Corpus: **10.304 exemplos**, 9.024 anteriores intactos + 1.280 supervisões
causais autorais; 6.784 treino / 3.520 validação. Os padrões/vetores são
compartilhados entre partições. Entidades/entradas das sondas não são usadas
no treino; isso **não** torna a validação independente nem prova compreensão
neural de temas inéditos.

Mesma GRU de **85.130 parâmetros**, 80 ocultos, embedding 9, 321 tokens.
Warm start do checkpoint próprio aprovado #134; 20 épocas, Adam 0,001,
lote 48, clip 5, semente 20261016, sem mistura/apagamento do contexto.
Selecionada época 20: validação **0,866781 → 0,006324** (ver valor preciso
em `treino.json`). CPU, NumPy 2.3.5, Python 3.12.14, BLAS com uma thread.
Treino 301,60 s; repetição 298,85 s, checkpoint **idêntico byte a byte**.

Candidato original `adf0fa8c297eab6cf9122c8da6a1bbd5796416f406e86e0b096ed2a23f7c5d0a`
permanece `aprovado=false / ativo_no_chat=false`. `promover.py` exige as
medições completas motor + HTTP, os gates históricos e reprodução antes de
criar uma cópia aprovada; não muda a aprovação do original. #134 arquivado
em `checkpoint_base_134.json.gz`. Hashes e hiperparâmetros versionados.

## Medição desta rodada

Motor e HTTP local real: **0/10 → 10/10** conversas de oito turnos mantêm
os critérios mínimos; **0/2 → 2/2** sondas esclarecem contexto incerto.
Zero troca de domínio, referente exigido ausente ou reversão de estado nos
critérios limitados. Quatro continuações distintas por estado sem copiar a
declaração inteira. Leitura/avaliação pelo agente, sem humanos ou avaliação cega.

`conversas_novas.json`: duas sondas prospectivas de **18 turnos**, três
acontecimentos conhecidos encadeados e operadores ausentes das 88 entradas.
Não usados no corpus. Sua janela real HTTP continua com vinte mensagens.
Motor e HTTP: **2/2** preservam os critérios mínimos nos mesmos 36 turnos.
Motor e HTTP preservam **110/114**, todos os **79** anteriores, **52** histórias,
zero domínio/referente/desvio; **40/40** práticos e **8/8** diversidade
(32 corpos distintos). Os mesmos quatro casos não pontuados permanecem
sem alteração do juiz histórico. Tudo em `validacao_local.json`.

## Extensão dos operadores comuns

A revisão encontrou que continuar pelas formas tradicionais ainda selecionava
a realização genérica. `sondas_aliases.json` congela três sessões de oito
turnos antes da ampliação: **0/3 → 3/3** no motor e HTTP. Não acrescentou outro
treino ou parâmetro: mesma ponte de estado e mesmos pesos. Os 114 casos
são repetidos motor/HTTP após essa mudança; a aprovação também exige
os 24 turnos de aliases nos dois modos.

## Limites que permanecem

Dez classes, quatro passos autorais e extração gramatical limitada. Fora
desses estados, deve esclarecer. Cabeçalhos/transições ainda repetitivos,
artigos copiados podem produzir concordância ruim, início clássico ainda
pode repetir episódios. Juízes lexicais não provam toda a coerência do enredo.
Dezoito turnos encadeados não são fôlego ilimitado. Não foi demonstrado
planejamento livre, diálogo humano geral nem generalização a novos assuntos.
Nenhum modelo externo foi baixado, executado ou chamado.

## Contratos e integração aprovada

**32 contratos locais passaram**, mais um contrato de prioridade prática: estado, guardas, proveniência, aprovação,
regressões dos checkpoints antigos e contexto prático. Smoke nativo de sete
turnos usa a cópia aprovada, sem modo experimental, com o SHA esperado.
Manifesto preserva 38 arquivos anteriores de pesos/arquivos e evidências
históricas. CI/merge/publicação são verificados antes de declarar entrega.

Uma revisão adicional durante CI detectou que a nova elipse global “E agora?”
roubava uma tarefa prática ativa. A ponte agora consulta o executor prático
existente antes de esclarecer; após fato, pede contexto. Contrato adicional
passou, registro antes/depois em `regressao_prioridade_pratica.json`.
Pesos e corpus não mudaram.

## Reproduzir e integrar

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/continuidade_causal_20261010/preparar.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/continuidade_causal_20261010/treinar.py --destino /tmp/dialogo-causal.json.gz
python experimentos/continuidade_causal_20261010/piloto.py --modo motor --bateria causal --saida /tmp/causal-motor.json
python experimentos/continuidade_causal_20261010/avaliar.py --arquivo /tmp/causal-motor.json --saida /tmp/causal-metricas.json --exigir-meta
```

Para HTTP, use `--modo http`; para 114/40/diversidade/fôlego, selecione a
bateria correspondente. Produção exige hashes fixos e aprovação V7 válida.
CI existente por escopo inclui os contratos, 114/40/48 e 88 + 36 + 24 HTTP;
sem matriz completa em todo PR nem repetição de escrita após merge.
Cópia aprovada para integração: `28d05179e4dda05473a5bdb0a3963d8e032b3d3e9c5d6d60a77404310545d4e8`.
Original false/false, 38 arquivos anteriores de pesos preservados/arquivados.
Só declarar publicado após confirmar commit/checkpoint no HTTP público e
repetir as entradas congeladas e smokes de fatos/fontes/memória.
