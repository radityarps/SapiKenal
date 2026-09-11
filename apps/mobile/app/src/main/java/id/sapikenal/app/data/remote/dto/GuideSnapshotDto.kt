package id.sapikenal.app.data.remote.dto

import com.squareup.moshi.Json

data class GuideSnapshotDto(
    val status: String,
    val locale: String,
    @Json(name = "snapshot_version") val snapshotVersion: String,
    val items: List<GuideArticleDto>,
)

data class GuideArticleDto(
    @Json(name = "article_key") val articleKey: String,
    val category: String,
    @Json(name = "sort_order") val sortOrder: Int,
    val title: String,
    val summary: String,
    val body: String,
    val sources: List<String>,
    val revision: Int,
)
