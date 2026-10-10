"""Acrescenta seis turnos realmente observados no site #127; não inventa casos."""
import copy
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent

def main():
    original = H.parent/'dialogo_20261010/casos_congelados.json'
    dados = copy.deepcopy(json.loads(original.read_text()))
    site = json.loads((H/'evidencias/site_127.json').read_text())
    sessoes = {s['sessao']:s for s in site['conversas']}
    novos = [
        ('conversa_desenho',4,'esclarecimento','retomar',['mariposa jardineira','caderno']),
        ('pronome_ambiguo',2,'memoria','consultar',['Dorlécio','guabiroba']),
        ('historia_restricoes',2,'escrita','corrigir',['coruja engenheira','jardim suspenso','um amigo']),
        ('historia_restricoes',3,'esclarecimento','restricao',['coruja engenheira','jardim suspenso','nome']),
        ('historia_restricoes',4,'escrita','historia',['coruja engenheira','jardim suspenso']),
        ('historia_restricoes',5,'esclarecimento','autoria',['coruja engenheira','jardim suspenso','gerador próprio']),
    ]
    for i,(sessao,turno,peca,ato,minimo) in enumerate(novos,1):
        ts=sessoes[sessao]['resultados'];anterior=ts[turno]['resposta']
        refs=minimo[:1] if sessao=='pronome_ambiguo' else minimo[:2]
        dados['casos'].append({'id':'pos127-%02d'%i,'origem':{'arquivo':'evidencias/site_127.json',
            'commit':'044ed446afd1c9b66c3b1ddd11b087c5c5a23658','sessao':sessao,'turno':turno+1},
            'entrada':{'texto':ts[turno]['usuario'],'anteriores':[t['usuario'] for t in ts[:turno]]},
            'usuario_queria':sessoes[sessao]['criterio'],'crivo_fez':{'id':anterior['id'],'resposta':anterior['response']},
            'esperado':{'peca':peca,'ato':ato,'referentes':refs,'conteudo_minimo':minimo,
                        'desvios_proibidos':['arroz','número primo','Pedido de escrita cancelado']},
            'grupos':['roteamento','tarefa_referente','falha_publica_127'],
            'resposta_minima_aceitavel':{'parafrase_permitida':True,'exige_historia':peca=='escrita',
                'frases':5 if turno==4 else None}})
    dados.update(versao=2,origem='37 casos intactos + seis turnos de três sessões reprovadas no HTTP público #127',
                 originais_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    p=H/'casos_congelados.json';raw=json.dumps(dados,ensure_ascii=False,indent=2)+'\n'
    if p.exists() and p.read_text()!=raw:raise ValueError('Conjunto já congelado')
    p.write_text(raw);(H/'SHA256').write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  casos_congelados.json\n')
    print('43 casos reais congelados')

if __name__=='__main__':main()
