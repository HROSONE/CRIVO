# Astronomia — BAO, distâncias cosmológicas, constante de Hubble, DESI e energia escura

**Data de pesquisa e revisão das fontes:** 2026-10-01.  
**Currículo:** módulos 6 (cosmologia), 7 (astronomia observacional), 8 (matemática aplicada), 9 (inferências), 10 (matriz de evidências para o integrador).  
**Status:** PESQUISA PARA REVISÃO; NÃO integrada ao CRIVO, NÃO treinada, NÃO certificada. Arquivo de documentação isolada.  
**Escopo complementar:** [Cosmologia primordial, CMB e nucleossíntese](2026-10-01-cosmologia-primitiva-nucleossintese-recombinacao-cmb.md), que explica a origem das oscilações acústicas; aqui se estuda como essas assinaturas são observadas hoje e como os parâmetros dependem de hipóteses.

## 1. Uma lei de expansão não é uma velocidade única de todo o Universo

A lei de Hubble–Lemaître, em regime cosmológico homogêneo e numa época dada, vincula a taxa de afastamento associada à expansão e a distância própria: v_rec ≈ H(t) D_propria. É uma expressão para a expansão da geometria FLRW, não a velocidade especial-relativística de um foguete passando localmente. Em redshift pequeno, a aproximação observacional frequentemente usada é c z ≈ H0 D, após considerar movimentos peculiares e calibrações [H1,H2].

**Redshift observacional:** z = (λ_obs - λ_emit)/λ_emit. Sob expansão ideal entre observador e fonte comóveis, 1+z = a_obs/a_emit. Outras contribuições podem vir de movimento peculiar da fonte e desvio gravitacional. Uma identificação espectral de linha permite estimar z, mas isso não determina distância única sem modelo/calibração quando z não é pequeno [H2,H3].

**Exemplo didático hipotético:** uma linha que em repouso está em 500 nm e chega em 1000 nm tem z=1, se a identificação da linha for correta. Isso representa duplicação do comprimento de onda. Não significa que a galáxia viajou localmente a 'c', nem que necessariamente estava hoje a um bilhão de quilômetros.

**Erro frequente:** definir H0 com unidade km/s/Mpc e depois interpretá-la como km/s de uma galáxia a qualquer distância, sem multiplicar pela distância adequada. Em modelo simples e baixo z, para distância 100 Mpc e H0=67,4 km/s/Mpc, obtém-se 6740 km/s *como componente de recessão da expansão*. Não confundir com velocidade radial observada sem corrigir movimento peculiar; para redshifts elevados, usar integral cosmológica [H2,H3].

## 2. Não há uma única distância para o mesmo objeto cosmológico

A nota técnica de David W. Hogg distingue distâncias comóveis, distância de luminosidade, distância de diâmetro angular e tempo de retrospectiva, cujo uso depende do observável físico [H3].

- **Distância comóvel transversal D_M:** separação espacial com expansão 'fatorada' segundo uma convenção geométrica.
- **Distância de luminosidade D_L:** definida operacionalmente pelo fluxo bolométrico observado F e luminosidade intrínseca L: F = L/(4π D_L²). Inclui efeitos da expansão na energia recebida e chegada de fótons.
- **Distância angular D_A:** definida pela relação entre tamanho transversal próprio de objeto e ângulo observado: D_A = tamanho/ângulo em aproximação de ângulos pequenos e objeto apropriado.
- **Tempo de retrospectiva:** diferença entre época atual do observador e época da emissão sob modelo cosmológico; não é, em geral, igual a distância comóvel dividida por c.

Sob propagação de luz em geometria métrica, conservação de número de fótons e condições apropriadas, a relação de dualidade de distância é D_L=(1+z)² D_A. Também se escreve D_L=(1+z) D_M e D_A=D_M/(1+z) na convenção de D_M transversal. Desvios aparentes podem refletir seleção, absorção/extinção, hipóteses ou física nova; antes de afirmar violação, verificar sistemáticos [H3,H4].

**Contraexemplo:** objeto mais distante não tem necessariamente menor diâmetro angular observado em todas as faixas de redshift: D_A(z) pode aumentar e depois diminuir num modelo de expansão; o tamanho físico e sua evolução também importam [H3].

## 3. Supernovas tipo Ia: por que foi possível descobrir aceleração?

