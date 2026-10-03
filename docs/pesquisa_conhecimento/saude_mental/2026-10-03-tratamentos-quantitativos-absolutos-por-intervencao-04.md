# Tratamentos quantitativos — efeitos absolutos, IC, NNT/NNH e danos por intervenção, lote 4

**Data:** 2026-10-03. **Branch:** `pesquisa/base-saude-mental-doutorado`. Pesquisa documental; não integra nem treina o CRIVO.

Este lote responde à lacuna registrada no README (Aprofundamento 19 e lote 3): "falta extrair absolute response/remission/relapse e AE rates com CI/NNT/NNH por transtorno/intervenção". Os lotes 1–3 definiram a estrutura (comparador, horizonte, estimands, NNT dependente do risco basal); aqui ficam os **números**, cada um ligado a uma fonte identificável e com o que ela **não** permite concluir.

## 0. Método e limites de verificação

**Como cada número foi conferido.** Nesta sessão o acesso direto a PubMed, PMC, WHO, NICE e editoras estava bloqueado pela rede do ambiente. Cada número abaixo foi confrontado com o resumo/abstract indexado da publicação (via mecanismo de busca que retorna o texto do resumo e o endereço da fonte). Status usados, compatíveis com o protocolo de rastreabilidade do acervo:

| Status | Significado neste lote |
|---|---|
| VERIFIED-ABS | número, população e desenho conferidos no resumo/abstract da fonte primária ou da síntese; texto integral **não** lido |
| PARTIAL | parte do claim conferida (ex.: taxas absolutas), outra parte (ex.: HR, IC) não localizada no resumo |
| UNVERIFIED | número lembrado da literatura e **não** confirmado nesta sessão; não usar como suporte |
| DERIVED | cálculo aritmético feito aqui a partir de números VERIFIED-ABS (ex.: NNT = 1/ARR); **não** é número reportado pela fonte |

**Regra de NNT/NNH derivado.** NNT derivado de taxas agregadas de meta-análise assume risco basal comum entre ensaios heterogêneos; serve como ordem de grandeza no contexto (população, comparador, horizonte) da fonte, nunca como propriedade do tratamento.

**Ressalva transversal.** Todos os efeitos abaixo são médias de populações de ensaio (frequentemente excluem suicidalidade aguda, gravidez, uso de substâncias, multimorbidade, deficiência intelectual). Eficácia em ensaio ≠ efetividade em serviço; diferença estatística ≠ importância clínica; taxa de resposta no braço ativo ≠ efeito causal do tratamento.

---

## 1. Depressão em adultos — tratamento agudo

### 1.1 Antidepressivos versus placebo (síntese em rede)
- **Fonte:** Cipriani A et al. *Lancet* 2018;391:1357–1366. PMID 29477251; DOI 10.1016/S0140-6736(17)32802-7. Rede de ensaios duplo-cegos (busca até 8 jan 2016), 522 ensaios, 116 477 participantes, 21 antidepressivos.
- **Resultado:** todos os 21 antidepressivos tiveram maior chance de resposta que placebo; OR de resposta aproximadamente de 2,13 (maior) a 1,37 (menor). A aceitabilidade (abandono por qualquer causa) variou entre moléculas e não acompanhou a eficácia.
- **Demonstra:** superioridade média de curto prazo (geralmente 8 semanas) sobre placebo em adultos com transtorno depressivo maior que entram em ensaios.
- **Não permite concluir:** (a) tamanho do benefício para um indivíduo — OR não é diferença de risco nem NNT sem taxa basal; (b) ranking clínico universal entre moléculas; (c) efeito em depressão leve, adolescentes, idosos frágeis ou comorbidades excluídas; (d) efeito de longo prazo; (e) etiologia monoaminérgica.
- **Status:** VERIFIED-ABS (desenho, N, faixa de OR); números molécula a molécula UNVERIFIED neste lote.

