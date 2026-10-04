"""Baixa somente dados estáticos públicos em revisões fixas; verifica SHA-256."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import urllib.request

FONTES = {
    'wikipedia': {
        'dataset':'wikimedia/wikipedia',
        'revisao':'b04c8d1ceb2f5cd4588862100d08de323dccfbaa',
        'arquivo':'20231101.pt/train-00001-of-00006.parquet',
        'destino':'wikipedia.pt.parquet',
        'sha256':'5e9b4476c0d69b0bffdcf76529de424dfda9510e3a6867676e5d482e6c70f1be',
        'licenca':'CC-BY-SA-3.0/GFDL'},
    'oasst2': {
        'dataset':'OpenAssistant/oasst2',
        'revisao':'179dd21fc55192153d94adb0e0ce8f69e222bf75',
        'arquivo':'2023-11-05_oasst2_ready.messages.jsonl.gz',
        'destino':'oasst2.messages.jsonl.gz',
        'sha256':'a9f240c4c77aa1378364f70d37e753c07ba284e247b019d700e1947a0e5da751',
        'licenca':'Apache-2.0'},
    'oasst2_completo': {
        'dataset':'OpenAssistant/oasst2',
        'revisao':'179dd21fc55192153d94adb0e0ce8f69e222bf75',
        'arquivo':'2023-11-05_oasst2_all.messages.jsonl.gz',
        'destino':'oasst2.all.messages.jsonl.gz',
        'sha256':'820146830e78634170f5a33d79d0b3e5022a7f169ce054886ad1f16e1d53a764',
        'licenca':'Apache-2.0'},
    'tucano': {
        'dataset':'TucanoBR/Tucano-SFT',
        'revisao':'0f5eb4d493e86d18abad5f9e085a74c49785ac76',
        'arquivo':'data/train-00000-of-00003.parquet',
        'destino':'tucano-sft.parquet',
        'sha256':'2d3b0b096897bf1036fd4a9ec391b6e0f7e831d9dd3e90fbf27c0432586b30a9',
        'licenca':'MIT para registros cnmoro/GPT4-500k-Augmented-PTBR-Clean selecionados'}}


def baixar(nome, out):
    origem = dict(FONTES[nome]); arquivo = out / origem['destino']
    url = 'https://huggingface.co/datasets/{dataset}/resolve/{revisao}/{arquivo}'.format(**origem)
    h = hashlib.sha256()
    if arquivo.exists():
        with arquivo.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''): h.update(b)
        if h.hexdigest() != origem['sha256']:
            raise ValueError('Arquivo existente difere da fonte: '+str(arquivo))
    else:
        temporario = arquivo.with_suffix(arquivo.suffix+'.tmp')
        with urllib.request.urlopen(url,timeout=120) as src, temporario.open('wb') as dst:
            while True:
                b = src.read(4*1048576)
                if not b: break
                h.update(b);dst.write(b)
        if h.hexdigest() != origem['sha256']:
            temporario.unlink(); raise ValueError('Hash público diverge: '+nome)
        temporario.replace(arquivo)
    origem.update(url=url,bytes=arquivo.stat().st_size)
    (out/('origem_'+nome+'.json')).write_text(json.dumps(origem,ensure_ascii=False,indent=2)+'\n')
    print(nome,origem['bytes'],'bytes, SHA verificado',flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True)
    p.add_argument('--dialogos-amplos',action='store_true', help='Também baixa a exportação humana completa OASST2')
    p.add_argument('--dialogos-publicos',action='store_true',
                   help='Também baixa textos sintéticos públicos; nunca pesos de modelos')
    args = p.parse_args(); out = Path(args.saida);out.mkdir(parents=True,exist_ok=True)
    for nome in FONTES:
        if nome == 'tucano' and not args.dialogos_publicos: continue
        if nome == 'oasst2_completo' and not args.dialogos_amplos: continue
        baixar(nome,out)
    # A mesma extração PT-BR usada no treino inicial, sem IDs privados novos.
    # O arquivo público já possui IDs de autores; os corpora selecionados não
    # distribuem esses campos, apenas IDs de mensagem/árvore para proveniência.
    destino = out / 'oasst2.pt.jsonl'
    tmp = destino.with_suffix('.jsonl.tmp')
    with gzip.open(out / FONTES['oasst2']['destino'], 'rt', encoding='utf-8') as src, \
            tmp.open('w',encoding='utf-8') as dst:
        for linha in src:
            mensagem = json.loads(linha)
            if mensagem.get('lang') == 'pt-BR':
                dst.write(json.dumps(mensagem,ensure_ascii=False)+'\n')
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if digest != '875108bb4cd7a77a07097e3919ed94faf7cbf449ca201d65eea958714ec38240':
        tmp.unlink(); raise ValueError('Extração PT-BR diverge da revisão publicada')
    tmp.replace(destino)
    print('Extração PT-BR verificada',digest,flush=True)


if __name__ == '__main__':main()
