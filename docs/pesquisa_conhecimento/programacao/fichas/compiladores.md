# Fichas avançadas: compiladores

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## compiladores_compiler — Pipeline de compilação

**Definição:** Lexing, parsing, análise semântica, IR, otimização e codegen transformam fonte com obrigações de preservar semântica.

**Mecanismo:** AST representa estrutura, CFG fluxo; otimizações precisam hipóteses válidas sobre efeitos/aliasing/UB.

**Falhas comuns:** Regex não substitui parser geral; transpilar para JS não valida execução nem fornece APIs.

**Escolha:** Construir etapas pequenas com posições de fonte e diagnósticos testáveis.

**Verificação proposta:** Testar fonte inválida, precedence, scope e equivalência em programas pequenos.

**Referências recomendadas:** [LLVM Language Reference](https://llvm.org/docs/LangRef.html)

## compiladores_jit — JIT, especialização e deopt

**Definição:** JIT pode usar perfis para otimizar caminhos e desotimizar quando hipótese deixa de valer.

**Mecanismo:** Warmup, shapes e polimorfismo podem influenciar runtime, mas detalhes não são garantias ECMAScript.

**Falhas comuns:** Microbenchmark curto mede warmup; escrever código obscuro por hipótese V8 pode piorar manutenção.

**Escolha:** Otimizar por perfil de produção e versão do engine; não depender de detalhe como correção.

**Verificação proposta:** Medir warm/cold, GC, deopts e workload completo.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## compiladores_wasm — WebAssembly e fronteira host

**Definição:** Wasm define máquina e formato de instruções com validação; acesso externo ocorre por imports/exports.

**Mecanismo:** Memória linear e ABI exigem ownership, encoding e bounds; engine e propostas alteram capacidades.

**Falhas comuns:** Wasm não torna algoritmo rápido automaticamente nem evita bug de memória dentro da linear memory.

**Escolha:** Usar para reuso de toolchains e kernels adequados; medir custo de crossing/copias.

**Verificação proposta:** Testar entradas fora de faixa, memória crescente, import failure e equivalência com referência.

**Referências recomendadas:** [WebAssembly specifications](https://webassembly.github.io/spec/)


