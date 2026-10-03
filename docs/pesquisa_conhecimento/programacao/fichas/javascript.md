# Fichas avançadas: javascript

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

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

**Relações:** js_event-loop; js_combinadores; js_erros

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

**Relações:** distribuidos_timeouts; fronteira_structured-concurrency

**Exemplo local:** exemplos/padroes.mjs#abortableDelay

**Conferência pontual (ver conferencia-fontes-2.json):** node-abort

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

**Relações:** js_workers; fronteira_streaming-parsers

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

## js_promise-resolution — Resolução de Promise e thenables

**Definição:** Resolver Promise com thenable assimila seu estado; resolver com valor não thenable produz fulfillment. Resolução e fulfillment não são sinônimos.

**Mecanismo:** Thenables podem chamar callbacks várias vezes ou lançar; algoritmo normativo controla settlement. Referência cíclica direta rejeita com TypeError.

**Falhas comuns:** Implementar Promise caseira ou confiar em objeto com then benigno pode quebrar scheduling, erro e segurança da abstração.

**Escolha:** Aceitar valores PromiseLike só quando contrato pede; não implementar algoritmo de assimilação por intuição.

**Verificação proposta:** Testar then getter que lança, resolução duplicada e Promise resolvida com outra ainda pendente.

**Relações:** js_promises

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_async-boundary — await e fronteira de erro

**Definição:** await assimila valor awaitable e retoma continuação de forma assíncrona mesmo para valor já resolvido.

**Mecanismo:** return promessa em try não captura rejeição futura; return await promessa dentro de try permite catch/finally acompanhar settlement.

**Falhas comuns:** Remover todo return await por regra de estilo pode alterar tratamento de erro e lifetime de recurso.

**Escolha:** Escolher pela semântica de erro/cleanup e medir performance na versão do engine.

**Verificação proposta:** Comparar return p e return await p em try/catch com p rejeitada.

**Relações:** js_erros

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_floating-promises — Promises soltas

**Definição:** Uma operação assíncrona chamada sem await/return/handler pode continuar fora do escopo responsável.

**Mecanismo:** Handlers de array forEach não aguardam callback async; execução fire-and-forget precisa dono, erro e deadline próprios.

**Falhas comuns:** forEach(async...) seguido de resposta HTTP pode anunciar conclusão antes de persistir e perder rejeição.

**Escolha:** Usar for...of sequencial, map com combinador ou scheduler limitado; detached task só com contrato explícito.

**Verificação proposta:** Instrumentar término das tarefas e verificar que operação principal só conclui quando efeitos exigidos terminaram.

**Relações:** js_combinadores

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_task-group — Grupos com cancelamento e join

**Definição:** Falha em uma tarefa deve iniciar cancelamento de siblings quando o contrato exige término do grupo.

**Mecanismo:** Sinalizar abort não garante que filhos terminaram; grupo precisa aguardar settlements e decidir qual erro propaga.

**Falhas comuns:** Rejeitar imediatamente e soltar recursos compartilhados pode fazê-los ser usados por tarefa ainda ativa.

**Escolha:** Definir erro primário, exceções de cleanup e política de tarefas que ignoram cancelamento.

**Verificação proposta:** Fazer uma task falhar e outra limpar recurso lentamente; grupo não retorna antes do cleanup.

**Relações:** fronteira_structured-concurrency

**Exemplo local:** exemplos/engenharia.mjs#runGroup

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_async-context — Contexto assíncrono

**Definição:** Contexto de request pode ser propagado entre callbacks sem global mutável compartilhado.

**Mecanismo:** AsyncLocalStorage no Node mantém storage conforme criação da cadeia assíncrona; integrações/custom async boundaries exigem revisão.

**Falhas comuns:** Variável global requestId mistura requests; contexto não deve transportar secrets indiscriminadamente nem autorizar implicitamente.

**Escolha:** Usar contexto para correlation e principal validado, mantendo autorização explícita em fronteira de operação.

**Verificação proposta:** Executar requests intercalados e checar IDs corretos em logs após awaits e callbacks.

