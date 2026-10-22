package br.crivo.app

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.job.JobInfo
import android.app.job.JobParameters
import android.app.job.JobScheduler
import android.app.job.JobService
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import kotlin.concurrent.thread

/**
 * Verificação em segundo plano: a cada 12 horas, com rede, confere o release e só avisa com uma notificação.
 * Não baixa nem instala nada. Quem instala é a pessoa, com o app aberto (Atualizador).
 */
class AtualizacaoFundo : JobService() {
    override fun onStartJob(params: JobParameters): Boolean {
        thread(name = "crivo-atualizacao-fundo") {
            try { conferir(this) } finally { jobFinished(params, false) }
        }
        return true
    }

    // Parou antes de terminar (sem rede, sistema sob pressão): tenta de novo no próximo ciclo.
    override fun onStopJob(params: JobParameters): Boolean = false

    companion object {
        private const val JOB = 0x4352
        private const val CANAL = "crivo_atualizacoes"
        private const val AVISO = 202

        /** Liga ou desliga conforme a opção "atualização automática" (Atualizador.abrirConfiguracoes). */
        fun agendar(contexto: Context) {
            val agendador = contexto.getSystemService(JobScheduler::class.java)
            if (!automatico(contexto)) {
                agendador.cancel(JOB)
                return
            }
            agendador.schedule(JobInfo.Builder(JOB, ComponentName(contexto, AtualizacaoFundo::class.java))
                .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
                .setPeriodic(12L * 60 * 60 * 1000)
                .build())
        }

        private fun automatico(contexto: Context): Boolean =
            contexto.getSharedPreferences(Atualizador.PREFS, Context.MODE_PRIVATE).getBoolean("automatico", true)

        private fun conferir(contexto: Context) {
            if (!automatico(contexto)) return
            val prefs = contexto.getSharedPreferences(Atualizador.PREFS, Context.MODE_PRIVATE)
            val publicada = Atualizador.publicada() ?: return
            if (publicada.codigo <= versaoInstalada(contexto)) return
            // Não repete o aviso da mesma versão, nem avisa a versão que a pessoa pulou.
            if (prefs.getLong("pular", -1) == publicada.codigo || prefs.getLong("avisado", -1) == publicada.codigo) return
            avisar(contexto, publicada)
            prefs.edit().putLong("avisado", publicada.codigo).apply()
        }

        @Suppress("DEPRECATION")
        private fun versaoInstalada(contexto: Context): Long {
            val info = contexto.packageManager.getPackageInfo(contexto.packageName, 0)
            return if (Build.VERSION.SDK_INT >= 28) info.longVersionCode else info.versionCode.toLong()
        }

        private fun avisar(contexto: Context, versao: Atualizador.Versao) {
            // Sem permissão de notificação (Android 13+), o aviso fica para quando o app for aberto.
            if (Build.VERSION.SDK_INT >= 33 &&
                contexto.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
            val gerenciador = contexto.getSystemService(NotificationManager::class.java)
            gerenciador.createNotificationChannel(NotificationChannel(CANAL, "Atualizações do CRIVO",
                NotificationManager.IMPORTANCE_DEFAULT))
            val abrir = PendingIntent.getActivity(contexto, 0, Intent(contexto, MainActivity::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            gerenciador.notify(AVISO, Notification.Builder(contexto, CANAL)
                .setSmallIcon(R.mipmap.ic_crivo)
                .setContentTitle("CRIVO ${versao.nome} disponível")
                .setContentText("Toque para abrir e atualizar.")
                .setContentIntent(abrir)
                .setAutoCancel(true)
                .build())
        }
    }
}
