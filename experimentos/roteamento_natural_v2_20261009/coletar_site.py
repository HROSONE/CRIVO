"""Sonda pública registrada antes de alterar o motor; nenhuma memória injetada."""
import concurrent.futures
import datetime
import json
from pathlib import Path
import urllib.request

H = Path(__file__).resolve().parent
URL = 'https://crivo-mauve.vercel.app/api/chat'
PROBES = [
 ('pos-01', 'Nunca usei você. O que consegue fazer?', []),
 ('pos-02', 'O que meu primo gosta?', ['Meu primo Zaurélio gosta de kiwi e não gosta de leite.']),
 ('pos-03', 'O que meu primo gosta agora?', ['Meu primo Zaurélio gosta de kiwi e não gosta de leite.', 'Ele mudou de ideia: agora gosta de manga.']),
 ('pos-04', 'Em que pode me ajudar?', []),
 ('pos-05', 'Mostra o que sabe fazer.', []),
 ('pos-06', 'O que ela não gosta?', ['Minha amiga Nerúbia prefere chá de hibisco.']),
 ('pos-07', 'O que meu primo prefere?', ['Meu primo Talveno prefere chá. Meu primo Orestino prefere café.']),
 ('pos-08', 'O que Véspera gosta?', ['Minha prima Véspera gosta de goiaba.', 'Ela não gosta mais de goiaba. Agora ela gosta de pêssego.']),
 ('pos-09', 'O que ele gosta?', ['Meu primo Talveno prefere chá. Meu primo Orestino prefere café.']),
 ('pos-10', 'E o RNA?', ['O que é DNA?']),
 ('pos-11', 'Agora me diga a cor de Marte.', ['Minha prima Véspera prefere goiaba.']),
 ('pos-12', 'Desses 30 minutos, separa 5 para descanso.', ['Tenho 30 minutos para estudar italiano.']),
 ('pos-13', 'Quanto tempo sobrou?', ['Tenho 30 minutos disponíveis.', 'Vou gastar 12 minutos na louça e 5 minutos no descanso.']),
 ('pos-14', 'Ela pode fazer o quê?', ['Minha amiga Nerúbia não pode beber leite.']),
 ('pos-15', 'O que você guardou sobre meu tio?', ['Meu tio Caldrino prefere suco de umbu.']),
 ('pos-16', 'Sem trocar a pessoa: o que minha amiga prefere?', ['Minha amiga Nerúbia prefere chá de hibisco.']),
 ('pos-17', 'Não quero uma receita. Quanto resta do tempo?', ['Tenho 30 minutos disponíveis.', 'Vou gastar 12 minutos na louça e 5 minutos no descanso.']),
 ('pos-18', 'Quero uma sugestão para ele respeitando a restrição.', ['Meu primo Talveno prefere leite. Ele não pode beber leite.']),
]


def consultar(probe):
 ident, texto, anteriores = probe
 payload = {'message': texto, 'history': anteriores}
 req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
 inicio = datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(req, timeout=35) as r:
   resposta = json.load(r); status=r.status
  return {'id':ident,'quando_utc':inicio,'pedido':payload,'http_status':status,'resposta':resposta}
 except Exception as e:
  return {'id':ident,'quando_utc':inicio,'pedido':payload,'erro_transporte':str(e)}


def main():
 with urllib.request.urlopen(URL, timeout=30) as r: health=json.load(r)
 out={'url':URL,'health_antes':health,'probes':[]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for row in pool.map(consultar, PROBES):
   out['probes'].append(row)
   (H/'site_antes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
   r=row.get('resposta',{})
   print(row['id'],r.get('id'),r.get('response',row.get('erro_transporte')),flush=True)
 with urllib.request.urlopen(URL, timeout=30) as r: out['health_depois']=json.load(r)
 (H/'site_antes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__': main()
