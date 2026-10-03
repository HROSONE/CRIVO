# Rastreabilidade das frases narrativas dos dossiês de 2026-10-02 (AD-05)

**Checagem:** 2026-10-03. **Origem:** déficit material AD-05 da auditoria adversarial 01. Complementa a rastreabilidade dos ledgers (Aprofundamentos 26–28).

## 1. Método

1. **Extração** por script de todas as frases dos 45 dossiês narrativos (ledgers, auditorias e protocolo excluídos) que contêm verbos de afirmação empírica: *eficaz, reduz, aumenta, associa, risco, superior, recomenda, evidência, melhora, previne, demonstra*.
2. **Filtro:** foram excluídas as frases que são explicitamente **regras de bloqueio** ("não demonstra", "≠", "nunca", "proibido").
3. **Mapeamento temático:** cada frase foi comparada, por expressões regulares, com ~50 tópicos que já têm âncora verificada na base (TQ1–4, B-01…66, SU, BR, VI/LG/RF/ID, IB).
4. **Revisão manual** de todas as frases sem tópico correspondente.

| Medida | n |
| --- | --- |
| Frases candidatas a afirmação empírica | 455 |
| Com tópico já ancorado na base | 174 (38%) |
| Sem tópico ancorado, revisadas manualmente | 281 |
| Destas, regras metodológicas, definições, princípios éticos ou recomendações de conduta sem magnitude empírica | ~266 (CONCEPTUAL) |
| Destas, **afirmações empíricas substantivas sem âncora** | **15** |

**Limite do método:**
- correspondência temática ≠ verificação frase a frase. Uma frase "sobre lítio" fica coberta pelas âncoras de lítio quanto ao **tema**, mas pode afirmar algo que a âncora não sustenta;
- por isso continua valendo a regra declarada desde o Aprofundamento 26: **o ledger e as âncoras prevalecem sobre o texto corrido**. O texto narrativo é explicação, não fonte.

## 2. Âncoras das 15 afirmações empíricas encontradas

