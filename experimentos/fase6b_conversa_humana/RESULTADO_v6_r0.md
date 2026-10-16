# Fase 6b v6-r0 — avaliação posterior (15/10/2026)

**Estado em 16/10/2026: candidato experimental; ainda não promovido nem confirmado como modelo ativo no chat.**

## Artefato avaliado

- Pasta informada no Google Drive: `CRIVO/transformer-crivo-46m-conversa-v6-r0/conversa_20261015_201812/`
- Checkpoint selecionado: passo **1.890**.
- Tamanho/arquitetura informados: aproximadamente **46,1 milhões de parâmetros**, 24 camadas e contexto de 1.024 tokens.
- Dados de destilação informados: aproximadamente **99.589 exemplos**, com professor Qwen3-32B-AWQ.
- Arquivos esperados no Drive: `pesos.pt`, `tokenizer.json`, `resumo_fase6b_v6_r0.json`.

**Limite de verificação:** os resultados abaixo foram transcritos da comparação compartilhada pelo criador na conversa de 16/10/2026. Os arquivos originais do Drive, os hashes e o checkpoint não foram obtidos diretamente durante a atualização desta documentação. Portanto, os números são registros informados, não uma reprodução independente.

## Comparação informada: modelo principal anterior × v6-r0

| Régua | Anterior | v6-r0 | Diferença |
|---|---:|---:|---:|
| Cego v3 (2.980 frases) | 62,1% | 63,5% | +1,4 p.p. |
| Cego v1 | 61,4% | 66,7% | +5,3 p.p. |
| Paráfrases (3.000) | 69,3% | 70,4% | +1,1 p.p. |
| Grok (2.980) | 64,2% | 70,8% | +6,6 p.p. |
| Cego v4 (600) | 82,5% | 90,0% | +7,5 p.p. |
| Frases reais do criador | 9/15 | 10/15 | +1 caso |

As taxas `all_ok` informadas também melhoraram levemente: v3 95,1% → 96,5%; v1 88,8% → 89,1%; paráfrases 92,5% → 92,9%; Grok 93,1% → 94,6%; v4 89,7% → 91,3%.

## Limitações e falhas que precisam continuar visíveis

A avaliação reportada aponta categorias com 0% de acerto, incluindo `amor_bom`, `insulto`, `motivacao`, `sem_sentido`, `ser_humano` e `tedio`, além de fraquezas em saudações, pedidos para continuar, testes, risadas, reformulações e contas/jogos. Foram relatadas interpretações literais fora de contexto e mudanças de assunto.

A melhora média **não significa aprovação geral**. Antes de promover:
1. conferir o hash de `pesos.pt` e do tokenizador e confirmar que correspondem ao passo 1.890 e ao resumo;
2. executar anterior e v6-r0 no mesmo conjunto congelado, com o mesmo código, parâmetros de geração e critérios;
3. reavaliar as categorias fracas e exemplos reais inéditos;
4. medir latência, memória e compatibilidade com site, PC e Android;
5. manter o modelo atual como fallback até aprovação explícita.

## Relação com o modelo atualmente configurado

No `main) observado nesta revisão, `conversa_v3d.py` continua descrevendo e carregando o modelo 46M da fase 6b v4 (com v4 F como alternativa). Esta atualização é documental: **não troca o modelo em produção, não adiciona pesos e não altera a lógica de carregamento**.

O checkpoint v6-r0 não foi encontrado no repositório público durante a busca; a localização indicada é o Drive acima. Não declarar o v6-r0 ativo até verificar os arquivos e a implantação real.
