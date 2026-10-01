# Astronomia — Matéria escura, dinâmica, lentes e crescimento da estrutura cósmica

**Pesquisa:** 2026-10-01. **Módulos:** 5 (galáxias), 6 (cosmologia), 7 (observação), 8 (matemática) e 9 (inferência).
**Status:** PESQUISA PARA REVISÃO; NÃO integrada, NÃO treinada, NÃO certificada. Material exclusivamente documental em branch isolada.
**Não duplicar:** dossiê existente de [dinâmica galáctica](2026-10-01-dinamica-galactica-via-lactea-montagem-hierarquica.md) introduz curva de rotação e a Via Láctea; [lentes e buracos negros](2026-10-01-lentes-buracos-negros-e-distancias.md) aborda princípios ópticos; aqui se comparam as linhas de evidência para massa gravitacional não luminosa e seus erros, incluindo resultados de 2025–2026.

## 1. Qual é a proposição científica?

Matéria escura é o nome atribuído a uma componente gravitacional cuja contribuição à dinâmica e à estrutura cósmica não corresponde à distribuição observada de gás, poeira, estrelas e outros bárions sob o quadro padrão da gravitação/cosmologia. **Não significa** substância fotografada, nevoeiro preto ou material identificado em laboratório. A evidência é inferida de movimentos, deflexão de luz, estruturas em colisão e anisotropias da radiação de fundo. O modelo ΛCDM trata uma componente fria e não bariônica, mas a composição microscópica ainda não foi determinada por essas observações [M1,M2].

**Separação de níveis:**
1. Observação instrumental: velocidade Doppler de gás, espectro de estrelas, formas de fontes de fundo, raios X do gás de aglomerados, mapas CMB.
2. Reconstrução: distribuição de massa/potencial gravitacional ou densidades cosmológicas segundo equações adotadas.
3. Interpretação: presença de massa não explicada pela matéria luminosa nas hipóteses do modelo.
4. Hipótese microscópica: natureza das partículas, autointeração, propriedades quânticas. A etapa 3 NÃO resolve a etapa 4.

## 2. Curvas de rotação e o papel dos bárions

Para massa esférica ideal e órbita circular, `v_c²(r)=GM(<r)/r`. Se toda massa gravitante estivesse concentrada no centro e M(<r) deixasse de crescer, a curva seria kepleriana: v∝r^(-1/2). A observação de velocidades externas quase constantes em muitas espirais motivou modelos com massa adicional distribuída por raios grandes [M1,M3].

**Mas galáxias são discos:** em uma galáxia achatada, gravidade de um anel exterior influencia o campo dentro dele; a expressão esférica não permite decompô-la exatamente. Balanço de massa modelado inclui disco de estrelas, gás H I e H₂, bojo e halo sob pressupostos de razão massa-luz, inclinação do disco e distâncias.

**SPARC** (Lelli, McGaugh e Schombert 2016) reúne curvas de rotação e fotometria de infravermelho 3,6 μm de **175 galáxias de disco** em ampla variedade de brilhos e morfologias. O levantamento mede velocidades de gás e luz para restringir contribuição bariônica, mas as frações de massa dependem da escolha de massa/luminosidade e hipóteses gravitacionais [M3].

**Não converter todo resultado da curva da Via Láctea em lei universal:** por estarmos dentro dela, reconstruir posições e velocidades exige modelos do Sol, distâncias, velocidades de estrelas e não circularidade. O dossiê de Gaia já explica por que uma curva ligeiramente declinante não elimina automaticamente a evidência cosmológica/circumaglomerada de massa escura.

### Cálculo ilustrativo de escala orbital (não dados SPARC)

Com G ≈ 4,3009×10^-6 kpc (km/s)²/M☉, para órbita circular em potencial ESFÉRICO com raio r=10 kpc e v=200 km/s:

`M(<r)=v²r/G ≈ (200²×10)/(4,3009×10^-6) ≈ 9,30×10^10 massas solares`.

A conta informa massa gravitacional equivalente DENTRO de r no modelo esférico. NÃO demonstra que 9,30×10^10 massas solares são matéria escura, pois falta subtrair bárions e avaliar geometria; não é resultado observado de galáxia específica.

