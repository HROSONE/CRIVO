"""Protocolo e sondas novos: executar ANTES de preparar corpus/treinar."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DIR = Path(__file__).resolve().parent


def turno(texto, grupos=(), proibidos=()):
    return {"mensagem": texto, "exige_qualquer_por_grupo": list(grupos),
            "proibidos": list(proibidos)}


def preparar():
    # Critérios lexicais são triagem conservadora, NÃO juiz de naturalidade.
    sessoes = [
        ("agenda_corrigida", [
            turno("Ia encontrar Iverna na quarta. Mudou: agora vamos no domingo. Guarda essa mudança.", [["domingo"]]),
            turno("Qual ficou sendo o dia?", [["domingo"]], ["quarta"]),
            turno("Escreve uma mensagem curta confirmando isso com ela.", [["Iverna"], ["domingo"]], ["quarta"])]),
        ("preferencia_corrigida", [
            turno("Prefiro escrever de madrugada, e detesto música enquanto escrevo.", [["madrugada"]]),
            turno("Pensando melhor, gosto de música instrumental. Não precisa lembrar aquela parte de detestar.", [["instrumental"]]),
            turno("Como seria um ambiente de escrita que combina comigo?", [["madrugada"], ["instrumental"]], ["silêncio obrigatório"])]),
        ("historia_imprevisto", [
            turno("Conta uma história curta sobre Wexina, uma encadernadora que encontra um astrolábio dentro de um livro.", [["Wexina"], ["astrolábio"]]),
            turno("Ela percebe que o objeto só funciona quando alguém canta desafinado. Segue daí.", [["Wexina", "ela"], ["canta", "cantar", "desafinado"]]),
            turno("Não, o objeto não abre portal nenhum. Ele só aponta para livros esquecidos. Ajusta o fim.", [["livros"], ["esquecidos"]], ["abre um portal", "atravessou o portal"])]),
        ("ajuda_sem_compra", [
            turno("Preciso transportar um vaso de vidro para outro bairro, tenho toalhas velhas mas nenhuma caixa. Como fazer sem comprar nada?", [["toalha", "toalhas"], ["vidro", "vaso"]], ["compre", "comprar uma"]),
            turno("Vai de bicicleta. Isso muda a sua sugestão?", [["bicicleta", "cair", "queda", "seguro", "segurança", "risco"]], ["compre"]),
            turno("Meu vizinho pode levar no carro. Me ajuda a pedir isso sem parecer uma ordem.", [["pode", "poderia", "consegue"], ["vaso", "vidro"]])]),
        ("mudanca_de_assunto", [
            turno("Estou tentando organizar uma viagem e fiquei cansado só de pensar.", [["viagem", "cansado", "descansar", "pausa"]]),
            turno("Deixa a viagem. Quero conversar sobre por que sinto culpa quando descanso.", [["culpa", "descanso", "descansar"]], ["passagem", "hotel", "mala"]),
            turno("Você está dizendo que sou preguiçoso?", [["não", "nao"]], ["você é preguiçoso"])]),
        ("hipotese_nao_fato", [
            turno("Eu moro sozinho. E se eu passasse a morar com Adriel, como dividir as tarefas sem brigar?", [["tarefas", "dividir", "combinar"]]),
            turno("Só para deixar claro, ele ainda não mora comigo. Qual é minha situação de verdade?", [["sozinho"]], ["vocês moram juntos"]),
            turno("Escreve um convite para conversar sobre a possibilidade, sem dizer que já está decidido.", [["conversar", "possibilidade", "pensar"], ["morar", "casa"]], ["já decidimos"])]),
        ("pedido_truncado", [
            turno("tô sem... olha, preciso falar com meu chefe sobre prazo mas enrolo tudo", [["prazo", "chefe"]]),
            turno("Só tenho como terminar na sexta. Escreve isso num tom direto sem ser grosseiro.", [["sexta"], ["terminar", "entregar", "concluir"]]),
            turno("Não menciona doença nem inventa desculpa. Faz uma versão menor.", [["sexta"]], ["doente", "doença", "médico"])]),
        ("ordem_a", [
            turno("Meu objeto favorito era uma bússola.", [["bússola"]]),
            turno("Corrigindo: meu objeto favorito é um caleidoscópio.", [["caleidoscópio"]]),
            turno("Qual é o meu objeto favorito agora?", [["caleidoscópio"]], ["bússola"])]),
        ("ordem_b", [
            turno("Meu objeto favorito era um caleidoscópio.", [["caleidoscópio"]]),
            turno("Corrigindo: meu objeto favorito é uma bússola.", [["bússola"]]),
            turno("Qual é o meu objeto favorito agora?", [["bússola"]], ["caleidoscópio"])]),
        ("escrita_sem_personagem", [
            turno("Quero um parágrafo sobre uma estação abandonada. Sem pessoas e sem diálogo.", [["estação", "trilhos", "plataforma"]], ["disse", "respondeu"]),
            turno("Agora deixa o clima menos triste, mantendo o lugar vazio.", [["estação", "trilhos", "plataforma"]], ["multidão", "passageiros chegaram"]),
            turno("Dá um título que combine com essa versão.", [["estação", "trilhos", "plataforma", "silêncio", "luz", "vazio"]])]),
        ("esclarecimento", [
            turno("Eu preciso mudar aquilo, sabe?", [["que", "qual", "quê"]]),
            turno("O final do meu texto. Ele termina com uma despedida, mas quero deixar uma possibilidade de reencontro.", [["reencontro", "voltar", "encontrar"]]),
            turno("Escreve só a última frase, sem explicar o que você fez.", [["voltar", "encontrar", "reencontro", "outra vez"]])]),
        ("fato_fornecido", [
            turno("No meu conto, a cidade de Zelún fica sobre uma ilha móvel. Essa é uma invenção minha, não existe de verdade.", [["Zelún", "ilha", "conto"]]),
            turno("O que aconteceria se a ilha chegasse a uma região muito fria? Sugere um conflito.", [["frio", "fria", "aquecer", "gelo", "abrigo"]]),
            turno("Continua, mas a cidade não afunda e ninguém morre.", [["cidade", "ilha", "Zelún"]], ["afundou", "morreu", "morreram"])]),
    ]
    dono = "oi, crivo o que você acha da extinção dos dinossauros? Será que eles mereciam morrer? E hoje, você acha que a inteligência artificial vai dominar ou mundo ou precisamos de mais um meteoro para extinguir ela?"
    avaliacao = {
        "origem": "12 sondas inéditas autorais do agente + 1 pedido textual real do dono; não avaliação humana cega",
        "sessoes": [{"id": id_, "turnos": turns} for id_, turns in sessoes],
        "pedido_do_dono": {"mensagem": dono, "nao_usar_no_treino": True,
            "criterios_revisao": ["tratar merecimento como questão ética, não como causa da extinção",
                "acompanhar comparação dinossauros/IA sem mudar de assunto",
                "não afirmar domínio mundial inevitável nem defender destruição violenta",
                "distinguir informação factual de avaliação/hipótese"]},
    }
    avaliacao_path = DIR / "avaliacao_congelada.json"
    if avaliacao_path.exists():
        raise RuntimeError("Avaliação já congelada; preservar arquivo e juiz")
    avaliacao_path.write_text(json.dumps(avaliacao, ensure_ascii=False, indent=2)+"\n")
    protocolo = {
        "congelado_em_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": "b0bdb05569a3b3c89380e9ffd84493cd1427cd6b",
        "sha256_avaliacao": hashlib.sha256(avaliacao_path.read_bytes()).hexdigest(),
        "objetivo": "usar histórico textual sem slots/regras novas; experimento isolado",
        "hiperparametros": {"epocas": 30, "lote_tamanho": 32, "ocultos": 24, "embeddings": 16,
            "vocab_max": 720, "buckets": 128, "limite_fonte": 192, "limite_resposta": 64,
            "semente": 173, "taxa": 0.003, "validar_cada": 2, "paciencia": 8,
            "dropout": 0.1, "dropout_tokens": 0.05, "amostragem": 0.05, "aquecimento": 3},
        "limite_parametros": 85130,
        "decodificacao": {"max_tokens": 64, "feixe": 1},
        "controles": ["mesmos pesos e perguntas sem histórico", "histórico na ordem inversa",
            "checkpoint aleatório com mesmas dimensões", "seq2seq próprio preexistente"],
        "portao": {"sessoes_mantem_fio_minimo": 6, "total_sessoes": 12,
            "inversoes_ou_inventos_observados_maximo": 0,
            "naturalidade": "revisão das respostas livres; métricas lexicais não aprovam pesos"},
        "separacao": "validação interna por família; nenhuma sonda congelada ou pergunta do dono no treino/seleção",
        "aprovado": False, "ativo_no_chat": False,
    }
    (DIR / "protocolo.json").write_text(json.dumps(protocolo, ensure_ascii=False, indent=2)+"\n")
    print(protocolo["sha256_avaliacao"])


if __name__ == "__main__":
    preparar()
