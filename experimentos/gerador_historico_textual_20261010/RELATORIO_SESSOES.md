# Sessões completas e respostas variadas — 10/10/2026

A última rodada de hoje foi concluída: corpus próprio, dois treinos reais,
seleção por desenvolvimento e avaliação congelada. **Não melhorou a conversa:
0/10 sessões mantêm o fio antes e depois; houve regressão.** Os dois novos
checkpoints continuam `aprovado: false` / `ativo_no_chat: false`, fora do chat.
Mesmo PR #137, em rascunho; nenhum merge ou substituição do modelo público.

## O que mudou

Foram escritos **36 episódios autorais de seis turnos**, com duas realizações
por resposta: **216 turnos de usuário / 424 respostas deslexicalizadas distintas**.
Incluem ajuda prática, mensagens, recusa de convite, conversa sem conselho,
correção, hipótese, histórias e alternância de tarefas. São textos autorais
do agente, não sessões humanas coletadas. Duas realizações não significam
dois padrões semânticos diferentes.

32 episódios vão ao treino; quatro famílias inteiras ficam no desenvolvimento:
`pessoa_silencio`, `correcao_autoria`, `esperar_sem_garantia`, `moradia_e_tarefas`.
Há operações e vocabulário compartilhados entre famílias; isso não equivale
a testar capacidades totalmente inéditas. O histórico de treino usa respostas
alvo; no teste livre usa somente as respostas realmente geradas.

Depois da expansão por nomes/cortesia e da deduplicação:

| Parte | Treino | Desenvolvimento |
|---|---:|---:|
| Sessões novas | 2.686 | 94 |
| Replay balanceado antigo | 999 | — |
| Apoio lexical autoral | 14 | — |
| Desenvolvimento anterior preservado | — | 334 |
| Total | **3.699** | **428** |

Antes da deduplicação as sessões expandidas tinham 3.072/96 exemplos. Nomes
e variantes de cortesia não contam como capacidades novas. Nenhuma entrada
literal ou nome exclusivo do teste final está no corpus. Os 334 exemplos
antigos de desenvolvimento foram preservados, não movidos para treino.
Fontes completas têm no máximo **124 tokens**; nenhum alvo é impossível de
gerar/copiar e todos cabem no limite de 64 tokens de resposta.

## Vocabulário e capacidade

Mesma arquitetura própria existente: BiGRU encoder + GRU decoder + atenção
e pointer-copy, **81.433 parâmetros**, h24/e16/b128, **720 entradas lexicais**.
Não houve aumento de capacidade, mudança de tokenizador ou uso de modelo externo.
A rede recebe texto e papéis do histórico, sem intenção/slot pronto,
catálogo de respostas ou lookup do corpus durante inferência.

Para gerar verbos novos ausentes do dicionário antigo foram **realocadas 151
das 720 entradas**, escolhidas pela cobertura dos alvos de treino (incluindo
replay e apoio lexical). Os 569 IDs mantidos e seus pesos lexicais foram
preservados exatamente na inicialização; pesos recorrentes, atenção e
caracteres permaneceram intactos. As novas entradas receberam inicialização
própria, semente 179. Todos os pesos antigos foram preservados em seus arquivos.

O dicionário mudou apesar de manter tamanho/tokenizador. Portanto, a comparação
não isola somente diversidade do corpus: realocação lexical, mistura de dados
e treino mudaram juntos. Não atribuir a regressão a uma causa única nem declarar
que esta arquitetura é incapaz de aprender com base apenas nesta rodada.

## Treinos e seleção antes do teste final

| Passagem | Épocas executadas / selecionada | CPU | Entropia desenvolvimento |
|---|---:|---:|---:|
| Sessões | 20 / 16 | 317,81 s | **1,387659** |
| Refino apenas por desenvolvimento | 6 / 2 | 60,18 s | 1,388287 |

Adam novo, taxa 0,0007, batch 32, validação a cada duas épocas, fonte192/saída64.
Primeira passagem: semente179, dropout0,15, lexical0,12, sampling0,15,
aquecimento3, paciência6. Refino: semente181, dropout/lexical/sampling0,05,
paciência4; solicitado20, interrompido automaticamente na época6.
NumPy2.3.5, OPENBLAS/OMP=1. Manifestos registram assinaturas e hiperparâmetros.
Tempo total de treino: **377,99 segundos**; não inclui preparação/avaliação.

O menor erro nos mesmos 428 exemplos selecionou a **primeira passagem** no
commit `a4c8312`, antes de abrir o teste final. O refino ficou preservado,
rejeitado por esse critério, sem avaliação final separada para escolher a
resposta mais favorável. Não houve treino depois da avaliação final.

Geração livre em desenvolvimento, comparada aos alvos literais:

| Pesos | Antigos (334) | Novos (94) | Total (428) |
|---|---:|---:|---:|
| Anteriores, antes da realocação | 107 | 0 | 107 |
| Inicialização realocada, sem treino | 80 | 0 | 80 |
| Primeira passagem | **47** | **1** | **48** |
| Refino | 50 | 1 | 51 |

O treino perdeu reprodução de casos antigos e quase não aprendeu as quatro
famílias novas. Igualdade literal não mede qualidade semântica. A diferença
48→51 não mudou o critério de seleção registrado previamente.

## Avaliação final: 10 sessões novas × seis turnos

