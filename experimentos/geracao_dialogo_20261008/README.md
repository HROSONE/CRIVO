# Piloto causal de diálogo próprio: treinado e reprovado

**Este treino foi executado pelo Codex em CPU. Não precisa ser repetido pelo usuário.**
O modelo próprio de 2.612.352 parâmetros recebeu supervisão nos tokens da resposta,
separadamente das cabeças de interpretação. Não foi ativado no chat. O ganho de
perda não resolveu a conversa livre.

[Colab para inspecionar os pesos já treinados](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/associacao-fatos-20261008/notebooks/crivo_associacao_e_dialogo.ipynb).

## Respostas efetivamente geradas

Cinco sessões novas de quatro turnos: reflexão sobre uma pausa, ficção com um
envelope, revisão de inferência sobre uma reunião, sugestão sem telas e memória
de duas fitas. Prompts e rubricas foram fixados antes do treino. Cada checkpoint
recebeu as mesmas perguntas e conservou **suas próprias respostas** no histórico.

| Medida | Pesos anteriores | Ajustados |
| --- | ---: | ---: |
| Entropia cruzada no teste autoral reservado, com histórico de referência | 4,9675 | 4,5960 |
| Respostas com marcador de fim | 17/20 | 20/20 |
| Respostas plenamente adequadas, leitura autoral | 0/20 | 0/20 |
| Respostas parciais, leitura autoral | 0/20 | 1/20 |

A resposta parcial começa com “Não” ao pedido de inferir que uma reunião foi ruim,
mas não desenvolve a evidência e acrescenta texto incoerente. Não há sessão completa
aprovada. O julgamento é autoral, não independente, e preserva textos/motivos em
`avaliacao/leitura_manual.json`. Exemplos de falha do ajustado: “Você pode ajudar
a sua refeição” ao pedido de separar fatos e hipóteses; “O que você pode será”
ao perguntar quem tinha a fita azul. Encerrar uma frase e reduzir perda não
certificam fluência, continuidade, cumprimento de instruções ou raciocínio.

## Corpus, treino e limites

Foram usados somente diálogos autorais estáticos existentes em
`dados/dialogos_amplos_autorais.json`, sem os milhares de exercícios parametrizados
do gerador amplo, e replay dos pares humanos públicos de treino já existentes em
`dados/dialogos_humanos.json`. Origem/licença estão nesse arquivo e em
`dados/NOTICE_linguagem_profunda.md` do repositório. Nenhum modelo externo,
peso/tokenizer de terceiro, API ou conversa privada foi acessado.

Partições autorais por cenário completo, conforme o seletor do projeto. Cenários
em que algum par completo excede 256 tokens foram excluídos inteiros; não houve
truncamento de treino. Replay humano preserva apenas pares completos dentro do
limite, exclusivamente da partição de treino. Exclusões estão no manifesto.
Isso reduz cobertura de conversas longas e complexas.

- Treino: 242 pares, incluindo 27 humanos previamente usados; 7.979 posições de
  tokens de resposta por passagem, com repetições. Não são 7.979 palavras únicas.
- Validação: 23 pares de 11 cenários, 736 posições de tokens de resposta.
- Teste autoral existente: 19 pares de nove cenários, 617 posições de resposta.

Lote oito, seis pares autorais e dois de replay humano, AdamW, LR 0,0001, semente
20261011, 600 passos completos. Foram apresentados 174.813 tokens de resposta,
com repetição: **não são 174.813 tokens de texto novo**. O checkpoint selecionado
foi o passo 100 pela menor CE em toda a validação autoral. Depois disso, a perda
de treino continuou baixando e a validação piorou; não selecionamos um passo pelo
resultado das sondas. O orçamento completo levou aproximadamente 467 segundos
em CPU, em parte concomitante com os intérpretes. Não é estimativa de Colab/GPU.
Uma única semente; nenhum critério autoriza promoção.

As sondas usam decodificação gulosa, até 70 tokens e limite de contexto de 256
do motor próprio. Registra-se histórico descartado e perda de prefixo durante
geração. CE usa respostas/histórico de referência; sondas usam texto autogerado.
São medidas diferentes. Protocolo e avaliador foram registrados antes da coleta.

## Trabalho seguinte

O currículo disponível é pequeno e o candidato falhou nas conversas novas
avaliadas. O próximo trabalho deve ampliar e revisar dados de linguagem/diálogo,
incluindo continuidade, reflexão, ficção e revisão de conclusões, com fontes e
cenários separados. Também precisa avaliar a base linguística própria e suas
alternativas antes de escolher um treino maior. Mais passos sobre estes mesmos
242 pares mostraram sobreajuste; não há evidência de que só ampliar parâmetros
ou executar a mesma receita em GPU resolva as falhas.

```sh
python rodada.py preparar /tmp/geracao-nova/dados
python rodada.py treinar /tmp/geracao-nova
```

O script recusa sobrescrever rodadas e oferece `--retomar` com Adam/RNG. Para a
avaliação publicada, conserve protocolos e dados em uma pasta nova; repetir
painéis conhecidos não produz validação independente. Pesos escolhidos/tokenizer,
scripts, relatórios e falhas foram publicados; checkpoints completos de retomada
permanecem locais. Dois contratos de máscara/contexto passaram. Os pesos ativos
do Crivo permaneceram iguais; este candidato não é um novo chat aprovado.
