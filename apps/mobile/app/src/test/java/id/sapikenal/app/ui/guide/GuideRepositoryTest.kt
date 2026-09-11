package id.sapikenal.app.ui.guide

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import id.sapikenal.app.data.local.AppDatabase
import id.sapikenal.app.data.remote.api.GuideContentApiService
import id.sapikenal.app.data.remote.dto.GuideArticleDto
import id.sapikenal.app.data.remote.dto.GuideSnapshotDto
import id.sapikenal.app.domain.model.BreedContract
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.HttpException
import retrofit2.Response

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class GuideRepositoryTest {
    private lateinit var database: AppDatabase
    private lateinit var api: FakeGuideApi
    private lateinit var repository: GuideRepository

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).allowMainThreadQueries().build()
        api = FakeGuideApi()
        repository =
            GuideRepository(
                context,
                database.guideArticleDao(),
                api,
                com.squareup.moshi.Moshi
                    .Builder()
                    .build(),
            )
    }

    @After
    fun tearDown() = database.close()

    @Test
    fun bundledArticlesAreUsedBeforeFirstSyncAndBreedLinksExistInBothLocales() =
        runTest {
            for (locale in listOf("id-ID", "en-US")) {
                val articles = repository.articles(locale).first()
                BreedContract.definitions.forEach { breed ->
                    assertNotNull("${breed.key}/$locale", articles.find { it.id == breed.guideArticleId })
                }
            }
        }

    @Test
    fun successfulSnapshotIsReadOfflineByListAndDetailWithoutMixingLocales() =
        runTest {
            api.snapshot = snapshot("id-ID", article("bali_1", "ID"))
            assertTrue(repository.refresh("id-ID").isSuccess)
            api.snapshot = snapshot("en-US", article("bali_1", "EN"))
            assertTrue(repository.refresh("en-US").isSuccess)
            api.failure = HttpException(Response.error<Unit>(500, "failed".toResponseBody("text/plain".toMediaType())))
            assertTrue(repository.refresh("id-ID").isFailure)

            assertEquals(listOf("ID"), repository.articles("id-ID").first().map { it.title })
            assertEquals("ID", repository.article("id-ID", "bali_1").first()?.title)
            assertEquals(listOf("EN"), repository.articles("en-US").first().map { it.title })
        }

    @Test
    fun invalidSnapshotsNeverChangeCache() =
        runTest {
            api.snapshot = snapshot("id-ID", article("bali_1", "cached"))
            repository.refresh("id-ID").getOrThrow()
            val invalid =
                listOf(
                    snapshot("en-US", article("bali_1", "wrong locale")),
                    snapshot("id-ID", article("bali_1", "wrong status")).copy(status = "error"),
                    snapshot("id-ID", article("bali_1", "no version")).copy(snapshotVersion = ""),
                    snapshot("id-ID", *Array(201) { article("item_$it", "$it") }),
                    snapshot("id-ID", article("oversized", "x".repeat(121))),
                    snapshot("id-ID", article("same", "one"), article("same", "two")),
                    snapshot("id-ID", article("bad-category", "bad").copy(category = "unknown")),
                    snapshot("id-ID", article("bad-url", "bad").copy(sources = listOf("javascript:bad"))),
                )
            invalid.forEach { value ->
                api.snapshot = value
                assertTrue(repository.refresh("id-ID").isFailure)
                assertEquals(listOf("cached"), repository.articles("id-ID").first().map { it.title })
            }
        }

    @Test
    fun emptySuccessfulSnapshotRemovesLocaleAndPreventsBundleFallback() =
        runTest {
            api.snapshot = snapshot("id-ID", article("bali_1", "cached"))
            repository.refresh("id-ID").getOrThrow()
            api.snapshot = snapshot("id-ID")
            repository.refresh("id-ID").getOrThrow()

            assertTrue(repository.articles("id-ID").first().isEmpty())
            assertNotNull(database.guideArticleDao().metadata("id-ID"))
        }

    @Test
    fun duplicateKeysAreRejectedBeforeReplacingCache() =
        runTest {
            api.snapshot = snapshot("id-ID", article("bali_1", "cached"))
            repository.refresh("id-ID").getOrThrow()
            api.snapshot = snapshot("id-ID", article("bali_1", "duplicate"), article("bali_1", "duplicate"))

            assertTrue(repository.refresh("id-ID").isFailure)
            assertEquals(listOf("cached"), repository.articles("id-ID").first().map { it.title })
        }

    private fun article(
        key: String,
        title: String,
    ) = GuideArticleDto(
        articleKey = key,
        category = "bali",
        sortOrder = 10,
        title = title,
        summary = "summary",
        body = "body",
        sources = listOf("https://example.org/source"),
        revision = 1,
    )

    private fun snapshot(
        locale: String,
        vararg items: GuideArticleDto,
    ) = GuideSnapshotDto("success", locale, "version", items.toList())

    private class FakeGuideApi : GuideContentApiService {
        lateinit var snapshot: GuideSnapshotDto
        var failure: Throwable? = null

        override suspend fun articles(locale: String): GuideSnapshotDto {
            failure?.let { throw it }
            return snapshot
        }
    }
}
