# Astronomia — Exoplanetas: trânsito, Doppler, microlentes, imagem direta e inferência atmosférica

**Data:** 2026-10-01. **Módulos:** 2 (comparação com Sistema Solar), 3 (diversidade de sistemas), 7 (observação), 8 (matemática), 9 (raciocínio), 10 (evidências preparadas).  
**Estado:** PESQUISA PARA REVISÃO; NÃO integrada ao CRIVO; NÃO treinada; NÃO certificada. Arquivo documental isolado, sem código, pesos ou mudanças em `main`.
**Escopo:** a main inclui categorias de trânsito, velocidade radial, microlente e imagem direta; ampliar mecanismos e limites, de modo que um agente integrador não treine o CRIVO apenas para reconhecer palavras.

## 1. Um planeta detectado não é necessariamente um planeta caracterizado

**Detecção:** evidência suficiente para reconhecer sinal compatível com planeta sob critérios observacionais (por exemplo repetição, validação estatística ou confirmação por método distinto, dependendo do caso).
**Caracterização:** estimar parâmetros como período, raio, massa, densidade, temperatura de equilíbrio, composição atmosférica e excentricidade; nem todos são mensuráveis de todo planeta.
**Confirmado, candidato, falso positivo:** estados diferentes de curadoria. Algoritmo de busca pode identificar eventos transitórios sem distinguir de binária eclipsante, variação estelar ou artefato do detector. Catálogos de exoplanetas são atualizados; não gravar contagem de 'planetas confirmados hoje' como fato permanente [X1,X2].

**Relação com observação:** o tipo de dado e a sensibilidade do método limitam o que se conhece sobre o corpo. Imagem direta em múltiplas bandas pode revelar fluxo do sistema e informações atmosféricas, mas não produz fotografia da superfície com continentes/vegetação em telescópios atuais. Uma curva de luz de trânsito mede obscurecimento temporário da estrela, não movimento da sonda através do planeta.

## 2. Trânsitos: por que um decréscimo de brilho pode indicar raio

Para planeta opaco com disco projetado diante de estrela, sem efeitos complicadores e desconsiderando obscurecimento de borda, a profundidade do trânsito é aproximadamente `δ≈(R_p/R_*)²`. Os parâmetros são raios do planeta e da estrela. A inferência depende do conhecimento de `R_*` e é afetada por *limb darkening*, impacto geométrico (b), mistura com estrelas próximas, manchas, ruído e eventual atmosfera [X1,X3].

**Conta didática:** um planeta com R_p/R_*=0,1 produz `δ≈0,01` (1%) na aproximação. Outro com razão 0,01 produz `δ≈0,0001` (0,01% = 100 partes por milhão). Os números NÃO são profundidades medidas de objetos reais. O método favorece corpos grandes diante de estrelas pequenas, mantidas outras condições.

**Probabilidade geométrica aproximada:** para órbita circular e alinhamentos isotrópicos, `P_trânsito≈(R_*+R_p)/a` se a≫R_* e condições adequadas. Quanto menor o semieixo maior, maior a chance de trânsito. Observar muitas estrelas e detectar muitos planetas próximos NÃO demonstra que planetas próximos são mais numerosos na natureza, sem correção de completude do levantamento [X1,X4].

**Período:** séries de eclipses aproximadamente periódicos permitem estimar duração de volta; nem toda oscilação repetida é planeta. Binárias eclipsantes, variabilidade periódica de superfície estelar e artefatos de satélite podem imitar sinais; comparar profundidades alternadas, eclipses secundários, centróide e velocidades radiais [X3,X4].

**Inclinação:** transitar significa que o plano orbital está favoravelmente alinhado para um observador, não que todo sistema exoplanetário esteja de frente para a Terra.

## 3. Velocidade radial: efeito sobre a estrela, não uma câmera filmando o planeta

Planeta e estrela orbitam o baricentro comum. A estrela sofre movimento de velocidade ao longo da linha de visada que desloca linhas espectrais conforme o efeito Doppler; pesquisadores extraem uma série temporal de velocidades. Para planeta muito menos massivo que a estrela, órbita aproximadamente kepleriana, o semiamplitude depende de `K ∝ M_p sin(i) / (M_*+M_p)^{2/3} × P^{-1/3} / sqrt(1-e²)`, com fatores `(2πG)^{1/3}` e as unidades apropriadas [X1,X5].

