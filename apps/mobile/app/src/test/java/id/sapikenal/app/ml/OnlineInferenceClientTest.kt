package id.sapikenal.app.ml

import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.data.remote.dto.HealthResponseDto
import id.sapikenal.app.data.remote.dto.HistorySyncRequestDto
import id.sapikenal.app.data.remote.dto.ModelInfoDto
import id.sapikenal.app.data.remote.dto.PredictResponseDto
import id.sapikenal.app.data.remote.dto.PredictionDto
import id.sapikenal.app.domain.model.ClassifyFailure
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import kotlinx.coroutines.test.runTest
import okhttp3.MultipartBody
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.HttpException
import retrofit2.Response

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class OnlineInferenceClientTest {
    @Test
    fun `breed response maps to accepted domain result`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = "brangus",
                        confidence = 0.7f,
                        scores =
                            mapOf(
                                "bali" to 0.1f,
                                "brahman" to 0.1f,
                                "brangus" to 0.7f,
                                "limusin" to 0.1f,
                            ),
                    ),
                )

            val result: DetectionResult = api.classify(byteArrayOf(1, 2, 3))

            assertEquals("brangus", result.label)
            assertEquals("Brangus", result.displayLabel)
            assertEquals(0.7f, result.confidence, 0.001f)
            assertEquals(
                listOf("bali", "brahman", "brangus", "limusin"),
                result.allScores.keys.toList(),
            )
            assertEquals("breed-v1", result.modelVersion)
        }

    @Test
    fun `online response preserves low confidence as a successful four class result`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = " bali ",
                        confidence = 0.31f,
                        scores =
                            mapOf(
                                "bali" to 0.31f,
                                "brahman" to 0.30f,
                                "brangus" to 0.29f,
                                "limusin" to 0.10f,
                            ),
                    ),
                )

            val result = api.classify(byteArrayOf(1, 2, 3))

            assertEquals("bali", result.label)
            assertEquals(InferenceMode.ONLINE, result.inferenceMode)
            assertEquals("breed-v1", result.modelVersion)
            assertEquals(0.31f, result.confidence, 0.001f)
            assertEquals(false, result.isReliable)
            assertEquals(4, result.allScores.size)
        }

    @Test
    fun `online response rejects a non-success status`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        status = "error",
                        predictedClass = "bali",
                        confidence = 1.0f,
                        scores =
                            mapOf(
                                "bali" to 1.0f,
                                "brahman" to 0.0f,
                                "brangus" to 0.0f,
                                "limusin" to 0.0f,
                            ),
                    ),
                )

            try {
                api.classify(byteArrayOf(1, 2, 3))
                throw AssertionError("Expected ClassifyFailure.Unknown")
            } catch (error: ClassifyFailure.Unknown) {
                assertEquals("Invalid prediction status", error.message)
            }
        }

    @Test
    fun `online response rejects an unknown predicted class`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = "unknown",
                        confidence = 1.0f,
                        scores =
                            mapOf(
                                "bali" to 1.0f,
                                "brahman" to 0.0f,
                                "brangus" to 0.0f,
                                "limusin" to 0.0f,
                            ),
                    ),
                )

            try {
                api.classify(byteArrayOf(1, 2, 3))
                throw AssertionError("Expected ClassifyFailure.Unknown")
            } catch (error: ClassifyFailure.Unknown) {
                assertEquals("Invalid predicted class", error.message)
            }
        }

    @Test
    fun `online response rejects confidence that does not match top score`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = "bali",
                        confidence = 0.6f,
                        scores =
                            mapOf(
                                "bali" to 0.9f,
                                "brahman" to 0.05f,
                                "brangus" to 0.04f,
                                "limusin" to 0.01f,
                            ),
                    ),
                )

            try {
                api.classify(byteArrayOf(1, 2, 3))
                throw AssertionError("Expected ClassifyFailure.Unknown")
            } catch (error: ClassifyFailure.Unknown) {
                assertEquals("Invalid prediction confidence", error.message)
            }
        }

    @Test
    fun `HTTP 422 is treated as invalid image`() =
        runTest {
            val client =
                clientFor(
                    HttpException(
                        Response.error<PredictResponseDto>(422, "".toResponseBody()),
                    ),
                )

            try {
                client.classify(byteArrayOf(1))
                throw AssertionError("Expected ClassifyFailure.InvalidImage")
            } catch (error: ClassifyFailure.InvalidImage) {
                assertEquals("Invalid image data", error.message)
            }
        }

    private fun responseFor(
        status: String = "success",
        predictedClass: String,
        confidence: Float,
        scores: Map<String, Float>,
        modelVersion: String = "breed-v1",
    ): PredictResponseDto =
        PredictResponseDto(
            status = status,
            prediction = PredictionDto(predictedClass, confidence, scores),
            modelInfo = ModelInfoDto(modelVersion),
            processingTimeMs = 8,
            preprocessingTimeMs = 2,
            inferenceTimeMs = 6,
        )

    private fun clientForResponse(response: PredictResponseDto): OnlineInferenceClient =
        OnlineInferenceClient(
            apiService =
                object : InferenceApiService {
                    override suspend fun predict(image: MultipartBody.Part): PredictResponseDto = response

                    override suspend fun health(): HealthResponseDto = HealthResponseDto("ok", "breed-v1", true)

                    override suspend fun upsertHistory(payload: HistorySyncRequestDto) = Response.success("{}".toResponseBody())
                },
        )

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

                override suspend fun upsertHistory(payload: HistorySyncRequestDto) = Response.success("{}".toResponseBody())
            }
        return OnlineInferenceClient(apiService = api)
    }
}