Uma supernova Ia não é lâmpada padronizada com luminosidade exatamente idêntica em todos os progenitores. Propriedades de suas curvas de luz e cores permitem padronização estatística. Com estimativa do fluxo e luminosidade calibrada obtém-se D_L; com linhas espectrais obtém-se z. Comparar D_L(z) a modelos da expansão restringe densidade de matéria e propriedades da energia escura [H1,H5,H6].

Em 1998, Riess e colaboradores estudaram supernovas em redshifts elevados e relataram distâncias, em média, maiores do que em determinados modelos sem constante cosmológica. Em 1999, Perlmutter e colaboradores apresentaram evidência independente baseada em dezenas de supernovas. Os resultados favoreceram aceleração cósmica sob as análises e sistemáticos então examinados [H5,H6].

**Por que a interpretação requer cuidado:** poeira e avermelhamento, evolução de populações progenitoras, calibração, seleção por brilho, identificação espectral e lenteamento podem deslocar a inferência. A descoberta histórica não significa que qualquer supernova isolada comprova aceleração sem outras medidas.

**Erro adicional:** chamar supernova Ia 'tipo de estrela que explodiu por falta de hidrogênio' é definição causal errada; canais termonucleares de anãs brancas e espectros constituem temas próprios, detalhados no dossiê de remanescentes.

## 4. BAO: transformar ondas de som de um plasma antigo em régua cósmica

O plasma primordial possuía oscilações entre compressão gravitacional e pressão de fótons/bárions. Quando a matéria se desacoplou suficientemente da radiação, uma escala característica permaneceu na distribuição estatística de matéria. Essa marca é identificada hoje como excesso sutil de pares de galáxias (ou outros traçadores) separados por distância comóvel perto de 150 Mpc [H7,H8].

**Como se mede sem encontrar uma 'parede de som' no espaço:** contar pares de posições de galáxias em função de sua separação e comparar com a distribuição esperada em uma amostra de referência; o sinal aparece como uma característica da função de correlação de dois pontos, não um anel que cada galáxia precisa exibir visualmente. O pico é estatístico e a seleção espacial/geométrica do levantamento altera sua observação [H7].

**Régua padrão condicional:** a escala física r_d do horizonte sonoro da era do desacoplamento de bárions depende de física do plasma, densidades e expansão primordial. Medir BAO muitas vezes entrega razões D_M/r_d e D_H/r_d, onde D_H(z)=c/H(z). Para transformar o resultado em uma distância absoluta é necessário r_d calibrado por evidência ou hipótese externa [H7,H8].

**Medição radial e transversal:** separações angulares e diferenças de redshift dependem de D_M e H(z), respectivamente. Erros de redshift, distorções peculiares, modelagem de viés de traçadores e não linearidades precisam ser representados [H7,H8].

**Par de inferências correto:** 'A distribuição mostra escala acústica' é resultado observacional após processamento; 'logo energia escura é constante' não se segue sem comparar diferentes épocas e combinar dados e modelos.

## 5. Por que DESI utiliza hidrogênio que nem pertence às galáxias observadas?

DESI registra espectros de galáxias, quasares e outros alvos. Um quasar distante atua como fonte de fundo; hidrogênio neutro intergaláctico situado entre fonte e observador absorve luz nas condições da transição Lyman-alfa. Regiões diferentes deixam absorção deslocada para comprimentos de onda diferentes devido à história de propagação e expansão [H7–H9].

**Floresta Lyman-alfa:** conjunto de linhas de absorção ao longo de uma visão para o quasar. Muitos quasares amostram diferentes percursos, permitindo reconstruir estatísticas tridimensionais da distribuição de hidrogênio e inferir BAO em épocas distantes. Nenhuma linha da floresta isolada corresponde a uma galáxia inteira; gás, temperatura, ionização e características instrumentais condicionam a absorção [H7,H9].

**Controle de contaminação:** absorvedores fortes (damped Lyα), metais, erros de continuum do quasar, modelagem da floresta, máscaras e seleção interferem nas correlações. DESI usa simulações de catálogo com condições conhecidas para verificar se o processo de análise recupera parâmetros inseridos artificialmente [H8,H9].

**Distinção importante:** simulações bem recuperadas são evidência de validação de pipeline em cenários ensaiados, não garantia lógica de que todo viés instrumental desconhecido já esteja excluído.

## 6. Atualização DESI DR2: março de 2025 versus julho de 2026

