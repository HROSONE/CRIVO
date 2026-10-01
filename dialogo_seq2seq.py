"""Encoder-decoder autoral com atenção e cópia aprendida de palavras.

O modelo lê texto real, incluindo os papéis e as últimas mensagens da
conversa. Nenhuma ação, intenção, frase de resposta ou slot é fornecido à
rede. Vocabulário e pesos são aprendidos do zero. Palavras fora do
vocabulário possuem atributos de subpalavras e podem ser copiadas da
fonte pela distribuição pointer-generator. Inferência usa NumPy quando
disponível e possui uma implementação equivalente em Python padrão.
"""
import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from operator import mul
from pathlib import Path

VERSAO = "dialogo-seq2seq-atencao-copia-v1"
ESPECIAIS = ("<pad>", "<inicio>", "<fim>", "<desconhecido>",
             "<usuario>", "<assistente>", "<mensagem>")
PAD, INICIO, FIM, DESCONHECIDO, USUARIO, ASSISTENTE, MENSAGEM = range(7)


def tokenizar(texto):
    if not isinstance(texto, str):
        raise ValueError("Texto deve ser uma string")
    return re.findall(r"\w+(?:[-'’]\w+)*|⏎|[^\w\s]", texto.replace("\n", " ⏎ "), re.UNICODE)


def detokenizar(tokens):
    texto = " ".join(tokens)
    texto = re.sub(r"\s+([.,;:!?%\)\]\}»”])", r"\1", texto)
    texto = re.sub(r"([\(\[\{«“])\s+", r"\1", texto)
    return re.sub(r" *⏎ *", "\n", texto).strip()


def fonte_dialogo(mensagem, historico=(), limite=192):
    """Mantém o pedido atual e depois os turnos mais recentes, em ordem."""
    if (not isinstance(mensagem, str) or not mensagem.strip() or
            not isinstance(historico, (list, tuple)) or len(historico)>32 or not 8 <= limite <= 512):
        raise ValueError("Mensagem, histórico ou limite inválidos")
    atual = [ESPECIAIS[MENSAGEM]] + tokenizar(mensagem)
    if len(atual) > limite:
        # Início e fim do pedido têm pistas distintas; preserve os dois.
        metade = (limite - 1) // 2
        atual = [ESPECIAIS[MENSAGEM]] + atual[1:1 + metade] + atual[-(limite - 1 - metade):]
    anteriores = []
    for item in historico[-24:]:
        if (not isinstance(item, dict) or item.get("papel") not in ("usuario", "assistente") or
                not isinstance(item.get("texto"), str)):
            raise ValueError("Turno de histórico inválido")
        papel = USUARIO if item["papel"] == "usuario" else ASSISTENTE
        anteriores.append([ESPECIAIS[papel]] + tokenizar(item["texto"]))
    restantes = limite - len(atual)
    selecionados = []
    for turno in reversed(anteriores):
        if len(turno)<=restantes:
            selecionados = turno+selecionados
            restantes -= len(turno)
        elif restantes>1:
            # Preserve a autoria do fragmento mais antigo que couber.
            selecionados = turno[:1]+turno[-(restantes-1):]+selecionados
            break
        else:
            break
    return selecionados+atual


def subpalavras(token, buckets=512, maximo=16):
    """Hash determinístico de 3/4-gramas; o léxico de sessão não é salvo."""
    if token in ESPECIAIS:
        return ()
    palavra = "^" + token.casefold()[:80] + "$"
    partes = {palavra[i:i+n] for n in (3, 4) for i in range(max(0, len(palavra)-n+1))}
    if not partes:
        partes = {palavra}
    return tuple(sorted({int.from_bytes(hashlib.sha256(p.encode("utf-8")).digest()[:4], "big") % buckets
                         for p in partes})[:maximo])


def vocabulario_treino(exemplos, limite=2500):
    """Resposta recebe prioridade; a validação não cria o vocabulário."""
    contagem = Counter()
    for ex in exemplos:
        resposta = tokenizar(ex["resposta"])
        contagem.update(resposta)
        contagem.update(resposta)
        contagem.update(fonte_dialogo(ex["mensagem"], ex.get("historico", [])))
    for especial in ESPECIAIS:
        contagem.pop(especial, None)
    ordenados = sorted(contagem, key=lambda t: (-contagem[t], t))[:limite-len(ESPECIAIS)]
    return list(ESPECIAIS) + ordenados


