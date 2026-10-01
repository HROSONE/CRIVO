# Auditoria 2 de 2 — coerência científica, métodos, matemática, descobertas 2026 e direitos

**Data da segunda passagem:** 2026-10-01. **Decisão:** **REPROVADA PARA ENCERRAMENTO DOCUMENTAL** (apesar dos reparos executados e controles estruturais positivos). Não foi uma segunda auditoria **satisfatória** nos termos do protocolo de conclusão. **Auditorias 1 e 2 foram realizadas pelo mesmo agente** e NÃO equivalem a duas revisões humanas ou metodologicamente independentes.  
**Primeira passagem:** [Auditoria 1: matriz de 279 afirmações e suas fontes](2026-10-01-auditoria-1-matriz-rastreabilidade-279-fatos.md). **Alcance distinto:** esta segunda passagem inspeciona coerência entre os 20 dossiês, mudanças de evidência ao longo do tempo, unidades, cálculos, bibliografia e limites de inferência.

## 1. Controle de escopo da segunda passagem

**Documentos inspecionados:** os 20 dossiês científicos referenciados no [índice de pesquisa](../README.md); protocolos/relatórios de auditoria não são contados como novos dossiês científicos. Todos foram consultados na branch durante esta segunda passagem em três grupos (8 + 8 + 4). Bibliografias presentes de dois tipos:
- **18 dossiês** com identificadores em linhas de tabela de fontes;
- **um dossiê** de dinâmica galáctica com bibliografia numerada **G1–G14** no formato de LISTA (não tabela);
- **um inventário** com links editoriais para dossiês e fontes institucionais sem tabela de códigos de referência.

Os códigos de fontes citados no corpo foram comparados com as definições bibliográficas correspondentes. O verificador inicial restrito ao cabeçalho `**G4 —` tinha marcado `G4` como ausente, mas a entrada é `4. **G4**, ...` e EXISTE na lista. **Falso positivo de parser, não referência perdida.** Não confundir verificação de rótulo com leitura integral de DOI.

**Navegação:** todas as **24 referências internas Markdown** encontradas nesses 20 dossiês apontam para nomes de arquivos presentes no índice da branch; os arquivos do índice haviam sido lidos pela auditoria anterior. Isso não testa todos os URLs EXTERNOS. Fontes da mesma agência, mesma missão ou mesmo estudo não foram contadas como confirmações independentes.

**Critério:** existência e coerência de IDs são necessários para curadoria, mas insuficientes para declarar 'verificado cientificamente'. A primeira auditoria foi corrigida após descobrir o verbete Lagrange no glossário NASA: **25 enunciados** com fonte pouco específica, **dois de Lagrange** com apoio conceitual parcial e **232** ainda não analisados semanticamente frase a frase.

## 2. Descoberta de 2026 ausente nos dossiês de DART — CORRIGIDA

A versão de 2022 da NASA documentava redução de **~32±2 minutos** no período **Dimorphos ao redor de Didymos**, inicialmente de **11 h 55 min para 11 h 23 min**. Atualizações do ajuste dinâmico posterior descrevem ~33 minutos no mesmo tipo de órbita.

**Evidência NOVA, publicada 06/03/2026:** Makadia et al., *Direct detection of an asteroid's heliocentric deflection: The Didymos system after DART*, *Science Advances* **12(10):eaea4259**, DOI https://doi.org/10.1126/sciadv.aea4259 . O estudo utilizou observações, inclusive **22 ocultações estelares entre outubro de 2022 e março de 2025**, e estimou mudança no período **do SISTEMA BINÁRIO ao redor do Sol** de cerca de **0,15 segundo**, num período de ~770 dias. A NASA/JPL publicou em 06/03/2026 https://www.jpl.nasa.gov/news/nasas-dart-mission-changed-orbit-of-asteroid-didymos-around-sun/ .

**Não fundir medidas:** redução de ~32–33 MINUTOS no período da lua não é redução de ~0,15 SEGUNDO do período heliocêntrico do par. **Ambas foram detectadas**, por métodos, escalas e precisões diferentes. É ERRADO ensinar que a DART só alterou a órbita interna ou que a órbita heliocêntrica ficou exatamente igual após o impacto.

**Correções EFETIVAMENTE gravadas nesta execução, na branch somente:**
1. [Corpos menores e DART](2026-10-01-corpos-menores-cometas-cinturoes-defesa-planetaria.md), commit `4df1142ab8c42ce530e22cf0cfdf74fc5c8767a9`: nova seção de duas escalas orbitais, tabela de inferência e fonte primária **P19**.
2. [Checagens numéricas](2026-10-01-checagens-numericas-dados-publicados-dimensoes.md), commit `087b38ec285879417c1a3877de7ca901fa32d11b`: nova advertência e referência **K12** para a detecção heliocêntrica.
3. [Matriz causal/ontológica](2026-10-01-ontologia-72-fichas-matriz-de-evidencias.md), commit `e9044c54ec6b63441a7c35c0d5a0a40a87e80170`: vínculo causal atualizado com duas mudanças distintas.

