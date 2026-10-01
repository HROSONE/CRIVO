# Skill de especialização: Astronomia (CRIVO)

## Definição operacional

**100% nesta skill significa concluir um currículo delimitado e passar nas provas especificadas abaixo.** Não significa conhecer todo o universo, equivaler a uma graduação reconhecida, ou responder qualquer pergunta. A cobertura editorial, o desempenho do mecanismo de consulta e a competência neural devem ser informados separadamente.

### Escada curricular: dez módulos, 10 pontos cada

| Módulo | Entregável verificável | Estado inicial (01/10/2026) |
| --- | --- | --- |
| 1. Vocabulário | Pelo menos 20 conceitos astronômicos com definição, fonte e limite | Candidato: 28 conceitos astronômicos próprios e fichas canônicas anteriores aprofundadas; CI e prova independente ainda exigidos |
| 2. Sistema solar | Sol, planetas, luas, corpos menores, órbitas, origem e distinções | Candidato: oito fichas planetárias com formação, propriedades e limites; ainda faltam testes conclusivos e luas em profundidade |
| 3. Formação planetária | Disco, agregação, planetesimais, diferenciação, migração, exemplos | Parcial |
| 4. Física estelar | Formação, fusão, espectros, equilíbrio, evolução e remanescentes | Parcial |
| 5. Galáxias | Via Láctea, tipos, meio interestelar, dinâmica, formação e observação | Parcial |
| 6. Cosmologia | Expansão, radiação cósmica, nucleossíntese, escalas e limites | Parcial |
| 7. Observação | Telescópios, espectroscopia, trânsito, paralaxe, erros e evidências | Parcial |
| 8. Matemática aplicada | Unidades, gravitação, Kepler, energia, cálculos reproduzíveis | Não demonstrado |
| 9. Explicação e raciocínio | Causas, comparações, perguntas compostas e contexto inéditos | Não demonstrado |
| 10. Prova final | Avaliação independente, respostas fundamentadas, abstenções, revisão | Não demonstrado |

### Como o percentual funciona

- **Cobertura editorial:** 10 pontos por módulo cuja lista de entregáveis e fontes esteja integralmente documentada e revisada. Conteúdo parcialmente escrito não recebe pontos integrais.
- **Competência demonstrada:** calculada separadamente com perguntas inéditas por módulo, incluindo paráfrases, relações, questões com premissas falsas e perguntas sem evidência. Registrar acertos, erros e abstenções; não converter presença de texto em capacidade de raciocinar.
- **Condição de conclusão:** 10/10 módulos editoriais aprovados **e** pelo menos 90% de acertos em avaliação independente por módulo, com nenhuma afirmação inventada em casos de controle de abstenção; compatibilidade e CI obrigatórios. Se falhar em qualquer etapa, manter a skill aberta e registrar lacunas. Esse 90% é um critério de projeto, não equivalência a diploma.
- **Progressão:** somente atualizar de 10% em 10% depois de evidência revisada. Para 20%, dois módulos precisam estar integralmente aprovados; não declarar percentuais por impressão. Um módulo pode ser dividido em entregas menores sem antecipar sua aprovação.
- **Fontes:** sínteses próprias, dados científicos verificáveis, licenças registradas; separar interpretações culturais de propriedades físicas. Não usar jw.org, LLM pré-treinado ou API externa de IA.
- **Segurança:** alterações em PR, testes de desenvolvimento e avaliação independente, regressão contra main, CI Python 3.8/3.11/3.13, sem merge automático quando checks faltarem.

### Próximo trabalho priorizado

1. Verificar CI e executar testes atuais do PR; corrigir falhas antes de ampliar.
2. Completar o módulo 1 com revisão de definições, fontes e limites do catálogo consolidado de astronomia; não contar apenas nomes.
3. Completar o módulo 2 com fichas científicas dos oito planetas, luas e propriedades físicas, diferenciando afirmações bem estabelecidas de hipóteses.
4. Avaliação retida v1 implementada e **executada**, porém com resultados insuficientes (ver `docs/avaliacao_astronomia_independente_v1.md`): investigar as causas gerais dos erros sem treinar com a prova; criar nova prova v2 após mudanças.
5. Só então prosseguir pelos módulos 3 a 10; publicar a matriz de evidências e o progresso verificável em cada PR.

