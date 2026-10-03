# Exemplos executáveis e fixtures de tipos

Node >=18; executar a partir da raiz:
```sh
node --test docs/pesquisa_conhecimento/programacao/exemplos/padroes.test.mjs
tsc -p docs/pesquisa_conhecimento/programacao/exemplos/tsconfig.json
```
O comando tsc requer TypeScript instalado no ambiente; este acervo não adiciona dependência à aplicação. Registrar versão e resultado; ausência de tsc deve ser declarada como check pendente.

14 implementações didáticas e 27 testes cobrem busca binária, parsing, agrupamento, iterator cleanup, topological sort, LRU, concorrência limitada, cancelamento, single-flight, Unicode, números e closures. Fixtures TS cobrem Results, brands, indexed access, exhaustiveness, conditional types e configurações estritas.

Limitações: parser assume objetos de dados comuns (não proxies/accessors hostis); Map/LRU e SingleFlight são locais ao processo, não duráveis, distribuídos ou quotas por bytes. mapBounded aceita array finito e aguarda tarefas iniciadas, sem cancelar automaticamente siblings. Delay depende de timers do host. decodeUtf8 acumula texto para demonstrar decode incremental, não é consumidor de tamanho ilimitado. Soma compensada possui limites numéricos. Tasks recursivas com a mesma chave de SingleFlight podem criar dependência circular. Comparator/domínio de lowerBound são números ordenados sem NaN. Nenhum exemplo implementa autorização ou isolamento de código não confiável.

Testes verificam propriedades e falhas observáveis dos exemplos; não são avaliação do CRIVO. Exemplos e testes são públicos/didáticos e não constituem holdout independente.

