# Melhoria própria de igualdade e índices

Esta etapa começou depois da regressão e integração do PR75. Corrige as duas falhas de aprendizado observadas: igualdade numérica e índices em arrays longos. A baseline V2 permanece intacta; seus hashes ficam em `dados/estados/v2-congelada.json`. A nova rede continua pequena: **1.679 parâmetros**, quatro a mais que os 1.675 anteriores, inicializados aleatoriamente e treinados do zero.

## Causas e alterações

Na V2, o índice 0 recebia 320 exemplos de treino; o índice 15 recebia apenas sete. Selecionar um valor exige aprender uma linha de 16 coeficientes, e sete exemplos não identificavam essa linha de forma confiável. O novo gerador inclui arrays de 16 posições e todos os índices válidos de cada array. Há entre 1.048 e 1.904 exemplos de treino por posição, e todos os índices de um mesmo conteúdo ficam na mesma partição. Os dados dos novos arrays de avaliação não aparecem em nenhuma das partições de efeitos.

Igualdade compartilhava um MLP com as outras comparações e apresentava erros perto da diagonal a=b. Agora recebe uma cabeça linear dedicada de quatro parâmetros. Seu atributo é a distância absoluta da **diferença prevista pela cabeça de subtração própria**, junto a uma constante. Os logits e a fronteira entre igual/diferente são aprendidos em exemplos balanceados; não há `a == b` calculado como resposta na entrada nem consulta ao executor exato. Se a subtração aprendida erra, a igualdade também pode errar — um teste demonstra essa dependência.

Esse formato incorpora uma escolha manual de representação. Não se afirma que a rede descobriu o conceito de distância ou a estratégia de comparação. `!==` reutiliza o complemento da igualdade, sem aprendizagem independente dessa inversão.

## Protocolo e resultados

A avaliação de foco fixa sete famílias e 228 execuções antes de treinar a V3. Inclui igualdade em objetos, desigualdade, ramificações, último índice, soma de extremos, cópia e soma de arrays de 16 posições. Os programas completos não são dados de treino; operadores numéricos isolados continuam conhecidos. Um dos 228 casos é idêntico a um caso da V2 e é identificado no protocolo; os 228 não são problemas independentes. Há arrays e entradas compartilhados entre famílias, que verificam composições diferentes.

A V2 e a V3 são treinadas do zero nas mesmas três seeds. V2 usa 5.000 passos com seus dados originais; V3 usa 5.000 passos nos operadores restantes com maior cobertura e depois 2.000 passos na cabeça de igualdade. Não é comparação de orçamento/dados idênticos; o custo adicional é registrado. Os modelos não são selecionados pelos resultados de teste.

| Seed | V2 no conjunto de foco | V3 no conjunto de foco | V3 na regressão conhecida |
|---|---:|---:|---:|
| 7 | 67/228 | 228/228 | 101/101 |
| 19 | 65/228 | 228/228 | 101/101 |
| 41 | 68/228 | 228/228 | 101/101 |

Nos efeitos reservados, cada seed acertou 115/115 igualdades e 2.774/2.774 índices. Na validação, houve 114/114 e 2.822/2.822. A busca com reparos preservou 7/7 contratos completos do conjunto anterior. Estes são resultados locais; o workflow repete todos os treinos e comparações no GitHub.

Tudo continua no domínio limitado: comparações de inteiros em -16..16, arrays numéricos de até 16 posições e executor próprio do subconjunto JS. Os resultados não demonstram competência em projetos gerais, arrays arbitrariamente grandes ou nível sênior. Os casos são autorais e públicos, sem revisão independente; após esta sessão, tornam-se também referências de regressão conhecidas. Nenhum candidato é ativado automaticamente na aplicação.

## Uso

Repetir o experimento em CPU:

```bash
OPENBLAS_NUM_THREADS=1 python scripts/experimento_precisao.py --saida /tmp/precisao --tsc /tmp/ts/node_modules/typescript/lib/tsc.js
```

Interpretar com o novo modelo:

```bash
python scripts/interpretar_preciso.py --rede /tmp/precisao/seed-7 --entrada-json '{"a":2,"b":3}' --codigo 'return entrada.a === entrada.b;'
```

A CLI também admite `--contrato` no mesmo formato de desenvolvimento da V2. Os formatos de pesos são distintos e verificados; a CLI V2 permanece disponível. O workflow **Precisão própria de igualdade e índices** verifica gradientes, baseline, partições e ausência de fallback, confirma paridade JS/TS isolados e publica modelos/relatórios por 30 dias.
