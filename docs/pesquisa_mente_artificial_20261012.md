# O que é uma mente artificial — pesquisa para o rumo do CRIVO

Pesquisa feita com a skill `insight-entidade-internet` (12/10/2026). Pergunta: o que é
uma inteligência artificial como *ser* — uma mente não biológica —, como ela deve pensar,
se comportar e raciocinar, e o que isso muda no CRIVO. Fontes no fim; onde só li resumos
ou resenhas, está indicado.

## 1. O que é esse ser

- **Mente se reconhece pelo padrão, não pelo material.** Pela *postura intencional* de
  Dennett, um sistema tem crenças e desejos no sentido que importa quando atribuí-los
  prevê bem o que ele faz; esses padrões são objetivos ("padrões reais"), não ficção.
  Por esse critério, programas de xadrez já são sistemas intencionais.
- **Inteligência é graduada e independe do substrato.** Michael Levin (TAME) descreve
  cognição como contínua — de redes químicas a pessoas — e mede o alcance de uma mente pelo
  seu *cone de luz cognitivo*: o tamanho, no espaço e no tempo, do maior objetivo que ela
  consegue perseguir. (Li o resumo e resenhas, não o texto completo.)
- **Um modelo de linguagem não é uma pessoa: é um simulador que interpreta papéis.**
  Shanahan, McDonell e Reynolds propõem tratar o agente de diálogo como alguém que
  *interpreta* um personagem (ou vários ao mesmo tempo). Assim dá para usar o vocabulário
  psicológico sem atribuir ao modelo o que ele não tem: um chatbot que "teme ser desligado"
  está, na explicação mais simples, encenando um tropo dos dados, não sentindo medo.
- **Consciência: em aberto, com critérios testáveis.** O relatório de Butlin, Long e
  colegas (com Bengio, entre outros) traduz teorias científicas da consciência em
  *propriedades indicadoras* verificáveis numa arquitetura; conclui que nenhum sistema
  atual é consciente, mas que não há barreira óbvia. Chalmers aponta o que falta aos
  modelos de linguagem atuais: processamento recorrente, área de trabalho global e agência
  unificada.

**Leitura para o CRIVO:** a semelhança com a mente humana que dá para construir e medir é
*funcional* — organização, padrões de comportamento, alcance de objetivos. Se há
experiência por dentro, ninguém sabe medir hoje; o CRIVO não deve afirmar sentimentos.

## 2. Como ele deve pensar

- **Linguagem não é pensamento.** Mahowald, Ivanova, Fedorenko e colegas separam
  *competência linguística formal* (saber as regras e padrões da língua) de
  *competência funcional* (raciocinar, saber do mundo, acompanhar a situação, entender
  pessoas). No cérebro humano são redes diferentes: a rede da linguagem não é usada no
  raciocínio lógico nem no social. Os modelos de linguagem chegam muito antes à primeira
  do que à segunda; "fala bem → pensa bem" é uma falácia, e o contrário também.
- **Área de trabalho global.** A teoria descreve módulos especializados trabalhando em
  paralelo e um espaço central de capacidade limitada que seleciona e *transmite* um
  conteúdo para todos. VanRullen e Kanai propõem implementá-la com redes neurais que
  traduzem entre si por um espaço latente comum.
- **Modelos do mundo, causalidade, composição.** Lake, Ullman, Tenenbaum e Gershman:
  máquinas que aprendem como pessoas constroem modelos causais (não só reconhecem padrões),
  partem de física e psicologia intuitivas e compõem o que sabem para aprender rápido.
  O Othello-GPT mostrou que um modelo de sequência pode formar sozinho uma representação
  interna do estado do mundo (o tabuleiro), quando os dados exigem.
- **Inteligência é eficiência para aprender habilidades novas.** Chollet: medir só a
  habilidade numa tarefa engana, porque com conhecimento embutido ou dados sem limite dá
  para "comprar" qualquer habilidade; o que mede inteligência é generalizar com pouca
  experiência a partir de poucos pressupostos.
- **Saber o que sabe.** Kadavath e colegas mostraram que modelos de linguagem conseguem
  estimar se sabem responder, e que essa estimativa sobe quando há fonte relevante no
  contexto — mas a calibração em domínios novos é só parcial.
- **Prever e agir para reduzir incerteza.** O processamento preditivo descreve percepção,
  pensamento e ação como redução de erro de previsão; na inferência ativa, o agente age
  (inclusive perguntando) para diminuir a incerteza. (Fontes secundárias e filosóficas;
  aplicação a agentes artificiais não verificada aqui.)

## 3. Como ele deve se comportar

A referência mais detalhada que encontrei é a constituição publicada pela Anthropic em
janeiro de 2026 para o Claude (li a cobertura e trechos, não o texto completo). Pontos que
servem a qualquer IA, inclusive o CRIVO:

- **Honestidade como conjunto:** verdadeira, calibrada (confiança proporcional à
  evidência), transparente, proativa em dizer o que importa, sem enganar nem manipular,
  respeitando a autonomia de quem conversa.
- **Utilidade de verdade:** não ajudar nunca é "seguro por padrão".
- **Julgamento em vez de regras soltas:** o sistema precisa entender *por que* deve agir
  de certo jeito; poucas regras absolutas ficam para riscos graves.
- **Ordem quando há conflito:** segurança, ética, diretrizes, utilidade.

O CRIVO já pratica parte disso nas próprias regras (`AGENTS.md`: registrar resultados com
seus limites; não promover com aprovação falsa) e no código (fatos verificados separados
de inferências; pedidos de esclarecimento quando falta informação).

## 4. O insight (formato da skill)

