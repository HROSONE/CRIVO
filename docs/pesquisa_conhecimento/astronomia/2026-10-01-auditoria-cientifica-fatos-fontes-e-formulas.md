# Auditoria científica focalizada — atribuição, causalidade, evidência e fórmulas

**Realizada em:** 2026-10-01. **Escopo:** auditoria científica focalizada dos dossiês e da rastreabilidade da base ativa lida **somente** da `main`.  
**Estado:** **auditoria parcial com correções efetivamente gravadas na branch**; **NÃO** é nenhuma das duas auditorias finais satisfatórias requeridas para encerramento editorial. Nenhuma integração, treinamento, teste de CRIVO ou certificação ocorreu.

## 1. Método e inventário conferido

- Fonte do currículo canônico: `main:conhecimento_mundo.json`, lido sem editar. Existem **72 itens marcados `area=astronomia` e 255 afirmações** nesses itens. Há ainda `main:conhecimento_astronomia_luas.json` com **quatro luas e 24 afirmações**; a soma resulta em **279 afirmações nominais**, sem presumir que todos os conceitos em outros arquivos foram cobertos.
- As **255 afirmações do arquivo mundo** apontam para **23 IDs distintos de fonte**, e **nenhum ID indicado estava ausente do mapa `fontes`**. As 24 afirmações do arquivo de luas também apontam para fontes existentes em seu mapa. Isso é integridade REFERENCIAL, não aderência da fonte a cada frase.
- **84 das 255 afirmações do arquivo mundo citam o mesmo ID `nasa_glossario`**, URL https://science.nasa.gov/universe/glossary/ . O uso massivo de uma única página geral é uma concentração de proveniência, não prova de falsidade; exige verificar especificamente cada conceito e substituir fundamentação genérica por referência física adequada quando necessário.
- Todos os **20 dossiês científicos indexados** foram acessados na branch em duas remessas (nove e onze documentos). As referências numeradas **indicadas nos textos de 19 dossiês com formato de tabela** estavam definidas nas tabelas correspondentes, na checagem de correspondência de ID editorial. O dossiê de dinâmica galáctica usa **lista numerada G1–G14**, não tabela; um verificador restrito a tabelas inicialmente sinaliza G1–G14 por formato, mas isso NÃO equivale a referências ausentes. O mapa das 72 fichas usa links narrativos, sem IDs bibliográficos numerados.
- Comparações numéricas pontuais foram refeitas por cálculo independente de aritmética simples. Não foi executado pipeline observacional, espectro, imagem ou catálogo científico bruto.

### Interpretação do controle automatizado

`Existem referências` ≠ `referências provam a afirmação`.  
`Código da fonte presente` ≠ `a fonte discute o conceito com esse alcance`.  
`DOI resolve` ≠ `autor, data, unidades e interpretação estão corretos`.  
`Conta confere` ≠ `os dados de entrada foram reprocessados`.

## 2. Correção científica/bibliográfica REALIZADA — bacia lunar Polo Sul–Aitken

**Antes:** o documento de cronologia atribuía a publicação *Evidence of a 4.33 billion year age for the Moon's South Pole–Aitken basin* a **"Tartèse e colaboradores"**, chamando-a artigo de 2025, sem esclarecer data de publicação on-line.  
**Verificação:** o artigo primário indica **K. H. Joy como primeira autora**, **R. Tartèse como coautor**, publicação on-line **16/10/2024** e inclusão no volume **9, 55–65 (2025)**. O estudo data componentes do meteorito lunar **Northwest Africa 2995 (~4,32–4,33 Ga)** e INTERPRETA a proveniência desse material como compatível com a bacia, não mede diretamente o instante de colisão.

Fonte primária: https://www.nature.com/articles/s41550-024-02380-y ; registro biomédico bibliográfico independente: https://pubmed.ncbi.nlm.nih.gov/39866548/ .

**Correção escrita:** seção 8 e entrada **C20** em [cronologia, meteoritos e crateras](2026-10-01-cronologia-meteoritos-crateras-e-proveniencia.md). Commit **`0e152507d344bcba85d6de1b0d9cbbfd5b2a020c`**. **Classe:** erro bibliográfico confirmado; datas agora separam publicação on-line e volume.

## 3. Correção FÍSICA REALIZADA — mecanismo DART

**Antes:** uma linha da matriz causal afirmava `Temperatura/ejeção DART + modelo termofísico → alteração orbital`, misturando a pressão por emissão térmica de radiação (**Yarkovsky/YORP**) com a demonstração experimental de **impacto cinético DART**.

