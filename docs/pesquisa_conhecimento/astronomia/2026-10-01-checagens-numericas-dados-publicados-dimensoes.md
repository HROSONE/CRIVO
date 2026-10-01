# Astronomia — verificações numéricas com dados publicados, unidades e pressupostos

**Data:** 2026-10-01. **Módulos:** 2, 4, 6, 7 e 8.  
**Estado:** MATERIAL DOCUMENTAL PARA REVISÃO; não foi integrado, treinado, certificado ou testado no CRIVO.  
**Método declarado:** os números de entrada abaixo foram retirados de fontes institucionais publicadas, e as relações são álgebra dimensional reprodutível. **Não houve download de catálogo FITS, cálculo estatístico de amostras, nem verificação por instrumento independente nesta execução.** Quando um número é hipotético, é rotulado como tal; não tratar como observação.

## 1. Kepler em escalas solares: checagem de Mercúrio

**Dados institucionais aproximados:** Mercúrio leva 88 dias para percorrer uma volta em torno do Sol e tem distância orbital característica da ordem 0,39 AU; Terra, por definição aproximada de unidade, ~1 AU e 1 ano. NASA ensina `P²=a³` em unidades anos/AU para pequenos corpos em torno da mesma massa solar [K1,K2].

**Cálculo com números arredondados:**
- para `a=0,39 AU`, `P=sqrt(0,39³)≈0,2436 anos`;
- multiplicar por ~365,25 dias/ano resulta `P≈89,0 dias`;
- adotar `a≈0,387 AU` mais preciso dá `P≈0,24075 anos≈87,9 dias`, próximo dos 88 dias citados.

**O que é validado:** coerência aproximada entre período e semieixo num modelo de corpo-teste. **Não é** medição independente do período, não substitui órbita n-corpos nem estabelece excentricidade/campo relativístico.

## 2. DART: período de Dimorphos antes/depois e porcentagem

**Dado publicado:** NASA descreve a órbita de Dimorphos de 11 h 55 min antes do impacto e 11 h 23 min depois; redução de ~32 min, com diferenças de arredondamento em atualizações posteriores [K3,K4].

**Conversão:** `P_antes=11×60+55=715 min`; `P_depois=11×60+23=683 min`. `ΔP=-32 min`. Redução fracional `-32/715≈-0,04476`, isto é, **−4,48%** com arredondamento.

**Não extrapolar:** a variação percentual do período da lua **não** é a variação percentual da órbita heliocêntrica do sistema Didymos; efeito do impacto incluiu momento dos fragmentos e é dependente do alvo. **Evidência publicada em 06/03/2026**, posterior às primeiras análises de 2022–2024, mostra que a DART **também** produziu alteração mensurável, MAS MUITO MENOR, do período do sistema em torno do Sol: cerca de **0,15 segundo para uma órbita de ~770 dias**, a partir de observações incluindo ocultações estelares [K12]. Não afirmar que o período solar ficou rigorosamente inalterado.

## 3. Astrometria: valores publicados versus exemplo sintético

**Dados da Gaia:** Gaia DR3 contém medições de paralaxe com erros e sistemáticos, inclusive correção de zero que depende de cor, magnitude e posição. Documentação ESA informa deslocamento global típico perto de −0,017 milissegundo de arco, que NÃO deve ser somado uniformemente a todo objeto [K5,K6].

**Exemplo sintético A (não Gaia):** `p=10,0±0,2 mas` → `d=1000/p=100 pc` e `σ_d≈(1000/p²)σ_p=2 pc` por linearização. O valor de 100±2 pc NÃO contém o zero-point instrumental.

**Exemplo sintético B (não Gaia):** `p=0,2±0,1 mas` → valor ingênuo 5000 pc, mas com 50% de erro relativo a posterior de distância é assimétrica e sensível à distribuição a priori. Não relatar 5000±2500 pc como intervalo universalmente calibrado [K6].