## 3. Aglomerado da Bala: deslocamento entre gás e massa inferida

Em aglomerados de galáxias em colisão, grande parte dos bárions pode estar em plasma quente emissor de raios X, que interage por colisões; as próprias galáxias são muito menos afetadas por colisões diretas estrela–estrela.

**Medições distintas:**
- Chandra mede emissão X de gás quente e permite modelar sua temperatura/densidade.
- Webb/Hubble medem centenas/milhares de fontes de fundo cujas imagens sofrem lente gravitacional.
- A reconstrução da lente estima distribuição da massa total projetada, sob geometria e calibração.

A análise Webb divulgada em **30/06/2025** refinou massa do Aglomerado da Bala usando imagens mais profundas, descrevendo alinhamento das concentrações de massa inferidas com galáxias, enquanto o gás quente aparece deslocado [M4]. É evidência importante para componente gravitacional que não sofre o mesmo arrasto do gás.

**Limite físico:** mapa azul de matéria escura é SOBREPOSIÇÃO COMPUTACIONAL da massa gravitacional reconstruída e componentes atribuídos, não fotografia em luz visível de partículas invisíveis. Deslocamento não determina sozinho seção de choque microscópica precisa, nem que toda teoria gravitacional alternativa esteja excluída sem modelagem separada. O sistema fornece restrições importantes sobre possíveis autointerações sob hipóteses [M4].

**Causa versus localização:** a distribuição estelar total não é idêntica à distribuição da massa; lentes respondem à gravitação de TODOS os componentes ao longo da linha de visão. Para inferir massa escura, comparar gravidade total a mapa bariônico; não chamar cor azul observação espectral do escuro.

## 4. Lente fraca: por que centenas de milhares de galáxias ajudam

Efeitos de lente fraca modificam sutilmente formas e orientação estatística de galáxias de fundo. A forma observada é mistura de elipticidade intrínseca, distorção gravitacional, PSF instrumental, ruído e efeitos de seleção. O sinal individual geralmente é muito menor do que a variabilidade natural de formas; estimadores combinam grandes populações e correlações [M5,M6].

**Esquema de inferência:**
1. Identificar fontes de fundo e selecionar qualidade/redshift.
2. Modelar PSF (como instrumentos e condições borram e deformam imagens).
3. Corrigir vieses de forma e estimar shear tangencial/2D.
4. Combinar formas e distâncias lente–fonte para reconstruir mapa de massa projetada.
5. Calibrar com simulações e validação cruzada. O mapa não é reprodução direta de uma distribuição 3D única.

**Problemas concretos:** se galáxias compartilham orientação intrínseca devido a ambientes comuns, parte da correlação aparente não é lente. Se fotoredshifts estiverem enviesados, a eficiência geométrica e o mapa de massa ficam enviesados. Efeitos de feedback bariônico podem deslocar gás e modificar distribuição total em escalas pequenas [M5,M6].

**Degenerescência de massa–folha:** em certas reconstruções de lentes, adicionar um componente de densidade aproximadamente uniforme e reescalar a fonte pode deixar parte dos observáveis de forma essencialmente invariante. A extrapolação de um mapa de shear para MASSA ABSOLUTA requer informações/condições adicionais, como amplificação e dados em vários redshifts. Não apresentar mapa fraco como solução única sem hipóteses [M5].

## 5. Webb COSMOS-Web em 26/01/2026: mapa muito detalhado, mas ainda inferencial

Scognamiglio e colaboradores publicaram em *Nature Astronomy* em janeiro de 2026 um mapa de massa por lente fraca no campo COSMOS-Web. O estudo informa área angular de **0,77°×0,70°**, resolução da massa reconstruída de aproximadamente **1 minuto de arco** e densidade de formas úteis da ordem de **129 galáxias por minuto de arco quadrado**, explorando imagens em diferentes filtros [M7].

A NASA/JPL divulgou a pesquisa em **26/01/2026**, mostrando região de ~0,54 grau quadrado com **quase 800 mil galáxias na imagem mais ampla**. Atenção: a contagem de galáxias que aparecem na imagem não é necessariamente igual ao catálogo que passa todos os cortes de qualidade de formas, redshift e modelagem para lentes. O artigo é a referência para interpretar essa distinção [M7,M8].

