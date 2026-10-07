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
   - **Liga só no site:** `api/chat.py` passa `usar_geracao=True` quando a variável de ambiente `VERCEL` vale `1`. Em `Crivo` e `responder_web` o padrão é desligado, para os testes antigos medirem o texto de sempre.
   - Testes: `testes_geracao_ancorada.py`, 13 passam.
   - **Medição parcial:** nas 69 perguntas de validação do tutor, entregando a ficha certa, o fato certo foi escolhido em 59, 55 respostas foram geradas e o F1 subiu de 0,398 para 0,62. Script: `experimentos/geracao_ancorada/v2_selecao.py`.
   - **Falta medir no CRIVO completo**, com e sem a geração, nas avaliações: sem nome, leitura v1/v2, bateria e lacunas (testes congelados só por agregados). O controle em `artefatos/geracao_pt/meta.json` está marcado como **provisório**.
3. **`.vercelignore`:** o deploy de prévia falhou porque o repositório passou de 194 MB. Agora só o necessário vai para a Vercel (cerca de 124 MB). Confirme que a prévia ficou pronta.
4. **Testes antigos:** o `integracao` falhou com `geracao:dna`, porque a geração estava ligada por padrão no `responder_web`. Corrigido: agora o padrão é desligado.

## Próximos passos
1. Ver o CI e o deploy de prévia do PR #103 verdes.
   - O job `laboratorio` às vezes trava no sandbox do Node; não tem relação com estes PRs. Rode de novo pela interface do Actions.
2. Medir com e sem a geração nas avaliações. Script de exemplo: copiar `experimentos/codificador/medir_sentido.py`, ligando `Crivo.usar_geracao`.
   - Se nenhuma classe piorar: tirar "provisório" do `meta.json`, tirar o PR do rascunho e fazer o merge.
   - Se piorar: subir `_CONFIANCA_GERACAO` em `crivo.py` ou endurecer a guarda.
3. Depois: transformar `experimentos/cerebro` em PR. Mova os `.py` para a raiz, aplique o patch e registre a espécie no `ecossistema.py`.
