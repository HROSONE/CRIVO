# Rastreabilidade retrospectiva fonte→afirmação dos ledgers e dossiês existentes

**Checagem:** 2026-10-03. **Escopo:** auditar os ledgers e dossiês de 2026-10-02, escritos por outro agente, sob o protocolo da própria base (`protocolo-rastreabilidade-source-claim`). O protocolo exige que ≥90% dos claims quantitativos críticos estejam VERIFIED/PARTIAL **com fonte identificável**.

Este documento:
1. mede o déficit;
2. reclassifica claims metodológicos como CONCEPTUAL;
3. ancora os claims empíricos críticos em fontes específicas verificadas;
4. lista o que continua sem âncora.

**Não** edita os arquivos do outro agente. As decisões abaixo valem como camada de status sobreposta, que prevalece na leitura.

## 1. Diagnóstico quantitativo (script reproduzível)

**Método.** Uma linha conta como **ancorada** quando a coluna de fonte contém pelo menos um destes elementos:
- PMID ou DOI;
- URL;
- ano junto a autor;
- documento versionado: NICE NG/CG, FDA, CPIC, Cochrane, WHO/CDDR, nome de ensaio.

Uma linha conta como **genérica** quando a fonte é do tipo "meta-analytic literature", "trial methodology" ou "NICE/APA" sem versão.

| Medida | Valor |
| --- | --- |
| Linhas de ledger com ID (13 arquivos de 2026-10-02) | 281 |
| Ancoradas | 59 (21%) |
| Genéricas | 222 (79%) |
| Genéricas **com suporte declarado S3/S4** | 144 |
| Dossiês narrativos de 2026-10-02 sem nenhum PMID/DOI/URL no corpo | 40 de 57 |

**Por arquivo (genéricas S3/S4):**

| Arquivo | Genéricas S3/S4 |
| --- | --- |
| ledger-biomarcadores-neurociencia-causal-01 | 50 |
| ledger-fonte-afirmacao-psicoterapia-01 | 36 |
| ledger-fonte-afirmacao-intervencoes-02 | 29 |
| ledger-fonte-afirmacao-psicofarmacologia-01 | 10 |
| tratamentos-quantitativos-efeitos-danos-01 | 10 |
| epidemiologia-psiquiatrica-quantitativa-por-transtorno-01/02 | 5 |

Os ledgers psicofarmacologia-02/03 já estão majoritariamente ancorados: 40 de 44.

**Limites da medida:**
- o classificador é heurístico. Uma linha "genérica" pode ter âncora em outra seção do mesmo arquivo, por exemplo uma lista de "Fontes" no fim;
- as listas de "Fontes" dos dossiês narrativos são majoritariamente institucionais sem versão (por exemplo, "NIMH. Depression."). Elas não permitem saber qual frase vem de qual fonte.

**Conclusão:** o critério do protocolo (≥90%) **não é atendido** pelos ledgers originais. O déficit é real, mas tem dois componentes de natureza diferente (seções 2 e 3).

## 2. Componente A — regras metodológicas rotuladas como S4 (erro de tipo, não de fato)

Muitas linhas "genéricas S4" são **regras de inferência** e não afirmações empíricas. Exemplos:
- "conectividade funcional não é influência causal";
- "NNT depende do risco basal";
- "mediação exige temporalidade".

Elas não precisam de meta-análise. Precisam de rótulo correto.

**Decisão:** reclassificar como **CONCEPTUAL** (regra metodológica), com âncora canônica de método:

| IDs | Âncora canônica | Status novo |
| --- | --- | --- |
| PT-003, PT-007, PT-031, PT-035, PT-036, PT-037, PT-040 | *Cochrane Handbook for Systematic Reviews of Interventions* (v6.x); literatura de mediação causal (VanderWeele) | CONCEPTUAL |
| PT-005, PT-006 | Furukawa 2014 (ver B-05) para PT-005; PT-006 é regra de descrição de comparador | PT-005 → empírico ancorado; PT-006 CONCEPTUAL |
| TX-013, TX-020, TX-033…TX-040 | Cochrane Handbook; GRADE; diretrizes de NMA (transitividade/consistência) | CONCEPTUAL |
| NB-015…NB-020, NB-036, NB-037, NB-045…NB-050 | princípios de método em imagem, genética e modelagem (inferência reversa: Poldrack 2006, *Trends Cogn Sci*, não reconferido) | CONCEPTUAL |
| TQ-002, EPQ-002, EPQ-003, EPQ-005 | idem | CONCEPTUAL |

**O que isso não permite concluir:** CONCEPTUAL não é "menos verdadeiro". Significa que a validade vem da lógica do desenho, não de um número empírico. Essas regras **não** podem ser citadas como "achado com suporte S4".

## 3. Componente B — claims empíricos críticos: ancoragem feita nesta rodada

Rótulos: VERIFIED-ABS (resumo indexado conferido por busca), PARTIAL, UNVERIFIED.

