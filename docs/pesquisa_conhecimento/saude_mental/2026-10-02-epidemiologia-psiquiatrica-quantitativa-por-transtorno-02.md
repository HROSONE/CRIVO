# Epidemiologia quantitativa — lote 2: trauma, desenvolvimento, alimentação, substâncias e neurocognição

**Data:** 2026-10-02  
**Regra:** prevalência de sintoma, diagnóstico, exposição, risco e burden são variáveis diferentes.

## 1. PTSD
WHO (11 set 2026): lifetime PTSD global estimado em 3,9%; ~70% experimentam potencial traumatic event ao longo da vida, mas uma minoria desenvolve PTSD. Entre expostos, estimate citado pela WHO ~5,6%. Exposure prevalence portanto não pode ser usada como disorder prevalence. Mulheres são mais afetadas em média, mas diferença observada agrega tipo de trauma, exposição, fatores sociais/biológicos e measurement.

ICD-11 PTSD/CPTSD e DSM-5 PTSD não são constructs idênticos; prevalence depende do sistema. Estudos DSM não devem ser reetiquetados retrospectivamente como ICD-11 CPTSD.

Fonte institucional atual: WHO, Post-traumatic stress disorder fact sheet, 2026-09-11.

## 2. Neurodesenvolvimento — WHO/GBD 2021
WHO World mental health today (2025), tabela GBD 2021:
- autism spectrum disorders: 62 milhões; age-standardized point prevalence 0,8% (male 1,1%, female 0,5%);
- ADHD: 85 milhões; 1,1% (male 1,6%, female 0,6%);
- idiopathic disorder of intellectual development: 88 milhões; 1,2%;
- conduct disorder: 41 milhões; 0,6%.

Para 20+ anos, GBD reportou autism 0,7% e ADHD 0,7%. Isto não significa simplesmente remission: age-dependent case definitions, data sparsity, recognition/cohort effects e modeling importam. Sex ratio observado não deve ser automaticamente interpretado como razão biológica: ascertainment e phenotype presentation podem contribuir.

Fonte: WHO, World mental health today: latest data, 2025, Table 2.1; underlying IHME GBD 2021.

## 3. Eating disorders
WHO/GBD 2021 estimou 16 milhões com eating disorders cobertos pela categoria GBD (anorexia e bulimia nervosa), point prevalence age-standardized 0,2% total, 0,1% male e 0,3% female. A categoria não captura necessariamente todo o universo ICD-11 de feeding/eating disorders; portanto não usar 16 milhões como prevalence de AN+BN+BED+ARFID etc.

Mudança de criteria pode alterar case counts. Atypical AN demonstra por que BMI threshold não deve ser confundido com ausência de gravidade clínica.

## 4. Substance use disorders
SUD epidemiology exige separar:
- exposure/use;
- hazardous use;
- intoxication/withdrawal;
- dependence/SUD;
- substance-specific disorder;
- mortality/overdose;
- treatment need/gap.

Prevalence de consumo nunca deve ser transformada em prevalence de disorder. Toxicology-positive não identifica compulsivity/impairment. Cross-substance aggregation esconde diferenças enormes de product, dose, route, potency e jurisdiction.

Para causal models, separar antecedent liability, availability, initiation, escalation, dependence, remission e mortality selection. Genetic correlation não identifica direção causal; Mendelian randomization também depende de relevance/independence/exclusion restriction e pode sofrer pleiotropy.

## 5. Neurocognição
Dementia prevalence depende fortemente de idade; age-standardized e crude rates respondem perguntas diferentes. Screening-positive cognitive impairment não é dementia. MCI/mild NCD não é simplesmente “early dementia”: há estabilidade, reversão aparente e múltiplas etiologias.

Incidence deve modelar competing risk de morte. Estudos de oldest-old são especialmente vulneráveis a survivor selection. Biomarker-defined Alzheimer pathology não equivale automaticamente a clinical dementia prevalence.

## 6. Suicide/self-harm — denominadores separados
Separar:
1. thoughts of death;
2. suicidal ideation;
3. plan;
4. attempt;
5. non-suicidal self-injury;
6. self-harm com intenção indeterminada;
7. suicide death.

Taxas de suicide death são eventos populacionais raros em comparação com ideation; isto limita PPV de instrumentos mesmo com boa sensitivity/specificity. Não usar associação de risk factor como algoritmo determinístico individual.

## 7. Measurement model
Para transtorno latente D e instrumento T:
P(T+) = Se·P(D) + (1-Sp)·[1-P(D)].
PPV = Se·Prev / [Se·Prev+(1-Sp)(1-Prev)].

Logo, mudança de prevalence altera PPV mesmo sem mudar Se/Sp. Surveys que usam screen sem diagnostic calibration podem superestimar ou subestimar case prevalence.

## 8. Burden
WHO/GBD 2021: mental disorders ~1,095 bilhão de casos modelados e age-standardized prevalence 13,6%. A tabela observa que anxiety inclui PTSD; eating disorders inclui AN/BN; residual other mental disorders inclui personality disorders sem comorbid mental/SUD. Estes agrupamentos GBD não são a árvore ICD-11.

Consequência: não treinar CRIVO a somar categorias sobrepostas para obter “total”. Comorbidity e hierarchy/modeling tornam soma ingênua inválida.

## 9. Ledger
| ID | Claim | Fonte | Limite |
|---|---|---|---|
| EPQ2-001 | lifetime PTSD global ~3,9% | WHO 2026 | estimate global/model-dependent |
| EPQ2-002 | trauma exposure é muito mais comum que PTSD | WHO 2026 | event definition varia |
| EPQ2-003 | GBD2021 autism point prevalence ~0,8% | WHO 2025/IHME | model, não census |
| EPQ2-004 | GBD2021 ADHD ~1,1% all ages | WHO 2025/IHME | age/model dependent |
| EPQ2-005 | GBD eating category ~0,2% | WHO 2025/IHME | só AN/BN na categoria |
| EPQ2-006 | GBD category != ICD-11 family | WHO 2025 notes | ontology mismatch |
| EPQ2-007 | screen prevalence depends on Se/Sp/base rate | probability identity | assumes stable operating characteristics |
| EPQ2-008 | suicide constructs require separate denominators | methodological | definitions/jurisdiction vary |

## 10. Próxima exigência quantitativa
Ainda buscar por família: incidence, age-specific curves, sex/gender, region, diagnostic version, uncertainty, ascertainment, temporal trend, comorbidity handling e underrepresented populations. OCD, dissociative, personality, SUD substance-specific e dementia etiologic subtypes permanecem particularmente incompletos.

**Integração/treino:** nenhum.
