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

## v2 (15/10/2026): aprovado nos gates, não ligado ao chat

Treino na conta G (T4, `notebooks/pensador_v2_colab.ipynb`); a sessão caiu antes da avaliação
final. A melhor versão pelo dev (passo 13.000, `pensador.pt` sha256 `7a5f0639…ee64a`, 918.343
parâmetros) foi avaliada depois, na CPU, com `treinar_pensador_v2.py --so-avaliar`: os mesmos
conjuntos congelados (sha `20deb41a…`) e os mesmos gates. Resultado: `resultado_pensador_v2.json`.

Prova exata (status entre parênteses); a conta que aprova, registrada antes, é a adaptativa com busca:

| | v1 | v2 rede (8 voltas) | v2 adaptativa | **v2 adaptativa + busca** | gate |
|---|---|---|---|---|---|
| blind iid | 84,5% | 85,7% (100%) | 85,8% | **99,6%** (100%) | ≥ 95% |
| ood profundidade | 57,9% | 75,4% (97,1%) | 72,8% | **95,9%** (96,9%) | ≥ 80% |
| ood tamanho | 64,6% | 78,8% (99,0%) | 77,6% | **97,8%** (98,8%) | ≥ 80% |

Afirmações erradas da rede sozinha: ≤ 0,4%; com a política (prova conferida), 0 erro. Invariância
à ordem das premissas: 99,95%. **Todos os gates passaram: aprovado.**

**Limites:**
- A busca usa o verificador do CRIVO: a rede ordena as premissas e diz o status; o verificador
  acha a prova mínima entre as 10 mais confiáveis. Boa parte do salto de 85% para 99% vem dessa
  combinação, não da rede sozinha (a rede sozinha melhorou de 57,9% para 75,4% nos casos mais
  profundos).
- A parada adaptativa sozinha não foi melhor que 8 voltas fixas (72,8% contra 75,4% na
  profundidade); ela economiza voltas (≈5 a 6 em vez de 8).
- São problemas lógicos sintéticos do próprio gerador (premissas formais), não frases em
  português. O pensador ainda não está ligado ao chat (`ativo_no_chat: false`); falta a ponte
  frase → premissas.
- Um treino só (uma semente), interrompido antes dos 30 mil passos.
