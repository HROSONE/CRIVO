# Estados, estruturas e reparo: segunda etapa própria

Esta etapa implementa os quatro avanços propostos: baseline congelada, operadores ampliados, estruturas de dados e busca com reparos. Todos os modelos continuam treinados do zero. O interpretador, a gramática e o mecanismo de reparo foram implementados manualmente; o relatório distingue sua contribuição da contribuição dos pesos aprendidos.

## Congelamento e avaliação

A implementação anterior permanece intacta em `interpretacao_estados.py`, `rede_efeitos.py` e `scripts/treinar_efeitos.py`. `dados/estados/v1-congelada.json` registra seus hashes e o benchmark antigo. Se essas fontes mudarem, o experimento interrompe a comparação em vez de alterar silenciosamente a baseline.

`dados/estados/benchmark-v2.json` fixa 16 famílias, 101 execuções e sete contratos. Foi produzido antes do primeiro treino V2. Os programas e contratos não são dados de treino das redes de efeitos. Três seeds predefinidos (7, 19, 41) iniciam modelos diferentes. Para cada um, o protocolo treina V2 por 5.000 passos e a baseline V1 por 4.000. Registra pesos aleatórios antes do treino, resultados posteriores, hashes de dados/fontes/benchmark/pesos, perdas e relatórios por seed. Nenhum seed é escolhido como vencedor.

A reserva é relativa ao treino, não sigilo: o benchmark é autoral e público, sem revisão independente. Operadores conhecidos reaparecem em novos programas; não se afirma descobrir semânticas desconhecidas. O script grava o protocolo antes de treinar. Resultados foram consultados nesta sessão; usos futuros deste mesmo benchmark são regressão, não nova avaliação independente.

## Representação e capacidades

`interpretacao_estruturas.py` expande o subconjunto de JS: multiplicação, comparações inclusivas, desigualdade, operadores booleanos com curto-circuito, arrays, índices, objetos simples e métodos autorizados. Inclui `push`, `slice`, `includes`, `trim`, minúsculas e maiúsculas. Os traces registram operadores, estados profundos antes/depois e métodos manuais. A avaliação respeita a ordem do alvo e do valor em atribuições. Aliases de objetos/arrays são preservados no executor exato. A entrada do chamador é copiada para evitar alterar objetos do processo pai.

Strings são medidas em unidades UTF-16 para corresponder a JS; `slice` respeita essas unidades e `trim` usa os espaços definidos no subconjunto de JS. Normalização Unicode não é uma capacidade aprendida. A referência também é compilada/avaliada em JS e TS isolados; os exemplos não constituem prova completa da semântica Unicode ou da linguagem.

O domínio continua restrito: inteiros entre -512 e 512, arrays/objetos de até 16 posições/chaves, profundidade até quatro, strings de até 64 unidades UTF-16, 16 variáveis, 768 tokens e 12 mil caracteres de fonte. Há orçamento de execução padrão de 512 passos (máximo 2.048). Não há floats, funções livres, imports, APIs de SO/rede, classes ou JavaScript completo. O interpretador não usa eval/exec para executar o código fornecido. TypeScript é uma forma de saída tipada das referências; o parser próprio não interpreta sintaxe TS arbitrária.

## Rede própria de 1.675 parâmetros

A rede tem cabeças distintas:

- Regressão condicionada pelo operador para soma/subtração; operandos são normalizados e enviados a canais separados, sem resultado pronto nos atributos.
- MLP para comparações numéricas e outro MLP para lógica booleana.
- Regressão de comprimento a partir da ocupação de 16 posições. Contar posições é aprendido; construir a máscara é manual. Arrays/strings diferentes podem compartilhar a mesma máscara conhecida.
- Seleção de índice por matriz aprendida entre uma consulta one-hot e todos os valores do array; o valor esperado não é colocado diretamente no vetor de entrada. Só aceita arrays numéricos.

Os dados numéricos usam operandos entre -16 e 16 e partições por operação/par não ordenado. Reversões ficam juntas, mas ambas são mantidas, pois subtração/comparação não são comutativas. Os dados estruturais são deduplicados por entrada real e particionados por conteúdo. As tabelas booleanas completas ficam no treino; sua avaliação reservada mede composição, não descoberta das tabelas.

