package id.sapikenal.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import id.sapikenal.app.data.local.entity.GuideArticleEntity
import id.sapikenal.app.data.local.entity.GuideSyncMetadataEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface GuideArticleDao {
    @Query("SELECT * FROM guide_articles WHERE locale = :locale ORDER BY category, sortOrder, articleKey")
    fun observeLocale(locale: String): Flow<List<GuideArticleEntity>>

    @Query("SELECT * FROM guide_articles WHERE locale = :locale AND articleKey = :articleKey LIMIT 1")
    fun observeArticle(
        locale: String,
        articleKey: String,
    ): Flow<GuideArticleEntity?>

    @Query("SELECT * FROM guide_sync_metadata WHERE locale = :locale LIMIT 1")
    suspend fun metadata(locale: String): GuideSyncMetadataEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertArticles(items: List<GuideArticleEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMetadata(metadata: GuideSyncMetadataEntity)

    @Query("DELETE FROM guide_articles WHERE locale = :locale")
    suspend fun deleteLocale(locale: String)

    @Transaction
    suspend fun replaceSnapshot(
        locale: String,
        snapshotVersion: String,
        syncedAt: Long,
        items: List<GuideArticleEntity>,
    ) {
        deleteLocale(locale)
        insertArticles(items)
        insertMetadata(GuideSyncMetadataEntity(locale, snapshotVersion, syncedAt))
    }
}
