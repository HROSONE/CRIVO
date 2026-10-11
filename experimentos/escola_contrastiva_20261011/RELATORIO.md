# Escola Cognitiva — aula contrastiva multivista

Mesma GRU, mesmos 81.433 parametros, mesmos 3.699 exemplos de geracao e lambda auxiliar total 0,25.

- Professor AÇÃO dev: **18.8%**.
- Professor FOCO dev: **35.4%**.
- old334: **69/334**, CE **0.708**.
- known94: **0/94**, CE **7.156**.
- fatorial96 operações: **47.9%**.
- holdout #146: **38.9%**.
- holdout #148: **51.4%**.
- prova nova 180: CE **1.101**, primeiro token **21.7%**, operações **33.9%**.

## Gate congelado

- old334_exatas: **PASSOU**.
- old334_ce: **PASSOU**.
- known94_exatas: **FALHOU**.
- known94_ce: **FALHOU**.
- fatorial96_operacoes: **PASSOU**.
- holdout146_operacoes: **FALHOU**.
- holdout148_operacoes: **PASSOU**.
- professor_acao_dev: **FALHOU**.
- professor_foco_dev: **FALHOU**.
- novo_ce: **FALHOU**.
- novo_primeiro: **FALHOU**.
- novo_operacoes_ganho: **FALHOU**.
- novo_operacoes_total: **FALHOU**.
- novo_operacao_individual: **FALHOU**.
- sucesso_conjunto: **FALHOU**.

**Sucesso conjunto: NÃO.**

Nenhuma promoção automática; `ativo_no_chat=false`.
