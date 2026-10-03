# Auditoria adversarial 01 — cobertura, profundidade, atualidade, fonte→afirmação e contradições

**Data:** 2026-10-03.

**Objeto:** a base inteira (63 arquivos), incluindo os blocos deste ciclo: Aprofundamentos 22–28.

**Postura:** procurar ativamente o que faria um examinador doutoral reprovar a base. "Parece boa" não é critério.

## 1. Critérios usados

| Eixo | Pergunta adversarial | Teste aplicado |
| --- | --- | --- |
| Cobertura | Há domínio clinicamente central sem tratamento quantitativo? | Busca por termos-chave em todos os arquivos, seguida de leitura das seções encontradas |
| Profundidade | O domínio tem números com denominador, IC e limite, ou só frases gerais? | Leitura das seções e contagem de claims ancorados |
| Atualidade | Diretrizes, regulação e códigos têm versão/data? Há algo superado? | Aprofundamentos 24–25 e verificação de datas |
| Fonte→afirmação | Cada claim crítico tem fonte específica? | Script mais revisão (Aprofundamentos 26–28) |
| Contradições | Contradições conhecidas da literatura estão registradas com os dois lados? | Lista C-* |
| Contexto de uso | A base cobre o contexto de quem vai usá-la (português, Brasil)? | Busca por Brasil, SUS, CAPS, RAPS, CVV |

## 2. Achados

### 2.1 Déficits **materiais** (impedem marcar a base como concluída)

| ID | Déficit | Evidência da auditoria | Por que é material |
| --- | --- | --- | --- |
| AD-01 | **Suicídio e autolesão sem tratamento quantitativo** | A base tem só parágrafos gerais (`epidemiologia-prevencao...` §14; `etica...` §18–19). Zero ocorrências de plano de segurança, contatos de cuidado, C-SSRS, InterSePT, meta-análises de predição (Franklin 2017), risco pós-alta, restrição de meios com números ou diretrizes de mídia | Desfecho mais grave da área. A ausência de magnitudes deixa sem base as decisões mais sensíveis |
| AD-02 | **Contexto brasileiro quase ausente** | "Brasil" aparece em 2 arquivos (um de validação de instrumento, um de adoção da ICD-11). CAPS/RAPS/SUS: ~0. Nada sobre a Lei 10.216/2001, epidemiologia brasileira (São Paulo Megacity), tendência de suicídio no Brasil ou CVV 188 com dados | A base está em português e se destina a esse contexto. Prevalências e serviços estrangeiros não substituem os locais |
| AD-03 | **Violência, transtorno mental e contexto forense ausentes** | Zero arquivos com tratamento de violência ↔ transtorno mental, vitimização ou risco | É um tema de estigma central. Sem números (por exemplo, o papel do uso de substâncias), a base fica vulnerável ao estereótipo "doente mental = perigoso" |
| AD-04 | **Populações especiais incompletas além de pediatria/DI** | LGBTQ+/estresse de minoria: 1 menção. Refugiados/migrantes: 4 menções sem números. Idosos: menções difusas sem bloco quantitativo próprio (depressão tardia, benzodiazepínicos e quedas, antipsicóticos em demência já parcialmente em TQ4) | O pedido original listava populações especiais como prioridade |
| AD-05 | **Frases narrativas dos dossiês de 2026-10-02 sem âncora** | 40 de 57 dossiês sem PMID/DOI/URL no corpo; listas de fontes institucionais sem versão | Os ledgers estão ancorados (93%), mas o texto corrido pode conter claims não rastreáveis. Mitigação parcial: a regra de que **o ledger prevalece** já está declarada. A conversão total continua pendente (RR-P3) |

### 2.2 Déficits **não materiais ou estruturais** (registrados, não bloqueiam isoladamente)

| ID | Item | Situação |
| --- | --- | --- |
| AD-06 | Verificação só pelo resumo (VERIFIED-ABS) | Limitação **estrutural** desta sessão: proxy 403 para PubMed/PMC/WHO/NICE. Está declarada em todos os blocos. Não é corrigível sem acesso; não se finge leitura integral |
| AD-07 | Pendências listadas nos blocos (RL-P1…P6, IB-P1…P7, pendências de TQ4/PED/DI, RR-P2, 6 claims S2-provisórios) | Todas explícitas, nenhuma preenchida de memória. Ficam como agenda |
| AD-08 | Notas de versão ICD-11 release a release | Depende de icd.who.int (bloqueado); a inferência de estabilidade está declarada |

### 2.3 Pontos que **passaram** na auditoria

- **Tratamentos quantitativos:** lotes 1–4 com efeito absoluto, IC, NNT/NNH e limites; dezenas de claims VERIFIED-ABS.
- **ICD-11:** arquitetura (partes 1–2) mais matriz código/release com contradições.
- **Integridade da evidência:** 17 casos com números.
- **Ledgers:** 93% dos claims empíricos ancorados.
- **Contradições:** 15+ registradas com os dois lados: C-PED-1, C-DI-1, C-ICD-1…3, C-INT-1…2, C-RT-1…5 e a contradição do lítio (Katz 2022) no TQ4.

## 3. Plano de correção (próximos blocos)

1. **AD-01 → Bloco "Suicídio e autolesão quantitativo":**
   - epidemiologia: WHO e Brasil;
   - predição: Franklin 2017, VPP;
   - risco pós-alta;
   - intervenções com efeito: plano de segurança, contatos breves, lítio, clozapina, cetamina, TCC/DBT para autolesão;
   - restrição de meios (paracetamol, pesticidas, armas de fogo);
   - mídia (Werther/Papageno);
   - instrumentos (C-SSRS, PHQ-9 item 9).
2. **AD-02 → Bloco "Brasil":**
   - Lei 10.216/2001, RAPS/CAPS;
   - São Paulo Megacity, PNS;
   - suicídio no Brasil;
   - CVV 188 e SAMU 192;
   - validações brasileiras de instrumentos.
3. **AD-03 + AD-04 → Bloco "Violência e populações especiais II":**
   - violência e vitimização: Fazel, Desmarais;
   - LGBTQ+ e estresse de minoria;
   - refugiados: Blackmore 2020;
   - idosos: depressão tardia, quedas e benzodiazepínicos, delirium.
4. **AD-05:** conversão progressiva das frases narrativas críticas em linhas de ledger. Prioridade: dossiês de humor, psicose, substâncias e trauma.
5. Nova auditoria adversarial (02) após os blocos 1–3.

**Resultado da auditoria 01:** a base **NÃO** está concluída. 5 déficits materiais.