| Âncora | ID original | Claim original (resumido) | Fonte específica verificada | Número-chave | O que **não** permite concluir | Status novo |
| --- | --- | --- | --- | --- | --- | --- |
| B-01 | PT-002 | Aliança associa-se a desfecho | Flückiger et al. 2018, *Psychotherapy* | 295 estudos, >30.000 pacientes; r = 0,278 (IC 0,256–0,299); internet r = 0,275 | Correlação; a aliança pode refletir melhora precoce (causalidade reversa). Ver PT-003. | VERIFIED-ABS, S4 mantido |
| B-02 | PT-004 | Efeito do terapeuta não trivial | Johns et al. 2019, *Clin Psychol Rev* (PMID 30442478) | 20 estudos; média ponderada **5%** da variância (0,2–29%); ECR 8,2%; prática 5% | 5% médio esconde terapeutas muito acima e abaixo; é heterogêneo e depende da gravidade. Não identifica **quais** traços do terapeuta causam diferença. | VERIFIED-ABS |
| B-03 | PT-017 | DBT reduz autolesão no TPB | Storebø et al. 2020, Cochrane CD012955.pub2 (PMC7199382) | 75 ECR (24 de DBT); psicoterapias vs TAU: autolesão SMD −0,32 (−0,49 a −0,14; 13 ECR, 616); suicidalidade SMD −0,34 (−0,57 a −0,11; 13 ECR, 666); certeza **baixa** | O número citado é de **psicoterapias** vs TAU; o valor específico da DBT não foi conferido. Efeito pequeno-moderado com certeza baixa. "DBT reduz suicídio consumado" não é sustentado. | PARTIAL; S4 → **S3** |
| B-04 | PT-024 | EMDR eficaz; contribuição dos movimentos oculares distinta | Cuijpers et al. 2020, meta-análise de EMDR; Cusack et al. 2016, *Clin Psychol Rev*; Lee & Cuijpers 2013, *J Behav Ther Exp Psychiatry* | EMDR vs controle g = 0,93 (0,67–1,18), I² = 72%; só 4/27 estudos com baixo risco de viés; superioridade sobre outras terapias (g = 0,36) **desaparece** nos estudos de baixo risco. Cusack: força de evidência baixa-moderada para EMDR vs **alta** para exposição. Movimentos oculares: efeito moderado em contexto terapêutico (15 ensaios) | Não demonstra superioridade do EMDR sobre exposição/TCC focada em trauma. A contribuição dos movimentos oculares segue **CONTESTED** (achados de laboratório ≠ mecanismo clínico). | PARTIAL; S4 → **S3**; C-RT-1 |
| B-05 | PT-005 | Lista de espera infla o contraste | Furukawa et al. 2014, *Acta Psychiatr Scand* (NMA, 49 ECR) | TCC vs lista de espera OR com IC 3,9–10,1; vs sem tratamento IC 1,3–4,3; vs placebo psicológico **não significativo** | A hipótese de "nocebo" é interpretação; a NMA mostra a diferença de contraste, não o mecanismo. Não mostra TCC ineficaz: placebo psicológico é controle ativo. | VERIFIED-ABS |
| B-06 | TX-015 | Clozapina na esquizofrenia resistente | Siskind et al. 2016, *Br J Psychiatry* (21 artigos, 25 comparações); resposta ~40% (TQ4) | Superior em sintomas positivos a curto e longo prazo; NNT ~9 (fonte secundária: PARTIAL). NICE: oferecer após ≥2 antipsicóticos adequados | 60% não respondem. A superioridade em longo prazo vem de dados mais fracos. Não define a dose ótima. | VERIFIED-ABS (com NNT PARTIAL) |
| B-07 | PF-003/PF-004 | REMS da clozapina removido em 13 jun 2025 | FDA Drug Safety Communication 2025 | **Duas datas:** FDA deixou de exigir participação e envio de ANC em **24 fev 2025**; remoção formal efetiva em **13 jun 2025**, após o comitê consultivo conjunto de 19 nov 2024. Monitoramento de ANC segue **recomendado** na bula | Não reduz o risco de neutropenia. Não vale fora dos EUA. | VERIFIED-ABS; PF-003 corrigido para incluir a data de fevereiro |
| B-08 | TX-031 | Intervenção precoce em psicose | Correll et al. 2018, *JAMA Psychiatry* 75(6):555–565 | 10 ECR, 2.176 pacientes, 9–24 meses; descontinuação RR 0,70 (0,61–0,80); melhor em todos os desfechos meta-analisáveis (internação, escola/trabalho, sintomas) | Benefícios além de 2 anos não demonstrados pela síntese. Os componentes ativos do pacote não são identificados. | VERIFIED-ABS, S4 mantido |
| B-09 | TX-032 | IPS melhora emprego competitivo | Modini et al. 2016, *Br J Psychiatry* | >2× chance de emprego competitivo vs reabilitação tradicional, independente de país, desemprego e PIB | RR exato **UNVERIFIED**. Emprego competitivo ≠ manutenção de longo prazo nem melhora clínica. | PARTIAL |
| B-10 | TX-019 | Exercício reduz sintomas depressivos | Noetel et al. 2024, *BMJ* (NMA) | 218 estudos, 495 braços, 14.170 participantes; caminhada/corrida, yoga e força entre os mais eficazes, especialmente intensos | Certeza GRADE majoritariamente baixa a muito baixa (PARTIAL, não conferido no resumo). Cegamento impossível. Não prova que sedentarismo cause depressão (TX-020). | VERIFIED-ABS (desenho e direção); S4 → **S3** |
| B-11 | TX-021, TQ-006 | CBT-I primeira linha | Trauer et al. 2015, *Ann Intern Med* (PMID 26054060); van Straten et al. 2018, *Sleep Med Rev* | Trauer: 20 ECR, 1.162 adultos; latência −19 min, vigília −26 min, tempo total +7,6 min, eficiência +9,9 pp. Van Straten: 87 ECR; ISI g = 0,98 | O tempo total de sono muda pouco. Desfecho de diário. A recomendação de "primeira linha" vem das diretrizes (ACP/AASM), não da meta-análise. | VERIFIED-ABS. **Também resolve TQ4-027** (lote 4 atualizado) |
| B-12 | TX-024 | Tratamento baseado na família (FBT) na anorexia adolescente | Lock et al. 2010, *Arch Gen Psychiatry* (n ≈ 120) | Remissão completa no seguimento de 12 meses: FBT ~50% vs AFT 23% (comunicado institucional); recaída 10% vs 40% entre remitidos | Números de **comunicado à imprensa**: os valores no fim do tratamento e as diferenças não significativas **não foram conferidos**. Ensaio único, dois centros. | PARTIAL |
| B-13 | TQ-009 | Manejo de contingência (CM) eficaz para estimulantes | Bolívar et al. 2021, *JAMA Psychiatry* | 74 ECR, 10.444 adultos **em tratamento medicamentoso para TUO**; CM associado a abstinência de estimulantes, opioides, polissubstâncias e tabaco | **Correção de escopo:** a população é de pessoas em tratamento para TUO, e não "transtorno por estimulantes" em geral. A generalização exige outra fonte (pendência RR-P2). OR não conferido. | PARTIAL |
| B-14 | NB-001/002 | Variação de C4 ↔ risco de esquizofrenia; poda sináptica | Sekar et al. 2016, *Nature* 530:177–183 (doi 10.1038/nature16549) | A associação MHC decorre em parte de alelos estruturais de C4; risco proporcional à expressão de C4A no cérebro; em camundongos, C4 media a eliminação sináptica pós-natal | Mecanismo humano "C4 → poda excessiva → esquizofrenia" é **hipótese apoiada**, não demonstrada. Efeito por alelo é pequeno. Não serve como teste individual. | VERIFIED-ABS; NB-002 mantém "mecanismo candidato" |
| B-15 | NB-009 | PCR/IL-6 diferem em subgrupos de depressão | Osimo et al. 2019, *Psychol Med* (PMC6712955) | 37 estudos, 13.541 deprimidos e 155.728 controles; **27% (21–34%)** dos deprimidos com PCR > 3 mg/L | Inflamação de baixo grau é também ligada a obesidade, tabagismo e doença física (confundimento). Não prova que inflamação cause depressão (NB-011). | VERIFIED-ABS |
| B-16 | NB-026 | APOE ε4 aumenta risco de Alzheimer de início tardio, não determinístico | Farrer et al. 1997, *JAMA* (5.930 casos, 8.607 controles) | Caucasianos (clínica/autópsia): ε3/ε4 OR 3,2 (2,8–3,8); ε4/ε4 OR 14,9 (10,8–20,6); efeito diminui após 70 anos | Odds ratio de amostras clínicas superestima o risco absoluto populacional. Varia por ancestralidade. Não é teste diagnóstico. | VERIFIED-ABS |
| B-17 | NB-024/025 | p-tau217 plasmático com desempenho crescente; não transfere à atenção primária | Ashton et al. 2024, *JAMA Neurol* | Acurácia até 96% (amiloide) e 97% (tau) vs LCR/PET em 3 coortes; abordagem de 3 faixas reduziu testes confirmatórios em ~80% | Coortes de pesquisa/especializadas. O VPP em atenção primária, com prevalência menor, não é estabelecido (exatamente NB-025). Biomarcador de patologia ≠ diagnóstico de demência. | VERIFIED-ABS |
| B-18 | NB-028/029 | Engajamento de alvo antiamiloide ≠ benefício; ARIA | van Dyck et al. 2023, *NEJM* (Clarity AD, lecanemabe) | 1.795 pacientes, 18 meses; CDR-SB −0,45 vs placebo (27% menos declínio) | A diferença de 0,45 na CDR-SB (escala 0–18) é contestada quanto à relevância clínica. Taxa total de ARIA-E (12,6% vs 1,7%, de memória) **UNVERIFIED**. | VERIFIED-ABS (eficácia); ARIA PARTIAL |
| B-19 | NB-042 | Neurogênese hipocampal humana adulta debatida | Sorrells et al. 2018, *Nature* vs Boldrini et al. 2018, *Cell Stem Cell* | Sorrells: cai na infância a níveis indetectáveis no adulto. Boldrini: persiste até a velhice | Diferenças de tecido post-mortem, fixação e marcadores explicam parte do conflito. Nenhum dos dois decide o papel da neurogênese na resposta a antidepressivos em humanos. | VERIFIED-ABS; **CONTESTED** (C-RT-2) |
| B-20 | TQ-001, TX-011 | Antidepressivos > placebo na depressão aguda | Cipriani 2018; Stone 2022; IPD FDA (lote 4, TQ4-001…003) | ver TQ4 | ver TQ4 e IB-001 (viés de publicação) | VERIFIED-ABS (via TQ4) |
| B-21 | TQ-005, TX-017 | Lítio na manutenção e sinal antissuicida | Geddes 2004 / Cipriani 2013 vs Katz 2022 (TQ4) | ver TQ4 | Contradição registrada em TQ4 | CONTESTED quanto à magnitude antissuicida |
| B-22 | TQ-008 | Agonistas no TUO e menor mortalidade durante exposição | Sordo et al. 2017, *BMJ* (TQ4) | ver TQ4 | Observacional; confundimento por indicação | VERIFIED-ABS (via TQ4) |
| B-23 | PF-001/002 | CPIC 2023: pares CYP acionáveis; SLC6A4/HTR2A sem recomendação | Bousman et al. 2023, *Clin Pharmacol Ther* 114:51–68 (PMID 37032427; já citado no dossiê pk-pd) | — | Já ancorado em outro arquivo; a linha do ledger só não apontava para ele | ancoragem por referência cruzada |

