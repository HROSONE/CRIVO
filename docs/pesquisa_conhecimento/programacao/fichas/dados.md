# Fichas avançadas: dados

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

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

**Relações:** dados_sql-model; dados_db-pool; distribuidos_idempotencia

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

## dados_optimistic-lock — Controle otimista de concorrência

**Definição:** Version column permite update condicionado à versão lida, detectando conflito em vez de sobrescrever silenciosamente.

**Mecanismo:** UPDATE ... WHERE id=? AND version=? incrementa versão e exige row count esperado; conflito leva reload/retry de regra inteira.

**Falhas comuns:** Retentar só write com dado stale mantém decisão inválida; versão sem tenant scope permite acesso cruzado.

**Escolha:** Usar para baixa contenção e conflito detectável; separar efeito externo da transação retentável.

**Verificação proposta:** Duas edições com mesma versão: uma vence, outra conflita; repetir mesma chave não duplica.

**Relações:** dados_transactions

**Exemplo local:** exemplos/engenharia.mjs#VersionedCell

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_locking-reads — Locks pessimistas e ordem

**Definição:** Lock de linhas serializa operações que precisam ler e atualizar sob invariant comum.

**Mecanismo:** SELECT FOR UPDATE e granularidade dependem do SGBD; múltiplas linhas exigem ordem consistente e transação curta.

**Falhas comuns:** Segurar lock durante HTTP externo aumenta contenção/deadlock; lock não protege linha inexistente em todo nível.

**Escolha:** Preferir update condicional simples; usar locks quando invariant requer leitura protegida.

**Verificação proposta:** Concorrer em duas linhas invertidas e observar deadlock/retry; checar isolamento.

**Relações:** dados_transactions

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_write-skew — Write skew e regras multi-row

**Definição:** Duas transações podem ler conjunto válido e escrever linhas diferentes produzindo invariant inválido.

**Mecanismo:** Snapshot isolation não garante serializability geral; constraints ou serializable/locks apropriados são necessários.

**Falhas comuns:** Cada row estar válida não implica regra global válida; SELECT antes de UPDATE não prova atomicidade.

**Escolha:** Formalizar invariant e escolher proteção do conjunto, considerando abort/retry.

**Verificação proposta:** Duas pessoas se removem do plantão ao ler duas disponíveis; exigir ao menos uma após commit.

**Relações:** dados_transactions

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_unique-null — Unicidade e NULL

**Definição:** Semântica de NULL em UNIQUE e comparações depende do banco/opção definida.

**Mecanismo:** PostgreSQL possui comportamento e opções específicas para tratar nulls distinct/not distinct; índice parcial restringe subconjunto.

**Falhas comuns:** Assumir que UNIQUE em coluna nullable impede todo duplicado lógico pode falhar.

**Escolha:** Definir identidade de ausência e criar constraint compatível com versão.

**Verificação proposta:** Inserir múltiplos nulls e duplicados por tenant; validar regra esperada.

**Relações:** dados_sql-model

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_keyset-consistency — Cursor e consistência entre páginas

**Definição:** Keyset ordena por chave total, mas não cria snapshot por si só.

**Mecanismo:** Nova inserção/exclusão entre páginas muda conjunto; cutoff/snapshot/version podem definir semântica de navegação.

**Falhas comuns:** Prometer exatamente todos itens sem duplicata em dataset mutável pode exigir contrato/estado adicional.

**Escolha:** Escolher feed fresco ou export snapshot e explicar garantia.

**Verificação proposta:** Inserir antes/depois do cursor, editar sort key e comparar página/replay.

**Relações:** backend_pagination

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_partitioning — Particionamento de dados

**Definição:** Partição separa dados por chave/range/hash e influencia pruning, índices e operação.

**Mecanismo:** Partition pruning pode reduzir scan; hot partition ou key skew cria gargalo; constraints/uniqueness têm limites específicos.

**Falhas comuns:** Particionar tabela pequena aumenta complexidade; escolher shard key ruim requer migração difícil.

**Escolha:** Medir consultas/volume e planejar crescimento/resharding antes de distribuir.

**Verificação proposta:** Carregar chave hot, testar pruning e consultas sem partition key.

**Relações:** dados_sql-index

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_cdc — Change data capture

**Definição:** CDC observa mudanças persistidas para alimentar projeções/integrações.

**Mecanismo:** Offsets/checkpoints, schema changes e ordering precisam tratamento; snapshot inicial deve alinhar com log.

**Falhas comuns:** Reiniciar sem checkpoint duplica/perde eventos; CDC técnico não contém sempre semântica de negócio.

**Escolha:** Escolher outbox para evento de domínio ou CDC com contrato próprio; idempotência no consumidor.

**Verificação proposta:** Testar restart, schema evolution e snapshot simultâneo à escrita.

**Relações:** distribuidos_outbox

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_wal-recovery — WAL e recuperação

**Definição:** Write-ahead log registra informação necessária antes de tornar mudanças duráveis conforme protocolo do banco.

**Mecanismo:** Replay e checkpoints recuperam estado; configuração de fsync/synchronous commit influencia perda tolerável.

**Falhas comuns:** Commit reconhecido com durabilidade relaxada pode perder após falha; réplica atrasada não garante mesmo estado.

**Escolha:** Declarar RPO e configuração, testar restore/PITR e impacto de performance.

**Verificação proposta:** Interromper serviço em pontos distintos e verificar dados recuperados.

**Relações:** operacao_recovery

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## dados_schema-registry — Contratos de serialização

**Definição:** Schemas descrevem tipos/encoding de mensagens; compatibilidade depende do formato e política.

**Mecanismo:** JSON, Protobuf e Avro têm regras diferentes de campos desconhecidos, defaults e IDs.

**Falhas comuns:** Reutilizar número de field removido em protocolo pode reinterpretar dado antigo; schema não prova autorização.

**Escolha:** Documentar formato e compatibilidade por direção, testar artefato cross-language.

**Verificação proposta:** Consumir mensagem antiga/nova e verificar roundtrip/campos não reconhecidos.

**Relações:** engenharia_api-evolution

**Referências recomendadas:** [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)

