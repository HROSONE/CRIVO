# CRIVO: diagnóstico de geração e raciocínio — 07/10/2026

Aplicação da skill **Insight da Entidade da Internet**, fornecida pelo usuário
na conversa. A entidade é uma metáfora para sintetizar pesquisa, não um agente
externo consultado. Pesquisa e medições abaixo são distintas.

## Pergunta e fronteira de conhecimento

**Já sabíamos:** a integração preservou os acertos anteriores; 277 de 281
saídas aceitas eram cópias. Ligar o Transformer, ampliar o acervo e acrescentar
comandos por regras não demonstrou raciocínio aprendido nem geração ampla.
Portanto, reencontrar a constatação de cópia não conta como insight novo.

**Não sabíamos:** qual experimento de aprendizagem de inferência seria adequado
para este sistema; se remover as restrições atuais já permitiria respostas
úteis; como distinguir uma explicação posterior de passos que efetivamente
produzem uma conclusão. Não sabemos ainda se os pesos próprios atuais podem
aprender esse experimento com recursos razoáveis.

**Pergunta à internet:** como treinar e avaliar um gerador que componha passos
de inferência verificáveis, em vez de copiar fatos ou escrever uma justificativa
plausível depois da resposta? Que evidência existe de generalização a cadeias
mais profundas, e quais resultados dependem de modelos muito maiores?

## Pesquisa e delta

