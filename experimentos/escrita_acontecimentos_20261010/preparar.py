"""Supervisão autoral de acontecimentos; nenhum alvo das sondas é usado."""
import copy
import hashlib
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent.parent))
from linguagem_gerativa import tokenizar

EVENTOS = {
    'cotidiano': ('', 'A personagem observou o trabalho diante de si. Escolheu uma parte para começar. O trabalho avançou com cuidado.'),
    'perda': ('A personagem perdeu um amuleto', 'A personagem procurou o objeto perdido. Observou o caminho com cuidado. Uma pista mostrou onde procurar.'),
    'recuperacao': ('O amuleto já foi recuperado', 'A personagem guardou o objeto recuperado. Verificou que estava seguro. A busca continuou sem repetir o problema.'),
    'encontro': ('A personagem encontrou um baú verde', 'A personagem observou o objeto encontrado. Uma pista chamou a atenção. Decidiu examinar o objeto com cuidado.'),
    'caixa_vazia': ('O baú estava vazio', 'A surpresa fez a personagem parar. Conferiu o objeto mais uma vez. Decidiu procurar uma explicação.'),
    'retorno': ('A personagem decidiu voltar para o lugar anterior', 'A personagem voltou pelo caminho conhecido. Levou o objeto com cuidado. O retorno encerrou aquela parte da história.'),
    'ajuda': ('A mensagem pediu auxílio', 'A personagem respondeu ao pedido. Disse que tentaria ajudar. Depois procurou saber qual era o problema.'),
    'costura': ('Uma colega trouxe um fio verde', 'A personagem usou o fio recebido. Costurou com cuidado para unir as partes. A ajuda trouxe um novo progresso.'),
    'devolucao': ('A personagem devolveu o objeto', 'A personagem deixou o objeto no lugar combinado. A entrega trouxe uma resposta. O problema pôde ser resolvido.'),
    'companhia': ('A personagem encontrou uma companhia', 'A personagem recebeu a ajuda. Juntos, decidiram o próximo passo. O encontro trouxe uma nova possibilidade.'),
    'conserto': ('A personagem tentou consertar um tecido rasgado', 'A personagem examinou o rasgo. Procurou unir as partes soltas. O trabalho avançou com cuidado.'),
    'divertido': ('', 'A personagem fez uma pose de coragem. Um susto fez a pose sair do avesso. Riu do próprio susto e tentou de novo.'),
}


PROGRESSO = (
    'A personagem observou o trabalho diante de si. Escolheu uma parte para começar. O trabalho avançou com cuidado.',
    'A personagem conferiu a primeira tentativa. Uma dúvida pediu atenção. Procurou um jeito de resolver aquela parte.',
    'A personagem tentou outro jeito. O resultado mostrou o que precisava mudar. Cuidou dos detalhes antes de continuar.',
    'A personagem recebeu uma ideia. A ideia mostrou o próximo passo. O trabalho continuou com cuidado.',
    'A personagem verificou a última tentativa. O trabalho estava diferente. Uma parte ficou pronta.',
    'A personagem comparou as tentativas. Escolheu o que tinha funcionado. A solução ficou mais clara.',
    'A personagem cuidou do que ainda faltava. A tarefa avançou mais um pouco. Restava conferir o resultado.',
    'A personagem terminou aquela parte. Observou o resultado com calma. Estava pronta para o próximo passo.',
)
HUMOR = (
    'A personagem fez uma pose de coragem. Um susto fez a pose sair do avesso. Riu do próprio susto e tentou de novo.',
    'A personagem tentou parecer muito séria. Um espirro atrapalhou a pose. Riu e começou de novo.',
    'A personagem falou com o próprio chapéu. O chapéu não respondeu. A personagem agradeceu mesmo assim.',
    'A personagem procurou um lugar para sentar. Sentou bem ao lado do banco. Depois riu da própria pressa.',
    'A personagem ensaiou uma dança. Os pés seguiram caminhos diferentes. Riu e tentou um passo menor.',
    'A personagem quis dar uma explicação. Esqueceu o começo da frase. Terminou com uma risada.',
    'A personagem fez uma reverência. O chapéu caiu bem na frente. Recolheu o chapéu com outra reverência.',
    'A personagem tentou andar em silêncio. Um espirro apareceu de novo. Riu e desistiu da pose séria.',
)


