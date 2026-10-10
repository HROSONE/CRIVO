"""Continuações autorais com estado selecionado; sem alvos das sondas."""
import copy,gzip,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent; ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))
from linguagem_gerativa import tokenizar
CORPOS={
'perda':[
'A personagem seguiu a pista para procurar @relato. Observou o caminho com cuidado. A busca avançou sem começar de novo.',
'A personagem conferiu a pista de @relato. Escolheu outra direção para procurar. A personagem ainda precisava procurar o objeto perdido.',
'A personagem procurou @relato pelo caminho conhecido. Uma dúvida pediu atenção. Decidiu conferir outra parte.',
'A personagem ainda procurou @relato. A busca mostrou o que faltava conferir. O objeto estava perdido.'],
'recuperacao':[
'A personagem guardou @relato em segurança. A busca terminou. Decidiu o próximo passo sem repetir o problema.',
'A personagem verificou que @relato estava seguro. O problema ficou resolvido. Depois observou o trabalho que faltava.',
'A personagem levou @relato com cuidado. O problema estava resolvido. Escolheu outra tarefa para começar.',
'A personagem guardou @relato com calma. Conferiu o resultado antes de continuar. Depois descansou.'],
'encontro':[
'A personagem decidiu examinar @relato. Observou outra parte do objeto. Uma pergunta mostrou o próximo passo.',
'A personagem conferiu @relato com cuidado. A personagem comparou os detalhes que tinha encontrado. A descoberta ficou mais clara.',
'A personagem observou @relato mais uma vez. Decidiu conferir a primeira ideia. Uma dúvida ainda pediu atenção.',
'A personagem guardou @relato com cuidado. O encontro trouxe uma descoberta. Restava procurar uma explicação.'],
'caixa_vazia':[
'A personagem conferiu @relato com surpresa. A personagem ainda precisava de uma explicação. Procurou o próximo passo antes de continuar.',
'A personagem observou @relato mais uma vez. A surpresa mostrou o que faltava conferir. Decidiu conferir outra parte.',
'A personagem levou @relato com cuidado. A personagem ainda precisava resolver aquela dúvida. Procurou um jeito de continuar.',
'A personagem guardou @relato em segurança. A pergunta ainda precisava de resposta. Decidiu continuar a procura.'],
'retorno':[
'A personagem voltou para @relato. Observou o caminho conhecido. O retorno mostrou o trabalho que faltava.',
'A personagem parou em @relato. Conferiu o resultado da última tentativa. Depois decidiu o próximo passo.',
'A personagem observou @relato com calma. Escolheu uma parte para começar. A tarefa avançou sem repetir a viagem.',
'A personagem ficou em @relato. Conferiu o trabalho diante de si. Depois descansou.'],
'devolucao':[
'A personagem deixou @relato no lugar combinado. A entrega terminou. Depois esperou uma resposta.',
'A personagem observou o lugar de @relato. A entrega terminou. Decidiu conferir o trabalho que faltava.',
'A personagem deixou @relato em segurança. O problema ficou mais claro. Escolheu outra tarefa para começar.',
'A personagem conferiu o lugar de @relato. A entrega encerrou aquela parte. Depois descansou.'],
'ajuda':[
'A personagem respondeu ao pedido de @relato. Procurou saber qual era o problema. A pergunta mostrou o próximo passo.',
'A personagem leu @relato mais uma vez. A personagem comparou o pedido com a primeira resposta. Decidiu saber o que ainda precisava saber.',
'A personagem guardou @relato com cuidado. Depois respondeu que tentaria ajudar. A personagem ainda precisava de uma explicação.',
'A personagem respondeu ao pedido de @relato. A conversa mostrou o que faltava resolver. Decidiu escutar antes de continuar.'],
'conserto':[
'A personagem procurou unir as partes de @relato. O rasgo pediu atenção. Conferiu o resultado da primeira tentativa.',
'A personagem examinou @relato. A personagem comparou as tentativas de unir as partes. O rasgo ficou mais claro.',
'A personagem cuidou do rasgo de @relato. A personagem tentou outro jeito de unir as partes. O trabalho avançou com cuidado.',
'A personagem conferiu o rasgo de @relato. Uma parte ficou pronta. Restava conferir o resultado.'],
'costura':[
'A personagem usou @relato com cuidado. Costurou para unir as partes. Conferiu o resultado da primeira tentativa.',
'A personagem conferiu @relato. Costurou outra parte do trabalho. O resultado mostrou um novo progresso.',
'A personagem usou @relato mais uma vez. Costurou o que ainda faltava. A tarefa avançou com calma.',
'A personagem guardou @relato com cuidado. Conferiu o resultado do trabalho. Depois descansou.'],
'companhia':[
'A personagem agradeceu a ajuda de @relato. Juntos, conferiram o trabalho que faltava. Juntos, decidiram o próximo passo.',
'A personagem retomou a conversa com @relato. Juntos, conferiram as tentativas. Uma ideia mostrou outra possibilidade.',
'A personagem recebeu uma ideia de @relato. Juntos, procuraram uma solução. A ajuda trouxe um novo progresso.',
'A personagem agradeceu a ajuda de @relato. Juntos, conferiram o resultado. Depois descansou.']}
def main():
 d=json.loads((H.parent/'diversidade_dialogo_20261010/corpus_gru.json').read_text());v=set(d['vocabulario']);novos=[]
 for classe,corpos in CORPOS.items():
  for corpo in corpos:
   assert not set(tokenizar(corpo))-v,(classe,set(tokenizar(corpo))-v)
  for lugar in (False,True):
   for companhia in (False,True):
    for acao in ('continuacao','final'):
     for estilo in ('neutro','simples'):
      for passo in range(4):
       for val in (False,True):
        slots={'tema1':'uma irara aprendiz' if not val else 'um ouriço viajante','relato':'um objeto declarado' if not val else 'um detalhe mencionado'}
        if lugar:slots['tema2']='um bosque distante' if not val else 'um castelo silencioso'
        if companhia:slots['detalhe']='uma colega' if not val else 'um aliado'
        prefix='Ficção: @tema1 '+('concluiu' if acao=='final' else 'continuou')+' a história'+(' com @detalhe' if companhia else '')+(' em @tema2' if lugar else '')+'. '
        ident=f'causal-{classe}-{lugar}-{companhia}-{acao}-{estilo}-{passo}-{val}'
        novos.append(dict(id=ident,dialogo=ident,familia='causal_'+classe,split='validacao' if val else 'treino',contexto=dict(acao=acao,slots=slots,estilo=estilo,variante=passo,mensagem='continuidade_causal '+classe+' estado_'+classe,historico=[],resposta_anterior='estado anterior '+classe),resposta=prefix+corpos[passo]+(' A história terminou.' if acao=='final' else ''),origem='Ligação autoral ao acontecimento selecionado; nenhuma entidade ou entrada das sondas.'))
 d['exemplos']+=novos;d.update(versao=7,origem='Corpus próprio anterior intacto, mais ligação causal autoral em dez classes e quatro passos.',limite='Classes/padrões/vetores compartilhados; não raciocínio neural geral nem validação independente.')
 p=H/'corpus_gru.json';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(H/'auditoria_corpus.json').write_text(json.dumps(dict(exemplos=len(d['exemplos']),novos=len(novos),treino=sum(e['split']=='treino' for e in d['exemplos']),validacao=sum(e['split']=='validacao' for e in d['exemplos']),vocabulario=len(v),tokens_novos=[],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),limite=d['limite']),ensure_ascii=False,indent=2)+'\n')
 print(len(d['exemplos']),len(novos),hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
