"""Resumo de resultados reais do ciclo; sucesso do job não significa promoção."""
import argparse
import json
from pathlib import Path


def relatorio(pasta):
    p=Path(pasta);m=json.loads((p/'corpus/manifesto.json').read_text())
    s=json.loads((p/'selecao.json').read_text());a=json.loads((p/'avaliacao.json').read_text())
    pre=json.loads((p/'pretreino/relatorio.json').read_text()) if (p/'pretreino/relatorio.json').exists() else None;sft=json.loads((p/'candidato/relatorio.json').read_text())
    partes=m['particoes'];linhas=['# Treino nativo JS/TS — resultado experimental','',
        f"Parâmetros: {sft['parametros']:,}. Código real: {sum(x['arquivos_reais'] for x in partes.values())} arquivos.",
        f"Pré-treino: {pre['passo']} passos, {pre['tokens_alvo']:,} tokens-alvo." if pre else 'Inicialização: candidato próprio anterior; nova etapa de ajuste, sem novo pré-treino ou retomada de Adam.',
        f"Ajuste por instruções: {sft['passo']} passos, {sft['tokens_alvo']:,} tokens-alvo.",
        f"Checkpoint selecionado: passo {s['passo']}, por acerto completo/acerto de casos/compilação/término/perda na validação.",'',
        '| Linguagem | Tarefas de teste | Compilam | Executadas | Corretas (pass@1) |',
        '|---|---:|---:|---:|---:|']
    for l,v in a['linguagens'].items():linhas.append(f"| {l} | {v['total']} | {v['compilam']} | {v['executadas']} | {v['corretas']} |")
    if (p/'avaliacao_logica.json').exists():
        extra=json.loads((p/'avaliacao_logica.json').read_text());linhas += ['', 'Composições novas reservadas (benchmark sintético separado):']
        for lang,v in extra['linguagens'].items():linhas.append(f"{lang}: {v['corretas']}/{v['total']} tarefas completas; {v['casos_corretos']}/{v['casos_total']} casos.")
    linhas+=['',f"Gate de promoção: {'aprovado' if a['gate']['aprovado'] else 'reprovado'}. Nenhuma ativação automática.",
        'Benchmark sintético pequeno e já observado; não comprova competência em projetos.',
        'Fontes analisadas por sintaxe; isso não verifica tipos/funcionamento dos projetos externos.',
        'Licenças, fontes, hashes, checkpoints e relatórios completos estão no artefato.',
        '',f"SHA-256 dos pesos selecionados: `{s['pesos_sha256']}`",'']
    return '\n'.join(linhas)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ciclo',required=True);p.add_argument('--saida',required=True)
    a=p.parse_args();texto=relatorio(a.ciclo);Path(a.saida).write_text(texto);print(texto)
