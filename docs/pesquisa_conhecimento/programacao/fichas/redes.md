# Fichas avançadas: redes

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## redes_http-semantica — Métodos e status HTTP

**Definição:** Métodos têm semântica de segurança e idempotência; códigos representam classe de resultado.

**Mecanismo:** GET é seguro; PUT e DELETE são idempotentes no efeito pretendido, embora respostas possam variar; POST não é idempotente por definição.

**Falhas comuns:** Retentar POST sem protocolo pode duplicar cobrança; responder 200 a toda falha esconde contrato.

**Escolha:** Escolher método/status pelo recurso e efeito; definir códigos e body de erro.

**Verificação proposta:** Testar repetição, ausência de recurso, conflito, validação e cliente com retry.

**Referências recomendadas:** [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)

## redes_http-cache — Cache HTTP e validators

**Definição:** Freshness evita revalidação enquanto válido; validators como ETag permitem revalidação condicional.

**Mecanismo:** Cache-Control e Vary orientam caches; no-cache permite armazenamento com revalidação, no-store instrui não armazenar.

**Falhas comuns:** Cache público de resposta personalizada pode vazar dados; Vary faltante serve variante errada.

**Escolha:** Classificar dados por privacidade e freshness; usar validators e invalidation clara.

**Verificação proposta:** Testar usuário A/B, mudança de conteúdo, 304, Age e headers de autorização.

**Referências recomendadas:** [HTTP Caching RFC 9111](https://www.rfc-editor.org/rfc/rfc9111)

## redes_cors — CORS e same origin

**Definição:** CORS regula acesso de scripts a respostas cross-origin no navegador; não é autenticação de API.

**Mecanismo:** Preflight verifica permissões em condições específicas; credentials exigem configuração compatível. Origin precisa de allowlist exata.

**Falhas comuns:** CORS não bloqueia cliente servidor nem impede todos requests de efeito; refletir origin indiscriminadamente é inseguro.

**Escolha:** Separar CORS, CSRF e autorização; responder allowlist e cachear com Vary quando aplicável.

**Verificação proposta:** Testar origin permitido/proibido, credentials, OPTIONS e request de forma simples.

**Referências recomendadas:** [Fetch Standard](https://fetch.spec.whatwg.org/)

## redes_websocket — WebSocket e reconexão

**Definição:** WebSocket mantém canal bidirecional; transporte não fornece protocolo de negócio automaticamente.

**Mecanismo:** Heartbeat, reconnect, backoff, sequência e resync detectam/recuperam conexão; buffers precisam bound.

**Falhas comuns:** Reconectar sem resync pode perder eventos; autenticação inicial não elimina necessidade de rever autorização.

**Escolha:** Definir frame schema, limites, heartbeat e snapshot após lacuna.

**Verificação proposta:** Testar rede interrompida, token revogado e consumidor lento.

**Referências recomendadas:** [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)

## redes_sse — Server Sent Events

**Definição:** SSE transmite eventos servidor-cliente sobre HTTP em formato próprio.

**Mecanismo:** IDs permitem retomada conforme servidor; proxies/timeouts podem exigir heartbeat e buffering adequado.

**Falhas comuns:** Manter conexão não garante evento único; callback deve suportar replay e lacunas.

**Escolha:** Usar para fluxo unidirecional; documentar ordem, dedupe e retenção.

**Verificação proposta:** Testar reconexão, replay, proxy e encerramento gracioso.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## redes_tcp — TCP e framing

**Definição:** TCP fornece fluxo ordenado de bytes sob seu protocolo; não preserva fronteiras de mensagens da aplicação.

**Mecanismo:** send/read podem dividir ou juntar dados; framing por tamanho/delimitador precisa parser incremental e bounds.

**Falhas comuns:** Uma read não corresponde a uma mensagem; half-open e timeout exigem gestão.

**Escolha:** Definir framing, tamanho máximo e manejo de EOF parcial.

**Verificação proposta:** Testar header/body fragmentados, múltiplas mensagens no chunk e EOF no meio.

**Referências recomendadas:** [HTTP Semantics RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)

## redes_dns-tls — DNS e TLS

**Definição:** DNS resolve nomes; TLS autentica peer e protege transporte sob parâmetros e confiança.

**Mecanismo:** Certificado precisa validar hostname e cadeia; session/resolution caches afetam comportamento e failover.

**Falhas comuns:** TLS não valida autorização nem sanitiza conteúdo; ignorar certificado anula propriedade essencial.

**Escolha:** Manter verificação TLS e políticas de timeout/rotação; medir etapa DNS/connect/handshake.

**Verificação proposta:** Testar certificado errado, expiração, mudança de IP e falha de resolução.

**Referências recomendadas:** [TLS 1.3 RFC 8446](https://www.rfc-editor.org/rfc/rfc8446)


