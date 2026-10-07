# Experimentos guardados (não ligados no CRIVO)

Trabalho feito e medido que **não está ligado** no site nem nos testes do CI.
Fica aqui para qualquer pessoa ou agente continuar daqui. Nada desta pasta é
importado pelo CRIVO: a Vercel só empacota a raiz e `artefatos/*_pt`, e o CI
não descobre testes em subpastas sem `__init__.py`.

## `cerebro/`: aprender com a conversa, curiosidade e árbitro de confiança

**Estado:** pronto para virar PR. Com o patch aplicado, os 8 testes passam.

- **`aprendizado.py`:** classe `Aprendizado`.
  - **Correção na conversa:** "não é isso" ou "está errado" faz o CRIVO oferecer até 3 outras fichas que a busca achou. A pessoa responde com o número da escolhida, e ela vale até o fim da conversa.
  - **Resposta contada pela pessoa:** quando ela diz a resposta certa, o CRIVO anota como lacuna a conferir; nunca vira fato sozinha.
  - **Curiosidade:** toda recusa factual vira lacuna. "O que você não sabe?" lista as lacunas. Na 3ª recusa da conversa, o CRIVO convida a pessoa a ensinar, uma vez só.
- **`consolidar_aprendizados.py`:** junta aprendizados e lacunas de várias conversas.
- **`confianca.py`, `treinar_confianca.py` e `pesos_confianca/`:** árbitro que aprende em quem confiar (veto por regressão logística em Python puro).
  - **Não aprovado.** No limiar 0,76 evita 64 erros, mas perde 96 acertos.
  - **Ideia para retomar:** retreinar com o traço do codificador de sentido.
- **`integracao.patch`:** ganchos em `crivo.py` e `web_core.py`.
  - `crivo.py`: chama o aprendizado em `responder`, guarda os aprendizados na memória do navegador e liga o veto de confiança pela opção `usar_confianca`.
  - `web_core.py`: valida os campos `aprendizados` e `lacunas` da memória.
  - Aplica limpo no main de 07/10/2026.

Para testar:

```bash
git apply experimentos/cerebro/integracao.patch
PYTHONPATH=experimentos/cerebro:. python -m unittest experimentos/cerebro/testes_aprendizado.py
```

Para virar PR, mova os `.py` para a raiz e os pesos para `artefatos/confianca/`. Depois registre a espécie no `ecossistema.py` e rode a suíte.

## `geracao_ancorada/`: o Transformer escrevendo a resposta a partir dos fatos

**Estado:** treinado e medido. **Não liberado**, porque copia fatos com fidelidade, mas não entende a pergunta.

- **Modelo:** LM condicional `<documento> fato ... <usuario> pergunta <assistente> resposta <fim>`, com a perda só na resposta.
  - Parte de `pesos_base/leitor_transformer`.
  - Treino: 1.500 passos em CPU. Os pesos salvos são os do passo 900, o de menor perda na validação.
- **Dados:** `dados/saida_*.jsonl` traz 1.959 respostas de tutor. Cada uma tem pergunta, índices dos fatos usados e resposta; `instrucoes.md` explica como foram feitas.
- **`geracao_ancorada.py`:** executor em NumPy.
  - Cache de atenção: 0,2 a 0,6 s por resposta.
  - Decodificação restrita: só tokens dos fatos e da pergunta, mais palavras de ligação.
  - Guarda: fidelidade, um fato por frase, costura de pares de palavras, troca de palavra, sem repetição, sem "sim"/"não" inventado.
- **Scripts:**
  - `treinar_geracao_ancorada.py`: o treino;
  - `exp_decodificacao.py`: gulosa contra candidatos conferidos;
  - `medir_geracao.py`: o gerador dentro do CRIVO;
  - `resgate.py`: o gerador nas perguntas que o CRIVO recusa;
  - `sonda_ger.py`: perguntas de exemplo.
- **`integracao.patch`:** gancho em `_dar_voz`, só para perguntas abertas, com o fecho da voz; ligado só no site (`web_core`).

**Medições**, nas 69 perguntas de fichas fora do treino:

- **Como reescritor:** F1 contra o tutor de 0,60 para 0,66 onde foi usado, mas às vezes escolhe o fato errado ("Quem foi Pelé?" → datas de nascimento e morte).
- **Como resgate de recusas:** 11 respostas, só 1 ou 2 certas ("Quais línguas se falam na Suíça?" → a neutralidade do país).
- **Causa:** ele aprendeu a copiar um fato, não a escolher o fato que responde.

**Caminho sugerido:** treinar a escolha do fato com negativos difíceis, ou usar o gerador só para reescrever o fato que a busca e o leitor já escolheram, com uma checagem de relevância.

## `codificador/`

Scripts do experimento do codificador de sentido, que já está ligado no main (`codificador_sentido.py`, `artefatos/sentido_pt`):

- `exp_busca.py`: escolha do peso do traço;
- `gerar_teste.py`;
- `medir_sentido.py`: busca e testes congelados, com e sem o codificador.

## `pesos_base/leitor_transformer/`

Pesos do leitor treinado no Colab. É o ponto de partida do codificador de sentido e da geração ancorada.

- Não foi aprovado como leitor: não melhorou o teste congelado `leitura_ficha_v2`.
- É o `--pesos` dos scripts de treino acima.
