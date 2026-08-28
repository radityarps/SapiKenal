package id.sapikenal.app.ui.guide

import androidx.annotation.StringRes
import androidx.compose.ui.graphics.Color
import id.sapikenal.app.R
import id.sapikenal.app.ui.theme.SapiKenalColors

data class GuideArticle(
    val id: String,
    val category: GuideCategory,
    val icon: String,
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
    FMD(R.string.guide_tab_fmd, "🦠", SapiKenalColors.DangerPMK),
    LSD(R.string.guide_tab_lsd, "🟠", SapiKenalColors.WarningLSD),
    HEALTHY(R.string.guide_tab_healthy, "✅", SapiKenalColors.Healthy),
}
