"""Estado interno do turno: o quadro que as espécies leem e escrevem.

Antes, cada mecanismo recebia o texto, decidia sozinho e devolvia uma resposta
ou uma recusa. Se a busca factual não achava as palavras exatas, dizia
"Reconheci o assunto Titã, mas não tenho evidência", mesmo com a ficha de Titã
falando de chuva. O conhecimento existia, mas nenhuma outra parte via a
recusa nem o que já tinha sido entendido.

Agora cada fala monta um estado único:

  compreensão   tipo de pergunta, entidades (da fala ou do contexto),
                pistas de conteúdo, negação;
  memória       assunto da conversa, turno anterior, oferta pendente;
  conhecimento  fatos e ligações das entidades;
  propostas     o que cada espécie propõe (responder, recusar, aproximar),
                com a evidência que tem;
  decisão       quem falou e por quê.

O árbitro lê as propostas. Quando a espécie que respondeu recusou e a leitura
da ficha tem evidência forte sobre a mesma entidade, a leitura fala. Com
evidência média, a resposta diz que não tem a resposta exata e mostra o fato
mais próximo. Sem evidência, a recusa fica.

O estado não é uma rede nem uma representação aprendida de ponta a ponta. É o
contrato comum que permite a várias espécies (regras, redes e acervo) operar
sobre o mesmo entendimento do turno. A API o expõe em `internal_state`.
"""
import re
from collections import namedtuple

from composicao_textual import normalizar

Entidade = namedtuple("Entidade", "id nome origem")
Proposta = namedtuple("Proposta", "especie ident acao evidencia")

RECUSAS = frozenset(("fora", "duvida", "social:nao_entendido"))
_RECUSA_TEXTO = ("não tenho", "ainda não", "reconheci o assunto", "não reconheci", "não consegui",
                 "não encontrei", "hum, não entendi")
_PRONOME = re.compile(r"\b(?:ele|ela|eles|elas|dele|dela|deles|delas|isso|disso|nele|nela)\b")
_ESCRITA = re.compile(r"\b(?:escrev\w*|resum\w*|frases?|roteiro|topicos|paragrafos?|linhas?|redacao|poema)\b")
# Pedido de escrita (imperativo); "quem escreveu" é pergunta factual.
_PEDIDO_ESCRITA = re.compile(r"\b(?:escreva|escreve|escrever|resum\w*|redija|frases?|roteiro|topicos|"
                             r"paragrafos?|linhas?|redacao|poema)\b")
_PESSOAL = re.compile(r"\b(?:voce|vc|seu|sua|te|contigo)\b")


class EstadoInterno:
    def __init__(self, fala):
        self.fala = fala
        self.quadro = None
        self.tipo = None
        self.entidades = []
        self.pistas = []
        self.negacao = False
        self.memoria = {}
        self.conhecimento = {}
        self.propostas = []
        self.decisao = None

    @property
    def entidade(self):
        """A entidade principal, quando há exatamente uma."""
        return self.entidades[0] if len(self.entidades) == 1 else None

    def propor(self, especie, ident, acao, evidencia=None):
        self.propostas.append(Proposta(especie, ident, acao, evidencia or {}))

    def decidir(self, especie, acao, motivo):
        self.decisao = {"especie": especie, "acao": acao, "motivo": motivo}

    def para_dict(self):
        return {
            "understanding": {"question_type": self.tipo,
                              "entities": [e._asdict() for e in self.entidades],
                              "cues": [p for _, p in self.pistas], "negation": self.negacao},
            "memory": self.memoria,
            "knowledge": self.conhecimento,
            "proposals": [{"species": p.especie, "id": p.ident, "action": p.acao, "evidence": p.evidencia}
                          for p in self.propostas],
            "decision": None if self.decisao is None else {
                "species": self.decisao["especie"], "action": self.decisao["acao"],
                "reason": self.decisao["motivo"]},
        }


