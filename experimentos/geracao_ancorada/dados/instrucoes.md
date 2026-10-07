# Tutor de respostas ancoradas (CRIVO)

Você recebe um arquivo JSON com fichas de conhecimento em português do Brasil: cada ficha tem "id", "nome" e "fatos" (frases verificadas).

Para CADA ficha, escreva 3 exemplos. Cada exemplo tem:
- "pergunta": uma pergunta natural que uma pessoa comum faria, em português do Brasil. Varie: "o que é", "quem foi", "quando", "onde", "quantos", "por que", "como funciona", "para que serve", "me explica…", algumas informais ("vc sabe…", "qual é a do…"), algumas SEM o nome exato do assunto (usando outras palavras). Pelo menos 1 dos 3 deve precisar de 2 fatos para ser bem respondida.
- "fatos": a lista dos ÍNDICES (0-based) dos fatos da ficha que a resposta usa (1 a 3).
- "resposta": a resposta ideal, direta, natural e curta (1 a 3 frases, até ~60 palavras), que começa respondendo exatamente o que foi perguntado.

REGRA DE OURO (fidelidade): a resposta só pode conter informação que está nos fatos indicados. Pode reordenar, juntar frases, trocar a ordem, usar pronomes e palavras de ligação ("por isso", "ou seja", "além disso", "isso porque"), mas NÃO pode acrescentar nenhum dado novo (nome, número, data, lugar, causa, adjetivo avaliativo) que não esteja nos fatos. Reaproveite as palavras dos fatos para os dados (nomes, números e termos técnicos exatamente como estão). Se um fato não responde bem a pergunta, mude a pergunta, não invente.

Formato de saída: um arquivo JSON Lines (um objeto por linha) com {"id": <id da ficha>, "pergunta": ..., "fatos": [...], "resposta": ...}.

Valide no fim: cada linha é JSON válido, "fatos" são índices válidos, e o arquivo tem 3 linhas por ficha. Responda só com o número de linhas escritas e problemas (curto).
