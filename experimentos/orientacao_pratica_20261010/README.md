# Orientação prática — 10/10/2026

O site publicado do #129 lembrava objetivos, mas falhava em dar o primeiro
passo, corrigir o desenho ou explicar um exercício. As três sessões de seis
turnos (desenho, estudo e horta) foram executadas no HTTP público, preservadas
em `evidencias/site129.json` e congeladas antes da mudança. São sondas
autorais do agente, não sessões de participantes humanos ou transcrições do dono.

## Medição e reprodução

`casos_congelados.json` conserva os 61 casos anteriores integralmente e
acrescenta os 18 turnos observados. `SHA256` protege o conjunto. Os cinco
turnos que já reconheciam corretamente objetivo, restrição ou memória
continuam aceitando o executor anterior; não contamos esses acertos como
orientação concreta. Os outros 13 exigem orientação e conteúdo específico.

A linha de base em `baseline_motor.json` tem **66/79** no total e **5/18**
nos novos casos. As três sessões práticas reprovaram no conjunto: lembrar
o objetivo não compensava a falta de ajuda. O relatório final registra a
avaliação depois da mudança no motor e em HTTP real, e a revisão das respostas.

Resultado final: **79/79 nos dois caminhos, 18/18 novos**, zero troca de
domínio e referente ausente. As dez sessões anteriores mantêm seus critérios
restritos nos dois caminhos; a revisão das três sessões práticas no motor
passa de **0/3 para 3/3** com ajuda/esclarecimento pertinente. Os 50 contratos
passaram; os nove novos foram repetidos após a correção de localização da horta.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/orientacao_pratica_20261010/avaliar.py --modo motor --saida /tmp/pratica-motor.json --exigir-meta
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/orientacao_pratica_20261010/avaliar.py --modo http --saida /tmp/pratica-http.json --exigir-meta
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/orientacao_pratica_20261010/sondar.py --modo motor --saida /tmp/pratica-sessoes.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_orientacao_pratica -v
```

O avaliador verifica peça executada, conteúdo mínimo, referências e desvios;
reproduz ainda as dez sessões anteriores com seus critérios restritos.
Esses critérios e buscas lexicais não certificam conversa humana geral.
A leitura das três sessões novas avalia ajuda concreta, não apenas memória.

## Mudança

`orientacao_pratica.py` lê o objetivo, as declarações literais e o trace da
tarefa no histórico existente. Não cria uma nova memória. Só recebe os
pedidos que os executores específicos anteriores não reconheceram.

- Desenho: proposta de oval para peixe, passo seguinte condicionado à
  forma relatada e ajuste da cauda; material e tempo declarados acompanham
  a resposta. Sem borracha, não manda apagar.
- Estudo: pergunta o tópico quando falta. Se frações foram declaradas,
  propõe exercício, explica com denominador comum, reformula com partes
  de uma figura e confere a resposta usando `Fraction`. A expressão do
  exemplo anterior é preservada. Sem exercício conhecido, pede a conta.
- Horta: dá uma ação observável para hoje e pede luz, espaço, vasos e
  objetivo antes de escolher plantas. Ausência hipotética de sol não
  vira uma observação nem uma garantia de cultivo.

A guarda verifica objetivo com fonte no usuário, restrição de material e
conversões/resultados exatos. Cancelamento, nova tarefa ou pergunta factual
suspendem o objetivo anterior. Fatos, fontes, cálculo e escrita mantêm seus
executores e guardas. A origem autoral das orientações é explícita quando
perguntada; não se inventa uma referência do acervo.

Trace: `peca=orientacao`, ato e quadro prático, declarações usadas,
hipótese e `gerador_neural_usado=false`. A política é `orientacao_contextual`.
Os exemplos numéricos são propostas autorais, não números pessoais inferidos.

## Limites

É orientação estruturada autoral em três tarefas restritas. Não houve
treino, aumento de parâmetros, alteração de pesos, novo acervo ou uso de
modelo externo. A GRU própria de **85.581 parâmetros** continua ativa
somente nas rotas de escrita já aprovadas; não gera estas orientações.

Não demonstra planejamento geral, tutoria matemática ampla, diagnóstico de
um desenho ou aconselhamento horticultural completo. O início do desenho é
principalmente de peixe; outros desenhos recebem orientação genérica e uma
pergunta. Frações aceitam soma/subtração de duas frações com denominadores
não nulos e até quatro dígitos por componente; outras formas podem exigir
esclarecimento. A horta não tem um plano de cultivo: precisa primeiro de
condições reais. A leitura do histórico é limitada a vinte mensagens, com
formatos explícitos para objetivos, tempo, vasos e correções de material.

O job existente de roteamento passa a verificar os nove contratos e os
79 casos por HTTP real. A matriz completa permanece manual/semanal.
Publicação requer checks relevantes verdes e replay do commit no site.
