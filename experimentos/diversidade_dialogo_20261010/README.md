# Diversidade da realização própria — 10/10/2026

**Cópia de integração aprovada no recorte medido. O original fica isolado.**
A publicação exige conferir commit e hash no site após merge.

Base: `0f46877e6d19011fb259c93a4b43f18147e127d7` (#133).
Treino da **GRU própria já existente**, sem outro modelo, API, arquitetura,
tokenizador, vocabulário ou aumento de parâmetros. Não é treino amplo de
conversa nem demonstração de raciocínio novo.

## Problema e medida congelada

Em oito sessões autorais de seis turnos, o site e o motor repetiam uma
mesma reação por tipo de acontecimento. Trocar o objeto declarado alterava
o texto copiado, mas a linguagem produzida continuava igual. `sondas.json`
foi congelado antes da medição e do treino. São classes conhecidas; não
sessões de humanos, avaliação cega ou generalização para novos assuntos.

O juiz remove o cabeçalho e a declaração copiada em `@relato`. Exige ao
menos três corpos distintos nos quatro acontecimentos de cada sessão,
além de geração entregue, reação compatível e argumentos preservados.
Critérios e código do juiz congelados antes de avaliar o candidato;
`SHA256` e `SHA256-juiz` permitem conferir a sequência.

| Medida nos mesmos 48 turnos | Base #133 | Candidato isolado |
|---|---:|---:|
| Sessões com pelo menos três reações distintas, motor | 0/8 | 8/8 |
| Sessões com pelo menos três reações distintas, HTTP | 0/8 (site) | 8/8 (local real) |
| Corpos distintos no total, retirando slots, motor/HTTP | 8 | 32 |
| Problemas nos critérios limitados de fidelidade | 0 | 0 |

As 48 respostas do candidato são idênticas no motor e HTTP. As seis
sessões anteriores de escrita preservam os critérios mínimos e têm os
mesmos 64 textos nos dois modos; leitura pelo agente, não avaliação cega.

Os mesmos 114 casos mantêm **110/114** no motor e HTTP, todos os
**79 antigos**, **52 histórias**, zero troca de domínio, referente ausente
ou desvio proibido. Os quatro não pontuados continuam usando esclarecimento
para restrição de nome/cor, participantes e resumo; não se alterou o juiz.
Os 40 turnos práticos mantêm **40/40** nos dois modos; todos os textos do
motor permanecem iguais aos do #133. As mesmas dez sessões, 104 turnos,
têm respostas idênticas nos dois modos. Os seis critérios mínimos de
escrita foram preservados; as quatro práticas continuam atendidas pelo
executor estrutural do #133, não pelo novo treino.

Candidato original: `4b871b3008542803544404e82042ab0a9dc6e8a0364de294a7f79870130a5b6d`,
continua false/false. Somente a cópia
`ca908bff34dece5d6b3b3ea208dbdeca2d5c499cecf31f1edd63ade77b575ee2`
recebe aprovação depois dos gates e da reprodução byte a byte. Arquivo
anterior `4e5894e2…` arquivado integralmente; pesos e evidências anteriores
permanecem verificáveis no manifesto.

## Treino realmente executado

Mesmos **85.130 parâmetros**, ocultos 80, embeddings 9 e vocabulário 321.
Warm start do checkpoint aprovado #133, arquivado integralmente em
`checkpoint_base_133.json.gz`. Corpus próprio: 9.024 exemplos,
6.144 treino / 2.880 validação. Foram modificados 1.920 alvos para
oferecer quatro formulações por classe; os demais ficaram iguais.

20 épocas, semente 20261015, lote 48, Adam 0,001, clip 5, CPU/NumPy.
Ambiente da reprodução: Python 3.12.14 / NumPy 2.3.5, uma thread BLAS.
Seleção da época 20 pela perda de validação, **1,28253 → 0,00380**.
391,24 segundos na primeira execução; repetição completa em 1.308,56
segundos com avaliações concorrentes, **arquivo idêntico byte a byte**.
A perda mede padrões compartilhados,
não qualidade de diálogo ou generalização. Classes, formas e muitos
vetores de contexto são compartilhados entre treino e validação.
O candidato isolado continua `aprovado=false, ativo_no_chat=false`.

## Evidência e reprodução

- `baseline_motor.json`, `baseline_site.json`: os mesmos 48 turnos antes.
- `piloto_motor.json`, `piloto_http.json`: candidato isolado, traces completos.
- `final_motor.json`, `final_http.json`: os mesmos 48 turnos no caminho
  normal aprovado, sem carregamento experimental; 8/8 nos dois modos e
  textos idênticos aos do candidato isolado.
- `piloto_114_*`: conjunto anterior intacto; gate mantém ao menos 110/114,
  todos os 79 antigos, 52 histórias e zero domínio/referentes/desvios.
- `piloto_40_*`: os mesmos 40 turnos práticos do #133.
- `piloto_sessoes_*`, `revisao_sessoes.json`: mesmas dez sessões autorais;
  revisão pelo agente, sem avaliadores humanos ou avaliação independente.
- `treino.json`, `reproducibilidade.json`: execução e repetição do treino.
- `auditoria_corpus.json`: proveniência, partições e limites dos dados.
- `aprovacao.json`: origem, métricas e hash da cópia de integração aprovada.
- `validar_publicacao.py`: exige commit e hash esperado no HTTP público e
  repete treze smokes conhecidos de fatos/fontes, memória e escrita.
- `manifesto.json`: hashes da evidência e dos checkpoints preservados.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/diversidade_dialogo_20261010/preparar.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/diversidade_dialogo_20261010/treinar.py --epocas 20 --destino /tmp/diversidade-repetida.json.gz
python experimentos/diversidade_dialogo_20261010/sondar.py --modo http --saida /tmp/diversidade-http.json
python experimentos/diversidade_dialogo_20261010/avaliar.py --arquivo /tmp/diversidade-http.json --saida /tmp/diversidade-metricas.json --exigir-meta
```

O runtime permite apenas hashes de pesos próprios avaliados. A nova
aprovação exige fidelidade, utilidade, diversidade, regressões e reprodução;
não habilita um arquivo arbitrário apenas por ter flags verdadeiras.
Os contratos testam adulteração, aprovação indevida, diversidade falsa por
troca de slots e geração livre sem prefixo alvo nas dez classes.

CI amplia a bateria existente por escopo com esses contratos e 48 turnos
HTTP. A matriz completa permanece manual/semanal; a bateria de escrita
continua sem gatilho `push` depois do merge. Nenhum workflow lateral alterado.

## Limites e próximo passo único

A escolha da classe e da variante continua estrutural; a rede realiza a
linguagem. Quatro padrões por classe tornam a escrita menos repetitiva,
mas não ensinam a interpretar qualquer evento. Declarações acumuladas
em `@relato` ainda são recopiadas; finais agradecem ajuda genérica,
personagens secundários participam pouco e o mapa reaparece no caminho
clássico. Uma formulação antiga de recuperação fala em continuar a busca;
isso é fraqueza semântica preservada, não nova capacidade demonstrada.
Guarda de reação é lexical e limitada. Presença de um referente não prova
consistência de todo o enredo. Não há fôlego infinito nem conversa humana.

Próximo passo único: medir e melhorar a ligação entre acontecimentos e
continuações, reduzindo relatos recopiados e transições genéricas, com
corpus próprio e a mesma rede. Preservar os gates atuais; não abrir nova
memória, ampliar acervo ou aumentar parâmetros.
