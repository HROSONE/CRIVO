"""Decisor aprendido: este fato do acervo responde à pergunta?

Quando a espécie que respondeu recusa, a busca aprendida (busca_semantica.py)
e a busca só por palavras propõem os melhores fatos do acervo inteiro. Para
cada candidato, o decisor junta tudo o que se sabe dele:

  busca     probabilidade e posição na busca aprendida, primeiro lugar na
            busca por palavras, e as evidências da busca (palavras, sentido,
            nome do assunto citado inteiro ou em parte, tipo de pergunta);
  leitura   o que a leitura da ficha (leitura_ficha.py) acha desse fato:
            probabilidade, pistas cobertas e quantas faltam;
  pergunta  pergunta direta, sim/não, "o que é X", qualificador absoluto,
            se ela cita a ficha do candidato ou outra.

Um modelo logístico, treinado uma vez (scripts/treinar_decisor.py), dá a
probabilidade de o fato responder. Ele aprendeu também a calar: no treino,
a mesma pergunta aparece com a ficha que responde retirada do acervo, e aí
nenhum candidato responde. Não há limiar por caso nem exceção escrita à mão;
dois cortes, escolhidos na validação, dizem se afirma (com todas as pistas
cobertas) ou aproxima ("não tenho a resposta exata; o mais próximo é…").

Python puro: o mesmo resultado no site e no CI.
"""
import json
import math
from pathlib import Path

CAMINHO_MODELO = Path(__file__).resolve().parent / "artefatos" / "decisor_resposta" / "meta.json"

TRACOS = ("vies", "b_prob", "b_topo", "b_palavras_topo", "b_bm", "b_bm_ficha", "b_nome", "b_nome_parcial",
          "b_sentido", "b_sentido_rel", "b_definicao", "b_tipo_sem_par",
          "l_prob", "l_cobertura", "l_razao", "l_todas", "l_nenhuma", "l_falta_uma", "l_faltam_duas",
          "l_exata", "l_lexico", "l_relacao", "l_vetor", "l_sem_leitura",
          "q_direta", "q_absoluto", "q_simnao", "q_pedido_nome", "q_citada", "q_outra_citada")
CANDIDATOS = 6


def pistas_para(compositor, busca, forma, assunto):
    """Palavras de conteúdo da fala, inclusive nomes de outros conceitos
    citados ("ATP", "células"), menos o nome do assunto do candidato."""
    from busca_semantica import PARADAS
    from leitura_ficha import GENERICAS
    nome = {w for f in busca.nomes.get(assunto, ()) for w in f.split()}
    raizes_nome = {w[:5] for w in nome}
    pistas = []
    for palavra in forma.replace("-", " ").replace(",", " ").split():
        palavra = palavra.strip("?!.;:")
        if (palavra in compositor._FORMA_PERGUNTA or palavra in PARADAS or palavra in GENERICAS
                or len(palavra) < 3 or palavra in nome or palavra[:5] in raizes_nome):
            continue
        palavra = compositor._FORMAS_VER.get(palavra, palavra)
        raiz = compositor._raiz(palavra)
        if raiz not in (r for r, _ in pistas):
            pistas.append((raiz, palavra))
    return tuple(pistas)


def candidatos(busca, fala, excluir=frozenset(), k=CANDIDATOS):
    """[(j, traços da busca, prob, posição, primeiro nas palavras?)] dos k
    melhores fatos fora das fichas em excluir, mais o primeiro da busca só
    por palavras."""
    cand = [(j, t) for j, t in busca.tracos(fala) if busca.fatos[j][0] not in excluir]
    if not cand:
        return []
    z = [sum(busca.pesos[n] * t[n] for n in busca.pesos) for _, t in cand]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    soma = sum(e)
    ordem = sorted(range(len(cand)), key=lambda a: (-z[a], cand[a][0]))
    from busca_semantica import termos
    notas = busca.bm.notas(termos(fala))
    palavras = next((j for j in sorted(notas, key=lambda j: (-notas[j], j))
                     if busca.fatos[j][0] not in excluir), None)
    escolhidos = ordem[:k]
    pos = {cand[a][0]: a for a in range(len(cand))}
    if palavras is not None and palavras in pos and pos[palavras] not in escolhidos:
        escolhidos.append(pos[palavras])
    return [(cand[a][0], cand[a][1], e[a] / soma, r, cand[a][0] == palavras)
            for r, a in enumerate(escolhidos)]


