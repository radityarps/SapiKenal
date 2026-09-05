package id.sapikenal.app.ml

import android.content.Context
import android.graphics.Bitmap
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import id.sapikenal.app.ml.preprocessing.ModelPreprocessor
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.ByteArrayOutputStream

@RunWith(AndroidJUnit4::class)
class OfflineInferenceEngineSmokeTest {
    @Test
    fun currentTfliteAssetRunsFourClassProbabilitySmokeTest() =
        runBlocking {
            val context = ApplicationProvider.getApplicationContext<Context>()
            val engine = OfflineInferenceEngine(context, ModelPreprocessor())

            val result = engine.classify(createJpeg())

            assertEquals(setOf("bali", "brahman", "brangus", "limusin"), result.allScores.keys)
            assertTrue(result.allScores.values.all { it.isFinite() && it in 0f..1f })
            assertEquals(1f, result.allScores.values.sum(), 0.01f)
            assertEquals(OfflineInferenceEngine.MODEL_VERSION, result.modelVersion)
            assertEquals("ACCEPTED", result.outcome)
        }

    private fun createJpeg(): ByteArray {
        val bitmap = Bitmap.createBitmap(224, 224, Bitmap.Config.ARGB_8888)
        bitmap.eraseColor(0xff808080.toInt())
        return ByteArrayOutputStream().use { output ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, output)
            bitmap.recycle()
            output.toByteArray()
        }
    }
}
