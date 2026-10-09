# Roteamento natural: 35 regressões reais

O candidato passou de 23/35 para 33/35 respostas com a peça correta e conteúdo
verificado, mantendo os 25 casos anteriores intactos e acrescentando dez falhas
observadas no site após o merge do #121. As dez novas passaram. Na bateria,
trocas de domínio caíram de quatro para zero e casos com referentes ausentes
caíram de cinco para zero. Estes resultados medem regressões conhecidas de
desenvolvimento; não provam generalização de conversa livre.

## Evidências e congelamento

- `site_antes.json`: 18 pedidos reais ao site público, com `message/history`,
  sem memória injetada. O health antes e depois identifica a main `ab157203`.
- `d4eff2b`: congela os 35 casos antes de alterar o motor. Os dez acrescentados
  incluem três falhas já relatadas e sete descobertas nessa coleta.
- `63a244c`: registra `baseline.json`, 23/35 e 0/10 nos novos, antes da correção.
- `SHA256`: conjunto atual `3f69ee2a6827ba1eaeb614dd914803c88a82a6eda3e360489a805cb9d8640a28`.
- Os 25 anteriores preservam seu SHA
  `c75845b1488ea1539fc4c69c5f5ccd9e74280a3a67ef4af9360f062f28836c2d`
  e são comparados integralmente pelo avaliador.
- `candidato_intermediario.json`: conserva o resultado insuficiente de 31/35,
  incluindo duas recusas indevidas de comparação factual, antes da correção.
- `candidato.json`: replay final pelo adaptador padrão da API no código
  `af3c9e39b8cf7b8a783ebc6de2d290cfceb36a42`, com os modelos próprios já ativos.

| Critério | Antes | Candidato |
| --- | ---: | ---: |
| Peça correta com conteúdo verificado | 23/35 | 33/35 |
| Dez falhas acrescentadas | 0/10 | 10/10 |
| Respostas com desvio proibido | 9 | 0 |
| Trocas de domínio | 4 | 0 |
| Casos com referentes ausentes | 5 | 0 |

## Correção

O roteador resolve pessoas por nome ou vínculo declarado, pede esclarecimento
quando há dois primos e encaminha perguntas sobre preferências, gostos e
restrições para a memória existente. Uma ponte de linguagem registra declarações
e correções naturais com a fala original como fonte. Gostar, não gostar e
preferir permanecem relações distintas; nenhuma delas implica permissão.

A guarda confere a seleção de afirmações, a pessoa, a relação, a polaridade,
a fonte do usuário e a validade atual. Uma informação desconhecida não pode
virar uma preferência afirmada. Na comparação factual, exige as unidades
selecionadas inteiras e permite nomes de conceitos cujas palavras aparecem
separadas na evidência, como “céu” e “azul”. Não basta repetir um título.

Reservas de tempo com unidade explícita chegam ao calculador existente, com
fonte preservada. Pedidos factuais explícitos encerram o relato pessoal sem
perder a ficha de memória. Não há nomes, respostas ou IDs de avaliação
embutidos nas regras do motor.

## Regressão tardia do #121

`diagnostico_121.json` registra o job `testes (3.13, regressoes-b)`: 645 testes,
seis falhas, 37 skips. O catálogo fixo introduzido pelo roteador ignorava a base
da instalação e não registrava a continuação “Só isso?”. A rota agora usa
`conversa_assistente.capacidades`, preserva `social:assuntos` e compartilha o
estado social com o caminho anterior. Outro assunto expira essa continuação.
As expectativas de `testes_autoconversa.py` permanecem intactas; essa suíte
passa a integrar o check obrigatório `compreensao-chat`.

## Validação e limites

O avaliador exige no mínimo 33/35, todos os dez novos, zero desvios de domínio
e zero referentes ausentes. Não conta uma rota apenas por seu rótulo: confere
o executor, a guarda e o conteúdo entregue. Contratos adicionais injetam
respostas com pessoa, polaridade ou evidência incorretas e verificam a rejeição.
Também foram executadas as regressões existentes de autoconversa, memória,
realização e raciocínio. As execuções e seus resultados estão em `validacao.json`.

`real-19` e `real-20` continuam falhando na entrega de história com cinco frases
e na alteração do final. A guarda pede esclarecimento; isso evita desvio, mas
não recebe ponto por cumprir a tarefa. Os oito pedidos da coleta inicial fora
dos dez selecionados não entram na pontuação: as respostas brutas permanecem
disponíveis. Ainda há dificuldades observadas com gastos de tempo compostos,
declarações de restrição em outros formatos e sugestões sob restrições.

As novas relações literais de gosto usam a resposta estrutural quando o
realizador atual não suporta esse campo. Os campos nativos continuam no
caminho já existente. Não foram alterados o gerador, sua entrada, os pesos,
os parâmetros, o acervo ou as opções que ativam modelos.

## Reprodução

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_autoconversa testes_roteamento_natural testes_roteamento_natural_v2 -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/roteamento_natural_v2_20261009/avaliar.py --saida /tmp/roteamento-natural.json --exigir-meta
```

`verificar_site.py --commit COMMIT_PUBLICADO --saida ARQUIVO` reproduz os mesmos
casos por HTTP público, exige o commit esperado no health antes e depois e
usa os mesmos critérios. A medição local não substitui a confirmação do site.
