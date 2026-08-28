package id.sapikenal.app.acceptance

import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.ImageSource
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.domain.model.LocationSource
import id.sapikenal.app.domain.usecase.ClassifyImageUseCase
import id.sapikenal.app.location.LocationResolver
import id.sapikenal.app.ml.OfflineInferenceEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Acceptance test suite covering PRD behavior requirements.
 * Tests are organized by feature area matching issue acceptance criteria.
 */
class AcceptanceTestSuite {
    // ══════════════════════════════════════════════════════════════════════
    // Consent Routing (Issue #2)
    // ══════════════════════════════════════════════════════════════════════

    @Test
    fun `consent ALLOWED maps from boolean true`() {
        assertEquals(ConsentStatus.ALLOWED, ConsentStatus.fromBoolean(true))
    }

    @Test
    fun `consent DENIED maps from boolean false`() {
        assertEquals(ConsentStatus.DENIED, ConsentStatus.fromBoolean(false))
    }

    @Test
    fun `consent UNDECIDED maps from null`() {
        assertEquals(ConsentStatus.UNDECIDED, ConsentStatus.fromBoolean(null))
    }

    @Test
    fun `consent status persists in DetectionResult`() {
        val result = createResult(consentStatus = ConsentStatus.DENIED)
        assertEquals(ConsentStatus.DENIED, result.consentStatus)
    }

    // ══════════════════════════════════════════════════════════════════════
    // Image Quality Gate (Issue #3 / spec)
    // ══════════════════════════════════════════════════════════════════════
    // Quality gate tests are in ImageQualityGateTest.kt

    // ══════════════════════════════════════════════════════════════════════
    // Classification Result (Issue #4)
    // ══════════════════════════════════════════════════════════════════════

    @Test
    fun `detection result has isReliable flag`() {
        val reliable = createResult(confidence = 0.85f)
        assertTrue(reliable.isReliable)

        val unreliable = createResult(confidence = 0.45f, isReliable = false)
        assertEquals(false, unreliable.isReliable)
    }

    @Test
    fun `detection result holds app version`() {
        val result = createResult(appVersion = "1.2.0")
        assertEquals("1.2.0", result.appVersion)
    }

    @Test
    fun `detection result holds model version`() {
        val result = createResult(modelVersion = "MobileNetV2-v3")
        assertEquals("MobileNetV2-v3", result.modelVersion)
    }

    // ══════════════════════════════════════════════════════════════════════
    // Local Scan History (Issue #5)
    // ══════════════════════════════════════════════════════════════════════
    // Room DAO tests are in DetectionDaoTest.kt and DetectionRepositoryTest.kt

    @Test
    fun `image source CAMERA maps correctly`() {
        assertEquals(ImageSource.CAMERA, ImageSource.fromBoolean(true))
    }

    @Test
    fun `image source GALLERY maps correctly`() {
        assertEquals(ImageSource.GALLERY, ImageSource.fromBoolean(false))
    }

    @Test
    fun `preprocessing summary constant is set`() {
        assertNotNull(ClassifyImageUseCase.PREPROCESSING_SUMMARY)
        assertTrue(ClassifyImageUseCase.PREPROCESSING_SUMMARY.isNotEmpty())
    }

    // ══════════════════════════════════════════════════════════════════════
    // Coarse Location (Issue #6)
    // ══════════════════════════════════════════════════════════════════════

    @Test
    fun `location resolver with GPS disabled and no manual returns null`() {
        val result = LocationResolver.resolve(false, null, null, null)
        assertNull(result.latitude)
    }

    @Test
    fun `location resolver with manual coords returns MANUAL source`() {
        val result = LocationResolver.resolve(false, null, -6.20, 106.85)
        assertEquals(LocationSource.MANUAL, result.source)
    }

    // ══════════════════════════════════════════════════════════════════════
    // Soft Delete and Purge (Issue #7)
    // ══════════════════════════════════════════════════════════════════════
    // PurgeManager tests are in PurgeManagerTest.kt

    @Test
    fun `detection result has deletedAt field for soft delete`() {
        val result = createResult()
        assertNull(result.deletedAt) // Not deleted by default
    }

    // ══════════════════════════════════════════════════════════════════════
    // PDF Export (Issue #8)
    // ══════════════════════════════════════════════════════════════════════
    // PDF content tests are in PdfReportContentTest.kt

    @Test
    fun `detection result has pdfCachePath field`() {
        val result = createResult(pdfCachePath = "/cache/report.pdf")
        assertEquals("/cache/report.pdf", result.pdfCachePath)
    }

    // ══════════════════════════════════════════════════════════════════════
    // TFLite Version Traceability (Issue #14)
    // ══════════════════════════════════════════════════════════════════════

    @Test
    fun `offline model version constant is defined`() {
        assertNotNull(OfflineInferenceEngine.MODEL_VERSION)
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.isNotEmpty())
    }

    @Test
    fun `offline model version follows naming convention`() {
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("mobilenetv3"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("v20260725"))
        assertTrue(OfflineInferenceEngine.MODEL_VERSION.contains("fp32"))
    }

    // ══════════════════════════════════════════════════════════════════════
    // Settings and Privacy (Issue #10)
    // ══════════════════════════════════════════════════════════════════════

    @Test
    fun `all inference modes are defined`() {
        val modes = InferenceMode.entries
        assertEquals(3, modes.size)
        assertTrue(modes.contains(InferenceMode.ONLINE))
        assertTrue(modes.contains(InferenceMode.OFFLINE))
        assertTrue(modes.contains(InferenceMode.OFFLINE_FALLBACK))
    }

    // ══════════════════════════════════════════════════════════════════════
    // Helpers
    // ══════════════════════════════════════════════════════════════════════

    private fun createResult(
        confidence: Float = 0.92f,
        isReliable: Boolean = true,
        consentStatus: ConsentStatus = ConsentStatus.ALLOWED,
        appVersion: String? = "1.0.0",
        modelVersion: String? = "MobileNetV2-v3",
        pdfCachePath: String? = null,
    ) = DetectionResult(
        id = 1L,
        label = "FMD",
        displayLabel = "PMK",
        confidence = confidence,
        isReliable = isReliable,
        allScores = mapOf("FMD" to 0.92f, "LSD" to 0.05f, "healthy" to 0.03f),
        inferenceMode = InferenceMode.ONLINE,
        consentStatus = consentStatus,
        appVersion = appVersion,
        modelVersion = modelVersion,
        pdfCachePath = pdfCachePath,
    )
}
