# Roteiro para geração futura de projetos completos

Este capítulo descreve requisitos de competência. O acervo não modifica pesos, roteador ou gerador atual do CRIVO.

## 1. Construir contrato observável
Extrair objetivo, entradas, saídas, usuários, host, escala, persistência, restrições, acessibilidade e critérios de aceite. Onde há ambiguidade, registrar hipótese reversível. Escolher primeira fatia que atravessa UI/API/dados quando necessário.

## 2. Projetar domínio e fronteiras
Listar estados válidos, transições, invariantes, DTOs e modelo de autorização. Definir dependências e owner de recursos. Para operação distribuída, descrever falha depois de cada efeito, retry e reconciliação. Escolher monólito modular antes de distribuir sem evidência de necessidade.

## 3. Emitir scaffold coerente
Manifest de dependências e versões; scripts de typecheck/test/build; tsconfig do host; diretórios por responsabilidade; documentação de execução e ambiente sem secrets; health checks quando aplicáveis. Não inventar API ou versão de biblioteca: consultar documentação e confirmar assinatura instalada.

## 4. Implementar menor fluxo completo
Validar unknown na fronteira; construir valores; executar regra; persistir com constraints; serializar resultado; UI mostra loading/empty/error/success acessíveis. Nenhum stub deve ser apresentado como funcional. Distinguir exemplo, pseudocódigo e implementação.

## 5. Verificar de forma independente
Typecheck estático, runtime de exemplos, testes de invariant/edge, integração real e jornada no navegador conforme aplicação. Oráculo não pode ser só uma cópia da implementação. Tarefas didáticas públicas deste acervo não são holdout: elaborar avaliação externa por família nova antes de medir capacidade.

## 6. Revisar como responsável pelo sistema
Inspecionar autorização, concorrência, cleanup, limite de recursos, risco de migração, compatibilidade, observabilidade e documentação. Empacotar artefato e executar como consumidor. Mensagem final identifica o que roda, o que foi medido e limitações específicas.

## Rubrica de geração (0–4 por eixo)
Correção funcional; modelagem/invariantes; robustez/falhas; tipos/contratos; segurança; teste independente; desempenho adequado; operação/reprodutibilidade; acessibilidade quando aplicável; manutenção/documentação.
0 ausente; 1 frágil em caso nominal; 2 atende contrato básico; 3 cobre falhas e limites; 4 demonstra decisões e evidência independente. Não somar e chamar de senioridade sem calibração humana e tarefas variadas.

## Famílias de projeto
CLI de CSV com streaming; API de estoque idempotente; calendário com timezone; editor colaborativo offline; dashboard acessível com paginação; pacote TS ESM com declarations; parser incremental; scheduler com bound; outbox worker; migração expand/contract; sistema de feature flags; motor de regras com AST. Cada projeto combina conceitos de forma diferente e deve ter requisitos novos.

