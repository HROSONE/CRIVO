# Diálogo cotidiano, contexto curto e conceitos básicos

A conversa cotidiana ainda apresentava falhas de intenção: vocativos
informais viravam assuntos factuais, críticas curtas não eram reconhecidas
e palavras ambíguas podiam responder sobre reciclagem num diálogo de
frustração. A correção trata atos completos e um contexto curto; não é um
treinamento de modelo generativo nem compreensão irrestrita de linguagem.

## Comportamento

- Uma saudação pode ter vocativos. A abertura é separada da consulta antes
  do planejador, preservando o conteúdo, os símbolos e a mensagem original
  no histórico usado pela API.
- Críticas dirigidas, pedidos para parar e desistência são atos distintos.
  Encerrar não força uma pergunta de continuidade. “Desisto” durante um
  exercício continua revelando a resposta da pergunta pendente.
- “Lixo” e “burro” isolados só viram críticas depois de um ato explícito de
  frustração nos últimos três turnos. Uma saudação, despedida ou reinício
  encerra esse contexto. Perguntas factuais, relatos, citações e código não
  são críticas só por conter essas palavras.
- Crise mantém precedência sobre todos esses caminhos. Nenhuma crítica
  transforma automaticamente o conteúdo da resposta anterior em fato falso.

## Conhecimento e fontes

Duas fichas textuais acrescentam ser humano e vácuo. Não acrescentam
classes à saída da rede principal: as 447 classes e os pesos próprios
continuam compatíveis. Os textos são sínteses autorais e permitem consulta
das fontes do conteúdo efetivamente exibido.

Fontes consultadas em 2026-10-04, todas com HTTP 200:

- [Smithsonian — Homo sapiens](https://humanorigins.si.edu/evidence/human-fossils/species/homo-sapiens): espécie dos humanos atuais, primatas, origem africana, ferramentas e cultura.
- [Smithsonian — Introduction to Human Evolution](https://humanorigins.si.edu/education/introduction-human-evolution): ancestralidade compartilhada com outros primatas.
- [CERN — A vacuum as empty as interstellar space](https://home.cern/science/engineering/vacuum-empty-interstellar-space/): baixa pressão, moléculas residuais e vácuo no LHC.
- [OpenStax — Maxwell’s Equations and Electromagnetic Waves](https://openstax.org/books/university-physics-volume-2/pages/16-1-maxwells-equations-and-electromagnetic-waves): luz eletromagnética que se propaga sem meio material.

As referências do Smithsonian e CERN estão marcadas como referência
bibliográfica, sem autorização de reprodução do texto original.

## Verificação

`avaliacoes/contato_contextual_v1/dev.json` foi registrado antes da
implementação. Os 14 casos são autorais de desenvolvimento, não uma
avaliação cega. `scripts/avaliar_contato_contextual.py` verifica IDs,
conteúdo esperado e conteúdo proibido via API com replay do histórico.

`testes_contato_contextual.py` verifica também expiração, reinício,
preservação de símbolos e mensagem original, variação de reparo, quiz,
prioridade de crise, citações e fontes. O workflow dedicado executa as
regressões com NumPy e sem dependências opcionais. O CI geral continua
executando os testes em Python 3.8, 3.11 e 3.13.

Conversas privadas usadas para diagnóstico local não integram o conjunto
público. Nenhum modelo externo, peso pré-treinado ou nova promessa de
inteligência geral foi acrescentado.
