# Intenção e contexto antes das respostas cadastradas (05/10/2026)

Primeira etapa da ordem recomendada na revisão de 05/10: **corrigir intenção e
contexto** e **ligar ao chat módulos que já existiam** (investigação, cálculo e
raciocínio). Nenhum peso foi treinado ou alterado. O Transformer de 16 M continua
fora do chat público.

## O que mudou

Novo módulo `compreensao_intencao.py`, chamado por `Crivo._responder_comum`
logo depois do motor de código e antes do recuperador:

| Peça | O que faz | Onde entra |
|---|---|---|
| `EstadoConversa` | Guarda objetivos ("hoje quero terminar o relatório"), preferências ("prefiro explicações curtas") e restrições ("evite termos técnicos"). Objetivos são guardados em silêncio: a declaração continua sendo respondida pelo diálogo existente, que alimenta o planejador. Preferências e restrições recebem confirmação. Nas perguntas sobre esses dados, devolve as palavras do usuário entre aspas, seguindo a convenção do repositório. Sem dado guardado aqui nem no rastreador antigo, admite que não sabe em vez de escolher uma ficha. | Antes do recuperador |
| `aplicar` | Com preferência por respostas curtas, encurta explicações longas para duas frases e mantém a linha de fontes. | Depois da resposta |
| `calcular` | Aritmética em português: `30.000`, `2,5`, `−`, `×`, "vezes", "dividido por", "15% de 200", "raiz quadrada de 81". Usa uma AST restrita, sem `eval`, com limites para potências e divisão por zero. | Antes do recuperador |
| `Inferencia` | Modus ponens e modus tollens sobre premissas em linguagem comum ("Se chove, a rua fica molhada. Está chovendo."), aponta as falácias de afirmar o consequente e de negar o antecedente, e aceita premissas espalhadas por vários turnos. Reaproveita `SistemaPremissas` de `raciocinio_ativo`. | Antes do recuperador |
| `reformular_finalidade` | "Pra que a célula precisa da mitocôndria?", "Por que o DNA é importante?" e "Qual o papel do DNA?" viram "Para que serve X?". Só reformula quando X é exatamente um conceito com ficha. Sujeito e qualificadores são mantidos ("…mitocôndria **na célula**", "…**no Sol**"), e o motor existente recusa os contextos sem evidência. | Antes da preparação |
| `InvestigacaoChat` | Liga `investigacao_memoria.py` (laboratório) ao chat: faz as perguntas de maior ganho, interpreta respostas livres ("continua crescendo depois do GC"), compara hipóteses e cita fontes. Se o ambiente não for Node, avisa que está fora do escopo do modelo. | Antes do recuperador |
| `ConsultaPratica` | Relaciona perguntas práticas às fichas do acervo de programação, com sinônimos ("tempo de execução" = runtime, "garante" = valida) e peso por raridade do termo (IDF). Em caso de empate, prefere não responder. Abre com "Não." quando a definição nega exatamente o que foi perguntado. | Só quando o resto respondeu "fora" |

Também mudou:

- `pedidos_gerativos.criacao` separa o personagem nomeado do cenário. Em "um farol
  abandonado, com uma personagem chamada Lia", o personagem agora é **Lia**, e não
  "uma personagem chamada Lia".
- A memória opcional do navegador (`web_core`) aceita `objetivos`, `preferencias`
  e `restricoes`. Assim esses dados passam da janela de 10 mensagens do replay.
  Memórias antigas continuam válidas.

## Antes e depois

As consultas do relatório foram reproduzidas localmente pelo mesmo `responder_web` do site:

| Consulta | Antes (main `8ab7fbf`) | Depois |
|---|---|---|
| Pra que a célula precisa da mitocôndria? | "não entendi" | função da mitocôndria (ATP) |
| Hoje eu quero terminar o relatório… → O que eu quero fazer hoje? | previsão do tempo | "Você me disse que quer “terminar o relatório de vendas”." |
| Prefiro explicações curtas… → Como eu prefiro as explicações? | "não entendi" | preferência lembrada e aplicada |
| Uma interface do TypeScript valida um JSON em tempo de execução? | "não entendi" | "Não." + ficha de apagamento de tipos com fontes |
| Quanto é 30000 − 15000? | "não entendi" | `30.000 - 15.000 = 15.000` |
| Se chove, a rua fica molhada. Está chovendo. O que acontece com a rua? | "não entendi" | conclusão com premissas e modus ponens |
| Se chove, então a rua molha. Chove. A rua molha? | resposta sobre **regar plantas** | "Sim", com as premissas |
| Se eu treino, fico mais forte. Eu não fiquei… Eu treinei? | "Ainda não interpreto essa negação" | "Não", modus tollens |
| Meu programa está consumindo cada vez mais memória | "não tenho evidência" | investigação guiada |
| História com "uma personagem chamada Lia" | instrução virou nome | Lia como personagem |

