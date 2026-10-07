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
