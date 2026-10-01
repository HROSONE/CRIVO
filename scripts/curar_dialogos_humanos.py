"""Seleciona texto humano público; nunca executa ou carrega um modelo externo.

Critérios de seleção definidos pela tarefa, sem acesso a qualquer sonda do Crivo.
Entradas: mensagens PT-BR do arquivo ready.messages, na revisão HF indicada.
Saídas preservam textos completos: não resumem, não traduzem e não truncam.
"""
import argparse
import collections
import gzip
import hashlib
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
DADOS = ROOT / 'dados'
REVISION = '179dd21fc55192153d94adb0e0ce8f69e222bf75'
DATASET = 'https://huggingface.co/datasets/OpenAssistant/oasst2'


def normalizar(texto):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', texto).casefold()).strip()


def tokens(texto):
    return re.findall(r'\w+|[^\w\s]', texto, re.UNICODE)


def etiquetas(mensagem):
    return {nome: item.get('value', 0) for nome, item in (mensagem.get('labels') or {}).items()}


def revisada(mensagem):
    if mensagem is None:
        return False
    e = etiquetas(mensagem)
    return (mensagem.get('review_result') is True and not mensagem.get('deleted')
            and mensagem.get('synthetic') is False
            and all(k in e and e[k] <= .1 for k in
                    ('spam', 'lang_mismatch', 'pii', 'not_appropriate', 'hate_speech',
                     'sexual_content', 'toxicity', 'violence')))


# Árvores identificadas por leitura humana dos pedidos de raiz, antes de filtrar
# respostas: escrita/reescrita/criação, diálogo social, esclarecimento de pedido,
# decisões cotidianas, relações pessoais e reflexão sem alegação factual específica.
# Ramos posteriores ainda passam pelos filtros de escopo abaixo.
arvores_conversacionais = set(json.loads((DADOS / 'selecao_arvores_oasst2.json').read_text(encoding='utf-8'))['arvores'])

# Revisão humana local identifica contradições simples em targets que receberam
# notas positivas no corpus. Recusar mantém o original intacto; não inventa correção.
erros_humanos = {
    'c3a94904-b985-4dbe-8660-10e28fa47b18': 'Afirma que Amor tem três letras e que A é consoante.',
    'dea9a20a-7d05-46f1-af1b-c1b76e2435e0': 'Correção conserva afim quando a expressão é a fim.',
    'ca2cee62-5d04-474c-aa6f-8a75f583af58': 'Muda desenho com apenas lápis para aquarela.',
    '9cc7060c-3ac9-4667-851a-2fb417180b9e': 'Concordância minha querido amigo.',
    'd81a74f5-222b-4ec1-b1de-4e4769d1d9a5': 'Recita obra existente ao invés de criar texto de estilo.',
    '124367e2-c243-407a-97bd-0c306c9d7e1c': 'Réplica duplicada com erro curríclo.',
    'c0003fd1-d6f6-412c-ad4f-c539d056d015': 'Apresenta lista ampla de capacidades não garantidas para o Crivo.',
    'afaa7431-ecec-4fcf-a3cf-29cb7c5fe16d': 'Apresenta capacidades amplas e conhecimento científico não garantidos.',
    '2017383f-2b87-456a-b562-d99738d5e075': 'Anúncio promete melhor do mercado sem fundamento e tem erros.',
    '6f78e1e9-da92-4a3c-bfd7-612cfc15539d': 'Sugere água e pincel quando o pedido permite somente lápis e papel.',
    '390bc9bd-69a6-4d28-9902-acc51d4dc581': 'Planeja cinco dias apesar de a apresentação ocorrer amanhã no histórico.',
    '9f648f55-ce69-4337-9995-74ab0ee361d5': 'Planeja cinco dias apesar de a apresentação ocorrer amanhã no histórico.',
    'f0cb7631-f40a-4db9-a6e6-974d2cf1944e': 'Não inclui a palavra amora solicitada; troca-a por amoras.',
    '6519157c-11e0-41fd-aaf2-6d5914f3314b': 'Inclui preâmbulo com palavras que não começam com c apesar da restrição apenas.',
    'f8ef13a0-9563-4526-8709-dd06f5b38cbc': 'O poema solicitado com rimas não segue a restrição.',
    'fcd3a597-a974-4c96-9cf2-fb18400f2497': 'Promete lucrar alto sem fundamento e recomenda plataformas sem verificação.',
    '48244e10-d5d8-4a25-9a5b-6a7554ba5250': 'O pedido exige todas as palavras citadas; o poema omite várias.',
    '77edf698-608b-451d-a383-82465fa30d38': 'Contém compactuamento, erro de linguagem no alvo.',
    'ae758049-3efe-4672-8c34-64ddadd91211': 'Pede sugestões de protagonistas, mas o alvo dá dicas genéricas e repete um item.',
}

