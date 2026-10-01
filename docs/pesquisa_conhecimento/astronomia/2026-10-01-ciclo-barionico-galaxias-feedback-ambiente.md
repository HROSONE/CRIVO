# Astronomia — Ciclo bariônico, formação estelar, feedback e evolução ambiental de galáxias

**Pesquisa:** 2026-10-01. **Módulos:** 5 (principal), 6 (evolução cósmica), 7 (observação), 8 (matemática aplicada) e 9 (explicação causal).
**Status:** PESQUISA DOCUMENTAL PARA REVISÃO; NÃO integrada ao CRIVO; NÃO treinada; NÃO certificada. Exclusivamente na branch `pesquisa/acervo-conhecimento-crivo`.
**Não duplicar:** o acervo já contém [dinâmica galáctica e montagem hierárquica](2026-10-01-dinamica-galactica-via-lactea-montagem-hierarquica.md) e [lentes, buracos negros e distâncias](2026-10-01-lentes-buracos-negros-e-distancias.md). Aqui se pesquisa o que aqueles materiais deixam aberto: o orçamento do gás, os mecanismos de consumo e a alteração por ambiente. Nenhuma regra executável é adicionada.

## 1. Três reservatórios diferentes

**Meio interestelar (ISM):** matéria entre as estrelas dentro da galáxia, que pode conter fases moleculares frias, hidrogênio neutro atômico, gás ionizado e plasma quente. A massa de gás frio é uma condição importante para formar estrelas; não significa que todo o gás disponível colapsará ao mesmo tempo.

**Meio circumgaláctico (CGM):** gás difuso em torno de uma galáxia, fora da região estelar principal e ainda no entorno gravitacional do halo. Pode estar em várias fases de temperatura e ionização; participa da acreção, dos ventos e de material reciclado. Não é sinônimo de matéria escura, pois é matéria bariônica que, em condições apropriadas, absorve e emite radiação. A revisão de Tumlinson, Peeples e Werk (2017) reúne observações de CGM por espectroscopia de fontes de fundo [B1,B2].

**Meio intraglomerado (ICM):** plasma quente que ocupa um aglomerado de galáxias, observado em raios X. Interage hidrodinamicamente com o gás das galáxias que atravessam o aglomerado e pode ser aquecido por jatos do núcleo central. Não confundir ICM com CGM de uma única galáxia nem com halo escuro [B3,B4].

**Matéria interestelar não é um gás uniforme:** as fases podem compartilhar a mesma região espacial em temperaturas e densidades distintas. Por isso uma câmera óptica, um mapa de CO, um espectro UV de absorção e um mapa de raios X estão medindo componentes distintos; cada método possui viés de seleção [B1,B5].

## 2. Por que o gás forma estrelas? A cadeia causal não é automática

Colapso de parte do gás requer gravidade capaz de superar o suporte térmico, turbulento e magnético nas escalas relevantes. Resfriamento permite que densidades aumentem, mas a eficiência real também depende de pressão externa, cisalhamento, rotação, forças de maré e história de turbulência. Poeira pode proteger moléculas da radiação, influenciando química e temperatura.

**Hidrogênio molecular H₂:** é abundante em regiões frias e densas, mas sua emissão direta pode ser difícil em muitas condições; o CO observado em linhas rotacionais atua como traçador indireto. A linha CO(2–1) é um dos mapas principais da colaboração PHANGS-ALMA, cujo programa registra observações de 90 galáxias e produtos de 74 galáxias publicados; esses números são universos de cobertura distintos no material do levantamento [B5,B6].

**Por que 'mapa de CO = mapa de massa de H₂' é inadequado?** Converter fluxo de linha de CO em massa total H₂ requer fator de conversão α_CO e hipóteses sobre excitação e abundância relativa do CO. Metalicidade baixa, irradiação e condições físicas podem mudar a fração de H₂ não detectada por CO; dois mapas com mesmo brilho de CO não necessariamente contêm mesma massa molecular total [B5,B6].

