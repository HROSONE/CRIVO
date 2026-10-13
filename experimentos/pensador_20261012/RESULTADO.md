# Pensador — resultado (13/10/2026)

Execução no Colab (T4): `MyDrive/CRIVO/pensador-20261012/execucao_20261013_023653/`. Números lidos do
resumo do notebook (célula 4) e do log da célula 2. Rede recursiva de 415.623 parâmetros, 20.000
passos; o controle usa a mesma rede com 1 volta só.

**Aprovado: não.** `ativo_no_chat: false`.

## Recursivo (8 voltas, passo 20.000 escolhido pelo dev)

| Conjunto | Exato | Status | Erradas (rede) | Cobertura segura |
|---|---|---|---|---|
| blind_iid | 84,5% (gate 95%) ❌ | 100,0% | 0,0% | 78,5% |
| ood_profundidade (provas de 4–6 regras) | 57,9% (gate 80%) ❌ | 97,1% | 1,3% | 39,4% |
| ood_tamanho (11–16 átomos) | 64,6% (gate 80%) ❌ | 97,2% | 1,0% | 53,5% |

Gates que passaram: afirmações erradas da rede ≤ 2%, zero afirmação errada com a política (prova
conferida + base consistente) e invariância a renomear e reordenar (99,9%).

O mesmo modelo avaliado com outro número de voltas:

| Voltas | blind exato | blind status | profundidade exato | tamanho exato |
|---|---|---|---|---|
| 1 | 41,8% | 88,8% | 22,7% | 7,8% |
| 8 (treino) | 84,5% | 100,0% | 57,9% | 64,6% |
| 16 | 82,7% | 100,0% | 55,9% | 65,8% |

## Controle raso (1 volta, passo 18.000)

| Conjunto | Exato | Status | Erradas (rede) | Cobertura segura |
|---|---|---|---|---|
| blind_iid | 40,2% | 80,7% | 11,2% | 24,6% |
| ood_profundidade | 14,6% | 62,1% | 21,7% | 3,4% |
| ood_tamanho | 1,8% | 29,6% | 12,4% | 0,0% |

Invariância 90,1%. A política continuou sem erro (a conferência barra o que a rede erra), mas
com quase nenhuma cobertura.

## O que isso mostra

- **A recursão é o que faz a rede raciocinar.** Com os mesmos parâmetros, 8 voltas em vez de 1
  levam o exato de 40% para 85% nos problemas parecidos com os do treino, e de 2% para 65% nos
  problemas maiores. A rede rasa erra muito com confiança (11–22%); a recursiva quase nunca (≤ 1,3%).
- **Ela acerta o veredito, mas ainda não a prova.** O status fica entre 97% e 100% em todos os
  conjuntos, inclusive fora da distribuição; o que falha é escolher o conjunto mínimo de premissas
  (e a pergunta útil), que é o que o "exato" exige.
- **Pensar mais que o treino não ajuda.** 16 voltas dão o mesmo que 8. A rede aprendeu um número
  fixo de passos, não a pensar até terminar.
- **Com a política, nenhuma afirmação errada**: tudo o que a rede afirma passa pela conferência do
  CRIVO. O custo é a cobertura (39–79%): no resto, o CRIVO diz que não consegue concluir.

## Limites

- Lógica proposicional limpa, com até 16 átomos. Não diz nada sobre raciocínio em linguagem livre.
- Até 10 átomos, o enumerador do CRIVO já resolve com exatidão; o ganho real só aparece acima disso
  (`ood_tamanho`), onde a cobertura segura foi de 53,5%.
- Uma execução, uma semente.

## Próximos passos possíveis (nada decidido)

- Supervisionar a prova com mais peso, ou fazer a rede apontar uma premissa por volta.
- Parada adaptativa (a rede decide quando terminou), para que mais voltas ajudem em provas longas.