fora_escopo = re.compile(
    r'https?://|www\.|```|\b(?:python|javascript|typescript|sql|iptables|xorg|grub|'
    r'linux|windows|macos|fastapi|tensorflow|pytorch|transformers|algoritmo|'
    r'compilador|fatorial|equação|teorema|cálculo|paroxetina|medicamento|'
    r'diagnóstico|diagnostico|doença|doenca|depressão|depressao|deprimid\w*|'
    r'transtorno|terapia|suicíd\w*|suicid\w*|veterinário|veterinario|'
    r'sexual\w*|sexo|erótic\w*|erotic\w*|picante|nua|nuas|'
    r'violência|violencia|abus\w*|guerra\w*|ataque\w*|assassin\w*|'
    r'matar|morte|mortos|sangue|arma|armas|sniper|vingativ\w*|'
    r'cracolândia|cracolandia|drog\w*|tortura\w*|'
    r'constituição|constituicao|legislação|legislacao|regulamentação|'
    r'estatístic\w*|estatistic\w*|científic\w*|cientific\w*|pesquisas científicas|'
    r'chatgpt|openassistant|open assistant|openai|oa|'
    r'fotossíntese|fotossintese|nucleares|fissão|fissao|evolução|evolucao|'
    r'covid|inflação|inflacao|criptomoeda\w*|blockchain|biológico|biologica|'
    r'capital inicial|lucratividade|retorno a curto prazo|'
    r'senha\w*|senha forte)\b', re.IGNORECASE)
pedidos_factuais = re.compile(
    r'\b(?:tradicional do brasil|quais mesas digitalizadoras|quais softwares|'
    r'de acordo com a ciência|de acordo com a ciencia|de acordo com estudos|'
    r'baseado em estudos|comunidade científica|comunidade cientifica|'
    r'cite fontes|fontes que|frases famosas|citações|citacoes|'
    r'recomendações do mercado|recomendacoes do mercado|biografia|'
    r'necessidades do mercado brasileiro|startup|startups|google ads|'
    r'decreto-lei|coluna|ergonômica|ergonomica|antebraços|antebracos|músculos|musculos)\b', re.IGNORECASE)
referencias_ou_contatos = re.compile(
    r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|'
    r'\b(?:[A-Za-z0-9-]+\.)+(?:com|org|net|edu|gov|io)(?:\.br)?\b|'
    r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|'
    r'(?<!\w)(?:\+?55\s*)?\(?\d{2}\)?\s*\d{4,5}[- ]\d{4}(?!\w)',
    re.IGNORECASE)
somente_abertura = {'408a6977-5916-4a82-86a2-5dbd774b983e',
                   '7b46c00f-38f4-4aba-8d46-4e8f290ebde7',
                   'b0e1c781-0d61-4df7-b858-9d1a5cb40bb3'}

ARQUIVO_ORIGEM = '2023-11-05_oasst2_ready.messages.jsonl.gz'
URL_ORIGEM = DATASET + '/resolve/' + REVISION + '/' + ARQUIVO_ORIGEM
SHA256_ARQUIVO_ORIGEM = 'a9f240c4c77aa1378364f70d37e753c07ba284e247b019d700e1947a0e5da751'
SHA256_MENSAGENS_PT = '9ee9fc94b7c4acb06e4764090f6d15236b399fd02953e8fda7eacaf0b83e753e'
SEMENTE_SPLIT = 'crivo-oasst2-conversa-v1:'


