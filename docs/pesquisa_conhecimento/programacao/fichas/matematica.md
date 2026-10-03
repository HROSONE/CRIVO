# Fichas avançadas: matematica

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## matematica_floating — Estabilidade numérica

**Definição:** Erro de arredondamento e condicionamento do problema são dimensões diferentes.

**Mecanismo:** Algoritmo estável controla erro relativo ao problema; cancelamento catastrófico e soma de escalas distintas degradam precisão.

**Falhas comuns:** Aumentar precisão não corrige modelo mal condicionado nem valida unidades.

**Escolha:** Usar métodos estáveis, tolerâncias justificadas e análise de escala.

**Verificação proposta:** Testar valores extremos, soma compensada e comparação com referência de maior precisão.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

