package id.sapikenal.app.ml

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineModelMetadataTest {
    @Test
    fun `offline model version matches selected dynamic range artifact`() {
        assertEquals(
            "cattle-disease-mobilenetv3-v20260725-fp32",
            OfflineInferenceEngine.MODEL_VERSION,
        )
    }

    @Test
    fun `offline model version preserves base model traceability`() {
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("mobilenetv3"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("v20260725"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("fp32"))
    }
}
