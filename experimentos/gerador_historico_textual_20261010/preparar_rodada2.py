"""Revisão guiada SÓ pelo desenvolvimento; holdout externo não é lido.

Mantém arquitetura/orçamento. Validação interna tem reformulações e nomes
novos, mas compartilha operações/saídas: isso NÃO demonstra generalização.
"""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from preparar_corpus import PADROES, NOMES, OBJETOS, LUGARES, CORES, DIAS, HOBBIES, RAIZ
from dialogo_seq2seq import fonte_dialogo, tokenizar, vocabulario_treino

# Uma reformulação autoral por operação, exclusiva da validação interna.
REFORMULACOES = [
    "Olá, tem espaço para um papo?", "É minha primeira vez aqui. Como você pode me ajudar?",
    "Minha cabeça está cheia; como escolho uma coisa para falar?", "Talvez eu esteja exigindo um acerto imediato.",
    "Concluir isso me alegrou, embora as pessoas não tenham se importado.", "Você conhece saudade por experiência própria?",
    "Como você vê a ideia de experimentar mesmo com risco de erro?", "Estou receoso de que riam da minha tentativa.",
    "Hoje prefiro ser ouvido, sem receber dicas.", "Eu só precisava compartilhar essa alegria.",
    "Você lembra meu nome?", "Qual pessoa eu apresentei como amigo?", "Qual objeto levei para essa pessoa?",
    "Em que lugar está quem mencionei?", "Qual atividade eu disse que gostaria de experimentar?",
    "Que dia combina melhor comigo?", "O que eu declarei preferir?", "O objeto é meu ou dessa pessoa?",
    "Quem me emprestou isso?", "Relembre o que preciso entregar e o prazo.",
    "Use a correção: quem é meu amigo?", "Depois da mudança, o que eu prefiro?",
    "Diga só o objeto que escolhi por último.", "Qual foi a data final do encontro?",
    "Mude o cenário para {outro_lugar} e me dê uma frase.", "Quero praticar com alguém agora, não sozinho. Qual é minha preferência?",
    "Não era defeito, estava desmontado. Resuma isso corretamente.", "Corrija a autoria: fui eu que fiz.",
    "Pode tornar essa cena feliz em vez de triste?", "Cancelei. Não vou fazer essa atividade agora.",
    "Invente um conto breve em que {nome} acha um {objeto} na {lugar}.", "Escreva o próximo trecho depois que encontrou isso.",
    "A porta continua presa; qual pode ser a próxima ação?", "Termine com o objeto ainda desaparecido.",
    "Quero uma mudança de decisão pacífica sobre esse segredo.", "O objeto perdeu a voz de repente. O que vem depois?",
    "A chuva chegou, e precisa proteger o objeto. Avance a cena.", "Mostre o efeito que a devolução teve na vida dessa pessoa.",
    "Resolva a porta fechada de modo realista, sem encantamento.", "Mostre o que faz ao descobrir que seguiu uma informação errada.",
    "Reduza o trecho, mantendo o mesmo acontecimento.", "Reformule com gentileza: quero meu {objeto} de volta imediatamente.",
    "Redija um pedido educado para {nome} me emprestar seu {objeto}.", "Preciso avisar que a entrega fica para {dia}. Escreva o aviso.",
    "Dê suspense ao trecho sem trocar a pessoa nem o objeto.", "Recuse o convite com educação, sem dar justificativa inventada.",
    "Redija um pedido de extensão do prazo, sem desculpas falsas.", "Faça uma pergunta usando: {nome} vai trazer um {objeto}.",
    "Como posso chamar um texto sobre um {objeto} abandonado?", "Deixe uma possibilidade de retorno no encerramento.",
    "Como experimentar {hobby} quando meu tempo é limitado?", "Como liberar espaço na mesa usando só o que já tenho?",
    "Qual seria uma etapa mínima para organizar o material dessa atividade?", "Derrubei meu {objeto}; é melhor conferir antes de usar?",
    "Vou levar caminhando. Como diminuir a chance de derrubar?", "Estou dividido entre descansar e fazer {hobby}.",
    "Tenho uma obrigação com prazo e outras sem prazo. Por onde começo?", "Redija um convite a {nome} para repartirmos o trabalho.",
    "Como revisar um texto comprido sem me perder nele?", "Como pedir um favor sem tornar isso uma cobrança?",
    "Imagine dividir a casa com {nome}. Como repartir o trabalho?", "Atualmente divido a casa ou apenas considerei isso?",
    "Como criar tensão se o objeto falante ficar em silêncio?", "Não gostar da experiência de {hobby} significa que falhei?",
    "A entrega do objeto por essa pessoa é certeza ou possibilidade?", "Sugira um acordo para duas pessoas usarem o mesmo {objeto}.",
    "Escreva o lugar depois que fica vazio, sem colocar personagens novos.", "O silêncio de uma pessoa sempre significa que está zangada?",
    "Você pode prometer que {nome} estará aqui no {dia}?", "Depois de começar {hobby}, ainda posso reconsiderar?",
    "Pode resolver aquela coisa?", "Repita o jeito de antes, por favor.", "Um desses objetos deu problema. Ajude a resolver.",
    "Uma dessas pessoas saiu; qual delas permaneceu?", "Você consegue melhorar um texto para mim?",
    "Preciso mandar algo para {nome}, mas estou me enrolando para explicar.", "Preciso começar a mensagem, mas ainda não dei os detalhes.",
    "Me ajuda a resolver?", "Qual é o restante?", "Dá para saber o pensamento de {nome}?",
    "Não vamos falar da viagem agora. Quero mandar uma mensagem para {nome}.", "Mude o tema: minha energia acabou.",
    "Interrompa o conto e me ajude a combinar um encontro.", "Por enquanto quero papo, em vez de instruções.",
    "Vamos falar sobre {hobby}, sem alterar o compromisso que mencionei.", "Retome o conto do ponto onde paramos.",
    "Pode ir além dessa dica? Quero compreender minha dificuldade de começar.", "Você pode fazer uma pergunta para acompanhar a minha decisão?",
    "Me ajude a comunicar que preciso interromper por um momento antes de terminar.", "Agora quero escrever um agradecimento para {nome}.",
    "Faça uma descrição da {lugar} sem nenhum personagem.", "Um {objeto} foi deixado para trás. Escreva sobre isso diretamente.",
    "Escreva um trecho sereno de chuva, sem transformar em aventura.", "Como começar um texto sobre a volta a uma {lugar}?",
    "Acrescente outro trecho ao ambiente vazio, sem personagem novo.", "Mostre duas falas combinando o empréstimo de um {objeto}.",
    "Sugira apenas um conflito de amizade, não o conto inteiro.", "Acrescente um detalhe do ambiente que eu consiga imaginar.",
    "Diga numa frase que rever uma opinião não precisa ser vergonhoso.", "Surpreenda na cena, mas ainda precisa devolver o objeto.",
]

