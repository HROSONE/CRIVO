"""Acervo bíblico: sínteses próprias referenciadas na TNM, sem transcrição."""
import json
import sys
from pathlib import Path

RAIZ = 'https://www.jw.org/pt/biblioteca/biblia/biblia-de-estudo/'
CONSULTA = '2026-10-07'
PAGINAS = {
    'indice': ('Índice de livros', 'livros/'),
    'sal83': ('Salmos 83', 'livros/salmos/83/'),
    'gen1': ('Gênesis 1', 'livros/G%C3%AAnesis/1/'),
    'gen2': ('Gênesis 2', 'livros/G%C3%AAnesis/2/'),
    'gen6': ('Gênesis 6', 'livros/G%C3%AAnesis/6/'),
    'gen12': ('Gênesis 12', 'livros/G%C3%AAnesis/12/'),
    'exo3': ('Êxodo 3', 'livros/%C3%8Axodo/3/'),
    'exo20': ('Êxodo 20', 'livros/%C3%8Axodo/20/'),
    'sal23': ('Salmos 23', 'livros/salmos/23/'),
    'jo3': ('João 3', 'livros/Jo%C3%A3o/3/'),
    'jo17': ('João 17', 'livros/Jo%C3%A3o/17/'),
    'mt6': ('Mateus 6', 'livros/mateus/6/'),
    'mt22': ('Mateus 22', 'livros/mateus/22/'),
    'lc10': ('Lucas 10', 'livros/lucas/10/'),
    'mt5': ('Mateus 5', 'livros/mateus/5/'),
    'mt28': ('Mateus 28', 'livros/mateus/28/'),
    'co13': ('1 Coríntios 13', 'livros/1-Cor%C3%ADntios/13/'),
    'gal5': ('Gálatas 5', 'livros/G%C3%A1latas/5/'),
    'pro3': ('Provérbios 3', 'livros/Prov%C3%A9rbios/3/'),
    'ti3': ('2 Timóteo 3', 'livros/2-Tim%C3%B3teo/3/'),
    'ec9': ('Eclesiastes 9', 'livros/eclesiastes/9/'),
    'ap21': ('Apocalipse 21', 'livros/apocalipse/21/'),
}