def ler_mensagens(caminho):
    """Aceita a exportação pública completa ou sua extração PT-BR, sem dependências."""
    abrir = gzip.open if str(caminho).endswith('.gz') else open
    mensagens = []
    with abrir(caminho, 'rt', encoding='utf-8') as arquivo:
        for linha in arquivo:
            if linha.strip():
                mensagem = json.loads(linha)
                if mensagem.get('lang') == 'pt-BR':
                    mensagens.append(mensagem)
    if len({m['message_id'] for m in mensagens}) != len(mensagens):
        raise ValueError('message_id duplicado na origem')
    canonico = json.dumps(sorted(mensagens, key=lambda m: m['message_id']),
                          ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    if hashlib.sha256(canonico).hexdigest() != SHA256_MENSAGENS_PT:
        raise ValueError('A origem PT-BR difere da revisão pública documentada; não atribuir outra origem a OASST2')
    return mensagens


def caminho_revisado(pedido, indice, grupo):
    caminho, vistos = [], set()
    atual = pedido
    while atual is not None:
        ident = atual['message_id']
        if ident in vistos or not revisada(atual) or atual.get('message_tree_id') != grupo:
            return None
        vistos.add(ident)
        caminho.append(atual)
        parent_id = atual.get('parent_id')
        if parent_id is None:
            if ident != grupo or atual.get('role') != 'prompter':
                return None
            break
        atual = indice.get(parent_id)
        if atual is None:
            return None
    caminho.reverse()
    if any(m.get('role') != ('prompter' if i % 2 == 0 else 'assistant')
           for i, m in enumerate(caminho)):
        return None
    return caminho


def selecionar(mensagens):
    indice = {m['message_id']: m for m in mensagens}
    recusas = collections.Counter()
    selecionados, vistos = [], set()
    candidatos = 0
    for resposta in mensagens:
        if resposta.get('role') != 'assistant':
            continue
        pedido = indice.get(resposta.get('parent_id'))
        if not pedido or pedido.get('role') != 'prompter' or not revisada(resposta):
            recusas['resposta ou pedido não revisado'] += 1
            continue
        grupo = resposta['message_tree_id']
        caminho = caminho_revisado(pedido, indice, grupo)
        if caminho is None:
            recusas['ancestral não revisado ou estrutura inválida'] += 1
            continue
        candidatos += 1
        if grupo not in arvores_conversacionais:
            recusas['raiz factual/técnica fora do escopo'] += 1
            continue
        if any(m['message_id'] in erros_humanos for m in caminho + [resposta]):
            recusas['erro de conteúdo humano no alvo ou ancestral'] += 1
            continue
        qualidade = etiquetas(resposta).get('quality')
        if qualidade is not None and qualidade < .5:
            recusas['qualidade rotulada abaixo de 0,5'] += 1
            continue
        if grupo in somente_abertura and len(caminho) > 1:
            recusas['ramo factual posterior à abertura social'] += 1
            continue
        textos = [m['text'] for m in caminho] + [resposta['text']]
        if any(fora_escopo.search(t) or pedidos_factuais.search(t)
               or referencias_ou_contatos.search(t) for t in textos):
            recusas['conteúdo fora do escopo, contato ou referência factual'] += 1
            continue
        if len(tokens(resposta['text'])) < 6:
            recusas['resposta curta demais para treino de diálogo'] += 1
            continue
        chave = tuple(normalizar(t) for t in textos)
        if chave in vistos:
            recusas['texto/contexto duplicado'] += 1
            continue
        vistos.add(chave)
        historico = [{'papel': 'usuario' if m['role'] == 'prompter' else 'assistente',
                     'texto': m['text']} for m in caminho[:-1]]
        bucket = int(hashlib.sha256((SEMENTE_SPLIT + grupo).encode('utf-8')).hexdigest()[:8], 16) % 10
        selecionados.append({'mensagem': pedido['text'], 'resposta': resposta['text'],
                             'historico': historico, 'source_id': resposta['message_id'],
                             'grupo': grupo, 'split': 'validacao' if bucket == 0 else 'treino'})
    selecionados.sort(key=lambda e: (e['grupo'], e['source_id']))
    return selecionados, candidatos, dict(recusas)


def sha_exemplos(exemplos):
    conteudo = json.dumps(exemplos, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(conteudo).hexdigest()


def gerar_corpus(caminho):
    mensagens = ler_mensagens(caminho)
    exemplos, candidatos, recusas = selecionar(mensagens)
    comprimentos = [{'source_id': e['source_id'], 'split': e['split'],
                    'fonte_tokens': sum(len(tokens(t['texto'])) for t in e['historico'])
                    + len(tokens(e['mensagem'])),
                    'resposta_tokens': len(tokens(e['resposta']))}
                   for e in exemplos]
    grupos_treino = {e['grupo'] for e in exemplos if e['split'] == 'treino'}
    grupos_validacao = {e['grupo'] for e in exemplos if e['split'] == 'validacao'}
    if grupos_treino & grupos_validacao:
        raise ValueError('Vazamento de árvore entre treino e validação')
    indice_bytes = (DADOS / 'selecao_arvores_oasst2.json').read_bytes()
    return {'versao': 1,
            'fonte': {'dataset': DATASET, 'revisao': REVISION,
                      'arquivo': ARQUIVO_ORIGEM, 'url': URL_ORIGEM,
                      'sha256_arquivo_gz': SHA256_ARQUIVO_ORIGEM,
                      'sha256_mensagens_pt_canonicas': SHA256_MENSAGENS_PT,
                      'licenca': 'Apache-2.0',
                      'origem': 'Mensagens públicas com synthetic=false e review_result=true.',
                      'idioma_rotulado': 'pt-BR'},
            'curadoria': {
                'script': 'scripts/curar_dialogos_humanos.py',
                'sha256_indice_arvores': hashlib.sha256(indice_bytes).hexdigest(),
                'sha256_exemplos': sha_exemplos(exemplos),
                'mensagens_pt_br_origem': len(mensagens),
                'pares_candidatos_revisados': candidatos,
                'pares_selecionados': len(exemplos),
                'arvores': len(grupos_treino | grupos_validacao),
                'particoes': dict(collections.Counter(e['split'] for e in exemplos)),
                'arvores_por_particao': {'treino': len(grupos_treino), 'validacao': len(grupos_validacao)},
                'com_historico': sum(bool(e['historico']) for e in exemplos),
                'criterios': [
                    'Revisão manual de raízes de conversa, escrita, criação, reflexão e decisões cotidianas.',
                    'Todo o caminho ancestral revisado, não apagado, não sintético e com árvore/alternância válida.',
                    'Rótulos spam/lang_mismatch/pii/not_appropriate/hate_speech/sexual_content/toxicity/violence <= 0.1.',
                    'Qualidade do alvo >= 0.5 quando rotulada; descarte de erros explícitos e seus descendentes.',
                    'Sem código ou consultas técnicas; sem alegações especializadas médicas/jurídicas/financeiras, contatos/URLs ou identidade de outro assistente.',
                    'Deduplicação de texto normalizado com contexto; árvore inteira em uma partição por hash fixo.',
                    'Textos preservados inteiros: sem correção, resumo, tradução, truncamento ou geração de respostas.',
                    'Somente texto, papéis e IDs públicos de mensagem/árvore; sem user_id, datas, eventos ou autoria pessoal.',
                    'Nenhuma sonda congelada, conversa privada do usuário, base de fatos ou saída do Crivo usada na seleção.'
                ],
                'descartes': recusas,
                'erros_humanos_revisados': erros_humanos,
                'split': {'algoritmo': 'sha256(semente + message_tree_id), primeiros 8 dígitos hex módulo 10; 0 = validação',
                          'semente': SEMENTE_SPLIT},
                'perfis_completos': {
                    f'fonte{s}_resposta{r}': sum(x['fonte_tokens'] <= s and x['resposta_tokens'] <= r
                                              for x in comprimentos)
                    for s, r in ((192, 63), (192, 95), (256, 96), (384, 192), (1024, 512))},
                'tokenizador_perfis': r'\w+|[^\w\s], sem tokens de papel; o treinador aplica seu limite próprio',
                'limites': [
                    'Subconjunto pequeno e manual; útil como dado complementar, não evidência de conversa geral.',
                    'A origem humana é a rotulagem do corpus; não foi feita verificação independente de autoria.',
                    'Revisões humanas não garantem veracidade ou perfeição de todas as frases.',
                    'OASST2 já engloba OASST1; não concatenar as versões sem deduplicação.',
                    'Treinar somente os exemplos treino; nunca ampliar artificialmente a contagem de diálogos humanos.'
                ]},
            'exemplos': exemplos}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonte', type=pathlib.Path, required=True,
                        help='Exportação ready.messages.jsonl(.gz), ou extração PT-BR dela')
    parser.add_argument('--saida', type=pathlib.Path, default=DADOS / 'dialogos_humanos.json')
    args = parser.parse_args()
    corpus = gerar_corpus(args.fonte)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: corpus['curadoria'][k] for k in
                     ('pares_selecionados', 'arvores', 'particoes', 'com_historico',
                      'perfis_completos', 'sha256_exemplos')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