### 1.2 Distribuição individual da resposta (dados individuais da FDA)
- **Fonte:** Stone MB, Yaseen ZS, Miller BJ, Richardville K, Kalaria SN, Kirsch I. *BMJ* 2022 (análise de dados individuais de 232 ensaios de monoterapia antidepressiva para depressão maior submetidos à FDA entre 1979 e 2016; 73 388 participantes). Análise complementar de efeitos por quantis em PMC10257092.
- **Resultado:** o modelo dos autores estima que cerca de **15%** dos participantes têm uma resposta robusta atribuível ao fármaco; a vantagem média sobre placebo é melhor descrita como aumento da probabilidade de resposta grande (ou redução da de resposta mínima) em uma minoria.
- **Demonstra:** a diferença média pequena droga–placebo é compatível com benefício concentrado em subgrupo, não com efeito pequeno uniforme.
- **Não permite concluir:** quem é esse subgrupo (não há marcador validado); que os outros 85% "não respondem" (muitos melhoram, inclusive no placebo); efeito fora de ensaios regulatórios. O modelo de mistura tem pressupostos próprios e foi debatido (ver lote de contradições).
- **Status:** VERIFIED-ABS (N, ensaios, ~15%).

### 1.3 Psicoterapia para depressão — resposta, remissão e deterioração absolutas
- **Fonte:** Cuijpers P et al. *Acta Psychiatrica Scandinavica* 2021;144:288–299. PMID 34107050; PMC8457213. 228 ensaios randomizados (75 de baixo risco de viés).
- **Resultado (2 ± 1 meses):** resposta (redução ≥50%) **41%** (IC95% 38–43) com psicoterapia vs **17%** (15–20) com cuidado usual e **16%** (14–18) em lista de espera; NNT 5,3 vs cuidado usual e 3,9 vs lista de espera; remissão ~um terço vs 7–13%; deterioração clinicamente significativa **5%** vs 12–13%.
- **Demonstra:** benefício absoluto relevante em média e menor deterioração que controles passivos.
- **Não permite concluir:** que 41% respondem *por causa* da terapia (parte responderia sem ela); que lista de espera é controle neutro (pode inflar o efeito); superioridade de uma escola sobre outra; durabilidade além de ~2 meses.
- **Status:** VERIFIED-ABS.

### 1.4 Estimulação magnética (rTMS 10 Hz vs theta burst)
- **Fonte:** Blumberger DM et al. *Lancet* 2018 (THREE-D). Ensaio de não inferioridade, 192 (10 Hz) e 193 (iTBS) participantes; mais da metade com ≥2 falhas antidepressivas.
- **Resultado:** resposta 47% (10 Hz) vs 49% (iTBS); remissão 27% vs 32%; iTBS de 3 minutos não inferior a 10 Hz de 37,5 minutos.
- **Demonstra:** equivalência dentro da margem pré-definida entre dois protocolos ativos.
- **Não permite concluir:** eficácia contra simulação (não houve braço sham); que qualquer theta burst seja equivalente; que as taxas absolutas sejam efeito específico (sem placebo, parte é melhora inespecífica).
- **Status:** VERIFIED-ABS.

### 1.5 Eletroconvulsoterapia (ECT)
- **Fonte:** UK ECT Review Group. *Lancet* 2003;361:799–808. PMID 12642045.
- **Resultado:** ECT real vs simulada: 6 ensaios, 256 pacientes, tamanho de efeito padronizado −0,91 (IC95% −1,27 a −0,54), diferença média na HRSD de 9,67 pontos (5,72–13,53).
- **Demonstra:** efeito agudo grande contra simulação em ensaios antigos e pequenos.
- **Não permite concluir:** magnitude atual com técnicas modernas (os ensaios sham são antigos e pequenos); efeito de manutenção; perfil cognitivo (avaliado separadamente na mesma revisão e em literatura posterior).
- **Status:** VERIFIED-ABS.

