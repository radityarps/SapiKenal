package id.sapikenal.app.ui.guide

import android.content.Context
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.data.local.dao.GuideArticleDao
import id.sapikenal.app.data.local.entity.GuideArticleEntity
import id.sapikenal.app.data.remote.api.GuideContentApiService
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

        fun articles(locale: String): Flow<List<GuideArticle>> =
            dao.observeLocale(locale).map { cached ->
                if (cached.isNotEmpty() || dao.metadata(locale) != null) {
                    cached.map(::toArticle)
                } else {
                    GuideDataSource.articles(localizedContext(locale))
                }
            }

        fun article(
            locale: String,
            key: String,
        ): Flow<GuideArticle?> = articles(locale).map { items -> items.find { it.id == key } }

        suspend fun refresh(locale: String): Result<Unit> =
            runCatching {
                val snapshot = api.articles(locale)
                validate(snapshot, locale)
                dao.replaceSnapshot(
                    locale = locale,
                    snapshotVersion = snapshot.snapshotVersion,
                    syncedAt = System.currentTimeMillis(),
                    items = snapshot.items.map { it.toEntity(locale, sourcesAdapter.toJson(it.sources)) },
                )
            }

        private fun validate(
            snapshot: GuideSnapshotDto,
            locale: String,
        ) {
            require(snapshot.status == "success" && snapshot.locale == locale)
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
                require(item.icon.isNotBlank() && item.icon.length <= 16)
                require(item.sortOrder in 0..100_000 && item.revision > 0)
                require(item.title.isNotBlank() && item.title.length <= 120)
                require(item.summary.isNotBlank() && item.summary.length <= 500)
                require(item.body.isNotBlank() && item.body.length <= 50_000)
                require(item.sources.isNotEmpty() && item.sources.size <= 20)
                require(item.sources.all(::validSource))
            }
        }

        private fun validSource(value: String): Boolean =
            runCatching {
                val uri = URI(value)
                value.length <= 2_048 && uri.scheme in setOf("http", "https") && !uri.host.isNullOrBlank()
            }.getOrDefault(false)

        private fun localizedContext(locale: String): Context {
            val config = android.content.res.Configuration(context.resources.configuration)
            config.setLocale(java.util.Locale.forLanguageTag(locale))
            return context.createConfigurationContext(config)
        }

        private fun toArticle(entity: GuideArticleEntity) =
            GuideArticle(
                id = entity.articleKey,
                category = GuideCategory.valueOf(entity.category.uppercase()),
                icon = entity.icon,
                title = entity.title,
                summary = entity.summary,
                body = entity.body,
            )

        private fun GuideArticleDto.toEntity(
            locale: String,
            sourcesJson: String,
        ) = GuideArticleEntity(
            locale,
            articleKey,
            category,
            icon,
            sortOrder,
            title,
            summary,
            body,
            sourcesJson,
            revision,
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