**19/03/2025 — análise de oscilações acústicas bariônicas:** o DR2 reuniu os primeiros três anos de dados DESI. Ao comparar as medidas BAO em diferentes redshifts com CMB e conjuntos de supernovas, a colaboração relatou aumento da preferência estatística por modelos em que a equação de estado da energia escura pode variar ao longo da história cósmica. A magnitude dessa preferência é dependente dos dados combinados e da parametrização [H7,H10].

**30/07/2026 — análise full-shape da floresta Lyα:** a colaboração DESI publicou uma nova medição que usa mais do que a posição do pico BAO, incorporando a forma completa da correlação de hidrogênio entre diferentes linhas de visada. Em comparação ao BAO isolado, a restrição estatística da geometria anisotrópica foi melhorada; a tendência central da nova medida se moveu na direção das previsões do ΛCDM de referência. O resultado é compatível com o modelo padrão neste teste e não exclui automaticamente todos os modelos alternativos [H8,H9].

**Por que os resultados não se contradizem automaticamente?**
- Conjuntos de dados, observáveis, covariâncias e escalas são diferentes.
- A inferência combina medidas de BAO, forma ampla da correlação, CMB, supernovas e escolhas do modelo.
- Um resultado que favorece dinâmica sob certo conjunto pode ficar menos significativo após incluir uma nova amostra ou incorporar outros erros.
- A pressão científica correta é reexaminar modelos e sistemáticos, não declarar vitória por uma medida isolada.

**Equação de estado cosmológica:** w=p/(ρ c²). Para constante cosmológica ideal, w=-1; alguns modelos empíricos usam w(a)=w0+wa(1-a). Isso é parametrização, não descoberta experimental da substância física que cria energia escura. A compatibilidade com w=-1 em uma análise não confirma de modo único a natureza microscópica da componente aceleradora [H7,H8].

**Conclusão limitada válida em 01/10/2026:** a aceleração tardia do Universo é bem sustentada; a hipótese de evolução temporal de energia escura exige acompanhamento de observações e modelos e NÃO deve ser anunciada como fato estabelecido com base apenas na divulgação de 2025. O artigo DESI de 2026 não equivale a uma descoberta final de nova física nem a refutação definitiva de todo cenário evolutivo.

## 7. A tensão de Hubble: medições locais não são o mesmo procedimento do CMB

**Escada de distâncias local:** paralaxe calibra estrelas próximas; estrelas como Cefeidas calibram relações entre período e luminosidade; Cefeidas em galáxias hospedeiras ajudam calibrar supernovas Ia; supernovas mais distantes ligam distâncias a redshifts [H1,H11,H12]. Cada degrau traz incertezas e correlações.

**Inferência pelo CMB:** Planck mede espectro angular, polarização e efeitos de lentes da radiação primordial, ajustando parâmetros da física inicial e sua evolução sob ΛCDM. Obtém, nesse modelo, H0=67,4 ± 0,5 km/s/Mpc, não uma contagem direta das velocidades de galáxias atuais [H13].

**Discrepância:** a NASA continua descrevendo as inferências de métodos locais e do CMB como não reconciliadas em sua discussão de tensão de Hubble. Não citar como se a diferença fosse explicada definitivamente por um único erro de poeira ou como se duas medidas calibradas fossem experimentos perfeitamente independentes [H1,H11,H12].

**Qual o papel do Webb?** Resolução infravermelha mais alta permite separar o brilho de Cefeidas de estrelas vizinhas em certos sistemas, investigando confusão de luz e poeira. As comparações de Hubble/Webb publicadas em 2023–2024 reforçaram a análise dos degraus específicos da equipe, mas não resolveram todos os caminhos alternativos de calibração, todas as sistemáticas nem todos os parâmetros cosmológicos [H11,H12].

**Não misturar níveis:** 'H0 é 67,4 na análise Planck-ΛCDM' é uma inferência publicada sob hipóteses; 'H0 é 67,4 independentemente de modelo, população e instrumento' é afirmação científica injustificada.

## 8. Incertezas: separar variação aleatória, erros sistemáticos e dependência do modelo

**Aleatória:** ruído de contagem, flutuação estatística, amostragem limitada de objetos. Mais observações independentes podem reduzir partes do erro, sob condições.

