package id.sapikenal.app.data.local.entity

import androidx.room.Entity

@Entity(tableName = "guide_articles", primaryKeys = ["locale", "articleKey"])
data class GuideArticleEntity(
    val locale: String,
    val articleKey: String,
    val category: String,
    val icon: String,
    val sortOrder: Int,
    val title: String,
    val summary: String,
    val body: String,
    val sourcesJson: String,
    val revision: Int,
)

@Entity(tableName = "guide_sync_metadata")
data class GuideSyncMetadataEntity(
    @androidx.room.PrimaryKey val locale: String,
    val snapshotVersion: String,
    val syncedAt: Long,
)