### 1.6 Psilocibina em depressão resistente (fase 2b)
- **Fonte:** Goodwin GM et al. *NEJM* 2022 (COMP360). 233 participantes, doses 1, 10 e 25 mg com suporte psicológico.
- **Resultado:** diferença de −6,6 na MADRS (25 mg vs 1 mg) na semana 3; cerca de 30% em remissão com 25 mg na semana 3; ideação suicida e autolesão relatadas com mais frequência nos braços 10 e 25 mg que em 1 mg.
- **Demonstra:** efeito agudo dose-dependente em ensaio de fase 2b, com sinal de dano a monitorar.
- **Resposta sustentada até a semana 12 (desfecho secundário):** 20,3% (25 mg) vs 10,1% (1 mg); 5,3% com 10 mg. Grupos: 25 mg n=79, 10 mg n=75, 1 mg n=79; 22 centros.
- **Não permite concluir:** benefício durável robusto (a vantagem diminui até a semana 12 e o desfecho sustentado é secundário); cegamento efetivo (efeitos subjetivos permitem adivinhar o braço); segurança fora de ambiente controlado; equivalência a cogumelos ou uso recreativo; dose-resposta monotônica (10 mg teve resposta sustentada menor que 1 mg).
- **Status:** VERIFIED-ABS.

## 2. Depressão — prevenção de recaída e retirada

### 2.1 Manter versus trocar por placebo (ensaios de retirada)
- **Fonte:** Geddes JR et al. *Lancet* 2003. 31 ensaios, 4 410 participantes.
- **Resultado:** recaída **18%** com antidepressivo vs **41%** com placebo; redução de 70% nas chances (IC95% 62–78).
- **Derivado:** ARR ≈ 23 pontos → NNT ≈ 4 no horizonte e população agregados (DERIVED).
- **Não permite concluir:** que todo paciente recairá ao parar; separar recaída verdadeira de sintomas de retirada em trocas abruptas por placebo (viés de retirada); horizonte além do ensaio.
- **Status:** VERIFIED-ABS (taxas e redução de chances).

### 2.2 Retirada em atenção primária (ANTLER)
- **Fonte:** Lewis G et al. *NEJM* 2021;385:1257–1267. 478 pacientes de 150 práticas no Reino Unido que se sentiam bem para parar.
- **Resultado (52 semanas):** recaída 39% (92/238) mantendo vs 56% (135/240) descontinuando; HR 2,06 (IC95% 1,56–2,70).
- **Derivado:** ARR ≈ 17 pontos → NNT ≈ 6 em 1 ano (DERIVED).
- **Demonstra:** para quem já estava estável e queria parar, a descontinuação aumentou recaída em 1 ano.
- **Não permite concluir:** que ninguém deva parar (56% não é 100%; 44% não recaíram); que todos os sintomas pós-retirada sejam recaída (houve mais sintomas de retirada no braço de descontinuação, e a redução foi relativamente rápida); efeito de redução mais lenta e individualizada.
- **Status:** VERIFIED-ABS.

### 2.3 Escetamina intranasal — manutenção (SUSTAIN-1)
- **Fonte:** Daly EJ et al. *JAMA Psychiatry* 2019. 297 adultos em fase de manutenção com depressão resistente.
- **Resultado (176 em remissão estável):** recaída 26,7% com escetamina + antidepressivo vs 45,3% com placebo + antidepressivo.
- **Derivado:** ARR ≈ 18,6 pontos → NNT ≈ 5 (DERIVED, desenho enriquecido).
- **Não permite concluir:** benefício em quem não respondeu à fase aberta (desenho de retirada randomizada seleciona respondedores); ausência de viés por cegamento imperfeito (efeitos dissociativos); segurança de longo prazo; mesmo efeito para cetamina genérica.
- **Status:** PARTIAL (taxas conferidas; HR e IC não localizados no resumo).

## 3. Esquizofrenia

