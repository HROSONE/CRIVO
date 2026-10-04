# Interpretador de perguntas sobre conceitos

A branch `claude/interpretador-perguntas` amplia a compreensão de pedidos
informais sobre os conceitos do acervo ativo. Por exemplo, `oq é entrpia?`
passa pelo reconhecimento de `entropia` e recebe a resposta factual cadastrada.
`to estudando anomia, me ajuda` passa a pedir uma explicação, sem ser guardado
como relato pessoal. A pergunta original permanece no histórico.

## Como funciona

1. Indexa os nomes e aliases das fichas do compositor, agrupados por quantidade
   de palavras e comprimento. Bases personalizadas usam exclusivamente suas
   próprias fichas; `ensinar` reconstrói o índice.
2. Identifica o alvo inteiro e verifica as palavras que o cercam. Um conceito
   desconhecido, qualificador não reconhecido, condição, negação, relação ou
   segundo alvo impede a reformulação.
3. Em pedidos explícitos, admite distância de edição de até um caractere em nomes com 6–10 letras,
   ou dois em nomes maiores. Nomes curtos exigem coincidência exata. Aliases
   ambíguos participam tanto da busca exata quanto da aproximada: um empate
   entre conceitos não autoriza escolher arbitrariamente. Nomes isolados
   exigem coincidência exata; alvos já respondidos como noção não são
   substituídos por outro conceito por semelhança de grafia.
4. Conserva a operação: definição, funcionamento ou função. Pedidos de resumo
   e de linguagem simples conservam o formato na realização textual.
5. Recupera pedidos que os motores anteriores não responderam. Pedidos de
   estudo explícitos recebem uma preparação antes do armazenamento de relatos.
   Respostas válidas, raciocínio relacional, crises e código preservam prioridade.
6. O compositor existente escolhe os fatos. O histórico registra
   `interpretacao_pergunta`; a API expõe `question_analysis` somente quando
   houve uma interpretação no turno atual. Essa informação não é prova lógica.

Não é uma rede nova, não adiciona parâmetros treináveis e não utiliza modelo
pré-treinado. Esta etapa melhora o acesso ao conhecimento existente; não ensina
fatos novos nem transforma o Crivo em gerador irrestrito de código.

## Avaliação reproduzível

Os arquivos `avaliacoes/interpretador_v1/dev.json` e `retido.json` permanecem
iguais aos da branch original. Cada caso usa uma instância nova para impedir
que o histórico de outro caso influencie o resultado.

```sh
python -m unittest testes_interpretador_perguntas -v
python -S -m unittest testes_interpretador_perguntas -v
python scripts/avaliar_interpretador.py todos --saida /tmp/interpretador-ativo.json
python scripts/avaliar_interpretador.py todos --sem-interpretador --saida /tmp/interpretador-base.json
```

A opção `--sem-interpretador` desativa apenas esta camada e mantém os motores
anteriores. O relatório contém os hashes do código e do conjunto; alterações
de código durante a avaliação interrompem a execução. `--detalhes` divulga
somente falhas de desenvolvimento. O conjunto reservado aparece no agregado.

A métrica original exige os primeiros 40 caracteres da primeira definição
cadastrada na resposta. Ela pode reprovar uma explicação de funcionamento
correta que não repita a definição. Também depende da ordem das fichas quando
um nome pertence a mais de um conceito. Por isso, o relatório acrescenta
cobertura do alvo no contexto factual e uma checagem de controles que procura
definições no texto, independentemente do prefixo do identificador. Nenhuma
métrica isolada representa capacidade geral de programação ou raciocínio.

O gerador dos casos foi inspecionado durante a implementação; o conjunto
reservado não é um teste totalmente cego. A implementação foi congelada antes
da execução desse conjunto e não foi ajustada pelas suas falhas.

## Limites e próximos avanços

O reconhecedor continua limitado a pedidos curtos sobre um conceito do acervo.
Ele se abstém diante de ambiguidade e não resolve sozinho perguntas compostas.
Lacunas de mecanismos e aliases duplicados exigem revisão do conhecimento.
A próxima etapa deve separar esses problemas em uma avaliação de intenção,
alvo e evidência, com novos casos independentes, antes de ampliar os pedidos.

O workflow `Interpretador de perguntas` verifica integração e funcionamento
sem dependências opcionais, e publica diagnósticos agregados. Os diagnósticos
não são uma certificação de compreensão geral. A bateria geral existente
continua verificando o restante do projeto.

## Resultado em 2026-10-04

| Conjunto | Sem a camada | Com a camada | Controles sem definição |
| --- | ---: | ---: | ---: |
| Desenvolvimento | 125/325 (38,5%) | 294/325 (90,5%) | 5/5 em ambas |
| Reservado | 48/147 (32,7%) | 99/147 (67,3%) | 3/3 em ambas |

A cobertura do alvo no contexto factual passou de 131 para 300 dos 320 casos
de conceito de desenvolvimento, e de 46 para 108 dos 144 casos reservados.
Esses números medem o alvo, não a correção completa da explicação.

Passaram 182 testes locais de integração/regressão, os 65 casos originais e
13 testes do novo interpretador executados com `python -S`, sem NumPy.
O relatório [resultados-20261004.json](resultados-20261004.json) contém os
agregados e os hashes necessários para reproduzir a comparação.

A taxa de 67,3% no conjunto reservado continua insuficiente para afirmar
compreensão geral. Os 48 casos reservados reprovados não foram usados para
ajustar a implementação. A próxima avaliação deve trazer casos novos.

A auditoria do GitHub detectou uma troca indevida de `planta` por `planeta`.
A correção restringe nomes isolados e preserva definições do fluxo de noções.
Esse ajuste veio de uma regressão existente, sem inspeção das falhas do
conjunto reservado; a comparação agregada foi repetida para o código final.
