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
    @Test
    fun `breed response maps to accepted domain result`() =
        runTest {
            var uploaded: MultipartBody.Part? = null
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = "madura",
                        confidence = 0.7f,
                        scores =
                            mapOf(
                                "aceh" to 0.05f,
                                "bali" to 0.05f,
                                "limusin" to 0.05f,
                                "madura" to 0.7f,
                                "non_sapi" to 0.05f,
                                "pasundan" to 0.05f,
                                "po" to 0.05f,
                            ),
                    ),
                    onUpload = { uploaded = it },
                )

            val result: DetectionResult = api.classify(byteArrayOf(1, 2, 3))

            assertEquals("madura", result.label)
            assertEquals("Madura", result.displayLabel)
            assertEquals(0.7f, result.confidence, 0.001f)
            assertEquals(
                listOf("aceh", "bali", "limusin", "madura", "non_sapi", "pasundan", "po"),
                result.allScores.keys.toList(),
            )
            assertEquals("sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32", result.modelVersion)
            assertTrue(uploaded?.headers?.get("Content-Disposition")?.contains("filename=\"photo.png\"") == true)
            assertEquals("image/png", uploaded?.body?.contentType().toString())
        }

    @Test
    fun `online response preserves low confidence as a successful six class result`() =
        runTest {
            val api =
                clientForResponse(
                    responseFor(
                        predictedClass = " aceh ",
                        confidence = 0.31f,
                        scores =
                            mapOf(
                                "aceh" to 0.31f,
                                "bali" to 0.30f,
                                "limusin" to 0.15f,
                                "madura" to 0.10f,
                                "non_sapi" to 0.05f,
                                "pasundan" to 0.05f,
                                "po" to 0.04f,
                            ),
                    ),
                )

            val result = api.classify(byteArrayOf(1, 2, 3))

            assertEquals("aceh", result.label)
            assertEquals(InferenceMode.ONLINE, result.inferenceMode)
            assertEquals("sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32", result.modelVersion)
            assertEquals(0.31f, result.confidence, 0.001f)
            assertEquals(false, result.isReliable)
            assertEquals(7, result.allScores.size)
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
                        scores = canonicalScores("bali", 1.0f),
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
                        scores = canonicalScores("bali", 1.0f),
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
                            canonicalScores(
                                "bali",
                                0.9f,
                                "aceh" to 0.05f,
                                "limusin" to 0.02f,
                                "madura" to 0.01f,
                                "pasundan" to 0.01f,
                                "po" to 0.01f,
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

    private fun canonicalScores(
        top: String,
        topScore: Float,
        vararg others: Pair<String, Float>,
    ): Map<String, Float> =
        linkedMapOf(
            "aceh" to 0f,
            "bali" to 0f,
            "limusin" to 0f,
            "madura" to 0f,
            "non_sapi" to 0f,
            "pasundan" to 0f,
            "po" to 0f,
        ).apply {
            this[top] = topScore
            others.forEach { (key, score) -> this[key] = score }
        }

    private fun responseFor(
        status: String = "success",
        predictedClass: String,
        confidence: Float,
        scores: Map<String, Float>,
        modelVersion: String = "sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32",
    ): PredictResponseDto =
        PredictResponseDto(
            status = status,
            prediction = PredictionDto(predictedClass, confidence, scores),
            modelInfo = ModelInfoDto(modelVersion),
            processingTimeMs = 8,
            preprocessingTimeMs = 2,
            inferenceTimeMs = 6,
        )

    private fun clientForResponse(
        response: PredictResponseDto,
        onUpload: (MultipartBody.Part) -> Unit = {},
    ): OnlineInferenceClient =
        OnlineInferenceClient(
            apiService =
                object : InferenceApiService {
                    override suspend fun predict(image: MultipartBody.Part): PredictResponseDto {
                        onUpload(image)
                        return response
                    }

                    override suspend fun health(): HealthResponseDto =
                        HealthResponseDto("ok", "sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32", true)

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
                        modelVersion = "sapikenal-jenis-sapi-mobilenetv3-contract-v2-fp32",
                        modelLoaded = true,
                    )

                override suspend fun upsertHistory(payload: HistorySyncRequestDto) = Response.success("{}".toResponseBody())
            }
        return OnlineInferenceClient(apiService = api)
    }
}