def main():
    original = json.loads((H.parent / 'generalizacao_dialogo_20261010/corpus_gru.json').read_text())
    exemplos = copy.deepcopy(original['exemplos'])
    novos = []
    for familia, (evento, corpo) in EVENTOS.items():
        for lugar in (False, True):
            for companhia in (False, True):
                for acao in (('historia', 'continuacao', 'final') if familia in ('cotidiano','divertido') else ('continuacao','final')):
                    for estilo in ('neutro', 'simples'):
                        for variante in range(8):
                            for val in (False, True):
                                slots = {'tema1': 'uma irara aprendiz' if not val else 'um ouriço viajante'}
                                if lugar:
                                    slots['tema2'] = 'um bosque distante' if not val else 'um castelo silencioso'
                                if companhia:
                                    slots['detalhe'] = 'uma colega' if not val else 'um aliado'
                                if evento:
                                    slots['relato'] = evento if not val else evento.replace('amuleto', 'medalhão').replace('baú verde', 'cofre roxo').replace('fio verde', 'fio lilás')
                                prefixo = ('Ficção: @tema1 ' + ('concluiu' if acao == 'final' else 'começou' if acao == 'historia' else 'continuou') + ' a história'
                                           + (' com @detalhe' if companhia else '') + (' em @tema2' if lugar else '') + '. ')
                                corpo_atual = PROGRESSO[variante] if familia == 'cotidiano' else HUMOR[variante] if familia == 'divertido' else corpo
                                texto = prefixo + ('@relato. ' if evento else '') + corpo_atual
                                if companhia:
                                    texto = texto.replace('Conferiu o objeto', 'Juntos, conferiram o objeto').replace('A personagem respondeu', 'Juntos, responderam')
                                if acao == 'final':
                                    texto += (' A personagem terminou o trabalho. Conferiu o resultado e descansou.' if familia in ('cotidiano','costura','conserto') else ' A personagem guardou o objeto em segurança. A busca terminou.' if familia == 'recuperacao' else ' A personagem agradeceu a ajuda. A história terminou com uma descoberta.')
                                ident = 'evento-%s-%d-%d-%s-%s-%d-%d' % (familia, lugar, companhia, acao, estilo, variante, val)
                                novos.append({'id': ident, 'dialogo': ident, 'familia': familia, 'split': 'validacao' if val else 'treino',
                                              'contexto': {'acao': acao, 'slots': slots, 'estilo': estilo, 'variante': variante,
                                                           'mensagem': 'acontecimento ' + familia + ' estado_' + familia, 'historico': [], 'resposta_anterior': ''},
                                              'resposta': texto, 'origem': 'Texto autoral de reação/ação; entidades e alvos das sondas excluídos.'})
    adicionais=[]
    for e in novos:
        if e['familia'] in ('cotidiano','divertido'):
            c=copy.deepcopy(e);c['id']+='-relato';c['dialogo']+='-relato'
            c['contexto']['slots']['relato']='A personagem escolheu uma nova tarefa' if c['split']=='treino' else 'A personagem pediu uma nova ideia'
            pos=c['resposta'].index('. ')+2;c['resposta']=c['resposta'][:pos]+'@relato. '+c['resposta'][pos:]
            adicionais.append(c)
    novos+=adicionais
    exemplos += novos
    vocabulario = list(original['vocabulario'])
    vocabulario += sorted({t for e in novos for t in tokenizar(e['resposta'])} - set(vocabulario))
    dados = {'versao': 5, 'origem': 'Corpus próprio com supervisão de acontecimento e final condicionado.',
             'fontes_externas': False, 'vocabulario': vocabulario, 'exemplos': exemplos,
             'limite': 'Doze classes autorais e padrões compartilhados nas partições. Não demonstra raciocínio nem generalização irrestrita.'}
    p = H / 'corpus_gru.json'
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n')
    auditoria = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'novos': len(novos), 'exemplos': len(exemplos),
                 'treino': sum(e['split'] == 'treino' for e in exemplos), 'validacao': sum(e['split'] == 'validacao' for e in exemplos),
                 'vocabulario': len(vocabulario), 'tokens_novos': sorted(set(vocabulario) - set(original['vocabulario'])),
                 'particao': 'Entidades e diálogos inteiros separados. Classes e padrões compartilhados; não teste independente de enredo.'}
    (H / 'auditoria_corpus.json').write_text(json.dumps(auditoria, ensure_ascii=False, indent=2) + '\n')
    print(auditoria)


if __name__ == '__main__':
    main()
