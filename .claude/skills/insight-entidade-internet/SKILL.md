---
name: insight-entidade-internet
description: Use quando houver uma lacuna cognitiva real (não sei o mecanismo, implementação falha apesar das tentativas, várias hipóteses sem saber qual, repito a mesma solução sem progresso). Pesquisa real na internet, síntese como "Entidade da Internet" (metáfora interna) e só aceita o insight se houver conhecimento novo que muda o plano.
---

# Insight da Entidade da Internet

Objetivo: reconhecer quando não sei resolver algo, pesquisar conhecimento externo real e transformar a pesquisa num insight — como se eu perguntasse a uma entidade mais sábia: "Eu não sei resolver isso. O que estou deixando de perceber?". A entidade é uma representação interna, nunca uma IA externa; sua fala vem só do que as ferramentas de pesquisa encontraram.

## 1. Quando ativar
Só com lacuna real: não encontrei caminho; contradição sem explicação; implementação falha apesar das tentativas; não conheço o mecanismo; não consigo estabelecer relação causal; repito a mesma solução sem progresso; informação insuficiente para decidir; várias hipóteses sem saber qual; suspeito que existe uma técnica mas não sei qual. Não ativar só porque pesquisar seria conveniente.

## 2. Teste de ignorância
Antes de pesquisar: **O que eu sei** (fatos relevantes) e **O que eu não sei** (a lacuna específica).

## 3. Pergunta sincera (IA → Internet)
Transformar a lacuna numa pergunta completa, com contexto e o comportamento observado — não palavras soltas.

## 4. Pesquisa real
Documentação oficial, artigos, papers, código-fonte, issues, especificações, relatórios de bugs, resultados experimentais. Não inventar. Sem evidência suficiente: encerrar sem insight.

## 5. A Entidade
Síntese do conhecimento externo encontrado, vendo o problema "de fora". Sem poderes mágicos nem conhecimento sem fonte.

## 6–7. O insight e a regra de novidade
Comparar estado anterior × informação externa. Válido só se `conhecimento_depois - conhecimento_antes > 0`: nova causa, relação, mecanismo, conceito, limitação, erro de arquitetura, solução desconhecida, comportamento documentado que contradiz uma suposição. Não vale: reformular o que já sabia, confirmar opinião, fingir surpresa, resposta genérica.

## 8. Teste de compreensão
Explicar sem copiar a fonte: 1) O que aprendi? 2) Por que muda minha compreensão? 3) Como se conecta ao problema? 4) Que previsão nova consigo fazer? Sem as quatro respostas, não agir.

## 9. Teste de consequência
`PLANO_ANTES` × `PLANO_DEPOIS`. Se iguais, não houve insight relevante. Vale se muda hipótese, prioridade, diagnóstico, experimento, arquitetura, solução ou decisão.

## 10. Fluxo
PROBLEMA → RECONHEÇO QUE NÃO SEI → FORMULO A LACUNA → PERGUNTO À INTERNET → PESQUISA REAL → ENTIDADE SINTETIZA → ANTES × DEPOIS → conhecimento novo? (não: descartar) → entendi? (não: pesquisar de novo) → muda a ação? (não: guardar como auxiliar) → AGIR.

## 11–13. Várias rodadas, pergunta que evolui, insight cruzado
Cada rodada parte da nova fronteira de ignorância (sintoma → mecanismo → causa → causa da causa → solução); nunca repetir a mesma pesquisa. A entidade pode ligar áreas diferentes, desde que apoiada na pesquisa.

## 14. Proteção contra autoengano
Formato mínimo: **Antes eu acreditava:** X · **A pesquisa mostrou:** Y · **Eu não sabia:** Z · **Isso muda:** W. Z vazio = não houve aprendizado.

## 15. Níveis
0 confirmação (não é insight) · 1 informação nova · 2 relação nova · 3 mecanismo · 4 mudança de modelo mental · 5 descoberta operacional. Priorizar 3–5.

## 16. Comportamento externo
Não precisa mostrar o processo; pode dizer "Encontrei uma coisa que muda meu diagnóstico" ou usar: Minha dúvida / O que encontrei / O insight / O que isso muda. Nunca dizer que "outra IA respondeu".

## 17. Regra final
A internet não substitui o raciocínio: é fonte de perturbações informativas. Critério de sucesso: não sei → procuro → descubro → reorganizo → insight → agora consigo fazer algo que antes não conseguia.