**Taxa de formação de estrelas (SFR):** medida como massa de novas estrelas formadas por unidade de tempo, estimada a partir de populações jovens via Hα, ultravioleta, infravermelho ou outros traçadores. Cada indicador é sensível a janelas temporais, poeira, população estelar, história de formação e parâmetros adotados para a função de massa inicial (IMF). Não confundir quantidade total de estrelas visíveis com taxa atual de formação [B7,B8].

## 3. Tempo de esgotamento é relação, não relógio inexorável

Em uma região ou galáxia, pode-se definir `t_dep = M_gas / SFR`, usando a mesma reserva de gás para a taxa pertinente. Um valor grande de `t_dep` significa que, *se a SFR permanecesse constante e não houvesse novos fluxos de massa*, levaria aquele tempo para consumir uma massa equivalente à reserva. Não é previsão de vida de galáxia.

**Exemplo didático, não medida de PHANGS:** uma galáxia tem M_H2=3×10^9 massas solares e forma 3 massas solares por ano; t_dep=10^9 anos (1 Gyr). Se recebe gás fresco, expele gás ou muda sua eficiência, o tempo efetivo não acompanha esse quociente fixo.

A análise de Leroy e colaboradores, iniciada em 2025, usou medidas de gás molecular e formação de estrelas em regiões de ~1,5 kpc de 67 galáxias PHANGS, comparando tempo de esgotamento à eficiência por tempo de queda livre. É um estudo estatístico de *amostra selecionada*: não demonstra que todas as regiões do Universo obedecem a taxa constante [B9].

**Distinção de tempo de queda livre:** `t_ff = sqrt(3π/(32Gρ))` para esfera ideal homogênea sem suporte não gravitacional, e `ε_ff = (SFR × t_ff) / M_gas` sob correspondência espacial/temporal. Uma eficiência pequena NÃO significa falta de gravidade: pode representar turbulência, magnetismo, feedback e regiões em fases diferentes. Não aplicar `t_ff` calculado de densidade média de um disco a uma nuvem densa sem justificar geometria.

## 4. Equação de contabilidade do ciclo bariônico

Como aproximação de reservatório único em balanço temporal:

`dM_g/dt = Mdot_entrada - (1 - R + η) × SFR`.

Aqui:
- M_g é massa de gás definida no reservatório adotado;
- Mdot_entrada é fluxo que entra no reservatório;
- R é fração do material de estrelas jovens que retorna rapidamente ao gás sob a aproximação de reciclagem instantânea;
- η é o fator de carga de massa dos ventos: fluxo de saída gasosa/SFR;
- as parcelas devem usar as mesmas unidades, por exemplo massas solares por ano.

A forma simplifica dependências temporais, acreção do halo, mudança de fase de H I/H₂ e diferentes destinos do gás. É um modelo de orçamento, não uma lei universal de toda região [B1,B2].

**Exemplo hipotético coerente:** Mdot_entrada=5 massas solares/ano; SFR=3; R=0,4 e η=0,8. Logo `dM_g/dt = 5 - (1-0,4+0,8)×3 = 5 - 4,2 = +0,8 massas solares/ano`. Isso não equivale a dizer que todas as galáxias com SFR=3 aumentam reservas: falta especificar entrada e vento. Não usar R=0,4 e η=0,8 como medições de objeto real.

**Ciclo físico:** gás externo → ISM → regiões densas → estrelas; ventos, supernovas e núcleos ativos devolvem matéria/energia ao ISM/CGM/ICM; parte do gás pode esfriar e retornar. Algumas partículas deixam o halo; outras circulam em fontes temporais múltiplas [B1,B2].

## 5. Feedback estelar: aquecer, comprimir e redistribuir