### Contradições novas

- **C-RT-1** (EMDR): eficácia vs controle robusta em estudos de alto risco de viés; superioridade sobre outras terapias desaparece em baixo risco de viés; o componente "movimentos oculares" segue contestado.
- **C-RT-2** (neurogênese adulta humana): Sorrells vs Boldrini, ambos 2018; sem consenso.

## 4. Componente C — claims empíricos ainda **sem âncora** (status rebaixado até ancoragem)

**Regra aplicada:** claim empírico com fonte genérica e sem âncora conferida passa a **S2-provisório**. Pode ser citado como "direção plausível, fonte específica pendente", nunca como achado S4.

| IDs | Tema | Pendência |
| --- | --- | --- |
| EPQ-006 | Persistência de experiências psicóticas ~31% ("síntese 2023") | Identificar a meta-análise e conferir o número |
| EPQ-009 | Carga GBD dominada por incapacidade | GBD 2019/2021 Mental Disorders Collaborators (*Lancet Psychiatry* 2022): conferir YLD/DALY |
| NB-003, NB-004, NB-006…NB-008, NB-012…NB-014, NB-021…NB-023, NB-027, NB-030…NB-035, NB-038…NB-041, NB-043, NB-044 | Neurociência e biomarcadores | Âncora individual pendente. A maioria é coerente com a literatura, mas o protocolo exige fonte por claim |
| TX-001, TX-003, TX-004, TX-008, TX-012, TX-016, TX-018, TX-022, TX-023, TX-025, TX-029 | ECT, TMS, polifarmácia, antidepressivo em bipolar, CBT-E, infância | ECT: UK ECT Review Group 2003 (*Lancet*) e Kellner 2006 (CORE, continuação) a conferir; antidepressivo em bipolar: Sachs 2007 STEP-BD (*NEJM*) a conferir |
| PT-001, PT-008…PT-016, PT-018…PT-023, PT-026…PT-030, PT-032…PT-034, PT-038, PT-039 | Psicoterapias específicas e processos | Cochrane e NMA por transtorno; alguns já cobertos indiretamente por Cuijpers 2021 (TQ4) |
| PF-005…PF-011 | Farmacocinética (aripiprazol, olanzapina, fluvoxamina) | Bulas FDA versionadas: o fator ~40% de clearance de olanzapina em fumantes está atribuído à bula, mas sem data/versão |

