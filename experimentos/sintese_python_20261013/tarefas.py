"""Tarefas para medir a síntese de funções Python a partir de exemplos (etapa 1 do caminho 3).

Cada tarefa: (nome, descrição em português, referência, entradas de desenvolvimento, entradas ocultas).
- A referência é a função certa, escrita à mão; as saídas esperadas vêm dela.
- O motor só vê os pares (entrada, saída) de desenvolvimento.
- As entradas ocultas medem se a função encontrada é a certa, ou só bate com os exemplos.

Duas partes:
- DESENVOLVIMENTO: posso olhar os erros e melhorar o motor.
- BLIND: escritas junto, antes do motor existir; SHA no manifesto; avaliadas uma vez, no fim.
Algumas tarefas estão de propósito fora do que o motor deve saber; ali o certo é não responder.

Autoria: assistente de programação, a pedido do criador do projeto.
"""
import math


def _primo(n):
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


VOGAIS = set("aeiouáéíóúâêôãõàAEIOUÁÉÍÓÚÂÊÔÃÕÀ")

DESENVOLVIMENTO = [
    ("soma_lista", "soma os números de uma lista", sum,
     [[1, 2, 3], [10, -4], []], [[5], [1, 1, 1, 1], [-3, -2], [100, 200, 300], [0, 7]]),
    ("tamanho_lista", "diz quantos itens tem a lista", len,
     [[4, 4, 4], [9], [1, 2]], [[], [1, 2, 3, 4, 5], [0, 0], [7, 8, 9, 10]]),
    ("maior", "devolve o maior número da lista", max,
     [[3, 9, 2], [-5, -1], [7]], [[1, 2, 3], [10, 0, -10], [4, 4], [-7, -8, -2]]),
    ("menor", "devolve o menor número da lista", min,
     [[3, 9, 2], [-5, -1], [7]], [[1, 2, 3], [10, 0, -10], [4, 4], [-7, -8, -2]]),
    ("dobro", "devolve o dobro do número", lambda n: 2 * n,
     [3, 0, -4], [1, 10, -1, 25, 7]),
    ("quadrado", "eleva o número ao quadrado", lambda n: n * n,
     [3, -2, 0], [1, 5, -7, 10, 4]),
    ("par", "diz se o número é par", lambda n: n % 2 == 0,
     [4, 7, 0], [1, 2, 13, 100, -3, -8]),
    ("inverte_texto", "inverte uma palavra", lambda s: s[::-1],
     ["abc", "casa", "a"], ["", "roma", "python", "ovo", "12345"]),
    ("maiusculas", "deixa o texto em letra maiúscula", lambda s: s.upper(),
     ["oi", "Casa", "abc d"], ["", "xyz", "Bom Dia", "a1b2"]),
    ("tamanho_texto", "conta quantas letras tem a palavra", len,
     ["casa", "", "ab"], ["a", "python", "bom dia", "xyz"]),
    ("palindromo", "diz se uma palavra é palíndromo", lambda s: s == s[::-1],
     ["ovo", "casa", "arara"], ["a", "ab", "radar", "python", "", "aba", "abca"]),
    ("dobra_lista", "dobra cada número da lista", lambda xs: [2 * x for x in xs],
     [[1, 2, 3], [], [-1]], [[5], [0, 10], [3, 3, 3], [-2, 4]]),
    ("pares_da_lista", "pega só os números pares da lista", lambda xs: [x for x in xs if x % 2 == 0],
     [[1, 2, 3, 4], [5, 7], [10]], [[], [2, 4, 6], [1, 3, 8], [0, -2, -3]]),
    ("ordena", "ordena a lista do menor para o maior", sorted,
     [[3, 1, 2], [], [5, 5, 1]], [[9], [2, 1], [10, -1, 3, 0], [4, 3, 2, 1]]),
    ("inverte_lista", "inverte a ordem da lista", lambda xs: xs[::-1],
     [[1, 2, 3], [], [7, 8]], [[1], [4, 3, 2, 1], [0, 0, 1], [5, 6, 7, 8, 9]]),
    ("conta_vogais", "conta as vogais de uma palavra", lambda s: sum(c in VOGAIS for c in s),
     ["casa", "xyz", "abacaxi"], ["", "a", "python", "aeiou", "bcd"]),
    ("conta_palavras", "conta quantas palavras tem a frase", lambda s: len(s.split()),
     ["bom dia", "oi", "um dois tres"], ["", "a b c d", "uma frase com cinco palavras", "x"]),
    ("primeiro", "devolve o primeiro item da lista", lambda xs: xs[0],
     [[3, 2, 1], [9], [0, 5]], [[7, 7], [-1, 2, 3], [100]]),
    ("ultimo", "devolve o último item da lista", lambda xs: xs[-1],
     [[3, 2, 1], [9], [0, 5]], [[7, 8], [-1, 2, 3], [100]]),
    ("soma_um", "soma 1 ao número", lambda n: n + 1,
     [1, 0, -5], [9, 99, -1, 41]),
    ("positivo", "diz se o número é positivo", lambda n: n > 0,
     [5, -2, 0], [1, -1, 100, -100, 3]),
    ("media", "calcula a média da lista", lambda xs: sum(xs) / len(xs),
     [[2, 4], [1, 2, 3], [5]], [[10, 20, 30], [1, 2], [0, 0, 6], [7, 7, 7, 7]]),
    ("sem_espacos", "tira os espaços do texto", lambda s: s.replace(" ", ""),
     ["bom dia", "a b c", "oi"], ["", "  x  ", "uma frase longa", "semespaco"]),
    ("absoluto", "devolve o valor absoluto do número", abs,
     [-3, 4, 0], [-10, 10, -1, 7]),
    ("eh_primo", "diz se o número é primo", _primo,
     [2, 4, 7, 9], [1, 0, 3, 11, 15, 17, 21, 29]),
    ("fatorial", "calcula o fatorial do número", math.factorial,
     [3, 0, 5], [1, 4, 6, 7]),
    ("soma_pares", "soma só os números pares da lista", lambda xs: sum(x for x in xs if x % 2 == 0),
     [[1, 2, 3, 4], [5], [10, 10]], [[], [2, 3, 6], [1, 3, 5], [-2, 2, 8]]),
    ("conta_maiores_que_10", "conta quantos números da lista são maiores que 10",
     lambda xs: sum(1 for x in xs if x > 10), [[5, 15, 20], [1], [11, 10]], [[], [100, 200], [9, 10, 11, 12], [50]]),
    ("junta_palavras", "junta as palavras da lista com espaço", lambda xs: " ".join(xs),
     [["bom", "dia"], ["oi"], ["a", "b", "c"]], [[], ["um", "dois", "tres"], ["x", "y"]]),
    ("sem_repetidos", "tira os números repetidos da lista, mantendo a ordem", lambda xs: list(dict.fromkeys(xs)),
     [[1, 1, 2], [3, 2, 3, 1], []], [[5, 5, 5], [1, 2, 3], [4, 1, 4, 1], [9, 8, 9]]),
    # fora do que o motor deve saber: o certo é não responder
    ("fibonacci", "devolve o n-ésimo número de Fibonacci", lambda n: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55][n],
     [3, 5, 6], [0, 1, 2, 7, 10]),
    ("binario", "converte o número para binário em texto", lambda n: bin(n)[2:],
     [5, 2, 8], [1, 3, 10, 255]),
]