| ID | Dossiê / afirmação narrativa | Fonte específica verificada | Número-chave | O que **não** permite concluir | Status |
| --- | --- | --- | --- | --- | --- |
| NA-01 | psicose: "uso pesado de cannabis está associado a risco aumentado" | Di Forti et al. 2019, *Lancet Psychiatry* (EU-GEI, caso-controle; 901 primeiros episódios, 1.237 controles, 11 sítios) | Uso diário vs nunca: OR 3,2. Uso diário de alta potência: OR ~4,8 (~5×). Variação por cidade: ~4× Paris, ~5× Londres, >9× Amsterdã. **12,2%** dos primeiros episódios seriam evitáveis sem cannabis de alta potência (FAP europeia) | Caso-controle: causalidade reversa e confundimento possíveis. A FAP **assume** causalidade. Os valores de FAP por cidade (~30% Londres, ~50% Amsterdã) **não foram conferidos** | VERIFIED-ABS (OR 3,2 e 12,2%); PARTIAL (4,8 e FAP por cidade) |
| NA-02 | ética: "pessoas com doença mental têm risco de condições físicas e mortalidade prematura" | Walker, McGee & Druss 2015, *JAMA Psychiatry* (203 artigos, 29 países) | Mortalidade RR 2,22 (148 estudos); mediana de 10 anos de vida potencial perdidos; ~14,3% das mortes mundiais (~8 milhões por ano) atribuídas a transtornos mentais; 67,3% das mortes por causas **naturais** | A atribuição de 8 milhões assume causalidade. A maioria das mortes é por doença física, o que aponta para **acesso a cuidado físico, tabagismo e efeitos metabólicos**, e não só para suicídio | VERIFIED-ABS |
| NA-03 | ética: "intervenções para mudar orientação sexual... associadas a danos" | Blosnich et al. 2020, *Am J Public Health* (Generations, 1.518 adultos de minorias sexuais, amostra nacional dos EUA) | Exposição a SOCE: ~2× chance de ideação suicida ao longo da vida; +75% de plano; +88% de tentativa com lesão leve; +67% de tentativa com lesão moderada/grave, **ajustado por experiências adversas na infância** | **Contradição C-NA-1:** reanálise de Sullins 2022 argumenta que a suicidalidade **prévia** à SOCE explicaria a associação (causalidade reversa). Os autores originais contestaram. Desenho transversal retrospectivo; a direção causal não está demonstrada por nenhum dos lados. A **falta de evidência de eficácia** das SOCE e a oposição de entidades profissionais são outro eixo (não conferido aqui) | VERIFIED-ABS; associação CONTESTED quanto à causalidade |
| NA-04 | prevenção/determinantes: "baixa renda pode aumentar risco de transtorno" | Ridley, Rao, Schilbach & Patel 2020, *Science* (PMID 33303583; revisão) | Relação **bidirecional**: choques econômicos negativos causam depressão/ansiedade; transferências de renda e programas antipobreza reduzem esses sintomas em **ECR**. Exemplo: o experimento de seguro do Oregon reduziu depressão em ~25% em poucos meses | Revisão narrativa interdisciplinar, não meta-análise. Magnitudes por programa variam. Mostra causalidade **em média** em contextos estudados, não em cada indivíduo | VERIFIED-ABS (S3 → **S4** para a direção causal "pobreza → depressão/ansiedade") |
| NA-05 | expansão clínica (FND): "fisioterapia melhora sintomas motores" | Physio4FMD, *Lancet Neurol* jul. 2024 (ECR pragmático fase 3; 355 adultos; Inglaterra e Escócia) | Fisioterapia especializada **não superior** ao tratamento usual no desfecho primário (SF-36 função física em 12 meses). Vários desfechos secundários favoreceram a intervenção. Alta probabilidade de custo-efetividade | **Contradição C-NA-2:** a frase narrativa (baseada em estudos menores/de viabilidade) é **mais otimista** que o maior ECR. Leitura correta: "a fisioterapia especializada pode ajudar em desfechos secundários; não demonstrou superioridade no desfecho primário vs cuidado usual (que também incluía fisioterapia comunitária)" | VERIFIED-ABS; a frase narrativa fica **SUPERSEDED/CONTESTED** |
| NA-06 | psicopatologia: depressão "pode coexistir/predizer neurodegeneração" | Livingston et al. 2024, Comissão *Lancet* | 14 fatores modificáveis, depressão entre eles, respondem por ~**45%** dos casos de demência (FAP combinada) | A FAP da depressão isolada (~3%) **não foi conferida**. A FAP assume causalidade. Depressão pode ser **pródromo** (causalidade reversa), algo que a Comissão reconhece como incerteza | VERIFIED-ABS (45% e inclusão da depressão); PARTIAL (FAP específica) |
| NA-07 | psicofarmacologia: bupropiona "pode reduzir limiar convulsivo" | Bula (Wellbutrin; monografias canadenses) | Liberação imediata 300–450 mg/dia: ~0,4% (13/3.200). Liberação prolongada 100–300 mg/dia: ~0,1%; 400 mg/dia: 0,4%. Risco ~10× maior entre 450 e 600 mg/dia | Dados antigos de vigilância. O risco individual depende de fatores predisponentes (convulsão prévia, TCE, transtornos alimentares) | VERIFIED-ABS (texto de bula via espelhos) |
| NA-08 | substâncias: manejo de contingência "forte evidência para alguns SUDs" | B-13 (Bolívar 2021) | ver B-13 | ver B-13 (escopo: pacientes em tratamento para TUO) | PARTIAL (referência cruzada) |
| NA-09 | tratamentos-01: "mortalidade pode aumentar após saída [do tratamento com agonista]" | Sordo 2017 (TQ4) | ver TQ4 | ver TQ4 | VERIFIED-ABS (referência cruzada) |
| NA-10 | humor: "NICE não recomenda lamotrigina para mania" | NICE CG185 (atualização de 2 set 2025, citada no dossiê) | — | — | referência cruzada (PF-045) |
| NA-11 | psicofarmacologia: "riscos da clozapina: neutropenia, miocardite, convulsões, hipomotilidade..." | Myles 2018 (TQ4); B-07 (FDA 2025) | ver TQ4 | Miocardite, convulsões e hipomotilidade **sem número** na base | PARTIAL |
| NA-12 | prevenção/determinantes: "intervenção pequena em população ampla pode prevenir mais casos" (paradoxo de Rose) | Rose 1985/1992 (princípio epidemiológico) | — | Princípio, não magnitude | CONCEPTUAL (reclassificado) |
| NA-13 | neuroendócrino: "puberdade precoce associada a desenvolvimento cerebral acelerado e mais problemas; brain age não mediou" | Já com números e fonte em `matriz-bibliografica-neurociencia-01` (β = 0,10; ~2,22 meses) | — | — | já ancorado no próprio acervo |
| NA-14 | tratamentos-01: "revisão 2025: 32 estudos, 5.231 participantes" (CBT-I em rotina) | Citado no lote 1; confirmado como existente no TQ4 §9 | — | Fonte específica não reconferida nesta sessão | PARTIAL |
| NA-15 | ética: "IA pode apoiar triagem..., riscos incluem alucinação, viés de automação..." | Literatura de IA em saúde | — | Afirmação de risco qualitativa; sem magnitude | CONCEPTUAL |

## 3. Efeito sobre o déficit AD-05

| Medida | Antes | Depois |
| --- | --- | --- |
| Frases empíricas substantivas sem âncora identificadas | desconhecido | 15, das quais 11 ancoradas ou com referência cruzada e 4 reclassificadas (CONCEPTUAL ou já ancoradas) |
| Frases narrativas contrariadas por evidência mais forte | desconhecido | **2** (C-NA-2 fisioterapia na FND; C-NA-1 parcialmente) |
| Regra de prevalência (ledger/âncora > texto) | declarada | mantida e agora com cobertura temática medida |

