# Diagnóstico pareado — 9 de outubro de 2026

Os casos e rubricas foram congelados no commit `3f1164f`, antes da inferência.
As respostas e entradas completas estão em `motor.json` e `gerador.json`.
`avaliacao.json` registra leitura autoral, sem cegamento, das respostas finais.
Não é teste independente, nem avaliação de sessões inteiras.

| Condição | Motor: adequadas / 12 | Motor: parciais / 12 | Gerador: adequadas / 12 |
| --- | ---: | ---: | ---: |
| Reunido | 1 | 0 | 0 |
| Multiturno | 2 | 5 | 0 |
| Recapitulação | 2 | 1 | 0 |
| Estado assistido | 1 | 0 | 0 |

O motor resolve a conta de tempo nas quatro apresentações e a referência ao
teatro em duas. Comparações que apenas citam os fatos e devolvem uma pergunta
genérica receberam crédito parcial, quando relevantes. A geração direta não
executa os pedidos nem com o estado manualmente organizado. Isso enfraquece a
hipótese de que corrigir apenas memória ou apresentação resolveria este gerador.
Não identifica uma causa única entre capacidade, corpus e aprendizagem.

O resultado do motor é sensível à formulação: emprego separado recebe uma
comparação parcial, reunido recebe recusa. O estado assistido enviado ao motor
ainda passa pelo interpretador normal; essa condição não isola seu executor.
O efeito de recapitulação encontrado em modelos de outros trabalhos não se
transfere automaticamente ao Crivo.

O gerador perde dois turnos de histórico na recapitulação da conta de tempo.
Nas demais 47 entradas finais, o histórico inicial está completo. A geração
usa janela móvel: mesmo uma entrada inicialmente completa pode perder tokens
do prefixo durante a saída. A avaliação registra esse limite separadamente.
As condições reunida e assistida são curtas e não dependem dessa perda.

## Auditoria e consequência para o piloto

`auditoria_corpus.json` mede os exemplos reais com o tokenizer do checkpoint.
O arquivo humano compacto tem 62 pares, de 26 árvores; 56 são treino, mas
somente 27 pares de treino cabem inteiros nos 256 tokens. Apenas seis pares
humanos, somando partições, têm histórico e resposta completos nesse limite.
O conjunto autoral estático tem 119 cenários e 257 pares. Nenhum desses dois
arquivos oferece exemplo completo com seis turnos de histórico.

O aviso geral descreve outro corpus humano, de 497 pares. Seus binários não
foram encontrados localmente. A contagem do aviso não deve ser atribuída ao
arquivo compacto usado no piloto.

O experimento anterior `geracao_dialogo_20261008` já treinou perda causal de
resposta: 242 pares, 600 passos, checkpoint escolhido no passo 100, com
sobreajuste posterior. Continuou em 0/20 respostas adequadas. Portanto, a
intervenção não será repetir esse mesmo ajuste: o controle usa o material
antigo; o novo braço recebe trajetórias autorais curtas de oito turnos, com
relações, correções e atribuição de fontes. O teste é restrito à aprendizagem
dessas relações, não uma promessa de conversa livre. Novos exercícios
procedurais não são novas conversas humanas nem diversidade independente.

Os dois braços continuam do mesmo checkpoint próprio, têm o mesmo orçamento
de tokens-alvo e replay humano. As 12 sondas deste diagnóstico ficam fora do
treino e da escolha de pesos. Nenhum candidato será promovido por perda menor
ou por palavras coincidentes. Se as novas sessões continuarem falhando, o
piloto será rejeitado e registrado, sem integração ao chat.