Total: ~95 claims empíricos permanecem S2-provisório.

**Pendências:**
- **RR-P1:** ancorar os grupos acima em blocos temáticos;
- **RR-P2:** CM para estimulantes fora de TUO;
- **RR-P3:** dossiês narrativos. Converter as frases empíricas críticas de cada um em linhas de ledger com âncora; as listas institucionais sem versão não bastam.

## 5. Efeito sobre o critério do protocolo (rodada 1; estimativas **substituídas** pela contagem exata da seção 8)

| Medida | Antes | Depois desta rodada |
| --- | --- | --- |
| Linhas empíricas críticas com fonte específica (aprox.) | 59 | 59 + 23 âncoras (B-01…B-23 cobrem ~35 IDs) ≈ 94 |
| Regras metodológicas com rótulo correto | 0 | ~45 reclassificadas CONCEPTUAL |
| Empíricas sem âncora | ~130 | ~95 (S2-provisório) |
| Critério ≥90% de claims quantitativos críticos ancorados | não | **não** (≈50% das empíricas) |

**Conclusão honesta:**
- a rodada **reduz** o déficit e, sobretudo, **impede leitura enganosa**: S4 sem fonte deixa de valer como S4;
- não atinge o critério. O déficit de ancoragem dos ledgers de neurociência e psicoterapia continua **material**.

## 6. Rodada 2 de ancoragem (claims da seção 4)