BLIND = [
    ("triplo", "devolve o triplo do número", lambda n: 3 * n, [2, 0, -3], [1, 7, -5, 12]),
    ("impar", "diz se o número é ímpar", lambda n: n % 2 == 1, [3, 8, 0], [1, 2, 15, -4, 99]),
    ("minusculas", "deixa o texto em minúscula", lambda s: s.lower(), ["OI", "Casa", "ABC d"], ["", "XyZ", "BOM DIA"]),
    ("produto", "multiplica todos os números da lista", math.prod, [[2, 3], [1, 4, 5], [7]], [[], [10, 10], [2, 2, 2], [-1, 5]]),
    ("quadrado_lista", "eleva ao quadrado cada número da lista", lambda xs: [x * x for x in xs],
     [[1, 2, 3], [], [-2]], [[4], [0, 5], [10, -10]]),
    ("impares_da_lista", "pega só os números ímpares", lambda xs: [x for x in xs if x % 2 == 1],
     [[1, 2, 3, 4], [6, 8], [7]], [[], [1, 3, 5], [2, 9, 10], [11, 12, 13]]),
    ("ordena_desc", "ordena a lista do maior para o menor", lambda xs: sorted(xs, reverse=True),
     [[1, 3, 2], [], [5, 1, 5]], [[9], [1, 2], [0, 10, -1], [1, 2, 3, 4]]),
    ("soma_digitos", "soma os dígitos do número", lambda n: sum(int(c) for c in str(abs(n))),
     [123, 0, 99], [5, 10, 4567, 1001]),
    ("primeira_letra", "devolve a primeira letra da palavra", lambda s: s[0], ["casa", "a", "python"], ["bola", "xyz", "zebra"]),
    ("ultima_letra", "devolve a última letra da palavra", lambda s: s[-1], ["casa", "a", "python"], ["bola", "xyz", "zebra"]),
    ("menos_um", "subtrai 1 do número", lambda n: n - 1, [5, 0, -2], [1, 10, 100, -10]),
    ("negativo", "diz se o número é negativo", lambda n: n < 0, [-3, 2, 0], [-1, 1, -100, 50]),
    ("dobro_mais_um", "devolve o dobro do número mais um", lambda n: 2 * n + 1, [1, 0, 5], [2, -1, 10, 7]),
    ("diferenca_max_min", "diz a diferença entre o maior e o menor da lista", lambda xs: max(xs) - min(xs),
     [[1, 5, 3], [4], [10, -2]], [[0, 0], [7, 1, 9], [-5, -1], [100, 1, 50]]),
    ("conta_pares", "conta quantos números pares tem a lista", lambda xs: sum(1 for x in xs if x % 2 == 0),
     [[1, 2, 4], [3], [6, 6, 6]], [[], [2, 3, 5, 8], [1, 3], [0, 10, 11]]),
    ("tira_negativos", "tira os números negativos da lista", lambda xs: [x for x in xs if x >= 0],
     [[1, -2, 3], [-1], [0, 5]], [[], [-5, -6], [2, 3, -4, 0], [10]]),
    ("mais_dez_lista", "soma 10 em cada número da lista", lambda xs: [x + 10 for x in xs],
     [[1, 2], [], [-10]], [[0], [5, 5, 5], [90, -3]]),
    ("palavras_maiusculas", "deixa cada palavra da lista em maiúscula", lambda xs: [x.upper() for x in xs],
     [["oi", "tchau"], [], ["a"]], [["bom", "dia"], ["xyz"], ["Ab", "cD"]]),
    ("separa_palavras", "separa a frase em uma lista de palavras", lambda s: s.split(),
     ["bom dia", "oi", "a b c"], ["", "uma frase maior aqui", "x y"]),
    ("comeca_com_a", "diz se a palavra começa com a letra a", lambda s: s.startswith("a"),
     ["abacaxi", "casa", "a"], ["", "banana", "amor", "Ana", "zebra"]),
    ("tira_vogais", "tira as vogais da palavra", lambda s: "".join(c for c in s if c not in VOGAIS),
     ["casa", "xyz", "abacaxi"], ["", "aeiou", "python", "banana"]),
    ("palindromo_frase", "diz se a frase é palíndromo, sem contar espaços e maiúsculas",
     lambda s: s.replace(" ", "").lower() == s.replace(" ", "").lower()[::-1],
     ["Ana", "socorram me subi no onibus em marrocos", "casa"], ["Arara", "bola", "A base do teto desaba", "ab", ""]),
    ("maior_que_cem", "diz se o número é maior que cem", lambda n: n > 100, [150, 100, 3], [101, 99, 1000, -5, 200]),
    ("metade", "divide o número por dois, sem casas decimais", lambda n: n // 2, [10, 7, 0], [1, 2, 99, 100, 15]),
    ("resto_por_3", "devolve o resto da divisão por 3", lambda n: n % 3, [7, 9, 2], [0, 1, 10, 11, 100]),
    ("tamanho_maior_palavra", "diz o tamanho da maior palavra da frase", lambda s: max(len(p) for p in s.split()),
     ["bom dia", "a casa amarela", "oi"], ["x", "uma frase qualquer", "aa bbb c"]),
    ("repete_texto", "repete o texto duas vezes", lambda s: s + s, ["ab", "", "oi"], ["x", "casa", "12"]),
    ("soma_quadrados", "soma os quadrados dos números da lista", lambda xs: sum(x * x for x in xs),
     [[1, 2], [3], []], [[1, 1, 1], [2, 3, 4], [-2, 2], [10]]),
    ("conta_letra_a", "conta quantas vezes a letra a aparece", lambda s: s.count("a"),
     ["banana", "xyz", "casa"], ["", "a", "abacaxi", "Ana"]),
    ("elemento_do_meio", "devolve o elemento do meio da lista", lambda xs: xs[len(xs) // 2],
     [[1, 2, 3], [5, 6, 7, 8, 9], [4]], [[10, 20, 30], [1, 2], [7, 8, 9, 10, 11, 12, 13]]),
    # fora do que o motor deve saber
    ("mediana", "calcula a mediana da lista", lambda xs: sorted(xs)[len(xs) // 2] if len(xs) % 2 else
     (sorted(xs)[len(xs) // 2 - 1] + sorted(xs)[len(xs) // 2]) / 2, [[3, 1, 2], [4, 1, 3, 2], [5]], [[1, 2], [9, 1, 5], [8, 2, 4, 6]]),
    ("mdc_com_12", "calcula o máximo divisor comum do número com 12", lambda n: math.gcd(n, 12),
     [8, 9, 5], [12, 18, 7, 24, 30]),
]
