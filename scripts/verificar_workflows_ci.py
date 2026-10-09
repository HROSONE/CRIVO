"""Confere a política do CI sem carregar pesos ou iniciar treinos."""
from pathlib import Path
import fnmatch
import json
import os
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'


def acionados(arquivos):
    nomes = []
    for p in sorted(WORKFLOWS.glob('*.yml')):
        w = yaml.load(p.read_text(), Loader=yaml.BaseLoader)
        eventos = w.get('on', {})
        if 'pull_request' not in eventos:
            continue
        filtros = eventos['pull_request'] or {}
        padroes = filtros.get('paths')
        if padroes is None or any(fnmatch.fnmatchcase(a, pat) for a in arquivos for pat in padroes):
            nomes.append(p.name)
    return nomes


GERACAO = (
    'linguagem_gerativa.py', 'geracao_conversa.py', 'intencao_gerativa.py',
    'rede_sequencial.py', 'rede_neural.py', 'compreensao_neural.py',
    '*seq2seq*.py', '*geracao*.json', '*gerativa*.json',
    'treinar_geracao.py', 'treinar_intencao_gerativa.py',
    'preparar_dialogos_geracao.py', 'dialogos_geracao.json',
    'dialogos_intencao_gerativa.json', 'dialogos_compreensao.json',
    'dados/dialogos_geracao*', 'dados/intencao_gerativa*', 'artefatos/geracao_pt/**',
    'testes_geracao.py', 'testes_intencao_gerativa.py', 'testes_compreensao.py',
    'testes_seq2seq.py', 'testes_treino_numpy.py', 'requirements.txt',
)
PROFUNDA = (
    'scripts/*linguagem*.py', 'scripts/*transformer*.py',
    'scripts/*conversa_gerativa*.py', 'scripts/*compreensao_contrastiva*.py',
    'scripts/gerador_frases.py', 'scripts/*codigo_real.py',
    'scripts/*logica_programacao*.py', 'scripts/selecao_programacao.py',
    'scripts/*dialogo_integro*.py', 'scripts/*backup*drive*.py',
    'artefatos/linguagem_profunda/**', 'artefatos/conversa_gerativa/**',
    'artefatos/leitor_transformer/**', 'artefatos/dialogo_integro/**',
    'scripts/curriculo_dialogos_amplos.py', 'scripts/preparar_dialogo_integro.py',
    'scripts/avaliar_dialogo_integro.py', 'scripts/gerar_logica_programacao.py',
    'dados/linguagem/**', 'dados/conversa_gerativa/**', 'dados/programacao/**',
    'testes_linguagem_profunda.py', 'testes_backup_treino_drive.py',
    'testes_dialogo_integro.py', 'testes_compreensao_contrastiva.py',
    'testes_transformer_16m.py', 'testes_conversa_gerativa.py',
    'testes_dialogos_amplos.py', 'testes_gerador_frases.py',
    'testes_codigo_real.py', 'testes_logica_programacao.py', 'requirements.txt',
)


def selecionar(arquivos):
    return {nome: any(fnmatch.fnmatchcase(a, pat) for a in arquivos for pat in padroes)
            for nome, padroes in [('geracao', GERACAO), ('profunda', PROFUNDA)]}


def publicar_escopo():
    caminho = os.environ.get('GITHUB_OUTPUT')
    if not caminho:
        return
    # Fora de PRs, dispatch/schedule têm condições próprias nos jobs.
    # Nunca selecionar uma bateria neural somente porque houve push na main.
    selecao = {'geracao': False, 'profunda': False}
    if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
        evento = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        pr = evento['pull_request']
        arquivos = subprocess.check_output([
            'git', 'diff', '--name-only', '-z',
            pr['base']['sha'] + '...' + pr['head']['sha'],
        ], cwd=ROOT).decode().split('\0')
        selecao = selecionar(arquivos)
    with open(caminho, 'a') as saida:
        for nome, ativo in selecao.items():
            saida.write(nome + '=' + str(ativo).lower() + '\n')
    print('Escopo dos contratos neurais:', selecao)


def main():
    w = yaml.load((WORKFLOWS / 'testes.yml').read_text(), Loader=yaml.BaseLoader)
    assert w['on']['pull_request'] in ('', None), 'O workflow principal precisa reportar status em todos os PRs'
    assert 'schedule' in w['on'] and 'workflow_dispatch' in w['on']
    jobs = w['jobs']
    for nome in ('roteamento-natural', 'compreensao-chat'):
        assert "github.event_name == 'pull_request'" in jobs[nome]['if'], nome
    assert jobs['testes']['if'] == "github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'"
    for nome, escopo in [('matematica-geracao', 'geracao'), ('matematica-linguagem-profunda', 'profunda')]:
        assert jobs[nome]['needs'] == 'configuracao-ci'
        esperado = ("github.event_name == 'workflow_dispatch' || github.event_name == 'schedule' || "
                    + "(github.event_name == 'pull_request' && needs.configuracao-ci.outputs."
                    + escopo + " == 'true')")
        assert jobs[nome]['if'] == esperado, nome
    matrix = jobs['testes']['strategy']['matrix']
    assert matrix['python-version'] == ['3.8', '3.11', '3.13']
    assert matrix['grupo'] == ['composicao', 'treino', 'regressoes-a', 'regressoes-b']
    assert acionados(['crivo.py', 'web_core.py']) == ['dialogo-situado.yml', 'testes.yml']
    assert acionados(['.github/workflows/biblia-tnm.yml', '.github/workflows/testes.yml', 'scripts/verificar_workflows_ci.py']) == ['testes.yml']
    assert 'biblia-tnm.yml' in acionados(['conhecimento_biblia.json'])
    assert 'motor-programacao-chat.yml' in acionados(['programacao_chat.py'])
    assert 'dialogo-situado.yml' in acionados(['memoria_sessao.py', 'compreensao_intencao.py'])
    assert 'tts-offline.yml' in acionados(['public/tts/index.js'])
    assert 'laboratorio-projetos.yml' in acionados(['laboratorio_projetos.py'])
    assert selecionar(['crivo.py', 'memoria_sessao.py']) == {'geracao': False, 'profunda': False}
    assert selecionar(['linguagem_gerativa.py']) == {'geracao': True, 'profunda': False}
    assert selecionar(['scripts/treinar_linguagem_profunda.py']) == {'geracao': False, 'profunda': True}
    assert selecionar(['requirements.txt']) == {'geracao': True, 'profunda': True}
    publicar_escopo()
    print('Política de CI válida: núcleo → 2 workflows; CI isolado → 1; baterias completas preservadas.')


if __name__ == '__main__':
    main()
