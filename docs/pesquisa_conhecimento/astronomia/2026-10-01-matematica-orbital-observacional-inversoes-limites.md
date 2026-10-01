# Astronomia — Caderno matemático integrado: órbitas, gravidade, radiação, distância e incertezas

**Pesquisa:** 2026-10-01. **Módulo principal:** 8 (matemática aplicada). **Conexões:** 2, 3, 4, 6, 7 e 9.  
**Status:** PESQUISA DOCUMENTAL PARA REVISÃO; NÃO integrada, NÃO treinada, NÃO certificada.  
**Método:** fórmulas com domínio de validade, símbolos, unidades e contas de checagem elaboradas editorialmente. **Nenhum catálogo externo foi baixado ou processado e nenhum teste neural foi executado.** Números de exemplos abaixo são sintéticos ou especificados por material didático de referência.

## 1. Sistema de unidades obrigatório

| Quantidade | Símbolo | Unidade SI típica | Observação |
| --- | --- | --- | --- |
| Comprimento | r, a, R | m | Astronomia também usa km, AU, parsec; não misturar sem converter |
| Massa | m, M | kg | Massa solar, terrestre e lunar são unidades escaladas |
| Tempo | t, P | s | Ano precisa de convenção para cálculo preciso |
| Velocidade | v | m/s | Dados observacionais frequentemente em km/s |
| Aceleração | g | m/s² | Difere entre superfície e órbita |
| Constante de gravitação | G | m³/(kg·s²) | Não confundir com aceleração g |
| Fluxo radiativo | F | W/m² | Não equivale a luminosidade total |
| Luminosidade | L | W | Energia por tempo |
| Densidade | ρ | kg/m³ | Densidade média e perfil interno são diferentes |
| Ângulo | θ | rad | 1 arcsec=1/206265 rad, aproximadamente |
| Redshift | z | adimensional | Não equivale a km/s em todos os regimes |

**Regra crítica de dimensões:** o lado esquerdo e o lado direito de uma equação física devem ter as mesmas dimensões. Se surgir `v = GM/r`, há erro dimensional porque `GM/r` tem dimensão de velocidade **ao quadrado**; a expressão circular é `v²=GM/r` [T1,T2].

## 2. Movimento em campo de massa esférica

Para partícula de massa desprezível comparada ao corpo central, gravitação newtoniana e campo aproximadamente esférico:

`g(r) = GM/r²` é a magnitude da aceleração da gravidade, independente da massa da pequena partícula no limite assumido.

`v_circ = sqrt(GM/r)`: velocidade circular, se não há forças adicionais relevantes e `r` é raio orbital em torno do centro de massa.

`P=2π sqrt(r³/(GM))`: período de órbita circular, se o raio permanece constante e o sistema corresponde à idealização.

`v_escape(r)=sqrt(2GM/r)`: velocidade de escape para atingir energia total zero em cenário de dois corpos newtoniano sem arrasto e sem outros potenciais.

**Comparação calculável:** na MESMA posição ideal, `v_escape/v_circ = sqrt(2)`. Isso não significa que nave com velocidade menor não possa escapar usando propulsão contínua; fórmula pressupõe velocidade inicial e ausência de empuxo posterior.

**Terceira lei em forma de dois corpos:** `P²=4π²a³/[G(M+m)]`, onde `a` é semieixo maior da órbita RELATIVA, `m` a massa do companheiro. No limite `m≪M` e na mesma estrela, `P²∝a³`. Em unidades ano e AU para órbitas em torno do Sol, aproximação `P²≈a³`, mas NÃO deve ser aplicada sem fator de massa para órbitas em torno de outras estrelas [T1,T2].

**Exemplo sintético:** em torno da mesma estrela, `a_2/a_1=4` implica `P_2/P_1=4^{3/2}=8` na aproximação. Isso é relação de períodos, não evidência que o planeta moveu-se dessa órbita para outra.

## 3. Órbita elíptica e conservação de energia

Para elipse kepleriana ideal, `r_p=a(1-e)`, `r_a=a(1+e)`, com `0≤e<1`. Daí `e=(r_a-r_p)/(r_a+r_p)`, e `a=(r_a+r_p)/2`. A massa central ocupa um foco, não o centro geométrico da elipse.

