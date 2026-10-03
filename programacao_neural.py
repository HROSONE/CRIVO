"""Geração experimental própria com recuperação limitada ao treino na avaliação."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extrair_codigo(texto):
    match = re.fullmatch(r'\s*```(?:javascript|typescript|js|ts)?\s*\n(.*?)\n```\s*', texto, re.S)
    return match.group(1) if match else texto.strip()


class GeradorProgramacao:
    def __init__(self, pasta, catalogo=None):
        from linguagem_profunda import carregar
        import torch
        torch.set_num_threads(3)
        self.pasta = Path(pasta)
        self.modelo, self.tokenizer, self.estado = carregar(self.pasta)
        self.catalogo = catalogo

    def gerar(self, mensagem, max_tokens=256, diagnostico=None, codigo_anterior=None):
        from linguagem_profunda import fonte_dialogo, ESPECIAIS, codificar_texto
        from geracao_incremental import gerar
        if not 1 <= max_tokens <= 1024:
            raise ValueError('Limite de geração inválido')
        prompt = mensagem
        fontes = []
        if self.catalogo:
            for u in self.catalogo.buscar(mensagem, 2):
                extra = '\nReferência: ' + u['definicao']
                if len(codificar_texto(self.tokenizer, prompt+extra)) < self.modelo.config.contexto-8:
                    prompt += extra; fontes.append(u['id'])
        if diagnostico:
            extra = '\nCorrija este código: '+(codigo_anterior or '')+'\nDiagnóstico: '+diagnostico[:1200]
            if len(codificar_texto(self.tokenizer,prompt+extra)) >= self.modelo.config.contexto-8:
                raise ValueError('Reparo excede contexto; não corta silenciosamente contrato/código')
            prompt += extra
        ids = fonte_dialogo(self.tokenizer,prompt,[],self.modelo.config.contexto)
        saida, completa = gerar(self.modelo,ids,self.tokenizer.token_to_id('<fim>'),
            max_tokens=max_tokens,temperatura=0,proibidos=[self.tokenizer.token_to_id(s) for s in ESPECIAIS[:-1]])
        texto = self.tokenizer.decode(saida,skip_special_tokens=True)
        return dict(codigo=extrair_codigo(texto), completa=completa, tokens=len(saida),
                    experimental=True, referencias=fontes, passo=self.estado['passo'])


def gate(relatorio):
    motivos=[]
    if relatorio.get('particao') != 'teste': motivos.append('exige partição teste')
    if relatorio.get('familias',0)<50: motivos.append('cobertura inferior a 50 famílias reservadas')
    if not relatorio.get('isolamento'): motivos.append('execução isolada indisponível')
    if relatorio.get('runtimes',{}).get('quickjs_sem_apis_host'):
        motivos.append('avaliação QuickJS exige confirmação no runtime Node para promoção')
    for lang in ('javascript','typescript'):
        m=relatorio.get('linguagens',{}).get(lang,{})
        if m.get('total',0)<50: motivos.append('amostra pequena: '+lang)
        taxa=m.get('pass_at_1')
        if not isinstance(taxa,(int,float)) or not .9 <= taxa <= 1:
            motivos.append('pass@1 ausente ou abaixo de 90%: '+lang)
        if m.get('completas',0)!=m.get('total',0): motivos.append('gerações incompletas: '+lang)
    if not relatorio.get('regressao_geral_aprovada'): motivos.append('regressão geral não aprovada')
    if not relatorio.get('revisao_independente'): motivos.append('revisão independente ausente')
    return dict(aprovado=not motivos,motivos=motivos)


def pode_ativar(pasta, relatorio):
    r=json.loads(Path(relatorio).read_text())
    p=Path(pasta)
    return (r.get('pesos_sha256')==digest(p/'pesos.pt') and
            r.get('tokenizer_sha256')==digest(p/'tokenizer.json') and
            r.get('tarefas_sha256')==digest(ROOT/'dados/programacao/tarefas.json') and
            gate(r)['aprovado'])


if __name__=='__main__':
    import argparse
    from conhecimento_programacao import ConhecimentoProgramacao
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--mensagem',required=True)
    p.add_argument('--max-tokens',type=int,default=256)
    a=p.parse_args()
    c=ConhecimentoProgramacao(ROOT/'docs/pesquisa_conhecimento/programacao/catalogo-avancado.json')
    print(json.dumps(GeradorProgramacao(a.modelo,c).gerar(a.mensagem,a.max_tokens),ensure_ascii=False,indent=2))