# ID, nome, aliases, fonte, referência, definição própria, detalhe próprio.
FICHAS = [
    ('biblia', 'Bíblia', ['Bíblia Sagrada'], 'indice', 'Índice de livros',
     'A Bíblia reúne os livros considerados sagrados no judaísmo e no cristianismo; esta ficha segue a organização da Tradução do Novo Mundo.',
     'A TNM organiza 66 livros em 39 das Escrituras Hebraico-Aramaicas e 27 das Escrituras Gregas Cristãs.'),
    ('tnm', 'Tradução do Novo Mundo', ['TNM', 'Bíblia de estudo TNM', 'Bíblia das Testemunhas de Jeová'], 'indice', 'Índice de livros',
     'A Tradução do Novo Mundo é a versão bíblica usada como referência neste acervo; a edição de estudo em português está no JW.ORG.',
     'Esta edição oferece capítulos, notas, referências e apêndices; o CRIVO apresenta sínteses próprias, não uma cópia integral da tradução.'),
    ('jeova', 'Jeová', ['nome de Deus', 'Deus na Bíblia', 'Jehovah', 'Salmos 83:18'], 'sal83', 'Salmos 83:18',
     'Na TNM, Jeová é o nome de Deus, identificado como a autoridade suprema sobre a Terra em Salmos 83:18.',
     'O salmo é dirigido a Deus e encerra pedindo que as pessoas reconheçam esse nome e sua posição.'),
    ('criacao_biblica', 'criação bíblica', ['criação em Gênesis', 'Gênesis 1:1'], 'gen1', 'Gênesis 1:1-31',
     'Segundo o relato de Gênesis na TNM, Deus dá origem ao céu, à Terra e aos seres vivos.',
     'A narrativa organiza a criação em etapas e apresenta o homem e a mulher no sexto dia; trata-se de um relato religioso.'),
    ('genesis', 'Gênesis', ['livro de Gênesis'], 'gen1', 'Gênesis 1',
     'Gênesis abre a Bíblia; seu primeiro capítulo, na TNM, apresenta a criação como obra de Deus.',
     'Nesse capítulo, a narrativa passa da luz e da organização do ambiente à vegetação, aos animais e aos seres humanos.'),
    ('primeiros_humanos', 'primeiros humanos na Bíblia', ['criação do homem na Bíblia', 'Adão e Eva'], 'gen2', 'Gênesis 2:7, 18-25',
     'Na narrativa da TNM, Jeová forma o primeiro homem e depois providencia a mulher como sua companheira.',
     'O relato apresenta a união do casal e sua vida inicial sem constrangimento diante da nudez.'),
    ('eden', 'jardim do Éden', ['Éden'], 'gen2', 'Gênesis 2:8-17',
     'Na TNM, o jardim do Éden é o lugar em que Jeová estabelece o homem no relato da criação.',
     'O homem recebe a tarefa de cuidar do jardim e uma restrição referente à árvore do conhecimento do bem e do mal.'),
    ('casamento_biblico', 'casamento no relato bíblico', ['casamento em Gênesis'], 'gen2', 'Gênesis 2:24',
     'Na TNM, Gênesis apresenta o casamento como uma união próxima entre o homem e sua esposa.',
     'O versículo relaciona essa união à formação de um vínculo que passa a ter prioridade sobre a casa dos pais.'),
    ('noe', 'Noé', ['arca de Noé'], 'gen6', 'Gênesis 6:9-22',
     'Na TNM, Noé é apresentado como um homem íntegro que recebe de Deus a orientação de construir uma arca.',
     'O relato contrasta sua conduta com a violência de seus contemporâneos e descreve sua obediência às instruções recebidas.'),
    ('abraao', 'Abraão', ['Abrão', 'patriarca Abraão'], 'gen12', 'Gênesis 12:1-7',
     'Na TNM, Abraão, chamado Abrão nesse trecho, é o homem a quem Jeová manda deixar sua terra e seguir para outro lugar.',
     'O relato associa sua viagem a uma promessa de descendência e de bênçãos que alcançariam outras famílias.'),
    ('moises', 'Moisés', ['chamado de Moisés', 'espinheiro em chamas'], 'exo3', 'Êxodo 3:1-15',
     'Na TNM, Moisés recebe de Jeová a missão de conduzir os israelitas para fora da opressão no Egito.',
     'O chamado ocorre no relato do espinheiro em chamas; Deus se identifica pelo nome Jeová ao responder à pergunta de Moisés.'),
    ('mandamentos', 'Dez Mandamentos', ['mandamentos de Êxodo', 'Êxodo 20'], 'exo20', 'Êxodo 20:1-17',
     'Na TNM, os Dez Mandamentos são instruções de Jeová a Israel sobre adoração e convivência.',
     'O trecho inclui respeito aos pais e proibições de assassinato, adultério, furto, falso testemunho e cobiça.'),
    ('salmo23', 'Salmo 23', ['Salmos 23', 'Jeová meu pastor'], 'sal23', 'Salmos 23:1-6',
     'Na TNM, o Salmo 23 compara o cuidado de Jeová ao de um pastor que protege e guia.',
     'A imagem transmite confiança mesmo em circunstâncias ameaçadoras e termina com a esperança de permanecer perto de Jeová.'),
    ('jesus', 'Jesus Cristo', ['Jesus', 'Cristo Jesus'], 'jo17', 'João 17:1-6',
     'Na TNM, Jesus Cristo é apresentado como o Filho enviado pelo Pai e fala com Deus em oração.',
     'Nessa oração, Jesus relaciona a vida eterna ao conhecimento do Pai e dele próprio, e diz ter revelado o nome do Pai.'),
    ('joao316', 'João 3:16', ['João 3 16', 'amor de Deus em João'], 'jo3', 'João 3:16-17',
     'Na TNM, João 3:16 relaciona o amor de Deus pela humanidade ao envio de seu Filho e à esperança de vida eterna.',
     'O trecho destaca a fé no Filho e apresenta seu envio como voltado à salvação.'),
    ('vida_eterna_biblica', 'vida eterna na Bíblia', ['João 17:3'], 'jo17', 'João 17:3',
     'Na TNM, João 17:3 vincula a vida eterna a conhecer o Pai, identificado como Deus verdadeiro, e Jesus Cristo.',
     'Essa declaração aparece numa oração de Jesus; é um ensinamento religioso do texto.'),
    ('reino_deus', 'Reino de Deus', ['Reino dos céus', 'Mateus 6:10'], 'mt6', 'Mateus 6:9-10, 33',
     'Na TNM, o Reino de Deus aparece na oração ensinada por Jesus, junto ao pedido de realização da vontade divina.',
     'Jesus orienta seus ouvintes a dar prioridade ao Reino e à justiça de Deus.'),
    ('oracao_biblica', 'oração bíblica', ['oração na Bíblia', 'como orar', 'Pai Nosso', 'Mateus 6:9'], 'mt6', 'Mateus 6:5-13',
     'Na TNM, Jesus ensina a orar ao Pai com sinceridade, evitando exibição e repetição sem reflexão.',
     'Sua oração-modelo inclui o nome de Deus, o Reino, necessidades diárias, perdão e proteção.'),
    ('perdao_biblico', 'perdão na Bíblia', ['perdão bíblico', 'Mateus 6:14'], 'mt6', 'Mateus 6:12, 14-15',
     'Na TNM, Jesus relaciona o pedido de perdão a Deus à disposição de perdoar outras pessoas.',
     'Jesus retoma o perdão depois da oração-modelo, enfatizando a relação entre perdoar e buscar o perdão do Pai.'),
    ('amor_proximo', 'amor ao próximo', ['maior mandamento', 'Mateus 22:37', 'Mateus 22:39'], 'mt22', 'Mateus 22:37-40',
     'Na TNM, Jesus apresenta amar a Jeová e amar o próximo como os dois mandamentos centrais.',
     'A resposta é dada a uma pergunta sobre o maior mandamento e relaciona esses princípios à Lei e aos Profetas.'),
    ('samaritano', 'bom samaritano', ['parábola do bom samaritano', 'Lucas 10:30'], 'lc10', 'Lucas 10:29-37',
     'Na TNM, o bom samaritano é o personagem da ilustração de Jesus que socorre um homem ferido por assaltantes.',
     'A narrativa valoriza a misericórdia demonstrada em ações, em contraste com os que passam sem ajudar.'),
    ('marta_maria', 'Marta e Maria', ['Maria e Marta'], 'lc10', 'Lucas 10:38-42',
     'Na TNM, Marta recebe Jesus em sua casa, enquanto Maria se dedica a escutar seus ensinamentos.',
     'Jesus responde à preocupação de Marta destacando o valor da escolha de Maria, que estava ouvindo.'),
    ('sermao_monte', 'Sermão do Monte', ['sermão da montanha', 'bem-aventuranças'], 'mt5', 'Mateus 5:1-12',
     'Na TNM, Mateus 5 abre um discurso de Jesus a seus discípulos conhecido como Sermão do Monte.',
     'A abertura valoriza qualidades como misericórdia, brandura, desejo de justiça e disposição para promover a paz.'),
    ('pacificadores', 'pacificadores na Bíblia', ['Mateus 5:9'], 'mt5', 'Mateus 5:9',
     'Na TNM, Jesus elogia os que promovem a paz e os associa à condição de filhos de Deus.',
     'Esse ensino está na abertura do Sermão do Monte, junto a outras qualidades valorizadas por Jesus.'),
    ('amor_inimigos', 'amor aos inimigos', ['Mateus 5:44'], 'mt5', 'Mateus 5:43-48',
     'Na TNM, Jesus orienta seus discípulos a amar até os inimigos e a orar por quem os persegue.',
     'O trecho contrasta esse ensino com amar apenas aqueles que retribuem o amor.'),
    ('ressurreicao_jesus', 'ressurreição de Jesus', ['Mateus 28:6'], 'mt28', 'Mateus 28:1-10',
     'Na TNM, Mateus relata que as mulheres encontram o túmulo vazio e recebem a notícia de que Jesus voltou à vida.',
     'Depois, a narrativa descreve o encontro de Jesus com as mulheres e a mensagem que elas devem levar aos discípulos.'),
    ('batismo_biblico', 'batismo cristão', ['batismo na Bíblia', 'Mateus 28:19'], 'mt28', 'Mateus 28:18-20',
     'Na TNM, Jesus instrui seus seguidores a formar discípulos e batizá-los em relação ao Pai, ao Filho e ao espírito santo.',
     'O mesmo trecho liga essa tarefa ao ensino e à obediência às orientações de Jesus.'),
    ('amor_biblico', 'amor na Bíblia', ['1 Coríntios 13', '1 Coríntios 13:4'], 'co13', '1 Coríntios 13:1-13',
     'Na TNM, 1 Coríntios 13 descreve o amor por atitudes de paciência, cuidado e ausência de arrogância.',
     'O capítulo afirma que habilidades e realizações perdem valor sem amor, e dá a ele destaque sobre fé e esperança.'),
    ('fruto_espirito', 'fruto do espírito', ['frutos do espírito', 'Gálatas 5:22'], 'gal5', 'Gálatas 5:22-23',
     'Na TNM, o fruto do espírito reúne qualidades como amor, alegria, paz, paciência, bondade, benignidade, fé, brandura e autodomínio.',
     'O trecho contrasta essas qualidades com condutas destrutivas descritas anteriormente no capítulo.'),
    ('confianca_jeova', 'confiança em Jeová', ['Provérbios 3:5'], 'pro3', 'Provérbios 3:5-7',
     'Na TNM, Provérbios aconselha confiar em Jeová em vez de tomar o próprio julgamento como suficiente.',
     'O conselho inclui considerar Deus nas decisões e evitar uma atitude de autossuficiência.'),
    ('inspiracao_biblica', 'inspiração da Bíblia', ['Escritura inspirada', '2 Timóteo 3:16'], 'ti3', '2 Timóteo 3:16-17',
     'Na TNM, 2 Timóteo atribui a origem das Escrituras à inspiração divina e destaca seu papel educativo.',
     'O trecho relaciona seu estudo ao preparo para agir bem; essa é uma afirmação religiosa da própria passagem.'),
    ('morte_biblica', 'morte em Eclesiastes', ['Eclesiastes 9:5', 'mortos em Eclesiastes'], 'ec9', 'Eclesiastes 9:5-10',
     'Na TNM, Eclesiastes descreve os mortos como sem consciência e sem participação nas atividades da vida.',
     'O trecho incentiva aproveitar a vida e realizar as tarefas enquanto há oportunidade; esta ficha resume esse contexto religioso.'),
    ('esperanca_biblica', 'esperança em Apocalipse', ['Apocalipse 21:4', 'fim do sofrimento na Bíblia'], 'ap21', 'Apocalipse 21:1-5',
     'Na TNM, Apocalipse apresenta uma visão de renovação em que Deus elimina sofrimento e morte.',
     'A passagem associa essa esperança à proximidade de Deus com a humanidade; é uma promessa religiosa do relato.'),
]


