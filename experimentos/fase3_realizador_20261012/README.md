# Fase 3 — o 17M como realizador do quadro

Fase 3 do salto (`experimentos/salto_17m_20261012/PLANO.md`). O Transformer próprio de
17M deixa de tentar ser a mente inteira e passa a ser a **rede da linguagem** do CRIVO:
o quadro (`estado_interno.py`) decide o ato e o conteúdo, e o 17M só transforma isso em
fala, no tom de `IDENTIDADE.md`, e para em `<fim>`. Motivo: `docs/pesquisa_mente_artificial_20261012.md`.

Nada aqui foi treinado em GPU ainda. **Os pesos resultantes não vão para o chat**: o
notebook grava `ativo_no_chat: false`, e a integração só acontece depois dos gates abaixo,
da porta conversacional (fase 4) e de um opt-in experimental como o #168 (fase 5).

## Formato (`formato_fase3.py`)

Mesmos tokens especiais da base, nenhum novo:

```
<documento> ato: registrar; relacao: amigo; nome: Pidedu <fim> <usuario> Tenho um amigo chamado Pidedu. <fim> <assistente>
→ Prazer, Pidedu! Fico feliz que você me contou sobre seu amigo. <fim>
```

A perda só conta na resposta e no `<fim>`. O mesmo módulo monta a entrada no gerador, no
notebook e, mais tarde, no runtime, para que treino e uso sejam idênticos.

Atos: `explicar`, `nao_sei`, `registrar`, `recordar`, `aceitar_correcao`, `acolher`,
`recusar`, `esclarecer`, `falar_de_si`, `saudar`.

## Dados (`gerar_fase3.py` → `dados_fase3.json`)

- Fatos de `explicar` vêm do acervo próprio do CRIVO (`Crivo().compositor.itens`); nomes
  são sílabas inventadas que não existem como palavra inteira no vocabulário (testa cópia,
  não memória).
- Respostas-alvo em templates no tom da identidade; **toda** resposta-alvo passa em
  `avaliar_saida` antes de entrar.
- Treino 4506 / dev 325 / blind 523. Nomes 600 / 60 / 100, disjuntos. O blind usa assuntos e
  nomes não vistos e a última variante de mensagem de cada ato, que nunca aparece no treino.
- SHAs em `manifesto.json`; o notebook recusa rodar se `dados_fase3.json` ou
  `formato_fase3.py` não baterem.

Para regenerar: `python experimentos/fase3_realizador_20261012/gerar_fase3.py` (precisa do
tokenizer do 17M; o resultado deve reproduzir os SHAs do manifesto).

## Treino (`notebooks/salto_17m_fase3_realizador_colab.ipynb`)

- Base: a exportação da fase 2 em `CRIVO/transformer-17m-continuo/base`.
- Ajuste fino completo, 1500 passos, lote 24 de SFT + 8 de replay do pré-treino (peso 0,5),
  lr 1e-4 com aquecimento de 100 passos.
- Avaliação no dev a cada 250 passos; o melhor checkpoint é escolhido pelo dev **entre os
  que preservam** a perda de LM (≤ 105% da base). Paciência 3.
- Saída em `CRIVO/transformer-17m-fase3`: `pesos.pt` (formato de `linguagem_profunda.carregar`),
  tokenizer e `resultado_fase3.json`.

## Gates (no blind, uma vez, no fim)

| Métrica | Mínimo |
|---|---|
| tudo ok | 85% |
| fatos fiéis (cada fato copiado sem alteração) | 90% |
| nome exato | 90% |
| terminou em `<fim>` | 95% |
| sem nome inventado | 95% |
| tudo ok em cada ato | 70% |
| perda de LM no pré-treino | ≤ 105% da base |

## Verificação feita (CPU, sem GPU)

- Simulação de ponta a ponta do notebook com uma base pequena falsa: carrega, treina,
  avalia, escolhe checkpoint e salva os três arquivos.
- Sobreajuste em 40 casos de treino com a arquitetura real: perda 0,001 e tudo ok 97,5%
  (fatos fiéis 75%) após 160 passos, com saídas como "Você tem razão, eu errei. O nome
  certo é Sale. Obrigado por me corrigir!" terminando em `<fim>`.

**Limites:** isso só mostra que o formato e a máscara da perda são aprendíveis e que o
código roda; não diz nada sobre generalização no blind. A cópia de fatos longos foi a parte
mais difícil no sobreajuste, e a sonda de nome na 2ª menção da fase 2 ainda oscila; se o
blind falhar em `fatos_fieis` ou `nome_exato`, o próximo passo é reforçar cópia de nomes em
frases reais nos dados, não baixar os gates.
