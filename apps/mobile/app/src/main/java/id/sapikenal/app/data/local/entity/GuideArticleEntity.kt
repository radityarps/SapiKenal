package id.sapikenal.app.data.local.entity

import androidx.room.Entity

@Entity(tableName = "guide_articles", primaryKeys = ["articleKey"])
data class GuideArticleEntity(
    val articleKey: String,
    val category: String,
    val sortOrder: Int,
    val title: String,
    val summary: String,
    val body: String,
    val sourcesJson: String,
    val revision: Int,
)

@Entity(tableName = "guide_sync_metadata")
data class GuideSyncMetadataEntity(
    @androidx.room.PrimaryKey val syncKey: String = "default",
    val snapshotVersion: String,
    val syncedAt: Long,
)
