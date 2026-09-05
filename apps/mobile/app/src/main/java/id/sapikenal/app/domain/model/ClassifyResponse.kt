package id.sapikenal.app.domain.model

sealed interface ClassifyResponse {
    data class Success(
        val result: DetectionResult,
    ) : ClassifyResponse

    data object ConsentRequired : ClassifyResponse
}
