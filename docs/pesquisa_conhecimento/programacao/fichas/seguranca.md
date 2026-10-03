# Fichas avançadas: seguranca

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## seguranca_authn-authz — Autenticação e autorização

**Definição:** Autenticação identifica principal; autorização decide acesso a recurso/ação sob contexto.

**Mecanismo:** Permissão deve ser verificada por objeto, tenant e operação no servidor; RBAC/ABAC modelam políticas distintas.

**Falhas comuns:** Usuário autenticado não pode acessar todo id; esconder botão não fornece autorização.

**Escolha:** Negar por padrão, centralizar política auditável e verificar escopo em consultas.

**Verificação proposta:** Trocar IDs entre usuários/tenants e testar cada papel em cada operação.

**Relações:** seguranca_session, seguranca_oauth, seguranca_threat-model

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_session — Sessões e cookies

**Definição:** Sessão associa credencial a estado autenticado; cookies possuem atributos que controlam envio/acesso.

**Mecanismo:** HttpOnly limita leitura via JS; Secure restringe transporte; SameSite reduz determinadas condições de CSRF, não toda exposição.

**Falhas comuns:** JWT em localStorage é acessível por XSS; HttpOnly não impede ação autenticada por script malicioso.

**Escolha:** Escolher sessão/revogação por ameaça; rotacionar após login e expirar credenciais.

**Verificação proposta:** Testar logout, session fixation, expiração, subdomínios e ações via origem externa.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_oauth — OAuth, OIDC e PKCE

**Definição:** OAuth delega autorização; OIDC adiciona identidade; PKCE vincula authorization code ao iniciador.

**Mecanismo:** Validar issuer, audience, assinatura, expiração e redirect URI; state/nonce têm papéis específicos.

**Falhas comuns:** Decodificar JWT não verifica assinatura; segredo embutido em SPA não é segredo.

**Escolha:** Usar bibliotecas/provedor revisados e BCP atual; minimizar escopos e proteger tokens.

**Verificação proposta:** Testar issuer/audience errado, replay, redirect inválido, algoritmo inesperado e clock skew.

**Referências recomendadas:** [OAuth 2.0 Security Best Current Practice RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)

## seguranca_xss — XSS e output encoding

**Definição:** Conteúdo não confiável pode se tornar script quando inserido em contexto executável.

**Mecanismo:** Encoding depende do contexto HTML, atributo, JS, URL ou CSS; textContent evita interpretação HTML. CSP ajuda como camada adicional.

**Falhas comuns:** Sanitizar com regex é insuficiente; string segura em HTML pode ser insegura em JavaScript.

**Escolha:** Preferir APIs de texto e templates com escape; sanitização revisada para HTML permitido.

**Verificação proposta:** Testar payloads em cada sink, URLs javascript e rich text com atributos/eventos.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_csrf — CSRF

**Definição:** Navegador pode enviar credenciais automaticamente em request induzido por origem externa.

**Mecanismo:** Tokens vinculados à sessão, verificações Origin/Referer e SameSite ajudam; escolha depende do fluxo.

**Falhas comuns:** CORS não impede todos requests de efeito; GET com mutação amplia risco.

**Escolha:** Exigir verificação em operações de mudança e evitar efeito em métodos seguros.

**Verificação proposta:** Testar formulário cross-origin, ausência/token errado e subdomínio não confiável.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_injection — SQL e command injection

**Definição:** Concatenar entrada em gramática de comandos permite que dados virem instruções.

**Mecanismo:** Queries parametrizadas separam valores de SQL; identificadores/ORDER BY precisam allowlist. Spawn com argumentos evita shell, mas opção maliciosa ainda importa.

**Falhas comuns:** Escaping caseiro e parâmetros para nomes de tabela não resolvem todos contextos; shell true reabre risco.

**Escolha:** Preferir APIs sem shell, argumentos validados e privilégios mínimos.

**Verificação proposta:** Testar aspas, delimitadores, flags como argumentos e nomes de coluna inesperados.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_ssrf — SSRF e acesso de rede

**Definição:** Servidor que busca URL fornecida pode acessar destinos internos ou serviços privilegiados.

**Mecanismo:** Allowlist de hosts/esquemas, validação de IP/resolução, redirect e egress control trabalham juntos; DNS rebinding exige cuidado.

**Falhas comuns:** Bloquear só localhost textual não bloqueia IPv6, redirects e resolução para IP privado.

**Escolha:** Restringir destinos por necessidade real e impor timeout/limites de bytes.

**Verificação proposta:** Testar URL privada, redirect para privado, mudança DNS e protocolos inesperados.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_crypto — Hash, MAC e criptografia

**Definição:** Hash resume dados; MAC autentica com segredo; criptografia protege confidencialidade conforme esquema.

**Mecanismo:** AEAD autentica ciphertext e dados associados; nonce deve seguir unicidade exigida pelo algoritmo. Senhas usam função de hashing apropriada.

**Falhas comuns:** SHA-256 simples não é armazenamento adequado de senha; nonce repetido pode quebrar garantias.

**Escolha:** Usar bibliotecas e parâmetros revisados, gerência de chaves e protocolos estabelecidos.

**Verificação proposta:** Testar adulteração, rotação de chave, nonce policy e recuperação autorizada.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_supply-chain — Cadeia de suprimentos

**Definição:** Dependências, scripts de instalação, CI e artefatos fazem parte da superfície de ataque.

**Mecanismo:** Lockfiles, provenance, checksums, scans e permissões mínimas reduzem risco; lockfile não prova ausência de vulnerabilidade.

**Falhas comuns:** Segredo em build log ou pacote persiste; pinning de tag mutável não fixa commit.

**Escolha:** Revisar dependências novas, automatizar updates e construir artefato verificável.

**Verificação proposta:** Inspecionar tarball, permissões CI, secrets redigidos e dependência adulterada.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_privacy — Minimização e classificação de dados

**Definição:** Dados precisam retenção, acesso e finalidade explícitos; classificação orienta controles.

**Mecanismo:** Redaction, criptografia, segregação e eliminação precisam cobrir logs, caches e backups.

**Falhas comuns:** Mascarar UI não remove informação da API; hash de valor previsível pode ser reidentificado.

**Escolha:** Coletar mínimo e testar export/eliminação dentro do escopo do produto.

**Verificação proposta:** Buscar campos sensíveis em response, telemetry, cache e artefato.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## seguranca_threat-model — Threat modeling

**Definição:** Modelo de ameaça identifica ativos, atores, boundaries e abusos plausíveis.

**Mecanismo:** Data flow e trust boundaries orientam controles e testes; atualizar quando integração muda.

**Falhas comuns:** Checklist genérico pode ignorar principal invariante do negócio; criptografia não corrige IDOR.

**Escolha:** Começar por fluxos críticos e evidência de controle por ameaça.

**Verificação proposta:** Desenhar request de usuário hostil e tentar atravessar tenant/privilege boundary.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)


