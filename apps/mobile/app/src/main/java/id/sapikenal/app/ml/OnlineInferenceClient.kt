package id.sapikenal.app.ml

import android.util.Log
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.domain.model.ClassifyFailure
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
open class OnlineInferenceClient
    @Inject
    constructor(
        private val apiService: InferenceApiService,
    ) : ImageClassifier {
        open override suspend fun classify(jpegBytes: ByteArray): DetectionResult =
            withContext(Dispatchers.IO) {
                Log.d(
                    "SapiKenal",
                    "OnlineInferenceClient: sending predict request (${jpegBytes.size} bytes)",
                )
                val body = jpegBytes.toRequestBody("image/jpeg".toMediaType())
                val part = MultipartBody.Part.createFormData("image", "photo.jpg", body)

                try {
                    val response = apiService.predict(part)
                    Log.d(
                        "SapiKenal",
                        "OnlineInferenceClient: response received — status=${response.status}, prediction=${response.prediction.predictedClass}",
                    )
                    val prediction = response.prediction
                    val scores =
                        canonicalScores(prediction.scores)
                            ?: throw ClassifyFailure.Unknown("Invalid prediction scores")

                    DetectionResult(
                        label = prediction.predictedClass,
                        displayLabel = prediction.predictedClass,
                        confidence = prediction.confidence,
                        isReliable = prediction.confidence >= 0.60f,
                        allScores = scores,
                        inferenceMode = InferenceMode.ONLINE,
                        processingMs = response.processingTimeMs,
                        modelVersion = response.modelInfo.version,
                    )
                } catch (e: HttpException) {
                    Log.w(
                        "SapiKenal",
                        "OnlineInferenceClient: HTTP exception code=${e.code()}",
                    )
                    if (e.code() == 422) {
                        throw ClassifyFailure.InvalidImage("Invalid image data", e)
                    } else if (e.code() in 500..599) {
                        throw ClassifyFailure.ServiceUnavailable("Server error: ${e.code()}", e)
                    } else {
                        throw ClassifyFailure.Network("HTTP error: ${e.code()}", e)
                    }
                } catch (e: IOException) {
                    throw ClassifyFailure.Network("Network I/O error", e)
                }
            }

        private fun canonicalScores(rawScores: Map<String, Float>): Map<String, Float>? {
            val normalized = linkedMapOf<String, Float>()
            rawScores.forEach { (rawLabel, score) ->
                val label = rawLabel.trim().lowercase()
                if (label !in EXPECTED_SCORE_KEYS ||
                    normalized.put(label, score) != null
                ) {
                    return null
                }
            }
            if (normalized.keys != EXPECTED_SCORE_KEYS.toSet()) return null
            if (normalized.values.any { !it.isFinite() || it !in 0f..1f }) return null
            if (kotlin.math.abs(normalized.values.sum() - 1f) > SCORE_TOLERANCE) return null
            return EXPECTED_SCORE_KEYS.associateWith { normalized.getValue(it) }
        }

        private companion object {
            const val SCORE_TOLERANCE = 0.01f
            val EXPECTED_SCORE_KEYS = listOf("bali", "brahman", "brangus", "limusin")
        }
    }
