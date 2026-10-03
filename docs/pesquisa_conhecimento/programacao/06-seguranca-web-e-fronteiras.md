# Segurança defensiva: fluxo de dados e limites de confiança

## Mapear primeiro
Identificar ativos, atores, entradas, saídas, armazenamentos e trust boundaries. A entrada pode ser HTTP, arquivo, mensagem, import de planilha, URL, webhook ou saída de ferramenta. O usuário autenticado continua potencialmente hostil ao recurso de outro usuário.

Para cada fluxo registre: principal, tenant, recurso, ação, efeito, limite de bytes/trabalho, credencial usada, log produzido e caminho de erro. Aplicar autorização por objeto no servidor e constraint/escopo em consulta.

## Contexto de interpretação
Entrada em SQL vira valor parametrizado; nome de coluna precisa allowlist. Entrada em shell deve evitar shell e validar opções. Texto em DOM deve usar textContent; HTML permitido exige sanitização revisada; URL exige esquema/destino permitidos. Encoding correto para um contexto não autoriza reutilização em outro.

CORS não autentica servidor nem bloqueia todo request externo. CSRF se preocupa com credenciais enviadas automaticamente. XSS pode agir com sessão mesmo sem ler cookie HttpOnly. CSP é camada, não substituto de sink seguro. SSRF é request originada pelo servidor e pede limites de destino, redirect, resolução e egress.

## Credenciais
Senhas usam algoritmo adequado de derivação/hashing; não hash rápido simples. Tokens exigem assinatura, issuer, audience, tempo e política de revogação. PKCE, state e nonce protegem propriedades específicas, não são intercambiáveis. Não colocar segredo em bundle, build context ou log. Rotação exige versão de chave e período de compatibilidade conforme política.

## Recursos também são superfície de ataque
Regex, parser, arquivo descompactado, consulta e função CPU-bound podem consumir tempo/memória excessivos. Limite após alocação é tardio. Definir tamanho, profundidade, taxa, prazo e comportamento no limite. Mensagem de erro não deve revelar stack, query interna ou detalhes de credenciais.

## Cadeia de suprimentos
Dependência nova, script postinstall, action CI e artefato devem ter origem e permissões revisadas. Tag mutável não é pin imutável. Lockfile fixa resolução, não atesta segurança. Scan é sinal que requer interpretação. Construir em ambiente mínimo, inspecionar tarball/layers e reduzir capacidades de deploy.

## Evidência
Matriz de autorização por papel/tenant; payload em cada sink; header/cookie em fluxos relevantes; origin inválida; token adulterado/expirado; URL com redirect privado; merge com chave especial; fuzz de parser e regex longa. Teste passa somente se efeito protegido não ocorreu e resposta/telemetria cumprem contrato.

