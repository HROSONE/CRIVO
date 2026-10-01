# Astronomia — funções de luminosidade, massa estelar e ligação galáxia–halo

**Data:** 2026-10-01. **Módulos:** 5 (principal), 6 (estrutura cósmica), 7 (levantamentos), 8 (estatística), 9 (inferência).  
**Status:** PESQUISA PARA REVISÃO; NÃO integrada, NÃO treinada, NÃO certificada. Somente branch documental.  
**Lacuna:** após documentar meio interestelar, fusões e distribuição de matéria escura, faltava explicar como comparar POPULAÇÕES inteiras de galáxias e por que massa estelar, massa de halo e brilho não são a mesma propriedade.

## 1. Três massas que não devem ser confundidas

- **Massa estelar M★:** massa atual das estrelas/remanescentes estelares sob convenções de modelagem e população. Inferida geralmente de espectro/fotometria e modelos de síntese populacional.
- **Massa bariônica:** pode incluir M★, gás atômico, gás molecular e outras componentes, descontadas hipóteses de contagem e raios.
- **Massa do halo M_h:** massa do sistema gravitantemente ligado definida por critério e raio próprios, frequentemente `M_200c` ou `M_vir` nos modelos cosmológicos. Diferentes convenções de overdensity não produzem automaticamente o mesmo número.

**Erro:** brilho da galáxia = massa estelar = massa de matéria escura. Mesmo sob massa estelar fixada, composição populacional, idade, poeira e geometria podem mudar luminosidade; mesmo sob M★ fixada, halos podem ter massas diversas [G1,G2].

## 2. Função de luminosidade e função de massa estelar

Uma **função de luminosidade** `φ(L)` descreve densidade numérica por volume e intervalo de luminosidade; uma **função de massa estelar** `φ(M★)` descreve densidade por intervalo de massa. Unidades diferem conforme usar intervalos lineares ou `dlog10M`: por exemplo, `Mpc^-3 dex^-1` significa número por volume comóvel e intervalo decimal de logaritmo da massa.

**Ajuste tipo Schechter:** `φ(L)dL = φ★ (L/L★)^α exp(-L/L★) d(L/L★)`. `φ★` é normalização volumétrica, `L★` a escala característica e `α` inclinação de objetos fracos. É ajuste estatístico, não lei determinística do ciclo de vida de uma galáxia. Duas populações podem requerer soma de componentes ou outra parametrização.

**Pontos de falha:** o mesmo levantamento pode perder objetos muito fracos, superfícies de brilho difuso e galáxias obscurecidas; observações em alto redshift selecionam fluxos, cores, linhas e áreas limitadas. Uma queda observada no extremo baixo da função não prova ausência física de galáxias fracas se a amostra é incompleta [G1,G3].

**Exemplo editorial de unidades:** em volume comóvel 1000 Mpc³, uma contagem bruta de 200 galáxias num intervalo de largura 0,5 dex forneceria 0,4 galáxias/(Mpc³·dex), *somente se* seleção e completude fossem perfeitas. Se o volume efetivo dos objetos varia com brilho, é preciso usar seleção e volume acessível por objeto [G1,G3].

## 3. Volume máximo observável e viés de seleção

Em levantamento limitado por fluxo, objeto luminoso pode ser detectado até uma distância maior que objeto fraco. Sem correção, números brutos favorecem intrinsicamente luminosos em amostras distantes e objetos próximos em outras circunstâncias.

Uma estimativa clássica de densidade usa soma de `1/Vmax_i` por objeto em faixas de luminosidade/massa, onde `Vmax_i` é o volume efetivo no qual o objeto ultrapassaria a seleção do levantamento. A validade depende de hipótese de homogeneidade e modelagem da seleção; redshift, poeira, perda de superfície de brilho e incompletude não desaparecem por invocar '1/Vmax'. [G1,G3]

**Variância cósmica:** dois campos pequenos com mesmo instrumento podem conter concentrações diferentes de estruturas; diferenças de contagem podem refletir densidade ambiental real, não falha de telescópio. Comparar levantamentos exige volume, área, função de seleção e estimativa de correlações entre objetos.

**Relação com JWST:** uma galáxia recordista do universo jovem pode ser extremamente brilhante *para sua época*. Essa seleção rara não é amostra representativa da massa típica de todas as galáxias.

## 4. Abundance matching: como unir observação de galáxias e simulação de halos