**Relações:** operacao_observability

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_cleanup-disposal — Cleanup e gerenciamento explícito de recursos

**Definição:** Recurso exige release em caminho normal, erro e cancelamento; GC não estabelece prazo para close.

**Mecanismo:** try/finally é base portátil; explicit resource management e símbolos de dispose dependem de versão/transpilação e host.

**Falhas comuns:** Assumir suporte a using porque o editor aceita sintaxe pode quebrar runtime; cleanup que lança pode ocultar causa.

**Escolha:** Documentar owner, operação idempotente de close e suporte instalado antes de adotar sintaxe nova.

**Verificação proposta:** Testar aquisição parcial, erro de operação, erro de cleanup e duplo dispose.

**Relações:** js_gc-retenção

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_semaphore — Semáforo assíncrono

**Definição:** Permits limitam número de atividades; acquire deve respeitar fila, cancelamento e release único.

**Mecanismo:** Cancelamento em fila remove waiter; cancelamento depois de grant exige entregar permit ou devolvê-lo sem vazamento.

**Falhas comuns:** Release em múltiplos caminhos aumenta capacidade ilegal; mutex local não protege processos diferentes.

**Escolha:** Usar release idempotente ou ownership único com finally, FIFO se fairness for requisito.

**Verificação proposta:** Testar abort antes do grant, abort na borda e active <= capacity em toda transição.

**Relações:** js_cancelamento

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_async-queue — Fila assíncrona limitada

**Definição:** Fila conecta producer/consumer sob capacidade e política de encerramento definida.

**Mecanismo:** push aguarda espaço; pop aguarda item; close pode drenar ou descartar por contrato. Abort deve remover apenas waiter correspondente.

**Falhas comuns:** Waiter abandonado consome futuro item/slot; fechar fila sem resolver esperas deixa processo pendurado.

**Escolha:** Escolher semântica de fechamento e implementar invariantes sobre itens/permits/waiters.

**Verificação proposta:** Testar produtor rápido, consumidor lento, close com waiters e cancelamento seletivo.

**Relações:** backend_node-streams

**Exemplo local:** exemplos/engenharia.mjs#AsyncQueue

**Conferência pontual (ver conferencia-fontes-2.json):** node-abort

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_circuit-breaker — Circuit breaker

**Definição:** Breaker interrompe chamadas quando dependência tem falhas conforme política e permite probe após intervalo.

**Mecanismo:** Estados closed/open/half-open têm transições; probe deve ser limitado e métricas distinguem recusa local de falha remota.

**Falhas comuns:** Breaker por request sem estado persistido no processo nunca aprende; rejeições de negócio não são falha técnica universal.

**Escolha:** Definir threshold/janela, classes de erro, clock e fallback; combinar com timeout/admission.

**Verificação proposta:** Testar falha repetida, tempo avançado, probes concorrentes e sucesso recuperando.

**Relações:** distribuidos_timeouts

**Exemplo local:** exemplos/engenharia.mjs#CircuitBreaker

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_retry-jitter — Backoff com jitter

**Definição:** Jitter distribui tentativas para evitar clientes sincronizados após falha comum.

**Mecanismo:** Full jitter sorteia atraso até limite exponencial; Retry-After e deadline podem reduzir próximas tentativas.

**Falhas comuns:** Retry recursivo infinito retém estado; incluir erro permanente ou request não idempotente cria dano.

**Escolha:** Injetar clock/RNG, limitar attempts/elapsed e distinguir retry seguro de efeito desconhecido.

**Verificação proposta:** Usar RNG determinístico e checar teto, deadline e nenhuma espera depois de abort.

**Relações:** distribuidos_timeouts

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_dedupe — Deduplicação e coalescing

**Definição:** Dedupe de efeitos durável difere de compartilhar Promise em andamento dentro de processo.

**Mecanismo:** Single-flight reduz trabalho paralelo da mesma chave, mas não armazena resultado após conclusão nem impede duplicata após restart.

**Falhas comuns:** Chave incompleta mistura tenants; cachear rejeição eternamente impede recuperação; tarefa reentrante pode esperar a si mesma.

