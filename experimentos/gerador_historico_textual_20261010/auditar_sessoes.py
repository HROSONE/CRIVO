"""Confere artefatos da última rodada sem treinar ou aprovar pesos."""
import subprocess
from collections import Counter

from executar import DIR, RAIZ, gravar, sha
from arquivos_contextuais import ler_json


def auditar():
    corpus = ler_json(DIR / 'corpus_sessoes.json.gz')['exemplos']
    validacao = [e for e in corpus if e['split'] == 'validacao']
    desenvolvimento = {}
    for nome in ['sessoes_desenvolvimento_antes_pesos_anteriores.json',
                 'sessoes_desenvolvimento_antes_inicializacao_realocada.json',
                 'treino_sessoes.json', 'treino_sessoes_refinado.json']:
        dados = ler_json(DIR / nome)
        geracao = dados.get('geracao_desenvolvimento', dados)
        grupos = {'antigo': dict(total=0, iguais_ao_alvo=0),
                  'sessoes_novas': dict(total=0, iguais_ao_alvo=0)}
        assert len(geracao['saidas']) == len(validacao) == 428
        for saida in geracao['saidas']:
            exemplo = validacao[saida['indice']]
            assert exemplo['mensagem'] == saida['mensagem']
            assert exemplo['resposta'] == saida['alvo']
            grupo = 'sessoes_novas' if exemplo['grupo'] == 'sessao_completa' else 'antigo'
            grupos[grupo]['total'] += 1
            grupos[grupo]['iguais_ao_alvo'] += int(saida['igual_ao_alvo'])
        desenvolvimento[nome] = grupos
    gravar('desenvolvimento_sessoes_por_origem.json', desenvolvimento)

    anterior = ler_json(DIR / 'auditoria.json')['pesos_raiz_preservados']
    pesos = {nome: sha(RAIZ / nome) for nome in anterior}
    assert pesos == anterior
    base = '4ba33991429f2a6089a728d1ee8d68428fee0a48'
    arquivos = ['dialogo_seq2seq.py', 'treinar_dialogo_seq2seq.py',
                'linguagem_gerativa.py', 'conversa_dialogo.py', 'web_core.py',
                'crivo.py', 'vercel.json', '.github/workflows/testes.yml']
    preservados = {nome: (RAIZ / nome).read_bytes() == subprocess.check_output(
        ['git', 'show', base + ':' + nome], cwd=RAIZ) for nome in arquivos}
    assert all(preservados.values())
    checkpoints = {}
    for relatorio, checkpoint, script, commit in [
        ('treino_sessoes.json', 'checkpoint_sessoes.json.gz', 'sessoes.py', '54259df'),
        ('treino_sessoes_refinado.json', 'checkpoint_sessoes_refinado.json.gz',
         'refinar_sessoes.py', 'cea54c7')]:
        dados = ler_json(DIR / relatorio)
        manifesto = dados['manifesto']
        rede = ler_json(DIR / checkpoint)
        assert sha(DIR / checkpoint) == manifesto['checkpoint_sha256']
        assert sha(DIR / 'corpus_sessoes.json.gz') == manifesto['corpus_sha256']
        assert sha(DIR / 'avaliacao_sessoes_congelada.json') == manifesto['avaliacao_sha256']
        assert sha(RAIZ / 'dialogo_seq2seq.py') == manifesto['arquitetura_sha256']
        assert sha(RAIZ / 'treinar_dialogo_seq2seq.py') == manifesto['treinador_sha256']
        import hashlib
        script_original = subprocess.check_output(
            ['git', 'show', commit + ':experimentos/gerador_historico_textual_20261010/' + script], cwd=RAIZ)
        assert hashlib.sha256(script_original).hexdigest() == manifesto['script_sha256']
        assert rede['aprovado'] is False and rede['ativo_no_chat'] is False
        assert rede['treino']['parametros'] == 81433 and len(rede['vocabulario']) == 720
        checkpoints[checkpoint] = dict(sha256=sha(DIR / checkpoint),
            epocas=rede['treino']['epocas'], epoca_selecionada=rede['treino']['epoca_selecionada'],
            segundos=rede['treino']['segundos'], aprovado=False, ativo_no_chat=False)
    selecao = ler_json(DIR / 'selecao_final_sessoes_antes_holdout.json')
    assert selecao['checkpoint_sha256'] == sha(DIR / selecao['checkpoint'])
    resultado = ler_json(DIR / 'sessoes_depois_com_historico.json')
    assert resultado['checkpoint_sha256'] == selecao['checkpoint_sha256']
    gravar('auditoria_sessoes.json', dict(base_ultima_rodada=base,
        pesos_raiz_preservados=pesos, quantidade_pesos_auditados=len(pesos),
        arquivos_preservados_nesta_rodada=preservados, checkpoints=checkpoints,
        corpus_sha256=sha(DIR / 'corpus_sessoes.json.gz'),
        grupos_corpus={str(k): v for k, v in Counter((e['split'], e['grupo']) for e in corpus).items()},
        avaliacao_sha256=sha(DIR / 'avaliacao_sessoes_congelada.json'),
        selecao_antes_avaliacao=selecao,
        aprovado=False, ativo_no_chat=False,
        limite='Audita oito pesos listados e arquivos críticos; não mede naturalidade nem autoriza promoção. Script de cada treino conferido no commit anterior correspondente.'))
    print({'pesos_preservados': len(pesos), 'arquivos_preservados': len(preservados),
           'checkpoints_isolados': len(checkpoints), 'desenvolvimento': desenvolvimento})


if __name__ == '__main__':
    auditar()
