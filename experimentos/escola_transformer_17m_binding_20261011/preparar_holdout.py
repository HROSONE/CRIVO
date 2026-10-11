"""Holdout prospectivo v2: ligação de entidades no Transformer 17M.

Congelar este gerador antes de implementar o treinador da segunda aula.
"""
from __future__ import annotations

SEMENTE = 202610112
OPERACOES = (
    "recordar_pessoa", "recordar_objeto", "corrigir_pessoa",
    "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe",
)
FAMILIAS = (
    ("aquário", "densímetro", "catalogação marinha", "Zerin", "Liora"),
    ("planetário", "espectroscópio", "observação espectral", "Mavin", "Selka"),
    ("hangar", "torquímetro", "manutenção de drone", "Noril", "Tessa"),
    ("estação meteorológica", "pluviômetro", "leitura climática", "Pavel", "Yara"),
    ("ateliê", "cavalete", "restauro de tela", "Roven", "Dalia"),
)
OBJETOS_EXTRA = (
    "salinômetro", "mapa estelar", "multímetro", "anemômetro", "espátula",
    "termômetro", "ocular", "chave dinamométrica", "barômetro", "paleta",
)
ATIVIDADES_EXTRA = (
    "triagem de corais", "projeção celeste", "inspeção de hélice", "registro de vento", "mistura de pigmentos",
    "medição de salinidade", "calibração óptica", "teste de bateria", "comparação de pressão", "limpeza de verniz",
)
ORDENS = (
    OPERACOES,
    ("recordar_objeto","pedir_detalhe","corrigir_pessoa","recordar_pessoa","mensagem_sem_horario","guardar_hipotese"),
    ("guardar_hipotese","recordar_pessoa","mensagem_sem_horario","corrigir_pessoa","recordar_objeto","pedir_detalhe"),
    ("pedir_detalhe","mensagem_sem_horario","recordar_objeto","guardar_hipotese","corrigir_pessoa","recordar_pessoa"),
)
PERGUNTAS = {
    "recordar_pessoa": (
        "No caso de {atividade} com {objeto}, recupere somente a pessoa que está valendo.",
        "Depois das mudanças deste caso com {objeto}, qual nome de pessoa devo usar?",
        "Para {atividade}, qual participante ficou como referência atual?",
        "Diga a identidade humana vigente na situação de {atividade} e {objeto}.",
    ),
    "recordar_objeto": (
        "Volte ao estado de {atividade} e diga qual item físico foi guardado.",
        "Na situação com {pessoa}, qual instrumento ou objeto material pertence ao caso?",
        "Recupere a coisa concreta associada a {atividade}, sem confundir com a atividade.",
        "Para {pessoa} em {atividade}, qual é o objeto registrado?",
    ),
    "corrigir_pessoa": (
        "Na situação de {atividade}, substitua {pessoa} por {nova} como participante.",
        "A referência humana do caso com {objeto} mudou de {pessoa} para {nova}; registre a troca.",
        "Corrija a pessoa ativa de {atividade}: deixe {pessoa} e use {nova}.",
        "No caso do {objeto}, o participante vigente passa a ser {nova}, no lugar de {pessoa}.",
    ),
    "guardar_hipotese": (
        "Estou considerando {atividade}, com {objeto} envolvido, mas isso segue incerto. Posso chamar de confirmado?",
        "{atividade} é só uma possibilidade no caso de {pessoa}. Já virou fato?",
        "Ainda não decidi sobre {atividade}; o {objeto} continua no contexto. Isso deve ser tratado como certeza?",
        "A ideia de {atividade} ligada a {pessoa} continua provisória. Está confirmada?",
    ),
    "mensagem_sem_horario": (
        "Escreva para {pessoa} propondo {atividade}; mantenha o horário totalmente em aberto.",
        "Formule um convite a {pessoa} para {atividade}, no contexto do {objeto}, sem inventar quando.",
        "Prepare uma mensagem curta para {pessoa} sobre {atividade}, sem marcar hora.",
        "Convide {pessoa} para fazer {atividade} comigo; o {objeto} é só contexto, não acrescente horário.",
    ),
    "pedir_detalhe": (
        "Quero solicitar algo a {pessoa} durante {atividade}, mas ainda não informei qual item.",
        "O destinatário do pedido é {pessoa}; no contexto de {atividade}, falta especificar a coisa pedida.",
        "Há um pedido para {pessoa}, porém o objeto do pedido não foi dito; {objeto} é apenas o item já registrado.",
        "Vou pedir alguma coisa a {pessoa} depois de {atividade}; antes preciso dizer exatamente o quê.",
    ),
}
RESPOSTAS = {
    "recordar_pessoa": "Considere {pessoa} como a pessoa atual.",
    "recordar_objeto": "O item vigente é {objeto}.",
    "corrigir_pessoa": "Atualização feita: agora a pessoa é {nova}.",
    "guardar_hipotese": "{atividade} continua provisória; ainda não é confirmação.",
    "mensagem_sem_horario": "{pessoa}, você gostaria de combinar {atividade} comigo?",
    "pedir_detalhe": "Qual item você pretende pedir a {pessoa}?",
}

def gerar():
    exemplos=[]
    for fi,(familia,obj0,ativ0,pbase,nbase) in enumerate(FAMILIAS):
        for variante in range(4):
            objeto = obj0 if variante == 0 else OBJETOS_EXTRA[(fi*2+variante-1)%len(OBJETOS_EXTRA)]
            atividade = ativ0 if variante == 0 else ATIVIDADES_EXTRA[(fi*2+variante-1)%len(ATIVIDADES_EXTRA)]
            pessoa = f"{pbase}-{121 + fi*111 + variante*7}"
            nova = f"{nbase}-{232 + fi*111 + variante*7}"
            historico=[
                {"papel":"usuario","texto":f"Estado inicial no {familia}: pessoa={pessoa}; objeto={objeto}; atividade={atividade}."},
                {"papel":"assistente","texto":"Entendido. Vou manter separados pessoa, objeto e atividade desse estado."},
            ]
            ordem=ORDENS[variante]
            for turno,op in enumerate(ordem,1):
                estilo=(fi+variante+turno)%4
                msg=("Neste contexto de "+familia+", "+PERGUNTAS[op][estilo].format(
                    pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade))
                resp=RESPOSTAS[op].format(pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade)
                exemplos.append({
                    "id":f"esc17m-bind-{fi}-{variante}-{turno}",
                    "familia":familia,"variante":variante,"turno":turno,
                    "historico":[dict(x) for x in historico],"mensagem":msg,"resposta":resp,"operacao":op,
                })
                historico.extend([{"papel":"usuario","texto":msg},{"papel":"assistente","texto":resp}])
                if op=="corrigir_pessoa": pessoa=nova
    assert len(exemplos)==120
    assert len({x["id"] for x in exemplos})==120
    assert len({x["mensagem"] for x in exemplos})==120
    assert {op:sum(x["operacao"]==op for x in exemplos) for op in OPERACOES} == {op:20 for op in OPERACOES}
    return exemplos

if __name__=="__main__":
    import json
    print(json.dumps(gerar(),ensure_ascii=False,indent=2))
