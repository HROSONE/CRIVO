"""Sonda numérica do gerador próprio; NÃO é treino completo nem aprovação.

Inicializa aleatoriamente, usa tokenizer próprio do repositório e faz poucas
atualizações para verificar o percurso entrada -> loss -> gradiente -> pesos.
Os exemplos-semente ainda precisam de revisão humana para um treino real.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import torch
    from tokenizers import Tokenizer
    from linguagem_profunda import LinguagemProfunda, segmentos_dialogo, codificar_texto
    from scripts.experimento_transformer_16m import carregar_config
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida', type=Path, required=True)
    p.add_argument('--passos', type=int, default=3)
    args = p.parse_args()
    if not 1 <= args.passos <= 12:
        p.error('Sonda limitada a 1–12 passos; não é o treinador completo')
    torch.set_num_threads(1)
    torch.manual_seed(20261007)
    dados, config, parametros = carregar_config(ROOT/'configs/gerador_diverso_16m.json')
    caminho_tokenizer = ROOT/'artefatos/linguagem_profunda/tokenizer.json'
    tokenizer = Tokenizer.from_file(str(caminho_tokenizer))
    tokenizer.encode_special_tokens = True
    if tokenizer.get_vocab_size() != config.vocabulario:
        raise ValueError('Tokenizador próprio incompatível')
    modelo = LinguagemProfunda(config)
    otimizador = torch.optim.AdamW(modelo.parameters(), lr=dados['dialogo']['lr'])
    caminho = ROOT/'dados/gerador_diverso_semente.jsonl'
    exemplos = [json.loads(l) for l in caminho.read_text(encoding='utf-8').splitlines()]
    antes = modelo.embedding.weight.detach().clone()
    perdas = []
    for i in range(args.passos):
        ex = exemplos[i % len(exemplos)]
        _, fonte = segmentos_dialogo(tokenizer, ex['mensagem'])
        alvo = codificar_texto(tokenizer, ex['resposta']) + [tokenizer.token_to_id('<fim>')]
        seq = fonte + alvo
        if len(seq) - 1 > config.contexto:
            raise ValueError('Exemplo excede contexto; recusar truncamento silencioso')
        x = torch.tensor([seq[:-1]], dtype=torch.long)
        y = torch.tensor([[-100] * (len(fonte)-1) + alvo], dtype=torch.long)
        otimizador.zero_grad(set_to_none=True)
        _, perda = modelo(x, y)
        if not math.isfinite(float(perda.detach())):
            raise ValueError('Perda não finita')
        perda.backward()
        norma = torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        if not math.isfinite(float(norma)) or float(norma) <= 0:
            raise ValueError('Gradiente inválido')
        otimizador.step()
        perdas.append({'passo': i+1, 'id': ex['id'], 'loss': float(perda.detach()), 'norma_gradiente': float(norma)})
    delta = float((modelo.embedding.weight.detach() - antes).abs().max())
    if delta <= 0:
        raise ValueError('Os pesos não foram atualizados')
    args.saida.mkdir(parents=True, exist_ok=True)
    relatorio = {'parametros': parametros, 'passos_executados': args.passos, 'perdas': perdas,
                 'delta_max_embedding': delta, 'inicializacao': 'aleatoria', 'pesos_externos': False,
                 'aprovado_para_chat': False, 'treino_completo': False,
                 'tokenizer_sha256': hashlib.sha256(caminho_tokenizer.read_bytes()).hexdigest(),
                 'corpus_sha256': hashlib.sha256(caminho.read_bytes()).hexdigest(),
                 'limite': 'Sonda numérica em exemplos sintéticos pendentes de revisão; não demonstra qualidade de respostas.'}
    torch.save({'config': dados['modelo'], 'estado': modelo.state_dict(),
                'aprovado_para_chat': False, 'sonda_numerica': True}, args.saida/'sonda.pt')
    (args.saida/'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(relatorio, ensure_ascii=False))


if __name__ == '__main__':
    main()
