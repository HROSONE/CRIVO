"""Snapshots imutáveis: treine no disco local, publique só entre blocos.

Não sobrescreve binários no Drive. Só remove snapshots criados por este módulo,
para o mesmo experimento/etapa, depois de verificar o substituto remoto.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile

ARQUIVOS = ('checkpoint.pt', 'pesos.pt', 'tokenizer.json', 'relatorio.json')
PERMITIDOS = set(ARQUIVOS) | {'melhor/' + n for n in ARQUIVOS}
GESTOR = 'crivo-snapshot-v1'


def digest(path, algoritmo='sha256'):
    h = hashlib.new(algoritmo)
    with Path(path).open('rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def empacotar(pasta, destino):
    """Chamado somente com o subprocesso de treino parado."""
    pasta, destino = Path(pasta), Path(destino)
    nomes = list(ARQUIVOS)
    if (pasta / 'melhor').exists():
        nomes += ['melhor/' + n for n in ARQUIVOS]
    for prefixo in ('', 'melhor/') if len(nomes) > 4 else ('',):
        r = json.loads((pasta / prefixo / 'relatorio.json').read_text())
        if digest(pasta / prefixo / 'pesos.pt') != r['pesos_sha256']:
            raise ValueError('Pesos não correspondem ao relatório; não publicar')
    manifesto = {n: {'sha256': digest(pasta / n), 'bytes': (pasta / n).stat().st_size} for n in nomes}
    with zipfile.ZipFile(destino, 'w', compression=zipfile.ZIP_STORED) as z:
        for nome in nomes:
            z.write(pasta / nome, nome)
        z.writestr('manifesto_backup.json', json.dumps(manifesto, sort_keys=True))
    return destino


def restaurar(arquivo, destino):
    """Valida tudo antes de criar o destino; nunca sobrescreve um treino."""
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError('Destino já existe; não sobrescrever checkpoint')
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as tmp:
        raiz = Path(tmp) / 'restaurado'
        raiz.mkdir()
        with zipfile.ZipFile(arquivo) as z:
            nomes = z.namelist()
            if len(nomes) != len(set(nomes)) or set(nomes) - (PERMITIDOS | {'manifesto_backup.json'}):
                raise ValueError('Arquivo inesperado ou duplicado no snapshot')
            manifesto = json.loads(z.read('manifesto_backup.json'))
            esperados = set(ARQUIVOS)
            if any(n.startswith('melhor/') for n in manifesto):
                esperados |= {'melhor/' + n for n in ARQUIVOS}
            if set(manifesto) != esperados or set(nomes) != esperados | {'manifesto_backup.json'}:
                raise ValueError('Snapshot incompleto')
            for nome, meta in manifesto.items():
                info = z.getinfo(nome)
                if info.file_size != meta['bytes'] or info.file_size > 2 * 1024**3:
                    raise ValueError('Tamanho inválido no snapshot')
                alvo = raiz / nome
                alvo.parent.mkdir(parents=True, exist_ok=True)
                with z.open(nome) as src, alvo.open('wb') as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                if digest(alvo) != meta['sha256']:
                    raise ValueError('Snapshot corrompido: ' + nome)
        raiz.rename(destino)
    return destino


def _listar(recurso, **kwargs):
    itens = []
    token = None
    while True:
        r = recurso.list(pageToken=token, **kwargs).execute()
        itens.extend(r.get('files', r.get('revisions', [])))
        token = r.get('nextPageToken')
        if not token:
            return itens


def _escapar(s):
    return str(s).replace('\\', '\\\\').replace("'", "\\'")


def _validado(meta):
    props = meta.get('appProperties', {})
    return (props.get('gestor') == GESTOR and props.get('md5') == meta.get('md5Checksum')
            and props.get('bytes') == str(meta.get('size')))


def snapshots(servico, pasta_id, experimento, etapa):
    chave = hashlib.sha256((experimento + '/' + etapa).encode()).hexdigest()
    q = ("'" + _escapar(pasta_id) + "' in parents and trashed = false "
         "and appProperties has { key='gestor' and value='" + GESTOR + "' } "
         "and appProperties has { key='execucao' and value='" + chave + "' }")
    itens = _listar(servico.files(), q=q, pageSize=100,
                    fields='nextPageToken,files(id,name,createdTime,size,md5Checksum,appProperties)',
                    orderBy='createdTime desc')
    return [i for i in itens if _validado(i) and i['appProperties'].get('execucao') == chave]


def publicar(servico, arquivo, pasta_id, experimento, etapa, manter=2, media_factory=None):
    if manter < 2:
        raise ValueError('Preservar pelo menos dois snapshots')
    if media_factory is None:
        from googleapiclient.http import MediaFileUpload
        media_factory = MediaFileUpload
    arquivo = Path(arquivo)
    md5 = digest(arquivo, 'md5')
    props = dict(gestor=GESTOR, execucao=hashlib.sha256((experimento + '/' + etapa).encode()).hexdigest(),
                 md5=md5, bytes=str(arquivo.stat().st_size))
    body = dict(name='crivo-' + etapa + '-' + uuid.uuid4().hex + '.zip', parents=[pasta_id], appProperties=props)
    novo = servico.files().create(body=body, media_body=media_factory(str(arquivo), mimetype='application/zip', resumable=True), fields='id').execute()
    meta = servico.files().get(fileId=novo['id'], fields='id,size,md5Checksum,appProperties').execute()
    if not _validado(meta) or meta['md5Checksum'] != md5:
        raise ValueError('Upload não confirmado; backups anteriores preservados')
    anteriores = [i for i in snapshots(servico, pasta_id, experimento, etapa) if i['id'] != novo['id']]
    removidos = []
    # O recém-confirmado sempre conta como uma das cópias preservadas.
    for item in anteriores[manter - 1:]:
        servico.files().delete(fileId=item['id']).execute()
        removidos.append(item['id'])
    return dict(id=novo['id'], md5=md5, removidos=removidos)


def baixar(servico, meta, destino):
    from googleapiclient.http import MediaIoBaseDownload
    destino = Path(destino)
    with destino.open('wb') as f:
        req = MediaIoBaseDownload(f, servico.files().get_media(fileId=meta['id']))
        pronto = False
        while not pronto:
            _, pronto = req.next_chunk()
    if destino.stat().st_size != int(meta['size']) or digest(destino, 'md5') != meta['md5Checksum']:
        raise ValueError('Download incompleto; não restaurar')
    return destino


def limpar_revisoes_antigas(servico, file_id, parent_id, executar=False):
    """Mantém o arquivo atual, as duas revisões mais novas e revisões fixadas.

    parent_id e nome limitam a operação aos binários do treino selecionado.
    Por padrão apenas lista. Não toca na lixeira ou em outros projetos.
    """
    meta = servico.files().get(fileId=file_id, fields='id,name,parents,headRevisionId,size').execute()
    if meta['name'] not in ('checkpoint.pt', 'pesos.pt') or parent_id not in meta.get('parents', []):
        raise ValueError('Arquivo fora da pasta de treino esperada')
    head = meta.get('headRevisionId')
    if not head or not int(meta.get('size', 0)):
        raise ValueError('Não foi possível confirmar a revisão atual')
    itens = _listar(servico.revisions(), fileId=file_id, pageSize=100,
                    fields='nextPageToken,revisions(id,modifiedTime,keepForever,size)')
    itens.sort(key=lambda x: x.get('modifiedTime', ''), reverse=True)
    preservar = {head} | {i['id'] for i in itens[:2]}
    antigos = [i for i in itens if i['id'] not in preservar and not i.get('keepForever', False)]
    removidos = []
    if executar:
        for item in antigos:
            atual = servico.files().get(fileId=file_id, fields='headRevisionId').execute()['headRevisionId']
            if item['id'] == atual:
                raise RuntimeError('Revisão atual mudou; limpeza interrompida')
            # A API só permite excluir revisões binárias marcadas keepForever.
            servico.revisions().update(fileId=file_id, revisionId=item['id'], body={'keepForever': True}).execute()
            servico.revisions().delete(fileId=file_id, revisionId=item['id']).execute()
            removidos.append(item['id'])
    return dict(arquivo=meta['name'], revisoes_antigas=len(antigos),
                bytes_historicos=sum(int(i.get('size', 0)) for i in antigos), removidas=len(removidos))