`f0da064` congelou o teste antes da autoria/expansão do corpus. A linha de
base foi executada antes do treino; a seleção final só usa desenvolvimento.
Dados, teste e revisão são autorais do agente; **não avaliação independente
ou cega**. Depois de aberto, este conjunto vira regressão conhecida.

| Condição | Sessões na triagem | Turnos na triagem | Turnos com termos proibidos |
|---|---:|---:|---:|
| Pesos anteriores, histórico real | 0/10 | 11/60 | 1 |
| Selecionado, histórico real | **0/10** | **8/60** | **3** |
| Selecionado, sem histórico | 0/10 | 14/60 | 0 |
| Selecionado, histórico invertido | 0/10 | 10/60 | 3 |

Triagem lexical só localiza falhas. Revisão semântica de todas as 60 saídas
antes e depois: **0/10 mantêm o fio em ambos**. Frases quebradas, perda de
referentes e substituição de tarefas persistem. O placar lexical maior sem
histórico não prova que essa condição converse bem; não demonstramos benefício
de histórico ordenado. Em todas as condições: EOS nas 60 respostas e zero
fontes truncadas; os limites de saída/fonte não explicam estas falhas.

Exemplos confirmados após treino:

- Empréstimo: após corrigir a devolução para sábado, responde **“O sexta, na sexta.”**
- Preferência corrigida para companhia em casa: **“sozinho, obrigado pela ajuda.”**
- Agradecimento a **Umévia** durante pausa de história com Izelta: **“Izelta, obrigado pela ajuda.”**
- Usuário mantém a busca aberta: **“A busca terminou, mas deixou.”**; no turno seguinte repete o encerramento.

São pelo menos quatro exemplos documentados, não contagem exaustiva. O portão
prévio exigia ≥5/10 sessões coerentes e zero violação de sessão: **reprovado**.
As saídas completas e justificativas por sessão estão em
`revisao_qualitativa_sessoes.json`; não ocultamos os casos piores.

Regressões conhecidas, fora do placar novo: rodada3 **0/12**, triagem9/48;
rodada2 **0/12**, triagem4/36. À pergunta real sobre dinossauros/IA responde
**“Você pode rever a escolha.”**, sem tratar a comparação e a questão ética.
Não foi escrito um alvo sob medida para essa pergunta.

## Proveniência, integridade e reprodução

- Teste/protocolo: commit **`f0da064`**, antes do corpus.
- Corpus/inicialização/script do primeiro treino: **`54259df`**, antes desse treino.
- Protocolo/script do refino: **`cea54c7`**, antes do refino.
- Seleção final: **`a4c8312`**, antes da avaliação final.
- Teste SHA-256: `13ca31d6a2702fc9c8b7c8ba8ef2129513174d520feb4d66aae016f5aaeb3500`.
- Corpus: `fceefde42f10dfa0606ca1c43f8ee7fe13343a5ef4156261563cb33297ffe1ba`.
- Inicialização realocada: `d978777bf8c1d07ea89207408e6cfa7abe5a97998ff6103793bc0f30c426bd78`.
- Checkpoint selecionado: `5ea28636d8150da1f909621181bc352c26a785931cae7960b14131b365112030`.
- Refino rejeitado: `2d33641a4460cb3d282aaa2ee99ad2691320e8d4dc7c695e806dcd032486fb5f`.

Para repetir o primeiro treino, usar checkout isolado do commit54259df:
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/sessoes.py treinar`.
Para o refino, checkout isolado de cea54c7: mesmas variáveis e
`python experimentos/gerador_historico_textual_20261010/refinar_sessoes.py treinar`.
Os scripts recusam sobrescrever pesos/resultados existentes. Manifestos
preservam versões/hashes; não foi feita segunda reprodução byte a byte.
O script do primeiro treino é conferido no commit54259df, pois sua versão
atual apenas acrescentou a seleção final opcional à etapa de avaliação.

**5/5 testes novos de integridade passaram**, incluindo separação de dados,
alvos geráveis, pesos mantidos e isolamento. Auditoria confirma os **oito
pesos de raiz** previamente listados e oito arquivos críticos inalterados
nesta rodada, incluindo arquitetura, treinador, runtime e workflow.
`rede_dialogo_conversa.json.gz` público continua SHA `28d05179e4dd…`.
Testes e auditoria não certificam conversa natural.

CI por escopo continua configurado como antes. A sonda antiga de escrita
com três subcasos falhos foi reproduzida na base com as mesmas respostas
na rodada anterior (`divida_ci_rodada3.json`). Sem enfraquecer teste,
alterar CI ou mesclar com checks relevantes vermelhos. O estado do novo
commit deve ser consultado no PR; este relatório não presume CI verde.

## Limite e encerramento de hoje

Corpus e treinos estão entregues; **a melhora do gerador não está entregue**.
Não houve integração, deploy, nova memória, acervo, regra ou aumento de
parâmetros. O modelo público não recebeu os pesos que regrediram.

Antes de outro treino de conversa, o próximo trabalho dentro desta frente
é separar, no desenvolvimento, o custo da realocação lexical e da mistura
de replay dos ganhos de sessões variadas. A hipótese de que apenas mais
variedade bastaria não foi confirmada. Não ajustar aos 10 testes finais
agora conhecidos; qualquer futura avaliação inédita precisa ser congelada
antes. A última rodada de hoje termina com este resultado negativo registrado.