### 3.1 Antipsicóticos versus placebo — resposta aguda
- **Fonte:** Leucht S et al. *Am J Psychiatry* 2017. 167 ensaios duplo-cegos, 28 102 participantes, majoritariamente crônicos.
- **Resultado:** resposta mínima 51% vs 30%; boa resposta 23% vs 14%.
- **Derivado:** resposta mínima NNT ≈ 5; boa resposta NNT ≈ 11 (DERIVED).
- **Demonstra:** cerca do dobro de melhora com antipsicótico, mas boa resposta é minoria.
- **Não permite concluir:** eficácia em primeiro episódio (que tende a responder melhor e foi sub-representado); efeito sobre sintomas negativos ou cognição; desfechos funcionais.
- **Status:** VERIFIED-ABS.

### 3.2 Manutenção versus retirada
Já registrado no lote 3 (Ceraso 2020 Cochrane: 75 ensaios, ~9 145 participantes; recaída ~24% vs ~61% em 7–12 meses; RR ~0,38, IC95% ~0,32–0,45; NNT ~3). **Mantido como PARTIAL** até conferência do resumo; o achado é coerente com a meta-análise anterior de Leucht 2012.
- **Não permite concluir:** risco de recaída com redução gradual planejada versus retirada abrupta dos ensaios; trajetória de longo prazo de funcionamento (contestado por coortes de longo prazo; ver lote de contradições).

### 3.3 Clozapina — resposta e neutropenia
- **Resposta em resistentes:** Siskind D et al. 2017 (revisão sistemática e meta-análise): resposta global **40,1%** em esquizofrenia resistente. Status: VERIFIED-ABS para a taxa; IC não registrado aqui.
  - Não permite concluir: que os 60% restantes não melhorem nada (critério de resposta é limiar); comparação causal com outros antipsicóticos (é taxa de braço único agregada).
- **Neutropenia:** Myles N et al. 2018 (108 estudos, >450 000 pacientes): neutropenia 3,8% (IC95% 2,7–5,2); neutropenia grave **0,9%** (0,7–1,1); morte por complicações de agranulocitose **0,013%** (≈1 em 7 700). Uma fonte secundária cita 0,7% para neutropenia grave — **discrepância** registrada; preferir o valor com IC do resumo (0,9%) até leitura integral. Status: PARTIAL.
  - Não permite concluir: risco individual sem monitoramento (os números vêm em grande parte de populações monitoradas); que o fim do REMS americano em 2025 reduza o risco biológico.

### 3.4 Discinesia tardia — incidência comparada
- **Fonte:** Carbon M et al. *World Psychiatry* 2018. 57 ensaios randomizados cabeça a cabeça.
- **Resultado:** incidência anualizada 6,5% (IC95% 5,3–7,8) com antipsicóticos de primeira geração vs 2,6% (2,0–3,1) com segunda geração.
- **Atenção a citação:** os números são frequentemente atribuídos ao artigo de prevalência de 2017 (*J Clin Psychiatry*: prevalência 30,0% com FGA vs 20,7% com SGA em 41 estudos). São estudos diferentes, com medidas diferentes (incidência anual em ensaios vs prevalência em amostras).
- **Não permite concluir:** que SGA "não causam" DT; comparações justas de dose (haloperidol em dose alta foi comparador frequente); risco em idosos (maior).
- **Status:** VERIFIED-ABS.

### 3.5 Antipsicóticos em demência — mortalidade (dano)
- **Fonte:** FDA, alerta de abril de 2005 (e tarja preta subsequente). 17 ensaios controlados por placebo (olanzapina, aripiprazol, risperidona, quetiapina) em idosos com demência e sintomas comportamentais; 15 deles (>5 106 pacientes) com aumento de 1,6–1,7 vezes na mortalidade; mortalidade ≈4,5% vs ≈2,6% em ~10 semanas; mortes sobretudo cardiovasculares (insuficiência cardíaca, morte súbita) ou infecciosas (pneumonia).
- **Derivado:** ARI ≈ 1,9 ponto → NNH ≈ 53 em ~10 semanas (DERIVED).
- **Não permite concluir:** mecanismo causal único; que antipsicóticos de primeira geração sejam mais seguros (estudos observacionais posteriores sugerem risco igual ou maior); proibição absoluta (decisões individuais ponderam risco–benefício).
- **Status:** VERIFIED-ABS (regulatório, EUA, 2005).

