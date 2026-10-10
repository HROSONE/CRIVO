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
    def test_contrastes_preservam_desenvolvimento_e_nao_tem_holdout(self):
        casos=json.loads(gzip.decompress((DIR/'corpus_contrastes.json.gz').read_bytes()))['exemplos']
        base=json.loads((DIR/'corpus_rodada3.json').read_text())['exemplos']
        def chaves(exemplos,split):
            return {json.dumps([e['mensagem'],e['historico'],e['resposta']],sort_keys=True,ensure_ascii=False)
                    for e in exemplos if e['split']==split}
        self.assertEqual(chaves(casos,'validacao'),chaves(base,'validacao'))
        texto=json.dumps(casos,ensure_ascii=False)
        for nome in ['Nerila','Tarsen','Ulira','Vordana','Herlina','Qirina','Nuvren','Ólvira','Návea-','Zorém-']:
            self.assertNotIn(nome,texto)
        entradas={e['mensagem'] for e in casos}
        for s in json.loads((DIR/'avaliacao_rodada3_congelada.json').read_text())['sessoes']:
            for t in s['turnos']:
                self.assertNotIn(t['mensagem'],entradas)

    def test_contrastes_alvos_possiveis_e_checkpoint_isolado(self):
        origem=json.loads(gzip.decompress((DIR/'checkpoint_rodada2.json.gz').read_bytes()))
        vocab=set(origem['vocabulario'])
        casos=json.loads(gzip.decompress((DIR/'corpus_contrastes.json.gz').read_bytes()))['exemplos']
        for e in casos:
            self.assertFalse(set(tokenizar(e['resposta']))-vocab-set(fonte_dialogo(e['mensagem'],e['historico'],192)))
        destino=DIR/'checkpoint_contrastes.json.gz'
        if destino.exists():
            novo=json.loads(gzip.decompress(destino.read_bytes()))
            self.assertEqual(novo['vocabulario'],origem['vocabulario'])
            self.assertEqual(novo['treino']['parametros'],81433)
            self.assertIs(novo['aprovado'],False)
            self.assertIs(novo['ativo_no_chat'],False)

    def test_holdout_rodada3_preservado_sem_entrada_ou_nome_no_treino(self):
        avaliacao=DIR/'avaliacao_rodada3_congelada.json'
        self.assertEqual(hashlib.sha256(avaliacao.read_bytes()).hexdigest(),
            '5ba9c48eebac0b461fb115ca368ec6e9cfc6a4f8fc79c0847e20aedfd33f9f0b')
        corpus=json.loads((DIR/'corpus_rodada3.json').read_text())['exemplos']
        entradas={e['mensagem'] for e in corpus}
        for sessao in json.loads(avaliacao.read_text())['sessoes']:
            for turno in sessao['turnos']:
                self.assertNotIn(turno['mensagem'],entradas)
        texto=json.dumps(corpus,ensure_ascii=False)
        for nome in ['Nerila','Tarsen','Ulira','Vordana','Herlina','Qirina','Nuvren','Ólvira']:
            self.assertNotIn(nome,texto)

    def test_reformulacoes_rodada3_nao_incorporam_validacao_anterior(self):
        antigo=json.loads((DIR/'corpus_rodada2.json').read_text())['exemplos']
        novo=json.loads((DIR/'corpus_rodada3.json').read_text())['exemplos']
        def entradas(casos,split):
            return {json.dumps([e['mensagem'],e['historico'],e['resposta']],sort_keys=True,ensure_ascii=False)
                    for e in casos if e['split']==split}
        self.assertEqual(entradas(antigo,'validacao'),entradas(novo,'validacao'))
        self.assertFalse(entradas(novo,'validacao') & entradas(novo,'treino'))

    def test_rodada3_vocabulario_e_capacidade_preservados_sem_alvos_impossiveis(self):
        origem=json.loads(gzip.decompress((DIR/'checkpoint_rodada2.json.gz').read_bytes()))
        vocab=set(origem['vocabulario'])
        corpus=json.loads((DIR/'corpus_rodada3.json').read_text())['exemplos']
        for e in corpus:
            fonte=fonte_dialogo(e['mensagem'],e['historico'],192)
            self.assertFalse(set(tokenizar(e['resposta']))-vocab-set(fonte))
        destino=DIR/'checkpoint_rodada3.json.gz'
        if destino.exists():
            novo=json.loads(gzip.decompress(destino.read_bytes()))
            self.assertEqual(novo['vocabulario'],origem['vocabulario'])
            self.assertEqual(novo['treino']['parametros'],origem['treino']['parametros'])
            self.assertIs(novo['aprovado'],False)
            self.assertIs(novo['ativo_no_chat'],False)

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
