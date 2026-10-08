"""Treino com quatro tarefas distintas; seleção dev e novo teste retido."""
import argparse
import copy
import hashlib
import json
import random
import shutil
import sys
import time
from pathlib import Path

PASTA=Path(__file__).resolve().parent
RAIZ=PASTA.parents[1]
sys.path[:0]=[str(PASTA),str(RAIZ),str(RAIZ/'scripts')]
from modular import TAREFAS,CODIGOS,corpus_modular,exemplos_modulares,avaliar_modular,ModeloNumpyModular


class ModeloTorchModular:
    def __init__(self,modelo,bpe):
        self.m=modelo
        self.bpe=bpe
        self.cache={}

    def prompt(self,texto):
        esp=self.bpe.especiais
        p=[esp['<documento>']]+self.bpe.codificar(texto)+[esp['<assistente>']]
        if len(p)+40 > self.m.config.contexto:
            raise ValueError('Contexto excedido; não truncar.')
        return p

    def probabilidades(self,texto,classes):
        import torch
        chave=(texto,classes)
        if chave not in self.cache:
            ids=[self.bpe.codificar(c) for c in classes]
            if any(len(i)!=1 for i in ids):raise ValueError('Classe não unitária.')
            self.m.eval()
            with torch.no_grad():
                l=self.m(torch.tensor([self.prompt(texto)]))[0][0,-1,[i[0] for i in ids]]
                self.cache[chave]=l.softmax(-1).cpu().numpy()
        return self.cache[chave]

    def classe(self,texto,classes):
        return classes[int(self.probabilidades(texto,classes).argmax())]

    def probabilidade(self,texto,classe,classes):
        return float(self.probabilidades(texto,classes)[classes.index(classe)])

    def redigir(self,texto):
        from pontuador_frases import _bytes_unicode
        esp=self.bpe.especiais
        ids,fim=self.m.gerar(self.prompt(texto),esp['<fim>'],max_tokens=40,temperatura=0,
                             proibidos=[esp[t] for t in ('<pad>','<documento>','<usuario>','<assistente>')])
        vocab={i:t for t,i in self.bpe.vocab.items()}
        bs={c:b for b,c in _bytes_unicode().items()}
        t=''.join(vocab[i] for i in ids if i not in esp.values())
        return bytes(bs[c] for c in t if c in bs).decode('utf-8','replace').strip() if fim else ''