**Distinção do estudo de 2024:** NASA/JPL descreve em https://www.jpl.nasa.gov/news/nasa-study-asteroids-orbit-shape-changed-after-dart-impact/ ajuste de ~33 min e 15 s na órbita INTERNA e mudança de forma do satélite. Isso NÃO contradiz a análise heliocêntrica de 2026 nem invalida 32±2 min do anúncio inicial.

## 3. Quadro de consistência científica amostral

| Caso | Confronto do acervo com fonte externa | Conclusão limitada da auditoria |
| --- | --- | --- |
| DART: órbita interna e heliocêntrica | NASA 2022, JPL 2024 e artigo primário 2026 | **Nova evidência 2026 incorporada**; não converter ΔP da órbita interna em ΔP solar. |
| Lua, bacia Polo Sul–Aitken | Joy et al., https://www.nature.com/articles/s41550-024-02380-y | Autora principal K. H. Joy, publicado on-line 16/10/2024, volume 9 de 2025; meteorito NWA 2995 datado ~4,32–4,33 Ga; atribuição da formação da bacia condicionada à proveniência interpretada. Correção anterior preservada. |
| Radiação cósmica de fundo e Gaia | Documentação Gaia DR3 https://gea.esac.esa.int/archive/documentation/GDR3/ | Zero-point geral de paralaxe ~−0,017 mas NÃO é correção fixa para toda estrela; a DR3 conserva astrometria EDR3 e seus sistemáticos. |
| Energia escura DESI | Divulgação institucional da colaboração em https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/ | Medida Lyα full-shape de 30/07/2026 teve centro mais próximo de ΛCDM neste teste; isso não resolve em definitivo a natureza da energia escura. |
| DES Y6 e projeções da tensão S8 | Estudo primário DES https://arxiv.org/abs/2601.14559 | S8=0,789±0,012 e Ωm≈0,333 na combinação Y6 3×2pt sob ΛCDM; o artigo diferencia **2,6σ projetados em S8** de **1,8σ no espaço paramétrico completo**. Não declarar a tensão como refutação do modelo a partir do valor central isolado. |
| Estabilidade de Hill | Hamilton & Burns 1992 https://doi.org/10.1016/0019-1035(92)90005-R | Estudo técnico em torno de ASTEROIDES. Apoia a ressalva de que a esfera de Hill não é região de estabilidade universal, mas não mede diretamente toda população de luas planetárias. |
| Direitos NASA | NASA media: https://www.nasa.gov/nasa-brand-center/images-and-media/ | Conteúdos governamentais podem ter regras gerais de uso, porém logotipos, endossos, pessoas e conteúdo de TERCEIROS exigem cautela/licenças. Campo `dominio_publico` no JSON não substitui revisão item a item. |

**Bibliografia não exaustiva:** nesta passagem foram confirmados por acesso a fonte externa alguns estudos primários e comunicados, além de conferir URLs internamente. **Não foi concluída auditoria de cada URL/DOI de todas as bibliografias.**

## 4. Quinze verificações aritméticas independentes da escrita dos exemplos

**Método:** operações reexecutadas com os números e hipóteses que os dossiês citam; tolerância explícita de aproximação. NÃO são reduções de fotometria, simulações orbital-barianas, análises de mapas ou dados brutos.

| Relação e condição | Conta reexecutada | Resultado |
| --- | --- | --- |
| Mercúrio, Kepler ideal, a=0,39 AU | 365,25×sqrt(0,39³) | 88,9584 dias |
| Mercúrio, Kepler ideal, a=0,387 AU | 365,25×sqrt(0,387³) | 87,9340 dias |
| DART interno (valor inicial NASA) | 683−715 | −32 minutos |
| DART interno relativo ao pré-impacto | −32/715×100 | −4,4755% |
| DART heliocêntrico publicado, escala fracionária hipotética de comparação | 0,15/(770×86400) | 2,2547×10⁻⁹ do período, NÃO 4,48% |
| CMB térmico em z=7,31 | 2,725×8,31 | 22,64475 K |
| CMB térmico em z=1100 | 2,725×1101 | 3000,225 K |
| Exoplaneta SINTÉTICO, M=8M⊕ e R=2R⊕ | 8/2³ | ρ/ρ⊕=1 |
| Exoplaneta SINTÉTICO, erros independentes M=5%, R=2% | sqrt(0,05²+9×0,02²)×100 | 7,8103% |
| Tempo de esgotamento SINTÉTICO | 3×10⁹/3 | 10⁹ anos |
| Variação de reserva SINTÉTICA, entrada 5, SFR 3, R=0,4, η=0,8 | 5−(1−0,4+0,8)×3 | +0,8 M⊙/ano |
| H0=67,4, D=10 Mpc, BAIXO z | 67,4×10 | 674 km/s, componente cosmológica |
| Redshift sintético | 750/500−1 | z=0,5 |
| Relação Kepler ressonância periódica 2:1 | 2^(2/3) | 1,58740, semieixo maior sob MESMA massa central |
| Razão de parâmetros Planck | 0,120/0,0224 | 5,35714, razões de DENSIDADE cosmológica |