**Sistemática:** calibração de zero de paralaxe, extinção não modelada, função de seleção que prefere objetos brilhantes, identificação de absorvedores, erro de fotometria, modelo de velocidades peculiares, correções de instrumentos e população estelar. Muitas medidas usando a mesma calibração compartilham o mesmo erro; repetir a coleta sem corrigir calibração não o elimina [H3,H9,H12].

**Modelagem:** escolher ΛCDM, parâmetros w0wa, densidade de neutrinos ou modelo de extinção introduz diferentes espaços de inferência. Um intervalo de confiança publicado pode ser estreito dentro de um modelo, sem incluir incerteza estrutural de escolher o modelo incorreto [H7,H13].

**Covariância:** se duas medidas compartilham fonte de erro, tratá-las como independentes reduz artificialmente o intervalo de confiança de uma combinação. A matriz de covariância guarda variâncias nas diagonais e covariâncias entre observáveis fora da diagonal. Não 'somar porcentagens de confiança' para alegar precisão independente [H9,H13].

**Risco de evidência circular:** se uma régua cósmica r_d é calibrada usando o CMB sob modelo ΛCDM, não chamá-la automaticamente de medida independente de ΛCDM ao usá-la para testar ΛCDM, a menos que a análise diferencie cuidadosamente as dependências. O mesmo vale para Cefeidas e supernovas que compartilham instrumentos e anfitriãs calibradoras.

## 9. Matemática editorial com unidades e pressupostos

| Relação | Significado e condição | Uso inadequado |
| --- | --- | --- |
| z=(λ_obs/λ_rest)-1 | Deslocamento de linha identificada | Tratar todo z como velocidade local |
| H(z)=ȧ/a | Definição de taxa instantânea de expansão para modelo FLRW | Aplicar a sistema gravitacionalmente ligado como se a órbita sempre acompanhasse H |
| D_H(z)=c/H(z) | Escala radial de Hubble; distância por intervalo apropriado de redshift | Equiparar diretamente a diâmetro de galáxia |
| D_L=(1+z)²D_A | Relação de dualidade sob propagação métrica e conservação de fótons | Usá-la sem considerar absorção e pressupostos em um teste de desvios |
| F=L/(4π D_L²) | Definição operacional bolométrica de distância de luminosidade | Usar distância euclidiana em alto redshift sem correção |
| w=p/(ρc²) | Equação de estado cosmológica homogênea | Igualar w a medida direta de uma partícula ainda não identificada |

**Conta 1 hipotética:** se λ_rest=500 nm e λ_obs=750 nm, z=0,5. Não se conhece D_L apenas a partir desse valor sem modelo ou outros observáveis.

**Conta 2 hipotética:** para H0=67,4 km/s/Mpc, a aproximação linear de recessão em 10 Mpc dá 674 km/s. Em galáxias relativamente próximas, velocidades peculiares de ordem centenas de km/s podem ser importantes em comparação ao efeito cosmológico; portanto estimar H0 de uma só fonte é impreciso.

**Conta 3 hipotética de covariância:** duas medidas de mesma grandeza compartilham erro de calibração comum, além de ruído independente. Tirar a média diminui parte do ruído, mas NÃO faz desaparecer o erro comum. As magnitudes reais só podem ser calculadas com variâncias e covariâncias explícitas.

**Conta 4 hipótese em distância-dualidade:** se z=1, D_L=4 D_A sob os pressupostos do teorema. Não pressupor que D_L=4 vezes a distância de linha de visada em todos os modelos: D_A e outros tipos de distância são distintos.

## 10. Matriz de afirmações, evidências e condições que um revisor deve exigir