**Massa mínima:** sem conhecer a inclinação orbital `i`, uma detecção Doppler usualmente restringe combinação `M_p sin i`, não massa verdadeira em geral. A combinação com trânsito fornece informação geométrica e pode permitir massa e densidade: `ρ≈3M/(4πR³)`, se M e R forem estimadas de forma consistente.

**Contraexemplo:** duas estrelas com mesmo padrão de redshift periódico podem ter companheiros de massas distintas se as inclinações são distintas. E atividade estelar também pode deslocar linhas e produzir sinais quase periódicos.

**Precisão instrumental:** não se pode inferir exoplaneta terrestre simplesmente porque encontrou variação de ~1 m/s numa noite sem calibração de deriva do espectrógrafo, ruído de linhas e periodicidade consistente.

## 4. Microlente gravitacional: uma ampliação que não exige trânsito

Se estrela de primeiro plano passa perto da linha visual de outra estrela distante, a geometria gravitacional pode amplificar temporariamente a luz da fonte. Um planeta ao redor da lente pode produzir perturbação na curva de brilho. A assinatura depende da massa e geometria do sistema, velocidade transversal e movimento observador–lente–fonte [X1,X6].

**Pontos fortes:** detectar planetas em órbitas relativamente afastadas e, em determinadas condições, populações que trânsito/Doppler amostram mal, incluindo fontes distantes.

**Limites:** muitos eventos são únicos na escala humana; reconstruir massa e distância exige informações adicionais, paralaxe de microlente, observações de alta resolução, modelos de massa e parâmetros geométricos. Uma única curva de magnificação pode admitir degenerescências.

**Erro a evitar:** microlente é fenômeno gravitacional da trajetória da luz; não significa câmera que resolveu visualmente dois pequenos objetos separados no céu.

## 5. Imagem direta: bloquear luz da estrela e recuperar emissão fraca

Coronógrafos e técnicas de processamento podem suprimir grande parte do brilho da estrela, deixando ver companheiro. Exoplanetas jovens, quentes, massivos e relativamente afastados são alvos favoráveis; distância angular e contraste limitam detecções. A fotometria espectral de algumas fontes permite investigar temperatura, nuvens e componentes atmosféricos sob modelos [X1,X7].

**Viés:** muitos planetas terrestres pequenos e próximos a estrelas são extremamente difíceis de detectar diretamente por causa do contraste e da separação angular. Portanto a amostra de imagem direta não pode ser usada sem correções como censo das massas típicas do universo.

**Observação e interpretação:** um ponto de luz separado no infravermelho é dado de imagem; massa/tamanho estimados de seu brilho podem depender de idade, evolução térmica e atmosfera, sobretudo em gigantes jovens [X7].

## 6. Astrometria e variações temporais de trânsito

**Astrometria:** posição de estrela no céu oscila devido ao movimento relativo ao baricentro; para distância estelar d e semieixo estelar `a_*`, a amplitude angular ≈`a_*/d` em unidades coerentes. Estimativa exige corrigir paralaxe e movimento próprio, que podem ser muito maiores que sinal do planeta. Combinações astrométricas e Doppler podem reduzir ambiguidade de inclinação [X8].

**Variações de tempo de trânsito (TTV):** a gravidade de outros planetas desloca horários esperados sob órbitas isoladas. Isso pode restringir massas e ressonâncias quando existem conjuntos temporais bem amostrados. Mudança de tempo não exige novo planeta em todo caso: atividade estelar, efemérides imprecisas e relógios precisam de controle. [X3]

## 7. Atmosferas: componentes de espectro não significam automaticamente biossinal

Na espectroscopia de transmissão, uma pequena fração da luz estelar atravessa a região limítrofe da atmosfera do planeta durante o trânsito. Gases absorvem/espalham determinadas bandas, modificando a profundidade aparente por comprimento de onda [X1,X9].