**Verificação:** NASA mede encurtamento do período de **Dimorphos em torno de Didymos** de **11 h 55 min para 11 h 23 min**, aproximadamente **32±2 minutos** na versão factual; o impacto e o momento dos fragmentos ejectados contribuíram para a alteração. Não foi uma demonstração de que o calor do DART desviou orbitalmente Dimorphos por Yarkovsky.

Fonte NASA: https://science.nasa.gov/solar-system/asteroids/didymos/ . Dossiê de pequenos corpos já separava Yarkovsky e DART.

**Correção escrita:** linha da [matriz ontológica e causal](2026-10-01-ontologia-72-fichas-matriz-de-evidencias.md) substituída por `impacto cinético + fotometria orbital antes/depois + dinâmica dos ejecta → redução do período orbital e transferência de momento`. Commit **`e0253fbb60cdbbdd8ed58493afbf999826c72c04`**. **Classe:** erro causal confirmado e corrigido.

## 4. Rastreabilidade INSUFICIENTE na main — SEM modificar a main

Duas famílias de afirmações estão cientificamente razoáveis em conteúdo, mas a fonte original indicada não é evidência suficientemente específica:

| Ficha ativa | Fonte atualmente associada na main | Problema identificado | Referência melhor, externa e verificável |
| --- | --- | --- | --- |
| `velocidade de escape` (três afirmações) | `nasa_glossario` → https://science.nasa.gov/universe/glossary/ | Não se encontrou entrada explícita `escape velocity` ou `escape speed` nesse glossário na consulta. Isso NÃO torna a fórmula falsa; impede considerar a associação `fonte→afirmação` individualmente verificada. | NASA/GSFC descreve `v_escape=sqrt(2GM/r)` e suas hipóteses: https://cosmicopia.gsfc.nasa.gov/qa_gp_gr.html ; definição e ressalvas em https://cdaweb.gsfc.nasa.gov/pub/documents/archived_websites/pwg.gsfc.nasa.gov/stargaze/Lkepl2nd.htm . |
| `esfera de Hill` (três afirmações) | `nasa_sistema` → https://science.nasa.gov/solar-system/solar-system-facts/ | Não há menção explícita a `Hill` na página geral pesquisada. A definição do fenômeno pode ser válida, mas a fonte indicada não sustenta diretamente o detalhe e a ressalva da estabilidade. | Hamilton & Burns (1992), *Icarus* 96:43–64, DOI https://doi.org/10.1016/0019-1035(92)90005-R ; análise adicional https://academic.oup.com/mnras/article/527/3/4371/7424981 . |

**Ação executada sem violar a divisão de agentes:** bibliografia **T11** adicionada ao [caderno de matemática orbital](2026-10-01-matematica-orbital-observacional-inversoes-limites.md) e **S21** ao [dossiê de luas](2026-10-01-luas-ressonancias-mares-oceanos.md), ambos explicitando limite das conclusões extrapoladas a luas de planetas. Commits **`b37a2ec218dd95c7262da7a56d7eae46fd0bf06f`** e **`05d3c6b04c7bc5d7d3763c2d32bfb49811e1fda6`**.

**Pendente para o integrador:** atualizar na **main**, após revisão própria e testes, a proveniência dessas seis afirmações se decidir importar correções. **A main NÃO foi alterada** por esta auditoria.

## 5. Verificação de números dos próprios dossiês

Contas realizadas com as mesmas hipóteses explicitadas na documentação, sem pretensão de medir instrumentos:

| Teste | Cálculo de controle | Resultado e conclusão |
| --- | --- | --- |
| Mercúrio com `a=0,39 AU` | `365,25×sqrt(0,39³)` | **88,9584 dias**, consistente com arredondamento ~89 dias, mas não medição orbital nova. |
| Mercúrio com `a=0,387 AU` | `365,25×sqrt(0,387³)` | **87,9340 dias**, próximo de 88 dias, sob Kepler ideal solar. |
| DART | `(683–715)/715×100` | **−4,4755%** do período da binária; não fração do período heliocêntrico. |
| Densidades Planck | `0,120/0,0224` | **5,3571**, razão dos parâmetros de densidade sob `ΛCDM`, não razão do número de partículas. |
| CMB em `z=1100` | `2,725×1101` | **3000,225 K**, aproximado para época de recombinação. |
| CMB em `z=7,31` | `2,725×8,31` | **22,64475 K**, não temperatura de toda nuvem da época. |
| Exoplaneta sintético `M=8M⊕, R=2R⊕` | `8/2³` | **1**, razão de densidades médias; não identidade da composição interna. |
| Exoplaneta sintético, erros 5% massa e 2% raio | `sqrt(0,05²+9×0,02²)` | **7,8103%**, sob erro pequeno e NÃO correlacionado. |

