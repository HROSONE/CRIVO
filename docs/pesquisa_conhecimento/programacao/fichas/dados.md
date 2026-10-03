# Fichas avançadas: dados

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## dados_sql-model — Modelo relacional e constraints

**Definição:** Tabelas representam relações; chaves e constraints expressam integridade.

**Mecanismo:** PK, UNIQUE, FK, NOT NULL e CHECK protegem invariantes locais; NULL usa lógica de três valores em SQL.

**Falhas comuns:** WHERE campo = NULL não encontra ausentes; duplicar invariantes só na aplicação permite bypass.

**Escolha:** Modelar cardinalidade e integridade no banco; distinguir missing e desconhecido.

**Verificação proposta:** Testar nulidade, FK, unicidade, cascading e escrita fora do caminho normal.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_sql-index — Índices e plano de execução

**Definição:** Índice acelera acessos compatíveis ao custo de armazenamento e escrita.

**Mecanismo:** B-tree atende igualdade/ranges em determinadas ordens; índice composto depende das condições e ordenação. EXPLAIN ANALYZE executa consulta.

**Falhas comuns:** Índice em toda coluna aumenta write amplification; query pequena pode preferir seq scan corretamente.

**Escolha:** Medir plano com cardinalidade real e usar consultas representativas.

**Verificação proposta:** Comparar estimated/actual rows, buffers, sorting e desempenho após crescimento.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_transactions — Transações e isolamento

**Definição:** Transação define unidade de atomicidade e visibilidade; níveis de isolamento têm garantias específicas do SGBD.

**Mecanismo:** MVCC mantém versões; locks e conflitos determinam comportamento. Serializable pode abortar transação que precisa retry completo.

**Falhas comuns:** Read committed não protege toda regra multi-step; await em app não torna read-modify-write atômico.

**Escolha:** Usar constraints, UPDATE atômico, locks ou serializable conforme invariante.

**Verificação proposta:** Testar lost update, write skew e retry transacional com duas conexões.

**Invariantes:** Toda escrita preserva regras de domínio e constraints; falha não anuncia commit inexistente.

**Relações:** dados_sql-model, dados_db-pool, distribuidos_idempotencia

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_migrations — Migrações compatíveis

**Definição:** Mudanças de schema devem funcionar durante coexistência de versões e volume real.

**Mecanismo:** Expand/migrate/contract adiciona estrutura compatível, faz backfill e só depois remove legado; lock e duração importam.

**Falhas comuns:** ALTER inocente pode bloquear tabela; rollback de código não reverte dados incompatíveis.

**Escolha:** Planejar compatibilidade bidirecional, chunking e ensaio em cópia representativa.

**Verificação proposta:** Testar versões antiga/nova, restart de backfill e timeout de lock.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_n-plus-one — N+1 e batching

**Definição:** N+1 realiza consulta inicial e uma por item, multiplicando roundtrips.

**Mecanismo:** Join, prefetch e batch loaders podem reduzir chamadas; escopo do cache deve acompanhar request/tenant.

**Falhas comuns:** Batch loader global pode vazar entre usuários; join indiscriminado pode explodir cardinalidade.

**Escolha:** Medir consultas e escolher join ou batch pelo shape e volume.

**Verificação proposta:** Verificar contagem de queries, duplicação de linhas e isolamento de caches.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_db-pool — Pools e saturação

**Definição:** Pool limita conexões e reutiliza recursos; capacidade precisa considerar todas réplicas da aplicação.

**Mecanismo:** Fila de aquisição, timeout e duração de transações determinam throughput; conexão ocupada durante I/O externo reduz capacidade.

**Falhas comuns:** Aumentar pool além do orçamento do banco pode piorar latência; transação esquecida retém locks.

**Escolha:** Orçar conexões globalmente e manter transações curtas.

**Verificação proposta:** Testar carga acima da capacidade, acquisition timeout e conexões devolvidas após erro.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_redis-cache — Cache e invalidation

**Definição:** Cache guarda cópia derivada com política de atualização e expiração.

**Mecanismo:** Cache-aside pode retornar stale; stampede ocorre quando muitos misses recompõem mesma chave. TTL com jitter e coalescing ajudam.

**Falhas comuns:** Cache não deve ser única autoridade de integridade; chave sem tenant/versão mistura contextos.

**Escolha:** Definir freshness, orçamento de memória e fallback em indisponibilidade.

**Verificação proposta:** Testar expiração simultânea, eviction, cache outage e invalidation atrasada.

**Referências recomendadas:** [Redis documentation](https://redis.io/docs/latest/)

## dados_sql-vs-document — Relacional, documento e key-value

**Definição:** Modelos de dados oferecem capacidades distintas de consulta, transação e evolução.

**Mecanismo:** Denormalização reduz joins mas duplica dados; documento agrega estruturas, sem eliminar índices/consistência.

**Falhas comuns:** NoSQL não implica ausência de schema nem escala infinita; SQL não implica incapacidade de distribuir.

**Escolha:** Escolher pelo padrão de acesso e invariantes, não moda.

**Verificação proposta:** Modelar três queries críticas e medir custo de atualização/consistência.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)


