# Prioridades ativas do CRIVO — 10/10/2026

1. **Encerramento das Fases 0 e 1.** #125 verde e mesclado; seis smokes
   preservaram domínio/referentes. Congelados 37 casos reais, produzido
   corpus autoral de 5.760 turnos e treinados dois checkpoints próprios.
   A GRU condicionada fez 0/10 → 7/10 e entregou duas histórias; a
   reprodução gerou pesos idênticos. Ambos continuam desativados e
   sem aprovação. Isso ainda não melhorou o site.
2. **Próximo passo único: Fase 2, rota de conversa.** Integrar de forma
   seletiva, com estado da sessão já existente, guarda que permita
   paráfrase e proíba invenção de dados da sessão; conservar guarda
   rígida para fatos/cálculos/fontes. Preservar o percurso atual onde
   o candidato falha. Não ligar geração indiscriminadamente.
3. **Medir antes de promover.** No motor e HTTP, ≥34/37 com peça certa,
   zero troca de domínio e 100% dos referentes exigidos; ≥6/10 conversas
   reais de 6–8 turnos mantendo o fio; história e final com personagem.
   Registrar falhas restantes e validar o commit no site após merge.

Máximo um PR grande de capacidade por vez, com checks relevantes verdes.
CI por escopo; matriz completa manual/semanal. Nenhuma mudança lateral
em CI, acervo, parâmetros, memória ou microcircuitos nesta frente.

Somente arquitetura, tokenizadores e pesos próprios. O relatório contém
números, dados, limites e comandos reproduzíveis:
[diálogo 20261010](experimentos/dialogo_20261010/README.md).