Soma/subtração permitem operandos além da faixa de treino, com limite do executor: a avaliação reporta essa extrapolação separadamente. Comparações continuam limitadas a -16..16. Multiplicação é um algoritmo manual de adições previstas pela rede, com operandos em -16..16; não há multiplicação pronta no vetor nem alegação de que a rede inventou o algoritmo. Objetos e os métodos de texto são manipulados pelo interpretador; a rede não aprende a decodificar strings ou escolher propriedades arbitrárias. Fora das operações/domínios aprendidos, a previsão falha explicitamente, sem fallback para o oráculo.

## Busca e reparo

`busca_estados.py` amplia a gramática para expressões, condições, acumulação, transformação/filtro de arrays, operações de texto e campos de objetos. Ela é escrita manualmente e tem até 2.000 candidatos (padrão 1.000). A rede pode ordenar candidatos; até 64 finalistas são conferidos exatamente. O modo sem rede segue a ordem da gramática. O relatório conta chamadas de previsão, candidatos, verificações exatas e tempo total.

O reparo recebe somente contraexemplos de desenvolvimento previamente separados. Acrescenta um exemplo que o candidato atual falha, altera tokens de constantes/operadores e refaz a busca, no máximo duas vezes. Os casos reservados são executados somente depois de finalizar os reparos, tanto na solução inicial quanto na final. Nenhum erro reservado é reenviado à busca. A CLI recusa arquivos de contrato contendo campos extras, incluindo casos reservados.

Não modificar a entrada faz parte do contrato deste laboratório. Uma função que atende poucos exemplos pode falhar fora deles; não há prova de corretude geral. A geração ainda se restringe à gramática, sem projetos livres ou vários módulos.

## Resultados locais

| Seed | Execuções corretas | Efeitos reservados corretos | Busca guiada inicial → após reparos |
|---|---:|---:|---:|
| 7 | 97/101 | 1.458/1.478 | 6/7 → 7/7 |
| 19 | 95/101 | 1.450/1.478 | 6/7 → 7/7 |
| 41 | 97/101 | 1.456/1.478 | 6/7 → 7/7 |

A comparação de referências passou 202/202 casos, em 32 verificações JS/TS. Multiplicação composta passou 81/81 casos por seed e extrapolação aritmética passou 32/32. Igualdade e alguns índices, especialmente em arrays longos, ainda falham; erros pequenos podem se acumular numa execução.

A baseline V1 acertou 8/101, mas seu executor só suporta 8 desses casos. Portanto, esse salto inclui aumento manual da cobertura da linguagem e não pode ser atribuído integralmente ao aprendizado da rede.

A busca sem rede também passou 6/7 → 7/7 e foi mais rápida neste benchmark pequeno: aproximadamente 0,03–0,05 s somadas nas buscas iniciais, contra 0,39–0,47 s da ordenação neural, no ambiente local. Menos verificações exatas não demonstram ganho de velocidade total. A busca padrão permanece simbólica; a orientação neural é uma opção experimental explícita.

O verificador existente também recebeu uma correção: separa registros de stdout por LF em vez de `splitlines()`, que fragmentava JSON contendo caracteres Unicode U+0085/U+2028/U+2029. Um teste confirma que eles não invalidam saídas corretas.

## Uso

Repetir o protocolo completo em CPU:

```bash
OPENBLAS_NUM_THREADS=1 python scripts/experimento_estados_v2.py --saida /tmp/estados-v2 --tsc /tmp/ts/node_modules/typescript/lib/tsc.js --passos 5000
```

Executar uma soma sobre array com a rede:

```bash
python scripts/interpretar_estruturas.py --rede /tmp/estados-v2/seed-7 --entrada-json '[1,2,3]' --codigo 'let total = 0; let i = 0; while (i < entrada.length) { total += entrada[i]; i += 1; } return total;'
```

Sem `--rede`, usa o executor exato e marca a origem no trace. Para buscar com reparos, passe `--contrato contrato.json`, por exemplo:

```json
{
  "tipo": "numero",
  "desenvolvimento": [{"entrada": 0, "saida": true}, {"entrada": 3, "saida": false}],
  "contraexemplos_desenvolvimento": [{"entrada": 2, "saida": true}, {"entrada": 1, "saida": true}]
}
```

O workflow **Estados, estruturas e reparo próprios** repete testes matemáticos/semânticos, paridade e os três treinos CPU, e preserva modelos/relatórios por 30 dias. A primeira versão e o Transformer permanecem disponíveis; não há ativação automática na aplicação pública.
