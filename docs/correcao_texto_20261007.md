# Correção de conteúdo enviado — primeira versão

Branch `codex/correcao-texto`, sobre `codex/analise-conteudo` (PR #105).

## Uso

Envie `Corrija este texto: [conteúdo]` ou `Revise: [conteúdo]`. Dois-pontos,
quebra de linha ou aspas externas separam pedido e documento. Também é
possível enviar `Texto: [conteúdo]` e depois `Corrija isso`.

Exemplo:

> oi tudo bem eu nao vou hoje mas voces vai amanha

Proposta:

> Oi, tudo bem? Eu não vou hoje, mas vocês vão amanhã.

`Mostre as alterações` mostra o diff. `Qual a fonte?` retorna o original;
`Resuma isso` analisa o original, sem substituí-lo silenciosamente pela
proposta. Uma mudança de assunto encerra o documento. Não há armazenamento
de documentos no servidor, incorporação no acervo ou memória pessoal.

## Escopo

O módulo `correcao_texto.py` é determinístico e usa apenas a biblioteca padrão.
Corrige um conjunto explícito de grafias comuns, espaços junto à pontuação,
maiúsculas no início de frases e alguns pares locais de sujeito/verbo,
inclusive com negação. Propõe vírgulas antes de contrastes explícitos e em
expressões introdutórias; reconhece a saudação interrogativa no início de
parágrafo e um conjunto pequeno de perguntas. Não reescreve o estilo nem
completa ideias.

Preserva literalmente os padrões reconhecidos de números, datas, horários,
percentuais, endereços, identificadores com ponto, abreviaturas, código e
citações. A lista de padrões não cobre toda notação possível. Palavras com
maiúsculas fora do início de frase não passam pelo dicionário de grafias.
Isso reduz alterações de nomes e siglas; não reconhece todos os nomes próprios.

Termos ambíguos como `e/é`, `esta/está`, `nos/nós`, `a/há`, `tem/têm` e
`por que/porque` permanecem para revisão. O módulo não insere divisões
arbitrárias em longas sequências sem pontuação. A resposta apresenta uma
proposta e os limites; não promete correção gramatical completa nem equivalência
semântica garantida. Por exemplo, `Eu comprei dois casa.` permanece sem alteração.

Não há modelo externo, novos pesos ou treino do Transformer nesta mudança.
Um corretor abrangente exigirá dados anotados e avaliação semântica específica.

## Contrato e integração

A API usa o mecanismo `correcao_texto` e o campo `text_correction`, com:

- `original` e `corrigido`;
- `alteracoes`: offsets `inicio`/`fim` no original, `antes` e `depois`;
- `regras` aplicadas e `avisos` para revisão;
- `origem: conteudo_enviado` e `metodo: regras_conservadoras`.

Aplicar os trechos do diff, em ordem, ao original reconstrói exatamente a
proposta. Os offsets são índices de caracteres Python, como na análise;
clientes JavaScript devem converter para pontos de código quando houver
caracteres fora do plano básico. O diff pode agrupar mudanças em documentos
repetitivos para limitar custo computacional.

Entradas seguem o limite de 12.000 caracteres da mensagem inteira, incluindo
o cabeçalho. Histórico: dez mensagens e 24.000 caracteres somados; corpo HTTP:
256 KiB. A correção não exige o limite de 200 unidades da análise, mas um
pedido posterior de análise continua sujeito a esse limite.

A tarefa passa antes de acervo, código e aprendizado pessoal, após o protocolo
de crise existente. A geração factual não intervém. A interface identifica a
resposta como revisão a conferir, sem apresentar prova lógica.

## Verificação

Os testes específicos cobrem correção de texto sem pontuação, ambiguidades,
negações, preservação de dados, idempotência, reconstrução pelo diff, histórico,
isolamento, memória, limites HTTP e conteúdo que contém instruções/código.
O workflow de análise de conteúdo inclui correção com e sem NumPy. Resultados
após o ajuste que preserva o motor de código: 52 testes de correção, análise e
ecossistema passaram; oito testes HTTP chunked passaram novamente. Os 14
testes web também passaram na execução anterior. Memória, compreensão textual
e geração factual passaram na suíte mais ampla. Os 17 testes específicos de
correção passaram com e sem NumPy.

O navegador passou em conteúdo acima de 1.200 caracteres → correção → alterações
→ fonte → nova correção, conferindo a reconstrução pelo diff, as respostas e
o indicador de revisão. Não houve erros de JavaScript. Sintaxe Python,
`node --check` e `git diff --check` passaram. A validação foi local; esta entrega
não confirma a publicação do site nem substitui uma avaliação de qualidade
gramatical em textos inéditos anotados.
