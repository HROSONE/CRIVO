# O CRIVO como ecossistema (05/10/2026)

## A ideia

Na natureza, nada se sustenta sozinho. O CO₂ em excesso é absorvido pelas
florestas e pelos oceanos, os predadores regulam as presas e os decompositores
devolvem ao solo o que sobra. O equilíbrio vem das interações, não de uma peça
perfeita.

O CRIVO passa a ser descrito e testado assim. Cada mecanismo que pode responder
no chat é uma **espécie** com papel, nicho e **contrapeso**. Nenhuma espécie age
sem alguém que corrija o excesso dela.

## 1. Mapa das espécies (`ecossistema.py`)

São 26 espécies em 6 reinos (conhecimento, raciocínio, linguagem, conversa,
neural e programação). Cada uma declara:

| Campo | O que é | Exemplo (`compreensao_neural`) |
|---|---|---|
| papel | o que faz | reconhece o assunto de formulações novas e pergunta se entendeu |
| nicho | quando entra | só quando as regras dizem "não entendi", nunca com negação |
| alimento | recursos de que depende | `artefatos/entendimento_pt` |
| regulado por | quem corrige o excesso dela | a pessoa, a recusa, as catracas |
| guardiões | testes que medem a saúde dela | `testes_entendimento_neural.py` |

Além das espécies, há **reguladores** que equilibram todas elas: crise, fontes,
catracas, estado da conversa, a pessoa e a recusa.

`testes_ecossistema.py` garante que:

- todo mecanismo gravado no código está no mapa, e toda espécie do mapa existe
  no código. A varredura lê o código-fonte, então um mecanismo novo sem papel
  nem contrapeso reprova a suíte;
- toda espécie tem contrapeso e guardião, e os arquivos citados existem;
- **redes neurais nunca se regulam só entre si**: precisam de um regulador
  externo (a pessoa, as fontes, a recusa ou as catracas), porque erram com
  confiança.

A API passa a informar `ecosystem` em cada resposta: espécie, reino, papel e
quem a regula.

## 2. Ciclo de retorno

Como os decompositores devolvem nutrientes ao solo, a reação da pessoa volta
como sinal para a espécie que respondeu:

- **confirmado:** "sim" a uma pergunta de confirmação;
- **rejeitado:** "não" a uma confirmação (da rede neural ou do recuperador);
- **contestado:** "não era isso" ou "sua resposta está errada" depois de uma
  resposta. Contestar uma recusa não gera sinal, porque não havia resposta.

Os sinais ficam em `Crivo.sinais`, e a API devolve os da fala atual em
`ecosystem_feedback`. **Nada é treinado automaticamente** com eles: um sinal
só vira melhoria depois de passar pelas medições, como qualquer mudança.

### Do sinal ao exemplo (atualização)

O servidor não guarda conversas. Por isso, o caminho do sinal até o treino
passa pela pessoa:

1. **No site.** Os 👍/👎 e os sinais automáticos ("sim" ou "não" a uma
   confirmação, "não era isso") ficam só no navegador. Cada um registra a
   espécie que respondeu e se a voz própria falou.
2. **Download.** "Baixar avaliações" gera `crivo-avaliacoes.json`. Nada é
   enviado sozinho.
3. **Fila.** `python scripts/retorno_para_exemplos.py fila crivo-avaliacoes.json`
   monta a fila `dados/retorno_fila.json`, sem duplicar e com
   `"revisado": false`:
   - 👍 numa resposta com voz: a resposta pode virar exemplo de tutor;
   - 👎 ou "não era isso": precisa de uma resposta corrigida;
   - "sim" a uma confirmação da rede: a fala vira exemplo daquele assunto;
   - "não" a essa confirmação: registro do erro, usado para medir.
4. **Revisão.** Quem revisa marca `"revisado": true` e escreve as correções.
   Depois, `python scripts/retorno_para_exemplos.py incorporar` move os itens
   revisados para `dados/voz_tutor.json` e `dados/entendimento_retorno.json`.
   Ficam de fora:
   - respostas com palavra inventada (guarda de fidelidade);
   - assuntos do teste congelado da voz;
   - perguntas do teste congelado da compreensão.
5. **Treino.** `treinar_voz.py` e `treinar_entendimento.py` leem esses
   arquivos. O retreino e as catracas continuam manuais: nenhum sinal muda
   pesos sozinho.

De quebra, "não era isso" deixou de ser lido como relato do dia a dia e passou a
ser reconhecido como contestação.

