"""Cabeça própria sobre o transformer 2,6M congelado; sem dados retidos.

Treina classificação de operação, não prova nem respostas. Templates de dev
e teste são separados do treino. O controle de conversas não é aberto aqui.
"""
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from pontuador_frases import Pontuador

CLASSES=['outro','custos','tempo','agenda','regra']
TEMPLATES={
 'treino':[
  ['Qual é a capital de {lugar}?','Como funciona a {coisa}?','Estou {emocao} com o que aconteceu.','Quero inventar uma história sobre {coisa}.','Você pode me explicar {coisa}?','Será que minha opinião sobre {coisa} faz sentido?'],
  ['Qual das opções custa menos?','Quanto dá a diferença dos preços?','A opção {a} custa {x} reais e a {b} custa {y} reais. Qual é a mais barata?','Qual valor total fica menor?','Quero comparar os custos dessas duas escolhas.','A taxa mudou para {x} reais. Recalcule os preços.'],
  ['Tenho {x} minutos e a tarefa dura {y}. Quanto tempo sobra?','Dá para encaixar as atividades no tempo disponível?','Quero saber se tudo cabe no horário que tenho.','Quantos minutos ainda restam?','A tarefa demora {x} minutos agora. Ainda dá tempo?','O trajeto ocupa {x} minutos, sobra quanto?'],
  ['Qual dia serve para todos?','{a} só pode {dia}. Quando podemos encontrar?','{b} também está livre {dia}. Podemos marcar?','Existe um dia em comum entre as agendas?','Quais dias estão disponíveis para a reunião?','Agora {a} não consegue {dia}. O encontro continua possível?'],
  ['{a} tem {objeto}, mas não tem {objeto2}. Cumpre os requisitos?','A regra exige {objeto} e {objeto2}. Ele pode entrar?','{b} ganhou {objeto}. Pela regra, mudou alguma coisa?','Quais requisitos ainda faltam?','Ele perdeu {objeto}. Ainda satisfaz as condições?','Basta {objeto} ou {objeto2}. Ela cumpre a regra?']
 ],
 'dev':[
  ['Por que {coisa} existe?','Estou pensando sobre {coisa}. Que sentido isso tem?'],
  ['Entre os valores informados, onde gasto menos?','Quanto economizaria pela escolha mais econômica?'],
  ['O plano ultrapassa meu limite de minutos?','É possível terminar antes de acabar o tempo livre?'],
  ['Quando as disponibilidades coincidem?','Os participantes conseguem se reunir em alguma data?'],
  ['Com esses itens, a condição declarada foi atendida?','Consegue cumprir o que a regra pede?']
 ],
 'teste':[
  ['Eu me senti {emocao}. Você entende?','Crie uma cena com {coisa}.','Qual é sua opinião sobre {coisa}?'],
  ['Qual delas pesa menos no bolso?','Existe empate entre os gastos das alternativas?','Compare o desembolso necessário em cada caso.'],
  ['Quanto resta da minha janela de tempo?','Qual é o saldo de minutos depois dessas atividades?','Preciso de mais minutos do que tenho?'],
  ['Há uma data que combine com os dias livres das pessoas?','Quando ambos estão desocupados?','Temos compatibilidade de agenda?'],
  ['A situação atende às exigências que descrevi?','O que falta para satisfazer essa condição?','Esses objetos são suficientes pelos requisitos declarados?']
 ]}


def corpus(split,n):
    rng=random.Random({'treino':619,'dev':823,'teste':1049}[split])
    nomes={'treino':['Ana','Beto','Dora','Leo'],'dev':['Tito','Vera'],'teste':['Nair','Zeca']}[split]
    exemplos=[]
    for label,templates in enumerate(TEMPLATES[split]):
        for i in range(n):
            dados=dict(a=rng.choice(nomes),b=rng.choice(nomes),x=rng.randrange(2,160),y=rng.randrange(2,160),
                       dia=rng.choice(['segunda','terça','quarta','quinta','sexta','sábado','domingo']),
                       objeto=rng.choice(['chave','selo','ticket','senha']),objeto2=rng.choice(['mapa','cartão','ficha','medalha']),
                       emocao=rng.choice(['triste','cansado','animado','inseguro']),coisa=rng.choice(['energia','chuva','música','viagem']),
                       lugar=rng.choice(['Chile','França','Japão']))
            exemplos.append(dict(texto=templates[i%len(templates)].format(**dados),classe=CLASSES[label],familia=i%len(templates)))
    return exemplos