Uma simulação cosmológica de matéria escura fornece, sob hipótese cosmológica, abundância `n_h(>M_h)` de halos acima de certo limiar; um catálogo corrigido de galáxias fornece `n_g(>M★)`.

**Versão determinística simplificada:** impor `n_g(>M★)=n_h(>M_h)` e atribuir as galáxias mais massivas aos halos mais massivos. Isso é uma correspondência ESTATÍSTICA entre distribuições, não medição individual direta de cada halo. A forma realista inclui satélites, subhalos, dispersão intrínseca e propriedades no momento da acreção. [G1,G2]

**O que a técnica tenta descobrir:** relação média e dispersão `P(M★|M_h)`, formação eficiente ou ineficiente em diferentes halos e evolução com redshift. Se halo cresce por fusões, estrelas podem crescer por formação *in situ* e por incorporação de satélites; não confundir os dois canais.

**Revisão Wechsler & Tinker (2018):** a eficiência de converter bárions disponíveis em estrelas não é uma constante universal. A curva M★/M_h geralmente tem máximo em massa característica de halo próxima da ordem `10^12 M☉` no universo tardio, mas o valor e a altura exatos dependem de definição de halo, época, população e modelo. Isso explica por que galáxias de halos maiores não convertem uma fração continuamente maior de toda matéria em estrelas. Não transformar o número histórico da revisão em parâmetro preciso de 2026 sem checar levantamentos novos. [G1]

**Fator f_b:** a razão cosmológica de bárions é `f_b≈Ω_b/Ω_m` sob convenções do modelo. Uma eficiência de conversão estelar poderia ser expressa como `M★/(f_b M_h)`. Esse quociente é MODELADO, pois nem todos os bárions do halo estão no disco e há entradas/saídas; não é a eficiência instantânea de formar estrelas numa nuvem molecular [G1].

## 5. Halo occupation e satélites: funções não são listas de objetos

Um modelo de ocupação de halo (HOD) parametriza distribuição de galáxias que residem em halo de dada massa, diferenciando central e satélites, às vezes por luminosidade, cor ou taxa de formação. Em média, halo pode conter uma galáxia central detectável e número de satélites que cresce com massa do halo, mas limites de seleção e física do subhalo importam.

**Aglomeração angular/espacial:** correlação de dois pontos mede excesso de pares em separação em relação à distribuição de referência. Em certas escalas, muitos pares dentro do mesmo halo (*termo um halo*); em outras, pares entre halos (*termo dois halos*). A interpretação requer espaço de seleção, redshift e física não linear [G1,G4].

**Confronto observacional:** combinações de função de massa estelar, aglomeração e lente fraca restringem ocupação de halo de modo que uma única curva de luminosidade não consegue; diversas combinações dos mesmos levantamentos mantêm covariâncias compartilhadas e não são três experiências independentes por mera contagem [G1].

## 6. Crescimento e mudança ao longo do tempo

Sob formação hierárquica em ΛCDM, halos podem crescer por acreção e fusões. Galáxias dentro deles podem experimentar períodos de entrada de gás, formação de estrelas, jatos/ventos e stripping ambiental. Uma galáxia passiva muito massiva hoje pode ter crescido por fusões predominantemente estelares quando já formava poucas estrelas novas, enquanto outras mantêm discos ativos [G1,G2,G4].

**Não aplicar relação M★–M_h local a alto redshift sem modelagem:** abundância e história de halos mudam, e o catálogo observa populações diferentes. Numa teoria de seleção fotométrica, massa estelar inferida depende de IMF, história de formação, poeira e metalicidade. Isso não significa que a massa é inventada; significa que o instrumento mede luz e o modelo converte em massa sob condições documentadas.

**Contraexemplo:** uma galáxia que possui atualmente poucas estrelas pode habitar halo grande se formação estelar foi suprimida e stripping alterou relação entre massa atual/antiga. Não inferir halo a partir de um único brilho sem dispersão.

## 7. Exemplos científicos sintéticos: quando relações falham