def formas(vocabulario, ocultos, embeddings, buckets):
    h, e, v = ocultos, embeddings, len(vocabulario)
    resultado = {"E": (v, e), "C": (buckets, e), "I": (2*h, h), "bi": (h,),
                 "K": (2*h, h), "Q": (h, h), "O": (3*h, v), "bo": (v,),
                 "G": (e+3*h, 1), "bg": (1,)}
    for nome, entrada in (("EF", e), ("EB", e), ("D", e+2*h)):
        resultado[nome+"W"] = (entrada, 3*h)
        resultado[nome+"U"] = (h, 3*h)
        resultado[nome+"b"] = (3*h,)
    return resultado


def _softmax(xs):
    pico = max(xs)
    ys = [math.exp(max(-70.0, x-pico)) for x in xs]
    soma = sum(ys)
    return [x/soma for x in ys]


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, x))))


def _mat(vetor, matriz):
    return [sum(map(mul, vetor, coluna)) for coluna in zip(*matriz)]


class DialogoSeq2Seq:
    def __init__(self, dados, acelerar=True):
        if dados.get("versao") != VERSAO:
            raise ValueError("Checkpoint de diálogo incompatível")
        self.vocabulario = dados["vocabulario"]
        self.ocultos, self.embeddings = dados["ocultos"], dados["embeddings"]
        self.buckets = dados.get("buckets", 512)
        self.limite_fonte = dados.get("limite_fonte", 192)
        if (not 16 <= self.ocultos <= 128 or not 8 <= self.embeddings <= 96 or
                not 32 <= self.buckets <= 2048 or not 8 <= self.limite_fonte <= 512 or
                not len(ESPECIAIS)+1 <= len(self.vocabulario) <= 8192 or
                self.vocabulario[:len(ESPECIAIS)] != list(ESPECIAIS) or
                any(not isinstance(t, str) for t in self.vocabulario) or
                len(set(self.vocabulario)) != len(self.vocabulario)):
            raise ValueError("Configuração de diálogo inválida")
        self.indices = {t:i for i,t in enumerate(self.vocabulario)}
        self.pesos = dados["pesos"]
        esperadas = formas(self.vocabulario, self.ocultos, self.embeddings, self.buckets)
        if set(self.pesos) != set(esperadas):
            raise ValueError("Matrizes de diálogo incompletas")
        for nome, forma in esperadas.items():
            a = self.pesos[nome]
            if (not isinstance(a, list) or len(a) != forma[0] or
                    len(forma) == 2 and any(not isinstance(l, list) or len(l) != forma[1] for l in a)):
                raise ValueError("Forma inválida: " + nome)
            valores = (x for l in a for x in l) if len(forma) == 2 else iter(a)
            if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in valores):
                raise ValueError("Peso não finito: " + nome)
        self.np = None
        if acelerar:
            try:
                import numpy as np
                self.np = np
                self.pesos = {k:np.asarray(v, dtype=np.float64) for k,v in self.pesos.items()}
            except ImportError:
                pass
        # Transpor apenas uma vez reduz o custo de cada passo em Python puro.
        self._colunas = ({k:tuple(zip(*a)) for k,a in self.pesos.items()
                          if len(esperadas[k]) == 2} if self.np is None else {})
        self.metadados = {k:v for k,v in dados.items() if k != "pesos"}

    def _produto(self, vetor, nome, inicio=0, fim=None):
        return [sum(map(mul, vetor, coluna))
                for coluna in self._colunas[nome][inicio:fim]]

    def _embedding(self, token):
        p, np = self.pesos, self.np
        indice = self.indices.get(token, DESCONHECIDO)
        partes = subpalavras(token, self.buckets)
        if np is not None:
            resultado = p["E"][indice].copy()
            if partes:
                resultado += p["C"][list(partes)].mean(axis=0)
            return resultado
        resultado = list(p["E"][indice])
        if partes:
            resultado = [x+sum(p["C"][i][j] for i in partes)/len(partes) for j,x in enumerate(resultado)]
        return resultado

    def _gru(self, x, anterior, nome):
        p, np, h = self.pesos, self.np, self.ocultos
        if np is not None:
            xi = x@p[nome+"W"] + p[nome+"b"]
            hu = anterior@p[nome+"U"][:, :2*h]
            z = 1/(1+np.exp(-np.clip(xi[:h]+hu[:h], -60, 60)))
            r = 1/(1+np.exp(-np.clip(xi[h:2*h]+hu[h:], -60, 60)))
            n = np.tanh(xi[2*h:] + (r*anterior)@p[nome+"U"][:, 2*h:])
            return (1-z)*anterior + z*n
        xi = [a+b for a,b in zip(self._produto(x, nome+"W"), p[nome+"b"])]
        hu = self._produto(anterior,nome+"U",fim=2*h)
        z = [_sigmoid(a+b) for a,b in zip(xi[:h], hu[:h])]
        r = [_sigmoid(a+b) for a,b in zip(xi[h:2*h], hu[h:])]
        n = [math.tanh(a+b) for a,b in zip(xi[2*h:], self._produto(
            [a*b for a,b in zip(r,anterior)],nome+"U",inicio=2*h))]
        return [(1-a)*b+a*c for a,b,c in zip(z,anterior,n)]

    def codificar(self, mensagem, historico=()):
        tokens = fonte_dialogo(mensagem, historico, self.limite_fonte)
        p, np, h = self.pesos, self.np, self.ocultos
        embeds = [self._embedding(t) for t in tokens]
        zero = np.zeros(h) if np is not None else [0.0]*h
        atual, fwd = zero, []
        for x in embeds:
            atual = self._gru(x, atual, "EF")
            fwd.append(atual)
        atual, bwd = zero, []
        for x in reversed(embeds):
            atual = self._gru(x, atual, "EB")
            bwd.append(atual)
        bwd.reverse()
        if np is not None:
            estados = np.asarray([np.concatenate((a,b)) for a,b in zip(fwd,bwd)])
            inicial = np.tanh(np.concatenate((fwd[-1],bwd[0]))@p["I"] + p["bi"])
            chaves = estados@p["K"]
            contexto = np.zeros(2*h)
        else:
            estados = [a+b for a,b in zip(fwd,bwd)]
            inicial = [math.tanh(a+b) for a,b in zip(self._produto(fwd[-1]+bwd[0],"I"),p["bi"])]
            chaves = [self._produto(s,"K") for s in estados]
            contexto = [0.0]*(2*h)
        return {"tokens": tokens, "estados": estados, "chaves": chaves,
                "h": inicial, "contexto": contexto}

    def passo(self, anterior, estado):
        """Retorna distribuição conjunta do vocabulário e das palavras copiáveis."""
        p, np, h = self.pesos, self.np, self.ocultos
        emb = self._embedding(anterior)
        if np is not None:
            novo = self._gru(np.concatenate((emb, estado["contexto"])), estado["h"], "D")
            query = novo@p["Q"]
            energia = estado["chaves"]@query/math.sqrt(h)
            atencao = np.exp(energia-energia.max());atencao /= atencao.sum()
            ctx = atencao@estado["estados"]
            hc = np.concatenate((novo,ctx))
            logits = hc@p["O"]+p["bo"]
            probs = np.exp(logits-logits.max());probs /= probs.sum()
            gate = _sigmoid(float(np.concatenate((emb,hc))@p["G"][:,0]+p["bg"][0]))
            probs, atencao = probs.tolist(), atencao.tolist()
        else:
            novo = self._gru(emb+estado["contexto"],estado["h"],"D")
            query = self._produto(novo,"Q")
            energia = [sum(a*b for a,b in zip(k,query))/math.sqrt(h) for k in estado["chaves"]]
            atencao = _softmax(energia)
            ctx = [sum(a*s[j] for a,s in zip(atencao,estado["estados"])) for j in range(2*h)]
            hc = novo+ctx
            probs = _softmax([a+b for a,b in zip(self._produto(hc,"O"),p["bo"])])
            gate = _sigmoid(self._produto(emb+hc,"G")[0]+p["bg"][0])
        distribuicao = {t:gate*a for t,a in zip(self.vocabulario,probs)}
        for t,a in zip(estado["tokens"],atencao):
            distribuicao[t] = distribuicao.get(t,0.0)+(1-gate)*a
        seguinte = dict(estado, h=novo, contexto=ctx)
        return distribuicao, seguinte, {"gerar": gate, "atencao": atencao}

    def probabilidades(self, mensagem, historico=(), prefixo=()):
        estado = self.codificar(mensagem,historico)
        distribuicao, estado, _ = self.passo(ESPECIAIS[INICIO],estado)
        for token in prefixo:
            distribuicao, estado, _ = self.passo(token,estado)
        return distribuicao

    def gerar(self, mensagem, historico=(), max_tokens=64, feixe=1):
        """Busca limitada; não consulta banco de frases ou catálogo de ações."""
        if not 1 <= max_tokens <= 128 or not 1 <= feixe <= 4:
            raise ValueError("Limite de geração inválido")
        estado = self.codificar(mensagem,historico)
        vivos = [([],0.0,ESPECIAIS[INICIO],estado,[])];finais = []
        proibidos = set(ESPECIAIS)-{ESPECIAIS[FIM]}
        for _ in range(max_tokens):
            seguintes = []
            for tokens,logp,anterior,st,gates in vivos:
                ps,novo,audit = self.passo(anterior,st)
                expandidos = 0
                for t,p in sorted(ps.items(),key=lambda item:item[1],reverse=True):
                    if t in proibidos or t == ESPECIAIS[FIM] and not tokens:
                        continue
                    if len(tokens)>=3 and tuple(tokens[-3:]+[t]) in {tuple(tokens[i:i+4]) for i in range(len(tokens)-3)}:
                        continue
                    novo_log = logp+math.log(max(p,1e-30))
                    gate = gates+[audit["gerar"]]
                    if t == ESPECIAIS[FIM]:
                        finais.append((tokens,novo_log,gate))
                    else:
                        seguintes.append((tokens+[t],novo_log,t,novo,gate))
                    expandidos += 1
                    if expandidos >= feixe:
                        break
            seguintes.sort(key=lambda item:item[1]/max(1,len(item[0]))**.65,reverse=True)
            vivos = seguintes[:feixe]
            finais.sort(key=lambda item:item[1]/max(1,len(item[0]))**.65,reverse=True)
            finais = finais[:feixe]
            # O logp só pode diminuir; a maior normalização possível usa o
            # limite final. O score atual do prefixo não é um limite superior.
            limite_vivo = max((v[1]/max_tokens**.65 for v in vivos),default=-float("inf"))
            if not vivos or finais and finais[0][1]/max(1,len(finais[0][0]))**.65 >= limite_vivo:
                break
        if finais:
            tokens,logp,gates = max(finais,key=lambda item:item[1]/max(1,len(item[0]))**.65)
            completa = True
        else:
            tokens,logp,_,_,gates = max(vivos,key=lambda item:item[1]/max(1,len(item[0]))**.65) if vivos else ([], -1e9, None, None, [])
            completa = False
        return {"texto":detokenizar(tokens),"tokens":tokens,"completa":completa,
                "log_prob_media":logp/max(1,len(gates)),"proporcao_geracao":sum(gates)/max(1,len(gates)),
                "fonte_tokens":len(estado["tokens"]),"arquitetura":VERSAO}


@lru_cache(maxsize=2)
def _carregar_cacheado(caminho, mtime_ns, tamanho, acelerar):
    from arquivos_contextuais import ler_json
    return DialogoSeq2Seq(ler_json(caminho), acelerar=acelerar)


def carregar(caminho, mtime=None, acelerar=True):
    """Reutiliza somente pesos; nenhum texto ou estado de sessão é cacheado.

    ``mtime`` é aceito para o mesmo contrato do leitor de compreensão;
    o stat real, em nanossegundos, invalida a instância após novo treino.
    """
    from arquivos_contextuais import localizar
    arquivo = localizar(caminho).resolve()
    stat = arquivo.stat()
    return _carregar_cacheado(str(arquivo), stat.st_mtime_ns, stat.st_size, bool(acelerar))
