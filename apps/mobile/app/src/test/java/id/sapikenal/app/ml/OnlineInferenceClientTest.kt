package id.sapikenal.app.ml

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.data.remote.dto.HealthResponseDto
import id.sapikenal.app.data.remote.dto.HistorySyncRequestDto
import id.sapikenal.app.data.remote.dto.PredictResponseDto
import id.sapikenal.app.domain.model.ClassifyFailure
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.HttpException
import retrofit2.Response

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class OnlineInferenceClientTest {
    private val rejectionJson =
        """
        {
          "status": "error",
          "error_code": "NON_CATTLE_IMAGE",
          "message": "No cattle detected",
          "rejection": {
            "outcome": "rejected",
            "reason": "non_cattle",
            "display_label_key": "validation.non_cattle",
            "confidence": 0.96,
            "scores": {
              "FMD": 0.01,
              "healthy": 0.02,
              "LSD": 0.01,
              "non_cattle": 0.96
            }
          },
          "model_info": {"version": "four-class-v1"},
          "processing_time_ms": 175
        }
        """.trimIndent()

    @Test
    fun `HTTP 422 non-cattle response maps to rejected domain result`() =
        runTest {
            val client = clientFor(HttpException(Response.error<PredictResponseDto>(422, rejectionJson.body())))

            val result = client.classify(byteArrayOf(1, 2, 3))

            assertEquals("non_cattle", result.label)
            assertEquals("REJECTED", result.outcome)
            assertEquals("non_cattle", result.rejectionReason)
            assertEquals(0.96f, result.confidence, 0.001f)
            assertEquals(4, result.allScores.size)
            assertEquals(0.96f, result.allScores["non_cattle"] ?: 0f, 0.001f)
            assertEquals("four-class-v1", result.modelVersion)
            assertEquals(175, result.processingMs)
        }

    @Test
    fun `HTTP 422 with missing canonical score is treated as invalid image`() =
        runTest {
            val invalidJson = rejectionJson.replace("\"LSD\": 0.01,", "")
            val client = clientFor(HttpException(Response.error<PredictResponseDto>(422, invalidJson.body())))

            try {
                client.classify(byteArrayOf(1))
                throw AssertionError("Expected ClassifyFailure.InvalidImage")
            } catch (error: ClassifyFailure.InvalidImage) {
                assertTrue(error.message!!.contains("Invalid image data"))
            }
        }

    private fun clientFor(error: HttpException): OnlineInferenceClient {
        val api =
            object : InferenceApiService {
                override suspend fun predict(image: MultipartBody.Part): PredictResponseDto = throw error

                override suspend fun health(): HealthResponseDto =
                    HealthResponseDto(
                        status = "ok",
                        modelVersion = "four-class-v1",
                        modelLoaded = true,
                    )

                override suspend fun upsertHistory(payload: HistorySyncRequestDto) = Response.success("{}".body())
            }
        return OnlineInferenceClient(
            apiService = api,
            moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build(),
        )
    }

    private fun String.body(): okhttp3.ResponseBody = toResponseBody("application/json".toMediaType())
}
