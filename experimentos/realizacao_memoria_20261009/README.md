# Realizador próprio lendo a memória da sessão

O estado integrado pelo PR 118 já seleciona pessoas, relações e valores, mas
a rota neural anterior só recebia fatos do acervo. Esta etapa conecta o
Transformer causal próprio de 17,428 milhões de parâmetros ao estado existente.
Não acrescenta coletores, gramáticas ou outra camada de memória.

`realizacao_memoria.py` recebe somente as afirmações ativas selecionadas para
a consulta atual. Cada documento contém sujeito, relação e valor completos,
com a proveniência original do usuário. Fala atribuída conserva a atribuição.
Afirmações substituídas ou retiradas, hipóteses e consultas sem evidência não
são usadas como documentos. Nenhum documento ou pergunta é truncado para
caber no contexto: o limite produz recuo.

O mesmo realizador ancorado já existente recebe os documentos como tokens
no prompt. Usa o prefixo de duas palavras da fonte, decodificação restrita e
sua guarda original. A ligação de sessão acrescenta igualdade literal após
normalização Unicode e espaços: uma troca de pessoa, valor, atribuição ou
polaridade conserva a resposta estrutural. Todos os fatos de uma consulta
precisam passar; uma realização parcial nunca substitui o resumo inteiro.

O trace público `generation` distingue `leu_memoria`, `usada`, documentos,
proveniência, hashes dos prompts e motivos de recuo. O identificador semântico
`conversa:memoria_sessao` é conservado. A pergunta original do usuário chega
ao realizador, sem alterações do grafador intermediário.

## Medição

O protocolo foi registrado antes da implementação em `8426130`, incluindo
uma sonda offline de 16/20 fatos realizados pelo checkpoint atual. O conjunto
usado é o desenvolvimento prospectivo já congelado, SHA-256
`5998a9d490eb3095927e433eddce9764f38145d95ae85f929e3c6a6e4c5d5081`.

O candidato `d1d88b9` conserva **20/20 sessões no motor e 20/20 na API web**
com os padrões de produção. Das vinte consultas
com fatos selecionados, a rede leu vinte e escreveu dezesseis; em quatro a
guarda rejeitou a realização e a resposta da memória foi conservada. Portanto,
20/20 mede fidelidade do sistema com recuo, enquanto **16/20 mede utilização
neural bem-sucedida** nessa bateria. O avaliador importa os critérios originais
sem alterá-los e observa o trace; critérios e respostas esperadas nunca entram
no prompt.

A bateria anterior também conserva 20/20 no motor. `motor.json`, `web.json`
e `retencao.json` preservam as respostas reais, traces e hashes das fontes.

Os dez contratos do consumidor passaram, incluindo duas integrações com o
chat. O teste com o checkpoint real repete a mesma pergunta antes e depois
de uma correção de preferência: muda o documento, muda o hash do prompt e
muda o valor emitido. Vinte e cinco contratos puros de memória e realização
passaram em Python 3.8 sem dependências opcionais.

As 92 regressões de memória, escopos, raciocínio e hipóteses foram verificadas:
91 passaram na primeira execução; uma foi bloqueada ao abrir socket local
pelo sandbox. Esse mesmo caso passou em reexecução com acesso de rede,
incluindo HTTP 200 do endpoint real. Os dois logs foram preservados, sem
atribuir o bloqueio de infraestrutura a uma falha do motor.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_realizacao_memoria -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/realizacao_memoria_20261009/avaliar.py --exigir-meta --exigir-realizacao --saida /tmp/realizacao-motor.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/realizacao_memoria_20261009/avaliar.py --modo web --exigir-meta --exigir-realizacao --saida /tmp/realizacao-web.json
```

`usar_geracao=False` conserva o controle geral; `usar_geracao_sessao=False`
permite comparar a memória estruturada sem desligar outras rotas de geração.
Modelo indisponível ou recuo conserva a resposta anterior. Os pesos não foram
alterados; SHA-256 do checkpoint NumPy:
`7ac0f3be921e2221d7ca538d118077662cff4a9c0861f288db49edc360164ab8`.

## Limites

O seletor de fatos continua estruturado. Receber e realizar documentos da
sessão não demonstra raciocínio neural sobre relações, solução de tarefas
novas ou conversa livre. O conjunto já foi usado para desenvolvimento;
esta medição não é cega. A saída aceita nesta etapa é cópia literal ancorada,
com prefixo da fonte, e não uma paráfrase livre. O 16/20 não é comparável aos
testes antigos de diálogo generativo aberto. Nenhum peso experimental foi
promovido e nenhum modelo externo foi utilizado.
