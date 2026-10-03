# Neurociência de métodos — EEG/MEG, fMRI, PET, genética, causalidade e neurociência computacional

**Data:** 2026-10-02

# 1. Regra central

Nenhum método “vê o pensamento”. Cada método mede um sinal físico específico e infere processos sob um modelo.

Perguntas obrigatórias:
**o que é medido diretamente? qual transformação gera a variável analisada? resolução? ruído? inferência permitida?**

# 2. EEG

Eletrodos no couro cabeludo medem diferenças de potencial produzidas principalmente por atividade pós-sináptica sincronizada de populações neuronais com geometria favorável.

Vantagem: resolução temporal em milissegundos.  
Limite: localização espacial inversa é mal-posta; fontes diferentes podem produzir padrões semelhantes no escalpo.

## ERP
Média time-locked a eventos pode revelar componentes. Nomear componente (“P300”, “ERN”) não significa que exista módulo cognitivo único.

## Oscilações
Delta/theta/alpha/beta/gamma são bandas convencionais. Potência e fase podem mudar com tarefa; banda não possui significado psicológico universal.

# 3. MEG

Mede campos magnéticos associados a correntes neurais. Excelente temporal, localização potencialmente melhor para certas fontes, mas problema inverso permanece. Sensibilidade depende da orientação/geometria.

# 4. fMRI/BOLD

BOLD reflete alterações hemodinâmicas ligadas ao metabolismo/atividade neural. Não mede disparos diretamente.

## HRF
Resposta hemodinâmica é lenta comparada a neurônios. Modelagem convolui eventos com HRF.

## GLM
`y = Xβ + ε`.
Qualidade da inferência depende do design matrix, ruído, autocorrelação, pré-processamento e contrastes.

## Múltiplas comparações
Milhares de voxels geram inflação de falso positivo sem controle apropriado.

## Movimento
Movimento pode produzir padrões espúrios, especialmente em conectividade e comparações de grupos que se movem diferentemente.

# 5. Conectividade

**funcional:** dependência estatística entre sinais.  
**efetiva:** modelos direcionais de influência sob suposições.

Correlação temporal entre regiões não demonstra conexão anatômica nem causalidade.

# 6. Reverse inference

Se região R é ativa em tarefa de medo, observar R ativa em outra tarefa não prova medo. Inferência depende de seletividade:
`P(processo|ativação)` não é igual a `P(ativação|processo)`.

# 7. MVPA e decodificação

Classificadores podem distinguir padrões. Acurácia acima do acaso não significa “leitura da mente”. Avaliar cross-validation, leakage, balanceamento, generalização externa e calibration.

# 8. PET

Usa radiotraçadores para estudar metabolismo, receptores/transportadores e outras moléculas. Binding potential depende de modelo cinético, disponibilidade de receptor, afinidade e referência.

PET de receptor não mede diretamente “quantidade de neurotransmissor” sem desenho/modelo apropriado.

# 9. TMS

Campo magnético induz corrente cortical e pode perturbar/modular atividade. Por ser intervenção, pode fornecer evidência causal mais forte sobre necessidade/contribuição de região/rede do que fMRI correlacional, mas focalidade e propagação em rede limitam interpretação.

# 10. Lesões

Déficit após lesão pode indicar necessidade de estrutura/rede, mas lesões não respeitam fronteiras funcionais e reorganização ocorre. Dissociações simples/duplas são ferramentas históricas importantes.

# 11. Optogenética/chemogenética

Permitem manipulação celular em modelos animais com especificidade. Causalidade é forte **no modelo**, mas tradução para experiência humana requer ponte adicional.

# 12. Single-cell

scRNA-seq caracteriza expressão em células/núcleos e revela diversidade celular. Cluster é construção analítica dependente de pipeline/resolução. Expressão de RNA não equivale automaticamente a proteína/função.

# 13. Spatial transcriptomics

Preserva informação espacial junto a expressão. Resolução e deconvolução variam por plataforma.

# 14. Genética quantitativa

## GWAS
Testa associação entre variantes e fenótipo em escala genômica. Significância não implica grande efeito. Estratificação populacional, LD e qualidade fenotípica importam.

## Heritability
Herdabilidade é proporção de variância atribuível a diferenças genéticas **na população/ambiente estudados**. Não é porcentagem genética de um indivíduo e não implica imutabilidade.

## Genetic correlation
Pode indicar arquitetura compartilhada; não prova que um transtorno cause outro.

# 15. Polygenic scores

`PGS_i = Σ β_j G_{ij}`.

Desempenho depende de GWAS de descoberta, ancestralidade, fenótipo e ambiente. Transferibilidade entre ancestralidades pode cair substancialmente. Associação populacional não é destino individual.

# 16. Mendelian randomization

Usa variantes genéticas como instrumentos sob pressupostos:
1. relevância;
2. independência de confundidores;
3. exclusão — instrumento afeta desfecho apenas via exposição.

Pleiotropia pode violar exclusão. MR não é “RCT genético” automaticamente.