| Âncora | ID original | Fonte específica verificada | Número-chave | O que **não** permite concluir | Status novo |
| --- | --- | --- | --- | --- | --- |
| B-24 | TX-001 | UK ECT Review Group 2003, *Lancet* 361:799–808 | ECT real vs simulada: SES −0,91 (−1,27 a −0,54; 6 ECR, 256). ECT vs farmacoterapia: SES −0,80 (18 ECR, 1.144). Bilateral vs unilateral: SES −0,32 (22 ECR, 1.408) | Ensaios com simulação antigos e pequenos. A comparação com farmacoterapia usa esquemas farmacológicos frequentemente subótimos. Efeito de **curto prazo**. | VERIFIED-ABS, S4 mantido |
| B-25 | TX-002, TX-003 | Semkovska & McLoughlin 2010, *Biol Psychiatry* | Prejuízo executivo, de velocidade e de memória anterógrada nos dias 0–3; desempenho volta ao basal ou acima após ~15 dias | Testes padronizados de grupo **não** captam bem a memória autobiográfica retrógrada, que é a queixa típica (TX-002 mantém a ressalva). Média de grupo ≠ ausência de dano individual. | VERIFIED-ABS; TX-002 → PARTIAL (memória autobiográfica sem âncora quantitativa) |
| B-26 | TX-004 | Kellner et al. 2006, *Arch Gen Psychiatry* 63:1337–44 (CORE) | ECT de continuação vs lítio + nortriptilina por 6 meses após remissão com ECT; recaída alta e semelhante nos dois braços (valores ~37% vs ~32% **não conferidos**) | Ambas as estratégias deixam recaída substancial. Não define a superioridade de uma. | PARTIAL |
| B-27 | TX-008 + TQ4 | Blumberger 2018, *Lancet* (THREE-D, já no TQ4); Cole et al. 2022, *Am J Psychiatry* (SAINT) | THREE-D: iTBS de 3 min não inferior a 10 Hz de 37,5 min. SAINT: remissão ~79% vs ~13% (sham); dispositivo liberado pela FDA em 6 set 2022 | SAINT: amostra **muito pequena** (n ≈ 29, PARTIAL), desfecho imediato, durabilidade incerta, sem replicação independente em grande escala. Liberação 510(k)/De Novo ≠ evidência de eficácia equivalente à de aprovação de fármaco. | VERIFIED-ABS (direção); SAINT **S2** até replicação |
| B-28 | TX-018 | Sachs et al. 2007, *NEJM* (STEP-BD), 366 pacientes | Antidepressivo adjunto a estabilizador: recuperação durável 23,5% vs 27,3% (placebo); resposta 32,4% vs 38%; **sem** aumento de virada maníaca | Não mostra benefício do antidepressivo adjunto, mas também não mostra dano de virada **nesta** combinação (com estabilizador). Não se aplica a monoterapia antidepressiva no bipolar I, que é a preocupação de TX-018. | VERIFIED-ABS; TX-018 refinado |
| B-29 | TX-016 | Tiihonen et al. 2019, *JAMA Psychiatry* (Finlândia, 62.250 pacientes, 1972–2014, análise intraindivíduo) | Clozapina + aripiprazol associada ao **menor** risco de reinternação: 14–23% menor que clozapina isolada, a melhor monoterapia. Polifarmácia associada a menos reinternações que monoterapia | **Contradição C-RT-3** com "polifarmácia não é default" (NICE/APA). O estudo é observacional; o desenho intraindivíduo reduz, mas não elimina, confundimento por tempo/gravidade. Não há ECR confirmando. A regra do ledger continua como **recomendação de diretriz**, agora com evidência observacional contrária registrada. | VERIFIED-ABS; TX-016 → CONTESTED |
| B-30 | EPQ-009 | GBD 2019 Mental Disorders Collaborators, *Lancet Psychiatry* 2022 | 970,1 milhões de casos (2019); DALYs 80,8 M (1990) → 125,3 M (2019); de 3,1% para 4,9% dos DALYs globais; 7ª causa de DALYs; carga quase toda em YLD | **Atribuição:** suicídio é contabilizado em "autolesão" (lesões), não em transtornos mentais. A carga mental fica **subestimada** em YLL por convenção do modelo, e não por ausência de mortalidade. | VERIFIED-ABS |
| B-31 | EPQ-006 | Staines et al. 2023, *Schizophr Bull* (meta-análise, população geral) | Incidência ~2/100 por ano; **persistência anual 31%**, maior em adolescentes. Conversão anual a desfecho psicótico clínico 0,56% vs 0,16% sem experiências psicóticas (~3,5×), com dose-resposta | Risco absoluto de conversão baixo: >99% por ano **não** convertem. Experiência psicótica ≠ esquizofrenia (EPQ-005). | VERIFIED-ABS (o "31%" do ledger agora tem fonte) |
| B-32 | NB-030 | FDA De Novo NEBA (jul. 2013); Arns et al. 2013, *J Atten Disord* (9 estudos, 1.253 com TDAH, 517 sem) | NEBA (razão teta/beta) liberado como **auxílio**, não teste isolado. Meta-análise: efeito 0,62–0,75, com heterogeneidade significativa e efeito **decrescente** ao longo dos anos (a razão subiu nos controles) | **Contradição C-RT-4:** liberação regulatória vs meta-análise que conclui que a razão teta/beta "não pode ser considerada medida diagnóstica confiável". Confirma NB-030 (TDAH sem biomarcador diagnóstico rotineiro). | VERIFIED-ABS |
| B-33 | NB-022 | Jansen et al. 2015, *JAMA* (55 estudos; 2.914 cognição normal, 697 queixa subjetiva, 3.972 CCL) | Amiloide positivo em cognição normal: 10% (8–13%) aos 50 anos → 44% (37–51%) aos 90 | Positividade amiloide **não** equivale a demência nem a destino (NB-022). O intervalo estimado de 20–30 anos entre positividade e demência é modelagem. | VERIFIED-ABS |
| B-34 | PF-009 | Bula FDA Zyprexa (olanzapina) | Fumantes: depuração maior e meia-vida ~21% menor (indução de CYP1A2). O "~40%" de depuração do ledger fica **PARTIAL**: não confirmado literalmente | Média populacional. Ao **parar de fumar**, a exposição sobe: fontes clínicas sugerem redução de dose de 30–50% (não é texto de bula). | PARTIAL |
| B-35 | PF-010 | Bula FDA Zyprexa | Fluvoxamina (inibidor de CYP1A2): Cmax +54% (mulheres não fumantes) e +77% (homens fumantes); AUC +52% e +108% | Valores de estudo de interação em voluntários; a magnitude individual varia. | VERIFIED-ABS (texto de bula via espelhos) |
| B-36 | PF-006 | Bula FDA Abilify (aripiprazol); anotação PharmGKB | Metabolizador lento de CYP2D6: **metade** da dose; lento + inibidor forte de CYP3A4: **um quarto**; inibidor forte de 2D6 ou 3A4: metade; ambos: um quarto | A fração de AUC do deidro-aripiprazol (~40%) **não foi conferida**. A versão da bula não foi registrada (pendência: data da revisão). | VERIFIED-ABS (regras de dose) |
| B-37 | PT-027 | Jauhar et al. 2014, *Br J Psychiatry* | TCC para psicose: sintomas globais −0,33 (−0,47 a −0,19; 34 estudos); positivos −0,25; negativos −0,13. Com **avaliação cega**: global −0,15 (−0,27 a −0,03); positivos −0,08 (n.s.) | Efeito pequeno, que encolhe muito com cegamento. "Pode reduzir alguns sintomas/sofrimento" está correto, mas com magnitude pequena e sensível a viés. | VERIFIED-ABS; S4 → **S3** |
| B-38 | PT-011 | Carpenter et al. 2018, *Depress Anxiety* (41 ECR **controlados por placebo**, 2.843) | TCC vs placebo psicológico ou de pílula: sintomas-alvo g = 0,56; resposta OR 2,97; efeitos maiores em TOC, TAG e estresse agudo; menores em TEPT, ansiedade social e pânico | Comparação com placebo (mais conservadora que lista de espera). Não isola a exposição como componente ativo. | VERIFIED-ABS |
| B-39 | PT-028 | de Jong et al. 2021, *Clin Psychol Rev* (58 estudos, 21.699 pacientes) | Feedback de progresso: efeito pequeno, mas robusto, em sintomas (d = 0,15; 0,17 em casos com evolução fora do esperado) | Inclui estudos não randomizados. Efeito pequeno. Depende de implementação (PT-028 já ressalvava). | VERIFIED-ABS |
| B-40 | PT-021 | Cuijpers et al. 2016, *Am J Psychiatry* (90 estudos, 11.434) | IPT na depressão aguda vs controle: g = 0,60 (0,45–0,75); vs outras terapias: diferença g = 0,06 (n.s.); vs farmacoterapia: g = −0,13 (n.s.); combinado > IPT isolada (g = 0,24) | "Sem diferença" ≠ equivalência (PT-007). Controles heterogêneos. Viés de publicação não corrigido no número citado. | VERIFIED-ABS |