**Mecanismo de nova resolução:** mais fontes de fundo bem medidas → melhor amostragem do shear → reconstrução menos suavizada de filamentos/halos e maior resolução angular, condicionada a sistema de ruído e PSF. Não inferir 'as partículas individuais foram vistas' nem prometer acesso a todo halo tridimensional de uma única projeção.

**Limite dos dados:** campo profundo ≠ mapa de todo Universo. Quantificar conclusões para populações globais exige amostras representativas, volume cosmológico e controlar variância cósmica. Mesmo imagens com milhares de objetos num pequeno campo podem ter viés ambiental.

## 6. CMB: uma evidência independente de órbitas em galáxias

Os picos acústicos da radiação cósmica de fundo respondem a densidade bariônica, potencial gravitacional, história térmica e geometria. A colaboração Planck obteve, sob ΛCDM de seis parâmetros, densidades físicas `Ω_c h²≈0,120` para matéria escura fria e `Ω_b h²≈0,0224` para bárions, com incertezas publicadas e combinações de dados específicas [M2].

**O que é direto e indireto:** detector mede anisotropias de temperatura/polarização em diferentes frequências; ajustar densidades é problema inverso. O valor da razão `Ω_c h²/Ω_b h²≈0,120/0,0224≈5,36` é um quociente de PARÂMETROS INFERIDOS sob ΛCDM; não é contagem de cinco partículas escuras para cada próton nem porcentagem de toda energia cósmica sem outras componentes.

A concordância entre estrutura e CMB pode apoiar um quadro físico conjunto, mas não se deve tratar parâmetros de modelo como medição diretamente fotografada. Comparar hipóteses alternativas requer rodar modelos sobre vários observáveis (CMB, lentes, velocidades, BAO), respeitando a literatura e suas diferentes limitações [M2,M6].

## 7. Crescimento de estrutura: porque não basta saber a geometria do Universo

Galáxias, filamentos e aglomerados resultam do crescimento gravitacional de pequenas perturbações, condicionado à expansão, à dinâmica de matéria comum, aos possíveis componentes escuros e à evolução de potencial. Observações em diferentes redshifts permitem inferir *crescimento* além de *distância*. A força da lente fraca depende tanto da geometria observador-lente-fonte quanto da massa/estrutura em cada época [M5,M6].

**Três estatísticas diferentes:**
- `Ω_m`: densidade cosmológica atual de matéria em unidades da densidade crítica, sob modelo.
- `σ_8`: amplitude estatística de flutuações de matéria numa escala definida de 8 Mpc/h (esferas comóveis), não velocidade de galáxia.
- `S_8=σ_8 sqrt(Ω_m/0,3)`: combinação frequentemente restringida por lentes fracas; valor depende dos conjuntos de dados e do modelo.

A análise Planck sob base-ΛCDM apresentou `Ω_m=0,315±0,007`, `σ_8=0,811±0,006`, `S_8≈0,831±0,013` (com convenções publicadas) [M2]. A colaboração Dark Energy Survey publicou análise de seis anos (Y6; versão divulgada janeiro de 2026) com `S_8≈0,789±0,012` e `Ω_m≈0,333` em ΛCDM na combinação indicada [M9].

**Interpretação prudente:** o deslocamento de valores centrais é indício de discrepância a examinar, não demonstra por si só que o modelo padrão foi falsificado. Sua significância exige comparar correlações, parâmetros, métodos, seleção e sistemáticos; outras análises e publicações podem concordar mais estreitamente. As próprias equipes documentam limites de modelagem, incluindo feedback bariônico, alinhamentos intrínsecos e não linearidades [M9,M10].

**Desafio específico:** matéria ordinária não é simples componente passivo; ventos estelares/AGN redistribuem gás, alterando perfis de massa total. Ignorar feedback pode simular conflito em lentes de pequena escala; remover todas as escalas difíceis reduz informação e também exige justificar as exclusões [M10].

## 8. Teorias concorrentes e estado de conhecimento

