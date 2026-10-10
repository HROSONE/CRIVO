"""Manifesto verificável; versões anteriores permanecem intactas/arquivadas."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent; ROOT = H.parent.parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    aprovacao = json.loads((H / 'aprovacao.json').read_text())
    assert sha(ROOT / 'rede_dialogo_conversa.json.gz') == aprovacao['checkpoint_producao_sha256']
    anterior = json.loads((H.parent / 'contexto_pratico_20261010/manifesto.json').read_text())
    preservados = dict(anterior['pesos_preservados_sha256'])
    base = preservados.pop('rede_dialogo_conversa.json.gz')
    preservados['experimentos/diversidade_dialogo_20261010/checkpoint_base_133.json.gz'] = base
    for nome, digest in preservados.items():
        assert sha(ROOT / nome) == digest, nome
    experimentos = {}
    for nome in ('escrita_acontecimentos_20261010', 'contexto_pratico_20261010'):
        for p in sorted((H.parent / nome).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                experimentos[str(p.relative_to(ROOT))] = sha(p)
    m = dict(base_commit='0f46877e6d19011fb259c93a4b43f18147e127d7',
             checkpoint_original_isolado_sha256=sha(H / 'checkpoint_gru_dialogo.json.gz'),
             checkpoint_producao_sha256=sha(ROOT / 'rede_dialogo_conversa.json.gz'),
             checkpoint_anterior_arquivado_sha256=base,
             parametros=85130, vocabulario=321,
             arquivos_sha256={p.name: sha(p) for p in sorted(H.iterdir()) if p.is_file() and p.name != 'manifesto.json'},
             pesos_preservados_sha256=preservados, experimentos_preservados_sha256=experimentos,
             runtime_sha256={f: sha(ROOT / f) for f in ('conversa_dialogo.py', 'orientacao_pratica.py',
                                'dialogo_situado.py', 'testes_diversidade_dialogo.py',
                                'testes_contexto_pratico.py', '.github/workflows/escrita-acontecimentos.yml')},
             limite='Avaliações autorais do agente e padrões conhecidos. Não valida conversa humana, planejamento ou generalização de assunto.')
    (H / 'manifesto.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n')
    print('Pesos preservados/arquivados:', len(preservados), 'evidências anteriores:', len(experimentos))


if __name__ == '__main__':
    main()