def guardar_fidelidade(bot, rota, ident, resposta):
    """Uma resposta de outra peça ou sem referente não chega ao usuário.

    Aplica-se às operações contextuais escolhidas explicitamente, preservando
    as verificações de segurança/fatos da entrada e os executores existentes.
    """
    peca = rota['peca']
    aceitos = {'memoria': ('conversa:memoria_sessao', 'conversa:sessao_'),
               'calculo': ('conversa:raciocinio', 'calculo:'),
               'programacao': ('programacao:',),
               'escrita': ('escrita:', 'conversa:gerada_'),
               'esclarecimento': ('conversa:esclarecer',)}
    motivos = []
    if peca == 'esclarecimento' and rota['ato'] == 'capacidades':
        aceitos['esclarecimento'] = ('social:assuntos',)
    n = normalizar(resposta)
    if rota['status'] == 'executado':
        if peca in aceitos and not ident.startswith(aceitos[peca]):
            motivos.append('executor não entregou o tipo pedido')
        if peca == 'fato' and bot.contexto_textual is None:
            motivos.append('resposta factual sem unidades com fonte')
        if peca == 'calculo':
            q = bot.raciocinio_conversa.ultimo or {}
            if 'minutos' not in n:
                motivos.append('resposta não trata da unidade de tempo')
            if q.get('operacao') == 'tempo_restante' and q.get('status') == 'calculado':
                resultado = q['resultado']
                for valor in (resultado['disponivel'], resultado['restante']):
                    esperado = valor.lstrip('-') if valor.startswith('-') and 'faltam' in n else valor
                    numero = re.escape(esperado).replace(r'\.', r'[.,]')
                    if not re.search(r'(?<!\d)' + numero + r'(?!\d)', resposta):
                        motivos.append('resultado calculado ausente')
                for atividade in q.get('entradas', {}):
                    if normalizar(atividade) not in n:
                        motivos.append('atividade ausente: ' + atividade)
        if peca in ('fato', 'escrita') and bot.contexto_textual is not None:
            from curriculo_mundo import texto_fato
            for e, i in bot.contexto_textual.exibidos:
                if normalizar(texto_fato(bot.compositor.itens[e]['fatos'][i])) not in n:
                    motivos.append('unidade factual selecionada ausente')
        if peca == 'memoria':
            q = (bot.historico[-1].get('memoria_sessao') or bot.historico[-1].get('conversa_sessao') or {})
            if 'afirmacoes_esperadas' in rota and q.get('afirmacoes', []) != rota['afirmacoes_esperadas']:
                motivos.append('seleção não corresponde à pergunta da sessão')
            if rota.get('dado_desconhecido') and (q.get('afirmacoes') or not re.search(
                    r'\b(?:nao tenho|nao sei|nao informou)\b', n)):
                motivos.append('ausência de informação virou uma afirmação')
            for i in q.get('afirmacoes', ()):
                if not isinstance(i, int) or not 0 <= i < len(bot.memoria_sessao.afirmacoes):
                    motivos.append('referência de memória inválida')
                    continue
                f = bot.memoria_sessao.afirmacoes[i]
                if (f['status'] != 'ativo' or f['fonte']['origem'] != 'usuario'
                        or f.get('escopo') not in ('declarado', 'fala_reportada')):
                    motivos.append('afirmação sem fonte ativa do usuário')
                if rota.get('sujeitos') and f['sujeito'] not in rota['sujeitos']:
                    motivos.append('afirmação de outra pessoa')
                from compreensao_intencao import frase_da_sessao
                if normalizar(frase_da_sessao(bot.memoria_sessao, f)) not in n:
                    motivos.append('sujeito, relação ou polaridade da afirmação alterados')
                nome = bot.memoria_sessao._nome(f['sujeito'], '')
                inversa = {'gosto': ' não gosta de ', 'não gosta': ' gosta de ',
                           'preferência': ' não prefere '}.get(f['relacao'])
                if inversa and normalizar(nome + inversa + f['valor']) in n:
                    motivos.append('resposta também contradiz a afirmação selecionada')
                if f['relacao'] == 'preferência' and normalizar(f['valor']) not in n:
                    motivos.append('preferência selecionada ausente')
        if peca in ('memoria', 'esclarecimento', 'fato') or peca == 'escrita' and rota['ato'] in ('historia', 'corrigir'):
            for referente in rota['referentes']:
                presente = normalizar(referente) in n
                if not presente and peca == 'fato' and bot.contexto_textual is not None:
                    # O nome da ficha pode ser composto ("céu azul"), enquanto
                    # suas unidades separam as palavras ("o azul ... o céu").
                    # Exigir ficha selecionada e seus termos, além das unidades
                    # literais verificadas acima, preserva a prova do assunto.
                    assunto = bot.compositor.resolver(referente)
                    selecionados = {e for e, _ in bot.contexto_textual.exibidos}
                    termos = re.findall(r'\w+', normalizar(referente))
                    presente = (assunto in selecionados and
                                (bot.compositor._menciona_conceito(assunto, n) or
                                 bool(termos) and all(re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', n)
                                                    for t in termos)))
                if not presente:
                    motivos.append('referente ausente: ' + referente)
        if rota.get('frases'):
            corpo = resposta.split('\n', 1)[-1].strip()
            frases = re.findall(r'[^.!?]+[.!?](?:\s|$)', corpo)
            if len(frases) != rota['frases']:
                motivos.append('quantidade de frases não atendida')
    if motivos:
        ident = 'conversa:esclarecer'
        resposta = ('Não consegui atender esse pedido preservando a tarefa' +
                    (' e ' + ', '.join(rota['referentes']) if rota['referentes'] else '') +
                    '. Pode esclarecer o que devo fazer?')
        if 'quantidade de frases não atendida' in motivos:
            resposta = ('Não consegui escrever ' + str(rota['frases']) + ' frases com ' +
                        ', '.join(rota['referentes']) + '. Quer um rascunho mais curto?')
        if '_escrita_anterior' in rota:
            bot.conversacao.geracao.ultima_escrita = rota['_escrita_anterior']
            bot.conversacao.geracao.ultima_criacao = rota['_escrita_anterior']
        rota['status'] = 'bloqueado_pela_guarda'
        bot.contexto_textual = None
        if bot.historico:
            bot.historico[-1]['id'] = ident
    rota['guarda'] = dict(aceita=not motivos, motivos=motivos)
    if bot.historico:
        bot.historico[-1]['natural_routing'] = {k:v for k,v in rota.items()
                                               if not k.startswith('_') and k not in ('resultado', 'consulta', 'fatos')}
    return ident, resposta