def avaliar_etapas(executor,exemplos):
    rel={}
    for tarefa in ('regra','apoio','estado'):
        # Amostra fixa e estratificada por classe, sempre do dev ou teste
        # solicitado. Limite para tornar medição CPU reproduzível e viável.
        classes=tuple(CODIGOS) if tarefa=='estado' else ('0','1')
        ls=[]
        for c in classes:
            ls += [e for e in exemplos[tarefa] if e[1]==c][:24]
        acertos={c:0 for c in classes};ns={c:0 for c in classes}
        for p,a in ls:
            ns[a]+=1;acertos[a]+=executor.classe(p,classes)==a
        rel[tarefa]=dict(n=len(ls),acertos=sum(acertos.values()),por_classe={c:dict(n=ns[c],acertos=acertos[c]) for c in classes})
    return rel


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saida',type=Path,required=True)
    ap.add_argument('--passos',type=int,default=800)
    ap.add_argument('--lote',type=int,default=8)
    ap.add_argument('--lr',type=float,default=.00015)
    ap.add_argument('--avaliar-a-cada',type=int,default=200)
    args=ap.parse_args()
    prod=(RAIZ/'artefatos').resolve();dest=args.saida.resolve()
    if dest==prod or prod in dest.parents:ap.error('Não sobrescrever pesos de produção.')
    if min(args.passos,args.lote,args.avaliar_a_cada)<1 or args.lr<=0:ap.error('Parâmetros positivos obrigatórios.')
    import numpy as np
    import torch
    from pontuador_frases import BPE
    from treinar_codificador_sentido import construir
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(8204);torch.use_deterministic_algorithms(True)
    rng=random.Random(8204)
    dados,hashes=corpus_modular()
    args.saida.mkdir(parents=True,exist_ok=True)
    for s,cs in dados.items():
        (args.saida/(s+'.json')).write_text(json.dumps(cs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.saida/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    ex=exemplos_modulares(dados['treino']);devex=exemplos_modulares(dados['dev'])
    base=RAIZ/'artefatos/geracao_pt';bpe=BPE(base/'tokenizer.json');esp=bpe.especiais
    m,cfg=construir(base)
    grupos={}
    for tarefa,ls in ex.items():
        grupos[tarefa]={}
        for p,a in ls:
            prompt=[esp['<documento>']]+bpe.codificar(p)+[esp['<assistente>']]
            alvo=bpe.codificar(a)+[esp['<fim>']]
            if len(prompt)+len(alvo)>cfg['contexto']:raise ValueError('Exemplo muito longo.')
            chave=a if tarefa!='redacao' else 'texto'
            grupos[tarefa].setdefault(chave,[]).append((prompt,alvo))
    executor=ModeloTorchModular(m,bpe)
    antes=avaliar_etapas(executor,devex)
    print('ANTES',antes,flush=True)
    opt=torch.optim.AdamW(m.parameters(),lr=args.lr,weight_decay=.01)
    melhor=None;historico=[];tokens={t:0 for t in TAREFAS}
    t0=time.monotonic()
    for passo in range(1,args.passos+1):
        tarefa=TAREFAS[(passo-1)%4];g=grupos[tarefa];keys=list(g)
        lote=[rng.choice(g[rng.choice(keys)]) for _ in range(args.lote)]
        largura=max(len(p)+len(a) for p,a in lote)
        x=torch.zeros((args.lote,largura),dtype=torch.long);y=torch.full_like(x,-100)
        for i,(p,a) in enumerate(lote):
            s=p+a;x[i,:len(s)]=torch.tensor(s);y[i,len(p)-1:len(s)-1]=torch.tensor(a)
            tokens[tarefa]+=len(a)
        m.train();opt.zero_grad();_,loss=m(x,y);loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step()
        if passo%25==0:print('passo',passo,tarefa,'perda',round(float(loss.detach()),4),'s',round(time.monotonic()-t0,1),flush=True)
        if passo%args.avaliar_a_cada==0 or passo==args.passos:
            executor=ModeloTorchModular(m,bpe)
            etapas=avaliar_etapas(executor,devex)
            # Só dev; o teste retido ainda não é avaliado.
            dev=avaliar_modular(executor,dados['dev'])
            score=(dev['neural']['total']['provas_completas'],dev['neural']['total']['acertos'],
                   dev['simbolica']['total']['provas_completas'],sum(v['acertos']/v['n'] for v in etapas.values()))
            historico.append(dict(passo=passo,etapas=etapas,dev={k:v['total'] for k,v in dev.items()}))
            print('DEV',historico[-1],flush=True)
            if melhor is None or score>melhor:
                melhor=score;melhor_passo=passo;estado=copy.deepcopy(m.state_dict())
    pasta=args.saida/'pesos';pasta.mkdir(exist_ok=True)
    np.savez_compressed(pasta/'pesos_numpy.npz',**{k:v.cpu().numpy().astype(np.float16) for k,v in estado.items()})
    shutil.copyfile(base/'tokenizer.json',pasta/'tokenizer.json')
    meta=dict(base=dict(config=cfg),papel='piloto modular',controle=dict(aprovado=False),
              treino=dict(passos=args.passos,lote=args.lote,lr=args.lr,semente=8204,
                          checkpoint=melhor_passo,exemplos={t:len(ls) for t,ls in ex.items()},tokens_alvo=tokens),
              corpus_sha256=hashes,pesos_externos=False)
    (pasta/'meta.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    m,_=construir(pasta);torch_exec=ModeloTorchModular(m,bpe)
    teste_torch=avaliar_modular(torch_exec,dados['teste'])
    numpy_exec=ModeloNumpyModular(pasta)
    teste_numpy=avaliar_modular(numpy_exec,dados['teste'])
    rel=dict(meta=meta,antes_dev=antes,historico=historico,
             etapas_teste=avaliar_etapas(numpy_exec,exemplos_modulares(dados['teste'])),
             teste_torch=teste_torch,teste_numpy=teste_numpy,
             pesos_sha256=hashlib.sha256((pasta/'pesos_numpy.npz').read_bytes()).hexdigest(),
             base_sha256=hashlib.sha256((base/'pesos_numpy.npz').read_bytes()).hexdigest(),
             segundos=time.monotonic()-t0,torch=torch.__version__,numpy=np.__version__)
    (args.saida/'resultado.json').write_text(json.dumps(rel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('RESULTADO', {k:v['total'] for k,v in teste_numpy.items()},flush=True)


if __name__=='__main__':main()
