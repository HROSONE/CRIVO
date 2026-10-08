"""Cabeças autorais de interpretação/cópia sobre o transformer próprio.

Nenhum texto do alvo é oferecido ao modelo. Os ponteiros procuram trechos no
histórico bruto. Copiar uma fonte não prova ter interpretado corretamente seu
papel: isso é medido separadamente e impede promoção automática.
"""
from decimal import Decimal
import math
import re
import sys
from pathlib import Path
import torch
from torch import nn
from corpus import OPERACOES, CLASSES


def norm(s): return ' '.join(s.casefold().split())


def codificar(tok, exemplo):
    ids = []; offsets = []
    for turno, texto in enumerate(exemplo['turnos']):
        ids.append(tok.token_to_id('<usuario>')); offsets.append(None)
        enc = tok.encode(texto, add_special_tokens=False)
        ids.extend(enc.ids); offsets.extend((turno, a, b) for a, b in enc.offsets)
        ids.append(tok.token_to_id('<fim>')); offsets.append(None)
    ids.append(tok.token_to_id('<assistente>')); offsets.append(None)
    if len(ids) > 256: raise ValueError('Não truncar o contexto.')
    null = len(ids) - 1
    pontos = []
    for s in exemplo['argumentos'] + [exemplo['referente']]:
        if s is None:
            pontos.extend([null, null]); continue
        indices = [i for i, o in enumerate(offsets) if o and o[0] == s['turno']
                   and o[2] > s['inicio'] and o[1] < s['fim']]
        if not indices: raise ValueError('Alvo sem tokens de suporte.')
        pontos.extend([indices[0], indices[-1]])
    return {'ids': ids, 'offsets': offsets, 'pontos': pontos, 'exemplo': exemplo}


def recuperar(item, inicio, fim):
    null = len(item['ids']) - 1
    if inicio == fim == null: return None
    if not 0 <= inicio <= fim < null: return {'invalido': True}
    os = item['offsets'][inicio:fim+1]
    if not os or any(o is None for o in os) or len({o[0] for o in os}) != 1:
        return {'invalido': True}
    t = os[0][0]; a = min(o[1] for o in os); b = max(o[2] for o in os)
    texto = item['exemplo']['turnos'][t][a:b]
    # Margens de espaço de BPE não mudam o trecho semântico nem sua origem.
    esquerda = len(texto) - len(texto.lstrip()); direita = len(texto.rstrip())
    return {'turno': t, 'inicio': a+esquerda, 'fim': a+direita, 'texto': texto.strip()}


def lote(itens, pad):
    n = max(len(i['ids']) for i in itens)
    x = torch.full((len(itens), n), pad, dtype=torch.long)
    for j, i in enumerate(itens): x[j, :len(i['ids'])] = torch.tensor(i['ids'])
    return x, torch.tensor([len(i['ids']) for i in itens])


class Interprete(nn.Module):
    def __init__(self, corpo, braco):
        super().__init__(); self.corpo = corpo; self.braco = braco
        d = corpo.config.dimensao
        self.operacao = nn.Linear(d, len(OPERACOES) if braco == 'contextual' else len(CLASSES))
        if braco == 'contextual':
            self.escopo = nn.Linear(d, 2)
            self.chaves = nn.Linear(d, d, bias=False)
            self.consultas = nn.Linear(d, 8*d, bias=False)
            self.vies_fonte = nn.Linear(d, 8)

    def forward(self, x, comprimentos):
        c = self.corpo
        h = c.embedding(x) + c.posicao(torch.arange(x.shape[1], device=x.device))
        for b in c.blocos: h = b(h)
        h = c.norm(h); atual = h[torch.arange(len(x)), comprimentos-1]
        op = self.operacao(atual)
        if self.braco != 'contextual': return {'operacao': op}
        q = self.consultas(atual).view(len(x), 8, -1)
        k = self.chaves(h)
        pontos = torch.einsum('bhd,btd->bht', q, k) / math.sqrt(k.shape[-1])
        pontos = pontos + self.vies_fonte(h).transpose(1, 2)
        mask = torch.arange(x.shape[1])[None, :] >= comprimentos[:, None]
        pontos = pontos.masked_fill(mask[:, None, :], -1e9)
        return {'operacao': op, 'escopo': self.escopo(atual), 'pontos': pontos}


def proposta(item, logits, idx):
    pr = logits['operacao'][idx].softmax(-1)
    op = OPERACOES[int(pr.argmax())]
    pares = logits['pontos'][idx].argmax(-1).tolist()
    trechos = [recuperar(item, pares[i], pares[i+1]) for i in range(0, 8, 2)]
    return {'operacao': op, 'confianca_operacao': float(pr.max()),
            'argumentos': trechos[:3], 'referente': trechos[3],
            'hipotese': bool(logits['escopo'][idx].argmax()),
            'fontes': sorted({s['turno'] for s in trechos if s and not s.get('invalido')})}


