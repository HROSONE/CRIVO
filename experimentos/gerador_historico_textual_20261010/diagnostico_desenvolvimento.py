"""Localiza memorização versus uso textual; NÃO entra na aprovação inédita."""
import json
import sys
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import gravar
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar, fonte_dialogo
from arquivos_contextuais import ler_json


def executar():
    exemplos=json.loads((DIR/'corpus_rodada2.json').read_text())['exemplos']
    por_familia={}
    for e in exemplos:
        if e['split']=='treino':
            por_familia.setdefault(e['familia'],e)
    modelo=DialogoSeq2Seq(ler_json(DIR/'checkpoint_rodada2.json.gz'))
    grupos={}
    for modo in ['com_historico','sem_historico']:
        saidas=[]
        for e in por_familia.values():
            historico=e['historico'] if modo=='com_historico' else []
            r=modelo.gerar(e['mensagem'],historico,max_tokens=64)
            saidas.append({'familia':e['familia'],'mensagem':e['mensagem'],'historico':historico,
                'alvo':e['resposta'],'saida':r,
                'igual_literal': [t.casefold() for t in r['tokens']]==[t.casefold() for t in tokenizar(e['resposta'])]})
        grupos[modo]={'exemplos':len(saidas),'iguais_literais':sum(s['igual_literal'] for s in saidas),'saidas':saidas}
    # Mesma pergunta treinada, entidades fora do treino: só teste de cópia.
    copias=[]
    for nome in ['Nuvaira-58','Eldóvia-71','Zarilu-26','Ocrênio-34']:
        h=[{'papel':'usuario','texto':f'Meu nome é {nome}.'}]
        r=modelo.gerar('Como eu me chamo?',h,max_tokens=64)
        copias.append({'nome':nome,'mensagem':'Como eu me chamo?','historico':h,'saida':r,
                      'nome_preservado':nome in r['tokens']})
    resultado={'limite':'100 pedidos/alvos vistos no treino. Novos nomes com MESMA formulação são só controle lexical; não são o holdout de conversa nem evidência de naturalidade.',
        'memorizar_cem_padroes':grupos,'copia_com_pergunta_treinada':copias,
        'copias_corretas':sum(c['nome_preservado'] for c in copias),'aprovado':False,'ativo_no_chat':False}
    gravar('diagnostico_desenvolvimento.json',resultado)
    print(json.dumps({'literais':{k:v['iguais_literais'] for k,v in grupos.items()},
        'copias_corretas':resultado['copias_corretas']},ensure_ascii=False))


if __name__=='__main__':
    executar()
