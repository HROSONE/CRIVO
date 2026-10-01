"""Coordena compreensão de sequência, memória e geração autorais.

Os fatos do motor original continuam sendo evidências. Uma interpretação
neural ou uma resposta gerada não vira fato nem prova. A memória pertence
à instância, e os checkpoints são os únicos objetos compartilhados.
"""
from pathlib import Path
import re
from arquivos_contextuais import localizar


class DialogoContextual:
    def __init__(self, usar_neural=True, modelo_linguagem=None):
        from memoria_dialogo import MemoriaDialogo
        self.memoria=MemoriaDialogo(max_turnos=12)
        self.usar_neural=usar_neural
        self.modelo_linguagem=modelo_linguagem
        self.ultimo_quadro=None
        self.erro=None

    def _compreender(self, texto):
        if not self.usar_neural or not isinstance(texto,str) or not 1<=len(texto)<=1200:
            return None
        caminho=localizar(Path(__file__).with_name("rede_compreensao.json"))
        if not caminho.is_file(): return None
        from compreensao_neural import carregar
        contexto=self.memoria.contexto(texto)
        modelo=carregar(str(caminho.resolve()),caminho.stat().st_mtime_ns)
        return modelo.analisar(texto,contexto.get("historico",[]))

    def _proteger(self, texto, bot, conversa):
        """Preserva uma consulta comprovadamente reconhecida pelo motor."""
        from crivo import chave_pergunta, normalizar, TOPICOS
        if chave_pergunta(texto) in bot.indices_exatos: return True
        if "```" in texto or re.match(r"\s*(?:print\(|def |class |import |SELECT\b)",texto,re.I):
            return True
        from pedidos_gerativos import criacao,mensagem,revisao
        if criacao(texto) or mensagem(texto) or revisao(texto): return True
        from conversa_assistente import responder_contato, responder, preparar_pedido, preparar_conversa
        if responder_contato(texto,bot.ultimo_turno) is not None:
            return True
        n=normalizar(texto).strip(" ?!. ")
        # Os comandos já atendidos têm contratos próprios. A recusa genérica
        # de perguntas pessoais não participa desta guarda.
        if n in ("exemplo","exemplos","me de exemplos","sugestoes"):
            return True
        if bot._social(n) is not None: return True
        social=responder(texto,bot,TOPICOS,bot.ultimo_ato_social)
        if social is not None and social[0]!="duvida": return True
        if bot.planejador.analisar(texto) is not None: return True
        consulta=preparar_pedido(preparar_conversa(texto))
        composicao=bot.compositor.responder(consulta,bot.contexto_textual)
        if composicao is not None and composicao[2] is not None:
            # Inclui o microcircuito associativo incorporado à main.
            return True
        alvo=bot._alvo_definicao(consulta)
        if alvo is not None and bot.compositor.resolver(alvo) is not None:
            return True
        factual=bot.analisador_portugues.analisar(consulta)
        if factual is not None and (factual.intencao!="definir" or
                bot.compositor.resolver(factual.sujeito) is not None):
            return True
        if bot.raciocinio is not None and bot.raciocinio.identificar_relacao(consulta) is not None:
            return True
        ato=conversa.analisar(texto,usar_neural=False)
        if ato is not None:
            if ato.operacao=="cancelar": return True
            if ato.operacao=="transformar" and bot.contexto_textual is not None:
                return True
            if ato.operacao=="consulta" and bot.compositor.resolver(ato.alvo) is not None:
                return True
        from consultas_relacionais import ConsultaInvalida
        try:
            if bot.consultas_relacionais.analisar(texto,bot.contexto_consulta) is not None:
                return True
        except ConsultaInvalida:
            # A recusa de uma consulta reconhecida pertence ao mesmo motor.
            return True
        # Quantificação universal pertence ao motor de premissas, que mantém
        # a hipótese separada do grafo factual.
        if re.match(r"\s*(?:se|suponha que)\s+tod[oa]s?\b",n): return True
        return False

    def preparar(self, texto, bot, conversa):
        self.ultimo_quadro=None
        self.erro=None
        if self.modelo_linguagem and self.usar_neural:
            # A geração causal não depende de reconhecer um dos 23 atos antigos.
            # O quadro recusado não cria spans, objetivos ou fatos na memória.
            if self._proteger(texto,bot,conversa): return None
            quadro={"ato":"livre", "aceita":False, "confianca":0.,
                    "rota":"conversa", "confianca_rota":None, "spans":[]}
            self.ultimo_quadro=quadro
            from dialogo_linguagem_profunda import responder
            contexto=self.memoria.contexto(texto)
            try:
                saida=responder(self.modelo_linguagem,texto,contexto.get("historico_ativo",[]))
            except (ImportError,ValueError,RuntimeError,OSError,KeyError) as exc:
                self.erro=str(exc);return None
            if not self._valida(saida): return None
            from linguagem_conversa import Ato,Preparacao
            self.ultimo_quadro=dict(quadro,geracao={k:v for k,v in saida.items() if k!="texto"})
            return Preparacao(Ato("dialogo_contextual_livre","dialogar"),
                              ("conversa:neural_livre",saida["texto"],None,""))
        try:
            q=self._compreender(texto)
        except (ValueError,TypeError,KeyError,OSError) as exc:
            self.erro=str(exc);return None
        if q is None: return None
        self.ultimo_quadro=q
        if self._proteger(texto,bot,conversa):
            self.ultimo_quadro=dict(q,aceita=False)
            return None
        if not q.get("aceita_rota") or q.get("rota")!="conversa": return None
        if q.get("aceita") and q["ato"] in ("consulta","escrita","saudacao","encerrar"):
            return None
        return self._responder(texto,q,bot,conversa)

    def _responder(self, texto, quadro, bot, conversa):
        from linguagem_conversa import Ato,Preparacao
        caminho=localizar(Path(__file__).with_name("rede_dialogo_seq2seq.json"))
        if not caminho.is_file(): return None
        from dialogo_seq2seq import carregar
        contexto=self.memoria.contexto(texto,quadro)
        historico=[h for h in contexto.get("historico_ativo",[]) if h["papel"] in ("usuario","assistente")]
        fontes=self.memoria.fontes_relevantes(texto,quadro)
        if fontes and not contexto.get("referencia_ambigua"):
            recentes=historico[-4:]
            historico=[f for f in fontes if f not in recentes]+recentes
        try:
            modelo=carregar(str(caminho.resolve()),caminho.stat().st_mtime_ns)
            saida=modelo.gerar(texto,historico=historico,max_tokens=96)
        except (ValueError,TypeError,KeyError,OSError) as exc:
            self.erro=str(exc);return None
        if not self._valida(saida): return None
        resposta=saida["texto"]
        self.ultimo_quadro=dict(quadro,geracao={k:v for k,v in saida.items() if k!="texto"})
        ato=quadro["ato"] if quadro.get("aceita") else "livre"
        identificador="conversa:neural_"+ato
        return Preparacao(Ato("dialogo_contextual_"+ato,"dialogar"),
                          (identificador,resposta,None,""))

    @staticmethod
    def _valida(saida):
        texto=saida.get("texto","")
        if not saida.get("completa") or not 8<=len(texto)<=2400:
            return False
        if not texto.rstrip().endswith((".","?","!")): return False
        palavras=re.findall(r"\w+|[^\w\s]",texto.casefold())
        sequencias=[tuple(palavras[i:i+5]) for i in range(len(palavras)-4)]
        return len(sequencias)==len(set(sequencias))

    def registrar(self, pergunta, resposta, identificador):
        self.memoria.registrar(pergunta,resposta,identificador,self.ultimo_quadro)

    def painel(self):
        q=self.ultimo_quadro
        if not q: return None
        return {"ato":q["ato"] if q.get("aceita") else None,
                "confianca":q["confianca"],"aceita":q.get("aceita",False),
                "rota":q.get("rota"),"confianca_rota":q.get("confianca_rota"),
                "trechos":[{"papel":s["papel"],"texto":s["texto"]} for s in q.get("spans",[])],
                "modelo":("Transformer causal treinado do zero" if self.modelo_linguagem else
                          "BiGRU com atenção e papéis; encoder-decoder com cópia")}
