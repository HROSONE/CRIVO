# Perguntas que não supõem (2026-10-02)

## Problema

Cada noção tinha uma pergunta só, quase sempre sobre um acontecimento:
"Fez com qual molho?", "Qual sabor você pediu?", "Gostou de como ficou?".
Ela soava estranha quando a pessoa contava um gosto ("eu adoro pizza"), um
plano ("vou cortar o cabelo sábado") ou um fragmento ("principalmente
massa"): a pergunta supunha algo que ela não disse.

## O que muda

- 78 noções ganharam `pergunta_geral`, uma pergunta aberta que não supõe
  nada ("Qual é o seu sabor preferido?", "Qual é o seu prato de massa
  preferido?").
- `nocoes.pergunta_para(nocao, fala)`: a pergunta específica só vale quando a
  fala é relato de algo que já aconteceu (verbo no passado e não gosto ou
  vontade, `nocoes.evento_passado`); nos outros casos vai a aberta.
- Formas movidas para a noção certa: "show" saiu de "festa"; "caminhada",
  "caminhar" e "caminhei" saíram de "corrida"; "trilha" saiu de "parque" para
  "montanha"; "assisti" deixou de puxar "filme" ("assisti uma peça").
- A métrica de palavras novas da presença passou a contar a pergunta aberta
  da noção como fonte (é texto da própria noção).

## Medição

Bateria nova `avaliacoes/suposicao_v1`, escrita antes da mudança: gosto,
plano ou fragmento não pode receber a pergunta que supõe; relato de algo que
aconteceu (controle) continua com a pergunta específica.

| | antes | depois |
|---|---|---|
| dev | 9/13 | 13/13 |
| retido (agregado) | 7/11 | 10/11 |

Os controles do retido estavam 0/2 antes e depois da primeira versão; a causa
apareceu num teste próprio ("fiz uma trilha hoje" recebia a pergunta do
parque) e levou à troca das formas acima. Os detalhes do retido não foram
abertos. Igual com e sem NumPy.

Demais baterias sem perda.
