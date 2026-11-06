# Auditoria técnica da expansão de psicologia cognitiva e neurociência

Data: 2026-10-15  
PR relacionado: https://github.com/HROSONE/CRIVO/pull/175  
Branch: `crivo/expandir-psicologia-cognitiva-neurociencia`

## Resultado

**Estado: bloqueada para integração direta.** Os arquivos V1–V8 são material de rascunho curricular; o formato atual não é compatível com o currículo carregado pelo CRIVO. Não declarar cobertura de 80% nem considerar os itens aprendidos pelo modelo.

## Bloqueios confirmados por leitura do código da main

1. **Loader não inclui os arquivos.** Em `curriculo_mundo.py`, a lista de catálogos temáticos carregados por `ler_curriculo()` inclui `conhecimento_mente.json`, mas não inclui `conhecimento_psicologia_cognitiva_neurociencia_v*.json`. Portanto, os oito arquivos novos não são carregados automaticamente.
2. **IDs fora do padrão.** O validador exige IDs no formato `mundo_[a-z0-9_]{1,56}`; IDs como `atencao`, `memoria` e `neurotransmissores` não passam.
3. **Campos de fatos incompatíveis.** O validador aceita os papéis `definicao`, `detalhe`, `causa`, `exemplo` e `limite`. Os lotes usam papéis como `explicacao`, `mecanismo`, `aplicacao`, `distincao` e `limite_inferencial`.
4. **Fonte por fato ausente.** Cada fato precisa apontar para uma chave existente em `fontes` via `fonte`. Os lotes registram algumas referências gerais no topo, mas não associam fonte individual aos fatos.
5. **Metadados das fontes incompatíveis.** O validador exige tipo, ano, ano_tipo, reutilizacao permitida, direitos_url, credito, verificado_em e escopo_uso. Os metadados atuais dos lotes não cumprem esse contrato.
6. **Ordem de fatos.** O primeiro fato de cada conceito precisa ter papel `definicao`; alguns lotes começam com outros papéis ou usam a definição em posição posterior.

## Auditoria reproduzível

Foi adicionado `scripts/auditar_expansao_psicologia.py`, um verificador conservador para listar conceitos, fatos, papéis inválidos, metadados incompletos, fatos sem fonte específica e duplicatas entre lotes. Ele não converte nem atribui fontes automaticamente. Execução prevista no clone local: `python scripts/auditar_expansao_psicologia.py`. O script foi criado na branch, mas não foi executado neste ambiente; seus resultados devem ser confirmados em CI ou clone local.

A inspeção estática dos oito JSONs encontrou **dois nomes repetidos entre os lotes**: “Desenvolvimento cognitivo ao longo da vida” (V3/V8) e “Motivação, metas e autorregulação” (V3/V8). A contagem confirmou 107 conceitos, 509 fatos e 37 entradas de fontes somadas entre arquivos (não necessariamente 37 fontes únicas). **Os 509 fatos não contêm o campo `fonte`**.

## Próximos passos seguros

1. Não alterar o loader para aceitar rascunhos automaticamente.
2. Converter os conceitos em catálogo compatível, com IDs únicos `mundo_...`, primeiro fato definicional, papéis válidos e fontes registradas com metadados completos.
3. Associar cada afirmação a uma fonte específica realmente consultada; não atribuir fontes por conveniência.
4. Comparar os conceitos com `conhecimento_mundo.json` e `conhecimento_mente.json` para evitar duplicatas.
5. Rodar `python scripts/verificar_acervo.py --base main` e os testes relevantes em ambiente com o repositório completo.
6. Verificar se a recuperação responde perguntas diretas e paráfrases dos conceitos recém-adicionados.
7. Medir cobertura curricular com uma rubrica explícita e perguntas de teste não usadas na criação do catálogo. O percentual de cobertura do acervo deve ser separado da taxa de acerto do modelo.

## Critério para considerar a meta de 80%

A meta só pode ser declarada atingida depois de:
- definir domínios e subdomínios curriculares e seu peso;
- marcar cada subdomínio como ausente, superficial ou adequadamente coberto;
- auditar duplicatas e qualidade das fontes;
- avaliar perguntas inéditas com gabarito e critérios de pontuação;
- reportar separadamente cobertura documental, recuperação e acurácia.

Adicionar mais fatos, isoladamente, não comprova 80% de cobertura nem inteligência funcional.
