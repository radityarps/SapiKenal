package id.sapikenal.app.data.remote.dto

import com.squareup.moshi.Json

data class GuideSnapshotDto(
    val status: String,
    val locale: String? = null,
    @Json(name = "snapshot_version") val snapshotVersion: String,
    val items: List<GuideArticleDto>,
)

data class ContentBlockDto(
    val id: String? = null,
    val type: String = "paragraph",
    val content: String = "",
    val items: List<String>? = null,
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
    @Json(name = "is_breed_profile") val isBreedProfile: Boolean = false,
    @Json(name = "breed_key") val breedKey: String? = null,
    @Json(name = "content_blocks") val contentBlocks: List<ContentBlockDto>? = null,
)
