"""Experimento próprio 16M, aleatório no início, retomável e sem promoção automática.

Pré-treino e SFT têm checkpoints diferentes. A pausa de tempo não é conclusão
do currículo. Reexecutar a mesma etapa retoma Adam/RNG; alterar corpus, código,
lote, LR ou política de seleção é rejeitado pelo treinador.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def carregar_config(caminho=None):
    from linguagem_profunda import Configuracao, LinguagemProfunda
    path = Path(caminho) if caminho else ROOT / 'configs/transformer_16m.json'
    dados = json.loads(path.read_text())
    if dados['pesos_externos'] or dados['promocao_automatica']:
        raise ValueError('Experimento exige pesos próprios e revisão antes da promoção')
    config = Configuracao(**dados['modelo'])
    parametros = sum(p.numel() for p in LinguagemProfunda(config).parameters())
    if parametros != dados['parametros_esperados']:
        raise ValueError('Contagem de parâmetros não corresponde ao experimento')
    return dados, config, parametros


def comando_treino(dados, config, corpus, saida, etapa, dispositivo, threads, max_segundos=None):
    if etapa not in ('pretreino', 'dialogo'):
        raise ValueError('Etapa de treino desconhecida')
    pasta = Path(saida) / etapa
    cfg = dados[etapa]
    cmd = [sys.executable, '-u', str(ROOT/'scripts/treinar_linguagem_profunda.py'),
           '--corpus', str(corpus), '--saida', str(pasta),
           '--fase', 'linguagem' if etapa == 'pretreino' else 'dialogo',
           '--dimensao', str(config.dimensao), '--camadas', str(config.camadas),
           '--cabecas', str(config.cabecas), '--contexto', str(config.contexto),
           '--passos', str(cfg['passos']), '--lote', str(cfg['lote']), '--lr', str(cfg['lr']),
           '--semente', str(dados['semente']), '--threads', str(threads),
           '--dispositivo', dispositivo, '--avaliar-a-cada', str(cfg['avaliar_a_cada']),
           '--salvar-a-cada', str(cfg['salvar_a_cada']), '--selecionar-melhor']
    if (pasta/'checkpoint.pt').exists():
        cmd += ['--retomar']
    elif etapa == 'dialogo':
        inicial = Path(saida)/'pretreino/melhor'
        if not (inicial/'pesos.pt').exists():
            raise ValueError('SFT exige o pré-treino próprio 16M preservado nesta execução')
        cmd += ['--inicial', str(inicial)]
    # Pré-treino sem --inicial: nunca redimensionar/renomear pesos 2,6M como 16M.
    if etapa == 'dialogo':
        cmd += ['--selecao-humana', '--podar-padding', '--repeticao-linguagem',
                str(cfg['repeticao_linguagem']), '--paciencia-validacoes',
                str(cfg['paciencia_validacoes'])]
    if max_segundos is not None:
        cmd += ['--max-segundos', str(max_segundos)]
    return cmd


def executar(cmd):
    print(json.dumps({'comando': cmd}, ensure_ascii=False), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main():
    import torch
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default=str(ROOT/'configs/transformer_16m.json'))
    p.add_argument('--corpus')
    p.add_argument('--saida')
    p.add_argument('--etapa', choices=('config', 'pretreino', 'dialogo', 'avaliar'), default='config')
    p.add_argument('--dispositivo', choices=('cpu', 'cuda'), default='cuda' if torch.cuda.is_available() else 'cpu')
    p.add_argument('--threads', type=int, default=2)
    p.add_argument('--max-segundos', type=int)
    args = p.parse_args()
    dados, config, parametros = carregar_config(args.config)
    print(json.dumps(dict(parametros=parametros, modelo=asdict(config),
        pesos_externos=False, promocao_automatica=False), ensure_ascii=False), flush=True)
    if args.etapa == 'config':
        return
    if not args.corpus or not args.saida or args.threads < 1 or (args.max_segundos is not None and args.max_segundos < 1):
        p.error('Etapa exige --corpus, --saida, threads positivas e orçamento positivo')
    saida = Path(args.saida).resolve()
    # Não gravar um candidato sobre os artefatos já publicados.
    artefatos = (ROOT/'artefatos').resolve()
    if saida == artefatos or artefatos in saida.parents:
        p.error('Use uma pasta de experimento fora de artefatos/')
    saida.mkdir(parents=True, exist_ok=True)
    if args.etapa != 'avaliar':
        cmd = comando_treino(dados, config, args.corpus, saida, args.etapa,
                             args.dispositivo, args.threads, args.max_segundos)
        executar(cmd)
        return
    for nome, pasta in (('baseline_2m6', ROOT/'artefatos/linguagem_profunda'),
                        ('candidato_16m', saida/'dialogo/melhor')):
        executar([sys.executable, '-u', str(ROOT/'scripts/avaliar_conversa_gerativa.py'),
            '--modelo', str(pasta), '--corpus', args.corpus,
            '--saida', str(saida/(nome+'.json'))])
    executar([sys.executable, str(ROOT/'scripts/exportar_pontuador.py'),
              '--origem', str(saida/'dialogo/melhor'), '--destino', str(saida/'numpy')])
    executar([sys.executable, '-u', str(ROOT/'scripts/avaliar_integracao_conversa.py'),
              '--modelo', str(saida/'numpy'), '--saida', str(saida/'contrato_72.json')])
    print('Avaliação registrada; nenhuma mudança no motor em produção.', flush=True)


if __name__ == '__main__':
    main()