**Exemplo:** `r_p=1 AU` e `r_a=3 AU` resultam em `a=2 AU` e `e=(3-1)/(3+1)=0,5`. A maior distância não significa que a órbita tem metade da velocidade máxima, pois vis-viva e momento angular definem velocidades reais.

**Equação vis-viva:** `v²=G(M+m)(2/r-1/a)`, sob dois corpos e movimento relativo. Quando `r` diminui em órbita elíptica, velocidade cresce, coerente com a segunda lei de Kepler. Energia orbital específica `ε=-G(M+m)/(2a)` para movimento relativo por unidade de massa reduzida sob convenções apropriadas; para corpo teste `E=-GMm/(2a)`. [T1,T2]

**Segunda lei de Kepler:** momento angular específico `h=r² dθ/dt=sqrt(G(M+m)a(1-e²))`; taxa de área varrida `dA/dt=h/2` constante sem torque, não velocidade linear constante. Reutilizar `h` em problema de disco com torque externo exige contabilizar `dh/dt`.

**Não confundir:** conservar energia orbital de planeta isolado e conservar energia total de sistema planeta–disco são afirmações distintas. Em migração, o planeta pode trocar energia e momento angular com gás e outros corpos.

## 4. Esfera de Hill, Roche e ressonância

`R_H≈a (m_p/(3M_*))^{1/3}` representa escala do domínio gravitacional de planeta pequeno frente à estrela em órbita aproximadamente circular; não é garantia de estabilidade permanente de satélite em qualquer órbita. Uma análise dinâmica distingue limites de satélites prógrados e retrógrados e perturbações estelares [T11]. O limite de Roche considera gradiente de maré versus coesão e auto-gravitação de corpo; é distinto do raio Hill e pode ser calculado sob várias hipóteses de fluido/rigidez [T3].

**Ressonância p:q:** razão aproximada entre frequências/períodos mais combinação angular de fases; relação de períodos 2:1 em órbitas keplerianas implica `a_2/a_1=2^{2/3}≈1,5874` para mesma massa central, não distância duplicada. Perturbações reais produzem librar ângulos ressonantes e podem alterar excentricidades.

**Lacunas de Kirkwood:** observadas em distribuição de semieixos de asteroides relacionadas a ressonâncias com Júpiter; não demonstram que toda ressonância elimina objetos. [T4]

## 5. Momento de força e migração orbital

Para planeta de massa aproximadamente fixa `m`, órbita circular e estrela com `M≫m`, `L=m sqrt(GMa)`. Se o torque líquido de disco é `T=dL/dt`, a variação de `a` depende do sinal do torque e do balanço energético. Um regime com massa crescente exige termo de acreção, portanto não substituir `dL/dt` pelo comportamento de um único `a` sem mencionar `dm/dt`.

**Conta sintética:** com m e M fixas, `a` cresce de 1 para 9 unidades de comprimento e `L` muda por fator `sqrt(9/1)=3`. Não se pode inferir tal migração apenas observando `a=9` hoje, sem evidências do passado [T5].

## 6. Paralaxe, velocidade transversal e incerteza

**Paralaxe:** `d[pc]=1/p[arcsec]=1000/p[mas]` somente como estimador simples de paralaxe bem medida e calibrada. Para `p=10±0,2 mas`, `d≈100 pc` e `σ_d≈(1000/p²)σ_p≈2 pc` pela propagação linear. Para p próximo de zero ou com desvio maior que valor nominal, distribuição posterior de distância pode ser muito assimétrica; não usar inversão automática em baixa SNR. Gaia DR3 tem zero de paralaxe com dependência de magnitude/cor/posição, não uma correção global única [T6,T7].

**Velocidade transversal:** `v_t[km/s]=4,74047 μ[arcsec/ano] d[pc]`. Exemplo `μ=0,1 arcsec/ano`, `d=20 pc`: `v_t≈9,48094 km/s`. Velocidade radial exige Doppler e composição vetorial depende da geometria. [T6]

