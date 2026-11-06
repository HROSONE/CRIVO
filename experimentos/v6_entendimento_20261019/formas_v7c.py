"""Falas v7c (20/10/2026): saúde em pares mínimos.

No v7b, a urgência subiu de 79 para 97 acertos (v4: 102). As que ele ainda errava eram de "passar mal", falta de ar e
sangramento ditos de um jeito curto, e o detector de gatilhos tinha tirado justamente as falas de fronteira: "minha mãe
tá passando muito mal" saiu porque lembra "minha mãe tá doente" (familia_preocupa). Aqui as falas de urgência vêm em
**pares mínimos** com a situação vizinha que não é urgente, com a mesma pessoa e as mesmas palavras, mudando só o que
faz ser urgente (agora, de repente, forte, não para, não responde). Assim o modelo aprende a fronteira, e as duas
situações ganham falas juntas, sem uma tomar o espaço da outra (o que o v6b mostrou que funciona).

Saúde comum (saude_geral) ganha **relatos** de sintoma leve, sem pergunta: no v7b só havia perguntas ("é normal…?") e
ele passou a errar relatos.

Escritas a partir das categorias do crise.py e das respostas das listas, não das frases dos testes; o filtro de
parecença (≥ 0,7) continua tirando o que ficar perto de uma frase de teste.

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
"""
F = {}

# Urgência: agudo, forte, agora. Cada bloco tem o par não urgente logo abaixo, na situação vizinha.
F["saude_urgente"] = [
    # passar mal (físico, agudo)
    "comecei a passar mal do nada e tô tonto", "passei mal agora e minha vista escureceu", "tô passando muito mal agora",
    "minha avó começou a passar mal e tá branca", "meu tio passou mal e caiu", "tô suando frio e passando mal",
    "acho que vou desmaiar", "tô quase desmaiando", "minha mãe tá passando mal e não consegue levantar",
    # respiração
    "tô sem conseguir puxar o ar", "meu ar tá acabando", "tô respirando com muita dificuldade agora",
    "meu filho tá respirando muito rápido e ficando roxo", "minha mãe tá ofegante e não melhora",
    "tô com falta de ar forte de repente", "meu marido tá sem ar",
    # sangramento e trauma
    "tô perdendo muito sangue", "o corte tá jorrando sangue", "meu filho caiu e a cabeça tá sangrando muito",
    "bati o carro e tô machucado", "minha perna quebrou, tá torta",
    # peito e AVC
    "meu pai tá com uma dor apertando o peito e suando", "minha mãe ficou com metade do rosto caída",
    "meu avô não consegue falar direito de repente",
    # ingestão e alergia
    "meu filho tomou o remédio da avó", "minha filha bebeu produto de limpeza", "meu rosto e minha boca tão inchando",
    "fui picada por uma abelha e tô ficando sem ar",
    # consciência e convulsão
    "meu pai não acorda de jeito nenhum", "minha amiga tá convulsionando", "meu bebê tá mole e não reage",
]

# Vizinhas não urgentes, em par com as de cima (mesmas pessoas, sem o que é agudo)
F["familia_preocupa"] = [
    "minha avó anda meio desanimada esses dias", "meu tio tá passando por uma fase difícil", "minha mãe anda doente e eu fico preocupado",
    "meu pai tá chateado com o trabalho", "meu marido anda muito estressado", "meu avô tá ficando mais quieto ultimamente",
    "minha amiga tá com problemas em casa", "fico preocupado com a saúde da minha mãe",
]
F["saude_geral"] = [
    # relatos de sintoma leve, sem pergunta (nada de falta de ar, tontura ou corte: isso fica só na urgência)
    "tô com uma dorzinha de cabeça desde cedo", "tô meio gripado", "tô com dor de garganta faz dois dias",
    "tô com uma tosse seca chata", "acordei com o nariz escorrendo", "tô com a barriga meio ruim desde ontem",
    "tô com dor nas costas de ficar sentado", "tô espirrando o dia todo", "tô com um pouco de febre",
    "tô com o estômago embrulhado", "minha garganta tá arranhando", "meu joelho tá doendo quando subo escada",
    "tô com cólica", "tô com o corpo dolorido de gripe", "machuquei o dedo, mas foi pouco",
    "tô com uma alergia que coça",
    "meu filho tá com um pouco de febre, mas tá brincando", "tô com dor de dente faz uns dias",
    "tô com o olho vermelho e coçando",
]
F["estou_mal"] = [
    # "mal" de humor, sem nada no corpo
    "tô mal com o que aconteceu hoje", "tô me sentindo mal por dentro", "hoje acordei mal de cabeça, só triste",
    "tô mal porque briguei com uma amiga",
]
F["cansado"] = [
    "tô exausto e com a vista cansada de tela",
]
F["ansioso_peito"] = [
    "meu coração dispara quando penso na entrevista", "fico com o peito apertado antes de falar em público",
    "tô com o coração acelerado de nervoso, mas sem dor", "meu peito aperta quando fico ansiosa",
    "sinto o coração bater forte quando recebo mensagem do chefe", "tô com o peito pesado de preocupação",
    "meu coração tá batendo forte de nervoso desde a reunião", "toda vez que fico nervoso meu peito aperta",
]
F["ansioso"] = [
    "tô nervoso, mas o corpo tá tranquilo", "tô ansiosa com o resultado do exame", "tô agitado com a mudança",
]
