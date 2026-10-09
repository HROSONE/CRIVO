# Continuidade de critérios pessoais — 9 de outubro de 2026

Correção estrutural sobre `faedc07` (PR 116). Não altera pesos, tokenizadores,
dados de treino ou aprovação de modelos para o chat.

## Problema observado e mudança

A sonda de emprego perdeu duas declarações porque elas não começavam por
“eu”, “quero” ou outra abertura pessoal já reconhecida. O pedido final pediu
novamente opções e critérios que a pessoa já havia informado. A abertura
reagiu com “que legal” a um objetivo acompanhado de medo de arrependimento.

Agora, declarações pessoais com possessivos ou primeira pessoa no meio da
frase entram no contexto ativo com sua fonte literal quando a rota nativa
não consegue interpretá-las. A rota nativa é consultada primeiro. Um pedido de comparação
referente a esse contexto recupera os critérios declarados. Consultas com
comparandos explícitos mantêm sua rota. A reação ao objetivo acompanhado de
receio pede avaliação e preserva a preocupação. Sugestões indiretas de outra
pessoa acompanhadas de discordância recebem atribuição e não substituem o
objetivo da pessoa.

O contexto continua limitado a oito relatos, com quatro usados no quadro de
comparação. Uma consulta factual suspende as referências pessoais implícitas.
Citações, perguntas e declarações condicionais não passam pela nova captura.
Os limites anteriores do replay web permanecem.

## Evidência e reprodução

`diagnostico_antes.json`: respostas integrais das três sondas novas, coletadas
antes desta correção em `faedc07`. `sondas_depois.json`: respostas e fontes
após a correção, com assinaturas de código e entradas. `sondas.json` conserva
as entradas das três sessões e duas variações adicionais.

```sh
python experimentos/detalhes_conversa_20261009/sondar.py --raiz . --saida /tmp/sondas-nova-execucao.json
python -m unittest testes_detalhes_conversa -v
python -S -m unittest testes_detalhes_conversa.TestesEscopoDetalhes -v
```

O relatório não soma palavras encontradas para declarar “compreensão”. Leia
as respostas completas. As sondas são autorais, já conhecidas e usadas no
diagnóstico. As variações de moradia e pesquisa também são de desenvolvimento,
e não constituem validação cega.

## Limites e falhas ainda presentes

A sequência de emprego agora conserva salário, família e a prioridade
expressa, mas a comparação ainda é uma organização de falas com perguntas
genéricas. Não pondera autonomamente utilidades nem decide pela pessoa.

A sonda sobre bateria/aplicativo continua sem responder adequadamente às
quatro perguntas. A sonda sobre perfeccionismo ainda não distingue cuidado
de perfeccionismo nem integra os turnos para explicar a contradição pedida.
A atribuição da sugestão da amiga melhorou. Essas falhas estão preservadas
no relatório; esta mudança não entrega conversa livre ou raciocínio causal
geral e não representa um novo treinamento neural.

O PR 116 permanece em sua branch original, sem receber estas alterações
ou ter seus checks reiniciados. Esta correção fica em branch separada até
concluir a verificação anterior.

## Verificação e controle de regressão

A primeira captura antecipada reduziu a bateria de presença `retido2` de
28/29 turnos e uma resposta genérica para 27/29 e duas genéricas. Os dois
resumos agregados estão preservados; não foram usados textos ou expectativas
da partição para cadastrar respostas. O resgate foi deslocado para depois
da interpretação nativa, reutilizando o protocolo de recusa existente.

Na versão final passaram os 20 testes de `testes_detalhes_conversa` e
`testes_presenca`, incluindo as catracas anteriores sem mudar limiares,
e os seis contratos de escopo sem NumPy. A bateria autoral anterior de
desenvolvimento permanece em 20/20 turnos, com seis sessões completas.
Os relatórios com `candidato_inicial` no nome são da versão anterior ao
ajuste de prioridade; os relatórios com `final` são da versão atual.

Também passaram os 73 testes de diálogo situado, contexto gerativo, bate-papo
e linguagem da versão final: 93 testes normais no total, mais os seis
contratos repetidos sem NumPy. Os 72 turnos públicos antigos permanecem
aprovados pelo contrato de `testes_bate_papo`; são controles conhecidos.
`verificacao.json` registra as assinaturas do código e os logs finais.