def construir(bot, fala):
    """Estado inicial do turno, antes de qualquer espécie responder."""
    estado = EstadoInterno(fala)
    if not isinstance(fala, str):
        return estado
    from leitura_ficha import GENERICAS, tipo_pergunta
    c = bot.compositor
    n = normalizar(fala)
    quadro = c.interpretar(fala)
    estado.quadro = quadro
    estado.tipo = tipo_pergunta(n.strip())
    estado.negacao = bool(re.search(r"\b(?:nao|nunca|jamais|nem)\b", n))
    if quadro is not None:
        estado.pistas = [(r, p) for r, p in quadro.pistas if p not in GENERICAS]
        for ident in ((quadro.assunto,) if quadro.assunto else ()) + tuple(quadro.outros):
            estado.entidades.append(Entidade(ident, c.itens[ident]["nome"], "fala"))
    assunto = getattr(bot, "assunto_conversa", None)
    if not estado.entidades and assunto in c.itens and _PRONOME.search(n):
        estado.entidades.append(Entidade(assunto, c.itens[assunto]["nome"], "contexto"))
    turno = getattr(bot, "ultimo_turno", None) or {}
    estado.memoria = {
        "conversation_subject": c.itens[assunto]["nome"] if assunto in c.itens else None,
        "previous_turn_id": turno.get("id"),
        "pending_offer": bool(getattr(bot, "oferta_pendente", None)),
    }
    for e in estado.entidades:
        item = c.itens[e.id]
        estado.conhecimento[e.id] = {
            "facts": len(item["fatos"]),
            "links": sum(1 for r in c.ligacoes_mundo if e.id in (r["origem"], r["destino"])),
        }
    return estado


