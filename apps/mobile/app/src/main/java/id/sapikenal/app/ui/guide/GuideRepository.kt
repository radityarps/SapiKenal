package id.sapikenal.app.ui.guide

import android.content.Context
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.data.local.dao.GuideArticleDao
import id.sapikenal.app.data.local.entity.GuideArticleEntity
import id.sapikenal.app.data.remote.api.GuideContentApiService
import id.sapikenal.app.data.remote.dto.ContentBlockDto
import id.sapikenal.app.data.remote.dto.GuideArticleDto
import id.sapikenal.app.data.remote.dto.GuideSnapshotDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.net.URI
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class GuideRepository
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val dao: GuideArticleDao,
        private val api: GuideContentApiService,
        moshi: Moshi,
    ) {
        private val sourcesAdapter =
            moshi.adapter<List<String>>(
                Types.newParameterizedType(List::class.java, String::class.java),
            )
        private val blocksAdapter =
            moshi.adapter<List<ContentBlockDto>>(
                Types.newParameterizedType(List::class.java, ContentBlockDto::class.java),
            )

        fun articles(): Flow<List<GuideArticle>> =
            dao.observeArticles().map { cached ->
                if (cached.isNotEmpty() || dao.metadata() != null) {
                    cached.map(::toArticle)
                } else {
                    GuideDataSource.articles(context)
                }
            }

        fun article(key: String): Flow<GuideArticle?> =
            articles().map { items -> items.find { it.id == key } }

        fun breedProfile(breedKey: String): Flow<GuideArticle?> =
            articles().map { items ->
                val canonical = breedKey.trim().lowercase()
                items.find { it.isBreedProfile && it.breedKey.equals(canonical, ignoreCase = true) }
                    ?: items.find { it.id == "${canonical}_1" }
                    ?: items.find { it.category.name.equals(canonical, ignoreCase = true) }
            }

        suspend fun refresh(): Result<Unit> =
            runCatching {
                val snapshot = api.articles()
                validate(snapshot)
                dao.replaceSnapshot(
                    snapshotVersion = snapshot.snapshotVersion,
                    syncedAt = System.currentTimeMillis(),
                    items =
                        snapshot.items.map { dto ->
                            val sourcesJson = sourcesAdapter.toJson(dto.sources)
                            val blocksJson = dto.contentBlocks?.let { blocks -> blocksAdapter.toJson(blocks) }
                            dto.toEntity(sourcesJson, blocksJson)
                        },
                )
            }

        private fun validate(snapshot: GuideSnapshotDto) {
            require(snapshot.status == "success")
            require(snapshot.snapshotVersion.isNotBlank() && snapshot.snapshotVersion.length <= 256)
            require(snapshot.items.size <= 200)
            require(
                snapshot.items
                    .map { it.articleKey }
                    .distinct()
                    .size == snapshot.items.size,
            )
            snapshot.items.forEach { item ->
                require(item.articleKey.matches(Regex("^[a-z0-9]+(?:[_-][a-z0-9]+)*$")))
                require(item.category in CATEGORIES)
                require(item.sortOrder in 0..100_000 && item.revision > 0)
                require(item.title.isNotBlank() && item.title.length <= 120)
                require(item.summary.isNotBlank() && item.summary.length <= 500)
                require(item.body.isNotBlank() && item.body.length <= 50_000)
                require(item.sources.size <= 20)
                require(item.sources.all(::validSource))
                if (item.isBreedProfile && !item.breedKey.isNullOrBlank()) {
                    require(item.breedKey.lowercase() in CATEGORIES)
                }
            }
        }

        private fun validSource(value: String): Boolean =
            runCatching {
                val uri = URI(value)
                value.length <= 2_048 && uri.scheme in setOf("http", "https") && !uri.host.isNullOrBlank()
            }.getOrDefault(false)

        private fun toArticle(entity: GuideArticleEntity) =
            GuideArticle(
                id = entity.articleKey,
                category = runCatching { GuideCategory.valueOf(entity.category.uppercase()) }.getOrDefault(GuideCategory.APP_USAGE),
                title = entity.title,
                summary = entity.summary,
                body = entity.body,
                isBreedProfile = entity.isBreedProfile,
                breedKey = entity.breedKey,
                contentBlocksJson = entity.contentBlocksJson,
            )

        private fun GuideArticleDto.toEntity(
            sourcesJson: String,
            blocksJson: String?,
        ) = GuideArticleEntity(
            articleKey = articleKey,
            category = category,
            sortOrder = sortOrder,
            title = title,
            summary = summary,
            body = body,
            sourcesJson = sourcesJson,
            revision = revision,
            isBreedProfile = isBreedProfile,
            breedKey = breedKey,
            contentBlocksJson = blocksJson,
        )

        companion object {
            private val CATEGORIES =
                setOf(
                    "app_usage",
                    "aceh",
                    "bali",
                    "brahman",
                    "brangus",
                    "limusin",
                    "madura",
                    "pasundan",
                    "po",
                )
        }
    }