**Resultado da amostra:** **15/15 contas reproduziram os valores-alvo** sob as mesmas hipóteses didáticas. Isso não mede acertos do CRIVO nem garante que modelos físicos inteiros, código ou centenas de fórmulas de todos os dossiês estejam certos. As constantes, unidades e fontes dos valores precisam acompanhar qualquer versão integrada.

## 5. Lacunas que permanecem apesar da segunda inspeção

1. **A primeira auditoria bloqueou a aprovação por fonte:** **25 fatos** usam fontes que não justificam suficientemente os seus detalhes; **dois fatos sobre Lagrange foram falsos positivos**, pois o glossário NASA já contém o verbete. Exemplos: 12 fatos de métodos exoplanetários citam a página genérica `nasa_planetarios`; nove afirmações de Roche, Hill e ressonância citam `nasa_sistema` sem os mecanismos exigidos; três de escape não encontram verbete no glossário, e uma das três de Lagrange requer informação de estabilidade além do verbete geral. As 25 correções e dois refinamentos foram preparados em proposta para o integrador. A main não foi corrigida por esta execução.
2. **Ausência de revisão por pares do acervo completo:** a consulta bibliográfica amostral não aprova individualmente os 279 fatos; 232 seguem marcados com semântica não conferida, e **22** ficaram apenas com suporte conceitual parcialmente comparado. Revisor externo do conhecimento específico ainda não examinou o currículo completo.
3. **Matemática, reproduções e direitos:** as 15 contas são verificações de cálculos fornecidos, não exercícios novos com medições independentes; dados observacionais brutos e incertezas reais NÃO foram reprocessados. A classificação dos direitos de cada obra também permanece necessária antes de importar imagens/datasets.
4. **Avaliação cognitiva e prova cega:** foram deliberadamente mantidas fora desta branch e são responsabilidade do integrador; pesquisa extensa não comprova competências do modelo.
5. **Risco de atualizações recentes:** ciência avançou depois da redação original, como DART 2026; estatísticas DESI e DES Y6 variam por combinação de dados/versão. Novos achados exigem correção editorial focada, não declaração de conhecimento eterno.

## 6. Veredito conjunto das duas auditorias solicitadas

**Auditoria 1 EXECUTADA:** matriz de todos 279 fatos, 25 enunciados com fonte insuficientemente específica, dois de Lagrange reclassificados como parcialmente sustentados, e 232 ainda sem validação semântica → **NÃO APROVADA**.

**Auditoria 2 EXECUTADA:** coerência estrutural dos 20 dossiês, 24 vínculos internos, 15 checagens aritméticas com resultados conformes, correção da nova descoberta DART 2026 em três documentos, leitura cruzada de fontes selecionadas, direitos e dependências → **NÃO APROVADA PARA ENCERRAMENTO** pelas mesmas lacunas sistêmicas ainda abertas.

**Importante:** são duas passagens diferentes conduzidas pelo mesmo agente, não dois revisores independentes; o protocolo pede **DUAS AUDITORIAS FINAIS CONSECUTIVAS SATISFATÓRIAS**, que não podem ser registradas se achados importantes persistem. Não declarar módulo ou disciplina pronta enquanto os 25 defeitos essenciais de fonte não forem integrados/revistos e os demais problemas não forem resolvidos.

**Mudanças efetivas:** apenas documentos na branch `pesquisa/acervo-conhecimento-crivo`. Nenhuma mudança em `main`, treino, pesos, testes, CI, deploy, PR ou modelo. Certificação oficial permanece inalterada. **Próximo trabalho não deve ser terceira auditoria repetida com a mesma rubrica:** corrigir raízes das fontes em parceria com o integrador e confrontar as 279 frases com fontes especializadas/humanas; repetir as auditorias finais somente depois de sanar as causas que fizeram ambas reprovar.