**Conclusão:** AD-05 deixa de ser déficit **material**. A conversão de todo o texto em linhas de ledger não é necessária para o uso pretendido, porque o texto narrativo é explicação, e as afirmações empíricas que ele carrega foram identificadas e ancoradas. A frase da fisioterapia na FND fica marcada como superada pelo Physio4FMD.

## Apêndice — extração e mapeamento temático (reprodutível)

```python
import re,glob,json,collections
kw=re.compile(r'\b(eficaz|eficácia|reduz|aumenta|associa|risco|superior|primeira linha|recomend|evidência|melhora|previne|demonstr)',re.I)
neg=re.compile(r'não (demonstra|prova|implica|permite|significa|equivale|deve|substitui|garante|autoriza|transforma)|≠|nunca|proib|não é ',re.I)
topics=[
 (r'lítio|lithium','TQ4-lítio; B-21; SU-015'),(r'clozapin','B-06; SU-013; TQ4; B-07'),(r'\bECT\b|eletroconvuls','B-24; B-25; B-26; TQ4'),
 (r'\bTMS\b|rTMS|theta','B-27; TQ4'),(r'exposi|exposure|extin','B-38; B-48; B-49'),(r'\bERP\b|\bTOC\b|OCD','B-52; TQ4'),
 (r'\bDBT\b','B-03; SU-012'),(r'EMDR','B-04'),(r'CBT-I|insôni|insomnia','B-11; TQ4-027'),(r'ativação comportamental|behavioral activation|\bBA\b','B-51'),
 (r'\bIPT\b|interpessoal','B-40'),(r'alian','B-01'),(r'antidepress','B-20; TQ4; ID-001; IB-001; IB-015'),(r'antipsic','B-63; B-29; TQ4; ID-004'),
 (r'famíl|family','B-55; B-12'),(r'psicose|psychosis|esquizofren|schizophren','B-37; B-08; B-63; VI-001; VI-002'),(r'precoce|early intervention','B-08'),
 (r'emprego|IPS|employment','B-09'),(r'exercí|exercise','B-10'),(r'contingên|contingency','B-13'),(r'metadona|buprenorf|agonist|opioid|naloxon','B-22; TQ4'),
 (r'\bC4\b|complement|micróglia|microglia|poda|pruning','B-14; B-41'),(r'inflama|\bCRP\b|\bPCR\b|IL-6','B-15'),(r'APOE','B-16'),(r'amiloid|amyloid|tau','B-17; B-18; B-33; B-66'),
 (r'cortisol|HPA|dexametas','B-43; B-44'),(r'BDNF','B-50'),(r'neurogên|neurogenes','B-19'),(r'dopamin','B-46; B-47'),(r'suic','SU-*'),
 (r'serotonin','IB-010'),(r'5-HTTLPR|gene candidato|candidate gene','IB-009'),(r'retirada|descontinua|withdrawal','IB-015'),(r'cetamin|esketamin|ketamin','IB-004; SU-014; TQ4'),
 (r'estimulante|metilfenid|stimulant|TDAH|ADHD','TQ4; PED; B-32; B-46'),(r'valpro','TQ4'),(r'autis','PED; NB-032 (S2)'),(r'demênc|dementia|delirium','ID-003; ID-004; B-17; B-18'),
 (r'benzodiaz','ID-002; TQ4'),(r'TEPT|PTSD|trauma','B-04; TQ4; RF-001'),(r'borderline|TPB|personalidade','B-03; B-65; B-53'),(r'anorex|bulim|alimentar|eating','B-12; B-60'),
 (r'álcool|alcohol','TQ4 (Jonas 2014)'),(r'tabag|smok|vareniclin','TQ4 (EAGLES); B-34'),(r'gravid|perinatal|pós-parto|postpartum','dossiê perinatal (Aprof. 21)'),
 (r'psicoterap|psychotherap|\bTCC\b|\bCBT\b','B-38; B-39; B-56; B-57; B-58; B-59; IB-006; TQ4 (Cuijpers 2021)'),(r'placebo','IB-001; B-05; TQ4'),
 (r'preval|epidemiolog|incidên','BR-001; BR-002; B-30; B-31; SU-001'),(r'estigma|stigma|violên|violen','VI-001…004; LG-001…003'),(r'idos|older|geriát','ID-001…005'),
 (r'neuroimag|fMRI|ressonân|MRI|conectividade|connectivity','B-42; NB-015…020 (CONCEPTUAL)'),(r'genét|genetic|herdab|heritab|poligên|polygenic','IB-009; B-14; NB-048…050 (CONCEPTUAL)'),
]
# para cada dossiê 2026-10-02 (exceto ledger/auditoria/protocolo): frases com kw e sem neg;
# frase 'coberta' se casar com algum padrão de topics; demais vão para revisão manual.
```

**Integração:** nenhuma. **Treinamento:** nenhum.
