"""Acrescenta somente turnos realmente executados, antes da implementação."""
import hashlib
import json
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    base=H.parent/'dialogo_v2_20261010/casos_congelados.json'
    d=json.loads(base.read_text()); evidence=json.loads((H/'baseline_motor.json').read_text())
    for s in evidence['sessoes'][3:]:
        hist=[]
        personagem={'amigo_sem_cenario':'lontra relojoeira','amigo_com_cenario':'esquilo pintor','aventura_natural':'raposa navegadora'}[s['id']]
        for i,row in enumerate(s['resultados']):
            refs=[personagem]
            if s['id']=='amigo_com_cenario':refs+=['torre distante']
            if i>=2 and s['id']!='aventura_natural':refs += ['uma amiga' if s['id']=='amigo_sem_cenario' else 'um parceiro']
            if i>=3 and s['id']=='aventura_natural':refs+=['uma companheira']
            ato='restricao' if row['usuario'].startswith('Não invente') else 'corrigir' if row['usuario'].startswith('Mude') else 'continuar' if row['usuario'].startswith('Continue') else 'historia'
            d['casos'].append(dict(id='pos128-'+s['id']+'-'+str(i+1),
                origem={'arquivo':'baseline_motor.json','commit':'3e8eed593288af6be17c83d11aeae5d14d1e598e','sessao':s['id'],'turno':i+1,'autor':'sonda do agente realmente executada'},
                entrada={'texto':row['usuario'],'anteriores':list(hist)},usuario_queria='Entregar a escrita pedida e preservar personagem, cenário e companhia; restrição não cancela a tarefa.',
                crivo_fez={'id':row['resposta']['id'],'resposta':row['resposta']['response']},
                esperado={'peca':'esclarecimento' if ato=='restricao' else 'escrita','ato':ato,'referentes':refs,'conteudo_minimo':refs,'desvios_proibidos':['número primo','Pedido de escrita cancelado','em uma amiga','em um parceiro','em uma companheira']},
                grupos=['roteamento','tarefa_referente','sonda_publica_128'],resposta_minima_aceitavel={'parafrase_permitida':True,'exige_historia':ato!='restricao','frases':5 if i==5 and ato!='restricao' else None}))
            hist.append(row['usuario'])
    d['versao']=3;d['origem']='43 casos anteriores intactos + 18 turnos realmente observados em sondas autorais novas; não sessões humanas.'
    d['base']= '3e8eed593288af6be17c83d11aeae5d14d1e598e';d['originais_sha256']=hashlib.sha256(base.read_bytes()).hexdigest()
    p=H/'casos_congelados.json';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(H/'SHA256').write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  casos_congelados.json\n');print('congelados',len(d['casos']))
if __name__=='__main__':main()
