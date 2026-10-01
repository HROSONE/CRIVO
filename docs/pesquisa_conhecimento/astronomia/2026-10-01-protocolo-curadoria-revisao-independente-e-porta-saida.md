# Astronomia — protocolo de curadoria independente, retenção de testes e encerramento da pesquisa

**Data:** 2026-10-01. **Módulo:** 10 (preparo documental de avaliações, não execução); também módulos 1–9.  
**Status:** MATERIAL DOCUMENTAL PARA O AGENTE INTEGRADOR; NÃO integrado, NÃO treinado, NÃO certificado. Não modifica `main`, CI, código, testes ou pesos.  
**Princípio:** a branch `pesquisa/acervo-conhecimento-crivo` contém literatura e raciocínio editorial. A aprovação da especialização do CRIVO necessita ser comprovada sobre o **sistema real**, não inferida do volume de informação disponível ao agente.

## 1. O que existe e o que não existe nesta entrega

A branch contém um acervo crescente de dossiês, um inventário nominal das 72 fichas de astronomia em `main:conhecimento_mundo.json` e das quatro luas no arquivo próprio, além de um protocolo de lacunas. Há documentos sobre planetas, pequenos corpos, exoplanetas, dinâmica, estrelas, galáxias, cosmologia, matemática e inferência.

**Isto NÃO prova:** revisão individual de cada fato; cobertura de todos os fenômenos; abstenção em casos sem evidência; boa interpretação de português livre; consulta simbólica correta; capacidade neural em perguntas fora do treino; nem aprovação da skill. Não reclassificar o CRIVO como 'graduado' ou '100%' só porque o acervo foi enriquecido.

## 2. Separar dois encerramentos

**Encerramento da PESQUISA DOCUMENTAL:** a decisão deste agente exige revisar a matriz dos dez módulos, conferir documentação de conceitos obrigatórios, relações causais, exemplos e limitações e realizar **duas auditorias documentais consecutivas sem lacuna central ou erro científico bloqueante**. Se atingir, registrar `pesquisa_documental_suficiente_para_curadoria` e **parar expansão genérica de Astronomia**; novidades futuras podem ser revisões pontuais. Não precisa esperar diploma ou acerto neural para encerrar apenas pesquisas.

**Certificação de CAPACIDADE do CRIVO:** pertence ao integrador; a skill da main exige dez módulos editoriais aprovados, pelo menos 90% de acertos em **avaliação independente por módulo**, nenhum caso de controle de abstenção com invenção e CI/compatibilidade. A conclusão documental NÃO aciona essa certificação.

**Regra de honestidade:** se um modelo atinge 100% de cobertura de fichas, mas acerta 20% em perguntas inéditas, seus eixos são 100% cobertura editorial de determinado escopo e 20% desempenho de determinada prova, não um 'cérebro 100% inteligente'.

## 3. Origem da revisão independente

Preferir revisor humano qualificado e não envolvido na redação dos dossiês, acompanhado de referências institucionais ou primárias. Se houver um segundo agente distinto, ele pode fazer triagem separada, mas NÃO declarar independência metodológica plena por simplesmente trocar o agente: ferramentas, fontes, prompts, codificações e modelos podem ser compartilhados.

O revisor deve:
1. Conhecer o escopo fechado da skill e a versão exata da branch/commit.
2. Auditar cada afirmação usada na base ativa: fonte, tipo de evidência, publicação, condições de validade, errata, conflito e direitos.
3. Marcar afirmações falsas, desatualizadas ou sem fonte como `corrigir` ou `evidencia_insuficiente`, não acrescentá-las ao treino por conveniência.
4. Produzir resumo das ambiguidades e da decisão por módulo, com razões reprodutíveis.
5. Conferir se DOI e URLs realmente correspondem aos artigos mencionados e se artigos diferentes compartilham o mesmo instrumento/dados.
6. Registrar decisões em arquivo separado, se autorizado, SEM modificar o acervo original ou forçar o pesquisador a certificar o CRIVO.

**Exemplo de revisão necessária na branch:** no dossiê de exoplanetas, links de quatro páginas institucionais foram substituídos por URLs reais de recursos NASA depois de auditoria de acesso; links são modificáveis e uma lista de 100 referências não significa 100 fontes confirmadas. O histórico de correções faz parte da governança de conhecimento.

## 4. Separação entre treinamento e avaliação

