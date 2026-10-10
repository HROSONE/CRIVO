# Referências e correções na escrita — 10/10/2026

Base pública e código: #135, `ca31090f6ce0f4e903b8dde1898efc36a69c9ada`.
Problema observado no HTTP público: depois de perder uma carteira e dizer
“Ela a recuperou”, o gerador esquecia o objeto na continuação; “novamente”
virava objeto. Correções explícitas não substituíam o detalhe anterior.

Foram congelados **11 casos / 52 turnos** e o juiz antes da implementação.
Não são sessões reais do dono: são sondas autorais do agente, executadas
como usuário no site, com nomes/objetos novos em classes já conhecidas.
Os casos e o juiz têm hashes próprios; não entram no corpus de treino.

Antes, site e motor concordaram: **0/6** sessões de referência/correção,
**0/5** fronteiras de ambiguidade/negação; 35 violações de referente e
18 de estado nos critérios limitados. Depois, no motor e HTTP real: **6/6**, **5/5**,
zero violações de referente, estado ou domínio. As regressões anteriores precisam ser aprovadas antes de mesclar;
publicação exige os mesmos casos no site.

A implementação lê o objeto do acontecimento ficcional atual e encaminha
um evento explícito para o gerador próprio aprovado. Resolve recuperação
com pronome e conserto com clítico; correção exige o trecho inteiro antigo
mais o novo. Não escolhe entre objetos coordenados nem usa história antiga
após mudança de assunto. Na negação, pede esclarecimento sem transformar
o acontecimento em recuperação. Correções fora da escrita permanecem com
os executores de memória existentes. O trace registra fonte, objeto anterior,
objeto selecionado e operação. Não foi criada nova memória.

**Não houve treino nem alteração dos pesos.** Continua ativo o checkpoint
próprio aprovado `28d05179e4dda05473a5bdb0a3963d8e032b3d3e9c5d6d60a77404310545d4e8`,
85.130 parâmetros. Checkpoints e experimentos anteriores são preservados.
Esta mudança melhora o contexto entregue ao gerador, não a capacidade neural
ou o vocabulário. Concordância, transições genéricas, quatro passos e dez
classes continuam limitados. Não demonstra resolução geral de pronomes,
narrativa livre, generalização a assuntos novos ou conversa humana.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/referentes_escrita_20261010/sondar.py --modo motor --saida /tmp/referentes-motor.json
python experimentos/referentes_escrita_20261010/avaliar.py --arquivo /tmp/referentes-motor.json --saida /tmp/referentes-metricas.json --exigir-meta
```

`--modo http` usa servidor real local; `--modo site` testa a URL pública.
CI acrescenta estes 52 turnos e os contratos ao workflow de escrita existente.
As baterias históricas permanecem intactas e obrigatórias por escopo; a matriz
completa continua manual/semanal. Não repetir a bateria pesada após merge.