## 4. Transtorno bipolar

### 4.1 Lítio — suicídio e mortalidade
- **Fonte:** Cipriani A, Hawton K, Stockton S, Geddes JR. *BMJ* 2013;346:f3646. 48 ensaios randomizados, 6 674 participantes.
- **Resultado:** suicídio: OR 0,13 (IC95% 0,03–0,66) lítio vs placebo; morte por qualquer causa: OR 0,38 (0,15–0,95).
- **Não permite concluir:** magnitude precisa (pouquíssimos eventos; IC muito largo); que o efeito seja independente da prevenção de episódios; transportabilidade para pacientes com alto risco excluídos dos ensaios. **Contradição:** ensaio randomizado duplo-cego posterior em veteranos americanos com depressão maior ou bipolaridade e evento suicida recente (Katz IR et al., *JAMA Psychiatry*, jan. 2022) foi interrompido por futilidade após 519 participantes: eventos relacionados a suicídio em 65 (lítio) vs 62 (placebo), sem diferença. Diferenças de população (alto risco, comorbidade com uso de substâncias, adesão e níveis séricos) impedem dizer que um resultado anula o outro; ver lote de contradições. Status Katz 2022: VERIFIED-ABS.
- **Status:** VERIFIED-ABS para Cipriani 2013.

### 4.2 Lítio — manutenção
- **Fonte:** Severus E et al. *Int J Bipolar Disord* 2014 (PMC4272359): lítio vs placebo previne claramente episódios maníacos; efeito sobre episódios depressivos equívoco. Consistente com Geddes 2004 (770 participantes).
- **Status:** PARTIAL (direção confirmada; RR por polo não localizado no resumo).

### 4.3 Valproato — dano reprodutivo (regulatório)
- **Fontes:** EMA/MHRA (comunicações 2018 e medidas reforçadas 2024). Exposição intrauterina: malformações congênitas em ~10–11% (vs 2–3% na população geral) e distúrbios do neurodesenvolvimento em até 30–40%; aumento de risco de autismo descrito em ordem de várias vezes. Valproato não deve ser prescrito a meninas, adolescentes e mulheres em idade fértil salvo falha/intolerância de alternativas, com programa de prevenção de gravidez.
- **Não permite concluir:** que os números sejam iguais para todas as doses (risco é dose-dependente); conclusões sobre exposição paterna (medidas do Reino Unido de 2024 para homens são precaucionais e baseadas em estudo observacional com limitações — conferir).
- **Status:** VERIFIED-ABS (faixas regulatórias); regras para homens UNVERIFIED.

## 5. Ansiedade e TOC

### 5.1 Transtorno de ansiedade generalizada — fármacos
- **Fonte:** Slee A et al. *Lancet* 2019;393:768–777. PMID 30712879. 89 ensaios, 25 fármacos, >25 000 pacientes.
- **Resultado (HAM-A, diferença vs placebo):** duloxetina −3,13 (ICr95% −4,13 a −2,13); pregabalina −2,79 (−3,69 a −1,91); venlafaxina −2,69 (−3,50 a −1,89); escitalopram −2,45 (−3,27 a −1,63), com boa aceitabilidade relativa.
- **Não permite concluir:** importância clínica individual (≈2,5–3 pontos na HAM-A é efeito modesto); eficácia de benzodiazepínicos de longo prazo (tolerância/dependência analisadas à parte); comparação com psicoterapia (fora da rede).
- **Status:** VERIFIED-ABS.

