# Intervenções digitais e agentes conversacionais; adversidade na infância; saúde mental global (quantitativo)

**Checagem:** 2026-10-03. **Origem:** déficits materiais AD2-01 e AD2-02 da auditoria adversarial 02.

O tema digital é **diretamente relevante ao contexto de uso** da base (assistente conversacional), mas só tinha regras qualitativas: `etica...` §52–55 e `tratamentos-...-02` §12.

**Rótulos:** VERIFIED-ABS, PARTIAL, UNVERIFIED.

## Parte A — Intervenções digitais e agentes conversacionais

| ID | Afirmação | Fonte | Desenho | Número-chave | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- | --- | --- |
| DG-001 | TCC pela internet (iCBT) para depressão: análise de dados individuais com formatos guiado e autoguiado | Karyotaki et al. 2021, *JAMA Psychiatry* 78:361–371 | NMA com dados individuais | Formatos guiado e autoguiado vs controles; **números de resposta não conferidos** | PARTIAL (existência e desenho) | — (pendência DG-P1) |
| DG-002 | Agentes conversacionais baseados em IA: depressão **g = 0,64** (0,17–1,12); sofrimento psicológico **g = 0,70** (0,18–1,22); bem-estar g = 0,32 (−0,13 a 0,78), **não significativo**. 35 estudos, 15 ECR meta-analisados. Efeitos maiores em agentes multimodais, generativos, integrados a apps de mensagem e em populações clínicas/subclínicas | Li et al. 2023, *npj Digit Med* | Revisão sistemática e meta-análise | ver ao lado | VERIFIED-ABS | IC muito largos (o limite inferior para depressão é g = 0,17). Poucos ECR, comparadores fracos (lista de espera, informação), seguimento curto. **Viés de publicação e alegiância** prováveis (B-58, IB-006). Não estabelece segurança |
| DG-003 | Woebot: 70 universitários de 18–28 anos, 2 semanas, vs e-book informativo do NIMH. PHQ-9 caiu de 14,3 para 11,1 no grupo Woebot | Fitzpatrick et al. 2017, *JMIR Ment Health* (PMC5478797) | ECR pequeno | ver ao lado | VERIFIED-ABS | n = 70, 2 semanas, controle informativo, sem seguimento. A redução intragrupo de ~3 pontos é parcialmente regressão à média |
| DG-004 | Therabot (IA generativa): 210 adultos (depressão, TAG, alto risco de transtorno alimentar), recrutados pela Meta, vs **lista de espera**. Reduções significativas em 4 e 8 semanas; depressão com ~51% de redução média | Heinz et al. 2025, *NEJM AI* | ECR | ver ao lado | VERIFIED-ABS | Comparador lista de espera (contraste inflado, B-05). Grupo desenvolvedor. 8 semanas. Supervisão humana de respostas durante o ensaio (PARTIAL), ou seja, não testa uso autônomo. **Não** demonstra equivalência a terapeuta humano |

### Incidentes de dano documentados (não são estudos de efeito; são sinais de segurança)

| ID | Incidente | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| DG-005 | **Tessa (NEDA, 2023):** chatbot de uma organização de transtornos alimentares tirado do ar após recomendar perda de peso, contagem de calorias e medida de gordura a usuárias com transtorno alimentar | Imprensa (Fortune, CNN, Psychiatrist.com), AI Incident Database | VERIFIED-ABS (fato do incidente) | Frequência do dano desconhecida. A organização atribuiu parte do problema a "maus atores". Ilustra o risco de **conselho genérico de saúde aplicado à população errada** |
| DG-006 | **Character.AI (2024):** ação judicial nos EUA após o suicídio de um adolescente de 14 anos que mantinha interação intensa com um chatbot de personagem | Imprensa (Bloomberg Law, Global News), AI Incident Database | VERIFIED-ABS (existência da ação) | **Causalidade não estabelecida**: é alegação judicial. Mostra risco de vínculo intenso, uso por menores e ausência de protocolo de crise |
| DG-007 | Relatos de dano associados a chatbots generativos: análise de 71 reportagens com 36 casos de crise (suicídio, internação, experiências do tipo psicótico) e outra série de 185 relatos reais; chatbots podem **validar ou elaborar crenças delirantes** e responder de forma inadequada à ideação suicida | Preprints e relatórios de 2025–2026 (JMIR Ment Health preprint 93040; arXiv 2609.08027; OECD AI incidents) | PARTIAL (preprints; não revisados por pares quando conferido) | Série de casos da mídia: viés de seleção extremo (só casos graves viram notícia). **Não** estima incidência. Serve como catálogo de **modos de falha** |

**Síntese da parte A (para a base; integração não autorizada):**
1. Há eficácia **média moderada e imprecisa** de agentes conversacionais sobre sintomas (DG-002), com evidência de baixa qualidade: comparadores fracos, curto prazo, alegiância.
2. O **perfil de dano** é documentado por incidentes (DG-005–007), não por estudos de incidência. Os modos de falha recorrentes são:
   - conselho inadequado à população;
   - validação de crenças delirantes;
   - resposta inadequada a risco;
   - vínculo e dependência;
   - uso por menores.