## 7. Luz, temperatura e potência

`F=L/(4πd²)` vale para fonte aproximadamente isotrópica em espaço não cosmológico, sem extinção, e distância geométrica pertinente. Em cosmologia usa-se distância de luminosidade `D_L`; em presença de poeira e lente, interpretar o fluxo exige correções.

`L≈4πR²σT_eff⁴` vale para corpo aproximadamente negro de raio R e temperatura efetiva T; espectro e linhas reais introduzem correções. Se R dobra e T permanece fixa, L quadruplica. Se T dobra e R fixo, L cresce por fator 16. Esses fatores não são previsão de como estrela *realmente* evoluirá, pois R e T podem mudar juntos [T8].

`F_estrela ∝1/r²` ao longo de distância em espaço livre. **Temperatura superficial** não segue simplesmente 1/r²; temperatura de equilíbrio ideal pode variar aproximadamente como `r^{-1/2}` sob albedo e emissão constantes, mas efeito estufa, geologia e atmosfera mudam a consequência. Explica por que Vênus pode ser mais quente que Mercúrio em métricas de superfície [T8].

## 8. Redshift e distâncias cosmológicas

`z=(λ_obs-λ_rest)/λ_rest`. Para `λ_rest=500 nm` e `λ_obs=600 nm`, z=0,2. Pequenos z podem seguir `cz≈H0D` após corrigir movimento peculiar e sob condições; alto z requer modelo. Unidade de H0: km/s/Mpc.

`D_L=(1+z)² D_A` sob relação de dualidade e pressupostos sobre propagação da luz. Distância comóvel, tempo de retrospectiva, D_L, D_A e distância própria atual são objetos físicos/matemáticos distintos [T9].

**Exemplo sintético:** se `z=1` e `D_A=1 Gpc`, então `D_L=4 Gpc` sob pressupostos. Não implica que a luz viajou 4 Gpc em 'tempo de viagem' euclidiano de 4 bilhões de anos.

## 9. Modelo inverso, erros e identifiabilidade

Medida pode ser escrita `y=f(θ)+ε`, com θ parâmetros e ε ruído/calibração. Dados podem restringir θ se o modelo é identificável, mas diferentes combinações de parâmetros podem produzir mesma previsão dentro da sensibilidade. Adicionar observáveis independentes e controlar covariâncias aumenta identificabilidade; adicionar medições repetidas com erro compartilhado nem sempre aumenta exatidão [T6,T10].

Para `y=f(x)` localmente diferenciável e erros pequenos: `σ_y≈|df/dx|σ_x`. Para várias variáveis, `Var(y)≈J C Jᵀ`, onde C é matriz de covariância. Essa aproximação pode falhar com paralaxe ruidosa, limites físicos ou distribuições assimétricas.

**Caso ilustrativo:** dois instrumentos têm erro estatístico independente de 0,2 e compartilham zero de calibração 0,3. Média tem erro estatístico `0,2/sqrt(2)=0,1414`, mas erro sistemático comum 0,3 persiste; incerteza total ≈`sqrt(0,1414²+0,3²)=0,3317`. Tratar o total como 0,1414 equivale a perder informação importante.

**Significância e múltiplos testes:** um sinal 5σ pode ser decisivo sob modelo correto de ruído e seleção, mas testar milhões de combinações sem correção altera a taxa de falsos positivos; a significância estatística não prova interpretação causal única.

## 10. Problemas de aplicação para outro agente, SEM gabarito contaminado

Exemplos editoriais construídos para ensinar princípios, NÃO banco retido para certificação:
1. Uma órbita com a=3 AU em torno da mesma estrela tem quantas vezes o período de a=1 AU? Indicar `3^{3/2}≈5,196`, com condições.
2. Um planetesimal fora do limite de Roche está obrigatoriamente estável dentro de Hill? Não; problemas distintos e perturbações.
3. Um planeta com dobro de massa e raio iguais possui g duas vezes maior em campo esférico; isso prova núcleo rico em ferro? Não.
4. Uma estrela com raio dobro e mesma T possui luminosidade quatro vezes maior em aproximação negra; não se conclui que sua idade é o dobro.
5. Para p=0,1±0,1 mas, é válido relatar d=10000±10000 pc como resultado simétrico confiável? Não.
6. Se a distância lunar é medida com erro sistemático no tempo de voo, milhares de pulsos eliminam o erro comum? Não.
7. D_L e D_A em z=1 são medidas idênticas? Não; dualidade.
8. Se redshift subiu em uma linha, massa de um exoplaneta necessariamente cresceu? Não; movimento, estrutura orbital e outras linhas importa.