def recusou(ident, resposta):
    return ident in RECUSAS or resposta.strip().lower().startswith(_RECUSA_TEXTO)


# Só a recusa por falta de evidência pode ser revista pela leitura. "duvida"
# (consulta lógica composta ou ambígua) e "logica:desconhecido" são recusas
# deliberadas de quem entendeu a pergunta.
REVISAVEIS = frozenset(("fora", "social:nao_entendido"))


def _pode_ler(estado, autoria=False):
    """A leitura da ficha só entra numa pergunta factual sobre UMA entidade
    citada na fala, sem negação, pedido de escrita ou pergunta pessoal."""
    q = estado.quadro
    # "Onde fica o Egito?" e "O que fazem os rins?" não têm pistas além do
    # assunto: o tipo da pergunta guia a leitura, que confere sozinha.
    if q is None or q.recusa and q.recusa != "sem_pistas" or q.outros or estado.negacao:
        return False
    e = estado.entidade
    if e is None or e.origem != "fala" or e.id != q.assunto:
        return False
    n = normalizar(estado.fala)
    escrita = _PEDIDO_ESCRITA if autoria else _ESCRITA
    return not (escrita.search(n) or _PESSOAL.search(n))


def arbitrar(bot, estado, ident, resposta):
    """Registra a proposta da espécie que respondeu e, se ela recusou, ouve
    a leitura da ficha. Devolve (ident, resposta) finais."""
    from ecossistema import mecanismo_do_turno
    especie = mecanismo_do_turno(bot, estado.fala, ident)
    recusa = recusou(ident, resposta)
    estado.propor(especie, ident, "recusar" if recusa else "responder")
    if not recusa or not isinstance(estado.fala, str) or not getattr(bot, "usar_leitura_ficha", True):
        estado.decidir(especie, "recusar" if recusa else "responder", "primeira espécie a responder")
        return ident, resposta
    if ident in REVISAVEIS and _pode_buscar(estado):
        return _ler_pela_busca(bot, estado, especie, ident, resposta)
    if ident not in REVISAVEIS or not _pode_ler(estado):
        estado.decidir(especie, "recusar", "leitura fora do nicho (negação, relação, escrita ou sem entidade)")
        return ident, resposta
    leitor = bot.leitura_ficha
    indice = None
    if estado.quadro.recusa == "sem_pistas":
        # Sem pistas ("Onde fica o Egito?"), a busca aprendida escolhe o fato
        # dentro da ficha (a definição que diz onde fica, não a capital) e a
        # leitura confere esse fato.
        from leitura_ficha import busca_aprendida
        busca = busca_aprendida(bot.compositor)
        achados = busca.buscar(estado.fala, k=1, assuntos={estado.entidade.id}) if busca.aprendida else []
        indice = achados[0][2] if achados else None
    leitura = leitor.ler(estado.quadro, estado.entidade.id, indice=indice)
    decisao = leitor.decisao(leitura)
    evidencia = None if leitura is None else {
        "fact": leitura.indice, "probability": leitura.prob, "margin": leitura.margem,
        "cues_covered": leitura.cobertura, "question_type": leitura.tipo}
    estado.propor("leitura_ficha", None, decisao or "calar", evidencia)
    if decisao is None:
        # A ficha citada não tem a resposta; numa pergunta aberta, ela pode
        # estar em outra ("Que cientista estudou a evolução?"). Sim/não e
        # "o que é X" são sobre a ficha citada: a recusa fica.
        # Conceito comum citado de passagem ("A luz passa pelo vácuo?") não é
        # o assunto do sim/não: a resposta pode estar na ficha do vácuo.
        comum = not bot.compositor.itens[estado.entidade.id]["nome"][:1].isupper()
        if (estado.tipo != "simnao" or comum) and not estado.quadro.pedido_nome:
            # Conceito amplo (água, temperatura) é só uma palavra da pergunta:
            # a busca procura em todas as fichas, como sem entidade citada.
            if bot.compositor._amplo(estado.entidade.id):
                return _ler_pela_busca(bot, estado, especie, ident, resposta, sem_citados=True)
            return _ler_pela_busca(bot, estado, especie, ident, resposta, citado=estado.entidade.id)
        estado.decidir(especie, "recusar", "a leitura da ficha não achou evidência suficiente")
        return ident, resposta
    return _responder_com_leitura(bot, estado, especie, leitura, decisao, evidencia)


