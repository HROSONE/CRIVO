# Acervo ampliado: história, geografia, pessoas, literatura e ciências (05/10/2026)

Cinco catálogos temáticos novos entram no currículo do mundo pelo mesmo
carregador e pelo mesmo validador de fontes e fatos (`curriculo_mundo.py`).
Nenhum peso foi treinado. O conteúdo é síntese própria em português, e cada fato
aponta uma fonte com URL, crédito e condições de reutilização.

| Arquivo | Conceitos | Conteúdo |
|---|---|---|
| `conhecimento_historia.json` | 44 | Do Neolítico à Guerra Fria, incluindo Mesopotâmia, Egito, Grécia, Roma, China imperial, Idade Média, expansão islâmica, Renascimento, Reforma, Grandes Navegações, tráfico atlântico, revoluções (Científica, Francesa, Haitiana, Industrial, Russa), guerras mundiais, Holocausto, descolonização e ONU. No Brasil: povos indígenas, Colônia, Palmares, Independência, Abolição, República, Era Vargas, ditadura e Constituição de 1988. |
| `conhecimento_pessoas.json` | 38 | Filósofos, cientistas, artistas, líderes e escritores. Entre os brasileiros: Zumbi, Tiradentes, Luiz Gama, D. Pedro II, Santos Dumont, Oswaldo Cruz, Carlos Chagas, Chico Mendes, Machado de Assis, Clarice Lispector, Carolina Maria de Jesus, Tarsila e Villa-Lobos. |
| `conhecimento_literatura.json` | 26 | Elementos da narrativa (enredo, personagem, narrador, conflito, jornada do herói), gêneros, figuras de linguagem, mitos, epopeias, contos de fadas, folclore, cordel e obras de referência. |
| `conhecimento_geografia.json` | 25 | Continentes, oceanos, tectônica, relevo, biomas (globais e os seis brasileiros), regiões do Brasil, clima, coordenadas, população e urbanização. |
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
