# Correções de rastreabilidade científica e verificação de aplicação — 01/10/2026

**Status:** 27 intervenções de citação preparadas e verificadas por aplicação SIMULADA na base lida da `main`; **nenhuma mudança feita na `main`**.  
**Responsabilidade:** pesquisador prepara fontes e propostas nesta branch; integrador aplica, testa e certifica capacidades em outro fluxo.

## 1. Correção do próprio diagnóstico anterior

A primeira auditoria reportara **27 fontes insuficientes**. A inspeção direta de https://science.nasa.gov/universe/glossary/ mostrou que a página **tem um verbete `Lagrange points`** e cita missões operando perto de L1/L2. Portanto, em dois fatos da main (definição geral e emprego por missões) a referência ORIGINAL dá suporte conceitual; a marcação de erro foi um falso positivo. A terceira frase, sobre **estabilidade de alguns pontos versus manutenção de órbitas**, precisa da fonte detalhada https://science.nasa.gov/solar-system/resources/faq/what-are-lagrange-points/ .

**Situação CORRIGIDA da auditoria 1:** **25 fontes insuficientes**, **22 afirmações com suporte conceitual parcialmente comparado** (incluindo as duas Lagrange) e **232 ainda sem comparação semântica frase a frase**; soma 279. Não é aprovação das 22 frases completas. O relatório original foi revisado, assim como a auditoria 2 e o controle geral.

## 2. O pacote exato, sem alterar textos dos fatos

**[Proposta estruturada de substituição de fontes (JSON)](2026-10-01-proposta-correcoes-fontes-27-afirmacoes.json)**

O arquivo contém 27 instruções por **ID da ficha + índice do fato (zero-based) + texto esperado + código de fonte antigo + novo**, e 15 registros de referência adicionais. As instruções distinguem **25 correções essenciais** de **dois aprimoramentos opcionais** da referência dos fatos Lagrange já parcialmente apoiados.