| Pergunta | Resposta científica limitada | Observação importante |
| --- | --- | --- |
| 'O que DESI mediu?' | Correlações de galáxias, quasares e absorção de hidrogênio; escalas/anisotropias BAO e full-shape | Não coletou uma amostra material de energia escura |
| 'O DESI 2026 confirmou energia escura mutável?' | Não; estreitou medidas e uma tendência se aproximou de ΛCDM | Precisamos comparar os modelos e observações conjuntamente |
| 'Qual instrumento mediu 67,4 km/s/Mpc diretamente?' | Planck inferiu H0 sob ΛCDM a partir do CMB; não cronometrou galáxia local | Diferenciar medidas da instrumentação de parâmetros ajustados |
| 'Uma curva de supernova brilhante prova aceleração?' | Não isoladamente; conjuntos calibrados de D_L e z fornecem restrições | Poeira, população, seleção e evolução entram na análise |
| 'O pico BAO é uma bolha vista em torno de cada galáxia?' | Não; aparece estatisticamente em distribuição de pares e correlações | Separação típica é em distância comóvel |
| 'Uma linha Lyα corresponde a uma galáxia?' | Não; absorção por gás intergaláctico em linha de visada | Contínuo quasar, metal e DLA interferem |
| 'Mais dados eliminam todo viés?' | Não; ruído pode cair e sistemáticos permanecerem | Necessária validação e auditoria cruzada |
| 'H0 mede taxa da expansão em toda época?' | H0 é valor atual; H(z) evolui com a época | Não aplicar H0 fixo ao Universo primordial |
| 'Idade, distância de luz e distância comóvel são equivalentes?' | Não; observáveis diferentes e expansão modificam as relações | Distinguir tempo de retrospectiva e geometria |
| 'Observações diferentes concordando são sempre independentes?' | Não; verificar calibração/física comum e covariâncias | Concordância com dependências compartilhadas não é confirmação completamente independente |

## 11. Questões futuras de avaliação — exemplos documentais, NÃO prova cega

As perguntas abaixo são exemplos para um futuro agente *desenvolver uma prova diferente*, não material que deva ser decorado por modelo:
1. A massa de uma galáxia pode ser determinada somente pela linha espectral que identifica seu redshift?
2. BAO exige que exista som propagando pelo vácuo interestelar de hoje?
3. Uma supernova em alto redshift determina H0 sem calibrar a luminosidade?
4. Duas equipes usam a mesma calibradora de brilho, e ambas encontram a mesma expansão. Elas são duas medidas independentes?
5. Uma medição de H0 derivada de Planck prova que a equipe fotografou galáxias próximas?
6. Se D_L e D_A discordam da dualidade numa análise, o que se verifica antes de alegar nova física?
7. A aproximação v≈cz se aplica a z=5 como velocidade local especial-relativística?
8. Medidas BAO e full-shape da mesma amostra DESI constituem duas amostras independentes?
9. Na análise de julho de 2026 do Lyα, os resultados caminharam para o modelo padrão: isso resolve todas as tensões cosmológicas?
10. Como o mesmo dado primordial pode calibrar uma régua usada em um teste posterior?

**Importante:** a futura prova independente deve ter novos itens e rubrica blindada à seleção de exemplos do currículo editorial, conforme a skill da main. Nada aqui mediu acertos do CRIVO.

## 12. Fontes institucionais e primárias com datas e direitos

