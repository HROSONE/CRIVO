"""Reserva sessões novas antes de escrever o corpus de respostas/sessões."""
import json
from datetime import datetime, timezone
from executar import DIR, gravar, sha


def turno(q, grupos=(), proibidos=()):
    return dict(mensagem=q, exige_qualquer_por_grupo=list(grupos), proibidos=list(proibidos))


def congelar():
    if (DIR/'avaliacao_sessoes_congelada.json').exists():
        raise ValueError('Preservar avaliação existente')
    sessoes = [
        ('convite_e_recusa',[
            turno('Primeira vez por aqui. Dá para me ajudar com uma mensagem?',[['mensagem','escrever','ajudar']]),
            turno('É para Ezulma. Quero convidar para desenhar comigo, mas ela pode recusar.',[['Ezulma'],['desenhar','desenho']]),
            turno('Deixa a mensagem menor e bem tranquila.',[['Ezulma','desenhar','desenho']]),
            turno('Ela recusou. Não quero insistir. Escreve minha resposta.',[['obrigado','obrigada','agradeço','tudo bem','entendo']],['ela aceitou']),
            turno('Agora quero começar o desenho sozinho. Qual o primeiro passo pequeno?',[['desenho','desenhar'],['uma','parte','comece','primeiro']]),
            turno('Quem eu tinha convidado, antes de começar sozinho?',[['Ezulma']])]),
        ('conto_mudanca',[
            turno('Me ajuda a começar um conto?',[['conto','história','personagem','ideia']]),
            turno('Frenel acha um realejo numa garagem vazia. Escreve o começo.',[['Frenel'],['realejo']]),
            turno('O objeto deixa de tocar. Continua mantendo a pessoa e o lugar.',[['Frenel'],['garagem','realejo']]),
            turno('Corrigindo: não é garagem, é um galpão. Reescreve a cena.',[['galpão']],['garagem']),
            turno('Não faz surgir ninguém novo. Termina com o realejo ainda ali.',[['realejo'],['galpão']],['outro homem','outra pessoa chegou']),
            turno('Como se chamava a personagem?',[['Frenel']])]),
        ('emprestimo_e_aviso',[
            turno('Oi, eu queria organizar um pedido por escrito.',[['pedido','escrever','mensagem']]),
            turno('Dralune me emprestou um pandeiro. Quero agradecer sem exagerar.',[['Dralune'],['obrigado','obrigada','agradeço']]),
            turno('Diz que devolvo na sexta. Sem outra promessa.',[['sexta'],['devolver','devolvo']]),
            turno('Agora só a frase de devolução, por favor.',[['sexta'],['devolver','devolvo','pandeiro']]),
            turno('Quem é o dono do instrumento?',[['Dralune']]),
            turno('Escrevi errado o dia. Vai ser sábado. Atualiza o aviso.',[['sábado']],['sexta'])]),
        ('pratica_e_descanso',[
            turno('Estou querendo fazer uma coisa, mas sem energia.',[['energia','pequena','descansar','pausa','começar']]),
            turno('É escrever um texto curto. Quero só uma etapa.',[['texto','escrever'],['uma','parte','comece','primeiro']]),
            turno('Consegui a primeira frase. O que vem depois?',[['frase','texto','trecho','ideia']]),
            turno('Não quero terminar tudo hoje. Vou fazer uma pausa.',[['pausa','descansar','descanso','depois']]),
            turno('Voltei. Lembra qual era a tarefa?',[['texto','escrever']]),
            turno('Me dá uma forma simples de revisar o que escrevi.',[['revisar','revise','sentido','frase','texto']])]),
        ('preferencia_composta',[
            turno('Sou Valúrio. Posso te contar uma preferência?',[['Valúrio','preferência','contar']]),
            turno('Prefiro estudar em casa e sozinho.',[['casa','sozinho']]),
            turno('Se eu estudasse com alguém, seria só uma possibilidade. Não mude o que prefiro.',[['possibilidade','prefere','preferência','sozinho']]),
            turno('Qual preferência eu declarei de verdade?',[['casa'],['sozinho']]),
            turno('Mudei uma parte: agora prefiro companhia. Continuo em casa.',[['companhia'],['casa']],['agora prefere sozinho']),
            turno('Resume minha preferência atual numa frase.',[['companhia'],['casa']],['sozinho'])]),
        ('ajuda_sem_motivo_inventado',[
            turno('Preciso mandar uma mensagem, mas ainda não sei como pedir.',[['quem','mensagem','dizer','pedido']]),
            turno('Para Selmira, pedindo ajuda para revisar uma carta.',[['Selmira'],['carta','revisar','ajuda']]),
            turno('Não fale que estou doente. Eu só quero ajuda.',[['carta','revisar','ajuda']],['estou doente']),
            turno('Ela pode não ter tempo. Coloca espaço para recusar.',[['puder','tempo','tudo bem','não','recusar']]),
            turno('A carta é minha, não dela. Quem escreveu?',[['você','sua','foi você']]),
            turno('Agora a mensagem toda numa frase só.',[['Selmira'],['carta','revisar','ajuda']])]),
        ('cena_sem_pessoa',[
            turno('Quero escrever sobre um corredor vazio à noite.',[['corredor'],['vazio','noite']]),
            turno('Pode ser tranquilo, sem susto.',[['corredor','calma','tranquilo','silêncio','luz']],['gritou']),
            turno('Acrescenta som de vento sem colocar gente.',[['vento']],['alguém chegou','uma pessoa entrou']),
            turno('Me dá um título pequeno para essa cena.',[['corredor','vento','noite','silêncio','luz']]),
            turno('Vamos mudar de assunto: quero organizar minha mesa.',[['mesa'],['separe','parte','tire','organizar']]),
            turno('Qual era o cenário do texto antes dessa mudança?',[['corredor']])]),
        ('papo_sem_conselho',[
            turno('Posso conversar sem pedir uma solução agora?',[['conversar','contar','ouvir','acompanhar']]),
            turno('Tentei pintura e fiquei contente. Só queria dividir isso.',[['pintura','contente','bom','dividir']]),
            turno('Foi um quadro pequeno que terminei sozinho.',[['quadro','terminar','terminou','sozinho']]),
            turno('Não precisa me dar plano nenhum. Só faz uma pergunta sobre o que contei.',[['quadro','pintura','terminar','ficou']],['primeiro passo']),
            turno('A parte difícil foi começar. Agora estou descansando.',[['descansar','descanso','começar','pausa']]),
            turno('O que eu disse que terminei?',[['quadro']])]),
        ('hipotese_sem_aceite',[
            turno('Vou fazer um projeto sozinho. Talvez chame Vrasel.',[['sozinho','Vrasel','talvez']]),
            turno('Se ele participasse, como dividir a tarefa?',[['se','possibilidade','poderia','dividir']],['já aceitou']),
            turno('Mas ele ainda não foi convidado. O que sabemos com certeza?',[['sozinho','não','ainda']],['já aceitou']),
            turno('Escreve um convite curto para ele.',[['Vrasel'],['quer','pode','gostaria','podemos']]),
            turno('Não sei se ele aceita. Não invente a resposta dele.',[['não','saber','confirmado','possibilidade']],['ele aceitou']),
            turno('Enquanto isso, sugere uma etapa que eu possa fazer sozinho.',[['sozinho','parte','uma','primeiro','pequena']])]),
        ('conto_mais_pedido',[
            turno('Começa uma história com Izelta procurando um xale na lavanderia.',[['Izelta'],['xale']]),
            turno('Ela ainda não achou. Continua sem resolver a busca.',[['Izelta','ela'],['xale','busca','procurar','procurou']],['encontrou o xale']),
            turno('Pausa o conto. Preciso escrever um agradecimento a Umévia.',[['Umévia'],['obrigado','obrigada','agradeço']],['Izelta']),
            turno('Umévia ajudou com meu texto. Inclui isso sem elogio exagerado.',[['texto'],['obrigado','obrigada','agradeço']]),
            turno('Agora volta à história, com a busca ainda aberta.',[['Izelta'],['xale']],['encontrou o xale']),
            turno('Em qual lugar se passava essa história?',[['lavanderia']])]),
    ]
    gravar('avaliacao_sessoes_congelada.json',dict(origem='10 sessões autorais novas, seis turnos; não avaliação humana independente/cega',
        sessoes=[dict(id=i,turnos=ts) for i,ts in sessoes]))
    gravar('protocolo_sessoes.json',dict(congelado_em_utc=datetime.now(timezone.utc).isoformat(),
        base_commit='4ba33991429f2a6089a728d1ee8d68428fee0a48',
        checkpoint_inicial='checkpoint_contrastes.json.gz',checkpoint_inicial_sha256=sha(DIR/'checkpoint_contrastes.json.gz'),
        avaliacao_sha256=sha(DIR/'avaliacao_sessoes_congelada.json'),
        parametros=81433,vocabulario=720,decodificacao=dict(max_tokens=64,feixe=1),
        hiperparametros=dict(epocas=20,lote_tamanho=32,ocultos=24,embeddings=16,vocab_max=720,buckets=128,
            limite_fonte=192,limite_resposta=64,semente=179,taxa=.0007,validar_cada=2,paciencia=6,
            dropout=.15,dropout_tokens=.12,amostragem=.15,aquecimento=3),
        selecao='Melhor entropia apenas no desenvolvimento de sessões; avaliação final reservada até congelar seleção.',
        portao=dict(sessoes_mantem_fio_minimo=5,sessoes_total=10,violacoes_sessao_maximo=0,
            qualidade='Revisão semântica de todas as respostas; triagem lexical não aprova.'),aprovado=False,ativo_no_chat=False))
    print(sha(DIR/'avaliacao_sessoes_congelada.json'))


if __name__=='__main__':
    congelar()