def resgatar(bot, estado, ident, resposta):
    """Última tentativa: conserva as respostas de todas as espécies anteriores."""
    if (ident not in REVISAVEIS or not recusou(ident, resposta)
            or not getattr(bot, "usar_leitura_ficha", True) or not _pode_ler(estado, autoria=True)):
        return ident, resposta
    leitura = bot.leitura_ficha.resgatar(estado.quadro, estado.entidade.id)
    if leitura is None:
        return ident, resposta
    evidencia = {"fact": leitura.indice, "probability": leitura.prob, "margin": leitura.margem,
                 "cues_covered": leitura.cobertura, "question_type": leitura.tipo,
                 "semantic_rescue": True, "reader_probability": leitura.tracos["prob_transformer"],
                 "verified_field": leitura.tracos.get("campo_verificado")}
    estado.propor("leitura_ficha", None, "aproximar", evidencia)
    return _responder_com_leitura(bot, estado, "política anterior", leitura, "aproximar", evidencia,
                                  "recusa final; leitor próprio e evidência calibrada sugerem uma aproximação")


def _responder_com_leitura(bot, estado, especie, leitura, decisao, evidencia, motivo=None):
    assunto, i = leitura.assunto, leitura.indice
    novo_ident, texto, ctx = bot.compositor.compor((assunto,), "explicacao", selecionados=((assunto, i),),
                                                  origem="conhecimento")
    bot.contexto_textual = ctx
    if decisao == "afirmar":
        novo_ident = "escrita:explicacao"
        texto, com_voz = bot._dar_voz(estado.fala, texto)
        bot.ultima_resposta_mostrada = texto
    else:
        novo_ident = "leitura:aproximacao"
        com_voz = False
        bot.oferta_pendente = None
        texto = ("Não tenho uma resposta exata para essa pergunta. O que a ficha de %s traz de mais "
                 "próximo é:\n\n%s" % (bot.compositor.itens[assunto]["nome"], texto))
    # Achado pela busca (fora da ficha citada) ou lido na ficha citada.
    mecanismo = "busca_aprendida" if "search_subject" in evidencia else "leitura_ficha"
    registro = {"pergunta": estado.fala, "id": novo_ident, "mecanismo": mecanismo,
                "leitura": dict(evidencia, decision=decisao, subject=assunto)}
    if com_voz:
        registro["voz"] = "voz_propria"
    if bot.historico and bot.historico[-1].get("pergunta") == estado.fala:
        bot.historico[-1].clear()
        bot.historico[-1].update(registro)
    else:
        bot.historico.append(registro)
        bot.historico = bot.historico[-20:]
    bot.ultimo_turno = {"pergunta": estado.fala, "id": novo_ident}
    bot.assunto_conversa = assunto
    bot.esclarecimento = None
    estado.decidir(mecanismo, decisao, motivo or "%s recusou; a ficha de %s tem evidência (p=%.2f)"
                   % (especie, bot.compositor.itens[assunto]["nome"], leitura.prob))
    return novo_ident, texto


