"""Miniprojetos ESM: geração por arquivo e execução Node em namespace isolado."""
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from verificacao_codigo import comando, sandbox_args, iguais

ROOT = Path(__file__).resolve().parent
CATALOGO = ROOT / 'dados/programacao/projetos.json'


def projetos(split='teste'):
    return [p for p in json.loads(CATALOGO.read_text())['projetos'] if p['split'] == split]


def validar_arquivos(projeto, arquivos):
    esperados = {a['caminho'] for a in projeto['arquivos']}
    if set(arquivos) != esperados:
        raise ValueError('Entrega deve conter exatamente os arquivos do contrato')
    for nome, texto in arquivos.items():
        p = PurePosixPath(nome)
        if p.is_absolute() or len(p.parts) != 1 or '..' in p.parts or p.suffix not in ('.js', '.ts'):
            raise ValueError('Caminho inválido')
        if not isinstance(texto, str) or len(texto.encode()) > 32768:
            raise ValueError('Arquivo inválido ou acima de 32 KiB')


def node_isolado():
    node = shutil.which('node')
    if not node:
        return False
    with tempfile.TemporaryDirectory() as d:
        args = sandbox_args(node, d)
        return bool(args and comando(args + ['-e', 'console.log("CRIVO_LAB_OK")'], d, memoria=True)[0])


def verificar_projeto(projeto, arquivos, casos, tsc=None):
    validar_arquivos(projeto, arquivos)
    r = dict(compila=False, executado=False, funcional=False, casos_total=len(casos),
             casos_corretos=0, diagnostico='', runtime=None)
    node = shutil.which('node')
    if not node:
        r['diagnostico'] = 'Node indisponível'; return r
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        (pasta / 'package.json').write_text('{"type":"module"}')
        for nome, texto in arquivos.items():
            (pasta / nome).write_text(texto)
        if projeto['linguagem'] == 'typescript':
            if not tsc or not Path(tsc).is_file():
                r['diagnostico'] = 'TypeScript indisponível'; return r
            # O compilador analisa arquivos e não executa o código candidato.
            args = [node, str(Path(tsc).resolve())] + [str(pasta / n) for n in arquivos]
            ok, log = comando(args + ['--strict', '--noEmitOnError', '--target', 'ES2022',
                                      '--module', 'NodeNext', '--moduleResolution', 'NodeNext',
                                      '--skipLibCheck'], pasta, timeout=30, cpu=20)
            if not ok:
                r['diagnostico'] = log[:1800]; return r
            for n in arquivos:
                (pasta / n).unlink()
        else:
            for n in arquivos:
                ok, log = comando([node, '--check', str(pasta / n)], pasta)
                if not ok:
                    r['diagnostico'] = log[:1800]; return r
        r['compila'] = True
        # Apenas entradas são montadas. Respostas esperadas permanecem no processo pai.
        (pasta / 'entradas.json').write_text(json.dumps([c['entrada'] for c in casos]))
        (pasta / 'runner.mjs').write_text('''import fs from 'node:fs';
import { resolver } from './index.js';
const entradas=JSON.parse(fs.readFileSync('/job/entradas.json','utf8'));
const resultados=[];
for(const entrada of entradas){
 const antes=JSON.stringify(entrada);
 try {const saida=await resolver(entrada);
  const texto=JSON.stringify(saida,(_k,v)=>{if(typeof v==='number'&&!Number.isFinite(v))throw Error('Número não finito');return v;});
  if(texto===undefined)throw Error('Saída undefined');
  resultados.push({saida:JSON.parse(texto),mutou:antes!==JSON.stringify(entrada)});
 } catch(e){resultados.push({erro:String(e).slice(0,300)});}
}
process.stdout.write('CRIVO_PROJETOS:'+JSON.stringify(resultados)+'\\n');
''')
        args = sandbox_args(node, pasta)
        if not args:
            r['diagnostico'] = 'Bubblewrap indisponível; execução bloqueada'; return r
        ok, log = comando(args + ['/job/runner.mjs'], pasta, memoria=True)
        if not ok:
            r['diagnostico'] = log[:1800]; return r
        linhas = [x[len('CRIVO_PROJETOS:'):] for x in log.splitlines() if x.startswith('CRIVO_PROJETOS:')]
        try:
            if len(linhas) != 1: raise ValueError('Protocolo ambíguo')
            resultados = json.loads(linhas[0])
            if not isinstance(resultados, list) or len(resultados) != len(casos):
                raise ValueError('Número de resultados divergente')
            acertos = [isinstance(v, dict) and 'saida' in v and v.get('mutou') is False and
                       iguais(v['saida'], c['saida']) for v, c in zip(resultados, casos)]
        except (ValueError, TypeError) as e:
            r['diagnostico'] = str(e); return r
        r.update(executado=True, runtime='node_bubblewrap', casos_corretos=sum(acertos),
                 funcional=bool(casos) and all(acertos))
        if not r['funcional']:
            i = acertos.index(False)
            # Não transmitir valor esperado: feedback de execução dos casos de desenvolvimento.
            r['diagnostico'] = json.dumps(dict(caso=i, entrada=casos[i]['entrada'],
                observado=resultados[i], falha='Resultado divergente, erro ou mutação'), ensure_ascii=False)
    return r