Estrelas massivas irradiam UV, produzem ventos e podem terminar em supernovas. Essas fontes criam regiões H II, bolhas e choques, ionizam parte do gás, injetam energia e momento e redistribuem metais. A intensidade depende do número e massa das estrelas, porosidade do gás, densidade, eficiência de acoplamento e gravidade da galáxia.

**Feedback negativo local:** aquecimento e dispersão podem impedir colapso continuado em algumas nuvens. **Feedback positivo localizado:** bordas comprimidas de bolhas podem criar condições favoráveis à formação de estrelas em outros trechos; não supor resultado líquido positivo para toda galáxia.

**Observação direta comparada:** PHANGS combina mapeamento de CO de ALMA, Hα, UV, imagens do Hubble e Webb para comparar nuvens, associações jovens e regiões ionizadas. A amostra de 74 galáxias com dados CO processados não é amostra aleatória de todas as galáxias, e resolução angular convertida em escala física difere com distância [B5,B6].

**Precaução:** coincidência espacial entre nuvem e aglomerado não prova qual veio primeiro. É necessário obter idades relativas, velocidades, feedback, estimativas de fase molecular e comparar cenários concorrentes.

## 6. Feedback de núcleo galáctico ativo (AGN): energia fora do horizonte

Matéria fora do horizonte de eventos pode formar disco de acreção; processos radiativos, ventos e jatos acoplam energia e momento ao CGM ou ICM. O papel é particularmente importante em alguns halos massivos porque o gás poderia resfriar e formar estrelas mais rapidamente na ausência de aquecimento adicional.

Em Perseus e Virgo, análises de raios X com Chandra mostraram flutuações em densidade do gás quente, usadas para estimar turbulência; os autores discutiram energia suficiente para compensar resfriamento em condições analisadas [B10]. A interpretação requer modelagem das flutuações e não estabelece que cada aglomerado teve o mesmo balanço.

**Aquecer sem expulsar:** a energia do AGN pode manter gás quente e inibir acreção fria mesmo que o halo não perca toda a massa. Isso diferencia 'quenching por aquecimento/prevenção de resfriamento' de 'quenching por remoção de massa'.

**Estímulo localizado:** jato ou vento pode comprimir gás em regiões específicas. A existência do fenômeno NÃO invalida efeito global inibidor em outros sistemas. Comparar escala, cinemática, massa gasosa e disponibilidade de gás depois da perturbação [B10,B11].

## 7. Ambiente do aglomerado: pressão de arrasto versus marés

Uma galáxia se movendo através do plasma quente ICM sente pressão de arrasto hidrodinâmico `P_ram = ρ_ICM v_rel²`. Na aproximação clássica de disco fino visto de frente, pode haver retirada de gás quando `ρ_ICM v_rel² > 2πG Σ_star Σ_gas`; `Σ` é massa por área. O critério de Gunn–Gott é aproximado e sofre mudanças com geometria orbital, duração do pulso, halo gasoso, campos magnéticos e distribuição real do potencial [B12].

**Não confundir maré gravitacional com pressão de arrasto:** marés alteram órbitas de estrelas e gás; ram pressure afeta preferencialmente o componente gasoso que interage com o meio. Ambos podem ocorrer na mesma galáxia, mas deixam assinaturas morfológicas/cinemáticas distintas.

**Observação D100:** o Hubble observou galáxia caindo no aglomerado Coma com faixa de poeira/gás expelido, interpretada como remoção por pressão do meio; não pressupor que todas as estrelas sejam expulsas junto com o gás [B13].

**Observação LEDA 42160:** a NASA divulgou em março de 2024 que a compressão por ram pressure pode desencadear regiões locais de formação estelar, ao mesmo tempo em que o mecanismo remove gás e pode reduzir formação futura [B14].

**Exemplo de inferência:** galáxia com cauda de gás apontando em uma direção e disco estelar relativamente menos deformado oferece evidência de componente hidrodinâmica, mas a orientação em projeção e a cinemática devem ser verificadas antes de reconstruir a trajetória 3D.

