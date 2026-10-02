# Estatística, psicometria e inferência causal para saúde mental — nível avançado

**Data:** 2026-10-02
**Função:** permitir avaliar evidência, não apenas armazenar resultados.

# 1. Estimando em vez de “provando”

Dados são amostra de um processo. Uma estimativa deve vir acompanhada de incerteza.

`estimativa ± incerteza` é mais informativo que “significativo/não significativo”.

# 2. p-value

Sob modelo nulo e demais pressupostos, p é probabilidade de observar dados/estatística tão ou mais extremos quanto os observados.

**Não é:**
- P(H0 ser verdadeira);
- probabilidade do resultado ser acaso;
- tamanho do efeito;
- importância clínica;
- probabilidade de replicar.

Dizer p=.03 não significa “97% de chance de hipótese ser verdadeira”.

# 3. Intervalo de confiança

IC é procedimento frequentista com cobertura de longo prazo. Um IC95% específico não significa literalmente 95% de probabilidade de o parâmetro fixo estar dentro, sob interpretação frequentista padrão.

Largura informa precisão e depende de variabilidade/amostra/modelo.

# 4. Tamanho de efeito

Exemplos:
- diferença média;
- standardized mean difference/Cohen d;
- risco relativo;
- odds ratio;
- hazard ratio;
- correlação;
- risk difference/NNT.

Padronização facilita comparação mas pode esconder escala clínica. d=0,5 não significa “50% de melhora”.

# 5. OR versus RR

`OR=(p1/(1-p1))/(p0/(1-p0))`.
Para eventos comuns, OR pode parecer numericamente muito maior que RR. Não interpretar OR como “vezes mais provável” sem cuidado.

# 6. NNT

`NNT = 1/ARR` quando apropriado.

Depende do risco basal, horizonte temporal e outcome. NNT não é propriedade universal do medicamento.

# 7. Poder estatístico

