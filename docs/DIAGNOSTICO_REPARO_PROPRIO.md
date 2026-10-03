# Diagnóstico e reparo local por contratos

Para a integração ativa na conversa, consulte [Motor de programação no chat](MOTOR_PROGRAMACAO_CHAT.md).

O laboratório agora recebe código e exemplos de entrada/saída, reproduz a falha,
mostra estados e efeitos da execução e testa edições locais na árvore sintática.
Por exemplo, uma soma de array sem incrementar `i` esgota o orçamento; inserir
`i += 1;` no corpo do `while` satisfaz os exemplos do contrato.

A posição `caminho_ast` identifica a edição na árvore da fonte original. Os
fragmentos `antes` e `depois` permitem revisar a mudança. São posições de AST,
não linhas da fonte nem um diagnóstico comprovado da intenção do autor.
`primeiro_exemplo_falho` identifica o primeiro exemplo que falhou; não promete
identificar a primeira operação semanticamente errada de um programa arbitrário.

## O que foi implementado

- Serialização da AST do subconjunto próprio, preservando precedência, strings,
  acesso a dados, atribuições e controle de fluxo.
- Troca de operadores, constantes, métodos e subexpressões. Nomes vêm do código;
  campos adicionais vêm das entradas de desenvolvimento.
- Remoção de statements e inserção de incremento/decremento em laços. São edições
  estruturais locais; não há catálogo de programas completos para substituir a função.
- Execução rastreada que preserva estados e efeitos anteriores a uma falha,
  inclusive em loops que excedem o orçamento. Nenhum `eval` ou acesso a APIs do host.
- Rede própria de **960 parâmetros**, inicializados aleatoriamente, que aprende
  a ordenar as edições. São 58 atributos de edição/contexto e 16 unidades `tanh`.
- Auditoria opcional da rede de efeitos V3: executa a mesma fonte nos modos exato
  e neural e aponta o primeiro efeito divergente. Isso mede erro do executor neural,
  separado de erro no comportamento pretendido do programa.

O parser, a semântica, a geração de edições e os atributos são programados à mão.
A rede aprende apenas o ranking. A correção final sempre passa pelo executor exato
com todos os exemplos fornecidos. Não é um modelo geral de raciocínio sobre código.

## Avaliação fixada antes do treino

`dados/estados/benchmark-diagnostico.json` tem 14 famílias autorais: seis de treino,
duas de validação e seis de teste. Cada família contém um programa com defeito,
referência independente e exemplos de desenvolvimento/reservados. As famílias
não aparecem em mais de uma partição. O benchmark é público e foi inspecionado
para implementar o laboratório; não constitui teste externo cego.

Os rótulos de treino indicam quais edições satisfazem **desenvolvimento** das seis
famílias de treino. O ranking não recebe a referência correta como atributo,
exemplos reservados ou famílias de validação/teste no treino. A API de diagnóstico
aceita somente fonte e desenvolvimento; a CLI rejeita `referencia` e `reservados`.
O avaliador consulta reservados apenas depois de encerrar cada busca, e não os usa
para pedir uma nova correção.

Sementes 7/19/41, 1.200 passos de Adam por rede, sem selecionar a melhor semente.
Orçamento principal: 16 verificações; cobertura adicional: 128 verificações. Cada
execução tem limite de 512 passos; são no máximo 512 edições por padrão (até 1.024
mediante configuração). Uma única edição por tentativa; reparos compostos não são
prometidos. O código fonte, benchmark, dados de treino e pesos têm hashes no artefato.
A V3 anterior continua congelada em `dados/estados/v3-congelada.json`.

## Resultado local

| Método | Verificações por programa | Famílias de teste reparadas |
|---|---:|---:|
| Variações de tokens V2, sem rede | 16 | 2/6 |
| Edições de AST, sem rede | 16 | 5/6 |
| Ranking aprendido, cada uma das três sementes | 16 | 5/6 |
| Edições de AST, sem rede | 128 | 6/6 |
| Ranking aprendido, cada uma das três sementes | 128 | 6/6 |

Com orçamento 128, as seis correções passaram nos 12 exemplos reservados. São seis
problemas pequenos, não doze tarefas independentes. O ganho sobre a busca por tokens
vem da ampliação manual das edições. O ranking aprendeu nos dados de treino, mas
**não superou a busca estrutural sem rede** neste benchmark; foi mais lento. Portanto
**o padrão permanece sem rede**, com orçamento 128. O ranking fica disponível como
experimento, sem aumentar automaticamente a rede de efeitos ou o Transformer.

38 testes locais verificam regressões, aprendizado/gradientes, preservação de aliases,
strings, traços em falhas, limites e separação de partições. A execução de avaliação
com `--tsc` também verifica referências e correções em JavaScript e TypeScript no
runtime isolado existente. O GitHub publica pesos, diagnósticos, hashes e relatórios
por 30 dias, sem ativação automática no chat.

## Usar

Sem NumPy e sem pesos, já funciona:

```sh
python scripts/diagnosticar_estados.py \
  --contrato exemplos/diagnostico-incremento.json
```

O contrato contém apenas:

```json
{
  "codigo": "return entrada - 2;",
  "desenvolvimento": [
    {"entrada": 0, "saida": 2},
    {"entrada": 3, "saida": 5}
  ]
}
```

Treinar a rede própria e avaliar:

```sh
python -m pip install 'numpy>=1.24,<3'
OPENBLAS_NUM_THREADS=1 python scripts/experimento_diagnostico.py \
  --saida /tmp/diagnostico
python scripts/diagnosticar_estados.py \
  --contrato exemplos/diagnostico-incremento.json \
  --rede-ranking /tmp/diagnostico/seed-7
```

A pasta de saída deve estar vazia. Para auditar efeitos, acrescente
`--rede-efeitos /caminho/seed-7` apontando para uma rede **V3** do experimento de
precisão (1.679 parâmetros), não para os pesos de ranking. São formatos distintos.
Para paridade JS/TS, passe `--tsc /caminho/typescript/lib/tsc.js` ao experimento.
No GitHub, rode **Diagnóstico e reparos próprios**; não precisa de GPU.

## Limites e próxima etapa

Aceita corpos de função do subconjunto do interpretador, não qualquer JavaScript
ou TypeScript: sem funções aninhadas, chamadas livres, imports, classes ou APIs do
navegador/Node. Arrays têm até 16 itens; o domínio e o limite de passos permanecem
os documentados em `ESTADOS_ESTRUTURAS_REPARO.md`. A semântica rastreada foi copiada
da baseline congelada para preservar os experimentos anteriores.

Satisfazer exemplos finitos não prova equivalência com a referência nem capacidade
sênior. Uma correção é hipótese revisável. Quando o orçamento falha, o resultado
informa a falha e não entrega um programa incorreto como aprovado. As próximas
extensões são reparos compostos com orçamento fixo e funções/chamadas com pilha e
escopos limitados, mantendo avaliação por contratos e comparação sem rede.
