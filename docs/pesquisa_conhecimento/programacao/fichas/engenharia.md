# Fichas avançadas: engenharia

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## engenharia_api-evolution — Compatibilidade e versionamento

**Definição:** Mudança precisa preservar contratos observados por consumidores, incluindo semântica e erros.

**Mecanismo:** Adicionar campo pode quebrar cliente estrito; remover/mudar significado exige migração; SemVer comunica intenção, não prova.

**Falhas comuns:** Só comparar assinatura ignora comportamento, performance e formato de erro.

**Escolha:** Catalogar consumidores e testar versões coexistentes; anunciar depreciação verificável.

**Verificação proposta:** Rodar consumidor antigo contra servidor novo e testar defaults.

**Referências recomendadas:** [Git reference](https://git-scm.com/docs)

## engenharia_debugging — Diagnóstico por hipótese

**Definição:** Debugging reduz conjunto de causas a partir de evidência e experimento.

**Mecanismo:** Reprodução mínima, bisect, tracing e comparação de estados isolam mudança causal.

**Falhas comuns:** Adicionar logs indiscriminados pode expor secrets e alterar timing; culpar framework sem reprodução prolonga incidente.

**Escolha:** Formular hipótese falsificável e testar uma variável por vez.

**Verificação proposta:** Registrar sintoma, expected/actual, experimento e evidência que descartou hipótese.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## engenharia_profiling — Profiling e benchmarking

**Definição:** Perfil atribui custo real; benchmark compara sob workload definido e condições controladas.

**Mecanismo:** CPU, alloc, I/O e lock contention são eixos distintos; warmup, GC e distribuição precisam controle.

**Falhas comuns:** Otimizar só média ignora p99; benchmark que elimina trabalho ou usa dataset irreal engana.

**Escolha:** Usar baseline, múltiplas amostras e checagem de correção antes de medir.

**Verificação proposta:** Registrar ambiente, amostras, percentis, memória e variação entre execuções.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## engenharia_git — Git, objetos e histórico

**Definição:** Git guarda snapshots por objetos content-addressed e refs para commits.

**Mecanismo:** Branch aponta commit; merge tem múltiplos pais; rebase reescreve identidade; reflog auxilia recuperação local.

**Falhas comuns:** Force push pode apagar trabalho alheio; stash não é backup remoto garantido.

**Escolha:** Inspecionar diff/status e usar updates fast-forward quando compartilhado.

**Verificação proposta:** Verificar pais, tree, conflitos e artefato após merge.

**Referências recomendadas:** [Git reference](https://git-scm.com/docs)

## engenharia_ci — CI e artefato reproduzível

**Definição:** CI verifica mudança e produz artefato com origem identificável.

**Mecanismo:** Separar lint/typecheck/test/build; lock e versão de toolchain reduzem variação; permissões por job limitam impacto.

**Falhas comuns:** Build passar não prova testes executados; cache indevido pode servir artefato de configuração antiga.

**Escolha:** Construir uma vez e promover artefato verificado entre ambientes.

**Verificação proposta:** Comparar build limpo/cacheado e registrar commit, dependências e checks.

**Referências recomendadas:** [Git reference](https://git-scm.com/docs)

## engenharia_code-review — Revisão de código por risco

**Definição:** Revisão avalia correção, contrato, manutenção e impacto operacional.

**Mecanismo:** Foco em invariant, dados externos, concorrência, migração e observabilidade antes de estilo.

**Falhas comuns:** Revisão só sintática deixa bug semântico; diff grande sem separação reduz atenção.

**Escolha:** Fornecer problema, comportamento e validação concreta no PR.

**Verificação proposta:** Seguir fluxo de sucesso/falha e conferir assertions/artefato.

**Referências recomendadas:** [Git reference](https://git-scm.com/docs)

## engenharia_requirements — Requisitos e critérios de aceite

**Definição:** Requisito descreve objetivo observável e restrições; critério de aceite fornece evidência de conclusão.

**Mecanismo:** Definir entradas, saídas, erros, escala, plataforma e ameaças antes de escolher tecnologia.

**Falhas comuns:** Pedido amplo sem contrato induz código que compila mas não resolve necessidade.

**Escolha:** Especificar mínima fatia completa e listar hipóteses reversíveis.

**Verificação proposta:** Converter cada requisito em demonstração ou teste relevante.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## engenharia_adr — Decisões arquiteturais

**Definição:** ADR registra contexto, decisão, alternativas e consequências verificáveis.

**Mecanismo:** Trade-offs incluem reversibilidade, custo operacional e limitações; decisão pode expirar quando condições mudam.

**Falhas comuns:** Justificativa por moda não permite revisão; esconder premissas impede reavaliar.

**Escolha:** Manter ADR curto com gatilho de revisão e evidência.

**Verificação proposta:** Reavaliar com volume/latência diferente e verificar se premissas ainda valem.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)