# Busca aprendida (busca_semantica.py): quando a pergunta não cita o nome de
# nenhum assunto, a busca procura o fato no acervo inteiro e a leitura da
# ficha confere se ele responde. A busca ordena bem, mas não sabe quando não
# há resposta; por isso só fala quando a leitura do fato achado o confirma
# (pelo menos duas pistas cobertas; afirmar exige todas).
LIMIAR_BUSCA = 0.5
LIMIAR_BUSCA_APROXIMAR = 0.7
LIMIAR_BUSCA_MINIMO = 0.2


def _pode_buscar(estado):
    """Pergunta factual sem nenhuma entidade reconhecida (nem da conversa),
    sem negação, relação, pedido de escrita ou pergunta pessoal. "O que é
    Ceres?" sem ficha de Ceres pede a identidade de algo desconhecido: um
    fato que só cita o nome não é a resposta, e a recusa continua."""
    q = estado.quadro
    if q is None or q.pedido_nome or estado.negacao:
        return False
    # "Qual organela produz ATP nas células?" cita dois conceitos, e a
    # resposta está numa terceira ficha. Relação com direção ("a memória
    # ajuda o sono?") continua recusada: só perguntas abertas, não sim/não.
    relacao = q.recusa == "relacao_entre_conceitos" and estado.tipo != "simnao"
    # Muitas palavras de conteúdo ("Por que uma geada que destrói parte da
    # safra de café faz o preço subir?") desanimam a busca por palavras
    # exatas, não a busca aprendida; a leitura continua conferindo cada pista.
    longa = q.recusa == "tamanho" and len(estado.fala) <= 200 or q.recusa == "sem_pistas" and len(q.pistas) > 6
    if not (relacao or longa) and (q.recusa or q.assunto or q.outros or estado.entidades):
        return False
    if longa and (q.assunto or q.outros or estado.entidades):
        return False
    if relacao and any(e.origem != "fala" for e in estado.entidades):
        return False
    n = normalizar(estado.fala)
    return not (_PEDIDO_ESCRITA.search(n) or _PESSOAL.search(n))


def _ler_pela_busca(bot, estado, especie, ident, resposta, citado=None, sem_citados=False):
    """citado: a ficha citada na fala, cuja leitura já não achou resposta; a
    busca só fala se achar outra ficha. Duas propostas, a da busca aprendida e
    a da busca só por palavras (melhor quando a pergunta não traz nome
    nenhum); a leitura confere cada uma e fala a que ela confirmar."""
    from leitura_ficha import busca_aprendida
    busca = busca_aprendida(bot.compositor)
    # As fichas citadas já foram lidas (ou a pergunta as relaciona): vale o
    # melhor fato de outra ficha.
    citados = set() if sem_citados else {e.id for e in estado.entidades} | ({citado} if citado else set())
    achados = [a for a in (busca.buscar(estado.fala, k=10) if busca.aprendida else ()) if a[1] not in citados]
    if not achados:
        estado.decidir(especie, "recusar", "a leitura da ficha não achou evidência suficiente" if citado
                       else "sem fato achado pela busca fora das fichas citadas")
        return ident, resposta
    # Probabilidade entre os fatos que sobraram (fora das fichas citadas).
    total = sum(a[0] for a in achados)
    probs = {(a[1], a[2]): a[0] / total for a in achados}
    propostas = [achados[0][1:]]
    palavras = next((a for a in busca.buscar_palavras(estado.fala, k=10) if a[0] not in citados), None)
    if palavras is not None and palavras not in propostas:
        propostas.append(palavras)
    conferidas = [_conferir(bot, estado, busca, probs.get(alvo, 0.0), *alvo) for alvo in propostas]
    ordem = {"afirmar": 2, "aproximar": 1, None: 0}
    decisao, leitura, evidencia, prob = max(
        conferidas, key=lambda c: (ordem[c[0]], c[1].prob if c[1] is not None else 0.0))
    assunto = evidencia["search_subject"]
    estado.propor("busca_aprendida", None, decisao or "calar", evidencia)
    if decisao is None:
        estado.decidir(especie, "recusar", "a busca achou %s, mas a leitura não confirmou"
                       % bot.compositor.itens[assunto]["nome"])
        return ident, resposta
    return _responder_com_leitura(
        bot, estado, especie, leitura, decisao, evidencia,
        "%s recusou; a busca achou %s (p=%.2f) e a leitura confirmou (p=%.2f)"
        % (especie, bot.compositor.itens[assunto]["nome"], prob, leitura.prob))


