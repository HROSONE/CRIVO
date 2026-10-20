# CRIVO para Android (offline)

O app abre a **mesma página do site**, mas tudo roda dentro do celular: o código do CRIVO, o
conhecimento e os pesos próprios (a v3 D e as outras redes), com Python e NumPy embutidos pelo
[Chaquopy](https://chaquo.com/chaquopy/). Chaquopy, Python e NumPy são bibliotecas de execução,
não modelos (AGENTS.md). A conversa roda no aparelho e não chama nenhum serviço de fora; sem
internet ele conversa igual. A internet só é usada pela atualização automática (abaixo).

## Como instalar

1. No celular, abra **https://github.com/HROSONE/CRIVO/releases/tag/android-latest** e baixe
   `CRIVO.apk` (uns 200 MB).
2. Abra o arquivo. O Android pede para permitir "instalar apps desta fonte"; permita para o
   navegador ou para o gerenciador de arquivos.
3. Abra o CRIVO. Na primeira vez ele copia os pesos para o aparelho (até um minuto). Depois disso,
   pode usar no modo avião.

## Atualização automática

Depois da primeira instalação, o app se atualiza sozinho:

1. Ao abrir (e, aberto, no máximo a cada 6 horas), ele lê `versao.json` no release `android-latest`.
2. Havendo versão nova, pergunta: **Atualizar**, **Depois** ou **Pular esta versão**. Mostra o tamanho e
   avisa quando o download vai usar dados móveis.
3. Baixa o APK com barra de progresso (retoma de onde parou se a conexão cair) e confere: SHA-256 igual
   ao do `versao.json`, mesmo pacote, versão mais nova e **a mesma chave** do app instalado.
4. Entrega ao instalador do Android. Na primeira vez, o Android pede para permitir que o CRIVO instale
   atualizações; depois, só um toque em "Atualizar". Um app de fora da loja não pode se instalar sem
   essa confirmação.

As conversas guardadas no app ficam. Sem internet, nada muda: ele só confere de novo depois.
Código: `app/src/main/java/br/crivo/app/Atualizador.kt` e `InstalacaoRecebedor.kt`. O CI publica o
`versao.json` (versão, SHA-256, tamanho e impressão digital da chave) junto com o APK.

Ainda dá para atualizar à mão: baixe o `CRIVO.apk` novo e instale por cima.

**Configurações** (menu da página, deslizando da esquerda para a direita ou no ☰ → "Configurações do app"):
- a versão instalada e a última verificação;
- ligar ou desligar a busca automática;
- **Procurar atualização agora**, que responde mesmo sem novidade ("Você já tem a versão mais recente").

## Tela

Desde o Android 15, o app ocupa a tela toda. A página fica dentro das margens da barra de status, da barra de navegação
e do teclado, no mesmo fundo escuro, em todas as versões do Android. O botão voltar fecha o menu antes de sair.

## Como é montado

- `scripts/empacotar_apk.py` junta os mesmos arquivos que a Vercel leva (`vercel.json` →
  `includeFiles`, mais `api/` e `public/`) em `app/src/main/assets/crivo.zip`. Com `--testar`, ele
  extrai o zip numa pasta vazia, sobe o servidor e conversa, como o app faz.
- `app/src/main/java/br/crivo/app/MainActivity.kt` copia o zip para o aparelho uma vez por versão,
  inicia o Python e mostra `http://127.0.0.1:<porta>/` num WebView.
- `app/src/main/python/crivo_app.py` sobe o servidor de `web_local.py` só em 127.0.0.1.
- `.github/workflows/apk-android.yml` compila no GitHub Actions, a cada mudança que chega na `main`
  (ou à mão em Actions → "APK Android (offline)" → Run workflow), e publica no release
  `android-latest`.

## Limites

- **Assinatura:** o CI gera uma chave uma vez e a guarda no cache do Actions, para cada APK novo
  instalar por cima. Se o cache expirar (7 dias sem compilar), vem outra chave, e o Android pede
  para desinstalar o antigo. O cache de um repositório público também pode ser lido por workflows
  de PRs de fora. Para uma chave fixa e protegida, guarde uma como segredo do repositório
  (`CRIVO_KEYSTORE_B64`, a keystore em base64, com alias `crivo`, e `CRIVO_KEYSTORE_SENHA`). O
  workflow usa o segredo quando ele existe.
- **Teste:** cada APK é instalado num emulador Android 14 (x86_64) no CI. O teste abre o app, espera
  o servidor do aparelho e conversa; os prints da tela ficam no artefato `CRIVO-apk`. Num celular
  de verdade, com processador ARM, ainda não foi medido (velocidade, memória, bateria).
- Só aparelhos de 64 bits (arm64-v8a; x86_64 para emulador), Android 8 ou mais novo.
- O botão "Ouvir" depende da voz do sistema, que o WebView nem sempre oferece.
- A atualização baixa o APK inteiro (uns 200 MB), não só o que mudou.
- **A chave precisa ser sempre a mesma.** Se o cache do Actions expirar e o CI gerar outra chave, o
  Android não deixa instalar por cima; o app avisa e manda para a página do release (desinstalar e
  instalar de novo, uma vez). O segredo `CRIVO_KEYSTORE_B64` evita isso de vez.
