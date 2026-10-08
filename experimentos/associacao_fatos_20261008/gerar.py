"""Novo painel autoral sintético: relações variadas, sem ler o teste anterior.

Os três bancos de declaração/pergunta são separados antes do treino. Não são
conversas humanas nem uma avaliação independente. Gramática fechada continua
ajudando a seleção de spans completos na variante limitada.
"""
import argparse
import random
import json
from pathlib import Path
from comum import ROOT, ANTERIOR, sha, escrever
from corpus import Sessao
from modelo import codificar, recuperar, esperado
from tokenizers import Tokenizer

BANCOS = {
 'treino': {
 'preco': ['O plano {n} custa {v} reais. ', 'Para {n}, o valor é {v} reais. ',
           '{n}: preço de {v} reais. ', '{v} reais é o custo de {n}. ',
           'O preço cobrado por {n} é {v} reais. ', '{n} fica por {v} reais. '],
 'corrigir': ['O preço de {n} estava errado: agora é {v} reais. ',
              'Corrigindo {n}: o custo real é {v} reais. ',
              '{n} foi atualizado para {v} reais. ',
              'O valor anterior de {n} foi substituído por {v} reais. '],
 'hipotese': ['Só numa hipótese, {n} custaria {v} reais. ',
              'Imagine {n} por {v} reais, sem alterar a realidade. ',
              'Se {n} custasse {v} reais, como simulação, ',
              'No cenário fictício, o preço de {n} é {v} reais. '],
 'voltar': ['Esqueça a hipótese e use os preços reais. ',
            'A simulação terminou; retome os valores reais. ',
            'Nada do cenário fictício ocorreu. Volte ao caso real. '],
 'pergunta': ['Compare {a} e {b}.', 'Qual custa menos: {a} ou {b}?',
              'Entre {a} e {b}, qual economiza e quanto?',
              'Qual a diferença de preço entre {a} e {b}?'],
 'regra': ['Para entrar são exigidos {v}. ', 'Nesta porta são requeridos {v}. ',
           'Na entrada, os objetos exigidos são {v}. ',
           'Os itens requeridos para entrar são {v}. '],
 'inventario': ['{n} {v}. ', 'Sobre {n}: {v}. ', 'A pessoa {n} {v}. ',
                'Inventário de {n}: {v}. '],
 'alteracao': ['Atualizando os objetos de {n}: agora {v}. ',
               'Corrijo o inventário de {n}: {v}. ',
               'A situação real de {n} mudou: {v}. '],
 'inventario_hip': ['Só na hipótese, {n} {v}. ',
                    'Imagine, sem mudar os fatos, que {n} {v}. ',
                    'No cenário fictício, {n} {v}. '],
 'voltar_regra': ['A hipótese não aconteceu. Use o inventário real. ',
                  'Desfaça a simulação; os objetos reais não mudaram. '],
 'pergunta_regra': ['{n} cumpre os requisitos?', 'Pela regra, {n} pode entrar?',
                    'O inventário de {n} satisfaz a regra?'],
 },
 'dev': {
 'preco': ['A mensalidade de {n} é {v} reais. ', 'Por {n}, paga-se {v} reais. '],
 'corrigir': ['Retifique a cobrança de {n} para {v} reais. ',
              'O preço real correto para {n} passa a ser {v} reais. '],
 'hipotese': ['Vamos supor {n} a {v} reais; isso não é fato. ',
              'Numa situação imaginária, {n} sairia por {v} reais. '],
 'voltar': ['Saia da situação imaginária e considere a cobrança real. ',
            'A suposição foi descartada; mantenha a correção real. '],
 'pergunta': ['Entre {a} e {b}, qual tem menor cobrança?',
              'Quanto separa os valores de {a} e {b}?'],
 'regra': ['Na porta, estão exigidos {v}. ', 'Para o ingresso são requeridos {v}. '],
 'inventario': ['Quanto a {n}, {v}. ', '{n}, neste momento, {v}. '],
 'alteracao': ['O inventário real correto de {n}: {v}. ',
               'Atualize o caso real: {n} {v}. '],
 'inventario_hip': ['Numa suposição, {n} {v}. ',
                    'Na situação imaginária, {n} {v}. '],
 'voltar_regra': ['Retome os itens reais, descartando a suposição. '],
 'pergunta_regra': ['{n} atende às exigências?', 'As condições permitem que {n} ingresse?'],
 },
 'teste': {
 'preco': ['{n} sai por {v} reais. ', 'Para contratar {n}, desembolso {v} reais. ',
           'No caso de {n}, cobram {v} reais. '],
 'corrigir': ['Eu me enganei sobre {n}: o valor certo é {v} reais. ',
              'Mude apenas a cobrança real de {n} para {v} reais. ',
              '{n} teve o preço retificado: {v} reais. '],
 'hipotese': ['Faça de conta que {n} vale {v} reais; é só simulação. ',
              'Considere provisoriamente {n} por {v} reais, num cenário hipotético. ',
              'E se {n} passasse a {v} reais? É uma suposição. '],
 'voltar': ['Chega de faz de conta: recupere os preços corrigidos de verdade. ',
            'Encerre o cenário hipotético e calcule com o caso factual. '],
 'pergunta': ['Qual cobra menos, {a} ou {b}, e por quanto?',
              'Ao comparar {a} com {b}, qual é a economia?',
              'Escolhendo entre {a} e {b}, qual tem o menor preço?'],
 'regra': ['Para ter acesso são exigidos {v}. ',
           'Os objetos requeridos nesse acesso são {v}. '],
 'inventario': ['No caso de {n}, {v}. ', 'O registro diz que {n} {v}. '],
 'alteracao': ['Substitua o registro real de {n}: {v}. ',
               'Os fatos corrigidos sobre {n}: {v}. '],
 'inventario_hip': ['Faça de conta que {n} {v}, só na simulação. ',
                    'E se {n} {v}? Isso é hipotético. '],
 'voltar_regra': ['Encerre o faz de conta e considere os objetos de verdade. '],
 'pergunta_regra': ['Com esses fatos, {n} consegue ingressar?',
                    'As exigências de acesso são cumpridas por {n}?'],
 },
}
OPCOES = {
 'treino': ['Azul','Verde','Rosa','Cinza','Cobre','Ouro','Básico','Plus','Leste','Oeste','Sol','Lua','Mar','Rio','Trilha','Brisa'],
 'dev': ['Âmbar','Violeta','Norte','Sul','Pedra','Nuvem'],
 'teste': ['Safira','Jade','Coral','Prata','Vento','Serra','Lago','Campo'],
}
PESSOAS = {'treino':['Ana','Beto','Caio','Dora','Iara','Rui','Lia','Leo'],
           'dev':['Vera','Tito','Lena','Bruno'], 'teste':['Nair','Zeca','Mila','Davi']}
