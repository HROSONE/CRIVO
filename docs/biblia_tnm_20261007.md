# Acervo bíblico com referência à Tradução do Novo Mundo

33 fichas, 66 sínteses próprias e 22 páginas oficiais de referência. A base é a
Tradução do Novo Mundo da Bíblia Sagrada (Edição de Estudo), em português do
Brasil, consultada no [JW.ORG](https://www.jw.org/pt/biblioteca/biblia/biblia-de-estudo/livros/)
em 07/10/2026. O nome Jeová é usado conforme essa edição, com referência
específica a Salmos 83:18 e Êxodo 3:15 nas fichas correspondentes.

## Conteúdo e uso

O acervo inclui Bíblia/TNM, Jeová, criação, Gênesis, primeiros humanos, Éden,
casamento no relato, Noé, Abraão, Moisés, Dez Mandamentos, Salmo 23, Jesus,
João 3:16, vida eterna, Reino de Deus, oração, perdão, amor ao próximo,
bom samaritano, Marta e Maria, Sermão do Monte, pacificadores, amor aos
inimigos, ressurreição de Jesus, batismo, amor em 1 Coríntios, fruto do espírito,
confiança em Jeová, inspiração das Escrituras, morte em Eclesiastes e
esperança em Apocalipse.

Exemplos: `Quem é Jeová?`, `Qual é o nome de Deus?`, `Quem foi Moisés?`,
`Quem é Jesus?`, `O que é o Reino de Deus?`, `Explique João 3:16` ou
`Explique Sl83:18`. `Resuma isso` e `Qual a fonte?` usam o contexto comum
das fichas. As fontes devolvidas apontam aos capítulos usados, com o nome
da edição e o crédito da publicação.

O arquivo `conhecimento_biblia.json` é reproduzível pelo gerador
`python scripts/catalogos/biblia.py`. O currículo inclui o arquivo na mesma
validação local dos demais acervos; `conhecimento*.json` e `*.py` já estão no
pacote da API Vercel.

## Atribuição e referências

As fontes têm `tipo: institucional_religiosa`; cada fato tem
`natureza: religioso` e `referencia_biblica`. O validador exige que natureza e
tipo correspondam. As explicações identificam a TNM e incluem referências.
Não apresentam crenças como comprovação científica e não produzem prova
lógica apenas por citar a Bíblia.

O realizador de voz não reformula essas fichas: sua regra de definição podia
transformar a abertura «Na TNM» em uma frase com gênero e sujeito inadequados.
A geração ancorada continua disponível, mas uma saída religiosa só substitui
a composição quando preserva a moldura de atribuição e a referência exata,
além das guardas de fidelidade já existentes. Caso contrário, mantém os fatos
curados.

O resolvedor `referencias_biblicas.py` confere referências numericamente,
sem aproximar capítulos ou versículos. Aceita nomes de livros e um conjunto
pequeno de abreviaturas comuns. Só resolve referências exatas registradas nos
aliases ou em uma referência simples dos fatos. Uma síntese de intervalo
não autoriza inventar explicações independentes para cada versículo dele.
Consultas ausentes recebem uma recusa explícita e o índice oficial da TNM;
referências múltiplas de fichas diferentes pedem envio separado. Listas de
versículos não são reduzidas silenciosamente ao primeiro. Relatos pessoais
e pedidos de poema não são tratados como consultas só por citar um versículo;
o motor de código mantém prioridade.

## Limites e direitos

Este é um acervo introdutório, não a Bíblia inteira e não um especialista em
qualquer passagem. Não inclui cronologias controversas, autoria histórica
como consenso científico nem comparação de traduções. Para ler os versículos
na redação exata, use os links oficiais.

Os registros são sínteses próprias, sem transcrição de capítulos, versículos,
notas, tabelas ou imagens. A publicação é usada como referência, conforme
o registro `somente_referencia` e `reproducao_autorizada: false`, com os
[termos de uso](https://www.jw.org/pt/termos-de-uso/) documentados. Não há
indicação de endosso ou vínculo institucional.

66 vetores novos de fatos foram adicionados ao cache do codificador, mantendo
os vetores anteriores e os pesos do modelo. O cache agora cobre 5.413 textos
distintos. Não houve novo treinamento ou instalação de modelo externo.

## Validação

Os testes próprios conferem as 33 fichas, perguntas de pessoas e referências,
fonte correta após resumo, referências ausentes e compostas, abreviaturas,
separação de código/relato e preservação de atribuição/referência pelo gerador.
Os 12 testes próprios passaram com e sem NumPy. Após o ajuste do validador,
36 testes de conhecimento do mundo e ecossistema passaram. Catálogos ampliados,
codificador de sentido (inclusive cobertura do cache) e geração ancorada
passaram na suíte mais ampla. Sintaxe Python e `git diff --check` passaram.

O navegador passou em Jeová → resumo → fonte → referência abreviada →
referência ausente → Jesus, sem erros de JavaScript e com as respostas
renderizadas. A fonte conferida foi Salmos 83 e a referência ausente 83:19
não foi aproximada para 83:18. Há workflow específico incluindo execução sem
NumPy. A publicação remota do site depende da integração/deploy.