Modelos com halos de partículas escuras são componentes estabelecidos do quadro cosmológico ΛCDM e possuem capacidade de explicar diversos observáveis. Existem também alternativas de gravitação modificada e formulações híbridas que procuram explicar a dinâmica sem a mesma matéria escura em algumas escalas.

**Critério para comparação científica:** testar a MESMA teoria contra curvas de rotação, dispersões, lentes, sistemas de aglomerados, formação de estrutura, CMB e expansão, incluindo parâmetros livres, erros sistemáticos e dados fora do ajuste. Não concluir que ajuste pontual de uma curva elimina necessariamente evidências de lentes/aglomerações; também não tratar qualquer alternativa matemática como refutação automática sem avaliação quantitativa.

**Limite do conhecimento atual:** detecção cosmológica da gravidade adicional não identifica por qual partícula/teoria microscópica ela se manifesta; experimentos subterrâneos e buscas astrofísicas fornecem restrições adicionais, frequentemente com resultados nulos para certos intervalos, sem inferir inexistência de toda família de hipóteses [M1,M2].

## 9. Matriz de casos de raciocínio científico

| Enunciado simplista | Explicação cientificamente limitada |
| --- | --- |
| 'A imagem azul da NASA fotografou matéria escura' | Azul representa inferência espacial de massa a partir de distorções de fontes. |
| 'Uma curva plana mede a massa só de matéria escura' | A curva estima potencial combinado; decomposição depende de gás/estrelas/geometria. |
| 'Galáxia de alto brilho possui necessariamente o maior halo' | Luz total e distribuição de halo não têm relação 1:1 sem dispersão/seleção. |
| 'Hubble viu a substância escura na colisão' | Chandra mede gás; Hubble/Webb medem lentes; matéria escura é interpretação da massa reconstruída. |
| 'Há 800 mil galáxias na foto; 800 mil medidas idênticas de shear' | Número visual e catálogo com cortes de PSF/redshift não são a mesma população. |
| 'CMB mede partículas individuais de matéria escura' | CMB permite inferir parâmetros de densidade sob modelos de plasma e expansão. |
| 'S8 de DES diferente de Planck resolve toda teoria cosmológica' | É necessário tratamento de erros, amostras e variáveis/cosmologias conjuntas. |
| 'Sonda que não detectou candidato X prova não existir nada escuro' | Limites dependem do experimento, parâmetros e seção de choque do modelo. |
| 'Uma região sem galáxias não tem massa' | Distribuição luminosa pode ser pobre sem gravidade total nula. |

## 10. Roteiro de futura validação pelo agente integrador

1. Isolar 5–10 conceitos e suas condições; selecionar exemplos não vistos pelo modelo para avaliação, de várias classes de galáxias.
2. Formular pergunta sobre hipótese falsa com explicação causal, não só correspondência lexical.
3. Separar 'quantidade inferida' de 'medida direta': curva de rotação, shear, mapa de raios X, CMB.
4. Se pedir massa a partir de velocidade circular, declarar geometria, raio, unidades e presença de bárions; exigir recusa de conclusão única sem dados adicionais.
5. Para S8, obrigar indicar época, modelo e colaboração em vez de número absoluto isolado.
6. Para resultado de Webb, diferenciar fonte visual, amostra de formas e inferência de massa.
7. Criar prova inédita cega que não reutilize formulações aqui publicadas; essas propostas são editoriais e não foram testadas.

## 11. Referências, limitações de fonte e direitos

