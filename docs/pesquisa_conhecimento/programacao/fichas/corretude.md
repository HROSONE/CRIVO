# Fichas avançadas: corretude

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## corretude_formal — Contratos e verificação formal

**Definição:** Pré/pós-condições, invariantes e modelos permitem provar propriedades delimitadas.

**Mecanismo:** Model checking explora estados sob modelo finito; SMT/assistentes de prova exigem hipóteses formais.

**Falhas comuns:** Provar modelo não prova implementação sem correspondência; bounded checking não cobre tamanho arbitrário.

**Escolha:** Aplicar em protocolo/invariante crítico e registrar premissas e limites.

**Verificação proposta:** Mapear cada propriedade ao código e testar casos fora das premissas.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## corretude_design-by-contract — Defesa de invariantes na API

**Definição:** API deve tornar estados válidos fáceis e violações observáveis.

**Mecanismo:** Factories, encapsulamento e transações separam construção válida de DTO externo; contracts em runtime reforçam boundaries.

**Falhas comuns:** Setter público para cada campo pode permitir estados intermediários inválidos.

**Escolha:** Expor operações de domínio, não mutação arbitrária; checar invariant após transição.

**Verificação proposta:** Gerar sequências de operações e verificar invariant sempre preservado.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## corretude_abstract-interpretation — Interpretação abstrata

**Definição:** Análise calcula aproximação de propriedades sobre domínio abstrato em vez de executar todos estados concretos.

**Mecanismo:** Soundness exige que abstração cubra comportamentos; widening pode garantir convergência sacrificando precisão.

**Falhas comuns:** Warning falso não significa análise inútil; ausência de warning só garante propriedade sob premissas.

**Escolha:** Declarar propriedade, abstração e limites antes de tratar checker como prova.

**Verificação proposta:** Comparar pequeno programa com execução exaustiva e localizar perda de precisão.

**Relações:** corretude_formal

**Referências recomendadas:** [LLVM Language Reference](https://llvm.org/docs/LangRef.html)

