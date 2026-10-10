"""Continuação textual contrastiva, escolhida apenas no desenvolvimento.

Não lê as respostas da avaliação congelada durante treino/seleção.
Não acrescenta regras, slots ou consulta ao corpus na inferência.
"""
import argparse
import gzip
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from executar import RAIZ, gravar, sha
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar
from treinar_dialogo_seq2seq import treinar
from preparar_contrastes import h


def preparar():
    destino = DIR / 'protocolo_contrastes.json'
    if destino.exists():
        raise ValueError('Preservar protocolo existente')
    exemplos = []
    for j in range(4):
        nome, outro = f'Návea-{47+j}', f'Zorém-{63+j}'
        casos = [
            ('nome_corrigido', h(f'Meu amigo se chama {nome}.', 'Certo.',
                f'O nome correto é {outro}, e não {nome}.', 'Obrigado por corrigir.'),
                'Qual é o nome desse meu amigo?', f'Seu amigo se chama {outro}.'),
            ('autoria', h(f'Meu nome é {nome}.', 'Entendi.',
                f'Meu amigo é {outro}.', 'Certo.'), 'Você lembra como me chamo?', f'Você se chama {nome}.'),
            ('preferencia', h('Minha preferência era azul.', 'Entendi.',
                'Agora quero ler em casa, não azul.', 'Certo.'),
                'Qual ficou sendo minha preferência?', 'Sua preferência agora é ler em casa.'),
            ('prazo', h(f'Vou encontrar {nome} no domingo.', 'Certo.',
                'O encontro ficou para terça, e não domingo.', 'Entendi.'),
                'Quando ficou o encontro?', f'O encontro com {nome} é no terça.'),
            ('fato_ausente', h(f'Meu amigo é {nome}.', 'Entendi.'),
                'Você lembra como me chamo?', 'Não tenho essa informação. Você pode me dizer?'),
            ('autoria_assistente', [{'papel':'assistente', 'texto':f'Eu sou {nome}.'}],
                'Você lembra como me chamo?', 'Não tenho essa informação. Você pode me dizer?'),
            ('hipotese', h('Eu moro sozinho.', 'Entendi.',
                f'Se eu morasse com {nome}, como dividir as tarefas?', 'Vocês poderiam combinar.'),
                'Como é minha moradia atualmente?', 'Atualmente você mora sozinho.'),
            ('retomada', h(f'{nome} ficou preso na estação.', 'A história parou nesse problema.',
                'Quero organizar minha mesa.', 'Comece por uma parte pequena.',
                'Terminei. Vamos voltar ao conto?', 'Vamos.'),
                'Retome a história de onde parou.',
                f'Podemos. {nome} ainda estava na estação, tentando encontrar uma saída.'),
        ]
        for categoria, historico, mensagem, resposta in casos:
            exemplos.append(dict(id=f'{categoria}-{j}', categoria=categoria,
                historico=historico, mensagem=mensagem, resposta=resposta))
    gravar('desenvolvimento_contrastes.json', {'exemplos':exemplos,
        'limite':'Sondas autorais de desenvolvimento para seleção; não avaliação independente nem holdout final.'})
    estat = ler_json(DIR / 'corpus_contrastes_estatisticas.json')
    gravar(destino.name, dict(preparado_em_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint_inicial='checkpoint_rodada3.json.gz',
        checkpoint_inicial_sha256=sha(DIR / 'checkpoint_rodada3.json.gz'),
        corpus='corpus_contrastes.json.gz', corpus_sha256=estat['sha256_corpus'],
        desenvolvimento_sha256=sha(DIR / 'desenvolvimento_contrastes.json'),
        avaliacao_final_sha256=sha(DIR / 'avaliacao_rodada3_congelada.json'),
        hiperparametros=dict(epocas=12, lote_tamanho=32, ocultos=24, embeddings=16,
            vocab_max=720, buckets=128, limite_fonte=192, limite_resposta=64,
            semente=173, taxa=.0006, validar_cada=2, paciencia=6,
            dropout=.10, dropout_tokens=.05, amostragem=.10, aquecimento=3),
        selecao='Antes de abrir a avaliação final: melhoria literal em sondas contrastivas e entropia de desenvolvimento não mais de 10% pior; se não, conservar rodada 3.',
        limite='Continuação supervisionada própria com novo Adam; não retomada exata. Sem nova capacidade de arquitetura ou regra no chat.',
        aprovado=False, ativo_no_chat=False))


def protocolo():
    p = ler_json(DIR / 'protocolo_contrastes.json')
    for nome, chave in [(p['checkpoint_inicial'], 'checkpoint_inicial_sha256'),
        (p['corpus'], 'corpus_sha256'), ('desenvolvimento_contrastes.json', 'desenvolvimento_sha256'),
        ('avaliacao_rodada3_congelada.json', 'avaliacao_final_sha256')]:
        if sha(DIR / nome) != p[chave]:
            raise ValueError(f'Artefato alterado: {nome}')
    return p