def montar():
    fontes = {}
    for chave, (titulo, caminho) in PAGINAS.items():
        fontes['bib_tnm_' + chave] = {
            'titulo': 'Tradução do Novo Mundo (Edição de Estudo) — ' + titulo,
            'url': RAIZ + caminho, 'tipo': 'institucional_religiosa',
            'ano': 2026, 'ano_tipo': 'consulta',
            'credito': 'Watch Tower Bible and Tract Society of Pennsylvania / JW.ORG',
            'reutilizacao': 'somente_referencia', 'reproducao_autorizada': False,
            'direitos_url': 'https://www.jw.org/pt/termos-de-uso/',
            'verificado_em': CONSULTA,
            'escopo_uso': 'Referência de sínteses próprias sobre a TNM. Sem transcrição de versículos, notas, tabelas ou imagens e sem indicação de endosso.',
        }
    itens = []
    for ident, nome, aliases, fonte, ref, definicao, detalhe in FICHAS:
        fatos = []
        for papel, texto in [('definicao', definicao), ('detalhe', detalhe)]:
            if not texto.startswith(('Na TNM', 'Segundo', 'A Bíblia', 'A Tradução')):
                proprio = texto.split()[0] in ('Jesus', 'Jeová', 'Moisés', 'Maria', 'Marta', 'Noé')
                texto = 'Na TNM, ' + (texto if proprio else texto[:1].lower() + texto[1:])
            fatos.append({'texto': texto + ' Referência: ' + ref + '.',
                          'fonte': 'bib_tnm_' + fonte, 'papel': papel,
                          'natureza': 'religioso', 'referencia_biblica': ref})
        itens.append({'id': 'mundo_biblia_' + ident, 'nome': nome, 'area': 'biblia',
                      'aliases': aliases, 'fatos': fatos})
    return {'versao': 1, 'revisado_em': CONSULTA,
            'criterio': 'Sínteses próprias atribuídas à Tradução do Novo Mundo, edição de estudo em português. Referências oficiais verificadas; natureza religiosa, sem transcrição integral ou novos pesos.',
            'fontes': fontes, 'itens': itens, 'ligacoes': [], 'comparacoes': []}


if __name__ == '__main__':
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'conhecimento_biblia.json'
    destino.write_text(json.dumps(montar(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
