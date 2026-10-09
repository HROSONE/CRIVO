# CI por escopo

O #121 foi integrado com os checks de roteamento, memória/continuidade,
conteúdo, programação e build aprovados. A matriz completa não foi declarada
aprovada: algumas execuções amplas ainda estavam em andamento no merge.

Este ajuste altera somente CI, sua verificação e documentação. Nenhum peso,
motor, memória ou entrada do conjunto congelado foi alterado.

## Validação em cada PR

- `configuracao-ci`: política de acionamento e actionlint 1.7.7 sobre todos os
  workflows. Edições só de CI passam por esse check, sem disparar todos os domínios.
- `roteamento-natural`: contratos de fontes/guardas e os 25 casos reais pelo
  adaptador HTTP, com os mesmos critérios de aprovação do #121.
- `compreensao-chat`: contratos essenciais de fatos, referentes, HTTP, gerador
  próprio, hipóteses e programação. A enumeração de todo o menu fica na suíte
  completa; ela não precisa bloquear cada edição do roteador.
- Suítes especializadas: continuam automáticas quando seus módulos, testes ou
  dados mudam. Alterar apenas `crivo.py`/`web_core.py` executa o workflow principal
  e a integração de memória/diálogo; não dispara Bíblia, laboratório ou treino.
- Contratos matemáticos de geração e linguagem profunda: automáticos quando
  seus arquivos neurais, pesos, testes ou requisitos mudam. A seleção compara
  a base e a cabeça do PR; a falha ao obter essa comparação falha o check de CI.

O workflow principal não tem filtro de caminhos no evento `pull_request`;
seus três checks centrais sempre reportam resultado. Os nomes anteriores foram
preservados. Para regras de proteção, os três checks centrais são os candidatos
estáveis; workflows filtrados não devem ser exigidos em todo PR, pois podem nem
ser criados quando seus arquivos não mudam. Este PR não altera regras de proteção.

## Bateria completa e execuções posteriores

Os quatro grupos em Python 3.8, 3.11 e 3.13 continuam disponíveis na execução
manual de `Testes Crivo` e rodam semanalmente, domingo às 03:00 UTC. Os contratos
matemáticos também rodam nesses eventos. As suítes especializadas conservam
seus acionamentos manuais existentes. Mudanças de pesos/acervo exigem avaliar
as baterias pertinentes antes de promover o candidato; os checks de conversa
não certificam um novo treinamento.

O push de merge na main mantém os cinco testes curtos de funcionamento e HTTP;
não repete a matriz completa. A configuração também é verificada. Execuções de
PR substituídas por um novo commit são canceladas por workflow e PR. Execuções
manuais e semanais não são canceladas por um push de PR. Branches, commits,
PRs e logs não são apagados. Os dois artefatos da matriz completa têm retenção
de sete dias; a retenção dos outros workflows foi preservada.

## Verificação

`python scripts/verificar_workflows_ci.py` confirma, entre outros contrastes,
que mudanças de núcleo acionam dois workflows, mudanças só de CI acionam um,
e que mudanças próprias de Bíblia, programação, memória, voz e redes continuam
chegando aos testes correspondentes. `actionlint` verifica sintaxe, expressões,
inputs das actions e dependências dos jobs em todos os arquivos de workflow.

## Checagem pública depois do merge

O endpoint `/api/chat` informou o commit `0edc6940bf9f9be72e0159b1b760f9c14ec2d845`.
O caso congelado “Oi, nunca usei você. O que você consegue fazer por mim?”
acionou `capacidades`, executor `conversa_assistente`, com guarda aprovada.
A paráfrase nova “Nunca usei você. O que consegue fazer?” ainda devolveu a
recusa antiga de negação. Na sessão nova “Meu primo Zaurélio gosta de kiwi e
não gosta de leite”, perguntar “O que meu primo gosta?” e corrigir a preferência
para manga não recuperou a pessoa; ambas as perguntas voltaram ao assunto
número primo. Esses resultados são falhas adicionais, fora dos 25 casos
congelados, e não foram contados como sucesso ou corrigidos neste PR de CI.
