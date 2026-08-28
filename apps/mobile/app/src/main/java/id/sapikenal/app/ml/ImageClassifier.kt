package id.sapikenal.app.ml

import id.sapikenal.app.domain.model.DetectionResult

/**
 * Common interface for inference engines (online and offline) to enable
 * unit testing without Android framework dependencies.
 */
interface ImageClassifier {
    suspend fun classify(jpegBytes: ByteArray): DetectionResult
}
