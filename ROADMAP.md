# Prioridades ativas do CRIVO — 10/10/2026

1. **Publicar a Fase 3 com checks relevantes verdes.** Segundo treino e
   correções das falhas públicas de #127: 37/43 → 43/43 no motor/HTTP,
   zero troca/referente ausente; 7/10 → 10/10 nas sessões intactas,
   revisão pelo agente. Após merge, conferir commit/checkpoint e repetir no site.
2. **Escopo aprovado permanece restrito.** História, continuação e final
   com argumentos resolvidos da sessão. Capacidades, funcionamento,
   autoria, memória, fatos, cálculo e fontes preservam os executores
   atuais. Guardas de conversa e de fatos têm políticas distintas.
3. **Próximo passo único após publicação.** Medir novos diálogos reais,
   especialmente orientação prática e continuação fora dos oito arcos,
   para selecionar a próxima ampliação do corpus autoral. Sem nova memória,
   acervo, parâmetros ou outra frente sem instrução do dono.

A Fase 3 treinou a GRU própria em oito arcos, passando de quatro para 52
padrões de ficção e **85.581 parâmetros**, abaixo dos 88.969 anteriores.
384 diálogos novos, 8.064 turnos documentados com o corpus anterior.
Reprodução byte a byte; contagens/estilos arbitrários e conversa livre geral
continuam limitados. O seq2seq da Fase 1 segue reprovado. O
experimento original conserva aprovado=false; a cópia de produção inclui
proveniência e critérios medidos. Não alegar conversa humana plena.

Um PR grande de capacidade por vez. CI por escopo, matriz completa
manual/semanal. Somente arquitetura, tokenizadores e pesos próprios.
Evidências: [Fase 3](experimentos/dialogo_v2_20261010/README.md),
[integração](experimentos/integracao_dialogo_20261010/README.md)
e [treino](experimentos/dialogo_20261010/README.md).