### 5.2 TOC — rede de tratamentos
- **Fonte:** Skapinakis P et al. *Lancet Psychiatry* 2016. 54 ensaios, 6 652 participantes; Y-BOCS.
- **Resultado:** terapia comportamental (exposição com prevenção de resposta) diferença média −14,48 (ICr95% −18,61 a −10,23) vs placebo, com base em 11 ensaios.
- **Não permite concluir:** que a terapia seja ~4 vezes "mais forte" que ISRS na prática: grande parte dos ensaios de psicoterapia usou lista de espera (controle passivo) e o efeito depende da rede; os próprios autores alertam para essa limitação. Diferenças médias de ISRS e clomipramina vs placebo: UNVERIFIED nesta sessão.
- **Status:** VERIFIED-ABS (terapia comportamental).

## 6. Trauma (PTSD)
- **Abandono:** Lewis C, Roberts NP, Gibson S, Bisson JI. *Eur J Psychotraumatol* 2020: abandono agregado em ensaios de psicoterapia para PTSD **16%** (IC95% 14–18); terapias focadas no trauma associadas a maior abandono.
- **Não permite concluir:** que abandono signifique dano ou falha (pode ser melhora, logística, intolerância); que terapias focadas no trauma sejam piores (têm maior eficácia média em outras sínteses).
- **Status:** VERIFIED-ABS. Efeito de eficácia por modalidade (PE, CPT, EMDR): UNVERIFIED nesta sessão — pendência registrada.

## 7. TDAH
- **Fonte:** Cortese S et al. *Lancet Psychiatry* 2018;5:727–738. 133 ensaios duplo-cegos (81 em crianças/adolescentes, 51 em adultos, 1 em ambos), 10 068 crianças/adolescentes e 8 131 adultos.
- **Resultado:** metilfenidato em crianças/adolescentes e anfetaminas em adultos como primeiras escolhas para tratamento de **curto prazo**, considerando eficácia (avaliação de clínicos/professores) e tolerabilidade (abandono por efeito adverso).
- **Não permite concluir:** efeitos de longo prazo (ensaios curtos, ~12 semanas); desfechos funcionais, acadêmicos ou de segurança cardiovascular de longo prazo; DMP por molécula (UNVERIFIED nesta sessão).
- **Status:** VERIFIED-ABS (desenho, N, conclusão).

## 8. Uso de substâncias

### 8.1 Álcool
- **Fonte:** Jonas DE et al. *JAMA* 2014. 122 ensaios + 1 coorte, 22 803 participantes.
- **Resultado:** NNT para evitar retorno a qualquer consumo: acamprosato **12** (IC95% 8–26); naltrexona oral 50 mg/dia **20** (11–500); sem diferença significativa entre os dois em comparação direta.
- **Não permite concluir:** precisão do efeito da naltrexona (IC até 500 = efeito incerto nesse desfecho); efeitos sobre consumo pesado (desfecho diferente, conferir); efetividade sem acompanhamento psicossocial.
- **Status:** VERIFIED-ABS.

### 8.2 Opioides — mortalidade dentro e fora do tratamento agonista
- **Fonte:** Sordo L et al. *BMJ* 2017;357:j1550. 19 coortes; 122 885 pessoas em metadona e 15 831 em buprenorfina.
- **Resultado:** mortalidade por todas as causas 11,3 vs 36,1 por 1 000 pessoas-ano dentro vs fora de metadona (razão fora/dentro 3,20; IC95% 2,65–3,86); 4,3 vs 9,5 para buprenorfina (2,20; 1,34–3,61). Overdose: 2,6 vs 12,7 (metadona) e 1,4 vs 4,6 (buprenorfina).
- **Não permite concluir:** efeito causal exato (coortes observacionais, razões não ajustadas, confundimento por quem permanece em tratamento); NNT (não é ensaio). Achado complementar importante: risco aumenta nas primeiras semanas de entrada e de saída do tratamento — retenção é desfecho de segurança.
- **Status:** VERIFIED-ABS.

