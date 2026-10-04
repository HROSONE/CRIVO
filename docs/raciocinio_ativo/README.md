# Compreensão e raciocínio ativo — 04/10/2026

O chat padrão ganha um motor próprio para manipular hipóteses explícitas e um
explorador que recombina evidências do acervo. Não exige GPU, retreino ou pesos
externos; não acrescenta parâmetros neurais. O classificador e as redes próprias
existentes continuam com seus papéis. O Transformer experimental continua sujeito
às avaliações do laboratório.

## Raciocínio com memória de trabalho

Comece com afirmações e condições separadas por ponto e vírgula:

> Considere estas premissas: a bateria tem carga; se a bateria tem carga e o circuito está fechado, então a luz acende

Depois pergunte:

- `Posso concluir que a luz acende?` — diferencia conclusão sustentada, negada,
  indeterminada e base inconsistente.
- `O que falta para concluir que a luz acende?` — procura conjuntos coerentes
  de até três suposições suficientes, sem assumir o próprio objetivo.
- `Acrescente a premissa: o circuito está fechado` — recalcula as consequências.
- `Corrija a premissa: o circuito não está fechado` — substitui uma afirmação
  assumida desse nome e remove conclusões que perderam apoio.
- `Retire a premissa: a bateria tem carga` — retira uma premissa explícita.
- `Que hipóteses você sugere?` — explora consequências possíveis das regras.
- `E se o circuito não está fechado?` — testa um ramo temporário; não altera
  as premissas originais. Esse ramo conserva as implicações, portanto não é
  um modelo causal nem uma intervenção causal.
- `O que você conclui?` — mostra consequências adicionais sustentadas.
- `Limpar hipótese` — descarta a memória de trabalho dessa hipótese.

`raciocinio_ativo.py` representa afirmações positivas/negativas e condições `e`
ou `ou`, enumera mundos booleanos compatíveis e consulta todos eles. A análise
produz as premissas usadas, contraexemplos quando disponíveis e hipóteses
suficientes. Uma contradição bloqueia a conclusão e mostra um conjunto de
premissas em conflito; não permite concluir qualquer coisa. A explicação usa
um subconjunto irredutível por remoção, não promete o menor subconjunto possível.

Limites deliberados: dez afirmações diferentes, dez turnos de inatividade,
dezesseis premissas, três condições por regra e orçamento de busca. A sintaxe
é explícita; quantificadores, condições vagas, duplas negações e precedência
ambígua pedem esclarecimento. Nomes equivalentes por significado não são
deduzidos. Esta etapa executa lógica proposicional exata sobre a interpretação
aceita, sem certificar compreensão geral de português.

O grafo factual mantém seu papel: `Posso concluir que pinguim é um ser vivo?`
sem hipótese ativa consulta relações cadastradas. Premissas do usuário não
modificam grafo, currículo ou arquivos de conhecimento. Código e protocolo de
crise mantêm prioridade. As hipóteses antigas de relações universais continuam
no motor anterior.

## Exploração do conhecimento

`Explore ideias sobre sono`, `Explore ideias sobre sono e ritmo circadiano`
e `Mais ideias` selecionam perguntas de investigação com trechos inteiros e
fontes. `Quais fontes?` mostra as referências dos trechos usados.

O explorador combina três operações: ligações/comparações editoriais explícitas,
comparações sugeridas por termos compartilhados entre unidades factuais e
investigações dos mecanismos, condições e limites de uma unidade. A associação
lexical nunca é apresentada como relação comprovada ou causalidade. Todas as
propostas continuam não verificadas. Não executa experiências, pesquisa na web
ou descoberta científica. Até três propostas por turno e doze por exploração,
sem repetir a mesma proposta; os conceitos precisam ser nomes inteiros e únicos.

## Compreensão do catálogo

O interpretador de perguntas agora usa os aliases resolvidos do compositor.
Preferências editoriais não são desfeitas ao reconstruir o índice. Ambiguidades
reais e qualificadores continuam exigindo esclarecimento; símbolos em `C++`
e `C#` continuam distintos. Ensinar recompõe o índice a partir do novo catálogo.

## Uso efetivo e rastros

As capacidades ficam ligadas na construção padrão do Crivo, inclusive pela
API e pelo replay do histórico. `reasoning` contém a operação, estado,
premissas e demonstrações dentro da hipótese. `knowledge_exploration` contém
propostas e suas evidências. Ambos indicam `comprovado_no_mundo: false`.
`has_proof` não marca essas operações como provas factuais. Os campos só
aparecem no turno que realmente usou o motor, evitando rastros herdados.

O status HTTP informa as capacidades ativas e o SHA público da compilação
quando disponibilizado pela hospedagem. O site distingue “Raciocínio sob
premissas” de “Exploração de ideias” e oferece exemplos executáveis.

## Verificação

Quinze diálogos de desenvolvimento foram escritos antes da implementação em
`avaliacoes/raciocinio_ativo_v1/dev.json`. O registro da versão anterior está
em `baseline.json`, e `resultado.json` registra os resultados novos e hashes.
O acerto nesses casos testa esse contrato delimitado, não inteligência geral.

Há também um oráculo independente: 45 teorias sorteadas com nomes opacos,
implicações, conjunções, disjunções e sinais positivos/negativos são avaliadas
por atribuições booleanas diretas. Os estados e o apoio das provas do motor
devem coincidir. Hipóteses de abdução são verificadas separadamente quanto à
consistência e suficiência. Outros testes cobrem revisão, expiração, histórico,
fontes, limites, prioridades e ausência de contaminação do conhecimento.

```bash
python -m unittest testes_raciocinio_ativo testes_integracao_raciocinio_ativo testes_exploracao_conhecimento -v
python -S -m unittest testes_raciocinio_ativo testes_integracao_raciocinio_ativo testes_exploracao_conhecimento -v
python scripts/avaliar_raciocinio_ativo.py --saida /tmp/raciocinio-ativo.json
```

O workflow dedicado executa esse contrato e regressões, e publica o diagnóstico.
O CI geral também descobre os novos testes nas três versões de Python.

## Próxima evolução

O próximo problema é interpretar mais variações de linguagem mantendo o sentido
das condições, sem depender de fórmulas de comando. Para isso, a rede própria
precisa aprender quadros de afirmações, regras e objetivos, usando pares de
frases equivalentes e não equivalentes, nomes inéditos e contraexemplos. A lógica
atual pode gerar supervisão verificável, mas a avaliação deve reservar famílias
e combinações antes do treino. Escalar a rede fica condicionado a ganhos nesses
testes; aumentar parâmetros, por si só, não demonstra compreensão.