# Diversificar entrada longa e equilibrar famílias sem multiplicar "padrões".
CONTEXTOS = [
    'Hoje foi um dia corrido. Agora posso conversar um pouco.',
    'Estou pelo celular e talvez escreva de um jeito meio solto.',
    'Acabei de chegar em casa e queria trazer outro assunto.',
    'Estou com pouco tempo; prefiro ir direto ao pedido.',
    'Ainda estou organizando minhas ideias, mas vou tentar explicar.',
    'Queria fazer uma pausa para conversar antes de voltar ao trabalho.',
    'Posso mudar de ideia enquanto explico. Vamos com calma.',
    'Vou tentar escrever sem ficar corrigindo cada palavra.',
    'Não tenho uma pergunta muito bem montada, mas posso começar.',
    'Tenho algo para pedir e gostaria de uma resposta simples.',
    'Prefiro conversar em português e explicar do meu jeito.',
    'Vou trazer só um pedido por enquanto.',
    'Minha mensagem pode ficar curta, mas ainda podemos conversar.',
    'Cheguei agora. Quero começar por um assunto diferente.',
    'Não precisa resolver tudo. Vamos olhar para uma coisa primeiro.',
    'Estou escrevendo devagar para organizar o que quero dizer.',
    'Depois de descansar, consegui pensar num pedido.',
    'Já terminei o que estava fazendo. Podemos começar outro papo.',
    'Eu estava distraído, mas agora quero prestar atenção ao pedido.',
    'Vou explicar só o que é necessário para começar.',
    'Podemos seguir com uma resposta curta e depois aprofundar.',
    'Estou testando como você acompanha uma conversa por texto.',
    'Quero tentar dizer isso de forma clara, mesmo sem saber o melhor começo.',
    'Estou com vontade de pensar em voz alta e depois escolher um caminho.',
]


