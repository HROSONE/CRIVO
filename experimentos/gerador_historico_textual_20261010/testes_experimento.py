"""Integridade dos dados/isolamento; não certifica qualidade de conversa."""
import gzip
import hashlib
import json
import sys
import unittest
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import protocolo, triagem, RAIZ
from dialogo_seq2seq import fonte_dialogo, tokenizar, vocabulario_treino


class IntegridadeExperimento(unittest.TestCase):
    def test_holdout_preservado_e_pedido_dono_ausente_do_treino(self):
        p=protocolo()
        self.assertEqual(p['sha256_avaliacao'],'70bfd19538677e6f617f0ab79b8a3856e844d9b3600865d876442e69f4e72d01')
        teste=json.loads((DIR/'avaliacao_congelada.json').read_text())
        for arquivo in ['corpus.json','corpus_rodada2.json']:
            corpus=json.loads((DIR/arquivo).read_text())['exemplos']
            entradas={e['mensagem'] for e in corpus}
            self.assertNotIn(teste['pedido_do_dono']['mensagem'],entradas)
            for sessao in teste['sessoes']:
                for turno in sessao['turnos']:
                    self.assertNotIn(turno['mensagem'],entradas)
            texto=json.dumps(corpus,ensure_ascii=False).casefold()
            for termo in ['dinossauro','meteoro','Wexina'.casefold(),'Zelún'.casefold(),'Iverna'.casefold(),'Adriel'.casefold()]:
                self.assertNotIn(termo,texto)

    def test_split_familias_rodada1_e_sem_duplicatas_rodada2(self):
        antigo=json.loads((DIR/'corpus.json').read_text())['exemplos']
        self.assertFalse({e['familia'] for e in antigo if e['split']=='treino'} &
                         {e['familia'] for e in antigo if e['split']=='validacao'})
        novo=json.loads((DIR/'corpus_rodada2.json').read_text())['exemplos']
        def entradas(split):
            return {json.dumps([e['mensagem'],e['historico']],sort_keys=True,ensure_ascii=False)
                    for e in novo if e['split']==split}
        self.assertFalse(entradas('treino') & entradas('validacao'))
        self.assertEqual(len(novo),len(entradas('treino'))+len(entradas('validacao')))

    def test_corpus_sem_truncamento_e_sem_alvos_impossiveis(self):
        corpus=json.loads((DIR/'corpus_rodada2.json').read_text())['exemplos']
        vocab=vocabulario_treino([e for e in corpus if e['split']=='treino'],720)
        for e in corpus:
            fonte=fonte_dialogo(e['mensagem'],e['historico'],192)
            bruto=1+len(tokenizar(e['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in e['historico'])
            self.assertEqual(len(fonte),bruto)
            self.assertLessEqual(len(tokenizar(e['resposta']))+1,64)
            self.assertFalse(set(tokenizar(e['resposta']))-set(vocab)-set(fonte))

    def test_juiz_rejeita_referencia_anterior_mesmo_com_nova_presente(self):
        t={'exige_qualquer_por_grupo':[['domingo']],'proibidos':['quarta']}
        saida={'texto':'É domingo, ou talvez quarta.','tokens':['É','domingo','quarta'],'completa':True}
        self.assertFalse(triagem(saida,t)['passou_triagem'])

    def test_checkpoint_isolado_e_orcamento(self):
        for nome in ['checkpoint.json.gz','checkpoint_rodada2.json.gz']:
            path=DIR/nome
            if not path.exists():
                continue
            modelo=json.loads(gzip.decompress(path.read_bytes()))
            self.assertIs(modelo['aprovado'],False)
            self.assertIs(modelo['ativo_no_chat'],False)
            self.assertLessEqual(modelo['treino']['parametros'],85130)
        # Arquivos que integram geração não podem referenciar esta rodada.
        for nome in ['conversa_dialogo.py','web_core.py','crivo.py']:
            self.assertNotIn('gerador_historico_textual_20261010',(RAIZ/nome).read_text())


if __name__=='__main__':
    unittest.main()
