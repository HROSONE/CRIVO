# Verificação do candidato de acontecimentos

A integração só pode ser promovida com todos os resultados abaixo. O candidato
isolado permanece `aprovado=false` e `ativo_no_chat=false`.

- Mesmos 114 casos: antigos 79/79 preservados, ≥103/114 total, zero troca
  de domínio e zero caso perdendo referentes, tanto motor quanto HTTP real.
- As dez sessões autorais anteriores, 104 turnos, são relidas completas;
  pelo menos seis mantêm o fio, atendem os acontecimentos e restrições.
  Cópia de evento e marcador lexical não bastam para aprovação qualitativa.
- Histórico HTTP experimental suporta vinte mensagens, mantendo limite de
  regras atuais por mensagem (1.200, ou 12.000 para conteúdo
  com pedido explícito de análise) e 24.000 no histórico. Produção só recebe
  essa alteração se a integração inteira for aprovada.
- Arquivo do treino repetido deve ser idêntico byte a byte. Dados, pesos,
  entradas congeladas e patch recebem hashes no manifesto.
- Fatos, fontes e cálculos conservam rotas rígidas. Novas ficções não podem
  se transformar em preferências ou fatos reais de sessão.
- CI obrigatório por escopo, sem repetir matriz completa depois do merge.

O diagnóstico de tokens em validação mede somente padrões autorais
compartilhados. As entidades específicas são argumentos copiados, não nomes
que a rede aprendeu a interpretar. A escolha de classe e a progressão são
estruturais; a GRU própria realiza o texto. Não é planejamento neural nem
compreensão geral de diálogos.
