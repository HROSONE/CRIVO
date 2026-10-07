"""Tarefas modulares supervisionadas e execução sem reparo por oráculo.

Compartilha o Transformer próprio, com tarefas/prefixos distintos. Adaptação
inspirada em FaiRR, não reprodução dos três Transformers daquele artigo.
"""
import hashlib
import json
import sys
from pathlib import Path

from piloto import gerar_casos, NOMES, STATUS, assinatura, ler_literal, ler_premissa
from diagnosticar import verificar_passos

CODIGOS = dict(A='sustentado', B='refutado', C='indeterminado', D='conflito', E='continuar')
INV = {v:k for k,v in CODIGOS.items()}
TAREFAS = ('regra', 'apoio', 'estado', 'redacao')


def corpus_modular():
    teste = ['O rádio toca', 'O radar gira', 'A sirene soa', 'O tubo abre',
             'O feixe passa', 'A placa aquece', 'O botão acende', 'O relógio para']
    dados = {s: gerar_casos(s,n,semente=seed,vocabulario=v) for s,n,seed,v in [
        ('treino',640,8201,NOMES['treino']), ('dev',56,8202,NOMES['dev']),
        ('teste',84,8203,teste)]}
    for s,cs in dados.items():
        for c in cs:
            c['id'] = 'modular-' + c['id']
    hashes = {s:hashlib.sha256(json.dumps(cs,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for s,cs in dados.items()}
    return dados, hashes


def literal_texto(l):
    return l.texto()


def preparar(caso, passos):
    ps = [ler_premissa(p) for p in caso['premissas']]
    regras = [('p%d'%i,p) for i,p in enumerate(ps) if p.antecedentes]
    fatos = [('p%d'%i,p.consequente) for i,p in enumerate(ps) if not p.antecedentes]
    fatos += [('s%d'%i,ler_literal(p['conclusao'])) for i,p in enumerate(passos)]
    return regras, fatos


def pergunta_regra(regra, fatos):
    return 'Tarefa: regra\nRegra: '+regra.texto+'\nFatos:\n'+'\n'.join(literal_texto(f) for _,f in fatos)


def pergunta_apoio(antecedente, fato):
    return 'Tarefa: apoio\nCondição: '+literal_texto(antecedente)+'\nFato: '+literal_texto(fato)


def pergunta_estado(caso, fatos):
    return 'Tarefa: estado\nObjetivo: '+caso['objetivo']+'\nPremissas:\n'+'\n'.join(caso['premissas'])+'\nFatos atuais:\n'+'\n'.join(literal_texto(f) for _,f in fatos)


def pergunta_redacao(regra, apoios):
    return 'Tarefa: redação\nRegra: '+regra.texto+'\nApoios:\n'+'\n'.join(literal_texto(a) for a in apoios)


def estados_professor(caso):
    """Alvos somente para treino e diagnóstico de etapas, nunca para execução."""
    passos=[]
    while True:
        regras,fatos=preparar(caso,passos)
        conhecidos={assinatura(f) for _,f in fatos}
        alvo=ler_literal(caso['objetivo'])
        propostas=[]
        if caso['status'] != 'conflito':
            for id_,r in regras:
                if assinatura(r.consequente) not in conhecidos and all(assinatura(a) in conhecidos for a in r.antecedentes):
                    refs=[next(idf for idf,f in fatos if assinatura(f)==assinatura(a)) for a in r.antecedentes]
                    propostas.append(dict(regra=id_,apoios=refs,conclusao=literal_texto(r.consequente)))
        estado = (caso['status'] if caso['status']=='conflito' or assinatura(alvo) in conhecidos or
                  assinatura(alvo.oposto()) in conhecidos or not propostas else 'continuar')
        yield passos.copy(), regras, fatos, propostas, estado
        if estado != 'continuar':
            return
        passos.append(propostas[0])


def exemplos_modulares(casos):
    out={t:[] for t in TAREFAS}
    for c in casos:
        for passos,regras,fatos,propostas,estado in estados_professor(c):
            ids={p['regra'] for p in propostas}
            out['estado'].append((pergunta_estado(c,fatos),INV[estado]))
            for id_,r in regras:
                out['regra'].append((pergunta_regra(r,fatos), '1' if id_ in ids else '0'))
                for a in r.antecedentes:
                    for _,f in fatos:
                        out['apoio'].append((pergunta_apoio(a,f),'1' if assinatura(a)==assinatura(f) else '0'))
                    # Negativo de polaridade com mesmo nome, evitando apenas
                    # aprender uma diferença de palavras entre entidades.
                    out['apoio'].append((pergunta_apoio(a,a.oposto()),'0'))
            for p in propostas:
                r=next(r for id_,r in regras if id_==p['regra'])
                fs=[f for idf,f in fatos if idf in p['apoios']]
                out['redacao'].append((pergunta_redacao(r,fs),p['conclusao']))
    return out


def executar_modular(caso, modelo, composicao='neural', limite=8):
    if composicao not in ('neural','simbolica'):
        raise ValueError('Composição desconhecida.')
    passos,trace=[],[]
    for _ in range(limite):
        regras,fatos=preparar(caso,passos)
        estado=CODIGOS[modelo.classe(pergunta_estado(caso,fatos),tuple(CODIGOS))]
        if estado != 'continuar':
            alvo=ler_literal(caso['objetivo'])
            desejado=alvo.oposto() if estado=='refutado' else alvo
            tem_prova=assinatura(desejado) in {assinatura(f) for _,f in fatos}
            if estado in ('sustentado','refutado') and not tem_prova:
                return dict(status=None,proposto=estado,passos=passos,motivo='termino_sem_prova',trace=trace)
            return dict(status=estado,passos=passos,motivo='terminou',trace=trace)
        scores=[(modelo.probabilidade(pergunta_regra(r,fatos),'1',('0','1')),id_,r) for id_,r in regras]
        if not scores:
            return dict(status=None,passos=passos,motivo='sem_regra',trace=trace)
        score,id_,r=max(scores,key=lambda x:(x[0],x[1]))
        if score < .5:
            return dict(status=None,passos=passos,motivo='regra_nao_selecionada',trace=trace)
        apoios=[]
        for a in r.antecedentes:
            candidatos=[(modelo.probabilidade(pergunta_apoio(a,f),'1',('0','1')),idf,f) for idf,f in fatos]
            if not candidatos:
                return dict(status=None,passos=passos,motivo='sem_apoio',trace=trace)
            s,idf,f=max(candidatos,key=lambda x:(x[0],x[1]))
            if s < .5:
                return dict(status=None,passos=passos,motivo='apoio_nao_selecionado',trace=trace)
            apoios.append((idf,f))
        # Testar a seleção com composição simbólica não gera acerto neural:
        # é uma ablação explicitamente separada e pode apenas vetar.
        selecionado=dict(regra=id_,apoios=[idf for idf,_ in apoios],conclusao=literal_texto(r.consequente))
        valido,motivo=verificar_passos(caso['premissas'],passos+[selecionado])
        trace.append(dict(regra=id_,apoios=selecionado['apoios'],selecao_valida=valido,score_regra=float(score)))
        if not valido:
            return dict(status=None,passos=passos,motivo='selecao:'+motivo,trace=trace)
        proposta=dict(selecionado)
        if composicao=='neural':
            proposta['conclusao']=modelo.redigir(pergunta_redacao(r,[f for _,f in apoios]))
            trace[-1]['conclusao_proposta']=proposta['conclusao']
            try:
                valido,motivo=verificar_passos(caso['premissas'],passos+[proposta])
            except (ValueError,TypeError,KeyError):
                valido,motivo=False,'formato_invalido'
            if not valido:
                return dict(status=None,passos=passos,motivo='redacao:'+motivo,trace=trace)
        if assinatura(ler_literal(proposta['conclusao'])) in {assinatura(f) for _,f in fatos}:
            return dict(status=None,passos=passos,motivo='passo_repetido',trace=trace)
        passos.append(proposta)
    return dict(status=None,passos=passos,motivo='limite_de_passos',trace=trace)


class ModeloNumpyModular:
    def __init__(self,pasta):
        meta=json.loads((Path(pasta)/'meta.json').read_text(encoding='utf-8'))
        if meta.get('papel') != 'piloto modular':
            raise ValueError('Exige pesos específicos do piloto modular.')
        from geracao_ancorada import GeracaoAncorada
        self.g=GeracaoAncorada(pasta,exigir_aprovacao=False)
        if not self.g.disponivel:
            raise RuntimeError(self.g.motivo)
        self.mascara=self.g.np.zeros(len(self.g.p['embedding.weight']),dtype=self.g.np.float32)
        for t in ('<pad>','<documento>','<usuario>','<assistente>'):
            self.mascara[self.g.bpe.especiais[t]]=-self.g.np.inf
        self.cache={}

    def prompt(self,texto):
        p=[self.g.doc]+self.g.bpe.codificar(texto)+[self.g.ass]
        if len(p)+40 > self.g.contexto:
            raise ValueError('Contexto excedido; não truncar.')
        return p

    def probabilidades(self,texto,classes):
        chave=(texto,classes)
        if chave not in self.cache:
            ids=[self.g.bpe.codificar(c) for c in classes]
            if any(len(i)!=1 for i in ids):
                raise ValueError('Classe deve ter um token.')
            l=self.g._passo(self.prompt(texto),0,{})[[i[0] for i in ids]]
            z=self.g.np.exp(l-l.max())
            self.cache[chave]=z/z.sum()
        return self.cache[chave]

    def classe(self,texto,classes):
        return classes[int(self.probabilidades(texto,classes).argmax())]

    def probabilidade(self,texto,classe,classes):
        return float(self.probabilidades(texto,classes)[classes.index(classe)])

    def redigir(self,texto):
        # Mesmo greedy de 40 tokens do avaliador Torch, sem restrições
        # lexicais, prefixo da fonte ou penalidades de repetição.
        entrada=self.prompt(texto); cache={}; saida=[]
        logits=self.g._passo(entrada,0,cache)
        pos=len(entrada)
        for _ in range(40):
            prox=int((logits+self.mascara).argmax())
            if prox==self.g.fim:
                return self.g.decodificar(saida).strip()
            saida.append(prox)
            logits=self.g._passo([prox],pos,cache);pos+=1
        return ''


def avaliar_modular(modelo,casos):
    rel={}
    for composicao in ('neural','simbolica'):
        linhas=[]
        for c in casos:
            r=executar_modular(c,modelo,composicao)
            r.update(id=c['id'],esperado=c['status'],correto=r['status']==c['status'],
                     ood=c['ood_estrutura'],profundidade=c['profundidade'])
            linhas.append(r)
        def resumo(ls):
            return dict(n=len(ls),acertos=sum(r['correto'] for r in ls),
                        provas_necessarias=sum(r['esperado'] in ('sustentado','refutado') for r in ls),
                        provas_completas=sum(r['correto'] and r['esperado'] in ('sustentado','refutado') for r in ls),
                        passos_aceitos=sum(len(r['passos']) for r in ls),
                        selecoes_validas=sum(t['selecao_valida'] for r in ls for t in r['trace']))
        rel[composicao]=dict(total=resumo(linhas),ood=resumo([r for r in linhas if r['ood']]),casos=linhas)
    return rel
