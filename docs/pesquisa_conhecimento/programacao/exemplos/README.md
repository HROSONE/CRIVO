# Exemplos executáveis, tipos e limites

Requer Node >=18 e Python >=3.10 para ferramentas. Validação executada em Node 24.19.0 e TypeScript 5.9.3.

## Conteúdo
- `padroes.mjs`: 14 implementações iniciais; 27 testes de semântica, propriedades e falhas.
- `engenharia.mjs`: seis padrões principais (fila bounded, breaker, framing, CAS, task group, state machine); 31 testes.
- `modelagem.ts`: modelos de moeda, patch, estado e erro; oito testes do JS emitido.
- `contratos.ts` e `modelagem.types.ts`: fixtures positivas/negativas compiladas sob strict, noUncheckedIndexedAccess e exactOptionalPropertyTypes.
- `tsconfig.json`: host independente, ES2022 sem globals Node/DOM; não substitui tsconfig de aplicação.

## Comandos na raiz
```sh
node docs/pesquisa_conhecimento/programacao/exemplos/padroes.test.mjs
node docs/pesquisa_conhecimento/programacao/exemplos/engenharia.test.mjs
npm exec --cache /tmp/crivo-npm-cache --yes --package=typescript@5.9.3 -- tsc -p docs/pesquisa_conhecimento/programacao/exemplos/tsconfig.json
npm exec --cache /tmp/crivo-npm-cache --yes --package=typescript@5.9.3 -- tsc -p docs/pesquisa_conhecimento/programacao/exemplos/tsconfig.json --noEmit false --outDir /tmp/crivo-ts-output
node docs/pesquisa_conhecimento/programacao/exemplos/modelagem.runtime.mjs /tmp/crivo-ts-output/modelagem.js
python scripts/test_acervo_programacao.py
python scripts/acervo_programacao.py --validar
```
npm exec baixa compilador no cache temporário se necessário; não adiciona dependência/lock ao CRIVO. Em ambiente sem rede, usar tsc 5.9.3 previamente instalado. O output compilado fica fora do repositório. Fixtures negativas servem ao checker e não devem ser usadas como programa de produção.

## Contratos e limitações
Parser de objetos presume dados comuns; accessors/proxies hostis pedem fronteira específica. Map/LRU/SingleFlight são locais, não duráveis ou distribuídos, e quotas por bytes não estão implementadas. mapBounded aceita array finito e aguarda tarefas iniciadas, sem cancelar siblings automaticamente.

AsyncQueue tem capacidade de itens e limite de waiters por direção; quantidade não limita bytes. close rejeita writers pendentes e drena itens aceitos. Shift/splice privilegiam clareza, com custo linear possível; ring buffer/deque é extensão. Não há ack/retry durável.

CircuitBreaker usa falhas técnicas consecutivas, clock monotônico, cooldown e probe único. Classificador precisa ser puro/não lançar. Não cancela task, não possui state global, janela de taxa ou métricas. Epoch impede resultado antigo alterar geração nova.

FrameDecoder aceita uint32 big endian e rejeita header >maxFrame antes de alocar payload. Payload é copiado; erro de framing é terminal. maxFrame não limita total de frames retornados em chunk enorme, nem timeout de conexão. Decoder UTF-8 inicial acumula texto e não é consumidor ilimitado.

VersionedCell clona valores compatíveis com structuredClone e detecta conflito em uma célula local. Não implementa transação, replicação ou shared-memory CAS. Comparação/versionamento não autorizam recurso.

runGroup cancela cooperativamente e aguarda settlements. Task que ignora signal e nunca termina impede retorno; isolamento/deadline de CPU são externos. Todas tasks iniciam sem limite de concorrência; usar scheduler quando necessário.

State machine pressupõe eventos internos confiáveis e IDs únicos gerados pelo dono. Reutilizar ID permite resposta antiga parecer atual. Congelamento de wrapper não congela profundamente data.

Money admite BRL/USD, usa minor bigint e range de domínio ±10^18, com wire string. Não modela câmbio, arredondamento tributário ou moedas com escalas diversas. JsonValue é tipo aproximado e admite Number não finito sem validação. Patch e reducer não validam arbitrário JSON sozinhos.

Testes exercitam exemplos e ferramentas, não o CRIVO. Materiais públicos/didáticos não constituem holdout nem prova de geração independente.