## 3. Painel de saúde (`scripts/saude_ecossistema.py`)

Roda os conjuntos de desenvolvimento (bateria e troca de assunto) e o teste
congelado de compreensão, e conta por espécie quantas decisões tomou e quantas
acertou. Os conjuntos retidos não entram: eles só aparecem no agregado das
catracas.

Retrato de hoje (296 casos):

| Espécie | Reino | Decisões | Acertos |
|---|---|---|---|
| recuperador | conhecimento | 182 | 134 (74%) |
| composicao_factual | conhecimento | 69 | 64 (93%) |
| busca_factual | conhecimento | 26 | 23 (88%) |
| linguagem_conversa | conversa | 16 | 12 (75%) |
| conversa_assistente | conversa | 1 | 1 |
| compreensao_neural | neural | 1 | 1 |
| consulta_relacional | raciocínio | 1 | 1 |

O ecossistema ainda está **desequilibrado**: o reino do conhecimento responde
94% das vezes, e o recuperador por palavras, sozinho, responde 61% com a menor
taxa de acerto entre os grandes. É para ele que as próximas melhorias devem ir.

## 4. Ligações entre assuntos

O acervo já tinha ligações diretas com fonte ("o sono ajuda a memória"), mas o
CRIVO não entendia "qual a relação entre X e Y?". Agora ele responde a:

- "Qual a relação entre X e Y?", "O que X tem a ver com Y?", "X e Y estão
  ligados?": usa a ligação direta cadastrada em qualquer sentido. Sem ligação,
  diz que conhece os dois mas não tem a ligação, em vez de supor uma;
- "Com o que X se relaciona?", "Quais são as ligações de X?": lista as
  ligações diretas de X;
- "O que regula, sustenta ou equilibra X?": lista as ligações que chegam a X.

Foram cadastradas 7 ligações ecológicas em `conhecimento_ecologia.json`, cada
uma apoiada em um fato com fonte do conceito de origem:

- ciclo do carbono → fotossíntese e respiração celular;
- oceano → efeito estufa (absorve calor e CO₂ em excesso);
- Amazônia → ciclo da água (regulação das chuvas);
- Cerrado → ciclo da água (berço das águas);
- floresta tropical e Mata Atlântica → biodiversidade.

O CRIVO **não deduz cadeias de causa**: liga só o que está cadastrado com fonte
e avisa isso na resposta.

### Experimento: recuperador que confirma quando não cobre a pergunta (não adotado)

O painel mostrou o recuperador por palavras como o elo mais fraco. Foi testada
uma regra: quando a entrada escolhida não cobre uma palavra de conteúdo da
pergunta ("Como ORDENO uma lista?" → append), o CRIVO pergunta "Você quis
perguntar algo como…?" em vez de afirmar. Também foi testada uma segunda
opinião: responder direto quando a compreensão neural aponta a mesma entrada.

| Variante | Teste congelado: diretas certas / recusas certas | Bateria dev: certas / parciais |
|---|---|---|
| Sem a regra | 45/75 · 49/55 | 116 · 9 |
| Confirma com 1 palavra faltando | 25/75 · 55/55 | 116 · 6 |
| A mesma, com segunda opinião da rede | 36/75 · 55/55 | 116 · 6 |
| Com 2 ou mais palavras faltando | 42/75 · 53/55 | 116 · 9 |
| Com metade do conteúdo faltando | 41/75 · 54/55 | 116 · 7 |

Todas as variantes trocam respostas diretas certas por recusas e confirmações,
e nenhuma mantém a catraca de 45/75. Por isso a regra não entrou. A lição: a
cobertura literal de palavras é uma pista fraca. Perguntas informais
("samambaia amarelando") usam palavras que a entrada certa não tem. O caminho
provável é várias espécies propondo respostas com evidência, e um árbitro
decidindo quando confirmar.

## Limites

- O mapa descreve e testa o equilíbrio; ainda não redistribui decisões sozinho.
- Os sinais de retorno valem por conversa (o servidor não guarda estado). Para
  virarem melhoria, precisam ser coletados com consentimento e medidos.
- São poucas ligações ecológicas. Um conceito de gás carbônico (CO₂) ainda não
  existe no acervo; ele aparece só dentro dos fatos de outros conceitos.

## Reproduzir

```bash
python ecossistema.py                       # mapa, reguladores e teia
python scripts/saude_ecossistema.py         # painel (~2,5 min)
python -m unittest testes_ecossistema
```
