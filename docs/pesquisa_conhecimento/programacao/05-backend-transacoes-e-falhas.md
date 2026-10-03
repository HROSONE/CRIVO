# Backend: preservar invariantes sob falha e concorrência

## Exemplo completo de requisito
Reserva de estoque: quantidade é inteiro positivo e não pode exceder disponível; usuário só reserva no tenant autorizado; retry do mesmo pedido não pode criar segunda reserva; sistema não pode anunciar sucesso sem registro durável.

Pipeline: autenticar, validar input, autorizar recurso/tenant, começar transação, registrar chave idempotente com unicidade, atualizar estoque condicionalmente, inserir reserva/outbox, commit, responder. Constraints e operações condicionais são a última linha contra interleaving. Checagem read-then-write fora de transação não basta.

```sql
UPDATE estoque
SET disponivel = disponivel - $1
WHERE tenant_id = $2 AND produto_id = $3 AND disponivel >= $1
RETURNING disponivel;
```
Quantidade precisa ser validada antes e protegida por constraints adequadas. Retorno vazio é falha/conflito de negócio, não sucesso. Caso outra etapa precise falhar, operação pertence à mesma transação. SQL é exemplo PostgreSQL; placeholders e regras mudam por driver/SGBD.

## Idempotência não é só cache
Chave deve incluir escopo/principal/operação; request hash evita reutilização com payload diferente. Estado em andamento exige comportamento definido. Persistir apenas depois do efeito permite duas execuções concorrentes. TTL curto demais permite duplicação tardia. Cache de memória não sobrevive a restart.

Retorno de timeout admite resultado desconhecido: o servidor pode ter cometido efeito e perdido resposta. Cliente consulta estado ou repete chave idempotente. Não registrar tarefa como falha definitiva só porque conexão caiu.

## Banco, broker e email
Transação de banco não inclui automaticamente broker/email. Outbox grava evento com mudança local; publisher pode duplicar na janela publish/mark. Consumer faz dedupe e efeito idempotente no seu escopo. Exactly once deve especificar limite, transporte e efeitos; não prometer por usar uma ferramenta.

## Contratos e overload
Defina método HTTP, status, erro estruturado, paginação, versão e timeout. Cada recurso tem orçamento de concorrência/bytes. Admission control rejeita cedo antes que fila ilimitada provoque colapso. Rate limiting por principal é diferente de capacidade global. Retry deve respeitar deadline e backoff; cascata de retries amplia incidente.

## Produção e observabilidade
Logar request/correlation ID sem secrets. Usar métricas de latência/erro/saturação e traces amostrados, evitando labels de cardinalidade ilimitada. No shutdown: readiness false, parar admissão, drenar com prazo, fechar pools, confirmar exit. Durante migração, versões antiga e nova devem coexistir; rollback de binário não recupera schema destrutivo.

## Exercícios de falha
Cair depois de commit e antes da resposta; cair depois de publish e antes de mark; fazer duas reservas simultâneas com último item; expirar token no meio da operação; provocar timeout do pool; iniciar rollout durante request longo. Especificar resultado legal em cada ponto antes de testar.