## 8. Investigação em 2026: gás frio no Universo de 700 milhões de anos

Em **12 de junho de 2026**, o ALMA divulgou observações conjuntas com o VLA em REBELS-25, a redshift **z=7,31**, vista aproximadamente **700 milhões de anos** após o Big Bang. O VLA identificou emissão de transição de baixa excitação do monóxido de carbono (CO), enquanto ALMA forneceu linhas de CO mais excitadas, poeira e carbono ionizado. Com modelagem, a equipe estimou reserva de **aproximadamente 100 bilhões de massas solares de gás molecular** [B15].

**Três camadas, sem inverter evidência:**
1. Medida: emissão de linhas específicas e contínuo de poeira, com fluxo e frequência observados.
2. Inferência: massa H₂ aproximada por conversão de CO e modelo de excitação, composição, temperatura e influência do CMB.
3. Consequência: sob as hipóteses do estudo, existia grande reserva de combustível para formação estelar em época antiga.

**Não afirmar:** que foi pesado cada átomo do gás; que todo universo jovem tinha a mesma massa de gás; que a idade exata e a massa estão livres de pressupostos; ou que todo o gás se tornaria inevitavelmente estrelas.

**Conexão com cosmologia:** T_CMB(z) ≈ 2,725(1+z) K. Para z=7,31, isso dá ~22,65 K sob expansão térmica padrão. Um fundo térmico mais quente afeta o contraste e a interpretação de linhas frias. É uma dependência física indicada pelo estudo, não 'o VLA viu o próprio gás na forma da CMB' [B15].

**Questão quantitativa ilustrativa, não resultado da publicação:** se M_H₂ = 10^11 massas solares e SFR fosse 100 massas solares/ano, t_dep = 10^9 anos. Essa conta NÃO atribui SFR=100 ao objeto; serve apenas para mostrar como usar a relação com dados que precisariam ser efetivamente medidos.

## 9. Como uma galáxia pode deixar de formar estrelas sem ficar sem estrelas?

**Quenching** designa queda persistente de atividade de formação estelar, não desaparicão das estrelas existentes. Pode envolver perda de gás, interrupção da entrada fria, aquecimento, estabilização dinâmica e mudanças ambientais. Diferenciar taxa absoluta SFR da taxa específica sSFR = SFR/M_estelar: galáxia grande com SFR moderada pode ter formação relativamente baixa por unidade de massa já formada [B1,B10].

**Nuvem molecular vs. galáxia inteira:** estrela envelhece no disco mas o reservatório de nuvens novas pode ser alimentado por gás entrante; um evento de feedback pode dissolver uma nuvem sem cessar toda a atividade na galáxia.

**Ambiente:** satélites em aglomerados podem perder gás; centrais em halos massivos podem ter aquecimento que dificulta resfriamento; fusões podem desencadear formação estelar temporária ou destruir o equilíbrio gasoso. 'Galáxia elíptica' não é sinônimo lógico de ausência total de qualquer gás ou estrela jovem [B13,B14].

## 10. Matriz epistêmica e contraexemplos

| Dado/afirmação | Interpretação condicionada | Conclusão inválida |
| --- | --- | --- |
| Emissão CO(2–1) em região | Reservatório molecular estimado sob α_CO e excitação | Toda a massa H₂ foi diretamente pesada |
| UV e Hα intensos | Populações estelares jovens, sob IMF/poeira e outros contaminantes | Idade de todas as estrelas da galáxia é pequena |
| Cauda de H I com estrelas menos deformadas | Remoção hidrodinâmica favorecida, verificar projeções | Todas as marés são impossíveis |
| Cavidades de raios X próximas a AGN | Gás deslocado e energia depositada, sob modelagem | O buraco negro emite luz de dentro do horizonte |
| Perda local de nuvem por feedback | Formação futura ali pode ser inibida | Taxa de formação de toda galáxia se torna zero |
| CO de REBELS-25 | Fonte antiga com grande massa de gás estimada | Todos os primeiros objetos eram idênticos |
| Taxa SFR elevada | Formação atual/intensa sob janela do traçador | Necessariamente maior eficiência por massa de gás |
| t_dep=1 Gyr | Relação atual reserva/taxa | Galáxia morrerá exatamente em 1 Gyr |
| Luz vermelha da população | Mistura de idade, poeira e metalicidade | Prova de extinção completa da formação de estrelas |