def tracos(bot, quadro, tipo, forma_fala, busca, candidato, citados):
    """(vetor de traços, leitura) de um candidato. forma_fala: (pergunta
    direta?, qualificador absoluto?)."""
    j, tb, prob, posicao, palavras_topo = candidato
    assunto, indice, _ = busca.fatos[j]
    leitor = bot.leitura_ficha
    pistas = pistas_para(bot.compositor, busca, quadro.forma, assunto)
    q = quadro._replace(assunto=assunto, outros=(), pistas=pistas, recusa="")
    leitura = leitor.ler(q, assunto, indice) if pistas else None
    lt = leitura.tracos if leitura is not None else {}
    n_pistas = len(leitor.pistas(q)) if pistas else 0
    cob = leitura.cobertura if leitura is not None else 0
    direta, absoluto = forma_fala
    # Nome do assunto citado em parte ou com outra flexão ("nominalista").
    from busca_semantica import palavras
    raizes = {w[:5] for w in palavras(quadro.texto)}
    parcial = max((sum(1 for w in f.split() if w[:5] in raizes) / len(f.split())
                   for f in busca.nomes.get(assunto, ()) if f), default=0.0)
    x = {
        "vies": 1.0, "b_prob": prob, "b_topo": 1.0 if posicao == 0 else 0.0,
        "b_palavras_topo": 1.0 if palavras_topo else 0.0,
        "b_bm": tb["bm"], "b_bm_ficha": tb["bm_ficha"], "b_nome": tb["nome"], "b_nome_parcial": parcial,
        "b_sentido": tb["sentido"], "b_sentido_rel": tb["sentido_rel"], "b_definicao": tb["definicao"],
        "b_tipo_sem_par": tb["tipo_sem_par"],
        "l_prob": leitura.prob if leitura is not None else 0.0,
        "l_cobertura": min(cob, 6) / 6.0, "l_razao": cob / n_pistas if n_pistas else 0.0,
        "l_todas": float(lt.get("todas", 0.0)), "l_nenhuma": float(lt.get("nenhuma", 0.0)),
        "l_falta_uma": float(lt.get("falta_uma", 0.0)), "l_faltam_duas": float(lt.get("faltam_duas", 0.0)),
        "l_exata": float(lt.get("exata", 0.0)), "l_lexico": float(lt.get("lexico", 0.0)),
        "l_relacao": float(lt.get("relacao", 0.0)), "l_vetor": float(lt.get("vetor", 0.0)),
        "l_sem_leitura": 1.0 if leitura is None else 0.0,
        "q_direta": 1.0 if direta else 0.0, "q_absoluto": 1.0 if absoluto else 0.0,
        "q_simnao": 1.0 if tipo == "simnao" else 0.0, "q_pedido_nome": 1.0 if quadro.pedido_nome else 0.0,
        "q_citada": 1.0 if assunto in citados else 0.0,
        "q_outra_citada": 1.0 if citados - {assunto} else 0.0,
    }
    return [x[t] for t in TRACOS], leitura


def ler_pergunta(bot, fala, quadro, citados=frozenset(), excluir=frozenset()):
    """[(vetor, leitura, assunto, índice, prob da busca)] dos candidatos."""
    from leitura_ficha import ABSOLUTOS, busca_aprendida, pergunta_direta, tipo_pergunta
    from composicao_textual import normalizar
    busca = busca_aprendida(bot.compositor)
    if not busca.aprendida or quadro is None:
        return []
    tipo = tipo_pergunta(normalizar(fala).strip())
    forma_fala = (pergunta_direta(fala), any(ABSOLUTOS.match(p) for _, p in quadro.pistas))
    saida = []
    for cand in candidatos(busca, fala, excluir):
        x, leitura = tracos(bot, quadro, tipo, forma_fala, busca, cand, set(citados))
        assunto, indice, _ = busca.fatos[cand[0]]
        saida.append((x, leitura, assunto, indice, cand[2]))
    return saida


class Decisor:
    def __init__(self, caminho=CAMINHO_MODELO, exigir_aprovacao=True):
        self.pesos = None
        self.limiar_afirmar = self.limiar_aproximar = None
        try:
            meta = json.loads(Path(caminho).read_text(encoding="utf-8"))
            if meta.get("tracos") == list(TRACOS) and (meta.get("controle", {}).get("aprovado")
                                                       or not exigir_aprovacao):
                self.pesos = [float(p) for p in meta["pesos"]]
                self.limiar_afirmar = float(meta["limiar_afirmar"])
                self.limiar_aproximar = float(meta["limiar_aproximar"])
        except (OSError, ValueError, KeyError, TypeError):
            pass

    @property
    def disponivel(self):
        return self.pesos is not None

    def prob(self, x):
        z = sum(w * v for w, v in zip(self.pesos, x))
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))

    def decidir(self, bot, fala, quadro, citados=frozenset(), excluir=frozenset()):
        """(decisão, leitura, assunto, índice, prob do decisor, prob da busca)
        do melhor candidato; decisão é 'afirmar', 'aproximar' ou None."""
        lidos = ler_pergunta(bot, fala, quadro, citados, excluir)
        if not lidos:
            return None, None, None, None, 0.0, 0.0
        notas = [(self.prob(x), x, leitura, a, i, pb) for x, leitura, a, i, pb in lidos]
        p, x, leitura, assunto, indice, pb = max(notas, key=lambda n: (n[0], -n[4]))
        todas = x[TRACOS.index("l_todas")] and not x[TRACOS.index("b_tipo_sem_par")]
        decisao = ("afirmar" if p >= self.limiar_afirmar and todas and leitura is not None
                   else "aproximar" if p >= self.limiar_aproximar and leitura is not None else None)
        return decisao, leitura, assunto, indice, p, pb


_CACHE = {}


def decisor():
    if "d" not in _CACHE:
        _CACHE["d"] = Decisor()
    return _CACHE["d"]