**Essas respostas NÃO foram testadas no CRIVO.** Novas provas independentes deverão ser criadas pelo integrador sem reciclar estes exemplos e os dados de treinamento.

## 11. Referências e limites de uso

| ID | Fonte | Área e natureza |
| --- | --- | --- |
| T1 | NASA, *Orbits and Kepler's Laws*: https://science.nasa.gov/solar-system/orbits-and-keplers-laws/ | Kepler 1ª–3ª leis e leis de áreas/periodos; institucional. |
| T2 | NASA/JPL, *Basics of Space Flight*, cap. 1: https://science.nasa.gov/learn/basics-of-space-flight/chapter1-3/ | Mecânica orbital e descrição de família de corpos; não substitui derivação de todos os casos. |
| T3 | NASA Science, *Cassini FAQ*: https://science.nasa.gov/mission/cassini/faq/ | Roche e processos em anéis; geometria e rigidez alteram escala. |
| T4 | NASA/JPL SSD, *Main Belt Distribution*: https://ssd.jpl.nasa.gov/diagrams/mb_hist.html | Distribuição/resonâncias, catálogo sujeito a seleção. |
| T5 | Nelson, R. P. (2018), *Planetary Migration in Protoplanetary Disks*: https://arxiv.org/abs/1804.10578 | Revisão teórica, torques e regimes de migração; acesso ao preprint não é licença irrestrita. |
| T6 | ESA Gaia DR3 Documentation: https://gea.esac.esa.int/archive/documentation/GDR3/ | Astrometria, erros e produtos; informar release em cálculos reais. |
| T7 | Bailer-Jones et al. (2021), distâncias Gaia EDR3: https://bailer-jones.www3.mpia.de/gedr3_distances.html | Modelos probabilísticos; mesmo conjunto Gaia, não detector independente. |
| T8 | NASA Science, *Sun Facts*: https://science.nasa.gov/sun/facts/ | Luminosidade, estrutura e radiação; equações didáticas requerem hipóteses. |
| T9 | D. Hogg, *Distance Measures in Cosmology*: https://arxiv.org/abs/astro-ph/9905116 | Definições e relações de distância; nota científica. |
| T10 | Gaia DR3 Data Model: https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html | Campos de erros, correlações e documentação de qualidade. |
| T11 | Hamilton, D. P. & Burns, J. A. (1992), *Orbital stability zones about asteroids. II: The destabilizing effects of eccentric orbits and of solar radiation*, *Icarus* 96, 43–64, DOI https://doi.org/10.1016/0019-1035(92)90005-R | Artigo científico sobre limite de estabilidade, inclinação, excentricidade e perturbações: **raio de Hill não garante estabilidade de toda órbita**. Os modelos estudam asteroides e seu domínio de aplicação deve ser explicitado. |

**Proveniência:** fórmulas comuns com domínio declarado; nenhum dado real foi processado. Direitos de publicações técnicas, NASA e ESA por item: https://www.nasa.gov/nasa-brand-center/images-and-media/ . Texto novo para pesquisa e revisão, sem cópia de fotos ou tabelas externas. Documento não é prova neural.

## 12. Lacunas para a promoção

A matemática central de órbitas, energia, gravidade, fluxo, distâncias e incertezas agora está organizada com exemplos quantitativos. Antes de declarar **módulo 8 documentalmente pronto**, é preciso revisão formal de unidades/aproximações, cálculos com dados observacionais versionados, propagação explícita de covariância nos exercícios e conferência completa da skill. Esses trabalhos não foram executados por esta pesquisa e continuam fora de uma certificação. Nenhum código, teste, peso ou main alterado.