Power é probabilidade de detectar efeito sob tamanho verdadeiro/modelo especificado. Estudos pequenos produzem falsos negativos e, entre achados significativos, estimativas exageradas (“winner's curse”).

# 8. Erros tipo I/II

Tipo I: rejeitar H0 quando H0 verdadeira.  
Tipo II: não rejeitar quando alternativa especificada é verdadeira.

“Não significativo” ≠ “sem efeito”. Equivalência/non-inferiority exigem desenhos próprios.

# 9. Multiplicidade

Muitos testes aumentam falso positivo. FWER e FDR controlam erros diferentes. Escolha deve corresponder ao objetivo.

P-hacking inclui decisões analíticas flexíveis condicionadas ao resultado.

# 10. Bayes

`Posterior ∝ Likelihood × Prior`.

Bayes permite probabilidade sobre parâmetros/hipóteses sob modelo/prior. Resultado depende de prior e likelihood; análise de sensibilidade é importante.

Bayes factor compara suporte relativo entre modelos, não “probabilidade absoluta de verdade”.

# 11. Base rates

Mesmo teste bom pode ter PPV baixo quando prevalência é baixa.

`PPV = Se×Prev / [Se×Prev +(1-Sp)×(1-Prev)]`.

Esse princípio é crítico para screening e biomarcadores.

# 12. Sensibilidade/especificidade

Sensibilidade: P(teste+ | condição).  
Especificidade: P(teste− | sem condição).

Não dependem da prevalência da mesma maneira que PPV/NPV, mas podem variar por spectrum/case mix e threshold.

# 13. ROC

AUROC é probabilidade de caso escolhido aleatoriamente receber escore maior que não-caso sob condições. Não informa calibração nem utilidade clínica e pode enganar em forte desbalanceamento.

# 14. Calibration

Se modelo prevê 20% para 100 pessoas comparáveis, aproximadamente 20 deveriam apresentar outcome para boa calibração naquele contexto.

Discriminação boa + calibração ruim = risco individual mal estimado.

# 15. Confiabilidade

Classical test theory:
`X = T + E`.

Confiabilidade = proporção da variância observada atribuível a diferenças estáveis/“true score” sob modelo.

Tipos:
- test–retest;
- inter-rater;
- consistência interna;
- formas paralelas.

Alta confiabilidade não garante validade.

# 16. Alpha

Cronbach α depende de número de itens e covariância e assume condições. α alto pode ocorrer por redundância. Não prova unidimensionalidade.

Omega frequentemente é alternativa sob modelos fatoriais mais flexíveis.

# 17. SEM

`SEM = SD√(1-r)`.
Ajuda interpretar incerteza de escore individual, sob pressupostos.

# 18. Reliable Change

Índice de mudança confiável compara diferença pré–pós com erro esperado. “Mudou 5 pontos” precisa ser contextualizado pela precisão da escala e por importância clínica.

# 19. Validade

Validade é argumento sobre interpretação/uso do escore, apoiado por evidência:
- conteúdo;
- estrutura interna;
- relações com outras variáveis;
- processo de resposta;
- consequências/uso.

“Escala validada” não é selo eterno para qualquer população/idioma/finalidade.

# 20. Validade de construto

Convergente: relaciona-se com medidas esperadas.  
Discriminante: distingue construtos relevantes.

Correlação alta demais entre construtos supostamente distintos também pode revelar redundância.

# 21. Factor analysis

EFA explora estrutura; CFA testa modelo especificado. Fit indices não transformam modelo em verdade. Modelos alternativos podem ajustar similarmente.

# 22. Measurement invariance

Para comparar grupos/tempo, testar se medida funciona de maneira comparável:
- configural;
- metric;
- scalar;
- residual/strict, conforme objetivo.

Sem invariância apropriada, diferença média pode refletir funcionamento da medida.

# 23. DIF

Differential Item Functioning: pessoas com mesmo nível latente mas grupos diferentes têm probabilidades distintas de resposta a item. Pode revelar viés ou diferenças substantivas; exige interpretação.

# 24. IRT

Probabilidade de resposta é função do traço latente e parâmetros do item. Modelo 2PL:
`P(X=1|θ)=1/(1+e^{-a(θ-b)})`.

a = discriminação; b = dificuldade/localização. Model fit e dimensionalidade importam.

# 25. Screening versus diagnóstico

Screening prioriza detectar possíveis casos e aceita falsos positivos conforme contexto. Diagnóstico integra entrevista, curso, funcionamento, diferencial e contexto.

Cutoff não cria fronteira natural necessariamente.

# 26. Regression to the mean

Pessoas selecionadas por escore extremo tendem a valores menos extremos em nova medida mesmo sem tratamento. Estudos pré–pós sem controle podem confundir isso com eficácia.

# 27. Confounding

C é confundidor quando influencia exposição e outcome (sob estrutura causal apropriada). Associação ajustada depende de conjunto de ajuste.

# 28. Mediation

Efeito total pode decompor-se em caminhos direto/indireto sob pressupostos fortes. Mediador medido depois do tratamento mas junto ao outcome não estabelece sequência causal.

# 29. Moderation

Interação indica que efeito varia por variável. Subgrupos pós-hoc têm alto risco de falsos positivos; hipóteses e poder importam.

# 30. Collider bias

Se `X → C ← Y`, condicionar em C pode induzir associação X–Y. Exemplo hospitalar: selecionar apenas pacientes internados pode criar relações inexistentes na população.

# 31. Selection bias

Participação, perda de follow-up e critérios de inclusão podem mudar relações observadas. Attrition diferencial é especialmente relevante em psicoterapia/longitudinal.

# 32. Time-varying confounding

Em dados longitudinais, tratamento e confundidores mudam e influenciam uns aos outros. Regressão convencional pode falhar; métodos g (IPTW/MSM, g-formula) foram desenvolvidos para certas estruturas.

# 33. Instrumental variables

Instrumento Z deve afetar exposição, ser independente de confundidores relevantes e afetar outcome apenas via exposição. Exclusão é frequentemente difícil de provar.

# 34. Target trial emulation

Para perguntas observacionais, especificar hipotético ensaio-alvo:
eligibilidade, estratégias, atribuição, follow-up, outcome, estimando e análise. Ajuda evitar immortal time e ambiguidades.

# 35. Missing data

MCAR/MAR/MNAR descrevem mecanismos. Imputação múltipla pode reduzir viés sob modelo plausível; análise de sensibilidade a MNAR é importante.

# 36. Meta-análise

Random effects assume distribuição de efeitos verdadeiros. Estimar τ²/intervalo de predição ajuda mostrar heterogeneidade.

**Prediction interval** responde aproximadamente onde efeito de novo estudo/contexto comparável pode cair; pode ser mais clinicamente revelador que IC da média.

# 37. I²

I² é proporção relativa de variabilidade observada atribuída a heterogeneidade além do erro amostral. Depende de precisão dos estudos e não mede magnitude absoluta da heterogeneidade.

# 38. Publication bias / small-study effects

Funnel asymmetry pode ter várias causas. Egger e trim-and-fill não “corrigem a verdade”. Registro de ensaios e busca de resultados não publicados são importantes.

# 39. Meta-regression

Associação entre característica de estudos e efeito é observacional no nível de estudo, vulnerável a ecological bias/confounding. Não inferir efeito individual automaticamente.

# 40. Network meta-analysis

Compara múltiplas intervenções usando evidência direta/indireta. Requer transitivity e consistency plausíveis. Ranking SUCRA/P-score não deve ser interpretado sem certeza e magnitude.

# 41. GRADE

Certeza da evidência considera risco de viés, inconsistência, indireção, imprecisão e publication bias, com regras adicionais. Certeza não é tamanho de efeito.

# 42. Clinical significance

Significância estatística pode coexistir com benefício trivial. Avaliar funcionamento, qualidade de vida, MCID quando válido, remissão/resposta e danos.

# 43. Multiplicidade de outcomes

Sintoma primário, secundários, subescalas e tempos geram muitas oportunidades analíticas. Outcome primário pré-especificado reduz cherry-picking.

# 44. Reproducibilidade

Separar:
- computational reproducibility;
- direct replication;
- conceptual replication;
- generalizability.

Falha de replicação pode revelar falso positivo, contexto/moderação ou diferença metodológica; precisa diagnóstico científico.

# 45. Regra operacional do CRIVO

Para qualquer afirmação quantitativa armazenar:
`estimando | população | desenho | N | medida | efeito | IC/CrI | comparador | follow-up | ajuste | missing | multiplicidade | risco de viés | heterogeneidade | generalização | fonte`.

## Fontes metodológicas estruturais
- AERA/APA/NCME Standards for Educational and Psychological Testing.
- Cochrane Handbook for Systematic Reviews of Interventions.
- GRADE Working Group.
- CONSORT / STROBE / PRISMA como padrões de relato.
- Literatura moderna de causal inference e psychometrics deverá ser ligada por capítulo na auditoria fonte–afirmação.

**Integração:** nenhuma. **Treinamento:** nenhum.
