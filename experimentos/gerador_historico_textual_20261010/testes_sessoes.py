"""Integridade de sessões/vocabulário; não certifica conversa natural."""
import sys
import unittest
from pathlib import Path
DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import sha,RAIZ
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq,tokenizar,fonte_dialogo,ESPECIAIS


class IntegridadeSessoes(unittest.TestCase):
    def test_holdout_preservado_e_fora_corpus(self):
        self.assertEqual(sha(DIR/'avaliacao_sessoes_congelada.json'),
            '13ca31d6a2702fc9c8b7c8ba8ef2129513174d520feb4d66aae016f5aaeb3500')
        corpus=ler_json(DIR/'corpus_sessoes.json.gz')['exemplos']
        texto=str(corpus);entradas={e['mensagem'] for e in corpus}
        for nome in ['Ezulma','Frenel','Dralune','Valúrio','Selmira','Vrasel','Izelta','Umévia']:
            self.assertNotIn(nome,texto)
        for s in ler_json(DIR/'avaliacao_sessoes_congelada.json')['sessoes']:
            self.assertEqual(len(s['turnos']),6)
            for t in s['turnos']:self.assertNotIn(t['mensagem'],entradas)
        self.assertNotIn(ler_json(DIR/'avaliacao_congelada.json')['pedido_do_dono']['mensagem'],entradas)

    def test_desenvolvimento_antigo_preservado_e_familias_novas_separadas(self):
        import json
        antigo=ler_json(DIR/'corpus_contrastes.json.gz')['exemplos']
        novo=ler_json(DIR/'corpus_sessoes.json.gz')['exemplos']
        def chave(e):return json.dumps([e['mensagem'],e.get('historico',[]),e['resposta']],sort_keys=True)
        self.assertTrue({chave(e) for e in antigo if e['split']=='validacao'} <=
            {chave(e) for e in novo if e['split']=='validacao'})
        familias={split:{e['familia'] for e in novo if e['split']==split and e['grupo']=='sessao_completa'}
            for split in ['treino','validacao']}
        self.assertEqual(len(familias['treino']),32);self.assertEqual(len(familias['validacao']),4)
        self.assertFalse(familias['treino'] & familias['validacao'])

    def test_fontes_inteiras_e_alvos_geraveis(self):
        vocab=set(ler_json(DIR/'inicializacao_sessoes.json.gz')['vocabulario'])
        for e in ler_json(DIR/'corpus_sessoes.json.gz')['exemplos']:
            hist=e.get('historico',[]);src=fonte_dialogo(e['mensagem'],hist,192)
            self.assertEqual(len(src),1+len(tokenizar(e['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in hist))
            self.assertLessEqual(len(tokenizar(e['resposta']))+1,64)
            self.assertFalse(set(tokenizar(e['resposta']))-vocab-set(src))

    def test_realocacao_preserva_palavras_mantidas_e_todos_pesos_recorrrentes(self):
        import numpy as np
        a=ler_json(DIR/'checkpoint_contrastes.json.gz');b=ler_json(DIR/'inicializacao_sessoes.json.gz')
        self.assertEqual(a['vocabulario'][:len(ESPECIAIS)],b['vocabulario'][:len(ESPECIAIS)])
        self.assertEqual(len(set(b['vocabulario'])),720)
        modelo=DialogoSeq2Seq(b)
        self.assertEqual(sum(np.asarray(v).size for v in b['pesos'].values()),81433)
        for i,(velha,nova) in enumerate(zip(a['vocabulario'],b['vocabulario'])):
            if velha==nova:
                np.testing.assert_array_equal(a['pesos']['E'][i],b['pesos']['E'][i])
                np.testing.assert_array_equal(np.asarray(a['pesos']['O'])[:,i],np.asarray(b['pesos']['O'])[:,i])
                self.assertEqual(a['pesos']['bo'][i],b['pesos']['bo'][i])
        for k in a['pesos']:
            if k not in ['E','O','bo']:np.testing.assert_array_equal(a['pesos'][k],b['pesos'][k])

    def test_isolado_sem_catalogo_e_producao_inalterada(self):
        for nome in ['inicializacao_sessoes.json.gz','checkpoint_sessoes.json.gz','checkpoint_sessoes_refinado.json.gz']:
            path=DIR/nome
            if not path.exists():continue
            d=ler_json(path)
            self.assertIs(d['aprovado'],False);self.assertIs(d['ativo_no_chat'],False)
            self.assertFalse({'respostas','exemplos','catalogo'} & d.keys())
            self.assertEqual(d['vocabulario'],ler_json(DIR/'inicializacao_sessoes.json.gz')['vocabulario'])
            self.assertEqual(len(d['vocabulario']),720)
            if nome!='inicializacao_sessoes.json.gz':self.assertEqual(d['treino']['parametros'],81433)
        for nome,hash_base in ler_json(DIR/'auditoria.json')['pesos_raiz_preservados'].items():
            self.assertEqual(sha(RAIZ/nome),hash_base)


if __name__=='__main__':unittest.main()
