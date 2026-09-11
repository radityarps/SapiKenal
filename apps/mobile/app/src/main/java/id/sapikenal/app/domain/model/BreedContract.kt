package id.sapikenal.app.domain.model

import androidx.annotation.StringRes
import id.sapikenal.app.R
import java.util.Locale

data class BreedDefinition(
    val key: String,
    val displayLabel: String,
    val englishDisplayLabel: String,
    val guideArticleId: String,
    @param:StringRes val displayNameResId: Int,
)

object BreedContract {
    val definitions =
        listOf(
            BreedDefinition("aceh", "Aceh", "Aceh", "aceh_1", R.string.result_breed_aceh),
            BreedDefinition("bali", "Bali", "Bali", "bali_1", R.string.result_breed_bali),
            BreedDefinition("limusin", "Limusin", "Limousin", "limusin_1", R.string.result_breed_limusin),
            BreedDefinition("madura", "Madura", "Madura", "madura_1", R.string.result_breed_madura),
            BreedDefinition("pasundan", "Pasundan", "Pasundan", "pasundan_1", R.string.result_breed_pasundan),
            BreedDefinition("po", "PO", "PO", "po_1", R.string.result_breed_po),
        )

    val CANONICAL_LABELS = definitions.map { it.key }
    val DISPLAY_LABELS = definitions.associate { it.key to it.displayLabel }
    val DISPLAY_LABELS_EN = definitions.associate { it.key to it.englishDisplayLabel }

    // Legacy definitions for backward compatibility when reading older detection history records
    private data class LegacyBreed(
        val key: String,
        val displayLabel: String,
        val englishDisplayLabel: String,
        val guideArticleId: String,
        @param:StringRes val displayNameResId: Int,
    ) {
        fun toBreedDefinition(): BreedDefinition =
            BreedDefinition(
                key = key,
                displayLabel = displayLabel,
                englishDisplayLabel = englishDisplayLabel,
                guideArticleId = guideArticleId,
                displayNameResId = displayNameResId,
            )
    }

    private val legacyDefinitions =
        listOf(
            LegacyBreed("brahman", "Brahman", "Brahman", "brahman_1", R.string.result_breed_brahman),
            LegacyBreed("brangus", "Brangus", "Brangus", "brangus_1", R.string.result_breed_brangus),
        ).map { it.toBreedDefinition() }

    private val byKey = (definitions + legacyDefinitions).associateBy { it.key }

    fun find(label: String): BreedDefinition? = byKey[label.trim().lowercase(Locale.ROOT)]
}
