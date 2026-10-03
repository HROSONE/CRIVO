# Validação da ampliação — 03/10/2026

## Executado
- Node.js v24.19.0: execução direta de `padroes.test.mjs`, **27 testes aprovados**, zero falhas/skips.
- Test runner `node --test`: arquivo aprovado; neste ambiente o relatório externo agregou o arquivo como um teste. A execução direta acima expôs os 27 subtestes.
- Sintaxe Python: `python3 -m py_compile scripts/acervo_programacao.py`.
- Busca local por `typescript narrowing unknown`: retornou `ts_unknown-any` e `ts_narrowing` como dois primeiros resultados.
- Validador de catálogo/manifesto: IDs únicos, campos, fontes, relações, pré-requisitos sem ciclos, 40 desafios, exportações Markdown, tamanhos e hashes. Resultado reproduzível com `python3 scripts/acervo_programacao.py --validar`.

## Pendências e limites
- TypeScript não está instalado no ambiente; fixtures `contratos.ts` foram escritas/revisadas, mas **typecheck não executado**. Comando: `tsc -p docs/pesquisa_conhecimento/programacao/exemplos/tsconfig.json`.
- Referências remotas não foram conferidas nesta execução. As URLs são referências recomendadas; não há declaração de verificação editorial por edição.
- Não houve treinamento, avaliação de geração do CRIVO ou alteração de runtime/roteador.
- Não foi executada a regressão geral da aplicação: mudanças são acervo novo e ferramenta separada, sem tocar código runtime.
- Desafios são públicos/didáticos; não medir generalização usando estes mesmos enunciados após treino.
- JSON e Markdown são representações duplicadas das 200 unidades; bytes de ambas não medem quantidade de conceitos.
- Hashes detectam alteração dos arquivos listados, não demonstram correção semântica dos conceitos.

