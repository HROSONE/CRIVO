"""Audita JSONL autoral: cobertura, repetições, fontes e isolamento dos cenários.

Sem modelos ou dependências externas. O relatório de um corpus pequeno é útil,
mas o código de saída é 1 até que as metas e a revisão humana sejam satisfeitas.
Similaridade lexical é uma triagem; não certifica verdade ou diversidade semântica.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def normalizar(texto):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', texto).casefold()))


def molde(texto):
    return re.sub(r'\d+(?:[.,]\d+)*', '<numero>', normalizar(texto))


def shingles(texto):
    palavras = molde(texto).split()
    return {tuple(palavras[i:i+5]) for i in range(len(palavras)-4)}


def auditar(exemplos, politica):
    erros, grupos, origens = [], defaultdict(set), defaultdict(set)
    cobertura = {s: {'dominio': Counter(), 'tarefa': Counter()} for s in ('treino', 'validacao', 'teste')}
    vistos, respostas, conteudos, ids, moldes, por_grupo = {}, {}, {}, set(), Counter(), Counter()
    indice, anteriores, proximos = defaultdict(set), [], []
    for i, ex in enumerate(exemplos):
        faltam = [k for k in ('id', 'grupo', 'source_id', 'dominio', 'tarefa', 'split',
                              'mensagem', 'resposta', 'conteudo', 'origem', 'licenca',
                              'fonte', 'revisao') if not isinstance(ex.get(k), str) or not ex[k].strip()]
        if faltam:
            erros.append({'exemplo': i, 'erro': 'campos_ausentes', 'campos': faltam})
            continue
        split = ex['split']
        if split not in cobertura or ex['dominio'] not in politica['dominios'] or ex['tarefa'] not in politica['tarefas']:
            erros.append({'exemplo': i, 'erro': 'classificacao_invalida'})
            continue
        if ex['revisao'] != 'humana_aprovada':
            erros.append({'exemplo': i, 'erro': 'revisao_humana_pendente'})
        if ex['id'] in ids:
            erros.append({'exemplo': i, 'erro': 'id_duplicado'})
        ids.add(ex['id'])
        cobertura[split]['dominio'][ex['dominio']] += 1
        cobertura[split]['tarefa'][ex['tarefa']] += 1
        grupos[ex['grupo']].add(split)
        origens[ex['source_id']].add(split)
        por_grupo[ex['grupo']] += 1
        conteudo = normalizar(ex['conteudo'])
        if conteudo in conteudos and conteudos[conteudo][1] != ex['grupo']:
            erros.append({'exemplo': i, 'erro': 'conteudo_duplicado_em_outro_grupo', 'anterior': conteudos[conteudo][0]})
        conteudos[conteudo] = (i, ex['grupo'])
        texto = normalizar(ex['mensagem'] + '\n' + ex['resposta'])
        if texto in vistos:
            erros.append({'exemplo': i, 'erro': 'par_duplicado', 'anterior': vistos[texto]})
        vistos[texto] = i
        alvo = normalizar(ex['resposta'])
        if alvo in respostas:
            erros.append({'exemplo': i, 'erro': 'resposta_repetida', 'anterior': respostas[alvo][0]})
        respostas[alvo] = (i, split)
        moldes[molde(ex['mensagem'] + '\n' + ex['resposta'])] += 1
        # Conteúdo e par são verificados separadamente; uma nova pergunta não
        # disfarça uma fonte quase idêntica nem alterações apenas numéricas.
        for tipo, texto in (('conteudo', ex['conteudo']), ('par', ex['mensagem'] + '\n' + ex['resposta'])):
            sh = shingles(texto)
            candidatos = set()
            for s in sh:
                candidatos.update(indice[(tipo, s)])
            for j in candidatos:
                ant, ant_i, ant_grupo, ant_split = anteriores[j]
                similaridade = len(sh & ant) / len(sh | ant)
                if similaridade >= politica['similaridade_proxima'] and (ant_grupo != ex['grupo'] or ant_split != split):
                    proximos.append({'exemplo': i, 'anterior': ant_i, 'tipo': tipo, 'similaridade': round(similaridade, 4)})
            j = len(anteriores)
            anteriores.append((sh, i, ex['grupo'], split))
            for s in sh:
                indice[(tipo, s)].add(j)
        # Mesmo conteúdo curto também não pode atravessar partições.
        origens['conteudo:' + hashlib.sha256(normalizar(ex['conteudo']).encode()).hexdigest()].add(split)
    for nome, tabela in (('grupo', grupos), ('fonte', origens)):
        for chave, splits in tabela.items():
            if len(splits) > 1:
                erros.append({'erro': 'vazamento_entre_particoes', 'tipo': nome, 'chave': chave})
    for grupo, n in por_grupo.items():
        if n > politica['max_exemplos_por_grupo']:
            erros.append({'erro': 'grupo_super_representado', 'grupo': grupo, 'quantidade': n})
    for split, contadores in cobertura.items():
        n = sum(contadores['dominio'].values())
        for tipo, categorias in (('dominio', politica['dominios']), ('tarefa', politica['tarefas'])):
            minimo = politica['min_por_' + tipo + ('_treino' if split == 'treino' else '_reservado')]
            for categoria in categorias:
                qtd = contadores[tipo][categoria]
                if qtd < minimo:
                    erros.append({'erro': 'cobertura_insuficiente', 'split': split, 'tipo': tipo, 'categoria': categoria, 'quantidade': qtd, 'minimo': minimo})
                if n and qtd / n > politica['max_fracao_' + tipo]:
                    erros.append({'erro': 'concentracao', 'split': split, 'tipo': tipo, 'categoria': categoria})
    n_treino = sum(cobertura['treino']['dominio'].values())
    grupos_treino = sum(splits == {'treino'} for splits in grupos.values())
    if (len(cobertura['treino']['dominio']) < politica['min_dominios'] or
            len(cobertura['treino']['tarefa']) < politica['min_tarefas']):
        erros.append({'erro': 'diversidade_insuficiente'})
    if n_treino < politica['min_exemplos_treino'] or grupos_treino < politica['min_grupos_treino']:
        erros.append({'erro': 'volume_insuficiente', 'exemplos_treino': n_treino, 'grupos_treino': grupos_treino})
    if exemplos and moldes and max(moldes.values()) / len(exemplos) > politica['max_fracao_molde']:
        erros.append({'erro': 'molde_repetitivo'})
    if proximos:
        erros.append({'erro': 'quase_duplicados', 'quantidade': len(proximos)})
    return {'apto_para_treino_completo': not erros, 'exemplos': len(exemplos),
            'grupos': len(grupos), 'cobertura': cobertura, 'quase_duplicados': proximos,
            'erros': erros, 'limite': 'Auditoria lexical e metadados não comprovam correção factual nem qualidade humana.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('corpus', type=Path)
    p.add_argument('--politica', type=Path, default=ROOT/'configs/curriculo_gerador_diverso.json')
    p.add_argument('--saida', type=Path, required=True)
    args = p.parse_args()
    dados = [json.loads(linha) for linha in args.corpus.read_text(encoding='utf-8').splitlines() if linha.strip()]
    resultado = auditar(dados, json.loads(args.politica.read_text(encoding='utf-8')))
    resultado['corpus_sha256'] = hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'exemplos': resultado['exemplos'], 'grupos': resultado['grupos'],
                      'apto_para_treino_completo': resultado['apto_para_treino_completo'], 'problemas': len(resultado['erros'])}))
    raise SystemExit(0 if resultado['apto_para_treino_completo'] else 1)


if __name__ == '__main__':
    main()