**Escolha:** Definir chave, isolamento e scope; persistir dedupe quando há efeito de negócio.

**Verificação proposta:** Testar request concurrente, falha seguida de recuperação e chaves de usuários diferentes.

**Relações:** distribuidos_idempotencia

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_textdecoder — Decoder incremental e texto

**Definição:** Sequência UTF-8 pode atravessar chunks, exigindo estado do decoder.

**Mecanismo:** decode com stream true conserva bytes incompletos; flush final detecta EOF truncado se fatal habilitado.

**Falhas comuns:** Buffer.toString em cada chunk pode substituir caractere dividido e corromper conteúdo silenciosamente.

**Escolha:** Usar decoder stateful, limite de bytes e política explícita para input inválido.

**Verificação proposta:** Fragmentar em cada byte de acento/emoji e comparar resultado; rejeitar prefixo incompleto.

**Relações:** fronteira_streaming-parsers

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_framing — Framing binário length-prefixed

**Definição:** Protocolo precisa distinguir sequência de bytes de fronteiras de mensagens.

**Mecanismo:** Header determina tamanho; parser mantém offset/estado e impõe maxFrame antes de alocar/aguardar payload grande.

**Falhas comuns:** read pode trazer meia mensagem ou várias; comprimento hostil pode consumir memória ou prender espera.

**Escolha:** Especificar endian, tamanho máximo, zero-length, EOF parcial e política de erro permanente.

**Verificação proposta:** Dividir frame em todos pontos, concatenar frames e simular header acima do máximo.

**Relações:** redes_tcp

**Exemplo local:** exemplos/engenharia.mjs#FrameDecoder

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_event-emitter — EventEmitter e eventos

**Definição:** Node EventEmitter invoca listeners normalmente de forma síncrona na emissão; regras de error event são especiais.

**Mecanismo:** Callbacks async podem rejeitar fora da emissão; listener lifecycle e once/importação precisam contrato.

**Falhas comuns:** Pensar que emit aguarda Promise dos listeners resulta em ordem/erros incorretos; listener leak cresce memória.

**Escolha:** Usar APIs/documentação do host e considerar canal explícito de erro/await para eventos assíncronos.

**Verificação proposta:** Testar listener que lança, async que rejeita, listener removido durante emit e cleanup.

**Relações:** js_erros

**Conferência pontual (ver conferencia-fontes-2.json):** node-events

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_reentrancy — Reentrância síncrona

**Definição:** Callback externo pode reentrar na abstração antes que a primeira operação complete.

**Mecanismo:** Invocar callback enquanto invariant temporário está quebrado permite observar/modificar estado ilegal mesmo em uma thread.

**Falhas comuns:** Registrar Promise depois de chamar factory síncrona abre janela de segunda execução; getters podem executar código.

**Escolha:** Restabelecer invariant antes de chamar código externo ou agendar callback após registro.

**Verificação proposta:** Factory chama mesma API novamente; verificar que estado permanece legal e não há duplicação imprevista.

**Relações:** js_closures

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_esm-live — Bindings vivos e ciclos ESM

**Definição:** Import observa binding exportado, não cópia congelada do valor; inicialização segue grafo de módulos.

**Mecanismo:** Ciclo pode acessar export lexical ainda na TDZ; side effects top-level dependem de ordem de avaliação.

**Falhas comuns:** Refactor que cria ciclo pode lançar ReferenceError só em entrada específica; import dinâmico pode mover timing.

**Escolha:** Eliminar ciclo por módulo de contratos/dados ou inicialização explícita.

**Verificação proposta:** Executar cada entrypoint e alterar binding exportado para observar live update.

**Relações:** js_modulos

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_package-exports — Export maps e encapsulamento de pacote

**Definição:** package.json exports controla pontos públicos e condições de resolução conforme host.

**Mecanismo:** Ordem/condições e caminhos types/import/require precisam combinar com artefatos. Subpaths privados não são API prometida.

**Falhas comuns:** Pacote pode funcionar por deep import local e quebrar após export map; types podem resolver arquivo diferente de JS.

