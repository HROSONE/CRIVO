# Geração de exemplos (professor com licença aberta)

Os exemplos de compreensão são gerados por um modelo com licença que permite treinar outro
modelo com as saídas (Qwen3-32B-AWQ, Apache 2.0). Não usamos modelos com licença restritiva
para isso: o `AGENTS.md` exige que a licença do professor permita o treino.

## Arquivos

- `gerar_pedidos.py`: cria `entrada_professor.jsonl.gz` (102 pedidos, 10 mensagens cada).
- `validar_saida.py`: confere a saída, descarta repetidas e as iguais à semente ou à régua, compara
  com as regras e grava `exemplos_candidatos.jsonl` com status `ok` ou `revisar`.

## Como rodar no Colab (A100)

1. Abrir o caderno do projeto no Colab, com GPU A100 ativa.
2. Garantir que o repositório está clonado em `/content/CRIVO` (o caderno do piloto já faz isso) e rodar, numa célula:

```
%cd /content/CRIVO
!python experimentos/destilacao_20261014/rodar_modelo.py --modelo Qwen/Qwen3-32B-AWQ --papel professor --entrada compreensao_semantica/geracao/entrada_professor.jsonl.gz --saida /content/drive/MyDrive/CRIVO/compreensao/saida_professor.jsonl.gz
```

3. Baixar do Drive `saida_professor.jsonl.gz` e `saida_professor_modelo.json`.
4. Rodar a validação:

```
python compreensao_semantica/geracao/validar_saida.py saida_professor.jsonl.gz saida_professor_modelo.json
```

## O que não fazer

- Não usar saída de modelo com licença restritiva (por exemplo, o Claude) para treinar.
- Não tratar as etiquetas do professor como verdade. O rótulo vem do pedido; quem confirma é a
  comparação com as regras e a revisão humana de uma amostra.
- Não colocar dados gerados no repositório sem a marca de origem.
