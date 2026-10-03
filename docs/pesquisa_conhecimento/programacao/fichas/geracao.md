# Fichas avançadas: geracao

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## geracao_codegen — Geração de código com verificação

**Definição:** Gerar código exige transformar contrato em artefato executável, além de recuperar conceitos.

**Mecanismo:** Pipeline: requisitos, design, implementação, typecheck, testes independentes, revisão de segurança e execução controlada.

**Falhas comuns:** Corpus grande não mede competência; template memorizado pode falhar em combinação inédita.

**Escolha:** Usar tarefas novas e critérios fixados antes de observar saída; separar retrieval e geração.

**Verificação proposta:** Gerar módulo do zero e avaliar hidden tests, edges e explicação de limites.

**Relações:** geracao_eval-leakage, geracao_sandbox, geracao_reproducibility, engenharia_requirements

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## geracao_eval-leakage — Vazamento e avaliação independente

**Definição:** Dados usados para desenvolver corpus não podem servir como prova cega de capacidade.

**Mecanismo:** Split por família/problema/tempo limita contaminação; hidden tests precisam não estar no treino recuperável.

**Falhas comuns:** Holdout com mesma solução textual mede memória; publicar todo teste remove sigilo.

**Escolha:** Manter tarefas didáticas públicas e avaliação independente produzida depois, com seeds/perímetros próprios.

**Verificação proposta:** Auditar overlap de texto, algoritmo e estrutura entre treino e avaliação.

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## geracao_reproducibility — Proveniência de corpus e versões

**Definição:** Corpus precisa IDs, schema, hash e fonte para reconstruir o que foi usado.

**Mecanismo:** Manifest conta unidades/bytes e fixa hashes; versão de fonte móvel deve ser registrada ao importar conteúdo.

**Falhas comuns:** Link para documento vivo não prova que foi conferido na data; autoral não é citação literal.

**Escolha:** Separar síntese autoral de importação, registrar validação editorial pendente e não inventar revisão.

**Verificação proposta:** Verificar hashes e ID uniqueness; reproduzir export sem alterar conteúdo.

**Referências recomendadas:** [Git reference](https://git-scm.com/docs)

## geracao_sandbox — Execução isolada de código gerado

**Definição:** Código não confiável precisa isolamento de filesystem, rede, tempo e recursos.

**Mecanismo:** Processo separado com timeout não é sandbox completo; container precisa políticas adicionais conforme ameaça.

**Falhas comuns:** Rodar código gerado com secrets/rede irrestrita pode exfiltrar ou consumir recursos.

**Escolha:** Executar em ambiente descartável com capabilities mínimas e input fixtures.

**Verificação proposta:** Testar loop infinito, subprocess, filesystem e rede bloqueada.

**Referências recomendadas:** [Linux kernel documentation](https://docs.kernel.org/)


