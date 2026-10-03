# Fichas avançadas: javascript

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## js_valores-tipos — Valores e tipos ECMAScript

**Definição:** Undefined, Null, Boolean, String, Symbol, Number, BigInt e Object são tipos da linguagem. Funções são objetos chamáveis; typeof null retorna object por compatibilidade histórica.

**Mecanismo:** typeof não distingue arrays nem null; Array.isArray é apropriado para arrays. Valores primitivos são imutáveis, enquanto bindings e objetos têm mutabilidade distinta.

**Falhas comuns:** Não usar typeof como validador completo de payload nem supor que const congela objetos.

**Escolha:** Classificar entradas antes de operações; preferir igualdade estrita quando coerção não é parte explícita do contrato.

**Verificação proposta:** Verificar null, NaN, Infinity, array, objeto chamável e BigInt.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_coercao — Coerção e igualdade

**Definição:** Coerção transforma valores segundo algoritmos normativos, incluindo ToPrimitive e conversões numéricas/textuais.

**Mecanismo:** + pode concatenar ou somar; == usa igualdade abstrata; === distingue tipos. Object.is distingue zeros com sinal e considera NaN igual a si mesmo; Map usa SameValueZero.

**Falhas comuns:** [] == false é verdadeiro, mas ambos são objetos/valores de naturezas diferentes. Truthiness não valida significado de entrada.

**Escolha:** Normalizar e validar na fronteira; não depender de coincidências de coerção.

**Verificação proposta:** Prever [] + [], 0 == false, NaN === NaN, Object.is(-0,0) e chaves NaN em Map.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_number — Number, precisão e inteiros

**Definição:** Number usa ponto flutuante binário IEEE 754 de dupla precisão; nem toda fração decimal é representável exatamente.

**Mecanismo:** Inteiros são seguros até Number.MAX_SAFE_INTEGER; acumulações propagam arredondamento. Number.EPSILON não é tolerância universal: escala e erro da operação importam.

**Falhas comuns:** Não usar floats sem política explícita para dinheiro nem parseInt para validar texto inteiro completo.

**Escolha:** Para moeda usar unidades menores inteiras com faixa validada ou decimal especializado; para ciência definir tolerâncias absoluta e relativa.

**Verificação proposta:** Testar 0.1+0.2, limite de inteiro seguro, overflow, divisão por zero e tolerância escalada.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_bigint — BigInt

**Definição:** BigInt representa inteiros arbitrariamente grandes com limitações práticas de memória e tempo.

**Mecanismo:** Não mistura aritmética implicitamente com Number; divisão inteira trunca em direção a zero. JSON.stringify de BigInt exige estratégia de serialização.

**Falhas comuns:** Conversão para Number pode perder precisão; operações BigInt não garantem tempo constante criptográfico.

**Escolha:** Usar para identificadores numéricos grandes e aritmética inteira; transmitir como string com contrato de parse.

**Verificação proposta:** Testar negativos, divisão, serialização, conversão além de 2^53 e custo de operandos grandes.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_unicode-js — Strings, UTF-16 e Unicode

**Definição:** String é sequência de unidades de código UTF-16; comprimento não mede necessariamente pontos de código ou grafemas.

**Mecanismo:** for...of itera pontos de código, Intl.Segmenter pode segmentar grafemas; normalize aplica formas Unicode. localeCompare/Intl.Collator dependem de locale e opções.

**Falhas comuns:** slice pode separar par substituto; remover acentos indiscriminadamente pode colidir identificadores.

**Escolha:** Separar representação, comparação e exibição. Para identificadores definir normalização, tamanho e caracteres permitidos.

**Verificação proposta:** Testar emoji composto, acento combinante, scripts RTL e truncamento sem quebrar grafemas.

**Relações:** fronteira_streaming-parsers

**Exemplo local:** exemplos/padroes.mjs#decodeUtf8

