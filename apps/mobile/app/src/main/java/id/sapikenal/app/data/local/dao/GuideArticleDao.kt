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
    @Query("SELECT * FROM guide_articles ORDER BY category, sortOrder, articleKey")
    fun observeArticles(): Flow<List<GuideArticleEntity>>

    @Query("SELECT * FROM guide_articles WHERE articleKey = :articleKey LIMIT 1")
    fun observeArticle(articleKey: String): Flow<GuideArticleEntity?>

    @Query("SELECT * FROM guide_sync_metadata WHERE syncKey = 'default' LIMIT 1")
    suspend fun metadata(): GuideSyncMetadataEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertArticles(items: List<GuideArticleEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMetadata(metadata: GuideSyncMetadataEntity)

    @Query("DELETE FROM guide_articles")
    suspend fun deleteAllArticles()

    @Transaction
    suspend fun replaceSnapshot(
        snapshotVersion: String,
        syncedAt: Long,
        items: List<GuideArticleEntity>,
    ) {
        deleteAllArticles()
        insertArticles(items)
        insertMetadata(GuideSyncMetadataEntity(snapshotVersion = snapshotVersion, syncedAt = syncedAt))
    }
}