**Escolha:** Testar consumidores reais e declarar apenas exports presentes no pacote.

**Verificação proposta:** Empacotar, instalar em diretório vazio e checar subpaths públicos/privados.

**Relações:** ts_declarations

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_source-maps — Source maps e diagnóstico

**Definição:** Source map relaciona código transformado ao fonte para stacks/debugging.

**Mecanismo:** Pipeline de transforms deve compor maps; paths/fontes embutidas podem revelar código ou detalhes de ambiente.

**Falhas comuns:** Map incorreto aponta linha errada e gera falsa hipótese; publicar sourceContent pode expor informação sensível.

**Escolha:** Gerar e testar stack de erro conhecido; decidir acesso aos mapas por política operacional.

**Verificação proposta:** Provocar erro em função transformada e comparar localização; inspecionar artefato por secrets.

**Relações:** engenharia_debugging

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_sort-comparator — Contratos de comparator

**Definição:** Comparator define relação de ordenação e deve ser coerente com equivalência/ordem.

**Mecanismo:** Valores negativos/zero/positivos indicam precedência; NaN se comporta como zero no sort, podendo ocultar dado inválido.

**Falhas comuns:** Comparator booleano como a>b não oferece sinais apropriados; comparar por locale muda regra de negócio.

**Escolha:** Normalizar dados e comparar múltiplas chaves com desempate estável explícito.

**Verificação proposta:** Gerar triplas e testar transitividade; testar undefined/NaN e empate.

**Relações:** algoritmos_sort

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_dates-wire — Datas em wire contracts

**Definição:** Instante, data civil, hora local e duração são conceitos diferentes e precisam schemas próprios.

**Mecanismo:** ISO com offset identifica instante; YYYY-MM-DD pode identificar data civil sem timezone; duração de calendário não é milissegundo fixo.

**Falhas comuns:** Serializar aniversário como midnight UTC pode deslocar dia na UI; Date inválida pode lançar ao serializar.

**Escolha:** Nomear campos por semântica e validar faixa/offset; documentar timezone quando civil.

**Verificação proposta:** Trocar fuso do cliente e verificar que aniversário permanece no dia declarado.

**Relações:** js_intl-datas

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_regexp-state — Estado e flags de regex

**Definição:** Regex com g ou y mantém lastIndex entre chamadas de exec/test.

**Mecanismo:** Chamadas repetidas em mesmo objeto podem alternar match; y exige posição exata e g busca a partir do índice.

**Falhas comuns:** Validador que reutiliza regex global pode rejeitar input válido conforme chamada anterior.

**Escolha:** Não usar flags stateful em validação independente ou resetar explicitamente.

**Verificação proposta:** Chamar test duas vezes com mesma entrada e verificar resultado esperado sem dependência histórica.

**Relações:** js_regex

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_safe-object — Objetos de dados e accessors

**Definição:** Objeto arbitrário pode executar código ao ler campo, refletir chaves ou acessar protótipo.

**Mecanismo:** Getter, Proxy e toJSON alteram observações; JSON.parse sem reviver produz estrutura mais previsível, ainda requer validação.

**Falhas comuns:** Validar duas leituras de getter pode obter valores diferentes; spread pode disparar efeitos.

**Escolha:** Definir se boundary aceita apenas dados serializados ou objetos arbitrários; capturar valor uma vez quando apropriado.

**Verificação proposta:** Getter que alterna tipo, proxy ownKeys que lança e toJSON que muda conteúdo.

**Relações:** js_descritores

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_url-parsing — URLs e canonicalização

**Definição:** URL tem componentes e parsing definido por host/standard; string includes não verifica destino.

**Mecanismo:** Hostname, port, username, scheme e resolução relativa precisam análise; redirects podem mudar destino final.

**Falhas comuns:** good.example.attacker.test não é domínio permitido; userinfo pode enganar visualmente; encoding não autentica alvo.

**Escolha:** Usar parser URL e allowlist de componentes com destino final/rede controlados.

