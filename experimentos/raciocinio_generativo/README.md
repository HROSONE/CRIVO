# Investigação de raciocínio generativo

Diagnóstico e experimento fora do caminho do chat. Consulte
[o relatório](../../docs/diagnostico_generativo_20261007.md) para fontes,
hipóteses, resultados e critérios do próximo treino.

`diagnosticar.py` mede candidatos válidos e inválidos contra as guardas atuais,
opcionalmente executa os pesos e uma ablação de restrições, e verifica seis
contratos de inferências com referências. Esses passos são escritos no
experimento; nenhum modelo aprendeu a gerá-los nesta entrega.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experimentos/raciocinio_generativo/diagnosticar.py --neural --ablacao \
  --saida /tmp/diagnostico-generativo.json
```

O verificador é restrito a afirmações proposicionais e modus ponens com
conjunção. Não interpreta livremente um texto, não implementa ProofWriter e
não verifica justificativas arbitrárias. O relatório exporta estas sondas
autorais, não perguntas das avaliações congeladas do projeto.

## Piloto de aprendizagem

`piloto.py` define o corpus determinístico, o protocolo e a execução iterativa.
`treinar_piloto.py` ajusta duas variantes dos pesos próprios de produção numa
pasta experimental: classificação direta e próximo passo. A primeira não
produz provas. A segunda gera `regra|apoios|conclusão` ou uma classificação
final; o verificador pode vetar, mas nunca calcular uma resposta substituta.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python treinar_piloto.py \
  --saida /tmp/crivo-piloto --passos 400 --avaliar-a-cada 100
PYTHONPATH=experimentos/raciocinio_generativo python -S -m unittest testes_piloto -v
```

O comando de treino é executado dentro desta pasta; os demais exemplos de
documentação usam a raiz do repositório. PyTorch e NumPy são necessários para
treinar; nenhum peso externo é baixado. A saída não pode ser a pasta de
artefatos de produção. Corpus, manifesto, metadados, checkpoints e avaliações
são gravados na pasta escolhida antes/depois das etapas correspondentes.

480 problemas de treino produzem 960 exemplos de próximo passo ou término;
o controle direto usa os mesmos 480 problemas. Desenvolvimento: 32 problemas
com outro vocabulário. Teste: 56, com vocabulário separado e subconjunto de
24 estruturas/profundidades fora do treino. Os outros casos testam transferência
lexical em estruturas já conhecidas. Isso não equivale a generalização livre
em textos arbitrários; o corpus usa linguagem controlada.

`responder_piloto.py` executa pesos explicitamente selecionados em NumPy.
Uma classificação positiva ou negativa sem a conclusão presente nas premissas
ou nos passos aceitos é vetada. Classificações de conflito e indeterminação
continuam sendo previsões do modelo, sem prova produzida por esse protocolo.
`avaliar_numpy.py` mede esse executor sem escolher outro checkpoint.
