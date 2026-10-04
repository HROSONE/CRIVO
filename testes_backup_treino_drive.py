"""Retenção, integridade e isolamento dos backups sem acessar o Drive real."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock
import zipfile

from scripts.backup_treino_drive import (ARQUIVOS, GESTOR, empacotar, restaurar,
                                         publicar, limpar_revisoes_antigas)


class TestesBackupDrive(unittest.TestCase):
    def fixture(self, pasta):
        pasta.mkdir()
        for prefixo in ('', 'melhor'):
            p = pasta / prefixo
            p.mkdir(exist_ok=True)
            for nome in ARQUIVOS:
                (p / nome).write_bytes(b'checkpoint de teste')
            (p / 'relatorio.json').write_text(json.dumps(dict(
                pesos_sha256=hashlib.sha256((p / 'pesos.pt').read_bytes()).hexdigest())))

    def test_roundtrip_preserva_todos_bytes_e_nao_sobrescreve(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); self.fixture(p/'origem')
            empacotar(p/'origem', p/'a.zip')
            restaurar(p/'a.zip', p/'restaurado')
            for f in (p/'origem').rglob('*'):
                if f.is_file(): self.assertEqual(f.read_bytes(), (p/'restaurado'/f.relative_to(p/'origem')).read_bytes())
            with self.assertRaises(FileExistsError): restaurar(p/'a.zip', p/'restaurado')

    def test_corrupcao_e_caminho_externo_nao_criam_destino(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); self.fixture(p/'origem'); empacotar(p/'origem',p/'bom.zip')
            with zipfile.ZipFile(p/'bom.zip') as z:
                dados={n:z.read(n) for n in z.namelist()}
            for nome in ('pesos.pt','../escape'):
                d=dict(dados); d[nome]=b'alterado'
                with zipfile.ZipFile(p/'ruim.zip','w') as z:
                    for n,b in d.items(): z.writestr(n,b)
                with self.assertRaises(ValueError): restaurar(p/'ruim.zip',p/'destino')
                self.assertFalse((p/'destino').exists())
                self.assertFalse((p/'escape').exists())

    def test_relatorio_incompativel_impede_upload(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); self.fixture(p/'origem'); (p/'origem/pesos.pt').write_bytes(b'outro')
            with self.assertRaises(ValueError): empacotar(p/'origem',p/'a.zip')

    def servico(self, arquivo):
        s=MagicMock(); f=s.files.return_value
        f.create.return_value.execute.return_value={'id':'novo'}
        props=dict(gestor=GESTOR,execucao=hashlib.sha256(b'run/dialogo').hexdigest(),
                   md5=hashlib.md5(arquivo.read_bytes()).hexdigest(),bytes=str(arquivo.stat().st_size))
        def meta(id): return dict(id=id,md5Checksum=props['md5'],size=props['bytes'],appProperties=dict(props))
        f.get.return_value.execute.return_value=meta('novo')
        estranho=meta('outro-projeto'); estranho['appProperties']['execucao']='outra'
        f.list.return_value.execute.return_value={'files':[meta('novo'),meta('anterior'),meta('antigo'),estranho]}
        return s

    def test_so_apaga_snapshot_antigo_apos_confirmar_novo(self):
        with tempfile.TemporaryDirectory() as td:
            arquivo=Path(td)/'a.zip';arquivo.write_bytes(b'backup')
            s=self.servico(arquivo)
            r=publicar(s,arquivo,'pasta','run','dialogo',media_factory=MagicMock())
            self.assertEqual(r['removidos'],['antigo'])
            s.files().delete.assert_called_once_with(fileId='antigo')
            self.assertIn("'pasta' in parents",s.files().list.call_args.kwargs['q'])
            s.files().update.assert_not_called()

    def test_upload_falho_ou_checksum_diferente_preservam_anteriores(self):
        with tempfile.TemporaryDirectory() as td:
            arquivo=Path(td)/'a.zip';arquivo.write_bytes(b'backup')
            for falha in ('rede','checksum'):
                s=self.servico(arquivo)
                if falha=='rede': s.files().create.return_value.execute.side_effect=RuntimeError('rede')
                else: s.files().get.return_value.execute.return_value['md5Checksum']='invalido'
                with self.assertRaises((RuntimeError,ValueError)):
                    publicar(s,arquivo,'pasta','run','dialogo',media_factory=MagicMock())
                s.files().delete.assert_not_called()

    def test_limpeza_preserva_head_mais_novas_e_fixadas(self):
        s=MagicMock(); s.files().get.return_value.execute.return_value=dict(
            name='checkpoint.pt',parents=['pasta'],headRevisionId='atual',size='100')
        s.revisions().list.return_value.execute.return_value={'revisions':[
            dict(id='velha',modifiedTime='1',size='100'),
            dict(id='fixada',modifiedTime='2',keepForever=True,size='100'),
            dict(id='penultima',modifiedTime='3',size='100'),
            dict(id='atual',modifiedTime='4',size='100')]}
        r=limpar_revisoes_antigas(s,'arquivo','pasta')
        self.assertEqual(r['revisoes_antigas'],1)
        s.revisions().delete.assert_not_called()
        r=limpar_revisoes_antigas(s,'arquivo','pasta',executar=True)
        self.assertEqual(r['removidas'],1)
        s.revisions().delete.assert_called_once_with(fileId='arquivo',revisionId='velha')
        s.files().delete.assert_not_called()
        with self.assertRaises(ValueError): limpar_revisoes_antigas(s,'arquivo','outro-projeto',True)


class TestesNotebookRecuperacao(unittest.TestCase):
    def notebook(self):
        import ast
        raiz=Path(__file__).resolve().parent
        n=json.loads((raiz/'notebooks/recuperar_dialogo_colab.ipynb').read_text())
        for c in n['cells']:
            if c['cell_type']=='code': ast.parse(''.join(c['source']))
        return n

    def test_executar_tudo_nao_inicia_gpu_por_padrao(self):
        from contextlib import redirect_stdout
        import io
        s=''.join(self.notebook()['cells'][5]['source'])
        sub=MagicMock()
        with redirect_stdout(io.StringIO()): exec(s,{'subprocess':sub})
        sub.run.assert_not_called()

    def test_retomada_nao_mistura_inicial_e_adam_e_retry_confirma_backup_primeiro(self):
        import ast
        import io
        import shutil
        import sys
        from contextlib import redirect_stdout
        from unittest.mock import patch
        from scripts.backup_treino_drive import digest
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); origem=p/'original'; fonte=origem/'pretreino/melhor'; fonte.mkdir(parents=True)
            (fonte/'pesos.pt').write_bytes(b'pesos'); (fonte/'tokenizer.json').write_text('{}')
            (fonte/'relatorio.json').write_text(json.dumps({'pesos_sha256':digest(fonte/'pesos.pt')}))
            (origem/'corpus_manifesto.json').write_text('{}')
            corpus=p/'crivo-corpus-dialogos-amplos'; corpus.mkdir();(corpus/'manifesto.json').write_text('{}')
            fonte_codigo=''.join(self.notebook()['cells'][5]['source']).replace('/content/',str(p)+'/')
            fonte_codigo=fonte_codigo.replace('TREINAR_PILOTO = False','TREINAR_PILOTO = True')
            comandos=[]; eventos=[]
            def run(cmd,**kwargs):
                if 'scripts/treinar_linguagem_profunda.py' not in cmd:return
                eventos.append('treino'); comandos.append(cmd)
                self.assertNotEqual('--retomar' in cmd,'--inicial' in cmd)
                etapa=Path(cmd[cmd.index('--saida')+1]); etapa.mkdir(exist_ok=True)
                passo=int(cmd[cmd.index('--parar-em')+1])
                r=dict(passo=passo,concluido=passo>=300,historico=[{'avaliacao':{}}])
                (etapa/'checkpoint.pt').write_bytes(b'checkpoint')
                (etapa/'relatorio.json').write_text(json.dumps(r))
                (etapa/'melhor').mkdir(exist_ok=True)
                (etapa/'melhor/relatorio.json').write_text(json.dumps(r))
            def upload(*args,**kwargs):
                eventos.append('backup')
                if eventos.count('backup')==1: raise RuntimeError('Rede indisponível')
                return {'id':'backup-verificado'}
            servico=MagicMock();servico.files().create.return_value.execute.return_value={'id':'pasta'}
            env=dict(Path=Path,subprocess=MagicMock(run=run),sys=sys,json=json,shutil=shutil,
                     LOCAL=None,ORIGEM=origem,ROOT=p,rec={},REVISAO='abc',digest=digest,
                     registro={'experimento':'run'},PONTEIRO_RECUPERACAO=p/'ponteiro.json',
                     servico=servico,snapshots=lambda *a:[],empacotar=MagicMock(),publicar=upload)
            torch_falso=MagicMock();torch_falso.cuda.is_available.return_value=True
            with patch.dict(sys.modules,{'torch':torch_falso}), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError,'Rede indisponível'):exec(fonte_codigo,env)
                self.assertEqual(eventos,['treino','backup'])
                self.assertTrue((p/'crivo-recuperacao-v1/backup_pendente').exists())
                exec(fonte_codigo,env)
            self.assertEqual(eventos[:4],['treino','backup','backup','treino'])
            self.assertEqual(len(comandos),3)
            self.assertIn('--inicial',comandos[0])
            self.assertIn('--retomar',comandos[1])
            self.assertFalse((p/'crivo-recuperacao-v1/backup_pendente').exists())


if __name__ == '__main__': unittest.main()
