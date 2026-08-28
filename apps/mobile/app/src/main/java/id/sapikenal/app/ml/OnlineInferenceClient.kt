package id.sapikenal.app.ml

import android.util.Log
import com.squareup.moshi.Moshi
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.data.remote.dto.PredictRejectionResponseDto
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
import kotlin.math.abs

@Singleton
open class OnlineInferenceClient
    @Inject
    constructor(
        private val apiService: InferenceApiService,
        moshi: Moshi,
    ) : ImageClassifier {
        private val rejectionAdapter = moshi.adapter(PredictRejectionResponseDto::class.java)

        open override suspend fun classify(jpegBytes: ByteArray): DetectionResult =
            withContext(Dispatchers.IO) {
                Log.d("SapiKenal", "OnlineInferenceClient: sending predict request (${jpegBytes.size} bytes)")
                val body = jpegBytes.toRequestBody("image/jpeg".toMediaType())
                val part = MultipartBody.Part.createFormData("image", "photo.jpg", body)

                try {
                    val response = apiService.predict(part)
                    Log.d(
                        "SapiKenal",
                        "OnlineInferenceClient: response received — status=${response.status}, prediction=${response.prediction.diseaseClass}",
                    )
                    val prediction = response.prediction

                    DetectionResult(
                        label = prediction.diseaseClass,
                        displayLabel = prediction.displayLabelKey,
                        confidence = prediction.confidence,
                        isReliable = prediction.isReliable,
                        allScores = prediction.scores,
                        inferenceMode = InferenceMode.ONLINE,
                        processingMs = response.processingTimeMs,
                        modelVersion = response.modelInfo.version,
                        outcome = "ACCEPTED",
                        rejectionReason = null,
                    )
                } catch (e: HttpException) {
                    Log.w("SapiKenal", "OnlineInferenceClient: HTTP exception code=${e.code()}")
                    if (e.code() == 422) {
                        val errorBody =
                            e
                                .response()
                                ?.errorBody()
                                ?.string()
                                .orEmpty()
                        val rejectionResult = parseRejectionResponse(errorBody)
                        if (rejectionResult != null) {
                            Log.d("SapiKenal", "OnlineInferenceClient: parsed NON_CATTLE_IMAGE rejection outcome")
                            return@withContext rejectionResult
                        }
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

        internal fun parseRejectionResponse(json: String): DetectionResult? {
            return runCatching {
                val payload = rejectionAdapter.fromJson(json) ?: return null
                if (payload.errorCode != NON_CATTLE_ERROR_CODE) return null
                val rejection = payload.rejection ?: return null
                if (rejection.outcome.lowercase() != "rejected" || rejection.reason != NON_CATTLE_REASON) {
                    return null
                }
                val scores = canonicalScores(rejection.scores) ?: return null
                val confidence = rejection.confidence
                if (!confidence.isFinite() || confidence !in 0f..1f) return null
                if (abs(confidence - (scores.values.maxOrNull() ?: return null)) > SCORE_TOLERANCE) {
                    return null
                }

                DetectionResult(
                    label = NON_CATTLE_REASON,
                    displayLabel = "Objek bukan sapi",
                    confidence = confidence,
                    isReliable = false,
                    allScores = scores,
                    inferenceMode = InferenceMode.ONLINE,
                    processingMs = payload.processingTimeMs,
                    modelVersion = payload.modelInfo?.version,
                    outcome = "REJECTED",
                    rejectionReason = NON_CATTLE_REASON,
                )
            }.getOrElse { error ->
                Log.e("SapiKenal", "OnlineInferenceClient: failed to parse rejection error body", error)
                null
            }
        }

        private fun canonicalScores(rawScores: Map<String, Float>): Map<String, Float>? {
            val normalized = linkedMapOf<String, Float>()
            rawScores.forEach { (rawLabel, score) ->
                val label =
                    when (rawLabel) {
                        "FMD", "fmd" -> "FMD"
                        "healthy", "Healthy" -> "healthy"
                        "LSD", "lsd" -> "LSD"
                        "non_cattle", "NON_CATTLE" -> "non_cattle"
                        else -> return null
                    }
                if (normalized.put(label, score) != null) return null
            }
            if (normalized.keys != EXPECTED_SCORE_KEYS.toSet()) return null
            if (normalized.values.any { !it.isFinite() || it !in 0f..1f }) return null
            if (abs(normalized.values.sum() - 1f) > SCORE_TOLERANCE) return null
            return EXPECTED_SCORE_KEYS.associateWith { normalized.getValue(it) }
        }

        private companion object {
            const val NON_CATTLE_ERROR_CODE = "NON_CATTLE_IMAGE"
            const val NON_CATTLE_REASON = "non_cattle"
            const val SCORE_TOLERANCE = 0.01f
            val EXPECTED_SCORE_KEYS = listOf("FMD", "healthy", "LSD", "non_cattle")
        }
    }