## 11. Perguntas para curadoria futura, NÃO como teste independente pronto

1. Por que uma galáxia com muita matéria escura pode ter pouco gás para novas estrelas?
2. Se o CO brilha duas vezes mais, a massa H₂ necessariamente dobrou?
3. Galáxia com sSFR pequena possui zero estrelas jovens?
4. Pressão do ICM pode aumentar formação estelar local e, a longo prazo, removê-la?
5. Uma cauda de gás com estrelas pouco deformadas prova colisão direta de estrelas?
6. O Sol produz energia, então por que um campo UV intenso pode impedir colapso de nuvens próximas?
7. Por que a detecção de CO em z=7,31 precisa modelar a CMB mais quente?
8. Se o CGM tem fluxo de entrada de 5 e vento de saída de 3 massas solares/ano, a SFR será necessariamente 2? (Não: retorno e alteração de reservatório importam.)
9. Uma fonte intensa em Hα sem correção por poeira fornece SFR universalmente exata?
10. O fato de um buraco negro aquecer gás prova que toda galáxia com buraco negro ficou estéril?

Os exemplos são conteúdo editorial para apoiar outra equipe; não compõem avaliação cega e não devem ser copiados para dados de treinamento com o rótulo de prova independente.

## 12. Bibliografia consultada e condições de reutilização

