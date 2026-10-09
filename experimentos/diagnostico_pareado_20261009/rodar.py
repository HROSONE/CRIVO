"""Diagnóstico pareado: entradas reais, respostas brutas e contexto visível."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

PASTA = Path(__file__).resolve().parent
CONDICOES = ('reunido', 'multiturno', 'recapitulacao', 'estado_assistido')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pedido(caso, condicao):
    if condicao in ('reunido', 'recapitulacao'):
        return '\n'.join(caso['falas'] + [caso['pedido']])
    if condicao == 'estado_assistido':
        return '\n'.join(caso['estado'] + [caso['pedido']])
    return caso['pedido']


def salvar(r, p):
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raiz', type=Path, required=True)
    ap.add_argument('--modo', choices=('motor', 'gerador'), required=True)
    ap.add_argument('--modelo', type=Path)
    ap.add_argument('--saida', type=Path, required=True)
    ap.add_argument('--tokens', type=int, default=80)
    ap.add_argument('--threads', type=int, default=1)
    ap.add_argument('--max-segundos', type=int, default=1800)
    a = ap.parse_args()
    if a.saida.exists():
        raise SystemExit('Use uma saída nova para preservar resultados.')
    sys.path.insert(0, str(a.raiz.resolve()))
    protocolo = json.loads((PASTA / 'protocolo.json').read_text())
    assert sha(PASTA / 'casos.json') == protocolo['casos_sha256']
    dados = json.loads((PASTA / 'casos.json').read_text())
    inicio = time.monotonic()
    r = {'modo': a.modo, 'protocolo': protocolo, 'limite': dados['limite'],
         'rodar_sha256': sha(__file__), 'entradas': [], 'concluido': False}
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    if a.modo == 'gerador':
        import torch
        torch.set_num_threads(a.threads)
        from linguagem_profunda import carregar, fonte_dialogo, segmentos_dialogo, ESPECIAIS
        modelo, tokenizer, estado = carregar(a.modelo)
        r['modelo'] = {'parametros': sum(p.numel() for p in modelo.parameters()),
                       'config': estado['config'], 'passo': estado['passo'],
                       'pesos_sha256': sha(a.modelo / 'pesos.pt'),
                       'tokenizer_sha256': sha(a.modelo / 'tokenizer.json')}

        def responder(texto, hist, bot):
            segmentos, atual = segmentos_dialogo(tokenizer, texto, hist)
            todos = sum(segmentos, []) + atual
            fonte = fonte_dialogo(tokenizer, texto, hist, modelo.config.contexto)
            retidos = []
            tamanho = len(atual)
            for i in range(len(segmentos) - 1, -1, -1):
                if tamanho + len(segmentos[i]) > modelo.config.contexto:
                    break
                retidos.insert(0, i)
                tamanho += len(segmentos[i])
            ini = time.monotonic()
            ids, terminou = modelo.gerar(fonte, tokenizer.token_to_id('<fim>'),
                max_tokens=a.tokens, temperatura=0., semente=20261009,
                proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
            return {'resposta': tokenizer.decode(ids), 'mecanismo': 'geracao_causal_direta',
                    'segundos': round(time.monotonic() - ini, 4), 'terminou': terminou,
                    'tokens_saida': len(ids), 'tokens_entrada': len(fonte),
                    'tokens_sem_limite': len(todos), 'historico_retido': retidos,
                    'historico_omitido': [i for i in range(len(hist)) if i not in retidos],
                    'entrada_real': tokenizer.decode(fonte, skip_special_tokens=False),
                    'tokens_entrada_ids': fonte}
    else:
        from crivo import Crivo
        from ecossistema import mecanismo_do_turno

        def responder(texto, hist, bot):
            ini = time.monotonic()
            ident, resposta = bot.responder(texto)
            return {'resposta': resposta, 'ident': ident,
                    'mecanismo': mecanismo_do_turno(bot, texto, ident),
                    'segundos': round(time.monotonic() - ini, 4),
                    'entrada_real': texto, 'relatos': list(bot.conversacao.relatos),
                    'quadro_situado': bot.dialogo_situado.quadro(bot.conversacao),
                    'raciocinio': bot.raciocinio_conversa.ultimo}

    for caso in dados['casos']:
        for condicao in CONDICOES:
            if time.monotonic() - inicio > a.max_segundos:
                r['pausa'] = 'Orçamento de tempo atingido.'
                salvar(r, a.saida)
                raise SystemExit(2)
            bot = Crivo() if a.modo == 'motor' else None
            hist = []
            row = {'caso': caso['id'], 'familia': caso['familia'], 'condicao': condicao,
                   'turnos': [], 'rubrica_passada_ao_modelo': False}
            textos = caso['falas'] + [pedido(caso, condicao)] if condicao in (
                'multiturno', 'recapitulacao') else [pedido(caso, condicao)]
            for texto in textos:
                t = {'texto_usuario': texto, 'historico_enviado': list(hist)}
                try:
                    t.update(responder(texto, hist, bot))
                except Exception as e:
                    t.update(erro=type(e).__name__, mensagem=str(e))
                row['turnos'].append(t)
                hist.append({'papel': 'usuario', 'texto': texto})
                if 'resposta' in t:
                    hist.append({'papel': 'assistente', 'texto': t['resposta']})
            r['entradas'].append(row)
            r['segundos'] = round(time.monotonic() - inicio, 3)
            salvar(r, a.saida)
            print(caso['id'], condicao, 'erro' if 'erro' in row['turnos'][-1] else 'coletado', flush=True)
    r['concluido'] = True
    salvar(r, a.saida)


if __name__ == '__main__':
    main()
