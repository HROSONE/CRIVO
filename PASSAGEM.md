# Passagem de trabalho: estado em 07/10/2026, 08:20 UTC

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
