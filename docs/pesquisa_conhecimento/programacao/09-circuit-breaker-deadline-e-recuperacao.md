# Circuit breaker: estado, falhas concorrentes e recuperação

## Por que timeout/retry/breaker são diferentes
Timeout limita espera de uma chamada; retry repete tentativa; breaker recusa novas chamadas quando histórico indica dependência degradada. Admission limita carga antes da execução. Nenhuma dessas técnicas torna uma operação de escrita idempotente.

O exemplo `CircuitBreaker` é local ao processo, usa falhas consecutivas para threshold e um cooldown monotônico. Não implementa janela deslizante, estado distribuído, métricas nem cancelamento da chamada remota. Seus parâmetros têm que ser escolhidos com evidência da dependência e SLO.

## Máquina de estados
- closed: admite chamadas; sucesso atual zera falhas; falha técnica incrementa contador.
- open: recusa sem executar task até retryAt.
- half-open: admite somente um probe; demais chamadas são recusadas.
- probe bem sucedido: fecha e zera falhas.
- probe com falha técnica: reabre e inicia novo cooldown.
- erro classificado como negócio durante probe: fecha neste modelo, pois resposta demonstra dependência operacional.

Classificador isFailure precisa ser puro e não lançar. Clock now precisa fornecer tempo monotônico coerente. Outros contratos são possíveis; por exemplo, considerar determinado erro de negócio como degradação deve ser decisão documentada, não regra universal.

## Corrida que implementação ingênua perde
Duas chamadas entram closed. B falha e abre circuito. A, iniciada antes, termina com sucesso depois. Sem controle de geração, A pode fechar imediatamente circuito que deveria permanecer open.

O exemplo atribui epoch ao estado; resultado só modifica histórico se epoch de admissão continua atual. Mudança de geração invalida efeito tardio sobre breaker, sem alterar o resultado entregue ao caller. Epoch não é fencing de banco nem sincronização entre réplicas: é mecanismo local de coerência de estado.

## Probe não é avalanche
Um probe em andamento precisa impedir centenas de probes simultâneos. O flag de probe é liberado em finally. Estado e epoch determinam quais resultados podem abrir/fechar. Teste com deferred promise permite deixar probe pendente sem dormir, então tenta segunda chamada e exige recusa.

Para produção, medir número de recusas, falhas técnicas, tempo em open e latência dos probes. Circuito por tenant/chave exige cardinalidade/bound; map de breakers ilimitado pode virar leak/ataque. Processo recém-iniciado não conhece histórico anterior.

## Retentativas
Retentativa deve ter budget global e política por erro/efeito. Full jitter reduz sincronização, mas depende de RNG e teto. Retry-After pode ser considerado dentro do prazo. Não retentar breaker aberto em loop apertado; não somar tentativas invisíveis em várias camadas.

## Evidência
Testes verificam threshold, task recusada não executada, probe único, nova janela após falha, erro de negócio e sucesso tardio. Próximas avaliações devem comparar goodput, cauda e custo de retries sob overload real. Testes de estado não substituem teste de carga.

**Relações:** js_circuit-breaker, distribuidos_timeouts, operacao_load-shedding, arquitetura_bulkheads.

