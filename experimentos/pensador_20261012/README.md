# O pensador — rede recursiva própria que raciocina sobre o quadro

**Resultado v2 (15/10/2026): aprovado nos gates** (99,6% / 95,9% / 97,8% com a busca conferida) e **no chat** pelo `raciocinio_ativo`, conferido pelo enumerador. A v1 (13/10) tinha sido reprovada. Detalhes e limites em [RESULTADO.md](RESULTADO.md).

No CRIVO, o Transformer 17M é a rede da linguagem: diz o que o quadro decidiu. Este
experimento testa a outra metade: uma rede **própria, pequena e treinada do zero** que
**pensa** sobre o conteúdo do quadro, sem ler texto.

Nada aqui vai para o chat. O resultado grava `ativo_no_chat: false`, e a integração só
acontece depois dos gates, da porta conversacional e de um opt-in como o #168.

## A tarefa

Entrada: premissas estruturadas — fatos, regras "se A e B então C", "se A ou B então C",
negações — e uma pergunta sobre um literal. É o que `raciocinio_ativo.py` monta a partir da
conversa ("Considere estas premissas: chove; se chove, então a rua molha").

Saída:

| Cabeça | O que decide |
|---|---|
| status | sustentado, refutado, indeterminado ou conflito |
| prova | quais premissas bastam para a conclusão (ou para o conflito) |
| perguntar | quando falta informação, qual átomo perguntar (o que mais resolve), ou nenhum |

**Professor:** o enumerador de mundos do próprio CRIVO (`SistemaPremissas`). O rótulo sempre
vem dele, não da forma como o problema foi montado.

## A rede (`pensador.py`)

- Um bloco Transformer de 2 camadas (d=128, ~0,4M parâmetros) aplicado **8 vezes** sobre o
  próprio estado, com a entrada reinjetada a cada volta. Pensar mais = mais voltas, sem mais
  parâmetros (ideia dos modelos recursivos pequenos, como o HRM e o TRM).
- Cada volta é supervisionada.
- Átomos e premissas recebem vagas sorteadas a cada exemplo: a rede não pode decorar nomes
  nem posições.
- Controle: a mesma rede com 1 volta só (sem recursão).

## Uso seguro: propor e conferir

O pensador **propõe**; o CRIVO **confere**. Uma afirmação só sai se a prova proposta, que é
pequena, realmente bastar e for mínima (`gerar_pensador.conferir_prova`), e se a base inteira
for consistente. Sem isso, o CRIVO diz que não consegue concluir. Por construção, a política
não afirma nada errado. O que se mede é quanto ela consegue afirmar (a "cobertura segura").

## Conjuntos congelados (`conjuntos_pensador.json`, SHA em `manifesto.json`)

| Conjunto | O que testa | n |
|---|---|---|
| dev | escolha do checkpoint | 1000 |
| blind_iid | mesma distribuição do treino (3–8 átomos, provas de até 3 regras) | 2000 |
| ood_profundidade | provas de 4 a 6 regras encadeadas | 1000 |
| ood_tamanho | 11 a 16 átomos, até 24 premissas — além do limite de 10 átomos do runtime | 500 |

Status em todos: 30% sustentado, 20% refutado, 35% indeterminado, 15% conflito. O treino
(400 mil problemas) é gerado com outra semente e exclui todo problema congelado.

## Gates (no número de voltas do treino, fixado antes)

- exato ≥ 95% no `blind_iid`, ≥ 80% em `ood_profundidade` e `ood_tamanho`
  (exato = status certo + prova que passa na conferência, ou pergunta útil quando indeterminado);
- afirmações erradas da rede sozinha ≤ 2% em todos;
- zero afirmação errada com a política;
- invariância a renomear e reordenar ≥ 98%.

## Como rodar

- Colab (GPU): `notebooks/pensador_colab.ipynb` → Executar tudo.
- Local: `python experimentos/pensador_20261012/treinar_pensador.py --saida /tmp/pensador`.
- Para regenerar os conjuntos: `python experimentos/pensador_20261012/gerar_pensador.py` (deve
  reproduzir o SHA do manifesto).

## Limites, ditos antes de rodar

- Até 10 átomos, o enumerador do CRIVO já resolve esta lógica com exatidão e rapidez; ali o
  pensador não acrescenta capacidade. Este experimento mede se uma rede própria **aprende a
  raciocinar e generaliza** (provas mais longas, problemas maiores) — o passo necessário antes
  de usá-la onde enumerar não dá (`ood_tamanho` é o primeiro sinal disso).
- Lógica proposicional é um mundo pequeno e limpo. Passar aqui não diz nada sobre raciocínio
  em linguagem livre, senso comum ou causalidade.
- A consistência da base é checada por enumeração; acima de ~20 átomos isso também fica caro,
  e a política precisaria de outro verificador.

## v2 (14/10/2026, a pedido do criador: "pode ser o pensador antes do imaginador?")

A v1 foi reprovada porque errava a prova mínima e não melhorava com mais voltas. A v2
(`pensador_v2.py`, `treinar_pensador_v2.py`, `notebooks/pensador_v2_colab.ipynb`) usa os mesmos
conjuntos congelados e as mesmas metas, com estas mudanças:
- voltas sorteadas de 4 a 16 no treino;
- parada adaptativa no uso (3 voltas iguais seguidas, de 4 a 32);
- busca conferida da prova nas 10 premissas mais confiáveis;
- d=192, peso 3 na prova, 30 mil passos.

**Registrado antes de rodar:** a aprovação usa a conta "adaptativo_busca", que é a que rodaria no
CRIVO. As contas "rede" (como na v1) e "adaptativo" são só relatadas. Mesmo aprovado, ele não vai
para o chat sem a ponte entre a frase em português e as premissas, e sem a decisão do criador.
