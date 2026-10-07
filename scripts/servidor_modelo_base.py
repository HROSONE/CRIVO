"""Inicia llama-server com o Qwen público quantizado, fora do pacote web."""
import argparse
import os
from pathlib import Path

MODELO='Qwen/Qwen2.5-1.5B-Instruct'
REPOSITORIO='Qwen/Qwen2.5-1.5B-Instruct-GGUF'
REVISAO='91cad51170dc346986eccefdc2dd33a9da36ead9'
ARQUIVO='qwen2.5-1.5b-instruct-q4_k_m.gguf'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host',default='127.0.0.1')
    ap.add_argument('--port',type=int,default=8780)
    ap.add_argument('--pesos',type=Path,required=True)
    ap.add_argument('--binario',default='llama-server')
    args=ap.parse_args()
    if not args.pesos.is_file():ap.error('Arquivo GGUF ausente.')
    # O endpoint permanece local por padrão. Servidor público requer uma
    # camada de hospedagem/autenticação; o site só conhece a URL e a chave.
    os.execvp(args.binario,[args.binario,'-m',str(args.pesos),'--alias',MODELO,
              '--host',args.host,'--port',str(args.port),'-t','2','-c','4096',
              '--parallel','1','--n-predict','256','--no-webui'])


if __name__=='__main__':main()