### Contradições novas
- **C-RT-3:** polifarmácia antipsicótica. A diretriz desaconselha como padrão; dados observacionais intraindivíduo finlandeses favorecem combinações específicas (clozapina + aripiprazol). Status CONTESTED, sem ECR decisivo.
- **C-RT-4:** razão teta/beta no TDAH. Liberação FDA 2013 vs meta-análise de 2013 que nega confiabilidade diagnóstica.

### Contagem atualizada (estimativa da rodada 2; **substituída** pela seção 8)

| Medida | Rodada 1 | Rodada 2 |
| --- | --- | --- |
| Âncoras verificadas | 23 (≈35 IDs) | 40 (≈55 IDs) |
| Empíricos ainda S2-provisório | ~95 | ~75 |
| Fração de empíricos críticos ancorados | ≈50% | ≈62% |

**Critério ≥90%: ainda NÃO atingido.** Grupos pendentes:
- neurociência: NB-003/004/006/007/008/012–014/021/023/027/031–035/038–041/043/044;
- psicoterapia: PT-001/008–010/012–016/018–020/022/026/029/030/032–034/038/039;
- intervenções: TX-022/023/025/029;
- farmacologia: PF-005/008/011.

## 7. Rodada 3 de ancoragem e reclassificação final

### 7.1 Reclassificados como CONCEPTUAL (definição ou regra de inferência)

PT-001 (definição APA de prática baseada em evidência), PT-008, PT-009, PT-016, PT-018, PT-039, NB-033, NB-041, NB-044, PF-011, TX-022, TX-023, TX-029.

Motivo: afirmam uma distinção lógica do tipo "X não prova Y", ou uma definição. Não afirmam magnitude empírica.

### 7.2 Novas âncoras

