package id.sapikenal.app.ui.settings

import android.content.Context
import android.content.SharedPreferences
import id.sapikenal.app.R
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.repository.DetectionRepository
import id.sapikenal.app.data.repository.PurgeManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

/**
 * Unit tests for SettingsViewModel upload consent toggle functionality.
 *
 * Validates: Requirements 4.1, 4.2, 4.3
 */
@OptIn(ExperimentalCoroutinesApi::class)
class SettingsViewModelTest {
    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var settingsDataStore: SettingsDataStore
    private lateinit var detectionRepository: DetectionRepository
    private lateinit var purgeManager: PurgeManager
    private lateinit var uploadConsentFlow: MutableStateFlow<Boolean?>

    private lateinit var viewModel: SettingsViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)

        settingsDataStore = mock()
        detectionRepository = mock()
        purgeManager = mock()

        // Set up flows for the mock
        uploadConsentFlow = MutableStateFlow(null)
        whenever(settingsDataStore.uploadConsent).thenReturn(uploadConsentFlow)
        whenever(settingsDataStore.textSize).thenReturn(MutableStateFlow("system"))

        viewModel = SettingsViewModel(settingsDataStore, detectionRepository, purgeManager)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `uploadConsent initial state is null when undecided`() =
        runTest(testDispatcher) {
            // Start a collector to activate WhileSubscribed
            val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
            advanceUntilIdle()

            assertNull(viewModel.uploadConsent.value)
            job.cancel()
        }

    @Test
    fun `uploadConsent reflects true when consent is granted`() =
        runTest(testDispatcher) {
            // Start a collector to activate WhileSubscribed
            val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
            advanceUntilIdle()

            uploadConsentFlow.value = true
            advanceUntilIdle()

            assertEquals(true, viewModel.uploadConsent.value)
            job.cancel()
        }

    @Test
    fun `uploadConsent reflects false when consent is denied`() =
        runTest(testDispatcher) {
            // Start a collector to activate WhileSubscribed
            val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
            advanceUntilIdle()

            uploadConsentFlow.value = false
            advanceUntilIdle()

            assertEquals(false, viewModel.uploadConsent.value)
            job.cancel()
        }

    @Test
    fun `setUploadConsent true calls settingsDataStore setUploadConsent with true`() =
        runTest(testDispatcher) {
            viewModel.setUploadConsent(true)
            advanceUntilIdle()

            verify(settingsDataStore).setUploadConsent(true)
        }

    @Test
    fun `setUploadConsent false calls settingsDataStore setUploadConsent with false`() =
        runTest(testDispatcher) {
            viewModel.setUploadConsent(false)
            advanceUntilIdle()

            verify(settingsDataStore).setUploadConsent(false)
        }

    @Test
    fun `toggle from true to false updates consent correctly`() =
        runTest(testDispatcher) {
            // Start a collector to activate WhileSubscribed
            val job = launch(testDispatcher) { viewModel.uploadConsent.collect {} }
            advanceUntilIdle()

            // Start with consent granted
            uploadConsentFlow.value = true
            advanceUntilIdle()
            assertEquals(true, viewModel.uploadConsent.value)

            // User disables consent via toggle
            viewModel.setUploadConsent(false)
            advanceUntilIdle()

            verify(settingsDataStore).setUploadConsent(false)

            // Simulate the data store updating the flow
            uploadConsentFlow.value = false
            advanceUntilIdle()

            assertEquals(false, viewModel.uploadConsent.value)
            job.cancel()
        }

    @Test
    fun `setTextSize calls settingsDataStore setTextSize`() =
        runTest(testDispatcher) {
            viewModel.setTextSize("large")
            advanceUntilIdle()

            verify(settingsDataStore).setTextSize("large")
        }

    @Test
    fun `clearAllHistory calls detectionRepository deleteAll and sets snackbar`() =
        runTest(testDispatcher) {
            viewModel.clearAllHistory()
            advanceUntilIdle()

            verify(detectionRepository).deleteAll()
            assertEquals(R.string.settings_history_cleared, viewModel.snackbarMessageRes.value)
        }

    @Test
    fun `purgeDeletedRecords calls purgeManager purgeExpired and sets snackbar`() =
        runTest(testDispatcher) {
            viewModel.purgeDeletedRecords()
            advanceUntilIdle()

            verify(purgeManager).purgeExpired()
            assertEquals(R.string.settings_purge_done, viewModel.snackbarMessageRes.value)
        }

    @Test
    fun `resetOnboarding writes false to shared preferences and sets snackbar`() {
        val mockContext: Context = mock()
        val mockPrefs: SharedPreferences = mock()
        val mockEditor: SharedPreferences.Editor = mock()

        whenever(mockContext.packageName).thenReturn("id.sapikenal.app")
        whenever(mockContext.getSharedPreferences("id.sapikenal.app_preferences", Context.MODE_PRIVATE))
            .thenReturn(mockPrefs)
        whenever(mockPrefs.edit()).thenReturn(mockEditor)
        whenever(mockEditor.putBoolean("has_completed_onboarding", false)).thenReturn(mockEditor)

        viewModel.resetOnboarding(mockContext)

        verify(mockEditor).putBoolean("has_completed_onboarding", false)
        verify(mockEditor).apply()
        assertEquals(R.string.settings_onboarding_reset, viewModel.snackbarMessageRes.value)
    }

    @Test
    fun `clearSnackbar sets snackbarMessageRes to null`() =
        runTest(testDispatcher) {
            viewModel.clearAllHistory()
            advanceUntilIdle()
            assertEquals(R.string.settings_history_cleared, viewModel.snackbarMessageRes.value)

            viewModel.clearSnackbar()
            assertNull(viewModel.snackbarMessageRes.value)
        }
}
