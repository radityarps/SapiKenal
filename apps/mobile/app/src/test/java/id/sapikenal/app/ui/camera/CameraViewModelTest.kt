package id.sapikenal.app.ui.camera

import android.content.Context
import android.net.Uri
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.domain.model.ClassifyResponse
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.domain.usecase.ClassifyImageUseCase
import id.sapikenal.app.ml.preprocessing.ClientPreprocessor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.kotlin.any
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
@OptIn(ExperimentalCoroutinesApi::class)
class CameraViewModelTest {
    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var appContext: Context
    private lateinit var classifyImageUseCase: ClassifyImageUseCase
    private lateinit var settingsDataStore: SettingsDataStore
    private lateinit var clientPreprocessor: ClientPreprocessor
    private lateinit var viewModel: CameraViewModel

    private val sampleCowResult =
        DetectionResult(
            id = 1L,
            label = "pasundan",
            displayLabel = "Pasundan",
            confidence = 0.88f,
            isReliable = true,
            allScores = mapOf("pasundan" to 0.88f),
            inferenceMode = InferenceMode.ONLINE,
            consentStatus = ConsentStatus.ALLOWED,
        )

    private val sampleNonCattleResult =
        DetectionResult(
            id = 0L,
            label = "non_sapi",
            displayLabel = "Bukan Sapi",
            confidence = 0.95f,
            isReliable = true,
            allScores = mapOf("non_sapi" to 0.95f),
            inferenceMode = InferenceMode.ONLINE,
            consentStatus = ConsentStatus.ALLOWED,
        )

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        appContext = mock()
        classifyImageUseCase = mock()
        settingsDataStore = mock()
        clientPreprocessor = mock()

        whenever(appContext.getString(any())).thenReturn("Mock string")
        whenever(settingsDataStore.uploadConsent).thenReturn(MutableStateFlow(true))

        viewModel = CameraViewModel(appContext, classifyImageUseCase, settingsDataStore, clientPreprocessor)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `classify with valid cow breed invokes onResult and keeps showNonCattleWarning false`() =
        runTest(testDispatcher) {
            val testUri: Uri = mock()
            val dummyBytes = byteArrayOf(1, 2, 3)
            whenever(clientPreprocessor.process(testUri)).thenReturn(dummyBytes)
            whenever(
                classifyImageUseCase.classifyPreprocessed(
                    imageBytes = eq(dummyBytes),
                    sourceImageUri = eq(testUri),
                    updateDetectionId = eq(null),
                    isFromCamera = eq(true),
                ),
            ).thenReturn(ClassifyResponse.Success(sampleCowResult))

            var resultCallbackCalled = false
            viewModel.classify(testUri, updateDetectionId = null, isFromCamera = true) { result ->
                resultCallbackCalled = true
                assertEquals("pasundan", result.label)
            }
            advanceUntilIdle()

            assertTrue(resultCallbackCalled)
            assertFalse(viewModel.uiState.value.showNonCattleWarning)
        }

    @Test
    fun `classify with non_sapi shows rejection warning and does not navigate to result`() =
        runTest(testDispatcher) {
            val testUri: Uri = mock()
            val dummyBytes = byteArrayOf(4, 5, 6)
            whenever(clientPreprocessor.process(testUri)).thenReturn(dummyBytes)
            whenever(
                classifyImageUseCase.classifyPreprocessed(
                    imageBytes = eq(dummyBytes),
                    sourceImageUri = eq(testUri),
                    updateDetectionId = eq(null),
                    isFromCamera = eq(true),
                ),
            ).thenReturn(ClassifyResponse.Success(sampleNonCattleResult))

            var resultCallbackCalled = false
            viewModel.classify(testUri, updateDetectionId = null, isFromCamera = true) {
                resultCallbackCalled = true
            }
            advanceUntilIdle()

            assertFalse(resultCallbackCalled)
            assertTrue(viewModel.uiState.value.showNonCattleWarning)
            assertEquals(testUri, viewModel.uiState.value.pendingImageUri)
            assertTrue(viewModel.uiState.value.pendingImageIsFromCamera)
        }

    @Test
    fun `dismissNonCattleWarning resets warning state and pending URI`() =
        runTest(testDispatcher) {
            val testUri: Uri = mock()
            val dummyBytes = byteArrayOf(7, 8, 9)
            whenever(clientPreprocessor.process(testUri)).thenReturn(dummyBytes)
            whenever(
                classifyImageUseCase.classifyPreprocessed(
                    imageBytes = eq(dummyBytes),
                    sourceImageUri = eq(testUri),
                    updateDetectionId = eq(null),
                    isFromCamera = eq(false),
                ),
            ).thenReturn(ClassifyResponse.Success(sampleNonCattleResult))

            viewModel.classify(testUri, updateDetectionId = null, isFromCamera = false) {}
            advanceUntilIdle()
            assertTrue(viewModel.uiState.value.showNonCattleWarning)

            viewModel.dismissNonCattleWarning()
            assertFalse(viewModel.uiState.value.showNonCattleWarning)
            assertEquals(null, viewModel.uiState.value.pendingImageUri)
        }
}
