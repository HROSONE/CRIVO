"""Preserva arquivos antigos em release DRAFT do MESMO repositório; não apaga."""
import hashlib,json,os,subprocess,urllib.request,urllib.error,zipfile
from pathlib import Path
REPO='HROSONE/CRIVO'
IDS=[11297460696,11296450260,11294207815,11193342860,11278684495]
TAG='backup-actions-20261009'
OUT=Path('backup-actions');OUT.mkdir(exist_ok=True)
assert os.environ['GITHUB_REPOSITORY']==REPO

def gh(*args):
    p=subprocess.run(['gh',*args],check=True,capture_output=True,text=True)
    return p.stdout

def api(path):return json.loads(gh('api',path))
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return 'sha256:'+h.hexdigest()
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def download(aid,path):
    request=urllib.request.Request(f'https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
    try:r=urllib.request.build_opener(NoRedirect).open(request,timeout=90)
    except urllib.error.HTTPError as e:r=e
    assert r.code in (301,302,303,307,308),'Download deve redirecionar.'
    location=r.headers['Location'];r.close()
    # Não enviar credencial do GitHub ao host do ZIP.
    with urllib.request.urlopen(location,timeout=180) as data,path.open('wb') as f:
        while True:
            b=data.read(4*1024*1024)
            if not b:break
            f.write(b)

def release():
    # A listagem pode ainda refletir a resposta anterior à criação da release.
    existing=api(f'repos/{REPO}/releases/407413740')
    assert existing['draft'] and existing['tag_name']==TAG,'Destino deve ser DRAFT.'
    return existing

def main():
    rel=release();manifest=[]
    for aid in IDS:
        meta=api(f'repos/{REPO}/actions/artifacts/{aid}')
        assert not meta['expired'] and meta.get('digest','').startswith('sha256:')
        filename=f'artifact-{aid}-{meta["name"]}.zip'
        assets=api(f'repos/{REPO}/releases/{rel["id"]}/assets?per_page=100')
        found=[a for a in assets if a['name']==filename]
        if not found:
            path=OUT/filename
            download(aid,path)
            assert path.stat().st_size==meta['size_in_bytes'],'Tamanho de origem divergente.'
            assert digest(path)==meta['digest'],'Checksum de origem divergente.'
            with zipfile.ZipFile(path) as z:assert z.testzip() is None,'ZIP inválido.'
            print(json.dumps({'download_verificado':aid,'bytes':path.stat().st_size}),flush=True)
            gh('release','upload',TAG,str(path),'--repo',REPO)
            path.unlink()
            assets=api(f'repos/{REPO}/releases/{rel["id"]}/assets?per_page=100')
            found=[a for a in assets if a['name']==filename]
        assert len(found)==1
        asset=found[0]
        assert asset['state']=='uploaded' and asset['size']==meta['size_in_bytes']
        assert asset.get('digest')==meta['digest'],'Checksum do backup divergente; não excluir origem.'
        assert api(f'repos/{REPO}/releases/{rel["id"]}')['draft'],'Release não pode ter sido publicada.'
        row={'artifact_id':aid,'artifact_name':meta['name'],'bytes':meta['size_in_bytes'],'sha256':meta['digest'],'release_id':rel['id'],'asset_id':asset['id'],'asset_name':asset['name'],'verified':True}
        manifest.append(row)
        print(json.dumps({'backup_verificado':aid,'asset_id':asset['id'],'bytes':asset['size']}),flush=True)
    p=OUT/'manifesto-backups-verificados.json';p.write_text(json.dumps(manifest,indent=2)+'\n')
    # Em retomada, não sobrescrever arquivo com conteúdo desconhecido.
    assets=api(f'repos/{REPO}/releases/{rel["id"]}/assets?per_page=100')
    previous=[a for a in assets if a['name']==p.name]
    if previous:assert len(previous)==1 and previous[0].get('digest')==digest(p)
    else:gh('release','upload',TAG,str(p),'--repo',REPO)
    print(json.dumps({'concluido':True,'arquivos':len(manifest),'bytes':sum(r['bytes'] for r in manifest),'release_draft':True}),flush=True)
if __name__=='__main__':main()