### Medição em frases que não foram usadas no desenvolvimento

| Lote | main | branch | Observação |
|---|---|---|---|
| Lote 1 (26 frases, 5 controles negativos) | 9/26 | 25/26 (era 26/26 antes da correção do qualificador; ver limites) | Na primeira medição deu 23/26, e a inspeção manual achou mais erros. Corrigi com regras gerais (radicais verbais, premissas em turnos, IDF), então este lote **deixou de ser inédito**. |
| Lote 2 (16 frases, escritas depois) | 6/16 | 15/16 → 16/16 | A primeira medição, antes de qualquer ajuste, deu 15/16. A inspeção manual achou 4 defeitos (pronome "minha", "gosto **das** explicações", "trabalhar em aprender", "peix**e** chamado), que foram corrigidos depois. O pronome agora segue a convenção existente: citação literal entre aspas. |

O número honesto de generalização é a **primeira** medição de cada lote. Os dois
lotes agora estão em `testes_compreensao_intencao.py` como regressão. A próxima
entrega precisa de um lote 3 novo, medido antes de qualquer ajuste.

### O que não mudou

- `crivo.py --teste`: 65/65 na main e na branch.
- Sondas do CI (`avaliar_conversacao`, `avaliar_mundo`, `avaliar_bate_papo`,
  `avaliar_geracao`, `avaliar_ampliacao`, `avaliar_retomada`,
  `avaliar_evolucao_integrada`, `avaliar_generalizacao --split validacao`): JSON
  numericamente idêntico entre main e branch.

## Limites conhecidos (não resolvidos aqui)

- **Escrita:** o personagem e o cenário agora chegam certos, mas a trama continua
  genérica ("recebeu uma mensagem sem assinatura…"), porque a GRU de 16 operações
  trabalha sobre poucos moldes. A coerência narrativa precisa de outro gerador e
  de verificação.
- **Inferência:** cobre condicionais simples (uma condição por regra) e negação. Não
  cobre quantificadores ("todo", "algum"), que continuam com o grafo relacional, nem
  tempo ou probabilidade. A conclusão usa a pessoa gramatical das premissas ("eu acordo").
- **Investigação:** só o modelo de heap JavaScript no Node. Para Python, RSS e
  outros ambientes, o chat diz que estão fora do escopo; ainda não há modelo para eles.
- **Objetivos e planos:** o planejador antigo ainda não usa os objetivos com marca de
  tempo ("hoje quero…"). Isso já acontecia na main; "Me ajude a organizar meu objetivo"
  pede o objetivo de novo. Unificar os dois rastreadores é a próxima integração.
- **Objetivos:** reconhece formas explícitas ("quero/preciso/vou + verbo", "minha
  tarefa é", "estou trabalhando em"). Planos implícitos ou negociados ao longo da
  conversa não são detectados.
- **Conhecimento técnico:** a consulta prática depende das fichas existentes, cuja
  revisão editorial continua pendente. O "Não." inicial é uma heurística sobre a
  definição, não uma prova.
- **Paráfrase com contexto:** como o sujeito vira qualificador, "Pra que a planta precisa
  da clorofila?" fica sem resposta. O motor recusa "clorofila na planta" por falta de
  evidência para esse contexto. É uma perda deliberada: apagar o contexto fazia "Qual é o
  papel da mitocôndria no Sol?" responder sobre ATP (falha pega pelo CI).
- Achado lateral: "Qual a função do coração?" ainda responde sobre partes da
  planta, um falso positivo do recuperador que fica para a próxima rodada.

## Próximos passos sugeridos

1. Lote 3 de frases inéditas e conversas completas, medido no site publicado antes
   de qualquer ajuste.
2. Programação: compor operações (remover duplicados → ordenar → pegar os k
   menores) com execução e casos de verificação independentes.
3. Revisar os 461 diálogos humanos (259 fora da janela no piloto) antes de outro
   treino longo.
4. Expor no JSON da API qual módulo respondeu de fato (`mechanism` já mostra
   `estado_conversa`, `calculo`, `inferencia_linguagem_comum`,
   `investigacao_guiada` e `consulta_pratica`). `neural_active` continua indicando
   só que a rede de classificação foi carregada.
