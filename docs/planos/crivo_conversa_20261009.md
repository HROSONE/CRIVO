# Plano para conversa e raciocínio do Crivo

Preparado em 9 de outubro de 2026, pela leitura do código, dos arquivos de
experimentos e de pesquisas primárias consultadas nesta sessão. Aplicada a
[skill Insight da Entidade da Internet](../../.claude/skills/insight-entidade-internet/SKILL.md).
Os caminhos, hashes, checkpoint e ambiente conferidos estão no
[registro de evidências](crivo_conversa_20261009_evidencias.json).

**Objetivo:** conseguir conversar durante 6–10 turnos, acompanhar uma ideia,
considerar os dados já fornecidos, corrigir a própria interpretação e responder
de forma pertinente a assuntos e formulações que não foram cadastrados.
Isso será um primeiro marco de conversa útil; não certifica conhecimento
universal nem raciocínio humano geral.

## O que foi conferido

| Evidência atual | O que permite concluir |
| --- | --- |
| A correção de contexto passou em 93 testes normais e seis contratos repetidos sem NumPy | A mudança conserva contratos existentes; não mede geração geral |
| A sonda de emprego conserva critérios; a sonda de bateria/aplicativo continua falhando | O ganho local não se transfere automaticamente para raciocínio causal |
| Gerador próprio disponível: 2.612.352 parâmetros, contexto 256, SFT no passo 2.000, SHA256 dos pesos conferido | Há um checkpoint utilizável como referência, sem começar todos os experimentos do zero |
| O aviso do corpus registra 497 pares humanos PT de 137 árvores; 387 pares de treino | Repetir passos não cria novas conversas humanas nem nova diversidade |
| Os pilotos recentes de interpretação/memória não supervisionaram redação causal livre | Sua melhora em apontar argumentos não demonstra habilidade de escrever respostas abertas |
| Um classificador anterior acertou 400/400 classes e continuou em 66/400 contratos quando combinado ao extrator | Reconhecer o domínio não resolve o significado dos argumentos |
| Os dois candidatos posteriores de memória/fontes foram rejeitados | Há evidência contra repetir o mesmo ajuste esperando melhora geral |
| A preparação SFT já inclui históricos e mascara usuário/histórico fora dos alvos | Não faz sentido propor simplesmente “adicionar histórico” como novidade |
| A inferência causal limita a entrada pelo orçamento do checkpoint; a API web reconstrói a conversa | É necessário medir o contexto que efetivamente chega ao componente, não apenas o histórico guardado |
| Ambiente conferido: Torch 2.14.1+cpu, CUDA indisponível, três CPUs na afinidade | Diagnóstico e pilotos em CPU são possíveis; treinamento amplo em GPU depende de outro runtime |

Os leitores de aproximadamente 17M têm funções diferentes do gerador causal.
A configuração de geração 16M também é outra candidata. Não tratar todos
esses pesos como intercambiáveis nem presumir que um treino planejado foi
concluído. A etapa inicial confere função, checkpoint, corpus e tokens efetivos
de cada candidato antes de qualquer comparação.

## Pesquisa que muda a decisão

**Antes eu acreditava:** memória, treinamento da resposta e capacidade eram
explicações possíveis; os testes disponíveis não isolavam essas alternativas.