## 4. Planck: razão de densidades de matéria fria escura e bariônica

**Parâmetros publicados:** na análise Planck-ΛCDM de seis parâmetros, `Ω_c h²≈0,120` e `Ω_b h²≈0,0224` [K7].

**Conta:** `(Ω_c h²)/(Ω_b h²)=0,120/0,0224≈5,357`. Isso exprime razão de **parâmetros cosmológicos de densidade** sob aquele modelo e dados: NÃO significa cinco partículas de matéria escura por próton, número observado diretamente de partículas ou densidade de uma galáxia específica.

**Incerteza:** sem a matriz de covariância e incerteza completa dos parâmetros, não inventar erro de razão nem alegar desvios estatísticos de modelos concorrentes.

## 5. CMB e temperatura em redshift

**Fonte institucional:** NASA/ESA fornecem T_CMB hoje de aproximadamente 2,725 K e descrevem época de recombinação de z~1100 [K8,K9].

**Relação:** sob expansão e espectro térmico `T(z)=T0(1+z)`; em z=1100, `T≈2,725×1101≈3000,2 K`. O cálculo recupera a ordem de grandeza da temperatura da recombinação.

**O que não significa:** não mede temperatura exata do Sol, nem da superfície de uma galáxia; valor aproximado da redshift não descreve largura temporal do desacoplamento nem a física de todos os átomos. Para z=7,31, `T≈2,725×8,31≈22,65 K`, relevante ao contraste de linhas frias; não assumir que todo gás naquela época tinha temperatura exatamente igual a essa radiação [K8,K10].

## 6. Densidade média de exoplaneta com massa/raio hipotéticos

**Sem planeta real:** massa 8 vezes a terrestre e raio 2 vezes o terrestre implicam `ρ/ρ_Terra=(M/M_Terra)/(R/R_Terra)³=8/8=1`, assumindo volume esférico. A inferência de **densidade média igual** não determina camadas, composição, tectônica ou história geológica.

**Propagação:** se erros relativos de M=5% e R=2% fossem pequenos e independentes, `(σρ/ρ)≈sqrt[(0,05)²+9(0,02)²]≈0,0781≈7,8%`. Se as duas grandezas compartilham calibrações, a matriz de covariância deve entrar e o resultado pode mudar. Este cálculo é exemplo de propagação, não incerteza publicada de planeta [K11].

## 7. Dado orbital: período versus massa

Considere dois satélites circulares fictícios com semieixos a1 e a2=4 a1 orbitando a mesma massa central dominante. Kepler fornece `P2/P1=(a2/a1)^{3/2}=8`. A relação é condicional; em satélites reais com marés, ressonâncias e gravitação adicional, soluções n-corpos podem deslocar períodos e órbitas. Propriedades de excentricidade, composição e temperatura não são identificadas por uma única razão entre períodos [K1].

## 8. Registro de incerteza para curadoria

| Valor | Tipo | Modelo/versão | O que não foi verificado por este documento |
| --- | --- | --- | --- |
| Mercúrio ~88 d | Dado institucional aproximado | NASA + terceiro Kepleriano | Reprocessamento independente de efemérides |
| DART ~32 min | Medição publicada do sistema binário | NASA, 2022 e atualizações | Nova estimativa com dados brutos fotométricos |
| Gaia −0,017 mas | Sistemático global aproximado | Gaia DR3, dependências conhecidas | Correção por estrela concreta |
| Planck 0,120/0,0224 | Parâmetros cosmológicos inferidos | ΛCDM Planck 2018/2020 | Cosmologia alternativa e covariância da razão |
| CMB 2,725 K | Medição instrumental publicada | COBE + ajustes subsequentes | Reprocessamento de espectro FIRAS |
| Cálculos de densidade sintética | Exemplo matemático | Modelo de esfera | Qualquer composição ou detecção real |

## 9. Fontes rastreáveis