def prompt_arquivo(projeto, arquivo, produzidos=None, diagnostico=None):
    texto = 'Escreva somente o módulo ESM '+arquivo['caminho']+' em '+projeto['linguagem']+'.\n'
    texto += projeto['requisitos']+'\n'+arquivo['contrato']
    if produzidos:
        texto += '\nMódulos já escritos:\n'+json.dumps(produzidos, ensure_ascii=False)
    if diagnostico:
        texto += '\nCorrija o projeto com este diagnóstico de desenvolvimento: '+diagnostico[:1800]
    return texto


def gerar_arquivos(gerador, projeto, diagnostico=None, anteriores=None):
    from linguagem_profunda import codificar_texto
    arquivos, geracoes = {}, []
    for a in projeto['arquivos']:
        prompt = prompt_arquivo(projeto, a, arquivos, diagnostico)
        if anteriores:
            prompt += '\nVersão anterior deste módulo:\n'+anteriores.get(a['caminho'], '')
        # Contratos e módulos nunca são truncados silenciosamente.
        if len(codificar_texto(gerador.tokenizer, prompt)) >= gerador.modelo.config.contexto - 8:
            raise ValueError('Projeto excede contexto ao gerar '+a['caminho'])
        g = gerador.gerar(prompt, max_tokens=512)
        arquivos[a['caminho']] = g['codigo']; geracoes.append(g)
    return arquivos, all(g['completa'] for g in geracoes), geracoes


def avaliar_projeto(gerador, projeto, tsc=None, reparos=2):
    if reparos not in (0, 1, 2): raise ValueError('Reparos deve estar entre 0 e 2')
    tentativas = []; diagnostico = None; anteriores = None
    for i in range(reparos + 1):
        try:
            arquivos, completa, geracoes = gerar_arquivos(gerador, projeto, diagnostico, anteriores)
        except ValueError as e:
            tentativas.append(dict(erro=str(e))); break
        dev = verificar_projeto(projeto, arquivos, projeto['desenvolvimento'], tsc)
        tentativas.append(dict(arquivos=arquivos, completa=completa, geracoes=geracoes, desenvolvimento=dev))
        if completa and dev['funcional']: break
        anteriores = arquivos
        diagnostico = dev['diagnostico'] or 'Geração incompleta: entregue todos os módulos completos.'
    # Primeiro e último avaliados em casos reservados só depois de encerrar os reparos.
    indices = sorted({0, len(tentativas)-1})
    for i in indices:
        t = tentativas[i]
        if 'arquivos' in t:
            t['reservados'] = verificar_projeto(projeto, t['arquivos'], projeto['reservados'], tsc)
    primeiro, ultimo = tentativas[0], tentativas[-1]
    def aprovado(t): return bool(t.get('completa') and t.get('reservados',{}).get('funcional'))
    return dict(id=projeto['id'], familia=projeto['familia'], linguagem=projeto['linguagem'],
                acerto_inicial=aprovado(primeiro), acerto_final=aprovado(ultimo),
                reparado=not aprovado(primeiro) and aprovado(ultimo), tentativas=tentativas)


def exemplos_projetos():
    """Somente famílias treino/validação; referências reservadas nunca viram alvos."""
    exemplos = []
    for split in ('treino', 'validacao'):
        for p in projetos(split):
            produzidos = {}
            for a in p['arquivos']:
                mensagem = prompt_arquivo(p, a, produzidos)
                base = dict(resposta=a['referencia'], grupo='projeto:'+p['familia'], split=split,
                    origem='miniprojeto_autoral', historico=[], linguagem=p['linguagem'])
                exemplos.append(dict(base, mensagem=mensagem, tipo='criacao'))
                errado = '// Módulo não implementado\n'
                exemplos.append(dict(base, mensagem=mensagem+'\nVersão anterior deste módulo:\n'+errado+
                    '\nDiagnóstico: exportação exigida ausente. Implemente o contrato.', tipo='reparo'))
                produzidos[a['caminho']] = a['referencia']
    return exemplos
