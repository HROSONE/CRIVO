"""Promove cópia após gates dos dois modos; original permanece false/false."""
import gzip,hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))
import conversa_dialogo as cd
def carregar(nome):return json.loads((H/nome).read_text())
def modulo(nome,arquivo):
 s=importlib.util.spec_from_file_location(nome,arquivo);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 novo=modulo('juiz_causal',H/'avaliar.py');folego=modulo('juiz_folego',H/'avaliar_folego.py');antigo=modulo('juiz_114',H.parent/'diversidade_dialogo_20261010/verificar_114.py');div=modulo('juiz_div',H.parent/'diversidade_dialogo_20261010/avaliar.py');util=modulo('juiz_util',H.parent/'contexto_pratico_20261010/avaliar.py');aliases=modulo('juiz_aliases',H/'avaliar_aliases.py');medidas={}
 for modo in ('motor','http'):
  c=novo.pontuar(carregar('piloto_'+modo+'.json'));f=folego.pontuar(carregar('piloto_folego_'+modo+'.json'));a=antigo.verificar(carregar('piloto_114_'+modo+'.json'));v=div.pontuar(carregar('piloto_diversidade_'+modo+'.json'));p=util.pontuar(carregar('piloto_40_'+modo+'.json'))
  assert c['conversas_mantem_fio']>=6 and c['esclarecimentos']==2 and c['referentes_ausentes']==c['trocas_dominio']==c['contradicoes_estado']==0
  al=aliases.pontuar(carregar('piloto_aliases_'+modo+'.json'));assert al['aprovadas']==3
  assert f['aprovadas']==2 and v['sessoes_aprovadas']==8 and v['problemas_fidelidade']==0 and p['corretos']==40 and p['desvios']==0
  medidas[modo]=dict(continuidade=c,folego=f,aliases=al,antigos=a,diversidade=v,praticos=p)
  # Confirma que todos os replays medem o candidato e não o modelo antigo.
  for arquivo in ('piloto_'+modo+'.json','piloto_folego_'+modo+'.json','piloto_diversidade_'+modo+'.json','piloto_aliases_'+modo+'.json'):
   for s in carregar(arquivo)['sessoes']:
    for r in s['resultados']:
     g=r['resposta'].get('dialogue_generation',{})
     if g.get('usada'):assert g['checkpoint_sha256']==cd.ORIGEM_V7_SHA256 and g['experimental'] is True
 repro=carregar('reproducibilidade.json');assert repro['identico_byte_a_byte'] and repro['sha256']==cd.ORIGEM_V7_SHA256
 raw=(H/'checkpoint_gru_dialogo.json.gz').read_bytes();assert hashlib.sha256(raw).hexdigest()==cd.ORIGEM_V7_SHA256;d=json.loads(gzip.decompress(raw));assert d['controle']=={'aprovado':False,'ativo_no_chat':False}
 assert hashlib.sha256((H/'corpus_gru.json').read_bytes()).hexdigest()==cd.CORPUS_V7_SHA256
 a=dict(checkpoint_origem_sha256=cd.ORIGEM_V7_SHA256,corpus_sha256=cd.CORPUS_V7_SHA256,casos_sha256=cd.CASOS_V5_SHA256,atos=sorted(cd.ATOS),diversidade_sha256=cd.DIVERSIDADE_V6_SHA256,praticos_sha256=cd.PRATICOS_V6_SHA256,continuidade_sha256=cd.CAUSAL_V7_SHA256,folego_sha256=cd.FOLEGO_V7_SHA256,aliases_sha256=cd.ALIASES_V7_SHA256,treino_reproduzido_byte_a_byte=True,
 metricas=dict(casos_total=114,casos_motor=medidas['motor']['antigos']['casos'],casos_http=medidas['http']['antigos']['casos'],casos_antigos_motor=79,casos_antigos_http=79,historias_entregues=52,trocas_dominio=0,referentes_ausentes=0,desvios_proibidos=0,conversas_mantem_fio=min(medidas[m]['continuidade']['conversas_mantem_fio'] for m in medidas),diversidade_turnos=48,diversidade_motor=8,diversidade_http=8,diversidade_problemas_fidelidade=0,praticos_motor=40,praticos_http=40,continuidade_turnos=88,continuidade_motor=medidas['motor']['continuidade']['conversas_mantem_fio'],continuidade_http=medidas['http']['continuidade']['conversas_mantem_fio'],esclarecimentos_motor=2,esclarecimentos_http=2,contradicoes_estado=0,folego_motor=2,folego_http=2,aliases_motor=3,aliases_http=3),
 limites='Seleção estrutural do objeto/estado e quatro passos supervisionados nas classes conhecidas. Ficção, não fatos de sessão; sem planejamento livre, compreensão neural geral, humanos ou fôlego ilimitado.')
 d.update(controle={'aprovado':True,'ativo_no_chat':True},aprovacao=a,limite=a['limites']);assert cd.aprovacao_valida(d)
 base=(H/'checkpoint_base_134.json.gz').read_bytes();assert (ROOT/'rede_dialogo_conversa.json.gz').read_bytes()==base
 promoted=gzip.compress(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0);a['checkpoint_producao_sha256']=hashlib.sha256(promoted).hexdigest()
 (H/'aprovacao.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');(H/'validacao_local.json').write_text(json.dumps(medidas,ensure_ascii=False,indent=2)+'\n');(ROOT/'rede_dialogo_conversa.json.gz').write_bytes(promoted);print('Cópia aprovada',a['checkpoint_producao_sha256'])
if __name__=='__main__':main()
