"""Currículo autoral de algoritmos, sem soluções das famílias de teste reservadas."""
from pathlib import Path
import json
import math
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]


def prefixos(xs):
    total=0; r=[]
    for x in xs: total+=x; r.append(total)
    return r


def sequencia(n):
    a,b=0,1;r=[]
    for _ in range(n):r.append(a);a,b=b,a+b
    return r


def maior_bloco(xs):
    atual=melhor=0
    for x in xs:
        atual=atual+1 if x>0 else 0;melhor=max(melhor,atual)
    return melhor


def balanceado(s):
    nivel=0
    for c in s:
        if c=='(':nivel+=1
        elif c==')':
            nivel-=1
            if nivel<0:return False
    return nivel==0


def contar_trechos(s,sub):
    if not sub:return 0
    return sum(s[i:i+len(sub)]==sub for i in range(len(s)-len(sub)+1))


def especificacoes():
    listas=[[],[1],[3,-2,5],[2,2,-1,4]]
    matrizes=[[],[[1,2],[3,4]],[[1,-2,3]],[[0],[4]]]
    # nome, argumentos TS, retorno TS, contrato, corpo JS/TS, casos completos
    specs=[]
    def add(nome,args,ret,contrato,corpo,entradas,oracle):
        specs.append((nome,args,ret,contrato,corpo,[dict(entrada=x,saida=oracle(*x)) for x in entradas]))
    add('somas_acumuladas','xs: number[]','number[]','retornar as somas acumuladas de xs; lista vazia retorna []',
        'const r: number[] = []; let total = 0; for (const x of xs) { total += x; r.push(total); } return r;',[[x] for x in listas],prefixos)
    add('diferencas_vizinhas','xs: number[]','number[]','retornar xs[i] - xs[i-1] para cada i a partir de 1',
        'const r: number[] = []; for (let i = 1; i < xs.length; i++) r.push(xs[i] - xs[i-1]); return r;',[[x] for x in listas],lambda xs:[b-a for a,b in zip(xs,xs[1:])])
    add('comprimento_bloco_positivo','xs: number[]','number','retornar o comprimento da maior sequência consecutiva de números positivos em xs',
        'let atual = 0, melhor = 0; for (const x of xs) { atual = x > 0 ? atual + 1 : 0; melhor = Math.max(melhor, atual); } return melhor;',[[x] for x in listas],maior_bloco)
    add('somar_matriz','m: number[][]','number','somar todos os elementos da matriz m, inclusive vazia',
        'let total = 0; for (const linha of m) for (const x of linha) total += x; return total;',[[x] for x in matrizes],lambda m:sum(sum(row) for row in m))
    add('somas_linhas','m: number[][]','number[]','retornar uma lista com a soma de cada linha de m',
        'return m.map(linha => linha.reduce((total, x) => total + x, 0));',[[x] for x in matrizes],lambda m:[sum(row) for row in m])
    add('transpor_matriz','m: number[][]','number[][]','transpor uma matriz retangular m; vazia retorna []',
        'if (m.length === 0) return []; return m[0].map((_, i) => m.map(linha => linha[i]));',[[x] for x in matrizes],lambda m:[list(row) for row in zip(*m)])
    add('diagonal_principal','m: number[][]','number[]','extrair a diagonal principal da matriz quadrada m',
        'return m.map((linha, i) => linha[i]);',[[[]],[[[1]]],[[[1,2],[3,4]]],[[[0,-1],[5,0]]]],lambda m:[row[i] for i,row in enumerate(m)])
    add('achatar_matriz','m: number[][]','number[]','concatenar as linhas de m em uma lista, preservando ordem',
        'const r: number[] = []; for (const linha of m) for (const x of linha) r.push(x); return r;',[[x] for x in matrizes],lambda m:[v for row in m for v in row])
    add('media_lista','xs: number[]','number','calcular a média aritmética de xs; vazia retorna 0',
        'if (xs.length === 0) return 0; return xs.reduce((s, x) => s + x, 0) / xs.length;',[[x] for x in listas],lambda xs:sum(xs)/len(xs) if xs else 0)
    add('mediana_lista','xs: number[]','number','calcular a mediana numérica de xs; vazia retorna 0; comprimento par usa média dos dois centrais',
        'if (!xs.length) return 0; const a = [...xs].sort((x,y) => x-y); const i = Math.floor(a.length / 2); return a.length % 2 ? a[i] : (a[i-1] + a[i]) / 2;',[[x] for x in listas],lambda xs:0 if not xs else (sorted(xs)[(len(xs)-1)//2]+sorted(xs)[len(xs)//2])/2)
    add('amplitude_lista','xs: number[]','number','retornar a diferença entre o maior e o menor item de xs; vazia retorna 0',
        'return xs.length ? Math.max(...xs) - Math.min(...xs) : 0;',[[x] for x in listas],lambda xs:max(xs)-min(xs) if xs else 0)
    add('frequencias_numericas','xs: number[]','Record<string, number>','retornar um objeto com a frequência de cada número inteiro em xs, usando chaves textuais',
        'const r: Record<string, number> = {}; for (const x of xs) { const chave = String(x); r[chave] = (r[chave] || 0) + 1; } return r;',[[x] for x in listas],lambda xs:dict(Counter(str(x) for x in xs)))
    add('separar_sinal','xs: number[]','number[][]','retornar [negativos, naoNegativos] preservando ordem e sem alterar xs',
        'return [xs.filter(x => x < 0), xs.filter(x => x >= 0)];',[[x] for x in listas],lambda xs:[[x for x in xs if x<0],[x for x in xs if x>=0]])
    add('pares_soma','xs: number[], alvo: number','number','contar pares de índices i<j de xs cuja soma é alvo; contar repetições por índice',
        'let total = 0; for (let i = 0; i < xs.length; i++) for (let j = i+1; j < xs.length; j++) if (xs[i]+xs[j] === alvo) total++; return total;',[[[],0],[[1,2,3],4],[[2,2,2],4],[[-1,1,0],0]],lambda xs,alvo:sum(xs[i]+xs[j]==alvo for i in range(len(xs)) for j in range(i+1,len(xs))))
    add('media_janelas','xs: number[], k: number','number[]','retornar médias de todas as janelas consecutivas de k itens; k inteiro positivo, maior que comprimento retorna []',
        'const r: number[] = []; for (let i = 0; i+k <= xs.length; i++) { let s = 0; for (let j = i; j < i+k; j++) s += xs[j]; r.push(s / k); } return r;',[[[],1],[[1,2,3],2],[[2,4],1],[[1],3]],lambda xs,k:[sum(xs[i:i+k])/k for i in range(len(xs)-k+1)])
    add('mesclar_ordenadas','a: number[], b: number[]','number[]','mesclar duas listas numéricas já ordenadas, preservando todos os itens e ordem crescente',
        'const r: number[] = []; let i = 0, j = 0; while (i<a.length || j<b.length) { if (j>=b.length || (i<a.length && a[i]<=b[j])) r.push(a[i++]); else r.push(b[j++]); } return r;',[[[],[]],[[1,3],[2,4]],[[1,1],[1]],[[2],[]]],lambda a,b:sorted(a+b))
    add('mdc_euclides','a: number, b: number','number','calcular o máximo divisor comum de dois inteiros não negativos; mdc(0,0)=0',
        'while (b !== 0) { const resto = a % b; a = b; b = resto; } return a;',[[0,0],[12,18],[7,5],[0,9]],math.gcd)
    add('mmc_euclides','a: number, b: number','number','calcular o mínimo múltiplo comum de dois inteiros não negativos; se algum for zero retorna 0',
        'if (a===0 || b===0) return 0; const produto = a*b; while (b !== 0) { const resto = a%b; a=b; b=resto; } return produto / a;',[[0,0],[12,18],[7,5],[0,9]],lambda a,b:a*b//math.gcd(a,b) if a and b else 0)
    add('sequencia_fibonacci','n: number','number[]','retornar os primeiros n termos de Fibonacci, começando por 0 e 1; n inteiro entre 0 e 12',
        'const r: number[] = []; let a=0, b=1; for (let i=0; i<n; i++) { r.push(a); const proximo=a+b; a=b; b=proximo; } return r;',[[0],[1],[5],[8]],sequencia)
    add('teste_primo','n: number','boolean','verificar se n é primo; n inteiro entre 0 e 100',
        'if (n<2) return false; for (let d=2; d*d<=n; d++) if (n%d===0) return false; return true;',[[0],[1],[2],[49],[97]],lambda n:n>=2 and all(n%d for d in range(2,math.isqrt(n)+1)))
    add('divisores','n: number','number[]','listar todos os divisores positivos de n em ordem crescente; n inteiro positivo pequeno',
        'const r: number[] = []; for (let d=1; d<=n; d++) if (n%d===0) r.push(d); return r;',[[1],[6],[7],[12]],lambda n:[d for d in range(1,n+1) if n%d==0])
    add('potencia_iterativa','base: number, expoente: number','number','calcular base elevado a expoente inteiro não negativo usando multiplicação iterativa',
        'let r = 1; for (let i=0; i<expoente; i++) r *= base; return r;',[[2,0],[2,3],[-2,3],[0,2]],lambda base,expoente:base**expoente)
    add('soma_digitos','n: number','number','somar os dígitos decimais de um inteiro não negativo',
        'let s=0; while (n>0) { s += n%10; n=Math.floor(n/10); } return s;',[[0],[9],[123],[1001]],lambda n:sum(map(int,str(n))))
    add('parenteses_balanceados','s: string','boolean','verificar se os parênteses de s estão balanceados; ignorar demais caracteres',
        'let nivel=0; for (const c of s) { if (c==="(") nivel++; else if (c===")") { nivel--; if (nivel<0) return false; } } return nivel===0;',[[''],['(a(b))'],[')('],['(()']],balanceado)
    add('contar_substrings','s: string, trecho: string','number','contar ocorrências de trecho em s incluindo sobreposições; trecho vazio retorna 0; entradas ASCII',
        'if (!trecho.length) return 0; let total=0; for (let i=0; i+trecho.length<=s.length; i++) if (s.slice(i,i+trecho.length)===trecho) total++; return total;',[['','a'],['aaaa','aa'],['abcabc','abc'],['abc','']],contar_trechos)
    add('contar_vogais','s: string','number','contar vogais ASCII em s sem distinguir maiúsculas de minúsculas',
        'let total=0; for (const c of s.toLowerCase()) if ("aeiou".includes(c)) total++; return total;',[[''],['AEIOU'],['Hello'],['xyz']],lambda s:sum(c in 'aeiou' for c in s.lower()))
    add('inverter_palavras','s: string','string','inverter a ordem das palavras separadas por espaços em s; remover espaços extras',
        'return s.trim().split(/\\s+/).filter(x => x.length>0).reverse().join(" ");',[[''],[' um  dois tres '],['a'],['x y']],lambda s:' '.join(s.split()[::-1]))
    add('maior_palavra','s: string','string','retornar a primeira palavra mais longa em s; palavras separadas por espaços; sem palavras retorna string vazia',
        'let maior=""; for (const p of s.trim().split(/\\s+/)) if (p.length>maior.length) maior=p; return maior;',[[''],['a bb ccc'],['aa bb'],['  x  ']],lambda s:max(s.split(),key=len,default=''))
    add('remover_caractere','s: string, c: string','string','remover todas as ocorrências do caractere c em s; c tem comprimento 1, entradas ASCII',
        'return s.split(c).join("");',[['','a'],['banana','a'],['abc','.'],['a.a','.']],lambda s,c:s.replace(c,''))
    add('indices_valor','xs: number[], valor: number','number[]','retornar todos os índices de xs cujo item é igual a valor',
        'const r: number[] = []; for (let i=0; i<xs.length; i++) if (xs[i]===valor) r.push(i); return r;',[[[],1],[[1,2,1],1],[[0,0],0],[[3],2]],lambda xs,valor:[i for i,x in enumerate(xs) if x==valor])
    return specs


def gerar():
    import re
    tarefas=[]
    reformulacoes=['Implemente','Escreva uma função para','Preciso de uma função que consiga','Crie uma solução para',
                   'Faça uma função para','Resolva a tarefa de','Produza código para','Retorne uma função capaz de']
    for i,(nome,args,ret,desc,corpo,casos) in enumerate(especificacoes()):
        split='validacao' if i in (1,5,10,15,20,25) else 'treino'
        for lang in ('javascript','typescript'):
            parametros=args if lang=='typescript' else re.sub(r': (?:number|string)(?:\[\])*','',args)
            body=corpo if lang=='typescript' else re.sub(r': (?:number\[\]|Record<string, number>)','',corpo)
            resposta=f'function resolver({parametros})'+(f': {ret}' if lang=='typescript' else '')+' { '+body+' }'
            for j,acao in enumerate(reformulacoes):
                # Dois formatos do mesmo contrato: idioma explícito + assinatura vs tipo do retorno.
                for formato in (0,1):
                    mensagem=(f'Em {lang}, {acao.lower()} {desc}. Assinatura: resolver({parametros})' +
                              (f': {ret}' if lang=='typescript' else '') + '.' if formato==0 else
                              f'{acao} {desc}. Use {lang}, função resolver; argumentos: {parametros}; retorno: {ret}.')
                    mensagem+=' Retorne somente código, sem imports, sem alterar as entradas. Entradas pequenas e finitas.'
                    tarefas.append(dict(id=f'alg_{nome}_{lang}_{j}_{formato}',familia='alg_'+nome,split=split,
                      linguagem=lang,mensagem=mensagem,resposta=resposta,casos=casos))
    return dict(versao=1,natureza='30 famílias autorais; variantes de prompts não são problemas independentes',tarefas=tarefas)


if __name__=='__main__':
    d=gerar();p=ROOT/'dados/programacao/algoritmos.json';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(len(d['tarefas']),'exemplos de algoritmos')