| ID | Fonte, ano e link | Natureza do apoio e limite |
| --- | --- | --- |
| B1 | Tumlinson, Peeples & Werk (2017), *The Circumgalactic Medium*, Annual Review of Astronomy and Astrophysics 55:389–432: https://doi.org/10.1146/annurev-astro-091916-055240 | Revisão científica de CGM e ciclo de gás, não uma medida de todos os halos. |
| B2 | NASA/Hubble (2011), *Hubble Confirms Galaxies Are the Ultimate Recyclers*: https://science.nasa.gov/missions/hubble/nasas-hubble-confirms-that-galaxies-are-the-ultimate-recyclers/ | Absorção UV e inflows/outflows; comunicação institucional de estudos. |
| B3 | NASA Chandra, *Galaxy Clusters* (visão institucional): https://science.nasa.gov/missions/chandra/ | Observação de plasma de aglomerados, não matéria escura diretamente. |
| B4 | NASA/Hubble (2019), *Hubble Sees Plunging Galaxy Losing Its Gas*: https://science.nasa.gov/missions/hubble/hubble-sees-plunging-galaxy-losing-its-gas/ | Evidência visual de stripping em D100. Mesma evidência citada em B13. |
| B5 | ALMA Science Portal, *PHANGS-ALMA Survey*: https://almascience.nrao.edu/alma-data/lp/PHANGS/ | 90 galáxias no programa e dados processados de 74; emissão CO(2–1); não contagem de nuvens de todo Universo. |
| B6 | PHANGS STScI, *PHANGS-HST/JWST*: https://phangs.stsci.edu/ | Dados UV, ópticos e IR comparados a ALMA; a amostra depende da seleção original. |
| B7 | SDSS DR17, *Data Release 17*: https://www.sdss4.org/dr17/ | Dados espectrais e mapas IFU de galáxias para estudos de formação estelar, sujeitos a calibração. |
| B8 | SDSS, *Portsmouth Galaxy Properties*: https://www.sdss4.org/dr17/spectro/galaxy_portsmouth/ | Estimativas de emissão Hα/Hβ e avisos sobre extinção; baixa S/N de Hβ impõe limites. |
| B9 | Leroy e colaboradores (2025), *Cloud-scale gas properties, depletion times, and star formation efficiency per free-fall time in PHANGS–ALMA*: https://arxiv.org/abs/2502.04481 | Análise da amostra de 67 galáxias em regiões de 1,5 kpc; preprint consultado. |
| B10 | NASA/Chandra (2014), *Impact of Cosmic Chaos on Star Birth*: https://www.nasa.gov/news-release/nasas-chandra-observatory-identifies-impact-of-cosmic-chaos-on-star-birth/ | Turbulência e regulação por feedback em Perseus/Virgo, cenário contextual. |
| B11 | NASA/Hubble (2022), *Black Hole Igniting Star Formation in a Dwarf Galaxy*: https://science.nasa.gov/missions/hubble/hubble-finds-a-black-hole-igniting-star-formation-in-a-dwarf-galaxy/ | Exemplo de compressão local de gás, não aumento universal. |
| B12 | *Ram pressure stripping: an analytical approach*, MNRAS 489 (2019): https://academic.oup.com/mnras/article/489/4/5582/5575211 | Condição Gunn–Gott, limites de disco fino e duração de interação; artigo técnico. |
| B13 | NASA/Hubble (2019), *Hubble Sees Plunging Galaxy Losing Its Gas*: https://science.nasa.gov/missions/hubble/hubble-sees-plunging-galaxy-losing-its-gas/ | MESMA fonte que B4; não contar como referência independente. |
| B14 | NASA/Hubble (25/03/2024), *Hubble Views a Galaxy Under Pressure*: https://www.nasa.gov/image-article/hubble-views-a-galaxy-under-pressure/ | LEDA 42160, compressão local e possível formação estelar induzida. |
| B15 | ALMA Observatory (12/06/2026), *ALMA and VLA Reveal a Vast Reservoir of Star-Forming Fuel in a Galaxy Near Cosmic Dawn*: https://www.almaobservatory.org/en/press-releases/alma-and-vla-reveal-a-vast-reservoir-of-star-forming-fuel-in-a-galaxy-near-cosmic-dawn/ | REBELS-25 z=7,31; emissões CO e conversão modelada para ~10^11 M⊙, não pesagem direta. |

**Condições de uso:** síntese original em português com referências, sem copiar figuras, arquivos brutos, artigos completos ou trechos extensos. Link público não garante licença irrestrita; verificar os direitos de cada publicação/figura individualmente. NASA: https://www.nasa.gov/nasa-brand-center/images-and-media/ ; ALMA/ESO: https://www.eso.org/public/outreach/copyright/ ; preprints e periódicos possuem direitos próprios. As fontes da NASA e estudos originais sobre um mesmo alvo não são automaticamente experimentos independentes.

## 13. Lacunas restantes

1. Mapear funções de massa e luminosidade de galáxias sob seleção e redshift; examinar métodos de halo occupation/abundance matching e seus pressupostos.
2. Separar efeito do halo escuro do comportamento do gás frio e da seleção observacional, sem imaginar detecção direta de partículas.
3. Exercícios reprodutíveis em dados abertos PHANGS/SDSS com propagação de erros e direitos verificados; este dossiê fornece relações e fontes, NÃO uma análise de catálogo executada.
4. Revisão científica cruzada e auditoria de cobertura completa do módulo 5, de acordo com o protocolo de parada documental.
5. Não atribuir coeficientes ilustrativos `R`, `η` a galáxia real nem afirmar que a natureza de mecanismos contestados está decidida.

**Estado:** módulo 5 significativamente aprofundado em ciclo bariônico e ambiente, ainda NÃO marcado pesquisa_documental_pronta; 0/10 módulos certificados segundo skill na main; nenhuma mudança na main, código, checkpoints, treino ou testes.
