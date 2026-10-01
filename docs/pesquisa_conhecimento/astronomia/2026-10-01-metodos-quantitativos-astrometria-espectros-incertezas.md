# Astronomia — Métodos quantitativos: paralaxe, espectros, mapas de gás e tratamento de incertezas

**Pesquisa documental:** 2026-10-01. **Módulos:** 7 (observação), 8 (matemática aplicada), 9 (raciocínio), 10 (preparo de matriz de evidências para o outro agente).
**Status:** PESQUISA PARA REVISÃO; NÃO integrada, NÃO treinada e NÃO certificada. Todos os exemplos numéricos abaixo são CONSTRUÍDOS DIDATICAMENTE: não foram baixados ou analisados catálogos por este agente, nem executadas provas do CRIVO.
**Prioridade:** passar de frases 'telescópio mede X' para procedimento observável → calibração → estimativa → incerteza → interpretação → limite.

## 1. As medidas não começam com os conceitos da resposta

A câmera ou detector registra sinais instrumentais: contagens, intensidades por pixel, tempos e comprimentos de onda calibrados. 'Temperatura', 'massa', 'distância', 'idade', 'matéria escura', 'oceano interno', 'planeta detectado' são quantidades inferidas em etapas específicas, não necessariamente variáveis que o telescópio mede diretamente.

**Cadeia mínima auditável:** objeto-alvo e modo instrumental → dados e metadados → remoção de defeitos e calibração → mensuração do observável → hipóteses físicas para obter parâmetro → comparação com modelos alternativos → incerteza e diagnóstico de possíveis vieses.

**Três dimensões de resolução:** resolução angular (separa posições), espectral (distingue comprimentos de onda) e temporal (resolve mudanças com o tempo). Uma imagem muito nítida não fornece automaticamente espectro de boa resolução; observar uma estrela milhares de vezes não garante distância sem geometria ou calibração [Q1,Q2].

## 2. Paralaxe: quando podemos inverter e quando não

Paralaxe anual é mudança angular aparente de posição medida em relação a fontes distantes devido ao movimento orbital da Terra e à geometria das observações. Em idealização simples, `d[pc]=1/p[arcsec]=1000/p[mas]`, para paralaxe positiva bem medida com vieses corrigidos. É definição geométrica do parsec, não distância calculada a partir de brilho [Q3–Q5].

**Gaia DR3:** a documentação ESA/DPAC afirma que a astrometria de DR3 reproduz EDR3 e registra desvio global de zero de paralaxe Gaia−real da ordem de **−0,017 mas**, com dependência de posição, magnitude e cor. Trata-se de um valor GLOBAL aproximado, não correção fixa universal para cada estrela. O instrumento mede soluções astrométricas com erro estatístico e sistemático correlacionado; há fontes com soluções de apenas posição, sem paralaxe [Q3,Q4].

**Exemplo sintético A, medição de boa relação sinal/ruído:** p=10,0±0,2 mas → d≈100 pc, e a aproximação de primeira ordem `σ_d≈(1000/p²)σ_p ≈2 pc`; se erros forem pequenos, essa propagação é razoável. Essa aproximação não incluiu calibração de zero nem covariâncias.

**Exemplo sintético B, medição relativa ruim:** p=0,20±0,10 mas. Inversão ingênua daria d=5000 pc e propagação linear ±2500 pc. A distribuição de distância é assimétrica e pode admitir valores enormes se p estiver perto de zero; um valor de paralaxe negativo pode decorrer de ruído sem implicar distância física negativa. É necessária inferência probabilística com priori apropriada e seu efeito explícito [Q5].

**Bailer-Jones e colaboradores (2021):** estimaram distâncias geométricas e fotogeométricas de **1,47 bilhão** de fontes Gaia EDR3 combinando paralaxe com informações de estrutura da Galáxia e, em um caso, brilho/cor. Isso não significa que o prior seja 'medida direta' da distância nem que a distância fotogeométrica seja perfeitamente independente da fotometria [Q5].

**Atenção operacional futura:** consultar `astrometric_params_solved`, `parallax_error`, `ruwe`, correlações e qualidade/duplicação da fonte; o RUWE pode apontar ajuste astrométrico inadequado, mas um limite numérico único não funciona como diagnóstico definitivo de todas as variáveis/binárias [Q4,Q6].

## 3. Movimento próprio versus velocidade radial

