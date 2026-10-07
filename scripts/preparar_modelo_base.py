"""Baixa um runtime CPU e pesos públicos com versão e hashes fixos (Linux x64)."""
import argparse
import hashlib
import platform
import tarfile
import urllib.request
from pathlib import Path

BINARIO='https://github.com/ggml-org/llama.cpp/releases/download/b11469/llama-b11469-bin-ubuntu-x64.tar.gz'
SHA_BINARIO='bf10f78cb5929f8a745d7d752ff2ec2c183535024ce0e310b784d745be929a5d'
MODELO='https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/91cad51170dc346986eccefdc2dd33a9da36ead9/qwen2.5-1.5b-instruct-q4_k_m.gguf'
SHA_MODELO='6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'


def hash_arquivo(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for bloco in iter(lambda:f.read(1024*1024),b''):h.update(bloco)
    return h.hexdigest()


def baixar(url,p,sha):
    if p.is_file() and hash_arquivo(p)==sha:return
    tmp=p.with_suffix(p.suffix+'.part')
    urllib.request.urlretrieve(url,tmp)
    if hash_arquivo(tmp)!=sha:
        tmp.unlink();raise ValueError('Hash diferente do arquivo publicado.')
    tmp.replace(p)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pasta',type=Path,default=Path('.modelos/qwen25'))
    args=ap.parse_args()
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
        ap.error('Este instalador é para Linux x64. Use llama-server da sua plataforma.')
    p=args.pasta.resolve();p.mkdir(parents=True,exist_ok=True)
    print('Baixando runtime e modelo Q4_K_M (~1,1 GB).',flush=True)
    baixar(BINARIO,p/'llama.tar.gz',SHA_BINARIO)
    with tarfile.open(p/'llama.tar.gz') as t:t.extractall(p,filter='data')
    baixar(MODELO,p/'qwen2.5-1.5b-instruct-q4_k_m.gguf',SHA_MODELO)
    print('Runtime:',p/'llama-b11469/llama-server')
    print('Pesos:',p/'qwen2.5-1.5b-instruct-q4_k_m.gguf')


if __name__=='__main__':main()
