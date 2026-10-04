"""Contratos do corpus, não alegações de inteligência a partir de loss."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISPONIVEL=all(importlib.util.find_spec(n) for n in ('torch','tokenizers','numpy'))


@unittest.skipUnless(DISPONIVEL,'Treino requer dependências opcionais')
class CorpusConversa(unittest.TestCase):
    def test_grupo_de_transferencia_e_memoria_nao_cruza_particoes(self):
        from scripts.preparar_conversa_gerativa import exemplos_autorais
        grupos={}
        for e in exemplos_autorais():grupos.setdefault(e['grupo'],set()).add(e['split'])
        self.assertTrue(grupos)
        self.assertTrue(all(len(s)==1 for s in grupos.values()))

    def test_historico_e_pergunta_nao_sao_alvos_supervisionados(self):
        from tokenizers import Tokenizer
        from linguagem_profunda import segmentos_dialogo, codificar_texto
        from scripts.preparar_linguagem_profunda import janelas_dialogo
        t=Tokenizer.from_file(str(Path(__file__).parent/'artefatos/linguagem_profunda/tokenizer.json'))
        t.encode_special_tokens=True
        ex=dict(mensagem='Qual nome eu informei?',historico=[dict(papel='usuario',texto='Meu nome é Cora.')],resposta='Você informou o nome Cora.')
        segmentos,atual=segmentos_dialogo(t,ex['mensagem'],ex['historico'])
        fonte=sum(segmentos,[])+atual
        janelas=janelas_dialogo(t,ex,256)
        self.assertEqual(len(janelas),1)
        x,y=janelas[0]
        self.assertTrue(all(a==-100 for a in y[:len(fonte)-1]))
        self.assertEqual([a for a in y if a!=-100],codificar_texto(t,ex['resposta'])+[t.token_to_id('<fim>')])

    def test_preparacao_isola_alvos_e_confere_hash_de_todos_os_arquivos(self):
        from scripts.preparar_conversa_gerativa import preparar
        from scripts.treinar_linguagem_profunda import Corpus,sha
        raiz=Path(__file__).parent
        humano=[]
        for split in ('treino','validacao','teste'):
            humano.append(dict(mensagem='Pedido '+split,resposta='Resposta humana '+split+'.',historico=[],grupo='humano_'+split,split=split,origem='humano_oasst2'))
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);fonte=p/'origem';fonte.write_text('origem simulada apenas no teste')
            with patch('scripts.preparar_conversa_gerativa.selecionar_humanos',return_value=(humano,{})):
                preparar(p/'corpus',fonte,raiz/'artefatos/linguagem_profunda/tokenizer.json')
            corpus=Corpus(p/'corpus',256,equilibrar_familias=True,podar_padding=True)
            alvos={s:{json.loads(l)['resposta'].casefold() for l in (p/'corpus'/f'dialogos_{s}.jsonl').read_text().splitlines()} for s in ('treino','validacao','teste')}
            self.assertFalse(alvos['treino']&alvos['validacao'])
            self.assertFalse(alvos['treino']&alvos['teste'])
            self.assertFalse(alvos['validacao']&alvos['teste'])
            self.assertEqual(corpus.manifesto['arquivos']['tokenizer.json'],sha(raiz/'artefatos/linguagem_profunda/tokenizer.json'))
            path=p/'corpus'/'dialogos_treino.jsonl';path.write_text(path.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'Corpus alterado'):
                Corpus(p/'corpus',256)


if __name__=='__main__':unittest.main()
