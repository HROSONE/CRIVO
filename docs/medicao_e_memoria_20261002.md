# Medição independente e memória entre conversas (02/10/2026)

## Retido 2

Conjuntos novos, escritos antes dos próximos blocos (gerador de frases,
diálogo único, ampliação de conhecimento), para medir sem viés:

| bateria | retido2 (linha de base) |
|---|---|
| presença | 27/29 turnos, 1 genérica, 0 repetições |
| memória de relatos | 10/10 diálogos |
| conversa cotidiana | 12/15 casos (11 sem o analisador), 3/3 diálogos |

Regra: o retido2 entra nas catracas, os testes não exibem seus detalhes, e o
código não é ajustado olhando suas falhas.

## Avaliação humana no site

Cada resposta do CRIVO tem 👍/👎. As avaliações ficam **só no navegador**; o
botão "Baixar avaliações" (em "Sobre") gera `crivo-avaliacoes.json`, que
`scripts/analisar_avaliacoes.py` resume (aprovação geral e por tipo de
resposta; `--reprovadas` lista as ruins). É a régua mais independente que
temos: quem avalia não é quem escreve o código.

## Memória entre conversas (opcional)

Em "Sobre", **Lembrar de mim neste navegador** (desligado por padrão). Ligado,
o navegador guarda nome, nomes citados (o cachorro Thor), os assuntos
marcantes e até 8 relatos, e os reenvia a cada pergunta; o servidor valida,
usa e devolve a versão atualizada, **sem guardar nada**. **Esquecer tudo**
apaga a memória.

Na volta: "Oi de novo, Ana! E o Thor, como está?" — e "o que eu te contei
da minha mãe?" responde com o que foi contado antes. Relatos de outra visita
nunca viram palpite de causa para algo novo.
