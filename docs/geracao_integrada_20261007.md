# Geração própria integrada — 07/10/2026

Implementação no PR #104, sobre o PR #103. O gerador utiliza os mesmos pesos autorais já existentes; não houve novo treino nem uso de um modelo externo.

## Fluxo em uso

`Crivo`, `responder_web` e `api/chat.py` usam geração por padrão. `Crivo(usar_geracao=False)`, `responder_web(..., usar_geracao=False)` e `web_local.py --sem-geracao` permitem medir o controle. No servidor local, `GET /api/chat` informa separadamente habilitação e disponibilidade do modelo.

O leitor/compositor escolhe as evidências e estabelece se há resposta. O Transformer escreve somente essas evidências, uma por passagem, até quatro. Não há nova busca para substituir a evidência nem resgate de uma recusa. Aproximações, provas, relações, código e consultas de fontes mantêm seus motores. Se uma passagem falha na guarda, a resposta inteira mantém o texto anterior.

A guarda verifica suporte, siglas de três letras, pares de palavras, números, identidade e repetição. Outra checagem impede omitir conteúdo, valores e negações da evidência. O começo de dois termos vem da fonte para preservar o sujeito; os tokens seguintes são preditos pelo Transformer. O cache contém pergunta e evidências completas e devolve cópias dos diagnósticos.

O ID semântico continua estável. Histórico, contexto textual e última resposta conversacional acompanham o texto mostrado. A redação substitui apenas os trechos factuais da resposta pronta, preservando títulos, conectores e ofertas de estudo. Uma simplificação já feita pelo compositor é mantida quando não há correspondência literal para a substituição. O replay do histórico também usa geração. Comparação seguida de resumo usa ambos os temas, e uma consulta de fontes apresenta as referências desses temas.

## O que medir

O campo `generation` expõe habilitação, uso efetivo, motivo de recuo, evidências, tentativas e rejeições. `texto_alterado` significa mudança na resposta final, incluindo formatação; não significa paráfrase. `copia_literal` informa se todos os segmentos produzidos estão literalmente nas fontes. A interface mostra “Modelo próprio · fatos da fonte” nesses casos.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/avaliar_geracao_ancorada.py --saida resultado.json
```

A avaliação usa os classificadores originais de sem nome, leitura v1/v2, bateria e lacunas, nos conjuntos disponíveis. Exporta somente agregados, inclusive áreas; não publica perguntas nem respostas dos conjuntos congelados. A execução retorna erro se alguma classe monitorada piorar. O workflow `geracao-ancorada.yml` roda essa comparação e publica o relatório. Resultados de saídas aprovadas pela guarda não são convertidos automaticamente em acertos.

## Validação da implementação

O teste interno `crivo.py --teste` passou em 65/65 casos. Sem NumPy, 26 testes executaram com sucesso (13 de inferência foram pulados). A suíte principal teve 80 testes aprovados, incluindo geração real com os pesos próprios, guardas, contexto, memória, API HTTP, codificador e raciocínio. Após corrigir as duas regressões encontradas pelo CI (oferta de estudo apagada e simplificação desfeita), 44 testes de geração e conversa passaram. O fluxo de navegador → API → modelo → interface passou novamente para comparação DNA/RNA, resumo e fontes, sem erros de JavaScript. Um processo novo com dez perguntas distintas no histórico respondeu em 7,8 s nesta máquina; isso não garante o mesmo tempo na Vercel.

A prévia anterior da Vercel foi publicada, mas exige autenticação. Os conectores de acesso retornaram 403. A validação remota não foi concluída; a proteção permaneceu ativa.

## Resultado da comparação completa

[Agregados e diagnóstico](resultados/geracao_integrada_20261007.json). As oito avaliações concluíram sem regressões nas classes e áreas monitoradas. O controle desligado também coincide com os agregados medidos na versão original antes desta integração. Não foram alterados classificadores, respostas esperadas ou os conjuntos congelados.

| Avaliação e métrica | Sem geração | Com geração | Turnos gerados |
|---|---|---|---|
| sem_nome_dev (certo / errado) | 22 / 1 | 22 / 1 | 6 |
| sem_nome_teste (certo / errado) | 29 / 7 | 29 / 7 | 6 |
| leitura_teste (afirmou certo / errado) | 23 / 1 | 23 / 1 | 22 |
| leitura_teste_v2 (afirmou certo / errado) | 12 / 2 | 12 / 2 | 13 |
| bateria_dev (acertos factuais / recusas corretas / invenções) | 117 / 13 / 0 | 117 / 13 / 0 | 85 |
| bateria_retido (acertos factuais / recusas corretas / invenções) | 55 / 10 / 0 | 55 / 10 / 0 | 45 |
| lacunas_dev (certo / errado) | 159 / 4 | 159 / 4 | 74 |
| lacunas_teste (certo / errado) | 85 / 12 | 85 / 12 | 30 |

Foram 863 turnos medidos com geração habilitada, 281 com saída do Transformer aceita e 869 tentativas registradas. 277 das 281 saídas aceitas (98,6%) foram cópias literais da evidência. 44 respostas finais mudaram, inclusive por formatação ou fecho; mudança textual não comprova paráfrase. Saídas que não são cópias literais também não demonstram, sozinhas, qualidade semântica ou geração ampla.

Os 15 diálogos da bateria dev e os 10 do conjunto retido permaneceram aprovados, e nenhuma invenção foi contada nessas duas baterias. A qualidade foi preservada; não houve ganho de acerto. A aprovação deste relatório é da integração restrita, não de capacidade generativa geral.

## Limite de capacidade e próximo treino

Esta integração torna o Transformer parte do caminho real, mas não demonstra capacidade generativa ampla. A restrição de pares de palavras e a preservação integral da evidência favorecem cópia. A formação de tópicos, títulos e parágrafos continua no compositor. Os pesos atuais e as guardas não sustentam geração livre, raciocínio aprendido nem paráfrases gerais.

A próxima versão precisa de treino e validação separados por tema, com pedidos de explicação, resumo, comparação e reformulação, mais negativos de perguntas sem resposta. Os conjuntos congelados permanecem fora do treino. O critério deve incluir atendimento ao pedido, preservação factual, capacidade de reformular e taxa de cópia literal; perda do modelo ou quantidade de respostas geradas não bastam. Uma guarda que aceite paráfrases precisará conferir relações e implicação factual antes de substituir a regra atual de pares. Nenhum novo peso foi marcado como aprovado nesta alteração.
