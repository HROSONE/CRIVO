package br.crivo.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.os.Build
import android.widget.Toast

/**
 * Resposta do instalador do Android à atualização (Atualizador.instalar).
 *
 * Quando o Android pede a confirmação da pessoa, abre a tela dele; nos outros casos, só avisa. Um app de fora da loja
 * não pode se instalar sem essa confirmação.
 */
class InstalacaoRecebedor : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Atualizador.ACAO_STATUS) return
        when (val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val confirmar = if (Build.VERSION.SDK_INT >= 33) {
                    intent.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
                } else {
                    @Suppress("DEPRECATION") intent.getParcelableExtra(Intent.EXTRA_INTENT)
                }
                confirmar?.let { context.startActivity(it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            }
            PackageInstaller.STATUS_SUCCESS -> Unit   // o Android fecha o app antigo; a pessoa abre a versão nova
            PackageInstaller.STATUS_FAILURE_ABORTED -> Toast.makeText(context, "Atualização cancelada.", Toast.LENGTH_SHORT).show()
            else -> {
                val msg = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE) ?: "código $status"
                Toast.makeText(context, "A atualização não foi instalada: $msg", Toast.LENGTH_LONG).show()
            }
        }
    }
}
