"""Memória de trabalho e operações verificáveis sobre declarações da sessão.

Não é um gerador irrestrito nem um banco de respostas de diálogos. Extrai
argumentos tipados, conserva a fonte de cada atualização e calcula a conclusão.
Uma hipótese opera numa cópia. Ausência de informação não significa negação.
O verificador proposicional do projeto certifica apenas os requisitos declarados.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re
from collections import deque

from raciocinio_ativo import Literal, Premissa, SistemaPremissas, normalizar


NUM = r'\d{1,7}(?:[.,]\d{1,2})?(?![\d.,]\d)'
DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')
ROTULOS_DIAS = dict(zip(DIAS, ('segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo')))
_DIAS = re.compile(r'\b('+'|'.join(DIAS)+r')(?:-feira)?\b')


def chave(texto):
    n = normalizar(texto).strip(' .,:;?!')
    return re.sub(r'^(?:(?:e|o|a|os|as|um|uma|de|do|da|meu|minha|sua|seu|agora)\s+)+', '', n)


def numero(texto):
    try:
        return Decimal(texto.replace(',', '.'))
    except InvalidOperation:
        return None


def valor(d):
    return format(d.normalize(), 'f')


def junto(itens):
    itens = list(itens)
    return ', '.join(itens[:-1])+' e '+itens[-1] if len(itens)>1 else (itens[0] if itens else '')


def limpar_citacoes(texto):
    return re.sub(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`', '', texto)


class RaciocinioConversa:
    """Estado limitado por instância; não aprende fatos a partir da saída."""
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.custos = []
        self.tempos = {}
        self.disponivel = None
        self.agendas = {}
        self.requisitos = []
        self.operador = 'e'
        self.posses = {}
        self.foco = None
        self.foco_agenda = None
        self.ativo = None
        self.eventos = deque(maxlen=48)
        self.fontes = {}
        self.turno = 0
        self.ultimo = None

    def _registrar(self, campo, antes, depois, fonte, hipotese):
        fonte=getattr(self,'_fonte_turno',fonte)
        repetidos=[e for e in self.eventos if e['turno']==self.turno and e['campo']==campo]
        revisao=re.search(r'\b(?:corrigindo|na verdade|ganhou|perdeu|recebeu|agora (?:tem|nao tem))\b',normalizar(fonte))
        if repetidos and repetidos[-1]['valor'] is not None and repetidos[-1]['valor']!=depois and not revisao:
            self._conflitos.append(campo)
        self.eventos.append(dict(turno=self.turno, campo=campo, anterior=antes,
                                 valor=depois, origem='hipotese' if hipotese else 'usuario',
                                 fonte=fonte[:1200]))
        self.fontes[campo]=dict(turno=self.turno,origem='hipotese' if hipotese else 'usuario',fonte=fonte[:1200])

    @staticmethod
    def _rotulo(texto):
        n = chave(texto)
        n = re.sub(r'^(?:corrigindo|na verdade|agora sei|descobri|mas|e agora|agora)[: ,]+', '', n)
        n = re.sub(r'\b(?:agora|na verdade|tambem|so|ainda|na realidade|passou a|voltou a|continua)\b', '', n)
        return chave(' '.join(n.split()))

    @staticmethod
    def _resolver(nome, nomes):
        """Somente referência única; nunca escolher por proximidade numérica."""
        if list(nomes).count(nome)==1:
            return nome
        tokens = set(nome.split()) - {'preco', 'custo', 'valor', 'tempo', 'duracao'}
        candidatos = [k for k in nomes if tokens and (tokens <= set(k.split()) or set(k.split()) <= tokens)]
        return candidatos[0] if len(candidatos)==1 else None

    def _custos(self, texto, hipotese):
        n = normalizar(texto)
        if re.search(r'\b(?:dolares|euros|centavos|iene|libras|dolar)\b',n):
            return False, None
        if not (re.search(r'\b(?:custa|custam|custava|custar|cobra|cobre|preco|reais|r\$|taxa|passagem|material)\b',n)
                or self.ativo=='custos'):
            return False, None
        # Valores cujo papel não está explicitado não são incorporados.
        padrao = re.compile(r'([^.!?;]+?)\s+(?:custa|custava|custam|cobra|cobre|sai por|e|passou a custar|subiu para|passou para)\s+(?:r\$\s*)?('+NUM+r')\b([^.!?;]*)')
        novos = []; atualizados = False; ambiguo = None
        for m in padrao.finditer(n):
            nome = self._rotulo(m.group(1))
            if len(nome)>90 or not nome or re.search(r'\b(?:se|fosse|vizinho disse|nao)\b', nome):
                continue
            custo = numero(m.group(2))
            componentes = {nome:custo}
            cauda = m.group(3)
            comp = re.search(r'\bmais\s+(?:r\$\s*)?('+NUM+r')\s*(?:reais\s*)?(?:de\s+)?(.+)',cauda)
            if comp:
                rot = self._rotulo(comp.group(2).split(',')[0])
                rot = re.split(r'\s+(?:qual|quanto|e agora|o que)\b',rot)[0].strip()
                if rot and len(rot)<60:
                    componentes[rot] = numero(comp.group(1))
            desconhecido = re.search(r'\bmais\s+(?:um|uma)?\s*(.+?)(?:\s+que|,|$)',cauda)
            if desconhecido and not comp and re.search(r'\b(?:nao sei|desconhec|falta)\b',cauda):
                componentes[self._rotulo(desconhecido.group(1))] = None
            existentes = [k for c in self.custos for k in c['componentes']]
            ref = self._resolver(nome, existentes)
            if ref:
                c = next(c for c in self.custos if ref in c['componentes'])
                antes = c['componentes'][ref]
                c['componentes'][ref] = custo
                self._registrar('custo:'+ref, None if antes is None else valor(antes),valor(custo),texto,hipotese)
                atualizados = True
            else:
                novos.append(dict(nome=nome,componentes=componentes))
        # Condicionais possuem verbo próprio, sem aplicar a hipótese ao estado real.
        cond = re.search(r'\b(?:se|e se)\s+(.+?)\s+(?:fosse|custasse)\s+(?:r\$\s*)?('+NUM+r')',n)
        if cond:
            existentes = [k for c in self.custos for k in c['componentes']]
            ref = self._resolver(self._rotulo(cond.group(1)),existentes)
            if ref:
                c = next(c for c in self.custos if ref in c['componentes'])
                antes=c['componentes'][ref]
                c['componentes'][ref] = numero(cond.group(2)); atualizados = True
                self._registrar('custo:'+ref,None if antes is None else valor(antes),valor(c['componentes'][ref]),texto,hipotese)
            elif existentes:
                ambiguo=self._rotulo(cond.group(1))
        if len(novos)>=2:
            self.custos = novos[:4]
            self.fontes={k:v for k,v in self.fontes.items() if not k.startswith('custo:')}
            self._registrar('custos',None,[c['nome'] for c in self.custos],texto,hipotese)
            atualizados = True
        elif len(novos)==1 and self.custos:
            # Não inserir automaticamente uma terceira opção numa correção ambígua.
            ambiguo = novos[0]['nome']
        if self.custos and re.search(r'\b(?:nao sei|esqueca|desconheco)\b',n):
            existentes = [k for c in self.custos for k in c['componentes']]
            refs = [k for k in existentes if re.search(r'\b'+re.escape(k)+r'\b',n)]
            if len(refs)==1:
                c = next(c for c in self.custos if refs[0] in c['componentes'])
                antes=c['componentes'][refs[0]]
                c['componentes'][refs[0]] = None; atualizados = True
                self._registrar('custo:'+refs[0],None if antes is None else valor(antes),None,texto,hipotese)
        return atualizados, ambiguo

    def _tempo(self, texto, hipotese):
        n = normalizar(texto)
        mudou = False
        horas = {'uma':Decimal(60),'duas':Decimal(120),'tres':Decimal(180)}
        m = re.search(r'\b(?:tenho|disponho de|tivesse|ter)\s+('+NUM+r'|uma|duas|tres)\s+(minutos?|horas?)\b',n)
        if m and not re.search(r'\b(?:nao tenho|nao sei)\b',n):
            qtd = horas.get(m.group(1)) if m.group(2).startswith('hora') and m.group(1) in horas else numero(m.group(1))
            if qtd is not None:
                if m.group(2).startswith('hora') and m.group(1) not in horas:
                    qtd *= 60
                antes = self.disponivel; self.disponivel = qtd; mudou = True
                self._registrar('tempo:disponivel',None if antes is None else valor(antes),valor(qtd),texto,hipotese)
        for m in re.finditer(r'([^.!?;]+?)\s+(?:leva|demora|dura|gasta)\s+('+NUM+r')\s+(minutos?|horas?)\b',n):
            nome = self._rotulo(m.group(1))
            nome = re.split(r'\s+e\s+(?=(?:o|a|os|as)\s)',nome)[-1]
            if not nome or len(nome)>90 or re.search(r'\b(?:nao|se|disse)\b',nome):
                continue
            if nome in ('ela','ele','isso'):
                # Só resolver uma referência local explicitamente nomeada na mesma fala.
                local = re.search(r'\bincluir\s+((?:a|o)\s+[\w ]+)\.',n)
                if not local:
                    continue
                nome = self._rotulo(local.group(1))
            qtd = numero(m.group(2))*(60 if m.group(3).startswith('hora') else 1)
            ref = self._resolver(nome,self.tempos) or nome
            if ref not in self.tempos and len(self.tempos)>=6:
                continue
            antes = self.tempos.get(ref); self.tempos[ref] = qtd; mudou = True
            self._registrar('tempo:'+ref,None if antes is None else valor(antes),valor(qtd),texto,hipotese)
        if re.search(r'\b(?:nao sei|nao tenho)\b.+\b(?:tempo|disponivel)\b',n) and self.disponivel is not None:
            antes=self.disponivel
            self.disponivel = None; mudou = True
            self._registrar('tempo:disponivel',valor(antes),None,texto,hipotese)
        return mudou

    def _agenda(self, texto, hipotese):
        n = normalizar(texto)
        mudou = False
        for clausula in re.split(r'[.!?;]',n):
            clausula=re.sub(r',\s*(?:na verdade|corrigindo|agora)\s*,?',' ',clausula)
            participante = re.search(r'^\s*([\w ]{1,40}?)\s+(?:tambem participa|vai participar|participa)\b',clausula)
            if participante:
                nome = self._rotulo(participante.group(1))
                if nome and len(self.agendas)<6:
                    if nome not in self.agendas:
                        self.agendas[nome]=None
                        self._registrar('agenda:'+nome,None,None,texto,hipotese)
                    self.foco_agenda = nome
                    mudou = True
                    resto=clausula[participante.end():].strip()
                    if resto.startswith('e '):clausula=nome+' '+resto[2:]
            dias = set(_DIAS.findall(clausula))
            if not dias:
                continue
            m = re.search(r'(?:^|,\s*)([\w ]{1,55}?)\s+(?:nao pode mais|nao pode|pode|consegue|esta livre|liberou|conseguiu liberar|pudesse)\s+(.+)',clausula.strip())
            if not m:
                continue
            nome = self._rotulo(m.group(1))
            if not nome or re.search(r'\b(?:se|quem|qual|quando|e se)\b',nome):
                continue
            if nome in ('ele','ela'):
                nome = self.foco_agenda
                if nome not in self.agendas:
                    continue
            if nome not in self.agendas and len(self.agendas)>=6:
                continue
            antes = set(self.agendas.get(nome) or ())
            negativo = 'nao pode' in m.group(0)
            adicionar = 'tambem' in clausula or 'liberou' in clausula or 'liberar' in clausula
            if negativo:
                if self.agendas.get(nome) is None:
                    # Exclusão de um dia não especifica os demais dias livres.
                    continue
                depois = antes-dias
            elif adicionar and nome in self.agendas and not re.search(r'\bso\b',clausula):
                depois = antes|dias
            else:
                depois = dias
            self.agendas[nome] = depois; self.foco_agenda = nome; mudou = True
            self._registrar('agenda:'+nome,sorted(antes),sorted(depois),texto,hipotese)
        # Um contrafactual simples sobre um participante já conhecido.
        m = re.search(r'\bse\s+([\w ]+?)\s+pudesse\s+(.+)',n)
        if m:
            nome = self._rotulo(m.group(1)); dias=set(_DIAS.findall(m.group(2)))
            if nome in self.agendas and dias:
                antes=sorted(self.agendas[nome] or ())
                self.agendas[nome] = (self.agendas[nome] or set())|dias if 'tambem' in m.group(2) else dias
                mudou = True
                self._registrar('agenda:'+nome,antes,sorted(self.agendas[nome]),texto,hipotese)
        return mudou

    def _regra(self, texto, hipotese):
        n = normalizar(texto)
        mudou = False
        m = re.search(r'(?:para\s+.+?\s+precisa(?:\s+de)?|so\s+.+?\s+quem\s+tem|basta)\s+([^.!?;]+)',n)
        if m:
            corpo = m.group(1)
            if ' e ' in corpo and ' ou ' in corpo:
                return False
            req = [chave(x) for x in re.split(r'\s+(?:e|ou)\s+',corpo)]
            if 1 <= len(req) <= 3 and all(re.fullmatch(r'[\w -]{1,32}',r) and len(r.split())<=4 for r in req):
                self.requisitos = list(dict.fromkeys(req))
                self.operador = 'ou' if ' ou ' in corpo else 'e'
                self.posses = {nome:{k:v for k,v in ps.items() if k in req} for nome,ps in self.posses.items()}
                validos={'posse:'+nome+':'+r for nome,ps in self.posses.items() for r in ps}
                self.fontes={k:v for k,v in self.fontes.items() if not k.startswith('posse:') or k in validos}
                self._registrar('regra',None,dict(itens=req,operador=self.operador),texto,hipotese)
                mudou = True
        if not self.requisitos:
            return mudou
        transferencia = re.search(r'\b([\w]+)\s+(?:deu|emprestou)\s+(?:a |o |sua |seu |uma |um |unica |unico )*([\w -]+?)\s+para\s+([\w]+)\b',n)
        if transferencia:
            de,item,para=transferencia.groups()
            req=self._resolver(chave(item),self.requisitos)
            if req and (para in self.posses or len(self.posses)<3):
                antes=self.posses.setdefault(para,{}).get(req)
                self.posses[para][req]=True
                self._registrar('posse:'+para+':'+req,antes,True,texto,hipotese)
                if de in self.posses and req in self.posses[de]:
                    antes=self.posses[de][req]
                    if re.search(r'\bunic[ao]\b',n):self.posses[de][req]=False
                    else:self.posses[de].pop(req,None)
                    self._registrar('posse:'+de+':'+req,antes,self.posses[de].get(req),texto,hipotese)
                self.foco=para;mudou=True
        for c in re.split(r'[.!?;]',n):
            c = re.sub(r'^(?:descobri que|descobri|agora|na realidade|corrigindo)[: ,]*','',c.strip())
            m = re.search(r'^([\w ]{1,45}?)\s+(?:(nao)\s+)?(tem|ganhou|recebeu|perdeu|recebesse)\s+(.+)',c)
            if not m:
                continue
            nome = self._rotulo(m.group(1))
            if nome.startswith('se '):
                nome = nome[3:]
            if nome in ('ele','ela'):
                nome = self.foco
            if not nome or (nome not in self.posses and len(self.posses)>=3):
                continue
            encontrados = [r for r in self.requisitos if re.search(r'\b'+re.escape(r)+r'\b',m.group(4))]
            if not encontrados:
                continue
            ps = self.posses.setdefault(nome,{})
            negativa=bool(m.group(2) or m.group(3)=='perdeu')
            for trecho in re.split(r',\s*|\s+mas\s+|\s+e\s+(?=(?:nao\s+)?tem\b)',m.group(4)):
                verbo=re.search(r'\b(?:(nao)\s+)?(tem|ganhou|recebeu|perdeu)\b',trecho)
                if verbo:negativa=bool(verbo.group(1) or verbo.group(2)=='perdeu')
                for r in encontrados:
                    if re.search(r'\b'+re.escape(r)+r'\b',trecho):
                        antes=ps.get(r);ps[r]=not negativa
                        self._registrar('posse:'+nome+':'+r,antes,not negativa,texto,hipotese)
            self.foco = nome; mudou = True
        return mudou

    def _concluir(self, dominio, hipotese):
        r = dict(operacao={'custos':'comparar_custos','tempo':'tempo_restante',
                           'agenda':'intersecao_agendas','regra':'verificar_requisitos'}[dominio],
                 hipotese=hipotese, fonte='declaracoes_da_sessao', status='calculado')
        if dominio=='custos':
            faltam=[k for c in self.custos for k,v in c['componentes'].items() if v is None]
            if len(self.custos)<2 or faltam:
                r.update(status='incompleto',faltam=faltam or ['outra opção'])
                return r, 'Para comparar, falta informar '+junto(r['faltam'])+'.'
            totais=[sum(c['componentes'].values(),Decimal(0)) for c in self.custos]
            minimo=min(totais); indices=[i for i,t in enumerate(totais) if t==minimo]
            diferenca=max(totais)-minimo
            r['resultado']=dict(totais=[valor(v) for v in totais],menor=indices[0] if len(indices)==1 else None,diferenca=valor(diferenca))
            r['entradas']=[dict(nome=c['nome'],componentes={k:valor(v) for k,v in c['componentes'].items()}) for c in self.custos]
            detalhe='; '.join(c['nome']+': R$ '+valor(t).replace('.',',') for c,t in zip(self.custos,totais))
            conclusao=('Há empate no menor custo.' if len(indices)>1 else
                       self.custos[indices[0]]['nome'].capitalize()+' custa menos, com diferença de R$ '+valor(diferenca).replace('.',',')+'.')
            return r, detalhe+'. '+conclusao
        if dominio=='tempo':
            if self.disponivel is None or not self.tempos:
                r.update(status='incompleto',faltam=['tempo disponível' if self.disponivel is None else 'duração das atividades'])
                conhecido=('Você informou '+valor(self.disponivel)+' minutos disponíveis. ' if self.disponivel is not None else '')
                return r, conhecido+'Falta informar '+junto(r['faltam'])+' para calcular se cabe.'
            gasto=sum(self.tempos.values(),Decimal(0)); resto=self.disponivel-gasto
            r['entradas']={k:valor(v) for k,v in self.tempos.items()}
            r['resultado']=dict(disponivel=valor(self.disponivel),gasto=valor(gasto),restante=valor(resto))
            detalhe='As atividades informadas somam '+valor(gasto)+' minutos, para '+valor(self.disponivel)+' disponíveis. '
            return r, detalhe+('Sobram '+valor(resto)+' minutos.' if resto>=0 else 'Faltam '+valor(-resto)+' minutos para caber tudo.')
        if dominio=='agenda':
            if len(self.agendas)<2 or any(v is None for v in self.agendas.values()):
                r.update(status='incompleto',faltam=['disponibilidade de outro participante'])
                return r, 'Preciso dos dias livres de outro participante para encontrar um dia em comum.'
            comuns=set.intersection(*self.agendas.values())
            dias=[d for d in DIAS if d in comuns]
            r['resultado']=dict(dias=dias)
            r['entradas']={k:[d for d in DIAS if d in v] for k,v in self.agendas.items()}
            return r, ('Os dias em comum são '+junto(ROTULOS_DIAS[d] for d in dias)+'.' if dias else 'Não há dia em comum entre os participantes com as disponibilidades que você informou.')
        if not self.requisitos or self.foco not in self.posses:
            r.update(status='incompleto',faltam=['requisitos e estado de uma pessoa'])
            return r, 'Preciso da regra e dos itens que a pessoa tem para verificar os requisitos.'
        ps=self.posses[self.foco]
        # O alvo é cumprir estes requisitos, não garantir que uma ação no mundo acontece.
        ls=[Literal('item'+str(i),False,self.foco+' tem '+req) for i,req in enumerate(self.requisitos)]
        alvo=Literal('cumpre',False,self.foco+' cumpre os requisitos informados')
        premissas=[Premissa(tuple(ls),alvo,self.operador,'Requisitos informados: '+junto(self.requisitos))]
        if self.operador=='e':
            premissas.extend(Premissa((alvo,),l,'e','Cumprir exige '+l.rotulo) for l in ls)
        else:
            premissas.append(Premissa(tuple(l.oposto() for l in ls),alvo.oposto(),'e','Sem nenhum dos itens, não cumpre os requisitos'))
        for req,l in zip(self.requisitos,ls):
            if req in ps:
                f=l if ps[req] else l.oposto()
                premissas.append(Premissa((),f,'e',f.texto()))
        analise=SistemaPremissas(premissas).analisar(alvo)
        r['resultado']=dict(status=analise['status'])
        r['prova']=analise
        r['entradas']=dict(pessoa=self.foco,requisitos=self.requisitos,operador=self.operador,posses=dict(ps))
        rotulo=self.foco.capitalize()
        if analise['status']=='sustentado':
            frase=rotulo+' cumpre os requisitos que você informou.'
        elif analise['status']=='refutado':
            faltam=[req for req in self.requisitos if ps.get(req) is False]
            frase=rotulo+' não cumpre esses requisitos: não tem '+junto(faltam)+'.'
        else:
            faltam=[req for req in self.requisitos if req not in ps]
            frase='Ainda não dá para concluir: falta saber se '+self.foco+' tem '+junto(faltam)+'.'
        return r, frase

    def responder(self, texto):
        self.ultimo = None
        if not isinstance(texto,str) or not texto.strip() or len(texto)>1200:
            return None
        n=normalizar(texto)
        if re.search(r'\b(?:comecar de novo|reiniciar|apague (?:a |essa )?memoria|esqueca tudo)\b',n):
            self.limpar(); return None
        # Consultas ao acervo, premissas formais, código e citações não se
        # tornam fatos novos nem uma pergunta sobre o último orçamento.
        if ('```' in texto or re.match(r'\s*(?:o que e|quem foi|como funciona|considere (?:estas|as) premissas)\b',n)):
            return None
        limpo=limpar_citacoes(texto)
        if re.search(r'\b(?:acho que|nao posso afirmar|nao sei se|ouvi dizer|disse que|talvez)\b',normalizar(limpo)):
            return None
        hip=bool(re.search(r'\b(?:se .+? (?:fosse|custasse|tivesse|pudesse|recebesse)|e se)\b',normalizar(limpo)))
        if re.search(r'\bse\b[^.!?]+\bnao (?:fosse|custasse|tivesse|pudesse|recebesse)\b',normalizar(limpo)):
            return None
        if re.search(r'\b(?:se|caso|desde que)\b',normalizar(limpo)) and not hip:
            return None
        if re.search(r'\b(?:dolares|euros|centavos|iene|libras|dolar)\b',normalizar(limpo)):
            return None
        # Uma pergunta isolada sobre um valor ou uma posse não o afirma.
        declaracoes=[]
        for m in re.finditer(r'((?:[^.!?;]|\.(?=\d))+)([.!?;]|$)',limpo):
            c,fim=m.groups()
            if fim=='?' and not hip:
                continue
            declaracoes.append(c+fim)
        dados=' '.join(declaracoes)
        alvo=deepcopy(self)
        alvo.turno += 1
        alvo._fonte_turno=texto
        alvo._conflitos=[]
        if re.search(r'\b(?:mudando de assunto|quero (?:aprender|retomar|estudar|praticar))\b',normalizar(dados)) and not re.search(r'\b(?:leva|demora|dura)\b',normalizar(dados)):
            alvo.tempos={}
            alvo.fontes={k:v for k,v in alvo.fontes.items() if not k.startswith('tempo:')}
        alteracoes={}
        custo, ambiguo=alvo._custos(dados,hip)
        alteracoes['custos']=custo or bool(ambiguo)
        alteracoes['tempo']=alvo._tempo(dados,hip)
        alteracoes['agenda']=alvo._agenda(dados,hip)
        alteracoes['regra']=alvo._regra(dados,hip)
        dominios=[d for d,v in alteracoes.items() if v]
        if len(dominios)>1:
            # Não juntar unidades, pessoas ou operações diferentes à força.
            return None
        dominio=dominios[0] if dominios else None
        pergunta=bool('?' in texto or re.search(r'\b(?:resumo|resume|quanto|qual|e agora|o que muda)\b',n))
        if dominio is None and pergunta:
            if alvo.custos and re.search(r'\b(?:precos|custo|custam|custava|valores|totais|diferenca|economiz|empate|barato|mais em conta|menor|taxa)\w*\b',n):
                dominio='custos'
            elif (alvo.tempos or alvo.disponivel is not None) and re.search(r'\b(?:saldo|sobra|sobraria|cabe|cabia|meu tempo|quanto tempo eu|tempo (?:real|disponivel))\w*\b',n):
                dominio='tempo'
            elif alvo.agendas and re.search(r'\b(?:em comum|encontro|reunir|marcar|qual dia (?:da|resta|serve)|quais dias.*(?:livres|comum))\b',n):
                dominio='agenda'
            elif alvo.requisitos and re.search(r'\b(?:regra|requisitos|cumpre|situacao)\b',n):
                dominio='regra'
            elif re.fullmatch(r'(?:e |entao|agora|o que muda|e agora|ainda assim|ficou diferente|sem essa hipotese)[ .?!]*',n):
                dominio=alvo.ativo
        if dominio is None:
            return None
        if dominio=='custos' and len(alvo.custos)<2:
            return None
        if dominio=='tempo' and not alvo.tempos and not re.search(r'\b(?:quanto|sobra|saldo|cabe|cabia)\w*\b',n):
            # Disponibilidade sozinha alimenta a memória; o diálogo pessoal
            # continua com a rota de objetivos, sem pedir durações à força.
            del alvo._fonte_turno
            del alvo._conflitos
            if not hip:self.__dict__.update(alvo.__dict__)
            return None
        alvo.ativo=dominio
        if dominio=='regra':
            mencionados=[p for p in alvo.posses if re.search(r'\b'+re.escape(p)+r'\b',n)]
            if len(mencionados)==1:
                alvo.foco=mencionados[0]
        if alvo._conflitos:
            r=dict(operacao={'custos':'comparar_custos','tempo':'tempo_restante','agenda':'intersecao_agendas','regra':'verificar_requisitos'}[dominio],
                   status='conflito',hipotese=hip,fonte='declaracoes_da_sessao',conflitos=list(alvo._conflitos))
            frase='Há afirmações incompatíveis na mesma fala. Qual delas devo considerar?'
        elif ambiguo and dominio=='custos':
            r=dict(operacao='comparar_custos',status='ambiguo',hipotese=hip,fonte='declaracoes_da_sessao',faltam=[ambiguo])
            frase='Não consegui ligar esse valor a uma opção de forma única. Qual opção ou componente você está corrigindo?'
        else:
            r,frase=alvo._concluir(dominio,hip)
        r['atualizacoes']=[dict(e) for e in alvo.eventos if e['turno']==alvo.turno]
        prefixes={'custos':('custos','custo:'),'tempo':('tempo:',),'agenda':('agenda:',),'regra':('regra','posse:')}[dominio]
        r['fontes']={k:dict(v) for k,v in alvo.fontes.items() if k.startswith(prefixes)}
        r['redacao']='estrutural_verificada'
        del alvo._fonte_turno
        del alvo._conflitos
        if not hip and r['status']!='conflito':
            self.__dict__.update(alvo.__dict__)
        self.ultimo=r
        return 'conversa:raciocinio', ('Nessa hipótese, ' if hip else 'Pelos dados que você informou, ')+frase