**Referências recomendadas:** [Unicode Standard](https://www.unicode.org/versions/latest/)

## js_escopo-tdz — Escopo léxico e temporal dead zone

**Definição:** let e const são bindings de bloco; var possui escopo de função ou script conforme contexto.

**Mecanismo:** Bindings lexicais existem antes da inicialização, mas acessá-los na TDZ lança ReferenceError. typeof também falha para binding lexical na TDZ.

**Falhas comuns:** Hoisting não significa que todas as declarações são inicializadas com undefined; var em loop captura um binding compartilhado.

**Escolha:** Preferir const por padrão e let para reatribuição; declarar perto do primeiro uso.

**Verificação proposta:** Comparar closures em loops var/let, sombra de bindings e acesso antes da declaração.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_closures — Closures

**Definição:** Função conserva acesso ao ambiente léxico em que foi criada, mesmo após o retorno da função externa.

**Mecanismo:** Captura bindings, não snapshots automáticos de valores; cada chamada de uma factory pode criar ambiente separado.

**Falhas comuns:** Listeners e caches podem reter grandes objetos por closure; captura de estado antigo em UI provoca comportamento desatualizado.

**Escolha:** Usar encapsulamento e funções puras; documentar lifetime e limpeza de callbacks.

**Verificação proposta:** Criar dois contadores independentes e analisar retenção por listeners removidos.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_this — this e funções arrow

**Definição:** this é determinado por modo de chamada nas funções ordinárias; arrow captura this lexical.

**Mecanismo:** Método extraído perde receptor; bind fixa receptor e argumentos iniciais. strict mode mantém undefined em chamadas sem receptor.

**Falhas comuns:** Arrow não é substituto universal de método nem pode ser usada como construtor; call/apply não mudam seu this lexical.

**Escolha:** Escolher arrow para callback lexical e função ordinária para comportamento dependente do receptor.

**Verificação proposta:** Comparar obj.metodo(), referência extraída, bind e arrow dentro de método.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_prototipos — Protótipos e classes

**Definição:** Objetos podem delegar lookup de propriedades pela cadeia de protótipos. class oferece sintaxe e semânticas adicionais sobre objetos e funções.

**Mecanismo:** Propriedades próprias e herdadas diferem; Object.hasOwn evita depender de método possivelmente sobrescrito. Campos privados # têm verificações de marca.

**Falhas comuns:** Alterar protótipos globais quebra terceiros; class não fornece imutabilidade ou tipagem nominal geral.

**Escolha:** Preferir composição quando hierarquia não modela substituição; encapsular invariantes em métodos.

**Verificação proposta:** Testar propriedade própria, shadowing, método herdado e acesso privado com receptor errado.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_descritores — Descritores e reflexão

**Definição:** Propriedades de dados possuem value/writable; acessoras possuem get/set; enumerable/configurable controlam operações.

**Mecanismo:** Object.keys não inclui símbolos nem propriedades não enumeráveis. Reflect.ownKeys inclui ambas; getters podem executar efeitos durante acesso.

**Falhas comuns:** Spread ou Object.assign pode disparar getters; cópia rasa não preserva todos os descritores e protótipos.

**Escolha:** Usar APIs de reflexão conforme contrato; não tratar objeto desconhecido como dado puro.

**Verificação proposta:** Comparar enumeração, getter com efeito, readonly por descritor e símbolo próprio.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_imutabilidade — Imutabilidade e cópia

**Definição:** const impede reatribuição do binding; Object.freeze limita mudanças no próprio objeto, não congela profundamente o grafo.

**Mecanismo:** Spread e slice copiam estrutura superficial. structuredClone suporta vários tipos e ciclos, mas não clona funções nem todos objetos de host.

**Falhas comuns:** JSON roundtrip perde tipos, undefined e outras informações; freeze superficial não protege objetos internos.

**Escolha:** Escolher imutabilidade por design, cópias estruturais ou clone com tipos suportados, conforme custo.

**Verificação proposta:** Testar alias interno, ciclo, Date, Map e transferência de ArrayBuffer.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## js_arrays — Arrays, buracos e ordenação

**Definição:** Arrays são objetos com regras especiais de índices e length; buraco difere de elemento undefined.

**Mecanismo:** map e algumas iterações pulam buracos; spread pode materializá-los como undefined. sort modifica original e compara strings por padrão.

**Falhas comuns:** sort numérico sem comparador ordena incorretamente; comparator inconsistente viola contrato; delete cria buraco.

**Escolha:** Usar arrays densos quando possível; comparador total coerente; toSorted quando runtime suportar ou copiar antes de sort.

**Verificação proposta:** Testar [2,10,1], arrays esparsos, estabilidade e preservação da entrada.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_map-set — Map, Set e weak collections

**Definição:** Map armazena pares chave/valor; Set mantém valores únicos; weak collections não impedem coleta de chaves elegíveis.

**Mecanismo:** Identidade de objeto define igualdade de chaves. Ordem de inserção é preservada em Map/Set; WeakMap não oferece enumeração de chaves.

**Falhas comuns:** Complexidade específica de hash table não é garantia universal de implementação; WeakMap não é cache TTL observável.

**Escolha:** Usar Map para chaves arbitrárias e WeakMap para metadados ligados ao lifetime do objeto.

**Verificação proposta:** Testar objetos estruturalmente iguais mas distintos, NaN, ordem e delete/reinsert.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_iteradores — Iteradores e generators

**Definição:** Iterables expõem Symbol.iterator; iterator produz objetos com value e done. Generator pode suspender e retomar execução.

**Mecanismo:** for...of consome valores; for...in enumera chaves enumeráveis inclusive herdadas. Iterator closing chama return em situações previstas.

**Falhas comuns:** Não confundir iterável com array nem ignorar limpeza de recursos em generator abandonado.

**Escolha:** Usar lazy traversal para fontes grandes; try/finally para recursos com lifetime explícito.

**Verificação proposta:** Interromper loop cedo e observar finally; testar iterable de uso único.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_async-iteracao — Iteração assíncrona

**Definição:** AsyncIterable produz valores por operações awaitable; for await...of também aceita iterables síncronos.

**Mecanismo:** Permite consumir streams incrementalmente; cancelamento e fechamento devem acompanhar o consumidor. Await sequencial limita throughput.

**Falhas comuns:** Acumular todos os chunks elimina benefício de streaming; abandono sem cleanup retém recursos.

**Escolha:** Usar streaming com limites, backpressure e política de erro; paralelizar somente com bound explícito.

**Verificação proposta:** Testar quebra antecipada, erro no produtor, cancelamento e consumidor lento.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_promises — Promises e propagação

**Definição:** Promise representa estado pending, fulfilled ou rejected; executor roda sincronamente e handlers rodam como jobs.

**Mecanismo:** then retorna nova Promise; retorno encadeia resolução e throw propaga rejeição. async sempre retorna Promise e await suspende continuação.

**Falhas comuns:** new Promise(async...) pode deixar rejeição sem tratamento e Promise externa pendente; callback sem return quebra encadeamento.

**Escolha:** Preferir composição direta e async/await; tratar rejeição na fronteira responsável.

**Verificação proposta:** Prever logs antes/depois do executor, cadeia com throw e retorno de thenable.

**Relações:** js_event-loop, js_combinadores, js_erros

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_combinadores — Combinadores de Promise

**Definição:** all reúne resultados em ordem de entrada e rejeita quando uma falha; allSettled registra todas; race adota primeiro settlement; any primeiro fulfillment.

**Mecanismo:** As operações iniciadas continuam após rejeição de all ou vitória de race, a menos que APIs suportem cancelamento explícito.

**Falhas comuns:** Promise.race com timeout não cancela requisição nem limpa recursos por si só.

**Escolha:** Escolher política por semântica do conjunto; cancelar tarefas perdedoras com AbortController quando suportado.

**Verificação proposta:** Testar conjunto vazio, rejeição precoce, resultados fora de ordem e tarefas ainda ativas.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_event-loop — Event loop e microtasks

**Definição:** ECMAScript define jobs; hosts organizam tasks, microtasks, renderização e I/O com regras próprias.

**Mecanismo:** Após tarefa do navegador, checkpoints processam microtasks; Node possui fases e fila nextTick própria. Timers indicam atraso mínimo, não prazo garantido.

**Falhas comuns:** Microtasks recursivas podem impedir render/I/O; ordem detalhada entre timers depende do contexto/runtime.

**Escolha:** Separar semântica da linguagem de scheduling do host; medir atraso do loop e ceder execução em trabalho longo.

**Verificação proposta:** Testar script, Promise, queueMicrotask e timer; repetir em navegador e Node sem supor equivalência universal.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## js_cancelamento — AbortSignal e cancelamento cooperativo

**Definição:** AbortController sinaliza interrupção; operação precisa observar signal para realmente interromper trabalho.

**Mecanismo:** Propagar sinal desde request até fetch, filas e tarefas. Verificar estado já abortado e remover listeners ao encerrar.

**Falhas comuns:** Abortar depois de side effect remoto não desfaz transação; cancelamento não garante rollback.

**Escolha:** Combinar deadline, limpeza em finally e idempotência para operações com efeitos.

**Verificação proposta:** Testar abort antes, durante e após resposta, e listener count após término.

**Relações:** distribuidos_timeouts, fronteira_structured-concurrency

**Exemplo local:** exemplos/padroes.mjs#abortableDelay

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## js_erros — Erros e causalidade

**Definição:** Erro representa falha com contexto; try/catch síncrono não captura rejeição futura sem await ou cadeia apropriada.

**Mecanismo:** Error.cause conserva causa; categorias de erro separam validação, indisponibilidade, conflito e defeito interno.

**Falhas comuns:** Engolir exceção produz sucesso falso; retornar stack ao cliente expõe detalhes e secrets.

**Escolha:** Falhar com contrato claro, preservar causa e registrar contexto redigido; não tratar todo erro como retentável.

**Verificação proposta:** Testar erro síncrono, rejeição, finally e serialização pública sem stack.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_modulos — ESM, CommonJS e resolução

**Definição:** ESM possui imports estáticos e bindings vivos; CommonJS usa require/module.exports em Node.

**Mecanismo:** Resolução depende de package.json type/exports/imports, extensão e host. Imports cíclicos podem observar bindings não inicializados.

**Falhas comuns:** Não supor equivalência entre default/named exports em interoperabilidade; bundler pode esconder erro de runtime.

**Escolha:** Definir estratégia ESM/CJS, target, resolução e export map; testar pacote compilado no consumidor real.

**Verificação proposta:** Testar ciclo, import dinâmico, export condicional e execução do artefato fora do source tree.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## js_json — JSON e dados não confiáveis

**Definição:** JSON representa dados limitados: números, strings, booleanos, null, arrays e objetos.

**Mecanismo:** JSON.parse produz valores sem garantir shape ou limites. Reviver permite conversões, não substitui validação. Precisão numérica pode se perder no parse.

**Falhas comuns:** Nunca usar eval para JSON; payload pequeno em bytes pode induzir trabalho caro por profundidade/estrutura.

**Escolha:** Impor tamanho, profundidade e schema; números grandes como strings com regras explícitas.

**Verificação proposta:** Testar campos desconhecidos, null, números fora de faixa, duplicidade de chaves e profundidade excessiva.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_regex — Expressões regulares

**Definição:** Regex reconhece padrões com flags e semântica específica de JS; estado lastIndex importa com g/y.

**Mecanismo:** Unicode mode altera parsing e matching; motores podem ter backtracking exponencial em certos padrões.

**Falhas comuns:** Padrão (a+)+ em texto hostil pode causar ReDoS; escape correto depende do contexto e suporte da API.

**Escolha:** Preferir padrões simples, limites de entrada e parsers para gramáticas complexas; medir casos adversariais.

**Verificação proposta:** Testar não-match longo, flags g/y reutilizadas, surrogate pairs e limites de comprimento.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_intl-datas — Datas e internacionalização

**Definição:** Date representa instante em milissegundos relativo ao epoch, com APIs locais/UTC; timezone e calendário são dimensões diferentes.

**Mecanismo:** Intl.DateTimeFormat/NumberFormat formatam conforme locale/opções. Mudança de horário local torna algumas horas ambíguas ou inexistentes.

**Falhas comuns:** Somar 24h não significa próximo dia civil em todo fuso; parsing de data sem contrato é ambíguo.

**Escolha:** Persistir instantes e timezone quando necessário; usar biblioteca/Temporal com suporte verificado para calendário civil.

**Verificação proposta:** Testar mudança de DST, leap day, data inválida e locale com separadores diferentes.

**Referências recomendadas:** [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)

## js_buffers — TypedArray, Buffer e transferência

**Definição:** TypedArray oferece visão tipada sobre memória de ArrayBuffer; Buffer é API Node para bytes.

**Mecanismo:** subarray compartilha memória; cópia exige operação apropriada. DataView controla endian. Transferência pode destacar buffer no emissor.

**Falhas comuns:** Tratar bytes como texto corrompe dados; views de offsets errados podem ler região indevida.

**Escolha:** Definir encoding, endian, ownership do buffer e política de cópia/transferência.

**Verificação proposta:** Testar UTF-8 dividido entre chunks, alias de views e buffer destacado após transferência.

**Relações:** js_workers, fronteira_streaming-parsers

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## js_proxy — Proxy e metaprogramação

**Definição:** Proxy intercepta operações internas por traps e precisa respeitar invariantes do objeto alvo.

**Mecanismo:** Reflect facilita encaminhamento padrão; objetos com slots internos podem falhar com receptor proxy inadequado.

**Falhas comuns:** Proxy não é fronteira de segurança nem invisível em performance/identidade; traps recursivas podem estourar stack.

**Escolha:** Usar com contrato pequeno e testes de reflexão, identidade e descritores.

**Verificação proposta:** Testar alvo frozen, getter com receiver, Map proxificado e invariantes de ownKeys.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_gc-retenção — Garbage collection e vazamentos

**Definição:** GC recupera memória inalcançável conforme implementação; alcançável não significa útil ao negócio.

**Mecanismo:** Timers, listeners, closures e caches sem bound mantêm referências. Heap snapshots mostram caminhos de retenção; crescimento temporário não prova leak.

**Falhas comuns:** FinalizationRegistry/WeakRef têm timing não determinístico e não garantem cleanup de recursos críticos.

**Escolha:** Fechar recursos explicitamente, limitar caches, medir heap após ciclos de carga e períodos de coleta.

**Verificação proposta:** Repetir monta/desmonta, comparar dominators e verificar listener/timer cleanup.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_workers — Workers e paralelismo JS

**Definição:** Workers executam trabalho em agentes separados, com mensagens, clonagem/transferência e recursos específicos do host.

**Mecanismo:** Worker threads Node podem ajudar CPU-bound; I/O assíncrono geralmente não exige worker dedicado. Pool evita custo por tarefa.

**Falhas comuns:** Worker não remove limite global de CPU/memória; serialização de payload pode dominar custo.

**Escolha:** Medir custo de comunicação e usar pools limitados; não compartilhar estado sem protocolo.

**Verificação proposta:** Testar crash, task timeout, ordem de respostas e fila saturada.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## js_atomics — SharedArrayBuffer e Atomics

**Definição:** Memória compartilhada requer operações e protocolo de sincronização apropriados; Atomics suporta operações atômicas em views permitidas.

**Mecanismo:** Flags e dados precisam de ordem coerente; Atomics.wait tem restrições de agente/host. Navegador exige condições de isolamento para memória compartilhada.

**Falhas comuns:** Operação atômica isolada não preserva invariantes de múltiplos campos; spin loop ocupa core e pode impedir progresso.

**Escolha:** Preferir mensagens; usar compartilhamento só com justificativa e modelo de correção.

**Verificação proposta:** Testar handoff, estados impossíveis, múltiplos produtores e limites da fila.

**Referências recomendadas:** [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_seguranca-objetos — Prototype pollution

**Definição:** Mesclar chaves controladas pelo usuário em objetos/protótipos pode alterar comportamento de acessos futuros.

**Mecanismo:** __proto__, constructor e prototype exigem atenção em caminhos de merge; Object.create(null) remove cadeia, mas não resolve toda lógica de merge.

**Falhas comuns:** Object.hasOwn ajuda em lookup, não torna todo deep merge seguro; blacklist parcial pode ser contornada por caminhos aninhados.

**Escolha:** Schemas allowlist, mapas apropriados e bibliotecas revisadas; impedir escrita em protótipos.

**Verificação proposta:** Testar chaves especiais aninhadas e confirmar que Object.prototype continua intacto.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)