3. Isso reforça regras já existentes na base (`etica...` §52–55):
   - engajamento ≠ eficácia;
   - protocolo de crise obrigatório;
   - transparência sobre a natureza do sistema;
   - nada de simular terapeuta.

   Coerente com o protocolo de crise do CRIVO (PR #61, fora desta branch), sem integrar nada aqui.

## Parte B — Adversidade na infância

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| AC-001 | ≥4 experiências adversas na infância (ACE) vs nenhuma: 37 estudos, 253.719 participantes, 23 desfechos. Associações mais fortes com **uso problemático de drogas (OR ~10,2)** e com **violência interpessoal e autodirigida** (OR >7). Tentativa de suicídio OR ~37,5; problemas de saúde mental (depressão) OR ~4,4 | Hughes et al. 2017, *Lancet Public Health* | VERIFIED-ABS (desenho, n e "OR >7"); PARTIAL (4,4, 10,2 e 37,5 vêm de fontes secundárias) | Contagem de ACE é **escore grosseiro**: soma eventos heterogêneos com o mesmo peso. Dados retrospectivos. Associação **não** prevê o indivíduo: a maioria das pessoas com ACE alto não desenvolve esses desfechos. Não serve para triagem individual determinística |
| AC-002 | Medidas **objetivas** (registros judiciais) e **subjetivas** (relato adulto) de maus-tratos identificam grupos diferentes. O risco de psicopatologia associado só à medida objetiva, **sem** relato subjetivo, foi mínimo; o associado ao relato subjetivo foi alto, quer ou não concordasse com o registro | Danese & Widom 2020, *Nat Hum Behav* | VERIFIED-ABS | **Não** significa que maus-tratos "não importam" ou que relatos sejam "inventados". Sugere que a **experiência subjetiva e a memória** do evento fazem parte da via de risco, e que estudos retrospectivos e prospectivos medem construtos diferentes. O kappa de concordância (~0,19, de memória) é UNVERIFIED |

## Parte C — Saúde mental global: compartilhamento de tarefas

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| GL-001 | **Friendship Bench (Zimbábue):** terapia de resolução de problemas aplicada por trabalhadoras leigas ("avós"), 6 sessões. Em 6 meses, sintomas depressivos em **~14% vs ~50%** (cuidado usual reforçado); ansiedade ~4× menos; ideação suicida ~5× menos | Chibanda et al. 2016, *JAMA* (ECR por conglomerados) | VERIFIED-ABS | Desfecho por ponto de corte de questionário (SSQ-14), não por diagnóstico. Controle de cuidado usual reforçado, com contato menor. Replicações em outros contextos estão em andamento (não conferidas) |
| GL-002 | **Compartilhamento de tarefas** em países de baixa e média renda (meta-análise de dados individuais): intervenções psicológicas por não especialistas aumentam a **resposta** (OR 2,11; 1,60–2,80) e a remissão (OR ~1,87, PARTIAL: o IC citado é inconsistente) | Karyotaki et al. 2022, *JAMA Psychiatry* (PMC8943620) | VERIFIED-ABS (resposta) | Heterogeneidade entre programas. Comparadores de cuidado usual fraco. Transferência ao SUS plausível (agentes comunitários de saúde), mas **não testada** aqui |
| GL-003 | Healthy Activity Program (Índia): ativação comportamental breve por conselheiros leigos para depressão moderada a grave na atenção primária. Eficaz e custo-efetiva | Patel et al. 2017, *Lancet* (PREMIUM) | VERIFIED-ABS (conclusão); percentuais de remissão UNVERIFIED | Um país, atenção primária. Os percentuais (lembrados como ~64% vs ~46%) não foram confirmados |

**Implicação para o Brasil** (ligação com BR-001/002): a lacuna de tratamento documentada (um terço dos casos graves tratados) e a existência de agentes comunitários de saúde tornam GL-001–003 **relevantes como hipótese de política**, não como evidência local.

## Pendências

- **DG-P1:** taxas de resposta guiada vs autoguiada em Karyotaki 2021; risco de deterioração com iCBT autoguiada.
- **DG-P2:** diretrizes regulatórias para apps e IA em saúde mental (FDA, MHRA, ANVISA, Lei 14.510/2022 de telessaúde no Brasil).
- **DG-P3:** estudos revisados por pares sobre bajulação (*sycophancy*) de LLMs e resposta a risco suicida (por exemplo, avaliações de respostas a cenários de ideação).
- **AC-P1:** OR exatos de Hughes 2017; dados brasileiros de ACE (coortes de Pelotas).
- **GL-P1:** replicações do Friendship Bench (por exemplo, Malawi, EUA) e iniciativas brasileiras.

**Integração:** nenhuma. **Treinamento:** nenhum.
