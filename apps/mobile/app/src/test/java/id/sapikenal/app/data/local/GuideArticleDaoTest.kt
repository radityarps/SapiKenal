package id.sapikenal.app.data.local

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import id.sapikenal.app.data.local.entity.GuideArticleEntity
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], manifest = Config.NONE)
class GuideArticleDaoTest {
    private lateinit var database: AppDatabase

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).allowMainThreadQueries().build()
    }

    @After
    fun tearDown() = database.close()

    @Test
    fun replaceSnapshotRollsBackRowsAndMetadataWhenInsertFailsAfterDelete() =
        runTest {
            val dao = database.guideArticleDao()
            dao.replaceSnapshot("id-ID", "old-version", 10, listOf(article("old", "Cached")))
            database.openHelper.writableDatabase.execSQL(
                "CREATE TRIGGER reject_broken_article BEFORE INSERT ON guide_articles " +
                    "WHEN NEW.title = 'reject' BEGIN SELECT RAISE(ABORT, 'test insert failure'); END",
            )

            val result =
                runCatching {
                    dao.replaceSnapshot(
                        "id-ID",
                        "new-version",
                        20,
                        listOf(article("new", "New"), article("broken", "reject")),
                    )
                }

            check(result.isFailure)
            assertEquals(listOf("old"), dao.observeLocale("id-ID").first().map { it.articleKey })
            assertEquals("old-version", dao.metadata("id-ID")?.snapshotVersion)
            assertEquals(10L, dao.metadata("id-ID")?.syncedAt)
        }

    private fun article(
        key: String,
        title: String,
    ) = GuideArticleEntity(
        locale = "id-ID",
        articleKey = key,
        category = "app_usage",
        sortOrder = 10,
        title = title,
        summary = "summary",
        body = "body",
        sourcesJson = "[]",
        revision = 1,
    )
}
