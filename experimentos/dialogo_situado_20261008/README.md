# Continuidade e escopos do diálogo — 08/10/2026

Base: main após PR113 (`6987fe72bb93c20886826a5dfac5b9c698a61d69`).

O chat agora resolve referências a alternativas ordenadas, conserva objetivo e disponibilidade real, acompanha circunstâncias pessoais e separa hipóteses, ficção e falas citadas. Mudanças explícitas de assunto e reinícios limpam o escopo adequado. Pedidos factuais, fontes, código, premissas formais e crise conservam suas prioridades.

`dialogo_situado.py` implementa uma política estrutural própria: extrai argumentos da sessão e compõe respostas com atos reutilizáveis. Lê os mesmos relatos e slots do diálogo nativo, sem cadastrar os novos diálogos como conhecimento ou treinamento. O histórico registra `mecanismo=dialogo_situado_estrutural`, as fontes e `pesos_promovidos=false`. O gerador e os pesos próprios existentes permanecem em uso; nenhum modelo externo ou peso experimental foi promovido.

## Resultados e ordem de avaliação

| Conjunto | Base PR113 | Primeira avaliação do candidato | Última medição registrada |
| --- | --- | --- | --- |
| Sonda pública original | 47/72 turnos; 1/18 diálogos | desenvolvimento iterativo | 72/72; 18/18 |
| Desenvolvimento adicional | 6/20; 0/6 | desenvolvimento iterativo | 20/20; 6/6 |
| Primeiro controle separado | 23/47; 2/12 | 45/47; 10/12 | 47/47; 12/12 |
| Segundo controle temporal | não medido | 22/24; 6/8 | 24/24; 8/8 |
| Terceiro controle novo | não medido | **25/25; 8/8** | sem ajuste posterior por seus erros |
| Escrita e reparo existentes | 28/28; 9/9 | regressão rejeitada: 23/28 | 28/28; 9/9 |

Os 20 casos de desenvolvimento e o primeiro controle foram fixados no commit `d61dacb`, antes da política estrutural. Só os agregados do baseline do primeiro controle foram lidos antes da implementação. A primeira avaliação desse controle usou o código congelado em `e274296`.

Após obter 45/47, os erros foram inspecionados: circunstâncias com “quando…” não eram acompanhadas. Fixou-se o segundo controle (`df072a5`) antes de ampliar esse suporte. Ele obteve 22/24: faltava conectar uma circunstância a uma hipótese anterior e interpretar definição de um termo citado explicitamente. Esses controles passaram a servir ao diagnóstico; suas reexecuções **não são validação inédita**.

O terceiro controle (25 turnos em oito diálogos) foi fixado no commit `7083dd5` e avaliado sem modificar a política por erros desse conjunto. Uma revisão posterior do código reforçou o encerramento de escopos na abertura nativa e sua suspensão diante de consulta factual; a reprodução desse conjunto e os contratos de integração verificam esse ajuste. Troca assuntos, números, objetos, alternativas e nomes ficcionais. Os hashes dos conjuntos estão em `manifesto_casos.json`; as respostas reais estão em `resultados/`.

A sonda pública e seu oráculo não foram alterados. O avaliador adicional reutiliza esse oráculo e adiciona exclusão de rotas pessoais nas consultas factuais. O desenvolvimento revelou uma falsa penalização lexical de uma frase negativa sobre vivências pessoais; a redação preservou a ausência de vivências próprias, sem afrouxar o oráculo.

## Regressões e reprodução

A revisão detectou e corrigiu regressões de abertura nativa, escuta neural, feedback no passado confundido com ordem, reinício, nomes de assunto e disponibilidade condicional ou negada como crença. Logs incluem candidatos rejeitados, erros encontrados e verificações posteriores; não substituímos os primeiros resultados pelos melhores.

A revisão final delimitou escopos em aberturas nativas e estruturais, arquivou relatos do assunto anterior para retomada e registrou a política no mapa do ecossistema. Os 22 contratos específicos passam, incluindo reconstrução independente pela API e ausência de prova factual para lembranças pessoais. Passaram também 35 testes de crise, interface HTTP e motor de programação, os seis contratos do mapa/API e os 17 contratos estruturais no Python 3.8 com `-S`, sem NumPy. As falhas da regressão ampla foram conferidas por reexecuções dos testes afetados; a suíte completa do GitHub permanece uma verificação separada.

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest testes_dialogo_situado -v
python -S -m unittest testes_dialogo_situado.TestesQuadroSituado -v
OPENBLAS_NUM_THREADS=1 python avaliar_dialogo_real.py --saida /tmp/original-novo.json
OPENBLAS_NUM_THREADS=1 python experimentos/dialogo_situado_20261008/avaliar.py desenvolvimento --exigir-todos --saida /tmp/dev-novo.json
OPENBLAS_NUM_THREADS=1 python experimentos/dialogo_situado_20261008/avaliar.py validacao_final_nova --saida /tmp/controle-novo.json
```

O workflow `dialogo-situado.yml` mantém contratos de escopo e as sondas original e de desenvolvimento como regressões. Os controles autorais são publicados para inspeção; sua execução futura será reprodução, não uma nova medição independente.

## Limites observados

Os critérios automáticos medem presença de argumentos pertinentes, continuidade e contratos. Todos os conjuntos novos são autorais, com avaliação automática e leitura técnica das respostas, sem avaliação humana independente. Não estimam desempenho em conversa livre nem compreensão geral.

A leitura dos 25 turnos finais confirma referências e tempos corretos e ausência de ficção como prova. Mostra também respostas ainda formularizadas, repetição de perguntas de exploração e ecos pouco naturais, como misturar objetivo e disponibilidade na mesma oração. Passar nos critérios não garante resposta útil, natural ou raciocínio profundo. Permanecem necessárias avaliações independentes, diálogos mais longos, paráfrases mais amplas e trabalho no gerador próprio. Este experimento melhora a condução estrutural do diálogo; não comprova capacidade de um LLM geral.
