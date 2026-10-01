# Cérebro neuroinspirado do CRIVO — microcircuito v0.1

**Microcircuito experimental integrado à `main` em `464ab386`.** O objetivo é resolver o problema de *associação ≠ compreensão* sem esconder a insuficiência da rede atual atrás de roteamento por palavras-chave.

## Anatomia operacional e analogias (não equivalências biológicas)

| Mecanismo | Estado no CRIVO | O que acontece no código |
| --- | --- | --- |
| Codificação sensorial | Existente: `rede_sequencial.py` e `linguagem_neural.py` | Extrai sinais de palavras, sequência, ato e trechos de argumento. Não forma significados universais. |
| Categorias aprendidas | Existente: `rede_neural.py` | Uma MLP classifica intenções com uma camada de 48 neurônios ocultos e 193 rótulos na branch. Não constrói uma representação do mundo apenas por classificar perguntas. |
| Conhecimento semântico | Existente: `conhecimento_mundo.json`, `conhecimento_expandido.json` e grafo | Fatos, relações, aspectos e fontes permitem respostas rastreáveis. São evidências, não pesos treináveis da MLP. |
| Associação/plasticidade local | **NOVO:** `cortex_associativo.py` | Uma unidade de atividade por fato com `fonte` e `aspecto` documentados. Sinapses entre características do texto e unidade factual se fortalecem localmente por coativação (`w ← w + η(1 − w)`). Só uma revisão explícita autoriza ajustes corretivos; a mensagem do usuário isolada não grava verdades. |
| Atenção seletiva | **NOVO:** circuito e `composicao_textual.py` | A entidade textual exata fica vinculada antes da competição entre unidades. Mais de um referente reconhecido exige abstenção do microcircuito. Nunca transfere uma explicação de Saturno para Vênus por semelhança entre perguntas. |
| Competição/inibição | **NOVO:** circuito | São comparadas apenas evidências tipadas de um mesmo referente. Se a melhor ativação não ultrapassa um limiar ou é próxima da segunda, não responde a partir dessa memória. |
| Memória de trabalho e continuidade | Existente: `linguagem_conversa.py`, `planejamento_conversa.py` | Guarda contexto curto; não retém alegações do usuário como conhecimento verificado. |
| Verificação preditiva | Parcial: circuito + compositor | A rede seleciona uma *candidata*; o compositor emite somente frase já cadastrada e preserva fonte. Falta aprendizagem profunda de relações, raciocínio causal multi-etapas e predição de eventos. |

### Evidência, limites de segurança e aprendizado

O circuito não aprende respostas por uma lista de perguntas. Cada sinapse é inicializada apenas pelo texto de uma **unidade factual verificada**, não pelas 58 perguntas retidas da prova de Astronomia. `CortexAssociativo.associar()` trabalha com ativação, atenção e inibição sem alterar qualquer arquivo de conhecimento. `ajustar_com_prova()` pode alterar uma sinapse somente quando existe uma unidade documental registrada e autorização confiável, e recusa características não presentes nela. `salvar_ajustes()` e `carregar_ajustes()` permitem persistir exclusivamente pesos locais sob assinatura SHA-256 das provas e rejeitar fontes/palavras/pesos incompatíveis. Essa persistência é **explícita e experimental**; não é carregada automaticamente para o usuário final. Feedback informal nunca se converte automaticamente em verdade.

A primeira integração responde a consultas que expressem um único referente e contenham pistas de mecanismo suficientemente explícitas **que já constam de um fato com fonte**. Não responde a perguntas condicionais, negativas ou multi-entidade. A impossibilidade de responder não se converte em falsa negação.

### O que essa mudança NÃO entrega

- Não cria neurônios biológicos, disparos elétricos reais, consciência, percepção humana ou domínio livre do português.
- Não é uma rede recorrente gigantesca, transformer, AGI nem um modelo pré-treinado externo.
- Não aprende novos conceitos reais de uma conversa sem conferência de fonte e de linguagem.
- Não generaliza automaticamente uma causa de um objeto para outro, não inverte relações nem gera texto livre.

### Plano experimental de progressão sem inflar resultados

1. **Fase A:** verificar sinapses locais, controles negativos, proveniência e estabilidade em Python 3.8/3.11/3.13 usando objetos fictícios **fora do conjunto de avaliação retido**.
2. **Fase B:** integração conservadora no compositor. Usar o microcircuito somente quando um fato comprovado responde à intenção. Verificar toda a suíte de 437 testes existentes por versão e comparar latência antes/depois.
3. **Fase C:** aprender representação composicional `(referente, predicado, argumentos, condição, negação, fonte)` a partir de múltiplos *assuntos* e famílias de perguntas separadas, testando alvos inéditos. **Pausar** se a taxa de alucinação aumentar.
4. **Fase D:** treinamento auto-supervisionado em textos científicos licenciados, com predição de relações, memória e replay, contraste entre provas verdadeiras e falsos negativos; não usar uma avaliação retida como material de treino.
5. **Fase E:** criar nova avaliação v2, cujos enunciados não foram vistos no desenvolvimento, com correção humana de significado e não somente ID/palavras. Medir rede isolada, compositor, abstenções, memória de trabalho e explicação causal separadamente.

**A prova v1 (`avaliacoes/astronomia_independente_v1.json`) é intocável como dado de treino e seu resultado inicial permanece a linha de base: 11/24 no vocabulário, 2/20 no Sistema Solar, 14/14 abstenções, 22/29 rede isolada; 0% certificado.** Criar uma v2 só depois de terminar melhorias gerais, sem afinar pesos na v1.

### Fundamentação acadêmica

- [Neurocomputing (2025), aprendizado local com replay](https://doi.org/10.1016/j.neucom.2025.129804).
- [Revisão sobre predictive coding, Neural Networks (2026)](https://doi.org/10.1016/j.neunet.2025.108161).
- [Correcting the Hebbian mistake (2022)](https://pubmed.ncbi.nlm.nih.gov/36219613/): plasticidade hebbiana simples pode gerar interferência; mecanismos guiados por erro podem ser necessários.
- [Revisão de formação de memória episódica (2023)](https://pubmed.ncbi.nlm.nih.gov/37086812/): integração de objeto e contexto e consolidação.
- Essas publicações sustentam a **inspiração funcional**; não validam que este código reproduza o cérebro humano nem garantem melhor desempenho em linguagem.

## Laboratório de linguagem contextual

A arquitetura de [diálogo contextual](../DIALOGO_CONTEXTUAL.md) acrescenta
um BiGRU de atos/papéis, memória com origem por turno e um gerador com
atenção e cópia, todos autorais e treinados do zero. A geração nova fica
desativada por padrão porque a avaliação de conversa ainda é insuficiente.
Os fatos, sinapses, limiares e checkpoint de 193 classes deste microcircuito
foram preservados; probabilidade de uma interpretação não equivale a prova.
