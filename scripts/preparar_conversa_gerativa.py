"""SFT de conversa: humanos revisados e exercícios autorais, sem pesos externos.

Reutiliza exclusivamente o tokenizer do Transformer próprio. Partições humanas
permanecem por árvore; exercícios de transferência separam entidades. Texto
autoral é sintético, inclusive quando preparado pelo assistente, e não é humano.
As sondas de avaliação nunca são lidas por este preparador.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from linguagem_profunda import codificar_texto
from scripts.preparar_linguagem_profunda import (
    selecionar_humanos, janelas_dialogo, escrever_jsonl, normalizar, sha)


# Cada linha ensina uma relação ou uma decisão de conversa, não um ID de resposta.
# Estas demonstrações são dados supervisionados, nunca usadas como tabela no chat.
DIALOGOS = [
 ("Minha amiga não respondeu à minha mensagem.", "Pode ser frustrante esperar. O silêncio sozinho não revela o motivo: ela pode estar ocupada ou precisar de tempo. Há quanto tempo você mandou a mensagem?"),
 ("Mandei um convite e minha colega ficou sem responder.", "Ainda não sabemos se ela viu o convite. Você pode esperar um pouco e depois confirmar se ela recebeu, sem concluir que a falta de resposta foi uma rejeição."),
 ("Ele leu o que mandei, mas ficou quieto.", "Ler uma mensagem não garante que a pessoa tenha tempo ou saiba como responder. Isso te deixou mais triste, preocupado ou irritado?"),
 ("Acho que ninguém gosta de mim porque uma pessoa não me respondeu.", "Uma pessoa ficar sem responder não prova que ninguém gosta de você. O que sabemos é que uma resposta não veio; o motivo continua desconhecido."),
 ("Estou decepcionado porque você repete a mesma coisa.", "Você esperava uma resposta que considerasse o que disse. Vou partir do problema específico e explicar o que consigo concluir, em vez de repetir uma frase genérica."),
 ("Essa resposta não faz sentido.", "Vamos localizar o erro. Qual parte contradiz o que você perguntou? Se você indicar o trecho, posso rever a explicação e separar o que sabemos do que foi uma suposição."),
 ("Estou perdido no que estou estudando.", "Escolha uma parte pequena e tente explicá-la com suas próprias palavras. Depois resolva um exemplo e identifique o ponto em que travou. Qual assunto você está estudando?"),
 ("Leio a matéria e logo esqueço tudo.", "Depois de ler um trecho, feche o material e tente lembrar a ideia principal. Faça uma pergunta sobre o trecho e responda sem olhar. Retome depois os pontos que esqueceu."),
 ("Como consigo aprender em vez de só decorar?", "Procure a relação entre as ideias: para que algo serve, como funciona e o que mudaria se fosse diferente. Use um exemplo concreto e explique com suas palavras; isso revela as lacunas."),
 ("Quero aprender programação, mas não sei por onde começar.", "Comece com variáveis, condições e funções, aplicando cada ideia em um programa pequeno. Por exemplo, calcule um preço e depois adicione uma condição de desconto. Qual linguagem você quer estudar?"),
 ("Tenho duas opções e não consigo escolher.", "Podemos comparar as opções pelo que importa para você: custo, tempo, risco e objetivo. Quais são as duas opções e qual resultado você quer alcançar?"),
 ("Será que vale a pena mudar de plano?", "Depende do que o plano atual entrega e do que a mudança custa. O que não está funcionando hoje e o que você espera ganhar com a alternativa?"),
 ("Você pode pensar comigo sobre uma ideia?", "Conte a ideia e o problema que ela tenta resolver. Podemos examinar as suposições, imaginar alternativas e escolher uma forma pequena de testar se funciona."),
 ("Me dá uma certeza sobre o que ela está pensando.", "Não tenho acesso aos pensamentos dela. Podemos examinar o que ela disse ou fez e considerar possibilidades, mas isso não oferece certeza sobre o motivo."),
 ("Por que uma pessoa que eu não conheço tomou essa decisão?", "Não tenho informações suficientes para saber o motivo dessa pessoa. Se você descrever a situação e as evidências disponíveis, podemos distinguir fatos de hipóteses."),
 ("Se ele perdeu o celular, então ele me ignorou de propósito?", "Não. Perder o celular pode impedir uma resposta sem intenção de ignorar. Essa hipótese explica o silêncio de outra maneira, mas ainda precisa ser confirmada."),
 ("A pessoa atrasou. Isso quer dizer que não se importa?", "O atraso sozinho não mostra se ela se importa. Pode haver um imprevisto ou outro motivo. Podemos verificar se foi um caso isolado e como ela explicou o atraso."),
 ("O que você sabe sobre mim?", "Sei apenas o que você informou nesta conversa. Não devo inventar sua idade, sua profissão ou sua história. Você pode corrigir qualquer informação que eu interpretar errado."),
 ("Você tem sentimentos?", "Não tenho sentimentos ou experiências pessoais. Posso conversar sobre o que você sente e ajudar a organizar as ideias, considerando o que você me conta."),
 ("Não quero conselho agora, só quero conversar.", "Tudo bem. Podemos conversar sobre o que aconteceu sem transformar isso em uma lista de tarefas. Qual parte está mais presente na sua cabeça?"),
 ("Isso era só uma hipótese, não aconteceu comigo.", "Entendi: era uma situação imaginada. Vou tratá-la como hipótese e não registrar isso como algo que aconteceu com você."),
 ("Você respondeu outra coisa; eu perguntei para que serve.", "Você quer entender a função, não apenas o nome ou a definição. Vamos relacionar o que isso faz com o resultado que produz."),
 ("Pode explicar de um jeito menos técnico?", "Posso explicar com palavras mais simples e um exemplo. Qual parte da explicação ficou difícil?"),
 ("Quero criar algo, mas só tenho uma ideia vaga.", "Podemos começar pelo objetivo: quem usaria isso e qual problema resolveria? Depois pensamos em uma versão pequena que dê para testar antes de aumentar o projeto."),
]

FATOS = [
 ("mitocôndria", "produzir ATP durante a respiração celular", "fornecer energia utilizável para atividades da célula", "OpenStax Biology 2e, 4.3 e 7.2"),
 ("ribossomo", "montar proteínas a partir de aminoácidos", "produzir proteínas que atuam na estrutura e nas funções celulares", "OpenStax Biology 2e, 4.3"),
 ("membrana plasmática", "controlar a passagem de substâncias entre a célula e o ambiente", "regular as trocas e preservar condições internas", "OpenStax Biology 2e, 5"),
 ("núcleo celular", "armazenar o DNA e participar do controle da expressão dos genes", "organizar informações genéticas usadas pela célula", "OpenStax Biology 2e, 4.3"),
 ("cloroplasto", "realizar a fotossíntese usando energia luminosa", "produzir açúcares a partir de água e gás carbônico", "OpenStax Biology 2e, 8"),
 ("lisossomo", "degradar materiais por meio de enzimas", "reciclar componentes e digerir materiais na célula", "OpenStax Biology 2e, 4.3"),
 ("raiz", "absorver água e sais minerais do solo", "sustentar o crescimento e fixar a planta", "OpenStax Biology 2e, 30.3"),
 ("coração", "bombear sangue pelos vasos", "distribuir oxigênio e nutrientes pelo organismo", "OpenStax Biology 2e, 40"),
 ("pulmão", "realizar trocas de gases com o sangue", "obter oxigênio e eliminar gás carbônico", "OpenStax Biology 2e, 39"),
 ("rim", "filtrar o sangue e regular água e sais", "remover resíduos e manter o equilíbrio do organismo", "OpenStax Biology 2e, 41"),
 ("variável", "associar um nome a um valor", "usar e atualizar valores em um programa", "MDN JavaScript Guide, Grammar and types"),
 ("função", "reunir instruções que podem receber argumentos e retornar um resultado", "reutilizar uma operação e organizar o programa", "MDN JavaScript Guide, Functions"),
 ("condição", "selecionar uma ação conforme uma expressão verdadeira ou falsa", "adaptar o comportamento do programa aos dados", "MDN JavaScript Guide, Control flow"),
 ("teste automatizado", "executar verificações de comportamento", "encontrar regressões ao alterar o código", "Documentação Node.js, Test runner"),
 ("fila", "retirar primeiro os elementos inseridos primeiro", "processar pedidos respeitando a ordem de chegada", "Open Data Structures, Queues"),
 ("pilha", "retirar primeiro o último elemento inserido", "organizar ações que precisam ser desfeitas na ordem inversa", "Open Data Structures, Stacks"),
]


def exemplos_autorais():
    itens = []
    def add(q, a, familia, grupo, split='treino', historico=()):
        itens.append(dict(mensagem=q, resposta=a, historico=list(historico),
            familia=familia, grupo=grupo, split=split, origem='sintetico_autoral_assistente'))
    for i, (q, a) in enumerate(DIALOGOS):
        add(q, a, 'conversa', 'conversa_%d' % i)
        for prefixo in ('Ei, ', 'Estou pensando nisso: ', 'Quero conversar. '):
            add(prefixo + q[0].lower() + q[1:], a, 'conversa', 'conversa_%d' % i)
    formas = ['Para que serve {e}?', 'Que função tem {e}?', 'Como {e} ajuda o sistema?',
              'Me explique a utilidade de {e}.', 'Qual resultado {e} permite obter?']
    for i, (e, f, r, fonte) in enumerate(FATOS):
        evidencia = f'Informação: {e} tem a função de {f}. Isso permite {r}.'
        respostas = [f'A função de {e} é {f}. Com isso, ajuda a {r}.',
                     f'{e[0].upper()+e[1:]} ajuda a {r}, porque atua para {f}.']
        for forma in formas:
            for a in respostas:
                add(forma.format(e=e), a, 'funcao', 'fato_'+e)
                add(evidencia+'\nPergunta: '+forma.format(e=e), a, 'evidencia', 'fato_'+e)
        h=[dict(papel='usuario',texto=f'Estou estudando {e}.'),
           dict(papel='assistente',texto=evidencia)]
        add('Como verifico se entendi?', f'Tente explicar por que {e} ajuda a {r}. Depois dê um exemplo da função de {f}, sem olhar a explicação.', 'contexto', 'fato_'+e, historico=h)
        add('Agora explique mais simplesmente.', f'{e[0].upper()+e[1:]} faz uma parte do trabalho: ajuda a {r}. A ideia principal é essa função.', 'contexto', 'fato_'+e, historico=h)
        add('E qual era a função mesmo?', f'A função de {e} é {f}.', 'contexto', 'fato_'+e, historico=h)
    # Transferência: nomes, fatos e relações inéditos em cada partição.
    # Um alvo completo não atravessa partições; resposta depende da evidência.
    verbos=[('guardar arquivos','recuperar arquivos'),('receber mensagens','receber mensagens'),
            ('medir temperatura','medir temperatura'),('calcular custos','calcular custos'),
            ('registrar eventos','consultar eventos'),('organizar pedidos','organizar pedidos')]
    rng=random.Random(20261004)
    for n in range(120):
        split='treino' if n<90 else 'validacao' if n<105 else 'teste'
        a,b='Ramo'+str(n),'Eixo'+str(n)
        for i,(f,r) in enumerate(verbos):
            outra=verbos[(i+1)%len(verbos)][0]
            info=f'O componente {a} serve para {f}. O componente {b} serve para {outra}.'
            for j,q in enumerate((f'Qual componente uso para {r}?',f'Quem tem a função de {f}?',f'Explique o papel de {a}.')):
                resposta=f'O componente {a} tem a função de {f}.'
                if rng.randrange(2): info=f'O componente {b} serve para {outra}. O componente {a} serve para {f}.'
                add('Considere esta informação: '+info+'\n'+q, resposta, 'transferencia', 'componentes_%d'%n, split)
    nomes=['Lia','Rui','Bia','Davi','Ivo','Lara','Caio','Mila','Nina','Téo','Eva','Otto','Cora','Hugo','Rita']
    for i,nome in enumerate(nomes):
        split='treino' if i<11 else 'validacao' if i<13 else 'teste'
        for animal in ('gato','cachorro','coelho'):
            h=[dict(papel='usuario',texto=f'Meu {animal} se chama {nome}.'),dict(papel='assistente',texto=f'Você disse que seu {animal} se chama {nome}.')]
            add('Como ele se chama?', f'Seu {animal} se chama {nome}.', 'memoria', 'nome_'+nome, split,h)
            add('Qual animal eu mencionei?',f'Você mencionou seu {animal}.','memoria','nome_'+nome,split,h)
            add('Era só um exemplo imaginário.', 'Entendi. Esse animal era parte de um exemplo, não uma informação sobre sua vida.', 'hipotese','nome_'+nome,split,h)
            add('Não escreva nada para ele. Só analise a situação.', 'Vou apenas analisar, sem escrever uma mensagem. Primeiro precisamos separar o que foi informado do que ainda é uma hipótese.', 'restricao','nome_'+nome,split,h)
    # Correção e negacão em contexto: não completar pelo turno anterior.
    for sujeito in ('amigo','irmão','colega','vizinho'):
        h=[dict(papel='usuario',texto='Minha amiga ficou sem responder.'),dict(papel='assistente',texto='Há quanto tempo você espera a resposta dela?')]
        add(f'Corrigindo: foi meu {sujeito}.',f'Entendi: quem não respondeu foi seu {sujeito}. O motivo ainda não está confirmado.', 'correcao', 'correcao_'+sujeito,historico=h)
        add('Não quero enviar mensagem. Quero pensar nos motivos.', 'Podemos pensar em possibilidades sem escrever uma mensagem: falta de tempo, um imprevisto ou dificuldade de responder. Nenhuma delas está confirmada.', 'restricao', 'restricao_'+sujeito,historico=h)
    return itens


def preparar(saida, oasst2, tokenizer_path, wikipedia=None, documentos=20000,
             dialogos_amplos=False, oasst2_completo=None, contexto=256):
    import numpy as np
    from tokenizers import Tokenizer
    out=Path(saida);out.mkdir(parents=True,exist_ok=True)
    tokenizer=Tokenizer.from_file(str(tokenizer_path));tokenizer.encode_special_tokens=True
    if contexto < 16 or contexto > 2048:
        raise ValueError('Contexto inválido')
    if dialogos_amplos:
        if oasst2_completo is None:
            raise ValueError('Diálogos amplos exigem a exportação humana completa verificada')
        from scripts.curar_oasst2_completo import selecionar_completo
        from scripts.curriculo_dialogos_amplos import exemplos_amplos
        humanos,recusas=selecionar_completo(oasst2,oasst2_completo)
        autorais=list(exemplos_amplos())
    else:
        humanos,recusas=selecionar_humanos(oasst2)
        autorais=exemplos_autorais()
    for e in humanos: e['familia']='humano'
    exemplos=humanos+autorais
    antes_filtros=len(exemplos)
    # Reservas globais dos alvos: exclui targets sintéticos que atravessam split.
    splits={}
    for e in exemplos: splits.setdefault(normalizar(e['resposta']),set()).add(e['split'])
    exemplos=[e for e in exemplos if len(splits[normalizar(e['resposta'])])==1]
    manifest=dict(versao=2 if dialogos_amplos else 1,contexto=contexto,vocabulario=tokenizer.get_vocab_size(),
        preparador_sha256=sha(Path(__file__)),peso_externo=False,
        tokenizer_reutilizado_proprio=True,particoes={},
        oasst2=dict(sha256=sha(oasst2),revisao='179dd21fc55192153d94adb0e0ce8f69e222bf75',licenca='Apache-2.0',recusas=recusas),
        sintetico='Demonstrações autorais preparadas pelo assistente; não são diálogos humanos.',
        fontes_fatos=sorted(set(f[3] for f in FATOS)),
        limites=['Currículo pequeno e em parte sistemático; não representa conversa aberta.',
                 'Métricas sintéticas devem ser separadas de métricas humanas.',
                 'A sonda não é lida pelo preparador e não seleciona checkpoints.'])
    if dialogos_amplos:
        from scripts.baixar_fontes_linguagem import FONTES
        from linguagem_profunda import segmentos_dialogo
        from scripts.curriculo_dialogos_amplos import ARQUIVO
        from scripts.curar_oasst2_completo import RECUSAS_CONTEUDO
        # Não supervisionar inferências autorais cujo contexto necessário não
        # cabe no modelo. Humanos longos conservam as janelas mascaradas originais.
        limpos=[]; contextos_recusados=0
        for e in exemplos:
            if e['origem'] != 'humano_oasst2':
                seg,atual=segmentos_dialogo(tokenizer,e['mensagem'],e.get('historico',[]))
                tamanho=sum(map(len,seg))+len(atual)+len(codificar_texto(tokenizer,e['resposta']))+1
                if tamanho > contexto+1:
                    contextos_recusados+=1
                    continue
            limpos.append(e)
        exemplos=limpos
        # A mesma entrada e contexto não podem aparecer em partições distintas.
        fontes={}
        def chave_fonte(e):
            return tuple(normalizar(h['texto']) for h in e.get('historico',[]))+(normalizar(e['mensagem']),)
        for e in exemplos: fontes.setdefault(chave_fonte(e),set()).add(e['split'])
        exemplos=[e for e in exemplos if len(fontes[chave_fonte(e)])==1]
        manifest.update(oasst2_completo=dict(FONTES['oasst2_completo']),
            amostragem_dialogo=dict(fracao_humana=0.75,pares_uniformes=True,sinteticos_por_familia=True),
            dependencias_sha256={str(p.relative_to(ROOT)):sha(p) for p in (
                ARQUIVO, ROOT/'scripts/curriculo_dialogos_amplos.py',
                ROOT/'scripts/curar_oasst2_completo.py', ROOT/'scripts/curar_dialogos_humanos.py',
                ROOT/'scripts/preparar_linguagem_profunda.py')},
            curadoria_adicional=RECUSAS_CONTEUDO,
            filtros=dict(candidatos=antes_filtros,autorais_contexto_incompleto=contextos_recusados,
                         pares_apos_filtros=len(exemplos)),
            limites=['Humanos têm autoria/revisão conforme os rótulos públicos; não há verificação independente de todos os fatos.',
                     'Exercícios calculados e conversas autorais são sintéticos, não novos interlocutores humanos.',
                     'Contexto maior ainda é limitado; não cria memória persistente nem prova compreensão.',
                     'A sonda não é lida pelo preparador e não seleciona checkpoints.'])
    docs=[]
    if wikipedia:
        from scripts.baixar_fontes_linguagem import FONTES
        from scripts.preparar_linguagem_profunda import selecionar_wikipedia
        if sha(wikipedia)!=FONTES['wikipedia']['sha256']:
            raise ValueError('Wikipedia difere da revisão pública fixada')
        docs,contagens=selecionar_wikipedia(wikipedia,documentos)
        manifest['wikipedia']=dict(FONTES['wikipedia'],contagens=contagens)
    shutil.copyfile(tokenizer_path,out/'tokenizer.json')
    familias={f:i for i,f in enumerate(sorted({e['familia'] for e in exemplos}))}
    for split in ('treino','validacao','teste'):
        es=[e for e in exemplos if e['split']==split]
        escrever_jsonl(out/f'dialogos_{split}.jsonl',es)
        xs,ys,origens,fs,pares=[],[],[],[],[]
        descartados_janelas=0
        for par,e in enumerate(es):
            janelas=janelas_dialogo(tokenizer,e,contexto)
            if not janelas: descartados_janelas+=1
            for x,y in janelas:
                xs.append(x+[0]*(contexto-len(x)));ys.append(y+[-100]*(contexto-len(y)))
                pares.append(par)
                origens.append(int(e['origem']=='humano_oasst2'));fs.append(familias[e['familia']])
        x=np.asarray(xs,dtype=np.int32).reshape(-1,contexto);y=np.asarray(ys,dtype=np.int32).reshape(-1,contexto)
        for nome,a in [('x',x),('y',y),('origem',np.asarray(origens,dtype=np.int8)),('familia',np.asarray(fs,dtype=np.int16))]:
            np.save(out/f'dialogo_{split}_{nome}.npy',a)
        if dialogos_amplos:
            np.save(out/f'dialogo_{split}_par.npy',np.asarray(pares,dtype=np.int32))
        # Replay somente desta partição: não reutiliza reservados como treino.
        ids=[]
        for e in es:
            ids.extend([tokenizer.token_to_id('<documento>')]+codificar_texto(tokenizer,e['resposta'])+[tokenizer.token_to_id('<fim>')])
        ds=[d for d in docs if d['split']==split]
        escrever_jsonl(out/f'documentos_{split}.jsonl',ds)
        with (out/f'linguagem_{split}.bin').open('wb') as f:
            np.asarray(ids,dtype='<u2').tofile(f)
            for d in ds:
                seq=[tokenizer.token_to_id('<documento>')]+codificar_texto(tokenizer,d['texto'])+[tokenizer.token_to_id('<fim>')]
                np.asarray(seq,dtype='<u2').tofile(f)
        manifest['particoes'][split]=dict(pares=len(es),humanos=sum(e['origem']=='humano_oasst2' for e in es),
            grupos=len({e['grupo'] for e in es}),janelas=len(x),tokens_alvo=int((y!=-100).sum()),familias=familias,
            sinteticos=sum(e['origem']!='humano_oasst2' for e in es),
            com_historico=sum(bool(e.get('historico')) for e in es),
            descartados_janelas=descartados_janelas,
            familias_contagens={f:sum(e['familia']==f for e in es) for f in familias},
            humanos_exportacao_completa=sum(e.get('fonte_exportacao')=='completa' for e in es),
            documentos=len(ds),tokens_linguagem=(out/f'linguagem_{split}.bin').stat().st_size//2)
    manifest['arquivos']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifesto.json'}
    (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest['particoes'],ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True);p.add_argument('--oasst2',required=True)
    p.add_argument('--tokenizer',default=str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'))
    p.add_argument('--dialogos-amplos',action='store_true')
    p.add_argument('--oasst2-completo')
    p.add_argument('--contexto',type=int,default=256)
    p.add_argument('--wikipedia');p.add_argument('--documentos',type=int,default=20000)
    a=p.parse_args();preparar(a.saida,a.oasst2,a.tokenizer,a.wikipedia,a.documentos,
                             a.dialogos_amplos,a.oasst2_completo,a.contexto)