| ID | Referência verificada | Escopo e ressalvas |
| --- | --- | --- |
| M1 | NASA Science, *Dark Matter*: https://science.nasa.gov/dark-matter/ | Síntese institucional de curvas de rotação, lentes e natureza não estabelecida; não artigo primário. |
| M2 | Planck Collaboration (2020), *Planck 2018 results. VI. Cosmological parameters*, DOI https://doi.org/10.1051/0004-6361/201833910 | Resultados modelados de CMB com hipóteses ΛCDM e limites; publicação técnica. |
| M3 | Lelli, McGaugh & Schombert (2016), *SPARC: Mass Models for 175 Disk Galaxies*, arXiv https://arxiv.org/abs/1606.09251 ; DOI https://doi.org/10.3847/0004-6256/152/6/157 | Estudo primário de rotação/fotometria. Preprint é acesso, não autorização automática de republicação. |
| M4 | NASA/Webb + Chandra (30/06/2025), *Webb Pierces Bullet Cluster, Refines Its Mass*: https://science.nasa.gov/missions/webb/nasa-webb-pierces-bullet-cluster-refines-its-mass/ | Gás em raios X vs. massa inferida por lentes; mapa em falsas cores. |
| M5 | NASA/Euclid (Caltech), *Weak Lensing*: https://euclid.caltech.edu/page/weak-lensing | Cautela com PSF, redshift fotométrico e alinhamentos intrínsecos; material didático de projeto. |
| M6 | ESA/Euclid Consortium, *Euclid: Overview of Mission* (A&A, 2025), DOI https://doi.org/10.1051/0004-6361/202450810 | Projeto e métodos estatísticos, revisão de sistemáticos e cosmologia. |
| M7 | Scognamiglio e colaboradores (2026), *An ultra-high-resolution map of (dark) matter*, Nature Astronomy: https://doi.org/10.1038/s41550-025-02763-9 | Pesquisa primária com COSMOS-Web ~0,77°×0,70°; amplitude de fontes e mapa de shear; verificar licença de publicação separadamente. |
| M8 | NASA/JPL (26/01/2026), *Reveals New Details About Dark Matter’s Influence on Universe*: https://www.nasa.gov/missions/webb/nasa-reveals-new-details-about-dark-matters-influence-on-universe/ | Comunicação do estudo M7, não dado independente; ~800 mil galáxias na visualização mais ampla. |
| M9 | Dark Energy Survey Collaboration, *Year 6 Results: Cosmological Constraints from Galaxy Clustering and Weak Lensing* (2026): https://arxiv.org/abs/2601.14559 | S8, Ωm sob ΛCDM em 3×2pt; datas e versões do preprint precisam acompanhar futuras revisões. |
| M10 | DES Y6 Collaboration (03/09/2026), *Weak lensing and galaxy clustering cosmological analysis framework*, Phys. Rev. D, DOI https://doi.org/10.1103/8n76-f6ln | Pipeline, modelos não lineares, feedback bariônico e covariâncias; direitos integrais NÃO presumidos. |
| M11 | NASA/Hubble, *Maps the Cosmic Web of Clumpy Dark Matter in 3-D*: https://science.nasa.gov/missions/hubble/nasa-hubble-maps-the-cosmic-web-of-clumpy-dark-matter-in-3-d/ | Precedente observacional; reconstrução de lentes e múltiplos redshifts, não foto 3D de partículas. |
| M12 | Bailer-Jones et al. (2021), *Estimating distances from parallaxes. V.*, https://bailer-jones.www3.mpia.de/gedr3_distances.html | Distância/seleção Gaia: outra dimensão de medidas inferenciais; métodos aprofundados em dossiê separado. |

**Direitos:** texto autoral novo, sem reprodução de figuras, mapas/arquivos de dados, artigos completos ou extratos extensos. Licença de artigos é específica; NASA/ESA/Euclid/Webb incluem direitos de terceiros, avisos sobre endosso e uso de marca/imagem. Consultar https://www.nasa.gov/nasa-brand-center/images-and-media/ e as condições próprias do periódico/dados antes de integrar produtos de mídia.

## 12. Lacunas e estado

**Ampliação:** comparação de linhas de evidência dinâmicas, colisões de aglomerados, lente fraca moderna JWST, CMB, curvas SPARC e DES 2026; exemplos matemáticos com hipóteses.

**Bloqueios para fechar módulo 5/6:** relação quantitativa halo–galáxia e funções de massa/luminosidade, estudos multiescala com sistemáticos e dados públicos reprocessados independentemente, análise de cenários alternativos com a mesma amostra e revisão científico-editorial completa. O próximo dossiê de métodos visa tornar unidades e limites de medição reproduzíveis.

**Separação:** material investigado não foi enviado para a main nem convertido em treino; consulta simbólica/neural não medida; certificação da skill ainda 0/10.
