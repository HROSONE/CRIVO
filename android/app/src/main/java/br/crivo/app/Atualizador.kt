package br.crivo.app

import android.app.Activity
import android.app.AlertDialog
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInfo
import android.content.pm.PackageInstaller
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.text.DateFormat
import java.util.Date
import kotlin.concurrent.thread

/**
 * Atualização automática do app.
 *
 * O CI publica no release `android-latest` o CRIVO.apk e um versao.json (número da versão, SHA-256 do APK e a
 * impressão digital da chave que assinou). O app confere esse arquivo ao abrir e, aberto, no máximo a cada
 * 6 horas. Havendo versão nova, pergunta; com o sim, baixa (retomando se cair), confere SHA-256, pacote, versão e
 * chave, e entrega ao instalador do Android, que pede a confirmação da pessoa.
 *
 * A internet só é usada para isto. A conversa continua dentro do aparelho, e o app não envia nada para fora.
 *
 * Nas configurações (menu da página → "Configurações do app"): a versão instalada, a busca automática (pode desligar)
 * e "Procurar atualização agora", que responde mesmo quando não há versão nova.
 */
class Atualizador(private val atividade: Activity) {
    companion object {
        const val BASE = "https://github.com/HROSONE/CRIVO/releases/download/android-latest/"
        const val ACAO_STATUS = "br.crivo.app.INSTALACAO_STATUS"
        private const val INTERVALO_MS = 6L * 60 * 60 * 1000
        private const val PREFS = "atualizacao"
    }

    private data class Versao(val codigo: Long, val nome: String, val sha256: String, val tamanho: Long,
                              val apk: String, val assinatura: String?)

    private val prefs = atividade.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private val pasta = File(atividade.cacheDir, "atualizacao")
    @Volatile private var ocupado = false
    @Volatile private var cancelado = false
    private var aguardandoPermissao: File? = null

    /** Confere se há versão nova. `abrindo`: na abertura do app confere sempre; depois, no máximo a cada 6 h.
     *  `manual`: pedido nas configurações; confere na hora, mesmo com a busca automática desligada, e sempre responde. */
    fun verificar(abrindo: Boolean = false, manual: Boolean = false) {
        if (ocupado) {
            if (manual) Toast.makeText(atividade, "Já estou procurando…", Toast.LENGTH_SHORT).show()
            return
        }
        val agora = System.currentTimeMillis()
        if (!manual && !automatico()) return
        if (!manual && !abrindo && agora - prefs.getLong("ultima", 0) < INTERVALO_MS) return
        ocupado = true
        if (manual) Toast.makeText(atividade, "Procurando atualização…", Toast.LENGTH_SHORT).show()
        thread(name = "crivo-atualizacao") {
            try {
                limparAntigos()
                val v = runCatching { buscarVersao() }.getOrNull()
                if (v == null) {
                    if (manual) naTela { avisar("Não consegui conferir agora. Veja se há internet e tente de novo.") }
                    return@thread
                }
                prefs.edit().putLong("ultima", agora).apply()
                if (v.codigo <= versaoInstalada()) {
                    if (manual) naTela { avisar("Você já tem a versão mais recente (${nomeInstalado()}).") }
                    return@thread
                }
                if (!manual && prefs.getLong("pular", -1) == v.codigo) return@thread
                val minha = assinaturaInstalada()
                if (v.assinatura != null && minha != null && !v.assinatura.equals(minha, ignoreCase = true)) {
                    naTela { avisarChaveDiferente(v, manual) }
                    return@thread
                }
                naTela { perguntar(v) }
            } finally {
                ocupado = false
            }
        }
    }

