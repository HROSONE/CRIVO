# Fichas avançadas: distribuidos

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## distribuidos_timeouts — Timeouts, retries e budgets

**Definição:** Timeout limita espera; retry repete operação quando falha é transitória e repetição é segura.

**Mecanismo:** Usar deadline global, attempts limitados, backoff com jitter e Retry-After quando relevante.

**Falhas comuns:** Retries em camadas multiplicam carga; timeout não prova que operação remota falhou antes de cometer efeito.

**Escolha:** Retentar só classes definidas e operações idempotentes; contabilizar tentativas no mesmo budget.

**Verificação proposta:** Simular resposta perdida após commit, 429/503 e cascata de retries.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## distribuidos_idempotencia — Idempotency keys

**Definição:** Protocolo associa chave de request a resultado para impedir duplicação de efeito durante retries.

**Mecanismo:** Persistir chave, hash do payload e resultado com unicidade/transação; concorrência exige serialização da primeira execução.

**Falhas comuns:** Cache em memória perde dedupe após restart; mesma chave com payload diferente precisa ser rejeitada.

**Escolha:** Definir escopo por tenant/operação, retenção e comportamento para execução em andamento.

**Verificação proposta:** Disparar requests concorrentes, reiniciar servidor e perder resposta após commit.

**Invariantes:** Uma chave no escopo identifica um payload e um efeito lógico; colisão de payload é rejeitada.

**Relações:** dados_transactions, distribuidos_outbox, distribuidos_timeouts

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## distribuidos_outbox — Transactional outbox

**Definição:** Outbox registra mudança de negócio e evento na mesma transação do banco.

**Mecanismo:** Publisher lê outbox e publica depois; pode repetir evento ao falhar entre publicação e marcação. Consumidor precisa dedupe/idempotência.

**Falhas comuns:** Enviar broker depois de commit sem outbox cria janela de perda; outbox sozinho não garante ordem global.

**Escolha:** Usar quando atualização e evento devem ser duráveis sem transação distribuída.

**Verificação proposta:** Simular crash antes/depois do publish e verificar nenhum evento perdido e duplicados tolerados.

**Pré-requisitos:** dados_transactions

**Relações:** distribuidos_queues, distribuidos_idempotencia

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## distribuidos_queues — Filas, leases e entrega

**Definição:** Broker e consumidores usam ack, visibility timeout/lease e redelivery para progresso.

**Mecanismo:** Entrega at least once exige efeitos idempotentes; poison message precisa política de tentativas/DLQ e investigação.

**Falhas comuns:** Ack antes de efeito pode perder trabalho; ack depois pode duplicar efeito após crash.

**Escolha:** Escolher semântica do efeito e bound de retry; não prometer exactly once sem delimitar sistema.

**Verificação proposta:** Simular worker morto, lease expirada, mensagem inválida e redelivery concorrente.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## distribuidos_consistency — Consistência e falhas parciais

**Definição:** Consistência descreve observações permitidas; falha de rede não informa com certeza estado remoto.

**Mecanismo:** Linearizability exige aparência de operação atômica em intervalo real; eventual converge sob condições, sem prazo universal.

**Falhas comuns:** CAP não significa escolher livremente dois atributos em todo momento; aplica restrição durante partição sob definições.

**Escolha:** Escolher modelo pelo invariante de negócio e documentar leitura stale/reconciliação.

**Verificação proposta:** Testar partição, failover, leitura após escrita e operações concorrentes.

**Referências recomendadas:** [Jepsen consistency models](https://jepsen.io/consistency)

## distribuidos_consensus — Consenso e Raft

**Definição:** Consenso decide valor/log sob modelo de falhas e quórum; não é mera eleição de líder.

**Mecanismo:** Raft usa termos, votação e replicação de log; safety e liveness dependem de condições diferentes.

**Falhas comuns:** Ter líder não prova commit; partição minoritária não pode progredir como maioria sem quebrar garantia.

**Escolha:** Usar implementação madura; compreender membership, quorum e limites de falha.

**Verificação proposta:** Testar leader crash, logs divergentes, eleição repetida e reconfiguração.

**Referências recomendadas:** [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf)

## distribuidos_sagas — Sagas e compensações

**Definição:** Saga organiza passos locais e compensações para negócio distribuído sem rollback global automático.

**Mecanismo:** Compensação é nova ação semântica e pode falhar; execução precisa estado durável, idempotência e reconciliação.

**Falhas comuns:** Estorno não apaga email enviado; rollback técnico não desfaz toda observação externa.

**Escolha:** Definir estados intermediários, prazos e recuperação manual para casos irresolvíveis.

**Verificação proposta:** Injetar falha em cada etapa e compensação; verificar ausência de recursos órfãos.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)


