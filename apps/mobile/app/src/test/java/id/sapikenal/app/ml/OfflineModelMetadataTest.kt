package id.sapikenal.app.ml

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineModelMetadataTest {
    @Test
    fun `offline model uses the four canonical breed classes`() {
        assertEquals(listOf("bali", "brahman", "brangus", "limusin"), OfflineInferenceEngine.CANONICAL_LABELS)
    }

    @Test
    fun `offline model version matches selected dynamic range artifact`() {
        assertEquals(
            "sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32",
            OfflineInferenceEngine.MODEL_VERSION,
        )
    }

    @Test
    fun `offline model version preserves base model traceability`() {
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("mobilenetv3"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("contract-v1"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("fp32"))
    }
}
