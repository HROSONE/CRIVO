"""Separação das fontes, integridade e seleção funcional de checkpoints."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts.preparar_codigo_real import baixar_fontes, permitido, particao
from scripts.selecao_programacao import pontuacao_validacao
import importlib.util
DISPONIVEL = all(importlib.util.find_spec(n) for n in ("torch","numpy","tokenizers"))


class TestesCodigoReal(unittest.TestCase):
    def test_fontes_excluem_testes_declaracoes_e_solucoes_reservadas(self):
        for p in ('src/__tests__/add.ts','src/add.test.ts','src/add.test-d.ts',
                  'src/types.d.ts','src/unique.ts','src/binarySearch.ts','src/../segredo.ts','out/add.ts'):
            self.assertFalse(permitido(p,'src/'),p)
        self.assertTrue(permitido('src/add.ts','src/'))
        self.assertEqual(particao('add'),particao('add'))

    def test_arquivo_fixo_licenca_deduplicacao_e_sem_extracao(self):
        with tempfile.TemporaryDirectory() as td:
            cache=Path(td);arquivo=cache/'fixture.tar.gz'
            with tarfile.open(arquivo,'w:gz') as t:
                for path,texto in [('repo/LICENSE','MIT License\nPermission is hereby granted'),
                    ('repo/src/add.js','export const add = (a,b) => a+b;'),
                    ('repo/src/copia.js','export const add = (a,b) => a+b;'),
                    ('repo/src/../escape.js','throw Error();'),('repo/src/add.test.js','throw Error();')]:
                    data=texto.encode();m=tarfile.TarInfo(path);m.size=len(data);t.addfile(m,io.BytesIO(data))
            f=dict(id='fixture',prefixo='src/',licenca='LICENSE',spdx='MIT',revisao='fixa',
                   arquivo_sha256=hashlib.sha256(arquivo.read_bytes()).hexdigest())
            docs,licencas=baixar_fontes(cache,[f]);self.assertEqual(len(docs),1)
            self.assertIn('fixture',licencas);self.assertEqual(docs[0]['split'],particao('add'))
            self.assertFalse((cache/'escape.js').exists())
            arquivo.write_bytes(arquivo.read_bytes()+b'alterado')
            with self.assertRaisesRegex(ValueError,'SHA'):baixar_fontes(cache,[f])

    def test_acerto_tem_prioridade_sobre_sintaxe_e_perda(self):
        def r(corretas,compilam,ce):
            return dict(avaliacao={'dialogo':{'entropia_cruzada':ce}},funcional={'linguagens':{
                'javascript':dict(corretas=corretas,compilam=compilam,completas=4)}})
        self.assertGreater(pontuacao_validacao(r(1,1,5),'dialogo',True),pontuacao_validacao(r(0,4,.1),'dialogo',True))
        self.assertGreater(pontuacao_validacao(r(0,2,5),'dialogo',True),pontuacao_validacao(r(0,1,.1),'dialogo',True))
        self.assertGreater(pontuacao_validacao(r(1,2,1),'dialogo',True),pontuacao_validacao(r(1,2,2),'dialogo',True))

    @unittest.skipUnless(DISPONIVEL,"Dependências do laboratório opcionais")
    def test_checkpoint_funcional_nao_e_substituido_por_perda_menor(self):
        from testes_linguagem_profunda import TestesMatematicaLinguagem
        from scripts import treinar_linguagem_profunda as t
        import sys
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as td:
            pasta=Path(td);corpus=pasta/'corpus';corpus.mkdir()
            TestesMatematicaLinguagem().fixture_corpus(corpus)
            base=['treinador','--corpus',str(corpus),'--lote','2','--dimensao','24','--camadas','1',
                  '--cabecas','3','--contexto','16','--threads','1','--avaliar-a-cada','1',
                  '--salvar-a-cada','1','--dispositivo','cpu']
            with patch.object(sys,'argv',base+['--saida',str(pasta/'pre'),'--fase','linguagem','--passos','1']),redirect_stdout(io.StringIO()):t.main()
            def ce(v):return {f:dict(entropia_cruzada=v,perplexidade=2.,tokens_avaliados=8,particao='validacao') for f in ('linguagem','dialogo')}
            acertos=iter([0,1,0])
            def avaliar(cmd,**kw):
                path=Path(cmd[cmd.index('--saida')+1]);modelo=Path(cmd[cmd.index('--modelo')+1]);n=next(acertos)
                path.write_text(json.dumps(dict(particao='validacao',pesos_sha256=t.sha(modelo/'pesos.pt'),
                    fontes_sha256={},isolamento=True,linguagens={'javascript':dict(corretas=n,compilam=1,completas=1)})))
            args=base+['--saida',str(pasta/'sft'),'--fase','dialogo','--passos','2','--inicial',str(pasta/'pre'),
                       '--selecionar-melhor','--validacao-funcional','--tsc','fixture']
            with patch.object(sys,'argv',args),patch.object(t,'avaliar',side_effect=[ce(3),ce(2),ce(1)]),patch.object(t.subprocess,'run',side_effect=avaliar),redirect_stdout(io.StringIO()):t.main()
            best=json.loads((pasta/'sft/melhor/relatorio.json').read_text());last=json.loads((pasta/'sft/relatorio.json').read_text())
            self.assertEqual(best['passo'],1);self.assertEqual(last['passo'],2)
            self.assertEqual(best['historico'][-1]['funcional']['linguagens']['javascript']['corretas'],1)
            self.assertEqual(last['historico'][-1]['avaliacao']['dialogo']['entropia_cruzada'],1)
            self.assertTrue((pasta/'sft/checkpoint.pt').exists())


if __name__=='__main__':unittest.main()
