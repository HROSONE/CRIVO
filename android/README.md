# CRIVO para Android (offline)

O app abre a **mesma página do site**, mas tudo roda dentro do celular: o código do CRIVO, o
conhecimento e os pesos próprios (a v3 D e as outras redes), com Python e NumPy embutidos pelo
[Chaquopy](https://chaquo.com/chaquopy/). Chaquopy, Python e NumPy são bibliotecas de execução,
não modelos (AGENTS.md). O app não chama nenhum serviço de fora; sem internet ele conversa igual.

## Como instalar

1. No celular, abra **https://github.com/HROSONE/CRIVO/releases/tag/android-latest** e baixe
   `CRIVO.apk` (uns 200 MB).
2. Abra o arquivo. O Android pede para permitir "instalar apps desta fonte"; permita para o
   navegador ou para o gerenciador de arquivos.
3. Abra o CRIVO. Na primeira vez ele copia os pesos para o aparelho (até um minuto). Depois disso,
   pode usar no modo avião.

Para atualizar, baixe o `CRIVO.apk` novo e instale por cima; as conversas guardadas no app ficam.

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

- A assinatura é uma chave guardada no cache do CI. Se o cache expirar (7 dias sem compilar), o
  próximo APK vem com outra chave, e o Android pede para desinstalar o antigo antes. Para uma chave
  fixa, guarde uma no GitHub como segredo e troque `signingConfig`.
- Só aparelhos de 64 bits (arm64-v8a; x86_64 para emulador), Android 8 ou mais novo.
- O botão "Ouvir" depende da voz do sistema, que o WebView nem sempre oferece.
- Atualização automática (baixar só o que mudou, conferindo o SHA) fica para depois.
