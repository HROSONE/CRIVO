# Ato auxiliar de diálogo — 2026-10-11

Experimento isolado para testar supervisão auxiliar de seis atos conversacionais no estado inicial da GRU.

- não altera o runtime;
- não adiciona token de ato à inferência;
- a cabeça auxiliar existe somente durante o treino;
- checkpoint final mantém a arquitetura serializada original;
- novo holdout prospectivo é congelado antes de o workflow de treino existir;
- promoção automática é proibida.