def desenvolver(path):
    modelo = DialogoSeq2Seq(ler_json(path))
    saidas = []
    for e in ler_json(DIR / 'desenvolvimento_contrastes.json')['exemplos']:
        r = modelo.gerar(e['mensagem'], e['historico'], max_tokens=64, feixe=1)
        igual = [t.casefold() for t in r['tokens']] == [t.casefold() for t in tokenizar(e['resposta'])]
        saidas.append(dict(**e, gerada=r['texto'], igual_ao_alvo=igual))
    return dict(checkpoint_sha256=sha(path), exemplos=len(saidas),
        iguais_ao_alvo=sum(s['igual_ao_alvo'] for s in saidas), saidas=saidas,
        limite='Desenvolvimento conhecido; igualdade literal não é medida de conversa natural.')


def treino():
    p = protocolo()
    destino = DIR / 'checkpoint_contrastes.json.gz'
    if destino.exists():
        raise ValueError('Preservar checkpoint existente')
    gravar('contrastes_desenvolvimento_antes.json', desenvolver(DIR / p['checkpoint_inicial']))
    temporario = DIR / 'checkpoint_contrastes.tmp.json'
    r = treinar(DIR / p['corpus'], temporario, checkpoint_inicial=DIR / p['checkpoint_inicial'],
        **p['hiperparametros'])
    dados = ler_json(temporario)
    dados.update(aprovado=False, ativo_no_chat=False, experimento='gerador-historico-textual-contrastes',
        sha256_corpus=p['corpus_sha256'], sha256_avaliacao_reservada=p['avaliacao_final_sha256'])
    if dados['treino']['parametros'] != 81433:
        raise ValueError('Orçamento de parâmetros alterado')
    destino.write_bytes(gzip.compress((json.dumps(dados, ensure_ascii=False, separators=(',',':'))+'\n').encode(), mtime=0))
    temporario.unlink()
    r['manifesto'] = dict(checkpoint_sha256=sha(destino),
        checkpoint_inicial_sha256=p['checkpoint_inicial_sha256'], corpus_sha256=p['corpus_sha256'],
        protocolo_sha256=sha(DIR / 'protocolo_contrastes.json'),
        desenvolvimento_sha256=p['desenvolvimento_sha256'], avaliacao_final_sha256=p['avaliacao_final_sha256'],
        script_sha256=sha(__file__), treinador_sha256=sha(RAIZ / 'treinar_dialogo_seq2seq.py'),
        arquitetura_sha256=sha(RAIZ / 'dialogo_seq2seq.py'), numpy=__import__('numpy').__version__,
        threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
        aprovado=False, ativo_no_chat=False)
    gravar('treino_contrastes.json', r)
    depois = desenvolver(destino)
    gravar('contrastes_desenvolvimento_depois.json', depois)
    antes = ler_json(DIR / 'contrastes_desenvolvimento_antes.json')
    referencia = ler_json(DIR / 'treino_rodada3.json')['validacao']['entropia_cruzada']
    escolher = (depois['iguais_ao_alvo'] > antes['iguais_ao_alvo'] and
        r['validacao']['entropia_cruzada'] <= referencia * 1.10)
    gravar('selecao_antes_holdout.json', dict(selecionado_em_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint=destino.name if escolher else p['checkpoint_inicial'],
        checkpoint_sha256=sha(destino if escolher else DIR / p['checkpoint_inicial']),
        criterio=p['selecao'], contrastes_antes=antes['iguais_ao_alvo'],
        contrastes_depois=depois['iguais_ao_alvo'], desenvolvimento_total=depois['exemplos'],
        entropia_antes=referencia, entropia_depois=r['validacao']['entropia_cruzada'],
        avaliacao_final_ainda_nao_executada=True, aprovado=False, ativo_no_chat=False))
    print(json.dumps(ler_json(DIR / 'selecao_antes_holdout.json'), ensure_ascii=False), flush=True)


def avaliar():
    from rodada3 import avaliar_checkpoint
    from executar import avaliar as regressao
    p = protocolo()
    selecao = ler_json(DIR / 'selecao_antes_holdout.json')
    path = DIR / selecao['checkpoint']
    if sha(path) != selecao['checkpoint_sha256']:
        raise ValueError('Seleção alterada')
    if (DIR / 'final_depois_com_historico.json').exists():
        raise ValueError('Preservar avaliação final existente')
    resumo = {}
    for modo in ['com_historico', 'sem_historico', 'ordem_inversa']:
        r = avaliar_checkpoint(path, modo)
        gravar('final_depois_'+modo+'.json', r)
        resumo[modo] = {k:r[k] for k in ['sessoes_triagem','turnos_triagem','turnos_com_proibidos','fontes_truncadas']}
    conhecido = regressao(DialogoSeq2Seq(ler_json(path)))
    conhecido['limite_adicional'] = 'Regressão já conhecida, inclusive pergunta do dono; não entra no holdout final novo.'
    gravar('final_regressao_conhecida.json', conhecido)
    gravar('final_resumo_automatico.json', resumo)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('etapa', choices=['preparar','treinar','avaliar'])
    {'preparar':preparar, 'treinar':treino, 'avaliar':avaliar}[ap.parse_args().etapa]()
