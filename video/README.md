# Vídeo: engenharia reversa, clones e o CRIVO

Vídeo de 73 s (1920×1080, 30 fps) feito em [Remotion](https://www.remotion.dev/), sobre a
semana de 6 a 13/10/2026 na engenharia reversa com agentes e sobre o que o CRIVO faz de
diferente. Cortes secos com clarão, zooms de câmera virtual, tremidas nos impactos e trilha
a 120 BPM (os cortes caem no tempo: 15 quadros por batida).

| Cena | Quadros | O que mostra |
| --- | --- | --- |
| Gancho | 120 | "ENGENHARIA REVERSA", os últimos 7 dias |
| REA | 330 | Reverse Engineer Anything: <10 mil → 115 mil+ estrelas em uma semana, MCP, Ghidra/IDA/Hopper |
| Binário | 240 | do binário ao código; 99% das funções de um jogo de tiro reconstruídas em C++ |
| Clones | 390 | ArtCraft (Brandon Thomas): PhotoCraft, VectorCraft, WordCraft, GridCraft… |
| Mas… | 240 | alpha, risco jurídico, cópia falsa do REA com trojan, limites do REA |
| Modelos | 270 | destilação adversarial: casos citados por OpenAI e (segundo relatos) Anthropic |
| CRIVO | 420 | Transformer próprio 17M → 46M, ~2,5 bi tokens, 3.947 fatos com fonte, app offline, 0 modelos de terceiros |
| Final | 180 | "a engenharia reversa desmonta. o CRIVO constrói o próprio." |

## Vídeo narrado: "a pirataria da IA" (composição `Narracao`)

68 s com a voz do criador (`public/voz/narracao.ogg`, tirada do vídeo que ele mandou, só
com áudio). 14 cenas trocam no início de cada frase dita: parede 3D de apps se clonando,
caveira de circuito em SVG, paywall e carteira vazia, plugue MCP ligando no "cérebro" 3D
que pulsa com a voz, pedido digitado e app recriado do zero, original × clone, vista
explodida 3D das camadas de um app (interface → binário) para a engenharia reversa, alarme
de perigo, moedas indo para a dona do app, relógio de menos de 1 hora, vilão, "melhor que
o original", "sem controle", celular vazando dados e saldo zerando, enquete e botão de
inscrição. Legendas por frase curta, trilha baixa e efeitos sintetizados.

Como o tempo de cada palavra foi obtido:

1. Transcrição: o roteiro (`public/voz/roteiro.txt`) é o texto que o criador colou, com
   pequenas correções de ditado ("softwere" → "software", "dir" → "dinheiro", "clube formal.
   E intencionada" → "clone for mal-intencionada", "men. O original é esse" → "melhor que o
   original. E esse"). O Whisper foi autorizado só para esta tarefa, mas a rede do ambiente
   bloqueou o download do modelo, então ele não foi usado. `scripts/transcrever.mjs` fica para
   quando houver acesso.
2. Alinhamento sem modelo: `scripts/alinhar_fala.py` detecta os núcleos de sílaba (picos de
   energia na faixa das vogais) e mapeia neles as sílabas do roteiro, preso nos respiros. A
   precisão fica perto de ±0,5 s; por isso a legenda entra por frase, sem destaque palavra por
   palavra. Conferência: a voz da saída bate com a original (correlação 0,7–1,0 por trecho).
3. `scripts/tempos_narracao.py` gera `src/narracao/dados.gen.ts` (início das cenas, páginas
   de legenda e quadro de cada palavra). `scripts/energia_voz.py` gera o envelope da voz.

```console
python scripts/alinhar_fala.py <narração 16 kHz .wav> public/voz/roteiro.txt public/voz/legendas.json
python scripts/tempos_narracao.py public/voz/legendas.json src/narracao/dados.gen.ts
npx remotion render Narracao out/narrado.mp4 --gl=swiftshader
```

A gravação original já chega a 0 dBFS; a voz entra a 72% e a saída final passou por um
limitador (`ffmpeg -af alimiter=limit=0.94`) para não estourar quando os efeitos somam.

## Sons

Toda a trilha e os efeitos (whoosh, boom, cliques, glitch, scratch, ding…) são sintetizados
do zero com NumPy em `scripts/gerar_sons.py`; nada é baixado. Os `.wav` não vão para o git:
`npm run sons` os recria em `public/sfx/` (o `dev` e o `render` já fazem isso antes).
`scripts/cortes.json` diz em que segundo a trilha muda de seção; se mudar a duração das
cenas em `src/tema.ts`, ajuste os dois.

## Comandos

```console
npm i
npm run dev       # Remotion Studio
npm run render    # out/crivo-engenharia-reversa.mp4
```

Num ambiente sem Chrome do Remotion, aponte para o Chromium já instalado com
`--browser-executable=<caminho do headless_shell>`.

As fontes (Space Grotesk e JetBrains Mono, licença OFL) ficam em `public/fontes/`, para a
renderização não depender da rede.

## Fontes da pesquisa (consultadas em 14/10/2026)

- REA: [repositório](https://github.com/morluto/rea), [DEV Community](https://dev.to/hassann/what-is-rea-reverse-engineer-anything-the-mcp-server-that-hit-115k-github-stars-in-a-week-1coc), [GBHackers](https://gbhackers.com/rea-new-ai-powered-reverse-engineering-tool/), [AICoder](https://aicoder.com/news/news-20261008-rea-reverse-engineer-anything-mcp-agents), [análise do que é verdade](https://pasqualepillitteri.it/en/news/23845/rea-reverse-engineer-anything-github-true-false), [KuCoin](https://www.kucoin.com/news/flash/ai-reverse-engineering-tool-rea-surges-by-100-000-stars-in-a-week-sparking-legal-and-technical-controversies)
- Engenharia reversa de binários por agentes: [Popular AI](https://www.popularai.org/p/ai-reverse-engineering-software-binaries), [clean-room e licenças](https://redreamality.com/blog/ai-reverse-engineering-clean-room-rewrite-licensing/)
- Clones ArtCraft: [PetaPixel](https://petapixel.com/2026/10/12/there-are-free-open-source-versions-of-microsoft-office-apps-thanks-to-ai/), [Cybernews](https://cybernews.com/ai-news/ai-adobe-alternatives-open-source/), [Futurism](https://futurism.com/artificial-intelligence/creator-free-adobe-suite-microsoft-office), [Vice](https://www.vice.com/en/article/everything-we-know-about-the-free-adobe-clones-built-with-ai-do-they-actually-work/), [HotHardware](https://hothardware.com/news/ai-developer-behind-free-photoshop-clones-now-takes-on-microsoft-office), [KDnuggets](https://www.kdnuggets.com/the-rise-of-ai-software-clones-why-rea-and-artcraft-are-going-viral)
- Destilação: [The Hacker News (OpenAI, 1º/10)](https://thehackernews.com/2026/10/openai-disrupts-reasoning-extraction.html), [Whalesbook (Anthropic, fonte secundária)](https://www.whalesbook.com/news/English/technology/Anthropic-Blocks-AI-Model-Copying-Names-Zhipu-AI/6acdaed279a16deaeaef459d)

Limites: as contagens de estrelas do REA variam entre fontes (de ~115 mil a ~160 mil em
12–13/10); o vídeo usa a mais conservadora. O caso da Anthropic vem de fonte secundária e
aparece marcado "segundo relatos". Os números do CRIVO vêm do README e do histórico do
repositório; não são uma avaliação nova.