**Problemas físicos:** nuvens e névoa podem mascarar bandas; temperatura, pressão e composição podem produzir soluções degeneradas; contaminação por manchas estelares pode produzir assinatura cromática confundida com atmosfera. Uma molécula inferida precisa ser associada a espectros, calibrações, hipóteses e incerteza.

**Temperatura de equilíbrio:** `T_eq≈[L_*(1-A)/(16πσa²)]^{1/4}` para órbita circular, radiação média global, redistribuição ideal de calor e corpo que irradia como corpo negro; A é albedo de Bond. Atmosfera/efeito estufa, rotação, superfície, excentricidade e calor interno podem produzir temperatura de superfície diferente. Nem `T_eq` prova presença de água líquida, nem temperatura na 'zona habitável' prova existência de organismos [X10].

**Falso positivo de vida:** oxigênio, metano, fosfina ou outro gás podem ter processos abióticos plausíveis dependendo do ambiente; é necessária análise conjunta do sistema estrela–planeta, geoquímica e contexto. A NASA descreve biossinais como hipóteses que exigem convergência de evidências e descarte de explicações não biológicas [X10].

## 8. Como combinar métodos e calcular uma densidade

**Cenário didático, SEM atribuição a planeta real:** trânsito determina R_p=2R_Terra; Doppler + geometria determinam M_p=8M_Terra. Então `ρ_p/ρ_Terra=(8)/(2³)=1`. Mesma densidade média não prova mesma composição, estrutura ou tectônica; núcleos, envelopes e estados térmicos diferentes podem compartilhar densidade média.

**Segundo cenário didático:** trânsito de profundidade 0,0025 implica `R_p/R_*=√0,0025=0,05`. Sem raio da estrela, o raio absoluto do planeta não foi medido.

**Terceiro cenário:** medição Doppler revela período e `M_p sin i`. Um modelo inclui i=90°, outro i=30°; `sin(30°)=0,5`. A massa verdadeira no segundo pode ser o dobro do valor mínimo no regime de pequenas massas, desde que os demais parâmetros e aproximações sejam comparáveis. Um trânsito com i suficientemente elevado reduziria a ambiguidade.

**Incerteza:** para `ρ∝M R^{-3}`, pequenos erros independentes levam aproximadamente `(σρ/ρ)²≈(σM/M)²+9(σR/R)²`. Se M e R são correlacionadas, adicionar termo covariante. Não usar porcentagem ilustrativa como resultado de arquivo real.

## 9. A NASA Exoplanet Archive não é um único gabarito imutável

O arquivo NASA permite encontrar múltiplas soluções publicadas para planeta e estrela. A tabela *Planetary Systems (PS)* registra soluções e referências por sistema, enquanto tabelas de parâmetros compostos favorecem completude mas podem reunir soluções que não foram ajustadas conjuntamente [X2]. Consequências:

- O raio da estrela e do planeta de estudos diferentes não podem ser combinados mecanicamente sem conferir coerência de parâmetros;
- parâmetros ausentes são informação sobre método/estudo, não prova de planeta inexistente;
- datas de atualização, autoria e status candidato/confirmado são parte da evidência;
- contagem histórica de exoplanetas muda com novas confirmações e revisões;
- estatística de ocorrência requer função de detecção/completude e viés geométrico, não a soma bruta da lista.

**Regra de origem de dado:** registrar ID do objeto, publicação, instrumentos, método, tabela, data de consulta e solução escolhida quando outro agente gerar fichas na main. Não usar APIs de IA para treinar o CRIVO; consultar repositório astronômico de dados não equivale à instalação de modelo de linguagem.

## 10. Matriz de raciocínio para curadoria futura

