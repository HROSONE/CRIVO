# Fichas avançadas: corretude

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

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


