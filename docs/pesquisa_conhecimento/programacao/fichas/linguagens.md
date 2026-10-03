# Fichas avançadas: linguagens

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## linguagens_python — Python e modelo de execução

**Definição:** Python tem objetos, tipagem dinâmica e protocolos; annotations não validam runtime por padrão.

**Mecanismo:** Iteradores, generators, context managers e dataclasses simplificam código; GIL e free threading dependem da implementação/versão.

**Falhas comuns:** Default mutável conserva objeto entre chamadas; copiar lista é superficial; thread não garante ganho CPU-bound.

**Escolha:** Usar with para recursos, type hints mais checker e processos/native para CPU conforme medição.

**Verificação proposta:** Testar argumento default, alias, iterator esgotado e versão de runtime.

**Referências recomendadas:** [Python documentation](https://docs.python.org/3/)

## linguagens_rust — Rust ownership e borrowing

**Definição:** Ownership delimita lifetime; referências compartilhadas/mutáveis seguem regras que sustentam segurança de safe code.

**Mecanismo:** Lifetimes relacionam validade, não prolongam objeto; Send/Sync tratam transferência/compartilhamento entre threads.

**Falhas comuns:** unsafe não desliga todas verificações nem torna operação correta; Arc não torna conteúdo interior thread-safe automaticamente.

**Escolha:** Preferir safe abstractions; unsafe pequeno com invariant documentado e ferramentas apropriadas.

**Verificação proposta:** Testar borrow errors, drop, compartilhamento e sanitizers/Miri quando compatível.

**Referências recomendadas:** [The Rust Programming Language](https://doc.rust-lang.org/book/)

## linguagens_go — Go, goroutines e channels

**Definição:** Go oferece goroutines, channels, interfaces estruturais e GC.

**Mecanismo:** Channel comunica/sincroniza; context propaga cancelamento; goroutines precisam terminar e leaks podem reter recursos.

**Falhas comuns:** Enviar para canal sem consumidor pode bloquear; fechar canal errado causa panic; nil interface com valor tipado pode não ser nil.

**Escolha:** Definir owner de close e cancelar pipelines; limitar concorrência.

**Verificação proposta:** Usar race detector, testar cancelamento e goroutine count após término.

**Referências recomendadas:** [Go Language Specification](https://go.dev/ref/spec)

## linguagens_cpp — C++ RAII e value semantics

**Definição:** RAII vincula cleanup a lifetime de objetos; value/move semantics e templates modelam recursos.

**Mecanismo:** unique_ptr expressa ownership exclusivo; shared_ptr tem custo e ciclos; UB limita raciocínio da implementação.

**Falhas comuns:** Use-after-free, dangling reference e invalidation de iterator persistem; move não significa fonte sempre vazia.

**Escolha:** Preferir containers e smart pointers; documentar lifetimes e evitar ownership ambíguo.

**Verificação proposta:** Compilar com warnings/sanitizers e testar iterator invalidation.

**Referências recomendadas:** [C++ working draft](https://eel.is/c++draft/)

## linguagens_java — Java, JVM e memory model

**Definição:** Java possui tipos nominais, GC e memory model que define sincronização e publicação.

**Mecanismo:** synchronized e volatile têm garantias específicas; generics normalmente usam erasure; virtual threads dependem da versão.

**Falhas comuns:** GC não fecha arquivo imediatamente; mutable object compartilhado ainda tem race; erasure afeta runtime types.

**Escolha:** Usar try-with-resources e estruturas concorrentes apropriadas; medir thread/heap.

**Verificação proposta:** Testar publicação, lock ordering, equals/hashCode e resource cleanup.

**Referências recomendadas:** [Java Language Specification](https://docs.oracle.com/javase/specs/)

## linguagens_csharp — C# e async no .NET

**Definição:** C# combina tipos nominais, generics, async/await e runtime gerenciado.

**Mecanismo:** Task representa operação; IDisposable/await using cuidam de recursos; CancellationToken é cooperativo.

**Falhas comuns:** async void fora de event handler complica erro; .Result pode bloquear e causar deadlock em contextos específicos.

**Escolha:** Propagar async/cancelamento e usar disposal explícito.

**Verificação proposta:** Testar exceção, cancellation, disposal e latência sem bloqueio síncrono.

**Referências recomendadas:** [C# documentation](https://learn.microsoft.com/en-us/dotnet/csharp/)


