package br.crivo.app

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.text.TextUtils
import android.view.View
import android.view.WindowInsets
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.util.zip.ZipInputStream
import kotlin.concurrent.thread

/**
 * O CRIVO no celular, sem internet.
 *
 * Na primeira abertura, o app copia o CRIVO empacotado (assets/crivo.zip, feito por
 * scripts/empacotar_apk.py: código, conhecimento e pesos próprios) para uma pasta do aparelho.
 * Depois sobe, com o Python do Chaquopy, o mesmo servidor de web_local.py em 127.0.0.1
 * (android/app/src/main/python/crivo_app.py) e mostra a mesma página do site.
 *
 * Com a página aberta, o Atualizador confere se há versão nova do app (a única coisa que usa a internet).
 * A página chama `CrivoApp.abrirConfiguracoes()` pelo menu (versão, atualização automática, procurar agora).
 */
class MainActivity : Activity() {
    private lateinit var web: WebView
    private lateinit var atualizador: Atualizador

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        registrarErroFatal()
        web = WebView(this)
        setContentView(raizComMargens(web))
        atualizador = Atualizador(this)
        AtualizacaoFundo.agendar(this)
        web.addJavascriptInterface(Ponte(), "CrivoApp")
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.cacheMode = WebSettings.LOAD_NO_CACHE
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                if (url.host == "127.0.0.1" || url.scheme == "file") return false
                // Links de fora (por exemplo, cvv.org.br) abrem no navegador, se houver internet.
                startActivity(Intent(Intent.ACTION_VIEW, url))
                return true
            }
        }
        web.loadUrl("file:///android_asset/carregando.html")
        thread(name = "crivo-inicio") {
            val resultado = runCatching { iniciar() }
            runOnUiThread {
                val erroAnterior = File(filesDir, ERRO_FATAL).takeIf { it.isFile }?.readText()
                if (erroAnterior != null) {
                    File(filesDir, ERRO_FATAL).delete()
                    mostrarTexto("Erro que fechou o app na abertura anterior:", erroAnterior)
                    return@runOnUiThread
                }
                resultado.onSuccess { porta ->
                    web.loadUrl("http://127.0.0.1:$porta/")
                    atualizador.verificar(abrindo = true)
                }
                resultado.onFailure { erro -> mostrarErro(erro) }
            }
        }
    }

    /**
     * Desde o Android 15 (targetSdk 35) o app ocupa a tela toda, por baixo da barra de status e da de navegação.
     * A página fica dentro das margens que o sistema informa (barras e teclado), no mesmo fundo escuro, em todas as
     * versões: do 11 em diante pelo WindowInsets novo, antes pelas margens antigas.
     */
    @Suppress("DEPRECATION")
    private fun raizComMargens(conteudo: View): View {
        val raiz = FrameLayout(this)
        raiz.setBackgroundColor(Color.parseColor("#0B0A1F"))
        raiz.addView(conteudo, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        if (Build.VERSION.SDK_INT >= 30) {
            window.setDecorFitsSystemWindows(false)
            window.insetsController?.setSystemBarsAppearance(0, android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                or android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS)   // ícones claros no fundo escuro
        } else {
            raiz.systemUiVisibility = View.SYSTEM_UI_FLAG_LAYOUT_STABLE or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        }
        raiz.setOnApplyWindowInsetsListener { v, insets ->
            if (Build.VERSION.SDK_INT >= 30) {
                val m = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.ime() or WindowInsets.Type.displayCutout())
                v.setPadding(m.left, m.top, m.right, m.bottom)
                WindowInsets.CONSUMED
            } else {
                v.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop, insets.systemWindowInsetRight,
                    insets.systemWindowInsetBottom)
                insets.consumeSystemWindowInsets()
            }
        }
        return raiz
    }

    /** O que a página pode pedir ao app. Só vale para a página do próprio CRIVO (127.0.0.1). */
    private inner class Ponte {
        @JavascriptInterface
        fun abrirConfiguracoes() = runOnUiThread {
            if (Uri.parse(web.url ?: "").host == "127.0.0.1") atualizador.abrirConfiguracoes()
        }
    }

    private fun iniciar(): Int {
        val pasta = prepararArquivos()
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(applicationContext))
        }
        return Python.getInstance().getModule("crivo_app")
            .callAttr("iniciar", pasta.absolutePath, applicationInfo.nativeLibraryDir).toInt()
    }

    /** Copia o CRIVO para o aparelho uma vez por versão; versões antigas são apagadas depois. */
    private fun prepararArquivos(): File {
        val versao = assets.open("crivo_versao.txt").bufferedReader().use { it.readText().trim() }
        val destino = File(filesDir, "crivo-$versao")
        val pronto = File(destino, ".pronto")
        if (pronto.isFile) return destino
        destino.deleteRecursively()
        destino.mkdirs()
        val raiz = destino.canonicalPath + File.separator
        ZipInputStream(assets.open("crivo.zip").buffered(1 shl 16)).use { zip ->
            var entrada = zip.nextEntry
            while (entrada != null) {
                val arquivo = File(destino, entrada.name)
                if (!arquivo.canonicalPath.startsWith(raiz)) throw SecurityException("caminho inválido no pacote: ${entrada.name}")
                if (entrada.isDirectory) {
                    arquivo.mkdirs()
                } else {
                    arquivo.parentFile?.mkdirs()
                    arquivo.outputStream().buffered(1 shl 16).use { zip.copyTo(it) }
                }
                entrada = zip.nextEntry
            }
        }
        pronto.writeText(versao)
        filesDir.listFiles()?.filter { it.isDirectory && it.name.startsWith("crivo-") && it != destino }
            ?.forEach { it.deleteRecursively() }
        return destino
    }

    private fun mostrarErro(erro: Throwable) =
        mostrarTexto("O CRIVO não conseguiu abrir", "${erro::class.java.simpleName}: ${erro.message}")

    private fun mostrarTexto(titulo: String, detalhe: String) {
        val texto = TextUtils.htmlEncode(detalhe)
        val html = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <body style="background:#0B0A1F;color:#E9E5FF;font-family:system-ui,sans-serif;padding:24px 16px">
            <h1>${TextUtils.htmlEncode(titulo)}</h1>
            <p>Feche e abra o app de novo. Se continuar, mande um print desta tela.</p>
            <pre style="white-space:pre-wrap;color:#B9B2E6">$texto</pre></body></html>"""
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
    }

    /** Um erro que nenhum try pega (o diálogo "o app tem um bug") fica num arquivo e aparece na próxima abertura. */
    private fun registrarErroFatal() {
        val padrao = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, erro ->
            runCatching { File(filesDir, ERRO_FATAL).writeText(erro.stackTraceToString()) }
            padrao?.uncaughtException(thread, erro)
        }
    }

    private companion object {
        const val ERRO_FATAL = "erro_fatal.txt"
    }

    override fun onResume() {
        super.onResume()
        atualizador.retomar()      // voltou da permissão "instalar apps desta fonte"
        atualizador.verificar()    // app aberto há muito tempo: confere no máximo a cada 6 h
    }

    @Deprecated("Fecha o menu da página, se estiver aberto; senão, usa o voltar do WebView quando há página anterior.")
    override fun onBackPressed() {
        web.evaluateJavascript("window.crivoVoltar ? window.crivoVoltar() : false") { fechou ->
            if (fechou == "true") return@evaluateJavascript
            if (web.canGoBack()) web.goBack() else finish()
        }
    }
}
