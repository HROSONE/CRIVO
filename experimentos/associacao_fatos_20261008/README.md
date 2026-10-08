# Continuação executada: associação de fatos e símbolos locais

**Treinos concluídos pelo Codex em CPU. O usuário não precisa repeti-los em GPU.**
Dois candidatos próprios de 2.947.216 parâmetros completaram 600 atualizações cada,
partindo dos pesos contextuais anteriores. Não passaram no critério local e não
foram ativados no chat. O piloto de geração de texto é separado, em
`../geracao_dialogo_20261008`.

[Inspecionar os pesos já treinados no Colab](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/associacao-fatos-20261008/notebooks/crivo_associacao_e_dialogo.ipynb).
O notebook não inicia treino nem precisa de GPU.

## Painel novo de 400 contratos

| Checkpoint / entrada | Acertos | Sessões completas / 100 | Preços / 200 | Requisitos / 200 |
| --- | ---: | ---: | ---: | ---: |
| Anterior, texto bruto | 9 (2,25%) | 0 | 1 | 8 |
| Anterior, nomes normalizados | 24 (6%) | 0 | 2 | 22 |
| Ajustado, texto bruto | 147 (36,75%) | 5 | 31 | 116 |
| Ajustado, nomes normalizados | 248 (62%) | 12 | 93 | 155 |

Todos os resultados da tabela usam **o mesmo decodificador de cópia limitada**.
Respostas sem essa ajuda também estão conservadas em `avaliacao_ablation/`.
As quatro condições distinguem normalização sem treino e ajuste dos pesos.
Diferenças de comprimento alteram o consumo de RNG/dropout e a seleção escolheu
passos diferentes. Há uma única semente, sem avaliação independente.

O resultado anterior de 85,5% era de **outro painel**, com molduras mais simples.
Não é comparável diretamente aos 62% do novo painel. No painel anterior conhecido,
estas quatro condições obtiveram 85,5%, 90,5%, 96,5% e 94,75%, respectivamente.
Esse painel agora é diagnóstico, não um novo teste cego.

Na variante normalizada ajustada, a decomposição do painel novo foi:

| Etapa | Preços corretos / 50 | Requisitos corretos / 50 |
| --- | ---: | ---: |
| Declaração inicial | 48 | 50 |
| Correção factual | 12 | 38 |
| Hipótese | 12 | 18 |
| Retorno aos fatos | 21 | 49 |

Reconhecer a operação foi correto nos 400 casos. Interpretar argumentos e escopo
permaneceu falho: preços tiveram escopo correto em 131/200, requisitos em 164/200.
**Classe correta não é raciocínio correto.** O critério exigia pelo menos 80% em
cada família nova, ganho de 20 pontos nas sessões completas sobre os pesos anteriores
com a mesma representação e queda máxima de 5 pontos no painel anterior conhecido.
Nenhuma condição atingiu todos esses limites.

As quatro condições ainda tiveram **0/4** na sonda de preços já conhecida da rodada
anterior. O diagnóstico encontrou uma limitação concreta do normalizador: “Estou”
e “Refaça” foram tratados como nomes, deslocando os símbolos dos planos. Esse erro
permanece publicado. Não corrigimos o detector após observar o teste para apresentar
aprovação. Os próximos dados precisam incluir frases iniciais diversas,
identificação de entidades por relações e continuidade de correções/hipóteses,
em outro painel registrado antes do ajuste.

## Dados e normalização

4.000 prefixos novos de 1.000 sessões, 300 prefixos de validação de 75 sessões e
400 prefixos de teste de 100 sessões. Os bancos de declarações, correções,
hipóteses, retornos e perguntas são separados. Cada sessão tem quatro falas.
Há nomes de planos, ordem trocada, terceiros/distratores numéricos e inventários
provados, refutados, indeterminados ou contraditórios. Nenhum contexto foi cortado.
Os valores são inteiros e distintos; não se trata de cobertura de toda linguagem,
empates, moedas ou nomes compostos. Os itens/pessoas reservados anteriormente
foram reutilizados como vocabulário, explicitamente; trajetórias e molduras deste
painel são novas. Molduras de tarefa e autoria continuam compartilhadas.

Cada lote contém 12 exemplos novos e quatro dos 1.000 exemplos de treino antigo
reservados para replay. Ambos os braços usam o mesmo checkpoint inicial,
semente 20261010, stream de exemplos, AdamW, LR 0,0001 e lote 16. Seleção somente
pela validação: 70% da média por família do novo dev limitado e 30% da média por
família do dev anterior limitado. O braço bruto selecionou passo 600; o normalizado,
passo 100. Ambos executaram as 600 atualizações completas. Levaram aproximadamente
894 e 757 segundos em CPU, parcialmente sobrepostos; não são estimativas de GPU.

A normalização usa até oito palavras com inicial maiúscula fora de uma lista fixa
de palavras funcionais. A ordem explícita da última consulta de dois nomes recebe
prioridade; em sua ausência, usa primeira menção. Nomes tornam-se símbolos locais
do próprio vocabulário; offsets voltam aos caracteres originais. Não lê operação,
família, preços, rótulos ou alvos para decidir aliases. É uma heurística limitada,
não reconhecimento universal de entidades ou memória persistente.

O método de cópia de spans da rodada anterior é usado com suporte declarado a
prefixos de regra como “exigidos são” e “requeridos nesse acesso são”. Essa gramática
ajuda ambos os checkpoints e não constitui entendimento neural de português livre.
Nenhum peso/tokenizer/modelo de terceiros, API externa ou conversa privada foi usado.

## Preservação e reprodução

`protocolo.json` foi registrado antes do primeiro treino. A normalização foi
motivada pelos erros do **dev** e registrada em `ablation_preteste.json`, antes
de seu treino e de qualquer previsão no painel final. Scripts e protocolos
anteriores foram conservados. Avaliações não escolhem nem alteram pesos.

```sh
python gerar.py /tmp/assoc-nova/dados
python ajustar.py --dados /tmp/assoc-nova/dados --saida /tmp/assoc-nova/candidato
python ajustar_normalizado.py --dados /tmp/assoc-nova/dados --saida /tmp/assoc-nova/candidato_normalizado
```

Para repetir a avaliação publicada, copie os protocolos e dados publicados para
uma pasta nova, execute os dois braços e invoque `avaliar_ablation.py --experimento
PASTA`. O painel publicado já é conhecido; repetir não cria validação independente.
Não sobrescreva rodadas. `--retomar` conserva Adam, RNG e progresso a partir de
`retomada.pt`; os checkpoints completos desta rodada permanecem locais. Pesos
escolhidos, relatórios, dados e erros foram publicados. Os dois treinadores são
snapshots separados para conservar a versão bruta congelada e distinguir assinaturas
de retomada.

Quatro contratos do corpus, quatro de normalização e dois de supervisão causal do
piloto de geração passaram. A confirmação em GPU/Colab não foi executada. Nenhum
arquivo de runtime ou peso ativo foi alterado.