| ID | Fonte e link | Status de evidência |
| --- | --- | --- |
| K1 | NASA Science, *Orbits and Kepler's Laws*, https://science.nasa.gov/solar-system/orbits-and-keplers-laws/ | Institucional; P²≈a³ com unidades apropriadas. |
| K2 | NASA Science, *Mercury Facts*, https://science.nasa.gov/mercury/facts/ | Parâmetros aproximados; não catálogo de efemérides reprocessado. |
| K3 | NASA Science, *Didymos & Dimorphos*, https://science.nasa.gov/solar-system/asteroids/didymos/ | 11:55→11:23, versão ~32 minutos. |
| K4 | NASA Science, *DART mission*, https://science.nasa.gov/mission/dart/ | Mesma missão K3, arredondamento histórico diferente. |
| K5 | ESA/DPAC, *Gaia DR3 Documentation*, https://gea.esac.esa.int/archive/documentation/GDR3/ | Astrometria, qualidade e correções. |
| K6 | Bailer-Jones et al. (2021), *Estimating Distances from Parallaxes V*, https://bailer-jones.www3.mpia.de/gedr3_distances.html | Inferência bayesiana com sistema Gaia, não solução única sem prior. |
| K7 | Planck Collaboration (2020), *Planck 2018 VI*, https://doi.org/10.1051/0004-6361/201833910 | Estimativa de parâmetros sob modelo específico; autorizações de material por artigo. |
| K8 | NASA/LAMBDA, *COBE FIRAS*, https://lambda.gsfc.nasa.gov/product/cobe/firas_overview.html | Espectro térmico e T0 publicado. |
| K9 | ESA Planck, *Why the microwave?*, https://www.esa.int/Science_Exploration/Space_Science/Planck/Why_the_microwave | Redshift e modelo físico de desacoplamento. |
| K10 | ALMA (12/06/2026), *REBELS-25 gas reservoir*, https://www.almaobservatory.org/en/press-releases/alma-and-vla-reveal-a-vast-reservoir-of-star-forming-fuel-in-a-galaxy-near-cosmic-dawn/ | Contraste de CO com CMB, estimativas inferidas. |
| K11 | NASA Science, *How We Find and Characterize*, https://science.nasa.gov/exoplanets/how-we-find-and-characterize/ | Massa e raio planetários por métodos distintos; exemplo 8/2 é **hipotético**. |
| K12 | Makadia, R. et al. (2026), *Direct detection of an asteroid's heliocentric deflection: The Didymos system after DART*, *Science Advances* 12(10), eaea4259, https://doi.org/10.1126/sciadv.aea4259 ; https://www.jpl.nasa.gov/news/nasas-dart-mission-changed-orbit-of-asteroid-didymos-around-sun/ | Aproximadamente 0,15 s no período heliocêntrico, **não** 32 minutos. Artigo e comunicado correspondem ao mesmo estudo. |

**Licenças:** nenhuma imagem, artigo integral ou tabela foi reproduzida; este documento inclui síntese, referências e contas autorais. NASA/ESA, periódicos e ALMA possuem termos por obra; conferir antes de distribuir mídia: https://www.nasa.gov/nasa-brand-center/images-and-media/ .

## 10. Critério de qualidade e limites honestos

Estes casos colocam **dados publicados** lado a lado com relações matemáticas e tipos de incerteza, fechando a lacuna de ausência de números provenientes de observações institucionais. **Ainda não** cumprem exigência de exercícios reprocessados sobre dados brutos por equipe/revisor independente. Não usar essas contas como nota neural, prova cega, detecção astronômica nova ou diplomação do CRIVO. A futura integração exige exame dos valores usados no contexto da época e rubrica inédita.

**Main, CI, redes e pesos:** intocados. **Status:** pesquisa pronta para curadoria; módulo 8 ainda não marcado documentalmente pronto até revisão e conferência de escopo.
