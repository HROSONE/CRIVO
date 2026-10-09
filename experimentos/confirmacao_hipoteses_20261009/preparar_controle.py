"""Controle autoral de desenvolvimento, fixado antes da alteração do motor."""
import hashlib
import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent


def etapa(texto, resultado, hipotese=False):
    return dict(texto=texto, resultado=resultado, hipotese=hipotese)


def custos(a, b):
    return dict(totais=[str(a), str(b)], menor=0 if a < b else 1 if b < a else None,
                diferenca=str(abs(a-b)))


def tempo(a, gasto):
    return dict(disponivel=str(a), gasto=str(gasto), restante=str(a-gasto))


def main():
    p = PASTA/'controle.json'
    if p.exists():
        raise SystemExit('Controle já existe; não sobrescrever.')
    sessoes = [
        dict(id='custos', operacao='comparar_custos', turnos=[
            etapa('O curso custa 48 reais. O livro custa 39 reais mais 12 de frete. Qual custa menos?', custos(48, 51)),
            etapa('Se o frete fosse 3 reais, qual seria menor?', custos(48, 42), True),
            etapa('E agora?', custos(48, 42), True),
            etapa('Confirmo essa hipótese como fato.', custos(48, 42)),
            etapa('Qual é a diferença dos custos reais?', custos(48, 42)),
            etapa('Se o frete fosse 8 reais, qual seria menor?', custos(48, 47), True),
            etapa('Descarte essa hipótese.', custos(48, 42)),
            etapa('Qual é a diferença dos custos reais?', custos(48, 42)),
        ]),
        dict(id='tempo', operacao='tempo_restante', turnos=[
            etapa('Tenho 80 minutos. A ida leva 12 minutos e a tarefa leva 14 minutos. Quanto sobra?', tempo(80, 26)),
            etapa('Se eu tivesse 32 minutos, caberia?', tempo(32, 26), True),
            etapa('Quanto sobraria?', tempo(32, 26), True),
            etapa('Essa hipótese aconteceu de verdade.', tempo(32, 26)),
            etapa('Quanto tempo real sobra?', tempo(32, 26)),
            etapa('Se eu tivesse 120 minutos, caberia?', tempo(120, 26), True),
            etapa('Volte aos fatos.', tempo(32, 26)),
            etapa('Quanto tempo real sobra?', tempo(32, 26)),
        ]),
        dict(id='agenda', operacao='intersecao_agendas', turnos=[
            etapa('Nina pode segunda ou sábado. Ravi pode sábado. Qual dia dá?', dict(dias=['sabado'])),
            etapa('Se Ravi pudesse segunda, qual dia daria?', dict(dias=['segunda']), True),
            etapa('E agora?', dict(dias=['segunda']), True),
            etapa('Confirme essa hipótese como fato.', dict(dias=['segunda'])),
            etapa('Qual dia resta em comum?', dict(dias=['segunda'])),
            etapa('Se Nina pudesse quarta, qual dia daria?', dict(dias=[]), True),
            etapa('Sem essa hipótese.', dict(dias=['segunda'])),
            etapa('Qual dia resta em comum?', dict(dias=['segunda'])),
        ]),
        dict(id='requisitos', operacao='verificar_requisitos', turnos=[
            etapa('Para entrar precisa de selo e chave. Ravi tem selo, mas não tem chave. Cumpre a regra?', dict(status='refutado')),
            etapa('Se ele recebesse uma chave, conseguiria entrar?', dict(status='sustentado'), True),
            etapa('Ele cumpre a regra?', dict(status='sustentado'), True),
            etapa('Confirmo essa hipótese como fato.', dict(status='sustentado')),
            etapa('Ravi cumpre a regra?', dict(status='sustentado')),
            etapa('Se Nina recebesse uma chave, conseguiria entrar?', dict(status='indeterminado'), True),
            etapa('Descarte essa hipótese.', dict(status='sustentado')),
            etapa('Ravi cumpre a regra?', dict(status='sustentado')),
        ]),
    ]
    p.write_text(json.dumps(dict(sessoes=sessoes), ensure_ascii=False, indent=2)+'\n')
    (PASTA/'protocolo.json').write_text(json.dumps(dict(
        controle_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        baseline_commit='836d351',
        limite='Controle de desenvolvimento da mesma autoria. Não é avaliação independente, treinamento neural ou conversa livre.',
    ), ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