**Estado auditado em 01/10/2026:** 28 conceitos do currículo `conhecimento_mundo.json` em Astronomia, incluindo os oito planetas. Sete conceitos repetidos foram consolidados em `conhecimento_expandido.json`; termos legados do sistema solar continuam na base original. Assim, a redução anterior de 31 para 20 fichas no currículo do mundo não significou perda das explicações consolidadas; oito planetas elevaram o total atual de 20 para 28. O primeiro e o segundo módulos permanecem *candidatos*, não aprovados. **Progresso certificado: 0/10 (0%) enquanto as provas e o CI completos estiverem pendentes.**

### Evidência de treinamento e próximos critérios de promoção

- Treinamento neural anterior, **antes da consolidação dos duplicados e dos oito planetas**: modelo autoral com 196 rótulos; 16/31 acertos exatos no classificador de desenvolvimento e 20/31 no motor híbrido. Esses números são históricos e **não se transferem** à nova população de conceitos.
- As novas perguntas neurais diversificam **formulações gerais**, mantêm `Defina X` fora do currículo de treino e filtram exemplos repetidos que causavam rótulos concorrentes. Esse mecanismo não substitui avaliação independente, compreensão causal nem escrita livre.
- O arquivo `testes_astronomia_sistema_solar.py` verifica existência, proveniência, formação, funcionamento e não regressão dos oito planetas. `testes_astronomia_editorial.py` verifica conteúdos iniciais e desambiguação.
- Executar a matriz Python 3.8, 3.11 e 3.13, as auditorias e a preparação do treino candidato **no commit mais recente**. Resolver qualquer falha antes de certificar 10%.
- Para completar o módulo 2, ainda acrescentar e testar principais luas, estruturas planetárias, dinâmica entre corpos, composição comparada, limites observacionais e uma prova independente. Cadastro de oito fichas, por si só, não certifica os 20%.

**Avaliação retida v1, primeira execução independente do treinamento (01/10/2026):** 58 perguntas novas (24 de vocabulário, 20 de Sistema Solar e 14 controles), executadas sem ajuste de pesos no checkpoint integrado de 193 classes. **Vocabulário 11/24 (45,8%); Sistema Solar 2/20 (10%); controles 14/14 (100% de abstenções); classificador isolado 22/29 (75,9% no subconjunto aplicável).** Falhou o critério ≥90% dos dois módulos e, portanto, **0% do currículo certificado**. Todos os enunciados e critérios ficam congelados. O avaliador é independente da rotina de treinamento, mas **não é um terceiro humano externo**; sua análise de IDs e palavras-chave necessita revisão científica/semântica. Evidências, limitações, erros exemplificados, hashes de modelo/prova e workflow: `docs/avaliacao_astronomia_independente_v1.md` e [execução 36819092257](https://github.com/HROSONE/CRIVO/actions/runs/36819092257). Não ajustar o gabarito v1 para promover percentual; corrigir princípios de interpretação e usar v2 inédita após alterações.

### Registro da entrega lunar — PR #41 (01/10/2026)

- **Módulo 2 — entregável parcial:** catálogo local `conhecimento_astronomia_luas.json` com Lua terrestre, Europa, Titã e Encélado, integrado a `ler_curriculo` em `curriculo_mundo.py`. São fichas editoriais, não prova de compreensão.
- **Fontes e limites:** referências NASA/JPL, URLs e escopo de reutilização registrados por fato; formação lunar e oceanos internos descritos com graus de incerteza. Habitabilidade não implica vida detectada.
- **Provas de desenvolvimento:** `testes_astronomia_luas.py` verifica quatro IDs, fontes, limites, formação, funcionamento e desambiguação. Corrigido erro de expectativa do teste: nome canônico é `Lua da Terra`, não `Lua`. **A execução do teste no commit atual ainda não foi verificada.**
- **Lacunas:** faltam corpos menores, dinâmica orbital comparada, relações causais e avaliação inédita independente do módulo 2; falta revisar o conjunto completo do módulo 1 e confirmar CI Python 3.8/3.11/3.13 no commit atual.
- **Métricas separadas:** cobertura editorial parcial, sem percentual editorial integral aprovado; consulta simbólica lunar **não aferida**; competência neural lunar **não aferida**. Resultados históricos da v1 não podem ser extrapolados às quatro novas luas.
- **Certificação:** 0/10 módulos, **0%**. Não promover com base apenas na integração ou em testes estruturais.
- **Próximo passo:** executar CI, corrigir regressões, criar prova v2 inédita com paráfrases, negações, entidades sintéticas e abstenções, e medir consulta simbólica e rede separadamente.

100% é o encerramento de um currículo delimitado, não uma equivalência automática a diploma universitário.
