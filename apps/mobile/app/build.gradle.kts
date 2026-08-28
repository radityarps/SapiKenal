import java.util.Properties


fun localProperty(name: String): String? {
    val file = rootProject.file("local.properties")
    if (!file.exists()) return null
    return Properties().apply { file.inputStream().use(::load) }.getProperty(name)
}

fun envOrProperty(
    name: String,
    defaultValue: String,
): String =
    providers.gradleProperty(name).orNull
        ?: System.getenv(name)
        ?: localProperty(name)
        ?: defaultValue

fun apiBaseUrl(defaultValue: String): String {
    val raw = envOrProperty("API_BASE_URL", defaultValue)
    val normalized = if (raw.endsWith("/")) raw else "$raw/"
    require(normalized.startsWith("http://") || normalized.startsWith("https://")) {
        "API_BASE_URL must start with http:// or https://"
    }
    return "\"$normalized\""
}

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "id.sapikenal.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "id.sapikenal.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"

        // Keep APK/App Bundle on ARM ABIs to avoid shipping incompatible x86_64 native libs.
        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a")
        }

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }

        buildConfigField("String", "API_BASE_URL", apiBaseUrl("http://10.0.2.2:8000/"))
        buildConfigField("String", "MODEL_FILE_NAME", "\"${envOrProperty("MODEL_FILE_NAME", "cattle_disease.tflite")}\"")
        buildConfigField("String", "MODEL_VERSION", "\"${envOrProperty("MODEL_VERSION", "cattle-disease-mobilenetv3-v20260725-fp32")}\"")
        buildConfigField("int", "MODEL_INPUT_SIZE", envOrProperty("MODEL_INPUT_SIZE", "224"))
        buildConfigField("float", "CONFIDENCE_THRESHOLD", "${envOrProperty("CONFIDENCE_THRESHOLD", "0.60")}f")
    }

    buildTypes {
        debug {
            buildConfigField("String", "API_BASE_URL", apiBaseUrl("http://10.0.2.2:8000/"))
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            buildConfigField("String", "API_BASE_URL", apiBaseUrl("https://api.sapikenal.example/"))
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.00")

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.6")

    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.8.2")
    implementation("androidx.compose.ui:ui-text-google-fonts")

    implementation("com.google.dagger:hilt-android:2.59")
    ksp("com.google.dagger:hilt-compiler:2.59")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    implementation("androidx.hilt:hilt-work:1.2.0")
    ksp("androidx.hilt:hilt-compiler:1.2.0")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Image loading
    implementation("io.coil-kt:coil-compose:2.6.0")
    implementation("io.coil-kt:coil-svg:2.6.0")

    // Settings persistence
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    implementation("org.tensorflow:tensorflow-lite:2.17.0")

    implementation("androidx.camera:camera-core:1.4.2")
    implementation("androidx.camera:camera-camera2:1.4.2")
    implementation("androidx.camera:camera-lifecycle:1.4.2")
    implementation("androidx.camera:camera-view:1.4.2")

    implementation("androidx.exifinterface:exifinterface:1.3.7")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    testImplementation("org.robolectric:robolectric:4.11.1")
    testImplementation("org.mockito:mockito-inline:5.2.0")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.3.1")
    testImplementation("androidx.test:core:1.5.0")
    testImplementation("androidx.room:room-testing:2.6.1")
    androidTestImplementation("androidx.test:core:1.5.0")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test:runner:1.6.2")
}

ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}