### 8.3 Tabaco em pessoas com e sem transtorno psiquiátrico
- **Fonte:** Anthenelli RM et al. *Lancet* 2016 (EAGLES). 8 144 fumantes, ~metade com história psiquiátrica (depressão, bipolar, ansiedade, psicose estáveis); vareniclina, bupropiona, adesivo de nicotina e placebo por 12 semanas.
- **Resultado:** sem aumento significativo de eventos neuropsiquiátricos graves com vareniclina ou bupropiona vs placebo e adesivo; vareniclina mais eficaz que placebo, adesivo e bupropiona para abstinência. Taxas absolutas de abstinência: UNVERIFIED nesta sessão.
- **Coorte psiquiátrica:** mais eventos em todos os braços que na coorte não psiquiátrica; diferença de risco no desfecho composto vs placebo de 2,7% (vareniclina), 2,2% (bupropiona) e 0,4% (adesivo) — sem significância para eventos graves, mas não zero.
- **Consequência regulatória:** a FDA retirou em dezembro de 2016 a tarja preta neuropsiquiátrica de vareniclina e bupropiona com base no EAGLES (VERIFIED-ABS; EUA).
- **Não permite concluir:** segurança em pacientes instáveis ou com suicidalidade ativa (excluídos).
- **Status:** VERIFIED-ABS (desenho, conclusão).

## 9. Insônia — terapia cognitivo-comportamental (CBT-I)
- **Fonte:** Trauer JM et al. *Ann Intern Med* 2015;163:191–204. PMID 26054060. Meta-análise de CBT-I em adultos com insônia crônica, desfechos de diário do sono.
- **Status:** desenho VERIFIED-ABS; magnitudes frequentemente citadas (latência −19 min, despertares −26 min, eficiência +9,9 pontos) **UNVERIFIED** nesta sessão — não usar até leitura do resumo/texto.
- O lote 1 do acervo já registra síntese de 2025 em atenção de rotina (32 estudos, 5 231 participantes; remissão ~45%, alto risco de viés) e superioridade de CBT-I sobre higiene do sono isolada (42 ensaios, 4 245 adultos).

## 10. Tabela-resumo (efeito relativo e absoluto)

