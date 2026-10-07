# Passagem de trabalho — 07/10/2026

## Piloto treinado: resultado negativo para geração de provas

Branch `codex/piloto-raciocinio-generativo`, sobre a investigação do PR #108.
Dois ajustes dos pesos próprios, 400 atualizações por variante em CPU. Controle
direto: 50/56 classificações no teste. Modelo por passos: 27/56 classificações
e 0/28 provas completas necessárias; nenhum passo aceito no teste selecionado.
O executor NumPy reproduziu os resultados. Pesos experimentais preservados em
`experimentos/raciocinio_generativo/pesos_piloto`, não aprovados para o chat.
Oito contratos passaram. Dados, código e critérios de seleção estão registrados
em `docs/piloto_raciocinio_generativo_20261007.md`. Não ajustar usando o teste
deste piloto e continuar chamando-o de cego. O diagnóstico posterior aponta
para avaliar seleção de regras/apoios separadamente de redação e término.

## Investigação: geração e raciocínio aprendido

Branch `codex/diagnostico-gerativo`: aplicação da skill fornecida pelo usuário,
pesquisa em fontes primárias e seis sondas dos pesos atuais, incluindo ablação
de restrições. Remover as restrições não demonstrou resolver a composição de
dois passos ou resumo seletivo. Verificador experimental de passos com apoios
explícitos passou em seis contratos, com e sem NumPy; ainda não há modelo
treinado para gerar esses passos. Diagnóstico, evidências e critérios do
próximo experimento em `docs/diagnostico_generativo_20261007.md`.
Não altera o chat nem aprova novos pesos.

## Continuação: PR #104

