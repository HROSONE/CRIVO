"""Avaliação única prospectiva, exclusivamente após finalizar os dois treinos.

As quatro condições usam a mesma decodificação e os mesmos exemplos. Nenhum
rótulo de evento, banco, trajetória ou alvo é fornecido à rede: lote recebe
somente IDs derivados de turnos. Gold é utilizado depois para medir o resultado.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

# apoio precisa preceder rede: fornece as interfaces próprias e seus caminhos.
from apoio import ROOT, ASSOC, CONTEXT, INICIAL, escrever, sha
from rede import carregar
from preparo import codificar as codificar_novo
from normalizacao import codificar as codificar_antigo
from rede_eventos import coletar, medidas
from tokenizers import Tokenizer
import torch

EVENTOS_CRITICOS = ('correcao', 'hipotese', 'retorno', 'confirmacao')
EVENTOS_TODOS = ('declaracao', 'correcao', 'hipotese', 'retorno', 'consulta', 'confirmacao')
PAINEIS_CONHECIDOS = ('retencao_conhecida', 'associacao_conhecida', 'contextual_conhecido')
RETENCAO = ROOT / 'experimentos/retencao_contrastes_20261008'
AUTORIA_CASOS_SHA256 = 'e4d12906a5de5538312754ee63d0af079686fb86e4145116c2e7c8bcb1938235'
AUTORIA_PROTOCOLO_SHA256 = 'a1c38076a0ffbf3c0e4b02e3fd2a8beb374c853b3726e24ffce4c53373df3faa'


def exigir(condicao, mensagem):
    if not condicao:
        raise RuntimeError(mensagem)


def ler(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fontes_identicas(gold, previsto):
    if gold is None or previsto is None:
        return gold is previsto
    if gold.get('invalido') or previsto.get('invalido'):
        return False
    return all(gold[k] == previsto.get(k) for k in ('turno', 'inicio', 'fim', 'texto'))


def enriquecer(rows, exemplos):
    exigir(len(rows) == len(exemplos), 'Número de traços diverge dos exemplos; não omitir falhas.')
    for r, e in zip(rows, exemplos):
        exigir((r['sessao'], r['etapa']) == (e['sessao'], e['etapa']), 'Traços fora de ordem.')
        previstos = r['proposta']['argumentos']
        estritos = [fontes_identicas(g, p) for g, p in zip(e['argumentos'], previstos)]
        ref = fontes_identicas(e['referente'], r['proposta']['referente'])
        r['argumentos_fonte_estrita'] = estritos
        r['referente_fonte_estrita'] = ref
        # O contrato legado aceita referente literal de outro turno. A métrica
        # adicional exige fonte exata dos argumentos sem mudar essa convenção.
        r['contrato_argumentos_fonte_estrita'] = r['contrato'] and all(estritos)
        r['contrato_todas_fontes_estritas'] = r['contrato_argumentos_fonte_estrita'] and ref
    return rows


def medir(rows):
    out = medidas(rows)
    n = len(rows)
    out['macro_contrato_familias'] = sum(v['acuracia'] for v in out['por_familia'].values()) / len(out['por_familia'])
    if out['por_evento']:
        out['macro_contrato_eventos'] = sum(v['acuracia_contrato'] for v in out['por_evento'].values()) / len(out['por_evento'])
    out['fracao_sessoes_completas'] = out['sessoes_completas'] / out['sessoes']
    out['resultado_correto'] = sum(r['resultado_correto'] for r in rows) / n
    out['proveniencia_estrita'] = {
        'argumentos_por_slot': [sum(r['argumentos_fonte_estrita'][i] for r in rows) / n for i in range(3)],
        'todos_argumentos': sum(all(r['argumentos_fonte_estrita']) for r in rows) / n,
        'referente': sum(r['referente_fonte_estrita'] for r in rows) / n,
        'contrato_argumentos': sum(r['contrato_argumentos_fonte_estrita'] for r in rows) / n,
        'contrato_todas_fontes': sum(r['contrato_todas_fontes_estritas'] for r in rows) / n,
    }
    agrupadas = defaultdict(list)
    for r in rows:
        agrupadas[r['sessao']].append(r['contrato_argumentos_fonte_estrita'])
    out['proveniencia_estrita']['sessoes_contrato_argumentos_completas'] = sum(all(v) for v in agrupadas.values())
    for ev, v in out['por_evento'].items():
        rs = [r for r in rows if r.get('evento') == ev]
        v['contrato_argumentos_fonte_estrita'] = sum(r['contrato_argumentos_fonte_estrita'] for r in rs) / len(rs)
    return out


def diagnostico(rows):
    out = {}
    for ev in EVENTOS_TODOS:
        rs = [r for r in rows if r.get('evento') == ev]
        out[ev] = {
            'n': len(rs), 'erros_contrato': sum(not r['contrato'] for r in rs),
            'escopo_errado': sum(not r['escopo'] for r in rs),
            'argumentos_errados': [sum(not r['argumentos'][i] for r in rs) for i in range(3)],
            'argumentos_fonte_estrita_errados': [sum(not r['argumentos_fonte_estrita'][i] for r in rs) for i in range(3)],
        }
    return out


def validar_antes_de_abrir_painel(lab, autoria, hash_protocolo):
    """Nenhum casos.json é desserializado até todos os guardas passarem."""
    exigir(sha(lab / 'protocolo.json') == hash_protocolo, 'Protocolo principal difere do hash congelado.')
    protocolo = ler(lab / 'protocolo.json')
    codigos = protocolo['codigo']
    exigir(len(codigos) == 5, 'Protocolo deve congelar os cinco arquivos de preparação/treino.')
    for nome, assinatura in codigos.items():
        exigir(Path(nome).name == nome, 'Nome de código deve ser relativo ao diretório do experimento.')
        exigir(sha(Path(__file__).parent / nome) == assinatura, f'Código de treino alterado: {nome}')
    exigir(sha(INICIAL) == protocolo['inicial_sha256'], 'Checkpoint inicial alterado.')
    exigir(sha(ROOT / 'artefatos/linguagem_profunda/pesos.pt') == protocolo['pesos_ativos_sha256'], 'Pesos ativos alterados.')
    for nome, assinatura in protocolo['dados_sha256'].items():
        exigir(sha(lab / protocolo['dados_dir'] / (nome + '.json')) == assinatura,
               f'Dados congelados de treino/validação alterados: {nome}.')
    exigir(sha(autoria / 'protocolo.json') == AUTORIA_PROTOCOLO_SHA256, 'Protocolo prospectivo alterado.')
    exigir(sha(autoria / 'casos.json') == AUTORIA_CASOS_SHA256, 'Painel prospectivo alterado.')
    painel_protocolo = ler(autoria / 'protocolo.json')
    exigir(painel_protocolo['sha256']['casos.json'] == AUTORIA_CASOS_SHA256, 'Hash prospectivo interno diverge.')
    exigir(sha(autoria / 'gerar.py') == painel_protocolo['sha256']['gerar.py'], 'Gerador prospectivo alterado.')
    if 'avaliacao_autoria' in protocolo:
        exigir(protocolo['avaliacao_autoria']['casos_sha256'] == AUTORIA_CASOS_SHA256, 'Treino vinculado a outro painel.')
        exigir(protocolo['avaliacao_autoria']['protocolo_sha256'] == AUTORIA_PROTOCOLO_SHA256, 'Treino vinculado a outro protocolo prospectivo.')
    relatorios = {}
    baseline = torch.load(INICIAL, map_location='cpu', weights_only=True)
    for braco in ('controle', 'fontes'):
        r = ler(lab / braco / 'relatorio.json')
        exigir(r['passos_completos'] == 400, f'Treino {braco} incompleto; não abrir teste.')
        exigir(r['assinatura']['protocolo_sha256'] == hash_protocolo,
               f'Treino {braco} executou com outro protocolo.')
        exigir(r['assinatura']['auxiliar'] == (0. if braco == 'controle' else .3),
               f'Peso auxiliar difere do braço registrado: {braco}.')
        exigir(r['teste_lido_no_treino'] is False and r['pesos_externos'] is False,
               f'Relatório {braco} não preserva os limites experimentais.')
        exigir(sha(lab / braco / 'pesos.pt') == r['pesos_sha256'], f'Pesos {braco} divergem do relatório.')
        candidato = torch.load(lab / braco / 'pesos.pt', map_location='cpu', weights_only=True)
        exigir(candidato['tokenizer_sha256'] == baseline['tokenizer_sha256'], f'Tokenizador incompatível: {braco}.')
        for k, peso in baseline['modelo'].items():
            exigir(k in candidato['modelo'] and torch.equal(peso, candidato['modelo'][k]),
                   f'Parâmetro anterior supostamente congelado foi alterado: {braco}/{k}.')
        relatorios[braco] = {'passos_completos': r['passos_completos'],
                            'passo_escolhido': r['passo_escolhido'],
                            'pesos_sha256': r['pesos_sha256'],
                            'relatorio_sha256': sha(lab / braco / 'relatorio.json')}
    return protocolo, relatorios


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--laboratorio', type=Path, required=True)
    p.add_argument('--autoria', type=Path)
    p.add_argument('--protocolo-sha256', required=True,
                   help='Hash do protocolo principal congelado antes dos treinos; não inferir silenciosamente.')
    a = p.parse_args()
    lab = a.laboratorio
    autoria = a.autoria or lab / 'avaliacao_autoria'
    out = lab / 'avaliacao'
    exigir(not out.exists(), 'Avaliação já existe; preservar traços e não repetir seleção no teste.')
    torch.set_num_threads(1)
    protocolo, relatorios = validar_antes_de_abrir_painel(lab, autoria, a.protocolo_sha256)
    torch.manual_seed(protocolo['seed'])
    base = ROOT / 'artefatos/linguagem_profunda'
    tok = Tokenizer.from_file(str(base / 'tokenizer.json'))
    tok.encode_special_tokens = True
    pad = tok.token_to_id('<pad>')
    exigir(sha(base / 'tokenizer.json') == ler(autoria / 'protocolo.json')['sha256']['tokenizer_proprio'], 'Tokenizador prospectivo alterado.')
    paineis = {
        'prospectivo_autoria': autoria / 'casos.json',
        'retencao_conhecida': RETENCAO / 'dados/teste.json',
        'associacao_conhecida': ASSOC / 'dados/teste.json',
        'contextual_conhecido': CONTEXT / 'dados/teste.json',
    }
    tamanhos = {'prospectivo_autoria': 408, 'retencao_conhecida': 370,
                'associacao_conhecida': 400, 'contextual_conhecido': 400}
    dados = {nome: ler(path) for nome, path in paineis.items()}
    for nome, exemplos in dados.items():
        exigir(len(exemplos) == tamanhos[nome], f'Tamanho inesperado: {nome}. Não omitir exemplos.')
    hashes_paineis = {nome: sha(path) for nome, path in paineis.items()}
    out.mkdir(parents=True, exist_ok=False)
    condicoes = [
        ('anterior_preparo_antigo', INICIAL, codificar_antigo),
        ('anterior_preparo_novo', INICIAL, codificar_novo),
        ('controle', lab / 'controle/pesos.pt', codificar_novo),
        ('fontes', lab / 'fontes/pesos.pt', codificar_novo),
    ]
    resumo, rasgos = {}, {}
    for nome, cp, enc in condicoes:
        # Todas as condições passam por MemoriaFontes. No checkpoint anterior,
        # delta_escopo/consultas_validade são zero: logits relevantes preservados.
        torch.manual_seed(protocolo['seed'])
        m, metadata = carregar(tok, path=cp)
        exigir(metadata['tokenizer_sha256'] == sha(base / 'tokenizer.json'), f'Tokenizador incompatível: {nome}.')
        resumo[nome] = {}
        for painel, exemplos in dados.items():
            # A codificação recebe somente turnos e placeholders nulos. O gold
            # é anexado depois para conferir as propostas, nunca codificado.
            items = []
            for e in exemplos:
                item = enc(tok, {'turnos': e['turnos'], 'argumentos': [None] * 3, 'referente': None})
                item['exemplo'] = e
                items.append(item)
            raw, lim = coletar(m, items, pad)
            for tipo, rows in (('bruto', raw), ('limitado', lim)):
                enriquecer(rows, exemplos)
                escrever(out / f'{nome}_{painel}_{tipo}.json', rows)
                resumo[nome][painel + '_' + tipo] = medir(rows)
                if nome.startswith('anterior_'):
                    resumo[nome][painel + '_' + tipo]['evento_turno_sem_treino'] = True
            if painel == 'prospectivo_autoria':
                rasgos[nome] = diagnostico(lim)
            print(json.dumps({'condicao': nome, 'painel': painel, 'n': len(lim),
                              'contratos': sum(r['contrato'] for r in lim),
                              'sessoes_completas': resumo[nome][painel + '_limitado']['sessoes_completas']},
                             ensure_ascii=False), flush=True)
    anterior = resumo['anterior_preparo_novo']
    criterios = {}
    for nome in ('controle', 'fontes'):
        r = resumo[nome]['prospectivo_autoria_limitado']
        b = anterior['prospectivo_autoria_limitado']
        eventos = {ev: r['por_evento'][ev]['acuracia_contrato'] for ev in EVENTOS_CRITICOS}
        familias = {f: v['acuracia'] for f, v in r['por_familia'].items()}
        exigir(set(familias) == {'precos', 'requisitos'}, 'Famílias prospectivas inesperadas.')
        aumento = r['fracao_sessoes_completas'] - b['fracao_sessoes_completas']
        quedas = {painel: anterior[painel + '_limitado']['acuracia_contrato'] -
                  resumo[nome][painel + '_limitado']['acuracia_contrato'] for painel in PAINEIS_CONHECIDOS}
        eventos_ok = all(v >= .80 for v in eventos.values())
        familias_ok = all(v >= .80 for v in familias.values())
        criterios[nome] = {
            'acuracias_eventos_criticos': eventos, 'acuracias_familias': familias,
            'eventos_criticos_80pct': eventos_ok, 'familias_80pct': familias_ok,
            'aumento_sessoes_completas_pp': 100 * aumento,
            'quedas_paineis_conhecidos_pp': {k: 100 * v for k, v in quedas.items()},
            'queda_maxima_paineis_conhecidos_pp': 100 * max(quedas.values()),
            'passou_criterio_sintetico': eventos_ok and familias_ok and aumento >= .20 and max(quedas.values()) <= .05,
            'aprovado_para_chat': False,
        }
    exigir(sha(ROOT / 'artefatos/linguagem_profunda/pesos.pt') == protocolo['pesos_ativos_sha256'], 'Pesos ativos alterados durante avaliação.')
    escrever(out / 'resumo.json', {
        'resultados': resumo, 'criterios': criterios, 'diagnostico_prospectivo': rasgos,
        'treinos_concluidos': relatorios, 'sha256_paineis': hashes_paineis,
        'protocolo_sha256': a.protocolo_sha256, 'avaliador_sha256': sha(__file__),
        'protocolo_autoria_sha256': AUTORIA_PROTOCOLO_SHA256,
        'baseline_criterio': 'anterior_preparo_novo; todos os critérios usam decodificação limitada',
        'descricao_contrato': 'Operação, argumentos literais com turno correto, referente literal e escopo. '
                              'Fonte exata turno/início/fim/literal também registrada separadamente.',
        'limites': [
            'Uma semente. O painel prospectivo foi escrito por outro agente da mesma equipe usando a '
            'mesma gramática fechada, não por avaliador externo independente.',
            '80 sessões e 408 prefixos são correlacionados. Preços inteiros, nomes de uma palavra e '
            'requisitos de dois itens; não avalia diálogo livre ou raciocínio geral.',
            'Os outros três painéis são conhecidos de experimentos anteriores e servem somente à regressão.',
            'Arquitetura e pesos próprios. Corpo/cabeças anteriores congelados; adaptações de escopo/fontes '
            'nos dois braços. Diferença entre braços é supervisão auxiliar de validade 0/.3.',
            'O evento é previsto pela cabeça auxiliar, não alimentado ao fusor. Banco/evento/trajetória/gold '
            'não entram no NN; entradas são IDs e comprimentos obtidos dos turnos.',
            'Nos dois baselines anteriores, a nova cabeça de evento_turno está inicializada sem treino. '
            'Sua acurácia de evento é mero diagnóstico dessa inicialização; logits de operação, escopo '
            'e ponteiros preservam o checkpoint anterior.',
            'Resultados limitados combinam transformer, enumerador de trechos da gramática e executor '
            'determinístico. Não atribuir todos os acertos à rede.',
            'Não há treino causal de redação nesta rodada, ativação automática ou aprovação de chat.',
        ],
        'aprovado_para_chat': False, 'avaliacao_de_redacao_livre': False,
        'pesos_externos': False,
    })


if __name__ == '__main__':
    main()
