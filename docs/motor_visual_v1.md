# Motor Visual v1

O Motor Visual é uma ferramenta de criação e pré-visualização de cenas. Ele não altera o modelo de linguagem nem participa das respostas do chat.

## Abrir

- No site ou no servidor local, use o botão de ferramenta na barra superior do chat.
- A rota direta é `/motor-visual.html`.
- No computador, o servidor local continua sendo iniciado com `python web_local.py`.
- O editor também é servido pelo mesmo servidor local usado pelo aplicativo, sem uma API adicional.

## Funcionamento offline

A página, o CSS, o código do editor e o Three.js são arquivos locais em `public/`. A versão incluída é Three.js r160, sob licença MIT; o texto da licença acompanha a biblioteca em `public/vendor/THREE-LICENSE.txt`. Não há CDN, fonte externa, endpoint de IA ou envio de cenas para um serviço remoto.

## Formato da cena

A cena é um objeto JSON com:

- `modo`: `"3d"` ou `"svg"`.
- `formato`: `"9:16"`, `"16:9"` ou `"1:1"`.
- `fundo`: cor CSS do fundo.
- `camera`: opcional no modo 3D; `"orbita_lenta"` ou `"zoom_suave"`.
- `objetos`: lista de formas e seus parâmetros.

### Objetos 3D

Tipos: `esfera`, `cubo`, `cilindro`, `anel` e `particulas`.

Campos comuns: `tam`, `cor`, `pos`, `brilho`, `opacidade`, `arame`, `anim` e `vel`. Para órbita, use `raio_orbita`; para anexar um anel ou outro objeto a outro índice da lista, use `segue`. Em partículas, `qtd` define a quantidade, `tam` define o espaço ocupado e `tamanho_particula` define o tamanho visual dos pontos.

Animações: `girar`, `pulsar`, `flutuar` e `orbita`.

### Objetos SVG

Tipos: `onda`, `circulo`, `retangulo`, `linha` e `seta`.

Campos principais: `pos`, `pos2`, `tam`, `cor`, `espessura`, `preenchido`, `anim` e `vel`. Para ondas, `tam` é [largura, amplitude].

Animações: `fluir` (ondas), `pulsar`, `girar` e `desenhar`.

## Exemplo

```json
{
  "modo": "svg",
  "formato": "9:16",
  "fundo": "#070b14",
  "objetos": [
    { "tipo": "onda", "pos": [0, 50], "tam": [100, 9], "cor": "#38bdf8", "anim": "fluir", "vel": 1 },
    { "tipo": "circulo", "pos": [50, 50], "tam": 12, "cor": "#f472b6", "preenchido": false, "anim": "pulsar" },
    { "tipo": "seta", "pos": [20, 78], "pos2": [80, 78], "cor": "#34d399", "anim": "desenhar" }
  ]
}
```

O editor limita a cena a 200 objetos e a nuvem de partículas a 5.000 pontos. JSON inválido ou tipos não reconhecidos são recusados antes da renderização.