[PR #104](https://github.com/HROSONE/CRIVO/pull/104), branch `codex/geracao-integrada`, sobre o #103. A implementação liga o gerador próprio por padrão no Crivo, no adaptador web e na API. Retira o resgate de recusas e usa somente evidências já verificadas pelo leitor/compositor. Mantém IDs, contexto, fontes e histórico; comparação seguida de resumo preserva os dois temas. A guarda também confere omissões, valores, negações e siglas. Acervo vazio deixa de causar erro no codificador.

A comparação completa terminou: oito avaliações sem regressão nas classes/áreas, 281 de 863 turnos com saída do gerador, 98,6% dessas saídas como cópia literal. Os 80 testes iniciais passaram e mais 44 testes de geração/conversa passaram após corrigir as regressões do CI. O fluxo completo no navegador passou para comparação DNA/RNA → resumo → fontes. A comparação de qualidade com/sem geração está registrada em `docs/geracao_integrada_20261007.md` e nos agregados associados. O workflow `geracao-ancorada.yml` passa a exigir essa comparação, com os classificadores originais e sem publicar os casos congelados.

**Limite:** ligar o Transformer não o torna um gerador geral. Os pesos existentes frequentemente copiam a fonte, e a restrição atual favorece essa cópia. O diagnóstico e a interface identificam esse comportamento. Nenhum novo peso foi treinado ou aprovado. Veja o documento para o critério do próximo treino.

A prévia Vercel exige autenticação; os conectores retornaram 403 e a validação remota não foi concluída. A implementação foi validada localmente. A entrega à main é feita pelo PR #104, que reúne também os commits e pesos do #103. Consulte o estado do PR para confirmar a integração.

## Histórico do PR #103, registrado às 08:20 UTC

Nota para quem continuar (pessoa, Claude ou Codex). Tudo o que existia só no servidor da sessão do Claude já está neste repositório.

## Já no main
- **PR #101:** 8 catálogos novos, com 269 conceitos.
  - A rede de intenções não se desliga mais quando o acervo cresce.
  - Mecanismos novos de busca e leitura das fichas.
- **PR #102:** codificador de sentido, o Transformer próprio dentro da busca.
  - Arquivos: `codificador_sentido.py`, `artefatos/sentido_pt`.
  - Quando os catálogos mudarem, rode `scripts/instalar_sentido.py`.

## Em andamento: PR #103 (rascunho)
Branch `ccr-989352a3-gk30in`. O PR traz quatro coisas.

1. **`experimentos/`:** trabalho guardado, não ligado. Veja `experimentos/README.md`.
   - "Cérebro": aprender com a conversa, curiosidade e árbitro de confiança. Pronto: com o `integracao.patch`, os 8 testes passam.
2. **Geração ancorada v2:** o principal pedido do dono do projeto.
   - O CRIVO escolhe a ficha e a busca escolhe o fato, com confiança de pelo menos 0,5.
   - O Transformer escreve a resposta só a partir desse fato (`geracao_ancorada.py`, pesos em `artefatos/geracao_pt`).
   - A guarda confere fidelidade, números no lugar certo, nome próprio em "quem", começo de resposta e repetição.
   - Ganchos: `Crivo._escrever_com_geracao` (`crivo.py`) e `voz.fecho_com_oferta` (`voz.py`).
   - **DESLIGADA no site** (`api/chat.py` passa `usar_geracao=False`), porque a medição completa mostrou piora (abaixo). O código, os pesos e os testes ficam prontos. Em `Crivo` e `responder_web` o padrão também é desligado.
   - Testes: `testes_geracao_ancorada.py`, 13 passam.
   - **Medição parcial:** nas 69 perguntas de validação do tutor, entregando a ficha certa, o fato certo foi escolhido em 59, 55 respostas foram geradas e o F1 subiu de 0,398 para 0,62. Script: `experimentos/geracao_ancorada/v2_selecao.py`.
   - **Medição no CRIVO completo (sem → com geração), feita em 07/10, 08:20:**

     | Avaliação | Sem | Com |
     |---|---|---|
     | Tutor (69 perguntas): F1 | 0,398 | 0,436 (22 respostas geradas) |
     | Lacunas, teste: certo / errado | 85 / 12 | 81 / 22 |
     | Lacunas, dev: certo / errado | 159 / 4 | 152 / 12 |
     | Leitura v1, respondíveis: afirmou certo / errado | 23 / 1 | 25 / 7 |
     | Leitura v2, respondíveis: afirmou certo / errado | 12 / 2 | 19 / 8 |
     | Bateria dev: recusas corretas / inventou | 13 / 0 | 10 / 3 |
     | Bateria retido: recusas corretas / inventou | 10 / 0 | 6 / 4 |
     | Sem nome, teste | 29 / 7 | 29 / 7 |

   - **Diagnóstico:** o maior estrago vem do **caminho de resgate**. Quando o CRIVO recusa e a pergunta cita uma ficha, a busca escolhe um fato com confiança ≥ 0,5 e o gerador responde. Mas várias dessas recusas eram corretas: a pergunta não tem resposta na ficha. O fato escolhido é do assunto, mas não responde.
   - O controle em `artefatos/geracao_pt/meta.json` ainda diz "provisório"; troque para `aprovado: false` ou mantenha desligado no `api/chat.py`.
3. **`.vercelignore`:** o deploy de prévia falhou porque o repositório passou de 194 MB. Agora só o necessário vai para a Vercel (cerca de 124 MB). Confirme que a prévia ficou pronta.
4. **Testes antigos:** o `integracao` falhou com `geracao:dna`, porque a geração estava ligada por padrão no `responder_web`. Corrigido: agora o padrão é desligado.

## Próximos passos
1. Ver o CI e o deploy de prévia do PR #103 verdes.
   - O job `laboratorio` às vezes trava no sandbox do Node; não tem relação com estes PRs. Rode de novo pela interface do Actions.
2. O PR #103 pode ser integrado como está: a geração fica desligada no site. Para ligá-la depois:
   - tire o caminho de resgate em `Crivo._escrever_com_geracao` (gere só quando o CRIVO já respondeu com uma ficha) ou exija a confirmação do leitor;
   - suba `_CONFIANCA_GERACAO`;
   - meça de novo com e sem. O script está em `experimentos/geracao_ancorada/` e é o mesmo que gerou a tabela acima. Só ligue se nenhuma classe de erro piorar.
3. Depois: transformar `experimentos/cerebro` em PR. Mova os `.py` para a raiz, aplique o patch e registre a espécie no `ecossistema.py`.
