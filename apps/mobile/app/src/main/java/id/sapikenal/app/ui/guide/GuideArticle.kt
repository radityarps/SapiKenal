package id.sapikenal.app.ui.guide

import androidx.annotation.StringRes
import androidx.compose.ui.graphics.Color
import id.sapikenal.app.R
import id.sapikenal.app.ui.theme.SapiKenalColors

data class GuideArticle(
    val id: String,
    val category: GuideCategory,
    val title: String,
    val summary: String,
    val body: String,
)

enum class GuideCategory(
    @StringRes val titleRes: Int,
    val icon: String,
    val color: Color,
) {
    APP_USAGE(R.string.guide_tab_app, "📱", SapiKenalColors.Primary),
    ACEH(R.string.guide_tab_aceh, "🟤", SapiKenalColors.Aceh),
    BALI(R.string.guide_tab_bali, "🟤", SapiKenalColors.Bali),
    LIMUSIN(R.string.guide_tab_limusin, "🟠", SapiKenalColors.Limusin),
    MADURA(R.string.guide_tab_madura, "🟤", SapiKenalColors.Madura),
    PASUNDAN(R.string.guide_tab_pasundan, "🟤", SapiKenalColors.Pasundan),
    PO(R.string.guide_tab_po, "⚪", SapiKenalColors.Po),
    BRAHMAN(R.string.guide_tab_brahman, "⚪", SapiKenalColors.Brahman),
    BRANGUS(R.string.guide_tab_brangus, "⚫", SapiKenalColors.Brangus),
}
