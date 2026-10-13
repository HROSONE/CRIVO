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

    buildTypes {
        release {
            isMinifyEnabled = false
            // Chave guardada no cache do CI (ver .github/workflows/apk-android.yml).
            signingConfig = signingConfigs.getByName("debug")
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