def mesmos(a, b, origem=True):
    if a is None or b is None: return a is b
    if a.get('invalido') or b.get('invalido'): return False
    return norm(a['texto']) == norm(b['texto']) and (not origem or a['turno'] == b['turno'])


def conferir(e, p):
    op = p['operacao'] == e['operacao']
    args = [mesmos(a,b) for a,b in zip(e['argumentos'],p['argumentos'])]
    ref = mesmos(e['referente'], p['referente'], origem=False)
    scope = p['hipotese'] == e['hipotese']
    return {'operacao': op, 'argumentos': args, 'referente': ref, 'escopo': scope,
            'contrato': op and all(args) and ref and scope}


def executar(p):
    """Operações fechadas, sem eval, código gerado ou alteração de memória real."""
    args = p['argumentos']
    if any(s and s.get('invalido') for s in args + [p['referente']]):
        return {'executavel': False, 'motivo': 'Ponteiro não é um trecho válido de uma fala.'}
    textos = [a['texto'] if a else None for a in args]
    op = p['operacao']; r = None
    try:
        if op in ('comparar_custos', 'tempo_restante', 'consultar_valor'):
            numeros = []
            for t in textos:
                if t is None: numeros.append(None); continue
                if not re.fullmatch(r'-?\d+(?:[.,]\d+)?', t): raise ValueError('Número sem formato suportado.')
                numeros.append(Decimal(t.replace(',', '.')))
            v = lambda n: int(n) if n == n.to_integral_value() else str(n)
            a, b, c = numeros
            if a is None: raise ValueError('Falta argumento numérico.')
            if op == 'comparar_custos':
                if b is None: raise ValueError('Falta o segundo custo.')
                r = {'totais':[v(a),v(b)],'menor':0 if a<b else 1 if b<a else None,'diferenca':v(abs(a-b))}
            elif op == 'tempo_restante':
                if b is None: raise ValueError('Falta duração.')
                gasto = b + (c or 0); r = {'disponivel':v(a),'gasto':v(gasto),'restante':v(a-gasto)}
            else:
                if not p['referente']: raise ValueError('Consulta sem referente.')
                r = {'pessoa':p['referente']['texto'],'valor':v(a)}
        elif op == 'verificar_requisitos':
            if not textos[0] or not textos[1]: raise ValueError('Faltam regra ou inventário.')
            requeridos = set(norm(textos[0]).split(' e '))
            if not all(re.fullmatch(r'[^\W\d_]+', x) for x in requeridos): raise ValueError('Regra não suportada.')
            positivos = set(); negativos = set()
            for m in re.finditer(r'(não\s+)?tem\s+([^\W\d_]+)(?:\s+e\s+(?!não\b)([^\W\d_]+))?', norm(textos[1])):
                alvo = negativos if m[1] else positivos
                alvo.add(m[2])
                if m[3]: alvo.add(m[3])
            if not positivos and not negativos: raise ValueError('Inventário sem declaração reconhecida.')
            status = 'contraditorio' if positivos & negativos else 'refutado' if requeridos & negativos else 'provado' if requeridos <= positivos else 'indeterminado'
            r = {'status':status}
        elif op == 'resumir_objetivos':
            if not textos[0] or not textos[1]: raise ValueError('Faltam objetivo e restrição.')
            r = {'objetivo':textos[0],'restricao':textos[1]}
        elif op == 'esclarecer':
            r = {'status':'ambiguo'}
        else: raise ValueError('Operação desconhecida.')
    except (ValueError, ArithmeticError) as exc:
        return {'executavel':False,'motivo':str(exc)}
    return {'executavel':True,'resultado':r,'hipotese':p['hipotese'],
            'limite':'Execução confere operação e cópia, mas não certifica o papel semântico dos argumentos.'}


def esperado(e):
    return executar({k:e[k] for k in ('operacao','argumentos','referente','hipotese')})


def metricas(rows):
    from collections import defaultdict
    grupos = defaultdict(list); familias = defaultdict(list)
    for r in rows:
        grupos[r['sessao']].append(r['contrato']); familias[r['familia']].append(r['contrato'])
    return {'n':len(rows),'contratos_corretos':sum(r['contrato'] for r in rows),
            'acuracia_contrato':sum(r['contrato'] for r in rows)/len(rows),
            'sessoes':len(grupos),'sessoes_completas':sum(all(v) for v in grupos.values()),
            'por_familia':{f:{'n':len(v),'corretos':sum(v),'acuracia':sum(v)/len(v)} for f,v in familias.items()}}
