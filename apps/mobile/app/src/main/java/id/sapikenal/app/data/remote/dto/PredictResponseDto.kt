package id.sapikenal.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PredictResponseDto(
    val status: String,
    val prediction: PredictionDto,
    @Json(name = "model_info")
    val modelInfo: ModelInfoDto,
    @Json(name = "processing_time_ms")
    val processingTimeMs: Int,
    @Json(name = "preprocessing_time_ms")
    val preprocessingTimeMs: Int,
    @Json(name = "inference_time_ms")
    val inferenceTimeMs: Int,
)

@JsonClass(generateAdapter = true)
data class PredictionDto(
    @Json(name = "disease_class")
    val diseaseClass: String,
    @Json(name = "display_label_key")
    val displayLabelKey: String,
    val confidence: Float,
    @Json(name = "is_reliable")
    val isReliable: Boolean,
    val scores: Map<String, Float>,
)

@JsonClass(generateAdapter = true)
data class ModelInfoDto(
    val version: String,
)

@JsonClass(generateAdapter = true)
data class RejectionDto(
    val outcome: String,
    val reason: String,
    @Json(name = "display_label_key")
    val displayLabelKey: String,
    val confidence: Float,
    val scores: Map<String, Float>,
)

@JsonClass(generateAdapter = true)
data class PredictRejectionResponseDto(
    val status: String,
    @Json(name = "error_code")
    val errorCode: String,
    val message: String,
    val rejection: RejectionDto? = null,
    @Json(name = "model_info")
    val modelInfo: ModelInfoDto? = null,
    @Json(name = "processing_time_ms")
    val processingTimeMs: Int? = null,
    @Json(name = "preprocessing_time_ms")
    val preprocessingTimeMs: Int? = null,
    @Json(name = "inference_time_ms")
    val inferenceTimeMs: Int? = null,
)
