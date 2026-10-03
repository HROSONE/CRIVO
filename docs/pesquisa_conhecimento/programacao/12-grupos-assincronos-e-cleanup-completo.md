# Grupo assíncrono: cancelar e esperar são obrigações distintas

## Contrato do exemplo
runGroup recebe array finito de funções, passa AbortSignal comum e retorna resultados em ordem de entrada. Primeira falha observada determina erro primário e aborta siblings. O grupo aguarda todos settlements antes de retornar erro, removendo listener do signal pai em finally. Parent já abortado não inicia tarefas.

Se a falha for undefined, um booleano separado registra que houve erro: usar apenas `if(error)` perderia rejeições falsy. A ordem da primeira falha é ordem observada pelo runtime, não ordem universal por horário remoto.

## Por que all não basta
Promise.all rejeita cedo, mas tarefas restantes continuam. O caller pode fechar recurso compartilhado enquanto sibling ainda usa o recurso. allSettled permite join, porém não cancela sozinho. O grupo combina cancelamento cooperativo com join para terminar o escopo.

Task precisa observar signal e fechar seus próprios recursos em finally. Uma task que ignora sinal e nunca conclui faz grupo nunca concluir. Deadline no pai sinaliza encerramento, mas não força CPU arbitrária a parar; para código não confiável ou não cooperativo, usar isolamento e terminável worker/processo com políticas adequadas.

## Início e falha síncrona
Factories são agendadas por Promise.resolve().then, e cada uma verifica sinal antes de iniciar. Throw síncrono é convertido em rejeição. O array de funções é validado antes de registrar listener; assim, input inválido não deixa listener pendurado.

Este exemplo admite todas as tarefas de uma vez. Para coleção grande, usar scheduler limitado, não criar milhões de Promises. Concorrência estruturada não implica concorrência limitada. Budget de memória/trabalho é obrigação adicional.

## Cleanup que falha
Erro de cleanup pode mascarar erro inicial se recurso lançar em finally. Política de produção pode manter causa, agregar falhas ou registrar erros secundários. Não substituir falha primária por mensagem genérica de cancelamento. O grupo conserva primeira falha observada, mas não fornece relatório completo de erros secundários.

## Evidência
Deferred promises forçam ordem sem sleeps. Testes verificam resultados ordenados, sibling abortado, cleanup atrasado ainda aguardado, parent abort, listener removido e nenhuma tarefa iniciada para parent já abortado. Os testes não simulam todos host callbacks nem falha de processo.

## Aplicação
Fan-out de leitura pode precisar cancelar consultas restantes quando resultado perde utilidade. Fluxo com efeitos externos exige idempotência/compensação antes de cancelar. Nunca inferir rollback porque tarefas locais terminaram ou foram abortadas.

**Relações:** js_task-group, js_cancelamento, js_combinadores, fronteira_structured-concurrency.

