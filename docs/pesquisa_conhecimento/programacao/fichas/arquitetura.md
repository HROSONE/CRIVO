# Fichas avançadas: arquitetura

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## arquitetura_rest-rpc — REST, RPC e contratos

**Definição:** REST modela recursos; RPC modela operações; ambos exigem contrato de compatibilidade e falha.

**Mecanismo:** OpenAPI descreve HTTP; schemas de request/response e versionamento precisam corresponder ao runtime.

**Falhas comuns:** Chamar endpoint de REST não garante semântica; gerador de client não prova implementação.

**Escolha:** Escolher pelo domínio, interoperabilidade e consumo; padronizar erros, paginação e autorização.

**Verificação proposta:** Validar servidor contra contrato e testar cliente de versão anterior.

**Referências recomendadas:** [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)

## arquitetura_ddd — Domínio, aggregates e boundaries

**Definição:** Modelo de domínio organiza regras e linguagem; aggregate delimita consistência transacional conceitual.

**Mecanismo:** Entity possui identidade; value object é definido pelo valor; bounded context explicita significado local.

**Falhas comuns:** Aggregate gigante serializa tudo; camada de domínio que só copia DTO não protege invariant.

**Escolha:** Começar por regras e transações reais; separar tradução de fronteira do comportamento.

**Verificação proposta:** Testar regra com serviço externo desligado e violação concorrente.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## arquitetura_modularity — Coesão e acoplamento

**Definição:** Módulo agrupa responsabilidade e oculta decisões internas; dependências determinam impacto de mudança.

**Mecanismo:** API pequena, direção de dependência e adapters permitem substituir detalhe sem alterar política.

**Falhas comuns:** Dividir por arquivos não garante modularidade; abstração sem necessidade adiciona indireção.

**Escolha:** Definir boundary por motivo de mudança e contrato, com exemplos de consumidores.

**Verificação proposta:** Trocar persistência em teste sem mudar regra e medir ciclos de import.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## arquitetura_monolith — Monólito modular e microserviços

**Definição:** Topologias distribuem deployment e ownership de formas diferentes.

**Mecanismo:** Microserviço adiciona rede, operação e consistência distribuída; monólito modular pode fornecer fronteiras internas fortes.

**Falhas comuns:** Separar prematuramente cria distributed monolith; ter um processo não significa código sem módulos.

**Escolha:** Escolher por autonomia, escala e organização observadas; registrar decisão e custo.

**Verificação proposta:** Simular dependência fora do ar e medir coordenação de rollout.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## arquitetura_event-driven — Arquitetura orientada a eventos

**Definição:** Eventos descrevem fatos e permitem desacoplamento temporal entre produtores/consumidores.

**Mecanismo:** Schemas, compatibilidade, ordering e replay precisam governança; command e event possuem semânticas diferentes.

**Falhas comuns:** Evento usado como RPC escondido mantém acoplamento; replay pode repetir emails/cobranças.

**Escolha:** Separar projeções reconstruíveis de efeitos externos e versionar contrato.

**Verificação proposta:** Testar replay, consumidor antigo, evento fora de ordem e duplicado.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## arquitetura_event-sourcing — Event sourcing

**Definição:** Estado é derivado de sequência durável de eventos de domínio.

**Mecanismo:** Snapshots reduzem replay; mudanças de schema precisam upcasting/compatibilidade; projeções podem ser eventualmente consistentes.

**Falhas comuns:** Log técnico não equivale a modelo event sourced; apagar dados pessoais requer estratégia específica.

**Escolha:** Usar quando histórico/auditoria/replay justificam complexidade.

**Verificação proposta:** Reconstruir estado do zero e comparar com snapshot/projeção atual.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)