    /** As configurações do app: versão, busca automática e "procurar agora". */
    fun abrirConfiguracoes() {
        if (atividade.isFinishing) return
        val d = atividade.resources.displayMetrics.density
        fun px(dp: Int) = (dp * d).toInt()
        val ultima = prefs.getLong("ultima", 0)
        val info = TextView(atividade).apply {
            text = "Versão instalada: ${nomeInstalado()} (${versaoInstalada()})\n" +
                "Última verificação: " + (if (ultima > 0) DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                    .format(Date(ultima)) else "nenhuma ainda")
            textSize = 15f
            setPadding(0, 0, 0, px(16))
        }
        val chave = Switch(atividade).apply {
            text = "Procurar atualizações automaticamente"
            textSize = 15f
            isChecked = automatico()
            setOnCheckedChangeListener { _, ligado -> prefs.edit().putBoolean("automatico", ligado).apply() }
        }
        val explica = TextView(atividade).apply {
            text = "Ao abrir o app e, aberto, no máximo a cada 6 horas. Sempre pergunta antes de baixar."
            textSize = 13f
            alpha = 0.7f
            setPadding(0, px(4), 0, px(20))
        }
        val botao = Button(atividade).apply { text = "Procurar atualização agora" }
        val caixa = LinearLayout(atividade).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(px(24), px(16), px(24), 0)
            addView(info); addView(chave); addView(explica); addView(botao)
        }
        val janela = AlertDialog.Builder(atividade)
            .setTitle("Configurações")
            .setView(caixa)
            .setPositiveButton("Fechar", null)
            .show()
        botao.setOnClickListener {
            janela.dismiss()
            verificar(manual = true)
        }
    }

    private fun automatico() = prefs.getBoolean("automatico", true)

    private fun nomeInstalado(): String =
        atividade.packageManager.getPackageInfo(atividade.packageName, 0).versionName ?: versaoInstalada().toString()

    private fun avisar(mensagem: String) {
        if (atividade.isFinishing) return
        AlertDialog.Builder(atividade).setTitle("Atualização").setMessage(mensagem).setPositiveButton("Ok", null).show()
    }

    /** Volta da tela de permissão "instalar apps desta fonte": segue a instalação que estava esperando. */
    fun retomar() {
        val arquivo = aguardandoPermissao ?: return
        if (podeInstalar()) {
            aguardandoPermissao = null
            instalar(arquivo)
        }
    }

    private fun buscarVersao(): Versao {
        val conexao = (URL(BASE + "versao.json").openConnection() as HttpURLConnection).apply {
            connectTimeout = 15_000
            readTimeout = 15_000
            instanceFollowRedirects = true
            setRequestProperty("Accept", "application/json")
        }
        try {
            if (conexao.responseCode != 200) throw IllegalStateException("versao.json: HTTP ${conexao.responseCode}")
            val j = JSONObject(conexao.inputStream.bufferedReader().use { it.readText() })
            val apk = j.getString("apk")
            require(Regex("[A-Za-z0-9._-]+\\.apk").matches(apk)) { "nome de APK inválido" }
            val sha = j.getString("sha256").lowercase()
            require(Regex("[0-9a-f]{64}").matches(sha)) { "SHA-256 inválido" }
            return Versao(j.getLong("versionCode"), j.optString("versionName", j.getLong("versionCode").toString()), sha,
                j.optLong("tamanho", 0), apk, j.optString("assinatura_sha256").takeIf { it.isNotBlank() }?.replace(":", ""))
        } finally {
            conexao.disconnect()
        }
    }

    private fun perguntar(v: Versao) {
        if (atividade.isFinishing) return
        val mb = if (v.tamanho > 0) " (${v.tamanho / 1_000_000} MB)" else ""
        val dados = if (redeMedida()) "\n\nVocê está usando dados móveis; se preferir, atualize no Wi-Fi." else ""
        AlertDialog.Builder(atividade)
            .setTitle("Nova versão do CRIVO")
            .setMessage("A versão ${v.nome}$mb está disponível. As conversas guardadas no app ficam.$dados")
            .setPositiveButton("Atualizar") { _, _ -> baixar(v) }
            .setNegativeButton("Depois", null)
            .setNeutralButton("Pular esta versão") { _, _ -> prefs.edit().putLong("pular", v.codigo).apply() }
            .show()
    }

    private fun avisarChaveDiferente(v: Versao, manual: Boolean = false) {
        if (atividade.isFinishing || (!manual && prefs.getLong("avisou_chave", -1) == v.codigo)) return
        prefs.edit().putLong("avisou_chave", v.codigo).apply()
        AlertDialog.Builder(atividade)
            .setTitle("Nova versão do CRIVO")
            .setMessage("A versão ${v.nome} foi assinada com outra chave, e o Android não deixa instalar por cima. " +
                "Para atualizar desta vez, desinstale o CRIVO e instale o CRIVO.apk novo pelo navegador.")
            .setPositiveButton("Abrir a página") { _, _ ->
                atividade.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/HROSONE/CRIVO/releases/tag/android-latest")))
            }
            .setNegativeButton("Agora não", null)
            .show()
    }

    private fun baixar(v: Versao) {
        cancelado = false
        val texto = TextView(atividade).apply { text = "Baixando…"; setPadding(0, 0, 0, 24) }
        val barra = ProgressBar(atividade, null, android.R.attr.progressBarStyleHorizontal).apply { max = 1000 }
        val caixa = LinearLayout(atividade).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(64, 32, 64, 0)
            addView(texto); addView(barra)
        }
        val janela = AlertDialog.Builder(atividade)
            .setTitle("Atualizando o CRIVO")
            .setView(caixa)
            .setCancelable(false)
            .setNegativeButton("Cancelar") { _, _ -> cancelado = true }
            .show()
        thread(name = "crivo-download") {
            val resultado = runCatching {
                val arquivo = baixarArquivo(v) { feito, total ->
                    naTela {
                        if (total > 0) barra.progress = (feito * 1000 / total).toInt()
                        texto.text = "Baixando… ${feito / 1_000_000} de ${if (total > 0) total / 1_000_000 else "?"} MB"
                    }
                }
                naTela { texto.text = "Conferindo o arquivo…" }
                conferir(arquivo, v)
                arquivo
            }
            naTela {
                runCatching { janela.dismiss() }
                resultado.onSuccess { instalar(it) }
                resultado.onFailure { erro ->
                    if (!cancelado) Toast.makeText(atividade, "A atualização não deu certo: ${erro.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    /** Baixa o APK para o cache do app, retomando de onde parou (cabeçalho Range). */
    private fun baixarArquivo(v: Versao, progresso: (Long, Long) -> Unit): File {
        pasta.mkdirs()
        val final = File(pasta, "CRIVO-${v.codigo}.apk")
        if (final.isFile && sha256(final) == v.sha256) return final
        val parte = File(pasta, "CRIVO-${v.codigo}.apk.parte")
        var inicio = if (parte.isFile) parte.length() else 0L
        val conexao = (URL(BASE + v.apk).openConnection() as HttpURLConnection).apply {
            connectTimeout = 20_000
            readTimeout = 60_000
            instanceFollowRedirects = true
            if (inicio > 0) setRequestProperty("Range", "bytes=$inicio-")
        }
        try {
            val codigo = conexao.responseCode
            if (codigo == 200) inicio = 0L else if (codigo != 206) throw IllegalStateException("HTTP $codigo")
            val total = if (v.tamanho > 0) v.tamanho else inicio + conexao.contentLengthLong
            var feito = inicio
            var ultimo = 0L
            conexao.inputStream.use { entrada ->
                FileOutputStream(parte, inicio > 0).use { saida ->
                    val buf = ByteArray(1 shl 16)
                    while (true) {
                        if (cancelado) throw InterruptedException("cancelado")
                        val n = entrada.read(buf)
                        if (n < 0) break
                        saida.write(buf, 0, n)
                        feito += n
                        if (feito - ultimo > 1_000_000) { ultimo = feito; progresso(feito, total) }
                    }
                }
            }
            progresso(feito, total)
        } finally {
            conexao.disconnect()
        }
        if (!parte.renameTo(final)) throw IllegalStateException("não consegui guardar o arquivo")
        return final
    }

    /** SHA-256 do versao.json, mesmo pacote, versão nova e a mesma chave do app instalado. */
    private fun conferir(arquivo: File, v: Versao) {
        if (sha256(arquivo) != v.sha256) {
            arquivo.delete()
            throw SecurityException("o arquivo baixado não confere (SHA-256)")
        }
        val pm = atividade.packageManager
        val info = pm.getPackageArchiveInfo(arquivo.path, flagsAssinatura())
            ?: throw SecurityException("o arquivo baixado não é um APK válido")
        if (info.packageName != atividade.packageName) throw SecurityException("o APK é de outro app")
        if (codigo(info) <= versaoInstalada()) throw IllegalStateException("o APK não é mais novo que o instalado")
        val nova = certificados(info)
        val minha = certificados(pm.getPackageInfo(atividade.packageName, flagsAssinatura()))
        if (nova.isEmpty() || nova.intersect(minha.toSet()).isEmpty()) throw SecurityException("o APK foi assinado com outra chave")
    }

    private fun instalar(arquivo: File) {
        if (!podeInstalar()) {
            aguardandoPermissao = arquivo
            AlertDialog.Builder(atividade)
                .setTitle("Permitir a atualização")
                .setMessage("O Android vai pedir para permitir que o CRIVO instale a própria atualização. Ligue a opção e volte.")
                .setPositiveButton("Continuar") { _, _ ->
                    atividade.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:${atividade.packageName}")))
                }
                .setNegativeButton("Agora não", null)
                .show()
            return
        }
        Toast.makeText(atividade, "Preparando a instalação…", Toast.LENGTH_SHORT).show()
        thread(name = "crivo-instalar") {
            val erro = runCatching {
                val instalador = atividade.packageManager.packageInstaller
                val parametros = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL)
                    .apply { setAppPackageName(atividade.packageName) }
                val id = instalador.createSession(parametros)
                instalador.openSession(id).use { sessao ->
                    sessao.openWrite("CRIVO.apk", 0, arquivo.length()).use { saida ->
                        arquivo.inputStream().use { it.copyTo(saida, 1 shl 16) }
                        sessao.fsync(saida)
                    }
                    val aviso = Intent(atividade, InstalacaoRecebedor::class.java).setAction(ACAO_STATUS)
                    val flags = PendingIntent.FLAG_UPDATE_CURRENT or
                        (if (Build.VERSION.SDK_INT >= 31) PendingIntent.FLAG_MUTABLE else 0)
                    sessao.commit(PendingIntent.getBroadcast(atividade, id, aviso, flags).intentSender)
                }
            }.exceptionOrNull()
            if (erro != null) naTela {
                Toast.makeText(atividade, "Não consegui instalar: ${erro.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun podeInstalar() = atividade.packageManager.canRequestPackageInstalls()

    private fun redeMedida(): Boolean {
        val cm = atividade.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager ?: return false
        return runCatching { cm.isActiveNetworkMetered }.getOrDefault(false)
    }

    /** Tira do cache os APKs que já foram instalados (ou ficaram velhos). */
    private fun limparAntigos() {
        val minha = versaoInstalada()
        pasta.listFiles()?.forEach { f ->
            val n = Regex("CRIVO-(\\d+)\\.apk").find(f.name)?.groupValues?.get(1)?.toLongOrNull()
            if (n == null || n <= minha) f.delete()
        }
    }

    private fun versaoInstalada(): Long = codigo(atividade.packageManager.getPackageInfo(atividade.packageName, 0))

    @Suppress("DEPRECATION")
    private fun codigo(info: PackageInfo): Long =
        if (Build.VERSION.SDK_INT >= 28) info.longVersionCode else info.versionCode.toLong()

    @Suppress("DEPRECATION")
    private fun flagsAssinatura(): Int =
        if (Build.VERSION.SDK_INT >= 28) PackageManager.GET_SIGNING_CERTIFICATES else PackageManager.GET_SIGNATURES

    /** SHA-256 (hex) dos certificados que assinam o pacote; é o mesmo que o apksigner imprime. */
    @Suppress("DEPRECATION")
    private fun certificados(info: PackageInfo?): List<String> {
        val brutos = if (Build.VERSION.SDK_INT >= 28) {
            val s = info?.signingInfo ?: return emptyList()
            (if (s.hasMultipleSigners()) s.apkContentsSigners else s.signingCertificateHistory)?.toList() ?: emptyList()
        } else {
            info?.signatures?.toList() ?: emptyList()
        }
        return brutos.map { hex(MessageDigest.getInstance("SHA-256").digest(it.toByteArray())) }
    }

    private fun assinaturaInstalada(): String? = runCatching {
        certificados(atividade.packageManager.getPackageInfo(atividade.packageName, flagsAssinatura())).lastOrNull()
    }.getOrNull()

    private fun sha256(f: File): String {
        val md = MessageDigest.getInstance("SHA-256")
        f.inputStream().use { entrada ->
            val buf = ByteArray(1 shl 16)
            while (true) {
                val n = entrada.read(buf)
                if (n < 0) break
                md.update(buf, 0, n)
            }
        }
        return hex(md.digest())
    }

    private fun hex(b: ByteArray) = b.joinToString("") { "%02x".format(it) }

    private fun naTela(bloco: () -> Unit) = atividade.runOnUiThread { if (!atividade.isFinishing) bloco() }
}
