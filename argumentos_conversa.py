"""Argumentos pessoais conservados por fonte; não são fatos do acervo.

Relaciona objetivos, impedimentos, associações lembradas e alternativas
explicitamente ditas. A redação é estrutural. Cenas solicitadas são ficção,
nunca observações novas sobre a pessoa. Não diagnostica sentimentos ou causas.
"""
from collections import deque
import re

from raciocinio_ativo import normalizar
from raciocinio_conversa import limpar_citacoes, junto


class ArgumentosConversa:
    def __init__(self):self.limpar()

    def limpar(self):
        self.objetivos=[]
        self.dilema=[]
        self.impedimentos=[]
        self.nao_principal=[]
        self.associacao=None
        self.sentimento=None
        self.recusado=None
        self.alternativa=None
        self.cena=None
        self.fontes=deque(maxlen=12)
        self.ultimo=None

    @staticmethod
    def _curto(texto):return ' '.join(texto.strip(' ,;.!?').split())[:240]

    def _guardar(self,lista,valor,limite):
        valor=self._curto(valor)
        if valor and valor not in lista:
            lista.append(valor)
            del lista[:-limite]

    def _resumo(self,com_alternativa=True):
        partes=[]
        if self.dilema:
            partes.append('Você está tentando conciliar '+junto('“'+s+'”' for s in self.dilema)+'.')
        outras=[g for g in self.objetivos if g not in self.dilema]
        if outras:partes.append('Também mencionou querer '+junto('“'+s+'”' for s in outras)+'.')
        if self.impedimentos:partes.append('A dificuldade que você trouxe foi '+junto('“'+s+'”' for s in self.impedimentos)+'.')
        if self.nao_principal:partes.append('Você esclareceu que '+junto(self.nao_principal)+' não é o principal.')
        if self.alternativa and com_alternativa:
            partes.append('A alternativa que propôs foi “'+self.alternativa+'”, como hipótese, ainda sem decidir por ela.')
        return ' '.join(partes)

    def _quadro(self,operacao):
        return dict(operacao=operacao,objetivos=list(self.objetivos),dilema=list(self.dilema),
                    impedimentos=list(self.impedimentos),nao_principal=list(self.nao_principal),
                    associacao=dict(self.associacao) if self.associacao else None,
                    sentimento=self.sentimento,recusado=self.recusado,alternativa=self.alternativa,
                    fontes=list(self.fontes),redacao='estrutural',prova_logica=False)

    def responder(self,texto):
        self.ultimo=None
        if not isinstance(texto,str) or not texto.strip() or len(texto)>1200:return None
        n=normalizar(texto)
        if re.search(r'\b(?:comecar de novo|reiniciar|esqueca tudo|mudando de assunto)\b',n):
            self.limpar();return None
        if ('`' in texto or re.match(r'\s*(?:o que e|quem foi|como funciona|considere (?:estas|as) premissas)\b',n)):
            return None
        limpo=limpar_citacoes(texto);nl=normalizar(limpo)
        condicional=bool(re.match(r'^(?:e )?(?:se|caso|talvez|imagine|suponha)\b',nl))
        if (re.match(r'^(?:e )?(?:se|caso|talvez|imagine|suponha)\b',nl) and not self.dilema
                or re.search(r'\b(?:disse que|escreveu que|ouvi dizer|nao posso afirmar)\b',nl)):
            return None
        if re.match(r'^(?:eu )?(?:quero|queria|gostaria de) (?:falar|conversar)\b',nl):
            self.limpar();return None
        # A associação precisa de dois argumentos afirmados pelo usuário.
        m=re.search(r'\bQuando\s+(.+?)(?:,\s*|\s+)(?:eu\s+)?(?:penso\s+(?:em|na|no|nas|nos)|lembro(?:\s+(?:de|das|dos|da|do))?|recordo(?:\s+(?:de|das|dos|da|do))?)\s+([^.!?]+)',limpo,re.I)
        nova_associacao=False
        if m and not condicional and not re.search(r'\b(?:se|talvez|nao|nao sei)\b',normalizar(m.group(0))):
            self.associacao=dict(gatilho=self._curto(m.group(1)),lembranca=self._curto(m.group(2)),declaracao=self._curto(m.group(0)))
            self.sentimento=self.recusado=None
            nova_associacao=True
        m=re.search(r'\b(?:estou|fico)\s+dividid[oa]\s+entre\s+([^.!?]+)',limpo,re.I)
        novo_dilema=False
        if m and not condicional:
            partes=re.split(r'\s+e\s+',m.group(1),maxsplit=1,flags=re.I)
            if len(partes)==2 and all(len(s.split())<=18 for s in partes):
                self.dilema=[self._curto(s) for s in partes]
                self.objetivos=list(self.dilema);self.impedimentos=[];self.nao_principal=[];self.alternativa=None
                novo_dilema=True
        # Novos objetivos só entram como declarações de desejo, sem ordens
        # ao assistente nem complementos interrogativos ou condicionais.
        novos_objetivos=False
        for m in re.finditer(r'\b(?:eu\s+)?(?:quero|queria|pretendo|gostaria de)\s+(.+?)(?=,|[.!?]|\s+mas\s+|$)',limpo,re.I):
            g=self._curto(m.group(1));primeiro=normalizar(g).split()[0] if g else ''
            if (not condicional and primeiro.endswith(('ar','er','ir')) and primeiro not in ('falar','conversar','saber','entender','explicar','escrever','criar','inventar','transformar','contar','verificar')
                    and not re.search(r'\b(?:se|caso|talvez|que)\b',normalizar(g))):
                self._guardar(self.objetivos,g,4);novos_objetivos=True
        novos_impedimentos=False
        if self.dilema and not condicional:
            m=re.search(r'\bmas\s+((?:eu\s+)?(?:estou|tenho|nao posso|nao consigo)[^.!?]+)',limpo,re.I)
            if m:
                self._guardar(self.impedimentos,m.group(1),3);novos_impedimentos=True
            m=re.search(r'\b(?:o|a)\s+([\wÀ-ÿ ]{1,45}?)\s+n[aã]o\s+[eé]\s+o\s+principal\b',limpo,re.I)
            if m:
                self._guardar(self.nao_principal,m.group(1),3);novos_impedimentos=True
        corrigiu=False
        if self.associacao and not condicional:
            neg=re.search(r'\bN[aã]o\s+[eé]\s+([^.!?]+)[.!?]',limpo,re.I)
            pos=re.search(r'(?:^|[.!?])\s*[EÉeé]\s+(?:uma?\s+)?(?:sensa[cç][aã]o\s+de\s+)?([^.!?]+)',limpo)
            if neg and pos:
                self.recusado=self._curto(neg.group(1));self.sentimento=self._curto(pos.group(1));corrigiu=True
        alterou=nova_associacao or novo_dilema or novos_objetivos or novos_impedimentos or corrigiu
        if alterou:self.fontes.append(dict(origem='usuario',texto=texto))
        hipotese=re.search(r'^(?:E\s+)?se\s+(?:eu\s+)?([^.!?]+)',limpo.strip(),re.I)
        if hipotese and self.dilema:
            self.alternativa=self._curto(hipotese.group(1))
            self.fontes.append(dict(origem='hipotese',texto=texto))
            frase=self._resumo()+(' Ao propor apenas uma experiência, você limita o compromisso inicial. ' if re.search(r'\b(?:apenas|so)\s+um[ao]?\b',normalizar(self.alternativa)) else ' ')
            frase+='Para comparar melhor, ainda faltam a duração e o custo reais dessa alternativa, junto do limite que você quer preservar.'
            self.ultimo=self._quadro('comparar_alternativa_pessoal')
            return 'conversa:argumentos',frase
        criativo=bool(re.search(r'\b(?:cena|conto|historia|narrador)\b',nl) and re.search(r'\b(?:escreva|escrever|crie|criar|transformar|muda|reescreva|tenta)\b',nl)
                      and re.search(r'\b(?:essa|esta|nessa|nesta|narrador|reescreva)\b',nl))
        if criativo and self.associacao:
            declaracao=self.associacao['declaracao']
            declaracao=re.sub(r'\bQuando\b','Quando',declaracao,flags=re.I)
            for a,b in [('escuto','escutava'),('ouço','ouvia'),('lembro','lembrava'),('penso','pensava'),('recordo','recordava')]:
                declaracao=re.sub(r'\b'+a+r'\b',b,declaracao,flags=re.I)
            curiosidade=bool(re.search(r'\b(?:crianca|curios[oa]|descobrir)\b',nl))
            inicio=('Eu queria descobrir por que aquele momento fazia uma lembrança aparecer.' if curiosidade else 'Parei por um instante para prestar atenção.')
            sentimento=(' Não era '+self.recusado+'; era '+self.sentimento+'.' if self.recusado and self.sentimento else '')
            self.cena=inicio+' '+declaracao+'.'+sentimento+' Fiquei ali mais um pouco, guardando aquela lembrança.'
            self.ultimo=self._quadro('cena_ficcional_estrutural')
            self.ultimo.update(escopo='ficcao',narrador='primeira_pessoa_curiosa' if curiosidade else 'primeira_pessoa')
            return 'conversa:argumentos',self.cena
        resumo=bool(re.search(r'\b(?:resume|resuma|resumo)\b',nl) and
                    (re.search(r'\b(?:dilema|objetivos|metas|prioridades|preocupacao|impedimentos|essa alternativa|minha alternativa)\b',nl) or re.fullmatch(r'(?:resume|resuma|resumo)[.!? ]*',nl)))
        if self.dilema and (novo_dilema or novos_impedimentos or resumo):
            self.ultimo=self._quadro('resumir_argumentos_pessoais')
            return 'conversa:argumentos',self._resumo()
        referencia=bool(re.search(r'\b(?:essa|esta|minha|aquela) (?:associacao|ligacao|lembranca|memoria)\b|\b(?:voce entendeu|entendeu)\b',nl))
        if self.associacao and (nova_associacao or corrigiu or referencia):
            if corrigiu:
                frase='Entendi a correção: você descreve '+self.sentimento+', não '+self.recusado+'. '
            else:frase=''
            frase+='Você ligou “'+self.associacao['gatilho']+'” à lembrança de “'+self.associacao['lembranca']+'”.'
            self.ultimo=self._quadro('relacionar_memoria_declarada')
            return 'conversa:argumentos',frase
        return None
