package id.sapikenal.app.ui.result

import id.sapikenal.app.domain.model.BreedContract
import id.sapikenal.app.domain.model.DetectionResult

/** A history report is exportable only after its complete persisted record is available. */
internal fun selectResultForExport(
    fromHistory: Boolean,
    persistedResult: DetectionResult?,
    freshResult: DetectionResult?,
): DetectionResult? =
    when {
        fromHistory -> persistedResult?.takeIf { it.isCompleteForExport() }
        freshResult?.isCompleteForExport() == true -> freshResult
        else -> persistedResult?.takeIf { it.isCompleteForExport() }
    }

private fun DetectionResult.isCompleteForExport(): Boolean {
    val canonicalKeys = BreedContract.CANONICAL_LABELS.toSet()
    val expectedDisplayLabel = BreedContract.find(label)?.displayLabel
    return id > 0L &&
        expectedDisplayLabel != null &&
        displayLabel.trim() == expectedDisplayLabel &&
        allScores.keys == canonicalKeys &&
        allScores.values.all { it.isFinite() && it in 0f..1f } &&
        confidence.isFinite() &&
        confidence in 0f..1f
}