| Ref. | Fonte | Dados, limites e proveniência |
| --- | --- | --- |
| H1 | NASA Science, *Hubble Constant and Tension* (atualização divulgada 2025): https://science.nasa.gov/mission/hubble/science/science-behind-the-discoveries/hubble-constant-and-tension/ | Escada de distâncias e tensão; instituição, síntese sem solução final. |
| H2 | NASA Science, *Hubble–Lemaître relation*: https://science.nasa.gov/mission/hubble/science/science-behind-the-discoveries/hubble-constant-and-tension/ | Expansão e redshifts em contexto didático; H1 e H2 MESMA página, não evidências independentes. |
| H3 | David W. Hogg (1999), *Distance measures in cosmology*: https://arxiv.org/abs/astro-ph/9905116 | Referência técnica para z, diferentes distâncias, idade e volume; publicação como nota técnica, direitos integrais não presumidos. |
| H4 | Cong Ma & Pier-Stefano Corasaniti (2016), *Statistical Test of Distance--Duality Relation with Type Ia Supernovae and Baryon Acoustic Oscillations*: https://arxiv.org/abs/1604.04631 | Teste de Etherington, dados/covariâncias e sistemáticos; artigo técnico. |
| H5 | Riess, A. G. e colaboradores (1998), *Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant*, Astronomical Journal 116, DOI https://doi.org/10.1086/300499 | Estudo histórico primário; direitos reservados da American Astronomical Society na versão publicada, sem cópia integral. |
| H6 | Perlmutter, S. e colaboradores (1999), *Measurements of Omega and Lambda from 42 High-Redshift Supernovae*, ApJ 517, https://arxiv.org/abs/astro-ph/9812133 | Segundo estudo histórico independente; presença de preprint não equivale licença de republicação integral. |
| H7 | DESI Collaboration, *DESI DR2 Results: March 19 Guide*, 19/03/2025: https://www.desi.lbl.gov/2025/03/19/desi-dr2-results-march-19-guide/ | BAO de galáxias e Lyα, múltiplos modelos e sistemáticos; guia de artigos, não substituto de dados brutos ou paper. |
| H8 | DESI Collaboration, Wynne Turner, *New DESI DR2 Lyman-alpha Results Shed Light on Dark Energy*, 30/07/2026: https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/ | Atualização de correlação full-shape; central do teste mais próxima de ΛCDM, não resultado definitivo. |
| H9 | DESI Data, *DESI DR2 Publications* (artigos de 2025 e 30/07/2026): https://data.desi.lbl.gov/doc/papers/dr2/ | Índice de trabalhos primários e simulações de validação. Mesmo levantamento e séries de dados dos demais DESI, portanto NÃO necessariamente independente. |
| H10 | DESI Collaboration, *More Than a Hint of Evolving Dark Energy*, 19/03/2025: https://www.desi.lbl.gov/2025/03/19/more-than-a-hint-of-evolving-dark-energy-new-results-and-data-from-desi/ | Divulgação do cenário em 2025, contextualizar com H8. |
| H11 | NASA/Hubble–Webb, *Webb Confirms Accuracy of Universe's Expansion Rate Measured by Hubble*, 12/09/2023: https://science.nasa.gov/blogs/webb/2023/09/12/webb-confirms-accuracy-of-universes-expansion-rate-measured-by-hubble-deepens-mystery-of-hubble-constant-tension/ | Controle de crowding/extinção da amostra analisada, sem resolver todos os sistemas. |
| H12 | NASA, *Webb, Hubble Telescopes Affirm Universe's Expansion Rate, Puzzle Persists*, 11/03/2024: https://science.nasa.gov/missions/webb/nasas-webb-hubble-telescopes-affirm-universes-expansion-rate-puzzle-persists/ | Análise de calibração e limites, mesma família de equipes/instrumentos, sem tratar como independência total. |
| H13 | Planck Collaboration (2020), *Planck 2018 results. VI. Cosmological parameters*, DOI https://doi.org/10.1051/0004-6361/201833910 | H0=67,4 ± 0,5 sob ΛCDM, outros parâmetros, incerteza estatística e sistemáticas; consultar errata https://doi.org/10.1051/0004-6361/201833910e . |
| H14 | NASA, *Media Usage Guidelines*: https://www.nasa.gov/nasa-brand-center/images-and-media/ | Condições de reutilização NASA; avisos de terceiros e sem alegação de endosso. |

**Direitos e origem:** texto totalmente redigido de forma própria para estudo, não cópia de artigos, dados brutos, fotos ou gráficos. Trabalhos históricos de supernovas têm direitos de periódico; links arXiv não autorizam reutilização integral automaticamente. O DESI informa copyright em sua página; não tratar divulgação e catálogo DR2 como CC geral. Fotos e gráficos NASA/DESI/Planck não foram incorporados. Direitos de mídia NASA: H14; ESA e Planck: conferir https://www.cosmos.esa.int/web/planck/pla . Fonte específica, método, ano e hipótese devem acompanhar qualquer ficha futura criada pelo integrador.

## 13. Estado da pesquisa após este documento

**Novidade documental:** mecanismo BAO/régua; distinção das distâncias; interpretação de supernovas Ia, H0 local vs Planck, covariâncias e DESI DR2 2025–2026. Combinado ao dossiê de cosmologia primordial, preenche parte substantiva das lacunas do módulo 6, sem encerrá-lo.

**Lacunas bloqueantes remanescentes:** revisão de indicadores de crescimento de estruturas, dinâmica de matéria escura e energia escura em modelos concorrentes; rastreamento do que é consistente/controverso com séries de dados independentes; exercícios com dados públicos, unidades e covariância numérica reprodutíveis; auditoria científica externa e validação de bibliografia. Não declarar que módulo 6 passou ou que a pesquisa inteira já está concluída.

**Módulos 7/8/9/10:** os mecanismos e exemplos não substituem instrumentação, exercícios independentes, testes reais ou certificação. Nenhuma mudança de main, codebase, CI, checkpoint, pesos, consulta simbólica ou avaliação neural. Certificação permanece 0/10 conforme skill da main.
