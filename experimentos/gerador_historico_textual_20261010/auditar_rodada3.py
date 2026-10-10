"""Auditoria de isolamento/proveniência, sem aprovação de qualidade."""
import json
import subprocess
from executar import DIR, RAIZ, sha, gravar
from arquivos_contextuais import ler_json


def auditar():
    base = 'b0bdb05569a3b3c89380e9ffd84493cd1427cd6b'
    antigo = ler_json(DIR / 'auditoria.json')
    pesos = {nome:sha(RAIZ / nome) for nome in antigo['pesos_raiz_preservados']}
    if pesos != antigo['pesos_raiz_preservados']:
        raise ValueError('Peso de produção alterado')
    arquivos = ['dialogo_seq2seq.py','linguagem_gerativa.py','conversa_dialogo.py',
        'web_core.py','crivo.py','vercel.json','.github/workflows/testes.yml']
    preservados = {}
    for nome in arquivos:
        original = subprocess.check_output(['git','show',base+':'+nome],cwd=RAIZ)
        preservados[nome] = (RAIZ / nome).read_bytes() == original
    if not all(preservados.values()):
        raise ValueError('Arquitetura/runtime/publicação/CI alterados')
    manifestos = {}
    for nome in ['treino_rodada3.json','treino_contrastes.json']:
        treino = ler_json(DIR / nome)
        m = treino['manifesto']
        for arquivo,chave in [('treinar_dialogo_seq2seq.py','treinador_sha256'),
            ('dialogo_seq2seq.py','arquitetura_sha256')]:
            if sha(RAIZ / arquivo) != m[chave]:
                raise ValueError('Código não corresponde ao treino')
        checkpoint = 'checkpoint_rodada3.json.gz' if nome == 'treino_rodada3.json' else 'checkpoint_contrastes.json.gz'
        c = ler_json(DIR / checkpoint)
        if c['aprovado'] is not False or c['ativo_no_chat'] is not False or sha(DIR / checkpoint) != m['checkpoint_sha256']:
            raise ValueError('Checkpoint alterado ou indevidamente aprovado')
        manifestos[nome] = dict(checkpoint_sha256=m['checkpoint_sha256'],
            parametros=c['treino']['parametros'], vocabulario=len(c['vocabulario']),
            origem_sha256=m['checkpoint_inicial_sha256'], aprovado=False, ativo_no_chat=False)
    gravar('auditoria_rodada3.json', dict(base_commit=base, pesos_raiz_preservados=pesos,
        quantidade_pesos_auditados=len(pesos), arquivos_preservados=preservados,
        treinador_alterado='Somente inicialização opcional pelos próprios pesos e preservação dos IDs; Adam reiniciado. Matemática de BPTT, arquitetura e inferência intactas.',
        manifestos=manifestos, avaliacao_nova_sha256=sha(DIR / 'avaliacao_rodada3_congelada.json'),
        selecao_antes_avaliacao=ler_json(DIR / 'selecao_antes_holdout.json'),
        validacao_local=dict(matematica_seq2seq='21 testes passaram.',
            matematica_inferencia_escopo=ler_json(DIR / 'divida_ci_rodada3.json'),
            integridade_dados_isolamento='10 testes passaram; não certifica conversa.'),
        limite='Auditoria verifica os oito pesos listados e arquivos críticos; não declara auditoria de todos os modelos existentes. Nenhum checkpoint deste experimento entrou no chat.'))
    print(json.dumps({'pesos_preservados':len(pesos),'arquivos_preservados':len(arquivos),'checkpoints_isolados':len(manifestos)}))


if __name__ == '__main__':
    auditar()
