# Continuidade prática — 10/10/2026

Base publicada: `498a36248787022d7635cbb825521cfdda318aa7` (#132).
Este experimento corrige quatro sessões práticas que continuavam falhando:
frações/tempo, bicicleta/rodas, horta/condições e troca/retomada de tarefa.
Usa histórico e traces existentes; não cria memória, acervo ou rede nova.

| Medição congelada | Antes | Depois |
| --- | ---: | ---: |
| Mesmos 40 turnos, motor | 15/40 | 40/40 |
| Mesmos 40 turnos, HTTP real | 15/40 público | 40/40 local |
| Sessões com todos os critérios mínimos | 0/4 | 4/4 |
| Desvios textuais proibidos nos 40 | 5 | 0 |
| Conjunto anterior de 114, motor/HTTP | 110/114 | 110/114 |
| Troca de domínio/referente ausente nos 114 | 0/0 | 0/0 |

Os 79 anteriores continuam 79/79 e as 52 histórias continuam entregues.
Os quatro casos antigos ainda não pontuam porque esperam escrita onde o
chat usa esclarecimento de restrição/metadados. Não mudamos o juiz nem
os dados para apagar essas falhas. Os 40 não contêm roteamento factual
arbitrário; ausência de desvios neste conjunto não prova ausência geral.

## Casos e execução

`sondas.json`: as mesmas quatro sessões autorais de dez turnos, copiadas
do experimento de generalização após #132. `criterios.json`: presença de
conteúdo mínimo, rota admissível, guarda aceita e desvios proibidos;
ambos congelados e com SHA antes da implementação. Baseline independente
no motor e no site, com commit e checkpoint público confirmados antes e
depois. Não são sessões de quatro participantes humanos nem teste cego.

```sh
OPENBLAS_NUM_THREADS=1 python experimentos/contexto_pratico_20261010/sondar.py --modo motor --saida /tmp/pratico-motor.json
python experimentos/contexto_pratico_20261010/avaliar.py --arquivo /tmp/pratico-motor.json --saida /tmp/pratico-metricas.json --exigir-meta
OPENBLAS_NUM_THREADS=1 python experimentos/contexto_pratico_20261010/sondar.py --modo http --saida /tmp/pratico-http.json
python experimentos/contexto_pratico_20261010/avaliar.py --arquivo /tmp/pratico-http.json --saida /tmp/pratico-metricas-http.json --exigir-meta
OPENBLAS_NUM_THREADS=1 python experimentos/escrita_acontecimentos_20261010/avaliar.py --modo http --so-congelado --saida /tmp/preservacao-114.json --exigir-meta
OPENBLAS_NUM_THREADS=1 python -m unittest testes_contexto_pratico testes_orientacao_pratica testes_dialogo_situado -v
```

As respostas e traces completos estão em `baseline_{motor,site}.json`,
`final_{motor,http}.json`; pontuação em `*_metricas.json`.
`preservacao_114_{motor,http}.json` usa as entradas antigas intactas.
Pilotos e a versão antes da revisão manual foram preservados. A última
revisão retirou a suposição de terraço quando o local é outro e evitou
transformar um círculo em dois. `revalidacao_final_http.json` registra
as duas saídas HTTP reexecutadas e hashes; respostas anteriores ficam
em `antes_revalidacao_final_http.json`. O CI mede os 114 no motor e os
40 pelo HTTP no código final, junto aos contratos de chat e aprovação.

## O que mudou e o que foi lido

- Disponibilidade numérica/por extenso e tarefa separadas; “quinze
  minutos” e “vinte minutos” deixam de desaparecer. Correções valem;
  hipótese, crença e citação não substituem declarações reais.
- Histórico identifica mudança/retomada de tarefa e recupera o último
  cálculo daquela tarefa. Pedido de outro exercício oferece outro;
  reformulação usa partes iguais da mesma conta, com `Fraction` exata.
- Desenho usa os traços relatados. Dois círculos são rodas somente após
  confirmação; um círculo não vira dois. Bicicleta recebe propostas de
  quadro, ajuste e acabamento, sem apagar se não há borracha. Passarinho
  continua a partir do corpo relatado.
- “Quero cultivar” refina a horta. Sol de manhã é observação da sessão;
  sombra condicional continua hipótese. Vasos/budget entram na orientação;
  faltam duração da luz, tamanho/furos e escolha da erva, sem prometer
  espécie ou sucesso de cultivo.
- Guarda rejeita tempo e quantidade de vasos alterados/inventados.
  Trace mostra condições declaradas, fontes da disponibilidade,
  executor de orientação e `gerador_neural_usado: false`.

Quatro sondas novas autorais, 29 turnos (`conversas_novas.json`), foram
congeladas separadamente e executadas no site anterior e no motor/HTTP
corrigidos. Revisão pelo agente: 0/4 → 4/4 atendem aos critérios mínimos
escritos. Exercícios novos conferidos (7/12 e 11/18), mudança de 17 para
19 minutos, bicicleta azul, pátio/dois vasos e retomada após passarinho.
A leitura encontrou uma alegação indevida de que o usuário pediu
simplificação numa sessão que não pediu; foi corrigida e verificada.
`revisao_sessoes.json` registra avaliação e limites. Não é avaliação
independente nem demonstra transferência a assuntos não cobertos.

## Pesos, limites e próximo passo

Não houve treino, troca de checkpoint ou aumento de parâmetros. A GRU
aprovada permanece `4e5894e2fe4a23bab63cb3a6b8a69da023a2b07b43829a7e706e6528bd1e780d`.
Os 35 arquivos anteriores, arquivo do checkpoint antigo e conjuntos
congelados/experimento #132 foram preservados. Guardas de fato, cálculo
com fonte e acervo não foram afrouxadas. As orientações são propostas
autorais explícitas, não novos fatos sem fonte.

Ainda há regras e linguagem repetitiva. Suporte de números por extenso,
formas e luz é parcial; desenho desconhecido continua genérico ou pede
esclarecimento. Não vê o papel, não decide a espécie de planta sem
condições e não resolve planejamento geral. Janela de vinte mensagens,
sem memória infinita. Estas quatro tarefas melhores não equivalem a
conversa livre geral ou raciocínio neural apurado.

CI por escopo no workflow existente de escrita: estes contratos/40 HTTP
entram junto aos 114. Sem novo workflow, push ou matriz completa depois
do merge. Publicação deve ser confirmada pelo commit/checkpoint e pelos
mesmos 40 casos públicos; resultado local não substitui essa confirmação.

Próximo passo único: diversificar a realização do contexto já correto,
com corpus próprio de diálogo e as novas falhas medidas no site;
preservar estes gates e pesos próprios, sem nova memória/acervo/rede.
