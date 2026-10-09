# O Crivo atual na conversa de um usuário novo

O site está atualizado e a integração do #120 funciona em seu recorte. A conversa
comum ainda falha com frequência: o sistema perde pedidos, referentes e relações,
e rotas antigas respondem antes que a capacidade adequada seja acionada.

## O que foi realmente testado

Foram registrados **61 turnos em nove sessões no site público**:
https://crivo-mauve.vercel.app. Sete sessões foram conversas de uso comum, sobre
descoberta de capacidades, ciência, família, planejamento, código, criação e
consulta ao acervo. Duas foram controles de memória e programação, em formatos
explicitamente aceitos pelo sistema.

A Vercel e o GET da API confirmaram a produção no commit
`1e40650f28b5feb236ff619a182e8c833fe9068f` (#120). O SHA-256 do JavaScript
publicado coincidiu com o checkout. O endpoint informou geração própria
disponível. Usei somente `message` e `history`, com as últimas dez mensagens do
usuário, como o frontend. Não injetei `memory`, entidades ou IDs internos.

Auditoria exploratória, com continuações escolhidas após ler respostas. A revisão
é humana e posterior; esses números não são benchmark cego nem taxa de sucesso
estimada para todos os usuários. Não alterei o motor, os pesos ou a produção.

| Grupo | Turnos enviados | Adequadas | Parciais | Falharam no pedido | Sem avaliação de conteúdo |
|---|---:|---:|---:|---:|---:|
| Conversas naturais | 47 | 7 | 5 | 34 | 1 |
| Controles específicos | 14 | 11 | 1 | 2 | 0 |

Uma chamada falhou no túnel do ambiente antes da resposta HTTP. Ela foi preservada
e repetida separadamente com o payload exato: o Crivo respondeu HTTP 200, mas não
resolveu o pedido. Não atribuí o erro de transporte ao produto. As outras 60
chamadas principais responderam HTTP 200; isso não significou utilidade.

A mediana dessas respostas foi **2,62 segundos**, e a maior foi **8,29 segundos**.
Neste ensaio, a falha dominante foi semântica, não demora da inferência.

## Respostas que expõem o problema

| Pedido real | Resposta observada | O que falta |
|---|---|---|
| “Oi, nunca usei você. O que você consegue fazer por mim?” | “Ainda não interpreto essa negação com segurança.” | Interpretar a intenção da pergunta sem aplicar indiscriminadamente uma guarda factual à palavra “nunca”. |
| Depois de explicar o pôr do sol: “Eu sou leigo. Explica isso com um exemplo do dia a dia.” | Repete a fala como relato e pergunta se quero contar mais. | Executar o pedido de explicação com o referente já disponível. |
| “Minha irmã Brena prefere tapioca. Meu primo Tácio prefere bolo de fubá.”; depois perguntar por eles | Nas retomadas, “Reconheci o assunto número primo”. | Extrair entidades de declarações naturais e impedir que um sentido do acervo substitua o familiar citado. |
| Após calcular 23 minutos livres: “E se eu deixar 5 minutos para descansar?” | Receita de arroz, incluindo deixar descansar cinco minutos. | Manter a tarefa e seu orçamento; julgar pertinência em vez de aceitar coincidência lexical. |
| “Escreve uma história curta com essa personagem, umas cinco frases.” | “Num lugar distante, essa personagem, umas cinco frases recebeu uma mensagem…” | Resolver a capivara astronauta do turno anterior e separar personagem de instrução de tamanho. |
| Depois de definir DNA: “Me explica DNA em três tópicos, para uma criança de dez anos.” | “Ainda não tenho uma definição cadastrada para esse conceito.” | Aplicar a transformação solicitada ao conhecimento já acessado. |
| “Você disse que interpreta JavaScript limitado. Analise este código…” | Resposta sobre não ter gostos ou vida própria. | Reconhecer o comando depois de um preâmbulo conversacional. |

As respostas completas e os julgamentos por turno estão em
[CONVERSAS.md](CONVERSAS.md). Os JSON de cada sessão preservam também pedidos,
histórico, mecanismos, estados internos, uso neural, HTTP e tempo.

## O que funciona e mudou de verdade

Na produção, “Brena é minha irmã”, “Brena prefere tapioca” e os demais registros
nominais alimentaram a memória. As três consultas do controle sugeriram tapioca,
usaram **cuscuz após a correção**, e retomaram **Tácio** sem misturar preferências.
O trace confirmou o Transformer causal próprio realizando os fatos ativos. A
seleção da pessoa, a operação e os complementos de sugestão continuam estruturais;
esse resultado não prova raciocínio generativo aprendido.

O cálculo isolado `35 - 12 - 5` retornou **18**. O raciocínio de orçamento também
recuperou 35 minutos e calculou 23 após a tarefa de 12; depois atualizou o orçamento
para 20 e calculou oito restantes, mas não organizou as três atividades.

A definição direta de DNA respondeu com fatos pertinentes e realização pelo
Transformer ancorado. A explicação de Marte foi correta. A pergunta do pôr do
sol teve uma aproximação relevante, apesar da ressalva de não ter resposta exata.

O motor JavaScript explicou seu contrato, executou `return entrada + 2` com
entrada 3 e devolveu **5**. Também corrigiu `entrada - 2` para `entrada + 2` nos
dois exemplos fornecidos, dizendo que era uma hipótese e pedindo validação nova.
O laço com `i++` foi recusado pelo parser; o motor aceita um subconjunto, não
JavaScript geral, e não se deve apresentar ausência de execução Python como
regressão de uma capacidade que ele não anunciou.

`generation.usada` foi verdadeiro em quatro respostas principais: três de
memória e uma de DNA. Esse campo mede o Transformer ancorado, não todas as redes.
A criação de histórias tem uma GRU própria anterior; a rede de efeitos de código
também é diferente. Não concluo que as outras respostas são todas não neurais.

## Por que parece o Crivo anterior

Comparei localmente os mesmos casos selecionados no #119
(`ef2fafdbf25344f7d4f7f48e36f23779cde97ec6`) e no #120. A saudação inicial,
as duas falas de ciência e as três de planejamento produziram **IDs e respostas
iguais**, incluindo a receita de arroz. Os quatro registros nominais também
ficaram iguais, porque essa memória já existia.

A consulta “Me sugira uma opção para Brena” mudou: no #119 caiu em “não entendi”;
no #120 sugeriu tapioca a partir da memória. A mudança é real, mas afeta um caminho
específico. A experiência geral continua usando muitos caminhos anteriores.
Dados: [comparacao_119.json](comparacao_119.json) e
[comparacao_120.json](comparacao_120.json). São controles locais de casos já
inspecionados, separados dos 61 turnos públicos.

## Causas encontradas no código e no trace

1. **A entrada natural não chega sempre à memória.** A reprodução isolada do
   coletor com as duas declarações naturais de família terminou com zero entidades
   e zero afirmações. Os registros nominais separados criaram as duas pessoas e
   atualizaram cuscuz corretamente. O coletor usa padrões de frase inteira e não
   extrai declarações de mensagens que contêm `?`; a mistura de pedido e relato
   também pode impedir captura. Não significa que toda informação existe no
   estado e apenas o gerador a ignora. [diagnostico_extracao.json](diagnostico_extracao.json).
2. **Uma resposta superficial pode encerrar a decisão.** O árbitro registra
   “primeira espécie a responder” e aceita candidatos que não considera recusas.
   Nos traces, relatos/reflexões/planejamento genéricos interrompem pedidos de
   exemplo, comparação ou explicação da resposta. Não há confirmação suficiente
   de que o candidato cumpriu a operação do usuário.
3. **O consumo de memória tem escopo estreito.** `conversa_sessao` reconhece atos
   por padrões e requer pessoas/referentes elegíveis. Uma conversa científica,
   comparação causal, personagem de história ou plano de tarefas não se torna
   automaticamente uma operação desse consumidor. Ele não é um controlador
   geral de diálogo.
4. **As rotas ainda dependem da redação.** A guarda factual bloqueia `não/nunca/jamais`;
   o comando de programação é procurado no início; a criação copia o trecho
   após “com/sobre” para slots sem resolver “essa personagem”. O Transformer pode
   estar disponível e nem ser chamado para a tarefa pretendida.
5. **Os checks medem contratos de nichos.** Os testes existentes demonstraram
   funcionalidades reais, mas não certificam a conversa livre. Os casos naturais
   desta auditoria expuseram combinações, preâmbulos e retomadas que os controles
   anteriores não cobriam.

Referências no commit testado:
[guarda de negação](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/crivo.py#L2630),
[coletor existente](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/memoria_sessao.py#L143),
[consumidor](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/conversa_sessao.py#L35),
[árbitro](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/estado_interno.py#L146),
[entrada de código](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/programacao_chat.py#L77),
[personagens de criação](https://github.com/HROSONE/CRIVO/blob/1e40650f28b5feb236ff619a182e8c833fe9068f/pedidos_gerativos.py#L66).

## Prioridade de trabalho recomendada

1. **Melhorar a compreensão da fala sobre o estado existente.** Reconhecer pedido,
   relato e correção em mensagens naturais e compostas; resolver a pessoa/objeto
   antes de buscar palavras no acervo. Aperfeiçoar o coletor e o consumidor atuais,
   sem abrir outra camada de memória ou aumentar o acervo para encobrir o problema.
2. **Preservar a tarefa na continuidade e validar a resposta escolhida.** Pedidos
   como “explica isso”, “qual a diferença”, “refaz” e “muda o final” devem operar
   sobre o assunto, evidências e resultado anterior. Um candidato sobre arroz ou
   sobre a personalidade não satisfaz a tarefa ativa e deve ser descartado.
3. **Depois, treinar e avaliar o componente próprio para essa transferência.**
   Fornecer à rede o pedido, as entidades, os fatos e as restrições relevantes;
   medir preservação e execução da operação em diálogos humanos reservados.
   Treino de geração livre ou mais parâmetros, por si sós, não corrigem informação
   não extraída nem uma rota que impede o modelo de receber o pedido.

Os casos observados foram preservados com hashes para regressão. **Agora estão
inspecionados**: um teste de aceitação futuro precisa usar novas conversas humanas
reservadas e avaliar pela mesma API pública, além de exigir que estes erros não
retornem. Corrigir este arquivo de exemplos não provará generalização.

Nesta tarefa fiz avaliação e diagnóstico. Não abri um PR novo, não ajustei os
pesos e não declarei corrigidas as falhas encontradas.
