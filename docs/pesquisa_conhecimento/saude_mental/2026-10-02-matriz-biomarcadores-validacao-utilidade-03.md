# Matriz bibliográfica granular — neurociência, lote 3: tradução quantitativa

**Data:** 2026-10-02
**Objetivo:** consolidar como efeitos de pesquisa devem virar conhecimento utilizável sem inflar significado clínico.

## 1. ENIGMA e efeitos pequenos
Grandes consórcios de neuroimagem têm valor porque reduzem instabilidade de amostras pequenas. Porém, um efeito pequeno e replicável pode ser:
- etiologicamente informativo;
- útil para compreender heterogeneidade;
- insuficiente para classificação individual.

O ledger deve armazenar **effect size + overlap + external validation**, não apenas p-value.

## 2. Biomarker intended use
Cada biomarcador deve ser classificado:
- risk;
- susceptibility;
- diagnostic;
- differential diagnostic;
- prognostic;
- predictive;
- monitoring;
- pharmacodynamic/response;
- safety.

Um marcador prognóstico não deve ser promovido a marcador preditivo de tratamento.

## 3. Clinical utility
`analytical validity → clinical validity → clinical utility`.
Um assay pode medir precisamente uma molécula sem melhorar decisão clínica.

## 4. Calibration
Para risco previsto p:
calibration pergunta se eventos ocorrem aproximadamente na frequência prevista.
Discrimination boa + calibration ruim = previsão clinicamente problemática.

## 5. Spectrum bias
Performance em caso clássico versus controle saudável costuma ser melhor que em população real com diagnósticos diferenciais.

## 6. Verification bias
Se apenas positivos recebem gold-standard, sensibilidade/especificidade podem ficar enviesadas.

## 7. Incorporation bias
Se index test entra no próprio reference standard, desempenho pode ser artificialmente inflado.

## 8. Circular analysis
Escolher voxels com os mesmos dados usados para testar diferença (“double dipping”) infla efeitos.

## 9. Leakage
Feature selection, harmonization ou preprocessing feitos antes do split podem vazar informação para test set.

## 10. Nested CV
Hyperparameter tuning deve ficar dentro do treinamento; test set final permanece intocado.

## 11. External validation
Validação externa requer novo setting/time/site/population; novo split da mesma amostra não é external validation forte.

## 12. Temporal validation
Dados futuros no mesmo sistema testam drift, mas ainda não equivalem a geografia/população externa.

## 13. Transportability
Perguntar se mecanismos/measurement/selection diferem entre source e target population.

## 14. Ancestry
PGS construído majoritariamente em European ancestry geralmente perde desempenho em outras ancestralidades devido a LD, allele frequencies, effect estimates e environment.

## 15. Fairness
Diferenças de calibration por grupo podem coexistir com igual AUROC. Uma métrica não encerra fairness.

## 16. Causal biomarker
Biomarcador associado a doença pode ser:
- causal;
- consequence;
- compensatory;
- correlated consequence;
- confounded.
Intervir no marcador é teste mais forte, mas off-target/pleiotropy ainda importam.

## 17. Mendelian randomization
IV assumptions:
1. relevance;
2. independence;
3. exclusion restriction.
Horizontal pleiotropy ameaça inferência.

## 18. Colocalization
Mesmo locus para exposure/outcome não garante mesma causal variant; colocalization testa hipótese compartilhada sob modelo.

## 19. Fine mapping
Credible set não identifica automaticamente único causal variant.

## 20. Functional validation
Reporter assay/cell model demonstra função em contexto experimental, não necessariamente efeito clínico organism-level.

## 21. Omics multiple testing
Milhares/milhões de features exigem correção e replication. “Top hit” exploratório não vira mecanismo.

## 22. Batch effects
Sequencing/site/plate effects podem parecer biologia. Randomization/QC/covariates são essenciais.

## 23. Cell composition
Bulk tissue signal pode mudar porque proporção celular mudou, não expressão dentro de cada célula.

## 24. Single-cell clusters
Cluster label é inferência algorítmica; cell types/states podem ser contínuos e dependentes do pipeline.

## 25. Postmortem directionality
Doença, tratamento, duração, causa da morte e agonal state estão misturados; causalidade temporal é difícil.

## 26. Longitudinal biomarkers
Within-person change pode ser mais informativo que cross-sectional difference, mas regression-to-mean e measurement error persistem.

## 27. Reliable change
Mudança individual precisa exceder erro esperado e practice effects quando aplicável.

## 28. Digital biomarkers
Missingness pode ser informative: telefone desligado/sem uso pode relacionar-se ao estado. Tratar missing as random pode enviesar modelo.

## 29. Wearables
Device firmware/algorithm changes criam measurement drift mesmo sem mudança biológica.

## 30. Passive sensing
Mobilidade baixa pode refletir depressão, trabalho em casa, doença física, clima ou bateria. Proxy exige contexto.

## 31. Ecological momentary assessment
EMA reduz recall interval, mas reactivity, burden e nonresponse continuam.

## 32. Multimodal fusion
Combinar MRI+genetics+EMA pode aumentar dimensionalidade mais rápido que informação; overfitting cresce sem N/validation.

## 33. Foundation models/AI biomarkers
Representação potente não elimina dataset shift, leakage ou lack of ground truth.

## 34. Explainable AI
Feature attribution não é causal explanation. SHAP/attention/etc. não transformam predictor em mechanism.

## 35. Prospective impact
Última pergunta:
“usar este biomarcador melhora outcome comparado a não usar?”
Sem isso, clinical utility permanece não demonstrada.

# Template obrigatório para próxima extração
`source_id | claim_id | citation | year | design | population | N | exposure/index | comparator/reference | outcome | effect | CI | heterogeneity | bias | replication | intended_use | maturity_B | causal_level | generalizability | checked`.

# Gate de promoção
- B1→B2: independent replication.
- B2→B3: individual-level prediction + internal validation.
- B3→B4: external validation + calibration + target population.
- B4→B5: prospective decision/impact evidence.

# Conclusão
O acervo passa a distinguir três perguntas que frequentemente eram misturadas:
1. existe diferença biológica?
2. ela permite prever/classificar um indivíduo?
3. usar essa informação melhora uma decisão clínica?

Responder “sim” à primeira não responde as outras duas.

**Integração:** nenhuma. **Treinamento:** nenhum.