Um deslocamento angular por ano fornece `μ`, geralmente em mas/ano ou arco-segundo/ano. Em geometria euclidiana local, a velocidade transversal `v_t[km/s]≈4,74047 × μ[arcsec/ano] × d[pc]`. A velocidade RADIAL requer espectroscopia Doppler ou método equivalente; medir μ e paralaxe não fornece por si só velocidade radial [Q3,Q6].

**Conta construída:** fonte a 100 pc com μ=0,050 arcsec/ano tem v_t≈4,74047×0,050×100≈23,70235 km/s. Se a distância fosse duas vezes maior com o mesmo μ, a velocidade transversal estimada dobraria; a inferência herdaria a incerteza da distância.

**Inferência 3D:** converter velocidades em eixos de Galáxia requer posição no céu, movimento do Sol, distância, velocidade radial e referenciais. Uma projeção em imagem não revela o sinal de velocidade ao longo da linha de visão.

## 4. Espectros: diferenciar presença química, temperatura e velocidade

A luz dispersa pelo espectrógrafo revela intensidade versus comprimento de onda. Linhas absorvidas/emitidas são associadas a transições atômicas/moleculares, mas temperatura, pressão, composição, ionização, turbulência, rotação e campo magnético podem afetar força e formato. Uma linha isolada pode sofrer identificação ambígua; confirmar padrões de múltiplas linhas reduz degenerescências [Q2,Q7].

**Redshift:** `z = λ_observado/λ_repouso - 1`. Para uma linha Hα hipotética de 656,3 nm vista em 721,93 nm, `z=(721,93/656,3)-1=0,100`. NÃO converter z=0,1 em velocidade newtoniana exatamente 0,1c para qualquer contexto cosmológico; cosmologia exige modelo, e mesmo o Doppler especial relativístico possui forma diferente [Q7].

**Largura de linha:** ela pode representar rotação, dispersão/turbulência, movimento térmico, pressão e resolução do aparelho. `Δv≈cΔλ/λ` é aproximação para larguras pequenas; retirar alargamento instrumental é necessário. Um deslocamento aparente de linha não demonstra exoplaneta sem avaliar atividade estelar, binariedade e outros efeitos periódicos.

**Sinal de gás ionizado:** Hα pode indicar recombinação de hidrogênio em regiões H II próximas de estrelas massivas, mas AGN e choques também excitam gás. SDSS ajusta várias linhas e em certas amostras usa razões como [O III]/Hβ e [N II]/Hα para separar fontes de ionização com ressalvas [Q8,Q9].

## 5. Poeira e magnitudes

O fluxo recebido é afetado por distância, absorção, espalhamento e calibração. O brilho da fonte antes da atenuação não é necessariamente igual ao fluxo registrado.

**Magnitudes relativas:** `m1-m2=-2,5log10(F1/F2)`, no mesmo sistema de filtros e zero de magnitude. Se duas fontes têm F1/F2=100, então m1−m2=−5: a fonte 100 vezes mais brilhante tem magnitude 5 unidades MENOR. Não confundir escala invertida com 'mais magnitude = mais luz' [Q7].

**Extinção:** `F_intrínseco≈F_obs 10^{0,4 A_λ}` para uma extinção efetiva `A_λ` expressa em magnitudes, nas condições de modelo apropriadas. Se A_λ=1 mag, o fator de correção é 10^0,4≈2,512. A correção depende da banda, lei de extinção, geometria de poeira/fonte e tipo de população. Não aplicar o mesmo A_λ a UV, óptico e infravermelho sem avaliação.

**Degenerescências:** população antiga, poeira e metalicidade podem tornar uma galáxia vermelha em observações ópticas. 'Vermelho = velho' é atalho enganoso em objetos distantes cujo espectro inteiro está deslocado cosmologicamente.

## 6. Métodos de formação estelar com diferentes janelas temporais

**Hα:** rastreia ionização/recombinação em regiões que podem conter estrelas massivas jovens, mas pode receber contribuição de choques e AGN. **UV:** sensível à população jovem por janela temporal distinta da linha Hα e com fortes efeitos de poeira. **Infravermelho:** poeira aquecida por estrelas jovens e, em certos regimes, estrelas mais velhas/AGN; não converter todo IR em formação estelar sem ajustar [Q8,Q9].

O catálogo de propriedades galácticas do SDSS registra explicitamente limitações de baixa S/N em Hβ para corrigir poeira via decremento de Balmer; se Hβ é fracamente detectado, a extinção calculada pode se tornar instável [Q9].

**Questão causal:** duas galáxias com Hα de brilho similar podem ter SFR diferente se distâncias, extinção, fração de escape de fótons ionizantes, IMF e contaminação de AGN diferirem. É necessário decompor medição em hipótese.

