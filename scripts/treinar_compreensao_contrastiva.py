"""Piloto de contrastes contextuais nos pesos próprios, com replay humano.

Não ativa pesos no chat. Retomada exige mesma configuração, corpus e código.
Mantém somente o checkpoint atual e melhor; saída deve ser local, não Drive.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from linguagem_profunda import carregar, VERSAO
from scripts.compreensao_contrastiva import gerar, assinatura, lote, pontuar, perdas, medir
from scripts.treinar_linguagem_profunda import Corpus, perda_por_resposta, salvar_atomico, sha


def executar(a):
    if min(a.passos, a.lote, a.avaliar_a_cada, a.threads, a.max_segundos) < 1 or not 0 < a.lr < 1:
        raise ValueError('Orçamento e contagens devem ser positivos')
    if not 0 <= a.peso_contraste <= 10 or not 0 < a.peso_replay <= 10:
        raise ValueError('Pesos inválidos; replay não pode ser desligado')
    limite = a.passos if a.parar_em is None else min(a.passos, a.parar_em)
    if limite < 1:
        raise ValueError('Pausa deve ser positiva')
    torch.set_num_threads(a.threads)
    torch.manual_seed(a.semente)
    rng = np.random.default_rng(a.semente)
    out = Path(a.saida)
    if out.exists() and not a.retomar:
        raise FileExistsError('Use uma pasta nova ou --retomar; nada será sobrescrito')
    modelo, t, inicial = carregar(a.inicial, a.dispositivo)
    corpus = Corpus(a.corpus, modelo.config.contexto, podar_padding=True)
    if sha(Path(a.inicial)/'tokenizer.json') != corpus.manifesto['arquivos']['tokenizer.json']:
        raise ValueError('Tokenizer do replay difere dos pesos próprios')
    treino, validacao = gerar('treino'), gerar('validacao')
    # Corpus de teste não é instanciado durante o ajuste/seleção.
    execucao = dict(config=asdict(modelo.config), corpus=corpus.assinatura,
        tokenizer_sha256=sha(Path(a.inicial)/'tokenizer.json'), fase='dialogo_contrastivo',
        inicial_sha256=sha(Path(a.inicial)/'pesos.pt'),
        treino_sha256=assinatura(treino), validacao_sha256=assinatura(validacao),
        lote=a.lote, lr=a.lr, semente=a.semente, horizonte=a.passos,
        peso_contraste=a.peso_contraste, peso_replay=a.peso_replay,
        avaliar_a_cada=a.avaliar_a_cada,
        codigo_sha256={f:sha(ROOT/f) for f in ('linguagem_profunda.py',
            'scripts/compreensao_contrastiva.py', 'scripts/treinar_compreensao_contrastiva.py',
            'scripts/treinar_linguagem_profunda.py')})
    digest = hashlib.sha256(json.dumps(execucao, sort_keys=True).encode()).hexdigest()
    opt = torch.optim.AdamW(modelo.parameters(), lr=a.lr, weight_decay=.01)
    passo = 0; historico = []; melhor = None; tokens = 0
    if a.retomar:
        e = torch.load(out/'checkpoint.pt', map_location='cpu', weights_only=True)
        if e['assinatura'] != digest:
            raise ValueError('Retomada incompatível: configuração/código/dados mudaram')
        modelo.load_state_dict(e['modelo']); opt.load_state_dict(e['otimizador'])
        rng.bit_generator.state = json.loads(e['rng_numpy'])
        torch.set_rng_state(e['rng_torch'])
        if e['rng_cuda'] and torch.cuda.is_available(): torch.cuda.set_rng_state_all(e['rng_cuda'])
        passo=e['passo']; historico=e['historico']; melhor=e['melhor']; tokens=e['tokens_alvo']
    if limite < passo:
        raise ValueError('Pausa anterior ao checkpoint atual')
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(a.inicial)/'tokenizer.json', out/'tokenizer.json')
    inicio=time.monotonic(); inicial_passo=passo

    def avaliar():
        r=medir(modelo, t, validacao, a.dispositivo)
        modelo.eval()
        # Painel fixo de replay de treino, diagnóstico de esquecimento, não seleção humana reservada.
        with torch.no_grad():
            x,y=corpus.lote('treino', 'dialogo', 8, np.random.default_rng(91015), a.dispositivo)
            r['ce_replay_fixo']=float(perda_por_resposta(modelo(x)[0],y))
        r['passo']=passo
        return r

    def salvar(pasta=out):
        pasta.mkdir(parents=True, exist_ok=True)
        e=dict(versao=VERSAO, config=asdict(modelo.config), modelo=modelo.state_dict(),
            passo=passo, execucao=execucao, tokens_entrada=0, tokens_alvo=tokens,
            inicial=dict(passo=inicial['passo'],pesos_sha256=execucao['inicial_sha256']))
        salvar_atomico(e, pasta/'pesos.pt')
        checkpoint=dict(e, assinatura=digest,otimizador=opt.state_dict(),
            rng_numpy=json.dumps(rng.bit_generator.state),rng_torch=torch.get_rng_state(),
            rng_cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
            historico=historico,melhor=melhor)
        salvar_atomico(checkpoint, pasta/'checkpoint.pt')
        shutil.copyfile(Path(a.inicial)/'tokenizer.json', pasta/'tokenizer.json')
        rel={k:v for k,v in e.items() if k!='modelo'}
        rel.update(assinatura=digest,historico=historico,melhor=melhor,
            pesos_sha256=sha(pasta/'pesos.pt'),parametros=sum(p.numel() for p in modelo.parameters()),
            passos_esta_execucao=passo-inicial_passo,segundos=round(time.monotonic()-inicio,2),
            dispositivo=a.dispositivo,concluido=passo>=a.passos,pausado=passo<a.passos,
            decisao='experimental_nao_ativado',
            limite='Ranking de alvos fornecidos; requer geração livre e revisão antes de promoção.')
        tmp=pasta/'relatorio.json.tmp';tmp.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n');tmp.replace(pasta/'relatorio.json')

    if not historico:
        historico.append(avaliar()); melhor=dict(passo=0,pares=historico[0]['pares_corretos'])
        salvar(out/'melhor');print(json.dumps(historico[-1]),flush=True)
    ultimo_salvo = None
    while passo<limite:
        modelo.train()
        ps=[treino[i] for i in rng.integers(0,len(treino),size=a.lote)]
        x,y,c=lote(t,ps,modelo.config.contexto,a.dispositivo)
        opt.zero_grad(set_to_none=True)
        loss,lm,contraste=perdas(pontuar(modelo(x)[0],y),c,a.peso_contraste)
        loss.backward()
        xr,yr=corpus.lote('treino','dialogo',2,rng,a.dispositivo)
        replay=perda_por_resposta(modelo(xr)[0],yr)
        (a.peso_replay*replay).backward()
        if not all(torch.isfinite(v) for v in (loss,replay)):
            raise FloatingPointError('Perda não finita; último checkpoint preservado')
        torch.nn.utils.clip_grad_norm_(modelo.parameters(),1.)
        opt.step();passo+=1;tokens+=int((y.reshape(-1,2,y.shape[1])[torch.arange(len(c),device=c.device),c]!=-100).sum())+int((yr!=-100).sum())
        if passo%10==0:
            print(json.dumps(dict(passo=passo,lm=float(lm.detach()),contraste=float(contraste.detach()),
                replay=float(replay.detach()),segundos=round(time.monotonic()-inicio,2))),flush=True)
        medir_agora=passo%a.avaliar_a_cada==0 or passo==a.passos
        if medir_agora:
            historico.append(avaliar());print(json.dumps(historico[-1]),flush=True)
            r=historico[-1]
            if r['pares_corretos']>melhor['pares'] and r['ce_replay_fixo']<=historico[0]['ce_replay_fixo']*1.05:
                melhor=dict(passo=passo,pares=r['pares_corretos']);salvar(out/'melhor')
        if medir_agora or time.monotonic()-inicio>=a.max_segundos:
            salvar()
            ultimo_salvo=passo
        if time.monotonic()-inicio>=a.max_segundos:break
    if ultimo_salvo != passo: salvar()
    print(json.dumps(dict(passo=passo,melhor=melhor,saida=str(out))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inicial','corpus','saida'):p.add_argument('--'+name,required=True)
    p.add_argument('--passos',type=int,default=60);p.add_argument('--lote',type=int,default=2)
    p.add_argument('--lr',type=float,default=.00008);p.add_argument('--semente',type=int,default=20261005)
    p.add_argument('--peso-contraste',type=float,default=1.);p.add_argument('--peso-replay',type=float,default=.5)
    p.add_argument('--avaliar-a-cada',type=int,default=20);p.add_argument('--threads',type=int,default=2)
    p.add_argument('--max-segundos',type=int,default=600);p.add_argument('--dispositivo',default='cpu')
    p.add_argument('--parar-em',type=int,help='Pausa operacional; preserva o horizonte e RNG')
    p.add_argument('--retomar',action='store_true')
    executar(p.parse_args())
