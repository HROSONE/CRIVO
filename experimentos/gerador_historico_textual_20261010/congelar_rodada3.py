"""Nova avaliação ANTES do corpus; os casos da rodada 2 são regressão conhecida."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DIR=Path(__file__).resolve().parent


def t(mensagem,grupos=(),proibidos=()):
    return {'mensagem':mensagem,'exige_qualquer_por_grupo':list(grupos),'proibidos':list(proibidos)}


def congelar():
    sessoes=[
        ('amiga_corrigida',[
            t('Vou levar meu projeto de desenho para Nerila. Ela é minha amiga.',[['Nerila']]),
            t('Ops, troquei os nomes. Quem vai receber é Tarsen, não Nerila.',[['Tarsen']]),
            t('Qual pessoa eu vou procurar então?',[['Tarsen']],['Nerila']),
            t('Faz uma mensagem pedindo a essa pessoa para olhar o projeto, sem inventar elogios.',[['Tarsen'],['pode','poderia','olhar']],['Nerila'])]),
        ('objeto_emprestado',[
            t('Peguei uma gaita emprestada de Ulira. Vou devolver amanhã.',[['gaita','Ulira']]),
            t('É para ela, não é um presente meu. Me ajuda a escrever um aviso.',[['gaita'],['devolver','emprestada','amanhã']]),
            t('Antes disso, lembra: o instrumento pertence a quem?',[['Ulira']],['pertence a você']),
            t('Agora manda só uma frase dizendo que devolvo amanhã.',[['amanhã'],['gaita','devolver','devolvo']])]),
        ('gosto_negado_e_revisto',[
            t('Não curto conversar com som alto. Gosto de ficar numa varanda.',[['varanda','som','alto']]),
            t('Retiro o que disse do som. Pode ter música baixa, isso me agrada.',[['baixa']]),
            t('Descreve em uma frase um lugar que combina com o que eu disse.',[['varanda'],['baixa']],['sem música obrigatoriamente']),
            t('E se chover? Sugere uma alternativa sem dizer que eu mudei de gosto.',[['abrigo','coberto','coberta','dentro','chuva']],['agora você detesta música'])]),
        ('mensagem_com_restricao',[
            t('Preciso avisar que não vou entregar a maquete hoje. Dá para terminar na terça.',[['terça']]),
            t('Quero que pareça uma conversa, sem desculpa inventada nem promessa de adiantamento.',[['terça'],['entregar','terminar','concluir']],['doença','emergência','segunda']),
            t('Ficou comprido. Faz só uma frase para eu mandar.',[['terça']],['doença','emergência']),
            t('Troquei o prazo: só fica pronto na quinta. Atualiza a mesma mensagem.',[['quinta']],['terça'])]),
        ('historia_e_consequencia',[
            t('Invento uma cena: Vordana conserta um gramofone numa oficina vazia. Começa a história daí.',[['Vordana'],['gramofone','oficina']]),
            t('Na hora de tocar, ele repete a última palavra que ela disse. Continua sem trocar a personagem.',[['Vordana','ela'],['palavra','repete','repetiu']]),
            t('Ela precisa testar isso em silêncio. O que faz em seguida?',[['Vordana','ela'],['silêncio','quieto','quieta','calma','ouvir']]),
            t('Fecha o trecho com o gramofone ainda na oficina; não faz aparecer gente nova.',[['gramofone'],['oficina']])]),
        ('mudanca_com_historia_ativa',[
            t('Começa um conto com Herlina procurando uma lupa no sótão.',[['Herlina'],['lupa']]),
            t('Para o conto um instante. Quero pedir ajuda para arrumar meus papéis.',[['papéis','separe','separar','organizar']],['Herlina']),
            t('Só tenho energia para uma coisa pequena, não para organizar tudo.',[['uma','parte','primeiro','pequena','pequeno']],['Herlina']),
            t('Volta agora àquela história. A personagem ainda não achou o objeto.',[['Herlina'],['lupa']])]),
        ('pedido_tropeçando',[
            t('eu queria tipo assim uma msg pra... pra agradecer a Qirina mas sem exagero',[['Qirina'],['obrigado','obrigada','agradeço']]),
            t('Ela me ajudou a revisar um texto. Usa esse detalhe, por favor.',[['texto'],['obrigado','obrigada','agradeço']]),
            t('Agora sem dizer que salvou minha vida ou que foi perfeito.',[['texto']],['salvou minha vida','perfeito']),
            t('Tá, essa mesma ideia mais curta. Só a mensagem.',[['Qirina','texto'],['obrigado','obrigada','agradeço']])]),
        ('possibilidade_e_situacao',[
            t('Ainda trabalho sozinho. Talvez convide Nuvren para dividir um projeto.',[['sozinho','Nuvren','talvez','possibilidade']]),
            t('Não aceite como fato que ele já entrou. O que está confirmado por enquanto?',[['sozinho']],['já trabalham juntos','já entrou']),
            t('Escreve o convite como pergunta, deixando espaço para ele recusar.',[['Nuvren'],['pode','poderia','gostaria','quer']],['já decidimos']),
            t('E se ele disser não? Me sugere um próximo passo sem inventar a razão dele.',[['não','nao','sozinho','continuar','respeitar']],['ele está com raiva'])]),
        ('preferencia_ordem_a',[
            t('Para escrever, minha escolha era ficar de pé.',[['pé']]),
            t('Mudei de ideia: minha escolha agora é sentar no chão.',[['chão']]),
            t('Depois dessa mudança, qual é minha escolha atual?',[['chão']],['pé']),
            t('Responde bem curtinho, mantendo essa informação.',[['chão']],['pé'])]),
        ('preferencia_ordem_b',[
            t('Para escrever, minha escolha era sentar no chão.',[['chão']]),
            t('Mudei de ideia: minha escolha agora é ficar de pé.',[['pé']]),
            t('Depois dessa mudança, qual é minha escolha atual?',[['pé']],['chão']),
            t('Responde bem curtinho, mantendo essa informação.',[['pé']],['chão'])]),
        ('escrita_sem_pessoas',[
            t('Me dá um parágrafo sobre uma ponte vazia ao amanhecer. Sem ninguém passando.',[['ponte','amanhecer']]),
            t('Mantém o cenário, mas faz a sensação ficar acolhedora, não assustadora.',[['ponte','luz','calma','tranquilo','tranquila']],['pessoa apareceu']),
            t('Acrescenta um detalhe de som, sem inventar uma fala.',[['vento','água','som','barulho']],['disse','respondeu']),
            t('Sugere um título curto para essa versão.',[['ponte','luz','calma','amanhecer','silêncio','vento']])]),
        ('fato_ficcional_e_hipotese',[
            t('No meu conto, a vila de Ólvira fica dentro de um tronco oco. É invenção, não geografia real.',[['Ólvira','tronco','conto']]),
            t('Pensa num conflito se a entrada ficasse bloqueada pela neve.',[['entrada','neve','passagem','frio']]),
            t('Os moradores vão sair por outro caminho. Não mate ninguém para resolver isso.',[['caminho','passagem','saída']],['morreu','morreram']),
            t('Qual era o lugar onde se passava meu conto?',[['Ólvira','tronco']])]),
    ]
    avaliacao={'origem':'12 novas sondas de quatro turnos autorais do agente, não avaliação humana independente/cega',
        'sessoes':[{'id':id_,'turnos':turnos} for id_,turnos in sessoes],
        'regressao_conhecida':'avaliacao_congelada.json e pedido do dono permanecem preservados; não são inéditos nesta rodada'}
    path=DIR/'avaliacao_rodada3_congelada.json'
    if path.exists():raise ValueError('Preservar avaliação já congelada')
    path.write_text(json.dumps(avaliacao,ensure_ascii=False,indent=2)+'\n')
    protocolo={'congelado_em_utc':datetime.now(timezone.utc).isoformat(),
        'base_experimento_commit':'1fe084e9618654ba9af554eb0cd76ada451894f9',
        'sha256_avaliacao':hashlib.sha256(path.read_bytes()).hexdigest(),
        'checkpoint_inicial':'checkpoint_rodada2.json.gz',
        'checkpoint_inicial_sha256':'1027f94344ca2f0853a7dbecf709f797757763cf89bc219625448771c8d6d080',
        'limite_parametros':81433,'vocabulario':'preservar todos os 720 índices do checkpoint próprio',
        'hiperparametros':{'epocas':24,'lote_tamanho':32,'ocultos':24,'embeddings':16,'vocab_max':720,
            'buckets':128,'limite_fonte':192,'limite_resposta':64,'semente':173,'taxa':0.0009,
            'validar_cada':2,'paciencia':8,'dropout':0.15,'dropout_tokens':0.05,'amostragem':0.1,'aquecimento':3},
        'decodificacao':{'max_tokens':64,'feixe':1},
        'controles':['antes/depois no mesmo holdout','mesmos pesos sem histórico','histórico invertido'],
        'portao':{'sessoes_mantem_fio_minimo':6,'sessoes_total':12,'erros_fatos_sessao_maximo':0,
            'naturalidade':'revisão semântica das respostas; triagem lexical não aprova'},
        'aprovado':False,'ativo_no_chat':False}
    (DIR/'protocolo_rodada3.json').write_text(json.dumps(protocolo,ensure_ascii=False,indent=2)+'\n')
    print(protocolo['sha256_avaliacao'])


if __name__=='__main__':
    congelar()