## 7. Emissão CO, linhas de carbono e dados cúbicos

O programa PHANGS-ALMA disponibiliza cubos de dados espectrais em posição–posição–frequência, incluindo CO(2–1). A documentação menciona típica resolução de **~1,5 arcsec** (~100 pc em distâncias representativas), canais de velocidade de 2,5 km/s e características de sensibilidade do levantamento. Os 90 alvos do programa e os 74 com produtos descritos na entrega não representam duas contagens incompatíveis [Q10].

**Dimensão angular→física:** para ângulo pequeno, `s≈Dθ` com θ em radianos. Um arco-segundo corresponde a 1/206265 rad. Em uma distância DIDÁTICA de 20 Mpc, um pixel/feixe de 1,5 arcsec corresponde a aproximadamente `20×10^6 pc × 1,5/206265 ≈ 145,4 pc`. Esse valor não é uma medida da distância de uma galáxia PHANGS: mostra que uma mesma resolução angular cobre tamanhos diferentes para distâncias diferentes.

**Frequência/velocidade:** converter frequências observadas em velocidades exige referência de frequência de repouso, convenção Doppler (radio/óptica/relativística) e referencial baricêntrico/local. Uma estrutura espacial com gradiente de velocidade pode representar rotação, fluxo ou projeção de múltiplos componentes. Converter intensidade integrada de CO em massa de gás requer razão de excitação e α_CO; a observação de CO é direta no espectro, a massa H₂ é modelada.

**ALMA interferométrico:** sintetiza abertura a partir de múltiplas antenas, mas amostragem espacial incompleta e ausência de baselines curtos podem retirar emissão extensa; reconstrução de imagens e correções importam. Não concluir 'não existe gás difuso' de um mapa que filtrou grandes escalas sem investigar resposta do sistema [Q10].

## 8. Sinal versus ruído, detecção e limites superiores

**Razão sinal/ruído (SNR):** para medida F com incerteza de dispersão σ_F, pode-se definir SNR≈F/σ_F em contexto adequado. Um sinal 5σ tem determinada robustez estatística somente sob modelo de ruído, teste especificado e correção por múltiplas buscas; '5σ = verdade física sem hipótese' é falso.

**Seleção:** se milhares de frequências, períodos ou posições são testados e só o maior pico é relatado, a probabilidade de falso positivo global é diferente da de um teste pré-especificado. É importante registrar a função de seleção e número efetivo de comparações.

**Limite superior:** não detecção com um instrumento estabelece que determinado sinal não excede limiar sob condições de observação e modelo. Não implica massa=0, vida=0, ausência de oceano ou inexistência de planeta. Para massa H₂, por exemplo, limites de CO propagam-se por escolhas de conversão.

**Precisão vs. exatidão:** repetidas medidas podem ter baixa dispersão e zero-point errado. Mais dados podem reduzir ruído aleatório sem corrigir viés compartilhado.

## 9. Covariâncias e orçamento de erro

Em pequena-perturbação linear, para função `y=f(x1,...,xn)`, pode-se usar `Var(y)≈J C J^T`, onde J é vetor de derivadas e C matriz de covariância. Isso requer regularidade local e erros suficientemente pequenos: modelos não lineares com paralaxe baixa S/N ou truncamento de população exigem distribuição/pósterior completa.

**Exemplo de erro comum:** duas medidas hipotéticas x1=10,0±0,2 e x2=10,2±0,2 compartilham zero de calibração com incerteza 0,3. Tirar média reduz o ruído independente ~0,2/√2≈0,141, mas o termo de calibração comum não cai e a incerteza total aproximada seria `sqrt(0,141²+0,3²)≈0,332`, não 0,141. A conclusão vale para componentes independentes condicionados, não números observados.

**Calibração de Gaia:** o desvio de zero global DR3 ~−0,017 mas é variável com posição/cor/magnitude. Aplicar correção fixa +0,017 a todos os objetos seria um procedimento excessivamente simplificado: usar receita e controle adequados aos parâmetros resolvidos [Q3,Q4,Q11].

**Independência científica:** duas publicações da mesma base Gaia não são medições observacionais independentes, mesmo que implementem inferências diferentes. Confirmação entre métodos complementares é mais forte quando suas incertezas compartilhadas são explicitamente modeladas.

## 10. Exemplo de roteiro de análise reprodutível SEM BAIXAR DADOS nesta execução

O agente integrador pode futuramente, se autorizado, executar protocolos separados com versões congeladas:

### 10.1 Distância e velocidade de estrelas Gaia
1. Selecionar catálogo DR3 e fonte pelo `source_id` inequívoco, sem expor dados privados.
2. Ler `parallax`, `parallax_error`, `pmra`, `pmdec`, `radial_velocity` quando existir, `ruwe`, `astrometric_params_solved` e matriz de correlações.
3. Aplicar receita de zero-point apropriada à solução com cinco ou seis parâmetros, registrando versão.
4. Examinar S/N de paralaxe; se baixo, usar distância probabilística e informar sensibilidade ao prior.
5. Propagar incertezas a v_t e confrontar com velocidade radial calibrada, evitando confundir referencial heliocêntrico e galactocêntrico.
6. Conferir amostra controle com soluções independentes quando possível.

### 10.2 Espectro SDSS
1. Baixar espectro FITS e metadados de DR17 ou outra release especificada; registrar versão e ID.
2. Conferir correção de comprimento de onda, ruído por pixel e regiões mascaradas.
3. Identificar linhas em PADRÃO de pelo menos mais de uma linha sempre que possível.
4. Estimar z e conferir alternativas de identificação; usar linhas de calibração e efeitos instrumentais.
5. Se inferir SFR, separar contribuição de AGN/choques, poeira e hipóteses da IMF.
6. Medir incerteza e procurar discrepâncias entre redshifts de linhas diferentes.

### 10.3 Cubo PHANGS
1. Selecionar alvo, versão de entrega, cubo calibrado e canais de velocidade do mesmo levantamento.
2. Conferir mapa de ruído, feixe e escalas recuperadas; não misturar fluxo por canal e intensidade integrada.
3. Integrar linha CO sob máscara definida *antes* de avaliar objeto-alvo, para controlar viés de seleção.
4. Converter em massa molecular SOMENTE com α_CO, excitação, distância e seus erros explicitados.
5. Relacionar a mapa Hα/UV/IR com resolução angular e escala temporal compatíveis.
6. Documentar que correlação espacial não prova causalidade sem controle de outras variáveis.

**Este documento NÃO contém resultados obtidos após executar esses protocolos.** As contas numéricas anteriores foram formuladas para ensinar unidades, propagação e premissas.

## 11. Matriz de erros conceituais que uma IA científica deve evitar

| Suposição incorreta | Correção e evidência necessária |
| --- | --- |
| 'Paralaxe negativa indica distância negativa' | Ruído/correlações/zero-point; inferência de distância não é simples inversão em baixa S/N. |
| 'Gaia DR3 corrigiu automaticamente toda paralaxe' | Documentação diz que zero-point DR3 persiste em astrometria; calibrar por receita específica. |
| 'Toda fonte Gaia possui velocidade radial' | DR3 possui produtos diferentes por fonte e solução; verificar disponibilidade. |
| 'Linha óptica deslocada significa apenas Doppler local' | Redshift cosmológico e efeitos gravitacionais também podem contribuir. |
| 'Um detector viu uma galáxia de idade exata em um pixel' | Idade/metallicidade dependem de interpretação espectro-populacional. |
| 'Hα vermelho é medição direta de vida' | Linha mede gás e condições físicas, não organismos. |
| 'CO é todo o hidrogênio molecular' | Conversão e gás escuro ao CO podem mudar massa inferida. |
| '5σ é garantia matemática de que hipótese está certa' | Exige ruído e teste adequados, múltiplas buscas, viés e modelagem. |
| 'Instrumentos mais modernos não precisam calibrar' | PSF, zeropoint, seleção e covariância continuam importantes. |
| 'Não vejo sinal logo o objeto não existe' | Limite instrumental apenas sob sensibilidade/modelo. |
| 'Uma observação com 1,5″ tem escala de 100 pc em toda galáxia' | Escala linear depende de distância, resolução real e geometria. |

## 12. Referências técnicas e institucionais conferidas

