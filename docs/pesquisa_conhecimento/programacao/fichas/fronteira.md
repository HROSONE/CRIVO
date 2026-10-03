# Fichas avançadas: fronteira

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## fronteira_gpu — GPU e paralelismo de dados

**Definição:** GPU favorece muitos trabalhos de dados com acesso e sincronização compatíveis com arquitetura.

**Mecanismo:** Transfers, dispatch, workgroups e memória determinam custo; WebGPU possui validation e limites do dispositivo.

**Falhas comuns:** Kernel rápido pode perder para CPU após transferências; divergência e acesso irregular reduzem eficiência.

**Escolha:** Usar para dados grandes e trabalho paralelo medido; verificar suporte e fallback.

**Verificação proposta:** Comparar pipeline completo CPU/GPU e validar erro numérico/bounds.

**Referências recomendadas:** [WebGPU specification](https://www.w3.org/TR/webgpu/)

## fronteira_incremental — Computação incremental

**Definição:** Reutiliza resultados quando entradas mudam, rastreando dependências e invalidação.

**Mecanismo:** Build systems, spreadsheets e reatividade usam grafos; cache key deve incluir tudo que influencia saída.

**Falhas comuns:** Dependência oculta gera stale output; invalidar tudo elimina ganho.

**Escolha:** Tornar entradas/efeitos explícitos e verificar equivalência com recomputação completa.

**Verificação proposta:** Mutar cada dependência isoladamente e comparar incremental versus clean build.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## fronteira_crdt — CRDTs e convergência

**Definição:** CRDTs projetam operações/estado para convergir sob condições de merge e entrega específicas.

**Mecanismo:** State-based usa merge com propriedades algébricas; operation-based possui requisitos de transporte/causalidade.

**Falhas comuns:** Convergência não garante todo invariante de negócio; tombstones e metadados têm custos.

**Escolha:** Usar colaboração/offline quando resolução de conflitos do tipo é aceitável.

**Verificação proposta:** Testar operações reordenadas, duplicadas, concorrentes e replica reentrando.

**Pré-requisitos:** distribuidos_consistency

**Relações:** web_browser-storage, fronteira_incremental

**Referências recomendadas:** [Jepsen consistency models](https://jepsen.io/consistency)

## fronteira_agent-tools — Ferramentas e agentes de programação

**Definição:** Agente pode ler, editar e executar ferramentas para verificar artefatos sob autorização.

**Mecanismo:** Ferramentas devem ter schema, escopo, deadlines e evidência; arquivos/saídas externas são dados não confiáveis.

**Falhas comuns:** Texto de repo/URL pode tentar instruir agente a exfiltrar segredo; execução automática sem limites causa dano.

**Escolha:** Isolar execução e restringir capabilities ao necessário; registrar diffs e resultados.

**Verificação proposta:** Testar conteúdo malicioso em documentação e confirmar que não vira instrução privilegiada.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## fronteira_ai-retrieval — Recuperação híbrida e RAG

**Definição:** Recuperação seleciona unidades relevantes por índice lexical/vetorial e relações; geração usa contexto selecionado.

**Mecanismo:** Chunking semântico, metadados e reranking melhoram busca; citar unidade/fontes mantém rastreabilidade.

**Falhas comuns:** Embedding semelhante não prova fato; contexto excessivo pode misturar versões e consumir budget.

**Escolha:** Avaliar recall e precisão com consultas novas e registrar versão/proveniência.

**Verificação proposta:** Testar paráfrase, linguagem explícita e pergunta sem resposta no corpus.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## fronteira_effect-systems — Efeitos, pureza e composição

**Definição:** Efeito descreve interação além do retorno: I/O, estado, exceção ou concorrência.

**Mecanismo:** Linguagens/ferramentas podem rastrear efeitos com mecanismos diferentes; TypeScript não possui sistema geral sound de efeitos.

**Falhas comuns:** Tipo Promise não informa todos efeitos; função nomeada pure pode tocar global.

**Escolha:** Separar núcleo puro e adapters, documentar efeitos e testar isolamento.

**Verificação proposta:** Chamar função repetidamente e observar estado/recursos; revisar dependências ocultas.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## fronteira_linear-types — Tipos lineares e recursos

**Definição:** Tipos lineares/afins restringem número de usos para controlar recursos e ownership.

**Mecanismo:** Modelos diferem: linear exige uso, affine limita a no máximo uma vez; Rust não é simplesmente cálculo linear puro.

**Falhas comuns:** Readonly ou brand TS não impõe consumo único; cast/alias quebra disciplina.

**Escolha:** Aplicar disciplina de lifetime onde recurso exige release único; usar linguagem/framework adequado.

**Verificação proposta:** Testar duplo uso/close e transferência de ownership.

**Referências recomendadas:** [The Rust Programming Language](https://doc.rust-lang.org/book/)

## fronteira_structured-concurrency — Concorrência estruturada

**Definição:** Lifetime de tarefas fica associado a escopo para facilitar cancelamento, espera e propagação de erro.

**Mecanismo:** Parent scope espera ou cancela filhos; APIs variam por linguagem; Promise.all sozinho não cancela siblings.

**Falhas comuns:** Task órfã pode continuar após request e consumir recursos; cancelamento precisa cooperação.

**Escolha:** Modelar grupo de tarefas com deadline comum e política de falha.

**Verificação proposta:** Testar parent cancelado, child falha e confirmação de término de todos filhos.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/)

## fronteira_incremental-types — Compiladores e linguagem tooling

**Definição:** Language server, AST e incremental analysis oferecem refactors/navegação com entendimento estrutural.

**Mecanismo:** Mudanças dependem de grafo de arquivos/tipos; posições de source e snapshots precisam consistência.

**Falhas comuns:** Regex refactor altera strings/comments ou bindings errados; stale AST aplica edição no lugar incorreto.

**Escolha:** Preferir ferramentas semânticas e confirmar diff/typecheck após codemod.

**Verificação proposta:** Testar shadowing, comentário, import alias e atualização concorrente de arquivo.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## fronteira_streaming-parsers — Parsers incrementais e bounded memory

**Definição:** Parser incremental conserva estado entre chunks para reconhecer mensagens sem exigir toda entrada em memória.

**Mecanismo:** Decoder mantém sequência UTF-8 incompleta; estado de framing registra bytes restantes; limites de comprimento/profundidade impedem crescimento ilimitado.

**Falhas comuns:** Assumir chunk como mensagem quebra com fragmentação; validar tamanho só após allocation permite exaustão; EOF parcial deve ser erro explícito.

**Escolha:** Usar para protocolos, logs e arquivos grandes; definir política de erro/ressincronização e invariant de memória.

**Verificação proposta:** Dividir a mesma entrada em todas posições possíveis e comparar parse com leitura completa; testar EOF e tamanho declarado hostil.

**Referências recomendadas:** [Node.js API documentation](https://nodejs.org/api/); [Unicode Standard](https://www.unicode.org/versions/latest/)


