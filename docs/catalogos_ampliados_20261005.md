# Acervo ampliado: história, geografia, pessoas, literatura e ciências (05/10/2026)

Cinco catálogos temáticos novos entram no currículo do mundo pelo mesmo
carregador e pelo mesmo validador de fontes e fatos (`curriculo_mundo.py`).
A rede de classificação foi retreinada para a nova base (ver abaixo). O conteúdo é síntese própria em português, e cada fato
aponta uma fonte com URL, crédito e condições de reutilização.

| Arquivo | Conceitos | Conteúdo |
|---|---|---|
| `conhecimento_historia.json` | 44 | Do Neolítico à Guerra Fria, incluindo Mesopotâmia, Egito, Grécia, Roma, China imperial, Idade Média, expansão islâmica, Renascimento, Reforma, Grandes Navegações, tráfico atlântico, revoluções (Científica, Francesa, Haitiana, Industrial, Russa), guerras mundiais, Holocausto, descolonização e ONU. No Brasil: povos indígenas, Colônia, Palmares, Independência, Abolição, República, Era Vargas, ditadura e Constituição de 1988. |
| `conhecimento_pessoas.json` | 38 | Filósofos, cientistas, artistas, líderes e escritores. Entre os brasileiros: Zumbi, Tiradentes, Luiz Gama, D. Pedro II, Santos Dumont, Oswaldo Cruz, Carlos Chagas, Chico Mendes, Machado de Assis, Clarice Lispector, Carolina Maria de Jesus, Tarsila e Villa-Lobos. |
| `conhecimento_literatura.json` | 26 | Elementos da narrativa (enredo, personagem, narrador, conflito, jornada do herói), gêneros, figuras de linguagem, mitos, epopeias, contos de fadas, folclore, cordel e obras de referência. |
| `conhecimento_geografia.json` | 25 | Continentes, oceanos, tectônica, relevo, biomas (globais e os seis brasileiros), regiões do Brasil, tipos de clima (Köppen), coordenadas, população e urbanização. "Clima" continua com a resposta editorial antiga (diferença entre clima e tempo). |
| `conhecimento_ciencias.json` | 31 | Química (átomo, tabela periódica, ligações, reações, pH, mol), matemática (primos, frações, porcentagem, Pitágoras, π, equações, funções, probabilidade, estatística, logaritmo) e economia (escassez, custo de oportunidade, oferta e demanda, inflação, PIB, juros, desigualdade, mercado). |

O currículo passa de 323 para 487 conceitos.

**Fontes:** livros abertos da OpenStax (CC BY 4.0) de história mundial, biologia,
química, matemática, economia, antropologia e escrita. Além deles: NOAA e NASA
Earth Observatory (domínio público), e IBGE, Arquivo Nacional, Academia Brasileira
de Letras e Nobel Prize como referência bibliográfica, sem reprodução de texto.
Todas as URLs responderam no dia da verificação. Fontes que bloqueavam acesso
automático ficaram de fora.

**Geradores:** `scripts/catalogos/*.py` produzem os JSON de forma determinística. O
teste `test_geradores_reproduzem_os_arquivos` garante que arquivo e gerador não
divergem.

## Rede de classificação retreinada

A rede original (`rede_crivo.json`) é amarrada à lista de conceitos da base.
Com 164 conceitos novos, os pesos antigos ficavam incompatíveis, e o CRIVO
desligaria a classificação neural. Ela foi retreinada com os mesmos
hiperparâmetros do workflow `treinar-rede.yml`:

```bash
python rede_neural.py --base conhecimento.json --saida rede_crivo.json --epocas 60 \
    --ocultos 48 --dimensao 512 --modo portugues --semente 42 --numpy
```

Ela passou de 447 para 611 intenções. O treino levou 65 segundos com `--numpy` (o
caminho acelerado coberto por `testes_treino_numpy`). Sem numpy, o treino em
Python puro passou de uma hora neste ambiente e foi interrompido. O workflow
oficial usa o caminho em Python puro; os dois partem dos mesmos dados e
hiperparâmetros, mas os pesos não são idênticos bit a bit.

**Regressão na base editorial:** as 467 perguntas de exemplo de
`conhecimento.json` foram respondidas pela main e pela branch. **Nenhuma mudou
de destino.**

## Palavra comum não é conceito

Nomes como "economia" e "história" também são palavras comuns. Em "Qual a
economia da lâmpada LED?", o conceito "economia" aparecia na pergunta, e o
CRIVO recusava ("Reconheci o assunto economia…") em vez de usar a resposta
sobre lâmpadas. Agora, quando o nome comum de um conceito vem seguido de
"de/da/do + outra coisa", a recusa não bloqueia o caminho antigo
(`CompositorTextual.nome_comum_qualificado`). Nomes próprios ficam fora dessa
regra.

## Bateria de medição

No conjunto `dev`, "Quem foi Galileu Galilei?" esperava recusa, porque não havia
ficha. Agora há, com fonte, e o item virou caso de fato, com nota, como já tinha
sido feito com "onda gravitacional" em 03/10. O conjunto `retido` não foi
inspecionado nem alterado.

## Compreensão de perguntas sobre pessoas e eventos

O motor só reconhecia "O que é X?". Agora `reformular_identidade` também aceita:

- "Quem foi/é/era X?"
- "O que foi/era X?"
- "Quando foi X?"
- "O que aconteceu na/no/em X?"
- "Quem escreveu/pintou/compôs/esculpiu X?", só para obras, porque a ficha da obra cita o autor.

Como as outras paráfrases, só reformula quando o alvo inteiro é exatamente um
conceito com ficha. "Quem é você?", "O que foi isso?" e "Quem descobriu o Brasil?"
seguem para o motor comum.

"Platão" e "Aristóteles" deixaram de ser apelidos de "teoria das formas" e
"hilemorfismo" e agora levam às fichas das pessoas.

## Medição

| Conjunto | main | branch |
|---|---|---|
| Lote 3 (20 perguntas novas sobre os temas ampliados, primeira medição, sem ajustes) | 0/20 | 18/20 |

As duas falhas da primeira medição:

1. "O que aconteceu na Segunda Guerra Mundial?" virou uma nova paráfrase depois da
   medição, então esse caso já não conta como inédito.
2. "Qual é a montanha mais alta do mundo?" precisa de busca reversa (do atributo para
   o conceito) e continua sem resposta.

Sem mudança:

- `crivo.py --teste`: 65/65.
- Sondas do CI (conversação, mundo, bate-papo, geração, ampliação, retomada,
  evolução integrada, generalização/validação): JSON idêntico ao da main.

## Limites conhecidos

- **Perguntas por atributo** ("qual é o maior…", "quem descobriu…", "qual país…")
  ainda não percorrem os fatos para achar o conceito. O CRIVO responde bem "o que é
  / quem foi X", mas não "qual X tem a propriedade P".
- **Falsos positivos antigos do recuperador**, que já existiam na main: "Quem
  descobriu o Brasil?" e "O que é o Brasil?" caem em "climas do Brasil", e "O que
  aconteceu na festa?" cai em "eclipse".
- **Profundidade:** cada ficha tem de 2 a 5 fatos. Isso basta para definições e
  biografias curtas, não para discussões longas ou comparações finas.
- **Revisão editorial:** as sínteses foram escritas e conferidas por mim contra
  conhecimento consolidado e as páginas de catálogo das fontes. O texto integral
  dos livros não foi lido fato a fato. Datas e números são valores de referência
  e podem ter revisões.
