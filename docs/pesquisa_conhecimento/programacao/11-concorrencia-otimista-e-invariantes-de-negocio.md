# Controle otimista: detectar conflito sem inventar transação

## Modelo executável local
VersionedCell conserva valor clonado e versão monotônica. read retorna snapshot independente. compareAndSet só aceita versão atual; prepara clone antes de modificar estado e incrementa versão junto com atualização síncrona. Erro de clone não consome versão. Versão esgotada falha explicitamente.

O exemplo protege apenas esta célula dentro de um agente JS. Não é armazenamento persistente, banco de dados nem algoritmo lock-free de memória compartilhada. Duas réplicas com duas células locais continuam duas autoridades diferentes.

## Banco real
A tradução comum é atualização condicional:
```sql
UPDATE documento
SET conteudo = $1, versao = versao + 1
WHERE tenant_id = $2 AND id = $3 AND versao = $4
RETURNING id, versao;
```
SQL ilustrativo PostgreSQL, não executado neste acervo. row count vazio indica conflito ou recurso ausente/inacessível conforme contrato. Não revelar existência de outro tenant. Parametrização protege valores; autorização e scoping protegem recurso.

## Retry correto
Conflito exige reler e refazer decisão usando novo estado, ou pedir resolução ao usuário. Retentar só write de decisão antiga pode violar domínio. Retry limitado não deve repetir email, pagamento ou outra ação externa sem idempotência.

Para estoque, UPDATE condicionado a quantidade disponível pode ser mais direto que read/version/write. Para regra de múltiplas linhas, CAS de uma linha não fornece serializability. Write skew pode persistir se operações alteram partes diferentes de um conjunto.

## Snapshot e alias
read que retorna referência interna permite consumidor modificar valor sem incrementar versão. Clone fecha essa fronteira para tipos suportados. structuredClone não preserva toda classe/protótipo/função; DTO admitido precisa ser documentado e validado. Valores imensos tornam read/write caros; custo é proporcional ao grafo clonado.

Versão é contador de mudança no escopo definido, não timestamp nem permissão. Controle otimista não resolve lost response de uma operação já aplicada: protocolo idempotente deve relacionar request ao resultado.

## Evidência
Testes usam dois leitores na mesma versão, exigem um vencedor e um conflito sem sobrescrita, verificam clone nas fronteiras e erro de clone sem mudança. Em banco, repetir cenário com duas conexões e transações reais é obrigatório antes de usar como prova de produção.

## Escolha
Baixa contenção e conflitos resolvíveis favorecem versão otimista. Alta contenção pode exigir operação atômica direta, serialização/lock ou redesign do aggregate. Medir taxa de conflitos, duração/retries e latência de cauda.

**Relações:** dados_optimistic-lock, dados_transactions, dados_write-skew, distribuidos_idempotencia.