OBJETOS = {'treino':['chave','selo','ticket','senha','mapa','cartão','ficha','medalha'],
           'dev':['convite','pulseira','crachá','documento'],
           'teste':['licença','insígnia','bilhete','emblema']}

def partes(formato, **campos):
    """Suportes são anotados fora do texto; formato não vê rótulos."""
    import re
    out=[];ultimo=0
    for m in re.finditer(r'\{([a-z]+)\}',formato):
        out.append(formato[ultimo:m.start()]);out.append((m[1],str(campos[m[1]])));ultimo=m.end()
    out.append(formato[ultimo:]);return out

def construir(split, indice):
    rng=random.Random({'treino':61231,'dev':78143,'teste':91387}[split]+indice*65537)
    b=BANCOS[split];s=Sessao(f'assoc-{split}-{indice}', 'precos_nomeados' if indice%2==0 else 'requisitos_variados',split)
    pick=lambda k:rng.choice(b[k])
    out=[]
    if indice%2==0:
        nomes=rng.sample(OPCOES[split],3)
        valores=rng.sample(range(12,180) if split!='teste' else range(181,350),5)
        ordem=rng.sample([0,1],2);orig={}
        texto=[]
        for i in ordem:
            template=pick('preco')
            # Chaves distintas dentro do mesmo turno.
            texto+=partes(template.replace('{n}',f'{{n{chr(97+i)}}}').replace('{v}',f'{{v{chr(97+i)}}}'),
                          **{f'n{chr(97+i)}':nomes[i],f'v{chr(97+i)}':valores[i]})
        if rng.random()<.5: texto+=['A entrega leva ',('distrator',str(valores[4])),' dias. ']
        else: texto+=partes(pick('preco'),n=nomes[2],v=valores[4])
        pergunta=lambda:pick('pergunta').format(a=nomes[0],b=nomes[1])
        texto+=[pergunta()];a=s.fala(texto);real=[a['va'],a['vb']]
        out.append(s.exemplo('comparar_custos',real))
        corrigido=rng.randrange(2)
        c=s.fala(partes(pick('corrigir'),n=nomes[corrigido],v=valores[2])+[pergunta()]);real[corrigido]=c['v']
        out.append(s.exemplo('comparar_custos',real))
        imaginado=rng.randrange(2)
        h=s.fala(partes(pick('hipotese'),n=nomes[imaginado],v=valores[3])+[pergunta()]);virtual=list(real);virtual[imaginado]=h['v']
        out.append(s.exemplo('comparar_custos',virtual,hipotese=True))
        s.fala([pick('voltar'),pergunta()]);out.append(s.exemplo('comparar_custos',real))
    else:
        n,outra=rng.sample(PESSOAS[split],2);x,y,z=rng.sample(OBJETOS[split],3)
        itens=rng.sample([x,y],2);regra=' e '.join(itens)
        # As quatro situações são equilibradas por rotação de cenário.
        inventarios=[f'tem {x} e {y}',f'tem {x} e não tem {y}',f'tem {x}',f'tem {x} e não tem {x}']
        shift=(indice//2)%4;inicial=inventarios[shift];novo=inventarios[(shift+1)%4];hip=inventarios[(shift+2)%4]
        q=lambda:pick('pergunta_regra').format(n=n)
        # Outra pessoa e um objeto irrelevante tornam o vínculo necessário.
        p1=partes(pick('regra'),v=regra);p2=partes(pick('inventario'),n=n,v=inicial)
        if rng.random()<.5:
            texto=partes(pick('inventario'),n=outra,v=f'tem {z}')+p1+p2
        else:
            texto=p1+p2+partes(pick('inventario').replace('{n}','{d}').replace('{v}','{w}'),d=outra,w=f'tem {z}')
        # Evitar sobrescrever suportes da pessoa alvo com os do distrator.
        if any(isinstance(p,tuple) and p[0]=='n' and p[1]==outra for p in texto):
            texto=[('d',p[1]) if isinstance(p,tuple) and p[0]=='n' and p[1]==outra else
                   ('w',p[1]) if isinstance(p,tuple) and p[0]=='v' and p[1]==f'tem {z}' else p for p in texto]
        # v da regra é renomeado antes de combinar.
        seen=False
        for j,p in enumerate(texto):
            if isinstance(p,tuple) and p[0]=='v' and p[1]==regra:
                texto[j]=('regra',p[1]);seen=True
        assert seen
        a=s.fala(texto+[q()]);out.append(s.exemplo('verificar_requisitos',[a['regra'],a['v']],a['n']))
        c=s.fala(partes(pick('alteracao'),n=n,v=novo)+[q()]);out.append(s.exemplo('verificar_requisitos',[a['regra'],c['v']],a['n']))
        h=s.fala(partes(pick('inventario_hip'),n=n,v=hip)+[q()]);out.append(s.exemplo('verificar_requisitos',[a['regra'],h['v']],a['n'],True))
        s.fala([pick('voltar_regra'),q()]);out.append(s.exemplo('verificar_requisitos',[a['regra'],c['v']],a['n']))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('saida',type=Path);args=p.parse_args()
    args.saida.mkdir(parents=True,exist_ok=False)
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    dados={};stats={};vistos=set()
    for split,quantidade in [('treino',4000),('dev',300),('teste',400)]:
        items=[];indice=0;rejeitados=0;comprimentos=[]
        while len(items)<quantidade:
            es=construir(split,indice);indice+=1
            keys=[json.dumps(e['turnos'],ensure_ascii=False) for e in es]
            try: cs=[codificar(tok,e) for e in es]
            except ValueError:
                rejeitados+=1;continue
            if any(k in vistos for k in keys):rejeitados+=1;continue
            for e,c in zip(es,cs):
                for span,(inicio,fim) in zip(e['argumentos']+[e['referente']],zip(c['pontos'][::2],c['pontos'][1::2])):
                    rec=recuperar(c,inicio,fim)
                    if span is not None: assert rec and not rec.get('invalido') and rec['texto']==span['texto']
                assert esperado(e)['executavel']
                comprimentos.append(len(c['ids']))
            vistos.update(keys);items+=es
        escrever(args.saida/(split+'.json'),items)
        dados[split]=items;stats[split]={'exemplos':len(items),'sessoes':len(items)//4,'max_tokens':max(comprimentos),'tokens':sum(comprimentos),'rejeitados_contexto_ou_repeticao':rejeitados}
    # Repetição de treino anterior conserva domínios; não lê o teste anterior.
    anterior=json.loads((ANTERIOR/'dados/treino.json').read_text())
    rng=random.Random(13171);replay=rng.sample(anterior,1000)
    escrever(args.saida/'replay.json',replay)
    escrever(args.saida/'manifesto.json',{'sha256':{s:sha(args.saida/(s+'.json')) for s in ['treino','dev','teste','replay']},'estatisticas':stats,
        'gerador_sha256':sha(__file__),'fontes':'Sintético autoral; nenhum dado privado ou modelo externo.',
        'formas_declaracao_separadas':True,'tokenizer_sha256':sha(ROOT/'artefatos/linguagem_profunda/tokenizer.json'),
        'limites':'Bancos separados, mas mesma gramática, regras de turno e autoria. Não é conversa humana, independente ou livre. Nomes/itens anteriores reservados foram reutilizados como vocabulário diagnóstico; painel e formas desta rodada são novos.'})
    print(json.dumps(stats,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
