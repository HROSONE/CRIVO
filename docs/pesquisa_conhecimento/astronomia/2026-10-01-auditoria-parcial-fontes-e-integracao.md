# Auditoria pontual de fontes, estado da branch e integridade editorial

**Data:** 2026-10-01. **Tipo:** verificação amostral com fontes institucionais e artigos externos.  
**Importante:** este arquivo registra UMA AUDITORIA PARCIAL, não corresponde à primeira das duas auditorias científicas FINAIS exigidas pelo protocolo de encerramento. Não marca módulo documental pronto, não prova aprendizado neural e não altera `main`.

## 1. Estado verificado do GitHub

- Repositório: `HROSONE/CRIVO`, branch: `pesquisa/acervo-conhecimento-crivo`.
- Comparação `main...pesquisa/acervo-conhecimento-crivo` consultada: **branch 46 commits à frente e 2 commits atrás da main**, estado `diverged`. Todos os **23 arquivos listados como alterações próprias da branch** na comparação estavam sob `docs/pesquisa_conhecimento/` (README + auditoria + 21 outros documentos/protocolo, contabilizando os caminhos listados); não há modificações de código da main atribuídas a esta branch.
- Os **dois commits novos da main** incorporaram trabalho de linguagem/treinamento de outro agente (PR #45), inclusive `crivo.py`, `api/chat.py`, scripts, tokenizer e artefatos em `artefatos/linguagem_profunda/`. Não inferir que a documentação de Astronomia foi integrada por esse merge. Para futura integração, revisar diferenças atuais da main antes de operar sobre branch atrasada.
- A skill `main:docs/skill_especializacao_astronomia.md` não recebeu certificação desta branch; a auditoria editorial anterior registra 0/10. **Não foi executada prova neural, CI, treino ou merge nesta auditoria.**

## 2. Achado de qualidade editorial — CORRIGIDO

**Defeito:** na versão anterior de `docs/pesquisa_conhecimento/README.md`, onze linhas de documentos apareciam ANTES de `| Data | Área/módulos | Documento | Estado |` e da linha delimitadora Markdown, fazendo a primeira parte da tabela ser interpretada como texto irregular.

**Correção efetivamente gravada:** mover o único cabeçalho e a linha delimitadora para imediatamente depois de `## Dossiês disponíveis`. Não excluir, adicionar, renomear ou trocar nenhum caminho de documento. Commit **`d0e196f7b2f250ef821f21d8f6cabdb4b529e9e0`**. A verificação pós-escrita exige reler o README para garantir cabeçalho único e contagem de arquivos preservada.

## 3. Amostra de evidências EXTERNAS verificada diretamente

| Alegação do acervo / referência | Consulta externa | Resultado e limites |
| --- | --- | --- |
| DESI DR2 Lyα, 30/07/2026: análise full-shape com centro mais próximo das previsões ΛCDM | https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/ | **Confere.** A equipe relata tendência central em direção a ΛCDM e diz que a conclusão definitiva sobre evolução da energia escura continua em aberto. É comunicado oficial do próprio DESI, não réplica independente. |
| REBELS-25, `z=7,31`, aproximadamente 700 milhões de anos após o Big Bang; reserva gasosa de ~10^11 massas solares | https://www.almaobservatory.org/en/press-releases/alma-and-vla-reveal-a-vast-reservoir-of-star-forming-fuel-in-a-galaxy-near-cosmic-dawn/ | **Confere.** ALMA/VLA mediram emissões de CO e outros traçadores; a **massa é estimada mediante modelos**. Não é contagem direta de moléculas. |
| ESA/Hubble, 21/01/2026, estudo de estrelas `blue straggler` e binárias | https://esahubble.org/news/heic2602/ | **Confere.** Nota de 48 aglomerados e mais de 3000 blue stragglers; vínculo populacional ao ambiente e binariedade. Não demonstra origem individual de toda estrela com essas características. |
| NASA/JPL, 26/01/2026, mapa COSMOS-Web e imagem com quase 800 mil galáxias | https://www.jpl.nasa.gov/news/nasa-reveals-new-details-about-dark-matters-influence-on-universe/ e https://science.nasa.gov/photojournal/webb-data-reveals-dark-matter/ | **Confere.** Número é da imagem ampla; reconstrução de massa é inferida por efeito gravitacional. NÃO é contagem de 800 mil medidas igualmente boas de forma de fontes. |
| DES Y6 `S8≈0,789±0,012`, `Ωm≈0,333`, em `ΛCDM` | https://arxiv.org/abs/2601.14559 | **Confere** com resumo primário. A própria análise aponta diferenças estatísticas dependentes de quais dados/combinações e projeções; não transformar em refutação definitiva de ΛCDM. |
| PHANGS-ALMA: programa de 90 galáxias, entrega de cubos de dados de 74 alvos, resolução típica ~1,5 arcsec | https://almascience.nrao.edu/alma-data/lp/PHANGS/ | **Confere.** 90 é o levantamento e 74 a entrega indicada. Não significa que todos os 90 alvos tinham produtos nessa entrega. |
| DART: 11h55 para 11h23, alteração de ~32 min ±~2 min | https://science.nasa.gov/solar-system/asteroids/didymos/ | **Confere.** Mede a órbita de Dimorphos ao redor de Didymos; não variação desse par ao redor do Sol. |
| Planck VI DOI `10.1051/0004-6361/201833910e` corresponde a errata de 2021 | https://doi.org/10.1051/0004-6361/201833910e | **Confere.** Errata altera limites de profundidade óptica na reionização primordial; não é, por si só, correção do H0 citado pelo acervo. |
| Quatro recursos NASA de detecção de exoplanetas (trânsito, velocidade radial, microlente e imagem direta) | https://science.nasa.gov/resource/exoplanet-detection-transit-method/ ; https://science.nasa.gov/resource/exoplanet-detection-radial-velocity-method/ ; https://science.nasa.gov/resource/exoplanet-detection-microlensing-method/ ; https://science.nasa.gov/resource/direct-imaging/ | **URLs abrem e títulos correspondem.** São páginas de divulgação/recursos, não estudos primários nem autorização de copiar suas imagens. |
| Cronologia `238U/235U` DOI `10.1016/j.epsl.2010.10.015` | https://doi.org/10.1016/j.epsl.2010.10.015 | **Confere** o título/artigo na publicação e em repositório da Australian National University; validar precisão numérica de cada amostra requer leitura do artigo, não só resumo. |
| Hipótese de remeltimento lunar 4,35 Ga DOI `10.1038/s41586-024-08231-0` | https://doi.org/10.1038/s41586-024-08231-0 | **Confere** artigo de Nimmo/Kleine/Morbidelli (18/12/2024). É cenário proposto e modelado, não observação direta de todo o passado da Lua. |

**Escopo real desta auditoria:** conferência **amostral** de existência, data, título, números centrais e ressalvas de fontes selecionadas. NÃO houve validação exaustiva de centenas de URLs, das fórmulas linha a linha, de direitos individuais de cada figura ou de reprocessamento das bases observacionais.

## 4. Pendências e priorização da próxima auditoria

1. **Fontes:** estratificar todos os links em primário, artigo de revisão, comunicado institucional e página de recursos; verificar amostra cega de DOI e datas por dossiê, separando referências duplicadas da mesma missão.
2. **Afirmações:** cada uma das 72 fichas nominais da main tem fatos próprios cuja correspondência com publicação e incerteza precisa ser auditada individualmente. O índice de nomes é apenas navegação.
3. **Dados e matemática:** fontes publicadas de medições não equivalem a refazer o pipeline Gaia/SDSS/ALMA/Planck; requer dados abertos, scripts/versões e checagem independente se houver autorização.
4. **Modelos alternativos:** comparar teorias/dados conflitantes sem absolutizar uma parametrização, especialmente DESI 2025/2026, massa escura e cronologias do sistema planetário.
5. **Licenças:** revisar condições por obra e materiais de terceiros antes de redistribuir imagens, mapas, espectros ou artigos integrais.
6. **Navegação e sincronização:** corrigir regressões de índice e consultar SHA na hora de cada edição; comparar a branch à main antes de qualquer integração futura e nunca sobrescrever o outro agente.

**Decisão:** cobertura temática ampla e problemas de navegação sanados pontualmente, mas **não** houve prova de revisão científica integral nem duas auditorias finais consecutivas; a pesquisa documental **não** está formalmente encerrada. A rotina deve continuar auditar/ajustar, não criar dossiês de curiosidades sem lacuna estrutural. Certificação oficial e competência neural: não avaliadas por esta branch.
