"""Congela 144 casos prospectivos antes do treino fatorado. Não treina."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter
from pathlib import Path
DIR=Path(__file__).resolve().parent; RAIZ=DIR.parents[1]; sys.path.insert(0,str(RAIZ))
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq,fonte_dialogo,tokenizar
FAT=RAIZ/'experimentos/corpus_fatorial_20261011/corpus_fatorial.json.gz'
INIT=RAIZ/'experimentos/gerador_historico_textual_20261010/inicializacao_sessoes.json.gz'
ATOS=('recordar_pessoa','recordar_objeto','corrigir_pessoa','guardar_hipotese','mensagem_sem_horario','pedir_detalhe')
CONTEXTOS=[
('arquivo','No arquivo, estou organizando o {objeto} com {nome} enquanto pensamos em {atividade}.'),
('atelier','No ateliê, estou preparando o {objeto} com {nome} para uma atividade de {atividade}.'),
('horta','Na horta, estou cuidando do {objeto} com {nome} antes de praticar {atividade}.'),
('observatorio','No observatório, estou conferindo o {objeto} com {nome} e planejando {atividade}.'),
('cozinha','Na cozinha, estou separando o {objeto} com {nome} antes de fazer {atividade}.'),
('galpao','No galpão, estou arrumando o {objeto} com {nome} enquanto combinamos {atividade}.'),]
VALORES=[
 dict(nome='Mirena-14',outro='Calino-23',objeto='livro',atividade='leitura'),
 dict(nome='Calino-23',outro='Sorela-32',objeto='texto',atividade='escrita'),
 dict(nome='Sorela-32',outro='Davino-47',objeto='projeto',atividade='desenho'),
 dict(nome='Davino-47',outro='Mirena-14',objeto='caderno',atividade='fotografia'),]
M={
'recordar_pessoa':['Quem era a pessoa ligada a isso?','Qual pessoa eu tinha mencionado aqui?','Me lembre quem participava comigo.','Quem ficou como a pessoa nessa situação?'],
'recordar_objeto':['Qual era o objeto envolvido nisso?','Que objeto eu tinha mencionado aqui?','Me lembre qual coisa ficou nessa situação.','Qual item estava envolvido nessa história?'],
'corrigir_pessoa':['Troque somente a pessoa: use {outro} no lugar de {atual}.','Corrija quem participa: agora é {outro}, não {atual}.','Atualize só o nome da pessoa para {outro}.','A pessoa mudou de {atual} para {outro}.'],
'guardar_hipotese':['Talvez eu faça {atividade}, mas ainda não decidi. Isso é certeza?','Estou pensando em fazer {atividade}. Já posso tratar como confirmado?','Existe a possibilidade de eu fazer {atividade}; isso já virou fato?','Considerei fazer {atividade}, sem decidir. Está confirmado?'],
'mensagem_sem_horario':['Escreva para {atual} convidando para {atividade}, sem escolher horário.','Faça uma mensagem para {atual} sobre {atividade}, mas sem dizer quando.','Quero chamar {atual} para {atividade}; escreva sem marcar hora.','Monte um convite curto para {atual} fazer {atividade}, sem horário.'],
'pedir_detalhe':['Quero pedir algo a {atual}, mas não disse o quê. O que falta?','Vou fazer um pedido para {atual}; ainda não informei qual coisa.','Preciso pedir algo a {atual}, mas falta dizer o objeto do pedido.','Quero pedir uma coisa a {atual}; ainda não contei qual é.'],}
R={
'recordar_pessoa':['A pessoa é {atual}.','{atual} é a pessoa.'],
'recordar_objeto':['O objeto é {objeto}.','Você estava falando do {objeto}.'],
'corrigir_pessoa':['Certo. Agora a pessoa é {outro}.','Entendi. Agora fica {outro}.'],
'guardar_hipotese':['Ainda não está confirmado.','Não. Isso ainda é uma possibilidade.'],
'mensagem_sem_horario':['{atual}, podemos combinar {atividade}?','{atual}, você quer combinar {atividade} comigo?'],
'pedir_detalhe':['O que você quer pedir a {atual}?','Qual é o pedido para {atual}?'],}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sig(e):
 b={k:e.get(k,[]) for k in ('mensagem','historico','resposta')};return hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ordem(i,j):
 a=list(ATOS);d=(i+3*j)%6;a=a[d:]+a[:d];return list(reversed(a)) if (i*j)%2 else a
def gerar():
 out=[]
 for ci,(fam,seed) in enumerate(CONTEXTOS):
  for vi,v in enumerate(VALORES):
   hist=[{'papel':'usuario','texto':seed.format(**v)},{'papel':'assistente','texto':'Entendi. A pessoa é {nome}, o objeto é {objeto} e a atividade é {atividade}.'.format(**v)}]; atual=v['nome']
   for t,op in enumerate(ordem(ci,vi),1):
    f=dict(v,atual=atual); msg=M[op][(ci+vi+t)%4].format(**f); resp=R[op][(ci+2*vi+t)%2].format(**f)
    e={'id':f'fatorado-holdout-{fam}-{vi}-{t}','split':'prospectivo','familia':fam,'turno':t,'operacao':op,'mensagem':msg,'historico':list(hist),'resposta':resp};out.append(e)
    hist.extend([{'papel':'usuario','texto':msg},{'papel':'assistente','texto':resp}])
    if op=='corrigir_pessoa':atual=v['outro']
 return out
def main():
 p=ler_json(DIR/'protocolo.json')
 if sha(FAT)!=p['treino']['corpus_sha256'] or sha(INIT)!=p['treino']['inicializacao_sha256']:raise SystemExit('Fonte mudou')
 xs=gerar()
 if len(xs)!=144 or Counter(x['operacao'] for x in xs)!=Counter({a:24 for a in ATOS}):raise SystemExit('Holdout desbalanceado')
 old=ler_json(FAT);old=old['exemplos'] if isinstance(old,dict) else old; oldsig={sig(x) for x in old}; oldmsg={x['mensagem'].casefold() for x in old}
 modelo=DialogoSeq2Seq(ler_json(INIT)); vocab=set(modelo.vocabulario); erros=[]
 for x in xs:
  fonte=set(fonte_dialogo(x['mensagem'],x['historico'],modelo.limite_fonte)); falta=[z for z in tokenizar(x['resposta'])+['<fim>'] if z not in vocab and z not in fonte]
  if falta:erros.append({'id':x['id'],'tokens':falta})
 aud={'exemplos':len(xs),'por_operacao':dict(Counter(x['operacao'] for x in xs)),'sobreposicao':sum(sig(x) in oldsig for x in xs),'mensagens_repetidas':sum(x['mensagem'].casefold() in oldmsg for x in xs),'alvos_nao_geraveis':erros}
 aud['aprovado']=aud['sobreposicao']==0 and aud['mensagens_repetidas']==0 and not erros
 saida={'congelado_antes_do_treino':True,'exemplos':xs,'auditoria':aud}; hp=DIR/'holdout_novo.json';hp.write_text(json.dumps(saida,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 man={'holdout_sha256':sha(hp),'gerador_sha256':sha(Path(__file__)),'protocolo_sha256':sha(DIR/'protocolo.json'),'exemplos':144,'aprovado':aud['aprovado']};(DIR/'manifesto_holdout.json').write_text(json.dumps(man,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'auditoria':aud,'manifesto':man},ensure_ascii=False,indent=2))
 if not aud['aprovado']:raise SystemExit('Holdout reprovado')
if __name__=='__main__':main()
