package id.sapikenal.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/** Metadata-only payload used to synchronize one local detection record. */
@JsonClass(generateAdapter = true)
data class HistorySyncRequestDto(
    @Json(name = "device_id") val deviceId: String,
    @Json(name = "local_id") val localId: Long,
    val timestamp: Long,
    @Json(name = "predicted_class") val predictedClass: String,
    @Json(name = "display_label") val displayLabel: String,
    val confidence: Float,
    val scores: Map<String, Float>,
    val outcome: String,
    @Json(name = "rejection_reason") val rejectionReason: String? = null,
    @Json(name = "inference_mode") val inferenceMode: String,
    @Json(name = "is_reliable") val isReliable: Boolean,
    @Json(name = "processing_ms") val processingMs: Int? = null,
    val title: String? = null,
    val description: String? = null,
    @Json(name = "consent_status") val consentStatus: String? = null,
    @Json(name = "app_version") val appVersion: String? = null,
    @Json(name = "model_version") val modelVersion: String? = null,
    @Json(name = "image_source") val imageSource: String? = null,
    @Json(name = "preprocessing_summary") val preprocessingSummary: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @Json(name = "location_source") val locationSource: String? = null,
)
