plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "br.crivo.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.crivo.app"
        minSdk = 26
        targetSdk = 35
        // O CI preenche com o número da execução; cada APK novo instala por cima do anterior.
        versionCode = (System.getenv("CRIVO_VERSION_CODE") ?: "1").toInt()
        versionName = System.getenv("CRIVO_VERSION_NAME") ?: "dev"
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    // Mesma chave em todo APK, para cada versão nova instalar por cima da anterior.
    // O CI passa o arquivo e a senha (ver .github/workflows/apk-android.yml); sem eles, a chave de depuração.
    val chave = System.getenv("CRIVO_KEYSTORE")?.let { file(it) }?.takeIf { it.isFile }
    signingConfigs {
        if (chave != null) {
            create("crivo") {
                storeFile = chave
                storePassword = System.getenv("CRIVO_KEYSTORE_SENHA")
                keyAlias = "crivo"
                keyPassword = System.getenv("CRIVO_KEYSTORE_SENHA")
            }
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = if (chave != null) signingConfigs.getByName("crivo") else signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    androidResources {
        // O zip do CRIVO já vem comprimido; o app o lê direto do APK.
        noCompress += listOf("zip")
    }
}

chaquopy {
    defaultConfig {
        version = "3.12"
        pip {
            install("numpy")
        }
    }
}