# 17. Twin/family designs

Separam componentes sob pressupostos sobre ambientes, assortative mating etc. Modelos ACE são úteis, mas componentes dependem do desenho/população.

# 18. Epigenética

Metilação, histonas e cromatina regulam expressão. “Trauma muda seu DNA” é formulação enganosa: sequência geralmente não muda; marcas epigenéticas podem associar-se a exposição e estado celular.

Causalidade e especificidade tecidual são desafios enormes em estudos periféricos de saúde mental.

# 19. Multi-omics

Genômica, epigenômica, transcriptômica, proteômica, metabolômica podem ser integradas. Mais camadas aumentam dimensionalidade, batch effects e risco de overfitting; integração não garante mecanismo.

# 20. Biomarcador

Tipos:
- diagnóstico;
- prognóstico;
- preditivo;
- farmacodinâmico/resposta;
- risco/suscetibilidade.

Um marcador pode ser bom para um uso e inútil para outro.

# 21. Discovery versus validation

Pipeline correto:
`descoberta → validação interna → replicação independente → validação externa → utilidade clínica → impacto`.

Usar mesmo dataset para selecionar e avaliar inflaciona desempenho.

# 22. Machine learning clínico

Métricas:
- AUROC;
- AUPRC;
- sensibilidade/especificidade;
- calibration;
- decision-curve/net benefit.

Em condição rara, alta AUROC pode coexistir com baixo PPV. AUPRC e calibração tornam-se essenciais.

# 23. Leakage

Se informação do futuro, identidade ou outcome entra no treino indevidamente, desempenho é ilusório. Splits por pessoa/site/tempo devem corresponder ao uso real.

# 24. Domain shift

Modelo treinado em hospital A pode falhar em B por scanner, prevalência, população e prática clínica. Generalização precisa ser testada, não presumida.

# 25. Computational psychiatry

Integra modelos formais de aprendizagem/decisão com psicopatologia. Parâmetros latentes podem oferecer hipóteses mecanísticas.

Problemas:
- parameter recovery;
- identifiability;
- model comparison;
- test–retest;
- validade convergente;
- especificidade clínica.

Parâmetro matemático elegante sem confiabilidade não vira biomarcador.

# 26. Digital phenotyping

Smartphone/wearable pode medir atividade, sono aproximado, mobilidade, uso e interação. Riscos: privacidade, missingness, mudança de aparelho, inferência sensível e baixa validade externa.

Correlação “menos mobilidade = depressão” não é diagnóstico.

# 27. EMA

Ecological Momentary Assessment coleta experiência repetidamente no cotidiano, reduzindo parte do viés retrospectivo e capturando dinâmica. Pode gerar burden e reatividade.

Dados aninhados requerem modelos multinível/temporais apropriados.

# 28. Redes de sintomas

Network psychometrics modela sintomas como nós/relações. Centralidade não demonstra causalidade; estimativas podem ser instáveis. Rede estatística não é necessariamente rede biológica.

# 29. Modelos latentes

Factor analysis assume variáveis observadas refletindo fatores latentes sob um modelo. Network e latent variable são perspectivas diferentes e às vezes matematicamente relacionadas.

# 30. Longitudinal

Cross-lagged models tradicionais podem misturar diferenças entre pessoas e mudanças dentro da pessoa. RI-CLPM e modelos multinível tentam separar componentes sob outras suposições.

# 31. Causal inference

RCT: exchangeability por randomização em expectativa. Observacional exige modelagem de confundimento.

DAG antes da regressão ajuda a decidir o que ajustar. “Controlamos tudo” não é sinônimo de causal.

# 32. Missing data

MCAR, MAR, MNAR são mecanismos distintos. Complete-case pode enviesar. Imputação múltipla depende de modelo; não “cria verdade”.

# 33. Meta-análise

Efeito combinado depende de heterogeneidade, viés, modelo fixed/random, dependência e qualidade. I² descreve heterogeneidade relativa, não importância clínica.

Publication bias não é resolvido por um único funnel plot/teste.

# 34. Multiplicidade e researcher degrees of freedom

Muitas análises, outcomes e decisões elevam falsos positivos. Pré-registro, transparência, correções e replicação ajudam.

# 35. Open science

Dados/código abertos aumentam auditabilidade quando ética permite. Neuroimagem/genética possuem riscos de reidentificação; “open” deve respeitar consentimento/governança.

# 36. Regra de ouro

**Método → sinal → modelo → estimativa → incerteza → inferência.**
Nunca saltar de “scanner mostrou diferença” para “descobrimos a causa”.

## Fontes estruturais

- NIH BRAIN Initiative — sistemas, células/circuitos e tecnologias.
- NIMH RDoC — unidades de análise e abordagem multiescalar.
- NIMH Data Archive — compartilhamento de dados de saúde mental.
- Literatura metodológica específica deverá ser anexada por método na auditoria aprofundada.

**Integração:** nenhuma. **Treinamento:** nenhum.
