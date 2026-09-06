package id.sapikenal.app.domain.model

import androidx.annotation.StringRes
import id.sapikenal.app.R
import java.util.Locale

data class BreedDefinition(
    val key: String,
    val displayLabel: String,
    val englishDisplayLabel: String,
    val guideArticleId: String,
    @StringRes val displayNameResId: Int,
)

object BreedContract {
    val definitions =
        listOf(
            BreedDefinition("bali", "Bali", "Bali", "bali_1", R.string.result_breed_bali),
            BreedDefinition("brahman", "Brahman", "Brahman", "brahman_1", R.string.result_breed_brahman),
            BreedDefinition("brangus", "Brangus", "Brangus", "brangus_1", R.string.result_breed_brangus),
            BreedDefinition("limusin", "Limusin", "Limousin", "limusin_1", R.string.result_breed_limusin),
        )

    val CANONICAL_LABELS = definitions.map { it.key }
    val DISPLAY_LABELS = definitions.associate { it.key to it.displayLabel }
    val DISPLAY_LABELS_EN = definitions.associate { it.key to it.englishDisplayLabel }

    private val byKey = definitions.associateBy { it.key }

    fun find(label: String): BreedDefinition? = byKey[label.trim().lowercase(Locale.ROOT)]
}