**Conclusão da checagem de contas:** nesses oito exemplos não foi encontrado erro aritmético/material; a validação de pressupostos e dados brutos continua separada. A fórmula da estabilidade de Hill citada foi comparada a estudo de estabilidade; sua esfera nominal não é garantia de estabilidade em inclinação/excentricidade arbitrária.

## 6. Fontes revisadas nesta rodada (além de bibliografia já existente)

- DESI, atualização **30/07/2026**, https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/ : resultado `full-shape` Lyα deslocou centro em direção a `ΛCDM` num teste específico; não é demonstração conclusiva de inexistência de evolução da energia escura.
- DES Year 6, https://arxiv.org/abs/2601.14559 : `S8=0,789±0,012` em `ΛCDM` para a combinação especificada; uma discrepância projetada no parâmetro não equivale automaticamente a uma refutação estatística conjunta.
- Khan et al. (2023), https://www.nature.com/articles/s41586-023-06586-4 : raio inferido do núcleo marciano `1675±30 km`, camada basáltica/silicatada **fundida** de `150±15 km`; valores são modelados a partir do InSight, não sondagem direta por câmera.
- Scognamiglio et al. (2026), https://www.nature.com/articles/s41550-025-02763-9 : mapeamento por lentes fracas no COSMOS-Web com cerca de **129 formas úteis/arcmin²** e região `0,77°×0,70°`. Contagem de objetos na foto e catálogo de formas não são a mesma coisa.
- Joy et al., periódico 2025, publicado on-line em 2024, https://www.nature.com/articles/s41550-024-02380-y .
- Hamilton & Burns, 1992, https://doi.org/10.1016/0019-1035(92)90005-R .
- NASA DART, https://science.nasa.gov/solar-system/asteroids/didymos/ .
- NASA Newton, https://science.nasa.gov/learn/basics-of-space-flight/chapter3-3/ .
- NASA glossário, https://science.nasa.gov/universe/glossary/ .
- NASA Solar System Facts, https://science.nasa.gov/solar-system/solar-system-facts/ .

Essas consultas servem para **uma auditoria científica temática e de proveniência**, não correspondem a uma revisão exaustiva das ~centenas de URLs da branch. Links de artigos são fornecidos para consulta; não foram reproduzidos PDFs, artigos integrais ou imagens com direitos de terceiros.

## 7. Classificação do resultado, pendências e próximos gates

| Eixo | Resultado verificável |
| --- | --- |
| Integridade de IDs das 72 fichas e quatro luas | **Verificação referencial positiva:** nenhum ID de fonte citado estava ausente do objeto de fontes dos respectivos arquivos; a suficiência semântica dessas fontes não foi verificada por completo. |
| Integridade de citações de dossiês | **Triagem de 20 documentos**, com referências em tabelas ou listas; não identificadas referências editoriais ausentes na checagem superficial, mas formato de listas G1–G14 exige parser separado. |
| Erro bibliográfico lunar | **Confirmado e corrigido na branch.** |
| Confusão causal DART/Yarkovsky | **Confirmada e corrigida na branch.** |
| Proveniência escape/Hill na main | **Seis fatos candidatos a correção de fonte pelo integrador**; sem alterações na main. |
| Matemática | Oito resultados aritméticos amostrados conferiram; matemática total ainda não auditada. |
| Evidência observacional e licenças | Amostra de primários e institucionais consultada; sem auditoria da licença de todas as figuras/datasets. |
| Competência do CRIVO | NÃO medida nem aumentada por edição documental. |

**Bloqueio científico remanescente:** a verificação individual de 279 afirmações, o exame de fontes/DOIs não selecionados, propagação real de erros e revisão qualificada externa continuam abertos. Não alegar que os restantes são corretos por amostragem. A documentação nominal de dez módulos não satisfaz duas auditorias finais consecutivas sem lacunas científicas centrais.

**Próxima execução de pesquisa:** auditar sistematicamente os **255 fatos do arquivo mundo e 24 fatos lunares** por fonte e mecanismo; classificar cada relação como `suportado diretamente`, `inferência apoiada`, `fonte genérica insuficiente`, `desatualizado/contradito` ou `sem confirmação`; registrar correções NA BRANCH. É responsabilidade do outro agente integrar à base ativa depois, sem reaproveitar testes cegos do projeto. Apenas uma nova auditoria que examine todos os dez módulos e não encontre erros centrais poderá contar como a primeira das duas revisões finais satisfatórias.

**Governança:** main, pesos, CI, PRs, workflows e testes não foram alterados. **Certificação = 0/10** no último registro da skill da main, não reclassificada por esta pesquisa.
