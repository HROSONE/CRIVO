# Pointer/Copy Causal v5 — âncora na própria base

Notebook: `notebooks/pointer_copy_causal_v5_colab.ipynb`. Saída no Drive:
`CRIVO/checkpoints/experimento_pointer_copy_v5/pointer_copy_v5_<data>/`. **Ainda não executado.**

## Por quê

No v4 as cabeças aprenderam as tarefas (AB: cópia+fim 75–83% no dev; ABC: 50–83% nas seis
tarefas), mas mudaram as respostas comuns do modelo, e só o passo 1 passou na preservação
(`experimentos/pointer_copy_causal_v4_20261012/RESULTADO.md`).

## Única mudança causal

Perda `KL(base || cabeça)` nas continuações que a base congelada gera para mensagens comuns do
próprio CRIVO, somada à perda das tarefas com peso 1 ou 4. A cabeça aprende a ficar desligada
fora das tarefas.

- `ancoras_v5.json` (congelado, SHA-256 `e7a9529d…`): 800 mensagens de treino e 48 de dev,
  do split de treino de `curriculo_dialogo.json` e `curriculo_linguagem_neural.json`,
  sem as 12 perguntas da checagem final; gerado por `preparar_ancoras.py`.
  `perguntas_externas.json` não é usado (o arquivo proíbe uso em treino).
- Arquiteturas do v4 sem alteração: AB e ABC. A variante A saiu (não consegue parar).
- 4 configurações (AB/ABC × peso 1/4), mesmos lotes e hiperparâmetros do v2–v4.
- Escolha só pelo dev, com preservação medida nas 48 âncoras de dev; só o candidato abre o blind.
- Gates, blinds e dados congelados iguais ao v3/v4; as 12 perguntas fixas ficam como checagem final.

## Verificação feita antes de publicar

Execução completa em CPU com pesos aleatórios da mesma arquitetura (conferência de SHA,
geração das âncoras, treino das 4 configurações, escolha, avaliação, salvamento): sem erros.
Não mede capacidade. Duração estimada no T4: próxima de 1 hora.
