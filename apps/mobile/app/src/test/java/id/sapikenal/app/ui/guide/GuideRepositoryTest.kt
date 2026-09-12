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
    fun bundledArticlesAreUsedBeforeFirstSyncAndBreedLinksExist() =
        runTest {
            val articles = repository.articles().first()
            BreedContract.definitions.forEach { breed ->
                assertNotNull(breed.key, articles.find { it.id == breed.guideArticleId })
            }
        }

    @Test
    fun successfulSnapshotIsReadOfflineByListAndDetail() =
        runTest {
            api.snapshot = snapshot(article("bali_1", "Bali Title"))
            assertTrue(repository.refresh().isSuccess)
            api.failure = HttpException(Response.error<Unit>(500, "failed".toResponseBody("text/plain".toMediaType())))
            assertTrue(repository.refresh().isFailure)

            assertEquals(listOf("Bali Title"), repository.articles().first().map { it.title })
            assertEquals("Bali Title", repository.article("bali_1").first()?.title)
        }

    @Test
    fun invalidSnapshotsNeverChangeCache() =
        runTest {
            api.snapshot = snapshot(article("bali_1", "cached"))
            repository.refresh().getOrThrow()
            val invalid =
                listOf(
                    snapshot(article("bali_1", "wrong status")).copy(status = "error"),
                    snapshot(article("bali_1", "no version")).copy(snapshotVersion = ""),
                    snapshot(*Array(201) { article("item_$it", "$it") }),
                    snapshot(article("oversized", "x".repeat(121))),
                    snapshot(article("same", "one"), article("same", "two")),
                    snapshot(article("bad-category", "bad").copy(category = "unknown")),
                    snapshot(article("bad-url", "bad").copy(sources = listOf("javascript:bad"))),
                )
            invalid.forEach { value ->
                api.snapshot = value
                assertTrue(repository.refresh().isFailure)
                assertEquals(listOf("cached"), repository.articles().first().map { it.title })
            }
        }

    @Test
    fun emptySuccessfulSnapshotRemovesArticlesAndPreventsBundleFallback() =
        runTest {
            api.snapshot = snapshot(article("bali_1", "cached"))
            repository.refresh().getOrThrow()
            api.snapshot = snapshot()
            repository.refresh().getOrThrow()

            assertTrue(repository.articles().first().isEmpty())
            assertNotNull(database.guideArticleDao().metadata())
        }

    @Test
    fun duplicateKeysAreRejectedBeforeReplacingCache() =
        runTest {
            api.snapshot = snapshot(article("bali_1", "cached"))
            repository.refresh().getOrThrow()
            api.snapshot = snapshot(article("bali_1", "duplicate"), article("bali_1", "duplicate"))

            assertTrue(repository.refresh().isFailure)
            assertEquals(listOf("cached"), repository.articles().first().map { it.title })
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
        vararg items: GuideArticleDto,
    ) = GuideSnapshotDto("success", "id-ID", "version", items.toList())

    private class FakeGuideApi : GuideContentApiService {
        lateinit var snapshot: GuideSnapshotDto
        var failure: Throwable? = null

        override suspend fun articles(locale: String?): GuideSnapshotDto {
            failure?.let { throw it }
            return snapshot
        }
    }
}