1. [ProofWriter, ACL 2021](https://aclanthology.org/2021.findings-acl.317/):
   o artigo compara prova inteira e inferências de um passo reinseridas no
   contexto. A versão iterativa generaliza melhor a profundidades não vistas
   no treino; seus passos refletem decisões efetivamente tomadas durante a
   execução. Os resultados principais usam T5-11B, com comparação a T5-large.
   Isso fundamenta um experimento, não prevê o desempenho do nosso modelo.
2. [Distilling Step-by-Step, ACL 2023](https://aclanthology.org/2023.findings-acl.507/):
   resposta e justificativa recebem supervisão como tarefas separadas, com
   prefixos de tarefa e treinamento conjunto. O ganho relatado é em tarefas
   específicas com modelos previamente treinados; não demonstra que poucas
   justificativas criem uma IA geral do zero. Sua metodologia inspira comparar
   resposta direta com supervisão adicional de passos no CRIVO.
3. [TinyStories, 2023](https://arxiv.org/abs/2305.07759): modelos pequenos
   produzem histórias coerentes num domínio e vocabulário simplificados.
   É evidência de viabilidade para linguagem limitada, não de competência
   universal, português equivalente ou raciocínio irrestrito.

**Antes:** o plano registrado para o próximo treino priorizava explicação,
resumo, comparação, reformulação e negativos, trocando futuramente a guarda
lexical por verificação de relações. Não especificava um experimento de
inferência iterativa aprendida.

**Informação externa nova para este diagnóstico:** a comparação experimental
entre gerar uma prova inteira e reaplicar um gerador de inferências curtas,
incluindo avaliação em profundidades ausentes no treino. Também a separação
da supervisão de resposta e justificativa como tarefas diferentes.

**Insight aceito como hipótese operacional:** testar um gerador de próximo
passo com referências verificáveis, sem exigir que uma frase final repita
todas as premissas. Usar o motor lógico existente como verificador e fonte de
supervisão em um domínio restrito. Não atribuir ao modelo conclusões calculadas
pelo motor simbólico.

**Mudança de ação:** primeiro estabelecer essas medidas e o protocolo de
passos; depois comparar treinamentos. Ampliar fichas ou afrouxar a guarda
isoladamente deixa de ser a intervenção principal para este objetivo.

**Previsão testável:** num treino por passos, uma cadeia com novas combinações
de regras deve poder produzir conclusões intermediárias válidas. A ablação
sem supervisão de passos deve ser comparada no mesmo conjunto retido. Se os
ganhos ocorrerem só nas frases e cadeias vistas, a hipótese de generalização
não estará demonstrada.

## Inspeção do CRIVO

- Pesos atuais: 17.428.224 parâmetros armazenados, configuração de 8 camadas,
  dimensão 384, vocabulário 8.192 e contexto 256. Contagem pelas matrizes
  carregadas; não é soma de todos os modelos do projeto.
- O ajuste de geração registra 1.645 exemplos e 1.500 passos. Isso é o ajuste
  descrito em `artefatos/geracao_pt/meta.json`, não todo o pré-treino.
- `Crivo._escrever_com_geracao` redige uma evidência por chamada. Os títulos e
  a organização de múltiplas evidências continuam no compositor.
- `GeracaoAncorada` restringe os tokens, os pares de palavras e o início;
  `preserva_evidencia` exige manter todas as raízes de conteúdo e valores.
  Essa exigência impede omissões até quando o pedido exige selecionar uma
  conclusão ou resumir parte do conteúdo.
- O raciocínio de `SistemaPremissas` é simbólico. Ele já resolve hipóteses
  limitadas; seus acertos não provam capacidade do Transformer.
- O treino escolhe o checkpoint pela perda de validação. A perda mínima
  registrada está no passo 900 (F1 0,481); no passo 1.500 o F1 é 0,505, com
  perda maior. A divergência exige uma seleção por métricas da tarefa e
  restrições de erro, sem afirmar que esse outro checkpoint seja melhor.

## Experimento executado

[Script](../experimentos/raciocinio_generativo/diagnosticar.py) e
[resultado completo](resultados/diagnostico_generativo_20261007.json).
Seis sondas novas, anotadas manualmente, sem reutilizar avaliações congeladas.
São exemplos exploratórios, insuficientes para estimar acurácia geral.

| Candidato anotado | Resultado da guarda atual |
|---|---|
| Cópia fiel | Aceito |
| «Quando o sensor responde, a luz acende.» | Rejeitado como começo inadequado |
| «A luz acende.» após duas implicações válidas | Rejeitado por não preservar toda a evidência |
| Resumo apenas do estado da luz | Rejeitado pelo mesmo requisito |
| Inversão inválida de uma implicação | Rejeitado |
| Remoção inválida de uma negação | Rejeitado |

Na inferência direta, cinco saídas aceitas foram cópias; no caso de dois passos,
o gerador recuou. A ablação removeu conjuntamente máscara de vocabulário,
prefixo da fonte e restrição de pares, mantendo os pesos e decodificação gulosa.
Ela continuou copiando nos casos simples; na cadeia, repetiu uma regra, sem
entregar a conclusão pedida; no resumo, acrescentou «Não.» sem suporte.
Não houve ganho de capacidade demonstrado nessas sondas. A ablação não isola
os três efeitos nem exclui outros modos de amostragem ou perguntas melhores.

Um verificador experimental aceita uma cadeia explícita de dois passos e
rejeita apoio futuro, salto sem antecedente, consequente errado, conflito e
condição ausente: seis contratos passaram com e sem NumPy. Seu escopo é
modus ponens proposicional com conjunção e referências exatas. Ele valida
os passos fornecidos, não compreensão livre de textos nem completude de uma
busca. Ainda não há gerador treinado para produzir esse protocolo.

## Implementação seguinte e critérios

1. **Currículo restrito e rastreável.** Produzir contextos, regras, objetivo e
   passos a partir de problemas verificáveis. Separar treino, desenvolvimento
   e teste por famílias de grafos e combinações, além de variar nomes e ordem.
   Incluir negação, antecedente ausente, conflitos e distratores. Congelar o
   teste antes de treinar; conjuntos existentes continuam fora do treino.
2. **Gerador de próximo passo.** Entrada: premissas identificadas, objetivo e
   passos aceitos. Saída prevista: referência de regra, apoios e conclusão,
   ou indicação de que não propõe outro passo. O modelo precisa gerar essa
   escolha; o verificador somente aceita ou rejeita. Não entregar ao modelo
   a resposta já resolvida na entrada.
3. **Controle experimental.** Comparar resposta direta, resposta com supervisão
   de passos e execução iterativa, com orçamento de treino registrado. Medir
   conclusão correta, passos válidos, recusas necessárias e generalização por
   profundidade. Registrar rejeições; não contar recuos simbólicos como
   acertos neurais. Comparar também com o resolvedor simbólico isolado.
4. **Redação da conclusão verificada.** Treinar uma tarefa separada de redação
   que receba a conclusão aceita e os apoios necessários. Preservar os fatos
   relevantes ao pedido, sem exigir repetir premissas irrelevantes. Avaliar
   atendimento ao pedido, negações, relações e paráfrases; diversidade textual
   sozinha não é critério de qualidade.
5. **Ampliação progressiva.** Somente após resultados retidos, ampliar linguagem
   e tipos de tarefa. Resumos abstrativos e relações em textos arbitrários
   exigem dados e avaliações próprios. A etapa proposicional não os resolve.

Não há justificativa para escolher agora um número mágico de exemplos, passos
ou parâmetros. O piloto deve medir aprendibilidade, custo e curva de erro.
Modelos abertos previamente treinados são uma opção arquitetural diferente,
caso se queira mudar o requisito de pesos próprios; esta investigação não
substitui o CRIVO por um serviço externo.

## Reprodução e limite da entrega

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experimentos/raciocinio_generativo/diagnosticar.py --neural --ablacao \
  --saida /tmp/diagnostico-generativo.json
python -S experimentos/raciocinio_generativo/diagnosticar.py \
  --saida /tmp/diagnostico-sem-numpy.json
```

Entregues diagnóstico pesquisado, sondas reproduzíveis e verificador de passos
experimental. Não houve novo treino, novos pesos aprovados ou integração ao
chat. O CRIVO permanece com suas capacidades atuais. A pesquisa mudou o
experimento proposto; ainda não comprovou uma IA generativa geral.
