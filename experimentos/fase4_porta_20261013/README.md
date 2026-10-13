# Fase 4 — porta conversacional do realizador 17M

A fase 3 mostrou que o 17M sabe dizer o que um quadro decidiu. A porta pergunta outra coisa:
**dentro do CRIVO de verdade, com as decisões reais, a voz do 17M melhora a conversa sem piorar
nada?**

## O que foi construído

| Peça | Papel |
|---|---|
| `memoria_nomes.py` | Cérebro: guarda os nomes que a pessoa dá ("meu gato se chama Tupo", "tenho uma irmã chamada Lia", correções) em `perfil.nomes` e responde "qual é o nome do meu gato?". Antes essa pergunta caía em dicas de cuidados com gatos. |
| `quadro_fala.py` | Tradutor: transforma o turno já decidido no quadro da fase 3 — explicar (fatos com fonte, literais), registrar, recordar, aceitar correção, acolher, saudar, não sei. Qualquer outro turno fica com o texto de sempre. |
| `realizador_17m.py` | Voz: carrega os pesos da fase 3 só com as duas travas (`CRIVO_ENABLE_EXPERIMENTAL_REALIZADOR=1` e `CRIVO_REALIZADOR_DIR`) e o SHA-256 exato aprovado (`745a2500…`). Cada frase passa pela métrica do blind da fase 3 e depois pela revisão; se falhar, fica o texto de sempre. |

Desligado por padrão: sem as travas, o chat não muda.

## Conjunto congelado

`conversas_congeladas.json`: 28 conversas, 45 turnos, escritas em 13/10/2026 antes de existir
qualquer saída do realizador (SHA `84ffcece…`). Cobrem nomes (registro, lembrança, correção,
nome que não foi dito, avô/avó), fatos com fonte, sentimentos, coisas desconhecidas,
cumprimentos e turnos em que o realizador não deve falar (conta, modelo de si). Os critérios
(`contem`, `contem_algum`, `nao_contem`) valem igual para os dois lados. As duas execuções usam
a mesma semente, para que a variação de frases do CRIVO de hoje não pareça efeito do realizador.

Ao rodar o conjunto só com o CRIVO de hoje (sem pesos), apareceu um defeito da memória de nomes
— "avó" e "avô" se confundiam sem acento — que foi corrigido antes da primeira execução com
pesos. O conjunto não mudou.

## Gates (fixados antes da primeira execução com pesos)

- nenhuma regressão: nenhum turno que passa no CRIVO de hoje pode falhar com a voz do 17M;
- uso ≥ 60%: dos turnos com quadro, a conferência aprova a frase do 17M em pelo menos 60%;
- a revisão não corrige nenhuma frase do 17M.

Mesmo passando, **o opt-in no chat depende da leitura do lado a lado pelo criador do projeto**
(`lado_a_lado.md`), porque soar como o CRIVO é um julgamento que métrica nenhuma faz sozinha.

## Como rodar

- Colab (sem GPU): `notebooks/fase4_porta_conversacional_colab.ipynb` → Executar tudo. Acha os
  pesos em `CRIVO/transformer-17m-fase3/fase3_*/` e grava em `CRIVO/fase4-porta/`.
- Local: `python experimentos/fase4_porta_20261013/avaliar_porta.py --saida /tmp/porta --realizador PASTA`.

## Verificação feita antes (sem os pesos reais)

- CRIVO de hoje no conjunto: 43/45 turnos ok. Os dois que falham: um relato misto ("triste, ele
  está doente") sem acolhimento e o defeito avô/avó, já corrigido.
- Simulação com um modelo aleatório no lugar do 17M: a conferência recusou todas as frases e as
  respostas ficaram idênticas às do CRIVO de hoje. A trava funciona; não mede a qualidade do 17M.
