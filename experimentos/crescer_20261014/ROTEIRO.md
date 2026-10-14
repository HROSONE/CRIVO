# Roteiro do CRIVO (quem conduz é o assistente; o criador aprova e roda a GPU)

Combinado de 14/10/2026: "eu quem devo depender do que você diz [...] eu: tudo bem!". O assistente
decide o próximo passo e faz tudo o que não precisa de GPU nem de aparelho. O criador só:
1. aperta "Executar tudo" nos notebooks de GPU, na conta indicada;
2. manda print quando pedido;
3. conversa com o CRIVO e conta o que achou;
4. diz "tudo bem", ou "não", nas decisões que mudam o que ele é.

| # | Etapa | Quem | Situação |
|---|---|---|---|
| 1 | v4 F no chat, falando do jeito dele, sem texto pronto no lugar | assistente | feito (14/10) |
| 2 | "Peito apertado" e "coração disparado" no protocolo de urgência | assistente | feito |
| 3 | Memória ligada por padrão no app e no PC (fica só no aparelho) | assistente | feito |
| 4 | **6a: crescer para 46M e ler ~2,5 bi de tokens da web** | criador roda (A100, hr87676620) | feito (14/10): 46M, 3,6 bi de tokens, perda 2,962 → 2,723 (RESULTADO_6A.md) |
| 5 | 6b, dados: conversas de pessoas (OASST2 pt e outras abertas), lembranças no contexto, IDENTIDADE.md como leitura | assistente | feito (gerador, formato, notebook; fumaça em CPU) |
| 6 | 6b, treino: conversar com o modelo crescido | criador roda (A100/L4) | feito: 4 rodadas; a v4 empata com a F (RESULTADO.md) |
| 7 | 6c: o modelo crescido no chat, no site e no app (int8, conferido no emulador) | assistente | feito (14/10), em teste; o emulador roda na CI depois do merge |
| 8 | Caderno de lembranças usado pelo modelo (o que a pessoa contou, entre conversas) | assistente | junto com 6b/6c |
| 9 | Aprender de vez com as conversas que o criador permitir: botão para exportar, limpeza, re-treino | os dois | próximo |
| 9b | Mais conhecimento: enciclopédia com o começo de 120 mil verbetes da Wikipédia, com fonte, quando o acervo não sabe | assistente | feito (14/10) |
| 10 | Crescer de novo (~120–150M) e ler 8–10 bi de tokens, se o 6b provar o método | criador roda | depois |

Regra que não muda: crise e urgência de saúde têm resposta fixa (CVV 188, SAMU 192), antes do modelo.