| Âncora | ID original | Fonte específica verificada | Número-chave / achado | O que **não** permite concluir | Status novo |
| --- | --- | --- | --- | --- | --- |
| B-41 | NB-003 | Stevens et al. 2007, *Cell*; Schafer et al. 2012, *Neuron* (PMID 22632727) | Camundongos deficientes em C1q/C3 mantêm defeitos de eliminação sináptica retinogeniculada; micróglia engloba terminais pré-sinápticos de forma dependente de atividade e de CR3/C3 | Sistema visual de roedor no desenvolvimento ≠ córtex humano adolescente; a ponte para esquizofrenia é NB-004 (ainda sem âncora) | VERIFIED-ABS |
| B-42 | NB-006 | Bethlehem et al. 2022, *Nature* (123.984 RM, 101.457 pessoas, da 15ª semana fetal aos 100 anos) | Pico da substância cinzenta ~6 anos; branca ~29 anos; cinzenta subcortical ~14,5 anos | Volume ≠ maturidade funcional; dados transversais predominam; amostras majoritariamente de países de alta renda. **Refuta** "o cérebro termina aos 25" como marco único: diferentes medidas têm picos diferentes | VERIFIED-ABS |
| B-43 | NB-012 | Stetler & Miller 2011, *Psychosom Med* 73:114–126 | Ativação do eixo HPA em média elevada na depressão, com heterogeneidade grande (detalhes **não** conferidos) | Média de grupo; depende de subtipo, hora, ensaio e internação | PARTIAL |
| B-44 | NB-013/014 | Arana, Baldessarini & Ornsteen 1985, *Arch Gen Psychiatry* (DST) | Literatura correlata: sensibilidade ~45% e especificidade ~95% na depressão (número de estudo relacionado, PARTIAL) | Sensibilidade baixa e não especificidade frente a outras condições: o DST não serve como teste diagnóstico (confirma NB-014) | PARTIAL |
| B-45 | NB-021/023 | Jansen 2015 (B-33); Ashton 2024 (B-17) | ver B-17/B-33 | ver B-17/B-33 | ancoragem por referência cruzada |
| B-46 | NB-031 | Volkow et al. 2009, *JAMA* (PET; 53 adultos com TDAH sem medicação vs 44 controles) | Menor ligação de DAT e de D2/D3 na via de recompensa esquerda; accumbens DAT 0,63 vs 0,71; D2/D3 2,68 vs 2,85 (p = 0,004) | **Refinamento:** existe redução **média** de marcadores dopaminérgicos num estudo, mas a sobreposição entre grupos é grande, a amostra é de adultos de um único centro e há achados divergentes de DAT na literatura. A regra NB-031 permanece: "TDAH = baixa dopamina" é fórmula inválida, mesmo com evidência parcial de diferença de grupo | VERIFIED-ABS |
| B-47 | NB-035 | Schultz, Dayan & Montague 1997, *Science* 275:1593–1599 | Neurônios dopaminérgicos de primatas sinalizam erro de predição de recompensa (aumento à recompensa inesperada; deslocamento para o estímulo preditor) | Paradigmas específicos com primatas; dopamina também codifica saliência e movimento etc. (NB-036) | VERIFIED-ABS |
| B-48 | NB-038/039, PT-013 | Bouton 2004, *Learn Mem* 11:485–494 | Extinção não apaga a aprendizagem original: gera aprendizagem nova dependente de contexto; renovação, restabelecimento e recuperação espontânea demonstram isso | Base majoritariamente animal; a magnitude clínica do retorno do medo varia | VERIFIED-ABS |
| B-49 | NB-040, PT-012 | Craske et al. 2014, *Behav Res Ther* 58:10–23 | Modelo de aprendizagem inibitória: a redução do medo dentro da sessão não é necessária para o desfecho; 8 estratégias (violação de expectativa, extinção aprofundada, variabilidade etc.) | É revisão e proposta teórica com base experimental; a superioridade clínica das estratégias de otimização **não** está estabelecida por ECR grandes | VERIFIED-ABS (como revisão) |
| B-50 | NB-043 | Klein et al. 2011, *Int J Neuropsychopharmacol* | Rato: BDNF no sangue total × hipocampo r² = 0,44; porco: plasma × hipocampo r² = 0,41; indetectável no sangue de camundongo | **Refinamento:** existe correlação moderada em animais, ou seja, o BDNF periférico não é "leitura direta", mas também não é independente. Não há validação equivalente em humanos vivos. Plaquetas armazenam BDNF, então soro ≠ plasma | VERIFIED-ABS; NB-043 refinado |
| B-51 | PT-010 | Ekers et al. 2014, *PLoS One* (PMID 24936656; 26 ECR, 1.524); Richards et al. 2016, *Lancet* (COBRA) | Ativação comportamental vs controle SMD −0,74 (−0,91 a −0,56); vs medicação SMD −0,42 (4 ECR). COBRA: não inferior à TCC, ~21% mais barata, aplicada por profissionais júnior | Comparações com medicação em poucos ECR; viés de publicação não descartado (ver IB-006) | VERIFIED-ABS, S4 mantido |
| B-52 | PT-014 | Skapinakis 2016 (TQ4): TCC/ERP vs controle no TOC; Carpenter 2018 (B-38): TOC entre os maiores efeitos vs placebo | ver TQ4 e B-38 | ver TQ4 | ancoragem por referência cruzada |
| B-53 | PT-019 | Storebø 2020 Cochrane (B-03) | MBT entre as terapias avaliadas; certeza baixa | Número específico da MBT não conferido | PARTIAL |
| B-54 | PT-022 | Driessen et al. 2015, *Clin Psychol Rev* 42 (54 estudos, 33 ECR, 3.946 pessoas); Leichsenring et al. 2023, *World Psychiatry* (revisão guarda-chuva pré-registrada) | Psicoterapia psicodinâmica breve vs controles no pós-tratamento: d = 0,49–0,69 (depressão, psicopatologia geral, qualidade de vida) | Controles heterogêneos. Efeito de alegiância possível (B-58). A eficácia não valida a teoria psicodinâmica geral (como o próprio PT-022 afirma) | VERIFIED-ABS |
| B-55 | PT-026 | Pharoah et al. 2010, Cochrane CD000088 | Intervenção familiar na esquizofrenia: recaída RR 0,55 (0,5–0,6), NNT 7 (32 ECR, 2.981); internação RR 0,78, NNT 8; adesão RR 0,60, NNT 6 | Os próprios autores alertam que estudos pequenos negativos podem ter sido perdidos (viés de publicação). Heterogeneidade de "intervenção familiar" | VERIFIED-ABS |
| B-56 | PT-029/030 | Cuijpers 2018/2021 (deterioração 5% vs 12–13%, TQ4); Jonsson et al. 2014 (132 ECR) | Só **21%** (28/132) dos ECR de intervenções psicológicas relataram eventos adversos, quase sempre com definição incompleta | Ausência de relato ≠ ausência de dano | VERIFIED-ABS |
| B-57 | PT-032 | Swift et al. 2018, *J Clin Psychol* (53 estudos, >16.000) | Acomodar a preferência: menos abandono (OR 1,79) e desfecho um pouco melhor (d = 0,28) | Grande parte dos estudos não randomiza a preferência; confundimento possível | VERIFIED-ABS |
| B-58 | PT-038 | Munder et al. 2013, *Clin Psychol Rev* 33:501–511 (meta-meta-análise) | Associação alegiância do pesquisador × desfecho r = 0,262 (I² = 29%) | Alegiância pode refletir em parte verdadeira superioridade, debatido em Munder 2012; associação ≠ viés comprovado em cada estudo | VERIFIED-ABS |
| B-59 | PT-034 | Fernandez et al. 2021, *Clin Psychol Psychother* (meta-análise; 47 estudos entre grupos, 3.564) | Vídeo vs presencial: diferença desprezível; vídeo vs lista de espera g = 0,77; mais forte com TCC em ansiedade, depressão e TEPT | "Não diferença" ≠ equivalência formal (PT-007); amostras selecionadas com acesso a tecnologia | VERIFIED-ABS |
| B-60 | TX-025 | Fairburn et al. 2015, *Behav Res Ther* (PMC4461007, TCC-E vs IPT); Atwood & Friedman 2019/2020 (revisão, 20 estudos) | Remissão pós-tratamento TCC-E 65,5% vs IPT 33,3%; no seguimento 69,4% vs 49,0% | Ensaio sem anorexia de baixo peso (amostra de bulimia/outros). Grupo do desenvolvedor (alegiância, B-58). A eficácia na anorexia adulta é mais fraca | VERIFIED-ABS (TX-025 ganha a ressalva diagnóstica) |
| B-61 | PF-005 | B-07 (FDA, comitê conjunto 19 nov 2024) | ver B-07 | — | referência cruzada |
| B-62 | PF-008 | Bula FDA Abilify Maintena (accessdata, revisão 2026) | Meia-vida terminal aparente 29,9 dias (300 mg) e 46,5 dias (400 mg) após doses gluteais repetidas; sobreposição oral de 14 dias no início | A versão citada é a revisão de 2026; outras formulações LAI (Aristada, 2 meses) têm PK própria | VERIFIED-ABS |
| B-63 | TQ-003 | Leucht et al. 2012, *Lancet* 379:2063–71 (65 ECR, 6.493 pacientes) | Recaída em 7–12 meses: droga 27% vs placebo 64%; RR 0,40 (0,33–0,49); NNT 3 (2–3). Reinternação 10% vs 26%, NNT 5 | Desenho de **retirada**: parte da "recaída com placebo" pode ser efeito de descontinuação abrupta. Horizonte de ~1 ano; não responde sobre manutenção indefinida nem sobre redução gradual (ver a controvérsia Wunderink/redução de dose, não ancorada aqui) | VERIFIED-ABS |
| B-64 | PT-033 | Hall et al. 2016, *Behav Ther* (78 estudos, 13.998 participantes, 95% de amostras não euro-americanas) | Intervenções culturalmente adaptadas vs outras condições: g = 0,67; vs versão **não adaptada** da mesma intervenção: g = 0,52 | Heterogeneidade grande no que conta como "adaptação". Poucos ECR comparam diretamente adaptado vs não adaptado; o resultado depende de quem adapta e de como | VERIFIED-ABS |
| B-65 | PT-020 | Giesen-Bloo et al. 2006, *Arch Gen Psychiatry* (terapia do esquema vs TFP no TPB); Bamelis et al. 2014, *Am J Psychiatry* (323 pacientes, cluster C e outros) | TPB: recuperação completa 46% (esquema) vs 24% (TFP); abandono 25% vs 50%. Bamelis: maior recuperação com terapia do esquema que com TAU e com terapia de clarificação (% exatos não conferidos) | Ensaios do grupo desenvolvedor (alegiância, B-58). Giesen-Bloo compara duas psicoterapias ativas sem controle inativo. "Modo esquemático" segue construto teórico (PT-020) | VERIFIED-ABS (com % de Bamelis PARTIAL) |
| B-66 | NB-027 | Bateman et al. 2012, *NEJM* (DIAN, 128 participantes); revisões sobre DA autossômica dominante (PMC6052673) | Variantes em APP/PSEN1/PSEN2: penetrância quase completa; <1% de todos os casos de Alzheimer. Na DA dominante, Aβ42 no LCR cai ~25 anos antes do início esperado, amiloide no PET aparece ~15 anos antes e hipometabolismo e memória ~10 anos antes | A sequência temporal é estimada por **anos até o início esperado** (desenho transversal ancorado na idade parental). A generalização para a DA esporádica de início tardio é inferência (como o NB-027 já alerta) | VERIFIED-ABS |

