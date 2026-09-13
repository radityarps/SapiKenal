package id.sapikenal.app.ui.result

import id.sapikenal.app.data.repository.DetectionRepository
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.report.PdfReportGenerator
import id.sapikenal.app.ui.guide.GuideArticle
import id.sapikenal.app.ui.guide.GuideCategory
import id.sapikenal.app.ui.guide.GuideRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class ResultViewModelTest {
    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var detectionRepository: DetectionRepository
    private lateinit var pdfReportGenerator: PdfReportGenerator
    private lateinit var guideRepository: GuideRepository
    private lateinit var viewModel: ResultViewModel

    private val sampleBaliArticle =
        GuideArticle(
            id = "bali_1",
            category = GuideCategory.BALI,
            title = "Sapi Bali",
            summary = "Sapi asli Indonesia hasil domestikasi banteng.",
            body = "Karakteristik fisik: bulu merah bata pada betina, hitam pada jantan dewasa.",
        )

    private val sampleDetectionResult =
        DetectionResult(
            id = 42L,
            label = "bali",
            displayLabel = "Bali",
            confidence = 0.92f,
            isReliable = true,
            allScores =
                mapOf(
                    "aceh" to 0.01f,
                    "bali" to 0.92f,
                    "limusin" to 0.02f,
                    "madura" to 0.01f,
                    "non_sapi" to 0.01f,
                    "pasundan" to 0.01f,
                    "po" to 0.02f,
                ),
            inferenceMode = InferenceMode.ONLINE,
            consentStatus = ConsentStatus.ALLOWED,
            timestamp = 1700000000000L,
        )

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        detectionRepository = mock()
        pdfReportGenerator = mock()
        guideRepository = mock()

        viewModel = ResultViewModel(detectionRepository, pdfReportGenerator, guideRepository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `breedProfile returns guide article for valid canonical breed`() =
        runTest(testDispatcher) {
            whenever(guideRepository.article("bali_1")).thenReturn(flowOf(sampleBaliArticle))

            val profile = viewModel.breedProfile("bali").first()

            assertEquals(sampleBaliArticle, profile)
            assertEquals("bali_1", profile?.id)
            verify(guideRepository).article("bali_1")
        }

    @Test
    fun `breedProfile is case insensitive and trims whitespace`() =
        runTest(testDispatcher) {
            whenever(guideRepository.article("bali_1")).thenReturn(flowOf(sampleBaliArticle))

            val profile = viewModel.breedProfile("  BALI  ").first()

            assertEquals(sampleBaliArticle, profile)
            verify(guideRepository).article("bali_1")
        }

    @Test
    fun `breedProfile returns null flow for non_sapi label`() =
        runTest(testDispatcher) {
            val profile = viewModel.breedProfile("non_sapi").first()

            assertNull(profile)
        }

    @Test
    fun `breedProfile returns null flow for non_sapi variations`() =
        runTest(testDispatcher) {
            assertNull(viewModel.breedProfile("NON_SAPI").first())
            assertNull(viewModel.breedProfile("  non_sapi  ").first())
        }

    @Test
    fun `breedProfile returns null flow for unknown or empty label`() =
        runTest(testDispatcher) {
            assertNull(viewModel.breedProfile("").first())
            assertNull(viewModel.breedProfile("   ").first())
            assertNull(viewModel.breedProfile("unknown").first())
            assertNull(viewModel.breedProfile("UNKNOWN").first())
        }

    @Test
    fun `setDetectionId observes detection from repository`() =
        runTest(testDispatcher) {
            whenever(detectionRepository.observeDetection(42L)).thenReturn(flowOf(sampleDetectionResult))

            val job = launch(testDispatcher) { viewModel.selectedDetection.collect {} }
            advanceUntilIdle()

            viewModel.setDetectionId(42L)
            advanceUntilIdle()

            assertEquals(sampleDetectionResult, viewModel.selectedDetection.value)
            job.cancel()
        }

    @Test
    fun `setDetectionId with null or zero produces null selectedDetection`() =
        runTest(testDispatcher) {
            val job = launch(testDispatcher) { viewModel.selectedDetection.collect {} }
            advanceUntilIdle()

            viewModel.setDetectionId(null)
            advanceUntilIdle()
            assertNull(viewModel.selectedDetection.value)

            viewModel.setDetectionId(0L)
            advanceUntilIdle()
            assertNull(viewModel.selectedDetection.value)

            viewModel.setDetectionId(-1L)
            advanceUntilIdle()
            assertNull(viewModel.selectedDetection.value)

            job.cancel()
        }

    @Test
    fun `saveNote updates note in repository and sets noteSaved to true`() =
        runTest(testDispatcher) {
            assertFalse(viewModel.noteSaved.value)

            viewModel.saveNote(42L, "  Catatan Sapi  ", "  Kondisi sehat  ")
            advanceUntilIdle()

            verify(detectionRepository).updateNote(eq(42L), eq("Catatan Sapi"), eq("Kondisi sehat"))
            assertTrue(viewModel.noteSaved.value)

            viewModel.consumeNoteSaved()
            assertFalse(viewModel.noteSaved.value)
        }

    @Test
    fun `saveNote trims empty strings to null`() =
        runTest(testDispatcher) {
            viewModel.saveNote(42L, "   ", "")
            advanceUntilIdle()

            verify(detectionRepository).updateNote(eq(42L), eq(null), eq(null))
            assertTrue(viewModel.noteSaved.value)
        }

    @Test
    fun `exportPdf success sets pdfPath and updates cache path`() =
        runTest(testDispatcher) {
            val expectedPath = "/cache/reports/report_42.pdf"
            whenever(pdfReportGenerator.generate(sampleDetectionResult)).thenReturn(expectedPath)

            viewModel.exportPdf(sampleDetectionResult)
            advanceUntilIdle()

            assertEquals(expectedPath, viewModel.pdfPath.value)
            assertFalse(viewModel.pdfError.value)
            verify(detectionRepository).updatePdfCachePath(42L, expectedPath)

            viewModel.consumePdfPath()
            assertNull(viewModel.pdfPath.value)
        }

    @Test
    fun `exportPdf failure sets pdfError to true`() =
        runTest(testDispatcher) {
            whenever(pdfReportGenerator.generate(sampleDetectionResult)).thenReturn(null)

            viewModel.exportPdf(sampleDetectionResult)
            advanceUntilIdle()

            assertNull(viewModel.pdfPath.value)
            assertTrue(viewModel.pdfError.value)

            viewModel.consumePdfError()
            assertFalse(viewModel.pdfError.value)
        }
}