| Enunciado imprudente | Correção que exige explicação |
| --- | --- |
| 'Transitamos um planeta, portanto sua massa está conhecida' | Trânsito costuma dar raio relativo/órbita, e massa requer outras observações ou TTV sob modelo. |
| 'Uma oscilação Doppler fornece massa exata' | Sem inclinação, mede combinação `M sin i` em regime usual. |
| 'O planeta não transitou, portanto não existe' | Orientação geométrica e completude impedem conclusão. |
| 'Um planeta foi fotografado, então sabemos seus continentes' | Imagem direta atual geralmente separa ponto de luz e bandas, não geografia de superfície. |
| 'Microlente sempre se repete a cada órbita planetária' | Evento depende de alinhamento transitório de múltiplos corpos. |
| 'A atmosfera contém água, logo a superfície tem oceanos e vida' | Vapor e composição não demonstram estado de superfície/habitabilidade real. |
| 'Uma estrela menos brilhante implica planeta menor' | Profundidade relativa e raio estelar entram em inferência. |
| 'Há muitos planetas quentes no catálogo, logo o Universo só forma planetas quentes' | Seleção e eficiência de detecção variam por método. |

Esses exemplos editoriais não devem ser reaproveitados como prova cega do CRIVO. A avaliação independente deve ter formulações inéditas e controle de respostas sem evidência.

## 11. Fontes verificadas e limites de reutilização

| Ref. | Publicação ou documentação | Papel científico |
| --- | --- | --- |
| X1 | NASA Science, *How We Find and Characterize*: https://science.nasa.gov/exoplanets/how-we-find-and-characterize/ | Procedimentos gerais de trânsito, Doppler, microlente, imagem direta e espectroscopia; divulgação, sem substituição de artigos de inferência. |
| X2 | NASA Exoplanet Archive, *About Planetary Systems Table*: https://exoplanetarchive.ipac.caltech.edu/docs/planetarysystems_about.html | Tabela PS, versões de soluções, status e referências; não presumir independência de parâmetros compostos. |
| X3 | NASA Science, *Planetary Transits*: https://science.nasa.gov/exoplanets/planetary-transits/ | Geometria, periodos e detecção, com condição de alinhamento. |
| X4 | NASA Exoplanet Archive, *Statistics and candidates*: https://exoplanetarchive.ipac.caltech.edu/docs/counts_detail.html | Contagens dependem do método e atualização, não taxa universal de ocorrência. |
| X5 | NASA Science, *Radial Velocity*: https://science.nasa.gov/exoplanets/radial-velocity/ | Efeito Doppler e relação massa orbital, no nível introdutório. |
| X6 | NASA Science, *Gravitational Microlensing*: https://science.nasa.gov/exoplanets/gravitational-microlensing/ | Alinhamento gravitacional e seleção. |
| X7 | NASA Science, *Direct Imaging*: https://science.nasa.gov/exoplanets/direct-imaging/ | Contraste, bandas e fatores de seleção. |
| X8 | ESA/Gaia, *Gaia DR3 documentation*: https://gea.esac.esa.int/archive/documentation/GDR3/ | Astrometria, paralaxe e movimentos, não base de massa planetária automática. |
| X9 | NASA/Webb, *Spectroscopy 101*: https://science.nasa.gov/mission/webb/science-overview/science-explainers/spectroscopy-101-beyond-temperature-and-composition/ | Espectros, condições físicas e limitações. |
| X10 | NASA Science, *The Search for Life*: https://science.nasa.gov/exoplanets/search-for-life/ | Zona habitável, biossinais e ressalvas; material institucional. |
| X11 | NASA Exoplanet Archive, *About Composite Planet Table*: https://exoplanetarchive.ipac.caltech.edu/docs/composite_about.html | Maior completude pode significar menor consistência interna que uma solução única. |

**Direitos:** texto autoral em português sem reprodução de imagens, artigos integrais, tabelas completas, catálogos ou dados privados; links NASA/ESA e produtos ligados a terceiros têm direitos próprios. Conferir política de mídia NASA https://www.nasa.gov/nasa-brand-center/images-and-media/ antes de reutilizar figuras/identidade. O arquivo contém fórmulas e exemplos hipotéticos, não confirmação nova de planeta.

## 12. Pendências após este documento

A área de exoplanetas foi ampliada no acervo, mas ainda restam excentricidades e sistemas multiplanetários modelados quantitativamente, levantamentos de ocorrência com completude corrigida e estudos de atmosfera de objetos individuais com literatura primária atual. **Nenhum módulo foi marcado pronto só por existir esta revisão.** O outro agente decide integração, controles cegos, CI e treinamento; nenhum arquivo da main, pesos ou código foi modificado.