| Termos da main | Afirmações propostas | Evidências mais específicas e limitações |
| --- | ---: | --- |
| Velocidade de escape | 3 correções | [Hubble Glossary](https://science.nasa.gov/mission/hubble/multimedia/hubble-glossary/) (definição); [NASA GSFC](https://cosmicopia.gsfc.nasa.gov/qa_gp_gr.html) (dependência massa/raio); [NASA Glenn](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/four-rocket-forces/) e [NASA GSFC](https://pwg.gsfc.nasa.gov/stargaze/StarFAQ3.htm) (arrasto/empuxo). Não chamar fórmula balística de trajetória com motor/atmosfera. |
| Ponto de Lagrange | 1 correção e 2 aprimoramentos | [Glossário NASA já menciona Lagrange](https://science.nasa.gov/universe/glossary/); [NASA FAQ](https://science.nasa.gov/solar-system/resources/faq/what-are-lagrange-points/) especifica regiões e necessidade de manutenção em L1–L3. Não atribuir à página genérica uma explicação da estabilidade que ela não desenvolve. |
| Limite de Roche | 3 correções | [NASA Cassini FAQ](https://science.nasa.gov/mission/cassini/faq/) (maré e ruptura), [NASA NTRS](https://ntrs.nasa.gov/citations/19740055720) (materiais/elasticidade) e [Nature](https://www.nature.com/articles/047509b0) (dependência de densidades). O texto com densidade E estrutura precisa de evidências combinadas. |
| Esfera de Hill | 3 correções | [NASA Lucy](https://www.nasa.gov/missions/hide-and-seek-how-nasas-lucy-mission-team-discovered-eurybates-satellite/) (conceito e busca de satélites), [Domingos et al., MNRAS 2006](https://doi.org/10.1111/j.1365-2966.2006.11104.x) (limites de estabilidade orbitais sob condições). A esfera não é garantia de estabilidade. |
| Ressonância orbital | 3 correções | [NASA Europa](https://science.nasa.gov/jupiter/jupiter-moons/europa/europa-facts/) (exemplo Io–Europa–Ganimedes), [MNRAS 2023](https://academic.oup.com/mnras/article/522/2/1914/7081365) (comensurabilidade versus libração). Não basta encontrar uma razão próxima de inteiros. |
| Trânsito planetário | 3 correções | [NASA métodos de exoplanetas](https://science.nasa.gov/exoplanets/how-we-find-and-characterize/) e [NASA trânsito](https://science.nasa.gov/exoplanets/whats-a-transit/) (queda de brilho, periodicidade e geometria). |
| Velocidade radial | 3 correções | [NASA métodos](https://science.nasa.gov/exoplanets/how-we-find-and-characterize/) e [catálogo hospedado na NASA/HEASARC](https://heasarc.gsfc.nasa.gov/W3Browse/catalog/exoplanets.html) para a ressalva `M sin(i)`. Hospedagem na NASA não implica autoria institucional do catálogo. |
| Microlente gravitacional | 3 correções | [NASA métodos](https://science.nasa.gov/exoplanets/how-we-find-and-characterize/) e [NASA TESS, 2026](https://science.nasa.gov/missions/tess/nasas-tess-mission-finds-planetary-system-in-new-way/) (eventos não repetíveis em alinhamento usual). |
| Imagem direta de exoplanetas | 3 correções | [NASA Roman: direct imaging](https://science.nasa.gov/mission/roman-space-telescope/direct-imaging/) (contraste, distância à estrela, seleção de planetas jovens/grandes). |

**Observação:** DOI, páginas da NASA e registros de catálogo são tipos distintos de evidência e de direitos; nenhum deles autoriza copiar automaticamente figuras, artigos integrais ou dados em terceiros aplicativos. A proposta não reivindica permissão comercial de todo conteúdo científico publicado.

## 3. Teste de integração EM MEMÓRIA — PASSOU

A proposta foi recarregada diretamente do GitHub e aplicada a um clone temporário do JSON original lido da main, conferindo em cada operação:

- SHA da base original **`7c1f6a5fe5e95a145d082f9e552efb255d48fff7`** igual ao `sha_blob` do patch antes de calcular alterações. Se a main mudar, a operação DEVE PARAR e recomputar o diff.
- **27 de 27** índices/fatos/códigos de origem coincidiram e receberam a nova referência no clone.
- **15** identificadores novos foram adicionados sem colisão: 55→70 entradas de fontes no clone.
- **Zero IDs órfãos** de fonte em qualquer item.
- **Zero frases alteradas** (incluindo áreas fora de Astronomia), nenhum item removido, nenhuma alteração de alias, ligações e comparações.
- Estrutura de **113 itens** foi preservada; todas as afirmações originais permaneceram textualmente idênticas.

A simulação confirma consistência do *patch*, NÃO que todas as 279 afirmações sejam verdadeiras nem que a `main` tenha recebido os dados.

## 4. O que efetivamente falta

1. **Aplicação à main pelo integrador:** enquanto a outra equipe não incorporar o pacote, a base ativa ainda associa 25 fatos a fontes imprecisas e dois fatos Lagrange a fontes gerais (embora estes tenham apoio parcial).
2. **Verificação das demais 254 afirmações:** 232 ainda não conferidas semântica por frase; 22 apenas parcialmente comparadas com a fonte. As duas auditorias FINAIS do protocolo permanecem **0/2 aprovadas**.
3. **Validação de direitos individuais, versões de artigos, critérios de inferência e revisão científica independente:** não foi realizada de forma exaustiva.
4. **Testes do modelo e CI:** são tarefa do agente integrador; não atribuir desempenho de inteligência a correção de links.

**Decisão deste reparo:** corrigimos os erros de atribuição identificados **no artefato de pesquisa**, removemos o falso positivo do relatório e validamos um patch preciso, mas não consideramos a formação em Astronomia concluída nem declaramos que o CRIVO foi treinado. Não agendar nova auditoria final até que as fontes tenham sido importadas e os demais casos analisados.
