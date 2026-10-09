"""Seleciona somente falhas/parciais já observadas; executar antes do candidato."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
OUT = H.parent / 'roteamento_natural_20261009'
OUT.mkdir(exist_ok=True)
# Sessão, turno original, turnos anteriores relevantes, peça, ato, referentes,
# intenção humana, evidências mínimas de resposta útil, desvios vedados.
specs = [
('01_descoberta',1,[], 'esclarecimento','capacidades',[], 'Conhecer capacidades do produto', ['posso'], ['negação com segurança']),
('01_descoberta',2,[1], 'esclarecimento','capacidades',[], 'Receber ajuda em linguagem natural', ['posso'], ['hum, não entendi']),
('01_descoberta',3,[2], 'esclarecimento','exemplos',[], 'Receber três exemplos concretos de perguntas', ['1.', '2.', '3.'], ['hum, não entendi']),
('01_descoberta',6,[4,5], 'esclarecimento','funcionamento',[], 'Cumprir oferta de explicar o funcionamento', ['fatos','própr'], ['essa sobre mim']),
('02_ciencia',2,[1], 'escrita','exemplo',['céu'], 'Explicar o pôr do sol com exemplo acessível', ['luz'], ['você contou']),
('02_ciencia',4,[1,3], 'fato','comparar',['Marte','céu'], 'Distinguir as causas das duas cores vermelhas', ['Marte','luz'], ['reconheci o assunto']),
('02_ciencia',5,[1,3], 'fato','comparar',['Marte','céu'], 'Comparar explicitamente os mecanismos das cores', ['Marte','luz'], ['não tenho evidência']),
('03_pessoas',1,[], 'memoria','registrar',['Brena','Tácio'], 'Registrar as duas pessoas e preferências no relato composto', ['Brena','Tácio'], ['número primo']),
('03_pessoas',3,[1], 'memoria','corrigir',['Brena'], 'Atualizar a preferência feminina por pronome para cuscuz', ['Brena','cuscuz'], ['que bom']),
('03_pessoas',4,[1,3], 'memoria','sugerir',['Brena'], 'Preparar o lanche segundo a preferência corrigida', ['Brena','cuscuz'], ['número primo','tapioca']),
('03_pessoas',6,[1,5], 'memoria','sugerir',['Brena'], 'Retomar a pessoa após correção explícita de contexto', ['Brena','cuscuz'], ['número primo']),
('03_pessoas',7,[1,3], 'memoria','consultar',['Tácio'], 'Consultar preferência do primo familiar', ['Tácio','bolo de fubá'], ['número primo']),
('04_plano',1,[], 'calculo','planejar',['inglês','louça'], 'Dividir o orçamento de 35 minutos entre tarefas; pedir duração faltante', ['35','minutos'], ['arroz','refogue']),
('04_plano',3,[1,2], 'calculo','hipotese',['inglês','louça','descanso'], 'Reservar cinco minutos de descanso sem mudar de domínio', ['18','minutos'], ['arroz','refogue']),
('04_plano',4,[2,3], 'calculo','planejar',['inglês','louça','descanso'], 'Organizar três atividades dentro de 35 minutos', ['35','12','5','18'], ['arroz','refogue']),
('04_plano',5,[2,3], 'calculo','corrigir',['inglês','louça','descanso'], 'Atualizar orçamento para 20 mantendo louça e descanso; inglês fica com 3', ['20','12','5','3'], ['arroz','refogue']),
('04_plano',6,[2,3], 'calculo','planejar',['inglês','louça','descanso'], 'Reparar a tarefa após desvio para receita', ['louça','descanso'], ['arroz','refogue','você contou']),
('04_plano',8,[1,7], 'calculo','explicar',['inglês'], 'Relacionar os 18 minutos calculados à tarefa de inglês', ['18','inglês'], ['arroz','refogue']),
('06_criacao',2,[1], 'escrita','historia',['capivara astronauta'], 'Escrever história curta com a personagem declarada anteriormente', ['capivara','astronauta'], ['essa personagem, umas cinco frases']),
('06_criacao',3,[1,2], 'escrita','corrigir',['capivara astronauta','amigo'], 'Mudar o final para encontro com amigo e preservar personagem', ['capivara','amigo'], ['o que você já tentou']),
('06_criacao',4,[1,2], 'esclarecimento','autoria',['história'], 'Explicar a origem da história gerada, sem inventar fonte externa', ['gerador','própr'], ['qual história você quer dizer']),
('05_codigo',7,[2,6], 'programacao','analisar',['precos','total'], 'Acionar motor JS após preâmbulo; informar limites do subconjunto se necessário', ['código'], ['gostos','vida fora da conversa']),
('08_acervo',2,[1], 'fato','comparar',['DNA','RNA'], 'Comparar DNA e RNA referindo-se ao conceito anterior', ['DNA','RNA'], ['quais opções']),
('08_acervo',3,[1], 'escrita','topicos',['DNA'], 'Reformatar a explicação disponível em tópicos para criança', ['DNA'], ['não tenho uma definição']),
('08_acervo',4,[1,3], 'fato','consultar',['Moisés'], 'Mudar explicitamente de tema para pergunta factual bíblica', ['Moisés'], ['ideia','vontade','próximo passo']),
]
reviews = {(r['session'],r['turn']):r for r in json.loads((H/'avaliacao_manual.json').read_text())['records']}
cases=[]
for i,(s,t,prev,piece,act,refs,wanted,required,forbidden) in enumerate(specs,1):
    assert reviews[s,t]['verdict'] in ('falhou','parcial')
    session=json.loads((H/(s+'.json')).read_text())
    turn=session['turns'][t-1]
    contexts=[session['turns'][n-1] for n in prev]
    assert len(contexts)<=2 and all(x['number']<t for x in contexts)
    cases.append({'id':'real-%02d'%i,'origem':{'sessao':s,'turno':t,'sha256':hashlib.sha256((H/(s+'.json')).read_bytes()).hexdigest()},
                  'entrada':{'texto':turn['request']['message'],'anteriores':[x['request']['message'] for x in contexts]},
                  'usuario_queria':wanted,'crivo_fez':{'id':turn['result']['id'],'resposta':turn['result']['response']},
                  'esperado':{'peca':piece,'ato':act,'referentes':refs,'conteudo_minimo':required,'desvios_proibidos':forbidden}})
target=OUT/'casos_congelados.json'
assert not target.exists(), 'Conjunto já congelado; não sobrescrever.'
target.write_text(json.dumps({'versao':1,'base':'1e40650f28b5feb236ff619a182e8c833fe9068f','natureza':'regressão de casos reais já inspecionados; não teste cego',
                            'criterios':{'peca_correta_minimo':18,'total':25,'desvios_permitidos':0,'referentes':'preservados; nenhum fato inventado para resolver ambiguidade'},'casos':cases},ensure_ascii=False,indent=2)+'\n')
(OUT/'SHA256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  casos_congelados.json\n')
print('Congelados',len(cases),'casos;',hashlib.sha256(target.read_bytes()).hexdigest())
