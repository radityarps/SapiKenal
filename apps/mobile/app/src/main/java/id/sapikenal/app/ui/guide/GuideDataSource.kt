package id.sapikenal.app.ui.guide

import android.content.Context
import id.sapikenal.app.R

object GuideDataSource {
    fun articles(context: Context): List<GuideArticle> =
        listOf(
            // ── App Usage ───────────────────────────────────────────────────
            GuideArticle(
                id = "app_1",
                category = GuideCategory.APP_USAGE,
                icon = "📷",
                title = context.getString(R.string.guide_app_title_1),
                summary = context.getString(R.string.guide_app_summary_1),
                body = context.getString(R.string.guide_app_body_1),
            ),
            GuideArticle(
                id = "app_2",
                category = GuideCategory.APP_USAGE,
                icon = "🌐",
                title = context.getString(R.string.guide_app_title_2),
                summary = context.getString(R.string.guide_app_summary_2),
                body = context.getString(R.string.guide_app_body_2),
            ),
            GuideArticle(
                id = "app_3",
                category = GuideCategory.APP_USAGE,
                icon = "📊",
                title = context.getString(R.string.guide_app_title_3),
                summary = context.getString(R.string.guide_app_summary_3),
                body = context.getString(R.string.guide_app_body_3),
            ),
            // ── Bali ────────────────────────────────────────────────────────
            GuideArticle(
                id = "bali_1",
                category = GuideCategory.BALI,
                icon = "🔬",
                title = context.getString(R.string.guide_bali_title_1),
                summary = context.getString(R.string.guide_bali_summary_1),
                body = context.getString(R.string.guide_bali_body_1),
            ),
            GuideArticle(
                id = "bali_2",
                category = GuideCategory.BALI,
                icon = "🧬",
                title = context.getString(R.string.guide_bali_title_2),
                summary = context.getString(R.string.guide_bali_summary_2),
                body = context.getString(R.string.guide_bali_body_2),
            ),
            GuideArticle(
                id = "bali_3",
                category = GuideCategory.BALI,
                icon = "📏",
                title = context.getString(R.string.guide_bali_title_3),
                summary = context.getString(R.string.guide_bali_summary_3),
                body = context.getString(R.string.guide_bali_body_3),
            ),
            GuideArticle(
                id = "bali_4",
                category = GuideCategory.BALI,
                icon = "🌾",
                title = context.getString(R.string.guide_bali_title_4),
                summary = context.getString(R.string.guide_bali_summary_4),
                body = context.getString(R.string.guide_bali_body_4),
            ),
            // ── Brahman ─────────────────────────────────────────────────────
            GuideArticle(
                id = "brahman_1",
                category = GuideCategory.BRAHMAN,
                icon = "🔬",
                title = context.getString(R.string.guide_brahman_title_1),
                summary = context.getString(R.string.guide_brahman_summary_1),
                body = context.getString(R.string.guide_brahman_body_1),
            ),
            GuideArticle(
                id = "brahman_2",
                category = GuideCategory.BRAHMAN,
                icon = "🧬",
                title = context.getString(R.string.guide_brahman_title_2),
                summary = context.getString(R.string.guide_brahman_summary_2),
                body = context.getString(R.string.guide_brahman_body_2),
            ),
            GuideArticle(
                id = "brahman_3",
                category = GuideCategory.BRAHMAN,
                icon = "📏",
                title = context.getString(R.string.guide_brahman_title_3),
                summary = context.getString(R.string.guide_brahman_summary_3),
                body = context.getString(R.string.guide_brahman_body_3),
            ),
            GuideArticle(
                id = "brahman_4",
                category = GuideCategory.BRAHMAN,
                icon = "🌾",
                title = context.getString(R.string.guide_brahman_title_4),
                summary = context.getString(R.string.guide_brahman_summary_4),
                body = context.getString(R.string.guide_brahman_body_4),
            ),
            // ── Brangus ──────────────────────────────────────────────────────
            GuideArticle(
                id = "brangus_1",
                category = GuideCategory.BRANGUS,
                icon = "🐄",
                title = context.getString(R.string.guide_brangus_title_1),
                summary = context.getString(R.string.guide_brangus_summary_1),
                body = context.getString(R.string.guide_brangus_body_1),
            ),
            GuideArticle(
                id = "brangus_2",
                category = GuideCategory.BRANGUS,
                icon = "🧬",
                title = context.getString(R.string.guide_brangus_title_2),
                summary = context.getString(R.string.guide_brangus_summary_2),
                body = context.getString(R.string.guide_brangus_body_2),
            ),
            // ── Limusin ──────────────────────────────────────────────────────
            GuideArticle(
                id = "limusin_1",
                category = GuideCategory.LIMUSIN,
                icon = "📷",
                title = context.getString(R.string.guide_limusin_title_1),
                summary = context.getString(R.string.guide_limusin_summary_1),
                body = context.getString(R.string.guide_limusin_body_1),
            ),
            GuideArticle(
                id = "limusin_2",
                category = GuideCategory.LIMUSIN,
                icon = "🧬",
                title = context.getString(R.string.guide_limusin_title_2),
                summary = context.getString(R.string.guide_limusin_summary_2),
                body = context.getString(R.string.guide_limusin_body_2),
            ),
        )
}
