package id.sapikenal.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.dao.GuideArticleDao
import id.sapikenal.app.data.local.entity.DetectionEntity
import id.sapikenal.app.data.local.entity.GuideArticleEntity
import id.sapikenal.app.data.local.entity.GuideSyncMetadataEntity

@Database(
    entities = [DetectionEntity::class, GuideArticleEntity::class, GuideSyncMetadataEntity::class],
    version = 13,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun detectionDao(): DetectionDao

    abstract fun guideArticleDao(): GuideArticleDao

    companion object {
        val MIGRATION_12_13 =
            object : Migration(12, 13) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        """
                        CREATE TABLE guide_articles_new (
                            locale TEXT NOT NULL,
                            articleKey TEXT NOT NULL,
                            category TEXT NOT NULL,
                            sortOrder INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            summary TEXT NOT NULL,
                            body TEXT NOT NULL,
                            sourcesJson TEXT NOT NULL,
                            revision INTEGER NOT NULL,
                            PRIMARY KEY(locale, articleKey)
                        )
                        """.trimIndent(),
                    )
                    db.execSQL(
                        """
                        INSERT INTO guide_articles_new (
                            locale, articleKey, category, sortOrder, title, summary, body, sourcesJson, revision
                        )
                        SELECT locale, articleKey, category, sortOrder, title, summary, body, sourcesJson, revision
                        FROM guide_articles
                        """.trimIndent(),
                    )
                    db.execSQL("DROP TABLE guide_articles")
                    db.execSQL("ALTER TABLE guide_articles_new RENAME TO guide_articles")
                }
            }

        val MIGRATION_11_12 =
            object : Migration(11, 12) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        """
                        CREATE TABLE guide_articles (
                            locale TEXT NOT NULL,
                            articleKey TEXT NOT NULL,
                            category TEXT NOT NULL,
                            icon TEXT NOT NULL,
                            sortOrder INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            summary TEXT NOT NULL,
                            body TEXT NOT NULL,
                            sourcesJson TEXT NOT NULL,
                            revision INTEGER NOT NULL,
                            PRIMARY KEY(locale, articleKey)
                        )
                        """.trimIndent(),
                    )
                    db.execSQL(
                        """
                        CREATE TABLE guide_sync_metadata (
                            locale TEXT NOT NULL PRIMARY KEY,
                            snapshotVersion TEXT NOT NULL,
                            syncedAt INTEGER NOT NULL
                        )
                        """.trimIndent(),
                    )
                }
            }

        val MIGRATION_4_5 =
            object : Migration(4, 5) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN consentStatus TEXT NOT NULL DEFAULT 'UNDECIDED'",
                    )
                }
            }

        val MIGRATION_5_6 =
            object : Migration(5, 6) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN appVersion TEXT DEFAULT NULL",
                    )
                    db.execSQL(
                        "ALTER TABLE detection_records ADD COLUMN modelVersion TEXT DEFAULT NULL",
                    )
                }
            }

        val MIGRATION_6_7 =
            object : Migration(6, 7) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN imageSource TEXT DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN preprocessingSummary TEXT DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN latitude REAL DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN longitude REAL DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN deletedAt INTEGER DEFAULT NULL")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN pdfCachePath TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_7_8 =
            object : Migration(7, 8) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN locationSource TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_8_9 =
            object : Migration(8, 9) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    // Legacy score columns are removed by MIGRATION_10_11 after v9/v10 bookkeeping.
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN scoreNonCattle REAL NOT NULL DEFAULT 0.0")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN outcome TEXT NOT NULL DEFAULT 'ACCEPTED'")
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN rejectionReason TEXT DEFAULT NULL")
                }
            }

        val MIGRATION_10_11 =
            object : Migration(10, 11) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.query("SELECT 1 FROM detection_records LIMIT 1").use { cursor ->
                        if (cursor.moveToFirst()) {
                            throw IllegalStateException(
                                "Cannot migrate populated legacy detection history; back it up or reset it explicitly",
                            )
                        }
                    }
                    db.execSQL("ALTER TABLE detection_records RENAME TO detection_records_legacy")
                    db.execSQL(
                        """
                        CREATE TABLE detection_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            timestamp INTEGER NOT NULL,
                            imagePath TEXT,
                            predictedClass TEXT NOT NULL,
                            displayLabel TEXT NOT NULL,
                            confidence REAL NOT NULL,
                            scoresJson TEXT NOT NULL,
                            inferenceMode TEXT NOT NULL,
                            isReliable INTEGER NOT NULL,
                            processingMs INTEGER,
                            title TEXT,
                            description TEXT,
                            consentStatus TEXT NOT NULL,
                            appVersion TEXT,
                            modelVersion TEXT,
                            imageSource TEXT,
                            preprocessingSummary TEXT,
                            latitude REAL,
                            longitude REAL,
                            locationSource TEXT,
                            deletedAt INTEGER,
                            pdfCachePath TEXT,
                            syncStatus TEXT NOT NULL
                        )
                        """.trimIndent(),
                    )
                    // Legacy model results cannot be mapped to the breed contract.
                    // The table was verified empty above, so rebuilding it is safe.
                    db.execSQL("DROP TABLE detection_records_legacy")
                }
            }

        val MIGRATION_9_10 =
            object : Migration(9, 10) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL("ALTER TABLE detection_records ADD COLUMN syncStatus TEXT NOT NULL DEFAULT 'PENDING'")
                }
            }
    }
}
