package id.sapikenal.app.data.sync

import id.sapikenal.app.data.local.DeviceIdProvider
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.entity.DetectionEntity
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.data.remote.dto.HealthResponseDto
import id.sapikenal.app.data.remote.dto.HistorySyncRequestDto
import id.sapikenal.app.data.remote.dto.PredictResponseDto
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.Response
import java.io.IOException

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class HistorySyncRunnerTest {
    private lateinit var dao: DetectionDao
    private lateinit var settings: SettingsDataStore
    private lateinit var deviceIdProvider: DeviceIdProvider

    @Before
    fun setUp() {
        dao = mock()
        settings = mock()
        deviceIdProvider = mock()
        whenever(deviceIdProvider.value).thenReturn("device-12345678")
    }

    @Test
    fun `denied consent skips history upload`() =
        runTest {
            val api = RecordingHistoryApi()
            val runner = HistorySyncRunner(dao, settings, api, deviceIdProvider)

            assertEquals(HistorySyncAttempt.SUCCESS, runner.runWithConsent(false))
            assertTrue(api.requests.isEmpty())
            verify(dao, never()).findPendingSync()
        }

    @Test
    fun `allowed consent uploads rejected metadata and marks it synced`() =
        runTest {
            val entity = rejectedEntity()
            whenever(dao.findPendingSync()).thenReturn(listOf(entity))
            val api = RecordingHistoryApi()
            val runner = HistorySyncRunner(dao, settings, api, deviceIdProvider)

            assertEquals(HistorySyncAttempt.SUCCESS, runner.runWithConsent(true))

            val request = api.requests.single()
            assertEquals("device-12345678", request.deviceId)
            assertEquals(17L, request.localId)
            assertEquals("non_cattle", request.predictedClass)
            assertEquals("rejected", request.outcome)
            assertEquals("non_cattle", request.rejectionReason)
            assertEquals("offline", request.inferenceMode)
            assertEquals(4, request.scores.size)
            assertEquals(0.96f, request.scores["non_cattle"] ?: 0f, 0.001f)
            verify(dao).markSynced(17L)
        }

    @Test
    fun `upload failure requests WorkManager retry and keeps row pending`() =
        runTest {
            whenever(dao.findPendingSync()).thenReturn(listOf(rejectedEntity()))
            val api = RecordingHistoryApi(failure = IOException("offline"))
            val runner = HistorySyncRunner(dao, settings, api, deviceIdProvider)

            assertEquals(HistorySyncAttempt.RETRY, runner.runWithConsent(true))
            verify(dao, never()).markSynced(any())
        }

    private fun rejectedEntity() =
        DetectionEntity(
            id = 17L,
            timestamp = 1_710_000_000_000,
            imagePath = "/history/rejected.jpg",
            predictedClass = "non_cattle",
            displayLabel = "Objek bukan sapi",
            confidence = 0.96f,
            scoreHealthy = 0.02f,
            scoreFmd = 0.01f,
            scoreLsd = 0.01f,
            scoreNonCattle = 0.96f,
            inferenceMode = "OFFLINE",
            isReliable = false,
            processingMs = 80,
            consentStatus = "ALLOWED",
            appVersion = "0.1.0",
            modelVersion = "four-class-v1",
            outcome = "REJECTED",
            rejectionReason = "non_cattle",
        )

    private class RecordingHistoryApi(
        private val failure: Exception? = null,
    ) : InferenceApiService {
        val requests = mutableListOf<HistorySyncRequestDto>()

        override suspend fun predict(image: MultipartBody.Part): PredictResponseDto = error("predict is not used by sync tests")

        override suspend fun health(): HealthResponseDto = error("health is not used by sync tests")

        override suspend fun upsertHistory(payload: HistorySyncRequestDto): Response<ResponseBody> {
            failure?.let { throw it }
            requests += payload
            return Response.success("{}".toResponseBody("application/json".toMediaType()))
        }
    }
}
