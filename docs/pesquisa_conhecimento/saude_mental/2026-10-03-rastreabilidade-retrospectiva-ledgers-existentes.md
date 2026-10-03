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

## 5. Efeito sobre o critério do protocolo

| Medida | Antes | Depois desta rodada |
| --- | --- | --- |
| Linhas empíricas críticas com fonte específica (aprox.) | 59 | 59 + 23 âncoras (B-01…B-23 cobrem ~35 IDs) ≈ 94 |
| Regras metodológicas com rótulo correto | 0 | ~45 reclassificadas CONCEPTUAL |
| Empíricas sem âncora | ~130 | ~95 (S2-provisório) |
| Critério ≥90% de claims quantitativos críticos ancorados | não | **não** (≈50% das empíricas) |

**Conclusão honesta:**
- a rodada **reduz** o déficit e, sobretudo, **impede leitura enganosa**: S4 sem fonte deixa de valer como S4;
- não atinge o critério. O déficit de ancoragem dos ledgers de neurociência e psicoterapia continua **material**.

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