- **Treino/curadoria:** relações e exemplos públicos nos dossiês são elegíveis para revisão e adaptação pela equipe de integração, desde que licenciados/consistentes.
- **Validação de desenvolvimento:** itens criados pelo agente integrador durante desenvolvimento não fornecem prova independente, por contaminação dos exemplos.
- **Avaliação cega:** questões **novas** redigidas após congelar o candidato e mantidas fora do material de treino/curadoria. Cada questão pode exigir combinação de conceitos que nunca apareceram juntos na mesma frase.
- **Controle negativo:** enunciados com premissa falsa, referência inexistente, informação insuficiente, unidades incompatíveis e limites de observação; avaliar se o sistema corrige premissas ou se abstém.
- **Amostras:** diversas regiões da ontologia, casos específicos e transferência entre subáreas; não confundir dez paráfrases da mesma pergunta com dez fatos independentes.
- **Prevenção de repetição:** não transformar questões publicadas neste documento em avaliação cega futura; o avaliador deve criar novas questões sem disponibilizar gabarito ao sistema.

**Não implementar a prova aqui.** A branch de pesquisa não cria testes executáveis, nem configura workflow CI.

## 5. Rubrica proposta para o integrador, NÃO aplicada

| Dimensão avaliada | O que comprovar | Falha típica |
| --- | --- | --- |
| Identificação conceitual | Distinguir categorias e relação orbital/física | Meteoros como corpos equivalentes a meteoritos |
| Relação causal | Explicar mecanismo com condições | 'Todo vulcanismo é causado pelo Sol' |
| Transferência | Generalizar a sistemas/contextos nunca apresentados | Somente responde frases do treinamento |
| Matemática | Selecionar equação adequada, unidades e hipóteses | Usar distância em km com G em AU e resultado sem dimensão |
| Evidência | Dizer o que foi observado e o que foi inferido | Confundir mapa de massa com imagem de matéria escura |
| Incerteza | Mencionar erro/modelo e reconhecer não identificabilidade | Massa exata de exoplaneta obtida só de cor |
| Abstenção | Declarar dados insuficientes ao encontrar lacuna | Inventar medida de oceano numa lua remota |
| Linguagem portuguesa | Entender paráfrases, negações, elipses e correções do usuário | Reconhecer uma frase fixa, falhar em variante |
| Coerência temporal | Distinguir dado de 2025 de atualização de 2026 | Tratar energia escura variável como descoberta final |
| Verificabilidade | Associar proposição a instrumento, equipe e estudo | URL de artigo inexistente ou sem correspondência |

Esta tabela não atribui pontuação e NÃO substitui os critérios oficiais da skill. O integrador deve usar thresholds e controles publicados no arquivo da main.

## 6. Matriz de cobertura de dez módulos — responsabilidade documental e responsabilidade do integrador

| Módulo | Materiais atuais que ajudam | O que a pesquisa ainda não certificou |
| --- | --- | --- |
| 1 Vocabulário | [Mapa das 72 fichas](2026-10-01-ontologia-72-fichas-matriz-de-evidencias.md), taxonomias de planetas/corpos | Fatos individualmente auditados e IDs sem duplicidade |
| 2 Sistema Solar | [Planetas](2026-10-01-interiores-planetas-comparacao-diferenciacao.md), [luas](2026-10-01-luas-ressonancias-mares-oceanos.md), [menores](2026-10-01-corpos-menores-cometas-cinturoes-defesa-planetaria.md) | Revisão sistemática de fontes, períodos e composição |
| 3 Formação planetária | [Formação](2026-10-01-formacao-planetaria-dinamica-evidencias.md), [cronologia](2026-10-01-cronologia-meteoritos-crateras-e-proveniencia.md) | Modelos concorrentes/limitações revisitados por revisor externo |
| 4 Física estelar | [Fusão](2026-10-01-estrutura-estelar-fusao-neutrinos-e-observacao.md), [remanescentes](2026-10-01-remanescentes-supernovas-nucleossintese-evidencias.md), [binárias](2026-10-01-fisica-estelar-baixa-massa-binarias-cristalizacao.md) | Checagem de limiares e canais, exercícios/controle de equações |
| 5 Galáxias | [Dinâmica](2026-10-01-dinamica-galactica-via-lactea-montagem-hierarquica.md), [gás](2026-10-01-ciclo-barionico-galaxias-feedback-ambiente.md), [halos](2026-10-01-funcoes-massa-galaxias-halos-abundance-matching.md) | Seleção, funções de massa, universo jovem e covariâncias auditadas |
| 6 Cosmologia | [CMB](2026-10-01-cosmologia-primitiva-nucleossintese-recombinacao-cmb.md), [DESI](2026-10-01-baos-hubble-desi-energia-escura-inferencias.md), [matéria escura](2026-10-01-materia-escura-crescimento-estrutura-lentes.md) | Verificação cruzada de hipóteses/modelos e estatísticas |
| 7 Observação | [Instrumentos](2026-10-01-metodos-quantitativos-astrometria-espectros-incertezas.md), [exoplanetas](2026-10-01-exoplanetas-metodos-deteccao-vieses-atmosferas.md) | Reprocessamento de observações reais e calibragens por equipe |
| 8 Matemática | [Caderno de fórmulas](2026-10-01-matematica-orbital-observacional-inversoes-limites.md), [checagens com dados publicados](2026-10-01-checagens-numericas-dados-publicados-dimensoes.md) | Dados brutos, propagação real de incertezas, verificação cruzada |
| 9 Raciocínio | [Matriz causal](2026-10-01-ontologia-72-fichas-matriz-de-evidencias.md), seções epistêmicas de todos os dossiês | Comportamento em enunciados novos, não treinados |
| 10 Prova final | Este protocolo, [auditoria principal](2026-10-01-auditoria-de-lacunas-e-criterio-de-parada.md) | Testes, CI, treino e certificação pelo integrador; absolutamente NÃO realizados |

