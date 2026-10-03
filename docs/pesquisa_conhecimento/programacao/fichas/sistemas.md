# Fichas avançadas: sistemas

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## sistemas_processes — Processos, threads e isolamento

**Definição:** Processo fornece contexto de recursos/endereço; thread compartilha recursos segundo SO/runtime.

**Mecanismo:** Syscalls atravessam interface kernel; scheduling e contexto têm custos. Containers normalmente compartilham kernel do host.

**Falhas comuns:** Thread não é processo leve com isolamento equivalente; container não é VM completa.

**Escolha:** Escolher isolamento pelo modelo de ameaça e custo operacional.

**Verificação proposta:** Testar limite de recursos, crash isolation e acesso a filesystem/rede.

**Referências recomendadas:** [Linux kernel documentation](https://docs.kernel.org/)

## sistemas_virtual-memory — Memória virtual e page faults

**Definição:** Endereços virtuais são mapeados por tabelas e TLB; proteção e demanda são funções distintas.

**Mecanismo:** Page fault pode carregar página, implementar copy-on-write ou indicar acesso inválido.

**Falhas comuns:** Memória virtual não é só swap; RSS, virtual size e memória compartilhada não são intercambiáveis.

**Escolha:** Medir working set, faults e pressão física antes de diagnosticar leak.

**Verificação proposta:** Comparar alocação virtual com páginas tocadas e efeitos de fork/copy-on-write.

**Referências recomendadas:** [Linux kernel documentation](https://docs.kernel.org/)

## sistemas_cache-locality — Localidade e cache CPU

**Definição:** Caches exploram reuso temporal/espacial; layout influencia custo apesar da mesma complexidade.

**Mecanismo:** Pointer chasing, false sharing e acesso strided podem aumentar misses/coherence.

**Falhas comuns:** Estrutura assintoticamente melhor pode perder em tamanhos reais; cache line size não é constante universal.

**Escolha:** Medir com profiler e workloads representativos; agrupar dados usados juntos.

**Verificação proposta:** Comparar array contíguo com estrutura ligada e threads escrevendo campos próximos.

**Referências recomendadas:** [Linux kernel documentation](https://docs.kernel.org/)

## sistemas_memory-model — Happens-before e memory model

**Definição:** Modelo de memória define observações legais de operações concorrentes sob sincronização.

**Mecanismo:** Atomicidade, ordem e visibilidade são propriedades diferentes; linguagens definem relações específicas.

**Falhas comuns:** volatile tem semânticas distintas em C/C++/Java; não é mutex geral.

**Escolha:** Usar primitives adequadas e raciocinar por invariant compartilhado.

**Verificação proposta:** Testar litmus tests com modelo específico e detector de race quando disponível.

**Referências recomendadas:** [C++ working draft](https://eel.is/c++draft/)

## sistemas_deadlocks — Deadlock e progresso

**Definição:** Deadlock impede progresso por espera circular de recursos; starvation e livelock diferem.

**Mecanismo:** Ordem global de locks, redução de hold-and-wait e protocolos de timeout podem prevenir/mitigar classes.

**Falhas comuns:** Timeout apenas mascara alguns deadlocks e pode deixar estado parcial; lock-free não significa wait-free.

**Escolha:** Documentar ordem e recursos adquiridos; usar diagnóstico de waits.

**Verificação proposta:** Inverter ordem em cenário controlado e verificar prevenção e cleanup.

**Referências recomendadas:** [POSIX specifications](https://pubs.opengroup.org/onlinepubs/9799919799/)

## sistemas_filesystem — Filesystem e durabilidade

**Definição:** Arquivos, diretórios, metadata e flush têm garantias dependentes de SO/filesystem.

**Mecanismo:** Rename pode ser atômico em escopo específico; atomicidade não equivale a durabilidade após perda de energia.

**Falhas comuns:** write concluído não garante persistência física; renomear entre filesystems pode não ser operação atômica.

**Escolha:** Para durabilidade usar protocolo de temp/write/flush/rename/directory sync conforme plataforma.

**Verificação proposta:** Simular crash e validar arquivos completos/versões recuperáveis.

**Referências recomendadas:** [POSIX specifications](https://pubs.opengroup.org/onlinepubs/9799919799/)

## sistemas_ffi — FFI e fronteira de segurança

**Definição:** FFI conecta linguagens/runtime com regras próprias de ABI, lifetime e representação.

**Mecanismo:** Ownership de buffer, calling convention, exceções e threads precisam contrato compartilhado.

**Falhas comuns:** Ponte unsafe pode invalidar garantias de linguagem segura; ponteiro válido ontem pode expirar hoje.

**Escolha:** Minimizar superfície e encapsular unsafe com testes e validação de tamanhos.

**Verificação proposta:** Testar erro, callback após dispose, tamanho incorreto e execução concorrente.

**Referências recomendadas:** [The Rust Programming Language](https://doc.rust-lang.org/book/)

