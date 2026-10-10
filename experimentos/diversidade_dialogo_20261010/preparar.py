"""Variações autorais para as mesmas classes; vocabulário e arquitetura intactos."""
import copy
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))
from linguagem_gerativa import tokenizar
spec=importlib.util.spec_from_file_location('preparacao_anterior',H.parent/'escrita_acontecimentos_20261010/preparar.py')
anterior=importlib.util.module_from_spec(spec);spec.loader.exec_module(anterior)
VARIANTES={
'perda':[
'A personagem observou o caminho. Procurou uma pista para continuar a busca. Depois decidiu onde procurar.',
'A personagem parou para pensar. Procurou o objeto com cuidado. Uma pista mostrou outra direção.',
'A personagem procurou pelo caminho conhecido. Conferiu os detalhes diante de si. Decidiu continuar a busca.'],
'recuperacao':[
'A personagem verificou o objeto recuperado. Depois guardou tudo com cuidado. Depois decidiu o próximo passo.',
'A personagem guardou o objeto em segurança. Conferiu que estava seguro. O problema ficou resolvido.',
'A personagem observou o que havia recuperado. Depois guardou o objeto com calma. A busca terminou.'],
'encontro':[
'A personagem parou diante do objeto. Observou os detalhes com cuidado. Decidiu examinar outra parte.',
'A personagem observou o que tinha encontrado. Uma pergunta pediu atenção. Procurou uma explicação.',
'A personagem decidiu examinar o objeto. Conferiu os detalhes diante de si. Uma nova pista apareceu.'],
'caixa_vazia':[
'A personagem conferiu o objeto. A surpresa pediu uma explicação. Depois decidiu o próximo passo.',
'A personagem parou com surpresa. Observou o que estava diante de si. Decidiu examinar mais uma vez.',
'A personagem conferiu tudo com cuidado. Uma dúvida mostrou outra direção. Procurou um jeito de continuar.'],
'retorno':[
'A personagem voltou com calma. Observou o caminho conhecido. Depois decidiu o que ainda faltava.',
'A personagem decidiu o próximo passo. Depois voltou pelo caminho conhecido. O retorno trouxe uma nova ideia.',
'A personagem voltou com cuidado. Conferiu o caminho diante de si. O retorno encerrou aquela parte.'],
'devolucao':[
'A personagem deixou o objeto com cuidado. Conferiu o lugar combinado. Depois esperou uma resposta.',
'A personagem conferiu o objeto. A entrega trouxe uma nova possibilidade. O problema ficou mais claro.',
'A personagem deixou o objeto em segurança. A entrega encerrou aquela parte. Depois decidiu o próximo passo.'],
'ajuda':[
'A personagem leu o pedido. Depois respondeu com cuidado. Procurou saber qual era o problema.',
'A personagem respondeu ao pedido de ajuda. Uma pergunta mostrou o próximo passo. Depois procurou uma solução.',
'A personagem observou o pedido. Depois respondeu que tentaria ajudar. Depois decidiu o próximo passo.'],
'conserto':[
'A personagem observou o rasgo. Escolheu uma parte para começar. Procurou unir tudo com cuidado.',
'A personagem conferiu o que precisava mudar. Procurou unir as partes. O rasgo pediu uma nova tentativa.',
'A personagem examinou o trabalho. Decidiu unir as partes. O rasgo pediu atenção na tentativa.'],
'costura':[
'A personagem observou o fio recebido. Costurou com calma. O trabalho mostrou um novo progresso.',
'A personagem usou o fio com cuidado. Costurou para unir as partes. Conferiu o resultado da tentativa.',
'A personagem conferiu o fio. Costurou outra parte. A ajuda trouxe uma nova solução.'],
'companhia':[
'A personagem agradeceu a ajuda. Juntos, conferiram o que faltava. Depois decidiram o próximo passo.',
'A personagem recebeu a ajuda com calma. Juntos, procuraram uma solução. O encontro trouxe uma nova ideia.',
'A personagem recebeu uma ideia da companhia. Juntos, decidiram o próximo passo. A ajuda mostrou outra possibilidade.']}
# Cada versão original continua disponível; três alternativas usam apenas tokens existentes.
def main():
    d=json.loads((H.parent/'escrita_acontecimentos_20261010/corpus_gru.json').read_text());vocab=set(d['vocabulario']);mudados=0
    for classe,corpos in VARIANTES.items():
        for corpo in corpos:
            desconhecidos=set(tokenizar(corpo))-vocab
            if desconhecidos:raise ValueError((classe,sorted(desconhecidos)))
    for e in d['exemplos']:
        familia=e['familia']
        if e['id'].startswith('evento-') and familia in VARIANTES:
            v=e['contexto']['variante']%4
            if v:
                old=anterior.EVENTOS[familia][1];new=VARIANTES[familia][v-1]
                # A forma conjunta faz parte da supervisão anterior.
                if e['contexto']['slots'].get('detalhe'):
                    old=old.replace('Conferiu o objeto','Juntos, conferiram o objeto').replace('A personagem respondeu','Juntos, responderam')
                    new=new.replace('A personagem respondeu','Juntos, responderam')
                assert old in e['resposta'],e['id']
                e['resposta']=e['resposta'].replace(old,new,1);mudados+=1
            e['origem']='Reação autoral alternativa à mesma classe/cena; não usa alvos das sondas.'
    d['versao']=6;d['origem']='Mesmas 9.024 supervisões próprias; dez classes recebem quatro realizações condicionadas à cena.'
    d['limite']='Padrões e vetores de contexto compartilhados entre partições, com entidades distintas. Não demonstra planejamento ou generalização de assuntos.'
    p=H/'corpus_gru.json';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    auditoria={'exemplos':len(d['exemplos']),'alterados':mudados,'vocabulario':len(d['vocabulario']),'tokens_novos':[],
      'treino':sum(e['split']=='treino' for e in d['exemplos']),'validacao':sum(e['split']=='validacao' for e in d['exemplos']),
      'corpus_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sondas_no_treino':False,
      'limite':'Quatro padrões por classe; treino/validação compartilham padrões e vetores após mascarar entidades. Separação por nomes não é avaliação independente.'}
    (H/'auditoria_corpus.json').write_text(json.dumps(auditoria,ensure_ascii=False,indent=2)+'\n');print(auditoria)
if __name__=='__main__':main()