### Contradição nova
- **C-RT-5 (BDNF periférico):** o ledger dizia "não é leitura direta"; Klein 2011 mostra r² ≈ 0,4 em duas espécies. A formulação correta é intermediária: correlação moderada em animais e não validada em humanos. Isso **não** autoriza usar BDNF sérico como marcador cerebral individual.


### 7.3 Classificação dos casos residuais

- **CONCEPTUAL** (inferência proibida, sem magnitude empírica): NB-005, NB-010, NB-011, TX-012, PF-031, PF-050, PF-055, TQ-011.
- **Referência cruzada a fonte já ancorada na base:**
  - TQ-007: síntese de CBT-I vs higiene do sono, 42 ensaios, 4.245 adultos (lote 1);
  - TQ-010: B-26 (CORE);
  - PF-045: NICE CG185, atualização de 2 set 2025, já citada com versão no dossiê de humor;
  - NB-014: B-44;
  - NB-023/025: B-17;
  - NB-029: B-18;
  - NB-039: B-48;
  - NB-002: B-14;
  - PF-002: B-23.
- **Ainda sem âncora (S2-provisório):**
  - NB-004: evidência posterior complica "mais C4 = mais poda";
  - NB-007: puberdade/hormônios × cérebro;
  - NB-008: inferências no ABCD;
  - NB-032: autismo sem biomarcador de imagem;
  - NB-034: variabilidade de conectividade no autismo;
  - PT-015: tranquilização como neutralização no TOC.

## 8. Contagem final (exata, por conjunto de IDs)

| Conjunto | n |
| --- | --- |
| Linhas genéricas com S3/S4 nos ledgers originais | 144 |
| Reclassificadas CONCEPTUAL | 57 |
| Ancoradas em fonte específica verificada, diretamente ou por referência cruzada | 81 |
| Ainda sem âncora (S2-provisório) | 6 |

- **Empíricas:** 81 + 6 = 87. Ancoradas: 81/87 = **93%**.
- **Qualidade das âncoras:** cerca de 15% são PARTIAL, por número não confirmado ou fonte secundária. O critério "≥90% VERIFIED/PARTIAL com contexto" do protocolo é **atingido para os 144 claims auditados**.
- **Ressalvas que permanecem:**
  1. As âncoras são **VERIFIED-ABS** (resumo indexado), não leitura do texto integral, porque o acesso direto estava bloqueado.
  2. As **frases narrativas** dos 40 dossiês sem PMID/DOI **não** foram convertidas uma a uma (pendência RR-P3). O que vale como fonte desses dossiês é o ledger, não o texto corrido.
  3. Os 6 claims restantes ficam explicitamente rebaixados.

## Apêndice — classificador usado na seção 1

```python
import re, glob
specific = re.compile(r'PMID|10\.\d{4}|https?://|\b(19|20)\d{2}\b|NICE [A-Z]{1,3}\d+|CG\d+|NG\d+|FDA|EMA|CPIC|Cochrane|WHO|CDDR|DSM|label|bula|[A-Z][a-z]+ (et al|\d{4})|STAR\*D|CATIE|EAGLES|MTA|TADS|ANTLER', re.I)
for f in sorted(glob.glob("2026-10-02-*.md")):
    for l in open(f):
        cells = [c.strip() for c in l.strip().strip('|').split('|')]
        if not l.startswith('|') or len(cells) < 4 or not re.match(r'[A-Z]{1,4}[-_]?\d{2,3}', cells[0]):
            continue
        src = cells[-1]                      # última coluna = fonte/limite
        sup = next((c for c in cells if re.fullmatch(r'S[0-4]', c)), '')
        tag = 'ancorada' if specific.search(src) else 'genérica'
```
Limite conhecido: quando a última coluna é "limite", e não "fonte", a linha conta como genérica mesmo com âncora em outra coluna. Isso superestima um pouco o déficit; a revisão manual da seção 3 corrige os casos encontrados.

**Integração:** nenhuma. **Treinamento:** nenhum.