def construir():
    if len(REFORMULACOES) != len(PADROES):
        raise ValueError("Uma reformulação por família")
    corpus_path = DIR/'corpus_rodada2.json'
    if corpus_path.exists():
        raise ValueError("Corpus da rodada 2 já preparado; preservar")
    exemplos = {}
    for i, (grupo, hist, pedido, resposta) in enumerate(PADROES):
        for split, nomes in [('treino', NOMES), ('validacao', ['Ada', 'Ícaro', 'Nara', 'Téo'])]:
            for j, nome in enumerate(nomes):
                valores = dict(nome=nome, outro=nomes[(j+1)%len(nomes)],
                    objeto=OBJETOS[j%len(OBJETOS)], outro_objeto=OBJETOS[(j+3)%len(OBJETOS)],
                    lugar=LUGARES[j%len(LUGARES)], outro_lugar=LUGARES[(j+2)%len(LUGARES)],
                    cor1=CORES[j%len(CORES)], cor2=CORES[(j+1)%len(CORES)],
                    dia=DIAS[j%len(DIAS)], outro_dia=DIAS[(j+2)%len(DIAS)], hobby=HOBBIES[j%len(HOBBIES)])
                historico = [{'papel':'usuario' if k%2==0 else 'assistente', 'texto': t.format(**valores)}
                             for k,t in enumerate(hist)]
                prefixos = [[], [{'papel':'usuario','texto':CONTEXTOS[j]},
                                {'papel':'assistente','texto':'Pode trazer seu pedido.'}]] if split=='treino' else [[]]
                for variante, prefixo in enumerate(prefixos):
                    ex = {'id':f'rodada2-{i:03d}-{split}-{j:02d}-{variante}', 'familia':f'familia-{i:03d}',
                        'grupo':grupo, 'split':split, 'mensagem':(pedido if split=='treino' else REFORMULACOES[i]).format(**valores),
                        'historico':prefixo+historico, 'resposta':resposta.format(**valores)}
                    chave = json.dumps({k:ex[k] for k in ('mensagem','historico','resposta')},sort_keys=True)
                    if chave in exemplos and exemplos[chave]['split']!=split:
                        raise ValueError('Duplicata entre splits')
                    exemplos.setdefault(chave,ex)
    exs=list(exemplos.values());train=[e for e in exs if e['split']=='treino']
    vocab=vocabulario_treino(train,720)
    oov={split:Counter(t for e in exs if e['split']==split for t in tokenizar(e['resposta'])
        if t not in vocab and t not in fonte_dialogo(e['mensagem'],e['historico'])) for split in ['treino','validacao']}
    if oov['treino'] or oov['validacao']:
        raise ValueError(f'Alvos impossíveis: {oov}')
    dados={'origem':'100 famílias autorais anteriores; 100 reformulações autorais só no desenvolvimento; sem acesso ao holdout',
        'limite':'contexto inicial repetido não é nova família. Validação interna compartilha operações/respostas, não prova conversa natural.',
        'exemplos':exs}
    corpus_path.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n')
    estat={'familias_semanticas':100, 'padroes_pedidos_treino':100, 'padroes_pedidos_validacao':100,
        'splits':dict(Counter(e['split'] for e in exs)), 'total_exemplos':len(exs),
        'respostas_literais_distintas':len({e['resposta'] for e in exs}), 'vocabulario':len(vocab),
        'prefixos_conversacionais_autorais':len(CONTEXTOS),
        'tokens_alvo_nao_copiaveis_fora_vocab':{k:dict(v) for k,v in oov.items()},
        'turnos_textuais_treino':sum(2+len(e['historico']) for e in train),
        'fonte_max_tokens':max(1+len(tokenizar(e['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in e['historico']) for e in exs),
        'alvo_max_tokens':max(1+len(tokenizar(e['resposta'])) for e in exs),
        'sha256_corpus':hashlib.sha256(corpus_path.read_bytes()).hexdigest()}
    (DIR/'corpus_rodada2_estatisticas.json').write_text(json.dumps(estat,ensure_ascii=False,indent=2)+'\n')
    original=json.loads((DIR/'protocolo.json').read_text())
    novo={**original,'rodada':2,'congelado_em_utc':datetime.now(timezone.utc).isoformat(),
        'sha256_corpus':estat['sha256_corpus'],
        'motivo_antes_holdout':'rodada 1 tinha 396/3219 tokens de validação impossíveis e selecionou época 4 com respostas ruins; decisão só por desenvolvimento interno',
        'separacao':'validação interna com reformulações e nomes diferentes; famílias/saídas compartilhadas. Holdout congelado permanece intocado e reservado.'}
    (DIR/'protocolo_rodada2.json').write_text(json.dumps(novo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(estat,ensure_ascii=False,indent=2))


if __name__=='__main__':
    construir()