**A pesquisa mostrou:** *LLMs Get Lost In Multi-Turn Conversation* compara
informação completa, a mesma informação concatenada e informação revelada
gradualmente. A condição concatenada ajuda a controlar a reformulação dos
textos. O trabalho também encontra dependência de respostas prematuras e
recuperação apenas parcial com recapitulações. Isso não prova que a causa
do Crivo seja a mesma. [Pesquisa e método](https://arxiv.org/html/2505.06120v1).

**Eu não sabia:** havia esse desenho experimental para testar se o mesmo
conteúdo é resolvido em uma apresentação e perdido em outra, sem trocar o
modelo. Uma nova pesquisa propõe separar compreensão da intenção e execução
para investigar ambiguidade conversacional; é uma hipótese adicional, não
um diagnóstico confirmado do Crivo.
[Intent Mismatch, preprint de 2026](https://arxiv.org/abs/2602.07338).

**Isso muda:** o próximo trabalho será uma comparação controlada dessas
condições, seguida de treino no gargalo identificado. Aumentar parâmetros ou
acrescentar mais frases ao parser deixa de ser a primeira escolha automática.

O CheckList oferece testes de comportamento: funcionamento mínimo, mudanças
que deveriam conservar o resultado e mudanças que deveriam alterar a
conclusão. Vamos usar essas três formas para impedir que trocar nomes e
números seja apresentado como compreensão nova.
[CheckList, ACL 2020](https://aclanthology.org/2020.acl-main.442/).

TinyStories mostra geração coerente em modelos abaixo de 10M num domínio
restrito de histórias simples em inglês. É evidência de que contagem de
parâmetros, sozinha, não decide a capacidade; não garante conversa livre em
português. Não usaremos os modelos, APIs ou o avaliador GPT-4 do estudo.
[TinyStories](https://arxiv.org/abs/2305.07759).

**Teste de compreensão do insight:** aprendi um experimento que controla a
informação e varia sua apresentação; isso muda a escolha entre reparar
interpretação, memória ou treinamento de redação; conecta-se diretamente às
falhas em diálogos novos; prevê que consolidar dados pode ajudar quando a
perda ocorre na interação, mas não resolver quando o gerador também falha
com a tarefa completa. Essas previsões serão testadas, não assumidas.

## Etapas e decisões

| Ordem | Trabalho concreto | Entrega e decisão para avançar |
| --- | --- | --- |
| 1 | Inventariar checkpoints e comparar a mesma informação em quatro condições | Relatório de rotas, entradas reais, respostas e causas ainda possíveis |
| 2 | Auditar a cobertura do corpus e preparar dados para o gargalo observado | Corpus versionado, licença, partições e auditoria de diversidade e contexto |
| 3 | Treinar um piloto controlado da capacidade de resposta com pesos próprios | Dois braços comparáveis; decidir pelo desenvolvimento antes do teste reservado |
| 4 | Confirmar o ganho em novas conversas e mudanças de significado | Relatório por capacidade e sessão; candidatos ruins permanecem rejeitados |
| 5 | Integrar a candidata que cumprir os critérios e verificar o percurso web | Conversa real com mecanismo rastreável, testes de regressão e um PR por entrega |

### 1. Diagnóstico antes do treino grande

Começar com 12 situações de desenvolvimento, cobrindo escolhas pessoais,
planejamento, correção de interpretação, referência, incerteza causal e
conversa cotidiana/criação simples. As sondas já lidas servem ao diagnóstico,
nunca como teste novo independente.

Para cada situação, preservar os mesmos dados e a intenção final:

1. Informações reunidas em uma mensagem, com pedido explícito.
2. As mesmas informações em vários turnos, com respostas do próprio sistema.
3. A sequência anterior com recapitulação final apenas dos dados fornecidos.
4. Estado ativo e intenção conferidos manualmente, fornecidos ao componente
   de resposta para medir seu desempenho quando a interpretação está correta.

A quarta condição é diagnóstico assistido por informação correta, não prova
de que a rede aprendeu a interpretar. A recapitulação não acrescenta fatos ou
conclusões. No modelo causal, registrar tokens e turnos que couberam; comparar
apenas condições com os dados necessários presentes, reportando as demais
como falhas de orçamento de contexto. Não cortar silenciosamente informação
e atribuir a queda ao raciocínio.

Comparar o motor normal e a geração direta do checkpoint próprio. Identificar
qual mecanismo respondeu cada turno, sem chamar texto estrutural de geração
neural. Usar a mesma política de decodificação, orçamento de saída e versões
dos pesos entre condições. Se aparecer dependência de uma resposta anterior
errada, acrescentar uma ablação que retira essa resposta, preservando as
mensagens do usuário. Essa comparação mede uma possibilidade de ancoragem,
não autoriza inventar o histórico correto.

**Decisão:** se o modelo responde bem com os dados juntos, mas mal na
sequência, priorizar entendimento da intenção, seleção de fontes e contexto
efetivo. Se falha mesmo com dados e intenção corretos, priorizar redação,
supervisão e aprendizagem. Se a falha acompanha truncamento, corrigir a
entrada e medir novamente. Não escolher uma causa única por um exemplo.

### 2. Corpus alinhado ao comportamento desejado

Medir quantas conversas existentes realmente contêm vários turnos úteis e
quantas suas janelas de treinamento conseguem mostrar. Contar árvores,
trajetórias e relações diferentes, além de pares, janelas e tokens repetidos.
Auditar pedidos incompletos, correções, revisão de conclusão e respostas que
precisam usar mais de uma declaração anterior.

Conservar o corpus humano licenciado já existente; OASST2 inclui OASST1,
portanto baixar as duas versões não é uma expansão independente. O corpus
OpenAssistant é organizado em árvores, úteis para preservar trajetórias e
partições. [Fonte primária](https://arxiv.org/abs/2304.07327).

Adicionar exemplos autorais identificados para comparar, perguntar quando
falta informação, explicar uma conclusão apoiada e reformulá-la depois de
uma correção. Variar relações, formulações e ordem das declarações; alterar
apenas nomes e preços é insuficiente. Não adicionar exceções por assunto ao
runtime como forma de fazer o painel passar.

Reservar árvores e famílias de cenário inteiras. Não usar conversas privadas
do usuário, as respostas falhas do Crivo como alvo positivo ou modelos
externos para gerar/avaliar o corpus. Dados sintéticos públicos existentes
mantêm sua atribuição e não são contabilizados como novas conversas humanas.

Preservar a máscara de perda das respostas, que já existe. Reutilizar as
rotinas de integridade e auditar se o alvo ainda é aprendível com os dados
visíveis na janela. Não mudar formato, corpus, tamanho e algoritmo ao mesmo
tempo sem registrar que a comparação deixou de isolar uma intervenção.

### 3. Piloto que também treina a resposta

O primeiro modelo de referência será o gerador causal próprio 2,6M com
checkpoint e tokenizer conferidos. Não partir de um leitor especializado
como se ele já fosse um conversador. Preservar os pesos originais.

Se o diagnóstico justificar treinamento de linguagem, comparar dois braços:
continuação com os dados atuais e continuação com o currículo revisado para
o comportamento em falta. Usar a mesma inicialização, orçamento de tokens
supervisionados, validação e política de seleção. Isso compara o currículo;
não isola individualmente todas as mudanças de conteúdo. Incluir replay de
linguagem antiga para medir e limitar esquecimento.

Treinar redação com respostas contextualizadas e aprendizagem causal; não
substituir esse objetivo por uma classificação de domínio. Interpretação e
execução continuam sendo medidos separadamente. Cálculos e contratos
restritos podem usar os executores próprios, com atribuição explícita.

Antes da rodada, medir 100 atualizações no dispositivo escolhido e registrar
tokens/segundo, memória e tempo de avaliação. Só então estimar duração de
um horizonte maior. A primeira investigação terá um teto de 90 minutos de
computação ativa; interromper e salvar ao atingir o orçamento. Isso é limite
de custo do piloto, não promessa de resolver conversa livre em 90 minutos.

Escolher checkpoint por desenvolvimento. Continuar apenas se houver ganho
de pelo menos 10 pontos percentuais em sessões adequadas no desenvolvimento,
sem piora nos contratos críticos de fatos/correções e sem mais de 3 pontos
de queda nos painéis de retenção escolhidos antes do treino. Esses valores
são critérios propostos para o projeto, não resultados nem limites dos papers.

Se nenhum braço melhorar, publicar a rejeição e investigar dados visíveis,
máscara, objetivo, erro de treinamento e curvas de aprendizado. Um teste
pequeno de ajuste ao próprio treino ajuda a detectar implementação defeituosa;
seu sucesso não mede generalização. Aumentar a rede só entra após essa análise.

Comparar com uma candidata causal própria maior, inclusive 16M, apenas depois
de conferir seu checkpoint e preparação. Registrar orçamento e estado de
pré-treino: um modelo aleatório maior e um menor já treinado não isolam
capacidade. Não há requisito de exatamente 17 milhões de parâmetros.

### 4. Critério para chamar o ganho de conversa útil

Congelar, antes da seleção final, 60 sessões internas novas de 6–10 turnos,
com dez por família. Separar por cenário e relações, não apenas por frase
literal. Depois de olhar uma falha e adaptar o modelo, essa sessão vira
desenvolvimento; a próxima avaliação exige outro painel.

Usar rubrica prévia: responder ao pedido, conservar fatos e negações,
resolver referências relevantes, distinguir hipótese e declaração, revisar
uma interpretação corrigida e produzir uma resposta útil. Uma resposta que
só repete frases e faz uma pergunta genérica é parcial, mesmo que contenha
palavras esperadas. Fluência/pertinência precisam de leitura humana; contas
e operações têm verificações próprias. Medir sessões completas, não somar
acertos de turnos escondendo um diálogo quebrado.

Acrescentar variantes em que uma paráfrase deve conservar o resultado e em
que trocar uma condição, negar um fato ou corrigir um valor deve mudá-lo.
Publicar erros, respostas integrais e distinção entre componentes próprios
estruturais e neurais. Não confundir um número corretamente calculado com
a escolha correta dos argumentos.

Para o primeiro marco de integração, propor pelo menos 80% de sessões
inteiramente adequadas em cada família, ganho de pelo menos 20 pontos
percentuais sobre o baseline comparável e nenhum erro crítico de promoção
de hipótese/fonte nos contratos específicos. Esses limiares e os críticos
devem ser fechados antes do treino. Não tolerar regressão desses contratos
para compensar com um agregado melhor.

Repetir o treino com três sementes somente depois do piloto promissor; não
escolher a semente pelo teste reservado. Reportar variabilidade e a incerteza
por sessão. Um painel interno escrito/avaliado pela mesma autoria não é
avaliação externa independente. Uma revisão humana sem conhecer qual
candidata respondeu e conversas espontâneas posteriores constituem uma
verificação adicional; ainda não foram realizadas.

### 5. Entrega e proteção do que já funciona

Integrar somente a candidata que cumpra o protocolo, com configuração
reversível e versão identificada. Preservar base factual, fontes, programação,
aritmética, isolamento de sessão e distinção de hipótese/ficção. Um validador
restrito não consegue certificar a semântica de qualquer texto livre.

Verificar motor, adaptação web e uma conversa pelo endpoint real. Medir a
entrada efetiva do modelo e o comportamento após sair da janela de histórico;
memória persistente precisa de desenho próprio e não será fingida pelo replay.

Executar diagnóstico e treinos em laboratório antes de abrir PR. Usar checks
locais apropriados para cada mudança; fazer o CI completo na entrega fechada,
sem novos commits reiniciando uma rodada em andamento. Um PR por entrega,
mescla somente verde, preservando branches e checkpoints. O PR 116 e a
correção já salva são trabalhos existentes, não a comprovação desse novo plano.

Os artefatos serão pequenos relatórios com hashes e referências aos pesos
preservados. Guardar modelos nos destinos aprovados, evitando acumular novas
cópias grandes nos Actions. O notebook Colab existente será revisado para
retomada/backup e para este protocolo se o treino amplo exigir GPU; nenhum
runtime Colab foi iniciado por este planejamento.

## Primeiro próximo passo e prestação de contas

Começar pela etapa 1. Sua entrega deve dizer: o que foi testado, o que mudou
entre condições, o que continua incerto e qual treino/intervenção a evidência
autoriza fazer em seguida. Uma rodada sem conhecimento novo termina com
resultado negativo e mudança de hipótese, não com repetição indefinida.

O prazo do treino será calculado após o benchmark do dispositivo; o prazo
para alcançar conversa geral permanece desconhecido. Nenhum paper garante
que os pesos atuais alcançarão a meta. Este documento é o plano concluído;
diagnóstico pareado, corpus revisado, treinos e avaliação final são trabalhos
subsequentes, ainda não executados nesta entrega.
