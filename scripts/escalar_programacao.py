"""Perfis de capacidade do Transformer próprio; expansão exige novo pré-treino."""
import argparse
import json
PERFIS={
 'atual':dict(vocabulario=4096,dimensao=192,camadas=4,cabecas=6,contexto=256),
 '10m':dict(vocabulario=4096,dimensao=384,camadas=5,cabecas=6,contexto=512),
 '30m':dict(vocabulario=4096,dimensao=512,camadas=8,cabecas=8,contexto=512),
}


def estimar(nome):
    c=PERFIS[nome];d=c['dimensao']
    n=c['vocabulario']*d+c['contexto']*d+c['camadas']*(12*d*d+9*d)+2*d
    return dict(perfil=nome,config=c,parametros=n,
                memoria_minima_estado_adam_fp32_mib=round(n*16/2**20,2),
                aviso='Estimativa só de pesos, gradientes e Adam; ativações/runtime exigem memória adicional. Não converte pesos menores.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--perfil',choices=PERFIS,default='atual')
    a=p.parse_args();print(json.dumps(estimar(a.perfil),ensure_ascii=False,indent=2))
