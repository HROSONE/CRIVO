# Fichas avançadas: backend

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## backend_node-streams — Streams e backpressure

**Definição:** Streams permitem transportar dados incrementalmente com controle de fluxo.

**Mecanismo:** No Node, write false sinaliza pressão; aguardar drain ou usar pipeline. highWaterMark é limiar, não limite absoluto universal de memória.

**Falhas comuns:** Ignorar pressão aumenta memória; erro em stream intermediária sem cleanup deixa sockets abertos.

**Escolha:** Preferir pipeline, limites de bytes e AbortSignal; não bufferizar arquivo inteiro sem necessidade.

**Verificação proposta:** Testar consumidor lento, erro no meio, cancelamento e memória com arquivo grande.

**Relações:** fronteira_streaming-parsers, backend_shutdown, operacao_capacity

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## backend_node-pool — Thread pool e event loop Node

**Definição:** Node combina loop de eventos, operações do sistema e pool para determinadas APIs como fs/crypto/dns.lookup.

**Mecanismo:** API assíncrona pode consumir pool; saturação de tarefas longas aumenta latência de outras. DNS lookup/resolve têm caminhos diferentes.

**Falhas comuns:** Assumir que async nunca usa thread ou que aumentar pool sempre melhora performance é falso.

**Escolha:** Medir loop delay, duração e pool-bound workload antes de mudar concorrência.

**Verificação proposta:** Carregar crypto e fs simultaneamente e comparar cauda de latência e uso de CPU.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## backend_shutdown — Encerramento gracioso

**Definição:** Serviço precisa parar de aceitar trabalho, drenar operações e liberar recursos antes de sair.

**Mecanismo:** SIGTERM inicia deadline de shutdown; remover readiness, fechar listener, aguardar inflight e fechar conexões/workers.

**Falhas comuns:** process.exit imediato corta respostas/logs; drenar sem prazo trava rollout.

**Escolha:** Definir budget de encerramento e coordenar load balancer/orquestrador.

**Verificação proposta:** Enviar sinal durante request e verificar resposta, deadline e término sem handles pendentes.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## backend_pagination — Paginação offset e cursor

**Definição:** Offset pula posições; cursor usa continuidade por chave/ordem e evita certos problemas de escala.

**Mecanismo:** Keyset precisa ordenação total com tie-breaker e índice compatível; cursor inclui contexto do filtro.

**Falhas comuns:** Mutação entre páginas pode causar duplicidade/omissão; cursor assinado não substitui autorização.

**Escolha:** Usar keyset em grandes feeds; definir snapshot/freshness e expiração quando relevante.

**Verificação proposta:** Testar valores iguais, inserção concorrente, exclusão e cursor de outro tenant.

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)

## backend_validation — Validação em camadas

**Definição:** Parse de formato, invariantes de domínio e integridade transacional são verificações distintas.

**Mecanismo:** Schema valida estrutura; serviço verifica política; banco impõe constraints finais contra concorrência.

**Falhas comuns:** Checar unicidade apenas antes do INSERT tem janela TOCTOU; cliente validado não é confiável.

**Escolha:** Aplicar limites e allowlists cedo, invariantes no domínio e constraints no armazenamento.

**Verificação proposta:** Testar requests simultâneos, campos extras, limites e tentativa de bypass do frontend.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## backend_rate-limit — Rate limiting e admissão

**Definição:** Limita trabalho por principal/chave e período para proteger capacidade.

**Mecanismo:** Token bucket permite burst controlado; janela fixa tem efeito de borda. Coordenação distribuída exige semântica explícita.

**Falhas comuns:** Limiter por IP pode punir NAT e ignorar usuário autenticado; memória não limitada vira ataque.

**Escolha:** Combinar cotas por usuário/tenant e proteção global; retornar orientação de retry.

**Verificação proposta:** Testar borda de janela, bursts, múltiplas réplicas e indisponibilidade do limiter.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)


