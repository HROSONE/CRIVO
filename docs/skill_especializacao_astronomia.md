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
2. Completar o módulo 1 com revisão de definições, fontes e limites de todos os 31 conceitos; não contar apenas nomes.
3. Completar o módulo 2 com fichas científicas dos oito planetas, luas e propriedades físicas, diferenciando afirmações bem estabelecidas de hipóteses.
4. Implementar avaliações independentes com enunciados novos e relatório automático que distingue **cobertura**, **respostas corretas**, **erros** e **abstenções**.
5. Só então prosseguir pelos módulos 3 a 10; publicar a matriz de evidências e o progresso verificável em cada PR.

**Estado auditado em 01/10/2026:** 28 conceitos do currículo `conhecimento_mundo.json` em Astronomia, incluindo os oito planetas. Sete conceitos repetidos foram consolidados em `conhecimento_expandido.json`; termos legados do sistema solar continuam na base original. Assim, a redução anterior de 31 para 20 fichas no currículo do mundo não significou perda das explicações consolidadas; oito planetas elevaram o total atual de 20 para 28. O primeiro e o segundo módulos permanecem *candidatos*, não aprovados. **Progresso certificado: 0/10 (0%) enquanto as provas e o CI completos estiverem pendentes.**

### Evidência de treinamento e próximos critérios de promoção

- Treinamento neural anterior, **antes da consolidação dos duplicados e dos oito planetas**: modelo autoral com 196 rótulos; 16/31 acertos exatos no classificador de desenvolvimento e 20/31 no motor híbrido. Esses números são históricos e **não se transferem** à nova população de conceitos.
- As novas perguntas neurais diversificam **formulações gerais**, mantêm `Defina X` fora do currículo de treino e filtram exemplos repetidos que causavam rótulos concorrentes. Esse mecanismo não substitui avaliação independente, compreensão causal nem escrita livre.
- O arquivo `testes_astronomia_sistema_solar.py` verifica existência, proveniência, formação, funcionamento e não regressão dos oito planetas. `testes_astronomia_editorial.py` verifica conteúdos iniciais e desambiguação.
- Executar a matriz Python 3.8, 3.11 e 3.13, as auditorias e a preparação do treino candidato **no commit mais recente**. Resolver qualquer falha antes de certificar 10%.
- Para completar o módulo 2, ainda acrescentar e testar principais luas, estruturas planetárias, dinâmica entre corpos, composição comparada, limites observacionais e uma prova independente. Cadastro de oito fichas, por si só, não certifica os 20%.

**Estado de avaliação independente:** ainda não medido nesta versão. 100% é o encerramento de um currículo delimitado, não uma equivalência automática a diploma universitário.
