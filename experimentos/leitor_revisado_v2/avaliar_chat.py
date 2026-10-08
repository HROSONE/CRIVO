import os
"""Comparação isolada do chat factual; pesos experimentais nunca são promovidos."""
import sys,json,torch
from pathlib import Path
ROOT=Path(os.environ['CRIVO_REPO']);OUT=Path(os.environ['CRIVO_SAIDA'])
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(Path(__file__).resolve().parent)]
from continuar_leitor import carregar
from scripts.treinar_leitor_transformer import lote_tensores

def main():
    torch.set_num_threads(2)
    import crivo
    from leitura_ficha import LeituraFicha
    from avaliar_leitura_ficha import avaliar
    original=crivo.Crivo
    m,bpe,_=carregar(OUT/'candidato_cabeca','cpu');m.eval()
    meta=json.loads((OUT/'combinador_cabeca.json').read_text())
    class LeitorExperimental:
        disponivel=True
        def probabilidades(self,q,fatos):
            if not fatos:return []
            ids,u=lote_tensores([(q,f) for f in fatos],bpe,256,'cpu')
            with torch.no_grad():return torch.sigmoid(m(ids,u)).tolist()
    class Experimento(original):
        def __init__(self,*args,**kwargs):
            kwargs['usar_geracao']=False
            super().__init__(*args,**kwargs)
            if modo=='adaptado':
                reader=LeituraFicha(self.compositor,caminho_modelo='/nao/existe',transformer=LeitorExperimental())
                # Uso explícito no laboratório; arquivos continuam aprovado:false.
                reader.pesos=meta['pesos'];reader.limiar=meta['limiar'];reader.limiar_aproximar=meta['limiar_aproximar']
                self._leitura_ficha=reader
    result={'protocolo':'Chat factual sem geração, classificadores originais, conjuntos congelados somente em agregados; instalação experimental em memória','aprovado':False,'modos':{}}
    try:
        crivo.Crivo=Experimento
        for modo in ['original','adaptado']:
            result['modos'][modo]={}
            for conjunto in ['teste','teste_v2']:
                agg,_=avaliar(conjunto)
                result['modos'][modo][conjunto]=agg
                print(modo,conjunto,json.dumps(agg,ensure_ascii=False),flush=True)
                (OUT/'controle_chat.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    finally:crivo.Crivo=original
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
