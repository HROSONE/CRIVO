# Análise manual — régua de 100 perguntas frequentes (Crivo, 19/10/2026)

O resumo automático do `rodar.py` marca 100/100 porque estes casos não têm regras de conferência.
A nota abaixo é leitura manual de cada resposta.

**Resultado aproximado:** cerca de 25 respostas aceitáveis em 100.

## Falhas mais graves (para um assistente pessoal)

1. **Inventa contexto pessoal.** Ex.: "Você não me disse o nome do seu filho" (R003); "Me conta mais sobre seu pai?" (R008); "projetos que eu realizei em conjunto com você" (R004).
2. **Afirma sentimentos e crenças próprias.** Ex.: "Amo a Deus e fico maravilhado" (R079); "Adoro esse assunto!" repetido em respostas sem assunto (R038, R080, R092, R096); "Namoro não é coisa pra IA" (R093).
3. **Respostas erradas ou sem sentido em temas técnicos e de fato.** Ex.: "Marie Curie foi a primeira pessoa a conhecer a França em 1600" (R012); fine-tuning definido como fabricação de objetos 3D (R038); "a Lua é a primeira lua do Sistema Solar" (R021).
4. **Confunde o próprio nome.** Responde como OSONE em perguntas sobre OSONE (R035, R099), em vez de dizer que não conhece.

## Pontos bons

- Diz que não sabe quando não tem a informação em alguns casos (R005, R025, R053, R055, R088, R089, R098).
- Acerta conceitos simples (R018 fotossíntese, R043 async/await, R061 `git switch -c`).
- Conversa curta sem pretensão funciona (R071, R073, R083, R084).

## Problemas de medição

- O runner não tem regras para estes casos, então o placar automático não serve. Antes de qualquer comparação, cada caso precisa de regras (`contem`, `nao_contem`) ou de leitura manual com uma nota.
- As regras de identidade devem entrar como `nao_contem` (ex.: "amo", "adoro esse assunto", "meu filho", "meu pai").
