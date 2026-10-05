# Compreensão por contrastes de contexto

O modelo próprio frequentemente mantém a conclusão quando uma negação, condição
ou informação do histórico muda. Este piloto ensina pares com contextos opostos:
cada contexto exige uma das duas respostas. A opção correta em um é incorreta
no outro. Não há uma tabela de respostas usada pelo chat; os exemplos servem
para calcular gradientes nos pesos próprios.

## Treino e limites dos dados

O currículo é sintético autoral, com cinco famílias: condição, negação,
atualização de informação, referência e evidência. O cenário fornece os fatos
necessários. Pessoas, objetos, locais e formulações reservadas são separados
do treino antes da execução. Não são conversas humanas nem novos conhecimentos
factuais certificados.

São 150 registros de pares de treino, 60 de validação e 60 de teste. **Há
repetições de enunciados** ao enumerar combinações. Ignorando IDs e ordem das
opções, são 84 pares textuais distintos no treino e 40 em cada reserva; no
treino há 162 entradas distintas, contando mensagem e histórico. As contagens
brutas não representam exemplos independentes. Cada família usa poucas formas
gramaticais; reservar entidades e enunciados não equivale a uma avaliação ampla.

A perda combina três termos:

1. Probabilidade da resposta correta, com média por resposta.
2. Penalidade `softplus(0,2 - score_correto + score_incorreto)` para a conclusão
   incompatível com o contexto. O score é o log da probabilidade média dos
   tokens-alvo, incluindo fim; pedido e histórico não recebem supervisão.
3. Replay de dois diálogos por passo do corpus próprio com contexto inteiro.

O objetivo é contrastivo e supervisionado. Não isola o efeito de cada termo nem
constitui DPO ou uma reprodução computacional do cérebro. O peso de replay
e a quantidade de dados deste piloto não impediram o estreitamento das respostas.

## Rodada executada em 2026-10-05

Inicialização: passo 50 do ajuste com contexto inteiro, SHA-256 dos pesos
`dec8f523ccc861bddd405aae82878cded428afe6e8f6029be0de909dad02db33`.
Arquitetura: o mesmo Transformer próprio de 15.953.664 parâmetros, sem pesos
externos e sem repetir o pré-treino de 30 mil passos.

Executei **60 passos reais em CPU**, com lote de dois pares, LR 0,00008,
peso contrastivo 1 e replay 0,5. A seleção só examinou validação. O passo 40
foi congelado antes de examinar o teste; seu SHA-256 é
`fa49d47713a6d682b451be4eec0d3203daf49f331f68a04ff153d37dab28e45b`.
O passo 60 regrediu para 7/60 pares de validação. Não houve outro ajuste depois
do teste. As reservas deste experimento agora estão expostas; não se tornam
novamente cegas em futuras rodadas.

| Medida | Antes | Passo 40 |
|---|---:|---:|
| Ranking: ambos os contextos corretos, validação | 12/60 | 25/60 |
| Ranking: ambos os contextos corretos, teste | 13/60 | 0/60 |
| Geração livre: ambos os contextos exatos, validação | 0/10 | 2/10 |
| Geração livre: ambos os contextos exatos, teste | 0/10 | 0/10 |

Ranking fornece os dois alvos ao avaliador, que mede suas probabilidades;
eles não são fornecidos como opções ao contexto do modelo. Geração livre não
recebe os alvos. Correspondência exata é um critério limitado: pode rejeitar
uma paráfrase correta. Os dois lados precisam acertar, porque uma resposta
constante pode acertar um lado por acaso.

No painel anterior de 17 turnos, respostas repetitivas caíram de 5 para 1,
mas o candidato passou a responder **“Não pode entrar”** em assuntos como café,
estudo e analogias. A revisão pelo assistente encontrou essa perda de pertinência.
Reduzir repetição ou terminar mais respostas não certifica compreensão.

**Decisão: candidato rejeitado, sem ativação no chat.** O ganho de validação
não se transferiu às formulações de teste nem à conversa geral. Os pesos e o
checkpoint completo continuam no workspace; esta rodada não criou arquivos
adicionais no Drive nem usou a GPU do usuário.

Os resultados completos, incluindo saídas ruins e a decisão, estão em
[`avaliacoes/linguagem_profunda/contrastes_20261005`](../avaliacoes/linguagem_profunda/contrastes_20261005/).

## Reproduzir

Use uma nova pasta local, com o corpus e os pesos próprios verificados:

```bash
python scripts/treinar_compreensao_contrastiva.py \
  --inicial modelo-proprio --corpus corpus-integro --saida piloto-contrastes \
  --passos 60 --lote 2 --lr 0.00008 --peso-contraste 1 --peso-replay 0.5 \
  --avaliar-a-cada 20 --threads 2 --max-segundos 600
python scripts/avaliar_compreensao_contrastiva.py \
  --modelo piloto-contrastes/melhor --split validacao --saida candidato-validacao.json
```

O checkpoint contém Adam e RNG de NumPy/PyTorch/CUDA. `--retomar` conserva
configuração, horizonte, dados e hashes de código; `--parar-em` permite pausar
sem alterar o experimento. Nunca inicia por cima de uma pasta existente sem
retomada. Mantém só os arquivos atuais e os do melhor ponto, com escrita
atômica, e deve usar disco local. O teste só deve ser consultado após congelar
o candidato e encerrar a seleção.

`avaliar_promocao_compreensao.py` compara anterior/candidato em validação e teste,
verifica os mesmos painéis e pesos congelados e recalcula acerto dos dois lados
da geração livre. Recusa regressão ou menos de 80% de pares corretos em qualquer
medida. Esse limite é um critério de engenharia desta tarefa; mesmo superá-lo
requer revisão semântica e nunca ativa pesos automaticamente.

Sete testes novos verificam partições, contextos opostos, supervisão, gradientes,
retomada exata, comparação de pesos e rejeição de respostas constantes. Os 23
testes anteriores de linguagem/contexto também passaram localmente.

O próximo experimento precisa de mais estruturas de diálogo e conclusões
variadas, com deduplicação e replay medido em conversa, antes de aumentar passos.
Repetir os mesmos poucos enunciados por mais tempo não é uma expansão de
capacidade demonstrada por esta rodada.