def _conferir(bot, estado, busca, prob, assunto, indice):
    """Leitura do fato proposto pela busca: (decisão, leitura, evidência, prob)."""
    from busca_semantica import PARADAS
    from leitura_ficha import GENERICAS
    # Pistas: todas as palavras de conteúdo da fala, inclusive os nomes de
    # conceitos citados ("ATP", "células"), menos o nome do assunto achado.
    c = bot.compositor
    nome = {w for f in busca.nomes.get(assunto, ()) for w in f.split()}
    raizes_nome = {w[:5] for w in nome}
    pistas = []
    for palavra in estado.quadro.forma.replace("-", " ").replace(",", " ").split():
        palavra = palavra.strip("?!.;:")
        if (palavra in c._FORMA_PERGUNTA or palavra in PARADAS or palavra in GENERICAS or len(palavra) < 3
                or palavra in nome or palavra[:5] in raizes_nome):
            continue
        palavra = c._FORMAS_VER.get(palavra, palavra)
        raiz = c._raiz(palavra)
        if raiz not in (r for r, _ in pistas):
            pistas.append((raiz, palavra))
    pistas = tuple(pistas)
    quadro = estado.quadro._replace(assunto=assunto, outros=(), pistas=pistas, recusa="")
    leitor = bot.leitura_ficha
    # A leitura confere o fato que a busca achou: todas as pistas cobertas.
    leitura = leitor.ler(quadro, assunto, indice) if pistas else None
    decisao = leitor.decisao(leitura)
    evidencia = {"search_subject": assunto, "search_fact": indice, "search_probability": round(prob, 4)}
    if leitura is not None:
        evidencia.update({"fact": leitura.indice, "probability": leitura.prob, "margin": leitura.margem,
                          "cues_covered": leitura.cobertura, "question_type": leitura.tipo})
    # Duas pistas cobertas no mínimo: uma só palavra em comum não basta para
    # dizer que um fato achado sem o nome do assunto responde. Aproximar ("não
    # tenho a resposta exata; o mais próximo é…") pede a busca mais confiante.
    cob = leitura.cobertura if leitura is not None else 0
    # Pergunta longa: a leitura só aproxima se faltar no máximo uma pista;
    # aqui basta cobrir três ou mais e pelo menos metade delas (perguntas sem
    # resposta no acervo cobrem uma ou nenhuma).
    if (decisao is None and leitura is not None and leitor.aprendida and cob >= 3
            and 2 * cob >= len(leitor.pistas(quadro)) and leitura.prob >= leitor.limiar_aproximar
            and leitura.tracos.get("pergunta_direta") and not leitura.tracos.get("absoluto")
            and not leitura.tracos.get("tipo_sem_par")):
        decisao = "aproximar"
    # A probabilidade da busca cai quando a ficha tem vários fatos parecidos;
    # com a leitura cobrindo três pistas ou mais, a evidência dela compensa.
    if not (cob >= 2 and (decisao == "afirmar" and prob >= LIMIAR_BUSCA
                          or decisao == "aproximar" and (prob >= LIMIAR_BUSCA_APROXIMAR
                                                         or cob >= 3 and prob >= LIMIAR_BUSCA_MINIMO))):
        decisao = None
    return decisao, leitura, evidencia, prob
