package id.sapikenal.app.ml

import android.content.Context
import android.os.SystemClock
import android.util.Log
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.di.NetworkModule
import id.sapikenal.app.ml.preprocessing.ModelPreprocessor
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.io.File
import java.util.Locale

@RunWith(AndroidJUnit4::class)
class LocalOnlineInferenceBenchmarkTest {
    @Test
    fun benchmarkSameImagesThroughLocalAndOnlineInference() =
        runBlocking {
            val context = ApplicationProvider.getApplicationContext<Context>()
            val arguments = InstrumentationRegistry.getArguments()
            val warmups = arguments.getString("warmups")?.toIntOrNull() ?: 3
            val runs = arguments.getString("runs")?.toIntOrNull() ?: 10
            val imageDir = File(context.filesDir, "benchmark")
            val images =
                imageDir
                    .listFiles { file -> file.extension.lowercase() in setOf("jpg", "jpeg") }
                    ?.sortedBy(File::getName)
                    .orEmpty()
            assertTrue("Push JPEG files to ${imageDir.absolutePath} before running the benchmark", images.isNotEmpty())

            val moshi = NetworkModule.provideMoshi()
            val api =
                Retrofit
                    .Builder()
                    .baseUrl(BuildConfig.API_BASE_URL)
                    .client(NetworkModule.provideOkHttpClient())
                    .addConverterFactory(MoshiConverterFactory.create(moshi))
                    .build()
                    .create(InferenceApiService::class.java)
            val local = OfflineInferenceEngine(context, ModelPreprocessor())
            val online = OnlineInferenceClient(api, moshi)

            val resultsJson = StringBuilder("[\n")
            var firstEntry = true

            Log.i(
                TAG,
                "BENCHMARK_META ${jsonObject(
                    "base_url" to BuildConfig.API_BASE_URL,
                    "warmups" to warmups,
                    "runs" to runs,
                    "images" to images.size,
                )}",
            )
            println(
                "BENCHMARK_META ${jsonObject(
                    "base_url" to BuildConfig.API_BASE_URL,
                    "warmups" to warmups,
                    "runs" to runs,
                    "images" to images.size,
                )}",
            )

            output.appendLine(
                jsonObject(
                    "record_type" to "meta",
                    "base_url" to BuildConfig.API_BASE_URL,
                    "warmups" to warmups,
                    "runs" to runs,
                    "images" to images.size,
                ),
            )
            images.forEach { image ->
                val bytes = image.readBytes()
                repeat(warmups) {
                    local.classify(bytes)
                    online.classify(bytes)
                }
                repeat(runs) { iteration ->
                    for ((mode, classifier) in listOf("local" to local, "online" to online)) {
                        val started = SystemClock.elapsedRealtimeNanos()
                        val result = classifier.classify(bytes)
                        val elapsedMs = (SystemClock.elapsedRealtimeNanos() - started) / 1_000_000.0
                        val obsJson =
                            jsonObject(
                                "image" to image.name,
                                "iteration" to iteration + 1,
                                "mode" to mode,
                                "total_ms" to elapsedMs,
                                "server_processing_ms" to result.processingMs,
                                "label" to result.label,
                                "confidence" to result.confidence,
                                "model_version" to result.modelVersion,
                                "status" to "ok",
                            )
                        Log.i(TAG, "BENCHMARK_OBSERVATION $obsJson")
                        println("BENCHMARK_OBSERVATION $obsJson")

                        if (!firstEntry) resultsJson.append(",\n")
                        resultsJson.append("  ").append(obsJson)
                        firstEntry = false
                    }
                }
            }
            resultsJson.append("\n]")
            File(context.filesDir, "benchmark_results.json").writeText(resultsJson.toString())
        }

    private fun jsonObject(vararg entries: Pair<String, Any?>): String =
        entries.joinToString(prefix = "{", postfix = "}") { (key, value) ->
            "\"${escape(key)}\":" +
                when (value) {
                    null -> "null"
                    is Number, is Boolean -> value.toString()
                    else -> "\"${escape(value.toString())}\""
                }
        }

    private fun escape(value: String): String = value.replace("\\", "\\\\").replace("\"", "\\\"")

    private companion object {
        const val TAG = "SapiKenalBenchmark"
    }
}
