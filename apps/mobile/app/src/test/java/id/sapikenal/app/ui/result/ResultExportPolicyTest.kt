package id.sapikenal.app.ui.result

import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Test

class ResultExportPolicyTest {
    private val canonicalScores =
        mapOf(
            "aceh" to 0.05f,
            "bali" to 0.7f,
            "limusin" to 0.05f,
            "madura" to 0.05f,
            "non_sapi" to 0.05f,
            "pasundan" to 0.05f,
            "po" to 0.05f,
        )

    private fun result(scores: Map<String, Float> = canonicalScores) =
        DetectionResult(
            id = 1L,
            label = "bali",
            displayLabel = "Bali",
            confidence = 0.7f,
            isReliable = true,
            allScores = scores,
            inferenceMode = InferenceMode.ONLINE,
        )

    @Test
    fun `fresh result requires exactly the canonical finite bounded scores`() {
        val complete = result()
        assertSame(complete, selectResultForExport(false, null, complete))

        listOf(
            canonicalScores - "limusin",
            canonicalScores + ("unknown" to 0f),
            canonicalScores + ("bali" to Float.NaN),
            canonicalScores + ("bali" to Float.POSITIVE_INFINITY),
            canonicalScores + ("bali" to Float.NEGATIVE_INFINITY),
            canonicalScores + ("bali" to -0.01f),
            canonicalScores + ("bali" to 1.01f),
        ).forEach { scores ->
            assertNull(selectResultForExport(false, null, result(scores)))
        }
    }

    @Test
    fun `fresh result requires valid identity and confidence`() {
        listOf(
            result().copy(id = 0L),
            result().copy(label = " "),
            result().copy(displayLabel = " "),
            result().copy(displayLabel = "Madura"),
            result().copy(confidence = Float.NaN),
            result().copy(confidence = Float.POSITIVE_INFINITY),
            result().copy(confidence = -0.01f),
            result().copy(confidence = 1.01f),
        ).forEach { candidate ->
            assertNull(selectResultForExport(false, null, candidate))
        }
    }

    @Test
    fun `history export waits for complete persisted result`() {
        val fresh = result()
        assertNull(selectResultForExport(true, null, fresh))
        assertSame(fresh, selectResultForExport(true, fresh, null))
        assertNull(selectResultForExport(true, fresh.copy(allScores = canonicalScores - "bali"), null))
    }

    @Test
    fun `fresh result can fall back to complete persisted result after recreation`() {
        val persisted = result()
        assertSame(persisted, selectResultForExport(false, persisted, null))
        assertNull(selectResultForExport(false, persisted.copy(confidence = Float.NaN), null))
    }
}