| ID | Fonte, link | Natureza e limite |
| --- | --- | --- |
| Q1 | NASA/Webb, *Webb's Scientific Instruments*, https://science.nasa.gov/mission/webb/science-overview/science-explainers/webbs-scientific-instruments/ | Resolução espectral, espacial, modos; explicação instrumental. |
| Q2 | NASA/Webb, *Spectroscopy 101: Beyond Temperature and Composition*, https://science.nasa.gov/mission/webb/science-overview/science-explainers/spectroscopy-101-beyond-temperature-and-composition/ | Linhas, velocidades e composição; resumo institucional. |
| Q3 | ESA/DPAC, *Gaia DR3 Documentation*, versão 10/07/2023, https://gea.esac.esa.int/archive/documentation/GDR3/ | Astrometria e fotometria, zero-point e tipos de solução. |
| Q4 | ESA/DPAC, *Gaia DR3 gaia_source Data Model*, https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html | Colunas, RUWE, solução, limites específicos; parte da mesma documentação Q3, não fonte independente. |
| Q5 | Bailer-Jones e colaboradores (2021), *Estimating distances from parallaxes V*, https://bailer-jones.www3.mpia.de/gedr3_distances.html | Priori espacial e fotogeométrica para 1,47 bilhão de fontes; depende dos mesmos dados Gaia. |
| Q6 | ESA/Gaia, *Gaia DR3 overview*, https://www.cosmos.esa.int/web/gaia/dr3 | Precisão de paralaxe/movimento por magnitude; divulgar faixas e seleção. |
| Q7 | NASA/Webb, *NIRSpec MSA emission spectra* (imagens didáticas), https://science.nasa.gov/asset/webb/webbs-first-deep-field-nirspec-msa-emission-spectra/ | Reconhecimento de mais de uma linha espectral; não contém rotina de calibração completa. |
| Q8 | SDSS DR17, *Spectroscopic Data*, https://www.sdss4.org/dr17/spectro/ | Acesso e classificação de espectros e catálogos; não é validação automática de cada dado. |
| Q9 | SDSS DR17, *Portsmouth Galaxy Properties*, https://www.sdss4.org/dr17/spectro/galaxy_portsmouth/ | Extinção Balmer, ajustes e aviso de Hβ de baixa S/N; depende da mesma fonte SDSS Q8. |
| Q10 | ALMA Science Portal/NRAO, *PHANGS-ALMA Survey*, https://almascience.nrao.edu/alma-data/lp/PHANGS/ | Cubos CO, 90 alvos de programa, 74 galáxias em produtos e resolução típica de 1,5″. |
| Q11 | Lindegren e colaboradores (2021), *Gaia EDR3 Parallax Bias Versus Magnitude, Colour, and Position*, DOI https://doi.org/10.1051/0004-6361/202039653 | Correção variável da paralaxe e sistemáticos, artigo primário; ESA Q3 o referencia. |
| Q12 | ESA/Gaia, *DR3 Software Tools*, https://www.cosmos.esa.int/web/gaia/dr3-software-tools | Exemplos oficiais de correção de paralaxe, covariância e acesso a produtos; não executados aqui. |
| Q13 | SDSS DR17, *Redshifts and Classifications*, https://www.sdss4.org/dr17/algorithms/redshifts/ | Ajustes de espectros e linhas múltiplas, qualidade e classificação; mesma release de Q8/Q9. |
| Q14 | NASA/SDSS, *Redshift Catalog Tutorial*, https://www.sdss4.org/dr17/tutorials/allspectra | Métodos para recuperar dados; licença/condições da base devem ser consultadas antes de redistribuição. |

**Direitos e métodos:** a síntese foi escrita originalmente; nenhuma imagem, tabela de dados obtida por download, espectro, foto, peso neural ou código do CRIVO foi copiado/mudado. Fontes NASA/ESA/SDSS/ALMA têm condições distintas, inclusive direitos de terceiros. Publicação de relatório próprio com links não autoriza redistribuir integralmente FITS e imagens sem verificar termos por arquivo. NASA: https://www.nasa.gov/nasa-brand-center/images-and-media/ .

## 13. Lacunas e condições para futura promoção documental

- **Módulo 7:** há métodos, fórmulas e fluxo reprodutível PLANEJADO, mas ainda falta validar exercícios em dados instrumentais reais por agente/revisor autorizado e verificar bibliografia de cada técnica (p. ex. trânsitos, imagem direta e espectros de objetos frios).
- **Módulo 8:** cálculos didáticos foram registrados com unidades e hipóteses, mas a matriz curricular completa inclui gravitação, Kepler, energia, órbitas, propagação de covariância e parâmetros cosmológicos; os exemplos não bastam para fechamento.
- **Módulo 9:** contraexemplos estão escritos, porém a independência de avaliação, adaptação linguística e interpretação sem padrões pré-especificados não foi demonstrada.
- **Módulo 10:** a preparação da matriz bibliográfica ajuda o futuro integrador, mas teste independente, CI e certificação NÃO foram realizados aqui.

**Estado global:** somado aos demais dossiês, este texto amplia conhecimento documental sem comprovar cognição do CRIVO; nenhum módulo marcado como `pesquisa_documental_pronta`; 0/10 na skill oficial da main.
