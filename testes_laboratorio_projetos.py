import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import laboratorio_projetos as lab


class LaboratorioTestes(unittest.TestCase):
    def test_familias_e_alvos_reservados(self):
        grupos=[{p['familia'] for p in lab.projetos(s)} for s in ('treino','validacao','teste')]
        self.assertFalse(grupos[0]&grupos[1] or grupos[0]&grupos[2] or grupos[1]&grupos[2])
        es=lab.exemplos_projetos()
        self.assertEqual(len(es),32)
        reservados={a['referencia'] for p in lab.projetos() for a in p['arquivos']}
        self.assertFalse(reservados & {e['resposta'] for e in es})
        self.assertFalse(any(e['split']=='teste' for e in es))

    def test_prompt_sem_gabarito(self):
        p=lab.projetos()[0]
        prompt=lab.prompt_arquivo(p,p['arquivos'][0])
        self.assertNotIn(p['arquivos'][0]['referencia'],prompt)
        self.assertNotIn(json.dumps(p['reservados']),prompt)

    def test_caminhos_e_limites(self):
        p=lab.projetos()[0]
        bons={a['caminho']:a['referencia'] for a in p['arquivos']}
        lab.validar_arquivos(p,bons)
        for ruins in ({'../escape.js':'x'},dict(bons,**{'extra.js':'x'}),{n:'x'*32769 for n in bons}):
            with self.assertRaises(ValueError):lab.validar_arquivos(p,ruins)

    def test_falha_fechada_sem_sandbox(self):
        p=next(p for p in lab.projetos() if p['linguagem']=='javascript')
        with patch.object(lab,'sandbox_args',return_value=None),patch.object(lab,'comando',return_value=(True,'')) as cmd:
            r=lab.verificar_projeto(p,{a['caminho']:a['referencia'] for a in p['arquivos']},p['reservados'])
        self.assertTrue(r['compila']);self.assertFalse(r['executado']);self.assertFalse(r['funcional'])
        self.assertTrue(all('--check' in c.args[0] for c in cmd.call_args_list))

    def test_reparo_nao_recebe_casos_reservados(self):
        p=lab.projetos()[0];arquivos={a['caminho']:a['referencia'] for a in p['arquivos']}
        chamadas=[]
        def verificar(_p,_a,casos,_tsc):
            chamadas.append(casos)
            dev=casos is p['desenvolvimento']
            return dict(funcional=not dev,diagnostico='falhou dev' if dev else 'SEGREDO RESERVADO')
        with patch.object(lab,'gerar_arquivos',return_value=(arquivos,True,[])) as gerar,patch.object(lab,'verificar_projeto',side_effect=verificar):
            r=lab.avaliar_projeto(object(),p,reparos=2)
        self.assertEqual(chamadas,[p['desenvolvimento']]*3+[p['reservados']]*2)
        self.assertEqual([c.args[2] for c in gerar.call_args_list],[None,'falhou dev','falhou dev'])
        self.assertTrue(r['acerto_inicial']);self.assertTrue(r['acerto_final']);self.assertFalse(r['reparado'])

    def test_protocolo_e_mutacao(self):
        p=lab.projetos()[0];arquivos={a['caminho']:a['referencia'] for a in p['arquivos']}
        c=p['reservados'][0]
        for mutou,ambigua in ((False,False),(True,False),(False,True)):
            log='CRIVO_PROJETOS:'+json.dumps([dict(saida=c['saida'],mutou=mutou)])+'\n'
            if ambigua:log+=log
            with patch.object(lab,'sandbox_args',return_value=['sandbox']),patch.object(lab,'comando',side_effect=lambda args,*a,**kw:(True,log if args[0]=='sandbox' else '')):
                r=lab.verificar_projeto(p,arquivos,[c])
            self.assertEqual(r['funcional'],not mutou and not ambigua)

    def test_reparo_melhora_sem_inflar_primeira_tentativa(self):
        p=lab.projetos()[0];arquivos={a['caminho']:a['referencia'] for a in p['arquivos']}
        with patch.object(lab,'gerar_arquivos',return_value=(arquivos,True,[])),patch.object(lab,'verificar_projeto',side_effect=[
            dict(funcional=False,diagnostico='erro'),dict(funcional=True,diagnostico=''),
            dict(funcional=False),dict(funcional=True)]):
            r=lab.avaliar_projeto(object(),p,reparos=2)
        self.assertFalse(r['acerto_inicial']);self.assertTrue(r['acerto_final']);self.assertTrue(r['reparado'])

    @unittest.skipUnless(os.environ.get('CRIVO_LAB_NODE')=='1','Integração Node isolado executada no workflow próprio')
    def test_referencias_e_bloqueios_reais(self):
        self.assertTrue(lab.node_isolado())
        for split in ('treino','validacao','teste'):
            for p in lab.projetos(split):
                with self.subTest(p=p['id']):
                    r=lab.verificar_projeto(p,{a['caminho']:a['referencia'] for a in p['arquivos']},p['desenvolvimento']+p['reservados'],os.environ['CRIVO_TSC'])
                    self.assertTrue(r['funcional'],r)
        p=next(p for p in lab.projetos() if p['linguagem']=='javascript')
        for corpo in ('while(true){}','return require("node:fs").readFileSync("/workspace/secreto");',
                      'return await import("node:fs").then(fs=>fs.readFileSync("/etc/passwd","utf8"));'):
            arquivos={'core.js':'export async function executar(x){'+corpo+'}', 'index.js':'export { executar as resolver } from "./core.js";'}
            r=lab.verificar_projeto(p,arquivos,p['reservados'])
            self.assertFalse(r['funcional'],r)


if __name__=='__main__':unittest.main()
