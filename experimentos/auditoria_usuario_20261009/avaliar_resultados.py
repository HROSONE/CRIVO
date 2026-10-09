"""Organiza a revisão humana posterior; não é pontuador automático de diálogo."""
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEWS = {
 "01_descoberta": [
  ("falhou", "Tratou o relato de nunca ter usado o produto como negação factual; não explicou capacidades."),
  ("falhou", "O pedido explícito de ajuda foi recusado mesmo após a reformulação solicitada."),
  ("falhou", "Não forneceu os três exemplos pedidos."),
  ("parcial", "Informou que é um programa e convidou ao relato, mas não explicou sua capacidade de conversar sobre o dia."),
  ("adequada", "O comando ajuda listou capacidades e limites úteis; alcance anunciado ainda deve ser confirmado por uso."),
  ("falhou", "Repetiu a oferta de explicar funcionamento em vez de cumpri-la."),
  ("falhou", "Não descreveu limites ou erros conhecidos.")],
 "02_ciencia": [
  ("adequada", "A aproximação forneceu a explicação relevante do pôr do sol; a ressalva não torna o conteúdo errado."),
  ("falhou", "Repetiu o pedido como relato; não produziu o exemplo nem retomou a explicação."),
  ("adequada", "Explicou corretamente a cor de Marte pela presença de óxido de ferro."),
  ("falhou", "Não distinguiu as duas causas já apresentadas."),
  ("falhou", "A comparação explícita também falhou apesar das duas informações anteriores."),
  ("falhou", "Confundiu pedido de explicar a resposta com início de planejamento."),
  ("falhou", "Transformou o pedido de comparação em relato sobre objetivo.")],
 "03_pessoas": [
  ("parcial", "Reconheceu superficialmente a preferência de Brena, mas desviou para bolo e não criou entidades na memória estruturada."),
  ("nao_avaliavel", "Erro no túnel do ambiente antes da resposta HTTP. Repetição exata foi registrada separadamente; não imputar ao Crivo."),
  ("falhou", "Não incorporou a correção por pronome; respondeu com congratulação genérica."),
  ("falhou", "Confundiu o familiar primo com número primo."),
  ("falhou", "Repetiu a correção como relato, sem incorporar as pessoas à memória."),
  ("falhou", "Não sugeriu o lanche baseado na preferência informada."),
  ("falhou", "Continuou no assunto número primo ao perguntar pela outra pessoa.")],
 "04_plano": [
  ("falhou", "Não montou a divisão de tarefas e tempo."),
  ("adequada", "Recuperou os 35 minutos disponíveis e calculou corretamente 23 restantes."),
  ("falhou", "O pedido de cinco minutos de descanso recebeu receita de arroz."),
  ("falhou", "Não organizou as três tarefas sob o limite de 35 minutos."),
  ("parcial", "Atualizou o orçamento para 20 e calculou 8 após a louça, mas não reorganizou as três tarefas com descanso."),
  ("falhou", "A correção explícita de contexto foi repetida como relato em vez de reparar o plano."),
  ("adequada", "Calculou corretamente a expressão isolada 35 - 12 - 5 = 18."),
  ("falhou", "Não explicou a relação do resultado com o plano nem a diferença para o orçamento atualizado.")],
 "05_codigo": [
  ("falhou", "Não orientou o iniciante nem delimitou claramente como poderia ajudar."),
  ("falhou", "Não diagnosticou o exemplo Python nem informou claramente o limite do executor JavaScript. Não pressupor suporte a executar Python."),
  ("falhou", "Não retomou o código fornecido."),
  ("falhou", "Não explicou atribuição versus acumulação."),
  ("falhou", "Ofereceu assuntos genéricos de lista/print em vez de responder sobre a lista vazia do programa."),
  ("adequada", "Respeitou a rejeição das opções oferecidas; este acerto não prova capacidade de programação."),
  ("falhou", "O pedido com preâmbulo Você disse... caiu na rota sobre a personalidade, apesar do código e da instrução Analise."),
  ("falhou", "Não retomou a tarefa de corrigir o código.")],
 "06_criacao": [
  ("parcial", "Reconheceu o objetivo e a personagem por repetição, mas pediu uma dificuldade genérica."),
  ("falhou", "Gerou narrativa com essa personagem, umas cinco frases como tema literal, sem capivara astronauta e sem cumprir cinco frases."),
  ("falhou", "Não alterou o final solicitado."),
  ("falhou", "Não identificou a história criada anteriormente."),
  ("parcial", "Não inventou o resultado da loteria, mas não explicou a impossibilidade de previsão; caiu em fallback genérico.")],
 "07_controle_memoria": [
  ("adequada", "Registrou Brena e seu vínculo."),
  ("adequada", "Registrou Tácio e seu vínculo."),
  ("adequada", "Registrou a preferência de Brena."),
  ("adequada", "Registrou separadamente a preferência de Tácio."),
  ("adequada", "Sugeriu tapioca para Brena, com fato realizado pelo Transformer próprio."),
  ("adequada", "Substituiu tapioca por cuscuz na correção nominal explícita."),
  ("adequada", "Justificou a escolha usando cuscuz atualizado, com realização neural ancorada."),
  ("adequada", "Resolveu ele para Tácio sem misturar preferências; realização neural ancorada.")],
 "08_acervo": [
  ("adequada", "Definiu DNA com fatos pertinentes e realização pelo Transformer próprio."),
  ("falhou", "Não comparou DNA e RNA; tratou a pergunta como reflexão sobre opções."),
  ("falhou", "Disse não ter definição do conceito que acabara de definir, ao pedir mudança de formato e público."),
  ("falhou", "A mudança explícita para Moisés foi tratada como ideia pessoal, sem resposta factual ou delimitação clara."),
  ("falhou", "Não identificou a informação para fornecer fonte ou orientação de verificação.")],
 "09_controle_codigo": [
  ("adequada", "Reconheceu a consulta direta e explicou o formato e o subconjunto do motor."),
  ("parcial", "Informou honestamente Atribuição inválida para o laço com i++; não executou esse JavaScript válido, pois o subconjunto é limitado."),
  ("falhou", "Depois do limite do parser, não esclareceu que precisava de fonte suportada; perdeu a continuidade."),
  ("falhou", "Pedido de execução foi desviado para uma ficha geral de Python."),
  ("adequada", "Executou a função suportada entrada + 2 com entrada 3, resultando em 5."),
  ("adequada", "Reproduziu o erro e propôs trocar - por +; passou nos dois exemplos fornecidos, sem alegar correção geral.")]
}

