"""Supervisão textual de escopo/correção; nada é aplicado na inferência.

Preparar usando só exemplos de desenvolvimento/treino e antes de abrir
a avaliação nova. Não lê o holdout para compor mensagem ou resposta.
"""
import gzip
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from preparar_corpus import NOMES,OBJETOS,DIAS,LUGARES
from preparar_rodada3 import VARIANTES
from dialogo_seq2seq import tokenizar,fonte_dialogo


def h(*textos):
    return [{'papel':'usuario' if i%2==0 else 'assistente','texto':texto} for i,texto in enumerate(textos)]


def construir():
    destino=DIR/'corpus_contrastes.json.gz'
    if destino.exists():raise ValueError('Preservar corpus de contrastes')
    exemplos=json.loads((DIR/'corpus_rodada3.json').read_text())['exemplos'];novos=[]
    preferencias=['azul','vermelho','ler em casa','ter companhia','praticar desenho','praticar fotografia','caderno','mapa']
    for j in range(24):
        nome=NOMES[j];outro=NOMES[(j+7)%24];obj=OBJETOS[j%8]
        pref=preferencias[j%8];nova=preferencias[(j+3)%8]
        dia=DIAS[j%7];novo_dia=DIAS[(j+2)%7];lugar=LUGARES[j%6]
        casos=[]
        # Mesmo campo, negação em posição diferente e resposta anterior errada.
        casos += [
            ('nome_corrigido_negacao_final',h(f'Meu amigo se chama {nome}.','Certo.',
                f'Eu disse errado: o nome é {outro}, não {nome}.','Entendi a correção.'),
                VARIANTES[20][j%3],f'Seu amigo se chama {outro}.'),
            ('nome_corrigido_assistente_errado',h(f'Meu amigo se chama {nome}.','Certo.',
                f'Não, me enganei. O nome é {outro}.',f'Seu amigo se chama {nome}.'),
                VARIANTES[20][(j+1)%3],f'Seu amigo se chama {outro}.'),
            ('nome_na_mensagem_atual',h(f'Meu nome é {nome}.','Certo.'),
                f'Corrija o que falei: pode me chamar de {outro}, não de {nome}. Qual é meu nome?',f'Você se chama {outro}.'),
            ('preferencia_negacao_final',h(f'Eu prefiro {pref}.','Entendi.',
                f'Agora prefiro {nova}, não {pref}.','Certo.'),
                VARIANTES[21][j%3],f'Sua preferência agora é {nova}.'),
            ('preferencia_assistente_errado',h(f'Eu prefiro {pref}.','Certo.',
                f'Mudei de ideia. Agora minha preferência é {nova}.',f'Sua preferência é {pref}.'),
                VARIANTES[21][(j+1)%3],f'Sua preferência agora é {nova}.'),
            ('preferencia_negacao_inicial',h(f'Minha escolha era {pref}.','Certo.',
                f'Não quero mais {pref}. Quero {nova}.','Estou acompanhando.'),
                VARIANTES[21][(j+2)%3],f'Sua preferência agora é {nova}.'),
            ('preferencia_alterada_na_pergunta',h(f'Eu prefiro {pref}.','Certo.'),
                f'Na verdade prefiro {nova}, e não {pref}. Pode me dizer minha preferência atual?',f'Sua preferência agora é {nova}.'),
            ('prazo_corrigido_negacao_final',h(f'Vou encontrar {nome} no {dia}.','Certo.',
                f'O encontro é no {novo_dia}, e não no {dia}.','Entendi.'),
                VARIANTES[23][j%3],f'O encontro com {nome} é no {novo_dia}.'),
            ('prazo_corrigido_na_mensagem',h(f'Posso entregar no {dia}.','Certo.'),
                f'O prazo mudou para {novo_dia}. Atualize a mensagem sem usar {dia}.',f'Posso entregar no {novo_dia}.'),
            ('prazo_correcao_assistente_errado',h(f'Vou encontrar {nome} no {dia}.','Certo.',
                f'Mudou: o encontro ficou para {novo_dia}.',f'O encontro é no {dia}.'),
                VARIANTES[23][(j+1)%3],f'O encontro com {nome} é no {novo_dia}.'),
            ('nome_usuario_amigo_separados',h(f'Meu nome é {nome}.',f'Olá, {nome}!',
                f'Meu amigo se chama {outro}.','Entendi.'),VARIANTES[10][j%3],f'Você se chama {nome}.'),
            ('amigo_usuario_separados',h(f'Meu nome é {nome}.','Certo.',
                f'Meu amigo se chama {outro}.','Estou acompanhando.'),VARIANTES[11][j%3],f'Seu amigo é {outro}.'),
            ('objeto_dono_distinto',h(f'{outro} me emprestou um {obj}.','Certo.',
                f'Meu nome é {nome}.','Entendi.'),VARIANTES[18][j%3],
                f'O {obj} pertence a {outro}; você está usando por empréstimo.'),
            ('nome_amigo_nao_e_usuario',h(f'Meu amigo se chama {nome}.','Entendi.'),
                VARIANTES[10][j%3],'Não tenho essa informação. Você pode me dizer?'),
            ('nome_assistente_nao_e_usuario',[{'papel':'assistente','texto':f'Eu sou {nome}.'}],
                VARIANTES[10][(j+1)%3],'Não tenho essa informação. Você pode me dizer?'),
            ('ficcao_interrompida_retornada',h(f'{nome} ficou preso na {lugar}.','A história parou nesse problema.',
                'Quero organizar minha mesa agora.','Tire da mesa o que não está usando.',
                'Já fiz essa parte. Quero voltar ao conto.','Podemos deixar a mesa para depois.'),
                VARIANTES[85][j%3],f'Podemos. {nome} ainda estava na {lugar}, tentando encontrar uma saída.'),
            ('moradia_atual_nao_e_hipotese',h('Eu moro sozinho.','Certo.',
                f'Se eu morasse com {nome}, como dividir as tarefas?','Vocês poderiam combinar uma divisão.'),
                VARIANTES[61][j%3],'Atualmente você mora sozinho.'),
            ('moradia_corrigida_assistente',h('Eu moro sozinho.',f'Você mora com {nome}.',
                'Eu disse sozinho. Não moro com ninguém.','Entendi essa correção.'),
                VARIANTES[61][(j+1)%3],'Atualmente você mora sozinho.'),
            ('possibilidade_sem_confirmacao',h(f'{nome} talvez traga um {obj}.','Certo.',
                'Não está confirmado, só estou pensando numa possibilidade.','Entendi.'),
                VARIANTES[64][j%3],f'Não. Você disse que {nome} talvez traga um {obj}; isso não confirma a entrega.'),
        ]
        for categoria,historico,mensagem,resposta in casos:
            novos.append({'id':f'contraste-{categoria}-{j:02d}','familia':categoria,'grupo':'contraste_textual',
                'split':'treino','mensagem':mensagem,'historico':historico,'resposta':resposta})
    # Pedidos de referência sem fatos: mesma pergunta recebe esclarecimento,
    # não um nome/prazo recuperado dos pesos. Sem catálogo na execução.
    for i in [10,11,12,13,14,15,16,17,18,19,20,21,22,23,61,85]:
        for v,pedido in enumerate(VARIANTES[i]):
            novos.append({'id':f'contraste-ausencia-{i:03d}-{v}','familia':f'ausencia-{i:03d}',
                'grupo':'sem_fato_fornecido','split':'treino','mensagem':pedido,
                'historico':[],'resposta':'Não tenho essa informação. Você pode me dizer?'})
    exemplos+=novos;unicos={}
    for e in exemplos:
        chave=json.dumps([e['mensagem'],e['historico']],sort_keys=True,ensure_ascii=False)
        if chave in unicos and (unicos[chave]['resposta']!=e['resposta'] or unicos[chave]['split']!=e['split']):
            raise ValueError('Entrada com alvos/splits conflitantes')
        unicos.setdefault(chave,e)
    exemplos=list(unicos.values());vocab=set(json.loads(gzip.decompress((DIR/'checkpoint_rodada2.json.gz').read_bytes()))['vocabulario'])
    oov=Counter(t for e in exemplos for t in tokenizar(e['resposta']) if t not in vocab and t not in fonte_dialogo(e['mensagem'],e['historico']))
    if oov:raise ValueError(f'Alvos impossíveis: {oov}')
    dados={'origem':'corpus da rodada 3 + contrastes autorais de negação, autoria, correção e referência ausente; sem ler holdout',
        'limite':'supervisão explícita autoral, não fatos novos de acervo nem regra aplicada no chat',
        'exemplos':exemplos}
    destino.write_bytes(gzip.compress((json.dumps(dados,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
    estat={'construido_em_utc':datetime.now(timezone.utc).isoformat(),'splits':dict(Counter(e['split'] for e in exemplos)),
        'contrastes_antes_deduplicacao':len(novos),'categorias_contraste':dict(Counter(e['familia'] for e in novos)),
        'vocabulario_preservado':720,'parametros_preservados':81433,
        'sha256_corpus':hashlib.sha256(destino.read_bytes()).hexdigest(),
        'fonte_max_tokens':max(1+len(tokenizar(e['mensagem']))+sum(1+len(tokenizar(t['texto'])) for t in e['historico']) for e in exemplos),
        'limite':'mesmo desenvolvimento preservado; novo holdout ainda reservado; não conta casos conhecidos como avaliação inédita'}
    (DIR/'corpus_contrastes_estatisticas.json').write_text(json.dumps(estat,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(estat,ensure_ascii=False,indent=2))


if __name__=='__main__':
    construir()