## 7. Duas auditorias finais da pesquisa — procedimento

**Primeira auditoria documental:** conferir sistematicamente o inventário dos dez módulos, conceitos centrais, evidências, fontes abertas/fechadas, erros factuais, duplicatas e condições. Registrar lista fechada de defeitos críticos e menores. Um DOI incorreto que fundamenta afirmação central é defeito crítico. Uma fonte correta duplicada na bibliografia é defeito menor, salvo se contada como confirmação independente. Se restar lacuna crítica, corrigir na branch e reiniciar contagem.

**Segunda auditoria documental:** depois de resolver todas lacunas críticas encontradas na primeira, reavaliar conteúdo sem assumir que lista anterior é completa; priorizar amostras não selecionadas pelo próprio redator, contradições e dependências. Somente se não houver lacuna central nova ou erro crítico, registrar encerramento documental, escopo e ressalvas.

**Critério de stop:** após duas auditorias documentais consecutivas satisfatórias, não continuar ampliando Astronomia com curiosidades marginais: passar à próxima área de ciência por dependências do currículo. Descobertas novas entram em revisões pontuais. Isso não requer nem significa que todas as questões astronômicas do universo foram resolvidas.

**Estado ATUAL desta execução:** os dossiês foram escritos, e houve checagens pontuais de arquivos/links e correções de URLs. **Não ocorreu auditoria científica independente de todos os conceitos e artigos, nem duas auditorias finais consecutivas satisfatórias. Logo o critério de parada da Astronomia AINDA NÃO foi atingido.**

## 8. Regras de coordenação segura com o outro agente

- Pesquisador grava SOMENTE `docs/pesquisa_conhecimento/` nesta branch; lê a `main` sem editá-la.
- Integrador é responsável por resolver duplicatas/IDs, adaptar modelo de conhecimento, criar novo PR se desejar, rodar testes e avaliação e decidir merge de fatos. O outro agente pode revisar este protocolo sem depender de aprovar notas que o pesquisador atribuiu a si.
- Qualquer atualização do README ou auditoria exige reler blob SHA atual; não sobrescrever alterações concorrentes do outro agente.
- Em registro de progresso, separar número de documentos, afirmações cientificamente revisadas, validação instrumental, acertos de prova cega, aprovação editorial e estado de CI.
- Não incluir material de jw.org nem afirmações de origem espiritual em base científica sem distinguir sua natureza não instrumental. Direitos de imagens, marcas, artigos e datasets precisam de licença por item.
- NUNCA transformar uma pesquisa textual em declaração de que os pesos/neurônios do CRIVO aprenderam os novos assuntos.

**Resultado:** a documentação do procedimento de validação e parada ficou disponível para o outro agente. A certificação oficial da skill da main permanece 0/10 pelo último registro consultado; nada foi alterado em CI, main ou rede neural.
