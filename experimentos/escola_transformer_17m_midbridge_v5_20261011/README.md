# Escola Transformer 17,43M — V5 Mid Bridge

## Pergunta causal

A V4 aprendeu a localizar pessoa, objeto e atividade, mas reinjetava o binding somente depois dos oito blocos Transformer. A V5 testa uma única alteração: o mesmo delta da ponte é aplicado depois do bloco 3 e antes dos blocos 4–7.

## Controle

- mesmo checkpoint V1 (`849bc465...c661`);
- mesmo tokenizador;
- mesmo currículo V4 de 3.072 exemplos;
- mesma ponte (~590.980 parâmetros);
- mesmos 150 passos de warmup + 1.000 passos conjuntos;
- mesmos learning rates e pesos auxiliares;
- blocos 0–3 e embeddings congelados; blocos 4–7 treináveis;
- nenhum modelo externo;
- `ativo_no_chat=false` independentemente do resultado do treino.

## Prova nova

O holdout V5 foi gravado antes da implementação da intervenção e usa cinco famílias novas. Seu hash canônico está congelado em `manifesto_holdout.json`. O conjunto não seleciona checkpoint e só é aberto depois dos passos de treinamento.

## Diagnóstico adicional

Além dos seis gates congelados, a V5 mede uma ablação com os mesmos pesos treinados e a ponte desligada. A ablação não altera a promoção; ela existe apenas para responder se o LM passou a consumir o binding.

## Promoção

Só é elegível se todos os gates passarem simultaneamente. Mesmo nesse caso, o artefato continua experimental e não é ligado automaticamente ao chat.
