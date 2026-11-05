# Lições e sondagens para fazer mais com pouco (19/10/2026)

Fonte: os registros de experimentos do próprio projeto (34 conclusões e relatórios) e duas
sondagens feitas hoje. Não são resultados validados por ninguém de fora: são hipóteses
extraídas dos nossos dados, para testar com a régua.

## Padrões que se repetem nos registros

1. **O modelo decora gatilhos quando tem poucas formas de dizer.** Ex.: "onde cada situação tinha
   só ~6 jeitos de falar, ele decorou gatilhos de palavra". Ganho em desenvolvimento não virou
   ganho em conversa real.
2. **Blind que já foi visto deixa de medir.** "Os blinds da v1 e da v2 deixam de ser limpos, porque
   eu já vi onde eles erram." Precisa de conjunto novo, congelado antes dos dados.
3. **Média esconde regressão.** "Melhor CE total pode esconder regressão em um subconjunto menor."
   Reportar sempre por subconjunto (perguntas do usuário, frases reais, blinds).
4. **Ganho de desenvolvimento não é ganho no chat.** Várias versões melhoraram o desenvolvimento e
   não foram aprovadas para o chat.
5. **Verificador exato vence gerador maior.** O pensador (918 mil parâmetros) propõe e o
   enumerador confere: a resposta exata só entra se os dois concordarem.

## Sondagem 1: escolher entre 6 candidatas do modelo de 46 milhões (19/10/2026)

- Modelo de 46 milhões sozinho, na régua das 100 perguntas frequentes, com o 1º resultado (guloso): **19/100**.
- Melhor de 6 candidatas, escolhendo com as mesmas regras de conferência: **39/100**. Mas isso é
  trapaça de medida: quem escolhe e quem julga usam o mesmo critério.
- Melhor de 6, escolhendo só com as proibições gerais (inventar contexto, sentimentos) e julgando
  com a régua completa: **19/100**. **Nenhum ganho.**
- Custo: cerca de 0,14 s por candidata, em CPU.

**Lição:** a seleção entre candidatas só ajuda quando o critério de escolha sabe o que é certo.
Os critérios que sabem (as regras da régua) não existem no chat. O que existe no chat é a base de
fatos. Então o caminho é verificar a resposta contra o fato recuperado, não contra a régua.

## Hipóteses para a próxima sondagem (da mais barata para a mais cara)

| # | Hipótese | Como testar | Critério para desistir |
|---|---|---|---|
| H1 | Verificar a candidata contra o fato recuperado da base (palavras-chave do fato precisam aparecer) | 100 perguntas frequentes: candidatas do 46M, escolher a que contém o fato da base | Não melhora sobre o guloso |
| H2 | Recusa calibrada: responder só quando a busca na base tem confiança acima de um limiar | Mesma régua; medir acerto e taxa de "não sei" | Taxa de invenção não cai |
| H3 | Roteamento pelo tipo da pergunta (classificador de regras, 0,92 na régua) antes da resposta | Regras da régua de 55 casos | Não reduz as respostas erradas por tipo |
| H4 | Cabeça pequena sobre o modelo congelado (como a cabeça do pointer, 25 mil parâmetros) para classificar o tipo | Treino em Colab, depois medir na régua de classificação | Abaixo de 0,90 na régua |

## O que não fazer

- Não usar as regras da régua para escolher a resposta e chamar isso de ganho.
- Não mudar o limiar depois de ver o resultado.
- Não tratar uma sondagem de 100 perguntas como medida final.

## Sondagem 2: o "truque do Qwen" no modelo de 46 milhões (05/11/2026)

Motivação: uma pesquisa do MIT (pesos do Qwen3.5-0.8B editados por outro modelo, sem treino) subiu
o acerto em matemática de 7,9% para 48,1%. A melhora veio de remover laços de repetição: as
respostas não terminavam.

Diagnóstico do 46M sozinho (sem contexto do chat):
- Régua de 100: 19/100; nenhuma resposta sem terminar; nenhuma repetição de 3 palavras; 6,3 palavras em média.
- Régua de 55: 12/55; nenhuma sem terminar; nenhuma repetição; 3,2 palavras em média.
- Mais de um terço das respostas termina devolvendo uma pergunta.

O problema é o oposto do Qwen: respostas curtas e vazias, não respostas que não terminam.

Teste: penalizar o token de fim nas 8 primeiras palavras (força 0, 1, 2, 3, 5), escolhida na régua de 55.
Resultado: 12/55 em todas as forças; tamanho médio de 3,2 para 3,8 palavras. Nenhum ganho.

**Lição:** a edição do Qwen tirou um obstáculo que escondia um conhecimento existente. No 46M, o
conhecimento não está lá: ele inventa nomes ("Sr. Lebowski") e repete a pergunta de volta.
Edição pequena de pesos não cria conhecimento. O caminho continua sendo dados e fatos.

Limite: o 46M foi medido com contexto vazio. No chat ele recebe identidade e fatos, o que muda o resultado.