**Verificação proposta:** Testar subdomínio falso, userinfo, porta inesperada, relativo e redirect.

**Relações:** seguranca_ssrf

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_timer-budget — Timers e precisão de prazo

**Definição:** Timer agenda execução não antes de atraso nominal sob regras do host, sem garantia de deadline exato.

**Mecanismo:** Loop ocupado, clamping e carga atrasam callback; timeouts grandes podem ser normalizados pelo runtime.

**Falhas comuns:** Timeout passado a setTimeout não impõe CPU deadline se código bloqueia loop; wall clock pode mudar.

**Escolha:** Usar clock monotônico para elapsed e isolamento para CPU não cooperativa.

**Verificação proposta:** Bloquear loop e medir atraso; testar clock civil ajustado e valor fora da faixa do timer.

**Relações:** js_event-loop

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_node-fetch — Fetch Node e consumo de body

**Definição:** Fetch oferece resposta/status; HTTP erro não é necessariamente rejeição da Promise.

**Mecanismo:** Checar status, limites e content type; consumir/cancelar body conforme documentação evita retenção de conexão.

**Falhas comuns:** response.json em body gigantesco estoura memória; 404 pode ser tratado erroneamente como sucesso.

**Escolha:** Definir status esperados, deadline e parsing limitado por contrato.

**Verificação proposta:** Testar 404, erro de decode, timeout durante body e corpo nunca terminado.

**Relações:** js_cancelamento

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_unhandled — Rejeições não tratadas e processo

**Definição:** Política de unhandled rejection depende de host/versão/configuração; diagnóstico não substitui tratamento local.

**Mecanismo:** Listener global pode registrar falha fatal, mas continuar após estado desconhecido exige estratégia definida.

**Falhas comuns:** Engolir exceção global mantém serviço possivelmente corrompido; exit prematuro perde contexto.

**Escolha:** Tratar erros esperados na boundary; para defeito crítico registrar e encerrar com supervisão.

**Verificação proposta:** Criar rejeição solta em processo isolado e observar política/version flags.

**Relações:** backend_shutdown

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_buffer-pool — Pooling de buffers e ownership

**Definição:** Reusar buffer reduz allocations mas exige lifetime e exclusividade corretos.

**Mecanismo:** View pode compartilhar backing store; devolver buffer ao pool antes do consumidor terminar corrompe dados.

**Falhas comuns:** Subarray enviado a callback e buffer reutilizado produz resultado que muda posteriormente.

**Escolha:** Definir ownership ou copiar na fronteira; medir benefício real antes de adicionar pool.

**Verificação proposta:** Consumidor atrasado verifica que conteúdo não muda depois do envio.

**Relações:** js_buffers

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_constant-time — Timing e comparação de segredo

**Definição:** Tempo de execução pode depender de dados e expor informação em contexto criptográfico.

**Mecanismo:** API de comparação timing-safe possui pré-condições como comprimentos e representação; entorno ainda pode vazar por branches.

**Falhas comuns:** Comparação === de tokens não oferece garantia constant-time; tratar diferença de comprimento de modo ingênuo pode revelar.

**Escolha:** Usar primitives criptográficas revisadas e avaliar protocolo completo.

**Verificação proposta:** Testar tamanho inválido e falha sem retornar detalhes; não afirmar segurança a partir de microbenchmark.

**Relações:** seguranca_crypto

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

## js_resource-budget — Limites por bytes e custo

**Definição:** Limite de número de itens não limita necessariamente memória/CPU total.

**Mecanismo:** Cada item pode ter tamanho variável; budget precisa medir payload, parsing, filas e estruturas derivadas.

**Falhas comuns:** Fila de 100 itens com cada item de 100 MB continua perigosa; limite após parse grande é tarde.

**Escolha:** Aplicar limites por item, total e operação antes de trabalho caro; definir resposta de overload.

**Verificação proposta:** Gerar poucos itens enormes e muitos itens pequenos; verificar bound e limpeza após rejeição.

**Relações:** operacao_capacity

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [ECMAScript Language Specification](https://tc39.es/ecma262/)