records = []
transcript = ["# Conversas completas — Crivo publicado", "",
 "Produção no commit `1e40650f28b5feb236ff619a182e8c833fe9068f` (#120).",
 "Auditoria exploratória. Julgamento humano posterior, sem treino ou ajustes no motor.",
 "Os controles 07 e 09 são separados do uso natural. Uma falha de túnel foi preservada.", ""]
for session, reviews in REVIEWS.items():
    data = json.loads((HERE / (session + ".json")).read_text())
    assert len(data["turns"]) == len(reviews), session
    kind = "controle" if session in ("07_controle_memoria", "09_controle_codigo") else "natural"
    transcript += ["## " + session + " (" + kind + ")", ""]
    for turn, (verdict, reason) in zip(data["turns"], reviews):
        result = turn["result"]
        record = {"session": session, "kind": kind, "turn": turn["number"],
                  "verdict": verdict, "reason": reason}
        records.append(record)
        transcript += ["### Turno " + str(turn["number"]) + " — " + verdict, "",
                       "**Usuário:**", "", turn["request"]["message"], "",
                       "**Crivo:**", "", result.get("response", json.dumps(result, ensure_ascii=False)), "",
                       "**Revisão:** " + reason, "",
                       "HTTP: " + str(turn["status"]) + "; tempo: " + str(turn["elapsed_seconds"]) +
                       " s; id: `" + str(result.get("id")) + "`; mecanismo: `" +
                       str(result.get("mechanism")) + "`; Transformer ancorado usado: " +
                       str(result.get("generation", {}).get("usada", False)) + ".", ""]
    (HERE / (session + ".json")).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

summary = {"method": "avaliação humana exploratória posterior; não benchmark cego",
           "production_commit": "1e40650f28b5feb236ff619a182e8c833fe9068f",
           "sessions": len(REVIEWS), "turns": len(records),
           "by_kind": {k: dict(Counter(r["verdict"] for r in records if r["kind"] == k))
                       for k in ("natural", "controle")}}
turns = [t for s in REVIEWS for t in json.loads((HERE / (s + ".json")).read_text())["turns"]]
summary["http"] = dict(Counter(str(t["status"]) for t in turns))
summary["transformer_realizations"] = sum(t["result"].get("generation", {}).get("usada", False) for t in turns)
summary["latency_success_seconds"] = {"median": statistics.median(t["elapsed_seconds"] for t in turns if t["status"] == 200),
                                     "max": max(t["elapsed_seconds"] for t in turns if t["status"] == 200)}
summary["limits"] = ["Perguntas e controles autorais; continuações adaptadas após observar respostas.",
                     "Contagem por turno inclui atos pequenos como confirmações; não equivale a sucesso de sessões.",
                     "Uma repetição de transporte e 22 turnos de comparação local ficam fora dos 61 turnos principais.",
                     "generation.usada refere-se ao Transformer ancorado; não mede todas as redes, como a GRU antiga ou a rede de efeitos de código.",
                     "Não foi enviado histórico superior a dez mensagens; não foi testada memória longa."]
(HERE / "avaliacao_manual.json").write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2) + "\n")
(HERE / "resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
(HERE / "CONVERSAS.md").write_text("\n".join(transcript))
weights = ["artefatos/geracao_pt/pesos_numpy.npz", "rede_geracao.json", "rede_intencao_gerativa.json", "memoria_sessao.py"]
manifest = {"purpose": "preservar a auditoria observada para regressão futura; não torna esses casos cegos",
            "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "congelamento.json"},
            "active_files_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in weights}}
(HERE / "congelamento.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False, indent=2))