| ID | Intervenção / população / horizonte | Comparador | Desfecho | Resultado | NNT/NNH | Status |
|---|---|---|---|---|---|---|
| TQ4-001 | 21 antidepressivos, MDD adulto, ~8 sem | placebo | resposta | OR 1,37–2,13 | não derivável sem risco basal | VERIFIED-ABS |
| TQ4-002 | antidepressivos (IPD FDA) | placebo | resposta robusta específica | ~15% dos participantes | — | VERIFIED-ABS |
| TQ4-003 | psicoterapia, depressão, 2±1 meses | cuidado usual / lista | resposta | 41% vs 17% / 16% | 5,3 / 3,9 (reportado) | VERIFIED-ABS |
| TQ4-004 | psicoterapia | controles | deterioração | 5% vs 12–13% | — | VERIFIED-ABS |
| TQ4-005 | iTBS vs rTMS 10 Hz | ativo | resposta/remissão | 49/32% vs 47/27% | não inferior | VERIFIED-ABS |
| TQ4-006 | ECT real | simulada | HRSD | SES −0,91; −9,67 pts | — | VERIFIED-ABS |
| TQ4-007 | psilocibina 25 mg, TRD, 3 sem | 1 mg | MADRS | −6,6 | — | VERIFIED-ABS |
| TQ4-007b | psilocibina 25 mg, até 12 sem | 1 mg | resposta sustentada | 20,3% vs 10,1% | ~10 (DERIVED, secundário) | VERIFIED-ABS |
| TQ4-008 | antidepressivo continuado | placebo | recaída | 18% vs 41% | ~4 (DERIVED) | VERIFIED-ABS |
| TQ4-009 | manter antidepressivo, APS, 52 sem | descontinuar | recaída | 39% vs 56%; HR 2,06 | ~6 (DERIVED) | VERIFIED-ABS |
| TQ4-010 | escetamina, remissão estável | placebo | recaída | 26,7% vs 45,3% | ~5 (DERIVED, enriquecido) | PARTIAL |
| TQ4-011 | antipsicóticos, esquizofrenia aguda | placebo | resposta mínima / boa | 51 vs 30% / 23 vs 14% | ~5 / ~11 (DERIVED) | VERIFIED-ABS |
| TQ4-012 | antipsicótico de manutenção, 7–12 m | retirada | recaída | ~24% vs ~61% | ~3 | PARTIAL (lote 3) |
| TQ4-013 | clozapina, resistente | — (braço único) | resposta | 40,1% | — | VERIFIED-ABS |
| TQ4-014 | clozapina | — | neutropenia grave / morte | 0,9% / 0,013% | — | PARTIAL |
| TQ4-015 | FGA vs SGA, ensaios | cabeça a cabeça | DT anualizada | 6,5% vs 2,6% | — | VERIFIED-ABS |
| TQ4-016 | antipsicóticos atípicos, demência, ~10 sem | placebo | morte | 4,5% vs 2,6% | NNH ~53 (DERIVED) | VERIFIED-ABS |
| TQ4-017 | lítio, transtornos do humor | placebo | suicídio / morte | OR 0,13 / 0,38 | IC largo | VERIFIED-ABS |
| TQ4-017b | lítio adicionado, veteranos com evento suicida recente | placebo | eventos relacionados a suicídio | 65 vs 62; interrompido por futilidade | — | VERIFIED-ABS (contradição com TQ4-017) |
| TQ4-018 | lítio, bipolar | placebo | episódios maníacos | redução clara; depressivos equívoca | — | PARTIAL |
| TQ4-019 | valproato na gestação | população geral | malformação / neurodesenvolvimento | ~10–11% vs 2–3% / até 30–40% | — | VERIFIED-ABS |
| TQ4-020 | 4 fármacos, TAG | placebo | HAM-A | −2,45 a −3,13 | — | VERIFIED-ABS |
| TQ4-021 | terapia comportamental, TOC | placebo (rede) | Y-BOCS | −14,48 | — | VERIFIED-ABS (com ressalva de lista de espera) |
| TQ4-022 | psicoterapias para PTSD | — | abandono | 16% (14–18) | — | VERIFIED-ABS |
| TQ4-023 | metilfenidato/anfetaminas, TDAH, curto prazo | placebo/rede | sintomas, tolerabilidade | primeira escolha por faixa etária | — | VERIFIED-ABS |
| TQ4-024 | acamprosato / naltrexona | placebo | retorno a qualquer consumo | NNT 12 / 20 | reportado | VERIFIED-ABS |
| TQ4-025 | metadona / buprenorfina (coortes) | fora do tratamento | mortalidade | 11,3 vs 36,1 / 4,3 vs 9,5 por 1 000 PA | não aplicável | VERIFIED-ABS |
| TQ4-026 | vareniclina/bupropiona (EAGLES) | placebo, adesivo | eventos neuropsiquiátricos graves | sem aumento significativo; coorte psiquiátrica DR 2,7% / 2,2% no composto | — | VERIFIED-ABS |
| TQ4-027 | CBT-I | controles | diário do sono | magnitudes | — | UNVERIFIED |

## 11. Lacunas que este lote não fecha
- taxas absolutas de resposta/remissão por molécula antidepressiva e IC (Cipriani 2018 suplementos);
- eficácia por modalidade em PTSD (PE, CPT, EMDR, TF-CBT) com IC e comparador;
- ISRS e clomipramina no TOC (valores da rede);
- números de CBT-I (Trauer 2015) e de higiene do sono;
- manutenção do lítio por polo (RR, IC);
- HR/IC de SUSTAIN-1;
- abstinência absoluta no EAGLES;
- danos com denominador para antidepressivos (disfunção sexual, hiponatremia, sangramento), benzodiazepínicos (quedas, fraturas) e estimulantes (cardiovascular, crescimento).

Essas lacunas exigem leitura do texto integral ou suplementos; ficam registradas como pendências, não como fatos.

**Integração:** nenhuma. **Treinamento:** nenhum.