1. **Mesma M★, duas cores:** população velha e rica em estrelas de baixa massa pode ser mais avermelhada e ter M/L maior; uma população jovem pode ser mais luminosa por unidade de massa. A massa não é função única de cor.
2. **Mesma M_h, diferentes SFRs:** uma central pode ter reserva de gás e outra estar quiescente, conforme história de alimentação, AGN e ambiente. A massa do halo não determina SFR instantaneamente.
3. **Parente antigo versus atual:** satélite perde massa de halo por marés, mantendo parte de suas estrelas por mais tempo; ligar M★ atual ao M_h atual pelo pareamento monotônico simples pode falhar. [G1,G2]
4. **Função observada de baixo brilho com lacuna:** não detectar objetos não equivale a demonstrar zero físicos sem limites de completude.
5. **Campo JWST pequeno e rico em galáxias:** pode ser estrutura real sob variância cósmica, ou seleção/contaminação; verificar volume e distribuição de redshifts.
6. **Curva de rotação versus M_200c:** massa gravitacional interior a raio orbital não é automaticamente massa de halo definida num raio de overdensity.

## 8. Matemática e dados que o agente integrador ainda precisaria executar

- Para amostra real, congelar release (SDSS DR17 ou outro catálogo com funções de seleção publicadas), filtro, população e faixas de redshift.
- Construir contagens por volume e faixa em dex, e comparar com estimadores corrigidos por completude; propagar erros de Poisson e variância cósmica.
- Ajustar uma função de Schechter com incerteza de parâmetros e covariâncias, se os dados justificarem forma; registrar hipótese de IMF.
- Comparar uma relação de massa de galáxia–halo publicada sob cosmologia e definição de halo explícitas, usando halo occupation/abundance matching sob sua dispersão documentada.
- Validar que resultados globais não se baseiam só em galáxias recordistas ou áreas selecionadas.

**Nada disso foi executado neste documento.** Ele delimita o procedimento científico. Exercícios numéricos acima são situações construídas e não testes de inteligência do CRIVO.

## 9. Matriz de evidências e bibliografia verificada

| ID | Fonte | Significado, escopo e direitos |
| --- | --- | --- |
| G1 | Wechsler, R. H. & Tinker, J. L. (2018), *The Connection between Galaxies and Their Dark Matter Halos*, Annual Review of Astronomy & Astrophysics 56, DOI https://doi.org/10.1146/annurev-astro-081817-051756 | Revisão primária de literatura. **Copyright do periódico reservado**; apenas síntese original e link, sem reprodução textual. |
| G2 | Behroozi, P., Wechsler, R. H. & Conroy, C. (2013), *The Average Star Formation Histories of Galaxies in Dark Matter Halos from z = 0–8*, ApJ 770:57, DOI https://doi.org/10.1088/0004-637X/770/1/57 | Método de vínculo massa/sistema e histórias modeladas; dependências de cosmologia. |
| G3 | NASA/IPAC Extragalactic Database (NED), apresentação da revisão por Wechsler/Tinker: https://ned.ipac.caltech.edu/level5/March18/Wechsler/Wechsler3.html | Abundâncias observacionais, função de seleção e técnicas; **mesma revisão G1**, não estudo independente. |
| G4 | Wechsler/Tinker, seções de funções halo/ocupação: https://ned.ipac.caltech.edu/level5/March18/Wechsler/Wechsler2.html | Abundance matching e HOD, **mesma revisão G1**. |
| G5 | SDSS DR17, descrição de alvos e redshifts: https://www.sdss4.org/dr17/ | Lançamento técnico de dados, não uma função de massa pronta sem inferências. |
| G6 | Planck Collaboration, *Planck 2018 results. VI*, DOI https://doi.org/10.1051/0004-6361/201833910 | Densidades cosmológicas sob modelo; já usado no dossiê de cosmologia, não fonte independente desta mesma equipe. |

**Direitos e rastreabilidade:** síntese em português escrita de novo, sem imagens, tabelas extraídas ou artigos reproduzidos. Relações funcionais são explicações conceituais derivadas das referências, não resultados de análise própria de catálogo. Artigos podem ser acessíveis publicamente sem licença comercial aberta; verificar texto integral/licença do item antes da reprodução. Respeitar a separação de dados NASA/ESA/SDSS e de relatórios científicos.

## 10. Lacunas restantes após fechamento desta subárea documental

O tema estatístico M★–M_h foi acrescentado. **Não** é permitido chamar módulo 5 'pesquisa_documental_pronta' antes de revisar a matriz completa do módulo e as condições de encerramento, particularmente: curvas de rotação sob modelos concorrentes, amostras em alto redshift, incerteza de massa estelar, evolução ambiental e validação por literatura externa. Não há análise própria de dados reais nesta execução, nem demonstração de cognição neural. Nenhum arquivo de produção, CI, pesos ou `main` foi alterado.