def main():
    pasta=Path(sys.argv[1]);pasta.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1);torch.manual_seed(771)
    rng=np.random.default_rng(771)
    g=Pontuador(ROOT/'artefatos/linguagem_profunda')
    dados={s:corpus(s,n) for s,n in [('treino',144),('dev',40),('teste',48)]}
    # Dev e teste usam famílias diferentes; frases com campos constantes podem
    # repetir dentro de um split, nunca cruzam os splits.
    assert not (set(c['texto'] for c in dados['treino']) & set(c['texto'] for c in dados['dev']+dados['teste']))
    features={};inicio=time.monotonic()
    for split,cs in dados.items():
        (pasta/(split+'.json')).write_text(json.dumps(cs,ensure_ascii=False,indent=2)+'\n')
        fs=[]
        for start in range(0,len(cs),16):
            seqs=[g.prefixo(c['texto']) for c in cs[start:start+16]]
            h=g.ocultos_lote(seqs)
            fs.extend(np.concatenate([h[i,:len(ids)].mean(0),h[i,len(ids)-1]]) for i,ids in enumerate(seqs))
        features[split]=np.stack(fs)
        print('features',split,len(fs),round(time.monotonic()-inicio,1),flush=True)
    media=features['treino'].mean(0);desvio=features['treino'].std(0).clip(.01)
    xs={s:torch.tensor((v-media)/desvio,dtype=torch.float32) for s,v in features.items()}
    ys={s:torch.tensor([CLASSES.index(c['classe']) for c in dados[s]]) for s in dados}
    head=torch.nn.Linear(xs['treino'].shape[1],len(CLASSES))
    opt=torch.optim.AdamW(head.parameters(),lr=.01,weight_decay=.05)
    melhor=None;nota=-1;hist=[]
    for epoca in range(1,101):
        for inds in np.array_split(rng.permutation(len(xs['treino'])),6):
            opt.zero_grad();loss=torch.nn.functional.cross_entropy(head(xs['treino'][inds]),ys['treino'][inds]);loss.backward();opt.step()
        if epoca%10==0:
            with torch.no_grad():
                score=float((head(xs['dev']).argmax(-1)==ys['dev']).float().mean())
            hist.append(dict(epoca=epoca,acuracia_dev=score))
            if score>nota:
                nota=score;melhor={k:v.detach().clone() for k,v in head.state_dict().items()};escolhida=epoca
    head.load_state_dict(melhor)
    teste=[]
    with torch.no_grad():
        ps=head(xs['teste']).softmax(-1).numpy()
    for c,prob in zip(dados['teste'],ps):
        idx=int(prob.argmax());teste.append(dict(c,predita=CLASSES[idx],confianca=float(prob[idx]),correto=idx==CLASSES.index(c['classe'])))
    precisao=sum(c['correto'] for c in teste)/len(teste)
    aceitos=[c for c in teste if c['confianca']>=.9]
    pa=sum(c['correto'] for c in aceitos)/len(aceitos) if aceitos else 0
    # Não basta bom agregado: cada classe também precisa atingir 90%.
    por_classe={s:sum(c['correto'] for c in teste if c['classe']==s)/sum(c['classe']==s for c in teste) for s in CLASSES}
    aprovado=precisao>=.90 and pa>=.98 and min(por_classe.values())>=.90
    sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
    estado=dict(versao=1,classes=CLASSES,pesos_externos=False,aprovado=aprovado,
                papel='proposta_de_operacao_sujeita_a_argumentos_e_verificador',limiar=.9,
                base_sha256=sha(ROOT/'artefatos/linguagem_profunda/pesos_numpy.npz'),
                tokenizer_sha256=sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json'),
                media=media.tolist(),desvio=desvio.tolist(),
                peso=head.weight.detach().numpy().tolist(),bias=head.bias.detach().numpy().tolist())
    (pasta/'cabeca.json').write_text(json.dumps(estado,ensure_ascii=False)+'\n')
    rel=dict(base_parametros=sum(v.size for v in g.p.values()),cabeca_parametros=sum(p.numel() for p in head.parameters()),
             base_congelada=True,epoca_escolhida_dev=escolhida,historico=hist,teste=dict(acuracia=precisao,
             precisao_aceitos=pa,aceitos=len(aceitos),n=len(teste),por_classe=por_classe),aprovado=aprovado,
             duracao_segundos=round(time.monotonic()-inicio,2),casos=teste,
             corpus_sha256={s:sha(pasta/(s+'.json')) for s in dados},
             limite='Templates autorais separados, não conversa livre nem validação independente; números e entidades não são extraídos pela cabeça.')
    (pasta/'relatorio.json').write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in rel.items() if k!='casos'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