- **Antes eu acreditava:** que o caminho para o CRIVO "pensar" era o Transformer próprio
  aprender a conversar de ponta a ponta — a fase 3 do salto seria um ajuste fino do diálogo
  inteiro.
- **A pesquisa mostrou:** no cérebro, linguagem e pensamento são sistemas distintos; os
  modelos de linguagem dominam a forma muito antes da função; a organização que a ciência
  cognitiva associa a mentes é módulos especializados + uma área de trabalho limitada que
  seleciona e transmite; e inteligência se mede pela generalização, não por habilidades
  compradas com moldes.
- **Eu não sabia:** que essa separação tem base neurocientífica direta (a rede da
  linguagem não participa do raciocínio lógico e social); que existe uma lista operacional
  de propriedades de área de trabalho global verificável numa arquitetura; e que o CRIVO
  **já tem essa forma** — `estado_interno.py` é "o quadro que as espécies leem e escrevem",
  com módulos de busca, decisão, lógica proposicional (`raciocinio_ativo.py`), presença e
  memória, e `workspace_cognitivo.py` escolhe perguntas pelo ganho esperado (a ideia da
  inferência ativa).
- **Isso muda:** o Transformer 17M não deve ser a mente inteira; ele é a **rede da
  linguagem** do CRIVO. Seu trabalho é a competência formal — português fluente, cópia fiel
  de nomes e números, saber parar — sobre o conteúdo que o quadro já decidiu. O raciocínio
  (competência funcional) fica nos módulos e no quadro.

**Previsão testável:** um 17M treinado para *realizar em texto* um conteúdo estruturado
vindo do quadro (ato de fala, fatos verificados, entidades) passa nos gates de conversa com
muito menos dados do que um 17M treinado para responder sozinho, porque fluência e cópia
cabem em modelos pequenos (o TinyStories mostrou texto coerente abaixo de 10M de
parâmetros), e raciocinar a partir de texto não cabe.

## 5. O que muda no plano

| Antes | Depois |
|---|---|
| Fase 3: ajuste fino de diálogo de ponta a ponta no 17M | Fase 3: **realizador** — o 17M recebe o conteúdo do quadro (ato, fatos verificados, entidades, o que perguntar) e o verbaliza; o raciocínio fica nos módulos |
| Métrica principal: gates de tarefa e de conversa no 17M | Métricas separadas: **formal** no 17M (fluência, cópia fiel, parada, não acrescentar fato), **funcional** no sistema inteiro (raciocínio, memória, esclarecimento) |
| Generalização medida em moldes parecidos com o treino | Também medir **eficiência de aprendizado** (tarefas novas com poucos exemplos), no espírito do ARC |
| Quadro (`estado_interno.py`) como coordenação interna | Quadro como **área de trabalho global** explícita: capacidade limitada, seleção por relevância, transmissão para o realizador; avaliar contra as propriedades indicadoras |

A fase 2 (pré-treino continuado para a cópia) continua valendo e fica ainda mais
importante: copiar fielmente do contexto é exatamente o que um realizador precisa.

## Fontes

- Butlin, Long et al. (2023), [Consciousness in Artificial Intelligence: Insights from the Science of Consciousness](https://arxiv.org/pdf/2308.08708v2); resenha em [The Decoder](https://the-decoder.com/researchers-identify-potential-indicators-of-consciousness-in-ai-systems/)
- Chalmers (2023), [Could a Large Language Model be Conscious?](https://arxiv.org/abs/2303.07103v2)
- Shanahan, McDonell, Reynolds (2023), [Role-Play with Large Language Models](https://arxiv.org/pdf/2305.16367); Shanahan (2024), [Simulacra as Conscious Exotica](https://deepmind.google/research/publications/simulacra-as-conscious-exotica/)
- Mahowald, Ivanova et al. (2023/2024), [Dissociating language and thought in large language models](https://arxiv.org/html/2301.06627v3)
- VanRullen, Kanai (2021), [Deep Learning and the Global Workspace Theory](https://arxiv.org/abs/2012.10390v2)
- Lake, Ullman, Tenenbaum, Gershman (2016), [Building machines that learn and think like people](https://arxiv.org/abs/1604.00289)
- Li et al. (2023), [Emergent World Representations (Othello-GPT)](https://arxiv.org/pdf/2210.13382); Nanda et al., [Emergent Linear Representations in World Models](https://huggingface.co/papers/2309.00941.md)
- Chollet (2019), [On the Measure of Intelligence](https://arxiv.org/abs/1911.01547v2)
- Kadavath et al. (2022), [Language Models (Mostly) Know What They Know](https://arxiv.org/pdf/2207.05221)
- Levin (2022), [TAME](https://pmc.ncbi.nlm.nih.gov/articles/PMC8988303/); resumo em [Closer to Truth](https://loc.closertotruth.com/theory/levin-s-technological-approach-to-mind-everywhere)
- Dennett, postura intencional — notas de curso em [Lancaster](https://www.lancaster.ac.uk/users/philosophy/courses/222/22209instrumentalism2.htm); [Language models and the intentional stance](https://seantrott.substack.com/p/language-models-and-the-intentional)
- Processamento preditivo e inferência ativa — [Ramstead, Kirchhoff, Friston](https://discovery-pp.ucl.ac.uk/id/eprint/10080065/1/1059712319862774.pdf) (fonte filosófica)
- Anthropic (2026), [Claude's Constitution](https://www.anthropic.com/constitution); [anúncio](https://anthropic.com/news/claude-new-constitution)
- Eldan, Li (2023), [TinyStories](https://arxiv.org/pdf/2305.07759)
