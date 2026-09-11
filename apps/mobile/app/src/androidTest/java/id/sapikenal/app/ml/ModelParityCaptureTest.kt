package id.sapikenal.app.ml

import android.content.Context
import android.net.Uri
import android.os.Build
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import id.sapikenal.app.domain.model.BreedContract
import id.sapikenal.app.ml.preprocessing.ClientPreprocessor
import id.sapikenal.app.ml.preprocessing.ModelPreprocessor
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest

/** Real local fixtures only. Captures evidence; the host comparator decides parity. */
@RunWith(AndroidJUnit4::class)
class ModelParityCaptureTest {
    @Test
    fun captureProductionPreprocessingAndOfflineScores() =
        runBlocking {
            val context = ApplicationProvider.getApplicationContext<Context>()
            val requestedRunId = InstrumentationRegistry.getArguments().getString("parityRun")
            assumeTrue("Parity capture requires the host script", requestedRunId != null)
            val runId = requireNotNull(requestedRunId)
            require(runId.matches(Regex("parity(-[a-f0-9]+)?")))
            val root = File(context.filesDir, runId)
            val fixtures = File(root, "input").listFiles()?.sortedBy { it.name }.orEmpty()
            assertTrue("Stage real JPEG fixtures in files/parity/input first", fixtures.isNotEmpty())
            val output = File(root, "output").apply { mkdirs() }
            val labels = listOf("aceh", "bali", "limusin", "madura", "pasundan", "po")
            assertEquals(labels, BreedContract.CANONICAL_LABELS)
            val client = ClientPreprocessor(context)
            val preprocessor = ModelPreprocessor()
            val engine = OfflineInferenceEngine(context, preprocessor)
            val observations = JSONArray()
            for (fixture in fixtures) {
                require(fixture.isFile && fixture.name.matches(Regex("fixture-[0-9]+\\.jpg")))
                val outputName = "${fixture.nameWithoutExtension}.png"
                val imageBytes = client.process(Uri.fromFile(fixture))
                val input = preprocessor.process(imageBytes)
                assertEquals(224 * 224 * 3 * 4, input.remaining())
                val tensor = ByteArray(input.remaining())
                input.get(tensor)
                val result = engine.classify(imageBytes)
                assertEquals(labels, result.allScores.keys.toList())
                assertEquals(labels.maxBy { result.allScores.getValue(it) }, result.label)
                File(output, outputName).writeBytes(imageBytes)
                File(output, "$outputName.f32").writeBytes(tensor)
                observations.put(
                    JSONObject()
                        .put("id", outputName)
                        .put("source_sha256", sha256(fixture.readBytes()))
                        .put("image_sha256", sha256(imageBytes))
                        .put("tensor_sha256", sha256(tensor))
                        .put("scores", JSONArray(labels.map { result.allScores.getValue(it) }))
                        .put("winner", result.label),
                )
            }
            val report =
                JSONObject()
                    .put("schema", 1)
                    .put("class_order", JSONArray(labels))
                    .put("model_version", OfflineInferenceEngine.MODEL_VERSION)
                    .put("model_sha256", sha256(context.assets.open("lokal_fp32.tflite").use { it.readBytes() }))
                    .put("device", "${Build.MANUFACTURER} ${Build.MODEL}; Android ${Build.VERSION.RELEASE}; API ${Build.VERSION.SDK_INT}")
                    .put(
                        "byte_order",
                        java.nio.ByteOrder
                            .nativeOrder()
                            .toString(),
                    ).put("input_shape", JSONArray(listOf(1, 224, 224, 3)))
                    .put("output_shape", JSONArray(listOf(1, 6)))
                    .put("dtype", "float32")
                    .put(
                        "tflite_runtime",
                        org.tensorflow.lite.TensorFlowLite
                            .runtimeVersion(),
                    ).put("observations", observations)
            File(output, "android.json").writeText(report.toString(2))
        }

    private fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
}
