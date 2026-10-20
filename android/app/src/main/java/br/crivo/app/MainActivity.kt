package br.crivo.app

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.text.TextUtils
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
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
 */
class MainActivity : Activity() {
    private lateinit var web: WebView
    private lateinit var atualizador: Atualizador

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        setContentView(web)
        atualizador = Atualizador(this)
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
                resultado.onSuccess { porta ->
                    web.loadUrl("http://127.0.0.1:$porta/")
                    atualizador.verificar(abrindo = true)
                }
                resultado.onFailure { erro -> mostrarErro(erro) }
            }
        }
    }

    private fun iniciar(): Int {
        val pasta = prepararArquivos()
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(applicationContext))
        }
        return Python.getInstance().getModule("crivo_app").callAttr("iniciar", pasta.absolutePath).toInt()
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

    private fun mostrarErro(erro: Throwable) {
        val texto = TextUtils.htmlEncode("${erro::class.java.simpleName}: ${erro.message}")
        val html = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <body style="background:#0B0A1F;color:#E9E5FF;font-family:system-ui,sans-serif;padding:24px 16px">
            <h1>O CRIVO não conseguiu abrir</h1>
            <p>Feche e abra o app de novo. Se continuar, mande um print desta tela.</p>
            <pre style="white-space:pre-wrap;color:#B9B2E6">$texto</pre></body></html>"""
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
    }

    override fun onResume() {
        super.onResume()
        atualizador.retomar()      // voltou da permissão "instalar apps desta fonte"
        atualizador.verificar()    // app aberto há muito tempo: confere no máximo a cada 6 h
    }

    @Deprecated("Usa o voltar do WebView quando há página anterior.")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
