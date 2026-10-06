# Acervo profundo (06/10/2026)

## O que mudou

O CRIVO só afirma o que está no acervo, com fonte. Até aqui, a maioria das
fichas tinha 2 ou 3 fatos, e várias áreas nem existiam: música, artes, direito,
medicina e linguística, por exemplo. Agora o acervo tem mais conceitos e fichas
bem mais fundas.

| | Antes | Agora |
|---|---|---|
| Conceitos | 544 | 680 |
| Fatos | 1.729 | 3.947 |
| Fatos marcados "como funciona" | | 495 |
| Fatos marcados "como surgiu" | | 259 |
| Fatos marcados "como se sabe" | | 147 |
| Fatos marcados "para que serve" | | 102 |

Por área (conceitos e fatos):

| Área | Conceitos | Fatos |
|---|---|---|
| biologia | 65 | 172 → 380 |
| física | 59 | 172 → 318 |
| filosofia | 50 | 125 → 269 |
| sociologia | 47 | 113 → 256 |
| história | 44 | 142 → 252 |
| saúde | 6 → 30 | 15 → 235 |
| pessoas | 38 | 110 → 184 |
| artes (nova) | 23 | 181 |
| computação e tecnologia | 10 → 28 | 36 → 207 |
| geografia | 25 | 79 → 148 |
| psicologia e neurociência | 20 → 37 | 58 → 238 |
| matemática e estatística | 11 → 25 | 34 → 188 |
| literatura | 26 | 75 → 125 |
| química | 11 → 19 | 30 → 122 |
| economia | 9 → 20 | 23 → 120 |
| direito e política (novas) | 11 | 88 |
| linguística (nova) | 5 | 41 |
| engenharia (nova) | 5 | 35 |

Os conceitos antigos ganharam de 3 a 5 fatos cada: mecanismos, causas,
exemplos concretos, como se sabe (evidências e experimentos), debates reais e
equívocos comuns corrigidos. Os catálogos novos são `conhecimento_artes.json`,
`conhecimento_sociedade.json`, `conhecimento_saude.json`,
`conhecimento_tecnologia.json`, `conhecimento_exatas.json` e
`conhecimento_mente.json`.

## Regras do trabalho

- **Só acréscimos.** Nenhum fato existente foi alterado, removido ou
  reordenado. Os fatos novos entram no fim de cada ficha. Como a composição
  mostra primeiro os fatos iniciais, a resposta de "O que é X?" continua a
  mesma; os fatos novos aparecem em perguntas de detalhe, em "como
  funciona/surgiu/para que serve", em "me conta mais" e na leitura da ficha.
- **Fichas protegidas.** Ficaram intactas a astronomia, porque a bateria
  retida de astronomia mede o CRIVO e um fato novo poderia tornar respondível
  uma pergunta que ela espera ver recusada; as fichas dos testes congelados
  (leitura v1 e v2, voz); e as fichas dos dados do tutor.
- **Fontes.** Todo fato cita uma fonte cadastrada com licença e data de
  verificação: manuais abertos da OpenStax (CC-BY-4.0) ou referências
  institucionais (IBGE, IPHAN, Fiocruz, Ministério da Saúde, OMS, STF, Banco
  Central, TSE, Museu da Língua Portuguesa e outras) como somente referência.
  Os textos são sínteses próprias.
- **Saúde e mente.** Conceitos explicados, sem dose, diagnóstico ou conduta
  individual; a orientação geral ("sintomas persistentes merecem avaliação
  profissional") é marcada como tal.
- **Verificação automática.** `scripts/verificar_acervo.py` compara o acervo
  com o git e confere tudo isso: carga e validação do currículo, só acréscimos,
  fichas protegidas, fonte, papel e natureza de cada fato novo, e nomes que não
  colidem.

## Como foi feito e revisado

Doze escritores trabalharam em paralelo, um por catálogo. A regra era "na
dúvida, não escreva". Cada um entregou a lista dos fatos de que tinha menos
certeza, e todos esses foram conferidos um a um. A revisão corrigiu:

- C. elegans: as 131 células que morrem são as do hermafrodita;
- células iPS: camundongo em 2006, humanas em 2007;
- a marcação de aspecto de um fato sobre escala de terremotos;
- um fato sobre o PNI que só citava a OMS (programa do Ministério da Saúde);
- o estudo de Jerry Morris (retirado, sem fonte cadastrada que o sustente);
- os apelidos "nervo" e "nervos", que levariam "nervo óptico" ao sistema
  nervoso periférico.

Todas as contas do catálogo de exatas foram refeitas à mão: médias, desvio
padrão, áreas, derivadas, integrais, massas molares e concentrações.

Os catálogos de história, geografia, pessoas, literatura e ciências são
produzidos por geradores (`scripts/catalogos/`). Os fatos novos deles ficam em
`scripts/catalogos/aprofundamento_<nome>.json`, que o gerador anexa ao fim de
cada ficha; `extrair_aprofundamento.py` refaz esses arquivos.

## Limites

- A astronomia não foi aprofundada nesta rodada; isso pede um teste
  congelado novo de astronomia antes.
- Fatos escritos por modelo e revisados por amostragem dirigida (os
  sinalizados como incertos) ainda podem ter erros que ninguém sinalizou.
  Contestações no chat ("não era isso", "está errado") voltam como sinal para
  revisão.
- Mais fatos não ensinam o CRIVO a entender perguntas novas. Eles dão o que
  dizer quando a pergunta é entendida; a compreensão continua a cargo da
  leitura da ficha e, adiante, do leitor Transformer.

## Reproduzir

```bash
python scripts/verificar_acervo.py --base origin/main
python -m unittest testes_conhecimento_mundo testes_catalogos_ampliados
cd scripts/catalogos && python extrair_aprofundamento.py historia geografia pessoas literatura ciencias
```
