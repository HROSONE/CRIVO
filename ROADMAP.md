# Prioridades ativas do CRIVO — 10/10/2026

1. **Concluir publicação da Fase 2.** Integração seletiva da GRU própria
   de diálogo: 35/37 → 37/37 no motor/HTTP, zero troca de domínio,
   referentes preservados, 2/2 histórias. Dez sessões pré-congeladas:
   4/10 → 7/10 na revisão pelo agente. Mesclar apenas com checks
   relevantes verdes e confirmar o commit e as capacidades no site.
2. **Escopo aprovado permanece restrito.** História, continuação e final
   com argumentos resolvidos da sessão. Capacidades, funcionamento,
   autoria, memória, fatos, cálculo e fontes preservam os executores
   atuais. Guardas de conversa e de fatos têm políticas distintas.
3. **Depois da validação pública, Fase 3.** Incorporar as falhas de
   retomada do desenho, resposta ao esclarecimento nominal e história
   com restrições/cenário. Aumentar diversidade do corpus autoral antes
   do segundo treino; não adicionar memória, acervo ou parâmetros.

A Fase 1 treinou dois checkpoints próprios. O seq2seq segue reprovado;
a GRU de 88.969 parâmetros foi aprovada somente no escopo acima. O
experimento original conserva aprovado=false; a cópia de produção inclui
proveniência e critérios medidos. Não alegar conversa humana plena.

Um PR grande de capacidade por vez. CI por escopo, matriz completa
manual/semanal. Somente arquitetura, tokenizadores e pesos próprios.
Evidências: [integração](experimentos/integracao_dialogo_20261010/README.md)
e [treino](experimentos/dialogo_20261010/README.md).
